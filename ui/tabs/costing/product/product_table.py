"""
ui/tabs/costing/product/product_table.py
=================================
_ProductTable  — جدول المنتجات المحفوظة مع FilterBar.
_WarningBar    — شريط تحذير المكونات الناقصة (orphans).
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QPushButton, QLabel, QTableWidgetItem, QMessageBox,
)
from PyQt5.QtCore import Qt

from db.shared.items_repo  import fetch_items_by_type
from models.costing import calc_cost
from ui.helpers import (
    make_table, buttons_row, section_label, danger_button,
)
from ui.widgets.shared.filter_bar import FilterBar
from ui.widgets.shared.connection_mixin import LiveConnMixin
from ui.events import bus

_TYPE_AR = {
    "raw":        "خامة",
    "semi":       "نصف مصنع",
    "labor_op":   "عملية عمالة",
    "machine_op": "عملية تشغيل",
}

_PRODUCT_SCOPE = {
    "semi":  "semi",
    "final": "final",
}


class _WarningBar(QFrame):
    def __init__(self, on_fix, on_edit, parent=None):
        super().__init__(parent)
        self.setObjectName("warningBar")
        self.setStyleSheet("""
            #warningBar {
                background: #fff3e0;
                border: 1px solid #e65100;
                border-radius: 6px;
            }
        """)
        self.setVisible(False)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(10)

        self._icon = QLabel("⚠️")
        self._icon.setStyleSheet("font-size:16px; background:transparent; border:none;")
        self._lbl = QLabel()
        self._lbl.setWordWrap(True)
        self._lbl.setStyleSheet(
            "color:#bf360c; font-weight:bold; background:transparent; border:none;"
        )

        btn_fix = QPushButton("🗑️ حذف الناقص")
        btn_fix.setStyleSheet(
            "background:#e65100; color:white; border:none; border-radius:4px; padding:4px 10px;"
        )
        btn_fix.clicked.connect(on_fix)

        btn_edit = QPushButton("✏️ تعديل")
        btn_edit.setStyleSheet(
            "background:#1565c0; color:white; border:none; border-radius:4px; padding:4px 10px;"
        )
        btn_edit.clicked.connect(on_edit)

        btn_dismiss = QPushButton("✖")
        btn_dismiss.setStyleSheet(
            "background:transparent; color:#888; border:1px solid #ccc;"
            "border-radius:4px; padding:4px 8px;"
        )
        btn_dismiss.clicked.connect(lambda: self.setVisible(False))

        lay.addWidget(self._icon)
        lay.addWidget(self._lbl, stretch=1)
        lay.addWidget(btn_fix)
        lay.addWidget(btn_edit)
        lay.addWidget(btn_dismiss)

    def show_orphans(self, orphans, product_name):
        if not orphans:
            self.setVisible(False)
            return
        lines = []
        for o in orphans:
            type_ar  = _TYPE_AR.get(o["child_type"], o["child_type"])
            display  = o["child_name"] or f"ID: {o['child_id']}"
            lines.append(f"• {type_ar}: «{display}»")
        msg = f"«{product_name}» — {len(orphans)} مكوّن محذوف:\n" + "  ".join(lines)
        self._lbl.setText(msg)
        self.setVisible(True)


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