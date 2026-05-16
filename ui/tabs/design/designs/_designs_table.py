
"""
ui/tabs/design/designs/_designs_table.py
==============================
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidgetItem, 
    QPushButton, QLabel, QLineEdit,
    QMessageBox, QFrame,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor


from db.designs.designs_repo import (
    fetch_design, delete_design,
)
from db.designs.designs_sizes_repo import (
    fetch_all_designs_summary,
)
from ui.helpers import make_table, danger_button, confirm_delete, buttons_row

from ._design_detail_panel import _DesignDetailPanel
# ── ألوان ──
_BLUE       = "#1565c0"
_BLUE_LIGHT = "#e8f0fe"
_BLUE_MID   = "#bbdefb"
_GREEN      = "#2e7d32"
_ORANGE     = "#e65100"


# ══════════════════════════════════════════════════════════
# جدول التصميمات (يسار)
# ══════════════════════════════════════════════════════════

class _DesignsTable(QWidget):
    """جدول التصميمات مع فلتر بسيط."""

    design_selected = pyqtSignal(int)
    design_deleted  = pyqtSignal()

    def __init__(self, conn, detail_panel: "_DesignDetailPanel", parent=None):
        super().__init__(parent)
        self.conn     = conn
        self._panel   = detail_panel
        self._all     = []
        self._build()
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        # ── فلتر ──
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"""
            QFrame {{
                background: {_BLUE_LIGHT};
                border: 1px solid {_BLUE_MID};
                border-radius: 6px;
            }}
        """)
        fl = QHBoxLayout(filter_frame)
        fl.setContentsMargins(8, 6, 8, 6)
        fl.setSpacing(6)

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 بحث بالاسم...")
        self.inp_search.setMinimumHeight(28)
        self.inp_search.textChanged.connect(self._apply_filter)

        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet(
            f"color: {_BLUE}; font-size: 10px; font-weight: bold; "
            "background: transparent; border: none;"
        )

        btn_new = QPushButton("➕  تصميم جديد")
        btn_new.setMinimumHeight(28)
        btn_new.setStyleSheet(f"""
            QPushButton {{
                background: {_BLUE}; color: white; border: none;
                border-radius: 4px; padding: 2px 10px; font-weight: bold; font-size: 11px;
            }}
            QPushButton:hover {{ background: #0d47a1; }}
        """)
        btn_new.clicked.connect(self._new_design)

        fl.addWidget(self.inp_search, stretch=1)
        fl.addWidget(self.lbl_count)
        fl.addWidget(btn_new)
        root.addWidget(filter_frame)

        # ── الجدول ──
        self.table = make_table(
            ["ID", "الاسم", "التصنيف", "المقاسات", "الملفات"],
            stretch_col=1
        )
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 65)
        self.table.setColumnWidth(4, 65)
        self.table.itemSelectionChanged.connect(self._on_select)
        self.table.doubleClicked.connect(self._on_select)
        root.addWidget(self.table)

        # ── أزرار ──
        btn_del = danger_button("🗑️  حذف")
        btn_del.setMinimumHeight(28)
        btn_del.clicked.connect(self._delete)
        root.addLayout(buttons_row(btn_del))

    def _load(self):
        self._all = list(fetch_all_designs_summary(self.conn))
        self._apply_filter()

    def _apply_filter(self):
        q    = self.inp_search.text().strip().lower()
        prev = self._selected_id()
        self.table.setRowCount(0)
        shown = 0

        for d in self._all:
            if q and q not in d["name"].lower():
                continue
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(d["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(d["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(d["category_name"] or "—"))

            sizes_cnt = d["sizes_count"] or 0
            files_cnt = d["files_count"] or 0

            item_sz = QTableWidgetItem(str(sizes_cnt))
            item_sz.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 3, item_sz)

            item_fl = QTableWidgetItem(str(files_cnt))
            item_fl.setTextAlignment(Qt.AlignCenter)
            if files_cnt == sizes_cnt and sizes_cnt > 0:
                item_fl.setForeground(QColor(_GREEN))
            elif files_cnt > 0:
                item_fl.setForeground(QColor(_ORANGE))
            self.table.setItem(r, 4, item_fl)

            self.table.item(r, 0).setData(Qt.UserRole, d["id"])
            shown += 1

        total = len(self._all)
        self.lbl_count.setText(f"({shown})" if shown == total else f"({shown}/{total})")

        if prev:
            for r in range(self.table.rowCount()):
                if self.table.item(r, 0).data(Qt.UserRole) == prev:
                    self.table.selectRow(r)
                    return

    def _selected_id(self):
        row  = self.table.currentRow()
        item = self.table.item(row, 0) if row >= 0 else None
        return item.data(Qt.UserRole) if item else None

    def _on_select(self):
        did = self._selected_id()
        if did:
            self._panel.load_design(did)
            self.design_selected.emit(did)

    def _new_design(self):
        self.table.clearSelection()
        self._panel.reset()

    def _delete(self):
        did = self._selected_id()
        if did is None:
            QMessageBox.information(self, "تنبيه", "اختر تصميماً أولاً")
            return
        d = fetch_design(self.conn, did)
        if not d:
            return
        if confirm_delete(self, d["name"]):
            delete_design(self.conn, did)
            self._panel.reset()
            self._load()
            self.design_deleted.emit()

    def refresh(self):
        self._load()

