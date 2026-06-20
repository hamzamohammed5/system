"""
ui/tabs/design/dimension_sets/_sets_panel.py
=====================================
قائمة اختيار مجموعات المقاسات فقط.
كل إدارة المجموعات (إضافة/تعديل/حذف) انتقلت لـ _GroupsPanel.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidgetItem,
    QLabel, QLineEdit,
    QComboBox,
)
from PyQt5.QtCore import Qt, pyqtSignal

from db.designs.dimension_sets_repo import (
    fetch_all_design_categories,
    build_category_tree,
    fetch_all_dimension_sets,
)
from ui.helpers import make_table
from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.font import FS_SM, FS_BASE, get_font_size, fs


class _SetsPanel(QWidget):
    """
    قايمة اختيار مجموعات المقاسات — بدون إضافة أو تعديل أو حذف.
    كل إدارة المجموعات في تبويب 'المجموعات' (_GroupsPanel).
    """

    set_selected = pyqtSignal(int)

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._all_rows = []
        self._build()
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        # ── رأس ──
        hdr = QLabel(tr("dim_sets_panel_title"))
        hdr.setStyleSheet(f"""
            font-weight: bold;
            font-size: {fs(get_font_size(), +1)}px;
            color: {_C["acc_type_asset"]};
            background: {_C["accent_light"]};
            border-radius: 6px;
            padding: 6px 10px;
        """)
        root.addWidget(hdr)

        # ── تلميح ──
        hint = QLabel(tr("dim_sets_card_hint"))
        hint.setStyleSheet(
            f"color: {_C['text_neutral']};"
            f"font-size: {FS_SM}px;"
            f"background: {_C['investor_link_bg']};"
            f"border: 1px solid {_C['investor_link_border']};"
            "border-radius: 4px; padding: 4px 8px;"
        )
        hint.setWordWrap(True)
        root.addWidget(hint)

        # ── فلتر ──
        filter_row = QHBoxLayout()
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText(tr("dim_sets_list_search"))
        self.inp_search.setMinimumHeight(28)
        self.inp_search.textChanged.connect(self._apply_filter)

        self.cmb_cat_filter = QComboBox()
        self.cmb_cat_filter.setMinimumHeight(28)
        self.cmb_cat_filter.setMinimumWidth(120)
        self.cmb_cat_filter.currentIndexChanged.connect(self._apply_filter)

        filter_row.addWidget(QLabel("🔍"))
        filter_row.addWidget(self.inp_search, stretch=1)
        filter_row.addWidget(QLabel("📁"))
        filter_row.addWidget(self.cmb_cat_filter)
        root.addLayout(filter_row)

        # ── جدول (للاختيار فقط) ──
        self.table = make_table(
            [
                tr("dim_sets_col_id"),
                tr("dim_sets_col_name"),
                tr("dim_sets_col_category"),
                tr("dim_sets_col_unit"),
                tr("dim_sets_col_fields"),
            ],
            stretch_col=1
        )
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 60)
        self.table.setColumnWidth(4, 60)
        self.table.itemSelectionChanged.connect(self._on_select)
        root.addWidget(self.table, stretch=1)

        self._reload_cat_filter()

    def _reload_cat_filter(self):
        prev = self.cmb_cat_filter.currentData()
        self.cmb_cat_filter.blockSignals(True)
        self.cmb_cat_filter.clear()
        self.cmb_cat_filter.addItem(tr("dim_sets_all_categories"), None)
        rows = fetch_all_design_categories(self.conn)
        tree = build_category_tree(rows)
        self._add_cat_nodes(tree, 0)
        for i in range(self.cmb_cat_filter.count()):
            if self.cmb_cat_filter.itemData(i) == prev:
                self.cmb_cat_filter.setCurrentIndex(i)
                break
        self.cmb_cat_filter.blockSignals(False)

    def _add_cat_nodes(self, nodes, depth):
        indent = "    " * depth
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            self.cmb_cat_filter.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            if node["children"]:
                self._add_cat_nodes(node["children"], depth + 1)

    def _load(self):
        self._all_rows = list(fetch_all_dimension_sets(self.conn))
        self._reload_cat_filter()
        self._apply_filter()

    def _apply_filter(self):
        q      = self.inp_search.text().strip().lower()
        cat_id = self.cmb_cat_filter.currentData()
        prev   = self._selected_id()
        self.table.setRowCount(0)

        for ds in self._all_rows:
            if q and q not in ds["name"].lower():
                continue
            if cat_id is not None and ds["category_id"] != cat_id:
                continue
            cnt = self.conn.execute(
                "SELECT COUNT(*) as c FROM dimension_fields WHERE set_id=?",
                (ds["id"],)
            ).fetchone()["c"]
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(ds["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(ds["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(ds["category_name"] or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(ds["default_unit"] or "cm"))
            self.table.setItem(r, 4, QTableWidgetItem(str(cnt)))
            self.table.item(r, 0).setData(Qt.UserRole, ds["id"])

        if prev is not None:
            for r in range(self.table.rowCount()):
                if self.table.item(r, 0).data(Qt.UserRole) == prev:
                    self.table.selectRow(r)
                    break

    def _selected_id(self):
        row  = self.table.currentRow()
        item = self.table.item(row, 0) if row >= 0 else None
        return item.data(Qt.UserRole) if item else None

    def _on_select(self):
        sid = self._selected_id()
        if sid:
            self.set_selected.emit(sid)

    def refresh(self):
        self._load()
