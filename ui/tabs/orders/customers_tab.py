"""
ui/tabs/orders/customers_tab.py
================================
تبويب العملاء — يستورد من customers/ فقط.
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout
from PyQt5.QtCore    import Qt

from ui.tabs.orders._customer_form import _CustomerForm
from ui.tabs.orders.customers.customers_list_panel import CustomersListPanel
from ui.tabs.orders.customers.customer_detail_panel import CustomerDetailPanel
from ui.widgets.shared.splitter_utils import SmartSplitter


class CustomersTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._splitter = SmartSplitter(Qt.Horizontal)

        self._list   = CustomersListPanel(self.conn)
        self._detail = CustomerDetailPanel(self.conn)

        self._splitter.addWidget(self._list)
        self._splitter.addWidget(self._detail)
        self._splitter.setCollapsible(0, False)
        self._splitter.setCollapsible(1, False)

        self._splitter.set_list_widget(
            self._list,
            list_table=self._list.table,
            min_w=300,
            max_w=560,
        )
        self._splitter.setSizes([380, 720])

        root.addWidget(self._splitter)

        self._list.customer_selected.connect(self._detail.load_customer)
        self._list.new_customer.connect(self._new_customer)
        self._detail.edited.connect(self._on_edited)
        self._detail.deleted.connect(self._list.refresh)

        self._splitter.fit_delayed(80)

    def _on_edited(self, cid: int):
        self._list.refresh()
        self._splitter.fit_delayed(50)

    def _new_customer(self):
        dlg = _CustomerForm(self.conn, parent=self)
        dlg.saved.connect(self._on_saved)
        dlg.exec_()

    def _on_saved(self, cid: int):
        self._list.refresh()
        self._list.select_customer(cid)
        self._detail.load_customer(cid)
        self._splitter.fit_delayed(50)

    def refresh(self):
        self._list.refresh()
        self._splitter.fit_delayed(50)