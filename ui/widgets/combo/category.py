"""
widgets/combo/category.py
==========================
CategoryCombo — QComboBox للتصنيفات الهرمية.

الإصلاحات:
  - [إصلاح 2] CategoryCombo يسمع لـ bus.company_data_changed فقط.
  - [FIX-14] Qt.UniqueConnection على كل ربط bus لمنع التسجيل المضاعف.
  - [إصلاح memory leak] استبدال lambda تحمل self بـ weakref.
  - [إصلاح هيكلة] استبدال imports مباشرة من db/ بـ CategoryService.
    القديم: from db.shared.categories_repo import fetch_all_categories, build_tree
    الجديد: from services.shared.category_service import CategoryService
            svc.get_all(scope) + svc.build_tree(rows)
    المسار الصحيح: widget → service → repo (db/)
  - [دمج events] حذف bus.data_changed — يستخدم company_data_changed فقط.
    القديم: bus.data_changed + bus.company_data_changed
    الجديد: bus.company_data_changed فقط
"""
import weakref

from PyQt5.QtWidgets import QComboBox
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QColor

from ..core.conn          import LiveConnMixin
from ..utils.signals      import blocked_signals
from ui.widgets.core.events import bus


def populate_category_combo(combo: QComboBox, conn,
                             scope: str = "all",
                             all_label: str = "— الكل —") -> None:
    """
    يملأ أي QComboBox بالتصنيفات الهرمية.
    تُستخدم من CategoryCombo وأي widget آخر.

    [إصلاح هيكلة] يستخدم CategoryService بدل db import مباشر.
    """
    if all_label:
        combo.addItem(all_label, None)

    try:
        from services.shared.category_service import CategoryService
        svc   = CategoryService(conn)
        rows  = svc.get_all(scope)
        nodes = svc.build_tree(rows)
    except Exception:
        return

    _add_nodes(combo, nodes, depth=0)


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

    [إصلاح 2] يسمع لـ company_data_changed فقط (data_changed محذوف).
    [FIX-14] Qt.UniqueConnection على كل ربط bus لمنع التسجيل المضاعف.
    [إصلاح memory leak] استخدام weakref بدل lambda.
    [إصلاح هيكلة] يستخدم CategoryService عبر populate_category_combo.
    """

    def __init__(self, conn, scope: str = "all", parent=None):
        super().__init__(parent)
        self.conn  = conn
        self.scope = scope
        self.refresh()

        # [دمج events] company_data_changed فقط — data_changed محذوف
        # [إصلاح memory leak] weakref بدل lambda
        _weak = weakref.ref(self)

        def _on_company_data_changed(_cid: int):
            obj = _weak()
            if obj is not None:
                obj.refresh()

        # نحفظ مرجع الـ slot لأن weakref لا يحمي الـ closure من الـ GC
        self._company_data_slot = _on_company_data_changed

        bus.company_data_changed.connect(
            self._company_data_slot, Qt.UniqueConnection
        )

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