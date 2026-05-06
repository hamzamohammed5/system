"""
ui/widgets/category_manager.py
===============================
CategoryManager  — شجرة QTreeWidget لإدارة التصنيفات الهرمية.
CategoryCombo    — QComboBox بيعرض التصنيفات بشكل هرمي (indent).
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QTreeWidget, QTreeWidgetItem, QComboBox,
    QLineEdit, QPushButton, QLabel, QColorDialog,
    QMessageBox, QGroupBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.categories_repo import (
    fetch_all_categories, fetch_category,
    insert_category, update_category, delete_category,
    count_category_items, build_tree, fetch_descendants, SCOPES,
)
from ui.events import bus


# ══════════════════════════════════════════════════════════
# CategoryCombo — Combo هرمي
# ══════════════════════════════════════════════════════════

class CategoryCombo(QComboBox):
    """
    Combo يعرض التصنيفات بشكل هرمي:
      — الكل —
      رئيسي
        ↳ فرعي
          ↳ تحت-فرعي
    """
    def __init__(self, conn, scope: str = "all", parent=None):
        super().__init__(parent)
        self.conn  = conn
        self.scope = scope
        self.refresh()
        bus.data_changed.connect(self.refresh)

    def refresh(self):
        prev = self.currentData()
        self.blockSignals(True)
        self.clear()
        self.addItem("— الكل —", None)

        rows  = fetch_all_categories(self.conn, self.scope)
        tree  = build_tree(rows)
        self._add_nodes(tree, depth=0)

        # استعادة الاختيار السابق
        for i in range(self.count()):
            if self.itemData(i) == prev:
                self.setCurrentIndex(i)
                break
        self.blockSignals(False)

    def _add_nodes(self, nodes: list, depth: int):
        indent = "    " * depth
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            self.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            # لوّن النص بلون التصنيف
            idx = self.count() - 1
            self.setItemData(idx, QColor(node["color"]), Qt.ForegroundRole)
            if node["children"]:
                self._add_nodes(node["children"], depth + 1)

    def get_category(self):
        return self.currentData()

    def set_category(self, cat_id):
        for i in range(self.count()):
            if self.itemData(i) == cat_id:
                self.setCurrentIndex(i)
                return
        self.setCurrentIndex(0)


# ══════════════════════════════════════════════════════════
# فورم إضافة / تعديل تصنيف
# ══════════════════════════════════════════════════════════

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
        """يحدّث Combo الأب — يستثني التصنيف الحالي وأبناءه منعاً للدورة."""
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
        # اختار الأب الحالي
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


# ══════════════════════════════════════════════════════════
# CategoryManager — الشجرة الرئيسية
# ══════════════════════════════════════════════════════════

class CategoryManager(QWidget):
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

        # ── الشجرة ──
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["التصنيف", "الأبناء", "العناصر"])
        self.tree.setColumnWidth(0, 260)
        self.tree.setColumnWidth(1, 60)
        self.tree.setColumnWidth(2, 80)
        self.tree.setAlternatingRowColors(True)
        self.tree.setAnimated(True)
        self.tree.itemSelectionChanged.connect(self._on_select)
        root.addWidget(self.tree)

        # ── أزرار ──
        btn_row = QHBoxLayout()
        btn_edit = QPushButton("✏️  تعديل")
        btn_del  = QPushButton("🗑️  حذف")
        btn_del.setStyleSheet(
            "background:#c62828; color:white; border-radius:4px;"
        )
        for btn in (btn_edit, btn_del):
            btn.setMinimumHeight(30)
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        btn_row.addWidget(btn_edit)
        btn_row.addWidget(btn_del)
        btn_row.addStretch()
        root.addLayout(btn_row)

        # ── الفورم ──
        self._form = _CategoryForm(self.conn, self.scope, self.tree)
        root.addWidget(self._form)

    def _load(self):
        # احفظ العناصر المفتوحة
        expanded = set()
        def _collect_expanded(item):
            if item.isExpanded():
                expanded.add(item.data(0, Qt.UserRole))
            for i in range(item.childCount()):
                _collect_expanded(item.child(i))
        for i in range(self.tree.topLevelItemCount()):
            _collect_expanded(self.tree.topLevelItem(i))

        self.tree.clear()
        rows = fetch_all_categories(self.conn, self.scope)
        tree = build_tree(rows)
        self._add_tree_items(tree, parent=None, expanded=expanded)
        self.tree.expandAll()

    def _add_tree_items(self, nodes, parent, expanded):
        for node in nodes:
            item = QTreeWidgetItem()
            item.setText(0, node["name"])
            item.setData(0, Qt.UserRole, node["id"])
            item.setForeground(0, QColor(node["color"]))

            # عدد الأبناء المباشرين
            child_count = len(node["children"])
            item.setText(1, str(child_count) if child_count else "—")

            # عدد العناصر (items/ops)
            counts = count_category_items(self.conn, node["id"])
            total  = sum(counts.values())
            item.setText(2, str(total) if total else "—")

            if parent is None:
                self.tree.addTopLevelItem(item)
            else:
                parent.addChild(item)

            if node["id"] in expanded:
                item.setExpanded(True)

            if node["children"]:
                self._add_tree_items(node["children"], item, expanded)

    def _selected_id(self):
        items = self.tree.selectedItems()
        if not items:
            return None
        return items[0].data(0, Qt.UserRole)

    def _on_select(self):
        pass  # ممكن تضيف preview هنا لاحقاً

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
        cat = fetch_category(self.conn, cat_id)
        if not cat:
            return

        # تحقق من الأبناء والعناصر
        descendants = fetch_descendants(self.conn, cat_id)
        counts      = count_category_items(self.conn, cat_id)
        total_items = sum(counts.values())
        child_cats  = len(descendants) - 1  # بدون نفسه

        msg = f"حذف تصنيف «{cat['name']}»؟"
        if child_cats:
            msg += f"\n⚠️ يحتوي على {child_cats} تصنيف فرعي — سيتم حذفها جميعاً."
        if total_items:
            details = "، ".join(f"{v} {k}" for k, v in counts.items() if v)
            msg += f"\n⚠️ {details} ستفقد تصنيفها."

        if QMessageBox.question(
            self, "تأكيد الحذف", msg,
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            # احذف الأبناء أولاً (من الأعمق للأعلى)
            for did in sorted(descendants, reverse=True):
                delete_category(self.conn, did)
            bus.data_changed.emit()