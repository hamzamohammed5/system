# دليل الكود — UI / Widgets (8): Managers, Main & Shared

> الجزء الثامن — مدير التصنيفات، النافذة الرئيسية، والأقسام المشتركة.

---

## فهرس هذا الجزء

| القسم | الملفات |
|-------|---------|
| [CategoryManager](#categorymanager) | `widgets/managers/category` |
| [Main Window](#main-window) | `main_window`, `settings_dialog` |
| [SharedItemsListPanel](#shareditemslistpanel) | `widgets/shared/list_panel_with_shared` |

---

## CategoryManager

### `ui/widgets/managers/category.py`

```python
CategoryManager(conn, scope="all")
# يستمع لـ bus.data_changed + bus.language_changed
# يستخدم _live_conn() مرة واحدة لكل action — يُمررها للدوال الفرعية
# عناوين الأعمدة والأزرار من tr()
# يشترك في bus.language_changed لتحديث النصوص تلقائياً

CategoryForm(conn, scope, tree_widget)
  .load_for_edit(cat_id: int)
# يشترك في bus.language_changed لتحديث نصوص الـ groupbox والأزرار
# _refresh_parent_combo(conn=None, exclude_id=None)
# conn اختياري — لو None يستدعي _live_conn() مرة واحدة
```

**ملاحظة [Q-03]:** كل action يُجري `_live_conn()` مرة واحدة فقط ويُمررها للدوال الفرعية بدل استدعاء جديد في كل عملية.

---

## Main Window

### `ui/main_window.py` — `MainWindow`

```python
MainWindow(app: QApplication)
# resize: WINDOW_DEFAULT_W × 820
# setLayoutDirection: Qt.RightToLeft
# setMinimumSize: (SIDEBAR_COLLAPSED_WIDTH + 400, 500)

# index_map للـ Navigation:
{
    "costing":    1,
    "pricing":    2,
    "accounting": 3,
    "inventory":  4,
    "design":     5,
    "orders":     6,
}

# سلوكيات خاصة:
# "settings"     → SettingsDialog (لا يغير الـ stack index)
# "shared_items" → SharedItemsManagerDialog مباشرة
# تغيير الشركة  → AppState.invalidate() + _refresh_tabs() + bus.company_data_changed
```

**إضافة Tab جديدة:**
```python
# في MainWindow._build_tabs():
from ui.tabs.my_section import MySection
self._stack.addWidget(MySection())  # index N

# في index_map:
"my_key": N

# في _sidebar._build():
_NavButton("🔑", "اسم القسم", key="my_key")
```

---

### `ui/settings_dialog.py` — `SettingsDialog`

```python
SettingsDialog(app: QApplication, parent=None)
# تبويبات: الخط | المظهر | اللغة | الوحدات | GIMP

# حفظ (_save):
#   - حجم الخط: set_font_size() + apply_font() + bus.font_changed
#   - الثيم: theme_manager.set_theme() → يُطلق bus.theme_changed تلقائياً
#   - اللغة: i18n_manager.set_language() + app.setLayoutDirection() + bus.language_changed
#   - GIMP path: set_setting() في erp DB

# _get_settings_conn_and_status() -> tuple[conn, has_company]
# يقرأ company_state.is_ready مرة واحدة فقط
```

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
# العناصر المنشورة (row["_is_published"] = True أو name في _published_names):
#   fg = PUBLISHED_COLOR, bg = PUBLISHED_BG
# من: ui/tabs/costing/shared/_utils.py
```

**مساعدات:**
```python
panel._selected_row_data() -> tuple[int | None, str]   # (item_id, item_name)
panel._get_current_row_dict() -> dict | None
# _live_conn() موروثة من LiveConnMixin — تستخدم self.conn ثم company_state كـ fallback
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