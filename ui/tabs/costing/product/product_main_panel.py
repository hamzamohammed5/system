"""
ui/tabs/costing/product/product_main_panel.py
===============================================
_ProductMainPanel — اللوحة الرئيسية: فورم + جدول + BOM tree + تحذير.

يرث من LiveConnMixin بدل كتابة _live_conn يدوياً.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter, QMessageBox,
)
from PyQt5.QtCore import Qt

from db.shared.items_repo import fetch_item, delete_item
from ui.helpers            import confirm_delete
from ui.widgets.shared.connection_mixin import LiveConnMixin
from ui.tabs.costing.shared.component_row import ComponentRow
from ui.tabs.costing.shared.bom_tree      import BomTree
from ui.events import bus

from .product_form  import _FormPanel
from .product_table import _ProductTable, _WarningBar
from ._catalog_provider import build_product_catalog
from ._orphan_handler   import _OrphanHandler

from ui.app_settings import _C

_SPLITTER_STYLE = f"""
    QSplitter::handle {{
        background: {_C['border']};
        border-top: 1px solid {_C['border_med']};
    }}
    QSplitter::handle:hover {{ background: {_C['accent_mid']}; }}
    QSplitter::handle:pressed {{ background: {_C['accent']}; }}
"""


class _ProductMainPanel(QWidget, LiveConnMixin):
    """
    اللوحة الرئيسية للمنتجات — تجمع بين:
      - الفورم (إضافة / تعديل) في الأعلى
      - جدول المنتجات في المنتصف
      - شجرة BOM في الأسفل
    """

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

    # ── بناء الواجهة ──────────────────────────────────────

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(_SPLITTER_STYLE)

        self._form = _FormPanel(self.conn, self.product_type, self._get_catalog)
        bus.data_changed.connect(self._refresh_form_catalog)

        from PyQt5.QtWidgets import QWidget as _W
        mid_widget = _W()
        mid_layout = QVBoxLayout(mid_widget)
        mid_layout.setContentsMargins(0, 0, 0, 0)
        mid_layout.setSpacing(0)

        self._warning = _WarningBar(
            on_fix=self._fix_orphans,
            on_edit=self._edit_selected,
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

    # ── أحداث البيانات ────────────────────────────────────

    def _on_data_changed(self):
        pid = self._prod_table.selected_pid()
        if pid is None:
            return
        try:
            conn = self._live_conn()
            self._check_orphans(pid, conn)
            self._bom_tree.load(conn, pid)
        except Exception:
            pass

    def _on_product_selected(self, pid: int | None):
        if pid is None:
            self._bom_tree.clear_tree()
            self._warning.setVisible(False)
            return
        try:
            conn = self._live_conn()
            self._check_orphans(pid, conn)
            self._bom_tree.load(conn, pid)
        except Exception:
            pass

    def _refresh_form_catalog(self):
        """يحدث الـ catalog في كل ComponentRow موجود في الفورم."""
        try:
            new_catalog = self._get_catalog()
        except Exception:
            return
        self._form._rows.refresh_catalog(new_catalog)

    def _check_orphans(self, pid: int, conn=None):
        if conn is None:
            conn = self._live_conn()
        orphans = self._orphan.fetch(conn, pid)
        item    = fetch_item(conn, pid)
        name    = item["name"] if item else f"ID {pid}"
        self._warning.show_orphans(orphans, name)

    # ── إجراءات ──────────────────────────────────────────

    def _fix_orphans(self):
        pid = self._prod_table.selected_pid()
        if pid is None:
            return
        try:
            conn = self._live_conn()
        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))
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
            QMessageBox.information(self, "تنبيه", "اختر منتجاً من الجدول أولاً")
            return
        self._warning.setVisible(False)
        self._form.load_product(pid)

    def _delete_product(self, pid: int | None):
        if pid is None:
            QMessageBox.information(self, "تنبيه", "اختر منتجاً أولاً")
            return
        try:
            conn = self._live_conn()
        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))
            return

        item = fetch_item(conn, pid)
        if not item:
            return

        if confirm_delete(self, item["name"]):
            if self._form.is_editing and self._form._editing_id == pid:
                self._form.reset()
            delete_item(conn, pid)
            self._warning.setVisible(False)
            self._bom_tree.clear_tree()
            bus.data_changed.emit()