"""
ui/tabs/companies/shared_items_mixin.py
========================================
مساعدات قراءة العناصر المشتركة من companies.db وتحويلها
لصفوف تشبه الصفوف المحلية — تُستخدم في:
  raw_table_panel.py  → get_shared_raws()
  machine_table.py    → get_shared_machines()
  labor_op_table.py   → get_shared_labor_ops()

منطق الـ ID:
  العناصر المشتركة بتاخد id خاص = SHARED_ID_OFFSET + shared_item_id
  عشان نفرقها عن العناصر المحلية في الجداول.

  is_shared_id(id)     → True لو id >= SHARED_ID_OFFSET
  extract_shared_id(id)→ shared_item_id الأصلي في companies.db

المزامنة:
  update_shared_item_data(shared_id, data) → يحدّث companies.db
  ويطلق bus.data_changed ليتحدث كل الجداول في كل الشركات.
"""

import json

SHARED_ID_OFFSET = 10_000_000  # أكبر من أي id محلي متوقع


# ══════════════════════════════════════════════════════════
# Connection للـ companies.db
# ══════════════════════════════════════════════════════════

def _get_central_conn():
    """
    يفتح أو يرجع connection لـ companies.db.
    يُنشئ الجداول لو مش موجودة.
    """
    from db.companies.companies_schema import (
        get_central_connection, create_central_tables
    )
    conn = get_central_connection()
    create_central_tables(conn)
    return conn


def _get_active_company_id() -> int | None:
    """يرجع id الشركة النشطة — None لو مفيش."""
    try:
        from db.companies.company_state import company_state
        return company_state.company_id if company_state.is_ready else None
    except Exception:
        return None


# ══════════════════════════════════════════════════════════
# is_shared_id / extract_shared_id
# ══════════════════════════════════════════════════════════

def is_shared_id(item_id) -> bool:
    """True لو الـ id ده خاص بعنصر مشترك."""
    try:
        return int(item_id) >= SHARED_ID_OFFSET
    except (TypeError, ValueError):
        return False


def extract_shared_id(item_id) -> int:
    """يرجع shared_item_id الأصلي في companies.db."""
    return int(item_id) - SHARED_ID_OFFSET


def make_shared_id(shared_item_id: int) -> int:
    """يحول shared_item_id → id مميز للجداول."""
    return SHARED_ID_OFFSET + shared_item_id


# ══════════════════════════════════════════════════════════
# قراءة العناصر المشتركة الخاصة بالشركة النشطة
# ══════════════════════════════════════════════════════════

def _fetch_shared_for_active(shared_type: str) -> list[dict]:
    """
    يجيب العناصر المشتركة من نوع معين للشركة النشطة.
    يرجع قائمة dicts جاهزة للعرض في الجداول.
    """
    company_id = _get_active_company_id()
    if company_id is None:
        return []

    try:
        conn = _get_central_conn()
        rows = conn.execute(
            """
            SELECT s.id, s.name, s.shared_type, s.data, s.updated_at
            FROM   company_shared_links lnk
            JOIN   shared_items s ON s.id = lnk.shared_item_id
            WHERE  lnk.company_id = ? AND s.shared_type = ?
            ORDER  BY s.name
            """,
            (company_id, shared_type)
        ).fetchall()
        conn.close()
        return rows
    except Exception:
        return []


def _decode(data_str: str) -> dict:
    try:
        return json.loads(data_str) if data_str else {}
    except Exception:
        return {}


# ══════════════════════════════════════════════════════════
# get_shared_raws / machines / labor_ops
# ══════════════════════════════════════════════════════════

def get_shared_raws() -> list[dict]:
    """
    يرجع الخامات المشتركة للشركة النشطة
    بنفس شكل صفوف fetch_items_by_type(conn, 'raw').
    """
    result = []
    for row in _fetch_shared_for_active("raw"):
        d = _decode(row["data"])
        result.append({
            "id":           make_shared_id(row["id"]),
            "name":         row["name"],
            "type":         "raw",
            "price":        d.get("price", 0.0),
            "total_qty":    d.get("total_qty"),
            "category_id":  None,
            "category_name": "🔗 مشترك",
            "is_shared":    True,
            "shared_id":    row["id"],
        })
    return result


def get_shared_machines() -> list[dict]:
    """
    يرجع الماكينات المشتركة للشركة النشطة
    بنفس شكل صفوف fetch_all_machines(conn).
    """
    result = []
    for row in _fetch_shared_for_active("machine"):
        d = _decode(row["data"])
        result.append({
            "id":            make_shared_id(row["id"]),
            "name":          row["name"],
            "rate_per_hour": d.get("rate_per_hour", 0.0),
            "rate_per_unit": d.get("rate_per_unit", 0.0),
            "category_id":   None,
            "category_name": "🔗 مشترك",
            "is_shared":     True,
            "shared_id":     row["id"],
        })
    return result


def get_shared_labor_ops() -> list[dict]:
    """
    يرجع عمليات العمالة المشتركة للشركة النشطة
    بنفس شكل صفوف fetch_all_labor_ops(conn).
    """
    result = []
    for row in _fetch_shared_for_active("labor_op"):
        d = _decode(row["data"])
        result.append({
            "id":           make_shared_id(row["id"]),
            "name":         row["name"],
            "minutes":      d.get("minutes", 0.0),
            "category_id":  None,
            "category_name": "🔗 مشترك",
            "is_shared":    True,
            "shared_id":    row["id"],
        })
    return result


def get_shared_machine_ops() -> list[dict]:
    """يرجع عمليات التشغيل المشتركة للشركة النشطة."""
    result = []
    for row in _fetch_shared_for_active("machine_op"):
        d = _decode(row["data"])
        result.append({
            "id":           make_shared_id(row["id"]),
            "name":         row["name"],
            "mode":         d.get("mode", "time"),
            "value":        d.get("value", 0.0),
            "machine_name": d.get("machine_name", ""),
            "rate_per_hour": d.get("rate_per_hour", 0.0),
            "rate_per_unit": d.get("rate_per_unit", 0.0),
            "category_id":  None,
            "category_name": "🔗 مشترك",
            "is_shared":    True,
            "shared_id":    row["id"],
        })
    return result


# ══════════════════════════════════════════════════════════
# تحديث بيانات عنصر مشترك (المزامنة)
# ══════════════════════════════════════════════════════════

def update_shared_item_data(shared_id: int, name: str, data: dict):
    """
    يحدّث بيانات عنصر مشترك في companies.db.
    بعدها يطلق bus.data_changed عشان كل الجداول تتحدث.
    """
    try:
        conn = _get_central_conn()
        conn.execute(
            "UPDATE shared_items SET name=?, data=?, updated_at=datetime('now') WHERE id=?",
            (name, json.dumps(data, ensure_ascii=False), shared_id)
        )
        conn.close()
        from ui.events import bus
        bus.data_changed.emit()
    except Exception as e:
        print(f"[shared_items_mixin] update error: {e}")


def get_shared_item_raw_data(shared_id: int) -> tuple[str, dict] | tuple[None, None]:
    """
    يرجع (name, data_dict) لعنصر مشترك.
    يُستخدم عند فتح نافذة التعديل.
    """
    try:
        conn = _get_central_conn()
        row  = conn.execute(
            "SELECT name, shared_type, data FROM shared_items WHERE id=?",
            (shared_id,)
        ).fetchone()
        conn.close()
        if not row:
            return None, None
        return row["name"], _decode(row["data"])
    except Exception:
        return None, None