"""
widgets/managers/category.py
=============================
CategoryManager — شجرة لإدارة التصنيفات الهرمية.
CategoryForm    — فورم إضافة/تعديل التصنيف.

دمج category_manager.py + category_form.py في ملف واحد.
التغييرات:
  - ColorPickerWidget مستوردة من widgets/helpers/color_picker
  - confirm_delete من widgets/dialogs/confirm
  - LiveConnMixin من widgets/core/conn
"""

from PyQt5.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout,
    QTreeWidget, QTreeWidgetItem, QLineEdit, QComboBox, QMessageBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.shared.categories_repo import (
    fetch_all_categories, fetch_category, insert_category,
    update_category, delete_category, count_category_items,
    build_tree, fetch_descendants,
)
from ..core.conn     import LiveConnMixin
from ..components.button  import make_btn
from ..dialogs.confirm import confirm_delete
from ..theme.styles import tree_style
from ..panels.form_parts import ModeLabel
from ui.events import bus

# ── CategoryForm ──────────────────────────────────────────

class CategoryForm(QGroupBox, LiveConnMixin):
    """فورم إضافة/تعديل التصنيف."""

    def __init__(self, conn, scope: str, tree_widget, parent=None):
        super().__init__("بيانات التصنيف", parent)
        self.conn        = conn
        self.scope       = scope
        self._tree       = tree_widget
        self._editing_id = None
        self._build()

    def _build(self):
        from ..helpers.color_picker import ColorPickerWidget

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

        self._color_picker = ColorPickerWidget(default="#607d8b")
        form.addRow("اللون :", self._color_picker)

        btn_row = QHBoxLayout()
        self.btn_add    = make_btn("➕  إضافة", "primary")
        self.btn_save   = make_btn("💾  حفظ",   "success")
        self.btn_cancel = make_btn("✖  إلغاء",  "ghost")
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        self.btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self._reset)
        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn_row.addWidget(btn)
        form.addRow(btn_row)

        self._refresh_parent_combo()

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

        excluded = set()
        if exclude_id is not None:
            try:
                excluded = set(fetch_descendants(conn, exclude_id))
            except Exception:
                pass

        self._add_parent_nodes(build_tree(rows), depth=0, excluded=excluded)
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
        insert_category(conn, name, self.scope,
                        self._color_picker.current_color(),
                        self.cmb_parent.currentData())
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
        try:
            update_category(conn, self._editing_id, name, self.scope,
                            self._color_picker.current_color(),
                            self.cmb_parent.currentData())
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


# ── CategoryManager ───────────────────────────────────────

class CategoryManager(QWidget, LiveConnMixin):
    """شجرة QTreeWidget لإدارة التصنيفات الهرمية."""

    def __init__(self, conn, scope: str = "all", parent=None):
        super().__init__(parent)
        self.conn  = conn
        self.scope = scope
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["التصنيف", "الأبناء", "العناصر"])
        self.tree.setColumnWidth(0, 260)
        self.tree.setColumnWidth(1, 60)
        self.tree.setColumnWidth(2, 80)
        self.tree.setAlternatingRowColors(True)
        self.tree.setAnimated(True)
        self.tree.setStyleSheet(get_tree_style())
        self.tree.itemSelectionChanged.connect(self._on_select)
        root.addWidget(self.tree)

        btn_row  = QHBoxLayout()
        btn_edit = make_btn("✏️  تعديل", "normal")
        btn_del  = make_btn("🗑️  حذف",   "danger")
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        btn_row.addWidget(btn_edit)
        btn_row.addWidget(btn_del)
        btn_row.addStretch()
        root.addLayout(btn_row)

        self._form = CategoryForm(self.conn, self.scope, self.tree)
        root.addWidget(self._form)

    def _load(self):
        try:
            conn = self._live_conn()
        except Exception:
            return

        expanded = set()

        def _collect(item):
            if item.isExpanded():
                expanded.add(item.data(0, Qt.UserRole))
            for i in range(item.childCount()):
                _collect(item.child(i))

        for i in range(self.tree.topLevelItemCount()):
            _collect(self.tree.topLevelItem(i))

        self.tree.clear()
        try:
            rows = fetch_all_categories(conn, self.scope)
        except Exception:
            return

        self._add_items(build_tree(rows), parent=None,
                        expanded=expanded, conn=conn)
        self.tree.expandAll()

    def _add_items(self, nodes, parent, expanded, conn):
        for node in nodes:
            item = QTreeWidgetItem()
            item.setText(0, node["name"])
            item.setData(0, Qt.UserRole, node["id"])
            item.setForeground(0, QColor(node["color"]))

            child_count = len(node["children"])
            item.setText(1, str(child_count) if child_count else "—")

            try:
                counts = count_category_items(conn, node["id"])
                total  = sum(counts.values())
            except Exception:
                total = 0
            item.setText(2, str(total) if total else "—")

            if parent is None:
                self.tree.addTopLevelItem(item)
            else:
                parent.addChild(item)

            if node["id"] in expanded:
                item.setExpanded(True)

            if node["children"]:
                self._add_items(node["children"], item, expanded, conn)

    def _selected_id(self):
        items = self.tree.selectedItems()
        return items[0].data(0, Qt.UserRole) if items else None

    def _on_select(self):
        pass

    def _edit(self):
        cat_id = self._selected_id()
        if cat_id is None:
            QMessageBox.information(self, "تنبيه", "اختر تصنيفاً أولاً")
            return
        self._form.load_for_edit(cat_id)

    def _delete(self):
        cat_id = self._selected_id()
        if cat_id is None:
            QMessageBox.information(self, "تنبيه", "اختر تصنيفاً أولاً")
            return
        try:
            conn = self._live_conn()
        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))
            return

        cat         = fetch_category(conn, cat_id)
        if not cat:
            return
        descendants = fetch_descendants(conn, cat_id)
        counts      = count_category_items(conn, cat_id)
        total_items = sum(counts.values())
        child_cats  = len(descendants) - 1

        extra = ""
        if child_cats:
            extra += f"⚠️ يحتوي على {child_cats} تصنيف فرعي — سيتم حذفها جميعاً.\n"
        if total_items:
            details = "، ".join(f"{v} {k}" for k, v in counts.items() if v)
            extra += f"⚠️ {details} ستفقد تصنيفها."

        if confirm_delete(self, cat["name"], extra_msg=extra.strip()):
            for did in sorted(descendants, reverse=True):
                delete_category(conn, did)
            bus.data_changed.emit()