"""
ui/widgets/utils/tooltip.py
=======================================
دوال مساعدة موحدة للـ tooltips في الجداول والـ widgets.

[Refactor V3 — المرحلة 3] إضافة refresh_tooltips alias لتوحيد الوظيفة
المتوزعة سابقاً على هذا الملف وعلى tables/flexible.py.
"""
from PyQt5.QtWidgets import QTableWidget, QTreeWidget, QTreeWidgetItem


def apply_table_tooltips(table: QTableWidget,
                          cols: "list[int] | None" = None) -> None:
    """
    يضيف tooltip = النص الكامل لكل خلية في الجدول.

    cols: أعمدة محددة، أو None لكل الأعمدة.
    يُستدعى بعد ملء الجدول بالبيانات.
    """
    n_cols      = table.columnCount()
    target_cols = cols if cols is not None else list(range(n_cols))

    for r in range(table.rowCount()):
        for c in target_cols:
            item = table.item(r, c)
            if item and item.text() and not item.toolTip():
                item.setToolTip(item.text())


# alias موحّد — يُستخدم من tables/flexible.py بدل تعريف مكرر
refresh_tooltips = apply_table_tooltips


def apply_tree_tooltips(tree: QTreeWidget,
                         item: "QTreeWidgetItem | None" = None,
                         cols: "list[int] | None" = None,
                         recursive: bool = True) -> None:
    """
    يضيف tooltip = النص الكامل لكل عنصر في الشجرة.

    item     : عنصر محدد، أو None لكل العناصر.
    cols     : أعمدة محددة، أو None لكل الأعمدة.
    recursive: يشمل العناصر الفرعية.
    """
    n_cols      = tree.columnCount()
    target_cols = cols if cols is not None else list(range(n_cols))

    def _apply(node: QTreeWidgetItem):
        for c in target_cols:
            text = node.text(c)
            if text and not node.toolTip(c):
                node.setToolTip(c, text)
        if recursive:
            for i in range(node.childCount()):
                _apply(node.child(i))

    if item is not None:
        _apply(item)
    else:
        for i in range(tree.topLevelItemCount()):
            _apply(tree.topLevelItem(i))