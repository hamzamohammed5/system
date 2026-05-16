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
from PyQt5.QtCore import Qt

from db.designs.dimension_sets_repo import (
    fetch_all_dimension_sets,
    fetch_dimension_set,
    insert_dimension_set,
    update_dimension_set,
    delete_dimension_set,
    fetch_all_design_categories,
    build_category_tree,
)
from ._categories_panel import _CategoriesPanel
from ._fields_panel      import _FieldsPanel
from ui.helpers import make_table, danger_button, buttons_row


# ══════════════════════════════════════════════════════════
# لوحة إدارة المجموعات + حقولها (يمين)
# ══════════════════════════════════════════════════════════

class _SetsManagerPanel(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._editing_id = None
        self._all_rows   = []
        self._build()
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        hdr = QLabel("📐  مجموعات المقاسات")
        hdr.setStyleSheet("""
            font-weight: bold; font-size: 13px; color: #1565c0;
            background: #e8f0fe; border-radius: 6px; padding: 6px 12px;
        """)
        root.addWidget(hdr)

        # ── فلتر ──
        filter_row = QHBoxLayout()
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 بحث باسم المجموعة...")
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

        # ══ Splitter رأسي: جدول المجموعات + فورم ↕ حقول المجموعة ══
        v_splitter = QSplitter(Qt.Vertical)
        v_splitter.setHandleWidth(5)
        v_splitter.setStyleSheet("""
            QSplitter::handle { background: #e0e0e0; }
            QSplitter::handle:hover { background: #bbdefb; }
        """)

        # ── الجزء العلوي: جدول + فورم ──
        top_w = QWidget()
        top_lay = QVBoxLayout(top_w)
        top_lay.setContentsMargins(0, 0, 0, 0)
        top_lay.setSpacing(6)

        self.table = make_table(
            ["ID", "اسم المجموعة", "التصنيف", "الوحدة", "عدد الحقول"],
            stretch_col=1
        )
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(2, 130)
        self.table.setColumnWidth(3, 60)
        self.table.setColumnWidth(4, 75)
        self.table.itemSelectionChanged.connect(self._on_set_select)
        top_lay.addWidget(self.table)

        # أزرار المجموعة
        btn_edit_set = QPushButton("✏️  تعديل")
        btn_del_set  = danger_button("🗑️  حذف")
        for b in (btn_edit_set, btn_del_set):
            b.setMinimumHeight(28)
        btn_edit_set.clicked.connect(self._edit_set)
        btn_del_set.clicked.connect(self._delete_set)
        top_lay.addLayout(buttons_row(btn_edit_set, btn_del_set))

        # فورم إضافة / تعديل المجموعة
        self._form_grp = QGroupBox("بيانات المجموعة")
        form = QFormLayout(self._form_grp)
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = QLabel("─── مجموعة جديدة ───")
        self.lbl_mode.setStyleSheet("font-weight: bold; color: #1565c0;")
        form.addRow(self.lbl_mode)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("مثال: مقاسات الثوب، مقاسات البنطلون...")
        self.inp_name.setMinimumHeight(30)
        form.addRow("الاسم :", self.inp_name)

        self.cmb_category = QComboBox()
        self.cmb_category.setMinimumHeight(28)
        form.addRow("التصنيف :", self.cmb_category)

        self.cmb_unit = QComboBox()
        self.cmb_unit.setEditable(True)
        self.cmb_unit.setMinimumHeight(28)
        for u in ["cm", "mm", "m", "inch"]:
            self.cmb_unit.addItem(u, u)
        form.addRow("الوحدة الافتراضية :", self.cmb_unit)

        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("ملاحظات...")
        self.inp_notes.setMinimumHeight(28)
        form.addRow("ملاحظات :", self.inp_notes)

        btn_form_row = QHBoxLayout()
        self.btn_add    = QPushButton("➕  إضافة مجموعة")
        self.btn_save   = QPushButton("💾  حفظ")
        self.btn_cancel = QPushButton("✖  إلغاء")
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

        # ── الجزء السفلي: _FieldsPanel للمجموعة المختارة ──
        bot_w = QWidget()
        bot_lay = QVBoxLayout(bot_w)
        bot_lay.setContentsMargins(0, 0, 0, 0)
        bot_lay.setSpacing(0)

        fields_hdr = QLabel("📋  حقول المجموعة المختارة")
        fields_hdr.setStyleSheet("""
            font-weight: bold; font-size: 12px; color: #7b1fa2;
            background: #f3e5f5; border-radius: 4px; padding: 5px 10px;
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
        rows = fetch_all_design_categories(self.conn)
        tree = build_category_tree(rows)

        prev_f = self.cmb_cat_filter.currentData()
        self.cmb_cat_filter.blockSignals(True)
        self.cmb_cat_filter.clear()
        self.cmb_cat_filter.addItem("— كل التصنيفات —", None)
        self._add_cat_nodes(self.cmb_cat_filter, tree, 0)
        for i in range(self.cmb_cat_filter.count()):
            if self.cmb_cat_filter.itemData(i) == prev_f:
                self.cmb_cat_filter.setCurrentIndex(i)
                break
        self.cmb_cat_filter.blockSignals(False)

        prev_c = self.cmb_category.currentData()
        self.cmb_category.blockSignals(True)
        self.cmb_category.clear()
        self.cmb_category.addItem("— بدون تصنيف —", None)
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
        self._all_rows = list(fetch_all_dimension_sets(self.conn))
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
            QMessageBox.warning(self, "تنبيه", "أدخل اسم المجموعة")
            return
        cat_id = self.cmb_category.currentData()
        unit   = self.cmb_unit.currentText().strip() or "cm"
        notes  = self.inp_notes.text().strip()
        new_id = insert_dimension_set(self.conn, name, cat_id, unit, notes)
        self._reset_form()
        self._load()
        for r in range(self.table.rowCount()):
            if self.table.item(r, 0).data(Qt.UserRole) == new_id:
                self.table.selectRow(r)
                break

    def _edit_set(self):
        sid = self._selected_id()
        if sid is None:
            QMessageBox.information(self, "تنبيه", "اختر مجموعة أولاً")
            return
        ds = fetch_dimension_set(self.conn, sid)
        if not ds:
            return
        self._editing_id = sid
        self.inp_name.setText(ds["name"])
        self.inp_notes.setText(ds["notes"] or "")
        for i in range(self.cmb_category.count()):
            if self.cmb_category.itemData(i) == ds["category_id"]:
                self.cmb_category.setCurrentIndex(i)
                break
        unit = ds["default_unit"] or "cm"
        idx  = self.cmb_unit.findText(unit)
        if idx >= 0:
            self.cmb_unit.setCurrentIndex(idx)
        else:
            self.cmb_unit.setCurrentText(unit)
        self.lbl_mode.setText(f"─── تعديل: {ds['name']} ───")
        self.btn_add.setVisible(False)
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)

    def _save_set(self):
        if self._editing_id is None:
            return
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم المجموعة")
            return
        cat_id = self.cmb_category.currentData()
        unit   = self.cmb_unit.currentText().strip() or "cm"
        notes  = self.inp_notes.text().strip()
        update_dimension_set(self.conn, self._editing_id, name, cat_id, unit, notes)
        self._reset_form()
        self._load()

    def _delete_set(self):
        sid = self._selected_id()
        if sid is None:
            QMessageBox.information(self, "تنبيه", "اختر مجموعة أولاً")
            return
        ds = fetch_dimension_set(self.conn, sid)
        if not ds:
            return

        fields_cnt  = self.conn.execute(
            "SELECT COUNT(*) as c FROM dimension_fields WHERE set_id=?", (sid,)
        ).fetchone()["c"]
        designs_cnt = self.conn.execute(
            "SELECT COUNT(*) as c FROM design_dimensions WHERE set_id=?", (sid,)
        ).fetchone()["c"]

        if designs_cnt:
            QMessageBox.warning(
                self, "تعذر الحذف",
                f"المجموعة «{ds['name']}» مرتبطة بـ {designs_cnt} تصميم.\n"
                "احذف الارتباط من التصميمات أولاً."
            )
            return

        msg = f"حذف مجموعة «{ds['name']}»؟"
        if fields_cnt:
            msg += f"\n⚠️ تحتوي على {fields_cnt} حقل — سيتم حذفها جميعاً."

        if QMessageBox.question(
            self, "تأكيد الحذف", msg,
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            self._fields_panel.clear()
            delete_dimension_set(self.conn, sid)
            self._reset_form()
            self._load()

    def _reset_form(self):
        self._editing_id = None
        self.inp_name.clear()
        self.inp_notes.clear()
        self.cmb_category.setCurrentIndex(0)
        self.cmb_unit.setCurrentIndex(0)
        self.lbl_mode.setText("─── مجموعة جديدة ───")
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


# ══════════════════════════════════════════════════════════
# لوحة المجموعات الرئيسية
# ══════════════════════════════════════════════════════════

class _GroupsPanel(QWidget):
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

        self._cats_panel = _CategoriesPanel(self.conn)
        self._cats_panel.changed.connect(self._on_categories_changed)
        splitter.addWidget(self._cats_panel)

        self._sets_manager = _SetsManagerPanel(self.conn)
        splitter.addWidget(self._sets_manager)

        splitter.setSizes([280, 720])
        root.addWidget(splitter)

    def _on_categories_changed(self):
        self._sets_manager.refresh_categories()

    def refresh(self):
        self._cats_panel.refresh()
        self._sets_manager.refresh()