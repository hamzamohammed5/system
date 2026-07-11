"""
ui/tabs/accounting/accounts_tree.py
=====================================
AccountsTreePanel — شجرة الحسابات مع فورم الإضافة والتعديل.

[تحسين v4]:
  - استخدام SectionHeader + _make_btn من panels بدل بناء يدوي.
  - استخدام get_splitter_style من panels.
  - استخدام confirm_delete من panels.
  - SafeConnMixin كما هو.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QSplitter,
    QLabel, QMessageBox,
    QHeaderView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor, QFont

from services.accounting.accounts_service import AccountsService
from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.widgets.components.headers_page import SectionHeader
from ui.widgets.components.button import make_btn as _make_btn
from ui.widgets.theme.table_styles import splitter_style as get_splitter_style
from ui.widgets.theme.layout_styles import tree_style as get_tree_style
from ui.widgets.dialogs.confirm import confirm_delete

from ui.widgets.core.i18n import tr
from ui.font import FS_MD
from ui.widgets.dialogs.message import msg_info, msg_warning, msg_critical
from .tree._tree_nodes import (
    rows_to_tree, filter_by_group, add_acc_nodes
)

from .tree._tree_headers import add_type_header
from .tree._account_form  import _AccountForm
from .tree._group_filter  import _GroupFilterCombo
from ui.constants import (
    SPLITTER_HANDLE_W,
    ACCOUNTS_TREE_COL_CODE_W, ACCOUNTS_TREE_COL_BAL_W,
    ACCOUNTS_TREE_SPLITTER_L, ACCOUNTS_TREE_SPLITTER_R,
    ACCOUNTS_TREE_FILTER_MIN_H,
    ACCOUNTS_TREE_LEFT_MARGIN_L, ACCOUNTS_TREE_LEFT_MARGIN_T,
    ACCOUNTS_TREE_LEFT_MARGIN_R, ACCOUNTS_TREE_LEFT_MARGIN_B,
    ACCOUNTS_TREE_LEFT_SPACING, ACCOUNTS_TREE_EXPAND_DEPTH,
)


class AccountsTreePanel(SafeConnMixin, QWidget, WidgetMixin):
    def __init__(self, conn, acc_types: list, title: str, parent=None):
        super().__init__(parent)
        self._init_safe_conn(conn, "accounting")
        self.acc_types   = acc_types
        self.title       = title
        self._loading    = False
        self._company_id = self._get_company_id()
        self._build()
        self._init_widget_mixin(theme=False, font=False, lang=False, data=True)
        self._load()

    def _refresh_data(self, company_id=None):
        if self._on_company_event_safe(company_id):
            self._load()

    def _build(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(SPLITTER_HANDLE_W)
        splitter.setStyleSheet(get_splitter_style())

        left = QWidget()
        ll   = QVBoxLayout(left)
        ll.setContentsMargins(ACCOUNTS_TREE_LEFT_MARGIN_L, ACCOUNTS_TREE_LEFT_MARGIN_T,
                              ACCOUNTS_TREE_LEFT_MARGIN_R, ACCOUNTS_TREE_LEFT_MARGIN_B)
        ll.setSpacing(ACCOUNTS_TREE_LEFT_SPACING)

        # ── هيدر القسم ──
        hdr = SectionHeader(self.title)
        ll.addWidget(hdr)

        # ── فلتر التصنيف ──
        filter_row = QHBoxLayout()
        lbl_tag = QLabel(tr("group_tag_icon"))
        lbl_tag.setStyleSheet("background:transparent; border:none;")
        self.cmb_group_filter = _GroupFilterCombo(self._get_safe_conn(), self.acc_types)
        self.cmb_group_filter.setMinimumHeight(ACCOUNTS_TREE_FILTER_MIN_H)
        self.cmb_group_filter.currentIndexChanged.connect(self._on_filter_changed)
        filter_row.addWidget(lbl_tag)
        filter_row.addWidget(self.cmb_group_filter, stretch=1)
        ll.addLayout(filter_row)

        # ── شجرة الحسابات ──
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([tr("accounts_col"), tr("account_name_col"), tr("balance")])
        hh = self.tree.header()
        hh.setSectionResizeMode(0, QHeaderView.Interactive)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Interactive)
        self.tree.setColumnWidth(0, ACCOUNTS_TREE_COL_CODE_W)
        self.tree.setColumnWidth(2, ACCOUNTS_TREE_COL_BAL_W)
        self.tree.setAlternatingRowColors(True)
        self.tree.setStyleSheet(get_tree_style())
        ll.addWidget(self.tree, stretch=1)

        # ── أزرار التعديل والحذف ──
        btn_row  = QHBoxLayout()
        btn_edit = _make_btn(tr("btn_edit"), "normal")
        btn_del  = _make_btn(tr("btn_delete"),  "danger")
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        btn_row.addWidget(btn_edit)
        btn_row.addWidget(btn_del)
        btn_row.addStretch()
        ll.addLayout(btn_row)

        splitter.addWidget(left)

        self._form = _AccountForm(self._get_safe_conn(), self.acc_types)
        splitter.addWidget(self._form)
        splitter.setSizes([ACCOUNTS_TREE_SPLITTER_L, ACCOUNTS_TREE_SPLITTER_R])

        main_layout.addWidget(splitter)

    def _on_filter_changed(self):
        if self._loading:
            return
        self._build_tree()

    def _load(self):
        if self._loading:
            return
        self._loading = True
        try:
            conn = self._get_safe_conn()
            self.cmb_group_filter.refresh(conn=conn)
            self._form.refresh_group_combos(conn=conn)
            self._build_tree()
        finally:
            self._loading = False

    def _build_tree(self):
        from ui.theme import _C
        self.tree.clear()
        conn       = self._get_safe_conn()
        gid_filter = self.cmb_group_filter.currentData()

        all_nodes_by_type: dict[str, list] = {}
        svc = AccountsService(conn)
        for acc_type in self.acc_types:
            try:
                rows = svc.list_all_accounts(acc_type)
            except Exception as e:
                print(f"[AccountsTreePanel] fetch error ({acc_type}): {e}")
                rows = []
            if not rows:
                continue
            nodes = rows_to_tree(rows)
            if gid_filter is not None:
                nodes = filter_by_group(conn, nodes, gid_filter)
            if nodes:
                all_nodes_by_type[acc_type] = nodes

        if not all_nodes_by_type:
            empty = QTreeWidgetItem()
            empty.setText(1, tr("no_accounts_msg"))
            empty.setForeground(1, QColor(_C["text_muted"]))
            self.tree.addTopLevelItem(empty)
            return

        non_equity    = [t for t in self.acc_types if t not in svc.get_equity_types()]
        equity_present = [
            t for t in self.acc_types
            if t in svc.get_equity_types() and t in all_nodes_by_type
        ]

        for acc_type in non_equity:
            if acc_type not in all_nodes_by_type:
                continue
            add_type_header(self.tree, acc_type, all_nodes_by_type[acc_type], conn)

        if equity_present:
            equity_item = QTreeWidgetItem()
            equity_item.setText(0, "")
            equity_item.setText(1, tr("owners_equity"))
            equity_item.setText(2, "")
            equity_item.setFlags(equity_item.flags() & ~Qt.ItemIsSelectable)
            f = equity_item.font(1)
            f.setBold(True)
            f.setPointSize(FS_MD)
            equity_item.setFont(1, f)
            equity_item.setForeground(1, QColor(_C["investor_capital_text"]))
            equity_item.setBackground(0, QColor(_C["success_bg"]))
            equity_item.setBackground(1, QColor(_C["success_bg"]))
            equity_item.setBackground(2, QColor(_C["success_bg"]))
            self.tree.addTopLevelItem(equity_item)

            for acc_type in ["capital", "drawings", "revenue", "expense"]:
                if acc_type not in equity_present:
                    continue
                nodes = all_nodes_by_type[acc_type]
                from ui.tabs.accounting.helpers import TYPE_COLORS
                sub_item = QTreeWidgetItem()
                sub_item.setText(0, "")
                sub_item.setText(1, tr("accounts_tree_sub_type_wrap", name=svc.get_type_labels_map().get(acc_type, acc_type)))
                sub_item.setFlags(sub_item.flags() & ~Qt.ItemIsSelectable)
                sf = sub_item.font(1)
                sf.setBold(True)
                sub_item.setFont(1, sf)
                sub_item.setForeground(1, QColor(TYPE_COLORS.get(acc_type, _C["investor_capital_text"])))
                equity_item.addChild(sub_item)
                add_acc_nodes(conn, self.tree, nodes, sub_item)
                sub_item.setExpanded(True)

            equity_item.setExpanded(True)

        self.tree.expandToDepth(ACCOUNTS_TREE_EXPAND_DEPTH)

    def _selected_id(self):
        items = self.tree.selectedItems()
        if not items:
            return None
        return items[0].data(0, Qt.UserRole)

    def _edit(self):
        aid = self._selected_id()
        if not aid:
            msg_info(self, tr("warning"), tr("select_item_first"))
            return
        self._form.load_for_edit(aid)

    def _delete(self):
        aid = self._selected_id()
        if not aid:
            return
        conn = self._get_safe_conn()
        svc  = AccountsService(conn)
        preview = svc.get_delete_preview(aid)
        if not preview:
            return

        if preview.has_lines:
            msg_warning(
                self, tr("warning"),
                tr("account_has_lines_msg", name=preview.account_name, count=preview.lines_count)
            )
            return

        extra = tr("sub_accounts_delete_warning", count=preview.child_count) if preview.child_count else ""

        if confirm_delete(self, preview.account_name, extra_msg=extra):
            try:
                svc.delete_account_cascade(aid)
                from ui.widgets.core.events import bus
                bus.company_data_changed.emit(self._company_id or 0)
            except Exception as e:
                msg_critical(self, tr("error"), tr("delete_failed_msg", error=str(e)))
