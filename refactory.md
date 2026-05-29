
# خطة إعادة بناء تبويبات التكلفة (Costing Tabs)

> الهدف: توحيد البنية مع النظام الجديد، دمج الترجمة والثيمات، والاعتماد الكامل على `services/` بدل `repos/` مباشرةً في الـ UI.

---

## 1. المشكلة الحالية

### 1.1 الاستدعاء المباشر للـ repos
```
قبل:  UI Tab → db/costing/operations_repo.py  (مباشر)
بعد:  UI Tab → services/costing/             → db/
```

الملفات المخالفة حالياً:
- `component_row.py` يستدعي `machine_op_rows_repo` و `raw_variants_repo` مباشرة
- `bulk_replace_dialog.py` يستدعي `items_repo.replace_bom` مباشرة
- `machine_op_form.py` يستدعي `operations_repo` مباشرة
- `bom_tree.py` يستدعي `items_repo.fetch_bom` مباشرة
- `product_form.py` يستدعي `bom_scenarios_repo` مباشرة

### 1.2 غياب الترجمة (`tr()`)
كل النصوص مدمجة كـ hardcoded Arabic بدون استخدام `tr()`.

### 1.3 غياب الـ Themes (`_C`)
الألوان hardcoded بدلاً من `_C['accent']` و`_C['bg_surface']` إلخ.

### 1.4 عدم استخدام base classes الجديدة
- `TabSectionBase` موجود لكن بعض التبويبات لا ترثه
- `BaseListPanel` موجود لكن بعض الجداول تبني يدوياً
- `BaseCrudForm` موجود لكن بعض الفورمات لا ترثه

### 1.5 ملفات `component_row` مكررة
- `ui/tabs/costing/shared/component_row.py` (القديم - 500+ سطر)
- `ui/widgets/components/component_row/widget.py` (الجديد - المرجعي)

---

## 2. هيكل البناء الجديد المستهدف

```
ui/tabs/costing/
├── costing_section.py          ← لا تغيير كبير
├── raw_tab.py                  ← تبسيط
├── labor_tab.py                ← تبسيط
├── machine_tab.py              ← تبسيط
├── product_tab.py              ← تبسيط
│
├── raw/
│   ├── raw_section.py          ← يرث BaseSection ✓ (موجود)
│   ├── raw_input_panel.py      ← يرث BaseCrudForm ✓ (موجود)
│   └── raw_table_panel.py      ← يرث BaseListPanel ✓ (موجود)
│
├── labor/
│   ├── labor_settings.py       ← إعادة بناء بـ _C + tr()
│   ├── labor_op_form.py        ← يرث BaseCrudForm ✓ (موجود جزئياً)
│   └── labor_op_table.py       ← يرث SharedItemsListPanel ✓
│
├── machine/
│   ├── machine_form.py         ← إعادة بناء: استخدام MachineService
│   ├── machine_table.py        ← يرث SharedItemsListPanel ✓
│   ├── machine_op_form.py      ← إعادة بناء: استخدام MachineService
│   └── machine_op_table.py     ← يرث SharedItemsListPanel ✓
│
├── product/
│   ├── product_main_panel.py   ← إعادة بناء: استخدام ProductService
│   ├── product_form.py         ← إعادة بناء: تنظيم + tr()
│   ├── product_table.py        ← يرث BaseListPanel (حالياً يدوي)
│   ├── _catalog_provider.py    ← لا تغيير
│   ├── _orphan_handler.py      ← لا تغيير
│   └── form/
│       ├── _header_bar.py      ← إعادة بناء: _C + tr()
│       ├── _rows_manager.py    ← تعديل: يستخدم ComponentRow الجديد
│       └── _save_logic.py      ← تعديل: يستخدم ProductService
│
└── shared/
    ├── component_row.py        ← حذف (استبدال بـ widgets/components/component_row/)
    ├── bom_tree.py             ← تعديل: _C + tr()
    ├── bom_scenarios_panel.py  ← تعديل: _C + tr()
    ├── catalog_builder.py      ← لا تغيير
    ├── machine_op_rows_editor.py ← تعديل: _C + tr()
    ├── raw_variants_panel.py   ← تعديل: _C + tr()
    ├── scenario_comparison_widget.py ← تعديل: _C + tr()
    └── bulk_replace/
        ├── bulk_replace_dialog.py    ← تعديل: services + _C + tr()
        ├── bulk_replace_helpers.py   ← تعديل: services
        ├── bulk_replace_products_panel.py ← تعديل: _C + tr()
        └── _operation_section.py    ← تعديل: _C + tr()
```

---

## 3. الملفات والتغييرات التفصيلية

### 3.1 حذف `component_row.py` القديم

**الملف:** `ui/tabs/costing/shared/component_row.py`  
**الإجراء:** حذف كامل  
**البديل:** `ui/widgets/components/component_row/widget.py`

كل مكان يستورد من القديم يتغير:
```python
# قبل
from ui.tabs.costing.shared.component_row import ComponentRow
# بعد
from ui.widgets.components.component_row.widget import ComponentRow
```

الملفات المتأثرة:
- `product/form/_rows_manager.py`
- `product/product_form.py`

---

### 3.2 `product/product_table.py` → يرث `BaseListPanel`

**الحالة الحالية:** بناء يدوي كامل (QTableWidget + FilterBar + أزرار)  
**الهدف:** يرث `BaseListPanel`

```python
class _ProductTable(BaseListPanel, LiveConnMixin):
    COLUMNS      = ["ID", "الاسم", "التصنيف", "التكلفة"]
    STRETCH_COL  = 1
    EMPTY_ICON   = "🏭"
    EMPTY_TITLE  = tr("no_products")
    LIST_TITLE   = tr("saved_products")
    SHOW_CATEGORY = True
    CONNECT_BUS  = True
    COL_WIDTHS   = {0: 45, 2: 110, 3: 120}

    def _load_rows(self) -> list:
        from services.costing.product_service import ProductService
        return ProductService(self.conn).list_by_type(self.product_type)

    def _fill_row(self, table, r, row):
        cost = calc_cost(self.conn, row["id"])
        table.setItem(r, 0, make_item(str(row["id"]), user_data=row["id"]))
        table.setItem(r, 1, make_item(row["name"]))
        table.setItem(r, 2, make_item(row.get("category_name") or "—"))
        table.setItem(r, 3, make_item(f"{cost:.4f}"))
```

---

### 3.3 `product/form/_rows_manager.py` → يستخدم ComponentRow الجديد

**التغيير الرئيسي:** تغيير الاستيراد فقط + ضمان التوافق مع API الجديد

```python
# قبل
from ui.widgets.shared.component_row._row_widget import ComponentRow
# بعد
from ui.widgets.components.component_row.widget import ComponentRow
```

API الجديد متوافق: `get_values()`, `removed`, `is_orphan()`, `expose_load_op_rows()` كلها موجودة.

---

### 3.4 `product/form/_save_logic.py` → يستخدم `ProductService`

```python
# قبل
from db.shared.items_repo import insert_item, update_item
from db.costing.bom_scenarios_repo import insert_scenario, replace_bom_for_scenario

# بعد
from services.costing.product_service import ProductService, BomComponent
```

```python
def save(self, *, is_editing, editing_id, name, product_type,
         category_id, current_scenario_id, rows,
         scenarios_panel, parent_widget) -> int | None:
    if not name:
        QMessageBox.warning(parent_widget, tr("warning"), tr("enter_product_name"))
        return None
    if not rows:
        QMessageBox.warning(parent_widget, tr("warning"), tr("add_one_component"))
        return None

    components = [
        BomComponent(
            child_type=r[0], child_id=r[1], qty=r[2],
            waste_pct=r[3] or 0.0,
            variant_id=r[4],
            machine_op_row_id=r[5],
        )
        for r in rows
    ]

    try:
        svc = ProductService(self._conn_fn())
        result = svc.save(
            product_data={
                "id":          editing_id if is_editing else None,
                "name":        name,
                "type":        product_type,
                "price":       0,
                "category_id": category_id,
            },
            components=components,
            scenario_id=current_scenario_id,
        )
        return result.product_id
    except Exception as e:
        QMessageBox.warning(parent_widget, tr("error"), str(e))
        return None
```

---

### 3.5 `machine/machine_form.py` → يستخدم `MachineService`

**التغيير:** استبدال `insert_machine` / `update_machine` بـ `MachineService`

```python
# قبل
from db.costing.operations_repo import fetch_machine, insert_machine, update_machine

# بعد
from services.costing.machine_service import MachineService
```

ملاحظة: `MachineService` موجود في `services/costing/machine_service.py` حسب file tree.

---

### 3.6 `machine/machine_op_form.py` → يستخدم `MachineService`

```python
# قبل
from db.costing.operations_repo import (
    fetch_machine, fetch_machine_op, fetch_all_machines,
    insert_machine_op, update_machine_op,
)

# بعد
from services.costing.machine_service import MachineService
```

---

### 3.7 `shared/bulk_replace/bulk_replace_dialog.py` → يستخدم `bulk_replace_service`

حسب file tree: `services/costing/bulk_replace_service.py` موجود.

```python
# قبل
from db.shared.items_repo import fetch_item, replace_bom, fetch_bom

# بعد
from services.costing.bulk_replace_service import BulkReplaceService
```

```python
def _apply(self):
    # ...التحقق من المدخلات...
    svc = BulkReplaceService(self.conn)
    result = svc.apply(
        child_type=self.child_type,
        old_child_id=self.child_id,
        new_child_id=new_child_id if do_replace else None,
        product_ids=[r.product_id for r in selected_rows],
        qty_map={r.product_id: r.new_qty for r in selected_rows} if do_qty else None,
        uniform_qty=uniform_qty,
    )
    # عرض النتيجة...
```

---

### 3.8 دمج `_C` في كل الملفات

كل ملف يحتوي على ألوان hardcoded يتحول لـ:

```python
from ui.app_settings import _C

# قبل
self.setStyleSheet("background: #f9f9f9; border: 1px solid #e0e0e0;")

# بعد
self.setStyleSheet(f"background: {_C['bg_surface']}; border: 1px solid {_C['border']};")
```

جدول التحويلات الشائعة:

| اللون القديم (hardcoded) | المفتاح الجديد في `_C` |
|---|---|
| `#f9f9f9`, `#f5f5f5` | `_C['bg_surface']` |
| `#ffffff` | `_C['bg_input']` |
| `#e0e0e0` | `_C['border']` |
| `#90caf9` | `_C['border_focus']` |
| `#1565c0` | `_C['accent']` |
| `#212121` | `_C['text_primary']` |
| `#757575`, `#555` | `_C['text_sec']` |
| `#999`, `#bbb` | `_C['text_muted']` |
| `#c0392b`, `#e53935` | `_C['danger']` |
| `#2e7d32` | `_C['success']` |
| `#e65100` | `_C['orange']` |
| `#6a1b9a` | `_C['purple']` |
| `#f3e5f5` | `_C['purple_bg']` |
| `#ce93d8` | `_C['purple_border']` |
| `#fff8e1` | `_C['warning_bg']` |
| `#ffe082` | `_C['warning_border']` |

---

### 3.9 دمج `tr()` في كل الملفات

```python
from ui.widgets.core.i18n import tr

# قبل
QLabel("🏷  فلتر بالتصنيف:")
QPushButton("✅ الكل")
QPushButton("☐ لا شيء")

# بعد
QLabel(f"🏷  {tr('filter_by_category')}:")
QPushButton(f"✅ {tr('select_all')}")
QPushButton(f"☐ {tr('select_none')}")
```

مفاتيح الترجمة المطلوب إضافتها لـ `ui/i18n/ar.py` و `ui/i18n/en.py`:

```python
# ar.py إضافات
"filter_by_category": "فلتر بالتصنيف",
"select_all":         "الكل",
"select_none":        "لا شيء",
"invert_selection":   "عكس",
"total":              "إجمالي",
"selected":           "محدد",
"no_products_linked": "لا توجد منتجات مرتبطة بهذا العنصر",
"operation_required": "العملية المطلوبة",
"replace_element":    "استبدال العنصر",
"edit_qty_only":      "تعديل الكمية فقط",
"both_operations":    "الاثنين معاً",
"apply_to_selected":  "تطبيق على المحدد",
"bom_tree":           "هيكل BOM",
"scenario":           "السيناريو",
"default_scenario":   "سيناريو افتراضي",
"add_scenario":       "إضافة سيناريو",
"clone_scenario":     "نسخ السيناريو",
"saved_products":     "المنتجات المحفوظة",
"no_products":        "لا توجد منتجات",
"enter_product_name": "ادخل اسم المنتج اولاً",
"add_one_component":  "اضف مكوناً واحداً على الأقل",
"product_name":       "اسم المنتج",
"add_component":      "+ مكون",
"op_rows_editor":     "صفوف العملية",
"raw_variants":       "وحدات الإنتاج (Variants)",
"waste_pct":          "نسبة الهادر %",
"op_row":             "صف العملية",
```

---

## 4. ترتيب تنفيذ العمل (Execution Order)

### المرحلة 1 — التنظيف الفوري (لا يكسر شيء)
1. حذف `ui/tabs/costing/shared/component_row.py`
2. تحديث imports في `_rows_manager.py` و `product_form.py`
3. إضافة مفاتيح الترجمة لـ `ar.py` و `en.py`

### المرحلة 2 — تحديث Services Layer
4. تحديث `_save_logic.py` → `ProductService`
5. تحديث `machine_form.py` → `MachineService`
6. تحديث `machine_op_form.py` → `MachineService`
7. تحديث `bulk_replace_dialog.py` → `BulkReplaceService`

### المرحلة 3 — تحديث Base Classes
8. تحديث `product_table.py` → `BaseListPanel`
9. تحديث `bom_scenarios_panel.py` → `_C` + `tr()`
10. تحديث `bom_tree.py` → `_C` + `tr()`

### المرحلة 4 — تحديث Styles
11. كل ملفات `shared/` → `_C` بدل hardcoded colors
12. كل ملفات `machine/` و `labor/` → `_C` + `tr()`
13. كل ملفات `product/form/` → `_C` + `tr()`

---

## 5. ملفات لا تحتاج تعديل

| الملف | السبب |
|---|---|
| `raw/raw_section.py` | يرث `BaseSection` بالفعل ✓ |
| `raw/raw_input_panel.py` | يرث `BaseCrudForm` بالفعل ✓ |
| `raw/raw_table_panel.py` | يرث `BaseListPanel` بالفعل ✓ |
| `labor/labor_op_form.py` | يرث `BaseCrudForm` بالفعل ✓ |
| `labor/labor_op_table.py` | يرث `SharedItemsListPanel` ✓ |
| `machine/machine_table.py` | يرث `SharedItemsListPanel` ✓ |
| `machine/machine_op_table.py` | يرث `SharedItemsListPanel` ✓ |
| `product/_catalog_provider.py` | منطق نقي، لا UI ✓ |
| `product/_orphan_handler.py` | منطق نقي، لا UI ✓ |
| `shared/catalog_builder.py` | منطق نقي، لا UI ✓ |
| `shared/_utils.py` | ثوابت فقط ✓ |

---

## 6. الملفات الجديدة المطلوب إنشاؤها

### 6.1 `ui/tabs/costing/shared/bom_tree_helper/_component_node.py`
فصل منطق بناء nodes عن الـ widget (موجود جزئياً في `_scenario_node_builder.py`).

### 6.2 تحديث `ui/i18n/ar.py` و `en.py`
إضافة مفاتيح costing المذكورة في القسم 3.9.

---

## 7. ملاحظات مهمة

### 7.1 `MachineService` — التحقق من الـ API
حسب `system_arch.txt`، الملف موجود في `services/costing/machine_service.py` لكن API غير موثق في `models&services.md`. قبل الاستخدام، يجب قراءة الملف مباشرة للتحقق من الدوال المتاحة.

### 7.2 `BulkReplaceService` — التحقق من الـ API
نفس الملاحظة. الملف موجود في `services/costing/bulk_replace_service.py`.

### 7.3 `ComponentRow` الجديد — التوافق
الـ API الجديد في `ui/widgets/components/component_row/widget.py` متوافق مع القديم في:
- `get_values()` → نفس التوقيع
- `removed` signal → نفس التوقيع
- `expose_load_op_rows()` → نفس التوقيع
- `is_orphan()` / `set_orphan_name()` → نفس التوقيع

**الفرق الوحيد:** الـ import path.

### 7.4 الـ Themes — Invalidation
عند تغيير الثيم، الـ stylesheets المدمجة في `__init__` لن تتحدث تلقائياً.  
الحل: ربط `bus.theme_changed` بدالة `_apply_theme()` في كل widget يستخدم `_C`.

```python
from ui.events import bus
bus.theme_changed.connect(self._apply_theme)

def _apply_theme(self, _=None):
    self.setStyleSheet(f"background: {_C['bg_surface']};...")
```

### 7.5 لا تكسر `_ProductsPanel`
`bulk_replace_products_panel.py` يستخدم `ProductRow` من `bulk_replace_helpers.py` — الاثنان يجب أن يُحدَّثا معاً.

---

## 8. ملخص الملفات حسب الأولوية

| الأولوية | الملف | نوع التغيير |
|---|---|---|
| 🔴 عالية | `shared/component_row.py` | حذف |
| 🔴 عالية | `product/form/_rows_manager.py` | تغيير import |
| 🔴 عالية | `product/form/_save_logic.py` | → ProductService |
| 🔴 عالية | `machine/machine_form.py` | → MachineService |
| 🔴 عالية | `machine/machine_op_form.py` | → MachineService |
| 🟡 متوسطة | `bulk_replace/bulk_replace_dialog.py` | → BulkReplaceService |
| 🟡 متوسطة | `product/product_table.py` | → BaseListPanel |
| 🟡 متوسطة | `shared/bom_scenarios_panel.py` | _C + tr() |
| 🟡 متوسطة | `shared/bom_tree.py` | _C + tr() |
| 🟢 منخفضة | كل الملفات المتبقية | _C + tr() فقط |

---

## 9. قاعدة الاتساق النهائية

بعد انتهاء الـ refactoring، كل ملف في `ui/tabs/costing/` يجب أن:

1. ✅ **لا يستورد من `db/` مباشرة** — فقط عبر `services/`
2. ✅ **يستخدم `_C[key]`** بدل ألوان hardcoded
3. ✅ **يستخدم `tr(key)`** بدل نصوص عربية مدمجة
4. ✅ **يرث من base class مناسب** (`BaseListPanel`, `BaseCrudForm`, `BaseSection`)
5. ✅ **يستخدم `LiveConnMixin`** بدل تخزين `conn` مباشرة حيثما ممكن
6. ✅ **يستمع لـ `bus.theme_changed`** إذا كان يعرض stylesheet ديناميكي



# بنية المشروع — المرحلة السادسة
### الأهداف البنيوية للمرحلة السابعة

الهدف الأساسي هو استكمال تحويل ملفات `tabs/` لتصبح مجرد orchestrators تستدعي الأدوات الجاهزة:

```
tabs/UI ──→ services/ ──→ repos/ (db/)
  ↑                            ↑
widgets/ (base classes)    schema/
```

### الربط الصحيح بين الطبقات

```
tabs/UI ──→ services/ ──→ repos/ (db/)
  ↑                            ↑
widgets/ (base classes)    schema/
```

**القواعد:**
- **tabs** تستدعي **services** مش الـ repos مباشرة
- **services** لا تعرف عن PyQt — pure Python
- **widgets** توفر الـ UI infrastructure فقط
- **conn** دايماً يجي من الخارج (constructor) مش يتفتح جوا الـ Widget

---

### الـ Base Classes المتاحة

| الحاجة | الـ Class | الملف |
|--------|-----------|-------|
| لوحة قائمة | `BaseListPanel` | `ui/widgets/base/list_panel.py` |
| لوحة تفاصيل | `BaseDetailPanel` | `ui/widgets/base/detail_panel.py` |
| فورم CRUD | `BaseCrudForm` | `ui/widgets/base/crud_form.py` |
| قسم list+detail | `BaseSection` | `ui/widgets/base/section.py` |
| قسم مع فورم | `CrudSection` | `ui/widgets/panels/crud_section.py` |
| تبويبات | `TabSectionBase` | `ui/widgets/base/tab_section.py` |

---

### Template — List Panel

```python
from ui.widgets.base.list_panel import BaseListPanel
from ui.widgets.tables.items import make_item
from PyQt5.QtCore import Qt

class MyListPanel(BaseListPanel):
    COLUMNS            = ["الاسم", "التصنيف", "السعر"]
    STRETCH_COL        = 0
    EMPTY_ICON         = "📦"
    EMPTY_TITLE        = "لا توجد عناصر"
    LIST_TITLE         = "العناصر"
    ADD_TEXT           = "➕ إضافة"
    SEARCH_PLACEHOLDER = "🔍  بحث في العناصر..."
    SHOW_CATEGORY      = True
    FILTER_SCOPE       = "raw"

    def _load_rows(self) -> list:
        from services.shared.item_service import ItemService
        return [vars(r) for r in ItemService(self.conn).list_by_type("raw")]

    def _fill_row(self, table, row_index: int, row_data: dict):
        table.setItem(row_index, 0, make_item(row_data["name"], user_data=row_data["id"]))
        table.setItem(row_index, 1, make_item(row_data.get("category_name") or "—"))
        table.setItem(row_index, 2, make_item(
            f"{row_data.get('price', 0):,.2f}", align=Qt.AlignCenter
        ))

    def _on_add_clicked(self):
        pass  # emit signal أو افتح dialog
```

---

### Template — Detail Panel

```python
from ui.widgets.base.detail_panel import BaseDetailPanel
from ui.widgets.panels.detail_section import DetailSection

class MyDetailPanel(BaseDetailPanel):
    EMPTY_ICON    = "📦"
    EMPTY_TITLE   = "اختر عنصراً من القائمة"
    MIN_CONTENT_W = 500
    CONNECT_BUS   = True

    def _build_header_cards(self):
        self._card_price = self._hdr.add_stat_card("💰", "السعر", "─", "#1565c0")

    def _build_header_buttons(self):
        self._hdr.toolbar.add_action("✏️ تعديل", self._edit, "primary")
        self._hdr.toolbar.add_danger("🗑️ حذف", self._delete)

    def _build_content(self, layout):
        self._sec      = DetailSection("البيانات الأساسية", cols=2)
        self._lbl_name = self._sec.add_row("الاسم:")
        self._lbl_cat  = self._sec.add_row("التصنيف:")
        layout.addWidget(self._sec)

    def _load_data(self, item_id: int):
        from services.shared.item_service import ItemService
        return ItemService(self.conn).get(item_id)

    def _fill_header(self, data: dict):
        self._hdr.set_title(data.get("name", "─"))
        self._card_price.set_value(f"{data.get('price', 0):,.2f} ج")

    def _fill_data(self, data: dict):
        self._lbl_name.setText(data.get("name", "─"))
        self._lbl_cat.setText(data.get("category_name") or "بدون تصنيف")
```

---

### Template — Crud Form

```python
from ui.widgets.base.crud_form import BaseCrudForm
from ui.widgets.panels.form_parts import FormGroup
from ui.widgets.forms.inputs import RequiredLineEdit, AmountSpinBox

class MyForm(BaseCrudForm):
    FORM_TITLE = "بيانات العنصر"
    ADD_TEXT   = "➕  إضافة"
    SAVE_TEXT  = "💾  حفظ التعديل"

    def _build_fields(self, group: FormGroup):
        self.inp_name   = RequiredLineEdit("اسم العنصر")
        self.spin_price = AmountSpinBox()
        group.add_row("الاسم *", self.inp_name)
        group.add_row("السعر",   self.spin_price)

    def _collect(self) -> dict | None:
        if not self.inp_name.validate():
            return None
        return {"name": self.inp_name.text_stripped(), "price": self.spin_price.value()}

    def _do_insert(self, data: dict) -> int:
        from services.shared.item_service import ItemService
        return ItemService(self.conn).add(data["name"], data["price"], "raw")

    def _do_update(self, item_id: int, data: dict):
        from services.shared.item_service import ItemService
        ItemService(self.conn).update(item_id, data["name"], data["price"])

    def _do_load(self, item_id: int) -> dict | None:
        from services.shared.item_service import ItemService
        result = ItemService(self.conn).get(item_id)
        return vars(result) if result else None

    def _fill_fields(self, data: dict):
        self.inp_name.setText(data.get("name", ""))
        self.spin_price.setValue(data.get("price", 0))

    def _reset_fields(self):
        self.inp_name.clear()
        self.spin_price.setValue(0)
```

---

### Template — Section كاملة

```python
from ui.widgets.base.section import BaseSection

class MySection(BaseSection):
    LIST_MIN_W   = 300
    LIST_MAX_W   = 500
    DETAIL_MIN_W = 400
    CONNECT_BUS  = True

    def _create_list(self):
        return MyListPanel(conn=self.conn)

    def _create_detail(self):
        return MyDetailPanel(conn=self.conn)

    def _connect_signals(self):
        self._list.item_selected.connect(self._detail.load_item)
        self._detail.deleted.connect(self._list.refresh)
```

---

### Checklist — Feature جديدة

- [ ] List Panel يورث من `BaseListPanel`
- [ ] Detail Panel يورث من `BaseDetailPanel`
- [ ] Form يورث من `BaseCrudForm`
- [ ] Section يورث من `BaseSection` أو `CrudSection`
- [ ] Business Logic في `services/` مش في الـ Widget
- [ ] الـ Widget تستدعي الـ Service مش الـ Repo مباشرة
- [ ] `emit_company_data_changed()` بدل `bus.data_changed.emit()`
- [ ] `CONNECT_BUS = True` في الـ Detail Panel لو محتاج يتحدث تلقائياً
- [ ] الـ conn بيجي من الخارج (constructor) مش يتفتح جوا الـ Widget
- [ ] تحقق من الـ inputs في الـ service layer مش الـ widget فقط

---

## ملفات tabs الموجودة حالياً

### Section Files
```
ui/tabs/accounting_section.py
ui/tabs/costing_section.py
ui/tabs/design_section.py
ui/tabs/inventory_section.py
ui/tabs/orders_section.py
ui/tabs/pricing_section.py
```

### Accounting
```
ui/tabs/accounting/accounting_tabs_builder.py
ui/tabs/accounting/accounts_tree.py
ui/tabs/accounting/account_combo.py
ui/tabs/accounting/accounts_combo_widget.py
ui/tabs/accounting/financial_statements.py
ui/tabs/accounting/group_manager.py
ui/tabs/accounting/helpers.py
ui/tabs/accounting/investors_tab.py
ui/tabs/accounting/journal_tab.py
ui/tabs/accounting/ledger_tab.py
ui/tabs/accounting/_conn_guard.py
ui/tabs/accounting/_state_widgets.py
ui/tabs/accounting/financial/balance_sheet_tab.py
ui/tabs/accounting/financial/income_statement_tab.py
ui/tabs/accounting/financial/owners_equity_tab.py
ui/tabs/accounting/financial/trial_balance_tab.py
ui/tabs/accounting/financial/_financial_helpers.py
ui/tabs/accounting/investors/_investor_details.py
ui/tabs/accounting/investors/_investor_form.py
ui/tabs/accounting/investors/_investors_layout.py
ui/tabs/accounting/investors/_investors_panel.py
ui/tabs/accounting/investors/_investors_table.py
ui/tabs/accounting/investors/_details_table.py
ui/tabs/accounting/investors/_helpers.py
ui/tabs/accounting/investors/_link_to_entry_panel.py
ui/tabs/accounting/investors/_movement_dialog.py
ui/tabs/accounting/journal/journal_account_picker.py
ui/tabs/accounting/journal/journal_filter.py
ui/tabs/accounting/journal/journal_form.py
ui/tabs/accounting/journal/journal_group_combo.py
ui/tabs/accounting/journal/journal_lines.py
ui/tabs/accounting/journal/journal_tab_widget.py
ui/tabs/accounting/journal/journal_tree_table.py
ui/tabs/accounting/journal/account_picker/_account_picker_button.py
ui/tabs/accounting/journal/account_picker/_account_tree_popup.py
ui/tabs/accounting/journal/form/_balance_bar.py
ui/tabs/accounting/journal/form/_entry_meta.py
ui/tabs/accounting/journal/form/_journal_header.py
ui/tabs/accounting/journal/group_combo/_no_select_delegate.py
ui/tabs/accounting/journal/group_combo/_tree_group_combo.py
ui/tabs/accounting/journal/lines/_lines_panel.py
ui/tabs/accounting/journal/lines/_smart_line.py
ui/tabs/accounting/ledger/ledger_accounts_panel.py
ui/tabs/accounting/ledger/ledger_filter_bar.py
ui/tabs/accounting/ledger/ledger_stat_cards.py
ui/tabs/accounting/ledger/ledger_t_account.py
ui/tabs/accounting/tree/_account_form.py
ui/tabs/accounting/tree/_group_filter.py
ui/tabs/accounting/tree/_tree_builder.py
ui/tabs/accounting/tree/_tree_headers.py
ui/tabs/accounting/tree/_tree_nodes.py
```

### Costing
```
ui/tabs/costing/product_tab.py
ui/tabs/costing/raw_tab.py
ui/tabs/costing/labor_tab.py
ui/tabs/costing/machine_tab.py
ui/tabs/costing/product/product_form.py
ui/tabs/costing/product/product_main_panel.py
ui/tabs/costing/product/product_table.py
ui/tabs/costing/product/_catalog_provider.py
ui/tabs/costing/product/_orphan_handler.py
ui/tabs/costing/product/form/_header_bar.py
ui/tabs/costing/product/form/_rows_manager.py
ui/tabs/costing/product/form/_save_logic.py
ui/tabs/costing/raw/raw_input_panel.py
ui/tabs/costing/raw/raw_section.py
ui/tabs/costing/raw/raw_table_panel.py
ui/tabs/costing/labor/labor_op_form.py
ui/tabs/costing/labor/labor_op_table.py
ui/tabs/costing/labor/labor_settings.py
ui/tabs/costing/machine/machine_form.py
ui/tabs/costing/machine/machine_op_form.py
ui/tabs/costing/machine/machine_op_table.py
ui/tabs/costing/machine/machine_table.py
ui/tabs/costing/shared/bom_scenarios_panel.py
ui/tabs/costing/shared/bom_tree.py
ui/tabs/costing/shared/catalog_builder.py
ui/tabs/costing/shared/component_row.py
ui/tabs/costing/shared/machine_op_rows_editor.py
ui/tabs/costing/shared/raw_variants_panel.py
ui/tabs/costing/shared/scenario_comparison_widget.py
ui/tabs/costing/shared/bom_scenarios/...
ui/tabs/costing/shared/bulk_replace/...
```

### Design
```
ui/tabs/design/designs_tab.py
ui/tabs/design/dimension_sets_tab.py
ui/tabs/design/design_styles.py
ui/tabs/design/designs/...
ui/tabs/design/dimension_sets/...
```

### Inventory
```
ui/tabs/inventory/inventory_inbound_tab.py
ui/tabs/inventory/inventory_items_tab.py
ui/tabs/inventory/inventory_outbound_tab.py
ui/tabs/inventory/inventory_report_tab.py
ui/tabs/inventory/items/_item_form.py
ui/tabs/inventory/items/_items_tab.py
ui/tabs/inventory/items/_items_table.py
```

### Orders
```
ui/tabs/orders/orders_tab.py
ui/tabs/orders/customers_tab.py
ui/tabs/orders/dashboard_tab.py
ui/tabs/orders/_customer_form.py
ui/tabs/orders/_item_form.py
ui/tabs/orders/_order_detail.py
ui/tabs/orders/_order_form.py
ui/tabs/orders/customers/customer_detail_panel.py
ui/tabs/orders/customers/customers_list_panel.py
ui/tabs/orders/dashboard/_config.py
ui/tabs/orders/dashboard/_recent_table.py
ui/tabs/orders/dashboard/_status_grid.py
ui/tabs/orders/dashboard/_top_cards.py
ui/tabs/orders/order_detail/_header_fill.py
ui/tabs/orders/order_detail/_items_section.py
ui/tabs/orders/order_detail/_log_section.py
ui/tabs/orders/order_detail/_status_config.py
ui/tabs/orders/order_detail/_status_dialog.py
ui/tabs/orders/order_form/_item_row_widget.py
ui/tabs/orders/order_form/_products_fetcher.py
ui/tabs/orders/orders/_filter_toolbar.py
ui/tabs/orders/orders/_orders_list_panel.py
ui/tabs/orders/orders/_status_delegate.py
```

### Pricing
```
ui/tabs/pricing/pricing_tab.py
ui/tabs/pricing/pricing/...
ui/tabs/pricing/offers/...
```

### Companies
```
ui/tabs/companies/companies_dialog.py
ui/tabs/companies/company_selector.py
ui/tabs/companies/no_company_screen.py
ui/tabs/companies/shared_items_dialog.py
ui/tabs/companies/shared_items_manager.py
ui/tabs/companies/shared_items_mixin.py
ui/tabs/companies/_link_item_picker.py
ui/tabs/companies/shared_items_manager_helper/_add_shared_item_dialog.py
```