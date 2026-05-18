"""
ui/tabs/orders/orders/_orders_list_panel.py
============================================
لوحة قائمة الطلبات — ترث من BaseListPanel.

✅ الأعمدة Interactive — المستخدم يقدر يحرك عرضها بحرية
✅ الـ splitter يتحرك بحرية بدون قيود MAX_W
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
    order_selected = pyqtSignal(int)
    new_order      = pyqtSignal()

    COLUMNS     = ["رقم الطلب", "العميل", "الحالة", "⚑", "التاريخ"]
    STRETCH_COL = -1
    # ✅ عرض ابتدائي مناسب — Interactive يسمح بالتعديل بعدين
    COL_WIDTHS  = {0: 130, 1: 150, 2: 100, 3: 32, 4: 90}
    MIN_W       = 280
    MAX_W       = 16777215   # ✅ بلا حد — الـ splitter يتحرك بحرية
    EMPTY_ICON  = "📋"
    EMPTY_TITLE = "لا توجد طلبات"

    def __init__(self, conn, parent=None):
        super().__init__(conn=conn, parent=parent)
        self.item_selected.connect(self.order_selected.emit)
        self._status_delegate = _StatusDelegate(self.table)
        self.table.setItemDelegateForColumn(2, self._status_delegate)

    # ══════════════════════════════════════════════════════
    # toolbar مخصص
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

    def _auto_resize(self):
        """
        ✅ الأعمدة Interactive — المستخدم يقدر يحرك عرضها.
        ✅ الـ panel له حد أدنى فقط — الـ splitter يتحرك بحرية.
        """
        from PyQt5.QtWidgets import QHeaderView
        from ui.widgets.shared.table_utils import auto_fit_columns

        # ضبط الأعمدة على عرضها المناسب (Interactive)
        auto_fit_columns(
            self.table,
            fixed_cols=list(self.COL_WIDTHS.keys()),
            stretch_col=self.STRETCH_COL,
            min_width=30, max_width=300,
        )

        # ✅ حد أدنى فقط — بدون MAX_W يقيد الحركة
        self.setMinimumWidth(self.MIN_W)
        self.setMaximumWidth(16777215)

    # ══════════════════════════════════════════════════════
    # API
    # ══════════════════════════════════════════════════════

    def select_order(self, order_id: int):
        self.select_item(order_id)