"""
ui/tabs/costing/product/_orphan_handler.py
==========================================
_OrphanHandler — منطق معالجة المكونات الناقصة (Orphans) في BOM.

مسؤوليته:
  - فحص المكونات الناقصة لمنتج معين
  - حذفها مع إشعار المستخدم
  - التنظيف التلقائي للمنتجات الفارغة

يُستخدم من _ProductMainPanel.

[Fix #5] استبدال bus.data_changed.emit() بـ emit_company_data_changed()
[Fix #10] استبدال db imports المباشرة بـ ProductService + ItemService:
  من: db.shared.items_repo → fetch_item, fetch_orphan_bom_rows,
      delete_orphan_bom_rows, cleanup_empty_products_after_orphan_fix
  إلى: ProductService.get_orphan_components() + ProductService.fix_orphans()
       + ItemService.get()
  ملاحظة: cleanup_empty_products_after_orphan_fix غير موجود في ProductService API
  يُبقى استدعاؤه المباشر مؤقتاً حتى إضافته للـ service.
"""

from PyQt5.QtWidgets import QMessageBox

from services.costing.product_service import ProductService
from services.shared.item_service     import ItemService
from ui.widgets.core.events           import emit_company_data_changed

# TODO: نقل cleanup_empty_products_after_orphan_fix إلى ProductService
from db.shared.items_repo import cleanup_empty_products_after_orphan_fix


class _OrphanHandler:
    """
    مساعد يتولى منطق الـ orphans — يُمرر له الـ parent widget للـ dialogs.

    الاستخدام:
        self._orphan = _OrphanHandler(parent=self)
        orphans = self._orphan.fetch(conn, pid)
        self._orphan.fix(conn, pid, warning_bar, bom_tree, form)
    """

    def __init__(self, parent):
        self._parent = parent

    # ── API عام ─────────────────────────────────────────

    @staticmethod
    def fetch(conn, pid: int) -> list:
        """يرجع قائمة المكونات الناقصة للمنتج."""
        return ProductService(conn).get_orphan_components(pid)

    def fix(self, conn, pid: int,
            warning_bar, bom_tree, form) -> None:
        """
        يحذف كل المكونات الناقصة للمنتج ويعالج النتائج.

        المعاملات:
            conn        : اتصال قاعدة البيانات
            pid         : ID المنتج
            warning_bar : BaseWarningBar لإخفائه بعد الإصلاح
            bom_tree    : BomTree لإعادة تحميله
            form        : _FormPanel لإعادة ضبطه لو المنتج اتحذف
        """
        prod_svc = ProductService(conn)

        # نجلب الأسماء قبل الحذف عشان نعرضها في الرسالة
        orphans      = prod_svc.get_orphan_components(pid)
        orphan_names = [
            getattr(o, "name", None) or f"ID:{getattr(o, 'child_id', '?')}"
            for o in orphans
        ]

        item      = ItemService(conn).get(pid)
        prod_name = item.name if item else f"ID {pid}"

        # الحذف عبر ProductService
        n = prod_svc.fix_orphans(pid)

        # TODO: نقل هذا المنطق لـ ProductService.fix_orphans()
        auto_deleted = cleanup_empty_products_after_orphan_fix(conn, [pid])

        warning_bar.setVisible(False)
        bom_tree.load(conn, pid)
        emit_company_data_changed()

        if auto_deleted:
            form.reset()
            bom_tree.clear_tree()
            QMessageBox.information(
                self._parent,
                "تم — وتم حذف المنتج",
                f"✅ تم حذف {n} مكوّن ناقص:\n"
                + "\n".join(f"  • {nm}" for nm in orphan_names)
                + f"\n\nبما أن «{prod_name}» لم يعد يحتوي على أي مكونات،\n"
                  "تم حذفه تلقائياً."
            )
        else:
            QMessageBox.information(
                self._parent,
                "تم",
                f"✅ تم حذف {n} مكوّن ناقص:\n"
                + "\n".join(f"  • {nm}" for nm in orphan_names)
            )