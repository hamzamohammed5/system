"""
ui/tabs/inventory/inventory_items_tab.py
========================================
Facade للتوافق مع الكود القديم — يُعيد تصدير من items/

التقسيم الداخلي:
  items/_item_form.py   → _ItemForm
  items/_items_table.py → _ItemsTable
  items/_items_tab.py   → _ItemsTab
"""

from .items._item_form   import _ItemForm    # noqa: F401
from .items._items_table import _ItemsTable  # noqa: F401
from .items._items_tab   import _ItemsTab    # noqa: F401

__all__ = ["_ItemForm", "_ItemsTable", "_ItemsTab"]