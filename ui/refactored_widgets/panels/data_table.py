"""
ui/refactored_widgets/panels/data_table.py
==========================================
DataTableWidget — جدول بيانات موحد يجمع:
  - ListHeader  (بحث + عنوان + أزرار)
  - QTableWidget (الجدول)
  - EmptyState  (حالة فارغة)
  - StatusBar   (عداد الصفوف)

يحل محل النمط المكرر في ملفات كثيرة.

الاستخدام:
    tbl = DataTableWidget(
        columns=["ID", "الاسم", "التاريخ"],
        stretch_col=1,
        title="المنتجات",
        add_text="➕ إضافة",
    )
    tbl.add_clicked.connect(self._on_add)
    tbl.search_changed.connect(self._on_search)
    tbl.row_selected.connect(self._on_select)
    layout.addWidget(tbl)

    # ملء الجدول:
    tbl.begin_fill()
    for row_data in data:
        r = tbl.insert_row()
        tbl.table.setItem(r, 0, QTableWidgetItem(str(row_data["id"])))
        tbl.table.setItem(r, 1, QTableWidgetItem(row_data["name"]))
    tbl.end_fill()
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt5.QtCore    import Qt, pyqtSignal

from ui.app_settings import _C
from ..tables.builders import make_list_table, ROW_HEIGHT_LARGE
from ..tables.items    import auto_fit_columns
from ..panels.header   import ListHeader, StatusBar
from ..panels.state    import EmptyState


class DataTableWidget(QWidget):
    """
    جدول بيانات موحد يحتوي على هيدر + جدول + حالة فارغة + عداد.

    Signals:
        add_clicked         → زر الإضافة ضُغط
        search_changed(str) → تغير نص البحث
        row_selected(int)   → صف مُحدد (يطلق ID من UserRole في العمود 0)
    """

    add_clicked    = pyqtSignal()
    search_changed = pyqtSignal(str)
    row_selected   = pyqtSignal(int)

    EMPTY_ICON  : str = "📋"
    EMPTY_TITLE : str = "لا توجد بيانات"

    def __init__(self,
                 columns: list,
                 stretch_col: int = -1,
                 col_widths: dict = None,
                 title: str = "",
                 add_text: str = "",
                 search_placeholder: str = "🔍  بحث...",
                 row_height: int = ROW_HEIGHT_LARGE,
                 empty_icon: str = "📋",
                 empty_title: str = "لا توجد بيانات",
                 parent=None):
        super().__init__(parent)

        self.EMPTY_ICON  = empty_icon
        self.EMPTY_TITLE = empty_title
        self._row_height  = row_height
        self._stretch_col = stretch_col

        self._build(columns, stretch_col, col_widths,
                    title, add_text, search_placeholder)

    # ── بناء الواجهة ──────────────────────────────────────

    def _build(self, columns, stretch_col, col_widths,
               title, add_text, placeholder):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setStyleSheet(f"background:{_C['bg_input']};")

        # Header
        self._header = ListHeader(
            title=title,
            add_text=add_text,
            show_search=True,
            search_placeholder=placeholder,
        )
        self._header.search_changed.connect(self.search_changed.emit)
        if add_text:
            self._header.add_clicked.connect(self.add_clicked.emit)
        root.addWidget(self._header)

        # Table
        self.table = make_list_table(
            columns=columns,
            stretch_col=stretch_col,
            col_widths=col_widths,
        )
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.itemSelectionChanged.connect(self._on_select)
        root.addWidget(self.table, stretch=1)

        # Empty state
        self._empty = EmptyState(
            icon=self.EMPTY_ICON,
            title=self.EMPTY_TITLE,
            style="plain", color="#9ca3af", min_height=100,
        )
        self._empty.setStyleSheet(
            f"QFrame {{ background:{_C['bg_input']}; border:none; }}"
        )
        self._empty.setVisible(False)
        root.addWidget(self._empty)

        # Status bar
        self._status = StatusBar()
        root.addWidget(self._status)

    # ── Table API ─────────────────────────────────────────

    def begin_fill(self):
        """يبدأ ملء الجدول — يمسح الصفوف القديمة."""
        self.table.setRowCount(0)

    def insert_row(self) -> int:
        """يضيف صف جديد ويرجع رقمه."""
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setRowHeight(r, self._row_height)
        return r

    def end_fill(self, shown: int = None):
        """
        ينهي ملء الجدول ويحدث العداد والحالة الفارغة.

        shown: عدد الصفوف الظاهرة (لو مختلفة عن الكل عند الفلترة)
        """
        total   = self.table.rowCount()
        visible = shown if shown is not None else total

        has_data = total > 0
        self.table.setVisible(has_data)
        self._empty.setVisible(not has_data)
        self._status.set_count(visible, total)

        if has_data:
            self._auto_resize()

    def _auto_resize(self):
        fixed = [i for i in range(self.table.columnCount())
                 if i != self._stretch_col]
        auto_fit_columns(
            self.table,
            fixed_cols=fixed,
            stretch_col=self._stretch_col,
            min_width=40,
            max_width=300,
        )

    # ── Selection ─────────────────────────────────────────

    def _on_select(self):
        row = self.table.currentRow()
        if row < 0:
            return
        item = self.table.item(row, 0)
        if item:
            data = item.data(Qt.UserRole)
            if data is not None:
                self.row_selected.emit(int(data))

    def selected_id(self) -> "int | None":
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if item:
            data = item.data(Qt.UserRole)
            return int(data) if data is not None else None
        return None

    def select_row_by_id(self, item_id: int):
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item and item.data(Qt.UserRole) == item_id:
                self.table.selectRow(r)
                return

    # ── Header API ────────────────────────────────────────

    def add_header_action(self, text: str, callback=None,
                          style: str = "normal"):
        return self._header.add_action(text, callback, style)

    def search_text(self) -> str:
        return self._header.search_text()

    def clear_search(self):
        self._header.clear_search()

    def set_add_enabled(self, enabled: bool):
        self._header.set_add_enabled(enabled)

    @property
    def header(self) -> ListHeader:
        return self._header