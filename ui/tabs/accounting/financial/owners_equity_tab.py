"""
ui/tabs/accounting/financial/owners_equity_tab.py
==================================================
OwnersEquityTab — تبويب قائمة حقوق الملكية.

[إصلاح v4 — توحيد الـ UI]:
  - PageHeader بدل hdr اليدوي.
  - StatRow بدل _stat_card اليدوية.
  - SafeConnMixin كما هو.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QTableWidgetItem,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor
from ui.widgets.panels.themed_inputs import ThemedFrame

from services.accounting.statements_service import StatementsService
from ui.widgets.tables.tables import make_table
from ui.widgets.core.events import bus
from ui.widgets.components.headers_page import PageHeader
from ui.widgets.components.stat_card import StatRow, StatItem
from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.font import FS_SM, FS_BASE
from ui.constants import (
    FINANCIAL_TAB_MARGIN_H, FINANCIAL_TAB_MARGIN_T, FINANCIAL_TAB_MARGIN_B,
    FINANCIAL_TAB_SPACING, FINANCIAL_SPLITTER_HANDLE_W, FINANCIAL_TABLE_MARGIN_INNER,
    FINANCIAL_COL_CODE_W, FINANCIAL_COL_TYPE_W,
    FINANCIAL_COL_AMOUNT_OE_W, FINANCIAL_HDR_BORDER_RADIUS,
    FINANCIAL_HDR_PAD_V, FINANCIAL_HDR_PAD_H,
    FINANCIAL_FRAME_MARGIN_H, FINANCIAL_FRAME_MARGIN_V,
    FINANCIAL_FRAME_BORDER_RADIUS, INPUT_BORDER_W,
)
from ._financial_helpers import _money


class OwnersEquityTab(SafeConnMixin, QWidget, WidgetMixin):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self._init_safe_conn(conn, "accounting")
        self._company_id = self._get_company_id()
        self._build()
        self._load()
        bus.company_data_changed.connect(self._on_company_event)
        self._init_widget_mixin(theme=True, font=False, lang=True, data=False)

    def _on_company_event(self, company_id: int):
        if self._on_company_event_safe(company_id):
            self._load()

    def _refresh_lang(self, *_):
        pass  # النصوص داخل _build — تُعاد عند إعادة البناء الكاملة

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(FINANCIAL_TAB_MARGIN_H, FINANCIAL_TAB_MARGIN_T, FINANCIAL_TAB_MARGIN_H, FINANCIAL_TAB_MARGIN_B)
        root.setSpacing(FINANCIAL_TAB_SPACING)

        # ── هيدر الصفحة (بدل hdr اليدوي) ──
        root.addWidget(PageHeader(
            title=tr("owners_equity_title"),
            icon="👑",
            accent=_C["acc_type_capital"],
        ))

        # ── البطاقات الإحصائية (بدل _stat_card اليدوية) ──
        self._stats = StatRow([
            StatItem(tr("capital_label_bs"),   color=_C["acc_type_capital"],  icon="💰"),
            StatItem(tr("net_income_col"),      color=_C["success"],           icon="📈"),
            StatItem(tr("drawings_label"),      color=_C["acc_type_drawings"], icon="💸"),
            StatItem(tr("net_equity"),          color=_C["accent"],            icon="⚖️"),
        ])
        root.addWidget(self._stats)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(FINANCIAL_SPLITTER_HANDLE_W)

        left_w = QWidget()
        ll = QVBoxLayout(left_w)
        ll.setContentsMargins(0, FINANCIAL_TABLE_MARGIN_INNER, FINANCIAL_TABLE_MARGIN_INNER, 0)
        cr_hdr = QLabel(tr("equity_increases"))
        cr_hdr.setStyleSheet(
            f"font-weight:bold; color:{_C['acc_type_capital']}; font-size:{FS_SM}px;"
            f"background:{_C['investor_capital_bg']}; border-radius:{FINANCIAL_HDR_BORDER_RADIUS}px;"
            f" padding:{FINANCIAL_HDR_PAD_V}px {FINANCIAL_HDR_PAD_H}px;"
        )
        ll.addWidget(cr_hdr)
        self.table_cr = make_table(
            [tr("code"), tr("item_col"), tr("type"), tr("amount")], stretch_col=1
        )
        self.table_cr.setColumnWidth(0, FINANCIAL_COL_CODE_W)
        self.table_cr.setColumnWidth(2, FINANCIAL_COL_TYPE_W)
        self.table_cr.setColumnWidth(3, FINANCIAL_COL_AMOUNT_OE_W)
        ll.addWidget(self.table_cr)
        splitter.addWidget(left_w)

        right_w = QWidget()
        rl = QVBoxLayout(right_w)
        rl.setContentsMargins(FINANCIAL_TABLE_MARGIN_INNER, FINANCIAL_TABLE_MARGIN_INNER, 0, 0)
        dr_hdr = QLabel(tr("equity_decreases"))
        dr_hdr.setStyleSheet(
            f"font-weight:bold; color:{_C['danger']}; font-size:{FS_SM}px;"
            f"background:{_C['investor_drawings_bg']}; border-radius:{FINANCIAL_HDR_BORDER_RADIUS}px;"
            f" padding:{FINANCIAL_HDR_PAD_V}px {FINANCIAL_HDR_PAD_H}px;"
        )
        rl.addWidget(dr_hdr)
        self.table_dr = make_table(
            [tr("code"), tr("item_col"), tr("type"), tr("amount")], stretch_col=1
        )
        self.table_dr.setColumnWidth(0, FINANCIAL_COL_CODE_W)
        self.table_dr.setColumnWidth(2, FINANCIAL_COL_TYPE_W)
        self.table_dr.setColumnWidth(3, FINANCIAL_COL_AMOUNT_OE_W)
        rl.addWidget(self.table_dr)
        splitter.addWidget(right_w)

        root.addWidget(splitter, stretch=1)

        eq_frame = ThemedFrame()
        eq_frame.setStyleSheet(
            f"QFrame {{ background:{_C['info_bg']}; border:{INPUT_BORDER_W}px solid {_C['info_border']};"
            f" border-radius:{FINANCIAL_FRAME_BORDER_RADIUS}px; }}"
        )
        eq_lay = QHBoxLayout(eq_frame)
        eq_lay.setContentsMargins(FINANCIAL_FRAME_MARGIN_H, FINANCIAL_FRAME_MARGIN_V, FINANCIAL_FRAME_MARGIN_H, FINANCIAL_FRAME_MARGIN_V)
        self.lbl_equation = QLabel("")
        self.lbl_equation.setStyleSheet(
            f"font-size:{FS_BASE}px; font-weight:bold; color:{_C['accent']};"
            "background:transparent; border:none;"
        )
        eq_lay.addWidget(self.lbl_equation)
        root.addWidget(eq_frame)

    def _load(self):
        try:
            data = StatementsService(self._get_safe_conn()).get_owners_equity_statement()
        except Exception as e:
            print(f"[OwnersEquityTab] _load error: {e}")
            return

        self.table_cr.setRowCount(0)
        for row in data["capital_accounts"]:
            r = self.table_cr.rowCount()
            self.table_cr.insertRow(r)
            self.table_cr.setItem(r, 0, QTableWidgetItem(row["code"]))
            n = QTableWidgetItem(row["name"])
            n.setToolTip(row["name"])
            self.table_cr.setItem(r, 1, n)
            self.table_cr.setItem(r, 2, QTableWidgetItem(tr("capital_label_bs")))
            ai = QTableWidgetItem(f"{row['amount']:,.2f}")
            ai.setForeground(QColor(_C["acc_type_capital"]))
            self.table_cr.setItem(r, 3, ai)

        ni = data["net_income"]
        r  = self.table_cr.rowCount()
        self.table_cr.insertRow(r)
        self.table_cr.setItem(r, 0, QTableWidgetItem(""))
        self.table_cr.setItem(r, 1, QTableWidgetItem(tr("net_income_row")))
        self.table_cr.setItem(r, 2, QTableWidgetItem(tr("income_minus_expenses")))
        ni_item = QTableWidgetItem(f"{ni:,.2f}")
        ni_item.setForeground(QColor(_C["success"]) if ni >= 0 else QColor(_C["danger"]))
        self.table_cr.setItem(r, 3, ni_item)

        self.table_dr.setRowCount(0)
        for row in data["drawings_accounts"]:
            r = self.table_dr.rowCount()
            self.table_dr.insertRow(r)
            self.table_dr.setItem(r, 0, QTableWidgetItem(row["code"]))
            n = QTableWidgetItem(row["name"])
            n.setToolTip(row["name"])
            self.table_dr.setItem(r, 1, n)
            self.table_dr.setItem(r, 2, QTableWidgetItem(tr("drawings_label")))
            ai = QTableWidgetItem(f"{row['amount']:,.2f}")
            ai.setForeground(QColor(_C["acc_type_drawings"]))
            self.table_dr.setItem(r, 3, ai)

        self._stats.set_value(0, _money(data["total_capital"]))
        self._stats.set_value(1, _money(ni),
                              color=_C["success"] if ni >= 0 else _C["danger"])
        self._stats.set_value(2, _money(data["total_drawings"]))

        total = data["total_equity"]
        self._stats.set_value(3, _money(total),
                              color=_C["accent"] if total >= 0 else _C["danger"])

        self.lbl_equation.setText(
            tr("equity_equation").format(
                capital=f"{data['total_capital']:,.2f}",
                net_income=f"{ni:,.2f}",
                drawings=f"{data['total_drawings']:,.2f}",
                total=f"{total:,.2f}",
            )
        )