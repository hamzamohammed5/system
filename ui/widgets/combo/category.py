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
  - [WidgetMixin] استبدال weakref وربط bus يدوي بـ WidgetMixin._init_widget_mixin.
"""
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QColor
from ui.widgets.panels.themed_inputs import ThemedComboBox

from ..core.conn              import LiveConnMixin
from ..utils.signals          import blocked_signals
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.widgets.core.i18n     import tr


def populate_category_combo(combo: ThemedComboBox, conn,
                             scope: str = "all",
                             all_label: str = None) -> None:
    """
    يملأ أي QComboBox بالتصنيفات الهرمية.
    تُستخدم من CategoryCombo وأي widget آخر.

    [إصلاح هيكلة] يستخدم CategoryService بدل db import مباشر.
    [i18n] all_label الافتراضي بقى tr('filter_all') بدل النص المكتوب مباشرة.
    """
    if all_label is None:
        all_label = tr('filter_all')
    if all_label:
        combo.addItem(all_label, None)
        from ui.theme import _C
        combo.setItemData(0, QColor(_C['bg_input']), Qt.BackgroundRole)

    try:
        from services.shared.category_service import CategoryService
        svc   = CategoryService(conn)
        rows  = svc.get_all(scope)
        nodes = svc.build_tree(rows)
    except Exception:
        return

    _add_nodes(combo, nodes, depth=0)


def _add_nodes(combo: ThemedComboBox, nodes: list, depth: int) -> None:
    from ui.theme import _C
    indent = "    " * depth
    arrow  = tr('tree_node_arrow') if depth > 0 else ""
    for node in nodes:
        combo.addItem(f"{indent}{arrow}{node['name']}", node["id"])
        idx = combo.count() - 1
        combo.setItemData(idx, QColor(node["color"]), Qt.ForegroundRole)
        # [إصلاح خلفية سوداء عند الاختيار] بدون تحديد BackgroundRole صراحة،
        # بعض توليفات Qt/Windows بترسم خلفية التحديد بمحرك الرسم الأصلي
        # للنظام بدل الـ QSS (selection-background-color)، وده بيتعارض
        # مع الـ ForegroundRole المخصص فوق فبيطلع تباين غامق/أسود تقريباً.
        # تحديد خلفية فاتحة ثابتة من الثيم هنا يمنع الاعتماد على أي رسم
        # افتراضي غير متوقع.
        combo.setItemData(idx, QColor(_C['bg_input']), Qt.BackgroundRole)
        if node["children"]:
            _add_nodes(combo, node["children"], depth + 1)


class CategoryCombo(ThemedComboBox, LiveConnMixin, WidgetMixin):
    """
    QComboBox للتصنيفات الهرمية مع تحديث تلقائي.

    [إصلاح 2] يسمع لـ company_data_changed فقط (data_changed محذوف).
    [إصلاح هيكلة] يستخدم CategoryService عبر populate_category_combo.
    [WidgetMixin] ربط bus عبر _init_widget_mixin بدل weakref يدوي.
    [i18n] lang=True مضاف لأن populate_category_combo/_add_nodes بقيا يستخدما tr()
           (filter_all + tree_node_arrow)، فلازم الكومبو يتحدث عند تغيير اللغة.
    """

    def __init__(self, conn, scope: str = "all", parent=None):
        super().__init__(parent)
        self.conn  = conn
        self.scope = scope
        self.refresh()

        self._init_widget_mixin(theme=False, font=False, lang=True, data=True)

    def _refresh_data(self, company_id=None):
        self.refresh()

    def _refresh_lang(self, *_):
        self.refresh()

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