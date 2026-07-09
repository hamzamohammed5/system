"""
ui/tabs/costing/product/_catalog_provider.py
=============================================
_CatalogProvider — مزود الـ catalog للـ ComponentRow في لوحة المنتجات.

يبني الـ catalog المطلوب لاختيار المكونات في الـ BOM:
  raw       → خامات
  semi      → نصف مصنع
  labor_op  → عمليات عمالة
  machine_op→ عمليات تشغيل

[Refactor] استخدام CatalogService من services layer بدل catalog_builder مباشرة،
  مع fallback لـ catalog_builder فقط (يشمل العناصر المشتركة).

[Fix هيكلي] حذف fallback الثاني (_build_local_catalog) الذي كان يستدعي
  db.shared.items_repo و db.costing.operations_repo مباشرة من tabs/,
  متجاوزاً services/. CatalogService.build() يغطي نفس الحالات
  (raw/semi/final/labor_op/machine_op) بشكل سليم هيكلياً عبر repos.
"""


def build_product_catalog(conn) -> dict:
    """
    يبني الـ catalog الكامل للـ ComponentRow.

    يحاول استخدام CatalogService أولاً (الطبقة المناسبة),
    ثم catalog_builder كـ fallback (يشمل العناصر المشتركة).

    يرجع:
        {
          "raw":        [(id, name, category_name, price, total_qty), ...],
          "semi":       [(id, name, category_name, price, None), ...],
          "labor_op":   [(id, name, category_name, minutes), ...],
          "machine_op": [(id, name, category_name, mode, machine_name), ...],
        }
    """
    # [Refactor] محاولة استخدام CatalogService (services layer)
    try:
        from services.costing.catalog_service import CatalogService
        return CatalogService(conn).build()
    except Exception:
        pass

    # fallback — catalog_builder (يشمل العناصر المشتركة)
    from ui.tabs.costing.shared.catalog_builder import build_catalog
    return build_catalog(conn)