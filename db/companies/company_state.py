"""
db/companies/company_state.py
==============================
Singleton يحفظ الشركة النشطة حالياً.
يُستخدم من أي مكان في التطبيق للحصول على connections الشركة الحالية.

الإصلاح (v2):
    ProtectedConnection أصبح "lazy-reconnecting":
    - conn.close() لا تزال no-op
    - أي عملية على connection مغلق → تُعيد الفتح تلقائياً
    - هذا يحل مشكلة "Cannot operate on a closed database" عند تغيير الشركة
      أو عند أي كود خارجي يستدعي close() عن طريق الخطأ.
"""

import sqlite3
import os
from db.companies.companies_schema import get_company_db_path


class ProtectedConnection:
    """
    Wrapper حول sqlite3.Connection مع:
    - منع الإغلاق العرضي (close() = no-op)
    - إعادة الاتصال التلقائي لو الـ raw connection مات لأي سبب
    - الإغلاق الحقيقي فقط عبر real_close()
    """

    def __init__(self, path: str):
        # نحفظ الـ path عشان نعيد الفتح لو احتجنا
        object.__setattr__(self, '_path', path)
        object.__setattr__(self, '_raw', None)
        object.__setattr__(self, '_closed', False)
        self._open()

    def _open(self):
        """يفتح أو يعيد فتح الـ raw connection."""
        path = object.__getattribute__(self, '_path')
        raw = sqlite3.connect(path)
        raw.row_factory     = sqlite3.Row
        raw.isolation_level = None
        raw.execute("PRAGMA foreign_keys = ON")
        raw.execute("PRAGMA journal_mode = WAL")
        object.__setattr__(self, '_raw', raw)
        object.__setattr__(self, '_closed', False)

    def _get_raw(self):
        """يرجع الـ raw connection، ويعيد الفتح لو مات."""
        closed = object.__getattribute__(self, '_closed')
        if closed:
            self._open()
            return object.__getattribute__(self, '_raw')

        raw = object.__getattribute__(self, '_raw')
        # تحقق إن الـ connection لسه شغّال
        try:
            raw.execute("SELECT 1")
            return raw
        except Exception:
            # مات → أعد الفتح
            self._open()
            return object.__getattribute__(self, '_raw')

    # ── تمرير كل الـ attributes للـ raw connection ──

    def __getattr__(self, name: str):
        if name.startswith('_'):
            raise AttributeError(name)
        return getattr(self._get_raw(), name)

    def __setattr__(self, name: str, value):
        if name.startswith('_'):
            object.__setattr__(self, name, value)
        else:
            setattr(self._get_raw(), name, value)

    # ── Override close() بـ no-op ──

    def close(self):
        """لا تفعل شيئاً — الإغلاق الحقيقي عبر real_close()."""
        pass

    def real_close(self):
        """الإغلاق الحقيقي للـ connection — بدون إمكانية إعادة الفتح."""
        object.__setattr__(self, '_closed', True)
        raw = object.__getattribute__(self, '_raw')
        if raw:
            try:
                raw.close()
            except Exception:
                pass
        object.__setattr__(self, '_raw', None)

    # ── دعم context manager ──

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    # ── تمرير execute و executescript و cursor مباشرة ──
    # (لأنها الأكثر استخداماً وعشان نتفادى أي overhead)

    def execute(self, sql, params=()):
        return self._get_raw().execute(sql, params)

    def executemany(self, sql, seq):
        return self._get_raw().executemany(sql, seq)

    def executescript(self, script):
        return self._get_raw().executescript(script)

    def cursor(self):
        return self._get_raw().cursor()

    def commit(self):
        return self._get_raw().commit()

    def rollback(self):
        return self._get_raw().rollback()


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

        # لو عندنا connection موجود → ارجعه (هو يعرف يعيد الفتح لو احتاج)
        conn = self._connections.get(db_name)
        if conn is not None:
            return conn

        path = get_company_db_path(self._company_id, db_name)
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"ملف قاعدة البيانات غير موجود: {path}\n"
                f"تأكد من تهيئة الشركة أولاً."
            )

        conn = ProtectedConnection(path)
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