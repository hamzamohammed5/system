"""
ui/widgets/shared/base_list_panel.py
=====================================
BaseListPanel — قاعدة مشتركة لكل لوحات القوائم.

[إصلاح v6]:
  - _get_search_query و _get_category_filter بدل من الاستدعاء المباشر
    بيستخدموا FilterToolbar.name_query و .category_id مباشرة
  - _build_header موحدة بدل branch مكرر
  - إزالة تكرار show_search=False / show_search=True logic المنتشرة
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

from .table_utils import (
    make_splitter_table_guarded,
    auto_fit_columns,
    fit_splitter_table,
    ROW_HEIGHT_LARGE,
)
from .panles_helper.empty_state    import EmptyState
from .panles_helper.list_header    import ListHeader, StatusBar as ListStatusBar
from .panles_helper.filter_toolbar import FilterToolbar
from .shared_ui_mixins import BusConnectedMixin

from ui.app_settings import _C

_MIN_W = 260


class BaseListPanel(QWidget, BusConnectedMixin):
    item_selected = pyqtSignal(int)

    # ── إعدادات الـ subclass ──────────────────────────────
    COLUMNS       : list = []
    STRETCH_COL   : int  = -1
    COL_WIDTHS    : dict = None
    MIN_W         : int  = _MIN_W
    EMPTY_ICON    : str  = "📋"
    EMPTY_TITLE   : str  = "لا توجد بيانات"
    LIST_TITLE    : str  = ""
    ADD_TEXT      : str  = ""
    SEARCH_PLACEHOLDER : str = "🔍  بحث..."

    # ── فلاتر ──────────────────────────────────────────────
    SHOW_CATEGORY : bool = False
    SHOW_DATE     : bool = False
    FILTER_SCOPE  : str  = "all"
    CONNECT_BUS   : bool = True

    def __init__(self, conn=None, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._all_rows = []
        self._timer    = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._apply_filter)

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setMinimumWidth(self.MIN_W)

        self._build()

        if self.CONNECT_BUS:
            self._connect_bus(data=True)

        self.refresh()

    # ── override في الـ subclass ──────────────────────────

    def _load_rows(self) -> list:
        return []

    def _fill_row(self, table, r: int, row: dict):
        pass

    def _match_filter(self, row: dict, q: str) -> bool:
        name = str(row.get("name", ""))
        return not q or q in name.lower()

    def _match_category(self, row: dict, cat_id) -> bool:
        if cat_id is None:
            return True
        return row.get("category_id") == cat_id

    def _get_row_id(self, row) -> int:
        return row.get("id", 0) if hasattr(row, 'keys') else 0

    def _on_add_clicked(self):
        pass

    def _on_data_changed(self):
        self.refresh()

    def _build_extra_header_actions(self, header: ListHeader):
        pass

    # alias للتوافق مع الكود القديم
    def _build_extra_toolbar(self, header: ListHeader):
        self._build_extra_header_actions(header)

    # ── بناء الواجهة ──────────────────────────────────────

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setStyleSheet(f"background:{_C['bg_input']};")

        # ── Header ──
        # دايماً نبني ListHeader للعنوان والأزرار
        self._header = ListHeader(
            title=self.LIST_TITLE,
            add_text=self.ADD_TEXT,
            show_search=not (self.SHOW_CATEGORY or self.SHOW_DATE),
            search_placeholder=self.SEARCH_PLACEHOLDER,
        )
        if not (self.SHOW_CATEGORY or self.SHOW_DATE):
            self._header.search_changed.connect(lambda _: self._timer.start())
        if self.ADD_TEXT:
            self._header.add_clicked.connect(self._on_add_clicked)
        self._build_extra_header_actions(self._header)
        root.addWidget(self._header)

        # ── FilterToolbar (لو محتاج تصنيف أو تاريخ) ──
        if self.SHOW_CATEGORY or self.SHOW_DATE:
            self._filter_toolbar = FilterToolbar(
                conn=self.conn,
                scope=self.FILTER_SCOPE,
                show_category=self.SHOW_CATEGORY,
                show_date=self.SHOW_DATE,
                placeholder=self.SEARCH_PLACEHOLDER,
            )
            self._filter_toolbar.filter_changed.connect(
                lambda: self._timer.start()
            )
            root.addWidget(self._filter_toolbar)
            # expose inp_search للتوافق مع الكود القديم
            self.inp_search = self._filter_toolbar.inp_search
        else:
            self._filter_toolbar = None
            self.inp_search = (
                self._header.search_bar.inp
                if self._header.search_bar else None
            )

        # ── الجدول ──
        self._splitter, self.table, self._table_guard = make_splitter_table_guarded(
            columns=self.COLUMNS,
            stretch_col=self.STRETCH_COL,
            col_widths=self.COL_WIDTHS,
            row_height=ROW_HEIGHT_LARGE,
        )
        self._splitter.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.itemSelectionChanged.connect(self._on_select)
        root.addWidget(self._splitter, stretch=1)

        # ── Empty State ──
        self._empty_state = EmptyState(
            icon=self.EMPTY_ICON, title=self.EMPTY_TITLE,
            style="plain", color="#9ca3af", min_height=100,
        )
        self._empty_state.setStyleSheet(
            f"QFrame {{ background:{_C['bg_input']}; border:none; }}"
        )
        self._empty_state.setVisible(False)
        root.addWidget(self._empty_state)

        # ── Status Bar ──
        self._status_bar = ListStatusBar()
        root.addWidget(self._status_bar)

    # ── تحميل وفلترة ────────────────────────────────────

    def refresh(self):
        self._all_rows = self._load_rows()
        if self._filter_toolbar and self.conn:
            self._filter_toolbar.reload(self.conn)
        self._apply_filter()

    def _apply_filter(self):
        q      = self._get_search_query()
        cat_id = self._get_category_filter()

        filtered = [
            row for row in self._all_rows
            if self._match_filter(row, q) and self._match_category(row, cat_id)
        ]

        self._fill_table(filtered)
        self._update_status(len(filtered))

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

    # ── selection ────────────────────────────────────────

    def _on_select(self):
        row = self.table.currentRow()
        if row < 0:
            return
        item = self.table.item(row, 0)
        if item:
            data = item.data(Qt.UserRole)
            if data is not None:
                self.item_selected.emit(int(data))

    def select_item(self, item_id: int):
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item and item.data(Qt.UserRole) == item_id:
                self.table.selectRow(r)
                self.item_selected.emit(item_id)
                return

    # ── API مساعد ────────────────────────────────────────

    def selected_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if item:
            data = item.data(Qt.UserRole)
            return int(data) if data is not None else None
        return None

    def add_header_action(self, text: str, callback=None,
                          style: str = "normal"):
        return self._header.add_action(text, callback, style)

    def set_add_enabled(self, enabled: bool):
        self._header.set_add_enabled(enabled)