"""
ui/tabs/accounting/account_combo.py
=====================================
_AccountCombo — Combo قابل للبحث والفلترة لاختيار الحسابات.
SafeConnMixin (v4): _get_safe_conn() بدل self.conn في كل query.

[إصلاح v5]:
  - _on_company_event(): حذف snapshot_id الزائد —
    _on_company_event_safe() تتحقق بالفعل من تطابق الشركة.

[تحديث v6]:
  - حذف _on_company_event() نفسها (كانت pass فقط، بدون أي استدعاء فعلي
    بعد التحويل لـ WidgetMixin الذي يوجّه company_data_changed مباشرة
    لـ _refresh_data).
  - استبدال القيم الـ hardcoded (الفاصل البصري "—"، spacing=4) بـ
    tr("dash") و ACCOUNT_COMBO_LAYOUT_SPACING.
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QLineEdit, QLabel,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui  import QColor, QFont

from services.accounting.accounts_service import AccountsService
from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.font import FS_XS
from ui.constants import (
    ACCOUNT_COMBO_GROUP_W,
    ACCOUNT_COMBO_SEARCH_W,
    ACCOUNT_COMBO_ACCOUNT_MIN_W,
    ACCOUNT_COMBO_NB_BADGE_W,
    ACCOUNT_COMBO_BADGE_BORDER_RADIUS,
    ACCOUNT_COMBO_BADGE_PAD_V,
    ACCOUNT_COMBO_BADGE_PAD_H,
    ACCOUNT_COMBO_LAYOUT_SPACING,
)
from .helpers import _get_type_colors


def _badge_style(side: str = "") -> str:
    from ui.theme import _C
    _pad = f"{ACCOUNT_COMBO_BADGE_PAD_V}px {ACCOUNT_COMBO_BADGE_PAD_H}px"
    _r   = f"{ACCOUNT_COMBO_BADGE_BORDER_RADIUS}px"
    if side == "dr":
        return (f"font-size:{FS_XS}px; font-weight:bold; color:{_C['badge_dr_text']};"
                f"background:{_C['badge_dr_bg']}; border-radius:{_r}; padding:{_pad};")
    if side == "cr":
        return (f"font-size:{FS_XS}px; font-weight:bold; color:{_C['badge_cr_text']};"
                f"background:{_C['badge_cr_bg']}; border-radius:{_r}; padding:{_pad};")
    return f"font-size:{FS_XS}px; font-weight:bold; border-radius:{_r}; padding:{_pad};"


class _AccountCombo(SafeConnMixin, QWidget, WidgetMixin):
    def __init__(self, conn, acc_types: list = None, parent=None):
        super().__init__(parent)
        self._init_safe_conn(conn, "accounting")
        self._init_widget_mixin(theme=True, font=False, lang=False, data=True)
        self.acc_types   = acc_types
        self._all_accs   = []
        self._company_id = self._get_company_id()
        self._build()
        self._refresh_style()
        self.refresh()

    def _refresh_style(self, *_):
        self.lbl_nb.setStyleSheet(_badge_style())

    def _refresh_data(self, company_id=None):
        if self._on_company_event_safe(company_id):
            QTimer.singleShot(0, self.refresh)

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(ACCOUNT_COMBO_LAYOUT_SPACING)

        self.cmb_group = QComboBox()
        self.cmb_group.setFixedWidth(ACCOUNT_COMBO_GROUP_W)
        self.cmb_group.setToolTip(tr("group_filter_tooltip"))
        self.cmb_group.currentIndexChanged.connect(self._apply_filter)

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText(tr("search_placeholder"))
        self.inp_search.setFixedWidth(ACCOUNT_COMBO_SEARCH_W)
        self.inp_search.textChanged.connect(self._apply_filter)

        self.cmb_account = QComboBox()
        self.cmb_account.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
        self.cmb_account.setMinimumWidth(ACCOUNT_COMBO_ACCOUNT_MIN_W)

        self.lbl_nb = QLabel("")
        self.lbl_nb.setFixedWidth(ACCOUNT_COMBO_NB_BADGE_W)
        self.lbl_nb.setAlignment(Qt.AlignCenter)
        self.lbl_nb.setStyleSheet(_badge_style())
        self.cmb_account.currentIndexChanged.connect(self._update_nb_label)

        lay.addWidget(self.cmb_group)
        lay.addWidget(self.inp_search)
        lay.addWidget(self.cmb_account, stretch=1)
        lay.addWidget(self.lbl_nb)

    def refresh(self):
        self._load_groups()
        self._load_accounts()

    def _load_groups(self):
        conn = self._get_safe_conn()
        self.cmb_group.blockSignals(True)
        prev = self.cmb_group.currentData()
        self.cmb_group.clear()
        self.cmb_group.addItem(tr("all_types_combo"), None)
        try:
            svc = AccountsService(conn)
            all_groups = svc.list_groups()
            seen_types = set(self.acc_types) if self.acc_types else set(svc.get_type_labels_map().keys())
            groups     = [g for g in all_groups if g["acc_type"] in seen_types]
            tree       = svc.build_group_tree(groups)
            self._add_group_nodes(tree, depth=0)
        except Exception:
            pass
        for i in range(self.cmb_group.count()):
            if self.cmb_group.itemData(i) == prev:
                self.cmb_group.setCurrentIndex(i)
                break
        self.cmb_group.blockSignals(False)

    def _add_group_nodes(self, nodes, depth):
        indent = "  " * depth
        arrow  = tr("tree_node_arrow") if depth > 0 else ""
        for node in nodes:
            self.cmb_group.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            idx = self.cmb_group.count() - 1
            self.cmb_group.setItemData(idx, QColor(node["color"]), Qt.ForegroundRole)
            if node["children"]:
                self._add_group_nodes(node["children"], depth + 1)

    def _load_accounts(self):
        conn = self._get_safe_conn()
        try:
            self._all_accs = list(AccountsService(conn).list_leaf_accounts(acc_types=self.acc_types))
        except Exception:
            self._all_accs = []
        self._apply_filter()

    def _apply_filter(self):
        from ui.theme import _C
        conn    = self._get_safe_conn()
        svc     = AccountsService(conn)
        prev_id = self.current_account_id()
        q       = self.inp_search.text().strip().lower()
        gid     = self.cmb_group.currentData()

        self.cmb_account.blockSignals(True)
        self.cmb_account.clear()
        self.cmb_account.addItem(tr("select_account_combo"), None)

        last_type = None
        for acc in self._all_accs:
            if gid is not None:
                try:
                    desc = svc.get_group_descendants(gid)
                    if acc["group_id"] not in desc:
                        continue
                except Exception:
                    pass
            if q and q not in acc["name"].lower() and q not in acc["code"].lower():
                continue

            if acc["type"] != last_type:
                sep_text = tr("account_tree_type_header", type=svc.get_type_labels_map().get(acc["type"], acc["type"]))
                self.cmb_account.addItem(sep_text, "__sep__")
                sep_index = self.cmb_account.count() - 1
                self._disable_item(sep_index)
                last_type = acc["type"]

            color   = _get_type_colors().get(acc["type"], _C["text_primary"])
            nb      = svc.get_normal_balance(acc["type"])
            nb_text = tr("dr_badge") if nb == "dr" else tr("cr_badge")
            label   = f"{acc['code']} {tr('dash')} {acc['name']}  [{nb_text}]"
            self.cmb_account.addItem(label, acc["id"])
            idx2 = self.cmb_account.count() - 1
            self.cmb_account.setItemData(idx2, QColor(color), Qt.ForegroundRole)

        self._remove_trailing_separators()
        self.cmb_account.blockSignals(False)

        if prev_id is not None:
            for i in range(self.cmb_account.count()):
                if self.cmb_account.itemData(i) == prev_id:
                    self.cmb_account.setCurrentIndex(i)
                    self._update_nb_label()
                    return

        self._select_first_real()
        self._update_nb_label()

    def _disable_item(self, idx: int):
        from ui.theme import _C
        model = self.cmb_account.model()
        item  = model.item(idx)
        if item:
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled & ~Qt.ItemIsSelectable)
            item.setForeground(QColor(_C["text_separator"]))
            f = QFont()
            f.setBold(True)
            item.setFont(f)

    def _remove_trailing_separators(self):
        changed = True
        while changed:
            changed = False
            count = self.cmb_account.count()
            for i in range(count - 1, -1, -1):
                d = self.cmb_account.itemData(i)
                if d == "__sep__":
                    if i == count - 1:
                        self.cmb_account.removeItem(i)
                        changed = True
                        break
                    next_d = self.cmb_account.itemData(i + 1)
                    if next_d == "__sep__":
                        self.cmb_account.removeItem(i)
                        changed = True
                        break

    def _select_first_real(self):
        for i in range(self.cmb_account.count()):
            d = self.cmb_account.itemData(i)
            if d is not None and d != "__sep__" and isinstance(d, int):
                self.cmb_account.setCurrentIndex(i)
                return
        self.cmb_account.setCurrentIndex(0)

    def _update_nb_label(self):
        acc_id = self.current_account_id()
        if not acc_id:
            self.lbl_nb.setText("")
            self.lbl_nb.setStyleSheet(_badge_style())
            return
        try:
            svc = AccountsService(self._get_safe_conn())
            acc = svc.get_account(acc_id)
            if not acc:
                return
            nb = svc.get_normal_balance(acc["type"])
            if nb == "dr":
                self.lbl_nb.setText(tr("dr_badge"))
                self.lbl_nb.setStyleSheet(_badge_style("dr"))
            else:
                self.lbl_nb.setText(tr("cr_badge"))
                self.lbl_nb.setStyleSheet(_badge_style("cr"))
        except Exception:
            pass

    def current_account_id(self):
        data = self.cmb_account.currentData()
        if data is None or data == "__sep__":
            return None
        if not isinstance(data, int):
            return None
        return data

    def set_account(self, acc_id):
        for i in range(self.cmb_account.count()):
            if self.cmb_account.itemData(i) == acc_id:
                self.cmb_account.setCurrentIndex(i)
                return