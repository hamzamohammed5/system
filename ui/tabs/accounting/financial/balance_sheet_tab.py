"""
ui/tabs/accounting/financial/balance_sheet_tab.py
==================================================
BalanceSheetTab — تبويب الميزانية العمومية.

[إعادة هيكلة]: استبدال الهيدر والبطاقات اليدوية بـ:
  - PageHeader   بدل QLabel اليدوي
  - StatRow      بدل QHBoxLayout + _stat_card
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QTableWidgetItem,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.accounting.accounting_repo import balance_sheet
from ui.helpers import make_table, section_label
from ui.events  import bus
from ui.widgets.shared.panels import (
    PageHeader,
    StatRow, StatItem,
    NotificationBar,
)
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
from ._financial_helpers import _money


class BalanceSheetTab(SafeConnMixin, QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self._init_safe_conn(conn, "accounting")
        self._company_id = self._get_company_id()
        self._build()
        self._load()
        bus.company_data_changed.connect(self._on_company_event)

    def _on_company_event(self, company_id: int):
        if self._on_company_event_safe(company_id):
            self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(10)

        # ── هيدر الصفحة (بدل QLabel اليدوي) ──
        self._page_hdr = PageHeader(
            title="الميزانية العمومية",
            icon="🏛️",
            accent="#1565c0",
        )
        # زر حالة التوازن في هيدر الصفحة
        self._btn_balanced = self._page_hdr.add_action(
            "✅ متوازنة", style="ghost"
        )
        self._btn_balanced.setEnabled(False)
        root.addWidget(self._page_hdr)

        # ── البطاقات الإحصائية (بدل QHBoxLayout + _stat_card) ──
        self._stats = StatRow([
            StatItem("إجمالي الأصول", color="#1565c0", icon="🏦"),
            StatItem("إجمالي الخصوم", color="#c62828", icon="📋"),
            StatItem("حقوق الملكية",  color="#2e7d32", icon="👑"),
        ])
        root.addWidget(self._stats)

        # ── الجداول ──
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
        try:
            data = balance_sheet(self._get_safe_conn())
        except Exception as e:
            print(f"[BalanceSheetTab] _load error: {e}")
            return

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

        # ── تحديث البطاقات عبر StatRow ──
        self._stats.set_value(0, _money(data["total_assets"]))
        self._stats.set_value(1, _money(data["total_liab"]))
        self._stats.set_value(2, _money(data["total_equity"]))

        # ── حالة التوازن في هيدر الصفحة ──
        diff = abs(data["total_assets"] - (data["total_liab"] + data["total_equity"]))
        if diff < 0.01:
            self._btn_balanced.setText("✅ الميزانية متوازنة")
            self._btn_balanced.setStyleSheet(
                "QPushButton { background:#ecfdf5; color:#065f46;"
                " border:1px solid #6ee7b7; border-radius:6px;"
                " padding:0 12px; font-weight:bold; }"
            )
        else:
            self._btn_balanced.setText(f"⚠️ فرق: {diff:,.2f}")
            self._btn_balanced.setStyleSheet(
                "QPushButton { background:#fef2f2; color:#c62828;"
                " border:1px solid #fca5a5; border-radius:6px;"
                " padding:0 12px; font-weight:bold; }"
            )