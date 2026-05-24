"""
ui/tabs/costing/product/product_table.py
=================================
_ProductTable  — جدول المنتجات المحفوظة مع FilterBar.
_WarningBar    — شريط تحذير المكونات الناقصة (orphans).

التحسين: _WarningBar الآن تستخدم BaseWarningBar من shared widgets
         بدل بناء الشريط يدوياً
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout,
    QPushButton, QTableWidgetItem,
)
from PyQt5.QtCore import Qt

from db.shared.items_repo  import fetch_items_by_type
from models.costing import calc_cost
from ui.helpers import (
    make_table, buttons_row, section_label, danger_button,
)
from ui.widgets.shared.filter_bar import FilterBar
from ui.widgets.shared.connection_mixin import LiveConnMixin
from ui.widgets.shared.base_warning_bar import BaseWarningBar
from ui.events import bus

_PRODUCT_SCOPE = {
    "semi":  "semi",
    "final": "final",
}


# ── إعادة تصدير للتوافق مع الكود الحالي في product_main_panel.py ──
# product_main_panel.py يستورد _WarningBar من هنا
_WarningBar = BaseWarningBar


class _ProductTable(QWidget, LiveConnMixin):
    def __init__(self, conn, product_type, on_select, on_edit, on_delete, parent=None):
        super().__init__(parent)
        self.conn         = conn
        self.product_type = product_type
        self._on_select   = on_select
        self._on_edit     = on_edit
        self._on_delete   = on_delete
        self._all_rows    = []
        self._scope       = _PRODUCT_SCOPE.get(product_type, product_type)
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 10)
        root.setSpacing(6)

        root.addWidget(section_label("─── المنتجات المحفوظة ───"))

        self._filter = FilterBar(self._live_conn(), scope=self._scope)
        self._filter.filter_changed.connect(self._apply_filter)
        root.addWidget(self._filter)

        self.table = make_table(["ID", "الاسم", "التصنيف", "التكلفة"], stretch_col=1)
        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(1, 220)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 120)
        self.table.itemSelectionChanged.connect(
            lambda: self._on_select(self.selected_pid())
        )
        root.addWidget(self.table)

        btn_edit = QPushButton("✏️ تعديل المحدد")
        btn_del  = danger_button("🗑️ حذف المحدد")
        btn_edit.setMinimumHeight(30)
        btn_del.setMinimumHeight(30)
        btn_edit.clicked.connect(lambda: self._on_edit(self.selected_pid()))
        btn_del.clicked.connect(lambda: self._on_delete(self.selected_pid()))
        root.addLayout(buttons_row(btn_edit, btn_del))

    def selected_pid(self):
        row = self.table.currentRow()
        return int(self.table.item(row, 0).text()) if row >= 0 else None

    def _load(self):
        try:
            conn = self._live_conn()
            self._all_rows = list(fetch_items_by_type(conn, self.product_type))
        except Exception:
            self._all_rows = []
        self._apply_filter()

    def _apply_filter(self):
        prev = self.selected_pid()
        self.table.setRowCount(0)
        shown = 0

        try:
            conn = self._live_conn()
        except Exception:
            self._filter.set_count(0, 0)
            return

        for row in self._all_rows:
            if not self._filter.match(row["name"], row["category_id"]):
                continue
            cost = calc_cost(conn, row["id"])
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(row["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(
                row["category_name"] if row["category_name"] else "—"
            ))
            self.table.setItem(r, 3, QTableWidgetItem(f"{cost:.4f}"))
            shown += 1

        self._filter.set_count(shown, len(self._all_rows))

        if prev is not None:
            for r in range(self.table.rowCount()):
                if int(self.table.item(r, 0).text()) == prev:
                    self.table.selectRow(r)
                    break