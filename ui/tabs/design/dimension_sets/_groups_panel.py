"""
ui/tabs/design/dimension_sets/_groups_panel.py
=====================================
تبويب 'المجموعات':
  - يسار:  إدارة التصنيفات (_CategoriesPanel)
  - يمين:  إدارة مجموعات المقاسات (إضافة / تعديل / حذف dimension_sets)
            + جدول الحقول التابعة للمجموعة المختارة
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTableWidgetItem, QTableWidget, QHeaderView, QAbstractItemView,
    QLabel, QLineEdit, QComboBox, QGroupBox, QFormLayout,
    QPushButton, QMessageBox,
)
from PyQt5.QtCore import Qt

from db.designs.dimension_sets_repo import (
    fetch_all_dimension_sets,
    fetch_dimension_set,
    insert_dimension_set,
    update_dimension_set,
    delete_dimension_set,
    fetch_fields_for_set,
    fetch_all_design_categories,
    build_category_tree,
)
from ._categories_panel import _CategoriesPanel
from ui.helpers import make_table, danger_button, buttons_row


# ══════════════════════════════════════════════════════════
# لوحة إدارة المجموعات (يمين)
# ══════════════════════════════════════════════════════════

class _SetsManagerPanel(QWidget):
    """
    إدارة كاملة لمجموعات المقاسات (dimension_sets):
      - جدول المجموعات مع بحث وفلتر
      - فورم إضافة / تعديل
      - حذف مع تأكيد
      - جدول الحقول للمجموعة المختارة
    """

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

        # ── Splitter رأسي: جدول المجموعات ↕ جدول الحقول ──
        v_splitter = QSplitter(Qt.Vertical)
        v_splitter.setHandleWidth(5)
        v_splitter.setStyleSheet("""
            QSplitter::handle { background: #e0e0e0; }
            QSplitter::handle:hover { background: #bbdefb; }
        """)

        # جدول المجموعات
        top_w = QWidget()
        top_lay = QVBoxLayout(top_w)
        top_lay.setContentsMargins(0, 0, 0, 0)
        top_lay.setSpacing(4)

        self.table = make_table(
            ["ID", "اسم المجموعة", "التصنيف", "الوحدة", "عدد الحقول", "الحقول"],
            stretch_col=1
        )
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 55)
        self.table.setColumnWidth(4, 65)
        self.table.setColumnWidth(5, 180)
        self.table.itemSelectionChanged.connect(self._on_select)
        top_lay.addWidget(self.table)

        # أزرار المجموعات
        btn_edit = QPushButton("✏️  تعديل")
        btn_del  = danger_button("🗑️  حذف")
        for b in (btn_edit, btn_del):
            b.setMinimumHeight(28)
        btn_edit.clicked.connect(self._edit_set)
        btn_del.clicked.connect(self._delete_set)
        top_lay.addLayout(buttons_row(btn_edit, btn_del))

        v_splitter.addWidget(top_w)

        # جدول الحقول للمجموعة المختارة
        bot_w = QWidget()
        bot_lay = QVBoxLayout(bot_w)
        bot_lay.setContentsMargins(0, 0, 0, 0)
        bot_lay.setSpacing(4)

        self.lbl_fields_hdr = QLabel("الحقول — (اختر مجموعة)")
        self.lbl_fields_hdr.setStyleSheet(
            "font-weight: bold; color: #555; font-size: 11px;"
        )
        bot_lay.addWidget(self.lbl_fields_hdr)

        self.fields_table = make_table(
            ["الترتيب", "الاسم", "التسمية", "الوحدة", "النوع", "إلزامي", "يعتمد على"],
            stretch_col=2
        )
        self.fields_table.setColumnWidth(0, 55)
        self.fields_table.setColumnWidth(1, 90)
        self.fields_table.setColumnWidth(3, 55)
        self.fields_table.setColumnWidth(4, 55)
        self.fields_table.setColumnWidth(5, 55)
        self.fields_table.setColumnWidth(6, 160)
        bot_lay.addWidget(self.fields_table)

        v_splitter.addWidget(bot_w)
        v_splitter.setSizes([280, 200])

        root.addWidget(v_splitter, stretch=1)

        # ── فورم إضافة / تعديل ──
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

        btn_row = QHBoxLayout()
        self.btn_add    = QPushButton("➕  إضافة")
        self.btn_save   = QPushButton("💾  حفظ")
        self.btn_cancel = QPushButton("✖  إلغاء")
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        for b in (self.btn_add, self.btn_save, self.btn_cancel):
            b.setMinimumHeight(30)
        self.btn_add.clicked.connect(self._add_set)
        self.btn_save.clicked.connect(self._save_set)
        self.btn_cancel.clicked.connect(self._reset_form)
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_cancel)
        form.addRow(btn_row)

        root.addWidget(self._form_grp)

        self._reload_cat_combos()

    # ── تحميل البيانات ──

    def _reload_cat_combos(self):
        """تحديث كومبو التصنيفات في الفلتر والفورم."""
        rows = fetch_all_design_categories(self.conn)
        tree = build_category_tree(rows)

        # فلتر
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

        # فورم
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

            fields      = fetch_fields_for_set(self.conn, ds["id"])
            cnt         = len(fields)
            field_names = "، ".join(f["label"] for f in fields[:5])
            if cnt > 5:
                field_names += f" ... (+{cnt - 5})"

            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(ds["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(ds["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(ds["category_name"] or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(ds["default_unit"] or "cm"))
            self.table.setItem(r, 4, QTableWidgetItem(str(cnt)))
            self.table.setItem(r, 5, QTableWidgetItem(field_names))
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
        if sid is None:
            self.fields_table.setRowCount(0)
            self.lbl_fields_hdr.setText("الحقول — (اختر مجموعة)")
            return
        ds = fetch_dimension_set(self.conn, sid)
        name = ds["name"] if ds else str(sid)
        self.lbl_fields_hdr.setText(f"حقول مجموعة: {name}")
        self._load_fields(sid)

    def _load_fields(self, set_id: int):
        self.fields_table.setRowCount(0)
        fields = fetch_fields_for_set(self.conn, set_id)
        for f in fields:
            r = self.fields_table.rowCount()
            self.fields_table.insertRow(r)
            self.fields_table.setItem(r, 0, QTableWidgetItem(str(f["sort_order"] + 1)))
            self.fields_table.setItem(r, 1, QTableWidgetItem(f["name"]))
            self.fields_table.setItem(r, 2, QTableWidgetItem(f["label"]))
            self.fields_table.setItem(r, 3, QTableWidgetItem(f["unit"] or "cm"))
            self.fields_table.setItem(r, 4, QTableWidgetItem(
                "رقم" if f["field_type"] == "number" else "نص"
            ))
            self.fields_table.setItem(r, 5, QTableWidgetItem("✓" if f["required"] else ""))

            dep_text = ""
            if f["source_field_id"]:
                sign    = "+" if f["dep_offset"] >= 0 else ""
                src_lbl = f["source_label"] or ""
                src_set = f.get("source_set_name") or ""
                dep_text = (
                    f"{src_lbl} ({src_set}) {sign}{f['dep_offset']:g}"
                    if src_set else
                    f"{src_lbl} {sign}{f['dep_offset']:g}"
                )
            self.fields_table.setItem(r, 6, QTableWidgetItem(dep_text))

    # ── عمليات CRUD ──

    def _add_set(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم المجموعة")
            return
        cat_id = self.cmb_category.currentData()
        unit   = self.cmb_unit.currentText().strip() or "cm"
        notes  = self.inp_notes.text().strip()
        insert_dimension_set(self.conn, name, cat_id, unit, notes)
        self._reset_form()
        self._load()

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

        # اختيار التصنيف
        for i in range(self.cmb_category.count()):
            if self.cmb_category.itemData(i) == ds["category_id"]:
                self.cmb_category.setCurrentIndex(i)
                break

        # اختيار الوحدة
        unit = ds["default_unit"] or "cm"
        idx = self.cmb_unit.findText(unit)
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

        # عدد الحقول والتصميمات المرتبطة
        fields_cnt = self.conn.execute(
            "SELECT COUNT(*) as c FROM dimension_fields WHERE set_id=?", (sid,)
        ).fetchone()["c"]
        designs_cnt = self.conn.execute(
            "SELECT COUNT(*) as c FROM design_dimensions WHERE set_id=?", (sid,)
        ).fetchone()["c"]

        msg = f"حذف مجموعة «{ds['name']}»؟"
        if fields_cnt:
            msg += f"\n⚠️ تحتوي على {fields_cnt} حقل — سيتم حذفها."
        if designs_cnt:
            msg += f"\n⚠️ مرتبطة بـ {designs_cnt} تصميم — لا يمكن الحذف."
            QMessageBox.warning(self, "تعذر الحذف", msg)
            return

        if QMessageBox.question(
            self, "تأكيد الحذف", msg,
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
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
        """يُستدعى لما تتغير التصنيفات."""
        self._reload_cat_combos()
        self._load()

    def refresh(self):
        self._load()


# ══════════════════════════════════════════════════════════
# لوحة المجموعات الرئيسية
# ══════════════════════════════════════════════════════════

class _GroupsPanel(QWidget):
    """
    تبويب 'المجموعات':
      - يسار:  إدارة التصنيفات (_CategoriesPanel)
      - يمين:  إدارة مجموعات المقاسات (_SetsManagerPanel)
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

        # ── يمين: إدارة المجموعات ──
        self._sets_manager = _SetsManagerPanel(self.conn)
        splitter.addWidget(self._sets_manager)

        splitter.setSizes([300, 700])
        root.addWidget(splitter)

    def _on_categories_changed(self):
        """لما تتغير التصنيفات، نحدّث كومبو التصنيفات في مدير المجموعات."""
        self._sets_manager.refresh_categories()

    def refresh(self):
        self._cats_panel.refresh()
        self._sets_manager.refresh()