"""
ui/tabs/pricing/offers/offers_table.py
================================
_OffersTable — جدول العروض المحفوظة مع فلتر وأزرار تعديل/حذف.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton,
    QTableWidgetItem,
)
from PyQt5.QtGui import QColor

from db.pricing.offers_repo import fetch_all_offers, calc_offer_summary
from ui.helpers import (
    make_table, buttons_row, section_label, danger_button,
)
from ui.widgets.shared.filter_bar import FilterBar
from ui.widgets.mixins.bus import BusConnectedMixin
from ui.widgets.core.i18n import tr
from ui.theme import _C


class _OffersTable(QWidget, BusConnectedMixin):
    """جدول العروض المحفوظة مع فلتر وأزرار."""

    def __init__(self, conn, on_edit, on_delete, on_select, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._on_edit   = on_edit
        self._on_delete = on_delete
        self._on_select = on_select
        self._all_rows  = []
        self._build()
        self._load()
        self._connect_bus(data=True)

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

    def _on_data_changed(self):
        self._load()

    def closeEvent(self, event):
        self._disconnect_bus()
        super().closeEvent(event)

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 10)
        root.setSpacing(6)

        root.addWidget(section_label(tr("offer_saved_list")))

        self._filter = FilterBar(self._live_conn(), scope="all")
        self._filter.filter_changed.connect(self._apply_filter)
        root.addWidget(self._filter)

        self.table = make_table(
            [
                "ID",
                tr("offer_col_product"),       tr("offer_col_category"),
                tr("offer_col_count"),          tr("offer_col_discount_pct"),
                tr("offer_col_total_listed"),   tr("offer_col_sell_price"),
                tr("offer_col_cost"),           tr("offer_col_profit"),
                tr("offer_col_date"),
            ],
            stretch_col=1,
        )
        self.table.setColumnWidth(0, 35)
        self.table.setColumnWidth(1, 140)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 55)
        self.table.setColumnWidth(5, 85)
        self.table.setColumnWidth(6, 80)
        self.table.setColumnWidth(7, 75)
        self.table.setColumnWidth(8, 75)
        self.table.setColumnWidth(9, 120)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self._on_selection)
        root.addWidget(self.table, stretch=1)

        btn_edit = QPushButton(tr("btn_edit"))
        btn_del  = danger_button(tr("btn_delete"))
        for btn in (btn_edit, btn_del):
            btn.setMinimumHeight(30)
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
            self._all_rows = list(fetch_all_offers(conn))
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
                s = calc_offer_summary(conn, offer["id"])
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
