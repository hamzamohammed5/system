"""
ui/tabs/accounting/safe_conn_mixin.py
======================================
SafeConnMixin — مكسن صغير يضاف لأي widget يحفظ accounting conn.

الهدف: ضمان أن الـ conn المستخدم في أي query هو دائماً
للشركة النشطة، حتى لو حدث تبديل شركات بشكل غير متوقع.

الاستخدام:
    class MyPanel(SafeConnMixin, QWidget):
        def __init__(self, conn, parent=None):
            super().__init__(parent)
            self._init_safe_conn(conn, "accounting")
            ...

        def _load(self):
            conn = self._get_safe_conn()
            rows = fetch_something(conn)
"""

from PyQt5.QtCore import QObject


class SafeConnMixin:
    """
    مكسن يوفر:
      _init_safe_conn(conn, db_name)  → تهيئة
      _get_safe_conn()                → conn صالح دايماً
      _get_company_id()               → company_id النشط
    """

    def _init_safe_conn(self, conn, db_name: str = "accounting"):
        """يُستدعى في __init__ بدلاً من self.conn = conn مباشرة."""
        self.__safe_conn     = conn
        self.__safe_db_name  = db_name

    def _get_safe_conn(self):
        """
        يرجع conn صالح دايماً.
        1. يتحقق من self.__safe_conn بـ SELECT 1
        2. لو فشل → يجيب conn جديد من company_state
        3. يحدّث self.__safe_conn للاستخدام القادم
        """
        try:
            self.__safe_conn.execute("SELECT 1")
            return self.__safe_conn
        except Exception:
            pass

        try:
            from db.companies.company_state import company_state
            db = getattr(self, '_SafeConnMixin__safe_db_name', 'accounting')
            new_conn = company_state._get_conn(db)
            self.__safe_conn = new_conn
            return new_conn
        except Exception:
            # fallback أخير — ارجع الـ conn القديم حتى لو تالف
            return self.__safe_conn

    @staticmethod
    def _get_company_id():
        """يرجع company_id النشط أو None."""
        try:
            from db.companies.company_state import company_state
            return company_state.company_id if company_state.is_ready else None
        except Exception:
            return None

    def _on_company_event_safe(self, company_id: int, stored_company_id_attr: str = '_company_id'):
        """
        منطق موحد للرد على company_data_changed.
        يعالج حالة _company_id=None (بُني قبل اختيار شركة).

        الاستخدام:
            def _on_company_event(self, company_id):
                if self._on_company_event_safe(company_id):
                    self._load()
        """
        stored = getattr(self, stored_company_id_attr, None)
        if stored is None:
            # بُني قبل اختيار شركة — نحدّث ونستجيب
            setattr(self, stored_company_id_attr, company_id)
            return True
        return stored == company_id


# ══════════════════════════════════════════════════════════════════════════════
# مثال على الاستخدام في التبويبات المالية
# ══════════════════════════════════════════════════════════════════════════════

USAGE_EXAMPLE = '''
# قبل الإصلاح:
class IncomeStatementTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn                          # ← مشكلة: ثابت
        self._company_id = _get_current_company_id()    # ← مشكلة: ممكن None
        ...

    def _on_company_event(self, company_id: int):
        if company_id == self._company_id:              # ← مشكلة: None != any int
            self._load()


# بعد الإصلاح:
class IncomeStatementTab(SafeConnMixin, QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self._init_safe_conn(conn, "accounting")        # ← صح
        self._company_id = self._get_company_id()       # ← ممكن None — لكن نعالجه
        ...

    def _on_company_event(self, company_id: int):
        if self._on_company_event_safe(company_id):     # ← يعالج None تلقائياً
            self._load()

    def _load(self):
        conn = self._get_safe_conn()                    # ← conn حي دايماً
        data = income_statement(conn)
        ...
'''