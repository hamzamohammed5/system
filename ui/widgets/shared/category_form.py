"""
ui/widgets/shared/category_form.py
============================
_CategoryForm — QGroupBox لإضافة وتعديل التصنيفات الهرمية.

[تحسين]: استخدام ColorPickerWidget و confirm_action بدل كود محلي مكرر.
"""

from PyQt5.QtWidgets import (
    QGroupBox, QFormLayout, QLineEdit, QPushButton,
    QLabel, QComboBox, QMessageBox, QHBoxLayout,
)
from PyQt5.QtCore import Qt

from db.shared.categories_repo import (
    fetch_all_categories, fetch_category,
    insert_category, update_category,
    build_tree, fetch_descendants,
)
from ui.widgets.shared.connection_mixin import LiveConnMixin
from ui.widgets.shared.color_picker_widget import ColorPickerWidget
from ui.events import bus


class _CategoryForm(QGroupBox, LiveConnMixin):
    def __init__(self, conn, scope: str, tree_widget, parent=None):
        super().__init__("بيانات التصنيف", parent)
        self.conn         = conn
        self.scope        = scope
        self._tree        = tree_widget
        self._editing_id  = None
        self._build()

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        from ui.widgets.shared.panles_helper.mode_label import ModeLabel
        from ui.widgets.shared.panles_helper.make_btn import _make_btn

        form = QFormLayout(self)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = ModeLabel(add_text="تصنيف جديد")
        form.addRow(self.lbl_mode)

        self.inp_name = QLineEdit()
        self.inp_name.setMinimumHeight(30)
        form.addRow("الاسم :", self.inp_name)

        self.cmb_parent = QComboBox()
        self.cmb_parent.setMinimumHeight(30)
        form.addRow("تابع لـ :", self.cmb_parent)

        # ── ColorPickerWidget الموحد ──
        self._color_picker = ColorPickerWidget(default="#607d8b")
        form.addRow("اللون :", self._color_picker)

        btn_row = QHBoxLayout()
        self.btn_add    = _make_btn("➕  إضافة", "primary")
        self.btn_save   = _make_btn("💾  حفظ", "success")
        self.btn_cancel = _make_btn("✖  إلغاء", "ghost")
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        self.btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self._reset)
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_cancel)
        form.addRow(btn_row)

        self._refresh_parent_combo()

    # ══════════════════════════════════════════════════════
    # تحميل التصنيفات الأب
    # ══════════════════════════════════════════════════════

    def _refresh_parent_combo(self, exclude_id: int = None):
        try:
            conn = self._live_conn()
        except Exception:
            return

        self.cmb_parent.blockSignals(True)
        self.cmb_parent.clear()
        self.cmb_parent.addItem("— بدون أب (رئيسي) —", None)

        try:
            rows = fetch_all_categories(conn, self.scope)
        except Exception:
            self.cmb_parent.blockSignals(False)
            return

        tree = build_tree(rows)

        excluded = set()
        if exclude_id is not None:
            try:
                excluded = set(fetch_descendants(conn, exclude_id))
            except Exception:
                pass

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

    # ══════════════════════════════════════════════════════
    # إجراءات
    # ══════════════════════════════════════════════════════

    def _add(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم التصنيف")
            return
        try:
            conn = self._live_conn()
        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))
            return
        parent_id = self.cmb_parent.currentData()
        insert_category(conn, name, self.scope,
                        self._color_picker.current_color(), parent_id)
        self._reset()
        bus.data_changed.emit()

    def _save(self):
        if self._editing_id is None:
            return
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم التصنيف")
            return
        try:
            conn = self._live_conn()
        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))
            return
        parent_id = self.cmb_parent.currentData()
        try:
            update_category(conn, self._editing_id, name,
                            self.scope, self._color_picker.current_color(), parent_id)
        except ValueError as e:
            QMessageBox.warning(self, "خطأ", str(e))
            return
        self._reset()
        bus.data_changed.emit()

    def load_for_edit(self, cat_id: int):
        try:
            conn = self._live_conn()
        except Exception:
            return
        cat = fetch_category(conn, cat_id)
        if not cat:
            return
        self._editing_id = cat_id
        self.inp_name.setText(cat["name"])
        self._color_picker.set_color(cat["color"])
        self._refresh_parent_combo(exclude_id=cat_id)
        for i in range(self.cmb_parent.count()):
            if self.cmb_parent.itemData(i) == cat["parent_id"]:
                self.cmb_parent.setCurrentIndex(i)
                break
        self.lbl_mode.set_edit_mode(cat["name"])
        self.btn_add.setVisible(False)
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)

    def _reset(self):
        self._editing_id = None
        self._color_picker.set_color("#607d8b")
        self.inp_name.clear()
        self.lbl_mode.set_add_mode()
        self.btn_add.setVisible(True)
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        self._refresh_parent_combo()