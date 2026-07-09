"""
ui/tabs/accounting/ledger/ledger_accounts_panel.py
===================================================
_AccountsPanel — قائمة الحسابات في دفتر الأستاذ.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QHeaderView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from services.accounting.accounts_service import AccountsService
from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import ACCOUNTS_PANEL_COL_CODE_W, ACCOUNTS_PANEL_COL_BAL_W, ACCOUNTS_PANEL_TYPE_FILTER_MARGIN, MARGIN_ZERO, SPACING_ZERO

from ui.widgets.components.headers_list import ListHeader, StatusBar
from ui.widgets.theme.layout_styles      import tree_style
from ui.tabs.accounting.accounts_combo_widget import AccountTypeFilter
from ui.tabs.accounting.helpers import TYPE_COLORS


class _AccountsPanel(SafeConnMixin, QWidget, WidgetMixin):
    def __init__(self, conn, on_select, parent=None):
        super().__init__(parent)
        self._init_safe_conn(conn, "accounting")
        self._init_widget_mixin(lang=False, data=False)
        self._on_select = on_select
        self._all       = []
        self._build()
        self._refresh_accounts()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(*MARGIN_ZERO)
        root.setSpacing(SPACING_ZERO)

        self._header = ListHeader(
            title=tr("ledger_accounts_title"),
            show_search=True,
            search_placeholder=tr("account_search_placeholder"),
        )
        self._header.search_changed.connect(self._filter_accounts)
        root.addWidget(self._header)

        self._type_filter = AccountTypeFilter(
            AccountsService(self._get_safe_conn()).get_type_labels_map(),
            include_all=True,
        )
        self._type_filter.setContentsMargins(*ACCOUNTS_PANEL_TYPE_FILTER_MARGIN)
        self._type_filter.type_changed.connect(self._filter_accounts)
        root.addWidget(self._type_filter)

        self.lst = QTreeWidget()
        self.lst.setHeaderLabels([tr("code"), tr("name"), tr("balance")])
        hh = self.lst.header()
        hh.setSectionResizeMode(0, QHeaderView.Interactive)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Interactive)
        self.lst.setColumnWidth(0, ACCOUNTS_PANEL_COL_CODE_W)
        self.lst.setColumnWidth(2, ACCOUNTS_PANEL_COL_BAL_W)
        self.lst.setAlternatingRowColors(True)
        self.lst.setStyleSheet(tree_style())
        self.lst.itemSelectionChanged.connect(self._on_selected)
        root.addWidget(self.lst, stretch=1)

        self._status = StatusBar()
        root.addWidget(self._status)

    def _refresh_accounts(self):
        try:
            self._all = AccountsService(self._get_safe_conn()).list_all_accounts()
        except Exception as e:
            print(f"[_AccountsPanel] _refresh_accounts error: {e}")
            self._all = []
        self._filter_accounts()

    def _filter_accounts(self, _=None):
        from ui.theme import _C
        q         = self._header.search_text()
        type_filt = self._type_filter.current_type()

        self.lst.clear()
        count = 0

        for acc in self._all:
            if not acc["is_leaf"]:
                continue
            if type_filt and acc["type"] != type_filt:
                continue
            if q and q not in acc["name"].lower() and q not in acc["code"].lower():
                continue

            bal = acc["balance"] if acc["balance"] is not None else 0.0

            item = QTreeWidgetItem()
            item.setText(0, acc["code"])
            item.setText(1, acc["name"])
            item.setText(2, f"{bal:,.2f}")
            item.setData(0, Qt.UserRole, acc["id"])

            color = TYPE_COLORS.get(acc["type"], _C["text_primary"])
            item.setForeground(0, QColor(color))
            item.setToolTip(1, f"{acc['code']} — {acc['name']}")

            if bal < 0:
                item.setForeground(2, QColor(_C["acc_type_liability"]))
            elif bal > 0:
                item.setForeground(2, QColor(_C["acc_type_capital"]))

            self.lst.addTopLevelItem(item)
            count += 1

        total = sum(1 for a in self._all if a["is_leaf"])
        self._status.set_count(count, total)

    def _on_selected(self):
        items = self.lst.selectedItems()
        if not items:
            return
        acc_id = items[0].data(0, Qt.UserRole)
        if acc_id:
            self._on_select(acc_id)