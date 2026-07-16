"""
ui/tabs/pricing/offers/offer_details.py
================================
_OfferDetails — لوحة عرض تفاصيل العرض المختار.
"""

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout,
    QLabel, QSizePolicy,
)
from PyQt5.QtCore import Qt

from ui.widgets.panels.themed_inputs import ThemedFrame

from services.pricing.offers_service import get_offer_summary
from ui.widgets.core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.widgets.tables.tables import (
    make_item, colored_item, make_splitter_table_guarded,
    fit_splitter_table, refresh_table_styles, ROW_HEIGHT_NORMAL,
)
from ui.constants import (
    TABLE_BORDER_RADIUS, FORM_LAYOUT_MARGIN, SPACING_MD, SPACING_SM,
    TABLE_MIN_HEIGHT_DEFAULT, TABLE_EXTRA_PAD,
    OFFER_DET_COL1_CAT_W, OFFER_DET_COL2_QTY_W, OFFER_DET_COL3_COST_W,
    OFFER_DET_COL4_PRICE_W, OFFER_DET_COL5_TOTAL_W, OFFER_DET_COL6_PROFIT_W,
)

from ..pricing._stat_box import stat_box


class _OfferDetails(ThemedFrame, WidgetMixin):

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
        # [توحيد الجداول] الجدول بقى مبني عبر make_splitter_table_guarded
        # وعليه property "_table_variant"؛ refresh_table_styles هي المصدر
        # الوحيد المركزي لإعادة تطبيق table_style() مع كل تغيير ثيم،
        # بدل ما الجدول يفضل بستايل الثيم القديم وقت الإنشاء بس.
        refresh_table_styles(self)

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
        self.sl_profit_frame = f5   # [إصلاح ثيم] مرجع الـ frame لاستخدام set_value_color
        for f in (f1, f2, f3, f4, f5):
            stats_row.addWidget(f, stretch=1)
        root.addLayout(stats_row)

        # [توحيد الجداول] عمود 0 كان Stretch لوحده وسط أعمدة Interactive
        # تانية — ده بالظبط السلوك المعكوس بصريًا في RTL المذكور في نمط
        # الجداول الموحّد (زي raw_table_panel.py قبل التصحيح). STRETCH_COL
        # لازم يبقى -1 دايمًا؛ الفراغ الباقي بياخده الـ spacer جوه الـ
        # splitter (setStretchLastSection بيتفعل تلقائيًا جوه _build_table).
        col_widths = {
            0: OFFER_DET_COL1_CAT_W,  # اسم المنتج — نفس عرض الفئة تقريبًا كبداية
            1: OFFER_DET_COL1_CAT_W, 2: OFFER_DET_COL2_QTY_W,
            3: OFFER_DET_COL3_COST_W, 4: OFFER_DET_COL4_PRICE_W,
            5: OFFER_DET_COL5_TOTAL_W, 6: OFFER_DET_COL6_PROFIT_W,
        }
        self._splitter, self.table, self._table_guard = make_splitter_table_guarded(
            columns    = [
                tr("offer_col_product"),   tr("offer_col_category"),
                tr("offer_col_qty"),       tr("offer_col_unit_cost"),
                tr("offer_col_unit_price"),tr("offer_col_line_total"),
                tr("offer_col_line_profit"),
            ],
            stretch_col = -1,
            col_widths  = col_widths,
            min_height  = TABLE_MIN_HEIGHT_DEFAULT,
            row_height  = ROW_HEIGHT_NORMAL,
        )
        self._splitter.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        root.addWidget(self._splitter, stretch=1)

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
        for line in s["lines"]:
            r = self.table.rowCount()
            self.table.insertRow(r)

            icon_key = "offer_item_final_icon" if line["item_type"] == "final" else "offer_item_semi_icon"
            self.table.setItem(r, 0, make_item(tr(icon_key).format(name=line["item_name"])))
            self.table.setItem(r, 1, make_item(line["category_name"] or tr("dash")))
            self.table.setItem(r, 2, make_item(f"{line['qty']:.4g}"))

            self.table.setItem(
                r, 3, colored_item(f"{line['unit_cost']:.2f}", color=_C["journal_dr_accent"])
            )

            if line["has_pricing"]:
                price_cell = colored_item(f"{line['unit_price']:.2f}", color=_C["success"])
            else:
                price_cell = colored_item(tr("offer_no_pricing_cell"), color=_C["orange"])
            self.table.setItem(r, 4, price_cell)

            if line["has_pricing"]:
                line_cell = colored_item(f"{line['line_listed']:.2f}", color=_C["orange"])
            else:
                line_cell = make_item(tr("dash"))
            self.table.setItem(r, 5, line_cell)

            if line["has_pricing"]:
                line_profit = (line["unit_price"] - line["unit_cost"]) * line["qty"]
                profit_color = _C["success"] if line_profit >= 0 else _C["danger"]
                self.table.setItem(r, 6, colored_item(f"{line_profit:.2f}", color=profit_color))
            else:
                self.table.setItem(r, 6, make_item(tr("dash")))

        fit_splitter_table(self._splitter, self.table, extra_pad=TABLE_EXTRA_PAD)

        disc_pct = s["discount"]
        disc_amt = s["total_listed"] - s["sell_price"]

        self.sl_listed.setText(tr("amount_fmt").format(amount=s["total_listed"]))
        self.sl_disc.setText(tr("amount_disc_fmt").format(amount=disc_amt, pct=disc_pct))
        self.sl_sell.setText(tr("amount_fmt").format(amount=s["sell_price"]))
        self.sl_cost.setText(tr("amount_fmt").format(amount=s["total_cost"]))

        profit = s["profit"]
        profit_key = "success" if profit >= 0 else "danger"
        self.sl_profit.setText(tr("amount_fmt").format(amount=profit))
        # [إصلاح ثيم] set_value_color بدل setStyleSheet مباشر — بتحفظ
        # اللون وتطبقه تلقائيًا مع كل تغيير ثيم كمان.
        self.sl_profit_frame.set_value_color(profit_key)

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
