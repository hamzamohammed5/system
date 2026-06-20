"""
ui/tabs/costing/product/product_table.py
=================================
_ProductTable  — جدول المنتجات المحفوظة مع FilterBar.

[Refactor] يرث من BaseListPanel بدل البناء اليدوي:
  - حذف: make_table, FilterBar, أزرار يدوية
  - إضافة: COLUMNS, _load_rows, _fill_row, COL_WIDTHS
  - الحفاظ على: API الخارجي (on_select, on_edit, on_delete)
    عبر override لـ _on_add_clicked, _on_edit_item, _on_delete_item
    وربط itemSelectionChanged → on_select callback

التحسين: حذف _WarningBar alias الزائد —
         استخدم BaseWarningBar مباشرة من:
         ui/widgets/components/notification.py
[Fix #7] إضافة style="normal" صريح لزر التعديل لتوحيد المظهر
"""

from db.shared.items_repo  import fetch_items_by_type
from models.costing        import calc_cost
from ui.widgets.base.list_panel  import BaseListPanel
from ui.widgets.tables.tables     import make_item, colored_item

_PRODUCT_SCOPE = {
    "semi":  "semi",
    "final": "final",
}


class _ProductTable(BaseListPanel):
    """
    جدول المنتجات — يرث من BaseListPanel.

    BaseListPanel يوفر:
      - بناء الجدول
      - FilterBar (بحث + تصنيف)
      - _load / _apply_filter
      - section label
      - bus.data_changed auto-connect
    """

    COLUMNS       = ["ID", "الاسم", "التصنيف", "التكلفة"]
    STRETCH_COL   = 1
    EMPTY_ICON    = "🏭"
    EMPTY_TITLE   = "لا توجد منتجات"
    LIST_TITLE    = "─── المنتجات المحفوظة ───"
    ADD_TEXT      = ""           # بدون زر Add — الفورم منفصل
    SHOW_CATEGORY = True
    CONNECT_BUS   = True
    COL_WIDTHS    = {0: 45, 2: 110, 3: 120}

    def __init__(self, conn, product_type: str,
                 on_select, on_edit, on_delete, parent=None):
        self.product_type  = product_type
        self._on_select_cb = on_select
        self._on_edit_cb   = on_edit
        self._on_delete_cb = on_delete
        self._scope        = _PRODUCT_SCOPE.get(product_type, product_type)

        # FILTER_SCOPE يتحدد ديناميكياً حسب product_type
        self.FILTER_SCOPE = self._scope

        super().__init__(conn, parent)

        # ربط اختيار الصف بالـ callback الخارجي
        if hasattr(self, 'table'):
            self.table.itemSelectionChanged.connect(self._on_selection_changed)

    # ══════════════════════════════════════════════════════
    # BaseListPanel interface
    # ══════════════════════════════════════════════════════

    def _load_rows(self) -> list:
        try:
            return list(fetch_items_by_type(self.conn, self.product_type))
        except Exception:
            return []

    def _fill_row(self, table, r: int, row):
        """ملء صف واحد في الجدول."""
        try:
            cost = calc_cost(self.conn, row["id"])
        except Exception:
            cost = 0.0

        table.setItem(r, 0, make_item(str(row["id"]), user_data=row["id"]))
        table.setItem(r, 1, make_item(row["name"]))
        table.setItem(r, 2, make_item(row["category_name"] if row["category_name"] else "—"))
        table.setItem(r, 3, make_item(f"{cost:.4f}"))

    # ══════════════════════════════════════════════════════
    # فلترة مخصصة
    # ══════════════════════════════════════════════════════

    def _match_filter(self, row, query: str) -> bool:
        name   = row["name"] if hasattr(row, "__getitem__") else ""
        cat_id = row["category_id"] if hasattr(row, "__getitem__") else None
        if hasattr(self, "_filter"):
            return self._filter.match(name, cat_id)
        return query.lower() in name.lower()

    # ══════════════════════════════════════════════════════
    # أزرار إضافية (تعديل / حذف)
    # ══════════════════════════════════════════════════════

    def _build_extra_header_actions(self, header):
        """إضافة أزرار تعديل وحذف في الهيدر."""
        # [Fix #7] style="normal" صريح لتوحيد المظهر مع بقية الجداول
        header.add_action("✏️ تعديل المحدد", self._trigger_edit,   style="normal")
        header.add_action("🗑️ حذف المحدد",   self._trigger_delete, style="danger")

    # ══════════════════════════════════════════════════════
    # ربط الـ callbacks الخارجية
    # ══════════════════════════════════════════════════════

    def _on_selection_changed(self):
        """يُطلق callback الخارجي عند تغيير الاختيار."""
        pid = self.selected_pid()
        if self._on_select_cb:
            self._on_select_cb(pid)

    def _trigger_edit(self):
        if self._on_edit_cb:
            self._on_edit_cb(self.selected_pid())

    def _trigger_delete(self):
        if self._on_delete_cb:
            self._on_delete_cb(self.selected_pid())

    def _on_add_clicked(self):
        pass  # الإضافة تتم عبر الـ form المنفصل

    def _on_edit_item(self, item_id):
        if self._on_edit_cb:
            self._on_edit_cb(item_id)

    def _on_delete_item(self, item_id, item_name: str):
        if self._on_delete_cb:
            self._on_delete_cb(item_id)

    def _on_row_double_clicked(self, item_id):
        if self._on_edit_cb:
            self._on_edit_cb(item_id)

    # ══════════════════════════════════════════════════════
    # API متوافق مع الكود القديم
    # ══════════════════════════════════════════════════════

    def selected_pid(self) -> int | None:
        """يرجع ID المنتج المختار حالياً."""
        return self.selected_id()