"""
ui/widgets/shared/safe_conn_mixin.py
======================================
SafeConnMixin — مكسن يضاف لأي widget يحفظ accounting conn.

إصلاحات (v6):
  - FIX: كل except Exception: pass استُبدلت بـ logger.debug/warning
    عشان الأخطاء تظهر في الـ logs بدل ما تُبتلع بصمت.
  - DualConnMixin: مكسن إضافي لأي widget يحتاج acc_conn + erp_conn معاً.
"""

import logging

logger = logging.getLogger(__name__)


class SafeConnMixin:
    """
    مكسن يوفر:
      _init_safe_conn(conn, db_name)  → تهيئة
      _get_safe_conn()                → conn صالح دايماً للشركة النشطة
      _get_company_id()               → company_id النشط
      _sync_company_id()              → تحديث _company_id من company_state
    """

    def _init_safe_conn(self, conn, db_name: str = "accounting"):
        self.__safe_conn    = conn
        self.__safe_db_name = db_name

    def _get_safe_conn(self):
        """
        يرجع conn صالح للشركة النشطة دايماً.
        1. يتحقق من self.__safe_conn بـ SELECT 1
        2. لو فشل → يجيب conn جديد من company_state
        3. لو الشركة اتغيرت → يجيب conn الشركة الجديدة تلقائياً
        """
        current_cid = self._get_company_id()
        try:
            self.__safe_conn.execute("SELECT 1")
            if current_cid is not None and hasattr(self.__safe_conn, 'validate'):
                from db.companies.companies_schema import get_company_db_path
                expected = get_company_db_path(current_cid, self.__safe_db_name)
                if not self.__safe_conn.validate(expected):
                    raise RuntimeError("conn لشركة مختلفة")
            return self.__safe_conn
        except Exception as e:
            # FIX 3: سجّل السبب بدل ما نبتلعه بصمت
            logger.debug(
                "%s._get_safe_conn: conn check failed (%s), reconnecting",
                type(self).__name__, e
            )

        try:
            from db.companies.company_state import company_state
            db = self.__safe_db_name
            new_conn = company_state._get_conn(db)
            self.__safe_conn = new_conn
            return new_conn
        except Exception as e:
            logger.warning(
                "%s._get_safe_conn: reconnect failed: %s",
                type(self).__name__, e
            )
            return self.__safe_conn

    @staticmethod
    def _get_company_id():
        try:
            from db.companies.company_state import company_state
            return company_state.company_id if company_state.is_ready else None
        except Exception as e:
            logger.debug("_get_company_id failed: %s", e)
            return None

    def _sync_company_id(self, attr: str = '_company_id'):
        """يحدث company_id المحفوظ من company_state — اتصل بعد تغيير الشركة."""
        setattr(self, attr, self._get_company_id())

    def _on_company_event_safe(self,
                               company_id: int,
                               stored_attr: str = '_company_id') -> bool:
        """
        منطق موحد للرد على company_data_changed.

        القواعد:
          1. لو stored == None → بُني قبل اختيار شركة، نحدّث ونستجيب.
          2. لو stored == company_id → نفس شركتنا، نستجيب.
          3. غير ذلك → شركة تانية، نتجاهل.

        بعد الاستجابة بيحدّث الـ stored تلقائياً.
        """
        stored = getattr(self, stored_attr, None)
        should_respond = (stored is None) or (stored == company_id)
        if should_respond:
            setattr(self, stored_attr, company_id)
        return should_respond


# ══════════════════════════════════════════════════════════
# DualConnMixin — مكسن لأي widget يحتاج acc_conn + erp_conn
# ══════════════════════════════════════════════════════════

class DualConnMixin(SafeConnMixin):
    """
    يرث من SafeConnMixin ويضيف دعم erp_conn.

    يحل التكرار في:
      - _investor_form.py, _investors_table.py, _investor_details.py
      - _link_to_entry_panel.py, investors_tab.py
      - journal_form.py, _lines_panel.py, _smart_line.py

    الاستخدام:
        class _InvestorForm(DualConnMixin, QWidget):
            def __init__(self, acc_conn, erp_conn, parent=None):
                super().__init__(parent)
                self._init_dual_conn(acc_conn, erp_conn)

        # ثم في الكود:
        acc = self._get_safe_conn()   # accounting conn
        erp = self._get_erp_conn()    # erp conn
    """

    def _init_dual_conn(self, acc_conn, erp_conn, acc_db: str = "accounting"):
        """
        تهيئة كلا الـ connections.
        يستدعي _init_safe_conn داخلياً لـ acc_conn.
        """
        self._init_safe_conn(acc_conn, acc_db)
        self._erp_conn_ref = erp_conn
        self._company_id   = self._get_company_id()

    def _get_erp_conn(self):
        """
        يرجع erp conn صالح دايماً.
        لو الـ connection مات أو لشركة مختلفة → يعمل reconnect تلقائي.
        """
        try:
            if self._erp_conn_ref is not None:
                self._erp_conn_ref.execute("SELECT 1")
                return self._erp_conn_ref
        except Exception as e:
            logger.debug(
                "%s._get_erp_conn: erp conn failed (%s), reconnecting",
                type(self).__name__, e
            )

        try:
            from db.companies.company_state import company_state
            new = company_state._get_conn("erp")
            self._erp_conn_ref = new
            return new
        except Exception as e:
            logger.warning(
                "%s._get_erp_conn: reconnect failed: %s",
                type(self).__name__, e
            )
            return self._erp_conn_ref

    def _on_dual_company_event(self, company_id: int) -> bool:
        """
        Helper موحد للرد على company_data_changed في الـ widgets التي تملك dual conn.
        يرجع True لو يجب على الـ widget إعادة التحميل.

        الاستخدام:
            def _on_company_event(self, company_id: int):
                if self._on_dual_company_event(company_id):
                    self._reload()
        """
        return self._on_company_event_safe(company_id)