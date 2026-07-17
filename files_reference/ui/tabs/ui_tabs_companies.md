# ui_tabs_companies.md — ملف مرجعي لمسار `ui/tabs/companies`

يغطي هذا الملف كل الملفات الموجودة مباشرة تحت `ui/tabs/companies/`، بالإضافة إلى المجلد الفرعي `shared_items_manager_helper/` كقسم فرعي.

---

## `ui/tabs/companies/no_company_screen.py`

### الغرض من الملف
شاشة ترحيب تظهر للمستخدم عندما لا توجد شركة نشطة محددة بعد، وتحتوي على زر لفتح نافذة إدارة الشركات.

### الـ imports الخارجية المهمة
- `ui.widgets.core.widget_mixin.WidgetMixin` — يمنح الكلاس القدرة على `_init_widget_mixin`، والتحديث التلقائي للستايل/اللغة عبر `_refresh_style`/`_refresh_lang`.
- `ui.font` (`FS_BASE`, `FS_XL`, `fs`) — أحجام الخطوط.
- `ui.widgets.core.i18n.tr` — الترجمة النصية.
- `ui.constants` (`NO_COMPANY_BTN_H`, `NO_COMPANY_BTN_W`, `NO_COMPANY_BTN_RADIUS`, `NO_COMPANY_SPACING`) — ثوابت القياسات.

### من يستدعي هذا الملف
- `ui/main_window.py` — يستورده ويعرضه في `_stack` عندما لا توجد شركة نشطة (`is_company_ready() == False`)، ويستمع لـ `open_manager` signal لفتح `CompaniesDialog` (مؤكَّد من بنية `MainWindow`)

### الـ Classes

#### `NoCompanyScreen(QWidget, WidgetMixin)`
- **الوصف:** شاشة الترحيب التي تظهر قبل اختيار شركة نشطة.
- **Signals:**
  - `open_manager = pyqtSignal()` — يُطلَق عند الضغط على زر الإضافة، لفتح نافذة إدارة الشركات.
- **Methods:**
  - `__init__(self, parent=None)`: يستدعي `_init_widget_mixin(data=False)`، ثم `_build()`, `_refresh_style()`, `_refresh_lang()`.
  - `_build(self)`: يبني تخطيط عمودي (`QVBoxLayout`) موسّط، ويضيف: أيقونة (`_ico`)، عنوان (`_title`)، نص فرعي ملتف (`_sub` مع `setWordWrap(True)`)، وزر (`_btn`) بحجم ثابت مربوط بـ `open_manager.emit` عبر `clicked.connect(self.open_manager)`.
  - `_refresh_style(self, *_)`: يستورد `_C` من `ui.theme` بشكل lazy، ويضبط الستايل: حجم خط الأيقونة (`FS_XL+16`)، العنوان بخط عريض ولون `text_primary`، النص الفرعي بلون `text_muted`، والزر بلون `accent` مع `hover` للون `accent_hover` وحواف دائرية بقيمة `NO_COMPANY_BTN_RADIUS`.
  - `_refresh_lang(self, *_)`: يملأ النصوص عبر `tr(...)` لكل من: أيقونة اختيار الشركة (`company_selector_icon`)، عنوان الترحيب (`no_company_welcome`)، النص الفرعي (`no_company_subtitle`)، ونص الزر (`no_company_add_btn`).

### الثوابت على مستوى الملف
لا يوجد — كل الثوابت مستوردة من `ui.constants`.

### ملاحظات من التعليقات
تعليق توثيقي بسيط يوضح أن الملف "شاشة تظهر لما ما فيش شركة محددة بعد"، مع ملاحظة أن مسار الملف الموثّق داخل الـ docstring (`ui/widgets/shared/no_company_screen.py`) **مختلف عن مساره الفعلي الحالي** حسب `system_arch.txt` (`ui/tabs/companies/no_company_screen.py`) — هذا تضارب في التوثيق الداخلي القديم للملف يستحق الانتباه.

---

## `ui/tabs/companies/companies_dialog.py`

### الغرض من الملف
نافذة حوار (Dialog) كاملة لإدارة الشركات: عرض قائمة الشركات في جدول، إضافة/تعديل/حذف/تفعيل-تعطيل شركة، مع فورم جانبي لإدخال بيانات الشركة (اسم، اسم مختصر، لون، ملاحظات).

### الـ imports الخارجية المهمة
- `ui.widgets.panels.themed_inputs` (`ThemedLineEdit`, `ThemedFrame`, `ThemedTextEdit`) — حقول إدخال مُنسّقة حسب الثيم.
- `services.companies.company_service.CompanyService` — طبقة الخدمة للتعامل مع بيانات الشركات (CRUD + toggle).
- `ui.theme._C` — قاموس ألوان الثيم الحالي.
- `ui.font` (`FS_SM`, `FS_BASE`, `FS_MD`, `FS_LG`, `FS_XL`) — أحجام الخطوط.
- `ui.widgets.core.i18n.tr` — الترجمة.
- `ui.widgets.core.widget_mixin.WidgetMixin` — دعم التحديث التلقائي للستايل/اللغة.
- `ui.widgets.dialogs.message` (`msg_question`, `msg_info`, `msg_warning`, `msg_critical`) — رسائل حوار موحّدة.
- `ui.constants` — عدد كبير من ثوابت القياسات الخاصة بالنافذة (مبيّنة بالاسم في الكود، مثل `COMPANIES_DLG_MIN_W`, `COMPANIES_DLG_ROW_H`, إلخ).

### من يستدعي هذا الملف
- `ui/tabs/companies/company_selector.py` — يفتحه عبر `_open_manager()` عند الضغط على زر إدارة الشركات.
- `ui/tabs/companies/no_company_screen.py` يُطلق signal `open_manager` يُفترض أن مستمعاً خارجياً (غير مرفق) يفتح هذه النافذة استجابة له.

### الـ Classes

#### `CompaniesDialog(QDialog, WidgetMixin)`
- **الوصف:** نافذة حوار مودال لإدارة الشركات بالكامل (Splitter بجدول + فورم).
- **Class-level attributes مهمة أثناء `__init__`:** `_conn` (اتصال central db)، `_svc = CompanyService(central_conn)`، `_editing_id` (معرف الشركة قيد التعديل أو `None`)، `_color` (اللون الحالي المختار، يبدأ بلون accent).
- **Methods:**
  - `__init__(self, central_conn, parent=None)`: يهيئ الاتصال والخدمة، يضبط عنوان النافذة والحد الأدنى للحجم، مودال، ثم `_build()`, `_refresh_style()`, `_load()`.
  - `_build(self)`: يبني `QVBoxLayout` رئيسي يحوي: عنوان، `QSplitter` أفقي يضم لوحة الجدول (`_build_table_panel`) ولوحة الفورم (`_build_form_panel`) بأحجام `COMPANIES_DLG_SPLITTER_L/R`، وصف أزرار سفلي بزر إغلاق (`accept`).
  - `_build_table_panel(self) -> QWidget`: يبني لوحة تحوي شريط أدوات (عنوان + زر إضافة `_add_btn` يستدعي `_new_company`)، وجدول `QTableWidget` بـ 4 أعمدة (اسم، اسم مختصر، حالة، إجراءات) بخصائص: تحديد صفوف كاملة، بدون تعديل مباشر، ألوان متبادلة، بدون رأس عمودي، بدون شبكة. عمود آخر بعرض ثابت `COMPANIES_DLG_TABLE_COL3_W`.
  - `_build_form_panel(self) -> QWidget`: يبني فورم يحوي: عنوان الفورم، فاصل (`ThemedFrame` أفقي)، حقل الاسم (`_inp_name`)، حقل الاسم المختصر (`_inp_short`)، صف اختيار لون (معاينة `_color_preview` + زر `_color_btn` يفتح `_pick_color`)، حقل ملاحظات (`_inp_notes` من نوع `ThemedTextEdit`)، وأزرار حفظ (`_save_btn` → `_save`) وإلغاء (`_cancel_btn` → `_reset_form`).
  - `_refresh_style(self, *_)`: يعيد ضبط كل الستايلات (عنوان، زر إغلاق، لوحة الجدول بألوانها وحدودها، لوحة الفورم، الحقول، معاينة اللون، الأزرار) بالاعتماد على `_C` المحدّث. في النهاية، إن كان الجدول يحوي صفوفاً بالفعل يستدعي `_load()` لإعادة رسم صفوف الجدول (لأن أزرار الصف تعتمد على الألوان).
  - `_refresh_lang(self, *_)`: يحدّث كل النصوص (عنوان النافذة، تسميات الأعمدة، تسميات الحقول، نص عنوان الفورم حسب كون `_editing_id` مُعرّفاً أو لا) ويعيد `_load()` إن وُجدت صفوف.
  - `_btn_style(self, bg, hover) -> str`: يُرجع نص QSS موحّد لزر ملوّن (خلفية + hover + حواف دائرية) يُستخدم لأزرار الحفظ والإضافة.
  - `_load(self)`: يجلب كل الشركات عبر `_svc.list_companies()` ويعيد بناء صفوف الجدول: عمود اسم كـ `QLabel` ملوّن بلون الشركة (badge)، عمود اسم مختصر، عمود حالة (نشط/متوقف) بلون مختلف حسب `is_active`، وعمود أزرار إجراءات (تعديل/تفعيل-تعطيل/حذف) كل زر مرتبط بـ lambda يستدعي `_edit_company`, `_toggle`, `_delete` بمعرف الصف.
  - `_new_company(self)`: يصفّر `_editing_id`، يمسح كل الحقول، يعيد `_color` للون accent الافتراضي، ويضع التركيز على حقل الاسم.
  - `_edit_company(self, company_id: int)`: يجلب بيانات الشركة عبر `_svc.get_company`، يملأ الحقول (اسم، اسم مختصر، ملاحظات، لون)، ويحدّث عنوان الفورم.
  - `_pick_color(self)`: يفتح `QColorDialog` ويحدّث `_color` ومعاينته عند اختيار لون صالح.
  - `_save(self)`: يقرأ قيم الحقول، يتحقق من وجود اسم (وإلا يعرض تحذيراً)، ثم إما `_svc.update_company` (لو `_editing_id` موجود) أو `_svc.add_company`، يعرض رسالة نجاح، يستدعي `_reset_form()` و`_load()`. يلتقط أي استثناء ويعرضه كرسالة خطأ حرجة.
  - `_reset_form(self)`: مطابق منطقياً لـ `_new_company` (يصفّر الفورم بالكامل).
  - `_toggle(self, company_id: int)`: يستدعي `_svc.toggle_active(company_id)` ثم `_load()`.
  - `_delete(self, company_id: int, name: str)`: يعرض تأكيد حذف (`msg_question`)، وعند التأكيد يستدعي `_svc.delete_company` مع التقاط الاستثناءات.

### ملاحظات من التعليقات
لا توجد تعليقات "إصلاح" داخل هذا الملف بخلاف تعليق عربي بسيط يوضح أن إعادة تلوين معاينة اللون وصفوف الجدول تحدث معاً بعد أي تغيير ثيم.

---

## `ui/tabs/companies/shared_items_dialog.py`

### الغرض من الملف
نافذة حوار (`SharedItemsDialog`) لتعديل عنصر مشترك واحد (Shared Item) بين الشركات — تعرض بيانات العنصر حسب نوعه (raw / machine / labor_op / machine_op)، وتدير ربط/فك ربط الشركات بهذا العنصر، وأي تعديل ينعكس فوراً على كل الشركات المرتبطة.

### الـ imports الخارجية المهمة
- `ui.widgets.panels.themed_inputs.ThemedLineEdit` — حقل اسم العنصر.
- `services.companies.shared_items_service.SharedItemsService` — خدمة العناصر المشتركة (جلب/تحديث/ربط/فك ربط).
- `services.companies.company_service.CompanyService` — لجلب قائمة الشركات لعرضها في قائمة الربط.
- `ui.widgets.core.events.emit_company_data_changed` — إشعار عام بتغيّر بيانات الشركات لتحديث بقية الواجهة.
- `ui.widgets.core.i18n.tr`, `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.font` (`FS_SM`, `FS_LG`).
- `ui.constants` — مجموعة كبيرة من ثوابت القياسات الخاصة بهذه النافذة (`SHARED_DLG_*`).

### من يستدعي هذا الملف
- `ui/tabs/companies/shared_items_manager.py` — يفتحه عبر `_open_edit_dialog(item_id)` عند تعديل عنصر (سواء بالنقر المزدوج أو زر تعديل).

### دالة مساعدة top-level

#### `_spin(max_=SHARED_DLG_SPIN_MAX_DEFAULT, dec=SHARED_DLG_SPIN_DEC_DEFAULT) -> QDoubleSpinBox`
تنشئ `QDoubleSpinBox` بمدى `[0, max_]`، عدد منازل عشرية `dec`، وارتفاع أدنى `SHARED_DLG_INPUT_MIN_H`. تُستخدم لتوحيد إنشاء حقول الأرقام.

### الـ Classes

#### `SharedItemsDialog(QDialog, WidgetMixin)`
- **الوصف:** نافذة مودال لتعديل عنصر مشترك واحد وإدارة ربطه بالشركات.
- **Signals:**
  - `item_updated = pyqtSignal()` — يُطلَق بعد نجاح الحفظ.
- **Attributes مهمة:** `_conn`, `_svc` (`SharedItemsService`), `_co_svc` (`CompanyService`), `_item_id`, `_item` (الكائن المُحمَّل أو `None`)، `_data` (`dict` بيانات العنصر)، `_field_widgets` (قاموس اسم-حقل ديناميكي حسب النوع)، `_type_row_labels` (قاموس تسميات صفوف الفورم الديناميكية لإعادة الترجمة).
- **Methods:**
  - `__init__(self, central_conn, shared_item_id: int, parent=None)`: يهيئ الخدمات، يضبط الحجم الأدنى، اتجاه RTL، يستدعي `_load_item()` ثم `_build()`, `_populate()`, `_refresh_style()`, `_refresh_lang()`.
  - `_load_item(self)`: يجلب العنصر عبر `_svc.get_item(self._item_id)` ويخزن `_data = self._item.data or {}`. لو العنصر غير موجود، `_item` تبقى `None`.
  - `_build(self)`: إن كان `_item is None` يبني فقط `QLabel` مخفي (`_lbl_missing`) ويتوقف. وإلا يبني: Header (نص Rich)، `data_grp` (`QGroupBox` بفورم يحوي حقل الاسم + حقول حسب النوع عبر `_build_type_fields`)، `companies_grp` (قائمة `QListWidget` للشركات + زرا ربط/فك ربط)، وأزرار حفظ/إغلاق عبر `QDialogButtonBox`.
  - `_refresh_style(self, *_)`: يضبط ستايل الـ header، الـ GroupBoxes (نمط مشترك `grp_style`)، قائمة الشركات، أزرار الربط/فك الربط (ألوان success/danger)، زر الحفظ، ثم يستدعي `_refresh_type_fields_style()` وإعادة تحميل قائمة الشركات إن وُجدت.
  - `_refresh_lang(self, *_)`: لو `_item is None` يضبط فقط نص `_lbl_missing` (`shared_item_not_found`) ويتوقف. وإلا يضبط عنوان النافذة، نص الـ header (اسم العنصر + نوعه بلون مختلف)، عناوين المجموعات، تسمية حقل الاسم، نصوص الأزرار، ثم `_refresh_type_fields_lang()` و`_load_companies_list()`.
  - `_build_type_fields(self, form_lay: QFormLayout)`: يبني حقول الإدخال الديناميكية حسب `self._item.shared_type`:
    - `raw`: حقل `price`، حقل `total_qty`، ومعاينة سعر الوحدة (`lbl_unit`) تتحدث تلقائياً عبر `valueChanged.connect(self._update_raw_preview)`.
    - `machine`: حقل `rate_per_hour`، حقل `rate_per_unit`.
    - `labor_op`: حقل `minutes` (بمدى/دقة مختلفين `SHARED_DLG_SPIN_MAX_MINUTES`/`_DEC_MINUTES`).
    - `machine_op`: حقل `value`، ولابل عرض فقط لاسم الماكينة (`lbl_machine`، غير قابل للتعديل هنا).
    يُسجَّل كل تسمية صف في `_type_row_labels` لإعادة ترجمتها لاحقاً.
  - `_refresh_type_fields_lang(self)`: يعيد ضبط نصوص `_type_row_labels` عبر `tr(key)`، مع حالة خاصة لـ `machine_op_value_lbl` (يعتمد على `data.get("mode")` لعرض إما "وقت" أو "كمية"). لنوع `raw` يضبط `setSpecialValueText` لحقل `total_qty` ويستدعي `_update_raw_preview()`. لنوع `machine_op` يضبط `lbl_machine` من `_data.get("machine_name", tr("dash"))`.
  - `_refresh_type_fields_style(self)`: يضبط ستايل `lbl_unit` (لنوع raw) و`lbl_machine` (لنوع machine_op) بالألوان من `_C`.
  - `_update_raw_preview(self)`: يحسب سعر الوحدة = `price/total_qty` إن كانت الكمية والسعر أكبر من صفر، ويعرضه؛ وإلا يعرض السعر فقط أو `dash`.
  - `_populate(self)`: دالة فارغة (`pass`) — تعليق يوضح أن منطقها انتقل إلى `_refresh_lang` (عبر `_load_companies_list` و`_refresh_type_fields_lang`) لتوافق تحديث اللغة الديناميكي.
  - `_load_companies_list(self)`: يمسح `lst_companies` ويعيد ملأها بكل الشركات، مع علامة مختلفة (أيقونة/لون) للشركات المرتبطة بالعنصر (`_svc.list_linked_companies`) مقابل غير المرتبطة، ويخزن `co.id` و`is_linked` في بيانات كل عنصر قائمة (`Qt.UserRole`, `Qt.UserRole + 1`).
  - `_link_company(self)`: يتحقق من وجود عنصر محدد، ولو كان مرتبطاً بالفعل يعرض تنبيهاً؛ وإلا يستدعي `_svc.link_to_company` ثم يعيد التحميل ويُطلق `emit_company_data_changed()`.
  - `_unlink_company(self)`: مشابه لكن يتحقق من كون العنصر غير مرتبط أصلاً (تنبيه)، ويطلب تأكيداً (`QMessageBox.question`) قبل استدعاء `_svc.unlink_from_company`.
  - `_save(self)`: يتحقق من وجود اسم، يبني `new_data` نسخة من `_data` ويحدّثها حسب نوع العنصر (كل الحقول المطابقة لـ `_build_type_fields`)، يستدعي `_svc.update_item(item_id, name, new_data)`، يُطلق `emit_company_data_changed()` و`item_updated.emit()`، يعرض رسالة نجاح، ويقبل (`accept()`) النافذة.
  - `_type_ar(self) -> str`: يُرجع الاسم المترجم لنوع العنصر (`shared_type_raw`/`machine`/`labor_op`/`machine_op`) أو `tr("name")` كافتراضي.

### الثوابت على مستوى الملف
لا يوجد ثوابت محلية معرّفة داخل الملف نفسه (كلها مستوردة من `ui.constants`).

---

## `ui/tabs/companies/shared_items_mixin.py`

### الغرض من الملف
مجموعة دوال مساعدة (لا يحتوي أي Class) للتعامل مع العناصر المشتركة على مستوى الجداول المحلية: تحديد إن كان معرّف عنصر هو "مشترك"، استخراج معرّفه الرقمي، تحديد العناصر المحلية التي نُشرت كمشتركة (لعرض علامة 🔗)، منع تكرار ظهور العنصر، وجلب/تحويل العناصر المشتركة من `companies.db` إلى صيغة صفوف موحدة لكل نوع (raw/machine/labor_op/machine_op).

### الـ imports الخارجية المهمة
جميع الاستيرادات هنا **lazy imports** (داخل الدوال) لتفادي circular imports:
- `services.companies.company_service.CompanyService` — لجلب معرف/اتصال الشركة النشطة.
- `services.companies.shared_items_service.SharedItemsService` — لجلب العناصر المشتركة.
- `services.shared.item_service.ItemService` — لاستخراج `category_name` من erp.db المحلي كـ fallback (`get_category_name_by_item_name`).

### من يستدعي هذا الملف
- جداول التكلفة في `ui/tabs/costing/`: `raw_table_panel.py`, `labor_op_table.py`, `machine_table.py` — تستورد `get_shared_raws`, `get_shared_labor_ops`, `get_shared_machines` وما يقابلها لعرض العناصر المشتركة إلى جانب المحلية (مؤكَّد من `ui_tabs_costing.md` الذي يذكر `to_dict`, `SHARED_COLOR`, `SHARED_BG`, `PUBLISHED_COLOR`, `PUBLISHED_BG`)
- أي جدول في `tabs/` يعرض قوائم مدمجة (محلي + مشترك) يستخدم هذا الملف

### الدوال المستقلة (top-level functions)

- **`is_shared_id(item_id) -> bool`**: يتحقق أن `item_id` نص يبدأ بـ `"shared:"`.
- **`extract_shared_id(item_id) -> int | None`**: يستخرج الجزء الرقمي بعد `":"` من معرف مشترك (`shared:123` → `123`)؛ يُرجع `None` عند الفشل أو لو لم يكن معرّف مشترك أصلاً.
- **`_get_company_id() -> int | None`**: يُرجع معرف الشركة الحالية عبر `CompanyService.get_current_company_id()` فقط لو `CompanyService.is_company_ready()` صحيح، وإلا `None`.
- **`_get_erp_conn()`**: يُرجع اتصال erp.db للشركة النشطة عبر `CompanyService.get_active_erp_conn()` (اتصال مشترك، **لا يُغلق** من هذه الدالة — ملاحظة موضحة في الكود).
- **`remove_local_duplicates(local_rows: list, shared_rows: list) -> list`**: يبني مجموعة أسماء العناصر المحلية (بأحرف صغيرة، بعد trim)، ويُرجع من `shared_rows` فقط العناصر التي لا تتطابق أسماؤها مع أي اسم محلي — لمنع ظهور العنصر مرتين في الشركة الأصلية.
- **`_resolve_category_name_from_local(item_name: str, shared_type: str) -> str | None`**: fallback لجلب `category_name` من erp.db المحلي عبر `ItemService.get_category_name_by_item_name`، يُرجع `None` عند أي استثناء أو عدم وجود اتصال.
- **`get_published_local_names(shared_type: str) -> set`**: يُرجع مجموعة أسماء (بأحرف صغيرة) للعناصر المحلية المنشورة كمشتركة من الشركة الحالية — تُستخدم لتعليم العناصر الأصلية بعلامة 🔗 في الجداول. **[إصلاح v2]**: يستخدم `try/finally` حول `central.close()` لضمان إغلاق الاتصال حتى عند حدوث استثناء أثناء `svc.list_for_company`. عند أي استثناء عام تُطبع رسالة خطأ ويُرجع مجموعة فارغة.
- **`_fetch_shared(shared_type: str) -> list`**: يجلب العناصر المشتركة للشركة النشطة من `companies.db` عبر `SharedItemsService.list_for_company`، ويبني لكل عنصر قاموساً موحداً يشمل: `id` (بصيغة `"shared:<id>"`), `shared_item_id`, `name`, `shared_type`, `category_id=None`, `category_name` (من `data` أولاً، وإلا من `_resolve_category_name_from_local` كـ fallback، وإلا `None`)، `is_shared=True`, `updated_at`، ثم يدمج بقية حقول `data` مع إعادة فرض `category_name` و`is_shared` بعد الدمج (لمنع أن يطغى `data` عليهما). **[إصلاح v2]**: نفس نمط `try/finally` حول إغلاق `central` لمنع تسريب الاتصال (connection leak) حتى لو رمى `execute()` استثناءً. عند الفشل العام تُطبع رسالة خطأ ويُرجع `[]`.
- **`get_shared_raws(local_rows: list = None) -> list`**: يستدعي `_fetch_shared("raw")` ويحوّل كل عنصر لصيغة صف خام (`price`, `total_qty`, إلخ)؛ لو مُرِّر `local_rows` يُطبَّق عليه `remove_local_duplicates`.
- **`get_shared_machines(local_rows: list = None) -> list`**: مثل السابقة لنوع `machine` (حقول `rate_per_hour`, `rate_per_unit`).
- **`get_shared_labor_ops(local_rows: list = None) -> list`**: لنوع `labor_op` (حقل `minutes`).
- **`get_shared_machine_ops(local_rows: list = None) -> list`**: لنوع `machine_op` (حقول `mode`, `value`, `machine_name`, `rate_per_hour`, `rate_per_unit`).

كل دوال `get_shared_*` تتبع نفس النمط: استدعاء `_fetch_shared`، إعادة تهيئة القاموس بحقول محددة للنوع + `is_shared=True` + `category_name`، ثم تطبيق `remove_local_duplicates` اختيارياً.

### ملاحظات من التعليقات
docstring أعلى الملف يلخص 3 إصلاحات رئيسية: (1) fallback لـ `category_name` من erp.db المحلي، (2) تمييز العنصر الأصلي بعلامة 🔗 في شركته المصدر عبر `get_published_local_names`، (3) منع التكرار عبر `remove_local_duplicates`. بالإضافة إلى ملاحظة **[إصلاح v2]** الموضحة أعلاه بخصوص `try/finally` لمنع تسريب الاتصالات في دالتين.

---

## `ui/tabs/companies/company_selector.py`

### الغرض من الملف
ودجت (Widget، ليس Dialog) يظهر في هيدر النافذة الرئيسية — Dropdown لاختيار الشركة النشطة حالياً، مع زر لفتح نافذة إدارة الشركات. يُطلق signal عند تغيير الاختيار.

### الـ imports الخارجية المهمة
- `ui.widgets.panels.themed_inputs.ThemedComboBox` — الـ combo box المُنسّق.
- `services.companies.company_service.CompanyService` — جلب/ضبط الشركة النشطة والاتصال المركزي.
- `ui.font` (`FS_BASE`, `FS_LG`).
- `ui.widgets.core.i18n.tr`, `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.constants` — ثوابت قياسات الودجت (`COMPANY_SELECTOR_*`).
- (داخل `_open_manager`, lazy import) `ui.tabs.companies.companies_dialog.CompaniesDialog` — لفتح نافذة إدارة الشركات.

### من يستدعي هذا الملف
- `ui/main_window_helper/_sidebar.py` — يستورده مباشرة ويبني `CompanySelector` في رأس الشريط الجانبي (مؤكَّد من `ui_main_window.md`: "_sidebar.py يستورد أيضاً `CompanySelector` من `..tabs.companies.company_selector`")

### الـ Classes

#### `CompanySelector(QWidget, WidgetMixin)`
- **الوصف:** شريط اختيار الشركة النشطة، يظهر عادة في الهيدر.
- **Signals:**
  - `company_changed = pyqtSignal(int)` — يُطلَق بمعرف الشركة الجديدة عند تغيير الاختيار.
- **Attributes:** `_central_conn` (اتصال مركزي يُهيَّأ عند الحاجة عبر `_get_central`)، `_companies` (قائمة قواميس `{id, name, color}` للشركات النشطة).
- **Methods:**
  - `__init__(self, parent=None)`: يهيئ `_central_conn=None`, `_companies=[]`, يستدعي `_init_widget_mixin(data=False)`, `_build()`, `_refresh_style()`, `_load()`.
  - `_build(self)`: يبني `QHBoxLayout` يحوي أيقونة (`_ico`) بعرض ثابت، `ThemedComboBox` (`_combo`) بعرض/ارتفاع محددين مربوط بـ `currentIndexChanged → _on_changed`، وزر إدارة (`_manage_btn`) مربوط بـ `_open_manager`.
  - `_refresh_style(self, *_)`: يضبط ستايل الأيقونة، الـ combo (بألوان sidebar وhover وقائمة منسدلة منسّقة)، وزر الإدارة.
  - `_refresh_lang(self, *_)`: يحدّث نص الأيقونة، نص/tooltip زر الإدارة.
  - `_get_central(self)`: يُرجع `_central_conn` بعد تهيئته (Lazy) عبر `CompanyService.get_central_conn_and_init()` إن لم يكن موجوداً.
  - `_load(self)`: يمسح الـ combo، يجلب الشركات النشطة فقط (`svc.list_companies(active_only=True)`) ضمن `try/except` (طباعة خطأ عند الفشل وتفريغ `_companies`). لو لا توجد شركات، يعرض نص `no_companies_available` ويعطّل الـ combo. وإلا يملأ الـ combo بأسماء الشركات (مع `userData=company_id`)، ويحاول استعادة اختيار الشركة النشطة الحالية (عبر `CompanyService.is_company_ready()` و`get_current_company_id()`)، أو يختار أول شركة تلقائياً لو لا توجد شركة نشطة مسبقاً. في النهاية يستدعي `_activate(idx)` للشركة المختارة الحالية إن وُجدت شركات.
  - `_on_changed(self, idx: int)`: يستدعي `_activate(idx)` لو المؤشر صالح.
  - `_activate(self, idx: int)`: يجلب بيانات الشركة المختارة، يضبطها كشركة نشطة عبر `CompanyService.set_active_company(cid, name, color)` (اللون الافتراضي هو `_C["accent"]` لو الشركة بدون لون)، ويُطلق `company_changed.emit(cid)`.
  - `_open_manager(self)`: يفتح `CompaniesDialog` (استيراد lazy) مودالياً، وبعد إغلاقها يعيد تحميل القائمة (`_load()`) ويحاول استعادة اختيار الشركة النشطة القديمة إن كانت لا تزال موجودة.
  - `refresh(self)`: واجهة عامة بسيطة تستدعي `_load()` لإعادة التحميل من الخارج.
  - `closeEvent(self, event)`: يغلق `_central_conn` بأمان (ضمن `try/except`) قبل استدعاء `super().closeEvent(event)`.

### ملاحظات من التعليقات
docstring يوضح دور الملف والـ signal الرئيسي `company_changed(company_id, name, color)` — **ملاحظة تضارب:** التوثيق أعلى الملف يذكر أن الـ signal يحمل 3 قيم (`company_id, name, color`)، لكن التعريف الفعلي في الكود هو `pyqtSignal(int)` بقيمة واحدة فقط (`company_id`). هذا تضارب بين التوثيق والتنفيذ الفعلي يستحق تنبيه المستخدم.

---

## `ui/tabs/companies/shared_items_manager.py`

### الغرض من الملف
نافذة حوار (`SharedItemsManagerDialog`) لإدارة **كل** العناصر المشتركة دفعة واحدة: عرضها مجمّعة حسب النوع في شجرة (`QTreeWidget`)، إضافة عنصر جديد، تعديل عنصر (يفتح `SharedItemsDialog`)، وحذف عنصر.

### الـ imports الخارجية المهمة
- `ui.widgets.panels.themed_inputs.ThemedFrame` — لبناء الهيدر الملوّن.
- `services.companies.shared_items_service.SharedItemsService` — الخدمة الأساسية (list/add/delete/list_linked_companies).
- `services.companies.company_service.CompanyService` — (مُستوردة لكن أساساً تُستخدم بشكل غير مباشر عبر نوافذ فرعية).
- `ui.widgets.core.events.emit_company_data_changed`.
- `ui.widgets.core.i18n.tr`, `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.font` (`FS_SM`, `FS_LG`).
- `ui.constants` — ثوابت قياسات كثيرة (`SHARED_MGR_*`, `MARGIN_ZERO`, `SPACING_ZERO`).
- (داخل الدوال، lazy) `ui.theme._C` — لتلوين الشجرة والهيدر.
- (داخل `_add_item`, lazy, مع fallback) `ui.tabs.companies.shared_items_manager_helper._add_shared_item_dialog.PublishAsSharedDialog`.
- (داخل `_open_edit_dialog`, lazy) `ui.tabs.companies.shared_items_dialog.SharedItemsDialog`.

### من يستدعي هذا الملف
- `ui/main_window.py` — يفتحه عبر `_open_shared_items()` عند الضغط على زر "🔗 العناصر المشتركة" في الشريط الجانبي (مؤكَّد من `ui_main_window.md`: "يستورد `SharedItemsManagerDialog`/`SharedItemsService` محلياً داخل `_open_shared_items`")

### الدوال المستقلة (top-level functions)

- **`_type_label(t: str) -> str`**: يُرجع نص مُترجَم مع أيقونة لنوع العنصر المشترك (raw/machine/labor_op/machine_op) عبر قاموس تعيين ثابت مبني من `tr(...)`؛ يُرجع `t` نفسه كـ fallback.
- **`_type_color(t: str) -> str`**: (lazy import لـ `_C` من `ui.theme` عند كل استدعاء) يُرجع لون مميز لكل نوع (`acc_type_asset` لـ raw، `purple` لـ machine، `success` لـ labor_op، `orange` لـ machine_op)؛ fallback `text_primary`.

### الـ Classes

#### `SharedItemsManagerDialog(QDialog, WidgetMixin)`
- **الوصف:** نافذة مودال لإدارة جميع العناصر المشتركة، معروضة كشجرة مجمّعة بالنوع.
- **Signals:**
  - `items_changed = pyqtSignal()` — يُطلَق بعد أي إضافة/تعديل/حذف ناجح.
- **Attributes:** `_conn`, `_svc = SharedItemsService(central_conn)`.
- **Methods:**
  - `__init__(self, central_conn, parent=None)`: يضبط الحجم الأدنى، مودال، RTL، يستدعي `_init_widget_mixin(theme=True, font=True, lang=True, data=False)` ثم `_build()`, `_refresh_style()`, `_refresh_lang()`.
  - `_build(self)`: يبني هيدر ملوّن (`_build_header`)، ثم جسم (`body`) يحوي: تلميح (`lbl_hint`)، صف أزرار (إضافة/تعديل/حذف/تحديث)، شجرة (`tree`) بـ 5 أعمدة (اسم، نوع، بيانات رئيسية، شركات، آخر تحديث) مع تحديد أوضاع تحجيم الأعمدة، وزر إغلاق سفلي.
  - `_build_header(self) -> ThemedFrame`: يبني إطاراً ملوناً بارتفاع ثابت يحوي تسمية `lbl_header`.
  - `_refresh_style(self, *_)`: يضبط خلفية الجسم، ستايل التلميح (لون success)، أزرار الإضافة (accent) والحذف (danger)، ستايل الشجرة، وستايل الهيدر (خلفية accent). يستدعي `_load()` في النهاية إن كانت الشجرة موجودة.
  - `_refresh_lang(self, *_)`: يحدّث عنوان النافذة، نص الهيدر والتلميح، نصوص كل الأزرار، عناوين أعمدة الشجرة، ويستدعي `_load()`.
  - `_load(self)`: يمسح الشجرة، يجلب كل العناصر عبر `_svc.list_items()`، يجمّعها في `by_type` (قاموس نوع → قائمة عناصر)، ولكل نوع (بترتيب مفروز) يبني عقدة أب (`type_node`) بخط عريض وأكبر ولون مميز (`_type_color`) وخلفية، تحمل بيانات `("__type__", shared_type)` في `Qt.UserRole`. لكل عنصر ضمن النوع، يجلب الشركات المرتبطة (`list_linked_companies`)، يبني ملخص بيانات (`_data_summary`)، ويضيف عقدة ابن (`child`) بالأعمدة الخمسة، تحمل `("item", item.id)` في `Qt.UserRole`، مع tooltips للاسم وأسماء الشركات. يوسّع كل عقدة نوع تلقائياً (`setExpanded(True)`).
  - `_data_summary(self, shared_type: str, data: dict) -> str`: يبني ملخصاً نصياً قصيراً حسب النوع: `raw` → السعر (+الكمية الإجمالية إن وُجدت)، `machine` → المعدل بالساعة/بالوحدة، `labor_op` → عدد الدقائق، `machine_op` → القيمة حسب الوضع (وقت/وحدة). يُرجع `tr("dash")` لأي نوع غير معروف.
  - `_selected_item_id(self) -> int | None`: يُرجع معرف العنصر المحدد حالياً في الشجرة لو كانت بياناته من نوع `"item"`، وإلا `None`.
  - `_on_double_click(self, item, col)`: يفتح نافذة التعديل (`_open_edit_dialog`) لو العنصر المنقور من نوع `"item"`.
  - `_add_item(self)`: يحاول استيراد `PublishAsSharedDialog` من `shared_items_manager_helper._add_shared_item_dialog`؛ عند فشل الاستيراد (`ImportError`) يستخدم fallback بسيط (`_add_item_simple`). عند النجاح يفتح `PublishAsSharedDialog` بنوع افتراضي `"raw"` واسم/بيانات فارغة، وعند القبول يعيد التحميل ويُطلق `items_changed` و`emit_company_data_changed()`.
  - `_add_item_simple(self)`: fallback يستخدم `QInputDialog` لاختيار النوع (من قائمة تسميات مترجمة) ثم إدخال الاسم، يضيف العنصر مباشرة عبر `_svc.add_item(name, shared_type)` بدون بيانات إضافية، يعيد التحميل، ويفتح نافذة التعديل لملء التفاصيل (`_open_edit_dialog(new_id)`).
  - `_edit_item(self)`: يتحقق من وجود عنصر محدد (وإلا تنبيه)، ثم يفتح `_open_edit_dialog`.
  - `_open_edit_dialog(self, item_id: int)`: يفتح `SharedItemsDialog(self._conn, item_id, parent=self)`، يربط `item_updated` بكل من `_load` و`items_changed.emit`، وينفذها مودالياً.
  - `_delete_item(self)`: يتحقق من وجود عنصر محدد. لو له شركات مرتبطة (`list_linked_companies`)، يعرض تأكيد حذف خاص يذكر عدد الشركات وأسماءها؛ وإلا تأكيد حذف بسيط. عند التأكيد يستدعي `_svc.delete_item(item_id)`، يعيد التحميل، يُطلق `items_changed` و`emit_company_data_changed()`، ويعرض رسالة نجاح.

### ملاحظات من التعليقات
docstring يوضح الوظائف الأربع الرئيسية للنافذة (عرض مجمّع، إضافة، تعديل، حذف، إدارة ربط عبر `SharedItemsDialog`)، ومثال استخدام موصى به (`items_changed.connect(...)` ثم `central.close()` بعد `exec_()`).

---

## `ui/tabs/companies/_link_item_picker.py`

### الغرض من الملف
نافذة حوار بسيطة (`LinkItemPicker`) لاختيار عنصر مشترك واحد من قائمة، بهدف ربطه (مثلاً بجدول محلي)، وتُرجع `selected_id` عند القبول.

### الـ imports الخارجية المهمة
- `ui.widgets.core.i18n.tr`, `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.constants` — ثوابت قياسات (`LINK_PICKER_*`).

### من يستدعي هذا الملف
غير محدد من المرفقات الحالية.

### دالة مساعدة top-level

#### `_type_ar_map() -> dict`
تُرجع قاموس تعيين نوع العنصر → تسمية مترجمة (`raw`, `machine`, `labor_op`, `machine_op`)، مبني من استدعاءات `tr(...)` عند كل نداء للدالة (وليس ثابتاً مُخزَّناً، لضمان تحديثه عند تغيير اللغة).

### الـ Classes

#### `LinkItemPicker(QDialog, WidgetMixin)`
- **الوصف:** Dialog اختيار عنصر مشترك واحد من قائمة معطاة، مع دعم تحديث اللغة الديناميكي للعناصر المعروضة.
- **Attributes:** `selected_id` (يبدأ `None`، يُملأ عند القبول)، `_items` (القائمة الممرَّرة في `__init__`).
- **Methods:**
  - `__init__(self, items: list, parent=None)`: يخزن `_items`، يضبط عنوان النافذة والحجم الأدنى ومودال، يستدعي `_init_widget_mixin(data=False)`, `_build()`, `_refresh_style()`.
  - `_build(self)`: يبني تخطيطاً عمودياً: تسمية توجيه (`_prompt_lbl`)، `QListWidget` (`_list`) مربوط بـ `itemDoubleClicked → _accept`، تُملأ من `_items` (كل عنصر: `name`, `shared_type`, `source_company_name`, `id`) بنص مُنسَّق يجمع الاسم + النوع المترجم + مصدر الشركة عبر `tr('link_item_from').format(company=source)`، مع تخزين `item['id']` في `Qt.UserRole`. وصف أزرار: زر ربط (`_ok_btn → _accept`) وزر إلغاء (`_cancel_btn → reject`).
  - `_refresh_style(self, *_)`: يضبط ستايل القائمة (حدود، حواف، تحديد، hover) وزري الربط/الإلغاء.
  - `_refresh_lang(self, *_)`: يحدّث عنوان النافذة، نص التوجيه، نصوص الأزرار، ويعيد بناء نص كل عنصر في القائمة (بنفس منطق `_build`) عبر حلقة تربط `self._items[i]` بـ `self._list.item(i)`.
  - `_accept(self)`: لو يوجد عنصر محدد في القائمة، يضبط `self.selected_id` من بياناته (`Qt.UserRole`) ثم `self.accept()`.

### ملاحظات من التعليقات
لا توجد ملاحظات خاصة (docstring بسيط يوضح الغرض العام فقط).

---

## `ui/tabs/companies/shared_items_manager_helper/_add_shared_item_dialog.py`

### الغرض من الملف
نافذة حوار (`PublishAsSharedDialog`) لنشر عنصر (خام محلي، ماكينة، عملية عمالة، عملية ماكينة) كعنصر مشترك جديد بين الشركات، مع اختيار الشركات التي سيُربط بها فوراً عند النشر، ودعم حالة "العنصر موجود بالفعل" بربط الشركات المختارة بالعنصر الموجود بدلاً من إنشاء تكرار.

### الـ imports الخارجية المهمة
- `ui.widgets.panels.themed_inputs.ThemedLineEdit`.
- `services.companies.shared_items_service.SharedItemsService`.
- `services.companies.company_service.CompanyService` — لجلب كل الشركات ومعرف الشركة الحالية (المصدر).
- `ui.widgets.core.events.emit_company_data_changed`.
- `ui.widgets.core.i18n.tr`, `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.font.FS_SM`.
- `ui.constants` — ثوابت قياسات كثيرة (`PUBLISH_DLG_*`).

### من يستدعي هذا الملف
- `ui/tabs/companies/shared_items_manager.py` — يستورده (lazy، مع fallback عند `ImportError`) داخل `_add_item()` لفتح نافذة إضافة عنصر مشترك جديد.

### دالة مساعدة top-level

#### `_spin(max_=PUBLISH_DLG_SPIN_MAX_DEFAULT, dec=PUBLISH_DLG_SPIN_DEC_DEFAULT) -> QDoubleSpinBox`
مطابقة لدالة `_spin` في `shared_items_dialog.py` من حيث المنطق (مدى، دقة، ارتفاع أدنى)، لكنها معرّفة بشكل مستقل هنا بثوابت `PUBLISH_DLG_*` الخاصة بهذا الملف (لا استيراد مشترك بين الملفين).

### الـ Classes

#### `PublishAsSharedDialog(QDialog, WidgetMixin)`
- **الوصف:** نافذة مودال لنشر عنصر (من نوع محدد مسبقاً) كعنصر مشترك، مع اختيار الشركات المُشارَكة معها.
- **Attributes:** `_conn`, `_svc = SharedItemsService(central_conn)`, `_shared_type` (نوع العنصر، يُمرَّر عند الإنشاء ولا يتغيّر)، `_item_name` (اسم مبدئي)، `_item_data` (بيانات مبدئية، مثل بيانات عنصر محلي قبل النشر).
- **Methods:**
  - `__init__(self, central_conn, shared_type: str, item_name: str, item_data: dict, parent=None)`: يخزن كل الوسائط، يضبط عنوان النافذة، الحجم الأدنى، مودال، RTL، يستدعي `_init_widget_mixin(data=False)`, `_build()`, `_refresh_style()`.
  - `_build(self)`: يبني: تلميح (`_lbl_hint`)، مجموعة بيانات العنصر (`_data_grp`) بفورم يحوي حقل الاسم (`inp_name`) وحقول حسب النوع (`_build_type_fields`)، مجموعة اختيار الشركات (`_cos_grp`) تحوي `QListWidget` (`lst_companies`) بعناصر قابلة للتحديد (checkboxes) لكل الشركات (مُعلَّمة تلقائياً الشركة الحالية `current_co_id`)، مع صف أزرار اختيار سريع (تحديد الكل/إلغاء الكل عبر `_check_all`)، وأزرار حوار (`QDialogButtonBox`) نشر (`_btn_ok → _publish`) وإلغاء (`_btn_cancel → reject`).
  - `_refresh_style(self, *_)`: يضبط ستايل التلميح، الـ GroupBoxes (نمط مشترك)، قائمة الشركات، وزر النشر.
  - `_build_type_fields(self, form_lay: QFormLayout)`: يبني حقول الإدخال حسب `self._shared_type` (نفس الأنواع الأربعة: raw بحقلي `price`/`total_qty` مع `setSpecialValueText`، machine بحقلي `rate_per_hour`/`rate_per_unit`، labor_op بحقل `minutes`، machine_op بحقل `value`)، بقيم مبدئية مأخوذة من `self._item_data`. **ملاحظة:** هنا يتم استخدام `tr(...)` مباشرة كنص تسمية الصف عند `addRow` (بخلاف `shared_items_dialog.py` الذي يخزّن الـ label في قاموس لإعادة الترجمة لاحقاً) — أي أن هذه النافذة **لا تُحدّث تسميات حقول النوع تلقائياً** عند تغيير اللغة أثناء فتحها (غياب دالة مكافئة لـ `_refresh_type_fields_lang`).
  - `_check_all(self, checked: bool)`: يضبط `checkState` لكل عناصر `lst_companies` دفعة واحدة (`Qt.Checked` أو `Qt.Unchecked`).
  - `_publish(self)`: يتحقق من وجود اسم (وإلا تحذير). يجلب `current_co_id` (الشركة المصدر). يبني `data` حسب النوع (نفس حقول `_build_type_fields`؛ لنوع `machine_op` يضيف أيضاً `mode`, `machine_name`, `rate_per_hour`, `rate_per_unit` من `_item_data` الأصلية كمرجع). **يضيف** `data["source_company_id"] = current_co_id` (لو موجود) و`data["category_name"]` (لو موجود في `_item_data`) — هذا هو الإصلاح الموضح في docstring الملف. يتحقق من وجود عنصر بنفس الاسم (case-insensitive) ضمن `_svc.list_items(t)`:
    - لو موجود: يسأل المستخدم إن أراد الربط بدلاً من الإنشاء؛ عند الموافقة يربط الشركات المختارة بالعنصر الموجود (`_link_companies`) دون إنشاء عنصر جديد، ويقبل النافذة.
    - لو غير موجود: ينشئ عنصراً جديداً عبر `_svc.add_item(name, t, data)`، يربط الشركات المختارة، يُطلق `emit_company_data_changed()`، يعرض رسالة نجاح النشر، ويقبل النافذة.
  - `_link_companies(self, shared_id: int)`: يمر على كل عناصر `lst_companies`، ولكل عنصر محدد (`Qt.Checked`) يستدعي `_svc.link_to_company(shared_id, co_id)`.

### ملاحظات من التعليقات
docstring أعلى الملف يوثّق صراحة إصلاحاً مقصوداً: حفظ `source_company_id` و`category_name` داخل `data` عند النشر، لغرضين: (1) معرفة الشركة المصدر لتجنّب إظهار العنصر مرتين في شركته الأصلية (بالتكامل مع `remove_local_duplicates` في `shared_items_mixin.py`)، (2) عرض التصنيف الحقيقي للعنصر بدل نص عام مثل "مشترك".

---

## قسم علاقات الملفات

- **`company_selector.py`** يستورد (lazy) **`companies_dialog.py`** (`CompaniesDialog`) لفتح نافذة إدارة الشركات من زر الإدارة.
- **`shared_items_manager.py`** يستورد (lazy):
  - **`shared_items_manager_helper/_add_shared_item_dialog.py`** (`PublishAsSharedDialog`) لإضافة عنصر مشترك جديد، مع fallback داخلي (`_add_item_simple`) لو الاستيراد فشل.
  - **`shared_items_dialog.py`** (`SharedItemsDialog`) لتعديل عنصر موجود.
- **`shared_items_dialog.py`** و **`shared_items_manager_helper/_add_shared_item_dialog.py`** يتشاركان بنية شبه مطابقة لحقول الإدخال حسب النوع (`_build_type_fields` بنفس الأنواع الأربعة: raw/machine/labor_op/machine_op) ودالة `_spin` مساعدة، لكنهما **لا يستوردان بعضهما البعض** — كل ملف يعرّف نسخته المستقلة من `_spin` وحقول النوع (تكرار منطقي متعمد أو غير مقصود، غير موثّق في الكود).
- **نمط بناء مشترك** عبر كل الملفات في هذا المسار: كل الـ Dialogs/Widgets ترث من `(Qt-Class, WidgetMixin)` وتتبع نفس تسلسل الاستدعاء في `__init__`: `_init_widget_mixin(...)` ثم `_build()` ثم `_refresh_style()` ثم (غالباً) `_refresh_lang()`/`_load()`. كل ملف يفصل الستايل (`_refresh_style`) عن النصوص (`_refresh_lang`) في دالتين منفصلتين لدعم تبديل الثيم/اللغة ديناميكياً دون إعادة بناء الودجت.
- **تبعية مشتركة خارج هذا المسار** يعتمد عليها كل الملفات تقريباً: `services/companies/company_service.py` (`CompanyService`) و`services/companies/shared_items_service.py` (`SharedItemsService`) — تفصيل محتواهما من مسؤولية مرجع `services_companies.md` الخاص بهما (غير مغطى هنا).
- **`shared_items_mixin.py`** لا يستورد أي ملف آخر من هذا المسار، ولا يُستورَد بشكل صريح من أي ملف آخر ضمن هذه الدفعة (اعتماده يبدو من جهة ملفات الجداول/التابات الأخرى غير المرفقة في `ui/tabs/costing` مثلاً، حسب التسمية والدوال المُصدَّرة مثل `get_shared_raws`).
- **`_link_item_picker.py`** لا يستورد ولا يُستورَد من أي ملف آخر ضمن هذه الدفعة — يبدو مصمماً للاستخدام من مكان خارجي غير مرفق (ربما جدول محلي يريد ربط عنصر مشترك).
