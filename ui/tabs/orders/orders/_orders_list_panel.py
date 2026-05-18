"""
ui/tabs/orders/orders/_orders_list_panel.py
============================================
لوحة قائمة الطلبات — ترث من BaseListPanel.
عرض ثابت على المحتوى، لا يتمدد مع النافذة، بدون horizontal scroll.
"""

from PyQt5.QtWidgets import QSizePolicy, QVBoxLayout
from PyQt5.QtCore    import Qt, pyqtSignal

from db.orders.orders_repo import fetch_all_orders

from ui.widgets.shared.base_list_panel import BaseListPanel
from ui.widgets.shared.table_utils import (
    make_table_item, color_item, bold_item, muted_item,
    calc_table_width,
)
from ui.app_settings import _C

from ._filter_toolbar  import _FilterToolbar
from ._status_delegate import _StatusDelegate

STATUS_LABELS = {
    "pending":     ("⏳ انتظار",  "#b45309"),
    "confirmed":   ("✅ مؤكد",    "#1d4ed8"),
    "in_progress": ("🔧 تنفيذ",  "#6d28d9"),
    "ready":       ("📦 جاهز",   "#065f46"),
    "delivered":   ("🚚 مُسلَّم", "#374151"),
    "cancelled":   ("❌ ملغي",   "#991b1b"),
    "on_hold":     ("⏸ معلق",   "#9a3412"),
}
PRIORITY_LABELS = {
    "low":    ("⬇", "#9ca3af"),
    "normal": ("➡", "#6b7280"),
    "high":   ("⬆", "#f59e0b"),
    "urgent": ("🔴","#ef4444"),
}


class _OrdersListPanel(BaseListPanel):
    order_selected = pyqtSignal(int)   # alias لـ item_selected
    new_order      = pyqtSignal()

    COLUMNS     = ["رقم الطلب", "العميل", "الحالة", "⚑", "التاريخ"]
    STRETCH_COL = -1
    COL_WIDTHS  = {0: 130, 1: 150, 2: 95, 3: 32, 4: 90}
    MIN_W       = 280
    MAX_W       = 560
    EMPTY_ICON  = "📋"
    EMPTY_TITLE = "لا توجد طلبات"

    def __init__(self, conn, parent=None):
        super().__init__(conn=conn, parent=parent)
        # ربط item_selected بـ order_selected
        self.item_selected.connect(self.order_selected.emit)
        # تطبيق delegate على عمود الحالة
        self._status_delegate = _StatusDelegate(self.table)
        self.table.setItemDelegateForColumn(2, self._status_delegate)

    # ══════════════════════════════════════════════════════
    # toolbar مخصص — يستبدل الافتراضي بـ _FilterToolbar
    # ══════════════════════════════════════════════════════

    def _build_toolbar(self, lay: QVBoxLayout):
        self._filter_bar = _FilterToolbar()
        self._filter_bar.btn_new.clicked.connect(self.new_order.emit)
        self._filter_bar.changed.connect(self._apply_filter)
        lay.addWidget(self._filter_bar)

    # ══════════════════════════════════════════════════════
    # data
    # ══════════════════════════════════════════════════════

    def _load_rows(self) -> list:
        return fetch_all_orders(self.conn)

    def _match_filter(self, row, q: str) -> bool:
        status   = self._filter_bar.status_filter
        priority = self._filter_bar.priority_filter
        if status   and row["status"]   != status:   return False
        if priority and row["priority"] != priority: return False
        if q and q not in row["order_number"].lower() \
             and q not in row["customer_name"].lower():
            return False
        return True

    def _fill_row(self, table, r, row):
        num_item = make_table_item(row["order_number"], user_data=row["id"])
        bold_item(num_item)
        color_item(num_item, _C['accent'])
        table.setItem(r, 0, num_item)

        cust_item = make_table_item(row["customer_name"],
                                    tooltip=row["customer_name"])
        table.setItem(r, 1, cust_item)

        status_text = STATUS_LABELS.get(row["status"], (row["status"],))[0]
        s_item = make_table_item(status_text, align=Qt.AlignCenter)
        s_item.setData(Qt.UserRole + 1, row["status"])
        table.setItem(r, 2, s_item)

        pri_icon, pri_color = PRIORITY_LABELS.get(row["priority"], ("", "#555"))
        pri_item = make_table_item(pri_icon, align=Qt.AlignCenter)
        color_item(pri_item, pri_color)
        if row["priority"] in ("high", "urgent"):
            bold_item(pri_item)
        table.setItem(r, 3, pri_item)

        date_item = muted_item(make_table_item((row["order_date"] or "")[:10]))
        table.setItem(r, 4, date_item)

    # ══════════════════════════════════════════════════════
    # auto-resize مخصص — يضبط عمود الأولوية بحد أدنى
    # ══════════════════════════════════════════════════════

    def _auto_resize(self):
        self.table.resizeColumnsToContents()
        if self.table.columnWidth(3) < 32:
            self.table.setColumnWidth(3, 32)
        w = calc_table_width(self.table, padding=12)
        w = max(self.MIN_W, min(w, self.MAX_W))
        self.setFixedWidth(w)

    # ══════════════════════════════════════════════════════
    # API
    # ══════════════════════════════════════════════════════

    def select_order(self, order_id: int):
        self.select_item(order_id)