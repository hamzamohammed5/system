"""
ui/tabs/accounting/ledger_tab.py
=========================================
LedgerTab — التبويب الرئيسي لدفتر الأستاذ.

إصلاحات (v4 — SafeConnMixin):
  - SafeConnMixin بدل conn property يدوي (متسق مع باقي التبويبات).
  - يستمع لـ bus.company_data_changed ويعيد تحميل الحسابات بـ conn محدث.
  - _AccountsPanel و _TAccountPanel يستخدمان SafeConnMixin كمان.
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
)
from PyQt5.QtCore import Qt

from .ledger.ledger_accounts_panel import _AccountsPanel
from .ledger.ledger_t_account import _TAccountPanel
from ui.tabs.accounting.safe_conn_mixin import SafeConnMixin
from ui.events import bus


class LedgerTab(SafeConnMixin, QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self._init_safe_conn(conn, "accounting")
        self._company_id = self._get_company_id()
        self._build()
        bus.company_data_changed.connect(self._on_company_event)

    def _on_company_event(self, company_id: int):
        if self._on_company_event_safe(company_id):
            self._accounts_panel._refresh_accounts()
            self._t_panel.clear()

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet("""
            QSplitter::handle { background: #e0e0e0; }
            QSplitter::handle:hover { background: #bbdefb; }
        """)

        left = QWidget()
        ll   = QVBoxLayout(left)
        ll.setContentsMargins(10, 10, 6, 10)
        ll.setSpacing(0)
        self._accounts_panel = _AccountsPanel(
            self._get_safe_conn(),
            on_select=self._on_account_selected
        )
        ll.addWidget(self._accounts_panel)
        splitter.addWidget(left)

        right = QWidget()
        rl    = QVBoxLayout(right)
        rl.setContentsMargins(6, 10, 10, 10)
        rl.setSpacing(0)
        self._t_panel = _TAccountPanel(self._get_safe_conn())
        rl.addWidget(self._t_panel)
        splitter.addWidget(right)

        splitter.setSizes([240, 760])
        root.addWidget(splitter)

    def _on_account_selected(self, acc_id: int):
        self._t_panel.load(self._get_safe_conn(), acc_id)