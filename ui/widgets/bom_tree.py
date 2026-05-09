"""
ui/widgets/bom_tree.py  — مع عرض نص كامل flexible
======================
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTreeWidget, QTreeWidgetItem, QPushButton, QMessageBox,
    QHeaderView, QAbstractItemView, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont, QColor

from db.items_repo      import fetch_bom, fetch_item, delete_bom_row
from db.operations_repo import fetch_labor_op, fetch_machine_op
from models.costing     import (
    calc_cost, calc_labor_op_cost, calc_machine_op_cost, raw_unit_price
)
from ui.helpers import danger_button


_TYPE_LABELS = {
    "raw":        "🧱 خامة",
    "semi":       "🔧 نصف مصنع",
    "labor_op":   "👷 عملية عمالة",
    "machine_op": "⚙️ عملية تشغيل",
}

_TYPE_COLORS = {
    "raw":        "#1565c0",
    "semi":       "#6a1b9a",
    "labor_op":   "#2e7d32",
    "machine_op": "#e65100",
}


class BomTree(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pid  : int | None = None
        self._conn = None
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        lbl = QLabel("🔩 هيكل BOM")
        lbl.setStyleSheet("font-weight:bold; font-size:13px;")

        self.btn_expand   = QPushButton("⊞ توسيع")
        self.btn_collapse = QPushButton("⊟ طي")
        self.btn_del_node = danger_button("🗑 حذف المحدد")

        for btn in (self.btn_expand, self.btn_collapse, self.btn_del_node):
            btn.setEnabled(False)

        self.btn_expand.clicked.connect(lambda: self.tree.expandAll())
        self.btn_collapse.clicked.connect(lambda: self.tree.collapseAll())
        self.btn_del_node.clicked.connect(self._delete_node)

        header.addWidget(lbl)
        header.addStretch()
        for btn in (self.btn_expand, self.btn_collapse, self.btn_del_node):
            header.addWidget(btn)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["المكون", "الكمية", "التكلفة", "النوع"])
        self.tree.setSelectionMode(QTreeWidget.SingleSelection)

        hh = self.tree.header()
        # العمود الأول (الاسم) يتمدد
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        # الباقي Interactive — قابل للسحب
        hh.setSectionResizeMode(1, QHeaderView.Interactive)
        hh.setSectionResizeMode(2, QHeaderView.Interactive)
        hh.setSectionResizeMode(3, QHeaderView.Interactive)
        hh.setMinimumSectionSize(50)
        self.tree.setColumnWidth(1, 70)
        self.tree.setColumnWidth(2, 95)
        self.tree.setColumnWidth(3, 140)

        # scroll أفقي للأعمدة الضيقة
        self.tree.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.tree.setEditTriggers(QTreeWidget.NoEditTriggers)
        self.tree.setExpandsOnDoubleClick(True)
        # word wrap في النص
        self.tree.setWordWrap(True)
        self.tree.itemSelectionChanged.connect(self._on_selection)

        layout.addLayout(header)
        layout.addWidget(self.tree)

    def load(self, conn, parent_id: int):
        self._conn = conn
        self._pid  = parent_id
        for btn in (self.btn_expand, self.btn_collapse):
            btn.setEnabled(True)
        self._refresh()

    def clear_tree(self):
        self._pid = None
        self.tree.clear()
        for btn in (self.btn_expand, self.btn_collapse, self.btn_del_node):
            btn.setEnabled(False)

    def notify_refresh(self):
        if self._pid is not None:
            self._refresh()

    def _refresh(self):
        self.tree.clear()
        if self._pid is None:
            return
        for child_type, child_id, qty in fetch_bom(self._conn, self._pid):
            node = self._build_node(child_type, child_id, qty)
            if node:
                self.tree.addTopLevelItem(node)
        self.tree.expandToDepth(0)

    def _build_node(self, child_type: str, child_id: int,
                    qty: float) -> QTreeWidgetItem | None:

        if child_type == "raw":
            row = fetch_item(self._conn, child_id)
            if not row:
                return None
            name = row["name"]
            cost = raw_unit_price(row) * qty

        elif child_type == "semi":
            row = fetch_item(self._conn, child_id)
            if not row:
                return None
            name = row["name"]
            cost = calc_cost(self._conn, child_id) * qty

        elif child_type == "labor_op":
            op = fetch_labor_op(self._conn, child_id)
            if not op:
                return None
            name = op["name"]
            cost = calc_labor_op_cost(self._conn, child_id) * qty

        elif child_type == "machine_op":
            op = fetch_machine_op(self._conn, child_id)
            if not op:
                return None
            name = op["name"]
            cost = calc_machine_op_cost(self._conn, child_id) * qty

        else:
            return None

        qty_str  = str(qty) if qty == int(qty) else f"{qty:.4g}"
        type_lbl = _TYPE_LABELS.get(child_type, "")

        node = QTreeWidgetItem([name, qty_str, f"{cost:.4f}", type_lbl])
        node.setData(0, Qt.UserRole, (child_type, child_id))

        # tooltip بالنص الكامل لكل عمود
        node.setToolTip(0, name)
        node.setToolTip(1, f"الكمية: {qty_str}")
        node.setToolTip(2, f"التكلفة: {cost:.4f}")
        node.setToolTip(3, type_lbl)

        # لون حسب النوع
        color = QColor(_TYPE_COLORS.get(child_type, "#333"))
        node.setForeground(3, color)

        if child_type == "semi":
            font = node.font(0)
            font.setBold(True)
            node.setFont(0, font)
            node.setForeground(0, QColor(_TYPE_COLORS["semi"]))
            for sub_type, sub_id, sub_qty in fetch_bom(self._conn, child_id):
                child_node = self._build_node(sub_type, sub_id, sub_qty * qty)
                if child_node:
                    node.addChild(child_node)

        return node

    def _on_selection(self):
        item = self.tree.currentItem()
        self.btn_del_node.setEnabled(
            bool(item) and item.parent() is None
        )

    def _delete_node(self):
        node = self.tree.currentItem()
        if not node or self._pid is None:
            return
        if node.parent() is not None:
            QMessageBox.information(
                self, "تنبيه",
                "حذف المكونات الفرعية يتم من تبويب النصف مصنع مباشرةً."
            )
            return

        data = node.data(0, Qt.UserRole)
        if not data:
            return
        child_type, child_id = data
        delete_bom_row(self._conn, self._pid, child_type, child_id)
        self._refresh()