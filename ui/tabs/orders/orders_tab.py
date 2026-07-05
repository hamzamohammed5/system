"""
ui/tabs/orders/orders_tab.py
=============================
تبويب الطلبات — يستخدم BaseSection.
"""

from ui.tabs.orders._order_detail                    import _OrderDetail
from ui.tabs.orders.orders._orders_list_panel        import _OrdersListPanel
from ui.widgets.base.section                         import BaseSection
from ui.constants import ORDERS_LIST_MIN_W


class OrdersTab(BaseSection):

    LIST_MIN_W = ORDERS_LIST_MIN_W

    def __init__(self, conn, parent=None):
        self._conn = conn
        super().__init__(conn=conn, parent=parent)

    def _create_list(self):
        return _OrdersListPanel(self._conn)

    def _create_detail(self):
        return _OrderDetail(self._conn)

    def _connect_signals(self):
        self._list.order_selected.connect(self._on_order_selected)
        self._list.new_order.connect(self._on_new_order)
        self._detail.saved.connect(self._on_saved)
        self._detail.deleted.connect(self._on_deleted)
        self._detail.status_changed.connect(self._on_status_changed)
        # لما الفلتر يتغير، نضبط عرض الـ splitter
        self._list._filter_bar.changed.connect(self._fit_splitter_delayed)

    # ══════════════════════════════════════════════════════
    # handlers
    # ══════════════════════════════════════════════════════

    def _on_order_selected(self, order_id: int):
        self._detail.load_order(order_id)

    def _on_new_order(self):
        self._detail.new_order()

    def _on_saved(self, order_id: int):
        self._list.refresh()
        self._list.select_order(order_id)
        self._fit_splitter_delayed()

    def _on_deleted(self):
        self._list.refresh()
        self._detail.clear()
        self._fit_splitter_delayed()

    def _on_status_changed(self, order_id: int):
        self._list.refresh()
        self._list.select_order(order_id)
        self._detail.load_order(order_id)

    def _fit_splitter_delayed(self, *args):
        """wrapper يتجاهل أي arguments من الـ signals."""
        super()._fit_splitter_delayed()