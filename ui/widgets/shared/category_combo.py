"""
ui/widgets/shared/category_combo.py
=============================
CategoryCombo — QComboBox يعرض التصنيفات بشكل هرمي (indent).

يرث من LiveConnMixin بدل كتابة _live_conn يدوياً.
ملاحظة: الـ attribute هنا اسمه `conn` عشان يتوافق مع LiveConnMixin.
"""

from PyQt5.QtWidgets import QComboBox
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QColor

from db.shared.categories_repo import fetch_all_categories, build_tree
from ui.widgets.shared.connection_mixin import LiveConnMixin
from ui.events import bus


class CategoryCombo(QComboBox, LiveConnMixin):
    """
    Combo يعرض التصنيفات بشكل هرمي:
      — الكل —
      رئيسي
        ↳ فرعي
          ↳ تحت-فرعي
    """
    def __init__(self, conn, scope: str = "all", parent=None):
        super().__init__(parent)
        self.conn  = conn          # LiveConnMixin يقرأ self.conn
        self.scope = scope
        self.refresh()
        bus.data_changed.connect(self.refresh)

    # ── refresh ───────────────────────────────────────────

    def refresh(self):
        try:
            conn = self._live_conn()
        except Exception:
            return

        prev = self.currentData()
        self.blockSignals(True)
        self.clear()
        self.addItem("— الكل —", None)

        try:
            rows = fetch_all_categories(conn, self.scope)
        except Exception:
            self.blockSignals(False)
            return

        tree = build_tree(rows)
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