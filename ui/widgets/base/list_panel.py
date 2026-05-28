"""
ui/widgets/base/list_panel.py
==========================
BaseListPanel — قاعدة مشتركة لكل لوحات القوائم.

التغييرات:
  - [i18n/themes] _connect_bus يدعم theme=True و lang=True.
  - [i18n/themes] _on_theme_changed() يُعيد تطبيق الـ styles على الـ widget.
  - [i18n/themes] _on_language_changed() يُحدّث النصوص الظاهرة (search placeholder,
    empty state title, pagination buttons).
  - [i18n/themes] EmptyState تحمل reference للـ title label لتحديثه لاحقاً.
    ملاحظة: يستخدم EMPTY_TITLE كـ key للترجمة لو أمكن، وإلا يعرض النص مباشرة.
  - [تحسين 24 محفوظ] current_id property.
  - [تحسين 45 محفوظ] Custom Sort.
  - [تحسين 51 محفوظ] Pagination.
  - [تحسين 17 محفوظ] select_item binary search.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QFrame,
)
from PyQt5.QtCore    import Qt, pyqtSignal, QTimer

from ui.app_settings import _C, fs, get_font_size
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


def _tr_safe(key: str) -> str:
    """ترجمة آمنة — لو فشلت ترجع المفتاح كما هو."""
    try:
        from ui.widgets.core.i18n import tr
        return tr(key)
    except Exception:
        return key


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

    [تحسين 45] Sort-related overrides:
        SORTABLE, COL_KEYS, SORT_DEFAULT_COL, SORT_DEFAULT_ASC
        _sort_key(col, row)

    [تحسين 51] Pagination:
        PAGINATE  = True  لتفعيل التقسيم لصفحات
        PAGE_SIZE = عدد الصفوف في كل صفحة (افتراضي 200)
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

    # ── [تحسين 45] Sort settings ─────────────────────────
    SORTABLE          : bool = False
    COL_KEYS          : list = []
    SORT_DEFAULT_COL  : int  = -1
    SORT_DEFAULT_ASC  : bool = True

    # ── [تحسين 51] Pagination settings ───────────────────
    PAGINATE  : bool = False
    PAGE_SIZE : int  = 200

    def __init__(self, conn=None, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._all_rows : list = []
        self._timer    = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._apply_filter)

        # [تحسين 45] Sort state
        self._sort_col : int  = self.SORT_DEFAULT_COL
        self._sort_asc : bool = self.SORT_DEFAULT_ASC

        # [تحسين 51] Pagination state
        self._page_rows    : list = []
        self._shown_count  : int  = 0

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setMinimumWidth(self.MIN_W)
        self._build()

        if self.CONNECT_BUS:
            # [i18n/themes] اشترك في theme وlang أيضاً
            self._connect_bus(data=True, theme=True, lang=True)

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

        # [تحسين 45] ربط header click للـ sort
        if self.SORTABLE:
            hh = self.table.horizontalHeader()
            hh.setSectionsClickable(True)
            hh.sectionClicked.connect(self._on_header_clicked)
            if self.SORT_DEFAULT_COL >= 0:
                self._update_sort_indicators()

        root.addWidget(self._splitter, stretch=1)

        self._empty_state = EmptyState(
            icon=self.EMPTY_ICON, title=self.EMPTY_TITLE,
            style="plain", color=_C['text_muted'], min_height=100,
        )
        self._empty_state.setStyleSheet(
            f"QFrame {{ background:{_C['bg_input']}; border:none; }}"
        )
        self._empty_state.setVisible(False)
        root.addWidget(self._empty_state)

        # [تحسين 51] شريط الـ pagination
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

    # ── [i18n/themes] Theme & Language handlers ───────────

    def _on_theme_changed(self, theme_name: str):
        """
        [i18n/themes] يُعيد تطبيق الـ styles بعد تغيير الثيم.
        يُستدعى تلقائياً من BusConnectedMixin.
        """
        # إعادة تطبيق خلفية الـ widget الرئيسي
        self.setStyleSheet(f"background:{_C['bg_input']};")

        # إعادة تطبيق empty state background
        self._empty_state.setStyleSheet(
            f"QFrame {{ background:{_C['bg_input']}; border:none; }}"
        )

        # إعادة بناء pagination bar styles
        self._rebuild_pagination_styles()

        # إعادة بناء status bar style
        self._rebuild_status_style()

    def _on_language_changed(self, lang_code: str):
        """
        [i18n/themes] يُحدّث النصوص الظاهرة بعد تغيير اللغة.
        """
        # تحديث placeholder البحث
        if self._header.search_bar:
            placeholder = _tr_safe(self.SEARCH_PLACEHOLDER)
            self._header.search_bar.set_placeholder(placeholder)

        # تحديث نص الـ empty state
        self._update_empty_state_title()

        # تحديث أزرار الـ pagination
        self._update_pagination_texts()

    def _rebuild_pagination_styles(self):
        """يُعيد بناء styles شريط الـ pagination بعد تغيير الثيم."""
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
                border: 1px solid {_C['accent_mid']}; border-radius: 5px;
                padding: 0 14px; font-size: {fs(base, -1)}pt; font-weight: bold;
            }}
            QPushButton:hover {{
                background: {_C['accent_mid']}; border-color: {_C['accent']};
            }}
        """)
        self._btn_show_all.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {_C['text_muted']};
                border: 1px solid {_C['border_med']}; border-radius: 5px;
                padding: 0 12px; font-size: {fs(base, -1)}pt;
            }}
            QPushButton:hover {{
                color: {_C['text_primary']}; border-color: {_C['border_strong']};
            }}
        """)

    def _rebuild_status_style(self):
        """يُعيد بناء style الـ status bar."""
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
        """
        يُحدّث نص الـ empty state بعد تغيير اللغة.
        يستخدم set_title() من EmptyState مباشرة (أسرع وأوضح من findChildren).
        """
        translated = _tr_safe(self.EMPTY_TITLE)
        try:
            self._empty_state.set_title(translated)
        except Exception:
            pass

    def _update_pagination_texts(self):
        """يُحدّث نصوص أزرار الـ pagination بعد تغيير اللغة."""
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
        bar.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_surface_2']};
                border-top: 1px solid {_C['border']};
            }}
        """)
        bar.setFixedHeight(44)

        lay = QHBoxLayout(bar)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(10)

        base = get_font_size()

        self._lbl_page_info = QLabel("")
        self._lbl_page_info.setStyleSheet(
            f"color: {_C['text_muted']}; font-size: {fs(base, -1)}pt;"
            "background: transparent; border: none;"
        )
        lay.addWidget(self._lbl_page_info, stretch=1)

        self._btn_load_more = QPushButton()
        self._btn_load_more.setCursor(Qt.PointingHandCursor)
        self._btn_load_more.setFixedHeight(30)
        self._btn_load_more.setStyleSheet(f"""
            QPushButton {{
                background: {_C['accent_light']}; color: {_C['accent_text']};
                border: 1px solid {_C['accent_mid']}; border-radius: 5px;
                padding: 0 14px; font-size: {fs(base, -1)}pt; font-weight: bold;
            }}
            QPushButton:hover {{
                background: {_C['accent_mid']}; border-color: {_C['accent']};
            }}
        """)
        self._btn_load_more.clicked.connect(self._on_load_more)
        lay.addWidget(self._btn_load_more)

        self._btn_show_all = QPushButton("عرض الكل")
        self._btn_show_all.setCursor(Qt.PointingHandCursor)
        self._btn_show_all.setFixedHeight(30)
        self._btn_show_all.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {_C['text_muted']};
                border: 1px solid {_C['border_med']}; border-radius: 5px;
                padding: 0 12px; font-size: {fs(base, -1)}pt;
            }}
            QPushButton:hover {{
                color: {_C['text_primary']}; border-color: {_C['border_strong']};
            }}
        """)
        self._btn_show_all.clicked.connect(self._on_show_all)
        lay.addWidget(self._btn_show_all)

        bar.setVisible(False)
        return bar

    def _update_pagination_bar(self, total: int, shown: int):
        remaining = total - shown
        if not self.PAGINATE or remaining <= 0:
            self._pagination_bar.setVisible(False)
            return

        base = get_font_size()
        self._lbl_page_info.setText(f"يعرض {shown} من {total}")
        self._btn_load_more.setText(
            f"تحميل {min(remaining, self.PAGE_SIZE):,} إضافي  ▼"
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
        """
        [تحسين 51] يملأ الجدول مع دعم الـ pagination.
        """
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
        """
        [تحسين 17] البحث الذكي مع Pagination.
        """
        # الخطوة 1: ابحث في الصفوف الظاهرة
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item and item.data(Qt.UserRole) == item_id:
                self.table.selectRow(r)
                self.item_selected.emit(item_id)
                return

        # الخطوة 2: مش موجود في الصفوف الظاهرة — ابحث في _page_rows
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

    # [تحسين 24]
    @property
    def current_id(self) -> "int | None":
        return self.selected_id()

    # ── header API ────────────────────────────────────────

    def add_header_action(self, text: str, callback=None, style: str = "normal"):
        return self._header.add_action(text, callback, style)

    def set_add_enabled(self, enabled: bool):
        self._header.set_add_enabled(enabled)

    # ── [تحسين 45] Sort API ───────────────────────────────

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

    # ── [تحسين 51] Pagination API ─────────────────────────

    def reset_pagination(self):
        self._apply_filter()

    @property
    def total_rows(self) -> int:
        return len(self._page_rows)

    @property
    def shown_rows(self) -> int:
        return self._shown_count