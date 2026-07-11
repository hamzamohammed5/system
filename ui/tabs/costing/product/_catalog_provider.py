"""
ui/tabs/costing/product/_catalog_provider.py
=============================================
_CatalogProvider — مزود الـ catalog للـ ComponentRow في لوحة المنتجات.

يبني الـ catalog المطلوب لاختيار المكونات في الـ BOM:
  raw       → خامات
  semi      → نصف مصنع
  labor_op  → عمليات عمالة
  machine_op→ عمليات تشغيل

[Refactor] استخدام CatalogService من services layer كمصدر وحيد للكتالوج.

[Fix هيكلي] لا يوجد أي fallback يستدعي db.shared.items_repo أو
  db.costing.operations_repo مباشرة من tabs/ — CatalogService.build()
  هو المصدر الوحيد ويغطي كل الحالات (raw/semi/final/labor_op/machine_op)
  بشكل سليم هيكلياً عبر repos.

[Fix هيكلي 2] لا يوجد try/except Exception: pass حول CatalogService.build().
  أي خطأ فيها (bug، جدول ناقص، إلخ) يظهر كما هو — كما ينبغي لخطأ برمجي،
  بدل أن يُبلع بصمت.

[i18n] CatalogService يرجع SHARED_CATEGORY_KEY ("shared") كمفتاح رمزي
  فقط في مكان category_name للعناصر المشتركة (الـ service لا يعرف شيئاً
  عن نظام الترجمة). هذه الدالة — بصفتها طبقة ui — هي المسؤولة عن
  استبدال المفتاح بالنص المترجم عبر tr("shared") قبل تسليم الكتالوج
  لـ ComponentRow.
"""

from services.costing.catalog_service import CatalogService, SHARED_CATEGORY_KEY
from ui.widgets.core.i18n import tr

# فهرس category_name داخل كل tuple لكل نوع في الكتالوج (index ثابت = 2 للجميع)
_CATEGORY_NAME_INDEX = 2


def build_product_catalog(conn) -> dict:
    """
    يبني الـ catalog الكامل للـ ComponentRow عبر CatalogService،
    ثم يترجم مفتاح الفئة المشتركة (SHARED_CATEGORY_KEY) إلى نص معروض.

    يرجع:
        {
          "raw":        [(id, name, category_name, price, total_qty), ...],
          "semi":       [(id, name, category_name, price, None), ...],
          "final":      [(id, name, category_name, price, None), ...],
          "labor_op":   [(id, name, category_name, minutes), ...],
          "machine_op": [(id, name, category_name, mode, machine_name), ...],
        }
    """
    catalog = CatalogService(conn).build()
    return {
        item_type: [_translate_shared_row(row) for row in rows]
        for item_type, rows in catalog.items()
    }


def _translate_shared_row(row: tuple) -> tuple:
    """يستبدل SHARED_CATEGORY_KEY في category_name بالنص المترجم عبر tr()."""
    if row[_CATEGORY_NAME_INDEX] == SHARED_CATEGORY_KEY:
        return row[:_CATEGORY_NAME_INDEX] + (tr("shared"),) + row[_CATEGORY_NAME_INDEX + 1:]
    return row