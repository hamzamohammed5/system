# خطة إعادة الهيكلة — Costing Tabs
**التاريخ:** 2026-05-30  
**الهدف:** تحويل `ui/tabs/` لتصبح orchestrators نظيفة تستدعي services/ وwidgets/ الجاهزة

---

## 1. المشاكل الموجودة حالياً

### 1.1 مسارات imports خاطئة (يُصلَح بتعديل الـ import مباشرة)

| الملف | Import الخاطئ | يُستبدل بـ |
|-------|--------------|-----------|
| `raw_tab.py`, `product_tab.py`, `labor_tab.py`, `machine_tab.py` | `from ui.widgets.shared.tab_section_base import TabSectionBase` | `from ui.widgets.base.tab_section import TabSectionBase` |
| `raw_tab.py`, `product_tab.py`, `labor_tab.py`, `machine_tab.py` | `from ui.widgets.shared.category_manager import CategoryManager` | `from ui.widgets.managers.category import CategoryManager` |
| `product_main_panel.py` | `from ui.widgets.shared.base_warning_bar import BaseWarningBar` | `from ui.widgets.components.notification import BaseWarningBar` |
| `raw_table_panel.py` | `from ui.helpers import confirm_delete` | `from ui.widgets.dialogs.confirm import confirm_delete` |

---

### 1.2 DB access مباشر من UI (يجب المرور عبر services)

| الملف | Import المباشر | البديل |
|-------|--------------|--------|
| `product_form.py` | `from db.costing.bom_scenarios_repo import fetch_default_scenario, insert_scenario, fetch_bom_for_scenario` | `ScenarioService` |
| `product_form.py` | `from db.shared.items_repo import fetch_item, fetch_orphan_bom_rows` | `ItemService` / `ProductService` |
| `product_main_panel.py` | `from db.shared.items_repo import fetch_item, delete_item` | `ItemService` |
| `_orphan_handler.py` | `from db.shared.items_repo import fetch_item, fetch_orphan_bom_rows, delete_orphan_bom_rows, cleanup_empty_products_after_orphan_fix` | `ProductService.fix_orphans()` + إبقاء `cleanup_empty_products_after_orphan_fix` مؤقتاً (غير موثق في ProductService) |
| `bulk_replace_helpers.py` | SQL مباشر + `fetch_items_by_type`, `fetch_all_labor_ops`, `fetch_all_machine_ops` | `BulkReplaceService.fetch_candidates()` و `fetch_affected_products()` |
| `bom_tree.py` → `_fetch_node_data` | repos مباشرة داخل data_fetcher | ✅ مقبول — هذا pattern مقصود (BomTree يملك conn) |
| `labor_settings.py` | `get_setting` / `set_setting` | ✅ مقبول — لا service موجود لهذا |
| `machine_op_form.py` | `calc_op_total_cost` من repo | ✅ مقبول — للقراءة فقط |

---

### 1.3 bus events خاطئة

| الملف | الحالي | الصحيح |
|-------|--------|--------|
| `bulk_replace_dialog.py` | `bus.data_changed.emit()` | `emit_company_data_changed()` |
| `labor_settings.py` | `bus.data_changed.emit()` | `emit_company_data_changed()` |

---

### 1.4 مشكلة fallback غير موجود

في `_catalog_provider.py`:
```python
from ui.tabs.costing.shared.catalog_builder import build_catalog  # غير موجود في system_arch
```
الـ fallback لن يعمل لكن `CatalogService` يعمل أولاً — الأثر عملياً صفر.  
**الحل:** حذف الـ fallback الميت وإبقاء `CatalogService` + الـ fallback المحلي فقط.

---

## 2. خطة التنفيذ (مرتبة حسب الأولوية)


### الخطوة 4 — تنظيف `product_main_panel.py`

```python
# قبل
from db.shared.items_repo import fetch_item, delete_item

# بعد
from services.shared.item_service import ItemService
```

```python
# في _delete_product():
# قبل
item = fetch_item(conn, pid)
delete_item(conn, pid)

# بعد
svc = ItemService(conn)
item = svc.get(pid)
svc.delete(pid)  # يرفض لو مستخدم في BOM — يحتاج force_delete أو معالجة
```

**تحدي:** `delete_item` المباشر يحذف بغض النظر، لكن `ItemService.delete()` يرفض لو مستخدم.  
**الحل:** استخدام `svc.force_delete(pid)` للمنتجات لأن حذف المنتج يتضمن BOM بطبيعته.

---

### الخطوة 5 — إصلاح bus events

في `bulk_replace_dialog.py`:
```python
from ui.widgets.core.events import emit_company_data_changed
# استبدال bus.data_changed.emit() بـ emit_company_data_changed()
```

في `labor_settings.py`: نفس الاستبدال.

---

### الخطوة 6 — تنظيف `bulk_replace_helpers.py`

الدوال `fetch_candidates` و `fetch_affected_products` يمكن إعادة توجيهها لـ `BulkReplaceService`:
```python
# استبدال SQL المباشر بـ:
from services.costing.bulk_replace_service import BulkReplaceService

def fetch_candidates(conn, child_type, exclude_id):
    return BulkReplaceService(conn).fetch_candidates(child_type, exclude_id)

def fetch_affected_products(conn, child_type, child_id):
    return BulkReplaceService(conn).fetch_affected_products(child_type, child_id)
```

---

### الخطوة 7 — تنظيف `_catalog_provider.py`

حذف الـ fallback الميت:
```python
# حذف هذا الـ fallback (catalog_builder غير موجود):
try:
    from ui.tabs.costing.shared.catalog_builder import build_catalog
    return build_catalog(conn)
except Exception:
    pass
```

---

## 3. ما هو مقبول ولا يحتاج تعديل

| الملف | السبب |
|-------|-------|
| `bom_tree.py` → `_fetch_node_data` | data_fetcher pattern مقصود، BomTree يملك conn ✅ |
| `labor_settings.py` → `get_setting/set_setting` | لا service موجود، مقبول ✅ |
| `machine_op_form.py` → `calc_op_total_cost` | قراءة فقط، مقبول ✅ |
| كل `*_form.py` الوارث من `BaseCrudForm` | نمط صحيح ✅ |
| `scenario_comparison_widget.py` | يستخدم `ScenarioService` ✅ |
| `_db_scenarios.py` | يستخدم `ScenarioService` ✅ |
| `raw_variants_panel.py` | يستخدم `VariantService` ✅ |
| `machine_op_rows_editor.py` | يستخدم `MachineOpRowsService` ✅ |
| `_save_logic.py` | يستخدم `ProductService` ✅ |

---

## 4. ترتيب الأولوية النهائي

```
🔴 Critical (يكسر التطبيق):
   الخطوة 1 — إصلاح imports المكسورة في 6 ملفات

🟡 High (يُلوّث المعمارية):
   الخطوة 2 — product_form.py
   الخطوة 3 — _orphan_handler.py
   الخطوة 4 — product_main_panel.py

🟢 Medium (تحسين):
   الخطوة 5 — bus events
   الخطوة 6 — bulk_replace_helpers.py
   الخطوة 7 — _catalog_provider.py
```


