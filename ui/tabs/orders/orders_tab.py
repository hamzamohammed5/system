"""
ui/tabs/orders/orders_tab.py  — نسخة محسّنة UX
=============================
التحسينات:
  - قائمة الطلبات: كل صف يعرض badge الحالة بلون خلفية
  - الفلاتر: منظمة وواضحة
  - حالة "لا توجد نتائج" واضحة
  - الـ splitter بنسبة أفضل
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QFrame, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QAbstractItemView, QMessageBox,
    QDialog, QStyledItemDelegate, QStyle, QApplication,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QRect
from PyQt5.QtGui  import QColor, QFont, QPainter, QBrush, QPen

from db.orders.orders_repo import (
    fetch_all_orders, fetch_order, change_order_status,
    cancel_order, delete_order, fetch_orders_summary,
)
from ui.tabs.orders._order_form   import _OrderForm
from ui.tabs.orders._order_detail import _OrderDetail

# ── ثوابت الحالة (label, text_color, bg_color, border_color) ──
STATUS_LABELS = {
    "pending":     ("⏳ انتظار",   "#b45309", "#fffbeb", "#fde68a"),
    "confirmed":   ("✅ مؤكد",     "#1d4ed8", "#eff6ff", "#bfdbfe"),
    "in_progress": ("🔧 تنفيذ",   "#6d28d9", "#f5f3ff", "#ddd6fe"),
    "ready":       ("📦 جاهز",    "#065f46", "#ecfdf5", "#a7f3d0"),
    "delivered":   ("🚚 مُسلَّم",  "#374151", "#f9fafb", "#e5e7eb"),
    "cancelled":   ("❌ ملغي",    "#991b1b", "#fef2f2", "#fecaca"),
    "on_hold":     ("⏸ معلق",    "#9a3412", "#fff7ed", "#fed7aa"),
}

PRIORITY_LABELS = {
    "low":    ("⬇",  "#9ca3af"),
    "normal": ("➡",  "#6b7280"),
    "high":   ("⬆",  "#f59e0b"),
    "urgent": ("🔴", "#ef4444"),
}

TYPE_LABELS = {
    "new":     "جديد",
    "reorder": "إعادة",
    "custom":  "مخصص",
}

# ── ألوان ──
_BG    = "#f8f9fb"
_WHITE = "#ffffff"
_BLUE  = "#1565c0"
_BORDER = "#e5e9f0"


# ══════════════════════════════════════════════════════════
# Delegate لعرض badge الحالة بخلفية ملونة
# ══════════════════════════════════════════════════════════

class _StatusDelegate(QStyledItemDelegate):
    """يرسم badge ملون لخلية الحالة."""

    def paint(self, painter: QPainter, option, index):
        painter.save()

        # خلفية الصف (تحديد أو تبادل)
        self.initStyleOption(option, index)
        style = option.widget.style() if option.widget else QApplication.style()
        style.drawPrimitive(QStyle.PE_PanelItemViewItem, option, painter, option.widget)

        status_key = index.data(Qt.UserRole + 1)
        text = index.data(Qt.DisplayRole) or ""
        info = STATUS_LABELS.get(status_key, (text, "#555", "#f5f5f5", "#e0e0e0"))
        _, fg, bg, bd = info

        # رسم البadge
        rect = option.rect
        badge_w = min(rect.width() - 12, 90)
        badge_h = 22
        badge_x = rect.x() + (rect.width() - badge_w) // 2
        badge_y = rect.y() + (rect.height() - badge_h) // 2
        badge_rect = QRect(badge_x, badge_y, badge_w, badge_h)

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(bg)))
        painter.setPen(QPen(QColor(bd), 1))
        painter.drawRoundedRect(badge_rect, 8, 8)

        painter.setPen(QPen(QColor(fg)))
        f = painter.font()
        f.setBold(True)
        painter.setFont(f)
        painter.drawText(badge_rect, Qt.AlignCenter, text)

        painter.restore()

    def sizeHint(self, option, index):
        return __import__('PyQt5.QtCore', fromlist=['QSize']).QSize(100, 40)


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
        toolbar.setStyleSheet(f"""
            QFrame {{
                background: {_WHITE};
                border-bottom: 1px solid {_BORDER};
            }}
        """)
        tb = QVBoxLayout(toolbar)
        tb.setContentsMargins(10, 10, 10, 10)
        tb.setSpacing(6)

        # صف 1: بحث + زر جديد
        row1 = QHBoxLayout()
        row1.setSpacing(6)

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍  بحث برقم الطلب أو اسم العميل...")
        self.inp_search.setMinimumHeight(34)
        self.inp_search.setClearButtonEnabled(True)
        self.inp_search.setStyleSheet(f"""
            QLineEdit {{
                background: {_BG};
                border: 1px solid #cdd3e0;
                border-radius: 6px;
                padding: 0 10px;
            }}
            QLineEdit:focus {{ border-color: {_BLUE}; background: {_WHITE}; }}
        """)
        self.inp_search.textChanged.connect(lambda: self._timer.start())

        btn_new = QPushButton("＋  طلب جديد")
        btn_new.setMinimumHeight(34)
        btn_new.setCursor(Qt.PointingHandCursor)
        btn_new.setStyleSheet(f"""
            QPushButton {{
                background: {_BLUE};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #0d47a1; }}
        """)
        btn_new.clicked.connect(self.new_order.emit)
        row1.addWidget(self.inp_search, stretch=1)
        row1.addWidget(btn_new)
        tb.addLayout(row1)

        # صف 2: فلاتر
        row2 = QHBoxLayout()
        row2.setSpacing(6)

        cmb_ss = f"""
            QComboBox {{
                background: {_BG};
                border: 1px solid #cdd3e0;
                border-radius: 5px;
                padding: 0 8px;
                min-height: 28px;
            }}
            QComboBox:focus {{ border-color: {_BLUE}; }}
            QComboBox::drop-down {{ border: none; width: 16px; }}
        """

        self.cmb_status = QComboBox()
        self.cmb_status.setStyleSheet(cmb_ss)
        self.cmb_status.addItem("كل الحالات", None)
        for k, (lbl, *_) in STATUS_LABELS.items():
            self.cmb_status.addItem(lbl, k)
        self.cmb_status.currentIndexChanged.connect(self._apply_filter)

        self.cmb_type = QComboBox()
        self.cmb_type.setStyleSheet(cmb_ss)
        self.cmb_type.addItem("كل الأنواع", None)
        for k, v in TYPE_LABELS.items():
            self.cmb_type.addItem(v, k)
        self.cmb_type.currentIndexChanged.connect(self._apply_filter)

        self.cmb_priority = QComboBox()
        self.cmb_priority.setStyleSheet(cmb_ss)
        self.cmb_priority.addItem("كل الأولويات", None)
        for k, (icon, color) in PRIORITY_LABELS.items():
            self.cmb_priority.addItem(icon, k)
        self.cmb_priority.currentIndexChanged.connect(self._apply_filter)

        btn_reset = QPushButton("↺")
        btn_reset.setToolTip("مسح الفلاتر")
        btn_reset.setFixedSize(28, 28)
        btn_reset.setCursor(Qt.PointingHandCursor)
        btn_reset.setStyleSheet(f"""
            QPushButton {{
                background: #e8eaf6; color: #3949ab;
                border: 1px solid #c5cae9; border-radius: 5px;
            }}
            QPushButton:hover {{ background: #c5cae9; }}
        """)
        btn_reset.clicked.connect(self._reset_filters)

        row2.addWidget(self.cmb_status, stretch=2)
        row2.addWidget(self.cmb_type, stretch=1)
        row2.addWidget(self.cmb_priority, stretch=1)
        row2.addWidget(btn_reset)
        tb.addLayout(row2)

        root.addWidget(toolbar)

        # ── الجدول ───────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "رقم الطلب", "العميل", "الحالة", "الأولوية", "التاريخ"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: none;
                background: {_WHITE};
                alternate-background-color: #fafbff;
                outline: none;
            }}
            QTableWidget::item {{
                padding: 4px 10px;
                border-bottom: 1px solid #f0f2f8;
            }}
            QTableWidget::item:selected {{
                background: #dbeafe;
                color: #1e40af;
            }}
            QHeaderView::section {{
                background: {_BG};
                color: {_BLUE};
                font-weight: bold;
                padding: 5px 10px;
                border: none;
                border-bottom: 2px solid {_BORDER};
            }}
        """)

        # delegate لعمود الحالة
        self._status_delegate = _StatusDelegate(self.table)
        self.table.setItemDelegateForColumn(2, self._status_delegate)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.setColumnWidth(2, 100)
        hh.setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.setColumnWidth(3, 50)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.table.itemSelectionChanged.connect(self._on_select)
        self.table.doubleClicked.connect(self._on_select)
        root.addWidget(self.table, stretch=1)

        # ── رسالة "لا توجد نتائج" ─────────────────────────
        self._no_results = QFrame()
        self._no_results.setStyleSheet(f"background:{_WHITE}; border:none;")
        self._no_results.setVisible(False)
        nr_lay = QVBoxLayout(self._no_results)
        nr_lay.setAlignment(Qt.AlignCenter)
        lbl_nr1 = QLabel("🔍")
        lbl_nr1.setAlignment(Qt.AlignCenter)
        lbl_nr1.setStyleSheet("background:transparent;")
        lbl_nr2 = QLabel("لا توجد طلبات مطابقة")
        lbl_nr2.setAlignment(Qt.AlignCenter)
        lbl_nr2.setStyleSheet("color:#9ca3af; background:transparent;")
        nr_lay.addWidget(lbl_nr1)
        nr_lay.addWidget(lbl_nr2)
        root.addWidget(self._no_results)

        # ── شريط الحالة ───────────────────────────────────
        self._status_bar = QLabel("")
        self._status_bar.setAlignment(Qt.AlignCenter)
        self._status_bar.setStyleSheet(f"""
            background: {_BG};
            color: #6b7280;
            padding: 5px;
            border-top: 1px solid {_BORDER};
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
        self.table.setVisible(bool(filtered))
        self._no_results.setVisible(not bool(filtered) and bool(self._all_rows))

        for row in filtered:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, 42)

            # رقم الطلب
            num_item = QTableWidgetItem(row["order_number"])
            num_item.setData(Qt.UserRole, row["id"])
            f = QFont(); f.setWeight(QFont.Medium)
            num_item.setFont(f)
            num_item.setForeground(QColor(_BLUE))
            self.table.setItem(r, 0, num_item)

            # العميل
            cust_item = QTableWidgetItem(row["customer_name"])
            self.table.setItem(r, 1, cust_item)

            # الحالة — delegate يرسمها
            status_text = STATUS_LABELS.get(row["status"], (row["status"],))[0]
            s_item = QTableWidgetItem(status_text)
            s_item.setData(Qt.UserRole + 1, row["status"])
            s_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 2, s_item)

            # الأولوية
            pri_icon, pri_color = PRIORITY_LABELS.get(row["priority"], ("", "#555"))
            pri_item = QTableWidgetItem(pri_icon)
            pri_item.setTextAlignment(Qt.AlignCenter)
            pri_item.setForeground(QColor(pri_color))
            if row["priority"] in ("high", "urgent"):
                f2 = QFont(); f2.setBold(True)
                pri_item.setFont(f2)
            self.table.setItem(r, 3, pri_item)

            # التاريخ
            date_str = (row["order_date"] or "")[:10]
            date_item = QTableWidgetItem(date_str)
            date_item.setForeground(QColor("#9ba5be"))
            self.table.setItem(r, 4, date_item)

        cnt   = len(filtered)
        total = len(self._all_rows)
        self._status_bar.setText(
            f"{cnt} طلب" if cnt == total else f"عرض {cnt} من {total} طلب"
        )

    def _reset_filters(self):
        self.cmb_status.setCurrentIndex(0)
        self.cmb_type.setCurrentIndex(0)
        self.cmb_priority.setCurrentIndex(0)
        self.inp_search.clear()

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
        super().__init__(conn)
        self.conn = conn
        self._build()

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(3)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{ background: {_BORDER}; }}
            QSplitter::handle:hover {{ background: #bfdbfe; }}
        """)

        self._list   = _OrdersListPanel(self.conn)
        self._detail = _OrderDetail(self.conn)

        splitter.addWidget(self._list)
        splitter.addWidget(self._detail)

        # نسبة أفضل: القائمة أضيق، التفاصيل أعرض
        splitter.setSizes([360, 740])
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