"""
ui/tabs/pricing/offers/offers_table.py
================================
_OffersTable — جدول العروض المحفوظة مع فلتر وأزرار تعديل/حذف.

[توحيد الجداول] إعادة هيكلة كاملة — يرث الآن من BaseListPanel بدل
QWidget+WidgetMixin المبني يدويًا. التحويل شمل:
  - حذف _build/_load/_apply_filter اليدوية بالكامل؛ BaseListPanel
    توفرها عبر refresh()/_apply_filter() المركزية.
  - الجدول بقى splitter (make_splitter_table_guarded عبر BaseListPanel)
    بدل make_table() المطلَّق داخل QVBoxLayout — يعني بقى فيه spacer
    قابل للسحب وعرض محسوب من مجموع الأعمدة الفعلي (الخاصية 2 في نمط
    الجداول الموحّد)، مش الجدول بيتمطّط لعرض النافذة كله.
  - STRETCH_COL = -1 (نفس التصحيح الموحّد لكل الجداول — كل الأعمدة
    Interactive حرة + stretchLastSection، مفيش عمود واحد بيتصرف
    بعكس اتجاه باقي الأعمدة في RTL).
  - كل خلية بقت عبر make_item/colored_item بدل QTableWidgetItem خام:
    - عمود الربح (كان يدوي بـ setForeground) بقى colored_item بسيطة.
    - الـ ID بقى user_data=... عبر make_item بدل قراءة .text() بالنص
      وتحويله int() — أنضف وأأمن لو الـ ID اتلبس بـ prefix نصي مستقبلًا.
  - أزرار تعديل/حذف انتقلت من buttons_row() تحت الجدول إلى
    _build_extra_header_actions() في الهيدر الموحّد (نفس نمط كل
    الجداول التانية في المشروع).
  - _refresh_style اليدوي (setStyleSheet(table_style()) + إعادة تلوين
    الأزرار) اتشال بالكامل؛ BaseListPanel/refresh_table_styles تتكفل
    بالثيم مركزيًا.
  - الـ API الخارجي (conn, on_edit, on_delete, on_select) اتحافظ
    عليه بالكامل بنفس الـ signature عشان الكود الأب (اللي بينادي
    _OffersTable) يفضل شغال من غير تعديل.
"""
from services.pricing.offers_service import get_all_offers, get_offer_summary

from ui.widgets.base.list_panel import BaseListPanel
from ui.widgets.tables.tables    import make_item, colored_item
from ui.widgets.core.i18n        import tr
from ui.theme import _C


class _OffersTable(BaseListPanel):
    """جدول العروض المحفوظة — يرث من BaseListPanel."""

    COLUMNS     = [
        tr("id_col"),
        tr("offer_col_product"),       tr("offer_col_category"),
        tr("offer_col_count"),          tr("offer_col_discount_pct"),
        tr("offer_col_total_listed"),   tr("offer_col_sell_price"),
        tr("offer_col_cost"),           tr("offer_col_profit"),
        tr("offer_col_date"),
    ]
    STRETCH_COL   = -1
    EMPTY_TITLE   = "no_offers"
    LIST_TITLE    = tr("offer_saved_list")
    ADD_TEXT      = ""
    SHOW_CATEGORY = True
    FILTER_SCOPE  = "all"
    CONNECT_BUS   = True

    def __init__(self, conn, on_edit, on_delete, on_select, parent=None):
        self._on_edit_cb   = on_edit
        self._on_delete_cb = on_delete
        self._on_select_cb = on_select
        super().__init__(conn, parent)
        self.item_selected.connect(self._on_selection_changed)

    # ── connection صالح دايماً ────────────────────────────

    def _live_conn(self):
        from services.companies.company_service import CompanyService
        if CompanyService.is_conn_alive(self.conn):
            return self.conn
        return CompanyService.get_active_erp_conn()

    def _refresh_data(self, company_id=None):
        self.refresh()

    # ══════════════════════════════════════════════════════
    # BaseListPanel interface
    # ══════════════════════════════════════════════════════

    def _load_rows(self) -> list:
        try:
            conn = self._live_conn()
            return list(get_all_offers(conn))
        except Exception:
            return []

    def _match_filter(self, row: dict, query: str) -> bool:
        if hasattr(self, "_filter_toolbar") and self._filter_toolbar:
            return self._filter_toolbar.match(row["name"], row["category_id"])
        return query.lower() in row["name"].lower()

    def _fill_row(self, table, r: int, row: dict):
        try:
            conn = self._live_conn()
            s = get_offer_summary(conn, row["id"])
        except Exception:
            s = {}

        profit = s.get("profit", 0)
        profit_color = _C["success"] if profit >= 0 else _C["danger"]

        table.setItem(r, 0, make_item(str(row["id"]), user_data=row["id"]))
        table.setItem(r, 1, make_item(row["name"]))
        table.setItem(r, 2, make_item(row["category_name"] or tr("dash")))
        table.setItem(r, 3, make_item(str(len(s.get("lines", [])))))
        table.setItem(r, 4, make_item(f"{row['discount']:.1f} %"))
        table.setItem(r, 5, make_item(f"{s.get('total_listed', 0):.2f}"))
        table.setItem(r, 6, make_item(f"{s.get('sell_price', 0):.2f}"))
        table.setItem(r, 7, make_item(f"{s.get('total_cost', 0):.2f}"))
        table.setItem(r, 8, colored_item(f"{profit:.2f}", color=profit_color))
        table.setItem(r, 9, make_item(row["created_at"]))

    # ══════════════════════════════════════════════════════
    # أزرار الهيدر (بدل buttons_row تحت الجدول)
    # ══════════════════════════════════════════════════════

    def _build_extra_header_actions(self, header):
        header.add_action(tr("btn_edit"), self._trigger_edit, style="normal")
        header.add_action(tr("btn_delete"), self._trigger_delete, style="danger")

    def _trigger_edit(self):
        oid = self.selected_id()
        if oid is not None:
            self._on_edit_cb(oid)

    def _trigger_delete(self):
        oid = self.selected_id()
        if oid is not None:
            self._on_delete_cb(oid)

    def _on_add_clicked(self):
        pass  # الإضافة عبر فورم منفصل

    def _on_row_double_clicked(self, item_id):
        self._on_edit_cb(item_id)

    # ══════════════════════════════════════════════════════
    # ربط الاختيار بالـ callback الخارجي
    # ══════════════════════════════════════════════════════

    def _on_selection_changed(self, item_id: int):
        if self._on_select_cb:
            self._on_select_cb(item_id)
