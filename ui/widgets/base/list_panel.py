"""
widgets/base/list_panel.py
==========================
BaseListPanel — قاعدة مشتركة لكل لوحات القوائم.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt5.QtCore    import Qt, pyqtSignal, QTimer

from ui.app_settings import _C
from ..tables.builders  import (
    make_splitter_table_guarded,
    fit_splitter_table,
    ROW_HEIGHT_LARGE,
)
from ..tables.items     import auto_fit_columns
from ..panels.state     import EmptyState
from ..components.headers    import ListHeader, StatusBar
from ..panels.filter    import FilterToolbar
from ..mixins.bus       import BusConnectedMixin


class BaseListPanel(QWidget, BusConnectedMixin):
    """
    قاعدة مشتركة لكل لوحات القوائم.

    Override المطلوب:
        COLUMNS, STRETCH_COL, EMPTY_ICON, EMPTY_TITLE
        _load_rows()  → list[dict]
        _fill_row(table, row_index, row_data)

    Override الاختياري:
        _match_filter(row, query)      → bool
        _match_category(row, cat_id)   → bool
        _on_add_clicked()
        _on_data_changed()
        _build_extra_header_actions(header)
        COL_WIDTHS, LIST_TITLE, ADD_TEXT, SEARCH_PLACEHOLDER
        SHOW_CATEGORY, SHOW_DATE, FILTER_SCOPE
    """

    item_selected = pyqtSignal(int)

    # ── إعدادات الـ subclass ──────────────────────────────
    COLUMNS            : list = []
    STRETCH_COL        : int  = -1
    COL_WIDTHS         : dict = None
    MIN_W              : int  = 260
    EMPTY_ICON         : str  = "📋"
    EMPTY_TITLE        : str  = "لا توجد بيانات"
    LIST_TITLE         : str  = ""
    ADD_TEXT           : str  = ""
    SEARCH_PLACEHOLDER : str  = "🔍  بحث..."
    SHOW_CATEGORY      : bool = False
    SHOW_DATE          : bool = False
    FILTER_SCOPE       : str  = "all"
    CONNECT_BUS        : bool = True

    def __init__(self, conn=None, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._all_rows : list = []
        self._timer    = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._apply_filter)

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setMinimumWidth(self.MIN_W)
        self._build()

        if self.CONNECT_BUS:
            self._connect_bus(data=True)

        self.refresh()

    # ── override API ──────────────────────────────────────

    def _load_rows(self) -> list:
        return []

    def _fill_row(self, table, row_index: int, row_data: dict):
        pass

    def _match_filter(self, row: dict, query: str) -> bool:
        name = str(row.get("name", ""))
        return not query or query in name.lower()

    def _match_category(self, row: dict, cat_id) -> bool:
        return cat_id is None or row.get("category_id") == cat_id

    def _on_add_clicked(self):
        pass

    def _on_data_changed(self):
        self.refresh()

    def _build_extra_header_actions(self, header: ListHeader):
        pass

    # ── بناء الواجهة ──────────────────────────────────────

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setStyleSheet(f"background:{_C['bg_input']};")

        self._header = self._build_header()
        root.addWidget(self._header)

        self._filter_toolbar = self._build_filter()
        if self._filter_toolbar:
            root.addWidget(self._filter_toolbar)

        self._splitter, self.table, self._table_guard = make_splitter_table_guarded(
            columns    = self.COLUMNS,
            stretch_col= self.STRETCH_COL,
            col_widths = self.COL_WIDTHS,
            row_height = ROW_HEIGHT_LARGE,
        )
        self._splitter.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.itemSelectionChanged.connect(self._on_select)
        root.addWidget(self._splitter, stretch=1)

        self._empty_state = EmptyState(
            icon=self.EMPTY_ICON, title=self.EMPTY_TITLE,
            style="plain", color="#9ca3af", min_height=100,
        )
        self._empty_state.setStyleSheet(
            f"QFrame {{ background:{_C['bg_input']}; border:none; }}"
        )
        self._empty_state.setVisible(False)
        root.addWidget(self._empty_state)

        self._status_bar = StatusBar()
        root.addWidget(self._status_bar)

    def _build_header(self) -> ListHeader:
        use_search = not (self.SHOW_CATEGORY or self.SHOW_DATE)
        header = ListHeader(
            title              = self.LIST_TITLE,
            add_text           = self.ADD_TEXT,
            show_search        = use_search,
            search_placeholder = self.SEARCH_PLACEHOLDER,
        )
        if use_search:
            header.search_changed.connect(lambda _: self._timer.start())
        if self.ADD_TEXT:
            header.add_clicked.connect(self._on_add_clicked)
        self._build_extra_header_actions(header)
        return header

    def _build_filter(self) -> "FilterToolbar | None":
        if not (self.SHOW_CATEGORY or self.SHOW_DATE):
            return None
        toolbar = FilterToolbar(
            conn          = self.conn,
            scope         = self.FILTER_SCOPE,
            show_category = self.SHOW_CATEGORY,
            show_date     = self.SHOW_DATE,
            placeholder   = self.SEARCH_PLACEHOLDER,
        )
        toolbar.filter_changed.connect(lambda: self._timer.start())
        self.inp_search = toolbar.inp_search
        return toolbar

    # ── فلترة ─────────────────────────────────────────────

    def refresh(self):
        self._all_rows = self._load_rows()
        if self._filter_toolbar and self.conn:
            self._filter_toolbar.reload(self.conn)
        self._apply_filter()

    def _apply_filter(self):
        query  = self._get_search_query()
        cat_id = self._get_category_filter()

        filtered = [
            row for row in self._all_rows
            if self._match_filter(row, query) and self._match_category(row, cat_id)
        ]
        self._fill_table(filtered)
        self._update_status(len(filtered))

    def _get_search_query(self) -> str:
        if self._filter_toolbar:
            return self._filter_toolbar.name_query
        if self._header.search_bar:
            return self._header.search_text()
        return ""

    def _get_category_filter(self):
        return self._filter_toolbar.category_id if self._filter_toolbar else None

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
        fixed = [i for i in range(self.table.columnCount()) if i != self.STRETCH_COL]
        auto_fit_columns(self.table, fixed_cols=fixed,
                         stretch_col=self.STRETCH_COL, min_width=40, max_width=300)

    # ── selection ─────────────────────────────────────────

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

    def selected_id(self) -> "int | None":
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if item:
            data = item.data(Qt.UserRole)
            return int(data) if data is not None else None
        return None

    # ── header API ────────────────────────────────────────

    def add_header_action(self, text: str, callback=None, style: str = "normal"):
        return self._header.add_action(text, callback, style)

    def set_add_enabled(self, enabled: bool):
        self._header.set_add_enabled(enabled)