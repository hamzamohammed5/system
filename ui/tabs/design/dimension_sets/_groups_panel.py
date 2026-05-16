"""
ui/tabs/design/dimension_sets/_groups_panel.py
=====================================
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTableWidgetItem,
    QLabel, QLineEdit,

)
from PyQt5.QtCore import Qt

from db.designs.dimension_sets_repo import (
    fetch_all_dimension_sets,fetch_fields_for_set

)
from ._categories_panel import _CategoriesPanel

from ui.helpers import make_table


# ══════════════════════════════════════════════════════════
# لوحة المجموعات (عرض + إدارة التصنيفات)
# ══════════════════════════════════════════════════════════

class _GroupsPanel(QWidget):
    """
    تبويب 'المجموعات':
      - يسار:  إدارة التصنيفات (_CategoriesPanel)
      - يمين:  جدول كل مجموعات المقاسات
    """

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(5)
        splitter.setStyleSheet("""
            QSplitter::handle { background: #e0e0e0; }
            QSplitter::handle:hover { background: #bbdefb; }
        """)

        # ── يسار: إدارة التصنيفات ──
        self._cats_panel = _CategoriesPanel(self.conn)
        self._cats_panel.changed.connect(self._on_categories_changed)
        splitter.addWidget(self._cats_panel)

        # ── يمين: جدول المجموعات ──
        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(8, 8, 8, 8)
        right_lay.setSpacing(6)

        hdr = QLabel("📐  كل مجموعات المقاسات")
        hdr.setStyleSheet("""
            font-weight: bold; font-size: 13px; color: #1565c0;
            background: #e8f0fe; border-radius: 6px; padding: 6px 12px;
        """)
        right_lay.addWidget(hdr)

        search_row = QHBoxLayout()
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 بحث باسم المجموعة...")
        self.inp_search.setMinimumHeight(28)
        self.inp_search.textChanged.connect(self._apply_filter)
        search_row.addWidget(QLabel("🔍"))
        search_row.addWidget(self.inp_search, stretch=1)
        right_lay.addLayout(search_row)

        self.table = make_table(
            ["ID", "اسم المجموعة", "التصنيف", "الوحدة", "عدد الحقول", "الحقول"],
            stretch_col=1
        )
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 60)
        self.table.setColumnWidth(4, 70)
        self.table.setColumnWidth(5, 200)
        right_lay.addWidget(self.table, stretch=1)

        splitter.addWidget(right)
        splitter.setSizes([320, 580])

        root.addWidget(splitter)
        self._load()

    def _load(self):
        self._all_rows = list(fetch_all_dimension_sets(self.conn))
        self._apply_filter()

    def _apply_filter(self):
        q = self.inp_search.text().strip().lower()
        self.table.setRowCount(0)

        for ds in self._all_rows:
            if q and q not in ds["name"].lower():
                continue
            fields      = fetch_fields_for_set(self.conn, ds["id"])
            cnt         = len(fields)
            field_names = "، ".join(f["label"] for f in fields[:6])
            if cnt > 6:
                field_names += f" ... (+{cnt - 6})"

            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(ds["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(ds["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(ds["category_name"] or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(ds["default_unit"] or "cm"))
            self.table.setItem(r, 4, QTableWidgetItem(str(cnt)))
            self.table.setItem(r, 5, QTableWidgetItem(field_names))
            self.table.item(r, 0).setData(Qt.UserRole, ds["id"])

    def _on_categories_changed(self):
        """لما تتغير التصنيفات، نحدّث جدول المجموعات."""
        self._load()

    def refresh(self):
        self._cats_panel.refresh()
        self._load()

