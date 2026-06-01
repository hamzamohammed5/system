# دليل الكود — UI / Widgets (9): Managers & Shared

> `ui/widgets/managers/` و `ui/widgets/shared/` — مدير التصنيفات وقاعدة الجداول المشتركة.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [CategoryManager + CategoryForm](#categorymanager--categoryform) | `managers/category.py` |
| [SharedItemsListPanel](#shareditemslistpanel) | `shared/list_panel_with_shared.py` |

---

## CategoryManager + CategoryForm

### `ui/widgets/managers/category.py`

#### CategoryForm

```python
CategoryForm(conn, scope: str, tree_widget, parent=None)
# QGroupBox — فورم إضافة/تعديل تصنيف واحد
# يشترك في bus.language_changed لتحديث نصوص الـ groupbox والأزرار
# يستخدم CategoryService بدل db imports مباشرة [إصلاح هيكلة]
# [Q-03] _live_conn() مرة واحدة لكل action
```

**API:**
```python
.load_for_edit(cat_id: int)
# يملأ الحقول + يُحدّث cmb_parent (مع استثناء التصنيف وفروعه)
# يُبدّل الأزرار لـ edit mode
```

**الحقول:**
- `inp_name` — اسم التصنيف
- `cmb_parent` — التصنيف الأب (هرمي)
- `_color_picker` — ColorPickerWidget للاختيار اللوني

#### CategoryManager

```python
CategoryManager(conn, scope="all", parent=None)
# QWidget — شجرة QTreeWidget كاملة لإدارة التصنيفات
# يستمع لـ bus.data_changed + bus.language_changed
# يستخدم CategoryService بدل db imports مباشرة [إصلاح هيكلة]
```

**الأعمدة:**
| العمود | المحتوى |
|--------|---------|
| 0 | اسم التصنيف (بلون التصنيف) |
| 1 | عدد التصنيفات الفرعية المباشرة |
| 2 | إجمالي العناصر في التصنيف |

**الأزرار:**
- `btn_edit` — يفتح التصنيف المحدد في CategoryForm
- `btn_del` — يحذف مع تأكيد (confirm_delete) + إظهار warning_text من DeletePreview

**ملاحظات:**
- يحفظ حالة التوسع قبل reload ويُعيدها بعده.
- `_add_items` تُمرر نفس الـ `conn` من `_load()` بدل فتح connection جديد في كل node.
- `[Q-03]` كل action يُجري `_live_conn()` مرة واحدة ويُمررها للدوال الفرعية.

---

## SharedItemsListPanel

### `ui/widgets/shared/list_panel_with_shared.py`

```python
class SharedItemsListPanel(BaseListPanel, SharedOpsMixin, LiveConnMixin):
    """
    قاعدة مشتركة للجداول التي تدعم العناصر المشتركة/المنشورة.

    الـ inheritance chain:
        SharedItemsListPanel → BaseListPanel → BusConnectedMixin
                             → SharedOpsMixin
                             → LiveConnMixin

    [إصلاح] لا override لـ _live_conn — LiveConnMixin تتولى الأمر.
    [إصلاح FILTER_SCOPE] _build_filter يستخدم SHARED_TYPE كـ scope
    لو FILTER_SCOPE فارغ.
    """
```

#### إعدادات الـ subclass

```python
SHARED_TYPE      : str  = "raw"     # "raw" | "machine" | "labor_op" | "machine_op"
TABLE_COLS       : list = []        # → تُحوَّل لـ COLUMNS تلقائياً
TABLE_TITLE      : str  = ""        # → يُسند لـ LIST_TITLE تلقائياً
HAS_BULK_REPLACE : bool = False     # يُظهر زر "استبدال شامل"
SHOW_CATEGORY    : bool = True
CONNECT_BUS      : bool = True
FILTER_SCOPE     : str  = ""        # فارغ = استخدم SHARED_TYPE تلقائياً
# STRETCH_COL يُضبط على 1 تلقائياً
# العمود 0 يُخفى تلقائياً (setColumnHidden) — يُستخدم لحمل الـ ID
```

#### Hooks المطلوبة (override إلزامي)

```python
._fetch_local_rows() -> list[dict]
._fill_table_row(r: int, item: dict)
._edit_item(item_id: int)
._delete_item(item_id: int, item_name: str)
```

#### Hooks الاختيارية

```python
._get_shared_rows(local_rows: list) -> list[dict]   # افتراضياً: []
._get_item_data_for_publish(row: dict) -> dict       # افتراضياً: {}
._bulk_replace_item(item_id: int, item_name: str)
._setup_column_widths(table: QTableWidget)
._on_edit_shared()
# افتراضياً: يستدعي _edit_shared_item من SharedOpsMixin
```

#### أزرار الهيدر (تُضاف تلقائياً عبر _build_extra_header_actions)

| الزر | الظهور | الاستدعاء |
|------|--------|----------|
| `"🔄 استبدال شامل"` | فقط لو `HAS_BULK_REPLACE=True` | `_bulk_replace_item` |
| `"✏️ تعديل المحدد"` | دائماً | `_edit_item` |
| `"🗑️ حذف المحدد"` | دائماً | `_delete_item` |
| `"🔗 تعديل المشترك"` | دائماً | `_on_edit_shared` |
| `"📤 نشر كمشترك"` | دائماً | `_publish_item` من SharedOpsMixin |

#### التلوين التلقائي للصفوف

```python
# العناصر المشتركة (row["_is_shared"] = True):
#   fg = SHARED_COLOR, bg = SHARED_BG
# العناصر المنشورة (row["_is_published"] = True أو name في _published_names):
#   fg = PUBLISHED_COLOR, bg = PUBLISHED_BG
# من: ui/tabs/costing/shared/_utils.py
```

#### مساعدات

```python
._selected_row_data() -> tuple[int | None, str]
# يرجع (item_id, item_name) للصف المختار

._get_current_row_dict() -> dict | None
# يرجع dict بيانات الصف المختار من _all_rows
```

**مثال:**
```python
from ui.widgets.shared.list_panel_with_shared import SharedItemsListPanel
from ui.widgets.tables.tables import make_item
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

    def _setup_column_widths(self, table):
        table.setColumnWidth(1, 200)
        table.setColumnWidth(2, 100)
        table.setColumnWidth(3, 140)

    def _edit_item(self, item_id): ...
    def _delete_item(self, item_id, item_name): ...
```