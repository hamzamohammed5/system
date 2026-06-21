"""
ui/tabs/pricing/pricing/_pricing_panel.py
==========================================
_PricingPanel — لوحة إدارة أسعار المنتجات النهائية.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidgetItem, QLabel,
    QDoubleSpinBox, QMessageBox, QFrame, QComboBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.shared.items_repo     import fetch_items_by_type, fetch_item
from db.pricing.pricing_repo  import fetch_all_pricing, upsert_pricing, delete_pricing, fetch_pricing
from models.costing            import calc_cost
from ui.theme import _C
from ui.font import FS_BASE, FS_MD, FS_LG

# ── الاستدعاءات المُصحَّحة ──────────────────────────────
from ui.widgets.tables.tables       import make_table
from ui.widgets.components.button   import make_btn
from ui.widgets.panels.form_labels  import section_title
from ui.widgets.panels.filter       import FilterToolbar
from ui.widgets.core.events         import bus, emit_company_data_changed
from ui.widgets.core.i18n           import tr

from ui.tabs.costing.shared.scenario_comparison_widget import ScenarioComparisonWidget

from ._stat_box import stat_box


def _spin(max_=9999999, dec=2):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(30)
    return s


def buttons_row(*widgets):
    """بديل buttons_row القديمة — صف أزرار بسيط."""
    lay = QHBoxLayout()
    lay.setSpacing(8)
    for w in widgets:
        lay.addWidget(w)
    lay.addStretch()
    return lay


class _PricingPanel(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._all_rows   = []
        self._editing_id = None
        self._build()
        self._load_products_combo()
        self._load()
        # [إصلاح] data_changed محذوف — استخدم company_data_changed
        bus.company_data_changed.connect(lambda _cid: self._load_products_combo())
        bus.company_data_changed.connect(lambda _cid: self._load())

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(8)

        form_frame = QFrame()
        form_frame.setStyleSheet(f"""
            QFrame {{ background: {_C['bg_surface']}; border: 1px solid {_C['border']}; border-radius: 8px; }}
        """)
        form_lay = QVBoxLayout(form_frame)
        form_lay.setContentsMargins(14, 12, 14, 12)
        form_lay.setSpacing(10)

        self.lbl_mode = QLabel(tr("pricing_new_mode"))
        self.lbl_mode.setStyleSheet(f"font-weight:bold; color:{_C['orange']}; font-size:{FS_BASE}px;")
        form_lay.addWidget(self.lbl_mode)

        row1 = QHBoxLayout()
        row1.setSpacing(12)

        lbl_prod = QLabel(tr("pricing_product_label") + ":")
        lbl_prod.setStyleSheet(f"font-weight:bold; font-size:{FS_BASE}px;")

        self.cmb_product = QComboBox()
        self.cmb_product.setMinimumHeight(32)
        self.cmb_product.setMinimumWidth(200)
        self.cmb_product.currentIndexChanged.connect(self._on_product_selected)

        lbl_margin = QLabel(tr("pricing_margin_label") + ":")
        lbl_margin.setStyleSheet(f"font-weight:bold; font-size:{FS_BASE}px;")

        self.sp_margin = _spin(1000, 2)
        self.sp_margin.setValue(30)
        self.sp_margin.setFixedWidth(110)
        self.sp_margin.valueChanged.connect(self._update_preview)

        lbl_pct = QLabel(tr("pricing_margin_pct_sign"))
        lbl_pct.setStyleSheet(f"font-weight:bold; color:{_C['orange']}; font-size:{FS_MD}px;")

        lbl_price = QLabel(tr("pricing_final_price_label") + ":")
        lbl_price.setStyleSheet(f"font-weight:bold; font-size:{FS_BASE}px;")
        self.sp_price = _spin()
        self.sp_price.setFixedWidth(130)
        self.sp_price.valueChanged.connect(self._update_profit_from_price)

        row1.addWidget(lbl_prod)
        row1.addWidget(self.cmb_product, stretch=2)
        row1.addSpacing(8)
        row1.addWidget(lbl_margin)
        row1.addWidget(self.sp_margin)
        row1.addWidget(lbl_pct)
        row1.addSpacing(8)
        row1.addWidget(lbl_price)
        row1.addWidget(self.sp_price)
        row1.addStretch()
        form_lay.addLayout(row1)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(8)
        f1, self.lbl_stat_cost       = stat_box(tr("pricing_cost_stat"),              "info")
        f2, self.lbl_stat_price      = stat_box(tr("pricing_suggested_stat"),    "success")
        f3, self.lbl_stat_manual     = stat_box(tr("pricing_manual_stat"),         "orange")
        f4, self.lbl_stat_profit     = stat_box(tr("pricing_profit_stat"),                "success")
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

        root.addWidget(form_frame)

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
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 160)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 70)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 80)
        self.table.setColumnWidth(7, 90)
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
        for row in fetch_items_by_type(self.conn, "final"):
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
                lbl.setText("─")
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
        self.lbl_stat_manual.setText(tr("pricing_amount_currency_fmt", amount=manual))
        color_profit = _C["success"] if profit >= 0 else _C["danger"]
        self.lbl_stat_profit.setText(tr("pricing_amount_currency_fmt", amount=profit))
        self.lbl_stat_profit.setStyleSheet(
            f"font-size:{FS_LG}px; font-weight:bold; color:{color_profit};"
            "background:transparent; border:none;"
        )
        self.lbl_stat_margin_pct.setText(f"{margin_pct:.1f} %")

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
        upsert_pricing(self.conn, prod_id, self.sp_margin.value(), price)
        self._reset_form()
        emit_company_data_changed()   # [إصلاح] بدل bus.data_changed.emit()

    def _delete(self):
        if self._editing_id is None:
            return
        item = fetch_item(self.conn, self._editing_id)
        name = item["name"] if item else f"ID:{self._editing_id}"
        if QMessageBox.question(
            self, tr("confirm_delete"), tr("pricing_delete_confirm", name=name),
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            delete_pricing(self.conn, self._editing_id)
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
            lbl.setText("─")
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
        pricing = fetch_pricing(self.conn, prod_id)
        item    = fetch_item(self.conn, prod_id)
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
        self._all_rows = list(fetch_all_pricing(self.conn))
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
            self.table.setItem(r, 2, QTableWidgetItem(row["category_name"] or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{cost:.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(
                f"{margin:.1f} %" if margin is not None else "─"
            ))
            self.table.setItem(r, 5, QTableWidgetItem(
                f"{price:.2f}" if price is not None else "─"
            ))
            profit_item = QTableWidgetItem(
                f"{profit:.2f}" if profit is not None else "─"
            )
            if profit is not None:
                profit_item.setForeground(
                    QColor(_C["success"]) if profit >= 0 else QColor(_C["danger"])

                )
            self.table.setItem(r, 6, profit_item)
            self.table.setItem(r, 7, QTableWidgetItem(
                f"{margin_actual:.1f} %" if margin_actual is not None else "─"
            ))
            shown += 1
        self._filter.set_count(shown, len(self._all_rows))