# خطة التحسينات — تحليل الكود الحالي

> تاريخ التحليل: مايو 2026  
> المصدر: فحص ملفات `files_reference/` + ملفات UI الفعلية في السياق

---

## 1. مشاكل الـ Bus Events والأداء

### 1.1 استخدام `bus.data_changed` بدل `bus.company_data_changed`

**الملفات المتأثرة:**
- `ui/tabs/costing/labor/labor_op_table.py` — السطر: `emit_company_data_changed()` ✅ (مُعدَّل بالفعل)
- `ui/tabs/costing/machine/machine_op_table.py` — يستخدم `bus.data_changed.emit()` مباشرة ❌
- `ui/tabs/costing/machine/machine_table.py` — يستخدم `bus.data_changed.emit()` ❌
- `ui/tabs/costing/shared/raw_variants_panel.py` — يستخدم `bus.data_changed.emit()` ❌
- `ui/tabs/costing/shared/machine_op_rows_editor.py` — يستخدم `bus.data_changed.emit()` ❌
- `ui/tabs/costing/shared/bom_scenarios/_db_scenarios.py` — يستخدم `bus.data_changed.emit()` ❌

**الإصلاح المطلوب:**
```python
# من:
from ui.events import bus
bus.data_changed.emit()

# إلى:
from ui.widgets.core.events import emit_company_data_changed
emit_company_data_changed()
```

**الأولوية:** عالية — يؤثر على الأداء عند وجود شركات متعددة

---

### 1.2 تكرار الاشتراك في `bus.data_changed` بدون فصل

في `ui/tabs/costing/machine/machine_op_form.py`:
```python
bus.data_changed.connect(self._refresh_machines)
```
هذا يعني أن أي `data_changed` في أي مكان يُعيد تحميل الماكينات — يجب استخدام `company_data_changed` بدلاً منه.

---

## 2. مشاكل الـ Imports والمسارات

### 2.1 `confirm_delete` — مسارات غير موحدة

**المسار الصحيح الموثق في `ui_widgets.md`:**
```python
from ui.widgets.dialogs.confirm import confirm_delete
```

**ملفات تستخدم مسار خاطئ:**
- `ui/tabs/costing/machine/machine_table.py`:
  ```python
  from ui.helpers import confirm_delete  # ❌ غير موثق
  ```
- `ui/tabs/costing/raw/raw_table_panel.py`:
  ```python
  from ui.helpers import confirm_delete  # ❌ غير موثق
  ```

**ملفات بالمسار الصحيح (للمرجع):**
- `ui/tabs/costing/labor/labor_op_table.py` ✅
- `ui/tabs/costing/machine/machine_op_table.py` ✅
- `ui/tabs/costing/product/product_main_panel.py` ✅

---

### 2.2 `_SPLITTER_STYLE` — ألوان مُضمَّنة بدل `_C`

في `ui/tabs/costing/labor_tab.py` و `ui/tabs/costing/machine_tab.py`:
```python
_SPLITTER_STYLE = """
    QSplitter::handle { background: #e0e0e0; border-top: 1px solid #ccc; }
    QSplitter::handle:hover { background: #bbdefb; }
"""
```

يجب استخدام `_C` و `splitter_style()` من `ui/widgets/theme/styles.py`:
```python
from ui.widgets.theme.styles import splitter_style
# أو
from ui.app_settings import _C
_SPLITTER_STYLE = f"""
    QSplitter::handle {{ background: {_C['border']}; border-top: 1px solid {_C['border_med']}; }}
    QSplitter::handle:hover {{ background: {_C['accent_light']}; }}
"""
```

**الأولوية:** متوسطة — تأثير بصري عند تغيير الثيم

---

### 2.3 اشتراك `bus.theme_changed` مفقود في بعض المكونات

الملفات التالية تستخدم `_C` مباشرة في `_build()` لكن **لا تربط** `bus.theme_changed`:
- `ui/tabs/costing/shared/bom_scenarios_panel.py` — لا يوجد `bus.theme_changed.connect()`
- `ui/tabs/costing/labor/labor_op_form.py` — لا يوجد `bus.theme_changed.connect()`
- `ui/tabs/costing/product/form/_header_bar.py` ✅ موجود
- `ui/tabs/costing/shared/bom_tree.py` ✅ موجود
- `ui/tabs/costing/shared/machine_op_rows_editor.py` ✅ موجود

---

## 3. مشاكل معمارية (Architecture)

### 3.1 `_ProductMainPanel` — فصل مفقود في `_on_data_changed`

في `product_main_panel.py`:
```python
def _on_data_changed(self):
    pid = self._prod_table.selected_pid()
    if pid is not None:
        self._refresh_for_product(pid)
```

المشكلة: `_on_data_changed` يُستدعى لأي حدث في التطبيق كله، حتى لو لم يكن له علاقة بالمنتجات. يجب استخدام `company_data_changed` + `_should_respond_to_company()` من `SafeConnMixin`.

---

### 3.2 `BomTree._fetch_bom_with_row_id_by_scenario` — PRAGMA على كل استدعاء

```python
cols = {r["name"] for r in
        self._conn.execute("PRAGMA table_info(bom)").fetchall()}
```

هذا الاستعلام يُنفَّذ في كل مرة يُحمَّل فيها سيناريو. يجب تخزينه مؤقتًا (cache) عند أول استدعاء.

**الإصلاح:**
```python
# في __init__:
self._bom_cols: set | None = None

def _get_bom_cols(self) -> set:
    if self._bom_cols is None:
        self._bom_cols = {r["name"] for r in
            self._conn.execute("PRAGMA table_info(bom)").fetchall()}
    return self._bom_cols
```

---

### 3.3 `_SaveLogic` — لا يتحقق من تعارض الأسماء

`ProductService.save()` لا يتحقق من وجود منتج بنفس الاسم. يجب إضافة تحقق قبل الحفظ:
```python
# في _SaveLogic.save():
existing = conn.execute(
    "SELECT id FROM items WHERE name=? AND type=? AND id!=?",
    (name, product_type, editing_id or -1)
).fetchone()
if existing:
    QMessageBox.warning(parent_widget, "تنبيه", f"يوجد منتج بنفس الاسم: {name}")
    return None
```

---

### 3.4 `ScenarioComparisonWidget._calc_scenario_cost` — تكرار منطق `calc_cost`

الدالة تُعيد كتابة منطق حساب التكلفة الموجود في `models/costing.py` (`calc_product_cost`). يجب الاستفادة من:
```python
from models.costing import calc_product_cost
total_cost, breakdown = calc_product_cost(self.conn, self._item_id, scenario_id=sc_id)
```

---

## 4. مشاكل UX/UI

### 4.1 `_LaborOpForm` — لا يُطلق `saved` signal

`BaseCrudForm` يوفر `saved = pyqtSignal(int)` لكن `LaborOpForm` لا يستفيد منه لتحديث الجدول مباشرة.
الجدول يعتمد على `bus.data_changed` بدلاً من ربط مباشر — هذا مقبول لكن يمكن تحسينه.

---

### 4.2 `_ProductMainPanel` — زر "تعديل المحدد" مخفي بدون وصول واضح

عند تحميل منتج جديد، الزرار في `_ProductTable` تعمل لكن `BaseWarningBar` يختفي قبل أن يرى المستخدم المشكلة. يُقترح إضافة `auto_hide=0` للـ orphan warnings.

---

### 4.3 `BulkReplaceDialog` — لا يُغلق تلقائيًا عند تعديل الكمية فقط

```python
if do_replace:
    self.accept()
else:
    self._products_panel.reload()  # يبقى مفتوحًا
```

يُقترح إضافة زر "إغلاق بعد التطبيق" أو تغيير السلوك.

---

### 4.4 `_BomScenariosPanel` — لا يعرض عدد المكونات في كل سيناريو

الـ ComboBox يعرض اسم السيناريو فقط. يُقترح إضافة عدد المكونات:
```python
# بدل:
f"{star}{sc['name']}"
# الأفضل:
f"{star}{sc['name']}  ({count} مكون)"
```

---

## 5. مشاكل الأداء

### 5.1 `_ProductTable._fill_row` — `calc_cost` على كل صف

```python
cost = calc_cost(self.conn, row["id"])
```

يُستدعى لكل منتج في الجدول — إذا كان هناك 100 منتج، يُنفَّذ 100 استعلام متشعب. يجب:
1. تحميل التكاليف في دفعة واحدة (batch)
2. أو تأجيل الحساب (lazy loading) للصف المختار فقط

---

### 5.2 `fetch_affected_products` في `bulk_replace_helpers.py` — `calc_cost` لكل منتج

```python
"cost": calc_cost(conn, r["parent_id"]),
```

نفس المشكلة — يجب إضافة خيار `include_cost=False` افتراضيًا.

---

### 5.3 `catalog_builder._fetch_shared` — يفتح ويغلق `central_conn` في كل مرة

```python
central = get_central_connection()
rows = central.execute(...).fetchall()
central.close()
```

يُستدعى هذا مع كل `ComponentRow.refresh_catalog()`. يجب تخزينه مؤقتًا (TTL cache).

---

## 6. مشاكل الـ Error Handling

### 6.1 `_MachineOpForm._on_machine_changed` — يبتلع الأخطاء بصمت

```python
try:
    svc = MachineService(self._live_conn())
    m   = svc.get(machine_id)
except Exception:
    return
```

لو `_live_conn()` فشل (لا توجد شركة نشطة)، يرجع بصمت بدون إشعار المستخدم.

---

### 6.2 `CostingSection._build` — try/except يلتقط كل الأخطاء ❓

```python
try:
    widget = factory()
except Exception as e:
    widget = _make_error_tab(f"خطأ في تحميل التبويب: {e}")
```

هذا جيد ✅ لكن لا يُسجَّل الخطأ في أي log. يُقترح إضافة `logging.exception(e)`.

---

## 7. تحسينات الكود (Code Quality)

### 7.1 `_SPLITTER_STYLE` — ثابت مكرر في ملفين

نفس الثابت موجود في `labor_tab.py` و `machine_tab.py`. يجب نقله إلى ملف مشترك أو استخدام `splitter_style()` من `ui/widgets/theme/styles.py`.

---

### 7.2 `LaborOpTable._fill_table_row` — حساب `cost` مع كل صف

```python
rate = self._settings.get_hourly_rate()
minutes = item.get("minutes", 0)
cost = (minutes / 60.0) * rate
```

يُستدعى `get_hourly_rate()` لكل صف. يجب حسابه مرة واحدة قبل حلقة الصفوف.

---

### 7.3 `RawTablePanel._on_delete_item` — import داخل الدالة

```python
def _on_delete_item(self, item_id, item_name: str):
    from PyQt5.QtWidgets import QMessageBox
    from ui.helpers import confirm_delete
    from db.shared.items_repo import delete_item
```

يُقترح نقل الـ imports للأعلى بدلاً من داخل الدالة.

---

### 7.4 `BomTree._delete_node` — منطق معقد يستحق تقسيمًا

الدالة تتعامل مع 3 حالات مختلفة (سيناريو، مكون فرعي في semi، مكون رئيسي). يُقترح تقسيمها إلى:
- `_delete_from_scenario(node, parent)`
- `_delete_from_main_bom(node)`

---

## 8. ملاحظات على `_db_scenarios.py`

### 8.1 `_db_delete` — لا يتحقق من أن السيناريو هو الأخير

```python
def _db_delete(self, scenario_id: int) -> bool:
    result = delete_scenario(self.conn, scenario_id)
```

`delete_scenario` في `bom_scenarios_repo.py` يرفض لو آخر سيناريو ✅ لكن `_BomScenariosPanel._delete()` يتحقق أيضًا من `len(self._scenarios) <= 1` — التحقق مزدوج وغير ضروري.

---

## 9. خلاصة الأولويات

| الأولوية | المشكلة | الملفات المتأثرة | الجهد |
|----------|---------|-----------------|-------|
| 🔴 عالية | استخدام `emit_company_data_changed` بدل `bus.data_changed.emit()` | 6 ملفات | صغير |
| 🔴 عالية | توحيد import `confirm_delete` | 2 ملفات | صغير |
| 🟠 متوسطة | ربط `bus.theme_changed` في `_BomScenariosPanel` | 1 ملف | صغير |
| 🟠 متوسطة | `_SPLITTER_STYLE` بألوان ثابتة — لا يتحدث مع الثيم | 2 ملفات | صغير |
| 🟠 متوسطة | `PRAGMA table_info(bom)` يُنفَّذ بكثرة — يحتاج cache | 1 ملف | متوسط |
| 🟠 متوسطة | `_on_data_changed` يستجيب لكل الأحداث — يحتاج فلترة | 1 ملف | متوسط |
| 🟡 منخفضة | `calc_cost` على كل صف في `_ProductTable` — batch loading | 1 ملف | كبير |
| 🟡 منخفضة | تكرار منطق الحساب في `ScenarioComparisonWidget` | 1 ملف | متوسط |
| 🟡 منخفضة | `catalog_builder._fetch_shared` بدون cache | 1 ملف | متوسط |
| 🟡 منخفضة | `import` داخل الدوال في `RawTablePanel` | 1 ملف | صغير |
| ⚪ تحسين | إضافة عدد المكونات في عرض السيناريوهات | 1 ملف | صغير |
| ⚪ تحسين | تقسيم `_delete_node` في `BomTree` | 1 ملف | متوسط |

---

## 10. ترتيب التطبيق المقترح

### المرحلة الأولى — إصلاحات سريعة (يوم واحد)

1. استبدال `bus.data_changed.emit()` بـ `emit_company_data_changed()` في الملفات الـ6
2. توحيد import `confirm_delete` في `machine_table.py` و `raw_table_panel.py`
3. إضافة `bus.theme_changed.connect(self._apply_theme)` في `_BomScenariosPanel`
4. إصلاح `_SPLITTER_STYLE` في `labor_tab.py` و `machine_tab.py`

### المرحلة الثانية — تحسينات الأداء (يومان)

5. إضافة cache لـ `PRAGMA table_info(bom)` في `BomTree`
6. حساب `rate` مرة واحدة في `LaborOpTable._fill_table_row`
7. إضافة TTL cache لـ `catalog_builder._fetch_shared`

### المرحلة الثالثة — تحسينات معمارية (3 أيام)

8. استخدام `calc_product_cost` في `ScenarioComparisonWidget`
9. تقسيم `_delete_node` في `BomTree`
10. إضافة فلترة `company_data_changed` في `_ProductMainPanel._on_data_changed`
11. Batch loading للتكاليف في `_ProductTable`

---

## ملاحظة

جميع المسارات والأسماء الواردة في هذه الخطة مستخرجة من الملفات الفعلية في السياق. لم يُضف أي ملف أو دالة غير موثقة في `files_reference/`.


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