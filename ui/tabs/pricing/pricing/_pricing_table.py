"""
ui/tabs/pricing/pricing/_pricing_table.py
==========================================
_PricingTable — جدول الأسعار المحفوظة (منتجات نهائية + تسعيرها).

[توحيد الجداول] استُخرج من _pricing_panel.py القديم كجدول مستقل يرث
BaseListPanel، بدل ما يكون مبني يدويًا داخل _PricingPanel نفسه.
نفس نمط RawTablePanel/RawInputPanel: الجدول والفورم كلاسات منفصلة،
يجمعهم section أب (_PricingPanel هنا) في layout واحد.

نفس تعديلات _OffersTable بالظبط:
  - splitter بدل make_table() المطلَّق (خاصية الجدول 2)
  - STRETCH_COL = -1 (توحيد كل الجداول)
  - make_item/colored_item بدل QTableWidgetItem خام
  - زر "تعديل" عبر _build_extra_header_actions بدل buttons_row يدوي
    تحت الجدول (الحذف يفضل من جوه الفورم زي ما كان، مش من الجدول)
"""
from models.costing import calc_cost
from ui.widgets.base.list_panel import BaseListPanel
from ui.widgets.tables.tables    import make_item, colored_item
from ui.widgets.core.i18n        import tr
from ui.theme import _C


class _PricingTable(BaseListPanel):
    """جدول الأسعار المحفوظة — يرث من BaseListPanel."""

    COLUMNS       = [
        tr("pricing_col_id"), tr("pricing_col_product"), tr("pricing_col_category"),
        tr("pricing_col_cost"), tr("pricing_col_margin_pct"),
        tr("pricing_col_price"), tr("pricing_col_profit"), tr("pricing_col_margin_actual_pct"),
    ]
    STRETCH_COL   = -1
    EMPTY_TITLE   = "no_pricing"
    LIST_TITLE    = tr("pricing_saved_prices")
    ADD_TEXT      = ""
    SHOW_CATEGORY = True
    FILTER_SCOPE  = "final"
    CONNECT_BUS   = True

    def __init__(self, conn, on_edit_selected, on_select=None, parent=None):
        self._on_edit_cb   = on_edit_selected
        self._on_select_cb = on_select
        super().__init__(conn, parent)
        self.item_selected.connect(self._on_selection_changed)

    def _refresh_data(self, company_id=None):
        self.refresh()

    # ══════════════════════════════════════════════════════
    # BaseListPanel interface
    # ══════════════════════════════════════════════════════

    def _load_rows(self) -> list:
        from services.pricing.pricing_service import get_all_pricing
        try:
            return list(get_all_pricing(self.conn))
        except Exception:
            return []

    def _match_filter(self, row: dict, query: str) -> bool:
        if hasattr(self, "_filter_toolbar") and self._filter_toolbar:
            return self._filter_toolbar.match(row["name"], row["category_id"])
        return query.lower() in row["name"].lower()

    def _fill_row(self, table, r: int, row: dict):
        cost   = calc_cost(self.conn, row["id"])
        has_p  = row["pricing_id"] is not None
        price  = row["price"]  if has_p else None
        margin = row["margin"] if has_p else None
        profit = (price - cost) if has_p else None
        margin_actual = ((price - cost) / cost * 100) if (has_p and cost > 0) else None

        table.setItem(r, 0, make_item(str(row["id"]), user_data=row["id"]))
        table.setItem(r, 1, make_item(row["name"]))
        table.setItem(r, 2, make_item(row["category_name"] or tr("dash")))
        table.setItem(r, 3, make_item(f"{cost:.2f}"))
        table.setItem(r, 4, make_item(
            f"{margin:.1f} {tr('pricing_margin_pct_sign')}" if margin is not None else tr("empty_placeholder")
        ))
        table.setItem(r, 5, make_item(
            f"{price:.2f}" if price is not None else tr("empty_placeholder")
        ))

        if profit is not None:
            profit_color = _C["success"] if profit >= 0 else _C["danger"]
            table.setItem(r, 6, colored_item(f"{profit:.2f}", color=profit_color))
        else:
            table.setItem(r, 6, make_item(tr("empty_placeholder")))

        table.setItem(r, 7, make_item(
            f"{margin_actual:.1f} {tr('pricing_margin_pct_sign')}" if margin_actual is not None else tr("empty_placeholder")
        ))

    # ══════════════════════════════════════════════════════
    # أزرار الهيدر (بدل buttons_row تحت الجدول)
    # ══════════════════════════════════════════════════════

    def _build_extra_header_actions(self, header):
        header.add_action(tr("pricing_edit_selected_btn"), self._trigger_edit, style="normal")

    def _trigger_edit(self):
        pid = self.selected_id()
        if pid is None:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, tr("warning"), tr("pricing_select_product_table"))
            return
        self._on_edit_cb(pid)

    def _on_add_clicked(self):
        pass  # الإضافة عبر الفورم فوق الجدول

    def _on_row_double_clicked(self, item_id):
        self._on_edit_cb(item_id)

    def _on_selection_changed(self, item_id: int):
        if self._on_select_cb:
            self._on_select_cb(item_id)
