"""
ui/widgets/core/conn.py
================================
Mixins موحدة لإدارة اتصالات قاعدة البيانات.

التغييرات في LiveConnMixin:
  - _live_conn() بقت تعمل cache للـ connection بدل
    ما تحاول تجيب connection جديد في كل استدعاء.
  - _invalidate_conn_cache() جديدة — تُستدعى لو Connection اتبدل.
  - _test_conn() دالة مساعدة مشتركة — لم تتغير.

باقي الـ mixins (SafeConnMixin, DualConnMixin) لم تتغير.
"""
import logging

logger = logging.getLogger(__name__)


def _test_conn(conn) -> bool:
    """
    يختبر الاتصال — يرجع True لو سليم، False لو فشل.
    دالة مساعدة مشتركة تُلغي تكرار try/except في كل Mixin.
    """
    if conn is None:
        return False
    try:
        conn.execute("SELECT 1")
        return True
    except Exception:
        return False


class LiveConnMixin:
    """
    Mixin يوفر _live_conn() لأي QWidget يحتفظ بـ DB connection.

    التغيير: _live_conn() بقت تعمل cache — بدل ما تحاول
    تجيب connection جديد في كل استدعاء،
    بتختبر الـ cached connection الأول وبترجعه لو سليم.
    ده بيقلل عدد database round-trips بشكل ملحوظ
    في الـ widgets اللي بتستدعي _live_conn() كتير.

    الاستخدام (نفس الكود القديم — لا تغيير في الـ API):
        class MyWidget(QWidget, LiveConnMixin):
            def __init__(self, conn):
                self.conn = conn

            def load(self):
                conn = self._live_conn()
    """

    _conn_attr: str = "conn"
    _conn_cache = None   # الـ cached connection

    def _live_conn(self):
        """
        يرجع connection حي دائماً.

        الترتيب:
          1. لو الـ cached connection سليم → يرجعه مباشرة.
          2. لو لا → يجرب self.conn.
          3. لو لا → fallback من company_state.
        """
        # 1. جرب الـ cache الأول
        if _test_conn(self._conn_cache):
            return self._conn_cache

        # 2. جرب self.conn
        stored = getattr(self, self._conn_attr, None)
        if _test_conn(stored):
            self._conn_cache = stored
            return self._conn_cache

        # 3. Fallback من company_state
        logger.debug("%s._live_conn: stored conn failed, trying fallback",
                     type(self).__name__)
        try:
            from db.companies.company_state import company_state
            new_conn = company_state.get_erp_conn()
            self._conn_cache = new_conn
            # حدّث self.conn كمان عشان يتزامن
            setattr(self, self._conn_attr, new_conn)
            return self._conn_cache
        except Exception as e:
            logger.warning("%s._live_conn: fallback failed: %s",
                           type(self).__name__, e)
            return stored

    def _invalidate_conn_cache(self):
        """
        يمسح الـ cached connection.
        استدعه لو اتغيرت الشركة النشطة أو الـ connection.
        """
        self._conn_cache = None

    def _live_acc_conn(self):
        """يرجع accounting connection حي."""
        stored = getattr(self, "acc_conn", None)

        if _test_conn(stored):
            return stored

        logger.debug("%s._live_acc_conn: failed, trying fallback",
                     type(self).__name__)
        try:
            from db.shared.connection import get_accounting_connection
            return get_accounting_connection()
        except Exception as e:
            logger.warning("%s._live_acc_conn: fallback failed: %s",
                           type(self).__name__, e)
            return stored


class SafeConnMixin:
    """
    Mixin متقدم يدعم إعادة الاتصال التلقائي.

    الاستخدام:
        class MyWidget(QWidget, SafeConnMixin):
            def __init__(self, conn):
                self._init_safe_conn(conn, "accounting")
    """

    def _init_safe_conn(self, conn, db_name: str = "accounting"):
        self.__safe_conn    = conn
        self.__safe_db_name = db_name

    def _get_safe_conn(self):
        if _test_conn(self.__safe_conn):
            return self.__safe_conn

        logger.debug("%s._get_safe_conn: reconnecting", type(self).__name__)
        try:
            from db.companies.company_state import company_state
            new_conn = company_state._get_conn(self.__safe_db_name)
            self.__safe_conn = new_conn
            return new_conn
        except Exception as e:
            logger.warning("%s._get_safe_conn: reconnect failed: %s",
                           type(self).__name__, e)
            return self.__safe_conn

    @staticmethod
    def _get_company_id() -> int | None:
        try:
            from db.companies.company_state import company_state
            return company_state.company_id if company_state.is_ready else None
        except Exception:
            return None

    def _should_respond_to_company(self, company_id: int,
                                    stored_attr: str = "_company_id") -> bool:
        stored = getattr(self, stored_attr, None)
        should = (stored is None) or (stored == company_id)
        if should:
            setattr(self, stored_attr, company_id)
        return should


class DualConnMixin(SafeConnMixin):
    """
    Mixin لأي widget يحتاج acc_conn + erp_conn معاً.

    الاستخدام:
        class MyWidget(QWidget, DualConnMixin):
            def __init__(self, acc_conn, erp_conn):
                self._init_dual_conn(acc_conn, erp_conn)

            def load(self):
                acc = self._get_safe_conn()
                erp = self._get_erp_conn()
    """

    def _init_dual_conn(self, acc_conn, erp_conn, acc_db: str = "accounting"):
        self._init_safe_conn(acc_conn, acc_db)
        self._erp_conn_ref = erp_conn
        self._company_id   = self._get_company_id()

    def _get_erp_conn(self):
        if _test_conn(self._erp_conn_ref):
            return self._erp_conn_ref

        logger.debug("%s._get_erp_conn: reconnecting", type(self).__name__)
        try:
            from db.companies.company_state import company_state
            new = company_state._get_conn("erp")
            self._erp_conn_ref = new
            return new
        except Exception as e:
            logger.warning("%s._get_erp_conn: failed: %s",
                           type(self).__name__, e)
            return self._erp_conn_ref

    def _on_dual_company_event(self, company_id: int) -> bool:
        return self._should_respond_to_company(company_id)