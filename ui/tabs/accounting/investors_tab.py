"""
ui/tabs/accounting/investors_tab.py
====================================
InvestorsTab — تبويب المستثمرين.

[تحديث v8]:
  - RebuildMixin لتوحيد نمط _rebuild.
  - DualConnMixin كما هو.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PyQt5.QtCore import QTimer

from db.inventory.investors_repo import _migrate_investors

from .investors._investors_layout import build_investors_tabs
from .investors._investor_details import _InvestorDetails
from ui.widgets.shared.safe_conn_mixin import DualConnMixin
from ui.widgets.shared.rebuild_mixin import RebuildMixin
from ui.events import bus


class InvestorsTab(DualConnMixin, RebuildMixin, QWidget):
    def __init__(self, erp_conn, acc_conn, parent=None):
        super().__init__(parent)
        self._init_dual_conn(acc_conn, erp_conn)

        self._details: _InvestorDetails | None = None
        self._current_widget: QTabWidget | None = None
        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)

        self._migrate()
        self._build()
        bus.company_data_changed.connect(self._on_company_event)

    def _migrate(self):
        try:
            _migrate_investors(self._get_erp_conn())
        except Exception as e:
            print(f"[InvestorsTab] migrate error: {e}")

    def _on_company_event(self, company_id: int):
        if self._on_dual_company_event(company_id):
            QTimer.singleShot(0, self._rebuild)

    def _build(self):
        tabs_widget, self._details = build_investors_tabs(
            self._get_safe_conn(),
            self._get_erp_conn(),
            self._on_investor_selected,
        )
        self._replace_widget(tabs_widget)

    def _rebuild(self):
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