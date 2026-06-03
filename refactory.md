# خطة التحسين الشاملة — تحويل tabs/ إلى Orchestrators

**التاريخ:** 2026-06-03  
**الهدف:** استكمال تحويل ملفات `tabs/` لتصبح orchestrators نقية تستدعي الأدوات الجاهزة

```
widgets/ (base classes) → tabs/UI ──→ services/ ──→ repos/ (db/) ← schema/
```

---

## 1. المشكلات المكتشفة

### 1.1 استدعاءات مباشرة لـ repos بدل services

| الملف | الاستدعاء الخاطئ | البديل الصحيح |
|-------|-----------------|--------------|
| `ui/tabs/costing/machine_tab.py` | `from ui.app_settings import _C` | `from ui.theme import _C` |
| `ui/tabs/costing/labor_tab.py` | `from ui.app_settings import _C` | `from ui.theme import _C` |
| `ui/tabs/costing/machine/machine_form.py` | `from ui.widgets.mixins.edit import EditModeMixin` | `from ui.widgets.mixins.form_mixins import EditModeMixin` |
| `ui/tabs/costing/machine/machine_op_form.py` | `from ui.widgets.mixins.edit import EditModeMixin` | `from ui.widgets.mixins.form_mixins import EditModeMixin` |
| `ui/tabs/costing/shared/bulk_replace/bulk_replace_helpers.py` | `from ui.app_settings import _C` | `from ui.theme import _C` |
| `ui/tabs/costing/shared/bulk_replace/_operation_section.py` | `from ui.app_settings import _C` | `from ui.theme import _C` |
| `ui/tabs/costing/shared/scenario_comparison_widget.py` | `from ui.app_settings import _C` | `from ui.theme import _C` |
| `ui/tabs/costing/shared/bom_scenarios_panel.py` | `from ui.app_settings import _C` | `from ui.theme import _C` |
| `ui/tabs/costing/raw/raw_table_panel.py` | import مباشر `delete_item` | عبر `ItemService.force_delete` |
| `ui/tabs/costing/product/product_main_panel.py` | `bus.data_changed.emit()` (محذوف) | `emit_company_data_changed()` |
| `ui/tabs/costing/product/_orphan_handler.py` | `cleanup_empty_products_after_orphan_fix` مباشر | يبقى مؤقتاً (TODO موجود) |
| `ui/tabs/costing/machine/machine_op_form.py` | `bus.data_changed.connect(...)` (محذوف) | `bus.company_data_changed.connect(...)` أو `emit_company_data_changed` |
| `ui/tabs/costing/product/product_main_panel.py` | `bus.data_changed.connect(...)` (محذوف) | الربط بـ `company_data_changed` |
| `ui/tabs/costing_section.py` | `tr('costing_section')` مفتاح غير موجود | يحتاج إضافة للـ i18n |

### 1.2 مفاتيح i18n مفقودة

الملفات التالية تستدعي `tr()` بمفاتيح غير موجودة في `ar.py` / `en.py`:

| الملف | المفتاح المفقود |
|-------|---------------|
| `costing_section.py` | `"costing_section"` |
| `costing_section.py` | `"raw_materials"` (موجود كـ `"raw_materials"` → ✅ موجود) |
| `costing_section.py` | `"semi_product"` → غير موجود |
| `costing_section.py` | `"final_product"` → غير موجود |
| `costing_section.py` | `"labor"` → غير موجود |
| `costing_section.py` | `"machine"` → غير موجود |
| `machine_tab.py` | `tr('الماكينات')` نص عربي مباشر لـ tr() → خطأ |
| `machine_tab.py` | `tr('عمليات التشغيل')` نص عربي مباشر → خطأ |
| `machine_tab.py` | `tr('التصنيفات')` نص عربي مباشر → خطأ |
| `labor_tab.py` | `tr('إعدادات العمالة')` نص عربي مباشر → خطأ |
| `labor_tab.py` | `tr('عمليات العمالة')` نص عربي مباشر → خطأ |
| `labor_tab.py` | `tr('التصنيفات')` نص عربي مباشر → خطأ |
| `product_main_panel.py` | `tr('حذف الناقص')` نص عربي مباشر → خطأ |
| `product_main_panel.py` | `tr('تعديل')` نص عربي مباشر → خطأ |
| `product_main_panel.py` | `tr('خطأ')` نص عربي مباشر → خطأ |
| `product_main_panel.py` | `tr('تنبيه')` نص عربي مباشر → خطأ |
| `product_main_panel.py` | `tr('اختر منتجاً من الجدول أولاً')` نص مباشر → خطأ |
| `product_main_panel.py` | `tr('اختر منتجاً أولاً')` نص مباشر → خطأ |
| `product_form.py` | `"منتج جديد"` hardcoded بدل `tr("new_product")` |

### 1.3 ملفات غير موجودة يتم استيرادها

| الاستيراد | الملف المستورد | البديل |
|-----------|--------------|--------|
| `from ui.widgets.mixins.edit import EditModeMixin` | `ui/widgets/mixins/edit.py` → **غير موجود** | `from ui.widgets.mixins.form_mixins import EditModeMixin` |
| `from ui.widgets.theme.styles import wrap_in_scroll, tab_style` | `ui/widgets/theme/styles.py` → **غير موجود** | `wrap_in_scroll` من `ui.widgets.theme.builders`, `tab_style` من `ui.widgets.theme.layout_styles` |
| `from ui.widgets.panels.form_parts import FormGroup, spin_field, ...` | `ui/widgets/panels/form_parts.py` → **غير موجود** | كل الأدوات موزعة على `form_group.py`, `form_fields.py`, `form_badges.py`, `form_buttons.py`, `form_labels.py` |
| `from ui.widgets.tables.items import make_item, colored_item` | `ui/widgets/tables/items.py` → **غير موجود** | `from ui.widgets.tables.tables import make_item, colored_item` |
| `from ui.events import bus` | `ui/events.py` → **محذوف** | `from ui.widgets.core.events import bus` |
| `from ui.app_settings import _C` | `ui/app_settings.py` → **غير موجود** | `from ui.theme import _C` |
| `from ui.widgets.shared.list_panel_with_shared import SharedItemsListPanel` | `ui/widgets/shared/list_panel_with_shared.py` → موجود ✅ |
| `from ui.widgets.mixins.edit import EditModeMixin` | غير موجود | `from ui.widgets.mixins.form_mixins import EditModeMixin` |

### 1.4 مشاكل bus signals

`bus.data_changed` محذوف في النظام الجديد، لكن لا يزال يُستخدم في:
- `ui/tabs/costing/product/product_main_panel.py`: `bus.data_changed.connect(...)` و `bus.data_changed.emit()`
- `ui/tabs/costing/machine/machine_op_form.py`: `bus.data_changed.connect(...)`
- `ui/tabs/costing/labor/labor_op_form.py`: `bus.data_changed.connect(...)`
- `ui/tabs/costing/shared/bom_tree.py`: لا يوجد إشكال (يستخدم `bus.theme_changed` ✅)

البديل:
- للاشتراك: `bus.company_data_changed.connect(fn)` (تحتاج تعديل الـ slot لقبول `company_id`)
- للإطلاق: `emit_company_data_changed()`

---

## 2. الملفات التي تحتاج إنشاء

### 2.1 `ui/widgets/mixins/edit.py` (re-export بسيط)
**لا نريد re-export** → بدلاً من ذلك نُصلح كل استيراد مباشرة في الملف المستخدم.

### 2.2 `ui/widgets/theme/styles.py` (re-export)
**لا نريد re-export** → نُصلح كل استيراد مباشرة.

### 2.3 `ui/widgets/panels/form_parts.py` (re-export)
**لا نريد re-export** → نُصلح كل استيراد مباشرة.

### 2.4 `ui/widgets/tables/items.py` (re-export)
**لا نريد re-export** → نُصلح كل استيراد مباشرة.

---

## 3. خطة التنفيذ المرحلية

### المرحلة A: إصلاح imports الخاطئة (أعلى أولوية)

#### A1 — إصلاح `ui/app_settings.py` imports
كل ملف يستورد من `ui.app_settings` يجب تحويله إلى `ui.theme`:

**الملفات المتأثرة:**
- `ui/tabs/costing/machine_tab.py` — سطر `from ui.app_settings import _C`
- `ui/tabs/costing/labor_tab.py` — سطر `from ui.app_settings import _C`
- `ui/tabs/costing/shared/bulk_replace/bulk_replace_helpers.py`
- `ui/tabs/costing/shared/bulk_replace/_operation_section.py`
- `ui/tabs/costing/shared/scenario_comparison_widget.py`
- `ui/tabs/costing/shared/bom_scenarios_panel.py`
- `ui/tabs/costing/shared/raw_variants_panel.py`
- `ui/tabs/costing/shared/machine_op_rows_editor.py`
- `ui/tabs/costing/product/form/_header_bar.py`
- `ui/tabs/costing/product/product_main_panel.py`

#### A2 — إصلاح `ui.widgets.mixins.edit` imports
**الملفات المتأثرة:**
- `ui/tabs/costing/machine/machine_form.py`
- `ui/tabs/costing/machine/machine_op_form.py`

**الإصلاح:** `from ui.widgets.mixins.form_mixins import EditModeMixin`

#### A3 — إصلاح `ui/widgets/theme/styles.py` imports
**الملفات المتأثرة:**
- `ui/tabs/costing/machine/machine_form.py` — `wrap_in_scroll`
- `ui/tabs/costing/machine/machine_op_form.py` — `wrap_in_scroll`
- `ui/tabs/costing/labor/labor_settings.py` — `wrap_in_scroll`
- `ui/tabs/costing/product/form/_header_bar.py` — `wrap_in_scroll`
- `ui/tabs/costing_section.py` — `tab_style`

**الإصلاح:**
- `wrap_in_scroll` → `from ui.widgets.theme.builders import wrap_in_scroll`
- `tab_style` → `from ui.widgets.theme.layout_styles import tab_style`

#### A4 — إصلاح `ui/widgets/panels/form_parts.py` imports
**الملفات المتأثرة:**
- `ui/tabs/costing/machine/machine_form.py`
- `ui/tabs/costing/machine/machine_op_form.py`
- `ui/tabs/costing/labor/labor_settings.py`
- `ui/tabs/costing/raw/raw_input_panel.py`
- `ui/tabs/costing/labor/labor_op_form.py`

**الإصلاح:**
```python
# بدل: from ui.widgets.panels.form_parts import FormGroup, spin_field, labeled_widget, ResultBadge, ModeBadge
from ui.widgets.panels.form_group  import FormGroup
from ui.widgets.panels.form_fields import spin_field, labeled_widget
from ui.widgets.panels.form_badges import ResultBadge, ModeBadge
from ui.widgets.panels.form_labels import hint_label
```

#### A5 — إصلاح `ui/widgets/tables/items.py` imports
**الملفات المتأثرة:**
- `ui/tabs/costing/product/product_table.py`
- `ui/tabs/costing/raw/raw_table_panel.py`

**الإصلاح:** `from ui.widgets.tables.tables import make_item, colored_item`

#### A6 — إصلاح `ui/events.py` imports (محذوف)
**الملفات المتأثرة:**
- `ui/tabs/costing/machine/machine_op_form.py` — `from ui.events import bus`
- `ui/tabs/costing/shared/bom_tree.py` — `from ui.events import bus`
- `ui/tabs/costing/labor/labor_settings.py` — `from ui.events import bus`
- `ui/tabs/costing/shared/raw_variants_panel.py` — `from ui.events import bus`
- `ui/tabs/costing/shared/machine_op_rows_editor.py` — `from ui.events import bus`
- `ui/tabs/costing/shared/bulk_replace/bulk_replace_products_panel.py` — `from ui.events import bus`
- `ui/tabs/costing/product/product_main_panel.py` — `from ui.events import bus`
- `ui/tabs/costing/labor/labor_op_form.py` — `from ui.events import bus`

**الإصلاح:** `from ui.widgets.core.events import bus`

#### A7 — إصلاح `bus.data_changed` المحذوف
**الملفات المتأثرة:**

| الملف | المشكلة | الإصلاح |
|-------|---------|---------|
| `machine_op_form.py` | `bus.data_changed.connect(self._refresh_machines)` | `bus.company_data_changed.connect(lambda _: self._refresh_machines())` |
| `product_main_panel.py` | `bus.data_changed.connect(self._on_data_changed)` | `bus.company_data_changed.connect(lambda _: self._on_data_changed())` |
| `product_main_panel.py` | `bus.data_changed.connect(self._refresh_form_catalog)` | `bus.company_data_changed.connect(lambda _: self._refresh_form_catalog())` |
| `product_main_panel.py` | `bus.data_changed.emit()` | `emit_company_data_changed()` |
| `labor_op_form.py` | `bus.data_changed.connect(self._update_preview)` | `bus.company_data_changed.connect(lambda _: self._update_preview())` |

---

### المرحلة B: إضافة مفاتيح i18n المفقودة

#### B1 — مفاتيح جديدة تضاف لـ `ar.py` و `en.py`

```python
# ═══════════════════════════════════
# في ar.py
# ═══════════════════════════════════

# قسم التكلفة
"costing_section":    "حساب التكلفة",
"semi_product":       "نصف مصنع",
"final_product":      "منتج نهائي",
"labor":              "العمالة",
"machine":            "التشغيل",

# تبويبات الماكينات
"machines":           "الماكينات",
"machine_operations": "عمليات التشغيل",

# تبويبات العمالة
"labor_settings":     "إعدادات العمالة",
"labor_operations":   "عمليات العمالة",

# منتجات
"select_product_first":      "اختر منتجاً من الجدول أولاً",
"select_product_to_delete":  "اختر منتجاً أولاً",
"delete_orphan_components":  "حذف الناقص",

# ═══════════════════════════════════
# في en.py (المقابل الإنجليزي)
# ═══════════════════════════════════

"costing_section":    "Cost Management",
"semi_product":       "Semi-Finished",
"final_product":      "Final Product",
"labor":              "Labor",
"machine":            "Machine",
"machines":           "Machines",
"machine_operations": "Machine Operations",
"labor_settings":     "Labor Settings",
"labor_operations":   "Labor Operations",
"select_product_first":     "Select a product from the list first",
"select_product_to_delete": "Select a product first",
"delete_orphan_components": "Delete Missing",
```

---

### المرحلة C: إصلاح hardcoded strings

#### C1 — `ui/tabs/costing/product/product_form.py`
```python
# قبل
self.exit_edit_mode("منتج جديد")
# بعد
self.exit_edit_mode(tr("new_product"))
```

#### C2 — `ui/tabs/costing/product/product_main_panel.py`
```python
# كل tr() بنص عربي مباشر → مفاتيح i18n
tr('حذف الناقص')     → tr("delete_orphan_components")
tr('تعديل')          → tr("edit")
tr('خطأ')            → tr("error")
tr('تنبيه')          → tr("warning")
tr('اختر منتجاً من الجدول أولاً') → tr("select_product_first")
tr('اختر منتجاً أولاً')           → tr("select_product_to_delete")
```

#### C3 — `ui/tabs/costing/machine_tab.py`
```python
# قبل
tr('الماكينات')        → tr("machines")
tr('عمليات التشغيل')   → tr("machine_operations")
tr('التصنيفات')        → tr("categories_tab")
```

#### C4 — `ui/tabs/costing/labor_tab.py`
```python
# قبل
tr('إعدادات العمالة')  → tr("labor_settings")
tr('عمليات العمالة')   → tr("labor_operations")
tr('التصنيفات')        → tr("categories_tab")
```

#### C5 — `ui/tabs/costing_section.py`
```python
# قبل
tr('costing_section')  # مفتاح غير موجود → إضافته
tr('raw_materials')    # موجود ✅
tr('semi_product')     # إضافة
tr('final_product')    # إضافة
tr('labor')            # إضافة
tr('machine')          # إضافة
```

---

### المرحلة D: تحسينات هيكلية

#### D1 — `ui/tabs/costing/product/product_main_panel.py`
تحويل الربط بـ `bus.data_changed` (محذوف) إلى `bus.company_data_changed`:

```python
# قبل
bus.data_changed.connect(self._on_data_changed)
bus.data_changed.connect(self._refresh_form_catalog)
bus.data_changed.emit()

# بعد
bus.company_data_changed.connect(lambda _: self._on_data_changed())
bus.company_data_changed.connect(lambda _: self._refresh_form_catalog())
emit_company_data_changed()
```

**تحذير:** استخدام `lambda _: fn()` قد يسبب memory leaks في PyQt — الأفضل استخدام دوال named:
```python
def _on_company_data(self, _company_id):
    self._on_data_changed()

bus.company_data_changed.connect(self._on_company_data)
```

#### D2 — `ui/tabs/costing/machine/machine_op_form.py`
```python
# قبل
bus.data_changed.connect(self._refresh_machines)

# بعد (أفضل طريقة)
bus.company_data_changed.connect(self._on_company_data_changed)

def _on_company_data_changed(self, _company_id: int):
    self._refresh_machines()
```

#### D3 — `ui/tabs/costing/labor/labor_op_form.py`
```python
# قبل
from ui.events import bus
bus.data_changed.connect(self._update_preview)

# بعد
from ui.widgets.core.events import bus
bus.company_data_changed.connect(self._on_company_data_changed)

def _on_company_data_changed(self, _company_id: int):
    self._update_preview()
```

---

### المرحلة E: تحسينات إضافية للـ tabs/

#### E1 — `ui/tabs/costing/raw_tab.py`
الملف بسيط وصحيح لكن يستخدم strings مباشرة بدل `tr()`:
```python
# قبل
tabs.addTab(_RawSection(self.conn), "📦  الخامات")
tabs.addTab(CategoryManager(self.conn, scope="raw"), "🏷️  التصنيفات")

# بعد
tabs.addTab(_RawSection(self.conn), f"📦  {tr('raw_tab')}")
tabs.addTab(CategoryManager(self.conn, scope="raw"), f"🏷️  {tr('categories_tab')}")
```

#### E2 — `ui/tabs/costing/product_tab.py`
```python
# قبل
tabs.addTab(_ProductMainPanel(self.conn, self.product_type), f"{icon}  المنتجات")
tabs.addTab(CategoryManager(self.conn, scope=scope), "🏷️  التصنيفات")

# بعد
tabs.addTab(_ProductMainPanel(self.conn, self.product_type), f"{icon}  {tr('product_tab')}")
tabs.addTab(CategoryManager(self.conn, scope=scope), f"🏷️  {tr('categories_tab')}")
```

---

## 4. ملخص الملفات التي ستُعدَّل

| الملف | نوع التغيير | الأولوية |
|-------|------------|---------|
| `ui/i18n/ar.py` | إضافة مفاتيح جديدة | 🔴 عالية |
| `ui/i18n/en.py` | إضافة مفاتيح جديدة | 🔴 عالية |
| `ui/tabs/costing/machine_tab.py` | إصلاح imports + tr() | 🔴 عالية |
| `ui/tabs/costing/labor_tab.py` | إصلاح imports + tr() | 🔴 عالية |
| `ui/tabs/costing_section.py` | إصلاح imports + tr() | 🔴 عالية |
| `ui/tabs/costing/machine/machine_form.py` | إصلاح imports | 🔴 عالية |
| `ui/tabs/costing/machine/machine_op_form.py` | إصلاح imports + bus | 🔴 عالية |
| `ui/tabs/costing/labor/labor_op_form.py` | إصلاح imports + bus | 🔴 عالية |
| `ui/tabs/costing/labor/labor_settings.py` | إصلاح imports | 🔴 عالية |
| `ui/tabs/costing/raw/raw_input_panel.py` | إصلاح imports | 🔴 عالية |
| `ui/tabs/costing/product/product_main_panel.py` | إصلاح bus + imports + tr() | 🔴 عالية |
| `ui/tabs/costing/product/product_form.py` | إصلاح hardcoded strings | 🟡 متوسطة |
| `ui/tabs/costing/product/product_table.py` | إصلاح imports | 🔴 عالية |
| `ui/tabs/costing/raw/raw_table_panel.py` | إصلاح imports | 🟡 متوسطة |
| `ui/tabs/costing/shared/bulk_replace/bulk_replace_helpers.py` | إصلاح imports | 🔴 عالية |
| `ui/tabs/costing/shared/bulk_replace/_operation_section.py` | إصلاح imports | 🔴 عالية |
| `ui/tabs/costing/shared/bulk_replace/bulk_replace_products_panel.py` | إصلاح imports | 🔴 عالية |
| `ui/tabs/costing/shared/scenario_comparison_widget.py` | إصلاح imports | 🔴 عالية |
| `ui/tabs/costing/shared/bom_scenarios_panel.py` | إصلاح imports | 🔴 عالية |
| `ui/tabs/costing/shared/raw_variants_panel.py` | إصلاح imports | 🔴 عالية |
| `ui/tabs/costing/shared/machine_op_rows_editor.py` | إصلاح imports | 🔴 عالية |
| `ui/tabs/costing/shared/bom_tree.py` | إصلاح imports | 🔴 عالية |
| `ui/tabs/costing/raw_tab.py` | إضافة tr() | 🟢 منخفضة |
| `ui/tabs/costing/product_tab.py` | إضافة tr() | 🟢 منخفضة |

---

## 5. لا ملفات جديدة مطلوبة

جميع الإصلاحات تتم **مباشرة** في الملفات الموجودة — لا re-exports، لا wrappers:

- `ui.widgets.mixins.edit` → استدعاء مباشر من `ui.widgets.mixins.form_mixins`
- `ui.widgets.theme.styles` → استدعاء مباشر من `ui.widgets.theme.builders` و `ui.widgets.theme.layout_styles`
- `ui.widgets.panels.form_parts` → استدعاء مباشر من الملفات المقسمة
- `ui.widgets.tables.items` → استدعاء مباشر من `ui.widgets.tables.tables`
- `ui.events` → استدعاء مباشر من `ui.widgets.core.events`
- `ui.app_settings` → استدعاء مباشر من `ui.theme`

---

## 6. التحقق النهائي

بعد تطبيق كل الإصلاحات، الهيكل الصحيح سيكون:

```
tabs/costing/
├── costing_section.py          ← orchestrator: يبني tabs
├── raw_tab.py                  ← orchestrator: يجمع RawSection + CategoryManager
├── labor_tab.py                ← orchestrator: يجمع settings + ops + categories
├── machine_tab.py              ← orchestrator: يجمع machines + ops + categories
├── product_tab.py              ← orchestrator: يجمع ProductMainPanel + CategoryManager
│
├── raw/
│   ├── raw_section.py          ← orchestrator: يجمع form + table
│   ├── raw_input_panel.py      ← UI: يستخدم BaseCrudForm + ItemService
│   └── raw_table_panel.py      ← UI: يستخدم BaseListPanel + SharedOpsMixin
│
├── labor/
│   ├── labor_settings.py       ← UI: إعدادات + emit
│   ├── labor_op_form.py        ← UI: يستخدم BaseCrudForm + LaborOpService
│   └── labor_op_table.py       ← UI: يستخدم SharedItemsListPanel
│
├── machine/
│   ├── machine_form.py         ← UI: يستخدم EditModeMixin + MachineService
│   ├── machine_table.py        ← UI: يستخدم SharedItemsListPanel
│   ├── machine_op_form.py      ← UI: يستخدم EditModeMixin + MachineOpService
│   └── machine_op_table.py     ← UI: يستخدم SharedItemsListPanel
│
├── product/
│   ├── product_main_panel.py   ← orchestrator: يجمع form + table + tree
│   ├── product_form.py         ← UI: يستخدم LiveConnMixin + ScenarioService
│   ├── product_table.py        ← UI: يستخدم BaseListPanel
│   ├── _catalog_provider.py    ← helper: يبني catalog
│   └── _orphan_handler.py      ← helper: يعالج orphans
│
└── shared/
    ├── bom_tree.py             ← UI: يعرض BOM tree
    ├── bom_scenarios_panel.py  ← UI: يدير scenarios
    ├── scenario_comparison_widget.py ← UI: مقارنة
    ├── raw_variants_panel.py   ← UI: variants
    ├── machine_op_rows_editor.py ← UI: op rows
    └── bulk_replace/           ← نافذة الاستبدال الشامل
```

كل طبقة تستدعي الطبقة التي تحتها فقط — لا تجاوز للطبقات.