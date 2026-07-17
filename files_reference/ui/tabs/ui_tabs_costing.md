# ui_tabs_costing.md

مرجع شامل لمسار `ui/tabs/costing/` وكل المسارات الفرعية تحته: `labor/`, `machine/`, `product/`, `product/form/`, `raw/`, `shared/`, `shared/bom_scenarios/`, `shared/bom_tree_helper/`, `shared/bulk_replace/`. يشمل أيضاً `ui/tabs/costing_section.py` (نقطة الدخول الرئيسية للقسم، تقع في `ui/tabs/` مباشرة وليست داخل مجلد `costing/`، لكنها مُدرجة هنا لأنها المُستدعي الفعلي لكل التابات الموصوفة في هذا المرجع).

---

## القسم 0: `ui/tabs/costing_section.py`

### `ui/tabs/costing_section.py`

**الغرض:** الويدجت الرئيسي لقسم "حساب التكلفة" بالكامل — هيدر علوي + `QTabWidget` يجمع كل التابات الفرعية (الخامات، نصف مصنع، منتج نهائي، العمالة، التشغيل) في واجهة واحدة موحدة.

**Imports داخلية مهمة:**
- `ui.widgets.theme.layout_styles` — `tab_style()` (ستايل الـ QTabWidget)، `apply_tab_widths()` (يحسب min-width للتابات حسب أطول نص فعلي)، `normalize_tab_widget()`.
- `ui.theme._C` — ألوان الثيم الحالي.
- `ui.widgets.core.i18n.tr` — الترجمة.
- `ui.font` — `FS_MD`, `FS_LG` (أحجام الخط).
- `ui.constants` — `SECTION_HEADER_HEIGHT`, `SECTION_HEADER_BORDER_W`, `SECTION_HEADER_PAD_RIGHT`, `COSTING_ERR_TAB_BORDER_W`, `COSTING_ERR_TAB_RADIUS`, `COSTING_ERR_TAB_PAD`.
- `ui.widgets.core.widget_mixin.WidgetMixin` — التسجيل التلقائي على تحديثات الثيم/الخط/اللغة.
- `.costing.raw_tab.RawTab`, `.costing.product_tab.ProductTab`, `.costing.labor_tab.LaborTab`, `.costing.machine_tab.MachineTab` — التابات الفرعية الأربعة الفعلية المعروضة داخل `QTabWidget`.

**من يستدعي هذا الملف:** غير محدد من المرفقات الحالية (من المتوقع أن يُستدعى من شاشة رئيسية/تنقّل أعلى مستوى، خارج نطاق هذا المرجع).

**Module-level:**
- `_make_error_tab(msg: str) -> QLabel`: تُنشئ `QLabel` كتبويب بديل لعرض رسالة خطأ منسّقة (أيقونة تحذير + نص أحمر على خلفية حمراء فاتحة بحدود) عند فشل تحميل تبويب معيّن. **ملاحظة:** الدالة معرَّفة لكنها غير مُستخدمة فعليًا حاليًا داخل `_build` (منطق try/except حولها معلَّق/مُعطَّل بالكود — راجع ملاحظات [Fix #9] أدناه).

**Classes:**
- **`CostingSection(QWidget, WidgetMixin)`**
  - `__init__(self, parent=None)`: يبني الواجهة ثم يُفعّل `_init_widget_mixin(theme=True, font=True, lang=True, data=False)`.
  - `_build(self)`: يبني `QVBoxLayout` بلا هوامش، يضيف:
    1. هيدر (`QLabel` بارتفاع ثابت `SECTION_HEADER_HEIGHT`) يعرض أيقونة القسم + عنوانه.
    2. `QTabWidget` (`self._tabs`) بعد `normalize_tab_widget()` وتطبيق `tab_style()`.
    يبني قائمة `self._tab_label_keys` (أزواج مفاتيح أيقونة/نص لكل تاب) لدعم تحديث اللغة لاحقًا، ثم قائمة `_tab_defs` (دوال lambda منشئة لكل تبويب + نص عنوانه): `RawTab()`, `ProductTab("semi")`, `ProductTab("final")`, `LaborTab()`, `MachineTab()`. يُنشئ كل تبويب فعليًا عبر استدعاء الـ `factory()` مباشرة (بدون try/except فعّال حاليًا رغم وجود كود معلَّق لذلك) ويضيفه لـ `self._tabs`. أخيرًا يستدعي `apply_tab_widths(self._tabs)` لحساب عرض التابات من المحتوى الفعلي.
  - `_refresh_style(self, *_)`: يعيد بناء stylesheet الهيدر (خلفية، حد سفلي، لون، حجم خط) من `_C` الحالية، ويعيد تطبيق `tab_style()` + `apply_tab_widths()` على `self._tabs` إن وُجد.
  - `_refresh_lang(self, *_)`: عند تغيير اللغة، يعيد كتابة نص الهيدر، ويعيد كتابة نص كل تبويب من `self._tab_label_keys` عبر `self._tabs.setTabText(i, ...)`، ثم يعيد استدعاء `apply_tab_widths()` لأن طول النص العربي/الإنجليزي يختلف.

**الثوابت على مستوى الملف:** لا يوجد متغيرات module-level بخلاف الدالة `_make_error_tab`.

**ملاحظات من التعليقات:**
- [Fix A1] استبدال `ui.app_settings._C` بـ `ui.theme._C`.
- [Fix A3] استبدال `ui.widgets.theme.styles.tab_style` بـ `ui.widgets.theme.layout_styles.tab_style`.
- [Fix C5] استخدام مفاتيح i18n صحيحة لكل التبويبات.
- [Fix #9] كان المفروض إضافة try/except حول بناء كل تبويب لعزل الأخطاء وعرض `_make_error_tab` بدلاً من انهيار القسم بالكامل — الكود الفعلي لهذا الجزء **معلَّق حاليًا** (commented out)، والاستدعاء الفعلي `widget = factory()` بدون حماية.
- [إصلاح lang] `CostingSection` مسجَّل الآن على `lang=True` (كان سابقًا `lang=False`) بحيث يتحدث الهيدر والتابات فورًا عند تبديل اللغة، مع إعادة حساب `apply_tab_widths` لأن العربي والإنجليزي مختلفان في الطول.
- [حل مركزي لمشكلة قص نص التبويبات] استخدام `apply_tab_widths()` بدل الاعتماد على `TAB_MIN_W_NORMAL` الثابت في `constants.py`، بنفس منطق حساب عرض الأزرار في `make_btn`.

---

## القسم 1: `ui/tabs/costing/` (المستوى المباشر)

### `ui/tabs/costing/raw_tab.py`

**الغرض:** التبويب الرئيسي للخامات — يجمع بين قسم الخامات (RawSection) وإدارة التصنيفات (CategoryManager) داخل QTabWidget موحّد، ويرث النمط العام من TabSectionBase.

**Imports داخلية مهمة:**
- `ui.widgets.base.tab_section.TabSectionBase` — الأساس الذي يوفر بنية التبويب الموحدة (اتصال DB، بناء التابات، تحديث اللغة).
- `ui.widgets.managers.category.CategoryManager` — شاشة إدارة تصنيفات عامة (تُستخدم بـ scope="raw").
- `ui.widgets.core.i18n.tr` — الترجمة.
- `.raw.raw_section.RawSection` — القسم الفعلي لعرض/تعديل الخامات.

**من يستدعي هذا الملف:** غير محدد من المرفقات الحالية (يُستدعى عادة من `costing_section.py` خارج هذا المسار).

**Classes:**
- **`RawTab(TabSectionBase)`**
  - `__init__(self, parent=None)`: يستورد `CompanyService` ويمرر `conn_fn=CompanyService.get_active_erp_conn` لمُنشئ الأب.
  - `_build_tabs(self, tabs: QTabWidget)`: يضيف تابين: `RawSection(self.conn)` بعنوان `tab_icon_raw + raw_tab`، و `CategoryManager(self.conn, scope="raw")` بعنوان `categories_tab_icon + categories_tab`.
  - `_tab_label(self, index: int)`: hook لإعادة بناء نص التاب حسب الفهرس عند تغيير اللغة (index 0 = الخامات، 1 = التصنيفات).

**ملاحظات من التعليقات:** [Fix E1] استبدال نصوص hardcoded بـ `tr()`.

---

### `ui/tabs/costing/machine_tab.py`

**الغرض:** التبويب الرئيسي للماكينات وعمليات التشغيل — يحتوي 3 تابات فرعية: الماكينات، عمليات التشغيل، والتصنيفات.

**Imports داخلية مهمة:**
- `ui.widgets.base.tab_section.TabSectionBase` — الأساس.
- `ui.widgets.managers.category.CategoryManager`.
- `ui.widgets.core.i18n.tr`.
- `ui.widgets.core.widget_mixin.WidgetMixin` — لتحديث الستايل الديناميكي عند تغيير الثيم.
- `ui.constants` — ثوابت أحجام الـ splitter (`MACHINE_TAB_SPLITTER_HANDLE_W`, `MACHINE_TAB_MACHINES_SPLITTER_SIZES`, `MACHINE_TAB_OPS_SPLITTER_SIZES`).
- `.machine.machine_form._MachineForm`, `.machine.machine_table._MachineTable`, `.machine.machine_op_form._MachineOpForm`, `.machine.machine_op_table._MachineOpTable`.

**من يستدعي هذا الملف:** غير محدد من المرفقات الحالية.

**Classes:**
- **`_MachinesTab(QWidget, WidgetMixin)`**
  - `__init__(self, conn, parent=None)`: يبني QSplitter رأسي يحوي `_MachineForm` فوق `_MachineTable`، بأحجام من `MACHINE_TAB_MACHINES_SPLITTER_SIZES`، والقسم الأول قابل للطي (collapsible).
  - `_refresh_style(self, *_)`: يعيد بناء stylesheet الـ splitter (لون الحدود، hover، pressed) من `ui.theme._C` عند تغيير الثيم.
- **`_MachineOpsTab(QWidget, WidgetMixin)`**
  - نفس بنية `_MachinesTab` لكن يحوي `_MachineOpForm` و `_MachineOpTable` بأحجام `MACHINE_TAB_OPS_SPLITTER_SIZES`.
  - `_refresh_style(self, *_)`: نفس منطق تحديث الـ splitter.
- **`MachineTab(TabSectionBase)`**
  - `__init__(self, parent=None)`: يمرر `conn_fn=CompanyService.get_active_erp_conn`.
  - `_build_tabs(self, tabs: QTabWidget)`: يضيف 3 تابات: `_MachinesTab`, `_MachineOpsTab`, `CategoryManager(scope="machine")`.
  - `_tab_label(self, index: int)`: يرجع نص التاب حسب index (0/1/2) لدعم تحديث اللغة الحي.

**ملاحظات من التعليقات:**
- [Fix A1] استبدال `ui.app_settings._C` بـ `ui.theme._C`.
- [Fix C3] استبدال `tr()` الخاطئة بمفاتيح i18n صحيحة.
- [Fix E-icons] استبدال إيموجي hardcoded بمفاتيح `tr()`.
- [Fix C-const] استخدام ثوابت `constants.py` بدل أحجام splitter مباشرة.
- [Fix B] تحويل `_MachinesTab`/`_MachineOpsTab` إلى `WidgetMixin`.

---

### `ui/tabs/costing/labor_tab.py`

**الغرض:** التبويب الرئيسي للعمالة — يجمع إعدادات حساب تكلفة العمالة، عمليات العمالة، والتصنيفات.

**Imports داخلية مهمة:**
- `ui.widgets.base.tab_section.TabSectionBase`.
- `ui.widgets.managers.category.CategoryManager`.
- `ui.widgets.core.i18n.tr`.
- `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.constants` — `LABOR_TAB_SPLITTER_HANDLE_W`, `LABOR_TAB_SPLITTER_SIZES`.
- `.labor.labor_settings._LaborSettingsPanel`, `.labor.labor_op_form.LaborOpForm`, `.labor.labor_op_table.LaborOpTable`.

**من يستدعي هذا الملف:** غير محدد من المرفقات الحالية.

**Classes:**
- **`_LaborOpsTab(QWidget, WidgetMixin)`**
  - `__init__(self, conn, settings, parent=None)`: يبني QSplitter رأسي يحوي `LaborOpForm(conn, settings)` فوق `LaborOpTable(conn, settings, self._form)`، بأحجام `LABOR_TAB_SPLITTER_SIZES`.
  - `_refresh_style(self, *_)`: تحديث ستايل الـ splitter عند تغيير الثيم.
- **`LaborTab(TabSectionBase)`**
  - `__init__(self, parent=None)`: يمرر `conn_fn=CompanyService.get_active_erp_conn`.
  - `_build_tabs(self, tabs: QTabWidget)`: ينشئ `_LaborSettingsPanel` مرة واحدة ويمررها لـ `_LaborOpsTab`، ثم يضيف 3 تابات: الإعدادات، عمليات العمالة، التصنيفات (`scope="labor"`).
  - `_tab_label(self, index: int)`: نص التاب حسب index (0=إعدادات، 1=عمليات، 2=تصنيفات).

**ملاحظات من التعليقات:**
- [Fix A1] `ui.theme._C` بدل `ui.app_settings._C`.
- [Fix A6] تصحيح مسار `bus` إلى `ui.widgets.core.events`.
- [Fix C4] مفاتيح i18n صحيحة.
- [Fix C-const]/[Fix B] استخدام الثوابت و WidgetMixin لـ `_LaborOpsTab`.

---

### `ui/tabs/costing/product_tab.py`

**الغرض:** التبويب الرئيسي للمنتجات، قابل لإعادة الاستخدام لنوعين: `semi` (نصف مصنع) و `final` (منتج نهائي)، حسب معامل `product_type` المُمرَّر عند الإنشاء.

**Imports داخلية مهمة:**
- `ui.widgets.base.tab_section.TabSectionBase`.
- `ui.widgets.managers.category.CategoryManager`.
- `ui.widgets.core.i18n.tr`.
- `.product.product_main_panel._ProductMainPanel`.

**من يستدعي هذا الملف:** غير محدد من المرفقات الحالية (لكن `costing_section.py` — خارج هذا المسار — يستدعيه بـ `ProductTab("semi")` و `ProductTab("final")` حسب التعليقات الظاهرة في ملفات أخرى مرفقة).

**Module-level:**
- `_SCOPE_MAP = {"semi": "semi", "final": "final"}` — تعيين نوع المنتج إلى نطاق (scope) الفئات.
- `_icon_map()`: دالة ترجع dict `{"semi": tr("tab_icon_semi"), "final": tr("tab_icon_final")}`.

**Classes:**
- **`ProductTab(TabSectionBase)`**
  - `__init__(self, product_type: str, parent=None)`: **ملاحظة مهمة**: `self.product_type` يُضبط **قبل** استدعاء `super().__init__()` لأن الأب يستدعي `_build_tabs` مباشرة أثناء البناء.
  - `_build_tabs(self, tabs: QTabWidget)`: يحسب `scope` من `_SCOPE_MAP` و`icon` من `_icon_map()`، ويضيف تابين: `_ProductMainPanel(self.conn, self.product_type)` و `CategoryManager(scope=scope)`.
  - `_tab_label(self, index: int)`: نص التاب حسب index (0=المنتج، 1=التصنيفات).

**ملاحظات من التعليقات:** [Fix E2] استبدال نصوص hardcoded بـ `tr()`.

---

## القسم 2: `ui/tabs/costing/labor/`

### `ui/tabs/costing/labor/labor_settings.py`

**الغرض:** لوحة إعدادات معايير حساب تكلفة العمالة (راتب أساسي، أيام عمل، عطلات، ساعات عمل، معامل إضافي)، مع حساب حي لسعر الساعة وحفظه في `SettingsService`.

**Imports داخلية مهمة:**
- `services.shared.settings_service.SettingsService` — تخزين/قراءة إعدادات العمالة.
- `ui.widgets.panels.form_fields.labeled_widget`, `spin_field` — بناء حقول رقمية موحدة.
- `ui.widgets.panels.form_badges.ResultBadge` — عرض نتيجة الحساب الحي.
- `ui.widgets.panels.form_group.FormGroup` — تجميع الحقول بصريًا.
- `ui.widgets.theme.builders.wrap_in_scroll` — تغليف الفورم بـ scroll area.
- `ui.widgets.core.i18n.tr`.
- `ui.widgets.core.events.emit_company_data_changed` — إشعار باقي التطبيق بتغيّر بيانات الشركة بعد الحفظ.
- `ui.constants` — أحجام وحدود spin fields.

**من يستدعي هذا الملف:** `ui/tabs/costing/labor_tab.py` (`_LaborSettingsPanel` تُنشأ في `LaborTab._build_tabs` وتُمرَّر لـ `_LaborOpsTab` ولـ `LaborOpForm`).

**Classes:**
- **`_LaborSettingsPanel(QWidget)`**
  - `__init__(self, conn, parent=None)`: يبني الواجهة ثم يستدعي `_load()`.
  - `_build(self)`: ينشئ `FormGroup` بعنوان `labor_cost_settings` تحتوي 5 حقول spin (راتب، أيام عمل، أيام عطلة، ساعات يومية، معامل إضافي) + `ResultBadge` لسعر الساعة، وربط `valueChanged` لكل حقل بـ `_update_preview`. زر حفظ في الأسفل مربوط بـ `_save`.
  - `_calc_rate(self) -> float`: يحسب `net_days = days - holidays` (بحد أدنى 1)، `net_hours = net_days * max(hours, 1)`، ثم `(salary / net_hours) * overhead`؛ يرجع 0.0 لو `net_hours` صفر.
  - `_update_preview(self)`: يحدّث `lbl_rate` بنص السعر المحسوب لكل ساعة.
  - `_load(self)`: يقرأ كل القيم من `SettingsService.get(key, default)` (القيم الافتراضية: راتب 3000، أيام عمل 25، عطلات 4، ساعات 8، معامل 1.10) ويملأ الحقول، ثم يستدعي `_update_preview`.
  - `_save(self)`: يكتب كل القيم عبر `SettingsService.set(key, value)`، يعرض `QMessageBox.information`، ثم يستدعي `emit_company_data_changed()`.
  - `get_hourly_rate(self)`: يرجع نتيجة `_calc_rate()` — واجهة عامة تُستخدم من `LaborOpForm` لحساب تكلفة كل عملية عمالة.

**ملاحظات من التعليقات:** استيراد موحّد لـ `FormGroup`, `labeled_widget`, `spin_field`, `ResultBadge`, `wrap_in_scroll` من المسارات الموثقة الجديدة.

---

### `ui/tabs/costing/labor/labor_op_form.py`

**الغرض:** فورم إضافة/تعديل عملية عمالة واحدة (اسم، دقائق، تصنيف)، مع معاينة حية للتكلفة بالاعتماد على سعر الساعة من `_LaborSettingsPanel`. يرث من `BaseCrudForm` فيغنيه عن تكرار منطق CRUD/edit-mode.

**Imports داخلية مهمة:**
- `ui.widgets.base.crud_form.BaseCrudForm` — الأساس الذي يوفر `_build`, `_add`, `_save_edit`, `_cancel`, وضع التعديل.
- `ui.widgets.panels.form_group.FormGroup`.
- `ui.widgets.panels.form_fields.spin_field`, `labeled_widget`.
- `ui.widgets.panels.form_badges.ResultBadge`.
- `ui.widgets.forms.inputs.RequiredLineEdit` — حقل نص إلزامي مع validate.
- `ui.widgets.combo.category.CategoryCombo`.
- `ui.widgets.core.events.bus` — للاشتراك في `company_data_changed`.
- `ui.widgets.core.i18n.tr`.
- `ui.constants.LABOR_FORM_SPIN_MAX_MINUTES`, `LABOR_FORM_SPIN_DEC_MINUTES`.

**من يستدعي هذا الملف:** `ui/tabs/costing/labor_tab.py` (`_LaborOpsTab` ينشئ `LaborOpForm(conn, settings)`).

**Class-level attributes:** `FORM_TITLE = tr("labor_op_form_title")`, `ADD_TEXT = "➕ + add"`, `SAVE_TEXT = "💾 + save_edit"`.

**Classes:**
- **`LaborOpForm(BaseCrudForm)`**
  - `__init__(self, conn, settings, parent=None)`: يحفظ `_settings` (مرجع لـ `_LaborSettingsPanel`)، يستدعي أب، يربط `valueChanged` لحقل الدقائق بـ `_update_preview`، ويشترك في `bus.company_data_changed` لتحديث المعاينة عند تغيّر إعدادات الشركة.
  - `_on_company_data_changed(self, _company_id=None)`: يستدعي `_update_preview()`.
  - `_build_fields(self, group: FormGroup)`: ينشئ `_inp_name` (RequiredLineEdit)، `_sp_minutes` (spin field)، `_cmb_cat` (CategoryCombo scope="labor")، `_lbl_cost` (ResultBadge)، ويضيفها كصفوف في `group`.
  - `_update_preview(self)`: يحسب `cost = (minutes/60) * rate` من `self._settings.get_hourly_rate()` ويعرضه في `_lbl_cost` مع تفصيل المعادلة.
  - `_collect(self) -> dict | None`: يتحقق من صحة `_inp_name`، يرجع `{name, minutes, category_id}` أو `None`.
  - `_do_insert(self, data: dict) -> int`: يستدعي `LaborOpService(conn).add(name, minutes, category_id=...)`.
  - `_do_update(self, op_id: int, data: dict) -> None`: يستدعي `LaborOpService(conn).update(...)`.
  - `_do_load(self, op_id: int) -> dict | None`: يجلب العملية عبر `LaborOpService(conn).get(op_id)` ويرجعها كـ dict.
  - `_fill_fields(self, data: dict) -> None`: يملأ الحقول من dict محمّل، ويستدعي `_update_preview`.
  - `_reset_fields(self) -> None`: يمسح كل الحقول ويعيد `_lbl_cost` لحالتها الافتراضية.

**ملاحظات من التعليقات:**
- [Fix A6] تصحيح مسار `bus`.
- [Fix D3] استبدال `bus.data_changed` المحذوف بـ `bus.company_data_changed`.

---

### `ui/tabs/costing/labor/labor_op_table.py`

**الغرض:** جدول عرض عمليات العمالة (محلية + مشتركة من شركات أخرى)، مع دعم حذف/استبدال شامل/نشر كعنصر مشترك. يرث من `SharedItemsListPanel` الذي يوحّد كل منطق العناصر المشتركة والفلترة.

**Imports داخلية مهمة:**
- `ui.widgets.dialogs.confirm.confirm_delete`.
- `ui.widgets.shared.list_panel_with_shared.SharedItemsListPanel` — الأساس.
- `ui.tabs.companies.shared_items_mixin.get_shared_labor_ops` — جلب العمليات المشتركة من شركات أخرى.
- `ui.tabs.costing.shared._utils.to_dict`.
- `ui.tabs.costing.shared.bulk_replace.bulk_replace_dialog.BulkReplaceDialog`.
- `ui.widgets.core.events.emit_company_data_changed`.
- `ui.widgets.core.i18n.tr`.
- `ui.widgets.tables.tables.make_item`.
- `ui.constants` — عروض أعمدة الجدول.

**من يستدعي هذا الملف:** `ui/tabs/costing/labor_tab.py` (`_LaborOpsTab` ينشئ `LaborOpTable(conn, settings, self._form)`).

**Class-level attributes:**
- `SHARED_TYPE = "labor_op"`.
- `TABLE_COLS` — قائمة عناوين الأعمدة: id, اسم العملية, تصنيف, وقت العمالة, تكلفة الوحدة.
- `FILTER_SCOPE = "labor"`.
- `TABLE_TITLE = tr("labor_op_table_title")`.
- `HAS_BULK_REPLACE = True`.

**Classes:**
- **`LaborOpTable(SharedItemsListPanel)`**
  - `__init__(self, conn, settings, form, parent=None)`: يحفظ `_settings` و`_form` قبل استدعاء الأب.
  - `_setup_column_widths(self, table)`: يضبط عروض الأعمدة 0, 2, 3, 4 من الثوابت.
  - `_fetch_local_rows(self) -> list`: يجلب كل عمليات العمالة المحلية عبر `LaborOpService(conn).list()` ويحوّلها لقائمة dicts (id, name, minutes, category_id, category_name).
  - `_get_shared_rows(self, local_rows: list) -> list`: يستدعي `get_shared_labor_ops(local_rows)`.
  - `_fill_table_row(self, r: int, item: dict)`: يحسب `cost = (minutes/60) * rate` من `self._settings.get_hourly_rate()`، يحدد بادئة/أيقونة العنصر (مشترك/منشور/عادي)، ويملأ الأعمدة الخمسة.
  - `_edit_item(self, item_id: int)`: يستدعي `self._form.load_for_edit(item_id)`.
  - `_delete_item(self, item_id: int, item_name: str)`: لو العنصر قيد التعديل حاليًا يصفّر الفورم أولاً، يطلب تأكيد الحذف، يحذف عبر `LaborOpService(conn).delete(item_id)`، ثم `emit_company_data_changed()`.
  - `_bulk_replace_item(self, item_id: int, item_name: str)`: يفتح `BulkReplaceDialog(conn, child_type="labor_op", child_id=item_id, child_name=item_name)`.
  - `_get_item_data_for_publish(self, row: dict) -> dict`: يرجع `{minutes, category_name}` لنشر العنصر كمشترك.

---

## القسم 3: `ui/tabs/costing/machine/`

### `ui/tabs/costing/machine/machine_form.py`

**الغرض:** فورم إضافة/تعديل ماكينة (اسم، سعر بالساعة، سعر بالوحدة، تصنيف).

**Imports داخلية مهمة:**
- `services.costing.machine_service.MachineService`.
- `ui.widgets.mixins.form_mixins.EditModeMixin` — منطق وضع التعديل (add/save/cancel).
- `ui.widgets.core.conn.LiveConnMixin` — اتصال حي بقاعدة البيانات.
- `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.widgets.combo.category.CategoryCombo`.
- `ui.widgets.panels.form_group.FormGroup`.
- `ui.widgets.panels.form_fields.spin_field`, `labeled_widget`.
- `ui.widgets.theme.builders.wrap_in_scroll`.
- `ui.widgets.core.events.emit_company_data_changed`.
- `ui.widgets.core.i18n.tr`, `ui.font.FS_MD`.
- `ui.constants` — أبعاد الفورم وحدود spin.

**Module-level function:**
- `buttons_row(*buttons) -> QHBoxLayout`: يبني صف أزرار أفقي بمسافة `SPACING_SM` بين كل زر + stretch نهائي.

**من يستدعي هذا الملف:** `ui/tabs/costing/machine_tab.py` (`_MachinesTab` ينشئ `_MachineForm(conn)`)، و `ui/tabs/costing/machine/machine_table.py` (يستدعي `load_for_edit` عليه).

**Classes:**
- **`_MachineForm(QWidget, EditModeMixin, LiveConnMixin, WidgetMixin)`**
  - `__init__(self, conn, parent=None)`: يبني الواجهة، يفعّل وضع التعديل عبر `init_edit_mode`.
  - `_refresh_style(self, *_)`: يلوّن `lbl_mode` بلون `accent` عند تغيير الثيم.
  - `_build(self)`: ينشئ `FormGroup` بعنوان `machine_form_title` تحتوي: اسم الماكينة، سعر/ساعة (`spin_field` + `labeled_widget`)، سعر/وحدة، تصنيف (`CategoryCombo` scope="machine")، وصف أزرار إضافة/حفظ/إلغاء.
  - `load_for_edit(self, machine_id: int)`: يجلب الماكينة عبر `MachineService(conn).get(machine_id)` ويملأ الحقول، يدخل وضع التعديل.
  - `_add(self)`: يتحقق من الاسم، يستدعي `MachineService(conn).add(name, rate_hour, rate_unit, category_id=...)`، يصفّر الفورم، `emit_company_data_changed()`.
  - `_save_edit(self)`: نفس التحقق، يستدعي `MachineService(conn).update(editing_id, ...)`.
  - `_cancel(self)`: يستدعي `_reset()`.
  - `_reset(self)`: يمسح كل الحقول ويخرج من وضع التعديل.

**ملاحظات من التعليقات:** [Fix A2]/[Fix A3]/[Fix A4] توحيد مسارات استيراد `EditModeMixin`, `wrap_in_scroll`, `FormGroup`, `spin_field`, `labeled_widget`. [Refactor] استخدام `emit_company_data_changed` بدل `bus.data_changed.emit()`.

---

### `ui/tabs/costing/machine/machine_op_form.py`

**الغرض:** فورم إضافة/تعديل عملية تشغيل (machine op) — تشمل اختيار ماكينة، اسم، تصنيف، ومحرر صفوف فرعي (`_OpRowsEditor`) لتفصيل بنود التكلفة (وقت/عدد).

**Imports داخلية مهمة:**
- `services.costing.machine_service.MachineService`, `MachineOpService`.
- `services.costing.machine_op_rows_service.MachineOpRowsService` — لحساب التكلفة الإجمالية للعملية من صفوفها.
- `ui.widgets.mixins.form_mixins.EditModeMixin`.
- `ui.widgets.core.conn.LiveConnMixin`.
- `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.widgets.combo.category.CategoryCombo`.
- `ui.widgets.panels.form_group.FormGroup`.
- `ui.widgets.panels.form_badges.ResultBadge`, `ModeBadge` — `ModeBadge` تعرض وضع الحساب (وقت/وحدة) بلون مميز.
- `ui.widgets.theme.builders.wrap_in_scroll`.
- `ui.tabs.costing.shared.machine_op_rows_editor._OpRowsEditor`.
- `ui.widgets.core.events.emit_company_data_changed`, `bus`.
- `ui.widgets.core.i18n.tr`, `ui.font.FS_MD`.
- `ui.constants` — أبعاد وحدود.

**Module-level function:**
- `buttons_row(*buttons) -> QHBoxLayout`: نفس دالة `machine_form.py`.

**من يستدعي هذا الملف:** `ui/tabs/costing/machine_tab.py` (`_MachineOpsTab` ينشئ `_MachineOpForm(conn)`)، و `ui/tabs/costing/machine/machine_op_table.py` (يستدعي `load_for_edit`).

**Classes:**
- **`_MachineOpForm(QWidget, EditModeMixin, LiveConnMixin, WidgetMixin)`**
  - `__init__(self, conn, parent=None)`: يبني الفورم، يشترك في `bus.company_data_changed` عبر named slot (`_on_company_data_changed`) لتجنب memory leaks (بدل lambda).
  - `_refresh_style(self, *_)`: يلوّن `lbl_mode`.
  - `_on_company_data_changed(self, _company_id=None)`: يستدعي `_refresh_machines()`.
  - `_build(self)`: ينشئ حقول: اسم العملية، كومبو الماكينة، `ModeBadge` (لعرض وضع الماكينة الحالية)، تصنيف، `ResultBadge` للتكلفة الإجمالية، أزرار، ثم `_OpRowsEditor` أسفل الفورم. يربط `currentIndexChanged` لكومبو الماكينة بـ `_on_machine_changed`، ويستدعي `_refresh_machines()`.
  - `_refresh_machines(self)`: يعيد تحميل قائمة الماكينات في الكومبو من `MachineService(conn).list()`، يحافظ على الاختيار الحالي إن أمكن، ثم يستدعي `_on_machine_changed()`.
  - `_on_machine_changed(self)`: يقرأ الماكينة المختارة؛ لو `rate_per_hour > 0` الوضع `"time"` وإلا `"unit"`؛ يحدّث `ModeBadge` بالسعر المناسب ولون (orange للوقت، blue للوحدة)؛ يحدّث `_rows_editor.update_rates(...)` لو الفورم مفعّل؛ يستدعي `_update_cost_label()`.
  - `_update_cost_label(self)`: لو في وضع تعديل (`_editing_id` موجود وموجب)، يحسب التكلفة الإجمالية عبر `MachineOpRowsService(conn).calc_total_cost(editing_id)` ويعرضها؛ وإلا يعرض رسالة placeholder.
  - `load_for_edit(self, op_id: int)`: يجلب العملية عبر `MachineOpService(conn).get(op_id)`، يملأ الحقول، يدخل وضع التعديل، يحمّل صفوف التشغيل عبر `_rows_editor.load_op(...)` بمعدلات الماكينة المرتبطة.
  - `_collect(self)`: يتحقق من الاسم والماكينة المختارة، يحدد `mode` من معدل الماكينة، يرجع `(name, machine_id, mode, 0.0)` أو `None`.
  - `_add(self)`: يجمع البيانات، يستدعي `MachineOpService(conn).add(...)`، `emit_company_data_changed()`، يحمّل صفوف التشغيل الفارغة للعملية الجديدة، يدخل "وضع تعديل الصفوف"، يخفي زر الإضافة، يعرض رسالة نجاح.
  - `_save_edit(self)`: يجمع البيانات، يستدعي `MachineOpService(conn).update(...)`، يحدّث معدلات `_rows_editor`، يصفّر الفورم، `emit_company_data_changed()`.
  - `_cancel(self)`: يستدعي `_reset()`.
  - `_reset(self)`: يمسح الحقول، يمسح `_rows_editor`، يخرج من وضع التعديل، يُظهر زر الإضافة.

**ملاحظات من التعليقات:**
- [Fix A2]/[Fix A3]/[Fix A6]/[Fix D2] توحيد مسارات الاستيراد واستخدام named slot بدل lambda لـ `bus.company_data_changed`.
- [Fix] `emit_company_data_changed` بدل `bus.data_changed.emit()`.

---

### `ui/tabs/costing/machine/machine_op_table.py`

**الغرض:** جدول عمليات التشغيل (machine ops) مع دعم العناصر المشتركة، حذف، استبدال شامل، ونشر كعنصر مشترك.

**Imports داخلية مهمة:**
- `models.costing.calc_machine_op_cost` — حساب التكلفة الفعلية للعملية.
- `ui.widgets.dialogs.confirm.confirm_delete`.
- `ui.widgets.shared.list_panel_with_shared.SharedItemsListPanel` — الأساس.
- `ui.tabs.costing.shared.bulk_replace.bulk_replace_dialog.BulkReplaceDialog`.
- `ui.widgets.core.events.emit_company_data_changed`.
- `ui.widgets.core.i18n.tr`.
- `ui.widgets.tables.tables.make_item`.
- `ui.constants` — عروض أعمدة الجدول (7 أعمدة).
- `.machine_op_form._MachineOpForm` (نوع فقط، للـ type hint).

**من يستدعي هذا الملف:** `ui/tabs/costing/machine_tab.py` (`_MachineOpsTab` ينشئ `_MachineOpTable(conn, form)`).

**Class-level attributes:**
- `SHARED_TYPE = "machine_op"`.
- `TABLE_COLS` — id, اسم العملية, تصنيف, اسم الماكينة, الوضع, القيمة, التكلفة.
- `FILTER_SCOPE = "machine"`.
- `TABLE_TITLE = tr("machine_op_table_title")`.
- `HAS_BULK_REPLACE = True`.

**Classes:**
- **`_MachineOpTable(SharedItemsListPanel)`**
  - `__init__(self, conn, form: _MachineOpForm, parent=None)`: يحفظ `_form`.
  - `_setup_column_widths(self, table)`: يضبط عروض الأعمدة 0-6. (ملاحظة في الكود: تمت إزالة `setAlternatingRowColors` اليدوي لأنه مطبّق مركزيًا في `_build_table`).
  - `_fetch_local_rows(self) -> list`: يجلب عمليات التشغيل المحلية عبر `MachineOpService(conn).list()`.
  - `_get_shared_rows(self, local_rows: list) -> list`: يستدعي `get_shared_machine_ops(local_rows)` من `shared_items_mixin` (مع `try/except` يرجع `[]` عند الفشل).
  - `_fill_table_row(self, r: int, item: dict)`: يحسب التكلفة عبر `calc_machine_op_cost(conn, id)` (فقط لو ليست عنصر مشترك)، يحدد بادئة/أيقونة حسب الحالة، ويملأ 7 أعمدة.
  - `_edit_item(self, item_id: int)`: `self._form.load_for_edit(item_id)`.
  - `_delete_item(self, item_id: int, item_name: str)`: يصفّر الفورم لو قيد التعديل، تأكيد، حذف عبر `MachineOpService(conn).delete(...)`، `emit_company_data_changed()`.
  - `_bulk_replace_item(self, item_id: int, item_name: str)`: يفتح `BulkReplaceDialog(child_type="machine_op", ...)`.
  - `_get_item_data_for_publish(self, row: dict) -> dict`: يرجع `{mode, value, machine_name, category_name}`.

---

### `ui/tabs/costing/machine/machine_table.py`

**الغرض:** جدول الماكينات مع دعم العناصر المشتركة، حذف، نشر، وتعديل مشترك (بدون استبدال شامل — `HAS_BULK_REPLACE = False`).

**Imports داخلية مهمة:**
- `ui.widgets.dialogs.confirm.confirm_delete`.
- `ui.widgets.shared.list_panel_with_shared.SharedItemsListPanel`.
- `ui.tabs.companies.shared_items_mixin.get_shared_machines`.
- `ui.tabs.costing.shared._utils.to_dict`.
- `ui.widgets.core.events.emit_company_data_changed`.
- `ui.widgets.core.i18n.tr`.
- `ui.widgets.tables.tables.make_item`.
- `ui.constants` — عروض أعمدة.
- `.machine_form._MachineForm`.

**من يستدعي هذا الملف:** `ui/tabs/costing/machine_tab.py` (`_MachinesTab` ينشئ `_MachineTable(conn, form)`).

**Class-level attributes:**
- `SHARED_TYPE = "machine"`.
- `TABLE_COLS` — id, اسم, تصنيف, سعر/ساعة، سعر/وحدة.
- `FILTER_SCOPE = "machine"`.
- `TABLE_TITLE = tr("machines_table_title")`.
- `HAS_BULK_REPLACE = False`.

**Classes:**
- **`_MachineTable(SharedItemsListPanel)`**
  - `__init__(self, conn, form: _MachineForm, parent=None)`: يحفظ `_form`.
  - `_setup_column_widths(self, table)`: يضبط عروض 0, 2, 3, 4.
  - `_fetch_local_rows(self) -> list`: يجلب الماكينات عبر `MachineService(conn).list()`.
  - `_get_shared_rows(self, local_rows: list) -> list`: `get_shared_machines(local_rows)`.
  - `_fill_table_row(self, r: int, item: dict)`: يملأ 5 أعمدة حسب حالة العنصر (مشترك/منشور/عادي).
  - `_edit_item(self, item_id: int)`: `self._form.load_for_edit(item_id)`.
  - `_delete_item(self, item_id: int, item_name: str)`: يصفّر الفورم لو قيد التعديل، تأكيد، حذف عبر `MachineService(conn).delete(...)`، `emit_company_data_changed()`.
  - `_get_item_data_for_publish(self, row: dict) -> dict`: يرجع `{rate_per_hour, rate_per_unit, category_name}`.
  - `_on_edit_shared(self)`: **override** لسلوك التعديل المشترك الافتراضي — يتحقق من وجود عنصر مختار، وإلا يعرض تحذير، ثم يستدعي `self._edit_shared_item(item_id, self.SHARED_TYPE, self)`.

**ملاحظات من التعليقات:** [Fix] توحيد `confirm_delete` من `ui.widgets.dialogs.confirm`، و`emit_company_data_changed` بدل `bus.data_changed.emit()`.

---

## القسم 4: `ui/tabs/costing/product/`

### `ui/tabs/costing/product/_catalog_provider.py`

**الغرض:** يبني الـ "كتالوج" الكامل (raw/semi/final/labor_op/machine_op) المطلوب لعرض خيارات المكوّنات في `ComponentRow` داخل فورم المنتج، عبر `CatalogService`، مع ترجمة مفتاح الفئة المشتركة الرمزي إلى نص معروض.

**Imports داخلية مهمة:**
- `services.costing.catalog_service.CatalogService`, `SHARED_CATEGORY_KEY`.
- `ui.widgets.core.i18n.tr`.

**من يستدعي هذا الملف:** `ui/tabs/costing/product/product_main_panel.py` (`_ProductMainPanel._get_catalog` يستدعي `build_product_catalog`).

**Module-level constants:**
- `_CATEGORY_NAME_INDEX = 2` — فهرس ثابت لموقع `category_name` داخل كل tuple من كل الأنواع في الكتالوج.

**Module-level functions:**
- `build_product_catalog(conn) -> dict`: يستدعي `CatalogService(conn).build()`، ثم يمرر كل صف من كل نوع عبر `_translate_shared_row`. يرجع dict بمفاتيح `raw`, `semi`, `final`, `labor_op`, `machine_op` وكل قيمة قائمة tuples.
- `_translate_shared_row(row: tuple) -> tuple`: لو `row[2] == SHARED_CATEGORY_KEY` يستبدلها بـ `tr("shared")` مع الحفاظ على باقي عناصر الـ tuple، وإلا يرجع الصف كما هو.

**ملاحظات من التعليقات:**
- [Refactor] `CatalogService` هو المصدر الوحيد للكتالوج، ولا يوجد fallback يستدعي repos مباشرة من tabs/.
- [Fix هيكلي 2] لا يوجد `try/except: pass` حول `CatalogService.build()` — أي خطأ فيها يظهر كما هو.
- [i18n] هذا الملف (كطبقة UI) مسؤول عن ترجمة `SHARED_CATEGORY_KEY` لأن الـ service لا يعرف شيئًا عن نظام الترجمة.

---

### `ui/tabs/costing/product/_orphan_handler.py`

**الغرض:** يعالج منطق المكوّنات الناقصة (Orphans) في BOM منتج معين — جلبها، حذفها مع إشعار المستخدم، والتنظيف التلقائي للمنتجات التي تصبح فارغة بعد الحذف.

**Imports داخلية مهمة:**
- `services.costing.product_service.ProductService`.
- `services.shared.item_service.ItemService`.
- `ui.widgets.core.events.emit_company_data_changed`.
- `ui.widgets.core.i18n.tr`.

**من يستدعي هذا الملف:** `ui/tabs/costing/product/product_main_panel.py` (`_ProductMainPanel` ينشئ `self._orphan = _OrphanHandler(parent=self)`، ويستدعي `fetch` و `fix`).

**Classes:**
- **`_OrphanHandler`** (لا يرث من أي base)
  - `__init__(self, parent)`: يحفظ `_parent` للـ dialogs.
  - `fetch(conn, pid: int) -> list` *(staticmethod)*: يرجع قائمة المكوّنات الناقصة عبر `ProductService(conn).get_orphan_components(pid)`.
  - `fix(self, conn, pid: int, warning_bar, bom_tree, form) -> None`: يجلب أسماء الـ orphans قبل الحذف، يجلب اسم المنتج عبر `ItemService`، يحذف عبر `ProductService.fix_orphans(pid)`، ينظّف المنتجات الفارغة تلقائيًا عبر `cleanup_empty_products_after_orphan_fix([pid])`، يخفي `warning_bar`، يعيد تحميل `bom_tree`، يستدعي `emit_company_data_changed()`. لو تم حذف المنتج تلقائيًا (كان فارغًا)، يصفّر `form` ويمسح شجرة BOM ويعرض رسالة مختلفة عن حالة الحذف الجزئي العادي.

**ملاحظات من التعليقات:**
- [Fix #5] `emit_company_data_changed()` بدل `bus.data_changed.emit()`.
- [Fix #10] استبدال db imports المباشرة بـ `ProductService`/`ItemService` بدل `db.shared.items_repo`.

---

### `ui/tabs/costing/product/product_form.py`

**الغرض:** فورم إضافة/تعديل منتج (نصف مصنع أو نهائي) — يجمع الهيدر (اسم، تصنيف، سيناريوهات) وصفوف المكوّنات (BOM) ومنطق الحفظ، عبر تفويض للـ helper classes الثلاثة في `form/`.

**Imports داخلية مهمة:**
- `services.costing.scenario_service.ScenarioService`.
- `services.costing.product_service.ProductService`.
- `services.shared.item_service.ItemService`.
- `ui.widgets.core.conn.LiveConnMixin`.
- `ui.widgets.core.events.emit_company_data_changed`.
- `ui.widgets.core.i18n.tr`.
- `.form._header_bar._FormHeaderBar`.
- `.form._rows_manager._RowsManager`.
- `.form._save_logic._SaveLogic`.

**من يستدعي هذا الملف:** `ui/tabs/costing/product/product_main_panel.py` (`_ProductMainPanel` ينشئ `self._form = _FormPanel(conn, product_type, self._get_catalog)`).

**Classes:**
- **`_FormPanel(QWidget, LiveConnMixin)`**
  - `__init__(self, conn, product_type: str, catalog_fn, parent=None)`: يحفظ الحالة (`_editing_id`, `is_editing`, `_scope`, `_current_scenario_id`)، يستدعي `_build()`.
  - `_build(self)`: ينشئ `_FormHeaderBar` (يربط إشاراتها: `add_row_clicked→_add_row`, `save_clicked→save`, `cancel_clicked→_do_cancel`, `scenario_changed→_on_scenario_changed`)، `_RowsManager`، `_SaveLogic(conn_fn=self._live_conn)`، ثم يضيف صف مكوّن أولي فارغ عبر `_add_row()`.
  - `rows_layout` *(property)*: يرجع `self._rows.rows_layout`.
  - `lbl_mode` *(property)*: يرجع `self._header.lbl_mode`.
  - `_add_row(self, child_type="raw", child_id=None, qty=1.0, orphan_name=None, waste_pct=0.0, variant_id=None, machine_op_row_id=None) -> ComponentRow`: يفوّض لـ `self._rows.add_row(...)`.
  - `_remove_row(self, widget)`: يفوّض لـ `self._rows._remove_row(widget)`.
  - `collect_rows(self)`: يفوّض لـ `self._rows.collect_rows()`.
  - `clear_rows(self)`: يفوّض لـ `self._rows.clear_rows()`.
  - `load_product(self, pid: int)`: يجلب المنتج عبر `ItemService(conn).get(pid)`؛ يمسح الصفوف، يملأ الهيدر (اسم، تصنيف)، يحمّل لوحة السيناريوهات (`scenarios_panel.load_item(pid)`)؛ يجلب/يضمن السيناريو الافتراضي عبر `ScenarioService`؛ يحمّل BOM السيناريو الافتراضي عبر `_load_bom_for_scenario`؛ يحسب عدد الـ orphans ويبني label مناسب (مع/بدون تحذير)؛ يدخل وضع التعديل.
  - `_load_bom_for_scenario(self, pid: int, scenario_id: int)`: يمسح الصفوف، يجلب الـ orphans (لبناء `orphan_map`)، يجلب صفوف BOM عبر `ScenarioService(conn).get_bom(scenario_id)` (يدعم كلا الشكلين: كائن بخصائص أو dict)، يضيف صفًا لكل عنصر BOM (مع تمرير `orphan_name` لو كان orphan)؛ لو النوع `machine_op` يستدعي `component_row.expose_load_op_rows(child_id, machine_op_row_id)`؛ لو لا توجد صفوف BOM يضيف صفًا فارغًا واحدًا.
  - `_on_scenario_changed(self, scenario_id: int)`: لو في وضع تعديل، يحدّث `_current_scenario_id` ويعيد تحميل BOM للسيناريو الجديد.
  - `reset(self)`: يصفّر الهيدر، يمسح الصفوف، يضيف صفًا فارغًا، يصفّر `_current_scenario_id`، يخرج من وضع التعديل بعنوان `tr("new_product")`.
  - `save(self)`: يستدعي `self._saver.save(...)` بكل معطيات الحالة الحالية؛ لو نجح (`pid is not None`) يصفّر الفورم ويجدول `emit_company_data_changed` عبر `QTimer.singleShot(0, ...)`.
  - `enter_edit_mode(self, pid, label="")`: يضبط `_editing_id`, `is_editing=True`, يستدعي `self._header.enter_edit_mode(label)`.
  - `exit_edit_mode(self, label="")`: يصفّر `_editing_id`, `is_editing=False`, يستدعي `self._header.exit_edit_mode(label or tr("new_product"))`.
  - `_do_cancel(self)`: يستدعي `self.reset()`.

**ملاحظات من التعليقات:**
- [Fix #1] توحيد `LiveConnMixin` من `ui.widgets.core.conn`.
- [Fix #3] `emit_company_data_changed` بدل `bus.data_changed.emit()`.
- [Fix C1] `tr("new_product")` بدل نص hardcoded.
- [Fix #9] استبدال db imports بـ services.

---

### `ui/tabs/costing/product/product_main_panel.py`

**الغرض:** اللوحة الرئيسية للمنتج — تجمع فورم المنتج، جدول المنتجات، شجرة BOM، وشريط تحذير الـ orphans في splitter رأسي واحد، وتنسّق التفاعل بينهم (اختيار صف → تحديث الشجرة والتحذير، حذف، تعديل).

**Imports داخلية مهمة:**
- `services.shared.item_service.ItemService`.
- `ui.widgets.dialogs.confirm.confirm_delete`.
- `ui.widgets.core.conn.LiveConnMixin`.
- `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.widgets.core.i18n.tr`.
- `ui.widgets.components.notification.BaseWarningBar` — شريط تحذير الـ orphans.
- `ui.tabs.costing.shared.bom_tree.BomTree`.
- `ui.widgets.core.events.bus`, `emit_company_data_changed`.
- `.product_form._FormPanel`.
- `.product_table._ProductTable`.
- `._catalog_provider.build_product_catalog`.
- `._orphan_handler._OrphanHandler`.
- `ui.constants.PRODUCT_MAIN_SPLITTER_HANDLE_W`, `PRODUCT_MAIN_SPLITTER_SIZES`.

**من يستدعي هذا الملف:** `ui/tabs/costing/product_tab.py` (`ProductTab._build_tabs` ينشئ `_ProductMainPanel(self.conn, self.product_type)`).

**Classes:**
- **`_ProductMainPanel(QWidget, LiveConnMixin, WidgetMixin)`**
  - `__init__(self, conn, product_type: str, parent=None)`: يبني اللوحة، يشترك في `bus.company_data_changed` عبر named slot `_on_company_data_changed` (لتجنب memory leaks).
  - `_on_company_data_changed(self, _company_id=None)`: يستدعي `_on_data_changed()`.
  - `_get_catalog(self) -> dict`: يستدعي `build_product_catalog(self._live_conn())` مع `try/except` يرجع كتالوج فارغ عند الفشل.
  - `_refresh_style(self, *_)`: يحدّث stylesheet الـ splitter عند تغيير الثيم.
  - `_build(self)`: ينشئ splitter رأسي بثلاثة أقسام: `_FormPanel` (الفورم)، `mid_widget` (يحتوي `BaseWarningBar` + `_ProductTable`)، و `BomTree`. يربط `bus.company_data_changed` أيضًا بـ `_on_company_data_changed_catalog` لتحديث الكتالوج في صفوف الفورم. أحجام السبلتر من `PRODUCT_MAIN_SPLITTER_SIZES`؛ القسم الأوسط غير قابل للطي، الطرفين قابلين للطي.
  - `_on_company_data_changed_catalog(self, _company_id=None)`: يستدعي `_refresh_form_catalog()`.
  - `_refresh_for_product(self, pid: int)`: يستدعي `_check_orphans(pid, conn)` ثم `self._bom_tree.load(conn, pid)`، مع `try/except` صامت.
  - `_on_data_changed(self)`: لو يوجد منتج محدد حاليًا، يستدعي `_refresh_for_product(pid)`.
  - `_on_product_selected(self, pid: int | None)`: لو `pid is None` يمسح الشجرة ويخفي التحذير؛ وإلا يستدعي `_refresh_for_product(pid)`.
  - `_refresh_form_catalog(self)`: يعيد بناء الكتالوج ويستدعي `self._form._rows.refresh_catalog(new_catalog)`.
  - `_check_orphans(self, pid: int, conn)`: يجلب الـ orphans عبر `self._orphan.fetch(conn, pid)`، يجلب اسم المنتج، يستدعي `self._warning.show_orphans(orphans, name)`.
  - `_fix_orphans(self)`: يجلب `pid` المحدد، يستدعي `self._orphan.fix(conn, pid, warning_bar=..., bom_tree=..., form=...)`.
  - `_edit_selected(self, pid=None)`: لو لا يوجد `pid` يأخذه من الجدول المحدد؛ لو لا شيء محدد يعرض تحذير؛ وإلا يخفي التحذير ويحمّل المنتج في الفورم.
  - `_delete_product(self, pid)`: يتحقق من وجود `pid`، يجلب العنصر عبر `ItemService`، يطلب تأكيد الحذف، لو الفورم كان يعدّل نفس المنتج يصفّره، يحذف عبر `svc.force_delete(pid)`، يخفي التحذير، يمسح شجرة BOM، `emit_company_data_changed()`.

**ملاحظات من التعليقات:**
- [Fix #1]/[Fix #3]/[Fix #4]/[Fix #6]/[Fix #7]/[Fix #8]/[Fix A6]/[Fix C2]/[Fix D1] سلسلة إصلاحات توحيد مسارات استيراد ودمج منطق مكرر في `_refresh_for_product` واستخدام named slots بدل lambda.

---

### `ui/tabs/costing/product/product_table.py`

**الغرض:** جدول المنتجات المحفوظة (نصف مصنع/نهائي) مع فلترة، بدون زر إضافة (الإضافة تتم عبر الفورم المنفصل). يرث من `BaseListPanel`.

**Imports داخلية مهمة:**
- `services.shared.item_service.ItemService`.
- `models.costing.calc_cost` — حساب تكلفة المنتج لعرضها في الجدول.
- `ui.widgets.base.list_panel.BaseListPanel` — الأساس.
- `ui.widgets.tables.tables.make_item`, `colored_item`.
- `ui.widgets.core.i18n.tr`.

**من يستدعي هذا الملف:** `ui/tabs/costing/product/product_main_panel.py` (`_ProductMainPanel` ينشئ `_ProductTable(conn, product_type, on_select=..., on_edit=..., on_delete=...)`).

**Module-level constants:** `_PRODUCT_SCOPE = {"semi": "semi", "final": "final"}`.

**Class-level attributes:**
- `COLUMNS` — id, اسم, تصنيف, تكلفة.
- `STRETCH_COL = -1`.
- `EMPTY_ICON = "🏭"`, `EMPTY_TITLE = tr("no_products")`, `LIST_TITLE = tr("products_table_title")`.
- `ADD_TEXT = ""` (بدون زر إضافة).
- `SHOW_CATEGORY = True`, `CONNECT_BUS = True`.
- `COL_WIDTHS = {0: 45, 2: 110, 3: 120}`.

**Classes:**
- **`_ProductTable(BaseListPanel)`**
  - `__init__(self, conn, product_type: str, on_select, on_edit, on_delete, parent=None)`: يحفظ callbacks الخارجية، يحدد `_scope` و `FILTER_SCOPE` ديناميكيًا من `product_type`، يستدعي الأب، ثم يربط `itemSelectionChanged` بـ `_on_selection_changed`.
  - `_load_rows(self) -> list`: `ItemService(conn).list_by_type(product_type)` مع `try/except` يرجع `[]`.
  - `_fill_row(self, table, r: int, row)`: يحسب التكلفة عبر `calc_cost(conn, row.id)` (مع `try/except`)، يملأ 4 أعمدة.
  - `_match_filter(self, row, query: str) -> bool`: يستخدم `self._filter.match(name, category_id)` لو متاح، وإلا مطابقة نصية بسيطة.
  - `_build_extra_header_actions(self, header)`: يضيف زري "تعديل المحدد" و"حذف المحدد" (style="normal"/"danger").
  - `_on_selection_changed(self)`: يستدعي `self._on_select_cb(self.selected_pid())`.
  - `_trigger_edit(self)` / `_trigger_delete(self)`: يستدعيان الـ callbacks المقابلة بـ `selected_pid()`.
  - `_on_add_clicked(self)`: لا شيء (pass) — الإضافة عبر الفورم المنفصل.
  - `_on_edit_item(self, item_id)` / `_on_delete_item(self, item_id, item_name)` / `_on_row_double_clicked(self, item_id)`: كلها تستدعي الـ callback المناسب.
  - `selected_pid(self) -> int | None`: يرجع `self.selected_id()` — واجهة متوافقة مع الكود القديم.

**ملاحظات من التعليقات:** [Refactor] وراثة من `BaseListPanel` بدل بناء يدوي كامل. [Fix #7] `style="normal"` صريح لزر التعديل لتوحيد المظهر.

---

## القسم 5: `ui/tabs/costing/product/form/`

### `ui/tabs/costing/product/form/_header_bar.py`

**الغرض:** الشريط العلوي لفورم المنتج — يحتوي اسم المنتج، التصنيف، أزرار (إضافة مكوّن/حفظ/إلغاء)، لوحة السيناريوهات (`_BomScenariosPanel`)، وصف عناوين أعمدة صفوف المكوّنات.

**Imports داخلية مهمة:**
- `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.widgets.core.i18n.tr`.
- `ui.widgets.components.button.make_btn`.
- `ui.widgets.combo.category.CategoryCombo`.
- `ui.widgets.theme.builders.wrap_in_scroll`.
- `ui.font.FS_BASE`, `FS_SM`.
- `ui.tabs.costing.shared.bom_scenarios_panel._BomScenariosPanel`.
- `ui.constants` — أبعاد كثيرة لهيدر الفورم.

**من يستدعي هذا الملف:** `ui/tabs/costing/product/product_form.py` (`_FormPanel._build` ينشئ `_FormHeaderBar(conn, scope=self._scope)`).

**Classes:**
- **`_FormHeaderBar(QWidget, WidgetMixin)`**
  - **Signals:** `add_row_clicked = pyqtSignal()`, `save_clicked = pyqtSignal()`, `cancel_clicked = pyqtSignal()`, `scenario_changed = pyqtSignal(int)`.
  - `__init__(self, conn, scope: str, parent=None)`: يحفظ `_scope`, `_conn`، يبني الواجهة.
  - `_build(self)`: ينشئ صف علوي (وضع الفورم، اسم المنتج، تصنيف، زر إضافة مكوّن، حفظ/إلغاء)، يضيف `_BomScenariosPanel` ويربط `scenario_changed` منها بإشارة الفورم نفسه، ثم صف عناوين الأعمدة (نوع، عنصر، صف/variant، تكلفة الوحدة، كمية، نسبة الهدر، عمود فارغ للحذف) عبر دالة داخلية `_hdr`.
  - `_refresh_style(self, _=None)`: يحدّث ألوان/خطوط العناصر عند تغيير الثيم، ثم يستدعي `refresh_visible_buttons(self)` من `ui.widgets.components.button` لضمان تحديث ستايل الأزرار المبنية بـ `make_btn` (كان الفورم يفشل في تحديثها بعد التحول لـ dark theme).
  - `scenarios_panel` *(property)*: يرجع `self._scenarios_panel`.
  - `product_name` *(property + setter)*: قراءة/كتابة نص `inp_name`.
  - `category_id` *(property)*: يرجع `self.cmb_category.get_category()`.
  - `set_category(self, cat_id)`: `self.cmb_category.set_category(cat_id)`.
  - `set_mode(self, text: str)`: `self.lbl_mode.setText(text)`.
  - `enter_edit_mode(self, label="")`: يضبط نص `lbl_mode` (لو مُمرَّر) ويُظهر `btn_cancel`.
  - `exit_edit_mode(self, label="")`: يضبط نص `lbl_mode` (افتراضي `tr("new_product")`) ويخفي `btn_cancel`.
  - `reset(self)`: يمسح `inp_name`، يعيد التصنيف لأول عنصر، يمسح `_scenarios_panel`، يستدعي `exit_edit_mode()`.

**ملاحظات من التعليقات:** [Fix - dark theme buttons] استدعاء `refresh_visible_buttons` بعد تغيير الثيم لأن الأزرار كانت تفضل بستايل قديم.

---

### `ui/tabs/costing/product/form/_rows_manager.py`

**الغرض:** يدير صفوف مكوّنات BOM داخل فورم المنتج — إضافة، حذف، جمع القيم، مسح الكل، وتحديث الكتالوج في الصفوف الموجودة، ضمن منطقة قابلة للتمرير (scroll area).

**Imports داخلية مهمة:**
- `ui.widgets.components.component_row.widget.ComponentRow` — عنصر الصف الفعلي.
- `ui.constants` — `PRODUCT_FORM_ROWS_SPACING`, `PRODUCT_FORM_ROWS_MARGIN`, `PRODUCT_FORM_ROWS_SCROLL_MIN_H`, `MARGIN_ZERO`, `SPACING_ZERO`.

**من يستدعي هذا الملف:** `ui/tabs/costing/product/product_form.py` (`_FormPanel._build` ينشئ `self._rows = _RowsManager(self._catalog_fn)`).

**Classes:**
- **`_RowsManager(QWidget)`**
  - `__init__(self, catalog_fn, parent=None)`: يحفظ `_catalog_fn`، يستدعي `_build()`.
  - `_build(self)`: ينشئ `rows_container`/`rows_layout` (عمودي، مع stretch نهائي) داخل `QScrollArea` بحد أدنى ارتفاع.
  - `add_row(self, child_type="raw", child_id=None, qty=1.0, orphan_name=None, waste_pct=0.0, variant_id=None, machine_op_row_id=None) -> ComponentRow`: ينشئ `ComponentRow` جديد بالمعطيات، لو orphan يضبط `orphan_name`، يربط إشارة `removed` بـ `_remove_row`، يدرجه قبل الـ stretch، يجدول `refresh_catalog` عبر `QTimer.singleShot(0, ...)`، يرجع الصف.
  - `_remove_row(self, widget: QWidget)`: يزيل الودجت من الـ layout ويستدعي `deleteLater()`.
  - `collect_rows(self) -> list`: يمر على كل عناصر `rows_layout`، لكل `ComponentRow` يستدعي `get_values()`، يضمن أن كل tuple بطول 6 (يكمل بـ `None`)، يرجع القائمة الكاملة.
  - `clear_rows(self)`: يحذف كل الصفوف مع الإبقاء على الـ stretch (يكرر حتى `rows_layout.count() > 1`).
  - `refresh_catalog(self, new_catalog: dict = None)`: يمر على كل `ComponentRow` ويستدعي `w.refresh_catalog(new_catalog)`.

**ملاحظات من التعليقات:** [Refactor] استيراد `ComponentRow` من المسار الجديد `ui.widgets.components.component_row.widget` بدل المسار القديم `ui.widgets.shared.component_row._row_widget`.

---

### `ui/tabs/costing/product/form/_save_logic.py`

**الغرض:** منطق حفظ المنتج (إدراج/تحديث) والـ BOM المرتبط به عبر `ProductService`، مع ضمان وجود سيناريو افتراضي عند الحاجة.

**Imports داخلية مهمة:**
- `services.costing.product_service.ProductService`, `BomComponent`.
- `ui.widgets.core.i18n.tr`.

**من يستدعي هذا الملف:** `ui/tabs/costing/product/product_form.py` (`_FormPanel._build` ينشئ `self._saver = _SaveLogic(conn_fn=self._live_conn)`، ويستدعي `save()` من `_FormPanel.save()`).

**Classes:**
- **`_SaveLogic`** (لا يرث من أي base)
  - `__init__(self, conn_fn)`: يحفظ `conn_fn` (callable يرجع اتصال حي).
  - `save(self, *, is_editing: bool, editing_id, name: str, product_type: str, category_id, current_scenario_id, rows: list, scenarios_panel, parent_widget) -> int | None`: 
    - يتحقق من وجود `name` وrows، وإلا يعرض `QMessageBox.warning` ويرجع `None`.
    - يحوّل كل `row` tuple (`child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id`) إلى كائن `BomComponent`.
    - يبني `product_data` dict (id، name، type، price=0، category_id).
    - يحدد `save_scenario_id`: لو `current_scenario_id` موجب يستخدمه مباشرة؛ لو في وضع تعديل و `current_scenario_id is None` يضمن سيناريو افتراضي عبر `scenarios_panel.ensure_default_scenario(editing_id)`؛ غير ذلك `None` (يترك `ProductService` ينشئ سيناريو جديد لمنتج جديد/in-memory).
    - يستدعي `ProductService(conn).save(product_data, components, scenario_id)`، يعمل `conn.commit()`، يرجع `result.product_id`.
    - عند أي استثناء: يعرض `QMessageBox.warning` بالخطأ، يرجع `None`.

**ملاحظات من التعليقات:** [Refactor] استخدام `ProductService`+`BomComponent` بدل `db.shared.items_repo` + `db.costing.bom_scenarios_repo` مباشرة.

---

## القسم 6: `ui/tabs/costing/raw/`

### `ui/tabs/costing/raw/raw_section.py`

**الغرض:** القسم الرئيسي للخامات — splitter أفقي بين فورم الإدخال (list) وجدول الخامات (detail)، بنفس نمط شاشات Orders/Customers، بدل التخطيط العمودي القديم.

**Imports داخلية مهمة:**
- `ui.widgets.base.section.BaseSection` — الأساس الذي يبني الـ QSplitter الأفقي.
- `.raw_input_panel.RawInputPanel`.
- `.raw_table_panel.RawTablePanel`.
- `ui.constants.RAW_SECTION_LIST_MIN_W`.

**من يستدعي هذا الملف:** `ui/tabs/costing/raw_tab.py` (`RawTab._build_tabs` ينشئ `RawSection(self.conn)`).

**Class-level attributes:** `LIST_MIN_W = RAW_SECTION_LIST_MIN_W`, `CONNECT_BUS = False` (كل panel يتعامل مع bus بنفسه).

**Classes:**
- **`RawSection(BaseSection)`**
  - `_create_list(self)`: ينشئ `self._form_panel = RawInputPanel(conn=self.conn)` ويرجعه.
  - `_create_detail(self) -> QWidget`: ينشئ `self._table_panel = RawTablePanel(conn=self.conn, input_panel=None)` ويرجعه.
  - `_connect_signals(self)`: يربط `_form_panel.saved` بـ `_table_panel.refresh`، يربط `item_double_clicked` من الجدول (لو موجودة) بـ `_form_panel.load_for_edit`، ثم يضبط `self._table_panel._input_panel = self._form_panel` مباشرة (وليس اسمًا بدون underscore — كان هذا الخطأ الأصلي).

**ملاحظات من التعليقات:** [Fix] كان الربط يكتب على `self._table_panel.input_panel` (بدون underscore) بينما `RawTablePanel` يخزّن القيمة فعليًا في `self._input_panel` (مع underscore) — أي كان يضبط attribute مختلف تمامًا فيبقى زر التعديل غير فعّال. تم تصحيحه.

---

### `ui/tabs/costing/raw/raw_input_panel.py`

**الغرض:** فورم إضافة/تعديل خامة، مع لوحة variants مدمجة (`_RawVariantsPanel`) تدعم "وضع الذاكرة" (إضافة variants قبل حفظ الخامة نفسها). يرث من `BaseCrudForm`.

**Imports داخلية مهمة:**
- `ui.widgets.base.crud_form.BaseCrudForm` — الأساس.
- `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.widgets.core.events.emit_company_data_changed`.
- `ui.widgets.panels.form_fields.labeled_widget`, `spin_field`.
- `ui.widgets.panels.form_badges.ResultBadge`.
- `ui.widgets.panels.form_group.FormGroup`.
- `ui.widgets.forms.inputs.RequiredLineEdit`, `AmountSpinBox`.
- `ui.widgets.combo.category.CategoryCombo`.
- `ui.tabs.costing.shared.raw_variants_panel._RawVariantsPanel`.
- `ui.widgets.core.i18n.tr`, `ui.font.FS_XS`.
- `ui.constants` — أبعاد الفورم.

**من يستدعي هذا الملف:** `ui/tabs/costing/raw/raw_section.py` (`RawSection._create_list` ينشئ `RawInputPanel(conn=self.conn)`).

**Module-level function:** `_live_price(inp_price) -> float`: يقرأ سعرًا من `QLineEdit` بأمان (`try/except ValueError` يرجع 0.0).

**Class-level attributes:** `FORM_TITLE = tr("raw_form_title")`, `ADD_TEXT = tr("raw_add_btn")`, `SAVE_TEXT = tr("btn_save")`.

**Classes:**
- **`RawInputPanel(BaseCrudForm, WidgetMixin)`**
  - `__init__(self, conn, parent=None)`: يربط `inp_price.textChanged` بـ `_on_price_changed`، `sp_total_qty.valueChanged` بـ `_update_hint`، يفعّل لوحة الـ variants فورًا في "وضع الذاكرة" (`_variants.enter_memory_mode(0.0)`) لأن الفورم يفتح افتراضيًا في وضع "إضافة خامة جديدة".
  - `_on_add(self)` *(override)*: يجمع البيانات، يستدعي `_do_insert(data)`، يعرض خطأ لو فشل، وإلا يصفّر الفورم، `emit_company_data_changed()`، يُصدر إشارة `saved.emit(new_id)`.
  - `_build_fields(self, group: FormGroup)`: ينشئ `inp_name` (RequiredLineEdit)، `inp_price` (AmountSpinBox)، `sp_total_qty` (spin field)، `lbl_hint` (تلميح ديناميكي)، `cmb_category` (CategoryCombo scope="raw")، يضيفهم كصفوف، وينشئ `self._variants = _RawVariantsPanel(conn)` (تُضاف لاحقًا عبر `_build_extra`).
  - `_build_extra(self, root_layout)`: يضيف `self._variants` بعد الـ FormGroup (hook في `BaseCrudForm`).
  - `_on_price_changed(self)`: يستدعي `_update_hint()` ويحدّث السعر داخل `_variants.refresh_price(_live_price(inp_price))` — يعمل في كلا وضعي DB/الذاكرة.
  - `_update_hint(self)`: يحسب سعر الوحدة (`price/tq`) لو توفرت الكمية والسعر ويعرض تلميحًا مناسبًا (3 حالات: بسعر وكمية، بكمية فقط، بدون كمية).
  - `_collect(self) -> dict | None`: يتحقق من `inp_name.validate()`، يقرأ السعر (من `.value()` لو AmountSpinBox أو `_live_price` كـ fallback)، يرجع `{name, price, total_qty, category_id}`.
  - `_do_insert(self, data: dict) -> int`: يستدعي `ItemService(conn).add(name, price, "raw", category_id=..., total_qty=...)`، ثم يحفظ الـ variants المعلّقة فعليًا عبر `self._variants.save_pending_to_db(new_id)`.
  - `_do_update(self, item_id: int, data: dict) -> None`: `ItemService(conn).update(item_id, name, price, category_id=..., total_qty=...)`.
  - `_do_load(self, item_id: int) -> dict | None`: يجلب عبر `ItemService(conn).get(item_id)` ويرجع dict أو `None`.
  - `_fill_fields(self, data: dict) -> None`: يملأ الحقول من dict، يستدعي `_update_hint()`، يحمّل الـ variants الفعلية عبر `self._variants.load_item(data["id"], data["price"])`.
  - `_reset_fields(self) -> None`: يمسح كل الحقول، يستدعي `_update_hint()`، يمسح `_variants`، ثم يعيد تفعيلها في وضع الذاكرة (`enter_memory_mode(0.0)`) استعدادًا لخامة جديدة.

**ملاحظات من التعليقات:** [Feature] تدفق الـ variants: تُضاف في الذاكرة أثناء الإدخال، وتُحفظ فعليًا في DB دفعة واحدة فقط بعد نجاح إدراج الخامة نفسها وحصولها على `item_id` حقيقي.

---

### `ui/tabs/costing/raw/raw_table_panel.py`

**الغرض:** جدول الخامات الشامل — يدعم عناصر مشتركة/منشورة، فلترة، وصف فرعي قابل للفتح (expand row) يعرض mini-جدول لـ variants كل خامة محلية. يرث من `BaseListPanel` + `SharedOpsMixin`.

**Imports داخلية مهمة:**
- `ui.widgets.base.list_panel.BaseListPanel` — الأساس.
- `ui.widgets.mixins.shared_ops.SharedOpsMixin` — منطق العناصر المشتركة.
- `ui.widgets.tables.tables.make_item`, `colored_item`, `make_table`, `refresh_table_styles`, `make_splitter_table_guarded`, `fit_splitter_table`.
- `ui.widgets.components.button.make_btn`.
- `ui.widgets.dialogs.confirm.confirm_delete`.
- `ui.widgets.core.events.emit_company_data_changed`.
- `ui.widgets.core.i18n.tr`.
- `ui.tabs.costing.shared._utils.to_dict`, `SHARED_COLOR`, `SHARED_BG`, `PUBLISHED_COLOR`, `PUBLISHED_BG`.
- `ui.tabs.companies.shared_items_mixin.get_shared_raws`, `get_published_local_names`, `is_shared_id`.
- `services.costing.variant_service.VariantService`.
- `ui.theme._C`.
- `models.costing_base.raw_unit_price` (مستوردة محليًا داخل `_fill_row`).

**من يستدعي هذا الملف:** `ui/tabs/costing/raw/raw_section.py` (`RawSection._create_detail` ينشئ `RawTablePanel(conn=self.conn, input_panel=None)`؛ ثم `RawSection._connect_signals` يضبط `_table_panel._input_panel`).

**Module-level constants:** `_VARIANTS_SUBROW_H = 130` — ارتفاع الصف الفرعي بالبكسل.

**Class-level attributes:**
- `COLUMNS` — 8 أعمدة: فارغ (expand)، id، اسم، تصنيف، إجمالي السعر، الكمية، سعر الوحدة، إجراءات.
- `STRETCH_COL = -1` (قاعدة موحدة إلزامية لكل الجداول في المشروع).
- `COL_MAX_WIDTHS = {1: 90, 2: 260}`.
- `EMPTY_ICON`, `EMPTY_TITLE = tr("no_raws")`, `LIST_TITLE = tr("raw_table_list_title")`.
- `ADD_TEXT = ""`, `SHOW_CATEGORY = True`, `FILTER_SCOPE = "raw"`.
- `COL_WIDTHS = {1: 45, 3: 110, 4: 90, 5: 90, 6: 95, 7: 90}`.
- `CONNECT_BUS = True`.

**Classes:**
- **`RawTablePanel(BaseListPanel, SharedOpsMixin)`**
  - `__init__(self, conn, input_panel=None, parent=None)`: يحفظ `_input_panel`, `_published_names`, `_expanded_ids` (set لدعم فتح أكثر من صف)، `_variant_counts` (dict item_id→عدد variants، محسوب مرة واحدة لكل `_load_rows`).
  - `_load_rows(self) -> list`: يجلب الخامات المحلية عبر `ItemService(conn).list_by_type("raw")`، يحسب `_published_names`، يجلب الصفوف المشتركة عبر `get_shared_raws`، يحسب `_variant_counts` لكل خامة محلية عبر `VariantService(conn).list(item_id)` (العناصر المشتركة مستثناة لأنها قد تنتمي لقاعدة بيانات شركة أخرى). يرجع `local_rows + shared_rows`.
  - `_refresh_data(self, company_id=None)`: يستدعي `self.refresh()` — تعريف مطلوب لأن `WidgetMixin._on_data_change` تستدعي هذه الدالة (وليس `refresh()` مباشرة)، وكان الجدول لا يتحدث تلقائيًا بدونها.
  - `_fill_row(self, table, r: int, row: dict)`: يحدد `is_shared`/`is_published`، يحسب `unit` (سعر الوحدة) بمنطق مختلف للعناصر المشتركة (`price/total_qty`) عن المحلية (`raw_unit_price(row)`)، يملأ الأعمدة 1-6 (عمود الـ id يعرض الرقم الفعلي دائمًا، ليس أيقونة)، يلوّن الصف بالكامل لو مشترك/منشور، ثم يستدعي `_fill_expand_cell` و `_fill_actions_cell`.
  - `_fill_expand_cell(self, table, r: int, row: dict, is_shared: bool)`: يبني خلية عمود 0 — زر سهم (chevron) لفتح/قفل صف الـ variants، يظهر فقط للخامات المحلية التي لها variants فعلية. يستخدم `make_btn(style="ghost", icon=..., compact=True)` (بدل نص يونيكودي ▼/▶ كان يُعرض بشكل غير موثوق). لو الصف مفتوح مسبقًا (`item_id in self._expanded_ids`) يستدعي `_insert_variants_subrow` فورًا.
  - `_toggle_variants_row(self, item_id: int)`: يضيف/يزيل `item_id` من `_expanded_ids` ثم يعيد بناء الجدول عبر `_apply_filter()`.
  - `_insert_variants_subrow(self, table, item_id: int)`: يدرج صفًا فرعيًا مباشرة بعد صف الخامة، يبني mini-جدول عبر `_build_variants_mini_table`، يستخدم `setSpan` بدءًا من العمود 1 (وليس 0) لتفادي تمدد عمود الـ expand بسبب حساب `ResizeToContents`.
  - `_build_variants_mini_table(self, item_id: int)`: يبني جدول للقراءة فقط عبر `make_splitter_table_guarded` (نمط "compact")، يملأه من `VariantService(conn).list(item_id)` (اسم، عدد قطع، تكلفة الوحدة عبر `var.calc_unit_cost(price)`)، يطبّق `auto_fit_columns` و `table_style("compact")` يدويًا (لأن الجدول خارج شجرة `BaseListPanel`)، يعطّل `setStretchLastSection`، ويستدعي `fit_splitter_table(mini_splitter, mini, delay_ms=1)` (مؤجل لتفادي حساب عرض خاطئ قبل إدراج الودجت في الشجرة). يرجع `(mini_splitter, mini)`.
  - `_fill_actions_cell(self, table, r: int, row: dict, is_shared: bool)`: يبني خلية أزرار تعديل/حذف عبر `make_btn`؛ زر الحذف معطّل للعناصر المشتركة.
  - `_match_filter(self, row: dict, query: str) -> bool`: يستخدم `self._filter.match(name, category_id)`.
  - `selected_id(self) -> int | None` *(override)*: يقرأ الـ id من **عمود 1** (وليس 0، لأن عمود 0 أصبح لزر الـ expand بعد إضافة الميزة).
  - `_on_select(self)` *(override)*: نفس المنطق — يقرأ من عمود 1 ويُصدر `item_selected`.
  - `select_item(self, item_id: int)` *(override)*: يبحث في عمود 1 فقط، بدون استدعاء `super()` (لتفادي تعارض مع صفوف الـ variants الفرعية التي فيها `cellWidget` مدموج بـ `setSpan`).
  - `_build_extra_header_actions(self, header)`: يضيف أزرار "استبدال شامل"، "تعديل مشترك"، "نشر" في الهيدر.
  - `_on_add_clicked(self)`: لا شيء (الإضافة عبر الفورم المنفصل).
  - `_on_row_double_clicked(self, item_id)`: لو ليس عنصرًا مشتركًا، يستدعي `_input_panel.load_for_edit(item_id)`.
  - `_bulk_replace(self)`: يتحقق من التحديد، يمنع الاستبدال الشامل للعناصر المشتركة، يفتح `BulkReplaceDialog(child_type="raw", ...)`.
  - `_edit_shared_selected(self)`: يستدعي `_edit_shared_item(item_id, "raw", self)`.
  - `_publish_selected(self)`: يبني `item_data` وينشر عبر `_publish_item`.
  - `_on_edit_item(self, item_id)`: يمنع تعديل العناصر المشتركة مباشرة (يعرض إشعارًا)، وإلا يحمّل في `_input_panel`.
  - `_on_delete_item(self, item_id, item_name: str)`: يمنع حذف العناصر المشتركة، يصفّر الفورم لو قيد التعديل لنفس العنصر، يطلب تأكيد، يحذف عبر `ItemService(conn).delete(item_id)`، `emit_company_data_changed()` لو نجح فعليًا.
  - `_get_current_row_dict(self) -> dict | None`: يبحث عن الصف الحالي داخل `self._all_rows` بمطابقة نصية للـ id.

**ملاحظات من التعليقات:** ملف غني بالتعليقات التوثيقية لإصلاحات دقيقة (STRETCH_COL=-1 لضمان سلوك RTL صحيح، فصل الـ span عن عمود الـ expand، تأجيل `fit_splitter_table` لحل مشكلة حساب عرض قبل الإدراج الفعلي في الشجرة، إلخ) — جميعها موثقة inline وتم تلخيصها أعلاه.

---

## القسم 7: `ui/tabs/costing/shared/` (المستوى المباشر)

### `ui/tabs/costing/shared/_utils.py`

**الغرض:** أدوات مشتركة صغيرة لكل ملفات costing tabs — تحويل صفوف DB إلى dict، وقراءة ألوان العناصر المشتركة/المنشورة حيًا من الثيم الحالي.

**Imports داخلية مهمة:** `ui.theme._C`.

**من يستدعي هذا الملف:** `ui/tabs/costing/raw/raw_table_panel.py` (`to_dict`, `SHARED_COLOR`, `SHARED_BG`, `PUBLISHED_COLOR`, `PUBLISHED_BG`)، `ui/tabs/costing/labor/labor_op_table.py` (`to_dict`)، `ui/tabs/costing/machine/machine_table.py` (`to_dict`).

**Module-level functions:**
- `to_dict(row) -> dict`: يحوّل `sqlite3.Row` (أو أي iterable مشابه) إلى dict؛ لو كان dict بالفعل يرجعه كما هو؛ عند الفشل يرجع `{}`.
- `SHARED_COLOR() -> str`: يرجع `_C['shared_item_fg']` (دالة callable وليست قيمة ثابتة، حتى يتحدث اللون حيًا مع تبديل الثيم).
- `SHARED_BG() -> str`: يرجع `_C['shared_item_bg']`.
- `PUBLISHED_COLOR() -> str`: يرجع `_C['published_item_fg']`.
- `PUBLISHED_BG() -> str`: يرجع `_C['published_item_bg']`.

**ملاحظات من التعليقات:** [Fix] إزالة كل الألوان hardcoded؛ المصدر الوحيد هو `ui/theme_manager.py`. الدوال أصبحت callables (`SHARED_COLOR()`) بدل قيم ثابتة لتفادي تجميد اللون على الثيم الافتراضي وقت تحميل الموديول.

---

### `ui/tabs/costing/shared/bom_scenarios_panel.py`

**الغرض:** لوحة أفقية لعرض/إدارة سيناريوهات BOM لمنتج (تبديل، تعيين افتراضي، إعادة تسمية، استنساخ، إضافة، حذف)، تعمل في وضعين: ذاكرة (منتج جديد) أو DB (منتج محفوظ)، بالاعتماد على Mixins منفصلة.

**Imports داخلية مهمة:**
- `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.widgets.core.i18n.tr`, `ui.font.FS_XS/FS_SM/FS_LG`.
- `ui.constants` — أبعاد كثيرة للوحة والأزرار.
- `.bom_scenarios._memory_scenarios.MemoryScenariosMixin`.
- `.bom_scenarios._db_scenarios.DbScenariosMixin`.

**من يستدعي هذا الملف:** `ui/tabs/costing/product/form/_header_bar.py` (`_FormHeaderBar._build` ينشئ `_BomScenariosPanel(self._conn)`).

**Module-level (class-level) constants:** `_BTN_COLOR_KEYS = ("bg", "fg", "border", "hover")`، `_COLOR_NAME_TO_KEYS` — قاموس يربط اسم لون منطقي (warning/orange/info/success/danger) بمفاتيح `_C` الفعلية (bg/fg/border/hover).

**Classes:**
- **`_BomScenariosPanel(ThemedFrame, MemoryScenariosMixin, DbScenariosMixin, WidgetMixin)`**
  - **Signal:** `scenario_changed = pyqtSignal(int)`.
  - `__init__(self, conn, parent=None)`: يهيّئ الحالة (`_item_id=None`, `_scenarios=[]`, `_current_id=None`, `_in_memory=True`)، يبني الواجهة، يستدعي `_init_memory_scenario()` (من `MemoryScenariosMixin`).
  - `_build(self)`: ينشئ combo السيناريوهات، badge "افتراضي"، وأزرار ملوّنة (تعيين افتراضي، تعديل، استنساخ، جديد، حذف) عبر `_make_btn`.
  - `_refresh_style(self, *_)`: يعيد تطبيق ستايل الإطار والـ combo، يستدعي `_refresh_buttons()`.
  - `_apply_frame_style(self)` / `_apply_combo_style(self)`: بناء stylesheet الإطار البنفسجي والـ combo.
  - `_make_btn(self, text, width, bg, fg, border, hover, color_name=None) -> QPushButton`: يبني زرًا ملوّنًا، ويخزّن `color_name` كـ Qt property (`_scenario_btn_color`) لإعادة البناء لاحقًا من الثيم الحالي بدل تجميد الألوان وقت الإنشاء.
  - `_btn_stylesheet(bg, fg, border, hover) -> str` *(staticmethod)*: يبني نص الـ stylesheet لزر واحد.
  - `_refresh_buttons(self)`: يمر على كل `QPushButton` أبناء، يقرأ `_scenario_btn_color` منها، يعيد بناء الـ stylesheet من `_C` الحالية (حتى للأزرار المعطّلة، لضمان تحديث حالة `:disabled` أيضًا).
  - `clear(self)`: يستدعي `_init_memory_scenario()` — العودة لوضع الذاكرة.
  - `current_scenario_id(self) -> int | None`.
  - `is_in_memory(self) -> bool`.
  - `_rebuild_combo(self)`: يعيد بناء الـ combo من `self._scenarios` (مع نجمة للافتراضي)، يحافظ على تحديد `_current_id`.
  - `_sync_current(self)`: يقرأ `currentData()`، يحدّث `_current_id`، يُظهر/يخفي badge الافتراضي، يفعّل/يعطّل زر "تعيين افتراضي".
  - `_on_scenario_changed(self, _)`: يستدعي `_sync_current()`، يُصدر `scenario_changed` لو `_current_id` غير `None`.
  - `_set_default(self)`: يفوّض لـ `_memory_set_default` أو `_db_set_default` حسب `_in_memory`.
  - `_rename(self)`: يطلب اسمًا جديدًا عبر `QInputDialog`، يفوّض للـ mixin المناسب.
  - `_clone(self)`: يطلب اسمًا (افتراضي "نسخة من X")، يفوّض للـ mixin المناسب، يحدّث `_current_id` ويصدر `scenario_changed`.
  - `_add_new(self)`: يطلب اسمًا (افتراضي "سيناريو N")، يفوّض للـ mixin المناسب.
  - `_delete(self)`: يمنع حذف آخر سيناريو، يطلب تأكيد، يفوّض للـ mixin المناسب.

**ملاحظات من التعليقات:** [Fix - dark theme buttons] الأزرار كانت مبنية بألوان مجمّدة وقت الإنشاء فقط بدون إعادة رسم عند تغيير الثيم — تم حله بتخزين اسم اللون كـ Qt property وإعادة البناء من `_C` الحديثة في `_refresh_buttons`.

---

### `ui/tabs/costing/shared/bom_tree.py`

**الغرض:** شجرة عرض BOM كاملة لمنتج — تعرض كل السيناريوهات كعقد (nodes) منفصلة، مع دعم الحذف الانتقائي من سيناريو معين.

**Imports داخلية مهمة:**
- `services.costing.bom_tree_service.BomTreeService`.
- `ui.theme._C`.
- `ui.widgets.core.i18n.tr`.
- `ui.widgets.dialogs.confirm.confirm_delete`.
- `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.font.FS_XS/FS_SM/FS_MD`.
- `ui.constants` — أبعاد كثيرة للشجرة.
- `.bom_tree_helper._scenario_node_builder.BomNodeRawData`, `build_scenario_node`, `build_component_node`.

**من يستدعي هذا الملف:** `ui/tabs/costing/product/product_main_panel.py` (`_ProductMainPanel._build` ينشئ `self._bom_tree = BomTree()`، يستدعي `.load(conn, pid)` و `.clear_tree()`)، و `ui/tabs/costing/product/_orphan_handler.py` (يستدعي `bom_tree.load(conn, pid)`).

**Classes:**
- **`BomTree(QWidget, WidgetMixin)`**
  - `__init__(self, parent=None)`: يهيّئ `_pid=None`, `_conn=None`، يبني الواجهة.
  - `_build(self)`: يبني هيدر (عنوان + legend توضيحي + أزرار توسيع الكل/طي الكل/حذف المحدد)، ثم `QTreeWidget` بـ 7 أعمدة (المكوّن/السيناريو، كمية، نسبة هدر، كمية فعلية، تكلفة الوحدة، إجمالي التكلفة، النوع)، عمود 0 Stretch والباقي Interactive.
  - `_make_danger_btn(text: str) -> QPushButton` *(staticmethod)*: يبني زر "حذف" بستايل خطر موحّد.
  - `_refresh_style(self, _=None)`: يحدّث ستايل الـ legend، الشجرة، الهيدر، وزر الحذف عند تغيير الثيم.
  - `load(self, conn, parent_id: int)`: يضبط `_conn`/`_pid`، يفعّل أزرار التوسيع/الطي، يستدعي `_refresh()`.
  - `clear_tree(self)`: يصفّر `_pid`، يمسح الشجرة، يعطّل الأزرار.
  - `notify_refresh(self)`: يعيد `_refresh()` لو `_pid` موجود.
  - `_fetch_node_data(self, child_type, child_id, machine_op_row_id) -> BomNodeRawData | None`: يستدعي `BomTreeService(conn).get_node_data(...)` ويبني `BomNodeRawData` من النتيجة — هذا هو الـ `data_fetcher` الممرَّر لدوال بناء الـ nodes، لتفادي وصول `_scenario_node_builder` مباشرة إلى repos/models.
  - `_refresh(self)`: يمسح الشجرة، لو `_pid is None` يتوقف. يجلب السيناريوهات عبر `BomTreeService.get_scenarios(pid)`. لو لا توجد سيناريوهات، يعرض BOM مباشر (بدون عقدة سيناريو) عبر `get_bom_for_scenario(None)` ويبني عقدة مكوّن لكل صف. لو توجد سيناريوهات، لكل سيناريو يبني `sc_node` عبر `build_scenario_node`، يجلب BOM السيناريو، يبني عقدة مكوّن لكل صف كابن للسيناريو، يجمع التكلفة الإجمالية للسيناريو ويعرضها في العمود 5، ويوسّع فقط السيناريو الافتراضي.
  - `_get_sub_bom_for_item(self, item_id: int) -> list`: يستدعي `BomTreeService(conn).get_sub_bom(item_id)` — يُمرَّر كـ `fetch_sub_bom_fn` لدعم عرض المكوّنات الفرعية لنصف مصنع متداخل.
  - `_on_selection(self)`: يفعّل/يعطّل زر الحذف حسب نوع العنصر المحدد (عقدة سيناريو → معطّل دائمًا؛ عنصر فرعي داخل نصف مصنع → معطّل؛ عنصر مباشر تحت سيناريو أو بدون سيناريوهات → مفعّل).
  - `_delete_node(self)`: يحدد نوع العقدة المحددة، لو عقدة سيناريو يتجاهل. لو الأب عقدة سيناريو → يحذف مكوّنًا من سيناريو محدد عبر `BomTreeService.delete_bom_component(sc_id, child_type, child_id)` بعد تأكيد. لو الأب مكوّن فرعي (نصف مصنع متداخل) → يعرض رسالة أن الحذف يجب أن يتم من داخل نصف المصنع نفسه. لو لا يوجد أب (BOM مباشر بدون سيناريوهات) → يحذف عبر `BomTreeService.delete_bom_row_direct(pid, child_type, child_id)`.

**ملاحظات من التعليقات:** [Fix #10] ربط `bus.theme_changed` (عبر `WidgetMixin`) لتحديث الستايل ديناميكيًا، توافقًا مع باقي لوحات costing/shared.

---

### `ui/tabs/costing/shared/machine_op_rows_editor.py`

**الغرض:** محرر صفوف عملية تشغيل (machine op) — يسمح بإضافة/تعديل/حذف بنود التكلفة الفرعية لعملية تشغيل واحدة (وصف، قيمة وقت/وحدة، عدد)، مع معاينة حية وحساب المجموع.

**Imports داخلية مهمة:**
- `services.costing.machine_op_rows_service.MachineOpRowsService`.
- `ui.theme._C`, `ui.widgets.core.i18n.tr`.
- `ui.widgets.core.events.emit_company_data_changed`.
- `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.font.FS_XS/FS_SM/FS_BASE`.
- `ui.constants` — عدد كبير من الثوابت الخاصة بأبعاد المحرر.

**من يستدعي هذا الملف:** `ui/tabs/costing/machine/machine_op_form.py` (`_MachineOpForm._build` ينشئ `self._rows_editor = _OpRowsEditor(conn)`، يستدعي `load_op`, `update_rates`, `clear`).

**Classes:**
- **`_OpRowsEditor(QGroupBox, WidgetMixin)`**
  - `__init__(self, conn, parent=None)`: يهيّئ `_op_id=None`, `_mode="time"`, `_rate_hour=0.0`, `_rate_unit=0.0`, `_editing_row_id=None`، يبني الواجهة، يبدأ معطّلاً (`setEnabled(False)`).
  - `_build(self)`: ينشئ label شرح الوضع الحالي، صف فورم (وصف، قيمة، عدد، معاينة، أزرار إضافة/حفظ/إلغاء)، جدول صفوف (5 أعمدة: id مخفي، وصف، قيمة، عدد، تكلفة الوحدة)، صف مجموع التكلفة، وصف أزرار تعديل/حذف الصف.
  - `_apply_group_style(self)` / `_apply_info_style(self)`: بناء ستايل الإطار البرتقالي وlabel المعلومات.
  - `_refresh_style(self, _=None)`: يعيد تطبيق كل الأنماط (المجموعة، info label، حقل الاسم، المعاينة، الجدول، المجموع، labels النصية، زر الحذف الأحمر) عند تغيير الثيم.
  - `load_op(self, op_id: int, mode: str, rate_per_hour: float, rate_per_unit: float)`: يضبط الحالة، يفعّل الودجت، يحدّث UI الوضع، يصفّر الفورم، يحمّل الجدول.
  - `update_rates(self, mode, rate_per_hour, rate_per_unit)`: يحدّث المعدلات، UI الوضع، المعاينة، وإن وُجد `_op_id` يعيد تحميل الجدول.
  - `clear(self)`: يصفّر كل الحالة، يعطّل الودجت.
  - `_update_mode_ui(self)`: يحدّث نص `lbl_mode_info` و`lbl_value` حسب `_mode` ("وقت" بالدقائق أو "وحدة" بالعدد).
  - `_update_preview(self)`: يحسب `unit_cost` بناءً على `_mode` (وقت: `(value/60)*rate_hour`؛ وحدة: `value*rate_unit`) مقسومًا على `count` (بحد أدنى 0.0001)، يعرضه في `lbl_preview`.
  - `_load_table(self)`: يمسح الجدول، يجلب الصفوف عبر `MachineOpRowsService(conn).list(op_id)`، لكل صف يحسب `calc_row_cost(row.id)` ويعرضه، ثم يعرض `calc_total_cost(op_id)` في `lbl_total`.
  - `_add_row(self)`: يجمع القيم، يستدعي `svc.add(op_id, label, value, count, sort_order=table.rowCount())`، يصفّر الفورم، يعيد تحميل الجدول، `emit_company_data_changed()`.
  - `_edit_row(self)`: يقرأ الصف المحدد، يجلب البيانات عبر `svc.get(rid)`، يملأ الفورم، يبدّل وضوح الأزرار لوضع التعديل.
  - `_save_edit(self)`: يستدعي `svc.update(editing_row_id, label, value, count)`، يصفّر الفورم، يعيد التحميل، `emit_company_data_changed()`.
  - `_delete_row(self)`: يمنع حذف آخر صف متبقٍ (حد أدنى صف واحد)، يستدعي `svc.delete(rid)`، يعيد التحميل، `emit_company_data_changed()`.
  - `_reset_form(self)`: يمسح `_editing_row_id`، الحقول، المعاينة، يعيد ضبط وضوح الأزرار (وضع إضافة).

**ملاحظات من التعليقات:** [Refactor] استخدام `MachineOpRowsService` بدل `machine_op_rows_repo` مباشرة، `emit_company_data_changed` بدل `bus.data_changed.emit()`، وربط `bus.theme_changed` لتحديث الستايل ديناميكيًا.

---

### `ui/tabs/costing/shared/raw_variants_panel.py`

**الغرض:** لوحة إدارة variants الخامة (صفوف الإنتاج بأعداد قطع مختلفة)، تدعم وضعين: DB mode (خامة موجودة، الحفظ فوري) و Memory mode (خامة جديدة لم تُحفظ بعد، الحفظ في الذاكرة حتى يُستدعى `save_pending_to_db`).

**Imports داخلية مهمة:**
- `services.costing.variant_service.VariantService`.
- `ui.theme._C`, `ui.widgets.core.i18n.tr`.
- `ui.widgets.core.events.emit_company_data_changed`.
- `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.widgets.tables.tables.make_table`, `make_item`, `colored_item`, `refresh_table_styles`.
- `ui.font.FS_XS/FS_SM`.
- `ui.constants` — أبعاد كثيرة.

**من يستدعي هذا الملف:** `ui/tabs/costing/raw/raw_input_panel.py` (`self._variants = _RawVariantsPanel(conn)`، يستدعي `load_item`, `enter_memory_mode`, `refresh_price`, `clear`, `save_pending_to_db`).

**Module-level function:** `_spin_pieces(max_=..., dec=...) -> QDoubleSpinBox`: ينشئ spin box لعدد القطع بقيمة ابتدائية 1.0.

**Classes:**
- **`_RawVariantsPanel(QGroupBox, WidgetMixin)`**
  - `__init__(self, conn, parent=None)`: يهيّئ `_item_id=None`, `_item_price=0.0`, `_editing_id=None`, `_memory_mode=False`, `_pending=[]` (قائمة dicts `{tmp_id, name, pieces}`)، `_pending_seq=0`. يبني الواجهة، يبدأ معطّلاً.
  - `_build(self)`: label شرح + معادلة، صف فورم (اسم، عدد قطع، معاينة، أزرار إضافة/حفظ/إلغاء)، جدول (id مخفي، اسم، عدد قطع، تكلفة الوحدة) عبر `make_table` بـ `stretch_col=-1`، صف أزرار تعديل/حذف.
  - `_apply_group_style(self)` / `_refresh_style(self, *_)`: بناء وتحديث الأنماط (إطار أزرق، info label، حقل الاسم، labels، `refresh_table_styles`، زر الحذف الأحمر).
  - `load_item(self, item_id: int, item_price: float)`: DB mode — يضبط الحالة، يفعّل اللوحة، يصفّر الفورم، يحمّل الجدول.
  - `enter_memory_mode(self, item_price=0.0)`: Memory mode — يصفّر `_item_id`، يفرّغ `_pending`، يفعّل اللوحة.
  - `get_pending_variants(self) -> list`: يرجع نسخة من `_pending` بصيغة `[{name, pieces}]`.
  - `save_pending_to_db(self, item_id: int) -> None`: يحفظ كل عناصر `_pending` فعليًا عبر `VariantService(conn).add(item_id, name, pieces)` (مع `try/except` لكل عنصر يعرض تحذيرًا عند الفشل بدلًا من إيقاف الكل)، يفرّغ `_pending`، يستدعي `load_item(item_id, _item_price)` للتحويل إلى DB mode.
  - `clear(self)`: يصفّر كل الحالة، يعطّل اللوحة.
  - `refresh_price(self, new_price: float)`: يحدّث `_item_price`، يعيد المعاينة والجدول.
  - `_load_table(self)`: لو memory mode يعرض من `_pending`؛ وإلا يجلب من `VariantService(conn).list(item_id)`.
  - `_insert_row(self, row_id, name, pieces)`: يضيف صفًا للجدول، يحسب تكلفة الوحدة (`item_price/pieces`) لو كلاهما موجب.
  - `_update_preview(self)`: يحسب ويعرض تكلفة الوحدة الحية بناءً على `sp_pieces.value()`.
  - `_add(self)`: يتحقق من الاسم؛ في memory mode يضيف لـ `_pending` بـ `tmp_id` تسلسلي؛ في DB mode يستدعي `VariantService.add(...)` مباشرة، ثم `emit_company_data_changed()`.
  - `_edit(self)`: يقرأ الصف المحدد (بـ `Qt.UserRole`)؛ في memory mode يبحث في `_pending` بـ `tmp_id`؛ في DB mode يجلب عبر `VariantService.get(vid)`؛ يملأ الفورم ويبدّل لوضع التعديل.
  - `_save_edit(self)`: في memory mode يحدّث عنصر `_pending` مباشرة؛ في DB mode يستدعي `VariantService.update(...)`، `emit_company_data_changed()`.
  - `_delete(self)`: يطلب تأكيد؛ في memory mode يزيل من `_pending`؛ في DB mode يستدعي `VariantService.delete(vid)`، `emit_company_data_changed()`.
  - `_reset_form(self)`: يمسح `_editing_id`، الحقول، المعاينة، يعيد وضوح الأزرار.

**ملاحظات من التعليقات:** [Feature] شرح كامل لآلية "وضع الذاكرة" في docstring الملف — الغرض السماح بإضافة variants قبل حفظ الخامة الأم نفسها.

---

### `ui/tabs/costing/shared/scenario_comparison_widget.py`

**الغرض:** ودجت يقارن تكلفة السيناريو الافتراضي لمنتج بأي سيناريو آخر مختار — يعرض التكلفتين، الفرق، الربح في كل سيناريو، فرق الربح، وهامش الربح.

**Imports داخلية مهمة:**
- `models.costing.calc_cost`.
- `services.costing.scenario_service.ScenarioService`.
- `ui.theme._C`, `ui.widgets.core.i18n.tr`.
- `ui.widgets.components.stat_card.stat_card_pair`.
- `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.font.FS_XS/FS_SM/FS_BASE/FS_MD/FS_LG`.
- `ui.constants` — أبعاد كثيرة.

**من يستدعي هذا الملف:** غير محدد من المرفقات الحالية (لا يوجد ملف مرفق يستورده صراحة ضمن هذه الدفعة، رغم توفره في نفس المسار).

**Classes:**
- **`ScenarioComparisonWidget(ThemedFrame, WidgetMixin)`**
  - `__init__(self, conn, parent=None)`: يهيّئ `_item_id=None`, `_fixed_price=0.0`, `_default_cost=0.0`، يبني الواجهة.
  - `_build(self)`: هيدر (أيقونة، عنوان، تسمية "قارن بسيناريو" + combo)، صف تكاليف (3 stat cards: تكلفة الافتراضي، تكلفة المقارن، الفرق)، صف ربح (5 stat cards: السعر الثابت، ربح الافتراضي، ربح المقارن، فرق الربح، هامش ربح المقارن)، label توجيهي.
  - `_apply_frame_style(self)` / `_refresh_style(self, *_)`: بناء وتحديث ستايل الإطار البنفسجي، العنوان، الـ combo، والـ label.
  - `load_product(self, item_id: int, fixed_price: float)`: يضبط الحالة، يحسب `_default_cost` عبر `_calc_default_cost`، يعيد تحميل قائمة السيناريوهات.
  - `update_price(self, new_price: float)`: يحدّث `_fixed_price`، يعيد المقارنة.
  - `clear(self)`: يصفّر الحالة، يمسح الـ combo، يعيد ضبط الـ labels لحالتها الافتراضية.
  - `_reload_scenarios(self)`: يمسح الـ combo، يضيف عنصر placeholder، يجلب سيناريوهات المنتج عبر `ScenarioService(conn).list(item_id)`، يملأ الـ combo (نجمة للافتراضي)، يستدعي `_refresh_comparison()`.
  - `_calc_default_cost(self, item_id) -> float`: `calc_cost(conn, item_id)`.
  - `_calc_scenario_cost(self, scenario_id) -> float`: يستدعي `ScenarioService(conn).calc_cost(scenario_id)` (مع `try/except` يرجع 0.0).
  - `_refresh_comparison(self)`: يحسب ويعرض كل القيم (تكلفة افتراضي، ربح افتراضي، ولو تم اختيار سيناريو مقارنة: تكلفته، فرق التكلفة، ربحه، فرق الربح، هامشه)، يلوّن كل label حسب الإشارة (موجب/سالب/صفر)، ويبني رسالة توجيهية نصية تلخّص الفرق.
  - `_color_label(self, lbl, value)`: يلوّن label بالأخضر (موجب)/أحمر (سالب)/رمادي (صفر).
  - `_reset_labels(self)`: يعيد كل الـ labels لحالة placeholder.
  - `_on_scenario_changed(self, _)`: يستدعي `_refresh_comparison()`.

**ملاحظات من التعليقات:** [Refactor] استخدام `ScenarioService.calc_cost` بدل منطق حساب معقد كان مضمّنًا داخل الودجت مباشرة سابقًا.

---

## القسم 8: `ui/tabs/costing/shared/bom_scenarios/`

### `ui/tabs/costing/shared/bom_scenarios/_db_scenarios.py`

**الغرض:** Mixin يضيف منطق تحميل وإدارة سيناريوهات BOM من قاعدة البيانات (DB mode) — يُستخدم حصريًا كجزء من `_BomScenariosPanel`.

**Imports داخلية مهمة:**
- `services.costing.scenario_service.ScenarioService`.
- `ui.widgets.core.events.emit_company_data_changed`.
- `ui.widgets.core.i18n.tr`.

**من يستدعي هذا الملف:** `ui/tabs/costing/shared/bom_scenarios_panel.py` (`_BomScenariosPanel` يرث من `DbScenariosMixin`).

**Classes:**
- **`DbScenariosMixin`** (Mixin — يفترض وجود `self.conn`, `self._item_id`, `self._scenarios`, `self._current_id`, `self._in_memory`, `self._rebuild_combo()`, `self._sync_current()`, `self.scenario_changed`)
  - `load_item(self, item_id: int)`: يضبط `_in_memory=False`, `_item_id=item_id`، يستدعي `_reload()`.
  - `ensure_default_scenario(self, item_id: int) -> int`: يستدعي `ScenarioService(conn).ensure_default(item_id)` — يضمن وجود سيناريو افتراضي، ينشئ واحدًا إن لم يوجد.
  - `_reload(self)`: يجلب سيناريوهات المنتج عبر `ScenarioService(conn).list(item_id)`، يحوّلها لقائمة dicts (id, name, is_default)؛ يحاول الحفاظ على `_current_id` السابق لو ما زال موجودًا، وإلا يختار السيناريو الافتراضي؛ يستدعي `_rebuild_combo()` و `_sync_current()`.
  - `_db_set_default(self, scenario_id: int)`: `ScenarioService.set_default(scenario_id)`، `emit_company_data_changed()`، `_reload()`.
  - `_db_rename(self, scenario_id: int, name: str)`: `ScenarioService.rename(...)`، `emit_company_data_changed()`، `_reload()`.
  - `_db_clone(self, scenario_id: int, name: str) -> int | None`: `ScenarioService.clone(...)`، `emit_company_data_changed()`، يرجع الـ id الجديد أو `None` عند استثناء (يعرض `QMessageBox.warning`).
  - `_db_add_new(self, name: str) -> int | None`: يتطلب `_item_id` غير `None`؛ `ScenarioService.create(item_id, name, is_default=False)`، `emit_company_data_changed()`.
  - `_db_delete(self, scenario_id: int) -> bool`: `ScenarioService.delete(scenario_id)`، لو نجح `emit_company_data_changed()`، يرجع النتيجة.

**ملاحظات من التعليقات:** [Refactor] استخدام `ScenarioService` بدل `bom_scenarios_repo` مباشرة، [Fix] `emit_company_data_changed` بدل `bus.data_changed.emit()`، [Fix] استخدام مفتاح ترجمة `tr("error")` بدل نص مباشر.

---

### `ui/tabs/costing/shared/bom_scenarios/_memory_scenarios.py`

**الغرض:** Mixin يضيف منطق إدارة سيناريوهات BOM في الذاكرة (لمنتجات جديدة لم تُحفظ بعد) — يُستخدم حصريًا كجزء من `_BomScenariosPanel`.

**Imports داخلية مهمة:** `ui.widgets.core.i18n.tr`.

**من يستدعي هذا الملف:** `ui/tabs/costing/shared/bom_scenarios_panel.py` (`_BomScenariosPanel` يرث من `MemoryScenariosMixin`).

**Class-level attribute:** `_NEXT_TEMP_ID = -1` — عداد مشترك على مستوى الـ class لتوليد IDs مؤقتة سالبة فريدة.

**Classes:**
- **`MemoryScenariosMixin`** (Mixin — يفترض وجود `self._scenarios`, `self._current_id`, `self._in_memory`, `self._item_id`, `self._rebuild_combo()`, `self._sync_current()`, `self.scenario_changed`)
  - `_next_temp_id(self) -> int`: يُنقص `_NEXT_TEMP_ID` (على مستوى الـ class) ويرجع القيمة الجديدة — يضمن id سالب فريد لكل سيناريو مؤقت.
  - `_init_memory_scenario(self)`: ينشئ سيناريو افتراضي واحد في الذاكرة (اسمه `tr("default_scenario_initial_name")`، `is_default=True`) بـ id مؤقت، يضبطه كحالي، يعيد بناء الـ combo.
  - `get_memory_scenarios(self) -> list`: يرجع نسخة من `_scenarios` — تُستخدم عند حفظ منتج جديد لكتابة السيناريوهات في DB.
  - `get_current_memory_index(self) -> int`: يرجع فهرس السيناريو الحالي في قائمة `_scenarios` (أو 0 افتراضيًا).
  - `switch_to_db_mode(self, item_id: int, current_scenario_index: int = 0)`: يحوّل من in-memory إلى DB mode بعد حفظ المنتج — يمسح الحالة المؤقتة ويستدعي `_reload()` (المُعرَّفة في `DbScenariosMixin`).
  - `_memory_set_default(self, scenario_id: int)`: يضبط `is_default=True` للسيناريو المطابق و`False` للباقي.
  - `_memory_rename(self, scenario_id: int, name: str)`: يحدّث اسم السيناريو المطابق.
  - `_memory_clone(self, from_id: int, name: str) -> int`: يضيف سيناريو جديد بـ id مؤقت جديد مع `_cloned_from` يشير للمصدر.
  - `_memory_add_new(self, name: str) -> int`: يضيف سيناريو فارغ جديد بـ id مؤقت.
  - `_memory_delete(self, scenario_id: int) -> bool`: يرفض الحذف لو آخر سيناريو متبقٍ (يرجع `False`)؛ وإلا يحذف، ولو كان المحذوف هو الافتراضي ينقل الصفة لأول سيناريو متبقٍ، يحدّث `_current_id`، يرجع `True`.

**ملاحظات من التعليقات:** [Fix] استخدام مفتاح ترجمة `default_scenario_initial_name` بدل نص عربي مباشر.

---

## القسم 9: `ui/tabs/costing/shared/bom_tree_helper/`

### `ui/tabs/costing/shared/bom_tree_helper/_scenario_node_builder.py`

**الغرض:** منطق بناء عقد (nodes) السيناريو والمكوّنات في شجرة BOM — مُستخرج من `bom_tree.py` لتقليل حجمه وتسهيل الاختبار. لا يصل لأي repo أو DB مباشرة؛ يعتمد بالكامل على دالة `data_fetcher` تُمرَّر إليه من `BomTree`.

**Imports داخلية مهمة:**
- `models.costing_base.effective_qty` — حساب الكمية الفعلية بعد نسبة الهدر.
- `ui.widgets.core.i18n.tr`.
- (استيراد كسول داخلي: `from ui.theme import _C` داخل `_theme_colors()` لتفادي استيراد دائري).

**من يستدعي هذا الملف:** `ui/tabs/costing/shared/bom_tree.py` (يستورد `BomNodeRawData`, `build_scenario_node`, `build_component_node`).

**Data class:**
- **`BomNodeRawData`** *(dataclass)*: `name: str`, `unit_cost: float`, `op_row_label: Optional[str] = None` (لعمليات machine_op فقط) — البيانات الأولية اللازمة لبناء node واحد، تُملأ من `BomTree` (الذي يملك الاتصال).

**Module-level functions:**
- `_theme_colors() -> dict`: يرجع `_C` الحالية (قراءة كسولة، استيراد داخل الدالة لتفادي استيراد دائري).
- `_type_label(child_type: str) -> str`: يبني تسمية النوع (أيقونة + نص مترجم) من مفاتيح i18n حسب النوع (`raw`, `semi`, `labor_op`, `machine_op`)؛ يرجع سلسلة فارغة لنوع غير معروف.
- `_type_color(child_type: str, colors: dict) -> str`: يرجع لون النوع من الثيم (blue للخامة، purple لنصف مصنع، acc_type_capital للعمالة، orange للتشغيل؛ افتراضي text_primary).
- `build_scenario_node(sc: dict) -> QTreeWidgetItem`: يبني عقدة السيناريو — نص يحتوي نجمة (لو افتراضي) + اسم + لاحقة "(افتراضي)"، يخزّن `("__scenario__", sc_id)` في `Qt.UserRole`، خط عريض بحجم أكبر بمقدار 1، لون خلفية/نص مختلف حسب كونه افتراضيًا أو لا (من الثيم).
- `build_component_node(data_fetcher, child_type, child_id, qty, waste_pct=0.0, qty_multiplier=1.0, machine_op_row_id=None, fetch_sub_bom_fn=None) -> QTreeWidgetItem | None`: يستدعي `data_fetcher(child_type, child_id, machine_op_row_id)`؛ لو `None` يرجع `None`. يحسب `effective_qty`، `total_eff = eff_qty * qty_multiplier`، `total_cost = unit_cost * total_eff`. يبني نص كل عمود (كمية، هدر، كمية فعلية، تكلفة وحدة، تكلفة إجمالية، تسمية النوع) مع tooltips تفصيلية لكل عمود. يخزّن `(child_type, child_id)` في `Qt.UserRole`. يلوّن عمود النوع حسب `_type_color`؛ لو فيه هدر يلوّن عمودي الهدر والكمية الفعلية بالبرتقالي وخلفية تحذيرية. **حالة خاصة لنصف مصنع (`semi`)**: خط عريض، لون مميز، ولو `fetch_sub_bom_fn` موجودة يستدعيها لجلب BOM الفرعي ويبني عقدة ابن لكل عنصر فرعي (استدعاء تكراري لنفس الدالة، مع `qty_multiplier=total_eff` لضرب الكميات المتداخلة بشكل صحيح).
- `_fmt_qty(qty: float) -> str`: يرجع الكمية كعدد صحيح لو لا كسور، وإلا بصيغة `%.4g`.

**ملاحظات من التعليقات:** [Refactor] إزالة كل استدعاء مباشر لـ repos/models من هذا الملف — البيانات تصل عبر `data_fetcher` فقط. [Fix i18n]/[Fix colors] كل النصوص والألوان تأتي من `tr()`/`_C` حصرًا.

---

## القسم 10: `ui/tabs/costing/shared/bulk_replace/`

### `ui/tabs/costing/shared/bulk_replace/_operation_section.py`

**الغرض:** قسم اختيار نوع العملية (استبدال عنصر / تعديل كمية فقط / كلاهما) داخل نافذة الاستبدال الشامل، ويوفر واجهة قراءة لحالة الاختيار.

**Imports داخلية مهمة:**
- `ui.theme._C`, `ui.widgets.core.i18n.tr`.
- `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.constants` — أبعاد القسم.
- `ui.font.FS_BASE`, `FS_SM`.

**من يستدعي هذا الملف:** `ui/tabs/costing/shared/bulk_replace/bulk_replace_dialog.py` (`BulkReplaceDialog._build` ينشئ `self._op_section = _OperationSection(self.child_type)`).

**Classes:**
- **`_OperationSection(QGroupBox, WidgetMixin)`**
  - `__init__(self, child_type: str, parent=None)`: يحفظ `_child_type`، يبني القسم.
  - `_build(self)`: صف radio buttons (استبدال العنصر / تعديل الكمية فقط / كلاهما — الافتراضي "كلاهما")؛ إطار `_replace_frame` يحتوي combo البديل (`_cmb_replacement`) وصف كمية موحدة (checkbox + spin box)؛ يربط `toggled` لكل radio بـ `_update_ui`.
  - `_refresh_style(self, *_)`: يحدّث ستايل المجموعة، radio buttons، checkbox، combo، والإطار عند تغيير الثيم.
  - `_refresh_lang(self, *_)`: يحدّث نصوص العنوان وrRadio buttons وcheckbox عند تغيير اللغة.
  - `do_replace` *(property)*: `True` لو radio الاستبدال أو "كلاهما" مفعّل.
  - `do_qty` *(property)*: `True` لو radio الكمية أو "كلاهما" مفعّل.
  - `new_child_id` *(property)*: يرجع `currentData()` من combo البديل، أو `None` لو كانت قيمة خاصة (`None`, `"__sep__"`, `"__empty__"`).
  - `uniform_qty` *(property)*: يرجع قيمة spin box لو checkbox الكمية الموحدة مفعّل، وإلا `None`.
  - `load_candidates(self, candidates: list[tuple])`: يملأ combo البديل بعناصر `(id, name, category)`؛ يضيف فواصل غير قابلة للاختيار بين كل تصنيف؛ لو لا توجد بدائل يعطّل الاستبدال ويجبر وضع "تعديل كمية فقط".
  - `_update_ui(self)`: يفعّل/يعطّل combo البديل ويحدّث ستايل الإطار حسب `do_replace`.
  - `_update_frame_style(self, active: bool)`: يلوّن `_replace_frame` بلون معلوماتي (نشط) أو محايد (غير نشط).

---

### `ui/tabs/costing/shared/bulk_replace/bulk_replace_dialog.py`

**الغرض:** النافذة الرئيسية لـ "الاستبدال الشامل" — تُفتح من تبويبات الخامات/العمالة/التشغيل لإحلال عنصر BOM بآخر و/أو تعديل الكمية عبر عدة منتجات دفعة واحدة. تجمع `_OperationSection` و `_ProductsPanel` وتنسّق تطبيق العملية عبر `BulkReplaceService`.

**Imports داخلية مهمة:**
- `services.costing.bulk_replace_service.BulkReplaceService`.
- `ui.widgets.core.events.bus`, `emit_company_data_changed`.
- `ui.theme._C`, `ui.widgets.core.i18n.tr`.
- `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.constants` — أبعاد كثيرة للنافذة.
- `ui.font.FS_MD/FS_LG/FS_SM`.
- `.bulk_replace_products_panel._ProductsPanel`.
- `._operation_section._OperationSection`.

**من يستدعي هذا الملف:** `ui/tabs/costing/machine/machine_op_table.py`, `ui/tabs/costing/labor/labor_op_table.py`, `ui/tabs/costing/raw/raw_table_panel.py` (جميعها تفتح `BulkReplaceDialog(conn, child_type, child_id, child_name, parent)`).

**Classes:**
- **`BulkReplaceDialog(QDialog, WidgetMixin)`**
  - `__init__(self, conn, child_type: str, child_id: int, child_name: str = None, parent=None)`: يهيّئ `_svc = BulkReplaceService(conn)`؛ لو `child_name` غير مُمرَّر يجلبه عبر `_svc.get_element_name(...)`؛ يضبط عنوان النافذة، الحجم الأدنى، RTL؛ يبني الواجهة؛ يحمّل المرشحين للاستبدال.
  - `_build(self)`: هيدر متدرج اللون + جسم يحتوي `_OperationSection`، `_ProductsPanel`، وصف أزرار الإجراء؛ يستدعي `_update_apply_btn_state()`.
  - `_build_header(self) -> ThemedFrame`: هيدر بتدرج لوني أزرق، أيقونة، وعنوان يتضمن اسم العنصر بلون مميز (RichText).
  - `_build_action_buttons(self) -> QHBoxLayout`: زر "تطبيق على المحدد" (أزرق، يُعطَّل تلقائيًا لو لا توجد منتجات) وزر "إغلاق".
  - `_refresh_style(self, *_)`: يعيد ستايل زر التطبيق فقط (إعادة بناء الهيدر بالكامل تتطلب rebuild أكبر، لم تُعد هنا).
  - `_refresh_lang(self, *_)`: يحدّث عنوان النافذة ونص زر التطبيق.
  - `_load_candidates(self)`: يجلب المرشحين عبر `_svc.fetch_candidates(child_type, child_id)` ويمررهم لـ `_op_section.load_candidates(...)`.
  - `_update_apply_btn_state(self)`: يفعّل/يعطّل زر التطبيق حسب `_products_panel.has_products()`.
  - `_apply(self)`: يجلب الصفوف المحددة (يعرض تحذيرًا لو لا شيء محدد)؛ يقرأ `do_replace`, `do_qty`, `new_child_id`, `uniform_qty` من `_op_section`؛ يتحقق من اختيار بديل لو `do_replace`؛ يبني وصف نصي للعملية ويطلب تأكيد المستخدم؛ يستدعي `BulkReplaceService(conn).apply(child_type, old_child_id, new_child_id, product_rows, uniform_qty, do_replace, do_qty)`؛ `emit_company_data_changed()`؛ يعرض رسالة نجاح أو نجاح-مع-أخطاء؛ لو `do_replace` يغلق النافذة (`accept()`), وإلا يعيد تحميل لوحة المنتجات فقط (يسمح بتكرار تعديل الكمية).

**ملاحظات من التعليقات:** [Refactor] استخدام `BulkReplaceService` بدل استدعاء `db.shared.items_repo` مباشرة. [Fix i18n] كل النصوص المكتوبة مباشرة (عنوان، رسائل، أزرار) انتقلت لمفاتيح ترجمة. [Fix colors] كل الألوان hardcoded استُبدلت بمفاتيح `_C`.

---

### `ui/tabs/costing/shared/bulk_replace/bulk_replace_helpers.py`

**الغرض:** يحتوي حاليًا فقط عنصر واجهة `ProductRow` — صف منتج واحد قابل للاختيار داخل لوحة المنتجات المتأثرة في نافذة الاستبدال الشامل، مع checkbox وحقل كمية قابل للتعديل.

**ملاحظة هيكلية مهمة من الكود:** هذا الملف كان يحتوي سابقًا أيضًا على منطق أعمال واستعلامات DB (`get_element_name`, `fetch_candidates`, `fetch_affected_products`) — وهو كسر لمبدأ أن `ui/` يجب أن يستدعي `services/` فقط. هذه الدوال الثلاث **انتقلت بالكامل** إلى `services/costing/bulk_replace_service.py` (`BulkReplaceService`)، ولم تعد موجودة في هذا الملف.

**Imports داخلية مهمة:**
- `ui.widgets.panels.themed_inputs.ThemedFrame`.
- `ui.theme._C`, `ui.widgets.core.i18n.tr`.
- `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.constants` — أبعاد الصف.
- `ui.font.FS_BASE/FS_SM/FS_XS`.

**من يستدعي هذا الملف:** `ui/tabs/costing/shared/bulk_replace/bulk_replace_products_panel.py` (`_ProductsPanel` ينشئ `ProductRow(prod)` لكل منتج).

**Classes:**
- **`ProductRow(ThemedFrame, WidgetMixin)`**
  - `__init__(self, product: dict, parent=None)`: يحفظ `_product`، يبني الصف.
  - `_build(self)`: checkbox (مفعّل افتراضيًا)، أيقونة نوع المنتج (🔧 نصف مصنع / 🏭 نهائي)، عمود معلومات (اسم + تصنيف/تكلفة)، حقل كمية (`QDoubleSpinBox`) بقيمة ابتدائية من `product["qty"]`. يربط `toggled` لـ checkbox بـ `_on_toggle`.
  - `_refresh_style(self, *_)`: يعيد تطبيق ستايل الإطار ولون الاسم حسب حالة `checked`.
  - `_apply_style(self, checked: bool)`: ستايل خلفية/حدود مختلف حسب `checked` (لون accent مفعّل / رمادي معطّل، مع hover).
  - `_on_toggle(self, checked: bool)`: يفعّل/يعطّل حقل الكمية، يعيد تطبيق الستايل، يلوّن اسم المنتج.
  - `is_selected` *(property)*: حالة الـ checkbox.
  - `product_id` *(property)*: `self._product["id"]`.
  - `new_qty` *(property)*: قيمة حقل الكمية الحالية.
  - `set_selected(self, val: bool)`: يضبط حالة الـ checkbox برمجيًا.

---

### `ui/tabs/costing/shared/bulk_replace/bulk_replace_products_panel.py`

**الغرض:** لوحة عرض المنتجات المتأثرة بعملية الاستبدال الشامل — فلتر بالتصنيف، قائمة صفوف قابلة للتمرير (`ProductRow`)، وشريط تحديد سريع (تحديد الكل/إلغاء الكل/عكس التحديد).

**Imports داخلية مهمة:**
- `ui.theme._C`, `ui.widgets.core.i18n.tr`.
- `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.constants` — أبعاد كثيرة للوحة.
- `ui.font.FS_SM`.
- `services.costing.bulk_replace_service.BulkReplaceService`.
- `.bulk_replace_helpers.ProductRow`.

**من يستدعي هذا الملف:** `ui/tabs/costing/shared/bulk_replace/bulk_replace_dialog.py` (`BulkReplaceDialog._build` ينشئ `self._products_panel = _ProductsPanel(conn, child_type, child_id)`).

**Classes:**
- **`_ProductsPanel(QWidget, WidgetMixin)`**
  - `__init__(self, conn, child_type: str, child_id: int, parent=None)`: يهيّئ `_svc = BulkReplaceService(conn)`, `_all_products=[]`, `_product_rows=[]`، يبني الواجهة، يستدعي `load()`.
  - `_build(self)`: صف فلتر (label + combo تصنيفات + عداد)، منطقة صفوف قابلة للتمرير (`QScrollArea`)، شريط تحديد سريع (`_build_quick_bar`).
  - `_build_quick_bar(self) -> ThemedFrame`: يبني إطارًا يحتوي 3 أزرار (تحديد الكل، عدم التحديد، عكس التحديد) مربوطة بـ `select_all`/`invert_selection`.
  - `_refresh_style(self, *_)` / `_refresh_lang(self, *_)`: تحديث الأنماط والنصوص عند تغيير الثيم/اللغة.
  - `load(self)`: يجلب المنتجات المتأثرة عبر `_svc.fetch_affected_products(child_type, child_id)`، يملأ فلتر التصنيف، يبني الصفوف.
  - `reload(self)`: نفس `load` لكن يطبّق الفلتر الحالي بدل إعادة البناء الكامل (يُستدعى بعد تطبيق عملية جزئية مثل تعديل كمية فقط).
  - `_fill_category_filter(self)`: يجمع تصنيفات فريدة من `_all_products`، يملأ الـ combo مرتبة أبجديًا.
  - `_apply_filter(self)`: يفلتر `_all_products` حسب `cmb_cat_filter.currentData()` ويعيد بناء الصفوف.
  - `_rebuild_rows(self, products: list)`: يمسح الصفوف الحالية، لو القائمة فارغة يعرض رسالة "لا توجد منتجات مرتبطة"، وإلا ينشئ `ProductRow` لكل منتج.
  - `_update_count(self)`: يحدّث `lbl_count` بعدد الكل والمحدد.
  - `select_all(self, val: bool)`: يضبط كل الصفوف على `val`.
  - `invert_selection(self)`: يعكس تحديد كل صف.
  - `get_selected_rows(self) -> list`: يرجع الصفوف المحددة فقط.
  - `has_products(self) -> bool`: `True` لو توجد صفوف.

---

## قسم علاقات الملفات

### علاقات الاستيراد الداخلية (ضمن هذا المرجع)

- **`costing_section.py`** يستورد → `costing/raw_tab.py` (`RawTab`), `costing/product_tab.py` (`ProductTab`), `costing/labor_tab.py` (`LaborTab`), `costing/machine_tab.py` (`MachineTab`) — وهو المُستدعي الفعلي لجميع التابات الرئيسية الأربعة الموصوفة في القسم 1.
- **`raw_tab.py`** يستورد → `raw/raw_section.py`.
- **`raw/raw_section.py`** يستورد → `raw/raw_input_panel.py`, `raw/raw_table_panel.py` (يرث من `BaseSection` خارجي).
- **`raw/raw_input_panel.py`** يستورد → `shared/raw_variants_panel.py`.
- **`raw/raw_table_panel.py`** يستورد → `shared/_utils.py` (`to_dict`, ألوان shared/published)، ويفتح `shared/bulk_replace/bulk_replace_dialog.py`.
- **`machine_tab.py`** يستورد → `machine/machine_form.py`, `machine/machine_table.py`, `machine/machine_op_form.py`, `machine/machine_op_table.py`.
- **`machine/machine_op_form.py`** يستورد → `shared/machine_op_rows_editor.py`.
- **`machine/machine_op_table.py`** يستورد → `machine/machine_op_form.py` (type hint فقط)، `shared/bulk_replace/bulk_replace_dialog.py`.
- **`machine/machine_table.py`** يستورد → `machine/machine_form.py`، `shared/_utils.py`.
- **`labor_tab.py`** يستورد → `labor/labor_settings.py`, `labor/labor_op_form.py`, `labor/labor_op_table.py`.
- **`labor/labor_op_form.py`** يعتمد على `_LaborSettingsPanel` (كائن مُمرَّر، وليس import مباشر للملف — `labor_settings.py` لا يُستورد داخل `labor_op_form.py` بل يُمرَّر ككائن حي).
- **`labor/labor_op_table.py`** يستورد → `shared/_utils.py`, `shared/bulk_replace/bulk_replace_dialog.py`.
- **`product_tab.py`** يستورد → `product/product_main_panel.py`.
- **`product/product_main_panel.py`** يستورد → `product/product_form.py`, `product/product_table.py`, `product/_catalog_provider.py`, `product/_orphan_handler.py`, `shared/bom_tree.py`.
- **`product/product_form.py`** يستورد → `product/form/_header_bar.py`, `product/form/_rows_manager.py`, `product/form/_save_logic.py`.
- **`product/form/_header_bar.py`** يستورد → `shared/bom_scenarios_panel.py`.
- **`shared/bom_scenarios_panel.py`** يستورد → `shared/bom_scenarios/_memory_scenarios.py`, `shared/bom_scenarios/_db_scenarios.py` (Mixins).
- **`shared/bom_tree.py`** يستورد → `shared/bom_tree_helper/_scenario_node_builder.py`.
- **`shared/bulk_replace/bulk_replace_dialog.py`** يستورد → `shared/bulk_replace/_operation_section.py`, `shared/bulk_replace/bulk_replace_products_panel.py`.
- **`shared/bulk_replace/bulk_replace_products_panel.py`** يستورد → `shared/bulk_replace/bulk_replace_helpers.py` (`ProductRow`).

### أنماط بناء مشتركة

- **وراثة `TabSectionBase`**: `RawTab`, `MachineTab`, `LaborTab`, `ProductTab` — كلها تمرر `conn_fn=CompanyService.get_active_erp_conn` وتُعرِّف `_build_tabs` و `_tab_label`.
- **وراثة `BaseCrudForm`**: `RawInputPanel`, `LaborOpForm` — تعتمد على hooks `_build_fields`, `_collect`, `_do_insert`, `_do_update`, `_do_load`, `_fill_fields`, `_reset_fields`.
- **وراثة `EditModeMixin` + `LiveConnMixin` + `WidgetMixin`**: `_MachineForm`, `_MachineOpForm` (نمط فورم يدوي البناء بدل `BaseCrudForm`).
- **وراثة `SharedItemsListPanel`**: `LaborOpTable`, `_MachineOpTable`, `_MachineTable` — توفر منطق العناصر المشتركة/المنشورة، الفلترة، والأزرار الموحدة (`SHARED_TYPE`, `TABLE_COLS`, `FILTER_SCOPE`, `TABLE_TITLE`, `HAS_BULK_REPLACE` كـ class attributes، و`_fetch_local_rows`, `_get_shared_rows`, `_fill_table_row`, `_edit_item`, `_delete_item` كـ hooks).
- **وراثة `BaseListPanel`**: `RawTablePanel` (+ `SharedOpsMixin`), `_ProductTable` — نفس نمط `COLUMNS`, `STRETCH_COL`, `_load_rows`, `_fill_row`.
- **نمط `_refresh_style(self, *_)`**: متكرر في كل ملف يرث `WidgetMixin` — دالة موحدة تُستدعى عند إشارة `bus.theme_changed` لإعادة بناء الـ stylesheets من `ui.theme._C` الحالية.
- **نمط "وضع الذاكرة/DB"**: مكرر في `_RawVariantsPanel` و `bom_scenarios/_memory_scenarios.py` + `_db_scenarios.py` — كلاهما يسمح بالعمل على بيانات في الذاكرة قبل حفظ الكائن الأب، ثم نقلها فعليًا لقاعدة البيانات بعد الحصول على ID حقيقي.
- **`emit_company_data_changed()`**: نمط موحّد يُستدعى بعد أي عملية إضافة/تعديل/حذف تقريبًا في كل الملفات، بدل الاتصال المباشر القديم بـ `bus.data_changed.emit()`.

### تبعيات خارج هذا المسار (تُذكر بالاسم فقط)

- `ui.widgets.theme.layout_styles` (`tab_style`, `apply_tab_widths`, `normalize_tab_widget`) — يستخدمها `costing_section.py` فقط ضمن هذا المرجع.
- `ui.widgets.base.tab_section.TabSectionBase`, `ui.widgets.base.section.BaseSection`, `ui.widgets.base.crud_form.BaseCrudForm`, `ui.widgets.base.list_panel.BaseListPanel`.
- `ui.widgets.shared.list_panel_with_shared.SharedItemsListPanel`.
- `ui.widgets.mixins.shared_ops.SharedOpsMixin`, `ui.widgets.mixins.form_mixins.EditModeMixin`.
- `ui.widgets.core.conn.LiveConnMixin`, `ui.widgets.core.widget_mixin.WidgetMixin`, `ui.widgets.core.events` (`bus`, `emit_company_data_changed`), `ui.widgets.core.i18n.tr`.
- `ui.widgets.managers.category.CategoryManager`.
- `ui.widgets.combo.category.CategoryCombo`.
- `ui.widgets.panels.*` (form_group, form_fields, form_badges, themed_inputs).
- `ui.widgets.components.*` (button, notification, stat_card, component_row).
- `ui.widgets.tables.tables`, `ui.widgets.theme.builders`, `ui.widgets.dialogs.confirm`.
- `ui.tabs.companies.shared_items_mixin` (`get_shared_raws`, `get_shared_labor_ops`, `get_shared_machines`, `get_shared_machine_ops`, `get_published_local_names`, `is_shared_id`).
- `ui.theme._C`, `ui.font.*`, `ui.constants`.
- `services.costing.*` (machine_service, machine_op_rows_service, product_service, scenario_service, variant_service, labor_op_service, catalog_service, bom_tree_service, bulk_replace_service).
- `services.shared.item_service.ItemService`, `services.shared.settings_service.SettingsService`.
- `services.companies.company_service.CompanyService`.
- `models.costing`, `models.costing_base`.
