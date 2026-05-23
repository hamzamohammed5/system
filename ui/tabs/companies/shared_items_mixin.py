"""
ui/tabs/companies/shared_items_mixin.py
=========================================
إصلاحات:
1. category_name يُجلب من data["category_name"] لو موجود — يظهر التصنيف الحقيقي
2. العنصر لا يظهر مرتين في الشركة الأصلية:
   - get_shared_* تقبل local_rows اختياري وتستخدم remove_local_duplicates
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


def remove_local_duplicates(local_rows: list, shared_rows: list) -> list:
    """
    يزيل من shared_rows أي عنصر اسمه موجود بالفعل في local_rows.
    يحل مشكلة ظهور العنصر مرتين في الشركة الأصلية اللي نشرته.
    المقارنة بالاسم (case-insensitive, strip).
    """
    local_names = {str(r.get("name", "")).strip().lower() for r in local_rows}
    return [
        s for s in shared_rows
        if str(s.get("name", "")).strip().lower() not in local_names
    ]


def _fetch_shared(shared_type: str) -> list:
    """
    يجيب العناصر المشتركة للشركة النشطة من companies.db.
    يرجع list of dicts مع id = "shared:{n}".
    category_name يُجلب من data["category_name"] لو محفوظ.
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

            # category_name: من data لو محفوظ، وإلا None (الجدول يعرض "—")
            cat_name = data.get("category_name") or None

            item = {
                "id":             f"shared:{row['id']}",
                "shared_item_id": row["id"],
                "name":           row["name"],
                "shared_type":    row["shared_type"],
                "category_id":    None,
                "category_name":  cat_name,
                "is_shared":      True,
                "updated_at":     row["updated_at"],
            }
            item.update(data)
            # نعيد بعد update عشان data مش تطغى على category_name
            item["category_name"] = cat_name
            result.append(item)
        return result
    except Exception as e:
        print(f"[shared_items_mixin] _fetch_shared({shared_type}) error: {e}")
        return []


# ══════════════════════════════════════════════════════════
# دوال عامة للاستخدام من الجداول
# ══════════════════════════════════════════════════════════

def get_shared_raws(local_rows: list = None) -> list:
    """
    يرجع الخامات المشتركة للشركة النشطة.
    local_rows: لو مُمرَّرة تُزال المكررات (نفس الاسم) — لمنع ظهور العنصر مرتين.
    """
    items = _fetch_shared("raw")
    result = []
    for item in items:
        result.append({
            "id":             item["id"],
            "shared_item_id": item["shared_item_id"],
            "name":           item["name"],
            "price":          float(item.get("price", 0.0)),
            "total_qty":      item.get("total_qty"),
            "category_id":    None,
            "category_name":  item["category_name"],
            "is_shared":      True,
            "updated_at":     item.get("updated_at", ""),
        })
    if local_rows is not None:
        result = remove_local_duplicates(local_rows, result)
    return result


def get_shared_machines(local_rows: list = None) -> list:
    """
    يرجع الماكينات المشتركة للشركة النشطة.
    local_rows: لو مُمرَّرة تُزال المكررات.
    """
    items = _fetch_shared("machine")
    result = []
    for item in items:
        result.append({
            "id":             item["id"],
            "shared_item_id": item["shared_item_id"],
            "name":           item["name"],
            "rate_per_hour":  float(item.get("rate_per_hour", 0.0)),
            "rate_per_unit":  float(item.get("rate_per_unit", 0.0)),
            "category_id":    None,
            "category_name":  item["category_name"],
            "is_shared":      True,
            "updated_at":     item.get("updated_at", ""),
        })
    if local_rows is not None:
        result = remove_local_duplicates(local_rows, result)
    return result


def get_shared_labor_ops(local_rows: list = None) -> list:
    """
    يرجع عمليات العمالة المشتركة للشركة النشطة.
    local_rows: لو مُمرَّرة تُزال المكررات.
    """
    items = _fetch_shared("labor_op")
    result = []
    for item in items:
        result.append({
            "id":             item["id"],
            "shared_item_id": item["shared_item_id"],
            "name":           item["name"],
            "minutes":        float(item.get("minutes", 0.0)),
            "category_id":    None,
            "category_name":  item["category_name"],
            "is_shared":      True,
            "updated_at":     item.get("updated_at", ""),
        })
    if local_rows is not None:
        result = remove_local_duplicates(local_rows, result)
    return result


def get_shared_machine_ops(local_rows: list = None) -> list:
    """
    يرجع عمليات التشغيل المشتركة للشركة النشطة.
    local_rows: لو مُمرَّرة تُزال المكررات.
    """
    items = _fetch_shared("machine_op")
    result = []
    for item in items:
        result.append({
            "id":             item["id"],
            "shared_item_id": item["shared_item_id"],
            "name":           item["name"],
            "mode":           item.get("mode", "time"),
            "value":          float(item.get("value", 0.0)),
            "machine_name":   item.get("machine_name", ""),
            "rate_per_hour":  float(item.get("rate_per_hour", 0.0)),
            "rate_per_unit":  float(item.get("rate_per_unit", 0.0)),
            "category_id":    None,
            "category_name":  item["category_name"],
            "is_shared":      True,
            "updated_at":     item.get("updated_at", ""),
        })
    if local_rows is not None:
        result = remove_local_duplicates(local_rows, result)
    return result