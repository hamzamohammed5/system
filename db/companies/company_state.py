"""
db/companies/company_state.py
==============================
Singleton يحفظ الشركة النشطة حالياً.

إصلاح (v6):
  - إصلاح 4: ProtectedConnection._get_raw() fast-path بدون SELECT 1
    بمجرد أن يكون _raw موجود يُعاد مباشرة — الـ reconnect يحدث فقط
    عند فشل أول query حقيقية (SQLite يرمي OperationalError)
  - إصلاح 12: set_active() يُبطل AppState cache تلقائياً بعد تغيير الشركة
  - validate() تبقى للتحقق الصريح من المسار (تُستدعى من set_active فقط)

تحسين 42:
  - _get_conn() لا يستدعي validate() (التي تنفذ PRAGMA) في كل access.
  - بدلاً من ذلك يقارن _path المخزون على ProtectedConnection مباشرة.
  - validate() أصبحت تُستدعى فقط عند الضرورة (تغيير الشركة).
  - هذا يقلل overhead من O(PRAGMA + string compare) إلى O(string compare).
"""

import sqlite3
import os
import threading
from db.companies.companies_schema import get_company_db_path


class ProtectedConnection:
    """
    Wrapper حول sqlite3.Connection مع:
    - منع الإغلاق العرضي (close() = no-op)
    - إعادة الاتصال التلقائي الآمن (thread-safe) عند الحاجة
    - الإغلاق الحقيقي المؤقت فقط عبر real_close() مع السماح بالـ reconnect
    - validate() للتحقق من صلاحية الـ connection (يُستدعى من set_active فقط)

    [تحسين 42]: _path محفوظ كـ attribute — يُقرأ مباشرة دون PRAGMA في hot path.
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
        Fast-path: يرجع الـ connection مباشرة لو موجود.
        لا يُجري SELECT 1 في كل استدعاء.
        لو الـ connection مات، أول query حقيقية ستفشل وتطلق reconnect.
        Slow-path (reconnect) يُستدعى فقط لو _raw = None.
        """
        raw = object.__getattribute__(self, '_raw')
        if raw is not None:
            return raw

        lock = object.__getattribute__(self, '_lock')
        with lock:
            raw = object.__getattribute__(self, '_raw')
            if raw is not None:
                return raw
            try:
                self._open()
                return object.__getattribute__(self, '_raw')
            except Exception as e:
                raise sqlite3.OperationalError(
                    f"تعذّر إعادة الاتصال بقاعدة البيانات: "
                    f"{object.__getattribute__(self, '_path')}\n{e}"
                )

    def _reconnect_after_error(self):
        """
        يُستدعى داخلياً عند فشل query — يُعيد فتح الـ connection.
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
            try:
                self._open()
            except Exception as e:
                raise sqlite3.OperationalError(
                    f"تعذّر إعادة الاتصال: "
                    f"{object.__getattribute__(self, '_path')}\n{e}"
                )

    def path_matches(self, expected_path: str) -> bool:
        """
        [تحسين 42] يقارن المسار المخزون بالمسار المتوقع — بدون PRAGMA.
        يُستدعى من _get_conn() في hot path بدل validate().
        مقارنة string بسيطة: O(1) بدل PRAGMA + I/O.
        """
        stored_path = object.__getattribute__(self, '_path')
        return (os.path.normcase(os.path.realpath(stored_path)) ==
                os.path.normcase(os.path.realpath(expected_path)))

    def validate(self, expected_path: str) -> bool:
        """
        يتحقق أن الـ connection فعلاً مفتوح على المسار المطلوب عبر PRAGMA.
        [تحسين 42] لا يُستدعى في hot path — يُستخدم للتحقق الصريح فقط.
        """
        raw = object.__getattribute__(self, '_raw')
        if raw is None:
            return False
        try:
            row = raw.execute("PRAGMA database_list").fetchone()
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
        try:
            return self._get_raw().execute(sql, params)
        except sqlite3.OperationalError as e:
            err_msg = str(e).lower()
            if any(kw in err_msg for kw in ("closed", "unable to open", "disk i/o")):
                self._reconnect_after_error()
                return self._get_raw().execute(sql, params)
            raise

    def executemany(self, sql, seq):
        try:
            return self._get_raw().executemany(sql, seq)
        except sqlite3.OperationalError as e:
            err_msg = str(e).lower()
            if any(kw in err_msg for kw in ("closed", "unable to open", "disk i/o")):
                self._reconnect_after_error()
                return self._get_raw().executemany(sql, seq)
            raise

    def executescript(self, script):
        try:
            return self._get_raw().executescript(script)
        except sqlite3.OperationalError as e:
            err_msg = str(e).lower()
            if any(kw in err_msg for kw in ("closed", "unable to open", "disk i/o")):
                self._reconnect_after_error()
                return self._get_raw().executescript(script)
            raise

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
        self._company_id    : int | None = None
        self._company_name  : str        = ""
        self._company_color : str        = "#1565c0"
        self._connections   : dict       = {}
        self._state_lock                 = threading.Lock()

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

        لو الشركة جديدة → يمسح connections القديمة فوراً.
        لو نفس الشركة → يحدث الاسم واللون فقط بدون مسح connections.
        يُبطل AppState cache بعد تغيير الشركة تلقائياً.
        """
        with self._state_lock:
            if self._company_id == company_id:
                self._company_name  = name
                self._company_color = color or "#1565c0"
                return

            self._close_raw_connections_unsafe()
            self._connections.clear()

            self._company_id    = company_id
            self._company_name  = name
            self._company_color = color or "#1565c0"

        # خارج الـ lock — لتجنب deadlock مع PyQt signals
        try:
            from ui.app_state import AppState
            AppState.invalidate()
        except (ImportError, Exception):
            pass

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
        """
        [تحسين 42] يستخدم path_matches() بدل validate() في hot path.

        path_matches() = مقارنة string بسيطة: O(1)
        validate()     = PRAGMA database_list + I/O: O(PRAGMA)

        الفرق مهم عند استدعاء _get_conn في كل widget access.
        """
        if not self._company_id:
            raise RuntimeError("لم يتم تحديد شركة نشطة بعد")

        with self._state_lock:
            conn = self._connections.get(db_name)
            expected_path = get_company_db_path(self._company_id, db_name)

            if conn is not None:
                # [تحسين 42] path_matches() بدل validate() — بدون PRAGMA
                if conn.path_matches(expected_path):
                    return conn
                else:
                    # connection قديم لشركة مختلفة — أغلقه وأنشئ جديد
                    try:
                        conn.real_close()
                    except Exception:
                        pass
                    del self._connections[db_name]

            if not os.path.exists(expected_path):
                raise FileNotFoundError(
                    f"ملف قاعدة البيانات غير موجود: {expected_path}\n"
                    f"تأكد من تهيئة الشركة أولاً."
                )

            conn = ProtectedConnection(expected_path)
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