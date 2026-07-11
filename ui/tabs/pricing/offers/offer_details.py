"""
ui/tabs/pricing/offers/offer_details.py
================================
_OfferDetails — لوحة عرض تفاصيل العرض المختار.
"""

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from services.pricing.offers_service import get_offer_summary
from ui.widgets.core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import (
    TABLE_BORDER_RADIUS, FORM_LAYOUT_MARGIN, SPACING_MD, SPACING_SM,
    TABLE_MIN_HEIGHT_DEFAULT,
    OFFER_DET_COL1_CAT_W, OFFER_DET_COL2_QTY_W, OFFER_DET_COL3_COST_W,
    OFFER_DET_COL4_PRICE_W, OFFER_DET_COL5_TOTAL_W, OFFER_DET_COL6_PROFIT_W,
)

from ..pricing._stat_box import stat_box


class _OfferDetails(QFrame, WidgetMixin):

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._init_widget_mixin(lang=True, data=False)
        self._build()
        self._refresh_style()

    def _refresh_style(self, *_):
        from ui.theme import _C
        from ui.font import FS_XS, FS_MD
        self.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_surface']};
                border: 1px solid {_C['orange_border']};
                border-radius: {TABLE_BORDER_RADIUS}px;
            }}
        """)
        self.lbl_title.setStyleSheet(
            f"font-weight:bold; color:{_C['orange']}; font-size:{FS_MD}px;"
            "background:transparent; border:none;"
        )
        self.lbl_notes.setStyleSheet(
            f"font-size:{FS_XS}px; color:{_C['text_muted']}; background:transparent; border:none;"
        )

    # ── connection صالح دايماً ────────────────────────────

    def _live_conn(self):
        from services.companies.company_service import CompanyService
        if CompanyService.is_conn_alive(self.conn):
            return self.conn
        return CompanyService.get_active_erp_conn()

    def _build(self):
        root = QVBoxLayout(self)
        m = FORM_LAYOUT_MARGIN
        root.setContentsMargins(m[0], m[1], m[2], m[3])
        root.setSpacing(SPACING_MD)

        self.lbl_title = QLabel(tr("offer_details_placeholder"))
        self.lbl_title.setAlignment(Qt.AlignCenter)
        root.addWidget(self.lbl_title)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(SPACING_SM)
        f1, self.sl_listed = stat_box(tr("offer_total_before_disc"), "journal_dr_accent")
        f2, self.sl_disc   = stat_box(tr("offer_discount_value"),    "danger_strong")
        f3, self.sl_sell   = stat_box(tr("offer_sell_price"),        "success")
        f4, self.sl_cost   = stat_box(tr("offer_total_cost"),        "text_neutral")
        f5, self.sl_profit = stat_box(tr("offer_profit"),            "success")
        for f in (f1, f2, f3, f4, f5):
            stats_row.addWidget(f, stretch=1)
        root.addLayout(stats_row)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            tr("offer_col_product"),   tr("offer_col_category"),
            tr("offer_col_qty"),       tr("offer_col_unit_cost"),
            tr("offer_col_unit_price"),tr("offer_col_line_total"),
            tr("offer_col_line_profit"),
        ])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        col_widths = {
            1: OFFER_DET_COL1_CAT_W, 2: OFFER_DET_COL2_QTY_W,
            3: OFFER_DET_COL3_COST_W, 4: OFFER_DET_COL4_PRICE_W,
            5: OFFER_DET_COL5_TOTAL_W, 6: OFFER_DET_COL6_PROFIT_W,
        }
        for col, w in col_widths.items():
            hh.setSectionResizeMode(col, QHeaderView.Interactive)
            self.table.setColumnWidth(col, w)
        self.table.setMinimumHeight(TABLE_MIN_HEIGHT_DEFAULT)
        root.addWidget(self.table, stretch=1)

        self.lbl_notes = QLabel("")
        self.lbl_notes.setWordWrap(True)
        root.addWidget(self.lbl_notes)

    def load(self, offer_id: int):
        try:
            conn = self._live_conn()
            s = get_offer_summary(conn, offer_id)
        except Exception:
            return
        if not s:
            return

        cat_part = (
            tr("offer_details_category_part").format(category=s["category_name"])
            if s.get("category_name") else ""
        )
        self.lbl_title.setText(
            tr("offer_details_title").format(
                name=s["offer_name"],
                discount=s["discount"],
                created_at=s["created_at"],
                category=cat_part,
            )
        )

        self.table.setRowCount(0)
        from ui.theme import _C
        from ui.font import FS_LG
        for line in s["lines"]:
            r = self.table.rowCount()
            self.table.insertRow(r)

            icon_key = "offer_item_final_icon" if line["item_type"] == "final" else "offer_item_semi_icon"
            self.table.setItem(r, 0, QTableWidgetItem(
                tr(icon_key).format(name=line["item_name"])
            ))
            self.table.setItem(r, 1, QTableWidgetItem(line["category_name"] or tr("dash")))
            self.table.setItem(r, 2, QTableWidgetItem(f"{line['qty']:.4g}"))

            cost_item = QTableWidgetItem(f"{line['unit_cost']:.2f}")
            cost_item.setForeground(QColor(_C["journal_dr_accent"]))
            self.table.setItem(r, 3, cost_item)

            if line["has_pricing"]:
                price_item = QTableWidgetItem(f"{line['unit_price']:.2f}")
                price_item.setForeground(QColor(_C["success"]))
            else:
                price_item = QTableWidgetItem(tr("offer_no_pricing_cell"))
                price_item.setForeground(QColor(_C["orange"]))
            self.table.setItem(r, 4, price_item)

            if line["has_pricing"]:
                line_item = QTableWidgetItem(f"{line['line_listed']:.2f}")
                line_item.setForeground(QColor(_C["orange"]))
            else:
                line_item = QTableWidgetItem(tr("dash"))
            self.table.setItem(r, 5, line_item)

            if line["has_pricing"]:
                line_profit = (line["unit_price"] - line["unit_cost"]) * line["qty"]
                lp_item = QTableWidgetItem(f"{line_profit:.2f}")
                lp_item.setForeground(
                    QColor(_C["success"]) if line_profit >= 0 else QColor(_C["danger"])
                )
                self.table.setItem(r, 6, lp_item)
            else:
                self.table.setItem(r, 6, QTableWidgetItem(tr("dash")))

        disc_pct = s["discount"]
        disc_amt = s["total_listed"] - s["sell_price"]

        self.sl_listed.setText(tr("amount_fmt").format(amount=s["total_listed"]))
        self.sl_disc.setText(tr("amount_disc_fmt").format(amount=disc_amt, pct=disc_pct))
        self.sl_sell.setText(tr("amount_fmt").format(amount=s["sell_price"]))
        self.sl_cost.setText(tr("amount_fmt").format(amount=s["total_cost"]))

        profit = s["profit"]
        profit_key = "success" if profit >= 0 else "danger"
        self.sl_profit.setText(tr("amount_fmt").format(amount=profit))
        self.sl_profit.setStyleSheet(
            f"font-size:{FS_LG}px; font-weight:bold; color:{_C[profit_key]};"
            "background:transparent; border:none;"
        )

        notes = s.get("notes", "")
        self.lbl_notes.setText(
            tr("offer_details_notes_prefix").format(notes=notes) if notes else ""
        )

    def clear(self):
        self.lbl_title.setText(tr("offer_details_placeholder"))
        self.table.setRowCount(0)
        for lbl in (self.sl_listed, self.sl_disc, self.sl_sell,
                    self.sl_cost, self.sl_profit):
            lbl.setText(tr("empty_placeholder"))
        self.lbl_notes.setText("")
