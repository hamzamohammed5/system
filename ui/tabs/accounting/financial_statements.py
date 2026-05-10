"""
ui/tabs/accounting/financial_statements.py
==========================================
القوائم المالية:
  - TrialBalanceTab       — ميزان المراجعة
  - IncomeStatementTab    — قائمة الدخل
  - OwnersEquityTab       — قائمة حقوق الملكية
  - BalanceSheetTab       — الميزانية العمومية
  - FinancialStatementsTab — تبويب يجمعهم
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QFrame, QSplitter, QTableWidgetItem,
    QHeaderView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.accounting_repo import (
    trial_balance, income_statement, balance_sheet,
    owners_equity_statement,
)
from ui.helpers import make_table, setup_table_columns, section_label
from ui.events  import bus
from .helpers   import TYPE_COLORS, _money, _stat_card


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
            ["الكود", "اسم الحساب", "النوع", "مجموع المدين", "مجموع الدائن", "الرصيد"],
            stretch_col=1
        )
        setup_table_columns(self.table,
            widths={0: 70, 2: 100, 3: 120, 4: 120, 5: 110}, stretch_col=1)
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
        from db.accounting_schema import TYPE_AR
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
# قائمة الدخل
# ══════════════════════════════════════════════════════════

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
        f1, self.lbl_rev = _stat_card("إجمالي الإيرادات",     "#6a1b9a")
        f2, self.lbl_exp = _stat_card("إجمالي المصروفات",     "#e65100")
        f3, self.lbl_net = _stat_card("صافي الربح / الخسارة", "#1b5e20")
        for f in (f1, f2, f3):
            cards.addWidget(f, stretch=1)
        root.addLayout(cards)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)

        for attr_name, title, color in [
            ("table_rev", "💹 الإيرادات",  "#6a1b9a"),
            ("table_exp", "📤 المصروفات", "#e65100"),
        ]:
            w  = QWidget()
            wl = QVBoxLayout(w)
            wl.setContentsMargins(0, 4, 4, 0)
            wl.addWidget(section_label(title))
            tbl = make_table(["الكود", "البند", "المبلغ"], stretch_col=1)
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


# ══════════════════════════════════════════════════════════
# قائمة حقوق الملكية
# ══════════════════════════════════════════════════════════

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
            "font-size:15px; font-weight:bold; color:#2e7d32;"
            "background:#f1f8e9; border:1px solid #a5d6a7;"
            "border-radius:8px; padding:8px 16px;"
        )
        hdr.setAlignment(Qt.AlignCenter)
        root.addWidget(hdr)

        cards = QHBoxLayout()
        f1, self.lbl_cap   = _stat_card("رأس المال",          "#2e7d32")
        f2, self.lbl_ni    = _stat_card("صافي الدخل",         "#1b5e20")
        f3, self.lbl_draw  = _stat_card("المسحوبات",          "#4e342e")
        f4, self.lbl_total = _stat_card("صافي حقوق الملكية",  "#1565c0")
        for f in (f1, f2, f3, f4):
            cards.addWidget(f, stretch=1)
        root.addLayout(cards)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)

        left_w = QWidget()
        ll = QVBoxLayout(left_w)
        ll.setContentsMargins(0, 4, 4, 0)
        cr_hdr = QLabel("📈 ما يزيد حقوق الملكية (CR↑)")
        cr_hdr.setStyleSheet(
            "font-weight:bold; color:#2e7d32; font-size:11px;"
            "background:#f1f8e9; border-radius:4px; padding:4px 8px;"
        )
        ll.addWidget(cr_hdr)
        self.table_cr = make_table(["الكود", "البند", "النوع", "المبلغ"], stretch_col=1)
        self.table_cr.setColumnWidth(0, 60)
        self.table_cr.setColumnWidth(2, 80)
        self.table_cr.setColumnWidth(3, 100)
        ll.addWidget(self.table_cr)
        splitter.addWidget(left_w)

        right_w = QWidget()
        rl = QVBoxLayout(right_w)
        rl.setContentsMargins(4, 4, 0, 0)
        dr_hdr = QLabel("📉 ما ينقص حقوق الملكية (DR↑)")
        dr_hdr.setStyleSheet(
            "font-weight:bold; color:#c62828; font-size:11px;"
            "background:#fdecea; border-radius:4px; padding:4px 8px;"
        )
        rl.addWidget(dr_hdr)
        self.table_dr = make_table(["الكود", "البند", "النوع", "المبلغ"], stretch_col=1)
        self.table_dr.setColumnWidth(0, 60)
        self.table_dr.setColumnWidth(2, 80)
        self.table_dr.setColumnWidth(3, 100)
        rl.addWidget(self.table_dr)
        splitter.addWidget(right_w)

        root.addWidget(splitter, stretch=1)

        eq_frame = QFrame()
        eq_frame.setStyleSheet(
            "QFrame { background:#e8f4fd; border:1px solid #90caf9; border-radius:6px; }"
        )
        eq_lay = QHBoxLayout(eq_frame)
        eq_lay.setContentsMargins(12, 8, 12, 8)
        self.lbl_equation = QLabel("")
        self.lbl_equation.setStyleSheet(
            "font-size:12px; font-weight:bold; color:#1565c0;"
            "background:transparent; border:none;"
        )
        eq_lay.addWidget(self.lbl_equation)
        root.addWidget(eq_frame)

    def _load(self):
        data = owners_equity_statement(self.conn)

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

        ni = data["net_income"]
        r  = self.table_cr.rowCount()
        self.table_cr.insertRow(r)
        self.table_cr.setItem(r, 0, QTableWidgetItem(""))
        self.table_cr.setItem(r, 1, QTableWidgetItem("صافي الدخل للفترة"))
        self.table_cr.setItem(r, 2, QTableWidgetItem("إيرادات - مصروفات"))
        ni_item = QTableWidgetItem(f"{ni:,.2f}")
        ni_item.setForeground(QColor("#1b5e20") if ni >= 0 else QColor("#b71c1c"))
        self.table_cr.setItem(r, 3, ni_item)

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

        self.lbl_cap.setText(_money(data["total_capital"]))
        self.lbl_ni.setText(_money(ni))
        self.lbl_draw.setText(_money(data["total_drawings"]))
        total = data["total_equity"]
        self.lbl_total.setText(_money(total))
        tc = "#1565c0" if total >= 0 else "#b71c1c"
        self.lbl_total.setStyleSheet(
            f"font-size:14px; font-weight:bold; color:{tc};"
            "background:transparent; border:none;"
        )
        self.lbl_equation.setText(
            f"رأس المال  {data['total_capital']:,.2f}  +  "
            f"صافي الدخل  {ni:,.2f}  −  "
            f"المسحوبات  {data['total_drawings']:,.2f}  =  "
            f"صافي حقوق الملكية  {total:,.2f}"
        )


# ══════════════════════════════════════════════════════════
# الميزانية العمومية
# ══════════════════════════════════════════════════════════

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
        f1, self.lbl_assets = _stat_card("إجمالي الأصول", "#1565c0")
        f2, self.lbl_liab   = _stat_card("إجمالي الخصوم", "#c62828")
        f3, self.lbl_equity = _stat_card("حقوق الملكية",  "#2e7d32")
        self.lbl_balanced   = QLabel("✅ متوازنة")
        self.lbl_balanced.setStyleSheet(
            "font-weight:bold; color:#2e7d32; font-size:12px;"
        )
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
        self.table_assets = make_table(["الكود", "البند", "المبلغ"], stretch_col=1)
        self.table_assets.setColumnWidth(0, 60)
        self.table_assets.setColumnWidth(2, 110)
        l1.addWidget(self.table_assets)
        splitter.addWidget(w1)

        w2 = QWidget()
        l2 = QVBoxLayout(w2)
        l2.setContentsMargins(4, 4, 0, 0)
        l2.addWidget(section_label("📋 الخصوم وحقوق الملكية"))
        self.table_liab = make_table(
            ["الكود", "البند", "المبلغ", "النوع"], stretch_col=1
        )
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
            *[(r, "خصوم",      "#c62828") for r in data["liabilities"]],
            *[(r, "رأس المال", "#2e7d32") for r in data["capital"]],
            *[(r, "مسحوبات",  "#4e342e") for r in data["drawings"]],
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
            self.lbl_balanced.setStyleSheet(
                "font-weight:bold; color:#2e7d32; font-size:12px;"
            )
        else:
            self.lbl_balanced.setText(f"⚠️ فرق: {diff:,.2f}")
            self.lbl_balanced.setStyleSheet(
                "font-weight:bold; color:#c62828; font-size:12px;"
            )


# ══════════════════════════════════════════════════════════
# تبويب يجمع القوائم المالية
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
        tabs.setStyleSheet(
            "QTabBar::tab:selected { color:#1565c0; border-top:2px solid #1565c0; }"
        )
        tabs.addTab(IncomeStatementTab(self.conn), "📊 قائمة الدخل")
        tabs.addTab(OwnersEquityTab(self.conn),    "👑 حقوق الملكية")
        tabs.addTab(BalanceSheetTab(self.conn),    "🏛️ الميزانية العمومية")
        root.addWidget(tabs)