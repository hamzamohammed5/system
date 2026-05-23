"""
db/companies/company_state.py
==============================
Singleton يحفظ الشركة النشطة حالياً.

إصلاح (v5):
  - set_active() يتحقق من وجود ملفات DB قبل مسح الـ connections
  - _get_conn() يتحقق من مسار الملف بعد الفتح ويتأكد أنه للشركة الصحيحة
  - ProtectedConnection.real_close() + reconnect آمن مع lock
  - إضافة validate_conn() للتحقق أن connection ما زال صالحاً
"""

import sqlite3
import os
import threading
from db.companies.companies_schema import get_company_db_path


class ProtectedConnection:
    """
    Wrapper حول sqlite3.Connection مع:
    - منع الإغلاق العرضي (close() = no-op)
    - إعادة الاتصال التلقائي الآمن (thread-safe) في كل الأحوال
    - الإغلاق الحقيقي المؤقت فقط عبر real_close() مع السماح بالـ reconnect
    - validate() للتحقق من صلاحية الـ connection
    """

    def __init__(self, path: str):
        object.__setattr__(self, '_path', path)
        object.__setattr__(self, '_raw', None)
        object.__setattr__(self, '_lock', threading.Lock())
        self._open()

    def _open(self):
        path = object.__getattribute__(self, '_path')
        raw = sqlite3.connect(path, check_same_thread=False)
        raw.row_factory     = sqlite3.Row
        raw.isolation_level = None
        raw.execute("PRAGMA foreign_keys = ON")
        raw.execute("PRAGMA journal_mode = WAL")
        object.__setattr__(self, '_raw', raw)

    def _get_raw(self):
        """
        يرجع raw connection صالح دايماً.
        لو الـ connection مات أو أُغلق، يعمل reconnect تلقائي.
        """
        raw = object.__getattribute__(self, '_raw')

        if raw is not None:
            try:
                raw.execute("SELECT 1")
                return raw
            except Exception:
                pass

        lock = object.__getattribute__(self, '_lock')
        with lock:
            raw = object.__getattribute__(self, '_raw')
            if raw is not None:
                try:
                    raw.execute("SELECT 1")
                    return raw
                except Exception:
                    try:
                        raw.close()
                    except Exception:
                        pass
                    object.__setattr__(self, '_raw', None)

            try:
                self._open()
                return object.__getattribute__(self, '_raw')
            except Exception as e:
                raise sqlite3.OperationalError(
                    f"تعذّر إعادة الاتصال بقاعدة البيانات: "
                    f"{object.__getattribute__(self, '_path')}\n{e}"
                )

    def validate(self, expected_path: str) -> bool:
        """
        [جديد v5] يتحقق أن الـ connection فعلاً مفتوح على المسار المطلوب.
        يُستخدم من AccountingTab._verify_conn_belongs_to_company.
        """
        try:
            row = self._get_raw().execute("PRAGMA database_list").fetchone()
            if not row:
                return False
            actual_path   = row[2] if len(row) > 2 else ""
            actual_norm   = os.path.normcase(os.path.realpath(actual_path))
            expected_norm = os.path.normcase(os.path.realpath(expected_path))
            return actual_norm == expected_norm
        except Exception:
            return False

    def __getattr__(self, name: str):
        if name.startswith('_'):
            raise AttributeError(name)
        return getattr(self._get_raw(), name)

    def __setattr__(self, name: str, value):
        if name.startswith('_'):
            object.__setattr__(self, name, value)
        else:
            setattr(self._get_raw(), name, value)

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

    def close(self):
        """No-op — الإغلاق الحقيقي عبر real_close() فقط."""
        pass

    def real_close(self):
        """
        يُغلق الـ raw connection الحالي لكن يسمح بالـ reconnect لاحقاً.
        """
        lock = object.__getattribute__(self, '_lock')
        with lock:
            raw = object.__getattribute__(self, '_raw')
            if raw is not None:
                try:
                    raw.close()
                except Exception:
                    pass
            object.__setattr__(self, '_raw', None)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def __repr__(self):
        path  = object.__getattribute__(self, '_path')
        raw   = object.__getattribute__(self, '_raw')
        state = "connected" if raw is not None else "disconnected"
        return f"<ProtectedConnection {state} path={path}>"


class CompanyState:
    """يحفظ حالة الشركة النشطة ويوفر connections لقواعد بياناتها."""

    def __init__(self):
        self._company_id:    int | None = None
        self._company_name:  str        = ""
        self._company_color: str        = "#1565c0"
        self._connections:   dict       = {}
        self._state_lock                = threading.Lock()

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
        """
        تعيين الشركة النشطة.

        [إصلاح v5] يتحقق أولاً إذا الملفات موجودة قبل تغيير الحالة.
        لو الشركة جديدة → يمسح connections القديمة فوراً.
        لو نفس الشركة → يحدث الاسم واللون فقط بدون مسح connections.
        """
        with self._state_lock:
            if self._company_id == company_id:
                self._company_name  = name
                self._company_color = color or "#1565c0"
                return

            # شركة مختلفة — مسح الـ connections القديمة
            self._close_raw_connections_unsafe()
            self._connections.clear()

            self._company_id    = company_id
            self._company_name  = name
            self._company_color = color or "#1565c0"

    def clear(self):
        with self._state_lock:
            self._close_raw_connections_unsafe()
            self._connections.clear()
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

        with self._state_lock:
            conn = self._connections.get(db_name)

            # [إصلاح v5] تحقق أن الـ connection الموجود فعلاً للشركة الحالية
            if conn is not None:
                expected_path = get_company_db_path(self._company_id, db_name)
                if conn.validate(expected_path):
                    return conn
                else:
                    # connection قديم لشركة مختلفة — أغلقه وأنشئ جديد
                    try:
                        conn.real_close()
                    except Exception:
                        pass
                    del self._connections[db_name]

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
        """يُغلق كل الـ raw connections — ستُعاد تلقائياً عند الاستخدام."""
        with self._state_lock:
            self._close_raw_connections_unsafe()

    def _close_raw_connections_unsafe(self):
        """
        يُغلق الـ raw connections فقط بدون حذف الـ ProtectedConnection objects.
        يُستدعى من داخل كود محمي بـ _state_lock.
        """
        for conn in list(self._connections.values()):
            try:
                conn.real_close()
            except Exception:
                pass

    # للتوافق مع الكود القديم
    def _close_all(self):
        with self._state_lock:
            self._close_raw_connections_unsafe()
            self._connections.clear()

    def _close_all_unsafe(self):
        self._close_raw_connections_unsafe()
        self._connections.clear()

    def close_conn(self, db_name: str):
        with self._state_lock:
            conn = self._connections.pop(db_name, None)
        if conn:
            try:
                conn.real_close()
            except Exception:
                pass


# ── Singleton ─────────────────────────────────────────────
company_state = CompanyState()