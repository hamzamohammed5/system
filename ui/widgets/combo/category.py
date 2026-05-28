"""
widgets/combo/category.py
==========================
CategoryCombo — QComboBox للتصنيفات الهرمية.

الإصلاحات:
  - [إصلاح 2] CategoryCombo الآن يسمع لـ bus.company_data_changed
    الكود الجديد يبعت company_data_changed بدل data_changed،
    فالـ combo لم يكن يتحدث عند تغيير البيانات عبر النهج الجديد.
    الحل: ربط الاتنين معاً — data_changed للتوافق القديم،
    company_data_changed للنهج الجديد.
"""
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QColor

from db.shared.categories_repo import fetch_all_categories, build_tree
from ..core.conn          import LiveConnMixin
from ..utils.signals      import blocked_signals
from ui.events import bus


def populate_category_combo(combo: QComboBox, conn,
                             scope: str = "all",
                             all_label: str = "— الكل —") -> None:
    """
    يملأ أي QComboBox بالتصنيفات الهرمية.
    تُستخدم من CategoryCombo وأي widget آخر.
    """
    if all_label:
        combo.addItem(all_label, None)

    try:
        rows = fetch_all_categories(conn, scope)
    except Exception:
        return

    _add_nodes(combo, build_tree(rows), depth=0)


def _add_nodes(combo: QComboBox, nodes: list, depth: int) -> None:
    indent = "    " * depth
    arrow  = "↳ " if depth > 0 else ""
    for node in nodes:
        combo.addItem(f"{indent}{arrow}{node['name']}", node["id"])
        combo.setItemData(combo.count() - 1, QColor(node["color"]), Qt.ForegroundRole)
        if node["children"]:
            _add_nodes(combo, node["children"], depth + 1)


class CategoryCombo(QComboBox, LiveConnMixin):
    """
    QComboBox للتصنيفات الهرمية مع تحديث تلقائي.

    [إصلاح 2] يسمع الآن لـ company_data_changed إضافةً لـ data_changed.
    """

    def __init__(self, conn, scope: str = "all", parent=None):
        super().__init__(parent)
        self.conn  = conn
        self.scope = scope
        self.refresh()
        # تسمع فقط — لا تبعت
        bus.data_changed.connect(self.refresh)
        # [إصلاح 2] ربط bus.company_data_changed — النهج الجديد
        bus.company_data_changed.connect(lambda _: self.refresh())

    def refresh(self):
        try:
            conn = self._live_conn()
        except Exception:
            return

        prev = self.currentData()

        with blocked_signals(self):
            self.clear()
            populate_category_combo(self, conn, self.scope)

            for i in range(self.count()):
                if self.itemData(i) == prev:
                    self.setCurrentIndex(i)
                    break

    def get_category(self):
        return self.currentData()

    def set_category(self, cat_id):
        for i in range(self.count()):
            if self.itemData(i) == cat_id:
                self.setCurrentIndex(i)
                return
        self.setCurrentIndex(0)