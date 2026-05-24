"""
ui/widgets/shared/category_manager.py
===============================
CategoryManager — شجرة QTreeWidget لإدارة التصنيفات الهرمية.

[تحسين]: استخدام confirm_delete بدل QMessageBox.question المباشر.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem,
    QMessageBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.shared.categories_repo import (
    fetch_all_categories, fetch_category,
    delete_category, count_category_items,
    build_tree, fetch_descendants,
)
from ui.widgets.shared.connection_mixin import LiveConnMixin
from ui.widgets.shared.panels import _make_btn, confirm_delete, get_tree_style
from ui.events import bus

# إعادة تصدير للتوافق مع الكود القديم
from ui.widgets.shared.category_combo import CategoryCombo          # noqa: F401
from ui.widgets.shared.category_form  import _CategoryForm          # noqa: F401


class CategoryManager(QWidget, LiveConnMixin):
    def __init__(self, conn, scope: str = "all", parent=None):
        super().__init__(parent)
        self.conn  = conn
        self.scope = scope
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

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

        btn_row = QHBoxLayout()
        btn_edit = _make_btn("✏️  تعديل", "normal")
        btn_del  = _make_btn("🗑️  حذف", "danger")
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        btn_row.addWidget(btn_edit)
        btn_row.addWidget(btn_del)
        btn_row.addStretch()
        root.addLayout(btn_row)

        self._form = _CategoryForm(self.conn, self.scope, self.tree)
        root.addWidget(self._form)

    # ══════════════════════════════════════════════════════
    # تحميل البيانات
    # ══════════════════════════════════════════════════════

    def _load(self):
        try:
            conn = self._live_conn()
        except Exception:
            return

        expanded = set()

        def _collect_expanded(item):
            if item.isExpanded():
                expanded.add(item.data(0, Qt.UserRole))
            for i in range(item.childCount()):
                _collect_expanded(item.child(i))

        for i in range(self.tree.topLevelItemCount()):
            _collect_expanded(self.tree.topLevelItem(i))

        self.tree.clear()

        try:
            rows = fetch_all_categories(conn, self.scope)
        except Exception:
            return

        tree = build_tree(rows)
        self._add_tree_items(tree, parent=None, expanded=expanded, conn=conn)
        self.tree.expandAll()

    def _add_tree_items(self, nodes, parent, expanded, conn):
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
                self._add_tree_items(node["children"], item, expanded, conn)

    # ══════════════════════════════════════════════════════
    # إجراءات
    # ══════════════════════════════════════════════════════

    def _selected_id(self):
        items = self.tree.selectedItems()
        if not items:
            return None
        return items[0].data(0, Qt.UserRole)

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

        cat = fetch_category(conn, cat_id)
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

        # ── استخدام confirm_delete الموحد ──
        if confirm_delete(self, cat["name"], extra_msg=extra.strip()):
            for did in sorted(descendants, reverse=True):
                delete_category(conn, did)
            bus.data_changed.emit()