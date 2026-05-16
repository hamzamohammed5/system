"""
ui/tabs/design/dimension_sets/_categories_panel.py
=====================================
"""


from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit,
    QComboBox, QGroupBox,
    QFormLayout, QMessageBox, QColorDialog,
    QTreeWidget, QTreeWidgetItem,

)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui  import QColor

from db.designs.dimension_sets_repo import (
    fetch_all_design_categories, fetch_design_category,
    insert_design_category, update_design_category, delete_design_category,
    build_category_tree, fetch_category_descendants,
)
from ui.helpers import buttons_row, danger_button

# ══════════════════════════════════════════════════════════
# لوحة إدارة التصنيفات — تُستخدم داخل _GroupsPanel
# ══════════════════════════════════════════════════════════

class _CategoriesPanel(QWidget):
    """
    إدارة كاملة لتصنيفات التصميمات:
      - شجرة عرض التصنيفات الهرمية
      - فورم إضافة / تعديل (الاسم، اللون، التصنيف الأب)
      - حذف مع تحذير
    """

    changed = pyqtSignal()   # يُطلق بعد أي تغيير للتصنيفات

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._editing_id = None
        self._color      = "#1565c0"
        self._build()
        self._load_tree()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        hdr = QLabel("📁  تصنيفات التصميمات")
        hdr.setStyleSheet("""
            font-weight: bold; font-size: 13px; color: #1565c0;
            background: #e8f0fe; border-radius: 6px; padding: 6px 12px;
        """)
        root.addWidget(hdr)

        # ── الشجرة ──
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["التصنيف", "عدد المجموعات"])
        self.tree.setColumnWidth(0, 200)
        self.tree.setColumnWidth(1, 80)
        self.tree.setAlternatingRowColors(True)
        self.tree.setAnimated(True)
        root.addWidget(self.tree, stretch=1)

        # أزرار الشجرة
        btn_edit_cat = QPushButton("✏️  تعديل")
        btn_del_cat  = danger_button("🗑️  حذف")
        for b in (btn_edit_cat, btn_del_cat):
            b.setMinimumHeight(28)
        btn_edit_cat.clicked.connect(self._edit_category)
        btn_del_cat.clicked.connect(self._delete_category)
        root.addLayout(buttons_row(btn_edit_cat, btn_del_cat))

        # ── فورم إضافة / تعديل ──
        grp  = QGroupBox("بيانات التصنيف")
        form = QFormLayout(grp)
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = QLabel("─── تصنيف جديد ───")
        self.lbl_mode.setStyleSheet("font-weight: bold; color: #1565c0;")
        form.addRow(self.lbl_mode)

        self.inp_cat_name = QLineEdit()
        self.inp_cat_name.setPlaceholderText("اسم التصنيف...")
        self.inp_cat_name.setMinimumHeight(30)
        form.addRow("الاسم :", self.inp_cat_name)

        self.cmb_parent = QComboBox()
        self.cmb_parent.setMinimumHeight(28)
        form.addRow("تابع لـ :", self.cmb_parent)

        # اللون
        color_row = QHBoxLayout()
        self.lbl_color = QLabel()
        self.lbl_color.setFixedSize(28, 28)
        self._update_color_preview()
        btn_color = QPushButton("اختر لون")
        btn_color.setMinimumHeight(28)
        btn_color.clicked.connect(self._pick_color)
        color_row.addWidget(self.lbl_color)
        color_row.addWidget(btn_color)
        color_row.addStretch()
        form.addRow("اللون :", color_row)

        self.btn_cat_add    = QPushButton("➕  إضافة")
        self.btn_cat_save   = QPushButton("💾  حفظ")
        self.btn_cat_cancel = QPushButton("✖  إلغاء")
        self.btn_cat_save.setVisible(False)
        self.btn_cat_cancel.setVisible(False)
        for b in (self.btn_cat_add, self.btn_cat_save, self.btn_cat_cancel):
            b.setMinimumHeight(30)
        self.btn_cat_add.clicked.connect(self._add_category)
        self.btn_cat_save.clicked.connect(self._save_category)
        self.btn_cat_cancel.clicked.connect(self._reset_form)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.btn_cat_add)
        btn_row.addWidget(self.btn_cat_save)
        btn_row.addWidget(self.btn_cat_cancel)
        form.addRow(btn_row)
        root.addWidget(grp)

        self._reload_parent_combo()

    # ── شجرة التصنيفات ──

    def _load_tree(self):
        expanded = set()

        def _collect(item):
            if item.isExpanded():
                expanded.add(item.data(0, Qt.UserRole))
            for i in range(item.childCount()):
                _collect(item.child(i))

        for i in range(self.tree.topLevelItemCount()):
            _collect(self.tree.topLevelItem(i))

        self.tree.clear()
        rows = fetch_all_design_categories(self.conn)
        tree = build_category_tree(rows)
        self._add_tree_nodes(tree, parent=None, expanded=expanded)
        self.tree.expandAll()

    def _add_tree_nodes(self, nodes, parent, expanded):
        for node in nodes:
            item = QTreeWidgetItem()
            item.setText(0, node["name"])
            item.setData(0, Qt.UserRole, node["id"])
            item.setForeground(0, QColor(node["color"]))

            # عدد المجموعات المرتبطة
            cnt = self.conn.execute(
                "SELECT COUNT(*) as c FROM dimension_sets WHERE category_id=?",
                (node["id"],)
            ).fetchone()["c"]
            item.setText(1, str(cnt) if cnt else "—")

            if parent is None:
                self.tree.addTopLevelItem(item)
            else:
                parent.addChild(item)

            if node["id"] in expanded:
                item.setExpanded(True)

            if node["children"]:
                self._add_tree_nodes(node["children"], item, expanded)

    def _selected_cat_id(self):
        items = self.tree.selectedItems()
        return items[0].data(0, Qt.UserRole) if items else None

    # ── فورم التصنيف ──

    def _reload_parent_combo(self, exclude_id=None):
        self.cmb_parent.blockSignals(True)
        self.cmb_parent.clear()
        self.cmb_parent.addItem("— بدون أب (رئيسي) —", None)
        rows = fetch_all_design_categories(self.conn)
        tree = build_category_tree(rows)
        excluded = set()
        if exclude_id is not None:
            excluded = set(fetch_category_descendants(self.conn, exclude_id))
        self._add_parent_nodes(tree, 0, excluded)
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
            self._update_color_preview()

    def _update_color_preview(self):
        self.lbl_color.setStyleSheet(
            f"background:{self._color}; border-radius:4px; border:1px solid #ccc;"
        )

    def _add_category(self):
        name = self.inp_cat_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم التصنيف")
            return
        parent_id = self.cmb_parent.currentData()
        insert_design_category(self.conn, name, self._color, parent_id)
        self._reset_form()
        self._load_tree()
        self.changed.emit()

    def _edit_category(self):
        cat_id = self._selected_cat_id()
        if cat_id is None:
            QMessageBox.information(self, "تنبيه", "اختر تصنيفاً أولاً")
            return
        cat = fetch_design_category(self.conn, cat_id)
        if not cat:
            return
        self._editing_id = cat_id
        self._color      = cat["color"]
        self.inp_cat_name.setText(cat["name"])
        self._update_color_preview()
        self._reload_parent_combo(exclude_id=cat_id)
        for i in range(self.cmb_parent.count()):
            if self.cmb_parent.itemData(i) == cat["parent_id"]:
                self.cmb_parent.setCurrentIndex(i)
                break
        self.lbl_mode.setText(f"─── تعديل: {cat['name']} ───")
        self.btn_cat_add.setVisible(False)
        self.btn_cat_save.setVisible(True)
        self.btn_cat_cancel.setVisible(True)

    def _save_category(self):
        if self._editing_id is None:
            return
        name = self.inp_cat_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم التصنيف")
            return
        parent_id = self.cmb_parent.currentData()
        update_design_category(self.conn, self._editing_id, name, self._color, parent_id)
        self._reset_form()
        self._load_tree()
        self.changed.emit()

    def _delete_category(self):
        cat_id = self._selected_cat_id()
        if cat_id is None:
            QMessageBox.information(self, "تنبيه", "اختر تصنيفاً أولاً")
            return
        cat = fetch_design_category(self.conn, cat_id)
        if not cat:
            return

        # عدد المجموعات المرتبطة بهذا التصنيف وأبنائه
        descendants = fetch_category_descendants(self.conn, cat_id)
        placeholders = ",".join("?" * len(descendants))
        sets_count = self.conn.execute(
            f"SELECT COUNT(*) as c FROM dimension_sets WHERE category_id IN ({placeholders})",
            descendants
        ).fetchone()["c"]

        msg = f"حذف تصنيف «{cat['name']}»؟"
        child_count = len(descendants) - 1
        if child_count:
            msg += f"\n⚠️ يحتوي على {child_count} تصنيف فرعي — سيتم حذفها."
        if sets_count:
            msg += f"\n⚠️ {sets_count} مجموعة مقاسات ستفقد تصنيفها."

        if QMessageBox.question(
            self, "تأكيد الحذف", msg,
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            for did in sorted(descendants, reverse=True):
                delete_design_category(self.conn, did)
            self._load_tree()
            self.changed.emit()

    def _reset_form(self):
        self._editing_id = None
        self._color      = "#1565c0"
        self.inp_cat_name.clear()
        self._update_color_preview()
        self.lbl_mode.setText("─── تصنيف جديد ───")
        self.btn_cat_add.setVisible(True)
        self.btn_cat_save.setVisible(False)
        self.btn_cat_cancel.setVisible(False)
        self._reload_parent_combo()

    def refresh(self):
        self._load_tree()
        self._reload_parent_combo()

