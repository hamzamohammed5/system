"""
ui/tabs/accounting/tree/_tree_builder.py
==================================================
دوال مساعدة لبناء شجرة الحسابات وعرضها في QTreeWidget.

[تحديث v2]: الكود قُسِّم لملفين في نفس المجلد:
  - _tree_nodes.py   : rows_to_tree, filter_by_group, add_acc_nodes
  - _tree_headers.py : add_type_header

هذا الملف يُعيد تصدير كل الدوال للتوافق مع الكود الموجود.
"""

# re-export من الملفات الفرعية للتوافق مع الكود القديم
from ._tree_nodes   import rows_to_tree, filter_by_group, add_acc_nodes   # noqa: F401
from ._tree_headers import add_type_header                                  # noqa: F401