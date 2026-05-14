"""
ui/widgets/shared/category_form.py
============================
_CategoryForm — QGroupBox لإضافة وتعديل التصنيفات الهرمية.
"""

from PyQt5.QtWidgets import (
    QGroupBox, QFormLayout, QLineEdit, QPushButton,
    QLabel, QComboBox, QColorDialog, QMessageBox, QHBoxLayout,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.categories_repo import (
    fetch_all_categories, fetch_category,
    insert_category, update_category,
    build_tree, fetch_descendants,
)
from ui.events import bus


class _CategoryForm(QGroupBox):
    def __init__(self, conn, scope: str, tree_widget, parent=None):
        super().__init__("بيانات التصنيف", parent)
        self.conn         = conn
        self.scope        = scope
        self._tree        = tree_widget
        self._editing_id  = None
        self._color       = "#607d8b"
        self._build()

    def _build(self):
        form = QFormLayout(self)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = QLabel("─── تصنيف جديد ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0;")
        form.addRow(self.lbl_mode)

        # الاسم
        self.inp_name = QLineEdit()
        self.inp_name.setMinimumHeight(30)
        form.addRow("الاسم :", self.inp_name)

        # التصنيف الأب
        self.cmb_parent = QComboBox()
        self.cmb_parent.setMinimumHeight(30)
        form.addRow("تابع لـ :", self.cmb_parent)

        # اللون
        color_row = QHBoxLayout()
        self.lbl_color = QLabel()
        self.lbl_color.setFixedSize(28, 28)
        self.lbl_color.setStyleSheet(
            f"background:{self._color}; border-radius:4px; border:1px solid #ccc;"
        )
        btn_color = QPushButton("اختر لون")
        btn_color.setMinimumHeight(28)
        btn_color.clicked.connect(self._pick_color)
        color_row.addWidget(self.lbl_color)
        color_row.addWidget(btn_color)
        color_row.addStretch()
        form.addRow("اللون :", color_row)

        # أزرار
        btn_row = QHBoxLayout()
        self.btn_add    = QPushButton("➕  إضافة")
        self.btn_save   = QPushButton("💾  حفظ")
        self.btn_cancel = QPushButton("✖  إلغاء")
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn.setMinimumHeight(30)
        self.btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self._reset)
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_cancel)
        form.addRow(btn_row)

        self._refresh_parent_combo()

    def _refresh_parent_combo(self, exclude_id: int = None):
        self.cmb_parent.blockSignals(True)
        self.cmb_parent.clear()
        self.cmb_parent.addItem("— بدون أب (رئيسي) —", None)

        rows = fetch_all_categories(self.conn, self.scope)
        tree = build_tree(rows)

        excluded = set()
        if exclude_id is not None:
            excluded = set(fetch_descendants(self.conn, exclude_id))

        self._add_parent_nodes(tree, depth=0, excluded=excluded)
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

    def _pick_color(self):
        col = QColorDialog.getColor(QColor(self._color), self, "اختر لون التصنيف")
        if col.isValid():
            self._color = col.name()
            self.lbl_color.setStyleSheet(
                f"background:{self._color}; border-radius:4px; border:1px solid #ccc;"
            )

    def _add(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم التصنيف")
            return
        parent_id = self.cmb_parent.currentData()
        insert_category(self.conn, name, self.scope, self._color, parent_id)
        self._reset()
        bus.data_changed.emit()

    def _save(self):
        if self._editing_id is None:
            return
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم التصنيف")
            return
        parent_id = self.cmb_parent.currentData()
        try:
            update_category(self.conn, self._editing_id, name,
                            self.scope, self._color, parent_id)
        except ValueError as e:
            QMessageBox.warning(self, "خطأ", str(e))
            return
        self._reset()
        bus.data_changed.emit()

    def load_for_edit(self, cat_id: int):
        cat = fetch_category(self.conn, cat_id)
        if not cat:
            return
        self._editing_id = cat_id
        self._color      = cat["color"]
        self.inp_name.setText(cat["name"])
        self.lbl_color.setStyleSheet(
            f"background:{self._color}; border-radius:4px; border:1px solid #ccc;"
        )
        self._refresh_parent_combo(exclude_id=cat_id)
        for i in range(self.cmb_parent.count()):
            if self.cmb_parent.itemData(i) == cat["parent_id"]:
                self.cmb_parent.setCurrentIndex(i)
                break
        self.lbl_mode.setText(f"─── تعديل: {cat['name']} ───")
        self.btn_add.setVisible(False)
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)

    def _reset(self):
        self._editing_id = None
        self._color      = "#607d8b"
        self.inp_name.clear()
        self.lbl_color.setStyleSheet(
            "background:#607d8b; border-radius:4px; border:1px solid #ccc;"
        )
        self.lbl_mode.setText("─── تصنيف جديد ───")
        self.btn_add.setVisible(True)
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        self._refresh_parent_combo()