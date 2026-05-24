"""
ui/widgets/shared/list_panel_with_shared.py
============================================
SharedItemsListPanel — قاعدة مشتركة للجداول التي تدعم العناصر المشتركة.

يوحّد الكود المتكرر بين machine_table.py و labor_op_table.py:
  - legend العناصر المشتركة/المنشورة
  - FilterBar
  - أزرار تعديل/حذف/استبدال شامل/تعديل مشترك/نشر كمشترك
  - منطق التلوين
  - _load + _apply_filter pattern

الاستخدام:
    class _MachineTable(SharedItemsListPanel):
        SHARED_TYPE  = "machine"
        TABLE_COLS   = ["ID", "الاسم", "التصنيف", ...]
        FILTER_SCOPE = "machine"

        def _fetch_local_rows(self): ...
        def _get_item_data_for_publish(self, row): ...
        def _fill_table_row(self, r, item): ...
        def _edit_item(self, item_id): ...
        def _delete_item(self, item_id, item_name): ...
        def _bulk_replace_item(self, item_id, item_name): ...
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QTableWidgetItem, QMessageBox,
)
from PyQt5.QtGui import QColor

from ui.helpers import (
    make_table, buttons_row, section_label,
    confirm_delete, danger_button,
)
from ui.widgets.shared.filter_bar import FilterBar
from ui.widgets.shared.shared_ops_mixin import SharedOpsMixin
from ui.events import bus

_SHARED_COLOR    = "#2e7d52"
_SHARED_BG       = "#e8f5e9"
_PUBLISHED_COLOR = "#1565c0"
_PUBLISHED_BG    = "#e3f2fd"


class SharedItemsListPanel(QWidget, SharedOpsMixin):
    """
    قاعدة مشتركة للجداول التي تدعم العناصر المشتركة.

    Override المطلوب:
      SHARED_TYPE        : str  — نوع العنصر (machine / labor_op / ...)
      TABLE_COLS         : list — أعمدة الجدول
      FILTER_SCOPE       : str  — scope لـ FilterBar
      TABLE_TITLE        : str  — عنوان القسم
      HAS_BULK_REPLACE   : bool — هل يوجد زر استبدال شامل

      _fetch_local_rows()       → list[dict]
      _get_shared_rows(local)   → list[dict]
      _get_published_names()    → set[str]
      _fill_table_row(r, item)  → None
      _edit_item(item_id)       → None
      _delete_item(id, name)    → None
      _bulk_replace_item(id, name) → None (اختياري)
      _get_item_data_for_publish(row) → dict
    """

    SHARED_TYPE      : str  = ""
    TABLE_COLS       : list = []
    FILTER_SCOPE     : str  = "all"
    TABLE_TITLE      : str  = "─── العناصر المحفوظة ───"
    HAS_BULK_REPLACE : bool = False

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn             = conn
        self._all_rows        = []
        self._published_names = set()
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _live_conn(self):
        if self.conn is not None:
            try:
                self.conn.execute("SELECT 1")
                return self.conn
            except Exception:
                pass
        from db.companies.company_state import company_state
        return company_state.get_erp_conn()

    # ── بناء الواجهة ──────────────────────────────────────

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(6)
        root.addWidget(section_label(self.TABLE_TITLE))

        lbl_shared = QLabel("🔗 أخضر = عنصر مشترك وارد من شركة أخرى")
        lbl_shared.setStyleSheet(
            f"color:{_SHARED_COLOR}; background:{_SHARED_BG};"
            "border-radius:4px; padding:3px 8px; font-size:9pt;"
        )
        root.addWidget(lbl_shared)

        lbl_published = QLabel("📤 أزرق = عنصر محلي منشور ومشترك مع شركات أخرى")
        lbl_published.setStyleSheet(
            f"color:{_PUBLISHED_COLOR}; background:{_PUBLISHED_BG};"
            "border-radius:4px; padding:3px 8px; font-size:9pt;"
        )
        root.addWidget(lbl_published)

        self._filter = FilterBar(self._live_conn(), scope=self.FILTER_SCOPE)
        self._filter.filter_changed.connect(self._apply_filter)
        root.addWidget(self._filter)

        self.table = make_table(self.TABLE_COLS, stretch_col=1)
        self.table.setAlternatingRowColors(True)
        self._setup_column_widths(self.table)
        root.addWidget(self.table)

        root.addLayout(self._build_buttons())

    def _build_buttons(self):
        btn_edit        = QPushButton("✏️  تعديل")
        btn_del         = danger_button("🗑️  حذف")
        btn_edit_shared = QPushButton("🔗  تعديل المشترك")
        btn_publish     = QPushButton("📤  نشر كمشترك")

        btn_edit_shared.setStyleSheet(
            f"QPushButton {{ background:{_SHARED_BG}; color:{_SHARED_COLOR};"
            "border:1px solid #a5d6a7; border-radius:4px;"
            "padding:4px 10px; font-weight:bold; }}"
            f"QPushButton:hover {{ background:#c8e6c9; }}"
        )
        btn_publish.setStyleSheet(
            f"QPushButton {{ background:{_PUBLISHED_BG}; color:{_PUBLISHED_COLOR};"
            "border:1px solid #90caf9; border-radius:4px;"
            "padding:4px 10px; font-weight:bold; }}"
            "QPushButton:hover { background:#bbdefb; }"
        )

        btns = [btn_edit, btn_del]

        if self.HAS_BULK_REPLACE:
            btn_replace = QPushButton("🔄  استبدال شامل")
            btn_replace.setStyleSheet(
                "QPushButton { background:#e65100; color:white; border-radius:4px;"
                "padding:4px 10px; font-weight:bold; }"
                "QPushButton:hover { background:#bf360c; }"
            )
            btn_replace.clicked.connect(self._on_bulk_replace)
            btns.append(btn_replace)

        btns += [btn_edit_shared, btn_publish]

        for btn in btns:
            btn.setMinimumHeight(30)

        btn_edit.clicked.connect(self._on_edit)
        btn_del.clicked.connect(self._on_delete)
        btn_edit_shared.clicked.connect(self._on_edit_shared)
        btn_publish.clicked.connect(self._on_publish)

        return buttons_row(*btns)

    # ── Override hooks ─────────────────────────────────────

    def _setup_column_widths(self, table):
        """Override لتحديد عروض الأعمدة."""
        pass

    def _fetch_local_rows(self) -> list:
        raise NotImplementedError

    def _get_shared_rows(self, local_rows: list) -> list:
        return []

    def _get_published_names(self) -> set:
        try:
            from ui.tabs.companies.shared_items_mixin import get_published_local_names
            return get_published_local_names(self.SHARED_TYPE)
        except Exception:
            return set()

    def _fill_table_row(self, r: int, item: dict):
        """Override لملء صف الجدول."""
        raise NotImplementedError

    def _edit_item(self, item_id: int):
        """Override لمنطق التعديل."""
        raise NotImplementedError

    def _delete_item(self, item_id: int, item_name: str):
        """Override لمنطق الحذف."""
        raise NotImplementedError

    def _bulk_replace_item(self, item_id: int, item_name: str):
        """Override لمنطق الاستبدال الشامل (اختياري)."""
        pass

    def _get_item_data_for_publish(self, row: dict) -> dict:
        """Override لجمع بيانات النشر."""
        return {}

    # ── تحميل البيانات ────────────────────────────────────

    def _load(self):
        try:
            local_rows = [dict(r) for r in self._fetch_local_rows()]
        except Exception:
            local_rows = []

        self._published_names = self._get_published_names()
        shared_rows = self._get_shared_rows(local_rows)
        self._all_rows = local_rows + shared_rows
        self._apply_filter()

    def _apply_filter(self):
        self.table.setRowCount(0)
        shown = 0

        for item in self._all_rows:
            if not self._filter.match(item.get("name", ""), item.get("category_id")):
                continue

            is_shared    = item.get("is_shared", False)
            is_published = (
                not is_shared and
                str(item.get("name", "")).strip().lower() in self._published_names
            )
            item["_is_shared"]    = is_shared
            item["_is_published"] = is_published

            r = self.table.rowCount()
            self.table.insertRow(r)
            self._fill_table_row(r, item)
            self._apply_row_colors(r, is_shared, is_published)
            shown += 1

        self._filter.set_count(shown, len(self._all_rows))

    def _apply_row_colors(self, r: int, is_shared: bool, is_published: bool):
        if is_shared:
            bg, fg = _SHARED_BG, _SHARED_COLOR
        elif is_published:
            bg, fg = _PUBLISHED_BG, _PUBLISHED_COLOR
        else:
            return

        for col in range(self.table.columnCount()):
            item = self.table.item(r, col)
            if item:
                item.setBackground(QColor(bg))
                item.setForeground(QColor(fg))

    # ── الحصول على البيانات المحددة ───────────────────────

    def _selected_row_data(self) -> tuple:
        row = self.table.currentRow()
        if row == -1:
            return None, None
        item_id   = self.table.item(row, 0).data(0x0100)
        item_name = self.table.item(row, 1).text()
        # إزالة البادئة (🔗 أو 📤) من الاسم
        item_name = item_name.lstrip("🔗 📤 ")
        return item_id, item_name

    # ── أحداث الأزرار ─────────────────────────────────────

    def _on_edit(self):
        item_id, name = self._selected_row_data()
        if item_id is None:
            QMessageBox.information(self, "تنبيه", "اختر عنصراً أولاً")
            return
        if self._check_shared_id(item_id):
            QMessageBox.information(
                self, "عنصر مشترك",
                "هذا عنصر مشترك — استخدم «🔗 تعديل المشترك»."
            )
            return
        self._edit_item(int(item_id))

    def _on_delete(self):
        item_id, name = self._selected_row_data()
        if item_id is None:
            QMessageBox.information(self, "تنبيه", "اختر عنصراً أولاً")
            return
        if self._check_shared_id(item_id):
            QMessageBox.warning(self, "عنصر مشترك", "لا يمكن حذف عنصر مشترك من هنا.")
            return
        self._delete_item(int(item_id), name)

    def _on_bulk_replace(self):
        item_id, name = self._selected_row_data()
        if item_id is None:
            QMessageBox.information(self, "تنبيه", "اختر عنصراً أولاً")
            return
        if self._check_shared_id(item_id):
            QMessageBox.information(
                self, "تنبيه",
                "الاستبدال الشامل غير متاح للعناصر المشتركة."
            )
            return
        self._bulk_replace_item(int(item_id), name)

    def _on_edit_shared(self):
        item_id, _ = self._selected_row_data()
        if item_id is None:
            QMessageBox.information(self, "تنبيه", "اختر عنصراً أولاً")
            return
        self._edit_shared_item(item_id, self.SHARED_TYPE, self)

    def _on_publish(self):
        item_id, _ = self._selected_row_data()
        if item_id is None:
            QMessageBox.information(self, "تنبيه", "اختر عنصراً من الجدول أولاً")
            return
        if self._check_shared_id(item_id):
            QMessageBox.information(
                self, "مشترك بالفعل",
                "هذا العنصر مشترك بالفعل.\n"
                "استخدم «🔗 تعديل المشترك» لتعديل الربط."
            )
            return
        row = self._find_row_by_id(item_id)
        if not row:
            return
        item_data = self._get_item_data_for_publish(row)
        self._publish_item(row, self.SHARED_TYPE, item_data, self)
