"""
ui/tabs/companies/shared_items_mixin.py
=========================================
إصلاحات:
1. category_name في الشركة المرتبطة: لو مش موجود في data، نجيبه من erp.db المحلي
2. العنصر الأصلي يظهر بعلامة 🔗 في الشركة اللي نشرته:
   - get_published_local_ids() ترجع IDs المحلية المنشورة كمشتركة
3. remove_local_duplicates تمنع ظهور العنصر مرتين

[إصلاح v2]:
  - get_published_local_names(): استخدام try/finally لضمان central.close()
    حتى لو execute() رمى exception — منع connection leak.
  - _fetch_shared(): نفس الإصلاح — try/finally حول central.execute().
"""


# ══════════════════════════════════════════════════════════
# مساعدات أساسية
# ══════════════════════════════════════════════════════════

def is_shared_id(item_id) -> bool:
    return isinstance(item_id, str) and str(item_id).startswith("shared:")


def extract_shared_id(item_id) -> int | None:
    if is_shared_id(item_id):
        try:
            return int(str(item_id).split(":")[1])
        except Exception:
            return None
    return None


def _get_company_id() -> int | None:
    try:
        from db.companies.company_state import company_state
        return company_state.company_id if company_state.is_ready else None
    except Exception:
        return None


def _get_erp_conn():
    """يرجع erp connection للشركة النشطة (shared — لا تُغلقه)."""
    try:
        from db.companies.company_state import company_state
        if company_state.is_ready:
            return company_state.get_erp_conn()
    except Exception:
        pass
    return None


def remove_local_duplicates(local_rows: list, shared_rows: list) -> list:
    """
    يزيل من shared_rows أي عنصر اسمه موجود بالفعل في local_rows.
    يمنع ظهور العنصر مرتين في الشركة الأصلية.
    """
    local_names = {str(r.get("name", "")).strip().lower() for r in local_rows}
    return [
        s for s in shared_rows
        if str(s.get("name", "")).strip().lower() not in local_names
    ]


def _resolve_category_name_from_local(item_name: str, shared_type: str) -> str | None:
    """
    يجيب category_name من erp.db المحلي عن طريق اسم العنصر.
    يُستخدم كـ fallback لو category_name مش محفوظ في data.
    """
    try:
        conn = _get_erp_conn()
        if not conn:
            return None

        if shared_type == "raw":
            row = conn.execute("""
                SELECT c.name as cat_name
                FROM items i
                LEFT JOIN categories c ON c.id = i.category_id
                WHERE i.name = ? AND i.type = 'raw'
                LIMIT 1
            """, (item_name,)).fetchone()
        elif shared_type == "machine":
            row = conn.execute("""
                SELECT c.name as cat_name
                FROM machines m
                LEFT JOIN categories c ON c.id = m.category_id
                WHERE m.name = ?
                LIMIT 1
            """, (item_name,)).fetchone()
        elif shared_type == "labor_op":
            row = conn.execute("""
                SELECT c.name as cat_name
                FROM labor_ops lo
                LEFT JOIN categories c ON c.id = lo.category_id
                WHERE lo.name = ?
                LIMIT 1
            """, (item_name,)).fetchone()
        elif shared_type == "machine_op":
            row = conn.execute("""
                SELECT c.name as cat_name
                FROM machine_ops mo
                LEFT JOIN categories c ON c.id = mo.category_id
                WHERE mo.name = ?
                LIMIT 1
            """, (item_name,)).fetchone()
        else:
            return None

        if row and row["cat_name"]:
            return row["cat_name"]
    except Exception:
        pass
    return None


# ══════════════════════════════════════════════════════════
# العناصر المحلية المنشورة كمشتركة
# ══════════════════════════════════════════════════════════

def get_published_local_names(shared_type: str) -> set:
    """
    يرجع set من أسماء العناصر المحلية اللي اتنشرت كمشتركة من الشركة الحالية.
    يُستخدم في الجداول عشان نعلم على العناصر الأصلية بـ 🔗.

    [إصلاح v2]: try/finally يضمن central.close() حتى عند الخطأ.
    """
    try:
        company_id = _get_company_id()
        if company_id is None:
            return set()

        from services.companies.company_service import CompanyService
        from services.companies.shared_items_service import SharedItemsService

        central = CompanyService.get_central_conn_and_init()
        try:
            svc = SharedItemsService(central)
            items = svc.list_for_company(company_id, shared_type)
        finally:
            central.close()

        return {item.name.strip().lower() for item in items}
    except Exception as e:
        print(f"[shared_items_mixin] get_published_local_names error: {e}")
        return set()


# ══════════════════════════════════════════════════════════
# جلب العناصر المشتركة من companies.db
# ══════════════════════════════════════════════════════════

def _fetch_shared(shared_type: str) -> list:
    """
    يجيب العناصر المشتركة للشركة النشطة من companies.db.
    category_name:
      1. من data["category_name"] لو موجود
      2. من erp.db المحلي عن طريق الاسم (fallback)
      3. None لو مش موجود (الجدول يعرض "—")

    [إصلاح v2]: try/finally يضمن central.close() حتى عند الخطأ.
    """
    try:
        company_id = _get_company_id()
        if company_id is None:
            return []

        from services.companies.company_service import CompanyService
        from services.companies.shared_items_service import SharedItemsService

        central = CompanyService.get_central_conn_and_init()
        try:
            svc   = SharedItemsService(central)
            items = svc.list_for_company(company_id, shared_type)
        finally:
            central.close()

        result = []
        for it in items:
            data = it.data or {}

            # category_name: من data أولاً، ثم من erp.db المحلي كـ fallback
            cat_name = data.get("category_name") or None
            if not cat_name:
                cat_name = _resolve_category_name_from_local(it.name, shared_type)

            item = {
                "id":             f"shared:{it.id}",
                "shared_item_id": it.id,
                "name":           it.name,
                "shared_type":    shared_type,
                "category_id":    None,
                "category_name":  cat_name,
                "is_shared":      True,
                "updated_at":     it.updated_at,
            }
            item.update(data)
            # نعيد تعيين بعد update عشان data مش تطغى
            item["category_name"] = cat_name
            item["is_shared"]     = True
            result.append(item)
        return result
    except Exception as e:
        print(f"[shared_items_mixin] _fetch_shared({shared_type}) error: {e}")
        return []


# ══════════════════════════════════════════════════════════
# دوال عامة للاستخدام من الجداول
# ══════════════════════════════════════════════════════════

def get_shared_raws(local_rows: list = None) -> list:
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