"""
ui/tabs/orders/orders_tab.py
=============================
تبويب إدارة الطلبات:
  يسار  : قائمة الطلبات مع فلاتر متعددة
  يمين  : تفاصيل الطلب + إدارة البنود + سجل الحالة
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QFrame, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QAbstractItemView, QMessageBox,
    QDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui  import QColor, QFont

from db.orders.orders_repo import (
    fetch_all_orders, fetch_order, change_order_status,
    cancel_order, delete_order, fetch_orders_summary,
)
from ui.tabs.orders._order_form   import _OrderForm
from ui.tabs.orders._order_detail import _OrderDetail

# ── ثوابت الحالة ──────────────────────────────────────────
STATUS_LABELS = {
    "pending":     ("⏳ انتظار",   "#f59e0b", "#fffbeb"),
    "confirmed":   ("✅ مؤكد",     "#3b82f6", "#eff6ff"),
    "in_progress": ("🔧 تنفيذ",   "#8b5cf6", "#f5f3ff"),
    "ready":       ("📦 جاهز",    "#10b981", "#ecfdf5"),
    "delivered":   ("🚚 مُسلَّم",  "#6b7280", "#f9fafb"),
    "cancelled":   ("❌ ملغي",    "#ef4444", "#fef2f2"),
    "on_hold":     ("⏸ معلق",    "#f97316", "#fff7ed"),
}

PRIORITY_LABELS = {
    "low":    ("⬇ منخفض",   "#9ca3af"),
    "normal": ("➡ عادي",    "#6b7280"),
    "high":   ("⬆ عالي",   "#f59e0b"),
    "urgent": ("🔴 عاجل",   "#ef4444"),
}

TYPE_LABELS = {
    "new":     "جديد",
    "reorder": "إعادة طلب",
    "custom":  "مخصص",
}


def _make_status_item(status: str) -> QTableWidgetItem:
    label, color, bg = STATUS_LABELS.get(status, (status, "#555", "#fff"))
    item = QTableWidgetItem(label)
    item.setTextAlignment(Qt.AlignCenter)
    item.setForeground(QColor(color))
    return item


def _make_priority_item(priority: str) -> QTableWidgetItem:
    label, color = PRIORITY_LABELS.get(priority, (priority, "#555"))
    item = QTableWidgetItem(label)
    item.setTextAlignment(Qt.AlignCenter)
    item.setForeground(QColor(color))
    f = QFont()
    f.setBold(priority in ("high", "urgent"))
    item.setFont(f)
    return item


# ══════════════════════════════════════════════════════════
# لوحة قائمة الطلبات (يسار)
# ══════════════════════════════════════════════════════════

class _OrdersListPanel(QWidget):
    order_selected = pyqtSignal(int)
    new_order      = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._all_rows = []
        self._timer    = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._apply_filter)
        self._build()
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Toolbar ──────────────────────────────────────
        toolbar = QFrame()
        toolbar.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border-bottom: 1px solid #e5e9f0;
            }
        """)
        tb = QVBoxLayout(toolbar)
        tb.setContentsMargins(12, 10, 12, 10)
        tb.setSpacing(8)

        # صف 1: بحث + زر جديد
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("بحث برقم الطلب أو اسم العميل...")
        self.inp_search.setMinimumHeight(34)
        self.inp_search.setStyleSheet("""
            QLineEdit {
                background: #f8f9fb;
                border: 1px solid #cdd3e0;
                border-radius: 6px;
                padding: 0 10px;
                font-size: 12px;
            }
            QLineEdit:focus { border-color: #1565c0; background: white; }
        """)
        self.inp_search.textChanged.connect(lambda: self._timer.start())

        btn_new = QPushButton("  + طلب جديد")
        btn_new.setMinimumHeight(34)
        btn_new.setStyleSheet("""
            QPushButton {
                background: #1565c0;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 14px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover { background: #0d47a1; }
        """)
        btn_new.clicked.connect(self.new_order.emit)
        row1.addWidget(self.inp_search, stretch=1)
        row1.addWidget(btn_new)
        tb.addLayout(row1)

        # صف 2: فلاتر
        row2 = QHBoxLayout()
        row2.setSpacing(6)

        self.cmb_status = QComboBox()
        self.cmb_status.setMinimumHeight(28)
        self.cmb_status.addItem("كل الحالات", None)
        for k, (lbl, _, _) in STATUS_LABELS.items():
            self.cmb_status.addItem(lbl, k)
        self.cmb_status.currentIndexChanged.connect(self._apply_filter)

        self.cmb_type = QComboBox()
        self.cmb_type.setMinimumHeight(28)
        self.cmb_type.addItem("كل الأنواع", None)
        for k, v in TYPE_LABELS.items():
            self.cmb_type.addItem(v, k)
        self.cmb_type.currentIndexChanged.connect(self._apply_filter)

        self.cmb_priority = QComboBox()
        self.cmb_priority.setMinimumHeight(28)
        self.cmb_priority.addItem("كل الأولويات", None)
        for k, (lbl, _) in PRIORITY_LABELS.items():
            self.cmb_priority.addItem(lbl, k)
        self.cmb_priority.currentIndexChanged.connect(self._apply_filter)

        for cmb in (self.cmb_status, self.cmb_type, self.cmb_priority):
            cmb.setStyleSheet("""
                QComboBox {
                    background: #f8f9fb;
                    border: 1px solid #cdd3e0;
                    border-radius: 5px;
                    padding: 0 8px;
                    font-size: 11px;
                }
                QComboBox:focus { border-color: #1565c0; }
                QComboBox::drop-down { border: none; }
            """)

        row2.addWidget(self.cmb_status, stretch=2)
        row2.addWidget(self.cmb_type, stretch=1)
        row2.addWidget(self.cmb_priority, stretch=1)
        tb.addLayout(row2)

        root.addWidget(toolbar)

        # ── الجدول ───────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "رقم الطلب", "العميل", "النوع", "الحالة", "الأولوية", "التاريخ"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        self.table.setStyleSheet("""
            QTableWidget {
                border: none;
                background: white;
                alternate-background-color: #fafbff;
                font-size: 12px;
                outline: none;
            }
            QTableWidget::item { padding: 6px 10px; }
            QTableWidget::item:selected {
                background: #dbeafe;
                color: #1e40af;
            }
            QHeaderView::section {
                background: #f8f9fb;
                color: #6b7280;
                font-size: 11px;
                font-weight: bold;
                padding: 6px 10px;
                border: none;
                border-bottom: 2px solid #e5e9f0;
                border-right: 1px solid #e5e9f0;
            }
        """)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.table.itemSelectionChanged.connect(self._on_select)
        self.table.doubleClicked.connect(self._on_select)
        root.addWidget(self.table, stretch=1)

        # ── شريط الحالة ───────────────────────────────────
        self._status_bar = QLabel("")
        self._status_bar.setAlignment(Qt.AlignCenter)
        self._status_bar.setStyleSheet("""
            background: #f8f9fb;
            color: #6b7280;
            font-size: 10px;
            padding: 5px;
            border-top: 1px solid #e5e9f0;
        """)
        root.addWidget(self._status_bar)

    def _load(self):
        self._all_rows = fetch_all_orders(self.conn)
        self._apply_filter()

    def _apply_filter(self):
        q        = self.inp_search.text().strip().lower()
        status   = self.cmb_status.currentData()
        typ      = self.cmb_type.currentData()
        priority = self.cmb_priority.currentData()

        filtered = []
        for r in self._all_rows:
            if status   and r["status"]     != status:   continue
            if typ      and r["order_type"] != typ:      continue
            if priority and r["priority"]   != priority: continue
            if q and q not in r["order_number"].lower() \
                 and q not in r["customer_name"].lower(): continue
            filtered.append(r)

        self.table.setRowCount(0)
        for row in filtered:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, 40)

            num_item = QTableWidgetItem(row["order_number"])
            num_item.setData(Qt.UserRole, row["id"])
            f = QFont()
            f.setWeight(QFont.Medium)
            num_item.setFont(f)
            self.table.setItem(r, 0, num_item)

            self.table.setItem(r, 1, QTableWidgetItem(row["customer_name"]))
            self.table.setItem(r, 2, QTableWidgetItem(
                TYPE_LABELS.get(row["order_type"], row["order_type"])
            ))
            self.table.setItem(r, 3, _make_status_item(row["status"]))
            self.table.setItem(r, 4, _make_priority_item(row["priority"]))
            self.table.setItem(r, 5, QTableWidgetItem(
                row["order_date"] or ""
            ))

        cnt = len(filtered)
        total = len(self._all_rows)
        self._status_bar.setText(
            f"{cnt} طلب" if cnt == total else f"{cnt} من {total} طلب"
        )

    def _on_select(self):
        row = self.table.currentRow()
        if row < 0:
            return
        item = self.table.item(row, 0)
        if item:
            self.order_selected.emit(item.data(Qt.UserRole))

    def select_order(self, order_id: int):
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item and item.data(Qt.UserRole) == order_id:
                self.table.selectRow(r)
                break

    def refresh(self):
        self._load()


# ══════════════════════════════════════════════════════════
# تبويب الطلبات الرئيسي
# ══════════════════════════════════════════════════════════

class OrdersTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(4)
        splitter.setStyleSheet("""
            QSplitter::handle { background: #e5e9f0; }
            QSplitter::handle:hover { background: #bfdbfe; }
        """)

        # قائمة الطلبات
        self._list = _OrdersListPanel(self.conn)
        splitter.addWidget(self._list)

        # لوحة التفاصيل
        self._detail = _OrderDetail(self.conn)
        splitter.addWidget(self._detail)

        splitter.setSizes([420, 680])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        root.addWidget(splitter)

        # ربط الـ signals
        self._list.order_selected.connect(self._on_order_selected)
        self._list.new_order.connect(self._on_new_order)
        self._detail.saved.connect(self._on_saved)
        self._detail.deleted.connect(self._on_deleted)
        self._detail.status_changed.connect(self._on_status_changed)

    def _on_order_selected(self, order_id: int):
        self._detail.load_order(order_id)

    def _on_new_order(self):
        self._detail.new_order()

    def _on_saved(self, order_id: int):
        self._list.refresh()
        self._list.select_order(order_id)

    def _on_deleted(self):
        self._list.refresh()
        self._detail.clear()

    def _on_status_changed(self, order_id: int):
        self._list.refresh()
        self._list.select_order(order_id)
        self._detail.load_order(order_id)

    def refresh(self):
        self._list.refresh()