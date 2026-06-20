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
    QLabel, QLineEdit, QComboBox, QGroupBox, QFormLayout,
    QPushButton, QMessageBox, QDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal

from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.font import FS_SM, FS_BASE, FS_MD
from services.design.dimension_set_service import DimensionSetService

from ._categories_panel import _CategoriesPanel
from ._fields_panel      import _FieldsPanel
from ui.widgets.components.button   import make_btn
from ui.widgets.tables.tables       import make_table

from ui.widgets.combo.unit import UnitCombo

def buttons_row(*buttons) -> QHBoxLayout:
    """صف أزرار أفقي."""
    row = QHBoxLayout()
    row.setSpacing(6)
    for btn in buttons:
        row.addWidget(btn)
    row.addStretch()
    return row
# ══════════════════════════════════════════════════════════
# لوحة إدارة المجموعات + حقولها (يمين)
# ══════════════════════════════════════════════════════════

class _SetsManagerPanel(QWidget):
    sets_changed = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._svc        = DimensionSetService(conn)
        self._editing_id = None
        self._all_rows   = []
        self._build()
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        hdr = QLabel(tr("dim_sets_panel_title"))
        hdr.setStyleSheet(f"""
            font-weight: bold; font-size: {FS_MD}px; color: {_C['accent']};
            background: {_C['accent_light']}; border-radius: 6px; padding: 6px 12px;
        """)
        root.addWidget(hdr)

        # ── فلتر ──
        filter_row = QHBoxLayout()
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText(tr("dim_sets_search_placeholder"))
        self.inp_search.setMinimumHeight(28)
        self.inp_search.textChanged.connect(self._apply_filter)

        self.cmb_cat_filter = QComboBox()
        self.cmb_cat_filter.setMinimumHeight(28)
        self.cmb_cat_filter.setMinimumWidth(130)
        self.cmb_cat_filter.currentIndexChanged.connect(self._apply_filter)

        filter_row.addWidget(QLabel("🔍"))
        filter_row.addWidget(self.inp_search, stretch=1)
        filter_row.addWidget(QLabel("📁"))
        filter_row.addWidget(self.cmb_cat_filter)
        root.addLayout(filter_row)

        # ══ Splitter رأسي ══
        v_splitter = QSplitter(Qt.Vertical)
        v_splitter.setHandleWidth(5)
        v_splitter.setStyleSheet(f"""
            QSplitter::handle {{ background: {_C['border']}; }}
            QSplitter::handle:hover {{ background: {_C['accent_mid']}; }}
        """)

        # ── الجزء العلوي: جدول + فورم ──
        top_w = QWidget()
        top_lay = QVBoxLayout(top_w)
        top_lay.setContentsMargins(0, 0, 0, 0)
        top_lay.setSpacing(6)

        self.table = make_table(
            [tr("dim_sets_col_id"), tr("dim_sets_col_name"), tr("dim_sets_col_category"), tr("dim_sets_col_unit"), tr("dim_sets_col_fields")],
            stretch_col=1
        )
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(2, 130)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 75)
        self.table.itemSelectionChanged.connect(self._on_set_select)
        top_lay.addWidget(self.table)

        btn_edit_set = QPushButton("✏️  " + tr("edit"))
        btn_del_set  = make_btn("🗑️  " + tr("delete"), style="danger")
        for b in (btn_edit_set, btn_del_set):
            b.setMinimumHeight(28)
        btn_edit_set.clicked.connect(self._edit_set)
        btn_del_set.clicked.connect(self._delete_set)
        top_lay.addLayout(buttons_row(btn_edit_set, btn_del_set))

        # فورم إضافة / تعديل المجموعة
        self._form_grp = QGroupBox(tr("dim_sets_form_title"))
        form = QFormLayout(self._form_grp)
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = QLabel(tr("dim_sets_new_mode"))
        self.lbl_mode.setStyleSheet(f"font-weight: bold; color: {_C['accent']};")
        form.addRow(self.lbl_mode)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText(tr("dim_sets_name_placeholder"))
        self.inp_name.setMinimumHeight(30)
        form.addRow(tr("name") + " :", self.inp_name)

        self.cmb_category = QComboBox()
        self.cmb_category.setMinimumHeight(28)
        form.addRow(tr("category") + " :", self.cmb_category)

        # ── الوحدة الافتراضية — UnitCombo مع حفظ آخر اختيار ──
        self.cmb_unit = UnitCombo(
            conn     = self.conn,
            last_key = "dim_sets_default_unit",
            current  = "cm",
        )
        self.cmb_unit.setMinimumHeight(28)
        form.addRow(tr("dim_sets_default_unit_label") + " :", self.cmb_unit)

        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText(tr("notes"))
        self.inp_notes.setMinimumHeight(28)
        form.addRow(tr("notes") + " :", self.inp_notes)

        btn_form_row = QHBoxLayout()
        self.btn_add    = QPushButton(tr("dim_sets_add_btn"))
        self.btn_save   = QPushButton("💾  " + tr("save"))
        self.btn_cancel = QPushButton("✖  " + tr("cancel"))
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        for b in (self.btn_add, self.btn_save, self.btn_cancel):
            b.setMinimumHeight(30)
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
        bot_lay.setContentsMargins(0, 0, 0, 0)
        bot_lay.setSpacing(0)

        fields_hdr = QLabel(tr("dim_sets_fields_header"))
        fields_hdr.setStyleSheet(f"""
            font-weight: bold; font-size: {FS_BASE}px; color: {_C['purple']};
            background: {_C['purple_bg']}; border-radius: 4px; padding: 5px 10px;
        """)
        bot_lay.addWidget(fields_hdr)

        self._fields_panel = _FieldsPanel(self.conn)
        bot_lay.addWidget(self._fields_panel)

        v_splitter.addWidget(bot_w)
        v_splitter.setSizes([380, 300])

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
        arrow  = "↳ " if depth > 0 else ""
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
            self.table.setItem(r, 2, QTableWidgetItem(ds["category_name"] or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(ds["default_unit"] or "cm"))
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

class _GroupsPanel(QWidget):
    sets_changed = pyqtSignal()

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
        splitter.setStyleSheet(f"""
            QSplitter::handle {{ background: {_C['border']}; }}
            QSplitter::handle:hover {{ background: {_C['accent_light']}; }}
        """)

        self._cats_panel = _CategoriesPanel(self.conn)
        self._cats_panel.changed.connect(self._on_categories_changed)
        splitter.addWidget(self._cats_panel)

        self._sets_manager = _SetsManagerPanel(self.conn)
        self._sets_manager.sets_changed.connect(self.sets_changed.emit)
        splitter.addWidget(self._sets_manager)

        splitter.setSizes([280, 720])
        root.addWidget(splitter)

    def _on_categories_changed(self):
        self._sets_manager.refresh_categories()

    def refresh(self):
        self._cats_panel.refresh()
        self._sets_manager.refresh()

    def refresh_unit_combos(self):
        """يُستدعى من SettingsDialog بعد تعديل الوحدات."""
        self._sets_manager.refresh_unit_combo()