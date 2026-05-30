"""
ui/tabs/costing/product/product_main_panel.py
===============================================
_ProductMainPanel — اللوحة الرئيسية: فورم + جدول + BOM tree + تحذير.

[Fix #1] توحيد import LiveConnMixin من المسار الموثق في ui_widgets.md:
  من: ui.widgets.shared.connection_mixin
  إلى: ui.widgets.core.conn
[Fix #3] دمج المنطق المشترك في دالة _refresh_for_product بدل التكرار
[Fix #4] conn معامل إلزامي في _check_orphans — كل الاستدعاءات تمرره فعلاً
[Fix #6] توحيد import confirm_delete من المسار الموثق في ui_widgets.md
[Fix #7] استبدال hardcoded strings بـ tr()
[Fix #8] توحيد import BaseWarningBar من المسار الصحيح:
  من: ui.widgets.shared.base_warning_bar
  إلى: ui.widgets.components.notification
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter, QMessageBox,
)
from PyQt5.QtCore import Qt

from services.shared.item_service   import ItemService
from ui.widgets.dialogs.confirm     import confirm_delete
from ui.widgets.core.conn           import LiveConnMixin
from ui.widgets.core.i18n          import tr
from ui.widgets.components.notification import BaseWarningBar   # ✅ كان: ui.widgets.shared.base_warning_bar
from ui.tabs.costing.shared.bom_tree    import BomTree
from ui.app_settings import _C
from ui.events import bus

from .product_form  import _FormPanel
from .product_table import _ProductTable
from ._catalog_provider import build_product_catalog
from ._orphan_handler   import _OrphanHandler


def _splitter_style() -> str:
    """style موحد للـ QSplitter مربوط بـ _C."""
    return f"""
        QSplitter::handle {{
            background: {_C['border']};
            border-top: 1px solid {_C['border_med']};
        }}
        QSplitter::handle:hover {{ background: {_C['accent_mid']}; }}
        QSplitter::handle:pressed {{ background: {_C['accent']}; }}
    """


class _ProductMainPanel(QWidget, LiveConnMixin):
    def __init__(self, conn, product_type: str, parent=None):
        super().__init__(parent)
        self.conn         = conn
        self.product_type = product_type
        self._orphan      = _OrphanHandler(parent=self)
        self._build()
        bus.data_changed.connect(self._on_data_changed)

    def _get_catalog(self) -> dict:
        try:
            return build_product_catalog(self._live_conn())
        except Exception:
            return {"raw": [], "semi": [], "labor_op": [], "machine_op": []}

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(_splitter_style())

        self._form = _FormPanel(self.conn, self.product_type, self._get_catalog)
        bus.data_changed.connect(self._refresh_form_catalog)

        mid_widget = QWidget()
        mid_layout = QVBoxLayout(mid_widget)
        mid_layout.setContentsMargins(0, 0, 0, 0)
        mid_layout.setSpacing(0)

        self._warning = BaseWarningBar(
            on_fix=self._fix_orphans,
            on_edit=self._edit_selected,
            fix_text=f"🗑️ {tr('حذف الناقص')}",
            edit_text=f"✏️ {tr('تعديل')}",
        )
        mid_layout.addWidget(self._warning)

        self._prod_table = _ProductTable(
            self.conn,
            self.product_type,
            on_select=self._on_product_selected,
            on_edit=self._edit_selected,
            on_delete=self._delete_product,
        )
        mid_layout.addWidget(self._prod_table)

        self._bom_tree = BomTree()

        splitter.addWidget(self._form)
        splitter.addWidget(mid_widget)
        splitter.addWidget(self._bom_tree)
        splitter.setSizes([280, 220, 250])
        splitter.setCollapsible(0, True)
        splitter.setCollapsible(1, False)
        splitter.setCollapsible(2, True)

        root.addWidget(splitter)

    def _refresh_for_product(self, pid: int):
        """تحديث الـ warning bar والـ BOM tree لمنتج محدد."""
        try:
            conn = self._live_conn()
            self._check_orphans(pid, conn)
            self._bom_tree.load(conn, pid)
        except Exception:
            pass

    def _on_data_changed(self):
        pid = self._prod_table.selected_pid()
        if pid is not None:
            self._refresh_for_product(pid)

    def _on_product_selected(self, pid: int | None):
        if pid is None:
            self._bom_tree.clear_tree()
            self._warning.setVisible(False)
            return
        self._refresh_for_product(pid)

    def _refresh_form_catalog(self):
        try:
            new_catalog = self._get_catalog()
        except Exception:
            return
        self._form._rows.refresh_catalog(new_catalog)

    def _check_orphans(self, pid: int, conn):
        orphans = self._orphan.fetch(conn, pid)
        item    = ItemService(conn).get(pid)
        name    = item.name if item else f"ID {pid}"
        self._warning.show_orphans(orphans, name)

    def _fix_orphans(self):
        pid = self._prod_table.selected_pid()
        if pid is None:
            return
        try:
            conn = self._live_conn()
        except Exception as e:
            QMessageBox.warning(self, tr("خطأ"), str(e))
            return
        self._orphan.fix(
            conn, pid,
            warning_bar=self._warning,
            bom_tree=self._bom_tree,
            form=self._form,
        )

    def _edit_selected(self, pid: int | None = None):
        if pid is None:
            pid = self._prod_table.selected_pid()
        if pid is None:
            QMessageBox.information(self, tr("تنبيه"), tr("اختر منتجاً من الجدول أولاً"))
            return
        self._warning.setVisible(False)
        self._form.load_product(pid)

    def _delete_product(self, pid: int | None):
        if pid is None:
            QMessageBox.information(self, tr("تنبيه"), tr("اختر منتجاً أولاً"))
            return
        try:
            conn = self._live_conn()
        except Exception as e:
            QMessageBox.warning(self, tr("خطأ"), str(e))
            return

        svc  = ItemService(conn)
        item = svc.get(pid)
        if not item:
            return

        if confirm_delete(self, item.name):
            if self._form.is_editing and self._form._editing_id == pid:
                self._form.reset()
            # المنتج يُحذف بـ force_delete لأن حذفه يشمل BOM بطبيعته
            svc.force_delete(pid)
            self._warning.setVisible(False)
            self._bom_tree.clear_tree()
            bus.data_changed.emit()