"""
ui/tabs/accounting/safe_conn_mixin.py
======================================
SafeConnMixin — مكسن يضاف لأي widget يحفظ accounting conn.

إصلاحات (v4):
  - _on_company_event_safe: معالجة أفضل لحالة company_id=None
  - _get_safe_conn: تحقق إضافي من المسار بعد الـ reconnect
  - _sync_company_id: دالة مساعدة لتحديث _company_id بعد تغيير الشركة
"""


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
        # أولاً: تحقق إن الـ conn الحالي للشركة النشطة
        current_cid = self._get_company_id()
        try:
            self.__safe_conn.execute("SELECT 1")
            # تحقق إضافي: هل الـ conn للشركة الصح؟
            if current_cid is not None and hasattr(self.__safe_conn, 'validate'):
                from db.companies.companies_schema import get_company_db_path
                expected = get_company_db_path(current_cid, self.__safe_db_name)
                if not self.__safe_conn.validate(expected):
                    raise RuntimeError("conn لشركة مختلفة")
            return self.__safe_conn
        except Exception:
            pass

        # ثانياً: جيب conn جديد من company_state
        try:
            from db.companies.company_state import company_state
            db = self.__safe_db_name
            new_conn = company_state._get_conn(db)
            self.__safe_conn = new_conn
            return new_conn
        except Exception:
            return self.__safe_conn

    @staticmethod
    def _get_company_id():
        try:
            from db.companies.company_state import company_state
            return company_state.company_id if company_state.is_ready else None
        except Exception:
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