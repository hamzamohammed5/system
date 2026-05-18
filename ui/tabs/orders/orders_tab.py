"""
ui/tabs/orders/orders_tab.py  — نسخة UX v3 محسّنة
=============================
التحسينات:
  - _StatusDelegate محسّن: badge أوضح وأكبر
  - _FilterToolbar: تصميم نظيف مع spacing موحد
  - قائمة الطلبات: صفوف أوضح مع تمييز بصري للأولوية
  - شريط الحالة: معلومات واضحة
  - EmptyState احترافي
  - auto_fit_columns + resizable columns (NEW)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QFrame, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QAbstractItemView, QMessageBox,
    QDialog, QStyledItemDelegate, QStyle, QApplication,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QRect, QSize
from PyQt5.QtGui  import QColor, QFont, QPainter, QBrush, QPen

from db.orders.orders_repo import (
    fetch_all_orders, fetch_order, change_order_status,
    cancel_order, delete_order, fetch_orders_summary,
)
from ui.tabs.orders._order_form   import _OrderForm
from ui.tabs.orders._order_detail import _OrderDetail

from ui.widgets.shared.panels import EmptyState, _make_btn
from ui.widgets.shared.table_utils import (
    make_table_item, color_item, bold_item, muted_item,
    insert_row, ROW_HEIGHT_LARGE,
    auto_fit_columns,          # ← NEW
)
from ui.app_settings import _C, get_font_size, fs

# ── ثوابت الحالة ──
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

_BG     = "#f8f9fb"
_WHITE  = "#ffffff"
_BLUE   = _C['accent']
_BORDER = _C['border']


# ══════════════════════════════════════════════════════════
# Delegate لعرض badge الحالة — محسّن
# ══════════════════════════════════════════════════════════

class _StatusDelegate(QStyledItemDelegate):
    """يرسم badge ملون وواضح لخلية الحالة."""

    def paint(self, painter: QPainter, option, index):
        painter.save()
        self.initStyleOption(option, index)
        style = option.widget.style() if option.widget else QApplication.style()
        style.drawPrimitive(QStyle.PE_PanelItemViewItem, option, painter, option.widget)

        status_key = index.data(Qt.UserRole + 1)
        text = index.data(Qt.DisplayRole) or ""
        info = STATUS_LABELS.get(status_key, (text, "#555", "#f5f5f5", "#e0e0e0"))
        _, fg, bg, bd = info

        rect   = option.rect
        pad_v  = 7
        pad_h  = 6
        badge_w = min(rect.width() - pad_h * 2, 90)
        badge_h = rect.height() - pad_v * 2
        badge_h = max(badge_h, 22)
        badge_h = min(badge_h, 28)
        badge_x = rect.x() + (rect.width() - badge_w) // 2
        badge_y = rect.y() + (rect.height() - badge_h) // 2
        badge_rect = QRect(badge_x, badge_y, badge_w, badge_h)

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(bg)))
        painter.setPen(QPen(QColor(bd), 1.2))
        painter.drawRoundedRect(badge_rect, 10, 10)

        painter.setPen(QPen(QColor(fg)))
        f = painter.font()
        f.setBold(True)
        base = get_font_size()
        f.setPointSize(max(8, fs(base, -1)))
        painter.setFont(f)
        painter.drawText(badge_rect, Qt.AlignCenter, text)
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(100, ROW_HEIGHT_LARGE)


# ══════════════════════════════════════════════════════════
# شريط فلتر القائمة — محسّن
# ══════════════════════════════════════════════════════════

class _FilterToolbar(QFrame):
    """شريط البحث والفلاتر لقائمة الطلبات."""

    changed = pyqtSignal()

    _INPUT_SS = f"""
        QLineEdit {{
            background: {_C['bg_input']};
            border: 1.5px solid {_C['border_med']};
            border-radius: 6px;
            padding: 0 10px;
            font-size: 12px;
            color: {_C['text_primary']};
        }}
        QLineEdit:focus {{
            border-color: {_C['accent']};
            background: white;
        }}
    """

    _COMBO_SS = f"""
        QComboBox {{
            background: {_C['bg_surface_2']};
            border: 1px solid {_C['border']};
            border-radius: 5px;
            padding: 0 8px;
            min-height: 28px;
            font-size: 11px;
            color: {_C['text_primary']};
        }}
        QComboBox:focus {{ border-color: {_C['accent']}; }}
        QComboBox::drop-down {{ border: none; width: 16px; }}
        QComboBox QAbstractItemView {{
            background: {_C['bg_input']};
            border: 1px solid {_C['border_med']};
            selection-background-color: {_C['accent_light']};
            selection-color: {_C['accent_text']};
            outline: none;
        }}
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self.changed.emit)
        self._build()

    def _build(self):
        self.setStyleSheet(f"""
            QFrame {{
                background: {_WHITE};
                border: none;
                border-bottom: 1px solid {_BORDER};
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 10)
        root.setSpacing(8)

        # ── صف 1: زر جديد ──
        row0 = QHBoxLayout()
        self.btn_new = QPushButton("＋  طلب جديد")
        self.btn_new.setMinimumHeight(36)
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.setStyleSheet(f"""
            QPushButton {{
                background: {_C['accent']}; color: white;
                border: none; border-radius: 8px;
                padding: 0 16px; font-weight: 700; font-size: 12px;
                letter-spacing: 0.3px;
            }}
            QPushButton:hover {{ background: {_C['accent_hover']}; }}
        """)
        row0.addWidget(self.btn_new)
        row0.addStretch()
        root.addLayout(row0)

        # ── صف 2: البحث ──
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍  بحث برقم الطلب أو اسم العميل...")
        self.inp_search.setMinimumHeight(34)
        self.inp_search.setClearButtonEnabled(True)
        self.inp_search.setStyleSheet(self._INPUT_SS)
        self.inp_search.textChanged.connect(lambda: self._timer.start())
        root.addWidget(self.inp_search)

        # ── صف 3: فلاتر ──
        row2 = QHBoxLayout()
        row2.setSpacing(6)

        self.cmb_status = QComboBox()
        self.cmb_status.setMinimumHeight(28)
        self.cmb_status.setStyleSheet(self._COMBO_SS)
        self.cmb_status.addItem("كل الحالات", None)
        for k, (lbl, *_) in STATUS_LABELS.items():
            self.cmb_status.addItem(lbl, k)
        self.cmb_status.currentIndexChanged.connect(self.changed.emit)

        self.cmb_priority = QComboBox()
        self.cmb_priority.setMinimumHeight(28)
        self.cmb_priority.setStyleSheet(self._COMBO_SS)
        self.cmb_priority.addItem("كل الأولويات", None)
        for k, (icon, _) in PRIORITY_LABELS.items():
            self.cmb_priority.addItem(icon, k)
        self.cmb_priority.currentIndexChanged.connect(self.changed.emit)

        btn_reset = QPushButton("↺")
        btn_reset.setToolTip("مسح الفلاتر")
        btn_reset.setFixedSize(28, 28)
        btn_reset.setCursor(Qt.PointingHandCursor)
        btn_reset.setStyleSheet(f"""
            QPushButton {{
                background: {_C['bg_surface_2']}; color: {_C['text_muted']};
                border: 1px solid {_C['border']}; border-radius: 5px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {_C['bg_hover']};
                color: {_C['text_primary']};
            }}
        """)
        btn_reset.clicked.connect(self.reset)

        row2.addWidget(self.cmb_status, stretch=3)
        row2.addWidget(self.cmb_priority, stretch=2)
        row2.addWidget(btn_reset)
        root.addLayout(row2)

    @property
    def search_text(self) -> str:
        return self.inp_search.text().strip().lower()

    @property
    def status_filter(self):
        return self.cmb_status.currentData()

    @property
    def priority_filter(self):
        return self.cmb_priority.currentData()

    def reset(self):
        self.cmb_status.setCurrentIndex(0)
        self.cmb_priority.setCurrentIndex(0)
        self.inp_search.clear()


# ══════════════════════════════════════════════════════════
# لوحة قائمة الطلبات — محسّنة
# ══════════════════════════════════════════════════════════

class _OrdersListPanel(QWidget):
    order_selected = pyqtSignal(int)
    new_order      = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._all_rows = []
        self._build()
        self._load()

    def _build(self):
        self.setStyleSheet(f"background:{_WHITE};")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── شريط الفلتر ──
        self._filter_bar = _FilterToolbar()
        self._filter_bar.btn_new.clicked.connect(self.new_order.emit)
        self._filter_bar.changed.connect(self._apply_filter)
        root.addWidget(self._filter_bar)

        # ── جدول الطلبات ──
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["رقم الطلب", "العميل", "الحالة", "⚑", "التاريخ"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: none;
                background: {_WHITE};
                alternate-background-color: {_C['bg_surface']};
                outline: none;
            }}
            QTableWidget::item {{
                padding: 4px 10px;
                border-bottom: 1px solid {_C['border']};
                color: {_C['text_primary']};
            }}
            QTableWidget::item:selected {{
                background: {_C['accent_light']};
                color: {_C['accent_text']};
            }}
            QTableWidget::item:hover {{
                background: {_C['bg_hover']};
            }}
            QHeaderView::section {{
                background: {_C['bg_surface_2']};
                color: {_C['text_muted']};
                font-weight: 700;
                font-size: 10px;
                letter-spacing: 0.5px;
                padding: 6px 10px;
                border: none;
                border-bottom: 2px solid {_C['border_med']};
                border-right: 1px solid {_C['border']};
            }}
            QHeaderView::section:last {{
                border-right: none;
            }}
            QHeaderView::section:hover {{
                background: {_C['bg_hover']};
                color: {_C['text_primary']};
            }}
        """)

        self._status_delegate = _StatusDelegate(self.table)
        self.table.setItemDelegateForColumn(2, self._status_delegate)

        hh = self.table.horizontalHeader()

        # ── إعداد الأعمدة: Interactive بالكامل + أعمدة ثابتة العرض صغيرة ──
        hh.setSectionsMovable(False)

        # رقم الطلب — auto-fit لاحقاً
        hh.setSectionResizeMode(0, QHeaderView.Interactive)
        self.table.setColumnWidth(0, 130)

        # العميل — Stretch يأخذ باقي المساحة
        hh.setSectionResizeMode(1, QHeaderView.Stretch)

        # الحالة — Fixed
        hh.setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.setColumnWidth(2, 90)

        # الأولوية — Fixed ضيق
        hh.setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.setColumnWidth(3, 28)

        # التاريخ — Interactive مع عرض ابتدائي
        hh.setSectionResizeMode(4, QHeaderView.Interactive)
        self.table.setColumnWidth(4, 82)

        hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hh.setMinimumSectionSize(40)

        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        self.table.itemSelectionChanged.connect(self._on_select)
        self.table.doubleClicked.connect(self._on_select)
        root.addWidget(self.table, stretch=1)

        # ── حالة لا توجد نتائج ──
        self._no_results = EmptyState(
            icon="🔍",
            title="لا توجد طلبات مطابقة",
            subtitle="جرّب تعديل معايير البحث",
            style="plain",
            color="#9ca3af",
            min_height=100,
        )
        self._no_results.setStyleSheet(
            f"QFrame {{ background:{_WHITE}; border:none; }}"
        )
        self._no_results.setVisible(False)
        root.addWidget(self._no_results)

        # ── شريط الحالة ──
        self._status_bar = QLabel("")
        self._status_bar.setAlignment(Qt.AlignCenter)
        self._status_bar.setStyleSheet(f"""
            background: {_C['bg_surface_2']};
            color: {_C['text_muted']};
            padding: 5px 10px;
            font-size: 10px;
            font-weight: 600;
            border-top: 1px solid {_BORDER};
            letter-spacing: 0.3px;
        """)
        root.addWidget(self._status_bar)

    def _load(self):
        self._all_rows = fetch_all_orders(self.conn)
        self._apply_filter()

    def _apply_filter(self):
        q        = self._filter_bar.search_text
        status   = self._filter_bar.status_filter
        priority = self._filter_bar.priority_filter

        filtered = []
        for r in self._all_rows:
            if status   and r["status"]   != status:   continue
            if priority and r["priority"] != priority: continue
            if q and q not in r["order_number"].lower() \
                 and q not in r["customer_name"].lower(): continue
            filtered.append(r)

        self.table.setRowCount(0)
        has_data = bool(filtered)
        has_any  = bool(self._all_rows)

        self.table.setVisible(has_data)
        self._no_results.setVisible(not has_data and has_any)

        for row in filtered:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, ROW_HEIGHT_LARGE)

            # رقم الطلب
            num_item = make_table_item(row["order_number"], user_data=row["id"])
            bold_item(num_item)
            color_item(num_item, _C['accent'])
            self.table.setItem(r, 0, num_item)

            # العميل — tooltip بالاسم الكامل لو اتقطع
            cust_item = make_table_item(
                row["customer_name"],
                tooltip=row["customer_name"],
            )
            self.table.setItem(r, 1, cust_item)

            # الحالة — delegate يرسمها
            status_text = STATUS_LABELS.get(row["status"], (row["status"],))[0]
            s_item = make_table_item(status_text, align=Qt.AlignCenter)
            s_item.setData(Qt.UserRole + 1, row["status"])
            self.table.setItem(r, 2, s_item)

            # الأولوية
            pri_icon, pri_color = PRIORITY_LABELS.get(row["priority"], ("", "#555"))
            pri_item = make_table_item(pri_icon, align=Qt.AlignCenter)
            color_item(pri_item, pri_color)
            if row["priority"] in ("high", "urgent"):
                bold_item(pri_item)
            self.table.setItem(r, 3, pri_item)

            # التاريخ
            date_str = (row["order_date"] or "")[:10]
            date_item = muted_item(make_table_item(date_str))
            self.table.setItem(r, 4, date_item)

        cnt   = len(filtered)
        total = len(self._all_rows)
        self._status_bar.setText(
            f"{cnt} طلب" if cnt == total else f"{cnt} من {total}"
        )

        # ── auto-fit بعد ملء البيانات ──
        # رقم الطلب (0) والتاريخ (4) يتضبطوا حسب المحتوى
        # العميل (1) Stretch، الحالة (2) وأولوية (3) Fixed
        if has_data:
            auto_fit_columns(
                self.table,
                fixed_cols=[0, 4],   # auto-fit لهذين فقط
                stretch_col=1,       # العميل يفضل Stretch
                min_width=80,
                max_width=200,
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
        splitter.setHandleWidth(4)   # أوسع قليلاً → أسهل للسحب
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {_C['border']};
            }}
            QSplitter::handle:hover {{
                background: {_C['accent_mid']};
            }}
            QSplitter::handle:pressed {{
                background: {_C['accent']};
            }}
        """)

        self._list   = _OrdersListPanel(self.conn)
        self._detail = _OrderDetail(self.conn)

        splitter.addWidget(self._list)
        splitter.addWidget(self._detail)

        # ── عرض أوسع للقائمة عشان العميل يظهر كامل ──
        splitter.setSizes([480, 640])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        root.addWidget(splitter)

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