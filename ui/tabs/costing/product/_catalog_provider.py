"""
ui/tabs/costing/product/_catalog_provider.py
=============================================
_CatalogProvider — مزود الـ catalog للـ ComponentRow في لوحة المنتجات.

يبني الـ catalog المطلوب لاختيار المكونات في الـ BOM:
  raw       → خامات
  semi      → نصف مصنع
  labor_op  → عمليات عمالة
  machine_op→ عمليات تشغيل

يستخدم catalog_builder.py إذا كان متاحاً، وإلا يبني مباشرة.
"""


def build_product_catalog(conn) -> dict:
    """
    يبني الـ catalog الكامل للـ ComponentRow.

    يحاول استخدام catalog_builder أولاً (يشمل العناصر المشتركة)،
    وإذا فشل يبني مباشرة من DB المحلية.

    يرجع:
        {
          "raw":        [(id, name, category_id, category_name), ...],
          "semi":       [(id, name, category_id, category_name), ...],
          "labor_op":   [(id, name, category_id, category_name), ...],
          "machine_op": [(id, name, category_id, category_name), ...],
        }
    """
    # محاولة استخدام catalog_builder (يشمل العناصر المشتركة)
    try:
        from ui.tabs.costing.shared.catalog_builder import build_catalog
        return build_catalog(conn)
    except Exception:
        pass

    # fallback — بناء مباشر من DB المحلية
    return _build_local_catalog(conn)


def _build_local_catalog(conn) -> dict:
    """يبني catalog من DB المحلية فقط (بدون عناصر مشتركة)."""
    from db.shared.items_repo       import fetch_items_by_type
    from db.costing.operations_repo import fetch_all_labor_ops, fetch_all_machine_ops

    result: dict[str, list] = {
        "raw": [], "semi": [], "labor_op": [], "machine_op": []
    }

    for row in fetch_items_by_type(conn, "raw"):
        result["raw"].append((
            row["id"], row["name"],
            row["category_id"], row.get("category_name") or None,
        ))

    for row in fetch_items_by_type(conn, "semi"):
        result["semi"].append((
            row["id"], row["name"],
            row["category_id"], row.get("category_name") or None,
        ))

    for op in fetch_all_labor_ops(conn):
        result["labor_op"].append((
            op["id"], op["name"],
            op["category_id"], op.get("category_name") or None,
        ))

    for op in fetch_all_machine_ops(conn):
        result["machine_op"].append((
            op["id"], op["name"],
            op["category_id"], op.get("category_name") or None,
        ))

    return result