"""
ui/tabs/accounting/journal/account_picker/_account_tree_popup.py
=================================================================
_AccountTreePopup — نافذة popup شجرية لاختيار حساب.

إصلاح (v3):
  - self._conn أُزيل تماماً — الـ conn يُمرر فقط لـ _load_accounts() وقت الإنشاء.
  - get_selected_type() تستقبل conn صريح من المستدعي بدل self._conn.
  - هذا يمنع أي استخدام لـ conn قديم بعد تغيير الشركة.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout,
    QLabel,
    QListWidget, QListWidgetItem, QDialog,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor, QFont
from ui.widgets.panels.themed_inputs import ThemedLineEdit

from services.accounting.accounts_service import AccountsService
from ...helpers import TYPE_COLORS
from ui.font import FS_XS, FS_BASE
from ui.widgets.core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import (
    SPACING_XS, BTN_MIN_HEIGHT, INPUT_BORDER_RADIUS, FILTER_BAR_BORDER_RADIUS,
    ACCOUNT_TREE_POPUP_MIN_W, ACCOUNT_TREE_POPUP_MAX_H, ACCOUNT_TREE_POPUP_MARGINS,
    ACCOUNT_TREE_LIST_BORDER_RADIUS, ACCOUNT_TREE_LIST_ITEM_PAD_V, ACCOUNT_TREE_LIST_ITEM_PAD_H,
    ACCOUNT_TREE_SEARCH_PAD_V, ACCOUNT_TREE_SEARCH_PAD_H, ACCOUNT_TREE_BORDER_W,
    ACCOUNT_TREE_FONT_SIZE_DELTA_L0, ACCOUNT_TREE_FONT_SIZE_DELTA_L1,
)

_TYPE_ORDER = {
    "asset":     "account_tree_icon_asset",
    "liability": "account_tree_icon_liability",
    "capital":   "account_tree_icon_capital",
    "drawings":  "account_tree_icon_drawings",
    "revenue":   "account_tree_icon_revenue",
    "expense":   "account_tree_icon_expense",
}

# _EQUITY_COLOR now uses _C at runtime


class _AccountTreePopup(QDialog, WidgetMixin):
    """
    نافذة popup تعرض الحسابات في شجرة قابلة للطي مع بحث نصي.

    [إصلاح v3] لا يحفظ conn إطلاقاً — يُمرر فقط لـ _load_accounts()
    وقت الإنشاء. get_selected_type() تستقبل conn صريح.
    المستدعي (_AccountPickerButton) مسؤول دائماً عن تمرير conn حي.
    """

    def __init__(self, conn, acc_types=None, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        # [إصلاح] لا نحفظ conn — نستخدمه مباشرة في _load_accounts فقط
        self.acc_types      = acc_types or _TYPE_ORDER
        self._selected_id   = None
        self._selected_name = None
        self._expanded: set = set()
        self._expanded.add("group:equity")
        for t in self.acc_types:
            self._expanded.add(f"type:{t}")
        self._all_accounts = []
        self._filter_text  = ""
        _acc_svc = AccountsService(None)
        self._type_ar       = _acc_svc.get_type_labels_map()
        self._equity_types  = _acc_svc.get_equity_types()
        self._init_widget_mixin(lang=False, data=False)
        self._build()
        self._refresh_style()
        self._load_accounts(conn)  # conn يُستخدم هنا فقط

    def _build(self):
        self.setMinimumWidth(ACCOUNT_TREE_POPUP_MIN_W)
        self.setMaximumHeight(ACCOUNT_TREE_POPUP_MAX_H)
        root = QVBoxLayout(self)
        root.setContentsMargins(*ACCOUNT_TREE_POPUP_MARGINS)
        root.setSpacing(SPACING_XS)

        self.inp_search = ThemedLineEdit()
        self.inp_search.setPlaceholderText(tr("account_search_placeholder"))
        self.inp_search.setMinimumHeight(BTN_MIN_HEIGHT)
        self.inp_search.textChanged.connect(self._on_search)
        root.addWidget(self.inp_search)

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        root.addWidget(self.list_widget)

        self.hint_label = QLabel(tr("popup_hint_select"))
        self.hint_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self.hint_label)

    def _refresh_style(self, *_):
        from ui.theme import _C
        self.setStyleSheet(
            f"QDialog {{ background: {_C['bg_surface']}; border: {ACCOUNT_TREE_BORDER_W}px solid {_C['journal_header_border']}; border-radius: {FILTER_BAR_BORDER_RADIUS}px; }}"
        )
        self.inp_search.setStyleSheet(
            f"QLineEdit {{ background: {_C['journal_header_bg']}; border: {ACCOUNT_TREE_BORDER_W}px solid {_C['journal_header_border']};"
            f"border-radius: {INPUT_BORDER_RADIUS}px; padding: {ACCOUNT_TREE_SEARCH_PAD_V}px {ACCOUNT_TREE_SEARCH_PAD_H}px; font-size: {FS_BASE}px; }}"
            f"QLineEdit:focus {{ border-color: {_C['accent']}; background: {_C['bg_input']}; }}"
        )
        self.list_widget.setStyleSheet(
            f"QListWidget {{ border: {ACCOUNT_TREE_BORDER_W}px solid {_C['border']}; border-radius: {ACCOUNT_TREE_LIST_BORDER_RADIUS}px;"
            f"background: {_C['bg_surface']}; outline: none; }}"
            f"QListWidget::item {{ padding: {ACCOUNT_TREE_LIST_ITEM_PAD_V}px {ACCOUNT_TREE_LIST_ITEM_PAD_H}px; border-bottom: {ACCOUNT_TREE_BORDER_W}px solid {_C['border']}; }}"
            f"QListWidget::item:selected {{ background: {_C['badge_dr_bg']}; color: {_C['accent']}; }}"
            f"QListWidget::item:hover:!selected {{ background: {_C['bg_hover']}; }}"
        )
        self.hint_label.setStyleSheet(f"font-size:{FS_XS}px; color:{_C['text_hint']}; background:transparent;")

    def _load_accounts(self, conn):
        """يُستدعى مرة واحدة في __init__ بـ conn حي من المستدعي."""
        self._all_accounts = []
        svc = AccountsService(conn)
        for acc_type in self.acc_types:
            try:
                rows = svc.list_all_accounts(acc_type)
                for r in rows:
                    if r["is_leaf"]:
                        self._all_accounts.append({
                            "id":         r["id"],
                            "code":       r["code"],
                            "name":       r["name"],
                            "type":       r["type"],
                            "group_id":   r["group_id"],
                            "group_name": r["group_name"] if "group_name" in r.keys() else None,
                        })
            except Exception:
                pass
        self._render()

    def _on_search(self, text):
        self._filter_text = text.strip().lower()
        if self._filter_text:
            self._expanded.add("group:equity")
            for t in self.acc_types:
                self._expanded.add(f"type:{t}")
        self._render()

    def _render(self):
        from ui.theme import _C
        self.list_widget.clear()
        q = self._filter_text

        by_type: dict = {}
        for acc in self._all_accounts:
            t = acc["type"]
            if t not in by_type:
                by_type[t] = {}
            grp_key  = acc["group_name"] or tr("account_group_unassigned")
            grp_id   = acc["group_id"]   or -1
            grp_full = (grp_id, grp_key)
            if grp_full not in by_type[t]:
                by_type[t][grp_full] = []
            by_type[t][grp_full].append(acc)

        standalone_types = [t for t in self.acc_types if t not in self._equity_types]
        equity_types     = [t for t in self.acc_types if t in self._equity_types]

        for acc_type in standalone_types:
            if acc_type not in by_type:
                continue
            groups = by_type[acc_type]
            if q:
                has_match = any(
                    q in acc["name"].lower() or q in acc["code"].lower()
                    for accs in groups.values() for acc in accs
                )
                if not has_match:
                    continue
            self._render_type_section(acc_type, groups, q, indent=0)

        equity_has_match = False
        if equity_types:
            for t in equity_types:
                if t not in by_type:
                    continue
                if q:
                    for accs in by_type[t].values():
                        for acc in accs:
                            if q in acc["name"].lower() or q in acc["code"].lower():
                                equity_has_match = True
                                break
                        if equity_has_match:
                            break
                else:
                    equity_has_match = True
                if equity_has_match:
                    break

        if equity_types and equity_has_match:
            equity_key = "group:equity"
            expanded   = equity_key in self._expanded
            toggle     = tr("tree_toggle_expanded") if expanded else tr("tree_toggle_collapsed")

            eq_item = QListWidgetItem(f"{toggle} {tr('account_tree_equity_icon')}  {tr('equity_label')}")
            eq_item.setData(Qt.UserRole, {"kind": "equity_group", "key": equity_key})
            f = QFont(); f.setBold(True); f.setPointSize(f.pointSize() + ACCOUNT_TREE_FONT_SIZE_DELTA_L0)
            eq_item.setFont(f)
            eq_item.setForeground(QColor(_C["investor_capital_text"]))
            eq_item.setBackground(QColor(_C["investor_capital_bg"]))
            self.list_widget.addItem(eq_item)

            if expanded:
                equity_order = ["capital", "drawings", "revenue", "expense"]
                for acc_type in equity_order:
                    if acc_type not in equity_types or acc_type not in by_type:
                        continue
                    groups = by_type[acc_type]
                    if q:
                        has_match = any(
                            q in acc["name"].lower() or q in acc["code"].lower()
                            for accs in groups.values() for acc in accs
                        )
                        if not has_match:
                            continue
                    self._render_type_section(acc_type, groups, q, indent=1)

    def _render_type_section(self, acc_type, groups, q, indent=0):
        from ui.theme import _C
        type_key   = f"type:{acc_type}"
        expanded   = type_key in self._expanded
        icon       = tr(_TYPE_ORDER.get(acc_type, "account_tree_default_icon"))
        type_label = self._type_ar.get(acc_type, acc_type)
        toggle     = tr("tree_toggle_expanded") if expanded else tr("tree_toggle_collapsed")
        color      = TYPE_COLORS.get(acc_type, _C['text_muted'])
        pad        = "    " * indent

        type_item = QListWidgetItem(f"{pad}{toggle} {icon}  {type_label}")
        type_item.setData(Qt.UserRole, {"kind": "type", "type": acc_type, "key": type_key})
        f = QFont(); f.setBold(True); f.setPointSize(f.pointSize() + (ACCOUNT_TREE_FONT_SIZE_DELTA_L1 if indent else ACCOUNT_TREE_FONT_SIZE_DELTA_L0))
        type_item.setFont(f)
        type_item.setForeground(QColor(color))
        type_item.setBackground(QColor(_C["journal_header_bg"] if indent == 0 else _C["bg_surface_2"]))
        self.list_widget.addItem(type_item)

        if not expanded:
            return

        for (grp_id, grp_name), accs in sorted(groups.items(), key=lambda x: x[0][1]):
            matched_accs = accs
            if q:
                matched_accs = [a for a in accs
                                if q in a["name"].lower() or q in a["code"].lower()]
            if not matched_accs:
                continue

            grp_key_full = f"grp:{acc_type}:{grp_id}"
            grp_expanded = grp_key_full in self._expanded
            toggle_g  = tr("tree_toggle_expanded") if grp_expanded else tr("tree_toggle_collapsed")
            inner_pad = "    " * (indent + 1)

            grp_item = QListWidgetItem(f"{inner_pad}{toggle_g} {tr('account_tree_group_icon')}  {grp_name}")
            grp_item.setData(Qt.UserRole, {"kind": "group", "key": grp_key_full})
            gf = QFont(); gf.setBold(True); gf.setItalic(True)
            grp_item.setFont(gf)
            grp_item.setForeground(QColor(_C['group_label_text']))
            grp_item.setBackground(QColor(_C["journal_neutral_bg"]))
            self.list_widget.addItem(grp_item)

            if not grp_expanded and not q:
                continue

            acc_pad = "    " * (indent + 2)
            for acc in sorted(matched_accs, key=lambda a: a["code"]):
                nb = AccountsService(None).get_normal_balance(acc["type"])
                nb_text = tr("dr_badge") if nb == "dr" else tr("cr_badge")
                label = f"{acc_pad}{acc['code']}{tr('account_code_name_sep')}{acc['name']}  [{nb_text}]"
                acc_item = QListWidgetItem(label)
                acc_item.setData(Qt.UserRole, {
                    "kind": "account",
                    "id":   acc["id"],
                    "name": f"{acc['code']}{tr('account_code_name_sep')}{acc['name']}",
                    "type": acc["type"],
                })
                acc_item.setForeground(QColor(color))
                self.list_widget.addItem(acc_item)

    def _on_item_clicked(self, item):
        data = item.data(Qt.UserRole)
        if not data:
            return
        kind = data.get("kind")
        if kind in ("type", "group", "equity_group"):
            key = data["key"]
            if key in self._expanded:
                self._expanded.discard(key)
            else:
                self._expanded.add(key)
            self._render()

    def _on_item_double_clicked(self, item):
        data = item.data(Qt.UserRole)
        if not data or data.get("kind") != "account":
            return
        self._selected_id   = data["id"]
        self._selected_name = data["name"]
        self.accept()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            current = self.list_widget.currentItem()
            if current:
                self._on_item_double_clicked(current)
            return
        if event.key() == Qt.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)

    def get_selected(self):
        return self._selected_id, self._selected_name

    def get_selected_type(self, conn):
        """
        [إصلاح v3] يستقبل conn صريح من المستدعي بدل self._conn.
        المستدعي (_AccountPickerButton) يمرر _get_safe_conn() دايماً.
        """
        if not self._selected_id:
            return None
        acc = AccountsService(conn).get_account(self._selected_id)
        return acc["type"] if acc else None
