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
  من: ui.events.bus  → bus.data_changed.emit()
  إلى: ui.widgets.core.events → emit_company_data_changed()
  السبب: أكثر دقة وأفضل أداءً حسب files_reference/models&services.md
"""

from PyQt5.QtWidgets import QMessageBox

from db.shared.items_repo import (
    fetch_item,
    fetch_orphan_bom_rows,
    delete_orphan_bom_rows,
    cleanup_empty_products_after_orphan_fix,
)
# [Fix #5] استخدام emit_company_data_changed بدل bus.data_changed
from ui.widgets.core.events import emit_company_data_changed


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
        return fetch_orphan_bom_rows(conn, pid)

    def fix(self, conn, pid: int,
            warning_bar, bom_tree, form) -> None:
        """
        يحذف كل المكونات الناقصة للمنتج ويعالج النتائج.

        المعاملات:
            conn        : اتصال قاعدة البيانات
            pid         : ID المنتج
            warning_bar : _WarningBar لإخفائه بعد الإصلاح
            bom_tree    : BomTree لإعادة تحميله
            form        : _FormPanel لإعادة ضبطه لو المنتج اتحذف
        """
        orphans      = fetch_orphan_bom_rows(conn, pid)
        orphan_names = [
            o["child_name"] or f"ID:{o['child_id']}" for o in orphans
        ]
        item      = fetch_item(conn, pid)
        prod_name = item["name"] if item else f"ID {pid}"

        n            = delete_orphan_bom_rows(conn, pid)
        auto_deleted = cleanup_empty_products_after_orphan_fix(conn, [pid])

        warning_bar.setVisible(False)
        bom_tree.load(conn, pid)
        # [Fix #5] emit_company_data_changed بدل bus.data_changed.emit()
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