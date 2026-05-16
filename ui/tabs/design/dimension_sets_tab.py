"""
ui/tabs/design/dimension_sets_tab.py
=====================================
تبويب إدارة مجموعات المقاسات.

يتضمن:
  - قائمة المجموعات (مع فلتر بالتصنيف)
  - فورم إضافة/تعديل المجموعة
  - محرر حقول المجموعة (الحقول + اعتمادياتها)
  - إدارة تصنيفات التصميمات
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QPushButton, QLabel, QLineEdit,
    QComboBox, QDoubleSpinBox, QCheckBox, QGroupBox,
    QFormLayout, QMessageBox, QColorDialog, QDialog,
    QDialogButtonBox, QTreeWidget, QTreeWidgetItem, QScrollArea,
    QSizePolicy, QFrame,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont

from db.designs.dimension_sets_repo import (
    fetch_all_design_categories, fetch_design_category,
    insert_design_category, update_design_category, delete_design_category,
    build_category_tree, fetch_category_descendants,
    fetch_all_dimension_sets, fetch_dimension_set,
    insert_dimension_set, update_dimension_set, delete_dimension_set,
    fetch_fields_for_set, fetch_field,
    insert_field, update_field, delete_field, reorder_fields,
    fetch_field_dep, set_field_dep, remove_field_dep,
)
from ui.helpers import make_table, buttons_row, confirm_delete, danger_button


def _spin(min_=None, max_=9999, dec=2):
    s = QDoubleSpinBox()
    s.setRange(min_ if min_ is not None else -99999, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(30)
    return s


# ══════════════════════════════════════════════════════════
# محرر حقل واحد — Dialog
# ══════════════════════════════════════════════════════════

class _FieldDialog(QDialog):
    """نافذة إضافة/تعديل حقل مقاسات."""

    def __init__(self, conn, set_id: int,
                 field_data=None, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self.set_id    = set_id
        self.field_id  = field_data["id"] if field_data else None
        self.setWindowTitle("تعديل حقل" if field_data else "إضافة حقل جديد")
        self.setMinimumWidth(420)
        self.setModal(True)
        self._build()
        if field_data:
            self._load(field_data)

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.inp_name  = QLineEdit()
        self.inp_name.setPlaceholderText("مثال: length, width ...")
        self.inp_name.setMinimumHeight(30)

        self.inp_label = QLineEdit()
        self.inp_label.setPlaceholderText("مثال: الطول، العرض ...")
        self.inp_label.setMinimumHeight(30)

        self.inp_unit = QLineEdit()
        self.inp_unit.setPlaceholderText("cm / mm / m ...")
        self.inp_unit.setText("cm")
        self.inp_unit.setMinimumHeight(30)

        self.cmb_type = QComboBox()
        self.cmb_type.addItem("رقم", "number")
        self.cmb_type.addItem("نص", "text")
        self.cmb_type.setMinimumHeight(30)

        self.chk_required = QCheckBox("حقل إلزامي")
        self.chk_required.setChecked(True)

        form.addRow("الاسم (إنجليزي) :", self.inp_name)
        form.addRow("التسمية (عربي) :",  self.inp_label)
        form.addRow("الوحدة :",           self.inp_unit)
        form.addRow("النوع :",            self.cmb_type)
        form.addRow("",                   self.chk_required)
        root.addLayout(form)

        # ── قسم الاعتمادية ──
        dep_grp = QGroupBox("اعتماد على حقل آخر (اختياري)")
        dep_grp.setCheckable(True)
        dep_grp.setChecked(False)
        dep_lay = QFormLayout(dep_grp)
        dep_lay.setSpacing(8)
        dep_lay.setLabelAlignment(Qt.AlignRight)

        self._dep_grp = dep_grp

        self.cmb_source = QComboBox()
        self.cmb_source.setMinimumHeight(28)
        self._load_source_fields()

        self.sp_offset = _spin(min_=-9999, max_=9999, dec=4)
        self.sp_offset.setValue(0)

        dep_lay.addRow("مصدر الحساب :", self.cmb_source)
        dep_lay.addRow("الإضافة / الخصم :", self.sp_offset)

        hint = QLabel("القيمة = قيمة الحقل المصدر + الإضافة")
        hint.setStyleSheet(
            "color:#1565c0; font-size:10px;"
            "background:#e8f0fe; border-radius:4px; padding:4px 8px;"
        )
        dep_lay.addRow(hint)
        root.addWidget(dep_grp)

        # ── أزرار ──
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("💾  حفظ")
        btns.button(QDialogButtonBox.Cancel).setText("✖  إلغاء")
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    def _load_source_fields(self):
        """تحميل الحقول المتاحة كمصدر (كل حقول نفس المجموعة ما عدا الحقل الحالي)."""
        self.cmb_source.clear()
        fields = fetch_fields_for_set(self.conn, self.set_id)
        for f in fields:
            if f["id"] == self.field_id:
                continue
            self.cmb_source.addItem(f["label"] or f["name"], f["id"])

    def _load(self, field_data):
        self.inp_name.setText(field_data["name"])
        self.inp_label.setText(field_data["label"])
        self.inp_unit.setText(field_data["unit"] or "cm")
        idx = self.cmb_type.findData(field_data["field_type"])
        if idx >= 0:
            self.cmb_type.setCurrentIndex(idx)
        self.chk_required.setChecked(bool(field_data["required"]))

        # الاعتمادية
        if self.field_id:
            dep = fetch_field_dep(self.conn, self.field_id)
            if dep:
                self._dep_grp.setChecked(True)
                for i in range(self.cmb_source.count()):
                    if self.cmb_source.itemData(i) == dep["source_field_id"]:
                        self.cmb_source.setCurrentIndex(i)
                        break
                self.sp_offset.setValue(float(dep["offset"]))

    def _save(self):
        name  = self.inp_name.text().strip()
        label = self.inp_label.text().strip()
        if not name or not label:
            QMessageBox.warning(self, "تنبيه", "أدخل الاسم والتسمية")
            return

        unit       = self.inp_unit.text().strip() or "cm"
        ftype      = self.cmb_type.currentData()
        required   = self.chk_required.isChecked()
        sort_order = 0

        if self.field_id:
            # تحديث ترتيب بناءً على الموجود
            f = fetch_field(self.conn, self.field_id)
            if f:
                sort_order = f["sort_order"]
            update_field(self.conn, self.field_id, name, label,
                         unit, ftype, required, sort_order)
        else:
            # أضف في آخر ترتيب
            existing = fetch_fields_for_set(self.conn, self.set_id)
            sort_order = len(existing)
            self.field_id = insert_field(
                self.conn, self.set_id, name, label, unit, ftype, required, sort_order
            )

        # الاعتمادية
        if self._dep_grp.isChecked() and self.cmb_source.count() > 0:
            src_id = self.cmb_source.currentData()
            if src_id:
                set_field_dep(self.conn, self.field_id, src_id, self.sp_offset.value())
        else:
            remove_field_dep(self.conn, self.field_id)

        self.accept()


# ══════════════════════════════════════════════════════════
# لوحة حقول المجموعة
# ══════════════════════════════════════════════════════════

class _FieldsPanel(QWidget):
    """محرر حقول مجموعة مقاسات."""

    fields_changed = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn   = conn
        self._set_id = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        hdr = QLabel("حقول المجموعة")
        hdr.setStyleSheet("font-weight:bold; color:#1565c0; font-size:12px;")
        root.addWidget(hdr)

        self.table = make_table(
            ["الترتيب", "الاسم", "التسمية", "الوحدة", "النوع", "إلزامي", "يعتمد على"],
            stretch_col=2
        )
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 90)
        self.table.setColumnWidth(3, 60)
        self.table.setColumnWidth(4, 55)
        self.table.setColumnWidth(5, 55)
        self.table.setColumnWidth(6, 100)
        root.addWidget(self.table)

        btn_add  = QPushButton("➕  إضافة حقل")
        btn_edit = QPushButton("✏️  تعديل")
        btn_del  = danger_button("🗑️  حذف")
        btn_up   = QPushButton("▲")
        btn_dn   = QPushButton("▼")
        for btn in (btn_add, btn_edit, btn_del, btn_up, btn_dn):
            btn.setMinimumHeight(28)
        btn_up.setFixedWidth(34)
        btn_dn.setFixedWidth(34)

        btn_add.clicked.connect(self._add_field)
        btn_edit.clicked.connect(self._edit_field)
        btn_del.clicked.connect(self._del_field)
        btn_up.clicked.connect(self._move_up)
        btn_dn.clicked.connect(self._move_down)

        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_edit)
        btn_row.addWidget(btn_del)
        btn_row.addStretch()
        btn_row.addWidget(btn_up)
        btn_row.addWidget(btn_dn)
        root.addLayout(btn_row)

    def load_set(self, set_id: int):
        self._set_id = set_id
        self._refresh()

    def clear(self):
        self._set_id = None
        self.table.setRowCount(0)

    def _refresh(self):
        if self._set_id is None:
            self.table.setRowCount(0)
            return
        self.table.setRowCount(0)
        fields = fetch_fields_for_set(self.conn, self._set_id)
        for f in fields:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(f["sort_order"] + 1)))
            self.table.setItem(r, 1, QTableWidgetItem(f["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(f["label"]))
            self.table.setItem(r, 3, QTableWidgetItem(f["unit"] or "cm"))
            self.table.setItem(r, 4, QTableWidgetItem(
                "رقم" if f["field_type"] == "number" else "نص"
            ))
            self.table.setItem(r, 5, QTableWidgetItem("✓" if f["required"] else ""))
            dep_text = ""
            if f["source_field_id"]:
                sign = "+" if f["dep_offset"] >= 0 else ""
                dep_text = f"{f['source_label']} {sign}{f['dep_offset']:g}"
            self.table.setItem(r, 6, QTableWidgetItem(dep_text))
            # حفظ الـ field_id في العمود الأول كـ UserRole
            self.table.item(r, 0).setData(Qt.UserRole, f["id"])

    def _selected_field_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _add_field(self):
        if self._set_id is None:
            QMessageBox.information(self, "تنبيه", "اختر مجموعة مقاسات أولاً")
            return
        dlg = _FieldDialog(self.conn, self._set_id, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._refresh()
            self.fields_changed.emit()

    def _edit_field(self):
        fid = self._selected_field_id()
        if fid is None:
            QMessageBox.information(self, "تنبيه", "اختر حقلاً أولاً")
            return
        f = fetch_field(self.conn, fid)
        dlg = _FieldDialog(self.conn, self._set_id, field_data=f, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._refresh()
            self.fields_changed.emit()

    def _del_field(self):
        fid = self._selected_field_id()
        if fid is None:
            QMessageBox.information(self, "تنبيه", "اختر حقلاً أولاً")
            return
        f = fetch_field(self.conn, fid)
        if f and confirm_delete(self, f["label"]):
            delete_field(self.conn, fid)
            self._refresh()
            self.fields_changed.emit()

    def _move_up(self):
        self._move(-1)

    def _move_down(self):
        self._move(1)

    def _move(self, direction: int):
        row = self.table.currentRow()
        new_row = row + direction
        if new_row < 0 or new_row >= self.table.rowCount():
            return
        # جمع الـ field_ids بالترتيب الحالي
        ids = []
        for r in range(self.table.rowCount()):
            ids.append(self.table.item(r, 0).data(Qt.UserRole))
        # تبديل
        ids[row], ids[new_row] = ids[new_row], ids[row]
        reorder_fields(self.conn, self._set_id, ids)
        self._refresh()
        self.table.selectRow(new_row)
        self.fields_changed.emit()


# ══════════════════════════════════════════════════════════
# لوحة مجموعات المقاسات
# ══════════════════════════════════════════════════════════

class _SetsPanel(QWidget):
    """قائمة مجموعات المقاسات + فورم الإضافة/التعديل."""

    set_selected = pyqtSignal(int)   # set_id

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._editing_id = None
        self._all_rows   = []
        self._build()
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        # ── فلتر ──
        filter_row = QHBoxLayout()
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 بحث...")
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

        # ── جدول ──
        self.table = make_table(
            ["ID", "الاسم", "التصنيف", "الوحدة", "عدد الحقول"],
            stretch_col=1
        )
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 60)
        self.table.setColumnWidth(4, 70)
        self.table.itemSelectionChanged.connect(self._on_select)
        root.addWidget(self.table)

        # ── أزرار ──
        btn_edit = QPushButton("✏️  تعديل")
        btn_del  = danger_button("🗑️  حذف")
        for b in (btn_edit, btn_del):
            b.setMinimumHeight(28)
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        root.addLayout(buttons_row(btn_edit, btn_del))

        # ── فورم الإضافة/التعديل ──
        grp  = QGroupBox("بيانات المجموعة")
        form = QFormLayout(grp)
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = QLabel("─── مجموعة جديدة ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0;")
        form.addRow(self.lbl_mode)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("مثال: مقاسات الثوب, مقاسات البنطلون ...")
        self.inp_name.setMinimumHeight(30)

        self.cmb_category = QComboBox()
        self.cmb_category.setMinimumHeight(28)

        self.inp_unit = QLineEdit()
        self.inp_unit.setText("cm")
        self.inp_unit.setFixedWidth(80)
        self.inp_unit.setMinimumHeight(28)

        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("ملاحظات...")
        self.inp_notes.setMinimumHeight(28)

        form.addRow("الاسم :",        self.inp_name)
        form.addRow("التصنيف :",      self.cmb_category)
        form.addRow("الوحدة الافتراضية :", self.inp_unit)
        form.addRow("ملاحظات :",      self.inp_notes)

        self.btn_add    = QPushButton("➕  إضافة")
        self.btn_save   = QPushButton("💾  حفظ")
        self.btn_cancel = QPushButton("✖  إلغاء")
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        for b in (self.btn_add, self.btn_save, self.btn_cancel):
            b.setMinimumHeight(30)
        self.btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self._reset)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_cancel)
        form.addRow(btn_row)
        root.addWidget(grp)

        self._reload_categories()

    def _reload_categories(self):
        for combo in (self.cmb_category, self.cmb_cat_filter):
            prev = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            if combo is self.cmb_cat_filter:
                combo.addItem("— كل التصنيفات —", None)
            else:
                combo.addItem("— بدون تصنيف —", None)
            rows = fetch_all_design_categories(self.conn)
            tree = build_category_tree(rows)
            self._add_cat_nodes(combo, tree, 0)
            for i in range(combo.count()):
                if combo.itemData(i) == prev:
                    combo.setCurrentIndex(i)
                    break
            combo.blockSignals(False)

    def _add_cat_nodes(self, combo, nodes, depth):
        indent = "    " * depth
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            combo.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            if node["children"]:
                self._add_cat_nodes(combo, node["children"], depth + 1)

    def _load(self):
        self._all_rows = list(fetch_all_dimension_sets(self.conn))
        self._reload_categories()
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
            # عدد الحقول
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
        # استعادة الاختيار
        if prev is not None:
            for r in range(self.table.rowCount()):
                if self.table.item(r, 0).data(Qt.UserRole) == prev:
                    self.table.selectRow(r)
                    break

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _on_select(self):
        sid = self._selected_id()
        if sid:
            self.set_selected.emit(sid)

    def _add(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم المجموعة")
            return
        insert_dimension_set(
            self.conn, name,
            category_id=self.cmb_category.currentData(),
            default_unit=self.inp_unit.text().strip() or "cm",
            notes=self.inp_notes.text().strip()
        )
        self._reset()
        self._load()

    def _edit(self):
        sid = self._selected_id()
        if sid is None:
            QMessageBox.information(self, "تنبيه", "اختر مجموعة أولاً")
            return
        ds = fetch_dimension_set(self.conn, sid)
        if not ds:
            return
        self._editing_id = sid
        self.inp_name.setText(ds["name"])
        self.inp_unit.setText(ds["default_unit"] or "cm")
        self.inp_notes.setText(ds["notes"] or "")
        for i in range(self.cmb_category.count()):
            if self.cmb_category.itemData(i) == ds["category_id"]:
                self.cmb_category.setCurrentIndex(i)
                break
        self.lbl_mode.setText(f"─── تعديل: {ds['name']} ───")
        self.btn_add.setVisible(False)
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)

    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل الاسم")
            return
        update_dimension_set(
            self.conn, self._editing_id, name,
            category_id=self.cmb_category.currentData(),
            default_unit=self.inp_unit.text().strip() or "cm",
            notes=self.inp_notes.text().strip()
        )
        self._reset()
        self._load()

    def _delete(self):
        sid = self._selected_id()
        if sid is None:
            QMessageBox.information(self, "تنبيه", "اختر مجموعة أولاً")
            return
        ds = fetch_dimension_set(self.conn, sid)
        if not ds:
            return
        # تحقق من وجود تصميمات تستخدم هذه المجموعة
        used = self.conn.execute(
            "SELECT COUNT(*) as c FROM design_dimensions WHERE set_id=?", (sid,)
        ).fetchone()["c"]
        if used:
            QMessageBox.warning(
                self, "تنبيه",
                f"المجموعة «{ds['name']}» مستخدمة في {used} تصميم — لا يمكن حذفها."
            )
            return
        if confirm_delete(self, ds["name"]):
            delete_dimension_set(self.conn, sid)
            self._load()

    def _reset(self):
        self._editing_id = None
        self.inp_name.clear()
        self.inp_unit.setText("cm")
        self.inp_notes.clear()
        self.cmb_category.setCurrentIndex(0)
        self.lbl_mode.setText("─── مجموعة جديدة ───")
        self.btn_add.setVisible(True)
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)

    def refresh(self):
        self._load()


# ══════════════════════════════════════════════════════════
# تبويب تصنيفات التصميمات
# ══════════════════════════════════════════════════════════

class _CategoriesPanel(QWidget):
    """إدارة تصنيفات التصميمات."""

    categories_changed = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._editing_id = None
        self._color      = "#1565c0"
        self._build()
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # ── الشجرة ──
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["التصنيف", "العناصر"])
        self.tree.setColumnWidth(0, 260)
        self.tree.setAlternatingRowColors(True)
        self.tree.setAnimated(True)
        root.addWidget(self.tree)

        btn_edit = QPushButton("✏️  تعديل")
        btn_del  = danger_button("🗑️  حذف")
        for b in (btn_edit, btn_del):
            b.setMinimumHeight(28)
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        root.addLayout(buttons_row(btn_edit, btn_del))

        # ── فورم ──
        grp  = QGroupBox("بيانات التصنيف")
        form = QFormLayout(grp)
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = QLabel("─── تصنيف جديد ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0;")
        form.addRow(self.lbl_mode)

        self.inp_name   = QLineEdit()
        self.inp_name.setMinimumHeight(30)
        self.cmb_parent = QComboBox()
        self.cmb_parent.setMinimumHeight(28)

        color_row = QHBoxLayout()
        self.lbl_color = QLabel()
        self.lbl_color.setFixedSize(28, 28)
        self._update_color_label()
        btn_color = QPushButton("لون")
        btn_color.setMinimumHeight(28)
        btn_color.clicked.connect(self._pick_color)
        color_row.addWidget(self.lbl_color)
        color_row.addWidget(btn_color)
        color_row.addStretch()

        self.inp_notes = QLineEdit()
        self.inp_notes.setMinimumHeight(28)

        form.addRow("الاسم :",    self.inp_name)
        form.addRow("تابع لـ :", self.cmb_parent)
        form.addRow("اللون :",    color_row)
        form.addRow("ملاحظات :", self.inp_notes)

        self.btn_add    = QPushButton("➕  إضافة")
        self.btn_save   = QPushButton("💾  حفظ")
        self.btn_cancel = QPushButton("✖  إلغاء")
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        for b in (self.btn_add, self.btn_save, self.btn_cancel):
            b.setMinimumHeight(30)
        self.btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self._reset)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_cancel)
        form.addRow(btn_row)
        root.addWidget(grp)

    def _update_color_label(self):
        self.lbl_color.setStyleSheet(
            f"background:{self._color}; border-radius:4px; border:1px solid #ccc;"
        )

    def _pick_color(self):
        col = QColorDialog.getColor(QColor(self._color), self, "اختر لوناً")
        if col.isValid():
            self._color = col.name()
            self._update_color_label()

    def _load(self):
        self.tree.clear()
        rows = fetch_all_design_categories(self.conn)
        tree = build_category_tree(rows)
        self._add_tree_nodes(tree, None)
        self.tree.expandAll()
        self._reload_parent_combo()

    def _add_tree_nodes(self, nodes, parent_item):
        for node in nodes:
            item = QTreeWidgetItem()
            item.setText(0, node["name"])
            item.setData(0, Qt.UserRole, node["id"])
            item.setForeground(0, QColor(node["color"]))
            cnt = self.conn.execute(
                "SELECT COUNT(*) as c FROM dimension_sets WHERE category_id=?",
                (node["id"],)
            ).fetchone()["c"]
            item.setText(1, str(cnt) if cnt else "—")
            if parent_item is None:
                self.tree.addTopLevelItem(item)
            else:
                parent_item.addChild(item)
            if node["children"]:
                self._add_tree_nodes(node["children"], item)

    def _reload_parent_combo(self, exclude_id=None):
        self.cmb_parent.blockSignals(True)
        self.cmb_parent.clear()
        self.cmb_parent.addItem("— بدون أب —", None)
        rows = fetch_all_design_categories(self.conn)
        tree = build_category_tree(rows)
        self._add_parent_nodes(tree, 0, exclude_id or set())
        self.cmb_parent.blockSignals(False)

    def _add_parent_nodes(self, nodes, depth, excluded):
        indent = "    " * depth
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            if node["id"] in excluded:
                continue
            self.cmb_parent.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            if node["children"]:
                self._add_parent_nodes(node["children"], depth + 1, excluded)

    def _selected_id(self):
        items = self.tree.selectedItems()
        return items[0].data(0, Qt.UserRole) if items else None

    def _add(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل الاسم")
            return
        insert_design_category(self.conn, name, self._color,
                               self.cmb_parent.currentData(),
                               self.inp_notes.text().strip())
        self._reset()
        self._load()
        self.categories_changed.emit()

    def _edit(self):
        cid = self._selected_id()
        if cid is None:
            QMessageBox.information(self, "تنبيه", "اختر تصنيفاً")
            return
        cat = fetch_design_category(self.conn, cid)
        if not cat:
            return
        self._editing_id = cid
        self._color = cat["color"]
        self.inp_name.setText(cat["name"])
        self.inp_notes.setText(cat["notes"] or "")
        self._update_color_label()
        excluded = set(fetch_category_descendants(self.conn, cid))
        self._reload_parent_combo(exclude_id=excluded)
        for i in range(self.cmb_parent.count()):
            if self.cmb_parent.itemData(i) == cat["parent_id"]:
                self.cmb_parent.setCurrentIndex(i)
                break
        self.lbl_mode.setText(f"─── تعديل: {cat['name']} ───")
        self.btn_add.setVisible(False)
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)

    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل الاسم")
            return
        update_design_category(self.conn, self._editing_id, name, self._color,
                               self.cmb_parent.currentData(),
                               self.inp_notes.text().strip())
        self._reset()
        self._load()
        self.categories_changed.emit()

    def _delete(self):
        cid = self._selected_id()
        if cid is None:
            QMessageBox.information(self, "تنبيه", "اختر تصنيفاً")
            return
        cat = fetch_design_category(self.conn, cid)
        if not cat:
            return
        if confirm_delete(self, cat["name"]):
            delete_design_category(self.conn, cid)
            self._load()
            self.categories_changed.emit()

    def _reset(self):
        self._editing_id = None
        self._color = "#1565c0"
        self.inp_name.clear()
        self.inp_notes.clear()
        self._update_color_label()
        self.lbl_mode.setText("─── تصنيف جديد ───")
        self.btn_add.setVisible(True)
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        self._reload_parent_combo()


# ══════════════════════════════════════════════════════════
# تبويب المقاسات الرئيسي
# ══════════════════════════════════════════════════════════

class DimensionSetsTab(QWidget):
    """التبويب الرئيسي لإدارة مجموعات المقاسات."""

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        inner_tabs = QTabWidget()

        # ── تبويب المجموعات + الحقول ──
        sets_widget = QWidget()
        sets_layout = QVBoxLayout(sets_widget)
        sets_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(5)
        splitter.setStyleSheet("""
            QSplitter::handle { background: #e0e0e0; }
            QSplitter::handle:hover { background: #bbdefb; }
        """)

        self._sets_panel   = _SetsPanel(self.conn)
        self._fields_panel = _FieldsPanel(self.conn)

        self._sets_panel.set_selected.connect(self._fields_panel.load_set)

        splitter.addWidget(self._sets_panel)
        splitter.addWidget(self._fields_panel)
        splitter.setSizes([380, 500])

        sets_layout.addWidget(splitter)
        inner_tabs.addTab(sets_widget, "📐  مجموعات المقاسات")

        # ── تبويب التصنيفات ──
        self._cats_panel = _CategoriesPanel(self.conn)
        self._cats_panel.categories_changed.connect(self._sets_panel.refresh)
        inner_tabs.addTab(self._cats_panel, "🏷️  تصنيفات المقاسات")

        root.addWidget(inner_tabs)