"""
ui/widgets/shared/category_combo.py
=============================
CategoryCombo — QComboBox يعرض التصنيفات بشكل هرمي (indent).

[إصلاح v2]:
  - Qt.ForegroundRole بدل Qt.ForegroundRole (كان صح لكن نوحد الأسلوب).
  - _add_nodes مشتركة مع منطق filter_toolbar لتجنب التكرار.
"""

from PyQt5.QtWidgets import QComboBox
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QColor

from db.shared.categories_repo import fetch_all_categories, build_tree
from ui.widgets.shared.connection_mixin import LiveConnMixin
from ui.events import bus


def _populate_category_combo(combo: QComboBox, conn,
                              scope: str = "all",
                              all_label: str = "— الكل —") -> None:
    """
    دالة مساعدة مشتركة لملء أي QComboBox بالتصنيفات الهرمية.
    تُستخدم من CategoryCombo وأي widget آخر يحتاج نفس المنطق.

    combo     : الـ QComboBox المطلوب ملؤه
    conn      : connection قاعدة البيانات
    scope     : نطاق التصنيفات
    all_label : نص الخيار الأول (None = لا يضيف خيار "الكل")
    """
    if all_label:
        combo.addItem(all_label, None)

    try:
        rows = fetch_all_categories(conn, scope)
    except Exception:
        return

    tree = build_tree(rows)
    _add_tree_nodes(combo, tree, depth=0)


def _add_tree_nodes(combo: QComboBox, nodes: list, depth: int) -> None:
    """يضيف عقد الشجرة في الـ combo بشكل هرمي."""
    indent = "    " * depth
    arrow  = "↳ " if depth > 0 else ""
    for node in nodes:
        combo.addItem(f"{indent}{arrow}{node['name']}", node["id"])
        idx = combo.count() - 1
        combo.setItemData(idx, QColor(node["color"]), Qt.ForegroundRole)
        if node["children"]:
            _add_tree_nodes(combo, node["children"], depth + 1)


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

        _populate_category_combo(self, conn, self.scope)

        # استعادة الاختيار السابق
        for i in range(self.count()):
            if self.itemData(i) == prev:
                self.setCurrentIndex(i)
                break
        self.blockSignals(False)

    def get_category(self):
        return self.currentData()

    def set_category(self, cat_id):
        for i in range(self.count()):
            if self.itemData(i) == cat_id:
                self.setCurrentIndex(i)
                return
        self.setCurrentIndex(0)