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
       + ProductService.cleanup_empty_products_after_orphan_fix() + ItemService.get()
"""

from PyQt5.QtWidgets import QMessageBox

from services.costing.product_service import ProductService
from services.shared.item_service     import ItemService
from ui.widgets.core.events           import emit_company_data_changed
from ui.widgets.core.i18n             import tr


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

        auto_deleted = prod_svc.cleanup_empty_products_after_orphan_fix([pid])

        warning_bar.setVisible(False)
        bom_tree.load(conn, pid)
        emit_company_data_changed()

        names_block = "\n".join(f"  • {nm}" for nm in orphan_names)

        if auto_deleted:
            form.reset()
            bom_tree.clear_tree()
            QMessageBox.information(
                self._parent,
                tr("orphans_deleted_with_product_title"),
                tr("orphans_deleted_product_removed_msg").format(
                    count=n, names=names_block, product_name=prod_name
                )
            )
        else:
            QMessageBox.information(
                self._parent,
                tr("orphans_deleted_title"),
                tr("orphans_deleted_msg").format(count=n, names=names_block)
            )