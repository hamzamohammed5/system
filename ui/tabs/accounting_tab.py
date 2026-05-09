"""
ui/tabs/accounting_tab.py
==========================
تبويب الحسابات — مع:
  - تصنيفات هرمية للحسابات
  - قيد بعمليتين فقط (smart DR/CR تلقائي)
  - Owners' Equity مفصل (Capital/Revenue vs Expenses/Drawings)
  - فلترة بالتصنيفات في كل الـ dropdowns
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QFrame, QSplitter, QPushButton,
    QTableWidgetItem, QHeaderView, QMessageBox,
    QLineEdit, QDoubleSpinBox, QComboBox,
    QFormLayout, QGroupBox, QDateEdit, QScrollArea,
    QTreeWidget, QTreeWidgetItem, QRadioButton,
    QButtonGroup, QColorDialog, QAbstractItemView,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui  import QColor, QFont

from db.connection      import get_accounting_connection
from db.accounting_repo import (
    fetch_all_accounts, fetch_leaf_accounts,
    fetch_all_entries, fetch_entry_lines,
    insert_entry, add_entry_lines, delete_entry,
    validate_entry_balance, trial_balance,
    insert_account, update_account, delete_account,
    get_account_balance, get_account_natural_balance,
    fetch_account, income_statement, balance_sheet,
    owners_equity_statement, fetch_t_account,
    fetch_all_groups, fetch_group, insert_group,
    update_group, delete_group, build_group_tree,
    calc_signed_amount, get_normal_balance,
)
from db.accounting_schema import TYPE_AR, NORMAL_BALANCE
from ui.helpers import (
    make_table, setup_table_columns, buttons_row,
    section_label, danger_button, confirm_delete,
)
from ui.events import bus


# ── ألوان حسب النوع ─────────────────────────────────────
TYPE_COLORS = {
    "asset":    "#1565c0",
    "liability":"#c62828",
    "capital":  "#2e7d32",
    "revenue":  "#6a1b9a",
    "expense":  "#e65100",
    "drawings": "#4e342e",
}

# ── مجموعات owners equity ────────────────────────────────
EQUITY_CR_TYPES = {"capital", "revenue"}   # تزيد بـ CR
EQUITY_DR_TYPES = {"expense", "drawings"}  # تزيد بـ DR


def _spin(max_=999_999_999, dec=2):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(30)
    return s


def _money(val: float) -> str:
    return f"{val:,.2f}  ج"


# ══════════════════════════════════════════════════════════
# Searchable Account Combo (مع فلترة بالتصنيف)
# ══════════════════════════════════════════════════════════

class _AccountCombo(QWidget):
    """
    ComboBox للحسابات مع:
      - بحث نصي
      - فلترة بالتصنيف
      - عرض الـ normal balance
    """
    def __init__(self, conn, acc_types: list = None, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self.acc_types = acc_types  # None = كل الأنواع
        self._all_accs = []
        self._build()
        self.refresh()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        # فلتر التصنيف
        self.cmb_group = QComboBox()
        self.cmb_group.setMinimumHeight(28)
        self.cmb_group.setFixedWidth(130)
        self.cmb_group.setToolTip("فلتر بالتصنيف")
        self.cmb_group.currentIndexChanged.connect(self._apply_filter)

        # بحث
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 بحث...")
        self.inp_search.setFixedWidth(90)
        self.inp_search.setMinimumHeight(28)
        self.inp_search.textChanged.connect(self._apply_filter)

        # الحساب
        self.cmb_account = QComboBox()
        self.cmb_account.setMinimumHeight(28)
        self.cmb_account.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
        self.cmb_account.setMinimumWidth(200)

        # عرض الـ normal balance
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
        """يعيد تحميل التصنيفات والحسابات."""
        self._load_groups()
        self._load_accounts()

    def _load_groups(self):
        self.cmb_group.blockSignals(True)
        prev = self.cmb_group.currentData()
        self.cmb_group.clear()
        self.cmb_group.addItem("— كل التصنيفات —", None)

        # جيب التصنيفات المناسبة للأنواع المطلوبة
        all_groups = fetch_all_groups(self.conn)
        seen_types = set(self.acc_types) if self.acc_types else set(TYPE_AR.keys())
        groups = [g for g in all_groups if g["acc_type"] in seen_types]
        tree   = build_group_tree(groups)
        self._add_group_nodes(tree, depth=0)

        # استعادة الاختيار
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
            self._all_accs = [a for a in self._all_accs
                              if a["type"] in self.acc_types]
        self._apply_filter()

    def _apply_filter(self):
        prev_id = self.current_account_id()
        q       = self.inp_search.text().strip().lower()
        gid     = self.cmb_group.currentData()

        self.cmb_account.blockSignals(True)
        self.cmb_account.clear()
        self.cmb_account.addItem("— اختر الحساب —", None)

        last_type = None
        for acc in self._all_accs:
            # فلتر التصنيف
            if gid is not None and acc["group_id"] != gid:
                # شيك لو التصنيف ده فرع من التصنيف المطلوب
                from db.accounting_repo import _get_group_descendants
                desc = _get_group_descendants(self.conn, gid)
                if acc["group_id"] not in desc:
                    continue

            # فلتر النص
            if q and q not in acc["name"].lower() and q not in acc["code"].lower():
                continue

            # فاصل بين الأنواع
            if acc["type"] != last_type:
                sep_text = f"── {TYPE_AR.get(acc['type'], acc['type'])} ──"
                self.cmb_account.addItem(sep_text, "__sep__")
                idx = self.cmb_account.count() - 1
                model = self.cmb_account.model()
                item  = model.item(idx)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemIsEnabled & ~Qt.ItemIsSelectable)
                    item.setForeground(QColor("#78909c"))
                    f = QFont()
                    f.setBold(True)
                    f.setPointSize(f.pointSize() - 1)
                    item.setFont(f)
                last_type = acc["type"]

            color    = TYPE_COLORS.get(acc["type"], "#333")
            nb       = get_normal_balance(acc["type"])
            nb_text  = "DR↑" if nb == "dr" else "CR↑"
            label    = f"{acc['code']} — {acc['name']}  [{nb_text}]"
            self.cmb_account.addItem(label, acc["id"])
            idx2 = self.cmb_account.count() - 1
            self.cmb_account.setItemData(idx2, QColor(color), Qt.ForegroundRole)

        self.cmb_account.blockSignals(False)

        # استعادة الاختيار
        if prev_id is not None:
            for i in range(self.cmb_account.count()):
                if self.cmb_account.itemData(i) == prev_id:
                    self.cmb_account.setCurrentIndex(i)
                    return
        self._update_nb_label()

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
        if data in (None, "__sep__"):
            return None
        return data

    def set_account(self, acc_id):
        for i in range(self.cmb_account.count()):
            if self.cmb_account.itemData(i) == acc_id:
                self.cmb_account.setCurrentIndex(i)
                return


# ══════════════════════════════════════════════════════════
# إدارة تصنيفات الحسابات
# ══════════════════════════════════════════════════════════

class _GroupManagerPanel(QWidget):
    """لوحة إدارة التصنيفات الهرمية لنوع حساب معين."""

    def __init__(self, conn, acc_type: str, parent=None):
        super().__init__(parent)
        self.conn     = conn
        self.acc_type = acc_type
        self._editing_id = None
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        root.addWidget(section_label(
            f"── تصنيفات {TYPE_AR.get(self.acc_type, '')} ──"
        ))

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["التصنيف", "عدد الحسابات"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Interactive)
        self.tree.setColumnWidth(1, 100)
        self.tree.setAlternatingRowColors(True)
        root.addWidget(self.tree, stretch=1)

        btn_row = QHBoxLayout()
        btn_edit = QPushButton("✏️ تعديل")
        btn_del  = danger_button("🗑️ حذف")
        for b in (btn_edit, btn_del):
            b.setMinimumHeight(28)
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        btn_row.addWidget(btn_edit)
        btn_row.addWidget(btn_del)
        btn_row.addStretch()
        root.addLayout(btn_row)

        # فورم الإضافة/التعديل
        grp = QGroupBox("➕ إضافة / تعديل تصنيف")
        grp.setStyleSheet("""
            QGroupBox { font-weight:bold; color:#1565c0;
                border:1px solid #e0e0e0; border-radius:6px;
                margin-top:6px; padding-top:6px; }
            QGroupBox::title { subcontrol-origin:margin; padding:0 6px; }
        """)
        fl = QFormLayout(grp)
        fl.setSpacing(8)
        fl.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = QLabel("── تصنيف جديد ──")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0;")
        fl.addRow(self.lbl_mode)

        self.inp_name = QLineEdit()
        self.inp_name.setMinimumHeight(28)
        fl.addRow("الاسم:", self.inp_name)

        # تصنيف الأب
        self.cmb_parent = QComboBox()
        self.cmb_parent.setMinimumHeight(28)
        fl.addRow("تابع لـ:", self.cmb_parent)

        # اللون
        color_row = QHBoxLayout()
        self._color = "#607d8b"
        self.lbl_color = QLabel()
        self.lbl_color.setFixedSize(26, 26)
        self.lbl_color.setStyleSheet(
            f"background:{self._color}; border-radius:4px; border:1px solid #ccc;"
        )
        btn_color = QPushButton("اختر لون")
        btn_color.setMinimumHeight(26)
        btn_color.clicked.connect(self._pick_color)
        color_row.addWidget(self.lbl_color)
        color_row.addWidget(btn_color)
        color_row.addStretch()
        fl.addRow("اللون:", color_row)

        self.btn_add    = QPushButton("➕ إضافة")
        self.btn_save   = QPushButton("💾 حفظ")
        self.btn_cancel = QPushButton("✖ إلغاء")
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        for b in (self.btn_add, self.btn_save, self.btn_cancel):
            b.setMinimumHeight(28)
        self.btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save_edit)
        self.btn_cancel.clicked.connect(self._reset)
        btn_w = QWidget()
        bl = QHBoxLayout(btn_w)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.addWidget(self.btn_add)
        bl.addWidget(self.btn_save)
        bl.addWidget(self.btn_cancel)
        bl.addStretch()
        fl.addRow(btn_w)
        root.addWidget(grp)

        self._refresh_parent_combo()

    def _load(self):
        self.tree.clear()
        rows  = fetch_all_groups(self.conn, self.acc_type)
        tree  = build_group_tree(rows)
        self._add_tree_nodes(tree, None)
        self.tree.expandAll()
        self._refresh_parent_combo()

    def _add_tree_nodes(self, nodes, parent):
        for node in nodes:
            count = self.conn.execute(
                "SELECT COUNT(*) as c FROM accounts WHERE group_id=? AND is_leaf=1",
                (node["id"],)
            ).fetchone()["c"]
            item = QTreeWidgetItem()
            item.setText(0, node["name"])
            item.setText(1, str(count) if count else "—")
            item.setData(0, Qt.UserRole, node["id"])
            item.setForeground(0, QColor(node["color"]))
            if parent:
                parent.addChild(item)
            else:
                self.tree.addTopLevelItem(item)
            if node["children"]:
                self._add_tree_nodes(node["children"], item)

    def _refresh_parent_combo(self, exclude_id=None):
        self.cmb_parent.blockSignals(True)
        self.cmb_parent.clear()
        self.cmb_parent.addItem("— بدون أب (رئيسي) —", None)
        rows  = fetch_all_groups(self.conn, self.acc_type)
        tree  = build_group_tree(rows)
        self._add_parent_nodes(tree, 0, exclude_id)
        self.cmb_parent.blockSignals(False)

    def _add_parent_nodes(self, nodes, depth, exclude_id):
        indent = "  " * depth
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            if node["id"] == exclude_id:
                continue
            self.cmb_parent.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            if node["children"]:
                self._add_parent_nodes(node["children"], depth + 1, exclude_id)

    def _pick_color(self):
        col = QColorDialog.getColor(QColor(self._color), self, "اختر لون")
        if col.isValid():
            self._color = col.name()
            self.lbl_color.setStyleSheet(
                f"background:{self._color}; border-radius:4px; border:1px solid #ccc;"
            )

    def _selected_id(self):
        items = self.tree.selectedItems()
        return items[0].data(0, Qt.UserRole) if items else None

    def _add(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم التصنيف")
            return
        parent_id = self.cmb_parent.currentData()
        insert_group(self.conn, name, self.acc_type, parent_id, self._color)
        self._reset()
        bus.data_changed.emit()

    def _edit(self):
        gid = self._selected_id()
        if not gid:
            QMessageBox.information(self, "تنبيه", "اختر تصنيفًا أولًا")
            return
        grp = fetch_group(self.conn, gid)
        if not grp:
            return
        self._editing_id = gid
        self.inp_name.setText(grp["name"])
        self._color = grp["color"]
        self.lbl_color.setStyleSheet(
            f"background:{self._color}; border-radius:4px; border:1px solid #ccc;"
        )
        self._refresh_parent_combo(exclude_id=gid)
        for i in range(self.cmb_parent.count()):
            if self.cmb_parent.itemData(i) == grp["parent_id"]:
                self.cmb_parent.setCurrentIndex(i)
                break
        self.lbl_mode.setText(f"── تعديل: {grp['name']} ──")
        self.btn_add.setVisible(False)
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)

    def _save_edit(self):
        name = self.inp_name.text().strip()
        if not name or not self._editing_id:
            return
        parent_id = self.cmb_parent.currentData()
        update_group(self.conn, self._editing_id, name, parent_id, self._color)
        self._reset()
        bus.data_changed.emit()

    def _delete(self):
        gid = self._selected_id()
        if not gid:
            return
        grp = fetch_group(self.conn, gid)
        count = self.conn.execute(
            "SELECT COUNT(*) as c FROM accounts WHERE group_id=?", (gid,)
        ).fetchone()["c"]
        msg = f"حذف تصنيف «{grp['name']}»؟"
        if count:
            msg += f"\n⚠️ {count} حساب سيفقد تصنيفه."
        if QMessageBox.question(self, "تأكيد", msg,
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            delete_group(self.conn, gid)
            bus.data_changed.emit()

    def _reset(self):
        self._editing_id = None
        self.inp_name.clear()
        self._color = "#607d8b"
        self.lbl_color.setStyleSheet(
            "background:#607d8b; border-radius:4px; border:1px solid #ccc;"
        )
        self.lbl_mode.setText("── تصنيف جديد ──")
        self.btn_add.setVisible(True)
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        self._refresh_parent_combo()


# ══════════════════════════════════════════════════════════
# شجرة الحسابات مع التصنيفات
# ══════════════════════════════════════════════════════════

class AccountsTreePanel(QWidget):
    def __init__(self, conn, acc_types: list, title: str, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self.acc_types = acc_types
        self.title     = title
        self._editing_id = None
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(5)

        # ── يسار: الشجرة ──
        left = QWidget()
        ll   = QVBoxLayout(left)
        ll.setContentsMargins(10, 8, 6, 10)
        ll.setSpacing(6)
        ll.addWidget(section_label(f"── {self.title} ──"))

        # فلتر التصنيف
        filter_row = QHBoxLayout()
        self.cmb_group_filter = QComboBox()
        self.cmb_group_filter.setMinimumHeight(26)
        self.cmb_group_filter.addItem("— كل التصنيفات —", None)
        self.cmb_group_filter.currentIndexChanged.connect(self._load)
        filter_row.addWidget(QLabel("🏷"))
        filter_row.addWidget(self.cmb_group_filter, stretch=1)
        ll.addLayout(filter_row)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["الكود", "اسم الحساب", "الرصيد"])
        hh = self.tree.header()
        hh.setSectionResizeMode(0, QHeaderView.Interactive)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Interactive)
        self.tree.setColumnWidth(0, 70)
        self.tree.setColumnWidth(2, 110)
        self.tree.setAlternatingRowColors(True)
        ll.addWidget(self.tree, stretch=1)

        btn_row = QHBoxLayout()
        btn_edit = QPushButton("✏️ تعديل")
        btn_del  = danger_button("🗑️ حذف")
        for b in (btn_edit, btn_del):
            b.setMinimumHeight(28)
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        btn_row.addWidget(btn_edit)
        btn_row.addWidget(btn_del)
        btn_row.addStretch()
        ll.addLayout(btn_row)
        splitter.addWidget(left)

        # ── يمين: فورم الإضافة ──
        right = QWidget()
        rl    = QVBoxLayout(right)
        rl.setContentsMargins(6, 8, 10, 10)
        rl.setSpacing(8)

        grp = QGroupBox("➕ إضافة / تعديل حساب")
        grp.setStyleSheet("""
            QGroupBox { font-weight:bold; color:#1565c0;
                border:1px solid #e0e0e0; border-radius:6px;
                margin-top:8px; padding-top:8px; }
            QGroupBox::title { subcontrol-origin:margin; padding:0 6px; }
        """)
        fl = QFormLayout(grp)
        fl.setSpacing(8)
        fl.setLabelAlignment(Qt.AlignRight)

        self.lbl_form_mode = QLabel("── حساب جديد ──")
        self.lbl_form_mode.setStyleSheet("font-weight:bold; color:#1565c0;")
        fl.addRow(self.lbl_form_mode)

        self.inp_code = QLineEdit()
        self.inp_code.setPlaceholderText("مثال: 1141")
        self.inp_code.setMinimumHeight(28)
        fl.addRow("الكود:", self.inp_code)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم الحساب...")
        self.inp_name.setMinimumHeight(28)
        fl.addRow("الاسم:", self.inp_name)

        # النوع
        self.cmb_type = QComboBox()
        self.cmb_type.setMinimumHeight(28)
        for t in self.acc_types:
            self.cmb_type.addItem(TYPE_AR.get(t, t), t)
        self.cmb_type.currentIndexChanged.connect(self._on_type_changed)
        fl.addRow("النوع:", self.cmb_type)

        # التصنيف مع فلترة
        self.cmb_group = QComboBox()
        self.cmb_group.setMinimumHeight(28)
        fl.addRow("التصنيف:", self.cmb_group)

        btn_add    = QPushButton("➕ إضافة")
        self.btn_save   = QPushButton("💾 حفظ")
        self.btn_cancel = QPushButton("✖ إلغاء")
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        for b in (btn_add, self.btn_save, self.btn_cancel):
            b.setMinimumHeight(28)
        btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save_edit)
        self.btn_cancel.clicked.connect(self._cancel_edit)
        btn_w = QWidget()
        bl = QHBoxLayout(btn_w)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.addWidget(btn_add)
        bl.addWidget(self.btn_save)
        bl.addWidget(self.btn_cancel)
        bl.addStretch()
        fl.addRow(btn_w)
        rl.addWidget(grp)
        rl.addStretch()
        splitter.addWidget(right)
        splitter.setSizes([420, 280])

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(splitter)

        self._refresh_group_combos()

    def _on_type_changed(self):
        self._refresh_group_combo_for_type()

    def _refresh_group_combos(self):
        """يحدث كل الـ combos."""
        # فلتر التصنيف في الشجرة
        self.cmb_group_filter.blockSignals(True)
        prev = self.cmb_group_filter.currentData()
        self.cmb_group_filter.clear()
        self.cmb_group_filter.addItem("— كل التصنيفات —", None)
        for t in self.acc_types:
            rows = fetch_all_groups(self.conn, t)
            tree = build_group_tree(rows)
            self._add_filter_nodes(tree, 0)
        for i in range(self.cmb_group_filter.count()):
            if self.cmb_group_filter.itemData(i) == prev:
                self.cmb_group_filter.setCurrentIndex(i)
                break
        self.cmb_group_filter.blockSignals(False)

        self._refresh_group_combo_for_type()

    def _add_filter_nodes(self, nodes, depth):
        indent = "  " * depth
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            self.cmb_group_filter.addItem(
                f"{indent}{arrow}{node['name']}", node["id"]
            )
            self.cmb_group_filter.setItemData(
                self.cmb_group_filter.count() - 1,
                QColor(node["color"]), Qt.ForegroundRole
            )
            if node["children"]:
                self._add_filter_nodes(node["children"], depth + 1)

    def _refresh_group_combo_for_type(self):
        acc_type = self.cmb_type.currentData()
        if not acc_type:
            return
        self.cmb_group.blockSignals(True)
        prev = self.cmb_group.currentData()
        self.cmb_group.clear()
        self.cmb_group.addItem("— بدون تصنيف —", None)
        rows = fetch_all_groups(self.conn, acc_type)
        tree = build_group_tree(rows)
        self._add_group_nodes_to_combo(tree, 0)
        for i in range(self.cmb_group.count()):
            if self.cmb_group.itemData(i) == prev:
                self.cmb_group.setCurrentIndex(i)
                break
        self.cmb_group.blockSignals(False)

    def _add_group_nodes_to_combo(self, nodes, depth):
        indent = "  " * depth
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            self.cmb_group.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            self.cmb_group.setItemData(
                self.cmb_group.count() - 1,
                QColor(node["color"]), Qt.ForegroundRole
            )
            if node["children"]:
                self._add_group_nodes_to_combo(node["children"], depth + 1)

    def _load(self):
        self._refresh_group_combos()
        self.tree.clear()
        gid_filter = self.cmb_group_filter.currentData()

        for acc_type in self.acc_types:
            rows  = fetch_all_accounts(self.conn, acc_type)
            nodes = {r["id"]: dict(r) for r in rows}
            roots = []
            for nid, node in nodes.items():
                # فلتر التصنيف
                if gid_filter is not None:
                    from db.accounting_repo import _get_group_descendants
                    desc = _get_group_descendants(self.conn, gid_filter)
                    if node.get("group_id") not in desc:
                        pass  # مش نفلتر الـ parents

                pid = node["parent_id"]
                if pid and pid in nodes:
                    nodes[pid].setdefault("children", []).append(node)
                else:
                    roots.append(node)

            # فاصل للنوع
            if roots:
                type_item = QTreeWidgetItem()
                type_item.setText(1, f"── {TYPE_AR.get(acc_type, acc_type)} ──")
                type_item.setForeground(1, QColor(TYPE_COLORS.get(acc_type, "#333")))
                f = type_item.font(1)
                f.setBold(True)
                type_item.setFont(1, f)
                self.tree.addTopLevelItem(type_item)
                self._add_acc_nodes(roots, type_item)
                type_item.setExpanded(True)

        self.tree.expandToDepth(2)

    def _add_acc_nodes(self, nodes, parent):
        for node in nodes:
            bal   = get_account_balance(self.conn, node["id"])
            color = TYPE_COLORS.get(node["type"], "#333")
            item  = QTreeWidgetItem()
            item.setText(0, node["code"])
            item.setText(1, node["name"])
            item.setText(2, f"{bal:,.2f}")
            item.setData(0, Qt.UserRole, node["id"])
            item.setForeground(0, QColor(color))
            # تلميح: التصنيف
            if node.get("group_name"):
                item.setToolTip(1, f"{node['name']}  |  🏷 {node['group_name']}")
            if not node.get("is_leaf", 1):
                f = item.font(1)
                f.setBold(True)
                item.setFont(1, f)
            if bal < 0:
                item.setForeground(2, QColor("#c62828"))
            elif bal > 0:
                item.setForeground(2, QColor("#2e7d32"))
            if parent:
                parent.addChild(item)
            else:
                self.tree.addTopLevelItem(item)
            if node.get("children"):
                self._add_acc_nodes(node["children"], item)

    def _selected_id(self):
        items = self.tree.selectedItems()
        if not items:
            return None
        return items[0].data(0, Qt.UserRole)

    def _add(self):
        code = self.inp_code.text().strip()
        name = self.inp_name.text().strip()
        if not code or not name:
            QMessageBox.warning(self, "تنبيه", "أدخل الكود والاسم")
            return
        acc_type  = self.cmb_type.currentData()
        group_id  = self.cmb_group.currentData()
        parent_code = code[:-1] if len(code) > 1 else None
        parent_id   = None
        if parent_code:
            row = self.conn.execute(
                "SELECT id FROM accounts WHERE code=?", (parent_code,)
            ).fetchone()
            parent_id = row["id"] if row else None
        try:
            insert_account(self.conn, code, name, acc_type, parent_id, group_id)
            self.inp_code.clear()
            self.inp_name.clear()
            bus.data_changed.emit()
        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))

    def _edit(self):
        aid = self._selected_id()
        if not aid:
            QMessageBox.information(self, "تنبيه", "اختر حسابًا أولًا")
            return
        acc = fetch_account(self.conn, aid)
        if not acc:
            return
        self._editing_id = aid
        self.inp_code.setText(acc["code"])
        self.inp_code.setReadOnly(True)
        self.inp_name.setText(acc["name"])
        # اختار النوع
        for i in range(self.cmb_type.count()):
            if self.cmb_type.itemData(i) == acc["type"]:
                self.cmb_type.setCurrentIndex(i)
                break
        self._refresh_group_combo_for_type()
        # اختار التصنيف
        for i in range(self.cmb_group.count()):
            if self.cmb_group.itemData(i) == acc["group_id"]:
                self.cmb_group.setCurrentIndex(i)
                break
        self.lbl_form_mode.setText(f"── تعديل: {acc['name']} ──")
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)

    def _save_edit(self):
        name = self.inp_name.text().strip()
        if not name or not self._editing_id:
            return
        group_id = self.cmb_group.currentData()
        update_account(self.conn, self._editing_id, name, group_id)
        self._cancel_edit()
        bus.data_changed.emit()

    def _cancel_edit(self):
        self._editing_id = None
        self.inp_code.clear()
        self.inp_code.setReadOnly(False)
        self.inp_name.clear()
        self.lbl_form_mode.setText("── حساب جديد ──")
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)

    def _delete(self):
        aid = self._selected_id()
        if not aid:
            return
        acc = fetch_account(self.conn, aid)
        if not acc:
            return
        has = self.conn.execute(
            "SELECT COUNT(*) as c FROM journal_lines WHERE account_id=?", (aid,)
        ).fetchone()["c"]
        if has:
            QMessageBox.warning(self, "تحذير",
                f"الحساب «{acc['name']}» له {has} حركة — لا يمكن حذفه.")
            return
        if confirm_delete(self, acc["name"]):
            delete_account(self.conn, aid)
            bus.data_changed.emit()


# ══════════════════════════════════════════════════════════
# تبويب القيود — بعمليتين فقط مع smart DR/CR
# ══════════════════════════════════════════════════════════

class _SmartEntryLine(QFrame):
    """
    سطر واحد في القيد:
      [حساب مع فلتر]  [زيادة/نقص]  [المبلغ]  → يعرض: DR/CR تلقائي
    """
    def __init__(self, conn, on_change=None, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._on_change = on_change
        self._build()

    def _build(self):
        self.setStyleSheet("""
            QFrame {
                background: #fafafa;
                border: 1px solid #e8e8e8;
                border-radius: 6px;
            }
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(6)

        # ── صف اختيار الحساب ──
        row1 = QHBoxLayout()
        self._acc_combo = _AccountCombo(self.conn)
        self._acc_combo.cmb_account.currentIndexChanged.connect(self._on_acc_changed)
        row1.addWidget(self._acc_combo, stretch=1)
        lay.addLayout(row1)

        # ── صف العملية + المبلغ ──
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        lbl_op = QLabel("العملية:")
        lbl_op.setStyleSheet("font-weight:bold; font-size:11px;")

        # زيادة / نقص
        self.rdo_inc = QRadioButton("➕ زيادة")
        self.rdo_dec = QRadioButton("➖ نقص")
        self.rdo_inc.setChecked(True)
        self._rdo_grp = QButtonGroup(self)
        self._rdo_grp.addButton(self.rdo_inc)
        self._rdo_grp.addButton(self.rdo_dec)
        self._rdo_grp.buttonClicked.connect(self._on_change_trigger)

        row2.addWidget(lbl_op)
        row2.addWidget(self.rdo_inc)
        row2.addWidget(self.rdo_dec)
        row2.addSpacing(16)

        # المبلغ
        lbl_amt = QLabel("المبلغ:")
        lbl_amt.setStyleSheet("font-weight:bold; font-size:11px;")
        self.sp_amount = _spin()
        self.sp_amount.setFixedWidth(130)
        self.sp_amount.valueChanged.connect(self._on_change_trigger)
        row2.addWidget(lbl_amt)
        row2.addWidget(self.sp_amount)
        row2.addSpacing(12)

        # عرض DR/CR تلقائي
        self.lbl_dr_cr = QLabel("—")
        self.lbl_dr_cr.setFixedWidth(120)
        self.lbl_dr_cr.setAlignment(Qt.AlignCenter)
        self.lbl_dr_cr.setStyleSheet(
            "font-size:12px; font-weight:bold; border-radius:4px; "
            "padding:4px 8px; background:#f5f5f5;"
        )
        row2.addWidget(self.lbl_dr_cr)
        row2.addStretch()

        # تعديل يدوي (اختياري)
        self.btn_manual = QPushButton("⚙️ يدوي")
        self.btn_manual.setCheckable(True)
        self.btn_manual.setMinimumHeight(26)
        self.btn_manual.setStyleSheet(
            "QPushButton { background:#f5f5f5; border:1px solid #ccc;"
            "border-radius:4px; font-size:10px; padding:2px 6px; }"
            "QPushButton:checked { background:#fff3e0; border-color:#e65100;"
            "color:#e65100; }"
        )
        self.btn_manual.toggled.connect(self._toggle_manual)
        row2.addWidget(self.btn_manual)
        lay.addLayout(row2)

        # ── صف التعديل اليدوي (مخفي افتراضيًا) ──
        self._manual_frame = QFrame()
        self._manual_frame.setStyleSheet(
            "QFrame { background:#fff8e1; border:1px solid #ffe082;"
            "border-radius:4px; }"
        )
        ml = QHBoxLayout(self._manual_frame)
        ml.setContentsMargins(8, 4, 8, 4)

        lbl_m = QLabel("⚙️ تحديد يدوي:")
        lbl_m.setStyleSheet("font-size:10px; color:#e65100; font-weight:bold;")
        self.rdo_dr = QRadioButton("مدين (DR)")
        self.rdo_cr = QRadioButton("دائن (CR)")
        self.rdo_dr.setChecked(True)
        grp2 = QButtonGroup(self)
        grp2.addButton(self.rdo_dr)
        grp2.addButton(self.rdo_cr)
        grp2.buttonClicked.connect(self._on_change_trigger)

        ml.addWidget(lbl_m)
        ml.addWidget(self.rdo_dr)
        ml.addWidget(self.rdo_cr)
        ml.addStretch()
        self._manual_frame.setVisible(False)
        lay.addWidget(self._manual_frame)

        # بيان
        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("بيان (اختياري)...")
        self.inp_desc.setMinimumHeight(26)
        lay.addWidget(self.inp_desc)

    def _on_acc_changed(self):
        self._update_dr_cr_label()
        if self._on_change:
            self._on_change()

    def _on_change_trigger(self):
        self._update_dr_cr_label()
        if self._on_change:
            self._on_change()

    def _toggle_manual(self, checked):
        self._manual_frame.setVisible(checked)
        self._update_dr_cr_label()

    def _update_dr_cr_label(self):
        acc_id  = self._acc_combo.current_account_id()
        amount  = self.sp_amount.value()
        if not acc_id:
            self.lbl_dr_cr.setText("—")
            self.lbl_dr_cr.setStyleSheet(
                "font-size:12px; font-weight:bold; border-radius:4px; "
                "padding:4px 8px; background:#f5f5f5;"
            )
            return

        dr, cr = self.get_debit_credit()
        if dr > 0:
            self.lbl_dr_cr.setText(f"DR  {dr:,.2f}")
            self.lbl_dr_cr.setStyleSheet(
                "font-size:11px; font-weight:bold; color:#1565c0;"
                "background:#e3f2fd; border-radius:4px; padding:4px 8px;"
            )
        elif cr > 0:
            self.lbl_dr_cr.setText(f"CR  {cr:,.2f}")
            self.lbl_dr_cr.setStyleSheet(
                "font-size:11px; font-weight:bold; color:#c62828;"
                "background:#fdecea; border-radius:4px; padding:4px 8px;"
            )
        else:
            self.lbl_dr_cr.setText("0.00")
            self.lbl_dr_cr.setStyleSheet(
                "font-size:12px; font-weight:bold; border-radius:4px; "
                "padding:4px 8px; background:#f5f5f5;"
            )

    def get_debit_credit(self) -> tuple:
        """يرجع (debit, credit) بناءً على نوع الحساب والعملية."""
        acc_id = self._acc_combo.current_account_id()
        amount = self.sp_amount.value()
        if not acc_id or amount == 0:
            return 0.0, 0.0

        if self.btn_manual.isChecked():
            # تحكم يدوي
            if self.rdo_dr.isChecked():
                return amount, 0.0
            else:
                return 0.0, amount
        else:
            # تلقائي
            acc = fetch_account(self.conn, acc_id)
            if not acc:
                return 0.0, 0.0
            increase = self.rdo_inc.isChecked()
            return calc_signed_amount(acc["type"], increase, amount)

    def get_values(self) -> dict | None:
        acc_id = self._acc_combo.current_account_id()
        if not acc_id:
            return None
        dr, cr = self.get_debit_credit()
        return {
            "account_id":  acc_id,
            "debit":       dr,
            "credit":      cr,
            "description": self.inp_desc.text().strip(),
        }

    def clear(self):
        self._acc_combo.cmb_account.setCurrentIndex(0)
        self.rdo_inc.setChecked(True)
        self.sp_amount.setValue(0)
        self.inp_desc.clear()
        self.btn_manual.setChecked(False)
        self.lbl_dr_cr.setText("—")


class JournalTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        bus.data_changed.connect(self._load_table)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)

        # ── فورم القيد ──
        form_w = QWidget()
        fl     = QVBoxLayout(form_w)
        fl.setContentsMargins(12, 10, 12, 10)
        fl.setSpacing(8)

        self.lbl_mode = QLabel("── قيد يومية جديد ──")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0; font-size:12px;")
        fl.addWidget(self.lbl_mode)

        # صف التاريخ والوصف
        info_row = QHBoxLayout()
        self.dt_date = QDateEdit(QDate.currentDate())
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDisplayFormat("yyyy-MM-dd")
        self.dt_date.setFixedWidth(130)
        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("وصف القيد...")
        self.inp_desc.setMinimumHeight(30)
        self.cmb_type = QComboBox()
        self.cmb_type.setMinimumHeight(30)
        self.cmb_type.setFixedWidth(120)
        for key, label in [
            ("manual","يدوي"),("purchase","شراء"),("sale","بيع"),
            ("payment","دفع"),("receipt","تحصيل"),("adjustment","تسوية")
        ]:
            self.cmb_type.addItem(label, key)
        info_row.addWidget(QLabel("التاريخ:"))
        info_row.addWidget(self.dt_date)
        info_row.addWidget(QLabel("النوع:"))
        info_row.addWidget(self.cmb_type)
        info_row.addWidget(self.inp_desc, stretch=1)
        fl.addLayout(info_row)

        # ── العمليتان ──
        self.line1 = _SmartEntryLine(self.conn, on_change=self._update_balance)
        self.line2 = _SmartEntryLine(self.conn, on_change=self._update_balance)

        lbl1 = QLabel("العملية الأولى:")
        lbl2 = QLabel("العملية الثانية (المقابلة):")
        for l in (lbl1, lbl2):
            l.setStyleSheet("font-weight:bold; font-size:11px; color:#555;")

        fl.addWidget(lbl1)
        fl.addWidget(self.line1)
        fl.addWidget(lbl2)
        fl.addWidget(self.line2)

        # ملخص التوازن
        bal_row = QHBoxLayout()
        self.lbl_sum_d  = QLabel("مدين: 0.00")
        self.lbl_sum_c  = QLabel("دائن: 0.00")
        self.lbl_bal_st = QLabel("—")
        for l in (self.lbl_sum_d, self.lbl_sum_c, self.lbl_bal_st):
            l.setStyleSheet("font-weight:bold; font-size:11px;")
        bal_row.addWidget(self.lbl_sum_d)
        bal_row.addSpacing(16)
        bal_row.addWidget(self.lbl_sum_c)
        bal_row.addSpacing(16)
        bal_row.addWidget(self.lbl_bal_st)
        bal_row.addStretch()
        fl.addLayout(bal_row)

        btn_save  = QPushButton("💾 حفظ القيد")
        btn_save.setMinimumHeight(32)
        btn_save.setStyleSheet("""
            QPushButton { background:#1565c0; color:white;
                font-weight:bold; border-radius:6px; padding:0 18px; }
            QPushButton:hover { background:#0d47a1; }
        """)
        btn_save.clicked.connect(self._save)
        btn_clear = QPushButton("✖ مسح")
        btn_clear.setMinimumHeight(32)
        btn_clear.clicked.connect(self._clear_form)
        fl.addLayout(buttons_row(btn_save, btn_clear))
        splitter.addWidget(form_w)

        # ── جدول القيود ──
        table_w = QWidget()
        tl = QVBoxLayout(table_w)
        tl.setContentsMargins(12, 8, 12, 12)
        tl.setSpacing(6)
        tl.addWidget(section_label("── القيود المحاسبية ──"))

        self.table = make_table(
            ["#","رقم القيد","التاريخ","النوع","البيان","مدين","دائن"],
            stretch_col=4
        )
        setup_table_columns(self.table,
            widths={0:40,1:90,2:90,3:80,5:90,6:90}, stretch_col=4)
        self.table.setAlternatingRowColors(True)
        tl.addWidget(self.table, stretch=1)

        btn_del = danger_button("🗑️ حذف القيد")
        btn_del.setMinimumHeight(30)
        btn_del.clicked.connect(self._delete_entry)
        tl.addLayout(buttons_row(btn_del))
        splitter.addWidget(table_w)

        splitter.setSizes([400, 350])
        root.addWidget(splitter)

        self._load_table()

    def _update_balance(self):
        v1 = self.line1.get_values()
        v2 = self.line2.get_values()
        td = (v1["debit"]  if v1 else 0) + (v2["debit"]  if v2 else 0)
        tc = (v1["credit"] if v1 else 0) + (v2["credit"] if v2 else 0)
        self.lbl_sum_d.setText(f"مدين: {td:,.2f}")
        self.lbl_sum_c.setText(f"دائن: {tc:,.2f}")
        diff = abs(td - tc)
        if diff < 0.001 and td > 0:
            self.lbl_bal_st.setText("✅ متوازن")
            self.lbl_bal_st.setStyleSheet("font-weight:bold; color:#2e7d32;")
        else:
            self.lbl_bal_st.setText(f"⚠️ فرق: {diff:,.2f}" if td > 0 else "—")
            self.lbl_bal_st.setStyleSheet("font-weight:bold; color:#c62828;")

    def _save(self):
        v1 = self.line1.get_values()
        v2 = self.line2.get_values()
        if not v1 or not v2:
            QMessageBox.warning(self, "تنبيه", "اختر الحسابين أولًا")
            return
        if v1["account_id"] == v2["account_id"]:
            QMessageBox.warning(self, "تنبيه", "لا يمكن استخدام نفس الحساب في العمليتين")
            return
        lines = [v1, v2]
        if not validate_entry_balance(lines):
            QMessageBox.warning(self, "خطأ", "مجموع المدين ≠ مجموع الدائن\nتحقق من المبالغ")
            return
        desc = self.inp_desc.text().strip()
        if not desc:
            QMessageBox.warning(self, "تنبيه", "أدخل وصف القيد")
            return
        entry_id = insert_entry(
            self.conn,
            self.dt_date.date().toString("yyyy-MM-dd"),
            desc,
            self.cmb_type.currentData()
        )
        add_entry_lines(self.conn, entry_id, lines)
        self._clear_form()
        bus.data_changed.emit()
        QMessageBox.information(self, "تم", "✅ تم حفظ القيد")

    def _clear_form(self):
        self.line1.clear()
        self.line2.clear()
        self.inp_desc.clear()
        self.dt_date.setDate(QDate.currentDate())
        self._update_balance()

    def _load_table(self):
        entries = fetch_all_entries(self.conn)
        self.table.setRowCount(0)
        type_ar = {
            "manual":"يدوي","purchase":"شراء","sale":"بيع",
            "payment":"دفع","receipt":"تحصيل","adjustment":"تسوية"
        }
        for e in entries:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(e["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(e["ref_no"]))
            self.table.setItem(r, 2, QTableWidgetItem(e["date"]))
            self.table.setItem(r, 3, QTableWidgetItem(type_ar.get(e["type"], e["type"])))
            di = QTableWidgetItem(e["description"])
            di.setToolTip(e["description"])
            self.table.setItem(r, 4, di)
            self.table.setItem(r, 5, QTableWidgetItem(f"{e['total_debit']:,.2f}"))
            self.table.setItem(r, 6, QTableWidgetItem(f"{e['total_credit']:,.2f}"))

    def _delete_entry(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر قيدًا أولًا")
            return
        eid  = int(self.table.item(row, 0).text())
        desc = self.table.item(row, 4).text()
        if confirm_delete(self, desc):
            delete_entry(self.conn, eid)
            bus.data_changed.emit()


# ══════════════════════════════════════════════════════════
# دفتر الأستاذ T-Accounts
# ══════════════════════════════════════════════════════════

class LedgerTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        bus.data_changed.connect(self._refresh_accounts)

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)

        # يسار: قائمة الحسابات
        left = QWidget()
        ll   = QVBoxLayout(left)
        ll.setContentsMargins(10, 8, 6, 10)
        ll.setSpacing(6)
        ll.addWidget(section_label("── الحسابات ──"))

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 بحث...")
        self.inp_search.setMinimumHeight(28)
        self.inp_search.textChanged.connect(self._filter_accounts)
        ll.addWidget(self.inp_search)

        self.lst = QTreeWidget()
        self.lst.setHeaderLabels(["الكود","الاسم"])
        self.lst.setColumnWidth(0, 70)
        self.lst.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.lst.itemSelectionChanged.connect(self._on_selected)
        ll.addWidget(self.lst, stretch=1)
        splitter.addWidget(left)

        # يمين: T-Account
        right = QWidget()
        rl    = QVBoxLayout(right)
        rl.setContentsMargins(6, 8, 10, 10)
        rl.setSpacing(8)

        self.lbl_title = QLabel("اختر حسابًا لعرض حركاته")
        self.lbl_title.setStyleSheet(
            "font-size:13px; font-weight:bold; color:#1565c0;"
            "background:#e8f4fd; border:1px solid #90caf9;"
            "border-radius:6px; padding:8px 16px;"
        )
        self.lbl_title.setAlignment(Qt.AlignCenter)
        rl.addWidget(self.lbl_title)

        t_frame = QFrame()
        t_frame.setStyleSheet("QFrame { background:white; border:2px solid #1565c0; border-radius:8px; }")
        t_lay   = QHBoxLayout(t_frame)
        t_lay.setContentsMargins(0, 0, 0, 0)
        t_lay.setSpacing(0)

        def _t_side(title, color, bg):
            w = QWidget()
            w.setStyleSheet("background:transparent;")
            l = QVBoxLayout(w)
            l.setContentsMargins(8, 8, 4, 8)
            hdr = QLabel(title)
            hdr.setAlignment(Qt.AlignCenter)
            hdr.setStyleSheet(
                f"font-weight:bold; color:{color}; font-size:12px;"
                f"background:{bg}; border-radius:4px; padding:4px;"
            )
            tbl = make_table(["البيان","المبلغ"], stretch_col=0)
            tbl.setColumnWidth(1, 100)
            total = QLabel("الإجمالي: 0.00")
            total.setAlignment(Qt.AlignCenter)
            total.setStyleSheet(
                f"font-weight:bold; color:{color}; font-size:11px;"
                f"background:{bg}; border-radius:4px; padding:4px 8px;"
            )
            l.addWidget(hdr)
            l.addWidget(tbl, stretch=1)
            l.addWidget(total)
            return w, tbl, total

        left_t,  self.t_dr_table,  self.lbl_dr_total  = _t_side("مدين (DR)",  "#1565c0", "#e8f4fd")
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color:#1565c0;")
        right_t, self.t_cr_table, self.lbl_cr_total = _t_side("دائن (CR)", "#c62828", "#fdecea")
        for w in (left_t, sep, right_t):
            t_lay.addWidget(w if w is not sep else sep, stretch=0 if w is sep else 1)
        rl.addWidget(t_frame, stretch=1)

        self.lbl_balance = QLabel("الرصيد: —")
        self.lbl_balance.setAlignment(Qt.AlignCenter)
        self.lbl_balance.setStyleSheet(
            "font-size:13px; font-weight:bold; color:#2e7d32;"
            "background:#f0faf0; border:1px solid #a5d6a7;"
            "border-radius:6px; padding:6px 16px;"
        )
        rl.addWidget(self.lbl_balance)

        splitter.addWidget(right)
        splitter.setSizes([220, 580])
        root.addWidget(splitter)
        self._refresh_accounts()

    def _refresh_accounts(self):
        self._all = fetch_all_accounts(self.conn)
        self._filter_accounts()

    def _filter_accounts(self):
        q = self.inp_search.text().strip().lower()
        self.lst.clear()
        for acc in self._all:
            if not acc["is_leaf"]:
                continue
            if q and q not in acc["name"].lower() and q not in acc["code"].lower():
                continue
            item = QTreeWidgetItem()
            item.setText(0, acc["code"])
            item.setText(1, acc["name"])
            item.setData(0, Qt.UserRole, acc["id"])
            item.setForeground(0, QColor(TYPE_COLORS.get(acc["type"], "#333")))
            self.lst.addTopLevelItem(item)

    def _on_selected(self):
        items = self.lst.selectedItems()
        if not items:
            return
        aid = items[0].data(0, Qt.UserRole)
        data = fetch_t_account(self.conn, aid)
        if not data:
            return
        acc   = data["account"]
        lines = data["lines"]
        color = TYPE_COLORS.get(acc["type"], "#1565c0")
        nb    = data["normal_balance"]
        self.lbl_title.setText(
            f"حساب: {acc['code']} — {acc['name']}  │  "
            f"{TYPE_AR.get(acc['type'],'')}  │  "
            f"رصيد طبيعي: {'DR↑' if nb=='dr' else 'CR↑'}"
        )
        self.t_dr_table.setRowCount(0)
        self.t_cr_table.setRowCount(0)
        for line in lines:
            if line["debit"] > 0:
                r = self.t_dr_table.rowCount()
                self.t_dr_table.insertRow(r)
                d = QTableWidgetItem(f"{line['date']}  {line['entry_desc']}")
                d.setToolTip(f"{line['date']}  {line['entry_desc']}")
                self.t_dr_table.setItem(r, 0, d)
                self.t_dr_table.setItem(r, 1, QTableWidgetItem(f"{line['debit']:,.2f}"))
            if line["credit"] > 0:
                r = self.t_cr_table.rowCount()
                self.t_cr_table.insertRow(r)
                c = QTableWidgetItem(f"{line['date']}  {line['entry_desc']}")
                c.setToolTip(f"{line['date']}  {line['entry_desc']}")
                self.t_cr_table.setItem(r, 0, c)
                self.t_cr_table.setItem(r, 1, QTableWidgetItem(f"{line['credit']:,.2f}"))

        self.lbl_dr_total.setText(f"الإجمالي: {data['total_debit']:,.2f}")
        self.lbl_cr_total.setText(f"الإجمالي: {data['total_credit']:,.2f}")

        bal    = data["balance"]
        b_side = "مدين" if bal >= 0 else "دائن"
        self.lbl_balance.setText(f"الرصيد ({b_side}): {abs(bal):,.2f}  ج")
        b_color = "#1565c0" if bal >= 0 else "#c62828"
        self.lbl_balance.setStyleSheet(
            f"font-size:13px; font-weight:bold; color:{b_color};"
            "background:#f0f8ff; border:1px solid #90caf9;"
            "border-radius:6px; padding:6px 16px;"
        )


# ══════════════════════════════════════════════════════════
# ميزان المراجعة
# ══════════════════════════════════════════════════════════

class TrialBalanceTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(8)
        root.addWidget(section_label("── ميزان المراجعة ──"))

        self.table = make_table(
            ["الكود","اسم الحساب","النوع","مجموع المدين","مجموع الدائن","الرصيد"],
            stretch_col=1
        )
        setup_table_columns(self.table,
            widths={0:70,2:100,3:120,4:120,5:110}, stretch_col=1)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, stretch=1)

        totals = QFrame()
        totals.setStyleSheet(
            "QFrame { background:#f0f4ff; border:1px solid #c5cae9; border-radius:6px; }"
        )
        tl = QHBoxLayout(totals)
        tl.setContentsMargins(12, 8, 12, 8)
        self.lbl_sum_d  = QLabel("مجموع المدين: 0.00")
        self.lbl_sum_c  = QLabel("مجموع الدائن: 0.00")
        self.lbl_status = QLabel("─")
        for l in (self.lbl_sum_d, self.lbl_sum_c, self.lbl_status):
            l.setStyleSheet("font-weight:bold; font-size:12px;")
        tl.addWidget(self.lbl_sum_d)
        tl.addSpacing(24)
        tl.addWidget(self.lbl_sum_c)
        tl.addSpacing(24)
        tl.addWidget(self.lbl_status)
        tl.addStretch()
        root.addWidget(totals)

    def _load(self):
        rows = trial_balance(self.conn)
        self.table.setRowCount(0)
        sd = sc = 0.0
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(row["code"]))
            ni = QTableWidgetItem(row["name"])
            ni.setToolTip(row["name"])
            self.table.setItem(r, 1, ni)
            self.table.setItem(r, 2, QTableWidgetItem(TYPE_AR.get(row["type"], row["type"])))
            self.table.setItem(r, 3, QTableWidgetItem(f"{row['total_debit']:,.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"{row['total_credit']:,.2f}"))
            bi = QTableWidgetItem(f"{row['balance']:,.2f}")
            if row["balance"] < 0:
                bi.setForeground(QColor("#c62828"))
            self.table.setItem(r, 5, bi)
            sd += row["total_debit"]
            sc += row["total_credit"]
        self.lbl_sum_d.setText(f"مجموع المدين: {sd:,.2f}")
        self.lbl_sum_c.setText(f"مجموع الدائن: {sc:,.2f}")
        diff = abs(sd - sc)
        if diff < 0.01:
            self.lbl_status.setText("✅ الميزان متوازن")
            self.lbl_status.setStyleSheet("font-weight:bold; color:#2e7d32;")
        else:
            self.lbl_status.setText(f"⚠️ فرق: {diff:,.2f}")
            self.lbl_status.setStyleSheet("font-weight:bold; color:#c62828;")


# ══════════════════════════════════════════════════════════
# القوائم المالية
# ══════════════════════════════════════════════════════════

def _stat_card(label, color="#1565c0"):
    f = QFrame()
    f.setStyleSheet(f"""
        QFrame {{ background:white; border-left:4px solid {color}; border-radius:6px; }}
    """)
    l = QVBoxLayout(f)
    l.setContentsMargins(12, 8, 12, 8)
    lt = QLabel(label)
    lt.setStyleSheet("font-size:10px; color:#888; background:transparent; border:none;")
    lv = QLabel("0.00  ج")
    lv.setStyleSheet(
        f"font-size:14px; font-weight:bold; color:{color}; background:transparent; border:none;"
    )
    l.addWidget(lt)
    l.addWidget(lv)
    return f, lv


class IncomeStatementTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(10)

        hdr = QLabel("📊  قائمة الدخل")
        hdr.setStyleSheet(
            "font-size:15px; font-weight:bold; color:#6a1b9a;"
            "background:#f3e5f5; border:1px solid #ce93d8;"
            "border-radius:8px; padding:8px 16px;"
        )
        hdr.setAlignment(Qt.AlignCenter)
        root.addWidget(hdr)

        cards = QHBoxLayout()
        f1, self.lbl_rev = _stat_card("إجمالي الإيرادات",    "#6a1b9a")
        f2, self.lbl_exp = _stat_card("إجمالي المصروفات",    "#e65100")
        f3, self.lbl_net = _stat_card("صافي الربح / الخسارة","#1b5e20")
        for f in (f1, f2, f3):
            cards.addWidget(f, stretch=1)
        root.addLayout(cards)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)

        for attr_name, title, color, type_ in [
            ("table_rev", "💹 الإيرادات", "#6a1b9a", "revenue"),
            ("table_exp", "📤 المصروفات", "#e65100", "expense"),
        ]:
            w  = QWidget()
            wl = QVBoxLayout(w)
            wl.setContentsMargins(0, 4, 4, 0)
            wl.addWidget(section_label(title))
            tbl = make_table(["الكود","البند","المبلغ"], stretch_col=1)
            tbl.setColumnWidth(0, 60)
            tbl.setColumnWidth(2, 110)
            setattr(self, attr_name, tbl)
            wl.addWidget(tbl)
            splitter.addWidget(w)

        root.addWidget(splitter, stretch=1)

    def _load(self):
        data = income_statement(self.conn)
        for tbl, rows, color in [
            (self.table_rev, data["revenues"], "#6a1b9a"),
            (self.table_exp, data["expenses"], "#e65100"),
        ]:
            tbl.setRowCount(0)
            for row in rows:
                r = tbl.rowCount()
                tbl.insertRow(r)
                tbl.setItem(r, 0, QTableWidgetItem(row["code"]))
                n = QTableWidgetItem(row["name"])
                n.setToolTip(row["name"])
                tbl.setItem(r, 1, n)
                ai = QTableWidgetItem(f"{row['amount']:,.2f}")
                ai.setForeground(QColor(color))
                tbl.setItem(r, 2, ai)

        self.lbl_rev.setText(_money(data["total_rev"]))
        self.lbl_exp.setText(_money(data["total_exp"]))
        net   = data["net_income"]
        color = "#1b5e20" if net >= 0 else "#b71c1c"
        self.lbl_net.setText(_money(net))
        self.lbl_net.setStyleSheet(
            f"font-size:14px; font-weight:bold; color:{color};"
            "background:transparent; border:none;"
        )


class OwnersEquityTab(QWidget):
    """
    قائمة حقوق الملكية المفصلة:
      ── يزيد بـ CR (رصيد طبيعي دائن) ──
        Capital (رأس المال)
        Revenue (الإيرادات) — صافي الدخل
      ── يزيد بـ DR (رصيد طبيعي مدين) ──
        Expenses (المصروفات)
        Drawings (المسحوبات)
    """
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(10)

        hdr = QLabel("👑  قائمة حقوق الملكية")
        hdr.setStyleSheet(
            "font-size:15px; font-weight:bold; color:#2e7d32;"
            "background:#f1f8e9; border:1px solid #a5d6a7;"
            "border-radius:8px; padding:8px 16px;"
        )
        hdr.setAlignment(Qt.AlignCenter)
        root.addWidget(hdr)

        cards = QHBoxLayout()
        f1, self.lbl_cap   = _stat_card("رأس المال",              "#2e7d32")
        f2, self.lbl_ni    = _stat_card("صافي الدخل",             "#1b5e20")
        f3, self.lbl_draw  = _stat_card("المسحوبات",              "#4e342e")
        f4, self.lbl_total = _stat_card("صافي حقوق الملكية",      "#1565c0")
        for f in (f1, f2, f3, f4):
            cards.addWidget(f, stretch=1)
        root.addLayout(cards)

        # جدولين: CR side و DR side
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)

        # جانب CR (Capital + Revenue)
        left_w  = QWidget()
        ll = QVBoxLayout(left_w)
        ll.setContentsMargins(0, 4, 4, 0)

        cr_hdr = QLabel("📈 ما يزيد حقوق الملكية (CR↑)")
        cr_hdr.setStyleSheet(
            "font-weight:bold; color:#2e7d32; font-size:11px;"
            "background:#f1f8e9; border-radius:4px; padding:4px 8px;"
        )
        ll.addWidget(cr_hdr)
        self.table_cr = make_table(["الكود","البند","النوع","المبلغ"], stretch_col=1)
        self.table_cr.setColumnWidth(0, 60)
        self.table_cr.setColumnWidth(2, 80)
        self.table_cr.setColumnWidth(3, 100)
        ll.addWidget(self.table_cr)
        splitter.addWidget(left_w)

        # جانب DR (Expenses + Drawings)
        right_w = QWidget()
        rl = QVBoxLayout(right_w)
        rl.setContentsMargins(4, 4, 0, 0)

        dr_hdr = QLabel("📉 ما ينقص حقوق الملكية (DR↑)")
        dr_hdr.setStyleSheet(
            "font-weight:bold; color:#c62828; font-size:11px;"
            "background:#fdecea; border-radius:4px; padding:4px 8px;"
        )
        rl.addWidget(dr_hdr)
        self.table_dr = make_table(["الكود","البند","النوع","المبلغ"], stretch_col=1)
        self.table_dr.setColumnWidth(0, 60)
        self.table_dr.setColumnWidth(2, 80)
        self.table_dr.setColumnWidth(3, 100)
        rl.addWidget(self.table_dr)
        splitter.addWidget(right_w)

        root.addWidget(splitter, stretch=1)

        # ملخص المعادلة
        eq_frame = QFrame()
        eq_frame.setStyleSheet(
            "QFrame { background:#e8f4fd; border:1px solid #90caf9; border-radius:6px; }"
        )
        eq_lay = QHBoxLayout(eq_frame)
        eq_lay.setContentsMargins(12, 8, 12, 8)
        self.lbl_equation = QLabel("")
        self.lbl_equation.setStyleSheet(
            "font-size:12px; font-weight:bold; color:#1565c0; background:transparent; border:none;"
        )
        eq_lay.addWidget(self.lbl_equation)
        root.addWidget(eq_frame)

    def _load(self):
        data = owners_equity_statement(self.conn)

        # جانب CR: Capital + صافي الدخل
        self.table_cr.setRowCount(0)
        for row in data["capital_accounts"]:
            r = self.table_cr.rowCount()
            self.table_cr.insertRow(r)
            self.table_cr.setItem(r, 0, QTableWidgetItem(row["code"]))
            n = QTableWidgetItem(row["name"])
            n.setToolTip(row["name"])
            self.table_cr.setItem(r, 1, n)
            self.table_cr.setItem(r, 2, QTableWidgetItem("رأس المال"))
            ai = QTableWidgetItem(f"{row['amount']:,.2f}")
            ai.setForeground(QColor("#2e7d32"))
            self.table_cr.setItem(r, 3, ai)

        # صافي الدخل في جانب CR
        ni = data["net_income"]
        r  = self.table_cr.rowCount()
        self.table_cr.insertRow(r)
        self.table_cr.setItem(r, 0, QTableWidgetItem(""))
        self.table_cr.setItem(r, 1, QTableWidgetItem("صافي الدخل للفترة"))
        self.table_cr.setItem(r, 2, QTableWidgetItem("إيرادات - مصروفات"))
        ni_item = QTableWidgetItem(f"{ni:,.2f}")
        ni_item.setForeground(QColor("#1b5e20") if ni >= 0 else QColor("#b71c1c"))
        self.table_cr.setItem(r, 3, ni_item)

        # جانب DR: Drawings + Expenses
        self.table_dr.setRowCount(0)
        for row in data["drawings_accounts"]:
            r = self.table_dr.rowCount()
            self.table_dr.insertRow(r)
            self.table_dr.setItem(r, 0, QTableWidgetItem(row["code"]))
            n = QTableWidgetItem(row["name"])
            n.setToolTip(row["name"])
            self.table_dr.setItem(r, 1, n)
            self.table_dr.setItem(r, 2, QTableWidgetItem("مسحوبات"))
            ai = QTableWidgetItem(f"{row['amount']:,.2f}")
            ai.setForeground(QColor("#4e342e"))
            self.table_dr.setItem(r, 3, ai)

        # الإحصائيات
        self.lbl_cap.setText(_money(data["total_capital"]))
        self.lbl_ni.setText(_money(ni))
        self.lbl_draw.setText(_money(data["total_drawings"]))
        total = data["total_equity"]
        self.lbl_total.setText(_money(total))
        tc = "#1565c0" if total >= 0 else "#b71c1c"
        self.lbl_total.setStyleSheet(
            f"font-size:14px; font-weight:bold; color:{tc}; background:transparent; border:none;"
        )

        # المعادلة
        self.lbl_equation.setText(
            f"رأس المال  {data['total_capital']:,.2f}  +  "
            f"صافي الدخل  {ni:,.2f}  −  "
            f"المسحوبات  {data['total_drawings']:,.2f}  =  "
            f"صافي حقوق الملكية  {total:,.2f}"
        )


class BalanceSheetTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(10)

        hdr = QLabel("🏛️  الميزانية العمومية")
        hdr.setStyleSheet(
            "font-size:15px; font-weight:bold; color:#1565c0;"
            "background:#e8f4fd; border:1px solid #90caf9;"
            "border-radius:8px; padding:8px 16px;"
        )
        hdr.setAlignment(Qt.AlignCenter)
        root.addWidget(hdr)

        cards = QHBoxLayout()
        f1, self.lbl_assets  = _stat_card("إجمالي الأصول",  "#1565c0")
        f2, self.lbl_liab    = _stat_card("إجمالي الخصوم",  "#c62828")
        f3, self.lbl_equity  = _stat_card("حقوق الملكية",   "#2e7d32")
        self.lbl_balanced    = QLabel("✅ متوازنة")
        self.lbl_balanced.setStyleSheet("font-weight:bold; color:#2e7d32; font-size:12px;")
        self.lbl_balanced.setAlignment(Qt.AlignCenter)
        for f in (f1, f2, f3):
            cards.addWidget(f, stretch=1)
        cards.addWidget(self.lbl_balanced)
        root.addLayout(cards)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)

        w1 = QWidget()
        l1 = QVBoxLayout(w1)
        l1.setContentsMargins(0, 4, 4, 0)
        l1.addWidget(section_label("🏦 الأصول"))
        self.table_assets = make_table(["الكود","البند","المبلغ"], stretch_col=1)
        self.table_assets.setColumnWidth(0, 60)
        self.table_assets.setColumnWidth(2, 110)
        l1.addWidget(self.table_assets)
        splitter.addWidget(w1)

        w2 = QWidget()
        l2 = QVBoxLayout(w2)
        l2.setContentsMargins(4, 4, 0, 0)
        l2.addWidget(section_label("📋 الخصوم وحقوق الملكية"))
        self.table_liab = make_table(["الكود","البند","المبلغ","النوع"], stretch_col=1)
        self.table_liab.setColumnWidth(0, 60)
        self.table_liab.setColumnWidth(2, 110)
        self.table_liab.setColumnWidth(3, 80)
        l2.addWidget(self.table_liab)
        splitter.addWidget(w2)

        root.addWidget(splitter, stretch=1)

    def _load(self):
        data = balance_sheet(self.conn)

        self.table_assets.setRowCount(0)
        for row in data["assets"]:
            r = self.table_assets.rowCount()
            self.table_assets.insertRow(r)
            self.table_assets.setItem(r, 0, QTableWidgetItem(row["code"]))
            n = QTableWidgetItem(row["name"])
            n.setToolTip(row["name"])
            self.table_assets.setItem(r, 1, n)
            ai = QTableWidgetItem(f"{row['amount']:,.2f}")
            ai.setForeground(QColor("#1565c0"))
            self.table_assets.setItem(r, 2, ai)

        self.table_liab.setRowCount(0)
        for row, label, color in [
            *[(r, "خصوم",       "#c62828") for r in data["liabilities"]],
            *[(r, "رأس المال",  "#2e7d32") for r in data["capital"]],
            *[(r, "مسحوبات",   "#4e342e") for r in data["drawings"]],
        ]:
            r2 = self.table_liab.rowCount()
            self.table_liab.insertRow(r2)
            self.table_liab.setItem(r2, 0, QTableWidgetItem(row["code"]))
            n = QTableWidgetItem(row["name"])
            n.setToolTip(row["name"])
            self.table_liab.setItem(r2, 1, n)
            ai = QTableWidgetItem(f"{row['amount']:,.2f}")
            ai.setForeground(QColor(color))
            self.table_liab.setItem(r2, 2, ai)
            self.table_liab.setItem(r2, 3, QTableWidgetItem(label))

        # صافي الدخل
        ni = data["net_income"]
        if ni != 0:
            r2 = self.table_liab.rowCount()
            self.table_liab.insertRow(r2)
            self.table_liab.setItem(r2, 0, QTableWidgetItem(""))
            self.table_liab.setItem(r2, 1, QTableWidgetItem("صافي الدخل"))
            ni_item = QTableWidgetItem(f"{ni:,.2f}")
            ni_item.setForeground(QColor("#1b5e20" if ni >= 0 else "#b71c1c"))
            self.table_liab.setItem(r2, 2, ni_item)
            self.table_liab.setItem(r2, 3, QTableWidgetItem("حقوق ملكية"))

        self.lbl_assets.setText(_money(data["total_assets"]))
        self.lbl_liab.setText(_money(data["total_liab"]))
        self.lbl_equity.setText(_money(data["total_equity"]))

        diff = abs(data["total_assets"] - (data["total_liab"] + data["total_equity"]))
        if diff < 0.01:
            self.lbl_balanced.setText("✅ الميزانية متوازنة")
            self.lbl_balanced.setStyleSheet("font-weight:bold; color:#2e7d32; font-size:12px;")
        else:
            self.lbl_balanced.setText(f"⚠️ فرق: {diff:,.2f}")
            self.lbl_balanced.setStyleSheet("font-weight:bold; color:#c62828; font-size:12px;")


class FinancialStatementsTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        tabs = QTabWidget()
        tabs.setStyleSheet(
            "QTabBar::tab:selected { color:#1565c0; border-top:2px solid #1565c0; }"
        )
        tabs.addTab(IncomeStatementTab(self.conn), "📊 قائمة الدخل")
        tabs.addTab(OwnersEquityTab(self.conn),    "👑 حقوق الملكية")
        tabs.addTab(BalanceSheetTab(self.conn),    "🏛️ الميزانية العمومية")
        root.addWidget(tabs)


# ══════════════════════════════════════════════════════════
# التبويب الرئيسي
# ══════════════════════════════════════════════════════════

class AccountingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn = get_accounting_connection()
        self._init_schema()
        self._build()

    def _init_schema(self):
        from db.accounting_schema import create_accounting_tables
        create_accounting_tables(self.conn)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border:none; background:#f9f9f9; }
            QTabBar::tab {
                background:#f0f0f0; border:1px solid #ddd;
                border-bottom:none; padding:8px 14px;
                margin-left:2px; font-size:11px; color:#555;
            }
            QTabBar::tab:selected {
                background:#fff; color:#1565c0;
                font-weight:bold; border-top:2px solid #1565c0;
            }
            QTabBar::tab:hover:!selected { background:#e8f0fe; color:#1565c0; }
        """)

        # أصول
        asset_tab = QTabWidget()
        asset_tab.addTab(
            AccountsTreePanel(self.conn, ["asset"], "الأصول"), "📊 الحسابات"
        )
        asset_tab.addTab(
            _GroupManagerPanel(self.conn, "asset"), "🏷️ التصنيفات"
        )
        tabs.addTab(asset_tab, "🏦 الأصول")

        # خصوم
        liab_tab = QTabWidget()
        liab_tab.addTab(
            AccountsTreePanel(self.conn, ["liability"], "الخصوم"), "📊 الحسابات"
        )
        liab_tab.addTab(
            _GroupManagerPanel(self.conn, "liability"), "🏷️ التصنيفات"
        )
        tabs.addTab(liab_tab, "📋 الخصوم")

        # حقوق الملكية (Capital + Drawings)
        eq_tab = QTabWidget()
        eq_tab.addTab(
            AccountsTreePanel(self.conn,
                              ["capital","drawings","revenue","expense"],
                              "حقوق الملكية"),
            "📊 الحسابات"
        )
        # تصنيفات منفصلة لكل نوع
        eq_groups = QTabWidget()
        eq_groups.addTab(_GroupManagerPanel(self.conn, "capital"),  "رأس المال")
        eq_groups.addTab(_GroupManagerPanel(self.conn, "drawings"), "المسحوبات")
        eq_groups.addTab(_GroupManagerPanel(self.conn, "revenue"),  "الإيرادات")
        eq_groups.addTab(_GroupManagerPanel(self.conn, "expense"),  "المصروفات")
        eq_tab.addTab(eq_groups, "🏷️ التصنيفات")
        tabs.addTab(eq_tab, "👑 حقوق الملكية")

        tabs.addTab(FinancialStatementsTab(self.conn), "📊 القوائم المالية")
        tabs.addTab(JournalTab(self.conn),             "📒 قيود اليومية")
        tabs.addTab(LedgerTab(self.conn),              "📘 دفتر الأستاذ")
        tabs.addTab(TrialBalanceTab(self.conn),        "⚖️ ميزان المراجعة")

        root.addWidget(tabs)

    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)