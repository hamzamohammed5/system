"""
db/companies/company_state.py
==============================
Singleton يحفظ الشركة النشطة حالياً.
يُستخدم من أي مكان في التطبيق للحصول على connections الشركة الحالية.

الاستخدام:
    from db.companies.company_state import company_state

    # تعيين الشركة النشطة
    company_state.set_active(company_id)

    # جلب connection
    erp_conn = company_state.get_erp_conn()
    acc_conn = company_state.get_accounting_conn()
"""

import sqlite3
import os
from db.companies.companies_schema import get_company_db_path


class CompanyState:
    """يحفظ حالة الشركة النشطة ويوفر connections لقواعد بياناتها."""

    def __init__(self):
        self._company_id:   int | None = None
        self._company_name: str        = ""
        self._company_color: str       = "#1565c0"
        self._connections:  dict       = {}

    # ── الشركة النشطة ─────────────────────────────────────

    @property
    def company_id(self) -> int | None:
        return self._company_id

    @property
    def company_name(self) -> str:
        return self._company_name

    @property
    def company_color(self) -> str:
        return self._company_color

    @property
    def is_ready(self) -> bool:
        return self._company_id is not None

    def set_active(self, company_id: int, name: str = "", color: str = "#1565c0"):
        """تعيين الشركة النشطة وإغلاق الـ connections القديمة."""
        if self._company_id == company_id:
            return  # نفس الشركة — لا تغيير

        self._close_all()
        self._company_id    = company_id
        self._company_name  = name
        self._company_color = color or "#1565c0"

    def clear(self):
        """إلغاء الشركة النشطة."""
        self._close_all()
        self._company_id   = None
        self._company_name = ""

    # ── Connections ───────────────────────────────────────

    def get_erp_conn(self) -> sqlite3.Connection:
        return self._get_conn("erp")

    def get_accounting_conn(self) -> sqlite3.Connection:
        return self._get_conn("accounting")

    def get_inventory_conn(self) -> sqlite3.Connection:
        return self._get_conn("inventory")

    def get_orders_conn(self) -> sqlite3.Connection:
        return self._get_conn("orders")

    def get_designs_conn(self) -> sqlite3.Connection:
        return self._get_conn("designs")

    def _get_conn(self, db_name: str) -> sqlite3.Connection:
        if not self._company_id:
            raise RuntimeError("لم يتم تحديد شركة نشطة بعد")

        # أعد استخدام الـ connection لو ما زال مفتوحاً وصحيحاً
        conn = self._connections.get(db_name)
        if conn:
            try:
                conn.execute("SELECT 1")
                return conn
            except Exception:
                pass  # الـ connection مغلق أو معطوب — أنشئ جديداً

        path = get_company_db_path(self._company_id, db_name)
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"ملف قاعدة البيانات غير موجود: {path}\n"
                f"تأكد من تهيئة الشركة أولاً."
            )

        conn = sqlite3.connect(path)
        conn.row_factory     = sqlite3.Row
        conn.isolation_level = None
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        self._connections[db_name] = conn
        return conn

    def refresh_connections(self):
        """أغلق كل الـ connections وأعد فتحها عند الطلب."""
        self._close_all()

    def _close_all(self):
        for name, conn in list(self._connections.items()):
            try:
                conn.close()
            except Exception:
                pass
        self._connections.clear()

    def close_conn(self, db_name: str):
        """أغلق connection واحد فقط."""
        conn = self._connections.pop(db_name, None)
        if conn:
            try:
                conn.close()
            except Exception:
                pass


# ── Singleton ─────────────────────────────────────────────
company_state = CompanyState()