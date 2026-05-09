"""
ui/tabs/accounting_tab.py
==========================
تبويب الحسابات — accounting.db منفصل.

التبويبات الداخلية:
  🏦 الأصول
  📋 الخصوم
  👑 حقوق الملكية
  📊 القوائم المالية  (income statement / equity statement / balance sheet)
  📒 قيود اليومية
  📘 دفتر الأستاذ (T-Accounts)
  ⚖️ ميزان المراجعة
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QFrame, QSplitter, QPushButton,
    QTableWidgetItem, QHeaderView, QMessageBox,
    QLineEdit, QDoubleSpinBox, QComboBox,
    QFormLayout, QGroupBox, QDateEdit, QScrollArea,
    QAbstractItemView, QTreeWidget, QTreeWidgetItem,
    QStackedWidget,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui  import QColor, QFont

from db.connection      import get_accounting_connection
from db.accounting_repo import (
    fetch_all_accounts, fetch_leaf_accounts,
    fetch_all_entries, fetch_entry, fetch_entry_lines,
    insert_entry, add_entry_lines, delete_entry,
    validate_entry_balance, get_balances_by_type,
    trial_balance, insert_account, update_account,
    get_account_balance, fetch_account,
    income_statement, balance_sheet, owners_equity_statement,
    fetch_t_account,
)
from ui.helpers import (
    make_table, setup_table_columns, buttons_row,
    section_label, danger_button, confirm_delete,
)
from ui.events import bus


_TYPE_AR = {
    "asset":     "أصول",
    "liability": "خصوم",
    "equity":    "حقوق ملكية",
    "revenue":   "إيرادات",
    "expense":   "مصروفات",
}

_TYPE_COLORS = {
    "asset":     "#1565c0",
    "liability": "#c62828",
    "equity":    "#2e7d32",
    "revenue":   "#6a1b9a",
    "expense":   "#e65100",
}


def _spin(max_=999999999, dec=2):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(30)
    return s


def _money(val: float) -> str:
    return f"{val:,.2f}  ج"


# ══════════════════════════════════════════════════════════
# شجرة الحسابات (مشتركة بين Assets / Liabilities / Equity)
# ══════════════════════════════════════════════════════════

class AccountsTreePanel(QWidget):
    """
    شجرة حسابات لنوع محدد مع فورم إضافة.
    """
    def __init__(self, conn, acc_type: str = None, parent=None):
        super().__init__(parent)
        self.conn     = conn
        self.acc_type = acc_type
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(8)

        title = f"─── {_TYPE_AR.get(self.acc_type, 'الحسابات')} ───" if self.acc_type else "─── كل الحسابات ───"
        root.addWidget(section_label(title))

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["الكود", "اسم الحساب", "الرصيد"])
        self.tree.setWordWrap(True)
        self.tree.setUniformRowHeights(False)
        self.tree.setAlternatingRowColors(True)

        hh = self.tree.header()
        hh.setSectionResizeMode(0, QHeaderView.Interactive)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Interactive)
        self.tree.setColumnWidth(0, 75)
        self.tree.setColumnWidth(2, 120)
        root.addWidget(self.tree, stretch=1)

        # أزرار
        btn_row = QHBoxLayout()
        btn_edit = QPushButton("✏️  تعديل")
        btn_del  = danger_button("🗑️  حذف")
        for b in (btn_edit, btn_del):
            b.setMinimumHeight(28)
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        btn_row.addWidget(btn_edit)
        btn_row.addWidget(btn_del)
        btn_row.addStretch()
        root.addLayout(btn_row)

        # فورم إضافة
        grp = QGroupBox("➕  إضافة / تعديل حساب")
        grp.setStyleSheet("""
            QGroupBox { font-weight:bold; color:#1565c0;
                border:1px solid #e0e0e0; border-radius:6px;
                margin-top:8px; padding-top:8px; }
            QGroupBox::title { subcontrol-origin:margin; padding:0 6px; }
        """)
        fl = QFormLayout(grp)
        fl.setSpacing(8)
        fl.setLabelAlignment(Qt.AlignRight)

        self.lbl_form_mode = QLabel("─── حساب جديد ───")
        self.lbl_form_mode.setStyleSheet("font-weight:bold; color:#1565c0;")
        fl.addRow(self.lbl_form_mode)

        self.inp_code = QLineEdit()
        self.inp_code.setPlaceholderText("مثال: 1141")
        self.inp_code.setMinimumHeight(28)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم الحساب...")
        self.inp_name.setMinimumHeight(28)

        fl.addRow("الكود :", self.inp_code)
        fl.addRow("الاسم :", self.inp_name)

        self._editing_id = None
        btn_add    = QPushButton("➕  إضافة")
        self.btn_save_acc   = QPushButton("💾  حفظ")
        self.btn_cancel_acc = QPushButton("✖  إلغاء")
        self.btn_save_acc.setVisible(False)
        self.btn_cancel_acc.setVisible(False)
        for b in (btn_add, self.btn_save_acc, self.btn_cancel_acc):
            b.setMinimumHeight(28)
        btn_add.clicked.connect(self._add)
        self.btn_save_acc.clicked.connect(self._save_edit)
        self.btn_cancel_acc.clicked.connect(self._cancel_edit)

        row_w = QWidget()
        row_l = QHBoxLayout(row_w)
        row_l.setContentsMargins(0, 0, 0, 0)
        row_l.addWidget(btn_add)
        row_l.addWidget(self.btn_save_acc)
        row_l.addWidget(self.btn_cancel_acc)
        row_l.addStretch()
        fl.addRow(row_w)
        root.addWidget(grp)

    def _load(self):
        self.tree.clear()
        rows  = fetch_all_accounts(self.conn, self.acc_type)
        nodes = {r["id"]: dict(r) for r in rows}
        roots = []
        for nid, node in nodes.items():
            pid = node["parent_id"]
            if pid and pid in nodes:
                nodes[pid].setdefault("children", []).append(node)
            else:
                roots.append(node)
        self._add_nodes(roots, None)
        self.tree.expandToDepth(1)

    def _add_nodes(self, nodes, parent):
        for node in nodes:
            bal   = get_account_balance(self.conn, node["id"])
            color = _TYPE_COLORS.get(node["type"], "#333")
            item  = QTreeWidgetItem()
            item.setText(0, node["code"])
            item.setText(1, node["name"])
            item.setText(2, f"{bal:,.2f}")
            item.setData(0, Qt.UserRole, node["id"])
            item.setToolTip(1, node["name"])
            item.setForeground(0, QColor(color))
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
                self._add_nodes(node["children"], item)

    def _selected_id(self):
        items = self.tree.selectedItems()
        return items[0].data(0, Qt.UserRole) if items else None

    def _add(self):
        code = self.inp_code.text().strip()
        name = self.inp_name.text().strip()
        if not code or not name:
            QMessageBox.warning(self, "تنبيه", "أدخل الكود والاسم")
            return
        parent_code = code[:-1] if len(code) > 1 else None
        parent_id   = None
        if parent_code:
            row = self.conn.execute(
                "SELECT id FROM accounts WHERE code=?", (parent_code,)
            ).fetchone()
            parent_id = row["id"] if row else None
        type_map = {"1":"asset","2":"liability","3":"equity","4":"revenue","5":"expense"}
        acc_type = self.acc_type or type_map.get(code[0], "asset")
        try:
            insert_account(self.conn, code, name, acc_type, parent_id=parent_id)
            self.inp_code.clear()
            self.inp_name.clear()
            bus.data_changed.emit()
        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))

    def _edit(self):
        aid = self._selected_id()
        if not aid:
            QMessageBox.information(self, "تنبيه", "اختر حساباً أولاً")
            return
        acc = fetch_account(self.conn, aid)
        if not acc:
            return
        self._editing_id = aid
        self.inp_code.setText(acc["code"])
        self.inp_name.setText(acc["name"])
        self.lbl_form_mode.setText(f"─── تعديل: {acc['name']} ───")
        self.btn_save_acc.setVisible(True)
        self.btn_cancel_acc.setVisible(True)

    def _save_edit(self):
        name = self.inp_name.text().strip()
        if not name or not self._editing_id:
            return
        update_account(self.conn, self._editing_id, name)
        self._cancel_edit()
        bus.data_changed.emit()

    def _cancel_edit(self):
        self._editing_id = None
        self.inp_code.clear()
        self.inp_name.clear()
        self.lbl_form_mode.setText("─── حساب جديد ───")
        self.btn_save_acc.setVisible(False)
        self.btn_cancel_acc.setVisible(False)

    def _delete(self):
        aid = self._selected_id()
        if not aid:
            QMessageBox.information(self, "تنبيه", "اختر حساباً أولاً")
            return
        acc = fetch_account(self.conn, aid)
        if not acc:
            return
        # تحقق من وجود حركات
        has_lines = self.conn.execute(
            "SELECT COUNT(*) as c FROM journal_lines WHERE account_id=?", (aid,)
        ).fetchone()["c"]
        if has_lines:
            QMessageBox.warning(self, "تحذير",
                f"الحساب «{acc['name']}» له {has_lines} حركة — لا يمكن حذفه.")
            return
        if confirm_delete(self, acc["name"]):
            from db.accounting_repo import delete_account
            delete_account(self.conn, aid)
            bus.data_changed.emit()


# ══════════════════════════════════════════════════════════
# فورم سطر القيد
# ══════════════════════════════════════════════════════════

class _JournalLineWidget(QFrame):
    def __init__(self, conn, on_remove, on_change=None, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._on_remove = on_remove
        self._on_change = on_change
        self._build()

    def _build(self):
        self.setStyleSheet("""
            QFrame { background:#fafafa; border:1px solid #e8e8e8; border-radius:6px; }
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(8)

        self.cmb_account = QComboBox()
        self.cmb_account.setMinimumWidth(220)
        self.cmb_account.setMinimumHeight(28)
        self.cmb_account.addItem("— اختر الحساب —", None)
        for acc in fetch_leaf_accounts(self.conn):
            self.cmb_account.addItem(f"{acc['code']} — {acc['name']}", acc["id"])

        self.sp_debit  = _spin()
        self.sp_credit = _spin()
        self.sp_debit.setFixedWidth(110)
        self.sp_credit.setFixedWidth(110)
        if self._on_change:
            self.sp_debit.valueChanged.connect(self._on_change)
            self.sp_credit.valueChanged.connect(self._on_change)

        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("بيان...")
        self.inp_desc.setMinimumHeight(28)

        btn_del = QPushButton("❌")
        btn_del.setFixedSize(28, 28)
        btn_del.setStyleSheet(
            "QPushButton { background:transparent; border:none; font-size:13px; }"
            "QPushButton:hover { color:#e53935; }"
        )
        btn_del.clicked.connect(lambda: self._on_remove(self))

        lay.addWidget(self.cmb_account, stretch=2)
        lay.addWidget(QLabel("مدين:"))
        lay.addWidget(self.sp_debit)
        lay.addWidget(QLabel("دائن:"))
        lay.addWidget(self.sp_credit)
        lay.addWidget(self.inp_desc, stretch=1)
        lay.addWidget(btn_del)

    def get_values(self):
        acc_id = self.cmb_account.currentData()
        if not acc_id:
            return None
        return {
            "account_id":  acc_id,
            "debit":       self.sp_debit.value(),
            "credit":      self.sp_credit.value(),
            "description": self.inp_desc.text().strip(),
        }


# ══════════════════════════════════════════════════════════
# تبويب قيود اليومية
# ══════════════════════════════════════════════════════════

class JournalTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._line_widgets = []
        self._build()
        bus.data_changed.connect(self._load_table)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)

        # ── فورم القيد ──
        form_widget = QWidget()
        form_lay = QVBoxLayout(form_widget)
        form_lay.setContentsMargins(14, 12, 14, 12)
        form_lay.setSpacing(8)

        self.lbl_mode = QLabel("─── قيد يومية جديد ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0; font-size:12px;")
        form_lay.addWidget(self.lbl_mode)

        info_row = QHBoxLayout()
        info_row.setSpacing(10)

        self.dt_date = QDateEdit(QDate.currentDate())
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setMinimumHeight(30)
        self.dt_date.setDisplayFormat("yyyy-MM-dd")
        self.dt_date.setFixedWidth(130)

        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("وصف القيد...")
        self.inp_desc.setMinimumHeight(30)

        self.cmb_type = QComboBox()
        self.cmb_type.setMinimumHeight(30)
        self.cmb_type.setFixedWidth(130)
        for key, label in [
            ("manual","يدوي"), ("purchase","شراء"), ("sale","بيع"),
            ("payment","دفع"), ("receipt","تحصيل"), ("adjustment","تسوية")
        ]:
            self.cmb_type.addItem(label, key)

        info_row.addWidget(QLabel("التاريخ:"))
        info_row.addWidget(self.dt_date)
        info_row.addWidget(QLabel("النوع:"))
        info_row.addWidget(self.cmb_type)
        info_row.addWidget(self.inp_desc, stretch=1)
        form_lay.addLayout(info_row)

        # ملخص
        sum_row = QHBoxLayout()
        self.lbl_sum_d  = QLabel("مدين: 0.00")
        self.lbl_sum_c  = QLabel("دائن: 0.00")
        self.lbl_bal_st = QLabel("✅ متوازن")
        for l in (self.lbl_sum_d, self.lbl_sum_c, self.lbl_bal_st):
            l.setStyleSheet("font-weight:bold; font-size:11px;")
        sum_row.addWidget(self.lbl_sum_d)
        sum_row.addSpacing(16)
        sum_row.addWidget(self.lbl_sum_c)
        sum_row.addSpacing(16)
        sum_row.addWidget(self.lbl_bal_st)
        sum_row.addStretch()
        form_lay.addLayout(sum_row)

        # سطور القيد
        self._rows_container = QWidget()
        self._rows_container.setStyleSheet("background:transparent;")
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setSpacing(4)
        self._rows_layout.setContentsMargins(0, 0, 4, 0)
        self._rows_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._rows_container)
        scroll.setMinimumHeight(140)
        scroll.setMaximumHeight(280)
        scroll.setStyleSheet("""
            QScrollArea { border:1px solid #e0e0e0; border-radius:6px; background:#fafafa; }
        """)
        form_lay.addWidget(scroll, stretch=1)

        btn_add_line = QPushButton("➕  إضافة سطر")
        btn_add_line.setMinimumHeight(30)
        btn_add_line.setStyleSheet("""
            QPushButton { background:#e8f4fd; border:1px solid #90caf9;
                border-radius:4px; color:#1565c0; font-weight:bold; padding:4px 12px; }
            QPushButton:hover { background:#bbdefb; }
        """)
        btn_add_line.clicked.connect(self._add_line)

        self.btn_save_entry = QPushButton("💾  حفظ القيد")
        self.btn_save_entry.setMinimumHeight(32)
        self.btn_save_entry.setStyleSheet("""
            QPushButton { background:#1565c0; color:white;
                font-weight:bold; border-radius:6px; padding:0 18px; }
            QPushButton:hover { background:#0d47a1; }
        """)
        self.btn_save_entry.clicked.connect(self._save_entry)

        btn_clear = QPushButton("✖  مسح")
        btn_clear.setMinimumHeight(32)
        btn_clear.clicked.connect(self._reset_form)

        form_lay.addLayout(buttons_row(btn_add_line, self.btn_save_entry, btn_clear))
        splitter.addWidget(form_widget)

        # ── جدول القيود ──
        table_widget = QWidget()
        tl = QVBoxLayout(table_widget)
        tl.setContentsMargins(12, 8, 12, 12)
        tl.setSpacing(6)
        tl.addWidget(section_label("─── القيود المحاسبية ───"))

        self.table = make_table(
            ["#", "رقم القيد", "التاريخ", "النوع", "البيان", "مدين", "دائن"],
            stretch_col=4
        )
        setup_table_columns(self.table,
            widths={0:40, 1:90, 2:90, 3:80, 5:90, 6:90},
            stretch_col=4
        )
        self.table.setAlternatingRowColors(True)
        tl.addWidget(self.table, stretch=1)

        btn_del = danger_button("🗑️  حذف القيد")
        btn_del.setMinimumHeight(30)
        btn_del.clicked.connect(self._delete_entry)
        tl.addLayout(buttons_row(btn_del))
        splitter.addWidget(table_widget)

        splitter.setSizes([320, 380])
        splitter.setCollapsible(0, True)

        root.addWidget(splitter)

        self._add_line()
        self._add_line()
        self._load_table()

    def _add_line(self):
        w = _JournalLineWidget(self.conn, self._remove_line, self._update_totals)
        self._line_widgets.append(w)
        self._rows_layout.insertWidget(self._rows_layout.count() - 1, w)
        self._update_totals()

    def _remove_line(self, widget):
        if widget in self._line_widgets:
            self._line_widgets.remove(widget)
        self._rows_layout.removeWidget(widget)
        widget.deleteLater()
        self._update_totals()

    def _update_totals(self):
        total_d = sum(w.sp_debit.value()  for w in self._line_widgets)
        total_c = sum(w.sp_credit.value() for w in self._line_widgets)
        diff    = abs(total_d - total_c)
        self.lbl_sum_d.setText(f"مدين: {total_d:,.2f}")
        self.lbl_sum_c.setText(f"دائن: {total_c:,.2f}")
        if diff < 0.001:
            self.lbl_bal_st.setText("✅ متوازن")
            self.lbl_bal_st.setStyleSheet("font-weight:bold; color:#2e7d32;")
        else:
            self.lbl_bal_st.setText(f"⚠️ فرق: {diff:,.2f}")
            self.lbl_bal_st.setStyleSheet("font-weight:bold; color:#c62828;")

    def _save_entry(self):
        lines = [w.get_values() for w in self._line_widgets if w.get_values()]
        if len(lines) < 2:
            QMessageBox.warning(self, "تنبيه", "أضف سطرين على الأقل")
            return
        if not validate_entry_balance(lines):
            QMessageBox.warning(self, "خطأ", "مجموع المدين ≠ مجموع الدائن")
            return
        desc = self.inp_desc.text().strip()
        if not desc:
            QMessageBox.warning(self, "تنبيه", "أدخل وصف القيد")
            return
        entry_id = insert_entry(
            self.conn,
            self.dt_date.date().toString("yyyy-MM-dd"),
            desc, self.cmb_type.currentData()
        )
        add_entry_lines(self.conn, entry_id, lines)
        self._reset_form()
        bus.data_changed.emit()
        QMessageBox.information(self, "تم", "✅ تم حفظ القيد")

    def _reset_form(self):
        for w in list(self._line_widgets):
            self._rows_layout.removeWidget(w)
            w.deleteLater()
        self._line_widgets.clear()
        self.inp_desc.clear()
        self.dt_date.setDate(QDate.currentDate())
        self._add_line()
        self._add_line()
        self._update_totals()

    def _load_table(self):
        entries = fetch_all_entries(self.conn)
        self.table.setRowCount(0)
        type_ar = {
            "manual":"يدوي", "purchase":"شراء", "sale":"بيع",
            "payment":"دفع", "receipt":"تحصيل", "adjustment":"تسوية"
        }
        for e in entries:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(e["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(e["ref_no"]))
            self.table.setItem(r, 2, QTableWidgetItem(e["date"]))
            self.table.setItem(r, 3, QTableWidgetItem(type_ar.get(e["type"], e["type"])))
            desc_item = QTableWidgetItem(e["description"])
            desc_item.setToolTip(e["description"])
            self.table.setItem(r, 4, desc_item)
            self.table.setItem(r, 5, QTableWidgetItem(f"{e['total_debit']:,.2f}"))
            self.table.setItem(r, 6, QTableWidgetItem(f"{e['total_credit']:,.2f}"))

    def _delete_entry(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر قيداً أولاً")
            return
        eid  = int(self.table.item(row, 0).text())
        desc = self.table.item(row, 4).text()
        if confirm_delete(self, desc):
            delete_entry(self.conn, eid)
            bus.data_changed.emit()


# ══════════════════════════════════════════════════════════
# دفتر الأستاذ — T-Accounts
# ══════════════════════════════════════════════════════════

class LedgerTab(QWidget):
    """عرض أي حساب كـ T-Account مع جميع حركاته."""

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

        # ── قائمة الحسابات ──
        left = QWidget()
        ll   = QVBoxLayout(left)
        ll.setContentsMargins(12, 8, 8, 12)
        ll.setSpacing(6)
        ll.addWidget(section_label("─── الحسابات ───"))

        self.inp_search_acc = QLineEdit()
        self.inp_search_acc.setPlaceholderText("🔍 بحث بالاسم أو الكود...")
        self.inp_search_acc.setMinimumHeight(28)
        self.inp_search_acc.textChanged.connect(self._filter_accounts)
        ll.addWidget(self.inp_search_acc)

        self.lst_accounts = QTreeWidget()
        self.lst_accounts.setHeaderLabels(["الكود", "الاسم"])
        self.lst_accounts.setColumnWidth(0, 70)
        self.lst_accounts.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.lst_accounts.itemSelectionChanged.connect(self._on_account_selected)
        ll.addWidget(self.lst_accounts, stretch=1)
        splitter.addWidget(left)

        # ── T-Account ──
        right = QWidget()
        rl    = QVBoxLayout(right)
        rl.setContentsMargins(8, 8, 12, 12)
        rl.setSpacing(8)

        self.lbl_acc_title = QLabel("اختر حساباً لعرض حركاته")
        self.lbl_acc_title.setStyleSheet(
            "font-size:14px; font-weight:bold; color:#1565c0;"
            "background:#e8f4fd; border:1px solid #90caf9;"
            "border-radius:6px; padding:8px 16px;"
        )
        self.lbl_acc_title.setAlignment(Qt.AlignCenter)
        rl.addWidget(self.lbl_acc_title)

        # T-Account Frame
        t_frame = QFrame()
        t_frame.setStyleSheet("""
            QFrame { background:white; border:2px solid #1565c0; border-radius:8px; }
        """)
        t_lay = QHBoxLayout(t_frame)
        t_lay.setContentsMargins(0, 0, 0, 0)
        t_lay.setSpacing(0)

        # مدين (يسار)
        left_t = QWidget()
        left_t.setStyleSheet("background:transparent;")
        lt_l = QVBoxLayout(left_t)
        lt_l.setContentsMargins(8, 8, 4, 8)
        lbl_debit_hdr = QLabel("مدين (Debit)")
        lbl_debit_hdr.setAlignment(Qt.AlignCenter)
        lbl_debit_hdr.setStyleSheet(
            "font-weight:bold; color:#1565c0; font-size:13px; "
            "background:#e8f4fd; border-radius:4px; padding:4px;"
        )
        self.t_debit_table = make_table(["البيان", "المبلغ"], stretch_col=0)
        self.t_debit_table.setColumnWidth(1, 100)
        lt_l.addWidget(lbl_debit_hdr)
        lt_l.addWidget(self.t_debit_table, stretch=1)

        self.lbl_total_debit = QLabel("الإجمالي: 0.00")
        self.lbl_total_debit.setStyleSheet(
            "font-weight:bold; color:#1565c0; font-size:12px; "
            "background:#e8f4fd; border-radius:4px; padding:4px 8px;"
        )
        self.lbl_total_debit.setAlignment(Qt.AlignCenter)
        lt_l.addWidget(self.lbl_total_debit)

        # فاصل
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color:#1565c0;")

        # دائن (يمين)
        right_t = QWidget()
        right_t.setStyleSheet("background:transparent;")
        rt_l = QVBoxLayout(right_t)
        rt_l.setContentsMargins(4, 8, 8, 8)
        lbl_credit_hdr = QLabel("دائن (Credit)")
        lbl_credit_hdr.setAlignment(Qt.AlignCenter)
        lbl_credit_hdr.setStyleSheet(
            "font-weight:bold; color:#c62828; font-size:13px; "
            "background:#fdecea; border-radius:4px; padding:4px;"
        )
        self.t_credit_table = make_table(["البيان", "المبلغ"], stretch_col=0)
        self.t_credit_table.setColumnWidth(1, 100)
        rt_l.addWidget(lbl_credit_hdr)
        rt_l.addWidget(self.t_credit_table, stretch=1)

        self.lbl_total_credit = QLabel("الإجمالي: 0.00")
        self.lbl_total_credit.setStyleSheet(
            "font-weight:bold; color:#c62828; font-size:12px; "
            "background:#fdecea; border-radius:4px; padding:4px 8px;"
        )
        self.lbl_total_credit.setAlignment(Qt.AlignCenter)
        rt_l.addWidget(self.lbl_total_credit)

        t_lay.addWidget(left_t, stretch=1)
        t_lay.addWidget(sep)
        t_lay.addWidget(right_t, stretch=1)
        rl.addWidget(t_frame, stretch=1)

        # الرصيد
        self.lbl_balance = QLabel("الرصيد: —")
        self.lbl_balance.setAlignment(Qt.AlignCenter)
        self.lbl_balance.setStyleSheet(
            "font-size:14px; font-weight:bold; color:#2e7d32; "
            "background:#f0faf0; border:1px solid #a5d6a7; "
            "border-radius:6px; padding:6px 16px;"
        )
        rl.addWidget(self.lbl_balance)

        splitter.addWidget(right)
        splitter.setSizes([220, 580])
        root.addWidget(splitter)

        self._refresh_accounts()

    def _refresh_accounts(self):
        self._all_accounts = fetch_all_accounts(self.conn)
        self._filter_accounts()

    def _filter_accounts(self):
        q = self.inp_search_acc.text().strip().lower()
        self.lst_accounts.clear()
        for acc in self._all_accounts:
            if not acc["is_leaf"]:
                continue
            if q and q not in acc["name"].lower() and q not in acc["code"].lower():
                continue
            item = QTreeWidgetItem()
            item.setText(0, acc["code"])
            item.setText(1, acc["name"])
            item.setData(0, Qt.UserRole, acc["id"])
            color = _TYPE_COLORS.get(acc["type"], "#333")
            item.setForeground(0, QColor(color))
            self.lst_accounts.addTopLevelItem(item)

    def _on_account_selected(self):
        items = self.lst_accounts.selectedItems()
        if not items:
            return
        aid = items[0].data(0, Qt.UserRole)
        self._load_t_account(aid)

    def _load_t_account(self, account_id: int):
        data = fetch_t_account(self.conn, account_id)
        if not data:
            return

        acc   = data["account"]
        lines = data["lines"]
        color = _TYPE_COLORS.get(acc["type"], "#1565c0")

        self.lbl_acc_title.setText(
            f"حساب: {acc['code']} — {acc['name']}  |  "
            f"{_TYPE_AR.get(acc['type'], '')}"
        )

        self.t_debit_table.setRowCount(0)
        self.t_credit_table.setRowCount(0)

        for line in lines:
            if line["debit"] > 0:
                r = self.t_debit_table.rowCount()
                self.t_debit_table.insertRow(r)
                desc = f"{line['date']}  {line['entry_desc']}"
                d_item = QTableWidgetItem(desc)
                d_item.setToolTip(desc)
                self.t_debit_table.setItem(r, 0, d_item)
                self.t_debit_table.setItem(r, 1, QTableWidgetItem(f"{line['debit']:,.2f}"))
            if line["credit"] > 0:
                r = self.t_credit_table.rowCount()
                self.t_credit_table.insertRow(r)
                desc = f"{line['date']}  {line['entry_desc']}"
                c_item = QTableWidgetItem(desc)
                c_item.setToolTip(desc)
                self.t_credit_table.setItem(r, 0, c_item)
                self.t_credit_table.setItem(r, 1, QTableWidgetItem(f"{line['credit']:,.2f}"))

        self.lbl_total_debit.setText(f"الإجمالي: {data['total_debit']:,.2f}")
        self.lbl_total_credit.setText(f"الإجمالي: {data['total_credit']:,.2f}")

        bal    = data["balance"]
        b_side = "مدين" if bal >= 0 else "دائن"
        self.lbl_balance.setText(f"الرصيد ({b_side}): {abs(bal):,.2f}  ج")
        b_color = "#1565c0" if bal >= 0 else "#c62828"
        self.lbl_balance.setStyleSheet(
            f"font-size:14px; font-weight:bold; color:{b_color}; "
            "background:#f0f8ff; border:1px solid #90caf9; "
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
        root.addWidget(section_label("─── ميزان المراجعة ───"))

        self.table = make_table(
            ["الكود", "اسم الحساب", "النوع", "مجموع المدين", "مجموع الدائن", "الرصيد"],
            stretch_col=1
        )
        setup_table_columns(self.table,
            widths={0:70, 2:100, 3:120, 4:120, 5:110},
            stretch_col=1
        )
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, stretch=1)

        totals = QFrame()
        totals.setStyleSheet("""
            QFrame { background:#f0f4ff; border:1px solid #c5cae9; border-radius:6px; }
        """)
        t_lay = QHBoxLayout(totals)
        t_lay.setContentsMargins(12, 8, 12, 8)
        self.lbl_sum_d  = QLabel("مجموع المدين: 0.00")
        self.lbl_sum_c  = QLabel("مجموع الدائن: 0.00")
        self.lbl_status = QLabel("─")
        for l in (self.lbl_sum_d, self.lbl_sum_c, self.lbl_status):
            l.setStyleSheet("font-weight:bold; font-size:12px;")
        t_lay.addWidget(self.lbl_sum_d)
        t_lay.addSpacing(24)
        t_lay.addWidget(self.lbl_sum_c)
        t_lay.addSpacing(24)
        t_lay.addWidget(self.lbl_status)
        t_lay.addStretch()
        root.addWidget(totals)

    def _load(self):
        rows = trial_balance(self.conn)
        self.table.setRowCount(0)
        sum_d = sum_c = 0.0
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(row["code"]))
            name_item = QTableWidgetItem(row["name"])
            name_item.setToolTip(row["name"])
            self.table.setItem(r, 1, name_item)
            self.table.setItem(r, 2, QTableWidgetItem(_TYPE_AR.get(row["type"], row["type"])))
            self.table.setItem(r, 3, QTableWidgetItem(f"{row['total_debit']:,.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"{row['total_credit']:,.2f}"))
            bal_item = QTableWidgetItem(f"{row['balance']:,.2f}")
            if row["balance"] < 0:
                bal_item.setForeground(QColor("#c62828"))
            self.table.setItem(r, 5, bal_item)
            sum_d += row["total_debit"]
            sum_c += row["total_credit"]

        self.lbl_sum_d.setText(f"مجموع المدين: {sum_d:,.2f}")
        self.lbl_sum_c.setText(f"مجموع الدائن: {sum_c:,.2f}")
        diff = abs(sum_d - sum_c)
        if diff < 0.01:
            self.lbl_status.setText("✅ الميزان متوازن")
            self.lbl_status.setStyleSheet("font-weight:bold; color:#2e7d32;")
        else:
            self.lbl_status.setText(f"⚠️ فرق: {diff:,.2f}")
            self.lbl_status.setStyleSheet("font-weight:bold; color:#c62828;")


# ══════════════════════════════════════════════════════════
# القوائم المالية
# ══════════════════════════════════════════════════════════

def _stat_card(label: str, color: str = "#1565c0") -> tuple:
    frame = QFrame()
    frame.setStyleSheet(f"""
        QFrame {{
            background: white;
            border-left: 4px solid {color};
            border-radius: 6px;
        }}
    """)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(12, 8, 12, 8)
    lay.setSpacing(2)
    lbl_t = QLabel(label)
    lbl_t.setStyleSheet("font-size:10px; color:#888; background:transparent; border:none;")
    lbl_v = QLabel("0.00  ج")
    lbl_v.setStyleSheet(
        f"font-size:15px; font-weight:bold; color:{color};"
        "background:transparent; border:none;"
    )
    lay.addWidget(lbl_t)
    lay.addWidget(lbl_v)
    return frame, lbl_v


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

        # عنوان
        hdr = QLabel("📊  قائمة الدخل")
        hdr.setStyleSheet(
            "font-size:16px; font-weight:bold; color:#6a1b9a; "
            "background:#f3e5f5; border:1px solid #ce93d8; "
            "border-radius:8px; padding:8px 16px;"
        )
        hdr.setAlignment(Qt.AlignCenter)
        root.addWidget(hdr)

        # بطاقات ملخص
        cards_row = QHBoxLayout()
        f1, self.lbl_rev    = _stat_card("إجمالي الإيرادات",    "#6a1b9a")
        f2, self.lbl_exp    = _stat_card("إجمالي المصروفات",    "#e65100")
        f3, self.lbl_net    = _stat_card("صافي الربح / الخسارة", "#1b5e20")
        for f in (f1, f2, f3):
            cards_row.addWidget(f, stretch=1)
        root.addLayout(cards_row)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)

        # جدول الإيرادات
        rev_w = QWidget()
        rv_l  = QVBoxLayout(rev_w)
        rv_l.setContentsMargins(0, 4, 4, 0)
        rv_l.addWidget(section_label("💹  الإيرادات"))
        self.table_rev = make_table(["الكود", "البند", "المبلغ"], stretch_col=1)
        self.table_rev.setColumnWidth(0, 60)
        self.table_rev.setColumnWidth(2, 110)
        rv_l.addWidget(self.table_rev)
        splitter.addWidget(rev_w)

        # جدول المصروفات
        exp_w = QWidget()
        ex_l  = QVBoxLayout(exp_w)
        ex_l.setContentsMargins(4, 4, 0, 0)
        ex_l.addWidget(section_label("📤  المصروفات"))
        self.table_exp = make_table(["الكود", "البند", "المبلغ"], stretch_col=1)
        self.table_exp.setColumnWidth(0, 60)
        self.table_exp.setColumnWidth(2, 110)
        ex_l.addWidget(self.table_exp)
        splitter.addWidget(exp_w)

        root.addWidget(splitter, stretch=1)

    def _load(self):
        data = income_statement(self.conn)

        self.table_rev.setRowCount(0)
        for row in data["revenues"]:
            r = self.table_rev.rowCount()
            self.table_rev.insertRow(r)
            self.table_rev.setItem(r, 0, QTableWidgetItem(row["code"]))
            n = QTableWidgetItem(row["name"])
            n.setToolTip(row["name"])
            self.table_rev.setItem(r, 1, n)
            amt = QTableWidgetItem(f"{row['amount']:,.2f}")
            amt.setForeground(QColor("#6a1b9a"))
            self.table_rev.setItem(r, 2, amt)

        self.table_exp.setRowCount(0)
        for row in data["expenses"]:
            r = self.table_exp.rowCount()
            self.table_exp.insertRow(r)
            self.table_exp.setItem(r, 0, QTableWidgetItem(row["code"]))
            n = QTableWidgetItem(row["name"])
            n.setToolTip(row["name"])
            self.table_exp.setItem(r, 1, n)
            amt = QTableWidgetItem(f"{row['amount']:,.2f}")
            amt.setForeground(QColor("#e65100"))
            self.table_exp.setItem(r, 2, amt)

        self.lbl_rev.setText(_money(data["total_rev"]))
        self.lbl_exp.setText(_money(data["total_exp"]))
        net   = data["net_income"]
        color = "#1b5e20" if net >= 0 else "#b71c1c"
        self.lbl_net.setText(_money(net))
        self.lbl_net.setStyleSheet(
            f"font-size:15px; font-weight:bold; color:{color}; background:transparent; border:none;"
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
            "font-size:16px; font-weight:bold; color:#1565c0; "
            "background:#e8f4fd; border:1px solid #90caf9; "
            "border-radius:8px; padding:8px 16px;"
        )
        hdr.setAlignment(Qt.AlignCenter)
        root.addWidget(hdr)

        # المعادلة
        eq_row = QHBoxLayout()
        f1, self.lbl_assets  = _stat_card("إجمالي الأصول",       "#1565c0")
        f2, self.lbl_liab    = _stat_card("إجمالي الخصوم",       "#c62828")
        f3, self.lbl_equity  = _stat_card("حقوق الملكية",        "#2e7d32")
        self.lbl_balanced    = QLabel("✅  متوازنة")
        self.lbl_balanced.setStyleSheet("font-weight:bold; color:#2e7d32; font-size:13px;")
        self.lbl_balanced.setAlignment(Qt.AlignCenter)
        for f in (f1, f2, f3):
            eq_row.addWidget(f, stretch=1)
        eq_row.addWidget(self.lbl_balanced)
        root.addLayout(eq_row)

        splitter = QSplitter(Qt.Horizontal)

        # الأصول
        a_w = QWidget()
        al  = QVBoxLayout(a_w)
        al.setContentsMargins(0, 4, 4, 0)
        al.addWidget(section_label("🏦  الأصول"))
        self.table_assets = make_table(["الكود", "البند", "المبلغ"], stretch_col=1)
        self.table_assets.setColumnWidth(0, 60)
        self.table_assets.setColumnWidth(2, 110)
        al.addWidget(self.table_assets)
        splitter.addWidget(a_w)

        # الخصوم + حقوق الملكية
        le_w = QWidget()
        lel  = QVBoxLayout(le_w)
        lel.setContentsMargins(4, 4, 0, 0)
        lel.addWidget(section_label("📋  الخصوم وحقوق الملكية"))
        self.table_liab = make_table(["الكود", "البند", "المبلغ", "النوع"], stretch_col=1)
        self.table_liab.setColumnWidth(0, 60)
        self.table_liab.setColumnWidth(2, 110)
        self.table_liab.setColumnWidth(3, 80)
        lel.addWidget(self.table_liab)
        splitter.addWidget(le_w)

        root.addWidget(splitter, stretch=1)

    def _load(self):
        data = balance_sheet(self.conn)

        def _fill(table, rows, color):
            table.setRowCount(0)
            for row in rows:
                r = table.rowCount()
                table.insertRow(r)
                table.setItem(r, 0, QTableWidgetItem(row["code"]))
                n = QTableWidgetItem(row["name"])
                n.setToolTip(row["name"])
                table.setItem(r, 1, n)
                amt = QTableWidgetItem(f"{row['amount']:,.2f}")
                amt.setForeground(QColor(color))
                table.setItem(r, 2, amt)

        _fill(self.table_assets, data["assets"], "#1565c0")
        self.table_liab.setRowCount(0)
        for row in data["liabilities"]:
            r = self.table_liab.rowCount()
            self.table_liab.insertRow(r)
            self.table_liab.setItem(r, 0, QTableWidgetItem(row["code"]))
            n = QTableWidgetItem(row["name"])
            n.setToolTip(row["name"])
            self.table_liab.setItem(r, 1, n)
            amt = QTableWidgetItem(f"{row['amount']:,.2f}")
            amt.setForeground(QColor("#c62828"))
            self.table_liab.setItem(r, 2, amt)
            self.table_liab.setItem(r, 3, QTableWidgetItem("خصوم"))

        # صافي الدخل كسطر في حقوق الملكية
        for row in data["equity"]:
            r = self.table_liab.rowCount()
            self.table_liab.insertRow(r)
            self.table_liab.setItem(r, 0, QTableWidgetItem(row["code"]))
            n = QTableWidgetItem(row["name"])
            n.setToolTip(row["name"])
            self.table_liab.setItem(r, 1, n)
            amt = QTableWidgetItem(f"{row['amount']:,.2f}")
            amt.setForeground(QColor("#2e7d32"))
            self.table_liab.setItem(r, 2, amt)
            self.table_liab.setItem(r, 3, QTableWidgetItem("حقوق ملكية"))

        if data["net_income"] != 0:
            r = self.table_liab.rowCount()
            self.table_liab.insertRow(r)
            self.table_liab.setItem(r, 0, QTableWidgetItem(""))
            self.table_liab.setItem(r, 1, QTableWidgetItem("صافي الدخل"))
            ni_item = QTableWidgetItem(f"{data['net_income']:,.2f}")
            ni_color = "#1b5e20" if data["net_income"] >= 0 else "#b71c1c"
            ni_item.setForeground(QColor(ni_color))
            self.table_liab.setItem(r, 2, ni_item)
            self.table_liab.setItem(r, 3, QTableWidgetItem("حقوق ملكية"))

        self.lbl_assets.setText(_money(data["total_assets"]))
        self.lbl_liab.setText(_money(data["total_liab"]))
        self.lbl_equity.setText(_money(data["total_equity"]))

        diff = abs(data["total_assets"] - (data["total_liab"] + data["total_equity"]))
        if diff < 0.01:
            self.lbl_balanced.setText("✅  الميزانية متوازنة")
            self.lbl_balanced.setStyleSheet("font-weight:bold; color:#2e7d32; font-size:12px;")
        else:
            self.lbl_balanced.setText(f"⚠️  فرق: {diff:,.2f}")
            self.lbl_balanced.setStyleSheet("font-weight:bold; color:#c62828; font-size:12px;")


class OwnersEquityTab(QWidget):
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
            "font-size:16px; font-weight:bold; color:#2e7d32; "
            "background:#f1f8e9; border:1px solid #a5d6a7; "
            "border-radius:8px; padding:8px 16px;"
        )
        hdr.setAlignment(Qt.AlignCenter)
        root.addWidget(hdr)

        f1, self.lbl_equity_total = _stat_card("إجمالي حقوق الملكية", "#2e7d32")
        f2, self.lbl_net_income   = _stat_card("صافي الدخل المضاف",   "#1b5e20")
        cards = QHBoxLayout()
        cards.addWidget(f1, stretch=1)
        cards.addWidget(f2, stretch=1)
        cards.addStretch(1)
        root.addLayout(cards)

        self.table = make_table(["الكود", "البند", "الرصيد"], stretch_col=1)
        self.table.setColumnWidth(0, 70)
        self.table.setColumnWidth(2, 120)
        root.addWidget(self.table, stretch=1)

    def _load(self):
        data = owners_equity_statement(self.conn)
        self.table.setRowCount(0)
        for row in data["accounts"]:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(row["code"]))
            n = QTableWidgetItem(row["name"])
            n.setToolTip(row["name"])
            self.table.setItem(r, 1, n)
            amt = QTableWidgetItem(f"{row['amount']:,.2f}")
            amt.setForeground(QColor("#2e7d32"))
            self.table.setItem(r, 2, amt)

        # صافي الدخل
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setItem(r, 0, QTableWidgetItem(""))
        self.table.setItem(r, 1, QTableWidgetItem("➕  صافي الدخل للفترة"))
        ni_item = QTableWidgetItem(f"{data['net_income']:,.2f}")
        ni_color = "#1b5e20" if data["net_income"] >= 0 else "#b71c1c"
        ni_item.setForeground(QColor(ni_color))
        self.table.setItem(r, 2, ni_item)

        self.lbl_equity_total.setText(_money(data["total"]))
        self.lbl_net_income.setText(_money(data["net_income"]))


# ══════════════════════════════════════════════════════════
# تبويب القوائم المالية (3 قوائم)
# ══════════════════════════════════════════════════════════

class FinancialStatementsTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabBar::tab:selected { color:#1565c0; border-top:2px solid #1565c0; }
        """)
        tabs.addTab(IncomeStatementTab(self.conn),  "📊  قائمة الدخل")
        tabs.addTab(OwnersEquityTab(self.conn),     "👑  حقوق الملكية")
        tabs.addTab(BalanceSheetTab(self.conn),     "🏛️  الميزانية العمومية")
        root.addWidget(tabs)


# ══════════════════════════════════════════════════════════
# التبويب الرئيسي للحسابات
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
                border-bottom:none; padding:8px 16px;
                margin-left:2px; font-size:12px; color:#555;
            }
            QTabBar::tab:selected {
                background:#ffffff; color:#1565c0;
                font-weight:bold; border-top:2px solid #1565c0;
            }
            QTabBar::tab:hover:!selected { background:#e8f0fe; color:#1565c0; }
        """)

        tabs.addTab(AccountsTreePanel(self.conn, "asset"),     "🏦  الأصول")
        tabs.addTab(AccountsTreePanel(self.conn, "liability"), "📋  الخصوم")
        tabs.addTab(AccountsTreePanel(self.conn, "equity"),    "👑  حقوق الملكية")
        tabs.addTab(FinancialStatementsTab(self.conn),         "📊  القوائم المالية")
        tabs.addTab(JournalTab(self.conn),                     "📒  قيود اليومية")
        tabs.addTab(LedgerTab(self.conn),                      "📘  دفتر الأستاذ")
        tabs.addTab(TrialBalanceTab(self.conn),                "⚖️  ميزان المراجعة")

        root.addWidget(tabs)

    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)