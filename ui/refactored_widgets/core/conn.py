"""
ui/widgets/shared/core/conn.py
================================
Mixins موحدة لإدارة اتصالات قاعدة البيانات.

دمج LiveConnMixin + SafeConnMixin + DualConnMixin في ملف واحد
بدل ثلاثة ملفات متفرقة.
"""
import logging

logger = logging.getLogger(__name__)


class LiveConnMixin:
    """
    Mixin يوفر _live_conn() لأي QWidget يحتفظ بـ DB connection.

    الاستخدام:
        class MyWidget(QWidget, LiveConnMixin):
            def __init__(self, conn):
                self.conn = conn

            def load(self):
                conn = self._live_conn()
    """

    # اسم الـ attribute الذي يحتفظ بالـ connection (override لو مختلف)
    _conn_attr: str = "conn"

    def _live_conn(self):
        """يرجع connection حي دائماً — يعمل fallback من company_state."""
        stored = getattr(self, self._conn_attr, None)

        if stored is not None:
            try:
                stored.execute("SELECT 1")
                return stored
            except Exception as e:
                logger.debug("%s._live_conn: stored conn failed (%s)", type(self).__name__, e)

        try:
            from db.companies.company_state import company_state
            return company_state.get_erp_conn()
        except Exception as e:
            logger.warning("%s._live_conn: fallback failed: %s", type(self).__name__, e)
            return stored

    def _live_acc_conn(self):
        """يرجع accounting connection حي."""
        stored = getattr(self, "acc_conn", None)

        if stored is not None:
            try:
                stored.execute("SELECT 1")
                return stored
            except Exception as e:
                logger.debug("%s._live_acc_conn: failed (%s)", type(self).__name__, e)

        try:
            from db.shared.connection import get_accounting_connection
            return get_accounting_connection()
        except Exception as e:
            logger.warning("%s._live_acc_conn: fallback failed: %s", type(self).__name__, e)
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
        try:
            self.__safe_conn.execute("SELECT 1")
            return self.__safe_conn
        except Exception as e:
            logger.debug("%s._get_safe_conn: reconnecting (%s)", type(self).__name__, e)

        try:
            from db.companies.company_state import company_state
            new_conn = company_state._get_conn(self.__safe_db_name)
            self.__safe_conn = new_conn
            return new_conn
        except Exception as e:
            logger.warning("%s._get_safe_conn: reconnect failed: %s", type(self).__name__, e)
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
        """
        يحدد إذا كان الـ widget يجب أن يستجيب لـ company_data_changed.
        يحدّث الـ stored_attr تلقائياً عند الاستجابة.
        """
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
        try:
            if self._erp_conn_ref is not None:
                self._erp_conn_ref.execute("SELECT 1")
                return self._erp_conn_ref
        except Exception as e:
            logger.debug("%s._get_erp_conn: reconnecting (%s)", type(self).__name__, e)

        try:
            from db.companies.company_state import company_state
            new = company_state._get_conn("erp")
            self._erp_conn_ref = new
            return new
        except Exception as e:
            logger.warning("%s._get_erp_conn: failed: %s", type(self).__name__, e)
            return self._erp_conn_ref

    def _on_dual_company_event(self, company_id: int) -> bool:
        return self._should_respond_to_company(company_id)