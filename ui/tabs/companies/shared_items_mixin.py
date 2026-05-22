"""
ui/tabs/companies/shared_items_mixin.py
=========================================
دوال مساعدة لجلب العناصر المشتركة للشركة النشطة.

تُستخدم من:
  - raw_table_panel.py      → get_shared_raws()
  - machine_table.py        → get_shared_machines()
  - labor_op_table.py       → get_shared_labor_ops()
  - component_row.py / catalog_builder.py (عبر SharedItemsBridge)

المبدأ:
  - العناصر المشتركة مخزنة في companies.db فقط
  - الشركة تقرأ منها مباشرة — لا نسخ محلية
  - أي تعديل يتعكس فوراً على كل الشركات
  - ID = "shared:{n}" (string) للتمييز عن المحلي
"""

import json


# ══════════════════════════════════════════════════════════
# مساعدات
# ══════════════════════════════════════════════════════════

def is_shared_id(item_id) -> bool:
    """هل هذا ID لعنصر مشترك؟"""
    return isinstance(item_id, str) and str(item_id).startswith("shared:")


def extract_shared_id(item_id) -> int | None:
    """يستخرج الـ shared_item_id الحقيقي من الـ composite id."""
    if is_shared_id(item_id):
        try:
            return int(str(item_id).split(":")[1])
        except Exception:
            return None
    return None


def _get_company_id() -> int | None:
    """يرجع ID الشركة النشطة."""
    try:
        from db.companies.company_state import company_state
        return company_state.company_id if company_state.is_ready else None
    except Exception:
        return None


def _fetch_shared(shared_type: str) -> list:
    """
    يجيب العناصر المشتركة للشركة النشطة من companies.db.
    يرجع list of dicts مع id = "shared:{n}".
    """
    try:
        company_id = _get_company_id()
        if company_id is None:
            return []

        from db.companies.companies_schema import get_central_connection
        central = get_central_connection()
        rows = central.execute("""
            SELECT s.id, s.name, s.shared_type, s.data, s.updated_at
            FROM company_shared_links lnk
            JOIN shared_items s ON s.id = lnk.shared_item_id
            WHERE lnk.company_id = ? AND s.shared_type = ?
            ORDER BY s.name
        """, (company_id, shared_type)).fetchall()
        central.close()

        result = []
        for row in rows:
            try:
                data = json.loads(row["data"]) if row["data"] else {}
            except Exception:
                data = {}
            item = {
                "id":             f"shared:{row['id']}",
                "shared_item_id": row["id"],
                "name":           row["name"],
                "shared_type":    row["shared_type"],
                "category_id":    None,
                "category_name":  "🔗 مشترك",
                "is_shared":      True,
                "updated_at":     row["updated_at"],
            }
            item.update(data)
            result.append(item)
        return result
    except Exception as e:
        print(f"[shared_items_mixin] _fetch_shared({shared_type}) error: {e}")
        return []


# ══════════════════════════════════════════════════════════
# دوال عامة للاستخدام من الجداول
# ══════════════════════════════════════════════════════════

def get_shared_raws() -> list:
    """
    يرجع الخامات المشتركة للشركة النشطة.
    كل عنصر: {id, name, price, total_qty, category_name, is_shared, ...}
    """
    items = _fetch_shared("raw")
    result = []
    for item in items:
        result.append({
            "id":            item["id"],
            "shared_item_id": item["shared_item_id"],
            "name":          item["name"],
            "price":         float(item.get("price", 0.0)),
            "total_qty":     item.get("total_qty"),
            "category_id":   None,
            "category_name": "🔗 مشترك",
            "is_shared":     True,
            "updated_at":    item.get("updated_at", ""),
        })
    return result


def get_shared_machines() -> list:
    """
    يرجع الماكينات المشتركة للشركة النشطة.
    كل عنصر: {id, name, rate_per_hour, rate_per_unit, category_name, is_shared, ...}
    """
    items = _fetch_shared("machine")
    result = []
    for item in items:
        result.append({
            "id":            item["id"],
            "shared_item_id": item["shared_item_id"],
            "name":          item["name"],
            "rate_per_hour": float(item.get("rate_per_hour", 0.0)),
            "rate_per_unit": float(item.get("rate_per_unit", 0.0)),
            "category_id":   None,
            "category_name": "🔗 مشترك",
            "is_shared":     True,
            "updated_at":    item.get("updated_at", ""),
        })
    return result


def get_shared_labor_ops() -> list:
    """
    يرجع عمليات العمالة المشتركة للشركة النشطة.
    كل عنصر: {id, name, minutes, category_name, is_shared, ...}
    """
    items = _fetch_shared("labor_op")
    result = []
    for item in items:
        result.append({
            "id":            item["id"],
            "shared_item_id": item["shared_item_id"],
            "name":          item["name"],
            "minutes":       float(item.get("minutes", 0.0)),
            "category_id":   None,
            "category_name": "🔗 مشترك",
            "is_shared":     True,
            "updated_at":    item.get("updated_at", ""),
        })
    return result


def get_shared_machine_ops() -> list:
    """
    يرجع عمليات التشغيل المشتركة للشركة النشطة.
    كل عنصر: {id, name, mode, value, machine_name, rate_per_hour, rate_per_unit, ...}
    """
    items = _fetch_shared("machine_op")
    result = []
    for item in items:
        result.append({
            "id":            item["id"],
            "shared_item_id": item["shared_item_id"],
            "name":          item["name"],
            "mode":          item.get("mode", "time"),
            "value":         float(item.get("value", 0.0)),
            "machine_name":  item.get("machine_name", ""),
            "rate_per_hour": float(item.get("rate_per_hour", 0.0)),
            "rate_per_unit": float(item.get("rate_per_unit", 0.0)),
            "category_id":   None,
            "category_name": "🔗 مشترك",
            "is_shared":     True,
            "updated_at":    item.get("updated_at", ""),
        })
    return result