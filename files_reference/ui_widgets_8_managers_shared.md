# دليل الكود — UI / Widgets (8): Managers & Shared

> `ui/widgets/managers/` و `ui/widgets/shared/` — مدير التصنيفات والأقسام المشتركة.
> لـ MainWindow و SettingsDialog → راجع `ui_widgets_ui_root.md`

---

## فهرس هذا الجزء

| القسم | الملفات |
|-------|---------|
| [CategoryManager](#categorymanager) | `widgets/managers/category.py` |
| [SharedItemsListPanel](#shareditemslistpanel) | `widgets/shared/list_panel_with_shared.py` |

---

## CategoryManager

### `ui/widgets/managers/category.py`

```python
CategoryManager(conn, scope="all")
# يستمع لـ bus.data_changed + bus.language_changed
# يستخدم _live_conn() مرة واحدة لكل action
# عناوين الأعمدة والأزرار من tr()

CategoryForm(conn, scope, tree_widget)
  .load_for_edit(cat_id: int)
# يشترك في bus.language_changed لتحديث نصوص الـ groupbox والأزرار
# _refresh_parent_combo(conn=None, exclude_id=None)
```

**ملاحظة [Q-03]:** كل action يُجري `_live_conn()` مرة واحدة فقط ويُمررها للدوال الفرعية.

---

## SharedItemsListPanel

### `ui/widgets/shared/list_panel_with_shared.py` — `SharedItemsListPanel`

قاعدة مشتركة للجداول التي تدعم العناصر المشتركة/المنشورة.
يرث من `BaseListPanel + SharedOpsMixin + LiveConnMixin`.
العمود 0 يُخفى تلقائياً (`setColumnHidden(0, True)`) ويُستخدم لحمل الـ ID.

**إعدادات الـ subclass:**
```python
SHARED_TYPE:      str  = "raw"
TABLE_COLS:       list = []      # تُحوَّل لـ COLUMNS تلقائياً
TABLE_TITLE:      str  = ""      # يُسند لـ LIST_TITLE تلقائياً
HAS_BULK_REPLACE: bool = False   # يُظهر زر "استبدال شامل"
SHOW_CATEGORY:    bool = True
CONNECT_BUS:      bool = True
# STRETCH_COL يُضبط على 1 تلقائياً
```

**Hooks المطلوبة (override إلزامي):**
```python
_fetch_local_rows() -> list[dict]
_fill_table_row(r: int, item: dict)
_edit_item(item_id: int)
_delete_item(item_id: int, item_name: str)
```

**Hooks الاختيارية:**
```python
_get_shared_rows(local_rows: list) -> list[dict]   # افتراضياً: []
_get_item_data_for_publish(row: dict) -> dict       # افتراضياً: {}
_bulk_replace_item(item_id: int, item_name: str)
_setup_column_widths(table: QTableWidget)
_on_edit_shared()
# افتراضياً: يستدعي _edit_shared_item من SharedOpsMixin
```

**أزرار الهيدر (تُضاف تلقائياً):**
- `"🔄 استبدال شامل"` — يظهر فقط لو `HAS_BULK_REPLACE=True`
- `"✏️ تعديل المحدد"` — يستدعي `_edit_item`
- `"🗑️ حذف المحدد"` — يستدعي `_delete_item`
- `"🔗 تعديل المشترك"` — يستدعي `_on_edit_shared`
- `"📤 نشر كمشترك"` — يستدعي `_publish_item` من `SharedOpsMixin`

**التلوين التلقائي للصفوف:**
```python
# العناصر المشتركة (row["_is_shared"] = True):
#   fg = SHARED_COLOR, bg = SHARED_BG
# العناصر المنشورة (row["_is_published"] = True):
#   fg = PUBLISHED_COLOR, bg = PUBLISHED_BG
# من: ui/tabs/costing/shared/_utils.py
```

**مساعدات:**
```python
panel._selected_row_data() -> tuple[int | None, str]
panel._get_current_row_dict() -> dict | None
```

**مثال:**
```python
from ui.widgets.shared.list_panel_with_shared import SharedItemsListPanel
from ui.widgets.tables.items import make_item
from ui.widgets.core.i18n import tr

class RawMaterialsPanel(SharedItemsListPanel):
    SHARED_TYPE      = "raw"
    TABLE_COLS       = ["#", tr("name"), tr("price"), tr("category")]
    TABLE_TITLE      = tr("raw_materials")
    HAS_BULK_REPLACE = True

    def _fetch_local_rows(self):
        return fetch_items_by_type(self.conn, "raw")

    def _fill_table_row(self, r, item):
        self.table.setItem(r, 0, make_item(str(item["id"]), item["id"]))
        self.table.setItem(r, 1, make_item(item["name"]))
        self.table.setItem(r, 2, make_item(f"{item['price']:,.2f}"))
        self.table.setItem(r, 3, make_item(item.get("category_name", "─")))

    def _edit_item(self, item_id): ...
    def _delete_item(self, item_id, item_name): ...
```