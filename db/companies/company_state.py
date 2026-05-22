"""
db/companies/company_state.py
==============================
Singleton يحفظ الشركة النشطة حالياً.
يُستخدم من أي مكان في التطبيق للحصول على connections الشركة الحالية.

الإصلاح:
    الـ connections المشتركة محمية من الإغلاق العرضي عبر ProtectedConnection wrapper.
    أي كود يستدعي conn.close() على shared connection لن يُغلقه فعلاً.
    الإغلاق الحقيقي يحدث فقط عند _close_all() عبر conn.real_close().
"""

import sqlite3
import os
from db.companies.companies_schema import get_company_db_path


class ProtectedConnection:
    """
    Wrapper حول sqlite3.Connection يمنع الإغلاق العرضي.
    conn.close() → لا تفعل شيئاً.
    conn.real_close() → الإغلاق الحقيقي.
    كل الـ attributes والـ methods الأخرى تُمرَّر للـ connection الأصلي.
    """

    def __init__(self, raw_conn: sqlite3.Connection):
        # نحفظ الـ connection الأصلي في __dict__ مباشرة لتجنب __setattr__ recursion
        object.__setattr__(self, '_raw', raw_conn)

    # ── تمرير كل الـ attributes للـ connection الأصلي ──

    def __getattr__(self, name: str):
        return getattr(object.__getattribute__(self, '_raw'), name)

    def __setattr__(self, name: str, value):
        if name == '_raw':
            object.__setattr__(self, name, value)
        else:
            setattr(object.__getattribute__(self, '_raw'), name, value)

    # ── Override close() بـ no-op ──

    def close(self):
        """لا تفعل شيئاً — الإغلاق الحقيقي عبر real_close()."""
        pass

    def real_close(self):
        """الإغلاق الحقيقي للـ connection."""
        try:
            object.__getattribute__(self, '_raw').close()
        except Exception:
            pass

    # ── دعم context manager ──

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def _make_protected_connection(path: str) -> ProtectedConnection:
    """
    ينشئ ProtectedConnection — connection مع حماية من الإغلاق العرضي.
    """
    raw = sqlite3.connect(path)
    raw.row_factory     = sqlite3.Row
    raw.isolation_level = None
    raw.execute("PRAGMA foreign_keys = ON")
    raw.execute("PRAGMA journal_mode = WAL")
    return ProtectedConnection(raw)


class CompanyState:
    """يحفظ حالة الشركة النشطة ويوفر connections لقواعد بياناتها."""

    def __init__(self):
        self._company_id:    int | None = None
        self._company_name:  str        = ""
        self._company_color: str        = "#1565c0"
        self._connections:   dict       = {}

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
            return
        self._close_all()
        self._company_id    = company_id
        self._company_name  = name
        self._company_color = color or "#1565c0"

    def clear(self):
        """إلغاء الشركة النشطة."""
        self._close_all()
        self._company_id   = None
        self._company_name = ""

    def get_erp_conn(self) -> ProtectedConnection:
        return self._get_conn("erp")

    def get_accounting_conn(self) -> ProtectedConnection:
        return self._get_conn("accounting")

    def get_inventory_conn(self) -> ProtectedConnection:
        return self._get_conn("inventory")

    def get_orders_conn(self) -> ProtectedConnection:
        return self._get_conn("orders")

    def get_designs_conn(self) -> ProtectedConnection:
        return self._get_conn("designs")

    def _get_conn(self, db_name: str) -> ProtectedConnection:
        if not self._company_id:
            raise RuntimeError("لم يتم تحديد شركة نشطة بعد")

        conn = self._connections.get(db_name)
        if conn:
            try:
                conn.execute("SELECT 1")
                return conn
            except Exception:
                pass

        path = get_company_db_path(self._company_id, db_name)
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"ملف قاعدة البيانات غير موجود: {path}\n"
                f"تأكد من تهيئة الشركة أولاً."
            )

        conn = _make_protected_connection(path)
        self._connections[db_name] = conn
        return conn

    def refresh_connections(self):
        """أغلق كل الـ connections وأعد فتحها عند الطلب."""
        self._close_all()

    def _close_all(self):
        """الإغلاق الحقيقي لكل الـ connections."""
        for name, conn in list(self._connections.items()):
            try:
                conn.real_close()
            except Exception:
                pass
        self._connections.clear()

    def close_conn(self, db_name: str):
        """أغلق connection واحد فقط (إغلاق حقيقي)."""
        conn = self._connections.pop(db_name, None)
        if conn:
            try:
                conn.real_close()
            except Exception:
                pass


# ── Singleton ─────────────────────────────────────────────
company_state = CompanyState()