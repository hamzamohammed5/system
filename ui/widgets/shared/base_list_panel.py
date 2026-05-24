"""
ui/widgets/shared/base_list_panel.py
=====================================
BaseListPanel — قاعدة مشتركة لكل لوحات القوائم.

[تحديث v3]:
  - يستخدم SearchLineEdit من input_widgets بدل inp_search المباشر
  - يستخدم BusConnectedMixin للاشتراك في bus
  - لا تكرار في setup الجدول
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

from ui.widgets.shared.table_utils import (
    make_splitter_table_guarded, fit_splitter_table,
    ROW_HEIGHT_LARGE,
)
from ui.widgets.shared.panels import (
    EmptyState, ListHeader, ListStatusBar,
)
from ui.app_settings import _C

_MIN_W = 260


class BaseListPanel(QWidget):
    item_selected = pyqtSignal(int)

    COLUMNS     : list = []
    STRETCH_COL : int  = -1
    COL_WIDTHS  : dict = None
    MIN_W       : int  = _MIN_W
    EMPTY_ICON  : str  = "📋"
    EMPTY_TITLE : str  = "لا توجد بيانات"
    LIST_TITLE  : str  = ""
    ADD_TEXT    : str  = ""
    SEARCH_PLACEHOLDER : str = "🔍  بحث..."

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
        self.refresh()

    # ── override في الـ subclass ──────────────────────────

    def _load_rows(self) -> list:            return []
    def _fill_row(self, table, r, row):      pass
    def _match_filter(self, row, q) -> bool: return True
    def _get_row_id(self, row) -> int:
        return row.get("id", 0) if hasattr(row, 'keys') else 0

    def _on_add_clicked(self):
        pass

    # ── بناء الواجهة ──────────────────────────────────────

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setStyleSheet(f"background:{_C['bg_input']};")

        # ── Header ──
        self._header = ListHeader(
            title=self.LIST_TITLE,
            add_text=self.ADD_TEXT,
            show_search=True,
            search_placeholder=self.SEARCH_PLACEHOLDER,
        )
        self._header.search_changed.connect(lambda _: self._timer.start())
        if self.ADD_TEXT:
            self._header.add_clicked.connect(self._on_add_clicked)

        self._build_extra_toolbar(self._header)
        root.addWidget(self._header)

        # متاح للـ subclass
        self.inp_search = self._header.search_bar.inp

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

    def _build_extra_toolbar(self, header: ListHeader):
        """Override لإضافة أزرار إضافية في الهيدر."""
        pass

    # ── تحميل وفلترة ────────────────────────────────────

    def refresh(self):
        self._all_rows = self._load_rows()
        self._apply_filter()

    def _apply_filter(self):
        q = self._header.search_text()
        filtered = [r for r in self._all_rows if self._match_filter(r, q)]
        self._fill_table(filtered)

        self._status_bar.set_count(len(filtered), len(self._all_rows))

        has_data = bool(filtered)
        self.table.setVisible(has_data)
        self._splitter.setVisible(has_data)
        self._empty_state.setVisible(not has_data and bool(self._all_rows))
        self._auto_resize()

    def _fill_table(self, rows: list):
        self.table.setRowCount(0)
        for row_data in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, ROW_HEIGHT_LARGE)
            self._fill_row(self.table, r, row_data)

        if rows:
            fit_splitter_table(self._splitter, self.table, extra_pad=24)
            self._table_guard.refresh()

    def _auto_resize(self):
        from ui.widgets.shared.table_utils import auto_fit_columns
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
                return