"""
ui/widgets/shared/list_panel_filter.py
=======================================
_ListPanelFilterMixin — منطق الفلترة المشترك لـ BaseListPanel.

مستخرج من base_list_panel.py لتقليل الحجم.
يُستخدم فقط من base_list_panel.py.

يوفر:
  - _get_search_query()      : نص البحث من أي مصدر
  - _get_category_filter()   : category_id المختار
  - _apply_filter()          : تطبيق الفلتر على الصفوف
  - _update_status()         : تحديث شريط الحالة
  - _fill_table()            : ملء الجدول بالصفوف المفلترة
  - _auto_resize()           : ضبط عرض الأعمدة تلقائياً
"""

from ui.widgets.shared.table_utils import (
    fit_splitter_table,
    auto_fit_columns,
    ROW_HEIGHT_LARGE,
)


class _ListPanelFilterMixin:
    """
    Mixin يضيف منطق الفلترة والعرض لـ BaseListPanel.

    يفترض وجود:
      - self._all_rows       : list — كل الصفوف المحملة
      - self._filter_toolbar : FilterToolbar | None
      - self._header         : ListHeader
      - self.table           : QTableWidget
      - self._splitter       : QSplitter
      - self._table_guard    : _SplitterScrollGuard
      - self._empty_state    : EmptyState
      - self._status_bar     : StatusBar
      - self.STRETCH_COL     : int
      - self._fill_row()     : يملأ صف واحد
      - _match_filter()      : تحقق من تطابق الصف مع البحث
      - _match_category()    : تحقق من تطابق التصنيف
    """

    def _get_search_query(self) -> str:
        """يرجع نص البحث من أي مصدر متاح."""
        if self._filter_toolbar:
            return self._filter_toolbar.name_query
        if self._header.search_bar:
            return self._header.search_text()
        return ""

    def _get_category_filter(self):
        """يرجع category_id المختار أو None."""
        if self._filter_toolbar:
            return self._filter_toolbar.category_id
        return None

    def _apply_filter(self):
        q      = self._get_search_query()
        cat_id = self._get_category_filter()

        filtered = [
            row for row in self._all_rows
            if self._match_filter(row, q) and self._match_category(row, cat_id)
        ]

        self._fill_table(filtered)
        self._update_status(len(filtered))

    def _fill_table(self, rows: list):
        self.table.setRowCount(0)
        for row_data in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, ROW_HEIGHT_LARGE)
            self._fill_row(self.table, r, row_data)

        has_data = bool(rows)
        self.table.setVisible(has_data)
        self._splitter.setVisible(has_data)
        self._empty_state.setVisible(not has_data)

        if has_data:
            fit_splitter_table(self._splitter, self.table, extra_pad=24)
            self._table_guard.refresh()
            self._auto_resize()

    def _update_status(self, shown: int):
        total = len(self._all_rows)
        self._status_bar.set_count(shown, total)
        if self._filter_toolbar:
            self._filter_toolbar.set_count(shown, total)

    def _auto_resize(self):
        all_cols = [i for i in range(self.table.columnCount())
                    if i != self.STRETCH_COL]
        auto_fit_columns(
            self.table,
            fixed_cols=all_cols,
            stretch_col=self.STRETCH_COL,
            min_width=40,
            max_width=300,
        )