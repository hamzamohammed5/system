"""
ui/tabs/costing/product/product_main_panel.py
===============================================
_ProductMainPanel — اللوحة الرئيسية: فورم + جدول + BOM tree + تحذير.

[Fix #1] توحيد import LiveConnMixin من المسار الموثق:
  إلى: ui.widgets.core.conn
[Fix #3] دمج المنطق المشترك في دالة _refresh_for_product بدل التكرار
[Fix #4] conn معامل إلزامي في _check_orphans
[Fix #6] توحيد import confirm_delete من المسار الموثق
[Fix #7] استبدال hardcoded strings بـ tr()
[Fix #8] توحيد import BaseWarningBar:
  إلى: ui.widgets.components.notification
[Fix A6] from ui.widgets.core.events import bus (بدل ui.events)
[Fix C2] استبدال tr() بنصوص عربية مباشرة بمفاتيح i18n صحيحة
[Fix D1] bus.data_changed → bus.company_data_changed مع named slots
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter, QMessageBox,
)
from PyQt5.QtCore import Qt

from services.shared.item_service       import ItemService
from ui.widgets.dialogs.confirm         import confirm_delete
from ui.widgets.core.conn               import LiveConnMixin
from ui.widgets.core.widget_mixin       import WidgetMixin
from ui.widgets.core.i18n              import tr
from ui.widgets.components.notification import BaseWarningBar
from ui.tabs.costing.shared.bom_tree    import BomTree
from ui.widgets.core.events             import bus, emit_company_data_changed

from .product_form  import _FormPanel
from .product_table import _ProductTable
from ._catalog_provider import build_product_catalog
from ._orphan_handler   import _OrphanHandler

from ui.constants import (
    PRODUCT_MAIN_SPLITTER_HANDLE_W,
    PRODUCT_MAIN_SPLITTER_SIZES,
)


class _ProductMainPanel(QWidget, LiveConnMixin, WidgetMixin):
    def __init__(self, conn, product_type: str, parent=None):
        super().__init__(parent)
        self._init_widget_mixin(lang=False, data=False)
        self.conn         = conn
        self.product_type = product_type
        self._orphan      = _OrphanHandler(parent=self)
        self._build()
        self._refresh_style()
        # [Fix D1] named slots بدل lambda لتجنب memory leaks
        bus.company_data_changed.connect(self._on_company_data_changed)

    def _on_company_data_changed(self, _company_id: int = None):
        """يُستدعى عند تغيير بيانات الشركة."""
        self._on_data_changed()

    def _get_catalog(self) -> dict:
        try:
            return build_product_catalog(self._live_conn())
        except Exception:
            return {"raw": [], "semi": [], "labor_op": [], "machine_op": []}

    def _refresh_style(self, *_):
        """يُطبق stylesheet الـ splitter عند تغيير الثيم."""
        from ui.theme import _C
        if hasattr(self, '_splitter'):
            self._splitter.setStyleSheet(f"""
                QSplitter::handle {{
                    background: {_C['border']};
                    border-top: 1px solid {_C['border_med']};
                }}
                QSplitter::handle:hover {{ background: {_C['accent_mid']}; }}
                QSplitter::handle:pressed {{ background: {_C['accent']}; }}
            """)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(PRODUCT_MAIN_SPLITTER_HANDLE_W)
        self._splitter = splitter

        self._form = _FormPanel(self.conn, self.product_type, self._get_catalog)
        # [Fix D1] named slot لتحديث الـ catalog
        bus.company_data_changed.connect(self._on_company_data_changed_catalog)

        mid_widget = QWidget()
        mid_layout = QVBoxLayout(mid_widget)
        mid_layout.setContentsMargins(0, 0, 0, 0)
        mid_layout.setSpacing(0)

        self._warning = BaseWarningBar(
            on_fix=self._fix_orphans,
            on_edit=self._edit_selected,
            fix_text=tr("warning_bar_fix_text"),
            edit_text=tr("warning_bar_edit_text"),
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
        splitter.setSizes(list(PRODUCT_MAIN_SPLITTER_SIZES))
        splitter.setCollapsible(0, True)
        splitter.setCollapsible(1, False)
        splitter.setCollapsible(2, True)

        root.addWidget(splitter)

    def _on_company_data_changed_catalog(self, _company_id: int = None):
        """يُستدعى عند تغيير البيانات — يحدّث الـ catalog في الصفوف."""
        self._refresh_form_catalog()

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
            QMessageBox.warning(self, tr("error"), str(e))
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
            QMessageBox.information(
                self, tr("warning"), tr("select_product_first")
            )
            return
        self._warning.setVisible(False)
        self._form.load_product(pid)

    def _delete_product(self, pid: int | None):
        if pid is None:
            QMessageBox.information(
                self, tr("warning"), tr("select_product_to_delete")
            )
            return
        try:
            conn = self._live_conn()
        except Exception as e:
            QMessageBox.warning(self, tr("error"), str(e))
            return

        svc  = ItemService(conn)
        item = svc.get(pid)
        if not item:
            return

        if confirm_delete(self, item.name):
            if self._form.is_editing and self._form._editing_id == pid:
                self._form.reset()
            svc.force_delete(pid)
            self._warning.setVisible(False)
            self._bom_tree.clear_tree()
            emit_company_data_changed()