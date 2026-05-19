"""
ui/widgets/shared/base_list_panel.py
=====================================
BaseListPanel — قاعدة مشتركة لكل لوحات القوائم.

القواعد:
  - عرض ثابت على المحتوى (MIN_W → MAX_W)
  - الجداول والأزرار حجمهم ثابت
  - بدون horizontal scroll في القائمة نفسها
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame,
    QLineEdit, QHBoxLayout, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

from ui.widgets.shared.table_utils import (
    make_list_table, auto_fit_columns,
    ROW_HEIGHT_LARGE,
)
from ui.widgets.shared.panels import EmptyState
from ui.app_settings import _C

_MIN_W = 260
_MAX_W = 580


class BaseListPanel(QWidget):
    item_selected = pyqtSignal(int)

    COLUMNS     : list = []
    STRETCH_COL : int  = -1
    COL_WIDTHS  : dict = None
    MIN_W       : int  = _MIN_W
    MAX_W       : int  = _MAX_W
    EMPTY_ICON  : str  = "📋"
    EMPTY_TITLE : str  = "لا توجد بيانات"

    def __init__(self, conn=None, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._all_rows = []
        self._timer    = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._apply_filter)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self._build()
        self.refresh()

    # ── override في الـ subclass ──────────────────────────

    def _load_rows(self) -> list:           return []
    def _fill_row(self, table, r, row):     pass
    def _match_filter(self, row, q) -> bool: return True
    def _get_row_id(self, row) -> int:
        return row.get("id", 0) if hasattr(row, 'keys') else 0

    # ── بناء الواجهة ──────────────────────────────────────

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setStyleSheet(f"background:{_C['bg_input']};")

        self._toolbar = QFrame()
        self._toolbar.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_input']};
                border-bottom: 1px solid {_C['border']};
            }}
        """)
        self._toolbar_lay = QVBoxLayout(self._toolbar)
        self._toolbar_lay.setContentsMargins(10, 10, 10, 10)
        self._toolbar_lay.setSpacing(6)
        self._build_toolbar(self._toolbar_lay)
        root.addWidget(self._toolbar)

        self.table = make_list_table(
            self.COLUMNS,
            stretch_col=self.STRETCH_COL,
            col_widths=self.COL_WIDTHS,
        )
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.itemSelectionChanged.connect(self._on_select)
        root.addWidget(self.table, stretch=1)

        self._empty_state = EmptyState(
            icon=self.EMPTY_ICON, title=self.EMPTY_TITLE,
            style="plain", color="#9ca3af", min_height=100,
        )
        self._empty_state.setStyleSheet(
            f"QFrame {{ background:{_C['bg_input']}; border:none; }}"
        )
        self._empty_state.setVisible(False)
        root.addWidget(self._empty_state)

        self._status_bar = QLabel("")
        self._status_bar.setAlignment(Qt.AlignCenter)
        self._status_bar.setStyleSheet(f"""
            background: {_C['bg_surface_2']}; color: {_C['text_muted']};
            padding: 5px 10px; font-size: 10px; font-weight: 600;
            border-top: 1px solid {_C['border']};
        """)
        root.addWidget(self._status_bar)

    def _build_toolbar(self, lay: QVBoxLayout):
        row = QHBoxLayout()
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍  بحث...")
        self.inp_search.setMinimumHeight(34)
        self.inp_search.setClearButtonEnabled(True)
        self.inp_search.setStyleSheet(f"""
            QLineEdit {{
                background: {_C['bg_input']}; border: 1.5px solid {_C['border_med']};
                border-radius: 6px; padding: 0 10px; font-size: 12px;
            }}
            QLineEdit:focus {{ border-color: {_C['accent']}; }}
        """)
        self.inp_search.textChanged.connect(lambda: self._timer.start())
        row.addWidget(self.inp_search, stretch=1)
        lay.addLayout(row)

    # ── تحميل وفلترة ────────────────────────────────────

    def refresh(self):
        self._all_rows = self._load_rows()
        self._apply_filter()

    def _apply_filter(self):
        q = getattr(self, 'inp_search', None)
        q = q.text().strip().lower() if q else ""
        filtered = [r for r in self._all_rows if self._match_filter(r, q)]
        self._fill_table(filtered)

        cnt   = len(filtered)
        total = len(self._all_rows)
        self._status_bar.setText(f"{cnt}" if cnt == total else f"{cnt} / {total}")

        has_data = bool(filtered)
        self.table.setVisible(has_data)
        self._empty_state.setVisible(not has_data and bool(self._all_rows))
        self._auto_resize()

    def _fill_table(self, rows: list):
        self.table.setRowCount(0)
        for row_data in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, ROW_HEIGHT_LARGE)
            self._fill_row(self.table, r, row_data)

    def _auto_resize(self):
        all_cols = [i for i in range(self.table.columnCount())
                    if i != self.STRETCH_COL]
        auto_fit_columns(self.table, fixed_cols=all_cols,
                         stretch_col=self.STRETCH_COL,
                         min_width=40, max_width=300)
        self.setMinimumWidth(self.MIN_W)
        self.setMaximumWidth(self.MAX_W)

    # ── selection ────────────────────────────────────────

    def _on_select(self):
        row  = self.table.currentRow()
        if row < 0: return
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