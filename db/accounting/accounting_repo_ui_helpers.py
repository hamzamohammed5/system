"""
db/accounting/accounting_repo_ui_helpers.py
============================================
دوال مساعدة تُستخدم من الـ UI — كانت مكتوبة كـ SQL مباشر داخل الـ widgets.
نُقلت هنا لفصل قاعدة البيانات عن طبقة الواجهة.

الدوال:
  fetch_account_by_code(conn, code)         → row | None
  fetch_capital_line_for_entry(conn, entry_id) → line_id | 0
  fetch_drawings_line_for_entry(conn, entry_id) → line_id | 0
  fetch_entry_by_ref(conn, ref_no)          → row | None
  fetch_investor_entry_id(erp_conn, link_id) → entry_id | None
"""


def fetch_account_by_code(conn, code: str):
    """يجلب حساباً بالكود — يُستخدم عند تحديد الأب تلقائياً."""
    try:
        return conn.execute(
            "SELECT id FROM accounts WHERE code=?", (code,)
        ).fetchone()
    except Exception:
        return None


def fetch_capital_line_for_entry(conn, entry_id: int) -> int:
    """يرجع id أول سطر دائن (CR) في قيد رأس المال، أو 0."""
    try:
        row = conn.execute(
            "SELECT id FROM journal_lines WHERE entry_id=? AND credit>0 LIMIT 1",
            (entry_id,)
        ).fetchone()
        return row["id"] if row else 0
    except Exception:
        return 0


def fetch_drawings_line_for_entry(conn, entry_id: int) -> int:
    """يرجع id أول سطر مدين (DR) في قيد المسحوبات، أو 0."""
    try:
        row = conn.execute(
            "SELECT id FROM journal_lines WHERE entry_id=? AND debit>0 LIMIT 1",
            (entry_id,)
        ).fetchone()
        return row["id"] if row else 0
    except Exception:
        return 0


def fetch_entry_by_ref(conn, ref_no: str):
    """يجلب قيداً برقمه المرجعي."""
    try:
        return conn.execute(
            "SELECT id FROM journal_entries WHERE ref_no=?", (ref_no,)
        ).fetchone()
    except Exception:
        return None


def fetch_investor_entry_id(erp_conn, link_id: int):
    """
    يجلب entry_id المرتبط بـ link_id من investor_entries.
    يُستخدم قبل حذف القيد عند حذف حركة مستثمر.
    """
    try:
        row = erp_conn.execute(
            "SELECT entry_id FROM investor_entries WHERE id=?", (link_id,)
        ).fetchone()
        return row["entry_id"] if row else None
    except Exception:
        return None