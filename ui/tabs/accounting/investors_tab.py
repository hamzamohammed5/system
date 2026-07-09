"""
ui/tabs/accounting/investors_tab.py
====================================
InvestorsTab — تبويب المستثمرين.

[تحديث v7]:
  - استخدام make_tabs من tab_builder بدل QTabWidget يدوي.
  - DualConnMixin كما هو.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PyQt5.QtCore import Qt, QTimer

from services.accounting.investors_service import InvestorsService

from .investors._investors_layout import build_investors_tabs
from .investors._investor_details import _InvestorDetails
from ui.widgets.core.conn import DualConnMixin
from ui.widgets.core.events import bus


class InvestorsTab(DualConnMixin, QWidget):
    def __init__(self, erp_conn, acc_conn, parent=None):
        super().__init__(parent)
        self._init_dual_conn(acc_conn, erp_conn)

        self._details: _InvestorDetails | None = None
        self._tabs_widget: QTabWidget | None = None
        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)

        self._migrate()
        self._build()
        bus.company_data_changed.connect(self._on_company_event)

    def _migrate(self):
        try:
            InvestorsService(self._get_erp_conn()).migrate()
        except Exception as e:
            print(f"[InvestorsTab] migrate error: {e}")

    def _on_company_event(self, company_id: int):
        if self._on_dual_company_event(company_id):
            QTimer.singleShot(0, self._rebuild)

    def _build(self):
        self._tabs_widget, self._details = build_investors_tabs(
            self._get_safe_conn(),
            self._get_erp_conn(),
            self._on_investor_selected,
        )
        self._root_layout.addWidget(self._tabs_widget)

    def _rebuild(self):
        if self._tabs_widget:
            self._root_layout.removeWidget(self._tabs_widget)
            self._tabs_widget.hide()
            self._tabs_widget.deleteLater()
            self._tabs_widget = None
            self._details = None

        self._migrate()
        self._build()

    def _on_investor_selected(self, inv_id):
        if self._details is None:
            return
        if inv_id:
            self._details.load(inv_id)
        else:
            self._details.clear()