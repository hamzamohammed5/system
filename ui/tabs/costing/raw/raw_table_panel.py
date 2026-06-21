"""
ui/tabs/costing/raw/raw_table_panel.py
========================================
RawTablePanel — جدول الخامات مع دعم العناصر المشتركة/المنشورة.

يرث من BaseListPanel + SharedOpsMixin.
- لا بناء جدول يدوي
- لا _load / _apply_filter يدوي
- كل shared logic عبر SharedOpsMixin
"""

from PyQt5.QtGui  import QColor
from PyQt5.QtCore import Qt

from ui.widgets.base.list_panel        import BaseListPanel
from ui.widgets.mixins.shared_ops      import SharedOpsMixin
from ui.widgets.tables.tables           import make_item, colored_item
from ui.widgets.dialogs.confirm        import confirm_delete          # ✅ كان: ui.helpers
from ui.widgets.core.events            import emit_company_data_changed
from ui.widgets.core.i18n              import tr
from ui.tabs.costing.shared._utils     import (
    to_dict, SHARED_COLOR, SHARED_BG, PUBLISHED_COLOR, PUBLISHED_BG,
)
from ui.tabs.companies.shared_items_mixin import (
    get_shared_raws, get_published_local_names, is_shared_id,
)


class RawTablePanel(BaseListPanel, SharedOpsMixin):
    """
    جدول الخامات — يرث من BaseListPanel.

    BaseListPanel يوفر:
      - بناء الجدول
      - FilterBar (بحث + تصنيف)
      - _load / _apply_filter
      - section label
      - bus.data_changed auto-connect
    """

    COLUMNS            = [tr("raw_col_id"), tr("raw_col_name"), tr("raw_col_category"),
                           tr("raw_col_total_price"), tr("raw_col_qty"), tr("raw_col_unit_price")]
    STRETCH_COL        = 1
    EMPTY_ICON         = "🧱"
    EMPTY_TITLE        = tr("no_raws")
    LIST_TITLE         = f"─── {tr('saved_raws')} ───"
    ADD_TEXT           = ""
    SHOW_CATEGORY      = True
    FILTER_SCOPE       = "raw"
    COL_WIDTHS         = {0: 45, 2: 110, 3: 90, 4: 90, 5: 95}
    CONNECT_BUS        = True

    def __init__(self, conn, input_panel=None, parent=None):
        self._input_panel      = input_panel
        self._published_names  = set()
        super().__init__(conn, parent)

    # ══════════════════════════════════════════════════════
    # تحميل البيانات
    # ══════════════════════════════════════════════════════

    def _load_rows(self) -> list:
        from db.shared.items_repo import fetch_items_by_type
        local_rows = [to_dict(r) for r in fetch_items_by_type(self.conn, "raw")]
        self._published_names = get_published_local_names("raw")
        shared_rows = get_shared_raws(local_rows)
        return local_rows + shared_rows

    # ══════════════════════════════════════════════════════
    # ملء الجدول
    # ══════════════════════════════════════════════════════

    def _fill_row(self, table, r: int, row: dict):
        from models.costing_base import raw_unit_price

        is_shared    = row.get("_is_shared", False) or row.get("is_shared", False)
        is_published = (
            not is_shared and
            str(row.get("name", "")).strip().lower() in self._published_names
        )

        prefix = "🔗 " if is_shared else ("📤 " if is_published else "")
        color = (
                SHARED_COLOR()    if is_shared    else
                PUBLISHED_COLOR() if is_published else
                None
            )

        tq     = row.get("total_qty")
        price  = float(row.get("price", 0))
        unit   = (price / float(tq)) if (tq and float(tq) > 0 and is_shared) \
                 else raw_unit_price(row)

        id_text = "🔗" if is_shared else ("📤" if is_published else str(row.get("id", "")))
        id_item = make_item(id_text, user_data=row.get("id"))
        table.setItem(r, 0, id_item)
        table.setItem(r, 1, colored_item(prefix + row.get("name", ""), color=color))
        table.setItem(r, 2, colored_item(row.get("category_name") or tr("dash"), color=color))
        table.setItem(r, 3, colored_item(f"{price:.2f}", color=color))
        table.setItem(r, 4, colored_item(str(tq) if tq is not None else tr("dash"), color=color))
        table.setItem(r, 5, colored_item(f"{unit:.4f}", color=color))

        if color:
            bg = SHARED_BG() if is_shared else PUBLISHED_BG()
            for col in range(table.columnCount()):
                itm = table.item(r, col)
                if itm:
                    itm.setBackground(QColor(bg))
                    itm.setForeground(QColor(color))

    # ══════════════════════════════════════════════════════
    # فلترة مخصصة (يدعم shared rows)
    # ══════════════════════════════════════════════════════

    def _match_filter(self, row: dict, query: str) -> bool:
        name = row.get("name", "")
        cat  = row.get("category_id")
        return self._filter.match(name, cat) if hasattr(self, "_filter") \
               else query.lower() in name.lower()

    # ══════════════════════════════════════════════════════
    # أزرار إضافية
    # ══════════════════════════════════════════════════════

    def _build_extra_header_actions(self, header):
        header.add_action(tr("raw_bulk_replace_btn"),  self._bulk_replace,     "primary")
        header.add_action(tr("raw_edit_shared_btn"), self._edit_shared_selected)
        header.add_action(tr("raw_publish_btn"),    self._publish_selected)

    # ══════════════════════════════════════════════════════
    # إجراءات الأزرار
    # ══════════════════════════════════════════════════════

    def _on_add_clicked(self):
        pass

    def _on_row_double_clicked(self, item_id):
        if self._input_panel and not is_shared_id(item_id):
            self._input_panel.load_for_edit(int(item_id))

    def _bulk_replace(self):
        from PyQt5.QtWidgets import QMessageBox
        from ui.tabs.costing.shared.bulk_replace.bulk_replace_dialog import BulkReplaceDialog

        item_id = self.selected_id()
        if item_id is None:
            QMessageBox.information(self, tr("warning"), tr("raw_select_first"))
            return
        if is_shared_id(item_id):
            QMessageBox.information(self, tr("warning"),
                                    tr("raw_bulk_replace_not_available"))
            return
        row = self._get_current_row_dict()
        name = row.get("name", f"ID:{item_id}") if row else f"ID:{item_id}"
        BulkReplaceDialog(
            conn=self.conn, child_type="raw",
            child_id=int(item_id), child_name=name, parent=self,
        ).exec_()

    def _edit_shared_selected(self):
        from PyQt5.QtWidgets import QMessageBox
        item_id = self.selected_id()
        if item_id is None:
            QMessageBox.information(self, tr("warning"), tr("raw_select_first"))
            return
        self._edit_shared_item(item_id, "raw", self)

    def _publish_selected(self):
        from PyQt5.QtWidgets import QMessageBox
        item_id = self.selected_id()
        if item_id is None:
            QMessageBox.information(self, tr("warning"), tr("raw_select_first"))
            return
        row = self._get_current_row_dict()
        if not row:
            return
        item_data = {
            "price":         float(row.get("price", 0.0)),
            "total_qty":     row.get("total_qty"),
            "category_name": row.get("category_name") or None,
        }
        self._publish_item(row, "raw", item_data, self)

    # ══════════════════════════════════════════════════════
    # تعديل / حذف
    # ══════════════════════════════════════════════════════

    def _on_edit_item(self, item_id):
        from PyQt5.QtWidgets import QMessageBox
        if is_shared_id(item_id):
            QMessageBox.information(
                self, tr("shared_item_title"),
                tr("raw_shared_edit_notice")
            )
            return
        if self._input_panel:
            self._input_panel.load_for_edit(int(item_id))

    def _on_delete_item(self, item_id, item_name: str):
        from PyQt5.QtWidgets import QMessageBox
        from db.shared.items_repo import delete_item

        if is_shared_id(item_id):
            QMessageBox.warning(
                self, tr("shared_item_title"),
                tr("raw_shared_delete_blocked")
            )
            return
        item_id_int = int(item_id)
        if (self._input_panel and
                getattr(self._input_panel, "is_editing", False) and
                getattr(self._input_panel, "_editing_id", None) == item_id_int):
            self._input_panel._reset()
        if confirm_delete(self, item_name):
            try:
                delete_item(self.conn, item_id_int)
            except Exception as e:
                QMessageBox.warning(self, tr("error"), str(e))
                return
            emit_company_data_changed()

    # ══════════════════════════════════════════════════════
    # مساعد
    # ══════════════════════════════════════════════════════

    def _get_current_row_dict(self) -> dict | None:
        item_id = self.selected_id()
        if item_id is None:
            return None
        for row in self._rows:
            if str(row.get("id")) == str(item_id):
                return row
        return None