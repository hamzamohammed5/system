"""
ui/tabs/design/dimension_sets/_groups_panel.py
=====================================
تبويب 'المجموعات':
  - يسار:  إدارة التصنيفات (_CategoriesPanel)
  - يمين:  إدارة مجموعات المقاسات + حقولها
             ├── جدول المجموعات + فورم إضافة/تعديل/حذف
             └── _FieldsPanel (حقول المجموعة المختارة)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTableWidgetItem,
    QLabel, QGroupBox, QFormLayout,
    QPushButton, QMessageBox, QDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal
from ui.widgets.panels.themed_inputs import ThemedLineEdit, ThemedComboBox

from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.font import FS_BASE, FS_MD
from ui.constants import (
    SPLITTER_HANDLE_W, COL_MIN_WIDTH, DIM_SETS_LIST_CMB_CAT_MAX_W,
    DETAIL_LABEL_MIN_W, COMPONENT_ROW_WASTE_MIN_W,
    DIALOG_MIN_WIDTH, DETAIL_MIN_W, LIST_PANEL_MIN_W, DIM_VALUES_SPLITTER_R,
    FILTER_SEARCH_H, FILTER_COMBO_MIN_H,
    SPACING_SM, SPACING_MD, SPACING_ZERO, MARGIN_FORM, MARGIN_ZERO,
    BTN_MIN_HEIGHT, DIM_CAT_PANEL_COMBO_H, DIM_CAT_PANEL_TREE_BTN_H,
    DIM_CAT_PANEL_INPUT_H, DIM_CAT_PANEL_ACTION_BTN_H,
    DIM_GROUPS_BTN_ROW_SPACING, DIM_GROUPS_MGR_HDR_RADIUS,
    DIM_GROUPS_MGR_HDR_PAD_V, DIM_GROUPS_MGR_HDR_PAD_H,
    DIM_GROUPS_FIELDS_HDR_RADIUS, DIM_GROUPS_FIELDS_HDR_PAD_V, DIM_GROUPS_FIELDS_HDR_PAD_H,
    DIM_GROUPS_MGR_ROOT_SPACING, DIM_GROUPS_TOP_SPACING, DIM_GROUPS_MINI_BTN_H,
)
from services.design.dimension_set_service import DimensionSetService

from ._categories_panel import _CategoriesPanel
from ._fields_panel      import _FieldsPanel
from ui.widgets.components.button   import make_btn
from ui.widgets.tables.tables       import make_table

from ui.widgets.combo.unit import UnitCombo

def buttons_row(*buttons) -> QHBoxLayout:
    """صف أزرار أفقي."""
    row = QHBoxLayout()
    row.setSpacing(DIM_GROUPS_BTN_ROW_SPACING)
    for btn in buttons:
        row.addWidget(btn)
    row.addStretch()
    return row
# ══════════════════════════════════════════════════════════
# لوحة إدارة المجموعات + حقولها (يمين)
# ══════════════════════════════════════════════════════════

class _SetsManagerPanel(QWidget, WidgetMixin):
    sets_changed = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._svc        = DimensionSetService(conn)
        self._editing_id = None
        self._all_rows   = []
        self._build()
        self._load()
        self._init_widget_mixin(lang=False, data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        self._hdr.setStyleSheet(f"""
            font-weight: bold; font-size: {FS_MD}px; color: {_C['accent']};
            background: {_C['accent_light']}; border-radius: {DIM_GROUPS_MGR_HDR_RADIUS}px; padding: {DIM_GROUPS_MGR_HDR_PAD_V}px {DIM_GROUPS_MGR_HDR_PAD_H}px;
        """)
        self._v_splitter.setStyleSheet(f"""
            QSplitter::handle {{ background: {_C['border']}; }}
            QSplitter::handle:hover {{ background: {_C['accent_mid']}; }}
        """)
        self._fields_hdr.setStyleSheet(f"""
            font-weight: bold; font-size: {FS_BASE}px; color: {_C['purple']};
            background: {_C['purple_bg']}; border-radius: {DIM_GROUPS_FIELDS_HDR_RADIUS}px; padding: {DIM_GROUPS_FIELDS_HDR_PAD_V}px {DIM_GROUPS_FIELDS_HDR_PAD_H}px;
        """)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(*MARGIN_FORM)
        root.setSpacing(DIM_GROUPS_MGR_ROOT_SPACING)

        self._hdr = QLabel(tr("dim_sets_panel_title"))
        root.addWidget(self._hdr)

        # ── فلتر ──
        filter_row = QHBoxLayout()
        self.inp_search = ThemedLineEdit()
        self.inp_search.setPlaceholderText(tr("dim_sets_search_placeholder"))
        self.inp_search.setMinimumHeight(FILTER_SEARCH_H)
        self.inp_search.textChanged.connect(self._apply_filter)

        self.cmb_cat_filter = ThemedComboBox()
        self.cmb_cat_filter.setMinimumHeight(FILTER_COMBO_MIN_H)
        self.cmb_cat_filter.setMinimumWidth(DIM_SETS_LIST_CMB_CAT_MAX_W)
        self.cmb_cat_filter.currentIndexChanged.connect(self._apply_filter)

        filter_row.addWidget(QLabel(tr("empty_icon_search")))
        filter_row.addWidget(self.inp_search, stretch=1)
        filter_row.addWidget(QLabel(tr("account_tree_default_icon")))
        filter_row.addWidget(self.cmb_cat_filter)
        root.addLayout(filter_row)

        # ══ Splitter رأسي ══
        v_splitter = QSplitter(Qt.Vertical)
        self._v_splitter = v_splitter
        v_splitter.setHandleWidth(SPLITTER_HANDLE_W)

        # ── الجزء العلوي: جدول + فورم ──
        top_w = QWidget()
        top_lay = QVBoxLayout(top_w)
        top_lay.setContentsMargins(*MARGIN_ZERO)
        top_lay.setSpacing(DIM_GROUPS_TOP_SPACING)

        self.table = make_table(
            [tr("dim_sets_col_id"), tr("dim_sets_col_name"), tr("dim_sets_col_category"), tr("dim_sets_col_unit"), tr("dim_sets_col_fields")],
            stretch_col=1
        )
        self.table.setColumnWidth(0, COL_MIN_WIDTH)
        self.table.setColumnWidth(2, DIM_SETS_LIST_CMB_CAT_MAX_W)
        self.table.setColumnWidth(3, DETAIL_LABEL_MIN_W)
        self.table.setColumnWidth(4, COMPONENT_ROW_WASTE_MIN_W)
        self.table.itemSelectionChanged.connect(self._on_set_select)
        top_lay.addWidget(self.table)

        btn_edit_set = QPushButton(tr("btn_edit"))
        btn_del_set  = make_btn(tr("btn_delete"), style="danger")
        for b in (btn_edit_set, btn_del_set):
            b.setMinimumHeight(DIM_GROUPS_MINI_BTN_H)
        btn_edit_set.clicked.connect(self._edit_set)
        btn_del_set.clicked.connect(self._delete_set)
        top_lay.addLayout(buttons_row(btn_edit_set, btn_del_set))

        # فورم إضافة / تعديل المجموعة
        self._form_grp = QGroupBox(tr("dim_sets_form_title"))
        form = QFormLayout(self._form_grp)
        form.setSpacing(SPACING_MD)
        form.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = QLabel(tr("dim_sets_new_mode"))
        self.lbl_mode.setStyleSheet(f"font-weight: bold; color: {_C['accent']};")
        form.addRow(self.lbl_mode)

        self.inp_name = ThemedLineEdit()
        self.inp_name.setPlaceholderText(tr("dim_sets_name_placeholder"))
        self.inp_name.setMinimumHeight(DIM_CAT_PANEL_INPUT_H)
        form.addRow(tr("name") + tr("field_colon"), self.inp_name)

        self.cmb_category = ThemedComboBox()
        self.cmb_category.setMinimumHeight(DIM_CAT_PANEL_COMBO_H)
        form.addRow(tr("category") + tr("field_colon"), self.cmb_category)

        # ── الوحدة الافتراضية — UnitCombo مع حفظ آخر اختيار ──
        self.cmb_unit = UnitCombo(
            conn     = self.conn,
            last_key = "dim_sets_default_unit",
            current  = "cm",
        )
        self.cmb_unit.setMinimumHeight(DIM_CAT_PANEL_COMBO_H)
        form.addRow(tr("dim_sets_default_unit_label") + tr("field_colon"), self.cmb_unit)

        self.inp_notes = ThemedLineEdit()
        self.inp_notes.setPlaceholderText(tr("notes"))
        self.inp_notes.setMinimumHeight(DIM_CAT_PANEL_COMBO_H)
        form.addRow(tr("notes") + tr("field_colon"), self.inp_notes)

        btn_form_row = QHBoxLayout()
        self.btn_add    = QPushButton(tr("dim_sets_add_btn"))
        self.btn_save   = QPushButton(tr("btn_save"))
        self.btn_cancel = QPushButton(tr("btn_cancel"))
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        for b in (self.btn_add, self.btn_save, self.btn_cancel):
            b.setMinimumHeight(DIM_CAT_PANEL_ACTION_BTN_H)
        self.btn_add.clicked.connect(self._add_set)
        self.btn_save.clicked.connect(self._save_set)
        self.btn_cancel.clicked.connect(self._reset_form)
        btn_form_row.addWidget(self.btn_add)
        btn_form_row.addWidget(self.btn_save)
        btn_form_row.addWidget(self.btn_cancel)
        form.addRow(btn_form_row)

        top_lay.addWidget(self._form_grp)
        v_splitter.addWidget(top_w)

        # ── الجزء السفلي: _FieldsPanel ──
        bot_w = QWidget()
        bot_lay = QVBoxLayout(bot_w)
        bot_lay.setContentsMargins(*MARGIN_ZERO)
        bot_lay.setSpacing(SPACING_ZERO)

        self._fields_hdr = QLabel(tr("dim_sets_fields_header"))
        bot_lay.addWidget(self._fields_hdr)

        self._fields_panel = _FieldsPanel(self.conn)
        bot_lay.addWidget(self._fields_panel)

        v_splitter.addWidget(bot_w)
        v_splitter.setSizes([DIALOG_MIN_WIDTH, DETAIL_MIN_W])

        root.addWidget(v_splitter, stretch=1)

        self._reload_cat_combos()

    # ── تحميل ──

    def _reload_cat_combos(self):
        rows = self._svc.list_categories()
        tree = self._svc.build_tree(rows)

        prev_f = self.cmb_cat_filter.currentData()
        self.cmb_cat_filter.blockSignals(True)
        self.cmb_cat_filter.clear()
        self.cmb_cat_filter.addItem(tr("dim_sets_all_categories"), None)
        self._add_cat_nodes(self.cmb_cat_filter, tree, 0)
        for i in range(self.cmb_cat_filter.count()):
            if self.cmb_cat_filter.itemData(i) == prev_f:
                self.cmb_cat_filter.setCurrentIndex(i)
                break
        self.cmb_cat_filter.blockSignals(False)

        prev_c = self.cmb_category.currentData()
        self.cmb_category.blockSignals(True)
        self.cmb_category.clear()
        self.cmb_category.addItem(tr("design_detail_no_category"), None)
        self._add_cat_nodes(self.cmb_category, tree, 0)
        for i in range(self.cmb_category.count()):
            if self.cmb_category.itemData(i) == prev_c:
                self.cmb_category.setCurrentIndex(i)
                break
        self.cmb_category.blockSignals(False)

    def _add_cat_nodes(self, combo, nodes, depth):
        indent = "    " * depth
        arrow  = tr("category_tree_arrow") if depth > 0 else ""
        for node in nodes:
            combo.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            if node["children"]:
                self._add_cat_nodes(combo, node["children"], depth + 1)

    def _load(self):
        self._all_rows = list(self._svc.list_sets())
        self._reload_cat_combos()
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
                    return
        self._fields_panel.clear()

    def _selected_id(self):
        row  = self.table.currentRow()
        item = self.table.item(row, 0) if row >= 0 else None
        return item.data(Qt.UserRole) if item else None

    def _on_set_select(self):
        sid = self._selected_id()
        if sid:
            self._fields_panel.load_set(sid)
        else:
            self._fields_panel.clear()

    # ── CRUD ──

    def _add_set(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, tr("warning"), tr("enter_field").format(label=tr("name")))
            return
        cat_id = self.cmb_category.currentData()
        unit   = self.cmb_unit.current_unit()
        notes  = self.inp_notes.text().strip()
        new_id = self._svc.create_set(name, cat_id, unit, notes)
        self._reset_form()
        self._load()
        for r in range(self.table.rowCount()):
            if self.table.item(r, 0).data(Qt.UserRole) == new_id:
                self.table.selectRow(r)
                break
        self.sets_changed.emit()

    def _edit_set(self):
        sid = self._selected_id()
        if sid is None:
            QMessageBox.information(self, tr("info"), tr("select_item_first"))
            return
        ds = self._svc.get_set(sid)
        if not ds:
            return
        self._editing_id = sid
        self.inp_name.setText(ds["name"])
        self.inp_notes.setText(ds["notes"] or "")
        for i in range(self.cmb_category.count()):
            if self.cmb_category.itemData(i) == ds["category_id"]:
                self.cmb_category.setCurrentIndex(i)
                break

        # اختيار الوحدة الحالية في UnitCombo
        self.cmb_unit.set_unit(ds["default_unit"] or "cm")

        self.lbl_mode.setText(tr("dim_sets_edit_mode").format(name=ds['name']))
        self.btn_add.setVisible(False)
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)

    def _save_set(self):
        if self._editing_id is None:
            return
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, tr("warning"), tr("enter_field").format(label=tr("name")))
            return
        cat_id = self.cmb_category.currentData()
        unit   = self.cmb_unit.current_unit()
        notes  = self.inp_notes.text().strip()
        self._svc.update_set(self._editing_id, name, cat_id, unit, notes)
        self._reset_form()
        self._load()
        self.sets_changed.emit()

    def _delete_set(self):
        sid = self._selected_id()
        if sid is None:
            QMessageBox.information(self, tr("info"), tr("select_item_first"))
            return
        ds = self._svc.get_set(sid)
        if not ds:
            return

        fields_cnt  = self._svc.count_fields_for_set(sid)
        designs_cnt = self._svc.count_designs_for_set(sid)

        if designs_cnt:
            QMessageBox.warning(
                self, tr("warning"),
                tr("dim_sets_linked_designs_warn").format(name=ds['name'], count=designs_cnt)
            )
            return

        msg = tr("delete_confirm_msg").format(name=ds['name'])
        if fields_cnt:
            msg += f"\n{tr('dim_sets_has_fields_warn').format(count=fields_cnt)}"

        if QMessageBox.question(
            self, tr("confirm_delete"), msg,
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            self._fields_panel.clear()
            self._svc.delete_set(sid)
            self._reset_form()
            self._load()
            self.sets_changed.emit()

    def _reset_form(self):
        self._editing_id = None
        self.inp_name.clear()
        self.inp_notes.clear()
        self.cmb_category.setCurrentIndex(0)
        # UnitCombo يرجع لآخر اختيار محفوظ تلقائياً
        self.lbl_mode.setText(tr("dim_sets_new_mode"))
        self.btn_add.setVisible(True)
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)

    def refresh_categories(self):
        self._reload_cat_combos()
        self._load()

    def refresh(self):
        current_sid = self._selected_id()
        self._load()
        if current_sid:
            self._fields_panel.load_set(current_sid)

    def refresh_unit_combo(self):
        """يُستدعى بعد إضافة وحدات جديدة من الإعدادات."""
        self.cmb_unit.refresh()


# ══════════════════════════════════════════════════════════
# لوحة المجموعات الرئيسية
# ══════════════════════════════════════════════════════════

class _GroupsPanel(QWidget, WidgetMixin):
    sets_changed = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self._init_widget_mixin(lang=False, data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        self._splitter.setStyleSheet(f"""
            QSplitter::handle {{ background: {_C['border']}; }}
            QSplitter::handle:hover {{ background: {_C['accent_light']}; }}
        """)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(*MARGIN_ZERO)
        root.setSpacing(SPACING_ZERO)

        splitter = QSplitter(Qt.Horizontal)
        self._splitter = splitter
        splitter.setHandleWidth(SPLITTER_HANDLE_W)

        self._cats_panel = _CategoriesPanel(self.conn)
        self._cats_panel.changed.connect(self._on_categories_changed)
        splitter.addWidget(self._cats_panel)

        self._sets_manager = _SetsManagerPanel(self.conn)
        self._sets_manager.sets_changed.connect(self.sets_changed.emit)
        splitter.addWidget(self._sets_manager)

        splitter.setSizes([LIST_PANEL_MIN_W, DIM_VALUES_SPLITTER_R])
        root.addWidget(splitter)

    def _on_categories_changed(self):
        self._sets_manager.refresh_categories()

    def refresh(self):
        self._cats_panel.refresh()
        self._sets_manager.refresh()

    def refresh_unit_combos(self):
        """يُستدعى من SettingsDialog بعد تعديل الوحدات."""
        self._sets_manager.refresh_unit_combo()