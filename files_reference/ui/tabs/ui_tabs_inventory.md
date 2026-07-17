# ui_tabs_inventory — ملف مرجعي

يغطي: `ui/tabs/inventory_section.py` + مجلد `ui/tabs/inventory/` وكل ملفاته الفرعية.

---

## `ui/tabs/inventory_section.py`

**الغرض:** القسم الرئيسي لتبويب المخزن — يجمع 5 تابات فرعية (الأصناف، الوارد، الصادر، التقرير، الحركات) داخل `QTabWidget` واحد مع هيدر موحّد.

**Imports داخلية مهمة:**
- `ui.widgets.theme.layout_styles` (`tab_style`, `apply_tab_widths`, `normalize_tab_widget`).
- `ui.widgets.core.widget_mixin.WidgetMixin`.
- `.inventory.items._items_tab._ItemsTab`.
- `.inventory.inventory_inbound_tab._InboundTab`.
- `.inventory.inventory_outbound_tab._OutboundTab`.
- `.inventory.inventory_report_tab` (`_ReportTab`, `_MovesPanel`).

**من يستدعيه:** `ui/main_window.py` — يبنيه كقسم تنقل رئيسي (مؤكَّد من بنية `main_window_helper/_sidebar.py`).

### Class: `InventoryTab(QWidget, WidgetMixin)`
- **Attributes:** `self.inv_conn` (اتصال مخزن نشط عبر `CompanyService.get_active_inventory_conn()`), `self.acc_conn` (اتصال محاسبة عبر `CompanyService.get_active_accounting_conn()`), `self._moves_panel`, `self._tabs`, `self._header`.
- **`__init__(self, parent=None)`**: يفتح الاتصالين، يبني الواجهة، يفعّل WidgetMixin بـ `theme=True, font=False, lang=True, data=False`.
- **`_build(self)`**: يبني هيدر (`QLabel` بارتفاع `SECTION_HEADER_HEIGHT`)، ينشئ `_MovesPanel` أولاً (`self._moves_panel`) لأنه سيُستخدم كـ callback هدف من تاب الأصناف، ثم `QTabWidget` مطبَّع بـ 5 تابات: `_ItemsTab` (يمرر `on_select=self._on_item_selected`)، `_InboundTab`، `_OutboundTab`، `_ReportTab`، `self._moves_panel` نفسه كتاب خامس.
- **`_on_item_selected(self, inv_id)`**: إن وُجد `inv_id` و`self._moves_panel`، يستدعي `self._moves_panel.load(inv_id)` — يربط اختيار صنف من تاب الأصناف بعرض حركاته في تاب الحركات.
- **`_refresh_style(self, *_)`**: يحدّث ستايل الهيدر (لون accent) وستايل التابات.
- **`_refresh_lang(self, *_)`**: يحدّث نص الهيدر وكل عناوين التابات الخمسة، يعيد حساب عرض التابات (لازم لأن طول النص العربي/الإنجليزي مختلف).
- **`closeEvent(self, event)`**: يغلق `self.inv_conn` و`self.acc_conn`.

---

## `ui/tabs/inventory/items/_item_form.py`

**الغرض:** فورم إضافة/تعديل صنف مخزن — بيانات أساسية (اسم، وحدة، حد أدنى، ربط بصنف تكلفة اختياري، ربط بحساب محاسبي، ملاحظات) مع وضعي إضافة/تعديل.

**Imports داخلية:** `services.inventory.inventory_service.InventoryService`, `ui.widgets.mixins.form_mixins.EditModeMixin`, `ui.widgets.core.events.emit_company_data_changed`, `ui.widgets.core.i18n.tr`, `ui.widgets.core.widget_mixin.WidgetMixin`.

**من يستدعيه:** `ui/tabs/inventory/items/_items_tab.py` (يبنيه ويمرره لـ `_ItemsTable`)، `ui/tabs/inventory/items/_items_table.py` (`_edit` يستدعي `self._form.load_for_edit`).

### دالة module-level: `_spin(max_=INVENTORY_SPIN_MAX, dec=INVENTORY_SPIN_DEC) -> QDoubleSpinBox` — ينشئ QDoubleSpinBox موحّد.

### Class: `_ItemForm(QWidget, EditModeMixin, WidgetMixin)`
- **`__init__(self, inv_conn, acc_conn, parent=None)`**: ينشئ `InventoryService(inv_conn, acc_conn=acc_conn)`، يبني الواجهة، يهيئ `EditModeMixin` عبر `init_edit_mode(btn_add, btn_save, btn_cancel, lbl_mode)`.
- **`_refresh_style(self, *_)`**: ستايل `QGroupBox` (لون accent) وتسمية الوضع.
- **`_refresh_lang(self, *_)`**: يحدّث كل النصوص المترجمة (عنوان المجموعة، وضع الإضافة، placeholders، tooltips، الأزرار).
- **`_build(self)`**: `QFormLayout` بحقول: تسمية الوضع، اسم الصنف، الوحدة (افتراضي "قطعة")، الحد الأدنى للكمية، كومبو ربط بصنف خام (`cmb_item`، اختياري)، كومبو ربط بحساب أصول (`cmb_account`)، ملاحظات، وصف الأزرار (إضافة/حفظ/إلغاء) عبر `_make_btn_widget`.
- **`_make_btn_widget(self)`**: يبني `QWidget` بلايوت أفقي يحتوي الأزرار الثلاثة + stretch.
- **`_collect(self) -> dict | None`**: يتحقق من وجود اسم (وإلا يعرض تحذير ويرجع `None`)، يرجع dict بكل بيانات الفورم.
- **`_add(self)`**: يجمع البيانات، يستدعي `self._svc.add_item_by_account_id(**data)`، يعيد الضبط، يصدر `emit_company_data_changed()`.
- **`_save_edit(self)`**: يجمع البيانات، يستدعي `self._svc.update_item_by_account_id` بمعرف التعديل الحالي، يعيد الضبط، يصدر الحدث.
- **`_cancel(self)`**: يستدعي `_reset()`.
- **`load_for_edit(self, inv_id: int)`**: يجلب الصنف، يملأ كل الحقول، يدخل وضع التعديل عبر `enter_edit_mode(inv_id, ...)`.
- **`_reset(self)`**: يعيد كل الحقول لوضعها الافتراضي، يخرج من وضع التعديل عبر `exit_edit_mode(...)`.

---

## `ui/tabs/inventory/items/_items_table.py`

**الغرض:** جدول أصناف المخزن — عرض، تعديل (يستدعي فورم خارجي)، وحذف.

**Imports داخلية:** `services.inventory.inventory_service.InventoryService`, `ui.widgets.tables.tables.auto_fit_columns`/`make_table`/`refresh_table_styles`, `ui.widgets.panels.form_labels.section_title`, `ui.widgets.components.button` (`make_btn`, `refresh_visible_buttons`), `ui.widgets.dialogs.confirm.confirm_delete`, `ui.widgets.core.widget_mixin.WidgetMixin`, `ui.widgets.core.events.emit_company_data_changed`, `ui.widgets.core.i18n.tr`.

**من يستدعيه:** `ui/tabs/inventory/items/_items_tab.py` (يبنيه ويمرر له `form` و`on_select`).

### دالة module-level: `buttons_row(*buttons) -> QHBoxLayout` — صف أزرار أفقي بتباعد `SPACING_SM` + stretch نهائي.

### Class: `_ItemsTable(QWidget, WidgetMixin)`
- **`__init__(self, inv_conn, form, on_select, parent=None)`**: يحفظ `self._form` (مرجع فورم خارجي للتعديل)، `self._on_select` (callback عند تغيير التحديد)، ينشئ `InventoryService`، يفعّل WidgetMixin بـ `theme=True, font=False, lang=True, data=True`.
- **`_on_data_changed(self, *_)`** و **`_refresh_data(self, company_id=None)`**: كلاهما يستدعي `self._load()`.
- **`_refresh_style(self, *_)`**: يطبق `table_style()` مباشرة على الجدول (ملاحظة: [إصلاح ثيم] كانت `theme=False` سابقاً فالجدول الفارغ كان يفضل بخلفية بيضاء بعد التحويل لـ dark)، ويستدعي `refresh_visible_buttons(self)` لتحديث زر الحذف المبني بـ `make_btn`.
- **`_refresh_lang(self, *_)`**: فارغة (الأعمدة تُبنى مرة واحدة فقط في `_build`).
- **`_build(self)`**: عنوان القسم، جدول بأعمدة (معرف، صنف، وحدة، رصيد، حد أدنى، متوسط تكلفة، القيمة الإجمالية)، يربط `itemSelectionChanged`→`self._on_select(self._selected_id())`، زري تعديل/حذف تحت الجدول.
- **`_selected_id(self)`**: يرجع `id` الصف المحدد حالياً كـ int، أو `None`.
- **`_load(self)`**: يجلب كل الأصناف، يفرّغ الجدول ويعيد ملأه (id، اسم مع tooltip، وحدة، رصيد ملوّن أحمر إن كان ≤ الحد الأدنى مع tooltip تحذيري، حد أدنى، متوسط تكلفة، القيمة الإجمالية)، يستدعي `auto_fit_columns`.
- **`_edit(self)`**: يتحقق من وجود صنف محدد، يستدعي `self._form.load_for_edit(inv_id)`.
- **`_delete(self)`**: يتحقق من التحديد، يؤكد عبر `confirm_delete`، يستدعي `self._svc.delete_item` ويصدر الحدث.

---

## `ui/tabs/inventory/items/_items_tab.py`

**الغرض:** تبويب الأصناف — يجمع فورم الصنف وجدول الأصناف في `QSplitter` أفقي.

**Imports داخلية:** `._item_form._ItemForm`, `._items_table._ItemsTable`.

**من يستدعيه:** `ui/tabs/inventory_section.py` (`InventoryTab._build`).

### Class: `_ItemsTab(QWidget)`
- **`__init__(self, inv_conn, acc_conn, on_select, parent=None)`**: ينشئ `QSplitter(Qt.Horizontal)`، ينشئ `_ItemForm(inv_conn, acc_conn)` و`_ItemsTable(inv_conn, form, on_select)`، يضيفهما للـ splitter بأحجام (`INVENTORY_ITEMS_SPLITTER_FORM_SIZE`, `INVENTORY_ITEMS_SPLITTER_TABLE_SIZE`)، يجعل الفورم قابل للطي (`setCollapsible(0, True)`).

---

## `ui/tabs/inventory/inventory_inbound_tab.py`

**الغرض:** تبويب حركة الوارد (شراء/استلام مخزن) — فورم استلام صنف مع قيد محاسبي تلقائي، وجدول آخر حركات الوارد.

**Imports داخلية:** `services.accounting.inventory_posting_service.InventoryPostingService`, `services.inventory.inventory_service.InventoryService`, `ui.widgets.tables.tables` (`auto_fit_columns`, `make_table`), `ui.widgets.panels.form_labels.section_title`, `ui.widgets.core.widget_mixin.WidgetMixin`, `ui.widgets.core.events.emit_company_data_changed`, `ui.widgets.core.i18n.tr`.

**من يستدعيه:** `ui/tabs/inventory_section.py` (`InventoryTab._build`).

### دوال module-level:
- **`_spin(max_=INVENTORY_SPIN_MAX, dec=INVENTORY_SPIN_DEC) -> QDoubleSpinBox`**: spinbox موحّد.
- **`_safe_subtype(acc_row) -> str`**: يرجع `subtype` بأمان من `sqlite3.Row` أو dict (يتعامل مع `IndexError`/`KeyError`)، أو نص فارغ إن لم يوجد.

### Class: `_InboundTab(QWidget, WidgetMixin)`
- **`__init__(self, inv_conn, acc_conn, parent=None)`**: ينشئ `InventoryService(inv_conn, acc_conn=acc_conn)` و`InventoryPostingService(inv_conn, acc_conn)`، يفعّل WidgetMixin بـ `data=True`.
- **`_refresh_data(self, company_id=None)`**: يستدعي `_reload_items()` و`_load_moves()`.
- **`_refresh_style(self, *_)`**: ستايل المجموعة (لون success)، تسمية الإجمالي، زر الحفظ، ويستدعي `refresh_table_styles(self)` للجدول (نفس نمط الإصلاح في ملفات أخرى — الجدول مبني بستايل ثابت وقت الإنشاء).
- **`_build(self)`**: `QFormLayout` بحقول: كومبو الصنف (`cmb_item`، مرتبط بـ `currentIndexChanged`→`_on_item_changed`)، كمية، تكلفة الوحدة، تسمية الإجمالي (محسوبة)، تاريخ، كومبو حساب الدفع (`cmb_payment` — يُملأ من حسابات الخصوم ثم حسابات الأصول ذات subtype "cash"/"bank"، مع اختيار افتراضي لأول حساب يحتوي "211" أو كلمة "المورد")، ملاحظات، زر حفظ. تحته: عنوان "آخر حركات الوارد" وجدول (تاريخ، صنف، كمية، سعر وحدة، إجمالي، رقم قيد).
- **`_reload_items(self)`**: يعيد ملء كومبو الأصناف مع الحفاظ على التحديد السابق إن أمكن.
- **`_on_item_changed(self)`**: عند اختيار صنف له `avg_cost > 0`، يضبط تكلفة الوحدة تلقائياً على متوسط التكلفة، ثم يستدعي `_update_total`.
- **`_update_total(self)`**: يحسب `qty * unit_cost` ويحدّث تسمية الإجمالي.
- **`_save(self)`**: يتحقق من اختيار صنف وحساب دفع وقيمة كمية/تكلفة صحيحة، يستدعي `self._posting_svc.purchase(...)` (يُنشئ حركة مخزون + قيد محاسبي)، يمسح الملاحظات، يصدر الحدث، يعرض رسالة نجاح أو خطأ.
- **`_load_moves(self)`**: يجلب آخر 100 حركة وارد بالأسماء، يملأ الجدول (تاريخ، اسم مع tooltip، كمية، تكلفة وحدة، إجمالي، رقم قيد مرجعي أو شرطة)، يستدعي `auto_fit_columns`.

---

## `ui/tabs/inventory/inventory_outbound_tab.py`

**الغرض:** تبويب حركة الصادر (صرف/استهلاك مخزن) — فورم صرف صنف وجدول آخر حركات الصادر.

**Imports داخلية:** `services.inventory.inventory_service.InventoryService`, `ui.widgets.tables.tables` (`auto_fit_columns`, `make_table`), `ui.widgets.panels.form_labels.section_title`, `ui.widgets.core.widget_mixin.WidgetMixin`, `ui.widgets.core.events.emit_company_data_changed`, `ui.widgets.core.i18n.tr`.

**من يستدعيه:** `ui/tabs/inventory_section.py` (`InventoryTab._build`).

### دالة module-level: `_spin(max_=INVENTORY_SPIN_MAX, dec=INVENTORY_SPIN_DEC) -> QDoubleSpinBox`.

### Class: `_OutboundTab(QWidget, WidgetMixin)`
- **`__init__(self, inv_conn, parent=None)`**: ينشئ `InventoryService(inv_conn)`، يفعّل WidgetMixin بـ `data=True`. (لا يوجد اتصال محاسبة هنا — الصرف لا يُنشئ قيداً محاسبياً تلقائياً مثل الوارد).
- **`_refresh_data(self, company_id=None)`**: `_reload_items()` + `_load_moves()`.
- **`_refresh_style(self, *_)`**: ستايل المجموعة (لون orange)، تسمية الرصيد المتاح، زر الحفظ، `refresh_table_styles(self)` للجدول.
- **`_build(self)`**: `QFormLayout` بحقول: كومبو الصنف، كمية، تسمية الرصيد الحالي (`lbl_available`)، تاريخ، ملاحظات (الغرض من الصرف)، زر حفظ. تحته: جدول آخر حركات الصادر (تاريخ، صنف، كمية، متوسط تكلفة، القيمة، بيان).
- **`_reload_items(self)`**: نفس منطق `_InboundTab._reload_items`.
- **`_on_item_changed(self)`**: يحدّث تسمية الرصيد المتاح للصنف المحدد.
- **`_save(self)`**: يتحقق من اختيار صنف، يستدعي `self._svc.record_outbound(inv_id, qty, date, notes)`، يمسح الملاحظات، يصدر الحدث؛ يلتقط `ValueError` (مثال: رصيد غير كافٍ) ويعرضه كرسالة خطأ.
- **`_load_moves(self)`**: يجلب آخر 100 حركة صادر بالأسماء، يملأها في الجدول (تاريخ، اسم، كمية، متوسط تكلفة، إجمالي، ملاحظات مع tooltip أو شرطة).

---

## `ui/tabs/inventory/inventory_report_tab.py`

**الغرض:** يحتوي كلاسين: تقرير مخزن شامل مع بطاقات إحصائية وجدول تفصيلي، ولوحة عرض حركات صنف مخزن محدد.

**Imports داخلية:** `services.inventory.inventory_service.InventoryService`, `ui.widgets.panels.themed_inputs.ThemedFrame`, `ui.widgets.panels.form_labels.section_title`, `ui.widgets.tables.tables` (`make_table`, `auto_fit_columns`), `ui.widgets.core.widget_mixin.WidgetMixin`, `ui.widgets.core.events.emit_company_data_changed`, `ui.widgets.core.i18n.tr`.

**من يستدعيه:** `ui/tabs/inventory_section.py` (`InventoryTab._build` يبني كليهما: `_ReportTab` كتاب، و`_MovesPanel` كتاب خامس منفصل ومربوط بـ `_on_item_selected`).

### Class: `_ReportTab(QWidget, WidgetMixin)`
- **Attributes:** `self.inv_conn`, `self._svc`, `self._card_frames` (list من tuples `(frame, color)`)، تسميات القيم: `lbl_total_items`, `lbl_total_value`, `lbl_low_stock`, `lbl_zero_stock`، وجدول `self.table`.
- **`__init__(self, inv_conn, parent=None)`**: يفعّل WidgetMixin بـ `data=True`، يبني، يحمّل البيانات، يطبق الستايل.
- **`_refresh_data(self, company_id=None)`**: يستدعي `_load()`.
- **`_refresh_style(self, *_)`**: يعيد تلوين كل بطاقة في `_card_frames` بحدودها اليسرى الملوّنة، ويستدعي `refresh_table_styles(self)` للجدول التفصيلي.
- **`_build(self)`**: صف 4 بطاقات إحصائية (دالة محلية `_card(label, color)` تبني `ThemedFrame` بحد أيسر ملوّن وتسجّله في `_card_frames`، ترجع `lbl_v` للتحديث لاحقاً): إجمالي الأصناف (info)، القيمة الإجمالية (success)، مخزون منخفض (stock_critical_fg)، مخزون صفري (stock_low_fg). تحتها: عنوان "التقرير التفصيلي" وجدول (صنف، وحدة، رصيد، حد أدنى، متوسط تكلفة، القيمة، حالة).
- **`_load(self)`**: يجلب كل الأصناف، يملأ الجدول صفاً بصف مع حساب حالة كل صنف (نفدت/منخفض/سليم بألوان مختلفة)، يحسب إجمالي القيمة وعدّاد المنخفض/الصفري، يحدّث كل تسميات البطاقات، يستدعي `auto_fit_columns`.

### Class: `_MovesPanel(QWidget, WidgetMixin)`
- **Attributes:** `self.inv_conn`, `self._svc`, `self._inv_id` (الصنف المعروض حالياً)، `self.lbl_title`, `self.table`.
- **`__init__(self, inv_conn, parent=None)`**: يفعّل WidgetMixin بـ `data=False` (لا يحتاج إعادة تحميل تلقائي — يُحمَّل عبر `load()` يدوياً من الخارج).
- **`_refresh_style(self, *_)`**: ستايل تسمية العنوان (لون accent) و`refresh_table_styles(self)` للجدول.
- **`_build(self)`**: تسمية عنوان ("اختر صنفاً لعرض حركاته")، جدول (تاريخ، نوع، كمية، سعر وحدة، إجمالي، رقم قيد، ملاحظات).
- **`load(self, inv_id: int)`**: يحفظ `_inv_id`، يجلب بيانات الصنف، يحدّث عنوان اللوحة برصيده الحالي، يجلب كل حركاته، يملأ الجدول (تاريخ، نوع الحركة مترجم وملوّن — وارد أخضر/صادر أحمر/تسوية لون accent محاسبي، كمية، سعر وحدة، إجمالي، رقم قيد مرجعي، ملاحظات مع tooltip).
- **`clear(self)`**: يفرّغ الجدول ويعيد تسمية العنوان لوضعها الافتراضي.

---

## قسم علاقات الملفات

- **`inventory_section.py`** هو نقطة الدخول: يفتح اتصالي `inv_conn`/`acc_conn` عبر `CompanyService` ويمررهما (أو أحدهما) لكل التابات الفرعية، ويربط تاب الأصناف بلوحة الحركات عبر callback `_on_item_selected`.
- **`_items_tab.py`** يجمع `_item_form.py` (`_ItemForm`) و`_items_table.py` (`_ItemsTable`) في splitter، ويمرر مرجع الفورم نفسه للجدول (`_ItemsTable(inv_conn, form, on_select)`) لتفعيل زر "تعديل" من الجدول مباشرة على الفورم.
- **`_inventory_inbound_tab.py`** هو الوحيد من بين تابات الحركة الذي يحتاج `acc_conn` (لأنه يُنشئ قيداً محاسبياً عبر `InventoryPostingService`)؛ `_inventory_outbound_tab.py` يعمل على `inv_conn` فقط.
- **`_inventory_report_tab.py`** يحتوي كلاسين مستقلين تماماً (`_ReportTab`, `_MovesPanel`) بلا اعتماد أحدهما على الآخر داخل الملف؛ الربط بينهما (تحديد صنف من مكان آخر → عرض حركاته في `_MovesPanel`) يتم من `inventory_section.py` الخارجي عبر `_on_item_selected`.
- **نمط مشترك في كل التابات:** استخدام `refresh_table_styles()` صراحة داخل `_refresh_style` لأي جدول مبني عبر `make_table()`، لأن الجدول لا يتابع تغييرات الثيم تلقائياً بعد إنشائه الأول (ملاحظة تكررت في: `_ItemsTable`, `_InboundTab`, `_OutboundTab`, `_ReportTab`, `_MovesPanel`).
- **تبعيات خارج هذا المسار (بلا تفصيل محتواها هنا):** `services.inventory.inventory_service.InventoryService`, `services.accounting.inventory_posting_service.InventoryPostingService`, `services.companies.company_service.CompanyService`, `ui.widgets.mixins.form_mixins.EditModeMixin`, `ui.widgets.core.widget_mixin.WidgetMixin`, `ui.widgets.tables.tables`, `ui.widgets.panels.*`, `ui.widgets.dialogs.confirm.confirm_delete`, `ui.widgets.components.button`, `ui.theme._C`, `ui.font`, `ui.constants`, `ui.widgets.core.i18n.tr`, `ui.widgets.core.events.emit_company_data_changed`.

---

## بانتظار ملفات ناقصة

| اسم الملف | المسار الكامل | الحالة |
|---|---|---|
| (لا يوجد) | — | كل الملفات الموجودة في `system_arch.txt` تحت `ui/tabs/inventory/` و`ui/tabs/inventory_section.py` مرفقة محتواها بالكامل في هذه الدفعة. |
