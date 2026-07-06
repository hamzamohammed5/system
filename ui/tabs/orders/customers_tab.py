"""
ui/tabs/orders/customers_tab.py
================================
تبويب العملاء — يستخدم BaseSection.
"""

from PyQt5.QtCore import QTimer

from ui.tabs.orders._customer_form                   import _CustomerForm
from ui.tabs.orders.customers.customers_list_panel   import CustomersListPanel
from ui.tabs.orders.customers.customer_detail_panel  import CustomerDetailPanel
from ui.widgets.base.section                         import BaseSection
from ui.constants import CUSTOMERS_LIST_MIN_W, ORDERS_SPLITTER_FIT_DELAY_MS


class CustomersTab(BaseSection):

    LIST_MIN_W = CUSTOMERS_LIST_MIN_W

    def __init__(self, conn, parent=None):
        self._conn = conn
        super().__init__(conn=conn, parent=parent)
        self._list.refresh()  # [إصلاح] القائمة كانت فاضية عند فتح التاب لأول مرة

    # [إصلاح] BaseSection لا توفر _fit_splitter_delayed رغم أن هذا
    # الملف كان يستدعيها في _on_edited/_on_saved، مما كان يسبب
    # AttributeError عند أي حفظ أو تعديل لعميل. BaseSection توفر
    # فقط _apply_sizes() (بدون تأخير قابل للتخصيص) لضبط أحجام
    # الـ splitter لأول مرة عبر QTimer.singleShot. أُضيفت هنا نسخة
    # محلية تعيد استخدام self._apply_sizes الموروثة فعليًا، بدل تكرار
    # منطق ضبط الأحجام من الصفر.
    def _fit_splitter_delayed(self, delay_ms: int):
        QTimer.singleShot(delay_ms, self._apply_sizes)

    def _create_list(self):
        return CustomersListPanel(self._conn)

    def _create_detail(self):
        return CustomerDetailPanel(self._conn)

    def _connect_signals(self):
        self._list.customer_selected.connect(self._detail.load_customer)
        self._list.new_customer.connect(self._new_customer)
        self._detail.edited.connect(self._on_edited)
        self._detail.deleted.connect(self._list.refresh)

    # ══════════════════════════════════════════════════════
    # handlers
    # ══════════════════════════════════════════════════════

    def _on_edited(self, cid: int):
        self._list.refresh()
        self._fit_splitter_delayed(ORDERS_SPLITTER_FIT_DELAY_MS)

    def _new_customer(self):
        dlg = _CustomerForm(self._conn, parent=self)
        dlg.saved.connect(self._on_saved)
        dlg.exec_()

    def _on_saved(self, cid: int):
        self._list.refresh()
        self._list.select_customer(cid)
        self._detail.load_customer(cid)
        self._fit_splitter_delayed(ORDERS_SPLITTER_FIT_DELAY_MS)