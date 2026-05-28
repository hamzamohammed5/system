"""
db/accounting/accounting_audit_repo.py
=======================================
نظام تدقيق العمليات الحساسة (Audit Log) — مقترح 52.

يُسجّل كل عملية حذف أو تعديل أو إنشاء على الجداول الحساسة:
  - journal_entries  : حذف / تعديل القيود المحاسبية
  - journal_lines    : حذف سطور القيود
  - accounts         : حذف / تعديل الحسابات
  - inventory_moves  : حذف حركات المخزون (عبر inv_conn)
  - investor_entries : حذف ربط المستثمرين

الفلسفة:
  - الـ audit_log يُكتب دائماً قبل تنفيذ العملية الفعلية (pre-action snapshot).
  - الفشل في كتابة الـ log لا يوقف العملية الأصلية — يُسجَّل كـ warning فقط.
  - old_data مخزّن كـ JSON لقراءة سهلة ومرونة في الـ schema.
  - changed_by يُمرَّر من الـ UI أو يبقى 'system' كافتراضي.
"""

import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════
# DDL
# ══════════════════════════════════════════════════════════

AUDIT_LOG_DDL = """
    CREATE TABLE IF NOT EXISTS audit_log (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        action      TEXT    NOT NULL CHECK(action IN ('delete', 'update', 'create')),
        table_name  TEXT    NOT NULL,
        record_id   INTEGER,
        old_data    TEXT,
        changed_by  TEXT    NOT NULL DEFAULT 'system',
        created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
    );
"""


def create_audit_log_table(conn):
    """يُنشئ جدول audit_log لو لم يكن موجوداً."""
    try:
        conn.executescript(AUDIT_LOG_DDL)
        conn.commit()
    except Exception as e:
        logger.warning("[audit_log] فشل إنشاء الجدول: %s", e)


# ══════════════════════════════════════════════════════════
# كتابة السجلات
# ══════════════════════════════════════════════════════════

def log_action(conn,
               action: str,
               table_name: str,
               record_id: int = None,
               old_data: dict | list | str = None,
               changed_by: str = "system") -> int | None:
    """
    يُسجّل عملية في audit_log.

    Parameters:
        conn        : connection على نفس الـ DB التي تحتوي audit_log
        action      : 'delete' | 'update' | 'create'
        table_name  : اسم الجدول المتأثر
        record_id   : ID السجل
        old_data    : snapshot للبيانات القديمة (dict أو list أو str)
        changed_by  : المستخدم أو الوحدة المنفذة

    Returns:
        id السجل الجديد في audit_log، أو None لو فشل الـ insert.

    ملاحظة:
        الفشل لا يُوقف العملية الأصلية — فقط يُسجَّل كـ warning.
    """
    if action not in ("delete", "update", "create"):
        logger.warning("[audit_log] action غير صالح: %s", action)
        return None

    # تحويل old_data إلى JSON string
    if old_data is None:
        old_json = None
    elif isinstance(old_data, str):
        old_json = old_data
    else:
        try:
            old_json = json.dumps(old_data, ensure_ascii=False, default=str)
        except Exception as e:
            old_json = f"[serialize error: {e}]"

    try:
        cur = conn.execute("""
            INSERT INTO audit_log (action, table_name, record_id, old_data, changed_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (action, table_name, record_id, old_json,
              changed_by, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return cur.lastrowid
    except Exception as e:
        logger.warning(
            "[audit_log] فشل تسجيل العملية — action=%s table=%s record_id=%s: %s",
            action, table_name, record_id, e
        )
        return None


def log_delete(conn, table_name: str, record_id: int,
               old_data: dict | list = None,
               changed_by: str = "system") -> int | None:
    """اختصار لتسجيل عملية حذف."""
    return log_action(conn, "delete", table_name, record_id, old_data, changed_by)


def log_update(conn, table_name: str, record_id: int,
               old_data: dict | list = None,
               changed_by: str = "system") -> int | None:
    """اختصار لتسجيل عملية تعديل."""
    return log_action(conn, "update", table_name, record_id, old_data, changed_by)


def log_create(conn, table_name: str, record_id: int,
               data: dict | list = None,
               changed_by: str = "system") -> int | None:
    """اختصار لتسجيل عملية إنشاء."""
    return log_action(conn, "create", table_name, record_id, data, changed_by)


# ══════════════════════════════════════════════════════════
# دوال مساعدة لأخذ snapshot قبل الحذف
# ══════════════════════════════════════════════════════════

def snapshot_journal_entry(conn, entry_id: int) -> dict | None:
    """
    يأخذ snapshot كامل للقيد وسطوره قبل الحذف.
    يُستخدم في delete_entry لتمرير البيانات لـ log_delete.
    """
    try:
        entry = conn.execute(
            "SELECT * FROM journal_entries WHERE id=?", (entry_id,)
        ).fetchone()
        if not entry:
            return None

        lines = conn.execute("""
            SELECT jl.*, a.code AS account_code, a.name AS account_name
            FROM journal_lines jl
            JOIN accounts a ON a.id = jl.account_id
            WHERE jl.entry_id = ?
            ORDER BY jl.id
        """, (entry_id,)).fetchall()

        return {
            "entry": dict(entry),
            "lines": [dict(l) for l in lines],
        }
    except Exception as e:
        logger.warning("[audit_log] snapshot_journal_entry فشل: %s", e)
        return None


def snapshot_account(conn, account_id: int) -> dict | None:
    """يأخذ snapshot للحساب قبل الحذف أو التعديل."""
    try:
        row = conn.execute(
            "SELECT * FROM accounts WHERE id=?", (account_id,)
        ).fetchone()
        return dict(row) if row else None
    except Exception:
        return None


def snapshot_row(conn, table: str, record_id: int,
                 id_col: str = "id") -> dict | None:
    """
    snapshot عام لأي جدول وأي سجل.
    يُستخدم للجداول البسيطة التي ما فيهاش علاقات.
    """
    try:
        row = conn.execute(
            f"SELECT * FROM {table} WHERE {id_col}=?", (record_id,)
        ).fetchone()
        return dict(row) if row else None
    except Exception:
        return None


# ══════════════════════════════════════════════════════════
# قراءة السجل
# ══════════════════════════════════════════════════════════

def fetch_audit_log(conn,
                    table_name: str = None,
                    action: str = None,
                    limit: int = 200,
                    offset: int = 0) -> list:
    """
    يجلب سجلات الـ audit_log مع دعم فلترة وـ pagination.

    Parameters:
        table_name : فلتر على اسم الجدول (اختياري)
        action     : فلتر على نوع العملية (اختياري)
        limit      : عدد النتائج
        offset     : بداية الصفحة
    """
    conditions, params = [], []

    if table_name:
        conditions.append("table_name = ?")
        params.append(table_name)
    if action:
        conditions.append("action = ?")
        params.append(action)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    try:
        rows = conn.execute(f"""
            SELECT id, action, table_name, record_id,
                   old_data, changed_by, created_at
            FROM audit_log
            {where}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """, params + [limit, offset]).fetchall()

        result = []
        for r in rows:
            d = dict(r)
            # parse old_data من JSON إلى dict لو أمكن
            if d.get("old_data"):
                try:
                    d["old_data_parsed"] = json.loads(d["old_data"])
                except Exception:
                    d["old_data_parsed"] = None
            result.append(d)
        return result
    except Exception as e:
        logger.warning("[audit_log] fetch_audit_log error: %s", e)
        return []


def fetch_audit_log_count(conn,
                          table_name: str = None,
                          action: str = None) -> int:
    """يرجع إجمالي عدد سجلات الـ audit_log (للـ pagination)."""
    conditions, params = [], []
    if table_name:
        conditions.append("table_name = ?")
        params.append(table_name)
    if action:
        conditions.append("action = ?")
        params.append(action)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    try:
        row = conn.execute(
            f"SELECT COUNT(*) AS c FROM audit_log {where}", params
        ).fetchone()
        return row["c"] if row else 0
    except Exception:
        return 0


def fetch_record_history(conn, table_name: str, record_id: int) -> list:
    """
    يجلب كل سجلات الـ audit_log لسجل معين.
    مفيد لعرض تاريخ التعديلات على قيد أو حساب بعينه.
    """
    try:
        rows = conn.execute("""
            SELECT id, action, old_data, changed_by, created_at
            FROM audit_log
            WHERE table_name=? AND record_id=?
            ORDER BY id DESC
        """, (table_name, record_id)).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []