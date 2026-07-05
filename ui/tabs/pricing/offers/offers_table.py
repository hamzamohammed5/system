"""
ui/tabs/pricing/offers/offers_table.py
================================
_OffersTable — جدول العروض المحفوظة مع فلتر وأزرار تعديل/حذف.
"""
from PyQt5.QtWidgets import QHBoxLayout

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton,
    QTableWidgetItem,
)
from PyQt5.QtGui import QColor

from services.pricing.offers_service import get_all_offers, get_offer_summary

from ui.widgets.components.button   import make_btn

from ui.widgets.panels.form_labels   import section_title
from ui.widgets.tables.tables       import make_table

from ui.widgets.panels.filter import FilterToolbar
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.widgets.core.i18n import tr
from ui.theme import _C
from ui.constants import (
    SPACING_SM, BTN_MIN_HEIGHT, OFFERS_TABLE_ROOT_MARGIN,
    OFFERS_TABLE_COL0_ID_W, OFFERS_TABLE_COL1_NAME_W, OFFERS_TABLE_COL2_CAT_W,
    OFFERS_TABLE_COL3_COUNT_W, OFFERS_TABLE_COL4_DISC_W, OFFERS_TABLE_COL5_LISTED_W,
    OFFERS_TABLE_COL6_SELL_W, OFFERS_TABLE_COL7_COST_W, OFFERS_TABLE_COL8_PROFIT_W,
    OFFERS_TABLE_COL9_DATE_W,
)


def buttons_row(*buttons) -> QHBoxLayout:
    """صف أزرار أفقي."""
    row = QHBoxLayout()
    row.setSpacing(SPACING_SM)
    for btn in buttons:
        row.addWidget(btn)
    row.addStretch()
    return row


class _OffersTable(QWidget, WidgetMixin):
    """جدول العروض المحفوظة مع فلتر وأزرار."""

    def __init__(self, conn, on_edit, on_delete, on_select, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._on_edit   = on_edit
        self._on_delete = on_delete
        self._on_select = on_select
        self._all_rows  = []
        self._init_widget_mixin(theme=False, font=False, lang=False, data=True)
        self._build()
        self._load()

    # ── connection صالح دايماً ────────────────────────────

    def _live_conn(self):
        if self.conn is not None:
            try:
                self.conn.execute("SELECT 1")
                return self.conn
            except Exception:
                pass
        from db.companies.company_state import company_state
        return company_state.get_erp_conn()

    def _refresh_data(self, company_id=None):
        self._load()

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        root = QVBoxLayout(self)
        m = OFFERS_TABLE_ROOT_MARGIN
        root.setContentsMargins(m[0], m[1], m[2], m[3])
        root.setSpacing(SPACING_SM)

        root.addWidget(section_title(tr("offer_saved_list")))

        self._filter = FilterToolbar(self._live_conn(), scope="all")
        self._filter.filter_changed.connect(self._apply_filter)
        root.addWidget(self._filter)

        self.table = make_table(
            [
                tr("id_col"),
                tr("offer_col_product"),       tr("offer_col_category"),
                tr("offer_col_count"),          tr("offer_col_discount_pct"),
                tr("offer_col_total_listed"),   tr("offer_col_sell_price"),
                tr("offer_col_cost"),           tr("offer_col_profit"),
                tr("offer_col_date"),
            ],
            stretch_col=1,
        )
        self.table.setColumnWidth(0, OFFERS_TABLE_COL0_ID_W)
        self.table.setColumnWidth(1, OFFERS_TABLE_COL1_NAME_W)
        self.table.setColumnWidth(2, OFFERS_TABLE_COL2_CAT_W)
        self.table.setColumnWidth(3, OFFERS_TABLE_COL3_COUNT_W)
        self.table.setColumnWidth(4, OFFERS_TABLE_COL4_DISC_W)
        self.table.setColumnWidth(5, OFFERS_TABLE_COL5_LISTED_W)
        self.table.setColumnWidth(6, OFFERS_TABLE_COL6_SELL_W)
        self.table.setColumnWidth(7, OFFERS_TABLE_COL7_COST_W)
        self.table.setColumnWidth(8, OFFERS_TABLE_COL8_PROFIT_W)
        self.table.setColumnWidth(9, OFFERS_TABLE_COL9_DATE_W)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self._on_selection)
        root.addWidget(self.table, stretch=1)

        btn_edit = make_btn(tr('btn_edit'), style="normal")
        btn_del  = make_btn(tr("btn_delete"), style="danger")
        for btn in (btn_edit, btn_del):
            btn.setMinimumHeight(BTN_MIN_HEIGHT)
        btn_edit.clicked.connect(lambda: self._on_edit(self.selected_id()))
        btn_del.clicked.connect(lambda: self._on_delete(self.selected_id()))
        root.addLayout(buttons_row(btn_edit, btn_del))

    # ══════════════════════════════════════════════════════
    # تحميل وفلترة البيانات
    # ══════════════════════════════════════════════════════

    def selected_id(self):
        row = self.table.currentRow()
        return int(self.table.item(row, 0).text()) if row >= 0 else None

    def _on_selection(self):
        oid = self.selected_id()
        if oid is not None:
            self._on_select(oid)

    def _load(self):
        try:
            conn = self._live_conn()
            self._all_rows = list(get_all_offers(conn))
        except Exception:
            self._all_rows = []
        self._apply_filter()

    def _apply_filter(self):
        self.table.setRowCount(0)
        shown = 0
        try:
            conn = self._live_conn()
        except Exception:
            self._filter.set_count(0, 0)
            return

        for offer in self._all_rows:
            if not self._filter.match(offer["name"], offer["category_id"]):
                continue
            try:
                s = get_offer_summary(conn, offer["id"])
            except Exception:
                s = {}
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(offer["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(offer["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(offer["category_name"] or tr("dash")))
            self.table.setItem(r, 3, QTableWidgetItem(str(len(s.get("lines", [])))))
            self.table.setItem(r, 4, QTableWidgetItem(f"{offer['discount']:.1f} %"))
            self.table.setItem(r, 5, QTableWidgetItem(f"{s.get('total_listed', 0):.2f}"))
            self.table.setItem(r, 6, QTableWidgetItem(f"{s.get('sell_price', 0):.2f}"))
            self.table.setItem(r, 7, QTableWidgetItem(f"{s.get('total_cost', 0):.2f}"))

            profit = s.get("profit", 0)
            pi = QTableWidgetItem(f"{profit:.2f}")
            pi.setForeground(QColor(_C["success"]) if profit >= 0 else QColor(_C["danger"]))
            self.table.setItem(r, 8, pi)
            self.table.setItem(r, 9, QTableWidgetItem(offer["created_at"]))
            shown += 1

        self._filter.set_count(shown, len(self._all_rows))
