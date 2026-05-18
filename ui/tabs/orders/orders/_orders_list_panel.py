"""
ui/tabs/orders/orders/_orders_list_panel.py
============================================
لوحة قائمة الطلبات — جدول بعرض ثابت، مش بيتمدد مع النافذة.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHeaderView,
    QAbstractItemView, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal

from db.orders.orders_repo import fetch_all_orders

from ui.widgets.shared.table_utils import (
    make_table_item, color_item, bold_item, muted_item,
    auto_fit_columns, calc_table_width, ROW_HEIGHT_LARGE,
    make_list_table,
)
from ui.app_settings import _C
from ui.widgets.shared.panels import EmptyState

from ._filter_toolbar   import _FilterToolbar
from ._status_delegate  import _StatusDelegate

# ── ثوابت الحالة ──
STATUS_LABELS = {
    "pending":     ("⏳ انتظار",   "#b45309"),
    "confirmed":   ("✅ مؤكد",     "#1d4ed8"),
    "in_progress": ("🔧 تنفيذ",   "#6d28d9"),
    "ready":       ("📦 جاهز",    "#065f46"),
    "delivered":   ("🚚 مُسلَّم",  "#374151"),
    "cancelled":   ("❌ ملغي",    "#991b1b"),
    "on_hold":     ("⏸ معلق",    "#9a3412"),
}

PRIORITY_LABELS = {
    "low":    ("⬇",  "#9ca3af"),
    "normal": ("➡",  "#6b7280"),
    "high":   ("⬆",  "#f59e0b"),
    "urgent": ("🔴", "#ef4444"),
}

_WHITE  = "#ffffff"
_BORDER = _C['border']


class _OrdersListPanel(QWidget):
    order_selected = pyqtSignal(int)
    new_order      = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._all_rows = []
        # عرض ثابت — مش بيتمدد
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
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

        # ── الجدول — عرض ثابت ──
        self.table = make_list_table(
            columns=["رقم الطلب", "العميل", "الحالة", "⚑", "التاريخ"],
            stretch_col=-1,   # مفيش stretch — كل الأعمدة interactive
            col_widths={0: 130, 1: 150, 2: 95, 3: 32, 4: 90},
        )
        # لا نسمح بـ horizontal scroll — العرض مضبوط
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._status_delegate = _StatusDelegate(self.table)
        self.table.setItemDelegateForColumn(2, self._status_delegate)

        self.table.itemSelectionChanged.connect(self._on_select)
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

            # العميل
            cust_item = make_table_item(row["customer_name"],
                                        tooltip=row["customer_name"])
            self.table.setItem(r, 1, cust_item)

            # الحالة
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
            date_str  = (row["order_date"] or "")[:10]
            date_item = muted_item(make_table_item(date_str))
            self.table.setItem(r, 4, date_item)

        cnt   = len(filtered)
        total = len(self._all_rows)
        self._status_bar.setText(
            f"{cnt} طلب" if cnt == total else f"{cnt} من {total}"
        )

        if has_data:
            # ضبط عرض الأعمدة على المحتوى
            self.table.resizeColumnsToContents()
            if self.table.columnWidth(3) < 32:
                self.table.setColumnWidth(3, 32)

            # ضبط عرض الـ panel على قد الجدول — الـ horizontal scroll يختفي
            w = calc_table_width(self.table, padding=12)
            self.setFixedWidth(max(280, min(w, 560)))

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