"""
ui/widgets/core/conn.py
================================
Mixins موحدة لإدارة اتصالات قاعدة البيانات.

التغييرات في هذا الإصدار (v2 — Phase 4):
  - _live_conn() لم تعد تُعيد None صامتة — ترمي RuntimeError واضحة
    بدلاً من إرجاع stored (التي قد تكون None) بصمت.
  - _get_safe_conn() نفس الإصلاح — RuntimeError بدل None.
  - _get_erp_conn() نفس الإصلاح — RuntimeError بدل None.
  - _conn_null_error() دالة مساعدة مشتركة تبني رسالة الخطأ.
  - باقي الـ API لم يتغير.
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


def _conn_null_error(class_name: str, method: str, db: str = "erp") -> RuntimeError:
    """
    يبني RuntimeError موحدة لحالة فشل الاتصال.
    رسالة واضحة تساعد في التشخيص بدل crash صامت.
    """
    return RuntimeError(
        f"{class_name}.{method}: تعذّر الحصول على اتصال بقاعدة بيانات «{db}».\n"
        "تأكد من اختيار شركة نشطة من القائمة."
    )


class LiveConnMixin:
    """
    Mixin يوفر _live_conn() لأي QWidget يحتفظ بـ DB connection.

    التغيير (Phase 4):
      بدل ما ترجع None صامتة عند فشل كل المحاولات،
      دلوقتي بترمي RuntimeError واضحة بـ class name ومعلومات التشخيص.
      هذا يوقف الـ crash في مكان تاني بدون سبب واضح.

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
          4. لو فشل كل شيء → RuntimeError واضحة (بدل None).
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
            if _test_conn(new_conn):
                self._conn_cache = new_conn
                setattr(self, self._conn_attr, new_conn)
                return self._conn_cache
        except Exception as e:
            logger.warning("%s._live_conn: fallback failed: %s",
                           type(self).__name__, e)

        # 4. كل المحاولات فشلت — RuntimeError واضحة بدل None صامتة
        raise _conn_null_error(type(self).__name__, "_live_conn")

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
            new_conn = get_accounting_connection()
            if _test_conn(new_conn):
                return new_conn
        except Exception as e:
            logger.warning("%s._live_acc_conn: fallback failed: %s",
                           type(self).__name__, e)

        raise _conn_null_error(type(self).__name__, "_live_acc_conn", "accounting")


class SafeConnMixin:
    """
    Mixin متقدم يدعم إعادة الاتصال التلقائي.

    التغيير (Phase 4):
      _get_safe_conn() لم تعد تُعيد None — ترمي RuntimeError عند الفشل.

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
            if _test_conn(new_conn):
                self.__safe_conn = new_conn
                return new_conn
        except Exception as e:
            logger.warning("%s._get_safe_conn: reconnect failed: %s",
                           type(self).__name__, e)

        # الإصلاح: RuntimeError بدل إرجاع self.__safe_conn (اللي ممكن يكون None)
        raise _conn_null_error(
            type(self).__name__, "_get_safe_conn", self.__safe_db_name
        )

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

    التغيير (Phase 4):
      _get_erp_conn() لم تعد تُعيد None — ترمي RuntimeError عند الفشل.

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
            if _test_conn(new):
                self._erp_conn_ref = new
                return new
        except Exception as e:
            logger.warning("%s._get_erp_conn: failed: %s",
                           type(self).__name__, e)

        # الإصلاح: RuntimeError بدل إرجاع self._erp_conn_ref (اللي ممكن يكون None)
        raise _conn_null_error(type(self).__name__, "_get_erp_conn", "erp")

    def _on_dual_company_event(self, company_id: int) -> bool:
        return self._should_respond_to_company(company_id)