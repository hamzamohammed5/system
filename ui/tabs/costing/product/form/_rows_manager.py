"""
ui/tabs/costing/product/form/_rows_manager.py
==============================================
_RowsManager — إدارة صفوف مكونات BOM في فورم المنتج.

مسؤوليته:
  - إضافة صفوف ComponentRow
  - حذف الصفوف
  - جمع قيم الصفوف (collect_rows)
  - مسح كل الصفوف
  - تحديث الـ catalog في الصفوف الموجودة

[Refactor] تغيير import إلى ComponentRow الجديد:
  من: ui.widgets.shared.component_row._row_widget
  إلى: ui.widgets.components.component_row.widget
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea,
)
from PyQt5.QtCore import QTimer

# ✅ [Refactor] استخدام ComponentRow الجديد بدل القديم
from ui.widgets.components.component_row.widget import ComponentRow


class _RowsManager(QWidget):
    """
    المنطقة القابلة للتمرير التي تحتوي على صفوف المكونات.

    الاستخدام:
        mgr = _RowsManager(catalog_fn)
        layout.addWidget(mgr, stretch=1)

        # إضافة صف
        row = mgr.add_row(child_type="raw", child_id=5, qty=2.0)

        # جمع القيم عند الحفظ
        rows = mgr.collect_rows()

        # مسح كل الصفوف
        mgr.clear_rows()
    """

    def __init__(self, catalog_fn, parent=None):
        super().__init__(parent)
        self._catalog_fn = catalog_fn
        self._build()

    def _build(self):
        from PyQt5.QtWidgets import QVBoxLayout as _VL
        outer = _VL(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.rows_container = QWidget()
        self.rows_layout    = QVBoxLayout(self.rows_container)
        self.rows_layout.setSpacing(2)
        self.rows_layout.setContentsMargins(12, 4, 12, 4)
        self.rows_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.rows_container)
        scroll.setMinimumHeight(80)
        scroll.setStyleSheet("border:none;")
        outer.addWidget(scroll, stretch=1)

    # ── API خارجي ─────────────────────────────────────────

    def add_row(self, child_type: str = "raw", child_id=None,
                qty: float = 1.0, orphan_name: str = None,
                waste_pct: float = 0.0, variant_id: int = None,
                machine_op_row_id: int = None) -> ComponentRow:
        """
        يضيف صف ComponentRow جديد ويرجعه.
        """
        row = ComponentRow(
            catalog_fn=self._catalog_fn,
            child_type=child_type,
            child_id=child_id,
            qty=qty,
            waste_pct=waste_pct,
            variant_id=variant_id,
            machine_op_row_id=machine_op_row_id,
        )
        if row.is_orphan() and orphan_name:
            row.set_orphan_name(orphan_name)
        row.removed.connect(self._remove_row)
        self.rows_layout.insertWidget(self.rows_layout.count() - 1, row)
        QTimer.singleShot(0, row.refresh_catalog)
        return row

    def _remove_row(self, widget: QWidget):
        self.rows_layout.removeWidget(widget)
        widget.deleteLater()

    def collect_rows(self) -> list:
        """
        يجمع قيم كل الصفوف الصالحة.
        يرجع list of (child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id)
        """
        result = []
        for i in range(self.rows_layout.count()):
            item = self.rows_layout.itemAt(i)
            if not item:
                continue
            w = item.widget()
            if isinstance(w, ComponentRow):
                val = w.get_values()
                if val:
                    val = tuple(val)
                    while len(val) < 6:
                        val = val + (None,)
                    result.append(val)
        return result

    def clear_rows(self):
        """يحذف كل الصفوف ويبقي الـ stretch."""
        while self.rows_layout.count() > 1:
            item = self.rows_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    def refresh_catalog(self, new_catalog: dict = None):
        """
        يحدث الـ catalog في كل ComponentRow موجود.
        يُستدعى عند تغيير بيانات DB.
        """
        for i in range(self.rows_layout.count()):
            item = self.rows_layout.itemAt(i)
            if not item:
                continue
            w = item.widget()
            if isinstance(w, ComponentRow):
                w.refresh_catalog(new_catalog)