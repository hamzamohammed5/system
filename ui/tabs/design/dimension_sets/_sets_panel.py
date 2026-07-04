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
from ui.widgets.tables.tables       import make_table
from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.font import FS_SM, get_font_size, fs
from ui.constants import (
    COL_MIN_WIDTH, FINANCIAL_COL_AMOUNT_W, LIST_W_OFFSET,
    FILTER_SEARCH_H, FILTER_COMBO_MIN_H, LEDGER_MOVE_CMB_W,
    SPACING_SM, MARGIN_ZERO,
    DIM_SETS_PANEL_HDR_RADIUS, DIM_SETS_PANEL_HDR_PAD_V, DIM_SETS_PANEL_HDR_PAD_H,
    DIM_SETS_PANEL_HINT_RADIUS, DIM_SETS_PANEL_HINT_BORDER_W,
    DIM_SETS_PANEL_HINT_PAD_V, DIM_SETS_PANEL_HINT_PAD_H,
)


class _SetsPanel(QWidget, WidgetMixin):
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
        self._init_widget_mixin(lang=False, data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        size = get_font_size()
        self._hdr.setStyleSheet(f"""
            font-weight: bold;
            font-size: {fs(size, +1)}px;
            color: {_C["acc_type_asset"]};
            background: {_C["accent_light"]};
            border-radius: {DIM_SETS_PANEL_HDR_RADIUS}px;
            padding: {DIM_SETS_PANEL_HDR_PAD_V}px {DIM_SETS_PANEL_HDR_PAD_H}px;
        """)
        self._hint.setStyleSheet(
            f"color: {_C['text_neutral']};"
            f"font-size: {FS_SM}px;"
            f"background: {_C['investor_link_bg']};"
            f"border: {DIM_SETS_PANEL_HINT_BORDER_W}px solid {_C['investor_link_border']};"
            f"border-radius: {DIM_SETS_PANEL_HINT_RADIUS}px; "
            f"padding: {DIM_SETS_PANEL_HINT_PAD_V}px {DIM_SETS_PANEL_HINT_PAD_H}px;"
        )

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(*MARGIN_ZERO)
        root.setSpacing(SPACING_SM)

        # ── رأس ──
        self._hdr = QLabel(tr("dim_sets_panel_title"))
        root.addWidget(self._hdr)

        # ── تلميح ──
        self._hint = QLabel(tr("dim_sets_card_hint"))
        self._hint.setWordWrap(True)
        root.addWidget(self._hint)

        # ── فلتر ──
        filter_row = QHBoxLayout()
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText(tr("dim_sets_list_search"))
        self.inp_search.setMinimumHeight(FILTER_SEARCH_H)
        self.inp_search.textChanged.connect(self._apply_filter)

        self.cmb_cat_filter = QComboBox()
        self.cmb_cat_filter.setMinimumHeight(FILTER_COMBO_MIN_H)
        self.cmb_cat_filter.setMinimumWidth(LEDGER_MOVE_CMB_W)
        self.cmb_cat_filter.currentIndexChanged.connect(self._apply_filter)

        filter_row.addWidget(QLabel(tr("empty_icon_search")))
        filter_row.addWidget(self.inp_search, stretch=1)
        filter_row.addWidget(QLabel(tr("account_tree_default_icon")))
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
        self.table.setColumnWidth(0, COL_MIN_WIDTH)
        self.table.setColumnWidth(2, FINANCIAL_COL_AMOUNT_W)
        self.table.setColumnWidth(3, LIST_W_OFFSET)
        self.table.setColumnWidth(4, LIST_W_OFFSET)
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
        arrow  = tr("category_tree_arrow") if depth > 0 else ""
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
            self.table.setItem(r, 2, QTableWidgetItem(ds["category_name"] or tr("dash")))
            self.table.setItem(r, 3, QTableWidgetItem(ds["default_unit"] or tr("dim_sets_list_default_unit")))
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
