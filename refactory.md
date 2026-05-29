# خطة التحسينات — وحدة costing UI

> **ملاحظة:** كل التحسينات مبنية على الملفات الموجودة فعلاً في السياق وموثقة في `files_reference/`.
> لا يُستخدم أي import أو مسار غير موجود في الكود.

---

## فهرس

| # | التحسين | الأولوية | الملفات المتأثرة |
|---|---------|----------|-----------------|
| 1 | [توحيد import الـ LiveConnMixin](#1-توحيد-import-الـ-liveconnmixin) | عالية | `product_main_panel`, `product_form` |
| 2 | [حذف import قديم في product_form](#2-حذف-import-قديم-في-product_form) | عالية | `product_form.py` |
| 3 | [تبسيط _on_data_changed في product_main_panel](#3-تبسيط-_on_data_changed) | متوسطة | `product_main_panel.py` |
| 4 | [توحيد _check_orphans — دمج الـ conn الاختياري](#4-توحيد-_check_orphans) | متوسطة | `product_main_panel.py` |
| 5 | [استخدام emit_company_data_changed بدل bus.data_changed في _orphan_handler](#5-توحيد-bus-events-في-_orphan_handler) | متوسطة | `_orphan_handler.py` |
| 6 | [توحيد import confirm_delete](#6-توحيد-import-confirm_delete) | منخفضة | `product_main_panel.py` |
| 7 | [تحسين _build_extra_header_actions في product_table](#7-تحسين-_build_extra_header_actions) | منخفضة | `product_table.py` |
| 8 | [إزالة cleanup_empty_products بعد orphan fix — مراجعة السلوك](#8-مراجعة-cleanup_empty_products) | منخفضة | `_orphan_handler.py` |
| 9 | [توحيد tab_section_base — إضافة conn تلقائي في CostingSection](#9-conn-في-costingsection) | متوسطة | `costing_section.py` |
| 10 | [ربط bus.theme_changed في BomTree](#10-ربط-bustheme_changed-في-bomtree) | منخفضة | `bom_tree.py` |

---

## التفاصيل

---

### 1. توحيد import الـ LiveConnMixin

**المشكلة:**
- `product_main_panel.py` يستورد من `ui.widgets.shared.connection_mixin`:
  ```python
  from ui.widgets.shared.connection_mixin import LiveConnMixin
  ```
- بينما ملفات أخرى في نفس المشروع (`machine_form.py`, `machine_op_form.py`) تستورد من المسار الموثق:
  ```python
  from ui.widgets.core.conn import LiveConnMixin
  ```

**التحسين:**
تغيير import في `product_main_panel.py` و `product_form.py` للمسار الموثق في `files_reference/ui_widgets.md`.

**الملفات:**
- `ui/tabs/costing/product/product_main_panel.py` — السطر 13
- `ui/tabs/costing/product/product_form.py` — استخدام `ui.widgets.shared.connection_mixin`

**التغيير:**
```python
# قبل
from ui.widgets.shared.connection_mixin import LiveConnMixin

# بعد
from ui.widgets.core.conn import LiveConnMixin
```

**الملاحظة:** يجب التأكد أن `ui.widgets.shared.connection_mixin` هو alias أو أن `LiveConnMixin` موجود في كلا المسارين قبل التغيير. إن لم يكن كذلك، يُطبَّق التغيير بحذر مع اختبار.

---

### 2. حذف import قديم في product_form

**المشكلة:**
`product_form.py` يستورد `ComponentRow` من مسار قديم:
```python
from ui.widgets.shared.component_row._row_widget import ComponentRow
```
بينما `_rows_manager.py` يستورد بشكل صحيح من:
```python
from ui.widgets.components.component_row.widget import ComponentRow
```
وهو المسار الموثق في `files_reference/ui_widgets.md`.

**التحسين:**
حذف أو تصحيح هذا الـ import في `product_form.py` لأنه يُستخدم فقط في type hint داخلي ولا يُستدعى مباشرة (الاستدعاء الفعلي يمر عبر `_RowsManager`).

**الملف:** `ui/tabs/costing/product/product_form.py` — السطر 15

```python
# حذف هذا السطر (غير ضروري — ComponentRow يُستخدم فقط في _rows_manager)
from ui.widgets.shared.component_row._row_widget import ComponentRow
```

---

### 3. تبسيط _on_data_changed

**المشكلة:**
في `product_main_panel.py`، دالتا `_on_data_changed` و `_on_product_selected` تكرران نفس المنطق بشكل كبير:

```python
def _on_data_changed(self):
    pid = self._prod_table.selected_pid()
    if pid is None:
        return
    try:
        conn = self._live_conn()
        self._check_orphans(pid, conn)
        self._bom_tree.load(conn, pid)
    except Exception:
        pass

def _on_product_selected(self, pid: int | None):
    if pid is None:
        self._bom_tree.clear_tree()
        self._warning.setVisible(False)
        return
    try:
        conn = self._live_conn()
        self._check_orphans(pid, conn)
        self._bom_tree.load(conn, pid)
    except Exception:
        pass
```

**التحسين:**
استخراج المنطق المشترك في دالة واحدة `_refresh_for_product`:

```python
def _refresh_for_product(self, pid: int):
    """تحديث الـ warning bar والـ BOM tree لمنتج محدد."""
    try:
        conn = self._live_conn()
        self._check_orphans(pid, conn)
        self._bom_tree.load(conn, pid)
    except Exception:
        pass

def _on_data_changed(self):
    pid = self._prod_table.selected_pid()
    if pid is not None:
        self._refresh_for_product(pid)

def _on_product_selected(self, pid: int | None):
    if pid is None:
        self._bom_tree.clear_tree()
        self._warning.setVisible(False)
        return
    self._refresh_for_product(pid)
```

**الملف:** `ui/tabs/costing/product/product_main_panel.py`

---

### 4. توحيد _check_orphans

**المشكلة:**
`_check_orphans` تقبل `conn=None` وتُنشئ conn داخلياً إن لم يُمرر، لكن كل استدعاءاتها تمرر `conn` بالفعل. هذا يُربك القارئ.

```python
def _check_orphans(self, pid: int, conn=None):
    if conn is None:
        conn = self._live_conn()
    ...
```

**التحسين:**
إزالة القيمة الافتراضية وجعل `conn` معاملاً إلزامياً، بما يتوافق مع طريقة الاستخدام الفعلية:

```python
def _check_orphans(self, pid: int, conn):
    orphans = self._orphan.fetch(conn, pid)
    item    = fetch_item(conn, pid)
    name    = item["name"] if item else f"ID {pid}"
    self._warning.show_orphans(orphans, name)
```

**الملف:** `ui/tabs/costing/product/product_main_panel.py`

---

### 5. توحيد bus events في _orphan_handler

**المشكلة:**
`_orphan_handler.py` يستخدم `bus.data_changed.emit()` مباشرة، بينما ملفات أخرى مثل `raw_table_panel.py` تستخدم:
```python
from ui.widgets.core.events import emit_company_data_changed
```

حسب `files_reference/models&services.md`:
> استخدم `bus.company_data_changed.emit(cid)` بدل `bus.data_changed.emit()` — أكثر دقة وأفضل أداءً.

**التحسين:**
استبدال `bus.data_changed.emit()` بـ `emit_company_data_changed()` من `ui.widgets.core.events`:

```python
# قبل
from ui.events import bus
bus.data_changed.emit()

# بعد
from ui.widgets.core.events import emit_company_data_changed
emit_company_data_changed()
```

**الملف:** `ui/tabs/costing/product/_orphan_handler.py`

**تحذير:** يجب مراجعة أن `emit_company_data_changed` متاحة وتحتاج company_id أو لا — راجع `ui/widgets/core/events.py` قبل التطبيق.

---

### 6. توحيد import confirm_delete

**المشكلة:**
`product_main_panel.py` يستورد `confirm_delete` من:
```python
from ui.helpers import confirm_delete
```
بينما الملفات الأخرى (`labor_op_table.py`, `machine_op_table.py`) تستورد من المسار الموثق:
```python
from ui.widgets.dialogs.confirm import confirm_delete
```

**التحسين:**
```python
# قبل
from ui.helpers import confirm_delete

# بعد
from ui.widgets.dialogs.confirm import confirm_delete
```

**الملف:** `ui/tabs/costing/product/product_main_panel.py` — السطر 8

**تحذير:** يجب التأكد من وجود `confirm_delete` في `ui.widgets.dialogs.confirm` (مُوثق في `files_reference/ui_widgets.md` — نعم موجود).

---

### 7. تحسين _build_extra_header_actions في product_table

**المشكلة:**
`product_table.py` يُضيف زر "تعديل المحدد" وزر "حذف المحدد" عبر `_build_extra_header_actions`، لكن بدون ربط الـ style الصحيح لزر الحذف:

```python
def _build_extra_header_actions(self, header):
    header.add_action("✏️ تعديل المحدد", self._trigger_edit)
    header.add_action("🗑️ حذف المحدد",   self._trigger_delete, style="danger")
```

الزر الأول بدون `style` محدد — سيأخذ `"normal"` كقيمة افتراضية. لتوحيد المظهر مع بقية الجداول:

**التحسين:**
```python
def _build_extra_header_actions(self, header):
    header.add_action("✏️ تعديل المحدد", self._trigger_edit,   style="normal")
    header.add_action("🗑️ حذف المحدد",   self._trigger_delete, style="danger")
```

**الملف:** `ui/tabs/costing/product/product_table.py`

---

### 8. مراجعة cleanup_empty_products بعد orphan fix

**المشكلة:**
في `_orphan_handler.py`:
```python
auto_deleted = cleanup_empty_products_after_orphan_fix(conn, [pid])
```
هذه الدالة تحذف المنتج تلقائياً إن أصبح فارغاً بعد حذف الـ orphans — وهو سلوك قد يفاجئ المستخدم.

**التحسين المقترح:**
بدلاً من الحذف التلقائي الصامت، إضافة تأكيد من المستخدم قبل الحذف:

```python
# في fix():
n = delete_orphan_bom_rows(conn, pid)

# فحص هل المنتج فارغ الآن؟
from db.shared.items_repo import fetch_bom
remaining = fetch_bom(conn, pid)
auto_deleted = []
if not remaining:
    from PyQt5.QtWidgets import QMessageBox
    reply = QMessageBox.question(
        self._parent, "المنتج فارغ",
        f"«{prod_name}» لم يعد يحتوي على أي مكونات.\nهل تريد حذفه تلقائياً؟",
        QMessageBox.Yes | QMessageBox.No
    )
    if reply == QMessageBox.Yes:
        auto_deleted = cleanup_empty_products_after_orphan_fix(conn, [pid])
```

**الملف:** `ui/tabs/costing/product/_orphan_handler.py`

**ملاحظة:** هذا تغيير في السلوك — يحتاج موافقة على المتطلبات قبل التطبيق.

---

### 9. conn في CostingSection

**المشكلة:**
`CostingSection` يبني الـ tabs بدون تمرير `conn` صريح:
```python
self._tabs.addTab(RawTab(), ...)
self._tabs.addTab(ProductTab("semi"), ...)
```
بينما كل الـ tabs ترث من `TabSectionBase` الذي يحصل على `conn` من `company_state` داخلياً.

هذا يعني أي خطأ في `company_state` سيظهر متأخراً عند أول استخدام للـ tab بدلاً من وقت البناء.

**التحسين:**
إضافة `try/except` حول بناء الـ tabs مع رسالة خطأ واضحة، أو — إن كان `TabSectionBase` يدعم تمرير `conn` صريح — تمريره من `CostingSection`:

```python
# في CostingSection._build():
try:
    self._tabs.addTab(RawTab(),            f"📦  {tr('raw_materials')}")
    self._tabs.addTab(ProductTab("semi"),  f"🔧  {tr('semi_product')}")
    self._tabs.addTab(ProductTab("final"), f"🏭  {tr('final_product')}")
    self._tabs.addTab(LaborTab(),          f"👷  {tr('labor')}")
    self._tabs.addTab(MachineTab(),        f"⚙️  {tr('machine')}")
except Exception as e:
    from PyQt5.QtWidgets import QLabel
    self._tabs.addTab(QLabel(f"⚠️ خطأ في تحميل التبويبات: {e}"), "خطأ")
```

**الملف:** `ui/tabs/costing_section.py`

---

### 10. ربط bus.theme_changed في BomTree

**المشكلة:**
`BomTree` يبني الـ stylesheet في `_build()` مرة واحدة ولا يُحدثه عند تغيير الثيم، بينما ملفات مثل `_OpRowsEditor`, `_RawVariantsPanel`, `ScenarioComparisonWidget` تربط `bus.theme_changed`.

**التحسين:**
إضافة:
```python
# في __init__:
bus.theme_changed.connect(self._apply_theme)

# دالة جديدة:
def _apply_theme(self, _=None):
    self.tree.setStyleSheet(f"""
        QTreeWidget {{
            background: {_C['bg_surface']};
            border: 1px solid {_C['border']};
            color: {_C['text_primary']};
        }}
        QTreeWidget::item:selected {{
            background: {_C['accent_light']};
            color: {_C['accent']};
        }}
        QTreeWidget::item:hover {{
            background: {_C['bg_hover']};
        }}
    """)
    hh = self.tree.header()
    hh.setStyleSheet(
        f"QHeaderView::section {{"
        f"  background:{_C['bg_surface_2']}; color:{_C['text_sec']};"
        f"  border:none; border-bottom:1px solid {_C['border']};"
        f"  padding:4px 6px; font-weight:bold; font-size:11px;"
        f"}}"
    )
```

**الملفات:**
- `ui/tabs/costing/shared/bom_tree.py`
- يجب إضافة `from ui.events import bus` (موجود بالفعل في الملف)

---

## ترتيب التطبيق المقترح

```
المرحلة 1 — آمنة تماماً (تغيير imports فقط):
  ① التحسين 6 — توحيد confirm_delete import
  ② التحسين 2 — حذف import قديم في product_form
  ③ التحسين 1 — توحيد LiveConnMixin import

المرحلة 2 — تحسين هيكلي (refactor بدون تغيير سلوك):
  ④ التحسين 3 — دمج _on_data_changed و _on_product_selected
  ⑤ التحسين 4 — توحيد _check_orphans signature
  ⑥ التحسين 7 — إضافة style صريح لأزرار product_table

المرحلة 3 — تحسينات وظيفية:
  ⑦ التحسين 10 — ربط theme_changed في BomTree
  ⑧ التحسين 9  — error handling في CostingSection
  ⑨ التحسين 5  — توحيد bus events (يحتاج مراجعة events.py أولاً)

المرحلة 4 — تغيير سلوك (يحتاج موافقة):
  ⑩ التحسين 8  — تأكيد المستخدم قبل حذف المنتج الفارغ
```

---

## ما لم يُدرج (خارج النطاق)

- **ملفات `ui/widgets/shared/`** — لم تُوثَّق في `files_reference` ولا نعرف محتواها الكامل.
- **`ui/helpers.py`** — غير موثق، يحتاج فحص قبل إزالة imports منه.
- **تحسينات الأداء في `catalog_builder.py`** — يمكن إضافة caching لكن يحتاج تحليل أعمق للاستخدام.
- **`TabSectionBase`** — غير موجود في السياق، لا يمكن تعديله بأمان.

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