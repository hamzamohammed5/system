"""
ui/tabs/pricing/pricing/_pricing_panel.py
==========================================
_PricingPanel — لوحة إدارة أسعار المنتجات النهائية.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidgetItem, QLabel,
    QDoubleSpinBox, QMessageBox, QFrame,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor
from ui.widgets.panels.themed_inputs import ThemedComboBox

from services.pricing.pricing_service import (
    get_all_pricing, get_pricing, save_pricing, remove_pricing,
    get_final_products, get_item,
)
from models.costing            import calc_cost
from ui.theme import _C
from ui.constants import (
    PRICING_PANEL_SPIN_MIN_H, PRICING_PANEL_ROOT_MARGIN, PRICING_PANEL_ROOT_SPACING,
    PRICING_PANEL_BTN_ROW_SPACING, PRICING_PANEL_FORM_FRAME_RADIUS, PRICING_PANEL_FORM_FRAME_BORDER_W,
    PRICING_PANEL_FORM_MARGIN, PRICING_PANEL_FORM_SPACING, PRICING_PANEL_ROW1_SPACING,
    PRICING_PANEL_CMB_PRODUCT_MIN_H, PRICING_PANEL_CMB_PRODUCT_MIN_W, PRICING_PANEL_SP_MARGIN_W,
    PRICING_PANEL_SP_PRICE_W, PRICING_PANEL_ROW1_INNER_SPACING, PRICING_PANEL_STATS_ROW_SPACING,
    PRICING_PANEL_TABLE_COL0_ID_W, PRICING_PANEL_TABLE_COL1_NAME_W, PRICING_PANEL_TABLE_COL2_CAT_W,
    PRICING_PANEL_TABLE_COL3_COST_W, PRICING_PANEL_TABLE_COL4_MARGIN_W, PRICING_PANEL_TABLE_COL5_PRICE_W,
    PRICING_PANEL_TABLE_COL6_PROFIT_W, PRICING_PANEL_TABLE_COL7_MARGIN_ACTUAL_W,
)

# ── الاستدعاءات المُصحَّحة ──────────────────────────────
from ui.widgets.tables.tables       import make_table
from ui.widgets.components.button   import make_btn
from ui.widgets.panels.form_labels  import section_title
from ui.widgets.panels.filter       import FilterToolbar
from ui.widgets.core.events         import emit_company_data_changed
from ui.widgets.core.i18n           import tr

from ui.tabs.costing.shared.scenario_comparison_widget import ScenarioComparisonWidget
from ui.widgets.core.widget_mixin import WidgetMixin

from ._stat_box import stat_box


def _spin(max_=9999999, dec=2):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(PRICING_PANEL_SPIN_MIN_H)
    return s


def buttons_row(*widgets):
    """بديل buttons_row القديمة — صف أزرار بسيط."""
    lay = QHBoxLayout()
    lay.setSpacing(PRICING_PANEL_BTN_ROW_SPACING)
    for w in widgets:
        lay.addWidget(w)
    lay.addStretch()
    return lay


class _PricingPanel(QWidget, WidgetMixin):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._all_rows   = []
        self._editing_id = None
        self._last_profit = 0.0
        self._build()
        self._load_products_combo()
        self._load()
        self._init_widget_mixin(theme=True, font=True, lang=False, data=True)
        self._refresh_style()

    def _refresh_data(self, company_id=None):
        self._load_products_combo()
        self._load()

    def _refresh_style(self, *_):
        from ui.font import get_font_size, fs
        base = get_font_size()

        self.form_frame.setStyleSheet(
            f"QFrame {{ background: {_C['bg_surface']}; "
            f"border: {PRICING_PANEL_FORM_FRAME_BORDER_W}px solid {_C['border']}; "
            f"border-radius: {PRICING_PANEL_FORM_FRAME_RADIUS}px; }}"
        )
        self.lbl_mode.setStyleSheet(
            f"font-weight:bold; color:{_C['orange']}; font-size:{base}px;"
        )
        self.lbl_prod.setStyleSheet(f"font-weight:bold; font-size:{base}px;")
        self.lbl_margin.setStyleSheet(f"font-weight:bold; font-size:{base}px;")
        self.lbl_pct.setStyleSheet(
            f"font-weight:bold; color:{_C['orange']}; font-size:{fs(base, 1)}px;"
        )
        self.lbl_price.setStyleSheet(f"font-weight:bold; font-size:{base}px;")
        # [إصلاح ثيم] self.table كانت بتاخد table_style() مرة واحدة بس
        # وقت الإنشاء داخل make_table() في _build(). محدش كان بينادي
        # setStyleSheet(table_style()) تاني بعد كده، فلما الثيم يتغير
        # (خصوصاً والجدول فاضي/0 صف) كان يفضل ظاهر بالستايل القديم —
        # خلفية بيضاء واضحة فوق باقي اللوحة الداكنة.
        from ui.widgets.tables.tables import table_style
        self.table.setStyleSheet(table_style())
        # [إصلاح ثيم] btn_save/btn_cancel/btn_del/btn_edit مبنيين بـ
        # make_btn() — لازم refresh_visible_buttons عشان يتابعوا الثيم.
        from ui.widgets.components.button import refresh_visible_buttons
        refresh_visible_buttons(self)
        self._refresh_manual_stats_style()

    def _refresh_manual_stats_style(self):
        """يحدد لون قيمة lbl_stat_profit (success/danger) طبقاً لآخر ربح محسوب.
        set_value_color بتخزن اللون وتطبقه تلقائياً مع كل تغيير ثيم كمان،
        فمفيش فقدان للتلوين عند تبديل الثيم."""
        profit = getattr(self, "_last_profit", 0.0)
        color_key = "success" if profit >= 0 else "danger"
        self.lbl_stat_profit_frame.set_value_color(color_key)

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        root = QVBoxLayout(self)
        m = PRICING_PANEL_ROOT_MARGIN
        root.setContentsMargins(m[0], m[1], m[2], m[3])
        root.setSpacing(PRICING_PANEL_ROOT_SPACING)

        self.form_frame = QFrame()
        form_lay = QVBoxLayout(self.form_frame)
        fm = PRICING_PANEL_FORM_MARGIN
        form_lay.setContentsMargins(fm[0], fm[1], fm[2], fm[3])
        form_lay.setSpacing(PRICING_PANEL_FORM_SPACING)

        self.lbl_mode = QLabel(tr("pricing_new_mode"))
        form_lay.addWidget(self.lbl_mode)

        row1 = QHBoxLayout()
        row1.setSpacing(PRICING_PANEL_ROW1_SPACING)

        self.lbl_prod = QLabel(tr("pricing_product_label") + ":")

        self.cmb_product = ThemedComboBox()
        self.cmb_product.setMinimumHeight(PRICING_PANEL_CMB_PRODUCT_MIN_H)
        self.cmb_product.setMinimumWidth(PRICING_PANEL_CMB_PRODUCT_MIN_W)
        self.cmb_product.currentIndexChanged.connect(self._on_product_selected)

        self.lbl_margin = QLabel(tr("pricing_margin_label") + ":")

        self.sp_margin = _spin(1000, 2)
        self.sp_margin.setValue(30)
        self.sp_margin.setFixedWidth(PRICING_PANEL_SP_MARGIN_W)
        self.sp_margin.valueChanged.connect(self._update_preview)

        self.lbl_pct = QLabel(tr("pricing_margin_pct_sign"))

        self.lbl_price = QLabel(tr("pricing_final_price_label") + ":")
        self.sp_price = _spin()
        self.sp_price.setFixedWidth(PRICING_PANEL_SP_PRICE_W)
        self.sp_price.valueChanged.connect(self._update_profit_from_price)

        row1.addWidget(self.lbl_prod)
        row1.addWidget(self.cmb_product, stretch=2)
        row1.addSpacing(PRICING_PANEL_ROW1_INNER_SPACING)
        row1.addWidget(self.lbl_margin)
        row1.addWidget(self.sp_margin)
        row1.addWidget(self.lbl_pct)
        row1.addSpacing(PRICING_PANEL_ROW1_INNER_SPACING)
        row1.addWidget(self.lbl_price)
        row1.addWidget(self.sp_price)
        row1.addStretch()
        form_lay.addLayout(row1)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(PRICING_PANEL_STATS_ROW_SPACING)
        f1, self.lbl_stat_cost       = stat_box(tr("pricing_cost_stat"),              "info")
        f2, self.lbl_stat_price      = stat_box(tr("pricing_suggested_stat"),    "success")
        f3, self.lbl_stat_manual     = stat_box(tr("pricing_manual_stat"),         "orange")
        f4, self.lbl_stat_profit     = stat_box(tr("pricing_profit_stat"),                "success")
        self.lbl_stat_profit_frame = f4
        f5, self.lbl_stat_margin_pct = stat_box(tr("pricing_margin_actual_stat"), "purple")
        for f in (f1, f2, f3, f4, f5):
            stats_row.addWidget(f, stretch=1)
        form_lay.addLayout(stats_row)

        # ── مقارنة السيناريوهات ──────────────────────────
        self._scenario_comparison = ScenarioComparisonWidget(self.conn)
        form_lay.addWidget(self._scenario_comparison)

        self.btn_save   = make_btn(tr("pricing_save_price_btn"), "success")
        self.btn_cancel = make_btn(tr("btn_cancel"), "ghost")
        self.btn_del    = make_btn(tr("pricing_delete_price_btn"), "danger")
        self.btn_cancel.setVisible(False)
        self.btn_del.setVisible(False)
        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self._reset_form)
        self.btn_del.clicked.connect(self._delete)
        form_lay.addLayout(buttons_row(self.btn_save, self.btn_cancel, self.btn_del))

        root.addWidget(self.form_frame)

        root.addWidget(section_title(tr("pricing_saved_prices")))
        # [إصلاح] FilterBar → FilterToolbar
        self._filter = FilterToolbar(self.conn, scope="final")
        self._filter.filter_changed.connect(self._apply_filter)
        root.addWidget(self._filter)

        self.table = make_table(
            [tr("pricing_col_id"), tr("pricing_col_product"), tr("pricing_col_category"), tr("pricing_col_cost"), tr("pricing_col_margin_pct"),
             tr("pricing_col_price"), tr("pricing_col_profit"), tr("pricing_col_margin_actual_pct")],
            stretch_col=1
        )
        self.table.setColumnWidth(0, PRICING_PANEL_TABLE_COL0_ID_W)
        self.table.setColumnWidth(1, PRICING_PANEL_TABLE_COL1_NAME_W)
        self.table.setColumnWidth(2, PRICING_PANEL_TABLE_COL2_CAT_W)
        self.table.setColumnWidth(3, PRICING_PANEL_TABLE_COL3_COST_W)
        self.table.setColumnWidth(4, PRICING_PANEL_TABLE_COL4_MARGIN_W)
        self.table.setColumnWidth(5, PRICING_PANEL_TABLE_COL5_PRICE_W)
        self.table.setColumnWidth(6, PRICING_PANEL_TABLE_COL6_PROFIT_W)
        self.table.setColumnWidth(7, PRICING_PANEL_TABLE_COL7_MARGIN_ACTUAL_W)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self._on_table_select)
        root.addWidget(self.table, stretch=1)

        btn_edit = make_btn(tr("pricing_edit_selected_btn"), "normal")
        btn_edit.clicked.connect(self._edit_selected)
        root.addLayout(buttons_row(btn_edit))

    # ══════════════════════════════════════════════════════
    # تحميل وتحديث Combo المنتجات
    # ══════════════════════════════════════════════════════

    def _load_products_combo(self):
        prev = self.cmb_product.currentData()
        self.cmb_product.blockSignals(True)
        self.cmb_product.clear()
        self.cmb_product.addItem(tr("pricing_select_product_placeholder"), None)
        for row in get_final_products(self.conn):
            self.cmb_product.addItem(row["name"], row["id"])
        restored = False
        for i in range(self.cmb_product.count()):
            if self.cmb_product.itemData(i) == prev:
                self.cmb_product.setCurrentIndex(i)
                restored = True
                break
        if not restored:
            self.cmb_product.setCurrentIndex(0)
        self.cmb_product.blockSignals(False)

    # ══════════════════════════════════════════════════════
    # منطق المعاينة والإحصائيات
    # ══════════════════════════════════════════════════════

    def _on_product_selected(self):
        self._update_preview()
        self._refresh_scenario_comparison()

    def _update_preview(self):
        prod_id = self.cmb_product.currentData()
        if prod_id is None:
            for lbl in (self.lbl_stat_cost, self.lbl_stat_price,
                        self.lbl_stat_manual, self.lbl_stat_profit,
                        self.lbl_stat_margin_pct):
                lbl.setText(tr("empty_placeholder"))
            return
        cost   = calc_cost(self.conn, prod_id)
        margin = self.sp_margin.value() / 100.0
        price  = cost * (1 + margin)
        self.lbl_stat_cost.setText(tr("pricing_amount_currency_fmt", amount=cost))
        self.lbl_stat_price.setText(tr("pricing_amount_currency_fmt", amount=price))
        if self._editing_id is None:
            self.sp_price.blockSignals(True)
            self.sp_price.setValue(price)
            self.sp_price.blockSignals(False)
        self._refresh_manual_stats(cost)

    def _update_profit_from_price(self):
        prod_id = self.cmb_product.currentData()
        if prod_id is None:
            return
        cost = calc_cost(self.conn, prod_id)
        self._refresh_manual_stats(cost)
        self._scenario_comparison.update_price(self.sp_price.value())

    def _refresh_manual_stats(self, cost: float):
        manual = self.sp_price.value()
        profit = manual - cost
        margin_pct = ((manual - cost) / cost * 100) if cost > 0 else 0.0
        self._last_profit = profit
        self.lbl_stat_manual.setText(tr("pricing_amount_currency_fmt", amount=manual))
        self.lbl_stat_profit.setText(tr("pricing_amount_currency_fmt", amount=profit))
        self._refresh_manual_stats_style()
        self.lbl_stat_margin_pct.setText(f"{margin_pct:.1f} {tr('pricing_margin_pct_sign')}")

    def _refresh_scenario_comparison(self):
        prod_id = self.cmb_product.currentData()
        if prod_id is None:
            self._scenario_comparison.clear()
            return
        current_price = self.sp_price.value()
        self._scenario_comparison.load_product(prod_id, current_price)

    # ══════════════════════════════════════════════════════
    # CRUD
    # ══════════════════════════════════════════════════════

    def _save(self):
        prod_id = self.cmb_product.currentData()
        if prod_id is None:
            QMessageBox.warning(self, tr("warning"), tr("pricing_select_product"))
            return
        price = self.sp_price.value()
        if price <= 0:
            QMessageBox.warning(self, tr("warning"), tr("pricing_price_positive"))
            return
        save_pricing(self.conn, prod_id, self.sp_margin.value(), price)
        self._reset_form()
        emit_company_data_changed()   # [إصلاح] بدل bus.data_changed.emit()

    def _delete(self):
        if self._editing_id is None:
            return
        item = get_item(self.conn, self._editing_id)
        name = item["name"] if item else f"ID:{self._editing_id}"
        if QMessageBox.question(
            self, tr("confirm_delete"), tr("pricing_delete_confirm", name=name),
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            remove_pricing(self.conn, self._editing_id)
            self._reset_form()
            emit_company_data_changed()   # [إصلاح]

    def _reset_form(self):
        self._editing_id = None
        self.cmb_product.setCurrentIndex(0)
        self.sp_margin.setValue(30)
        self.sp_price.setValue(0)
        for lbl in (self.lbl_stat_cost, self.lbl_stat_price,
                    self.lbl_stat_manual, self.lbl_stat_profit,
                    self.lbl_stat_margin_pct):
            lbl.setText(tr("empty_placeholder"))
        self.lbl_mode.setText(tr("pricing_new_mode"))
        self.btn_cancel.setVisible(False)
        self.btn_del.setVisible(False)
        self._scenario_comparison.clear()

    def _edit_selected(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, tr("warning"), tr("pricing_select_product_table"))
            return
        self._load_for_edit(int(self.table.item(row, 0).text()))

    def _on_table_select(self):
        row = self.table.currentRow()
        if row == -1:
            return
        prod_id = int(self.table.item(row, 0).text())
        cost = calc_cost(self.conn, prod_id)
        self.lbl_stat_cost.setText(tr("pricing_cost_suffix", cost=cost))

    def _load_for_edit(self, prod_id: int):
        pricing = get_pricing(self.conn, prod_id)
        item    = get_item(self.conn, prod_id)
        if not item:
            return
        self._editing_id = prod_id
        for i in range(self.cmb_product.count()):
            if self.cmb_product.itemData(i) == prod_id:
                self.cmb_product.setCurrentIndex(i)
                break
        cost = calc_cost(self.conn, prod_id)
        if pricing:
            self.sp_margin.setValue(pricing["margin"])
            self.sp_price.setValue(pricing["price"])
        else:
            self.sp_margin.setValue(30)
            self.sp_price.setValue(cost * 1.3)
        self.lbl_mode.setText(tr("pricing_edit_mode", name=item['name']))
        self.btn_cancel.setVisible(True)
        self.btn_del.setVisible(bool(pricing))
        self._refresh_manual_stats(cost)
        self._scenario_comparison.load_product(prod_id, self.sp_price.value())

    # ══════════════════════════════════════════════════════
    # تحميل الجدول
    # ══════════════════════════════════════════════════════

    def _load(self):
        self._all_rows = list(get_all_pricing(self.conn))
        self._apply_filter()

    def _apply_filter(self):
        self.table.setRowCount(0)
        shown = 0
        for row in self._all_rows:
            if not self._filter.match(row["name"], row["category_id"]):
                continue
            cost   = calc_cost(self.conn, row["id"])
            has_p  = row["pricing_id"] is not None
            price  = row["price"]  if has_p else None
            margin = row["margin"] if has_p else None
            profit = (price - cost) if has_p else None
            margin_actual = ((price - cost) / cost * 100) if (has_p and cost > 0) else None

            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(row["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(row["category_name"] or tr("dash")))
            self.table.setItem(r, 3, QTableWidgetItem(f"{cost:.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(
                f"{margin:.1f} {tr('pricing_margin_pct_sign')}" if margin is not None else tr("empty_placeholder")
            ))
            self.table.setItem(r, 5, QTableWidgetItem(
                f"{price:.2f}" if price is not None else tr("empty_placeholder")
            ))
            profit_item = QTableWidgetItem(
                f"{profit:.2f}" if profit is not None else tr("empty_placeholder")
            )
            if profit is not None:
                profit_item.setForeground(
                    QColor(_C["success"]) if profit >= 0 else QColor(_C["danger"])

                )
            self.table.setItem(r, 6, profit_item)
            self.table.setItem(r, 7, QTableWidgetItem(
                f"{margin_actual:.1f} {tr('pricing_margin_pct_sign')}" if margin_actual is not None else tr("empty_placeholder")
            ))
            shown += 1
        self._filter.set_count(shown, len(self._all_rows))