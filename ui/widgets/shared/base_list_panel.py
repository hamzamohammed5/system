"""
ui/widgets/shared/base_list_panel.py
=====================================
BaseListPanel — قاعدة مشتركة لكل لوحات القوائم.

توفر:
  - toolbar فوق الجدول (بحث + أزرار)
  - جدول بعرض ثابت من المحتوى
  - status bar تحت الجدول
  - signal: item_selected(int id)

الاستخدام:
    class MyListPanel(BaseListPanel):
        COLUMNS    = ["الكود", "الاسم", "الحالة"]
        STRETCH_COL = 1

        def _load_rows(self):
            return fetch_all_items(self.conn)

        def _fill_row(self, table, r, row):
            table.setItem(r, 0, make_table_item(row["code"]))
            ...

        def _match_filter(self, row, q, **kwargs) -> bool:
            return q in row["name"].lower()
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame,
    QLineEdit, QPushButton, QHBoxLayout,
    QHeaderView, QAbstractItemView,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

from ui.widgets.shared.table_utils import (
    make_list_table, auto_fit_columns,
    fit_table_to_content, ROW_HEIGHT_LARGE,
)
from ui.app_settings import _C


class BaseListPanel(QWidget):
    """
    قاعدة مشتركة للوحات القوائم.
    Override:
      COLUMNS, STRETCH_COL, _load_rows(), _fill_row(), _match_filter()
    """

    item_selected = pyqtSignal(int)   # يُطلق بالـ id لما يُختار صف

    # ── قابل للـ override ──
    COLUMNS     : list = []
    STRETCH_COL : int  = -1
    COL_WIDTHS  : dict = None
    MIN_W       : int  = 280
    MAX_W       : int  = 560

    def __init__(self, conn=None, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._all_rows = []
        self._timer    = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._apply_filter)
        self._build()
        self.refresh()

    # ══════════════════════════════════════════════════════
    # override هنا في الـ subclass
    # ══════════════════════════════════════════════════════

    def _load_rows(self) -> list:
        """يرجع كل الصفوف من DB."""
        return []

    def _fill_row(self, table, row_idx: int, row_data):
        """يملأ صف واحد في الجدول."""
        pass

    def _match_filter(self, row_data, q: str) -> bool:
        """يرجع True لو الصف يطابق البحث."""
        return True

    def _get_row_id(self, row_data) -> int:
        """يرجع الـ id من بيانات الصف."""
        if isinstance(row_data, dict):
            return row_data.get("id", 0)
        return 0

    # ══════════════════════════════════════════════════════
    # بناء الواجهة الأساسية
    # ══════════════════════════════════════════════════════

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setStyleSheet(f"background:{_C['bg_input']};")

        # ── toolbar ──
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

        # ── جدول ──
        self.table = make_list_table(
            self.COLUMNS,
            stretch_col=self.STRETCH_COL,
            col_widths=self.COL_WIDTHS,
        )
        self.table.itemSelectionChanged.connect(self._on_select)
        root.addWidget(self.table, stretch=1)

        # ── status bar ──
        self._status_bar = QLabel("")
        self._status_bar.setAlignment(Qt.AlignCenter)
        self._status_bar.setStyleSheet(f"""
            background: {_C['bg_surface_2']};
            color: {_C['text_muted']};
            padding: 5px 10px;
            font-size: 10px;
            font-weight: 600;
            border-top: 1px solid {_C['border']};
        """)
        root.addWidget(self._status_bar)

    def _build_toolbar(self, lay: QVBoxLayout):
        """يبني الـ toolbar الافتراضي — ممكن override."""
        row = QHBoxLayout()

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍  بحث...")
        self.inp_search.setMinimumHeight(34)
        self.inp_search.setClearButtonEnabled(True)
        self.inp_search.setStyleSheet(f"""
            QLineEdit {{
                background: {_C['bg_input']};
                border: 1.5px solid {_C['border_med']};
                border-radius: 6px;
                padding: 0 10px;
                font-size: 12px;
            }}
            QLineEdit:focus {{ border-color: {_C['accent']}; }}
        """)
        self.inp_search.textChanged.connect(lambda: self._timer.start())
        row.addWidget(self.inp_search, stretch=1)

        lay.addLayout(row)

    # ══════════════════════════════════════════════════════
    # تحميل وفلترة
    # ══════════════════════════════════════════════════════

    def refresh(self):
        self._all_rows = self._load_rows()
        self._apply_filter()

    def _apply_filter(self):
        q = self.inp_search.text().strip().lower() if hasattr(self, 'inp_search') else ""
        filtered = [r for r in self._all_rows if self._match_filter(r, q)]
        self._fill_table(filtered)

        cnt   = len(filtered)
        total = len(self._all_rows)
        self._status_bar.setText(
            f"{cnt}" if cnt == total else f"{cnt} / {total}"
        )

        if filtered:
            auto_fit_columns(
                self.table,
                fixed_cols=[i for i in range(self.table.columnCount())
                             if i != self.STRETCH_COL],
                stretch_col=self.STRETCH_COL,
                min_width=40, max_width=300,
            )

    def _fill_table(self, rows: list):
        self.table.setRowCount(0)
        for row_data in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, ROW_HEIGHT_LARGE)
            self._fill_row(self.table, r, row_data)

    # ══════════════════════════════════════════════════════
    # selection
    # ══════════════════════════════════════════════════════

    def _on_select(self):
        row = self.table.currentRow()
        if row < 0:
            return
        # نحاول نجيب الـ id من العمود الأول
        item = self.table.item(row, 0)
        if item:
            data = item.data(Qt.UserRole)
            if data is not None:
                self.item_selected.emit(int(data))

    def select_item(self, item_id: int):
        """يحدد صف بالـ id."""
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item and item.data(Qt.UserRole) == item_id:
                self.table.selectRow(r)
                return