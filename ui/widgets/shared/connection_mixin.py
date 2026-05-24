"""
ui/widgets/shared/connection_mixin.py
======================================
LiveConnMixin — مكسن يوحّد نمط الـ live connection في كل الـ widgets.

المشكلة:
  كل widget بيكرر نفس الكود:
    def _live_conn(self):
        if self.conn is not None:
            try:
                self.conn.execute("SELECT 1")
                return self.conn
            except Exception:
                pass
        from db.companies.company_state import company_state
        return company_state.get_erp_conn()

الحل:
  يرث من LiveConnMixin ويستخدم self._live_conn() مباشرة.

الاستخدام:
    from ui.widgets.shared.connection_mixin import LiveConnMixin

    class MyWidget(QWidget, LiveConnMixin):
        def __init__(self, conn):
            super().__init__()
            self.conn = conn

        def load(self):
            conn = self._live_conn()
            ...

    # أو مع اسم attribute مختلف:
    class MyWidget(QWidget, LiveConnMixin):
        _conn_attr = "_my_conn"   # اسم الـ attribute اللي بيخزن conn

        def __init__(self, conn):
            self._my_conn = conn

ملاحظة: الـ attribute الافتراضي هو "conn".
"""


class LiveConnMixin:
    """
    مكسن يوفر _live_conn() لأي QWidget يحتفظ بـ DB connection.

    القواعد:
      1. يتحقق من self.conn (أو self.{_conn_attr}) بـ SELECT 1
      2. لو فشل → يجيب connection حي من company_state
      3. يعمل بأمان حتى لو conn = None
    """

    # اسم الـ attribute اللي بيخزن الـ connection
    # يمكن override في الـ subclass لو الاسم مختلف
    _conn_attr: str = "conn"

    def _live_conn(self):
        """
        يرجع connection حي صالح للشركة النشطة دايماً.
        """
        stored = getattr(self, self._conn_attr, None)

        if stored is not None:
            try:
                stored.execute("SELECT 1")
                return stored
            except Exception:
                pass

        # Fallback: اجلب من company_state
        try:
            from db.companies.company_state import company_state
            return company_state.get_erp_conn()
        except Exception:
            return stored  # آخر محاولة — قد يفشل

    def _live_acc_conn(self):
        """
        يرجع accounting connection حي.
        يستخدم self.acc_conn أو company_state.
        """
        stored = getattr(self, "acc_conn", None)

        if stored is not None:
            try:
                stored.execute("SELECT 1")
                return stored
            except Exception:
                pass

        try:
            from db.shared.connection import get_accounting_connection
            return get_accounting_connection()
        except Exception:
            return stored