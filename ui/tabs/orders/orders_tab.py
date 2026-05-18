"""
ui/tabs/orders/orders_tab.py  — نسخة UX v4 مع SmartSplitter
=============================
إصلاحات:
  - SmartSplitter: الـ list panel بيتضبط تلقائياً على عرض الجدول
  - لا فراغ زائد في القائمة
  - دعم double-click على الـ splitter handle للـ auto-fit
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout
from PyQt5.QtCore    import Qt

from ui.tabs.orders._order_detail import _OrderDetail
from ui.app_settings import _C
from ui.widgets.shared.splitter_utils import SmartSplitter

from .orders._orders_list_panel import _OrdersListPanel

_BG     = "#f8f9fb"
_WHITE  = "#ffffff"
_BLUE   = _C['accent']
_BORDER = _C['border']


class OrdersTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── SmartSplitter بدل QSplitter العادي ──
        self._splitter = SmartSplitter(Qt.Horizontal)
        self._splitter.setCollapsible(0, False)
        self._splitter.setCollapsible(1, False)

        self._list   = _OrdersListPanel(self.conn)
        self._detail = _OrderDetail(self.conn)

        self._splitter.addWidget(self._list)
        self._splitter.addWidget(self._detail)

        # ربط الـ SmartSplitter بالجدول لـ auto-fit
        self._splitter.set_list_widget(
            self._list,
            list_table=self._list.table,
            min_w=280,
            max_w=560,
        )

        # عرض مبدئي معقول — سيتضبط بعد تحميل البيانات
        self._splitter.setSizes([360, 760])

        root.addWidget(self._splitter)

        # ── الـ signals ──
        self._list.order_selected.connect(self._on_order_selected)
        self._list.new_order.connect(self._on_new_order)
        self._detail.saved.connect(self._on_saved)
        self._detail.deleted.connect(self._on_deleted)
        self._detail.status_changed.connect(self._on_status_changed)

        # ── auto-fit بعد أول تحميل (تأخير بسيط للـ layout) ──
        self._list._filter_bar.changed.connect(self._fit_splitter)
        self._fit_splitter_delayed()

    def _fit_splitter(self):
        """يضبط الـ splitter فوراً."""
        self._splitter.fit_now()

    def _fit_splitter_delayed(self, delay_ms: int = 80):
        """يضبط الـ splitter بعد اكتمال الـ layout."""
        self._splitter.fit_delayed(delay_ms)

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

    def refresh(self):
        self._list.refresh()
        self._fit_splitter_delayed()