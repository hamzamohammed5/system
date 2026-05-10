"""
ui/tabs/accounting/account_combo.py
=====================================
_AccountCombo — Combo قابل للبحث والفلترة لاختيار الحسابات.

الإصلاح:
  1. ربط bus.data_changed بـ refresh() حتى يتحدث الـ combo تلقائياً
     عند إضافة/حذف حسابات.
  2. تعطيل السيباريتور بشكل صريح حتى لا يظهر كاختيار.
  3. تنظيف السيباريتورات المتتالية أو الأخيرة.
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QLineEdit, QLabel,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui  import QColor, QFont

from db.accounting_repo import (
    fetch_leaf_accounts, fetch_account,
    fetch_all_groups, build_group_tree,
    get_normal_balance, _get_group_descendants,
)
from db.accounting_schema import TYPE_AR
from ui.events import bus
from .helpers import TYPE_COLORS


class _AccountCombo(QWidget):
    def __init__(self, conn, acc_types: list = None, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self.acc_types = acc_types
        self._all_accs = []
        self._build()
        self.refresh()
        # ✅ تحديث تلقائي عند أي تغيير في البيانات
        bus.data_changed.connect(self._on_data_changed)

    def _on_data_changed(self):
        """نستخدم QTimer لتجنب refresh متكرر في نفس اللحظة."""
        QTimer.singleShot(0, self.refresh)

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        self.cmb_group = QComboBox()
        self.cmb_group.setMinimumHeight(28)
        self.cmb_group.setFixedWidth(130)
        self.cmb_group.setToolTip("فلتر بالتصنيف")
        self.cmb_group.currentIndexChanged.connect(self._apply_filter)

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 بحث...")
        self.inp_search.setFixedWidth(90)
        self.inp_search.setMinimumHeight(28)
        self.inp_search.textChanged.connect(self._apply_filter)

        self.cmb_account = QComboBox()
        self.cmb_account.setMinimumHeight(28)
        self.cmb_account.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
        self.cmb_account.setMinimumWidth(200)

        self.lbl_nb = QLabel("")
        self.lbl_nb.setFixedWidth(55)
        self.lbl_nb.setAlignment(Qt.AlignCenter)
        self.lbl_nb.setStyleSheet(
            "font-size:10px; font-weight:bold; border-radius:3px; padding:2px 4px;"
        )
        self.cmb_account.currentIndexChanged.connect(self._update_nb_label)

        lay.addWidget(self.cmb_group)
        lay.addWidget(self.inp_search)
        lay.addWidget(self.cmb_account, stretch=1)
        lay.addWidget(self.lbl_nb)

    def refresh(self):
        self._load_groups()
        self._load_accounts()

    def _load_groups(self):
        self.cmb_group.blockSignals(True)
        prev = self.cmb_group.currentData()
        self.cmb_group.clear()
        self.cmb_group.addItem("— كل التصنيفات —", None)

        all_groups  = fetch_all_groups(self.conn)
        seen_types  = set(self.acc_types) if self.acc_types else set(TYPE_AR.keys())
        groups      = [g for g in all_groups if g["acc_type"] in seen_types]
        tree        = build_group_tree(groups)
        self._add_group_nodes(tree, depth=0)

        for i in range(self.cmb_group.count()):
            if self.cmb_group.itemData(i) == prev:
                self.cmb_group.setCurrentIndex(i)
                break
        self.cmb_group.blockSignals(False)

    def _add_group_nodes(self, nodes, depth):
        indent = "  " * depth
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            self.cmb_group.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            idx = self.cmb_group.count() - 1
            self.cmb_group.setItemData(idx, QColor(node["color"]), Qt.ForegroundRole)
            if node["children"]:
                self._add_group_nodes(node["children"], depth + 1)

    def _load_accounts(self):
        self._all_accs = list(fetch_leaf_accounts(self.conn))
        if self.acc_types:
            self._all_accs = [a for a in self._all_accs if a["type"] in self.acc_types]
        self._apply_filter()

    def _apply_filter(self):
        prev_id = self.current_account_id()
        q       = self.inp_search.text().strip().lower()
        gid     = self.cmb_group.currentData()

        self.cmb_account.blockSignals(True)
        self.cmb_account.clear()
        self.cmb_account.addItem("— اختر الحساب —", None)

        last_type      = None
        sep_index      = None   # نتتبع آخر سيباريتور أضفناه

        for acc in self._all_accs:
            # ── فلتر التصنيف ──
            if gid is not None:
                desc = _get_group_descendants(self.conn, gid)
                if acc["group_id"] not in desc:
                    continue

            # ── فلتر البحث ──
            if q and q not in acc["name"].lower() and q not in acc["code"].lower():
                continue

            # ── سيباريتور النوع ──
            if acc["type"] != last_type:
                sep_text = f"── {TYPE_AR.get(acc['type'], acc['type'])} ──"
                self.cmb_account.addItem(sep_text, "__sep__")
                sep_index = self.cmb_account.count() - 1
                self._disable_item(sep_index)
                last_type = acc["type"]

            # ── الحساب الفعلي ──
            color   = TYPE_COLORS.get(acc["type"], "#333")
            nb      = get_normal_balance(acc["type"])
            nb_text = "DR↑" if nb == "dr" else "CR↑"
            label   = f"{acc['code']} — {acc['name']}  [{nb_text}]"
            self.cmb_account.addItem(label, acc["id"])
            idx2 = self.cmb_account.count() - 1
            self.cmb_account.setItemData(idx2, QColor(color), Qt.ForegroundRole)
            sep_index = None   # يوجد عنصر حقيقي بعد السيباريتور

        # ── احذف السيباريتورات الفاضية في الآخر ──
        self._remove_trailing_separators()

        self.cmb_account.blockSignals(False)

        # ── استعادة الاختيار السابق ──
        if prev_id is not None:
            for i in range(self.cmb_account.count()):
                if self.cmb_account.itemData(i) == prev_id:
                    self.cmb_account.setCurrentIndex(i)
                    self._update_nb_label()
                    return

        # ── اختار أول حساب حقيقي لو مفيش اختيار سابق ──
        self._select_first_real()
        self._update_nb_label()

    def _disable_item(self, idx: int):
        """يعطّل السيباريتور بحيث لا يكون قابلاً للاختيار."""
        model = self.cmb_account.model()
        item  = model.item(idx)
        if item:
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled & ~Qt.ItemIsSelectable)
            item.setForeground(QColor("#78909c"))
            f = QFont()
            f.setBold(True)
            f.setPointSize(max(f.pointSize() - 1, 7))
            item.setFont(f)

    def _remove_trailing_separators(self):
        """يحذف أي سيباريتور في الآخر أو سيباريتورات متتالية."""
        changed = True
        while changed:
            changed = False
            count = self.cmb_account.count()
            for i in range(count - 1, -1, -1):
                d = self.cmb_account.itemData(i)
                if d == "__sep__":
                    # لو آخر عنصر أو التالي سيباريتور كمان → احذفه
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
        """يختار أول حساب حقيقي (مش سيباريتور ومش placeholder)."""
        for i in range(self.cmb_account.count()):
            d = self.cmb_account.itemData(i)
            if d is not None and d != "__sep__" and isinstance(d, int):
                self.cmb_account.setCurrentIndex(i)
                return
        # لو مفيش حسابات — ارجع للأول (placeholder)
        self.cmb_account.setCurrentIndex(0)

    def _update_nb_label(self):
        acc_id = self.current_account_id()
        if not acc_id:
            self.lbl_nb.setText("")
            self.lbl_nb.setStyleSheet(
                "font-size:10px; font-weight:bold; border-radius:3px; padding:2px 4px;"
            )
            return
        acc = fetch_account(self.conn, acc_id)
        if not acc:
            return
        nb = get_normal_balance(acc["type"])
        if nb == "dr":
            self.lbl_nb.setText("DR↑")
            self.lbl_nb.setStyleSheet(
                "font-size:10px; font-weight:bold; color:#1565c0;"
                "background:#e3f2fd; border-radius:3px; padding:2px 4px;"
            )
        else:
            self.lbl_nb.setText("CR↑")
            self.lbl_nb.setStyleSheet(
                "font-size:10px; font-weight:bold; color:#c62828;"
                "background:#fdecea; border-radius:3px; padding:2px 4px;"
            )

    def current_account_id(self):
        data = self.cmb_account.currentData()
        # ✅ تأكد إن المختار مش سيباريتور ومش None
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