"""
ui/tabs/orders/orders/_orders_list_panel.py 
=============================
"""
from PyQt5.QtWidgets import (
    QTableWidget, QWidget, QVBoxLayout,
    QLabel, QHeaderView,
    QAbstractItemView
)

from PyQt5.QtCore import Qt, pyqtSignal

from db.orders.orders_repo import (
    fetch_all_orders
)

from ui.widgets.shared.table_utils import (
    make_table_item, color_item, bold_item, muted_item,
    ROW_HEIGHT_LARGE,
)
from ui.app_settings import _C
from ui.widgets.shared.panels import EmptyState

from ._filter_toolbar import _FilterToolbar
from ._status_delegate import _StatusDelegate

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

_WHITE  = "#ffffff"
_BORDER = _C['border']


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

        # ── كل الأعمدة Interactive — بعرض مبدئي مناسب ──
        hh.setSectionsMovable(False)
        hh.setStretchLastSection(False)

        for col in range(5):
            hh.setSectionResizeMode(col, QHeaderView.Interactive)

        self.table.setColumnWidth(0, 130)   # رقم الطلب
        self.table.setColumnWidth(1, 150)   # العميل
        self.table.setColumnWidth(2, 95)    # الحالة
        self.table.setColumnWidth(3, 32)    # الأولوية
        self.table.setColumnWidth(4, 90)    # التاريخ

        hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hh.setMinimumSectionSize(30)

        # ── scroll أفقي ورأسي ──
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

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

            # العميل — tooltip بالاسم الكامل
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

        # ── resizeColumnsToContents بعد ملء البيانات ──
        # كل الأعمدة تتضبط على حجم محتواها الفعلي
        if has_data:
            self.table.resizeColumnsToContents()
            # حد أدنى لعمود الأولوية لأن أيقونته صغيرة
            if self.table.columnWidth(3) < 32:
                self.table.setColumnWidth(3, 32)

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
