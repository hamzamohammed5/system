"""
ui/widgets/base/list_panel.py — إصلاح refresh() double apply_filter

التغيير الوحيد عن النسخة الأصلية:
  [إصلاح 5] refresh() تُوقف الـ _timer قبل reload() لمنع تشغيل _apply_filter مرتين.

  المشكلة:
    _filter_toolbar.reload() يُعيد ملء categories combo → currentIndexChanged
    → filter_changed → _timer.start().
    ثم refresh() تستدعي _apply_filter() مباشرة.
    النتيجة: _apply_filter() تُنفَّذ مرتين (مرة فورية + مرة بعد 250ms من الـ timer).

  الحل:
    إيقاف الـ timer قبل reload() حتى لو بدأ من تغيير الـ combo،
    ثم _apply_filter() الفورية هي الوحيدة التي تُنفَّذ.

[i18n] EMPTY_ICON/EMPTY_TITLE/SEARCH_PLACEHOLDER الافتراضية، زر "عرض الكل"،
       ونصوص شريط الـ pagination — كلها استُبدلت بمفاتيح tr() من ar.py/en.py.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QFrame,
)
from PyQt5.QtCore    import Qt, pyqtSignal, QTimer

from ui.constants    import (
    BTN_MIN_HEIGHT, SPACING_SM,
    PAGINATION_BAR_H, PAGINATION_BTN_SPACING,
    PAGINATION_BTN_RADIUS, PAGINATION_BTN_PAD_H, PAGINATION_BTN_PAD_H_SM,
    LIST_PANEL_MIN_W_DEFAULT, FILTER_DEBOUNCE_MS, LIST_EMPTY_MIN_H,
    TABLE_EXTRA_PAD, COL_MIN_WIDTH, COL_MAX_WIDTH,
    SPACING_LG,
)
from ..tables.tables import (
    make_splitter_table_guarded,
    fit_splitter_table,
    ROW_HEIGHT_LARGE,
    auto_fit_columns,
)
from ..panels.state            import EmptyState
from ..components.headers_list import ListHeader, StatusBar
from ..panels.filter      import FilterToolbar
from ui.widgets.core.widget_mixin import WidgetMixin


from ui.widgets.core.i18n import tr


class BaseListPanel(QWidget, WidgetMixin):
    """
    قاعدة مشتركة لكل لوحات القوائم.

    Override المطلوب:
        COLUMNS, STRETCH_COL, EMPTY_ICON, EMPTY_TITLE
        _load_rows()  → list[dict]
        _fill_row(table, row_index, row_data)

    Override الاختياري:
        _match_filter(row, query)      → bool
        _match_category(row, cat_id)   → bool
        _match_date(row)               → bool
        _on_add_clicked()
        _refresh_data(company_id)
        _build_extra_header_actions(header)
        COL_WIDTHS, LIST_TITLE, ADD_TEXT, SEARCH_PLACEHOLDER
        SHOW_CATEGORY, SHOW_DATE, FILTER_SCOPE

    [تحسين 45] Sort-related overrides:
        SORTABLE, COL_KEYS, SORT_DEFAULT_COL, SORT_DEFAULT_ASC
        _sort_key(col, row)

    [تحسين 51] Pagination:
        PAGINATE  = True
        PAGE_SIZE = عدد الصفوف في كل صفحة (افتراضي 200)

    [E-02] Date filter:
        DATE_COL = اسم الـ key في dict البيانات اللي بيحتوي التاريخ
    """

    item_selected = pyqtSignal(int)

    COLUMNS            : list = []
    STRETCH_COL        : int  = -1
    COL_WIDTHS         : dict = None
    MIN_W              : int  = LIST_PANEL_MIN_W_DEFAULT
    EMPTY_ICON         : str  = "empty_icon_default"
    EMPTY_TITLE        : str  = "no_data"
    LIST_TITLE         : str  = ""
    ADD_TEXT           : str  = ""
    SEARCH_PLACEHOLDER : str  = "list_search_placeholder"
    SHOW_CATEGORY      : bool = False
    SHOW_DATE          : bool = False
    FILTER_SCOPE       : str  = "all"
    CONNECT_BUS        : bool = True
    DATE_COL           : str  = "date"

    SORTABLE          : bool = False
    COL_KEYS          : list = []
    SORT_DEFAULT_COL  : int  = -1
    SORT_DEFAULT_ASC  : bool = True

    PAGINATE  : bool = False
    PAGE_SIZE : int  = 200

    def __init__(self, conn=None, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._all_rows : list = []
        self._timer    = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(FILTER_DEBOUNCE_MS)
        self._timer.timeout.connect(self._apply_filter)

        self._sort_col : int  = self.SORT_DEFAULT_COL
        self._sort_asc : bool = self.SORT_DEFAULT_ASC

        self._page_rows    : list = []
        self._shown_count  : int  = 0

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setMinimumWidth(self.MIN_W)
        self._build()

        if self.CONNECT_BUS:
            self._init_widget_mixin(theme=True, font=True, lang=True, data=True)
        else:
            self._init_widget_mixin(theme=True, font=True, lang=True)
        self._refresh_style()

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

    def _match_date(self, row: dict) -> bool:
        if not self._filter_toolbar:
            return True
        date_str = str(row.get(self.DATE_COL, ""))
        return self._filter_toolbar.in_date_range(date_str)

    def _on_add_clicked(self):
        pass

    def _build_extra_header_actions(self, header: ListHeader):
        pass

    # ── [تحسين 45] Sort override ──────────────────────────

    def _sort_key(self, col: int, row: dict):
        if self.COL_KEYS and col < len(self.COL_KEYS):
            val = row.get(self.COL_KEYS[col], "")
            try:
                return float(val) if val not in (None, "") else 0.0
            except (TypeError, ValueError):
                return str(val).lower() if val is not None else ""
        return ""

    # ── بناء الواجهة ──────────────────────────────────────

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

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

        if self.SORTABLE:
            hh = self.table.horizontalHeader()
            hh.setSectionsClickable(True)
            hh.sectionClicked.connect(self._on_header_clicked)
            if self.SORT_DEFAULT_COL >= 0:
                self._update_sort_indicators()

        root.addWidget(self._splitter, stretch=1)

        self._empty_state = EmptyState(
            icon=tr(self.EMPTY_ICON), title=tr(self.EMPTY_TITLE),
            style="plain", color=None, min_height=LIST_EMPTY_MIN_H,
        )
        self._empty_state.setVisible(False)
        root.addWidget(self._empty_state)

        self._pagination_bar = self._build_pagination_bar()
        root.addWidget(self._pagination_bar)

        self._status_bar = StatusBar()
        root.addWidget(self._status_bar)

    def _build_header(self) -> ListHeader:
        use_search = not (self.SHOW_CATEGORY or self.SHOW_DATE)
        header = ListHeader(
            title              = self.LIST_TITLE,
            add_text           = self.ADD_TEXT,
            show_search        = use_search,
            search_placeholder = tr(self.SEARCH_PLACEHOLDER),
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

    # ── [i18n/themes] Theme & Language handlers ───────────

    def _refresh_style(self, *_):
        from ui.theme import _C
        self.setStyleSheet(f"background:{_C['bg_input']};")
        self._empty_state.setStyleSheet(
            f"QFrame {{ background:{_C['bg_input']}; border:none; }}"
        )
        if hasattr(self._empty_state, "set_color"):
            self._empty_state.set_color(_C['text_muted'])
        self._rebuild_pagination_styles()
        self._rebuild_status_style()

    def _refresh_lang(self, *_):
        if self._header.search_bar:
            placeholder = tr(self.SEARCH_PLACEHOLDER)
            self._header.search_bar.set_placeholder(placeholder)
        self._update_empty_state_title()
        self._update_pagination_texts()

    def _refresh_data(self, company_id=None):
        self.refresh()

    def _rebuild_pagination_styles(self):
        from ui.theme import _C
        from ui.font import fs, get_font_size
        base = get_font_size()
        self._pagination_bar.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_surface_2']};
                border-top: 1px solid {_C['border']};
            }}
        """)
        self._lbl_page_info.setStyleSheet(
            f"color: {_C['text_muted']}; font-size: {fs(base, -1)}pt;"
            "background: transparent; border: none;"
        )
        self._btn_load_more.setStyleSheet(f"""
            QPushButton {{
                background: {_C['accent_light']}; color: {_C['accent_text']};
                border: 1px solid {_C['accent_mid']}; border-radius: {PAGINATION_BTN_RADIUS}px;
                padding: 0 {PAGINATION_BTN_PAD_H}px; font-size: {fs(base, -1)}pt; font-weight: bold;
            }}
            QPushButton:hover {{
                background: {_C['accent_mid']}; border-color: {_C['accent']};
            }}
        """)
        self._btn_show_all.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {_C['text_muted']};
                border: 1px solid {_C['border_med']}; border-radius: {PAGINATION_BTN_RADIUS}px;
                padding: 0 {PAGINATION_BTN_PAD_H_SM}px; font-size: {fs(base, -1)}pt;
            }}
            QPushButton:hover {{
                color: {_C['text_primary']}; border-color: {_C['border_strong']};
            }}
        """)

    def _rebuild_status_style(self):
        from ui.theme import _C
        from ui.font import fs, get_font_size
        base = get_font_size()
        self._status_bar.setStyleSheet(f"""
            background:{_C['bg_surface_2']};
            color:{_C['text_muted']};
            padding:0 10px;
            font-size:{fs(base,-1)}pt;
            font-weight:600;
            border-top:1px solid {_C['border']};
        """)

    def _update_empty_state_title(self):
        translated = tr(self.EMPTY_TITLE)
        try:
            self._empty_state.set_title(translated)
        except Exception:
            pass

    def _update_pagination_texts(self):
        try:
            if self._pagination_bar.isVisible():
                shown = self._shown_count
                total = len(self._page_rows)
                self._update_pagination_bar(total, shown)
        except Exception:
            pass

    # ── [تحسين 51] Pagination bar ─────────────────────────

    def _build_pagination_bar(self) -> QWidget:
        bar = QFrame()
        bar.setFixedHeight(PAGINATION_BAR_H)

        lay = QHBoxLayout(bar)
        lay.setContentsMargins(SPACING_LG, SPACING_SM, SPACING_LG, SPACING_SM)
        lay.setSpacing(PAGINATION_BTN_SPACING)

        self._lbl_page_info = QLabel("")
        lay.addWidget(self._lbl_page_info, stretch=1)

        self._btn_load_more = QPushButton()
        self._btn_load_more.setCursor(Qt.PointingHandCursor)
        self._btn_load_more.setFixedHeight(BTN_MIN_HEIGHT)
        self._btn_load_more.clicked.connect(self._on_load_more)
        lay.addWidget(self._btn_load_more)

        self._btn_show_all = QPushButton(tr("show_all_records"))
        self._btn_show_all.setCursor(Qt.PointingHandCursor)
        self._btn_show_all.setFixedHeight(BTN_MIN_HEIGHT)
        self._btn_show_all.clicked.connect(self._on_show_all)
        lay.addWidget(self._btn_show_all)

        bar.setVisible(False)
        return bar

    def _update_pagination_bar(self, total: int, shown: int):
        remaining = total - shown
        if not self.PAGINATE or remaining <= 0:
            self._pagination_bar.setVisible(False)
            return

        self._lbl_page_info.setText(tr("showing_records").format(shown=shown, total=total))
        self._btn_load_more.setText(
            tr("load_more").format(count=min(remaining, self.PAGE_SIZE))
        )
        self._pagination_bar.setVisible(True)

    def _on_load_more(self):
        if not self._page_rows:
            return
        start = self._shown_count
        end   = min(start + self.PAGE_SIZE, len(self._page_rows))
        batch = self._page_rows[start:end]
        self.table.setUpdatesEnabled(False)
        for row_data in batch:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, ROW_HEIGHT_LARGE)
            self._fill_row(self.table, r, row_data)
        self.table.setUpdatesEnabled(True)
        self._shown_count = end
        self._update_pagination_bar(len(self._page_rows), self._shown_count)
        self._auto_resize()
        self._table_guard.refresh()

    def _on_show_all(self):
        if not self._page_rows:
            return
        remaining = self._page_rows[self._shown_count:]
        if not remaining:
            return
        self.table.setUpdatesEnabled(False)
        for row_data in remaining:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, ROW_HEIGHT_LARGE)
            self._fill_row(self.table, r, row_data)
        self.table.setUpdatesEnabled(True)
        self._shown_count = len(self._page_rows)
        self._pagination_bar.setVisible(False)
        self._auto_resize()
        self._table_guard.refresh()

    # ── [تحسين 45] Sort logic ─────────────────────────────

    def _on_header_clicked(self, col: int):
        if not self.SORTABLE:
            return
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True
        self._update_sort_indicators()
        self._apply_filter()

    def _update_sort_indicators(self):
        if not self.SORTABLE:
            return
        hh = self.table.horizontalHeader()
        if self._sort_col >= 0:
            hh.setSortIndicator(
                self._sort_col,
                Qt.AscendingOrder if self._sort_asc else Qt.DescendingOrder
            )
            hh.setSortIndicatorShown(True)
        else:
            hh.setSortIndicatorShown(False)

    def _sorted_rows(self, rows: list) -> list:
        if not self.SORTABLE or self._sort_col < 0:
            return rows
        try:
            return sorted(
                rows,
                key=lambda r: self._sort_key(self._sort_col, r),
                reverse=not self._sort_asc,
            )
        except Exception:
            return rows

    # ── فلترة ─────────────────────────────────────────────

    def refresh(self):
        """
        [إصلاح 5] إيقاف الـ _timer قبل reload() لمنع تشغيل _apply_filter مرتين.

        المشكلة القديمة:
          _filter_toolbar.reload() يُعيد ملء categories combo → currentIndexChanged
          → filter_changed → _timer.start().
          ثم refresh() تستدعي _apply_filter() مباشرة.
          النتيجة: _apply_filter() تُنفَّذ مرتين.

        الحل:
          إيقاف الـ timer قبل reload() حتى لو بدأ من تغيير الـ combo،
          ثم _apply_filter() الفورية في نهاية refresh() هي المرة الوحيدة.
        """
        self._all_rows = self._load_rows()
        if self._filter_toolbar and self.conn:
            self._timer.stop()                        # [إصلاح 5] منع double apply_filter
            self._filter_toolbar.reload(self.conn)
        self._apply_filter()

    def _apply_filter(self):
        query  = self._get_search_query()
        cat_id = self._get_category_filter()

        filtered = []
        for row in self._all_rows:
            if not self._match_filter(row, query):
                continue
            if not self._match_category(row, cat_id):
                continue
            if self.SHOW_DATE and not self._match_date(row):
                continue
            filtered.append(row)

        filtered = self._sorted_rows(filtered)
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
        self._page_rows   = rows
        self._shown_count = 0

        if self.PAGINATE and len(rows) > self.PAGE_SIZE:
            first_batch = rows[:self.PAGE_SIZE]
        else:
            first_batch = rows

        self.table.setUpdatesEnabled(False)
        for row_data in first_batch:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, ROW_HEIGHT_LARGE)
            self._fill_row(self.table, r, row_data)
        self.table.setUpdatesEnabled(True)

        self._shown_count = len(first_batch)

        has_data = bool(first_batch)
        self.table.setVisible(has_data)
        self._splitter.setVisible(has_data)
        self._empty_state.setVisible(not has_data)

        self._update_pagination_bar(len(rows), self._shown_count)

        if has_data:
            fit_splitter_table(self._splitter, self.table, extra_pad=TABLE_EXTRA_PAD)
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
                         stretch_col=self.STRETCH_COL, min_width=COL_MIN_WIDTH, max_width=COL_MAX_WIDTH)

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

        if not (self.PAGINATE and self._shown_count < len(self._page_rows)):
            return

        target_index = None
        for i, row_data in enumerate(self._page_rows):
            if row_data.get("id") == item_id:
                target_index = i
                break

        if target_index is None:
            return

        if target_index < self._shown_count:
            self._on_show_all()
        else:
            end_needed = target_index + 1
            batch = self._page_rows[self._shown_count:end_needed]
            if batch:
                self.table.setUpdatesEnabled(False)
                for row_data in batch:
                    r = self.table.rowCount()
                    self.table.insertRow(r)
                    self.table.setRowHeight(r, ROW_HEIGHT_LARGE)
                    self._fill_row(self.table, r, row_data)
                self.table.setUpdatesEnabled(True)
                self._shown_count = end_needed
                self._update_pagination_bar(len(self._page_rows), self._shown_count)
                self._auto_resize()
                self._table_guard.refresh()

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

    @property
    def current_id(self) -> "int | None":
        return self.selected_id()

    def add_header_action(self, text: str, callback=None, style: str = "normal"):
        return self._header.add_action(text, callback, style)

    def set_add_enabled(self, enabled: bool):
        self._header.set_add_enabled(enabled)

    def set_sort(self, col: int, ascending: bool = True):
        self._sort_col = col
        self._sort_asc = ascending
        if self.SORTABLE:
            self._update_sort_indicators()
        self._apply_filter()

    def clear_sort(self):
        self._sort_col = self.SORT_DEFAULT_COL
        self._sort_asc = self.SORT_DEFAULT_ASC
        if self.SORTABLE:
            self._update_sort_indicators()
        self._apply_filter()

    def reset_pagination(self):
        self._apply_filter()

    @property
    def total_rows(self) -> int:
        return len(self._page_rows)

    @property
    def shown_rows(self) -> int:
        return self._shown_count