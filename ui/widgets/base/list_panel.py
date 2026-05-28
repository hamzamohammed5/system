"""
ui/widgets/base/list_panel.py
==========================
BaseListPanel — قاعدة مشتركة لكل لوحات القوائم.

التحسينات:
  - [تحسين 24 محفوظ] current_id property للوصول المباشر للـ ID المحدد.
  - [تحسين 45] دعم Custom Sort بالضغط على header الجدول.
    SORTABLE = True يُفعّل الـ sort.
    COL_KEYS  قائمة بمفاتيح dict للأعمدة بالترتيب (لازم عددها = COLUMNS).
    _sort_key(col, row) override للـ sort المخصص.
    الضغط على نفس العمود مرتين يعكس الاتجاه (ASC/DESC).
    SORT_DEFAULT_COL / SORT_DEFAULT_ASC لضبط الترتيب الابتدائي.

مثال استخدام SORTABLE:
    class RawPanel(BaseListPanel):
        COLUMNS   = ["#", "الاسم", "التصنيف", "السعر"]
        COL_KEYS  = ["id", "name", "category_name", "price"]
        SORTABLE  = True
        SORT_DEFAULT_COL = 1   # ترتيب ابتدائي بالاسم
        SORT_DEFAULT_ASC = True

        def _sort_key(self, col, row):
            if col == 3:  # عمود السعر → رقمي
                return float(row.get("price") or 0)
            return super()._sort_key(col, row)
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

    [تحسين 45] Sort-related overrides:
        SORTABLE          → True لتفعيل Sort بالضغط على الهيدر
        COL_KEYS          → list[str] مفاتيح dict بترتيب الأعمدة
        SORT_DEFAULT_COL  → عمود الترتيب الابتدائي (-1 = بدون)
        SORT_DEFAULT_ASC  → True = تصاعدي، False = تنازلي
        _sort_key(col, row) → قيمة الـ sort المخصصة للعمود

    مثال تفعيل Sort:
        class MyPanel(BaseListPanel):
            COLUMNS          = ["الاسم", "التاريخ", "المبلغ"]
            COL_KEYS         = ["name", "date", "amount"]
            SORTABLE         = True
            SORT_DEFAULT_COL = 0

            def _sort_key(self, col, row):
                if col == 2:  # المبلغ → رقمي
                    return float(row.get("amount") or 0)
                return super()._sort_key(col, row)
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
    COL_KEYS          : list = []   # مفاتيح dict للأعمدة بالترتيب
    SORT_DEFAULT_COL  : int  = -1   # -1 = بدون ترتيب ابتدائي
    SORT_DEFAULT_ASC  : bool = True

    def __init__(self, conn=None, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._all_rows : list = []
        self._timer    = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._apply_filter)

        # [تحسين 45] Sort state — instance variables لعزل كل instance
        self._sort_col : int  = self.SORT_DEFAULT_COL
        self._sort_asc : bool = self.SORT_DEFAULT_ASC

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

    # ── [تحسين 45] Sort override ──────────────────────────

    def _sort_key(self, col: int, row: dict):
        """
        [تحسين 45] يرجع قيمة الـ sort للعمود المحدد.

        Override لتخصيص الـ sort:
            def _sort_key(self, col, row):
                if col == 2:  # عمود الرصيد
                    return float(row.get("balance", 0))
                return super()._sort_key(col, row)

        الـ fallback الافتراضي: يستخدم COL_KEYS لو موجود، وإلا يرجع "".
        """
        if self.COL_KEYS and col < len(self.COL_KEYS):
            val = row.get(self.COL_KEYS[col], "")
            # حاول تحويل للرقم للـ numeric sort الصحيح
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
            # أيقونة sort الابتدائية
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

    # ── [تحسين 45] Sort logic ─────────────────────────────

    def _on_header_clicked(self, col: int):
        """
        [تحسين 45] يُعالج الضغط على header العمود.
        نفس العمود → عكس الاتجاه. عمود مختلف → تصاعدي.
        """
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
        """
        [تحسين 45] يحدّث أيقونات الـ sort في الهيدر.
        يستخدم Qt built-in sort indicators بدل تعديل النص.
        """
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
        """
        [تحسين 45] يرتب الصفوف حسب العمود والاتجاه الحاليين.
        يُستدعى من _apply_filter قبل _fill_table.
        """
        if not self.SORTABLE or self._sort_col < 0:
            return rows
        try:
            return sorted(
                rows,
                key=lambda r: self._sort_key(self._sort_col, r),
                reverse=not self._sort_asc,
            )
        except Exception:
            # لو فشل الـ sort لأي سبب نرجع الصفوف بدون ترتيب
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

        # [تحسين 45] رتّب قبل العرض
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

    # [تحسين 24] property للوصول المباشر للـ ID المحدد
    @property
    def current_id(self) -> "int | None":
        """ID العنصر المحدد حالياً — None لو مفيش تحديد."""
        return self.selected_id()

    # ── header API ────────────────────────────────────────

    def add_header_action(self, text: str, callback=None, style: str = "normal"):
        return self._header.add_action(text, callback, style)

    def set_add_enabled(self, enabled: bool):
        self._header.set_add_enabled(enabled)

    # ── [تحسين 45] Sort API ───────────────────────────────

    def set_sort(self, col: int, ascending: bool = True):
        """
        [تحسين 45] يضبط الـ sort برمجياً بدون الضغط على الهيدر.

        مثال:
            self.list_panel.set_sort(col=2, ascending=False)
        """
        self._sort_col = col
        self._sort_asc = ascending
        if self.SORTABLE:
            self._update_sort_indicators()
        self._apply_filter()

    def clear_sort(self):
        """[تحسين 45] يلغي الـ sort ويرجع للترتيب الابتدائي."""
        self._sort_col = self.SORT_DEFAULT_COL
        self._sort_asc = self.SORT_DEFAULT_ASC
        if self.SORTABLE:
            self._update_sort_indicators()
        self._apply_filter()