"""
ui/tabs/accounting_tab.py (محدَّث)
=====================================
تبويب الحسابات — يستخدم accounting.db منفصل.

التبويبات الداخلية:
  📊 لوحة التحكم       — ملخص المعادلة المحاسبية
  🌳 شجرة الحسابات     — كل الحسابات هرمياً
  🏦 الأصول
  📋 الخصوم
  👑 حقوق الملكية
  💹 الإيرادات
  📤 المصروفات
  📒 دفتر اليومية      — إضافة/عرض القيود
  ⚖️ ميزان المراجعة
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QFrame, QSplitter, QPushButton,
    QTableWidgetItem, QHeaderView, QMessageBox,
    QLineEdit, QDoubleSpinBox, QComboBox,
    QFormLayout, QGroupBox, QDateEdit, QTextEdit,
    QScrollArea, QAbstractItemView,
    QTreeWidget, QTreeWidgetItem,
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
)
from ui.helpers import (
    make_table, setup_table_columns, buttons_row,
    section_label, danger_button, confirm_delete,
)
from ui.widgets.flexible_text import (
    make_flexible_table, FlexItem, WrapDelegate,
    set_flexible_columns, refresh_tooltips,
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


# ══════════════════════════════════════════════════════════
# بطاقة المعادلة المحاسبية
# ══════════════════════════════════════════════════════════

class _EquationCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
            }
        """)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        title = QLabel("⚖️  المعادلة المحاسبية الأساسية")
        title.setStyleSheet("font-size:14px; font-weight:bold; color:#333;")
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        eq_row = QHBoxLayout()
        eq_row.setSpacing(16)

        def _box(label, color):
            f = QFrame()
            f.setStyleSheet(f"""
                QFrame {{
                    background: {color}18;
                    border: 2px solid {color};
                    border-radius: 8px;
                }}
            """)
            lay = QVBoxLayout(f)
            lay.setContentsMargins(12, 10, 12, 10)
            lay.setSpacing(4)
            lbl_t = QLabel(label)
            lbl_t.setAlignment(Qt.AlignCenter)
            lbl_t.setStyleSheet(
                f"color:{color}; font-size:11px; font-weight:bold;"
                "background:transparent; border:none;"
            )
            lbl_v = QLabel("0.00  ج")
            lbl_v.setAlignment(Qt.AlignCenter)
            lbl_v.setStyleSheet(
                f"color:{color}; font-size:18px; font-weight:bold;"
                "background:transparent; border:none;"
            )
            lay.addWidget(lbl_t)
            lay.addWidget(lbl_v)
            return f, lbl_v

        f_a, self.lbl_assets      = _box("الأصول",          "#1565c0")
        f_l, self.lbl_liabilities = _box("الخصوم",          "#c62828")
        f_e, self.lbl_equity      = _box("حقوق الملكية",    "#2e7d32")

        lbl_eq   = QLabel("=")
        lbl_plus = QLabel("+")
        for lbl in (lbl_eq, lbl_plus):
            lbl.setStyleSheet("font-size:24px; font-weight:bold; color:#555;")
            lbl.setAlignment(Qt.AlignCenter)

        eq_row.addWidget(f_a, stretch=3)
        eq_row.addWidget(lbl_eq)
        eq_row.addWidget(f_l, stretch=3)
        eq_row.addWidget(lbl_plus)
        eq_row.addWidget(f_e, stretch=3)
        root.addLayout(eq_row)

        self.lbl_balance = QLabel("✅  المعادلة متوازنة")
        self.lbl_balance.setAlignment(Qt.AlignCenter)
        self.lbl_balance.setStyleSheet(
            "font-size:12px; font-weight:bold; color:#2e7d32;"
            "background:transparent; border:none;"
        )
        root.addWidget(self.lbl_balance)

    def refresh(self, conn):
        bal        = get_balances_by_type(conn)
        assets     = bal.get("asset",     {}).get("balance", 0)
        liab       = bal.get("liability", {}).get("balance", 0)
        revenue    = bal.get("revenue",   {}).get("balance", 0)
        expense    = bal.get("expense",   {}).get("balance", 0)
        equity_acc = bal.get("equity",    {}).get("balance", 0)
        net_income = revenue - expense
        equity     = equity_acc + net_income

        self.lbl_assets.setText(f"{assets:,.2f}  ج")
        self.lbl_liabilities.setText(f"{liab:,.2f}  ج")
        self.lbl_equity.setText(f"{equity:,.2f}  ج")

        diff = abs(assets - (liab + equity))
        if diff < 0.01:
            self.lbl_balance.setText("✅  المعادلة متوازنة")
            self.lbl_balance.setStyleSheet(
                "font-size:12px; font-weight:bold; color:#2e7d32;"
                "background:transparent; border:none;"
            )
        else:
            self.lbl_balance.setText(f"⚠️  فرق: {diff:,.2f} ج — راجع القيود")
            self.lbl_balance.setStyleSheet(
                "font-size:12px; font-weight:bold; color:#c62828;"
                "background:transparent; border:none;"
            )


# ══════════════════════════════════════════════════════════
# لوحة التحكم
# ══════════════════════════════════════════════════════════

class _DashboardPanel(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        bus.data_changed.connect(self.refresh)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(12)

        self._eq_card = _EquationCard()
        root.addWidget(self._eq_card)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)

        def _mini(label, color):
            f = QFrame()
            f.setStyleSheet(f"""
                QFrame {{
                    background: white;
                    border-left: 4px solid {color};
                    border-radius: 6px;
                }}
            """)
            lay = QVBoxLayout(f)
            lay.setContentsMargins(12, 8, 12, 8)
            lbl_t = QLabel(label)
            lbl_t.setStyleSheet(
                f"font-size:10px; color:#888; background:transparent; border:none;"
            )
            lbl_v = QLabel("0.00  ج")
            lbl_v.setStyleSheet(
                f"font-size:15px; font-weight:bold; color:{color};"
                "background:transparent; border:none;"
            )
            lay.addWidget(lbl_t)
            lay.addWidget(lbl_v)
            cards_row.addWidget(f, stretch=1)
            return lbl_v

        self.lbl_revenue = _mini("إجمالي الإيرادات",        "#6a1b9a")
        self.lbl_expense = _mini("إجمالي المصروفات",        "#e65100")
        self.lbl_net     = _mini("صافي الربح / الخسارة",   "#1b5e20")
        self.lbl_cash    = _mini("رصيد الصندوق + البنك",   "#1565c0")

        root.addLayout(cards_row)
        root.addStretch()

        btn_refresh = QPushButton("🔄  تحديث")
        btn_refresh.setMinimumHeight(32)
        btn_refresh.clicked.connect(self.refresh)
        root.addWidget(btn_refresh)

        self.refresh()

    def refresh(self):
        self._eq_card.refresh(self.conn)
        bal = get_balances_by_type(self.conn)

        rev = bal.get("revenue", {}).get("balance", 0)
        exp = bal.get("expense", {}).get("balance", 0)
        net = rev - exp

        cash_row = self.conn.execute("""
            SELECT COALESCE(SUM(jl.debit - jl.credit), 0) AS bal
            FROM journal_lines jl
            JOIN accounts a ON a.id = jl.account_id
            WHERE a.subtype IN ('cash', 'bank')
        """).fetchone()
        cash = cash_row["bal"] if cash_row else 0

        self.lbl_revenue.setText(f"{rev:,.2f}  ج")
        self.lbl_expense.setText(f"{exp:,.2f}  ج")

        color_net = "#1b5e20" if net >= 0 else "#c62828"
        self.lbl_net.setText(f"{net:,.2f}  ج")
        self.lbl_net.setStyleSheet(
            f"font-size:15px; font-weight:bold; color:{color_net};"
            "background:transparent; border:none;"
        )
        self.lbl_cash.setText(f"{cash:,.2f}  ج")


# ══════════════════════════════════════════════════════════
# شجرة الحسابات — مع عرض flexible
# ══════════════════════════════════════════════════════════

class _AccountsTree(QWidget):
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

        title = (
            f"─── شجرة {_TYPE_AR.get(self.acc_type, 'الحسابات')} ───"
            if self.acc_type else "─── كل الحسابات ───"
        )
        root.addWidget(section_label(title))

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["الكود", "اسم الحساب", "النوع", "الرصيد"])
        self.tree.setWordWrap(True)
        self.tree.setUniformRowHeights(False)   # ← مهم لـ word-wrap

        hh = self.tree.header()
        hh.setSectionResizeMode(0, QHeaderView.Interactive)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)          # ← يتمدد
        hh.setSectionResizeMode(2, QHeaderView.Interactive)
        hh.setSectionResizeMode(3, QHeaderView.Interactive)
        hh.setMinimumSectionSize(60)
        self.tree.setColumnWidth(0, 70)
        self.tree.setColumnWidth(2, 100)
        self.tree.setColumnWidth(3, 110)

        self.tree.setAlternatingRowColors(True)
        self.tree.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

        # ← WrapDelegate على عمود الاسم
        from ui.widgets.flexible_text import WrapDelegate
        self.tree.setItemDelegateForColumn(1, WrapDelegate(self.tree, min_row_height=28))

        root.addWidget(self.tree, stretch=1)

        # فورم إضافة حساب
        grp = QGroupBox("➕  إضافة حساب فرعي")
        grp.setStyleSheet("""
            QGroupBox { font-weight:bold; color:#1565c0; border:1px solid #e0e0e0;
                        border-radius:6px; margin-top:8px; padding-top:8px; }
            QGroupBox::title { subcontrol-origin:margin; padding:0 6px; }
        """)
        form_lay = QFormLayout(grp)
        form_lay.setSpacing(8)

        self.inp_code = QLineEdit()
        self.inp_code.setPlaceholderText("مثال: 1141")
        self.inp_code.setMinimumHeight(28)

        self.inp_name_acc = QLineEdit()
        self.inp_name_acc.setPlaceholderText("اسم الحساب...")
        self.inp_name_acc.setMinimumHeight(28)

        form_lay.addRow("الكود:", self.inp_code)
        form_lay.addRow("الاسم:", self.inp_name_acc)

        btn_add = QPushButton("➕  إضافة")
        btn_add.setMinimumHeight(30)
        btn_add.clicked.connect(self._add_account)
        form_lay.addRow(btn_add)
        root.addWidget(grp)

    def _load(self):
        # حفظ العناصر المفتوحة
        expanded = set()
        def _collect(item):
            if item.isExpanded():
                expanded.add(item.data(0, Qt.UserRole))
            for i in range(item.childCount()):
                _collect(item.child(i))
        for i in range(self.tree.topLevelItemCount()):
            _collect(self.tree.topLevelItem(i))

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

        self._add_nodes(roots, None, expanded)
        self.tree.expandToDepth(1)

    def _add_nodes(self, nodes, parent, expanded):
        for node in nodes:
            bal   = get_account_balance(self.conn, node["id"])
            color = _TYPE_COLORS.get(node["type"], "#333")

            item = QTreeWidgetItem()
            item.setText(0, node["code"])
            item.setText(1, node["name"])
            item.setText(2, _TYPE_AR.get(node["type"], node["type"]))
            item.setText(3, f"{bal:,.2f}")
            item.setData(0, Qt.UserRole, node["id"])

            # tooltip بالنص الكامل
            for col, tip in enumerate([
                node["code"], node["name"],
                _TYPE_AR.get(node["type"], ""), f"الرصيد: {bal:,.2f}"
            ]):
                item.setToolTip(col, tip)

            item.setForeground(0, QColor(color))
            item.setForeground(
                1, QColor(color) if not node.get("is_leaf", 1) else QColor("#333")
            )

            if not node.get("is_leaf", 1):
                font = item.font(1)
                font.setBold(True)
                item.setFont(1, font)

            if bal < 0:
                item.setForeground(3, QColor("#c62828"))
            elif bal > 0:
                item.setForeground(3, QColor("#2e7d32"))

            if parent:
                parent.addChild(item)
            else:
                self.tree.addTopLevelItem(item)

            if node["id"] in expanded:
                item.setExpanded(True)

            if node.get("children"):
                self._add_nodes(node["children"], item, expanded)

    def _add_account(self):
        code = self.inp_code.text().strip()
        name = self.inp_name_acc.text().strip()
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

        type_map = {"1": "asset", "2": "liability", "3": "equity",
                    "4": "revenue", "5": "expense"}
        acc_type = self.acc_type or type_map.get(code[0], "asset")

        try:
            insert_account(self.conn, code, name, acc_type, parent_id=parent_id)
            self.inp_code.clear()
            self.inp_name_acc.clear()
            bus.data_changed.emit()
        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))


# ══════════════════════════════════════════════════════════
# دفتر اليومية — فورم القيد
# ══════════════════════════════════════════════════════════

class _JournalLineWidget(QFrame):
    def __init__(self, conn, on_remove, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._on_remove = on_remove
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
        self._load_accounts()

        self.sp_debit  = _spin()
        self.sp_credit = _spin()
        self.sp_debit.setFixedWidth(110)
        self.sp_credit.setFixedWidth(110)

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

    def _load_accounts(self):
        self.cmb_account.clear()
        self.cmb_account.addItem("— اختر الحساب —", None)
        for acc in fetch_leaf_accounts(self.conn):
            self.cmb_account.addItem(f"{acc['code']} — {acc['name']}", acc["id"])

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


class _JournalForm(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._line_widgets = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        header = QFrame()
        header.setStyleSheet("""
            QFrame { background:white; border:1px solid #e0e0e0; border-radius:8px; }
        """)
        h_lay = QVBoxLayout(header)
        h_lay.setContentsMargins(14, 12, 14, 12)
        h_lay.setSpacing(8)

        self.lbl_mode = QLabel("─── قيد يومية جديد ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0; font-size:12px;")
        h_lay.addWidget(self.lbl_mode)

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
        h_lay.addLayout(info_row)

        # ملخص المدين/الدائن
        summary_row = QHBoxLayout()
        self.lbl_total_debit  = QLabel("مدين: 0.00")
        self.lbl_total_credit = QLabel("دائن: 0.00")
        self.lbl_diff         = QLabel("✅ متوازن")
        for lbl in (self.lbl_total_debit, self.lbl_total_credit, self.lbl_diff):
            lbl.setStyleSheet("font-weight:bold; font-size:11px;")
        summary_row.addWidget(self.lbl_total_debit)
        summary_row.addSpacing(16)
        summary_row.addWidget(self.lbl_total_credit)
        summary_row.addSpacing(16)
        summary_row.addWidget(self.lbl_diff)
        summary_row.addStretch()
        h_lay.addLayout(summary_row)
        root.addWidget(header)

        # رؤوس
        ch = QWidget()
        ch_lay = QHBoxLayout(ch)
        ch_lay.setContentsMargins(8, 0, 8, 0)
        ch_lay.setSpacing(8)
        for t, w, s in [("الحساب",None,2),("مدين",110,0),("دائن",110,0),("بيان",None,1),("",28,0)]:
            l = QLabel(t)
            l.setStyleSheet("font-size:9px; font-weight:bold; color:#888; background:transparent;")
            if w: l.setFixedWidth(w)
            ch_lay.addWidget(l, stretch=s)
        root.addWidget(ch)

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
        scroll.setMinimumHeight(120)
        scroll.setMaximumHeight(260)
        scroll.setStyleSheet("""
            QScrollArea { border:1px solid #e0e0e0; border-radius:6px; background:#fafafa; }
        """)
        root.addWidget(scroll, stretch=1)

        btn_add_line = QPushButton("➕  إضافة سطر")
        btn_add_line.setMinimumHeight(30)
        btn_add_line.setStyleSheet("""
            QPushButton { background:#e8f4fd; border:1px solid #90caf9;
                border-radius:4px; color:#1565c0; font-weight:bold; padding:4px 12px; }
            QPushButton:hover { background:#bbdefb; }
        """)
        btn_add_line.clicked.connect(self._add_line)

        self.btn_save = QPushButton("💾  حفظ القيد")
        self.btn_save.setMinimumHeight(32)
        self.btn_save.setStyleSheet("""
            QPushButton { background:#1565c0; color:white;
                font-weight:bold; border-radius:6px; padding:0 18px; }
            QPushButton:hover { background:#0d47a1; }
        """)
        self.btn_save.clicked.connect(self._save)

        self.btn_cancel = QPushButton("✖  مسح")
        self.btn_cancel.setMinimumHeight(32)
        self.btn_cancel.clicked.connect(self._reset)

        root.addLayout(buttons_row(btn_add_line, self.btn_save, self.btn_cancel))

        self._add_line()
        self._add_line()

    def _add_line(self):
        w = _JournalLineWidget(self.conn, self._remove_line)
        self._line_widgets.append(w)
        self._rows_layout.insertWidget(self._rows_layout.count() - 1, w)
        w.sp_debit.valueChanged.connect(self._update_totals)
        w.sp_credit.valueChanged.connect(self._update_totals)

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
        self.lbl_total_debit.setText(f"مدين: {total_d:,.2f}")
        self.lbl_total_credit.setText(f"دائن: {total_c:,.2f}")
        if diff < 0.001:
            self.lbl_diff.setText("✅ متوازن")
            self.lbl_diff.setStyleSheet("font-weight:bold; color:#2e7d32;")
        else:
            self.lbl_diff.setText(f"⚠️ فرق: {diff:,.2f}")
            self.lbl_diff.setStyleSheet("font-weight:bold; color:#c62828;")

    def _save(self):
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
        date_str = self.dt_date.date().toString("yyyy-MM-dd")
        etype    = self.cmb_type.currentData()
        entry_id = insert_entry(self.conn, date_str, desc, etype)
        add_entry_lines(self.conn, entry_id, lines)
        self._reset()
        bus.data_changed.emit()
        QMessageBox.information(self, "تم", "✅ تم حفظ القيد")

    def _reset(self):
        for w in list(self._line_widgets):
            self._rows_layout.removeWidget(w)
            w.deleteLater()
        self._line_widgets.clear()
        self.inp_desc.clear()
        self.dt_date.setDate(QDate.currentDate())
        self._add_line()
        self._add_line()
        self._update_totals()


# ══════════════════════════════════════════════════════════
# جدول القيود — مع flexible text
# ══════════════════════════════════════════════════════════

class _JournalTable(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(6)
        root.addWidget(section_label("─── القيود المحاسبية ───"))

        # ← make_flexible_table مع wrap على عمود البيان
        self.table = make_flexible_table(
            ["#", "رقم القيد", "التاريخ", "النوع", "البيان", "مدين", "دائن"],
            stretch_col=4,
            wrap_cols=[4],      # ← عمود البيان يتعمل wrap
        )
        setup_table_columns(self.table,
            widths={0:40, 1:90, 2:90, 3:80, 5:90, 6:90},
            stretch_col=4
        )
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, stretch=1)

        btn_del = danger_button("🗑️  حذف القيد")
        btn_del.setMinimumHeight(30)
        btn_del.clicked.connect(self._delete)
        root.addLayout(buttons_row(btn_del))

    def _load(self):
        entries = fetch_all_entries(self.conn)
        self.table.setRowCount(0)
        type_ar = {
            "manual":"يدوي", "purchase":"شراء", "sale":"بيع",
            "payment":"دفع", "receipt":"تحصيل", "adjustment":"تسوية"
        }
        for e in entries:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, FlexItem(str(e["id"])))
            self.table.setItem(r, 1, FlexItem(e["ref_no"]))
            self.table.setItem(r, 2, FlexItem(e["date"]))
            self.table.setItem(r, 3, FlexItem(type_ar.get(e["type"], e["type"])))
            self.table.setItem(r, 4, FlexItem(e["description"]))   # ← wrap
            self.table.setItem(r, 5, FlexItem(f"{e['total_debit']:,.2f}"))
            self.table.setItem(r, 6, FlexItem(f"{e['total_credit']:,.2f}"))

    def _delete(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر قيداً أولاً")
            return
        eid  = int(self.table.item(row, 0).text())
        desc = self.table.item(row, 4).text()
        if confirm_delete(self, desc):
            delete_entry(self.conn, eid)
            bus.data_changed.emit()


class _JournalTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.addWidget(_JournalForm(conn))
        splitter.addWidget(_JournalTable(conn))
        splitter.setSizes([320, 400])
        splitter.setCollapsible(0, True)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(splitter)


# ══════════════════════════════════════════════════════════
# ميزان المراجعة — مع flexible text
# ══════════════════════════════════════════════════════════

class _TrialBalanceTab(QWidget):
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

        self.table = make_flexible_table(
            ["الكود", "اسم الحساب", "النوع", "مجموع المدين", "مجموع الدائن", "الرصيد"],
            stretch_col=1,
            wrap_cols=[1],    # ← اسم الحساب يتعمل wrap
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
            self.table.setItem(r, 0, FlexItem(row["code"]))
            self.table.setItem(r, 1, FlexItem(row["name"]))
            self.table.setItem(r, 2, FlexItem(_TYPE_AR.get(row["type"], row["type"])))
            self.table.setItem(r, 3, FlexItem(f"{row['total_debit']:,.2f}"))
            self.table.setItem(r, 4, FlexItem(f"{row['total_credit']:,.2f}"))
            bal_item = FlexItem(f"{row['balance']:,.2f}")
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
# تبويب رئيسي للحسابات
# ══════════════════════════════════════════════════════════

class AccountingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn = get_accounting_connection()
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabBar::tab:selected { color:#1565c0; border-top:2px solid #1565c0; }
        """)

        tabs.addTab(_DashboardPanel(self.conn),              "📊  لوحة التحكم")
        tabs.addTab(_AccountsTree(self.conn),                "🌳  كل الحسابات")
        tabs.addTab(_AccountsTree(self.conn, "asset"),       "🏦  الأصول")
        tabs.addTab(_AccountsTree(self.conn, "liability"),   "📋  الخصوم")
        tabs.addTab(_AccountsTree(self.conn, "equity"),      "👑  حقوق الملكية")
        tabs.addTab(_AccountsTree(self.conn, "revenue"),     "💹  الإيرادات")
        tabs.addTab(_AccountsTree(self.conn, "expense"),     "📤  المصروفات")
        tabs.addTab(_JournalTab(self.conn),                  "📒  دفتر اليومية")
        tabs.addTab(_TrialBalanceTab(self.conn),             "⚖️  ميزان المراجعة")

        root.addWidget(tabs)

    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)