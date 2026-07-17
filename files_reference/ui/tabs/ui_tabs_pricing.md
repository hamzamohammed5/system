# ui_tabs_pricing.md
مرجع كامل لقسم "التسعير" — يغطي `ui/tabs/pricing_section.py` وكل الملفات تحت `ui/tabs/pricing/` (بما فيها subfolders `pricing/` و `offers/`).

---

## 1. `ui/tabs/pricing_section.py`

**الغرض:** الـ Widget الجذري لقسم "التسعير" بالكامل. يعرض هيدر القسم + `QTabWidget` بتابين فرعيين: "الأسعار الأساسية" (`PricingTab`) و "العروض" (`OffersTab`).

**الـ imports الخارجية المهمة:**
- `ui.widgets.theme.layout_styles` (`tab_style`, `apply_tab_widths`, `normalize_tab_widget`) — تنسيق شكل وعرض التابات.
- `ui.theme._C` — قاموس ألوان الثيم الحالي.
- `ui.widgets.core.i18n.tr` — الترجمة.
- `ui.font.FS_MD` — حجم خط.
- `ui.constants` (`SECTION_HEADER_HEIGHT`, `SECTION_HEADER_BORDER_W`, `SPACING_XL`).
- `ui.widgets.core.widget_mixin.WidgetMixin` — يوفر آلية الاشتراك بتحديثات الثيم/اللغة.
- `.pricing.pricing_tab.PricingTab` — تبويب الأسعار الأساسية.
- `.pricing.offers.offers_tab.OffersTab` — تبويب العروض.

**من يستدعي هذا الملف:** `ui/main_window.py` — يبنيه كقسم تنقل رئيسي (مؤكَّد من بنية `main_window_helper/_sidebar.py`).

### Class: `PricingSection(QWidget, WidgetMixin)`
- `__init__(self, parent=None)`: يستدعي `_build()` ثم `_init_widget_mixin(theme=True, font=True, lang=True, data=False)`.
- `_build(self)`: يبني `QVBoxLayout` بلا حواف/تباعد. يضيف `QLabel` هيدر (`self._header`) بارتفاع ثابت `SECTION_HEADER_HEIGHT` يحمل نص "أيقونة + اسم" التسعير عبر `tr('nav_icon_pricing')`/`tr('nav_pricing')`. يستدعي `_refresh_style()`. يبني `QTabWidget` (`self._tabs`) بعد تمريره على `normalize_tab_widget`، يضيف تابين: `PricingTab()` بعنوان `tr('pricing_tab')`، و `OffersTab()` بعنوان `tr('offers_tab')`، ثم `apply_tab_widths`.
- `_refresh_style(self, *_)`: يعيد تلوين الهيدر (خلفية `bg_surface`، حد سفلي بلون `border`، نص لون `orange` بارز bold) وإعادة تطبيق `tab_style()` + `apply_tab_widths` على `self._tabs` إن وُجد.
- `_refresh_lang(self, *_)`: يعيد ضبط نص الهيدر وعناوين التابين (index 0 و 1) عند تغيير اللغة، مع حارس `hasattr` لتفادي الاستدعاء قبل `_build`.

**ثوابت/متغيرات مستوى الملف:** لا يوجد.

**ملاحظات كود:** التعليق التوضيحي بالأعلى يذكر أن هذا "تحديث لتوحيد القسم" — النصوص عبر `tr()`، الألوان عبر `_C`، الخط عبر `font.py`، والثيم الديناميكي عبر `bus.theme_changed` (ضمنيًا عبر `WidgetMixin`).

---

## 2. `ui/tabs/pricing/pricing_tab.py`

**الغرض:** الـ Widget الرئيسي لتبويب "الأسعار الأساسية"، يحتوي تابين داخليين: لوحة الأسعار (`_PricingPanel`) وإدارة تصنيفات المنتجات النهائية (`CategoryManager`).

**الـ imports الخارجية المهمة:**
- `ui.widgets.core.i18n.tr`.
- `ui.widgets.managers.category.CategoryManager` — لوحة إدارة تصنيفات عامة قابلة لإعادة الاستخدام (scope="final" هنا).
- `ui.constants.MARGIN_ZERO`.
- `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.widgets.theme.layout_styles` (`tab_style`, `apply_tab_widths`, `normalize_tab_widget`).
- `.pricing._pricing_panel._PricingPanel` — لوحة إدارة الأسعار (الملف الرئيسي التالي في هذا المرجع).

**من يستدعي هذا الملف:** `ui/tabs/pricing_section.py` (يستورد `PricingTab` من `.pricing.pricing_tab`).

### Class: `PricingTab(QWidget, WidgetMixin)`
- `__init__(self, parent=None)`: يبني الواجهة (`_build()`) ثم `_init_widget_mixin(theme=True, font=False, lang=True, data=False)`.
- `_refresh_style(self, *_)`: يعيد تطبيق `tab_style()` و `apply_tab_widths` على `self._tabs` إن وُجد.
- `_refresh_lang(self, *_)`: يعيد ضبط عنوان تاب الأسعار (`pricing_prices_tab`) وتاب التصنيفات (`pricing_categories_tab`) عبر البحث عن `indexOf` كل بانل، ثم `apply_tab_widths`.
- `_live_conn(self)`: يرجع اتصال قاعدة البيانات النشط الحالي عبر `CompanyService.get_active_erp_conn()` (استيراد داخلي متأخر لتجنب circular import).
- `_build(self)`: `QVBoxLayout` بلا حواف (`MARGIN_ZERO`). ينشئ `self._tabs` (`QTabWidget` بعد `normalize_tab_widget`)، `self._panel_prices = _PricingPanel(self._live_conn())`، `self._panel_categories = CategoryManager(self._live_conn(), scope="final")`. يضيف التابين بعنواني `pricing_prices_tab` و `pricing_categories_tab`. يستدعي `_refresh_style()`.

**ثوابت/متغيرات مستوى الملف:** لا يوجد.

---

## 3. `ui/tabs/pricing/pricing/_stat_box.py`

**الغرض:** يوفر مكوّن "بطاقة إحصائية" (Stat Box) قابل لإعادة الاستخدام في كل واجهات التسعير والعروض، يعرض عنوان ثابت + قيمة متغيرة، مع دعم تلقائي لتحديث الألوان عند تغيير الثيم.

**الـ imports الخارجية المهمة:**
- `ui.widgets.panels.themed_inputs.ThemedFrame` — القاعدة البصرية للإطار.
- `ui.constants` (`STAT_BOX_BORDER_RADIUS`, `STAT_BOX_BORDER_W`, `STAT_BOX_PADDING`, `STAT_INNER_MARGIN_COMPACT`, `STAT_CARD_SPACING_COMPACT`).
- `ui.widgets.core.i18n.tr`.
- `ui.widgets.core.widget_mixin.WidgetMixin`.

**من يستدعي هذا الملف:** `_pricing_panel.py` و `offer_form.py` و `offer_details.py` (جميعها تستورد دالة `stat_box` من `..pricing._stat_box` أو `._stat_box`).

### Class: `StatBoxFrame(ThemedFrame, WidgetMixin)`
بطاقة إحصائية تتابع الثيم تلقائيًا (تحل مشكلة قديمة: الكروت كانت تفقد تلوينها الصحيح عند تبديل الثيم لأن الستايل كان يُحدَّد مرة واحدة فقط وقت الإنشاء).
- **class attributes/state:** `_color_key` (مفتاح اللون الافتراضي للقيمة)، `_value_color` (لون مخصص يتخطى `_color_key` إن وُجد، مثلاً "success"/"danger" حسب الربح).
- `__init__(self, label: str, color_key: str = "accent", parent=None)`: يبني `QVBoxLayout` صغير بهامش/تباعد مضغوط، يضيف `self.lbl_title` (نص العنوان، وسط) و `self.lbl_val` (نص القيمة، يبدأ بـ `tr('empty_placeholder')`، وسط). يستدعي `_init_widget_mixin(font=False, lang=False, data=False)` ثم `_refresh_style()`.
- `set_value_color(self, color_key: str = None)`: يحفظ `color_key` في `self._value_color` ويعيد استدعاء `_refresh_style()`. تمرير `None` يرجّع اللون الافتراضي الأصلي (`_color_key`).
- `_refresh_style(self, *_)`: يقرأ `_C` (ألوان الثيم) و `FS_XS`/`FS_LG` (أحجام خطوط)، يحدد `color = _C[self._value_color or self._color_key]`. يطبّق ستايل الإطار (خلفية `bg_surface`، حد `border`)، ستايل `lbl_title` (خط صغير، لون `text_muted`)، وستايل `lbl_val` (خط كبير bold باللون المحدد).

### دالة top-level: `stat_box(label: str, color_key: str = "accent") -> tuple`
تُنشئ `StatBoxFrame(label, color_key)` وترجع `(frame, frame.lbl_val)` — وهذا هو الـ API الخارجي المستخدم في كل الملفات الأخرى (توافقًا مع نمط قديم كان يرجع frame + label القيمة مباشرة).

**ثوابت/متغيرات مستوى الملف:** لا يوجد (كل الثوابت مستوردة من `ui.constants`).

---

## 4. `ui/tabs/pricing/pricing/_pricing_table.py`

**الغرض:** جدول عرض "الأسعار المحفوظة" (منتجات نهائية + تسعيرها إن وُجد)، مستخرَج كـ Widget مستقل يرث `BaseListPanel` بدل أن يكون مبنيًا يدويًا داخل `_PricingPanel` — بما يوحّد بنية الجداول في المشروع (نمط splitter + هيدر أزرار مركزي).

**الـ imports الخارجية المهمة:**
- `models.costing.calc_cost` — حساب تكلفة منتج معيّن.
- `ui.widgets.base.list_panel.BaseListPanel` — الكلاس الأساسي الذي يوفر بنية الجدول/الفلترة/الأنماط المركزية.
- `ui.widgets.tables.tables` (`make_item`, `colored_item`) — بناء خلايا جدول موحّدة الشكل.
- `ui.widgets.core.i18n.tr`.
- `ui.theme._C`.

**من يستدعي هذا الملف:** `_pricing_panel.py` (يستورد `_PricingTable` من `._pricing_table`).

### Class: `_PricingTable(BaseListPanel)`
- **Class-level attributes:**
  - `COLUMNS`: قائمة عناوين أعمدة (ID، منتج، تصنيف، تكلفة، نسبة الهامش، السعر، الربح، نسبة الهامش الفعلية) — كلها عبر `tr(...)`.
  - `STRETCH_COL = -1` (لا يوجد عمود يتمدد وحده — توحيد سلوك كل الجداول في المشروع؛ الامتداد يُترك لـ `stretchLastSection`).
  - `EMPTY_TITLE = "no_pricing"` (مفتاح ترجمة يُعرض عند عدم وجود صفوف).
  - `LIST_TITLE = tr("pricing_saved_prices")`.
  - `ADD_TEXT = ""` (لا يوجد زر إضافة من داخل الجدول — الإضافة تتم من الفورم فوق الجدول).
  - `SHOW_CATEGORY = True`.
  - `FILTER_SCOPE = "final"` (الفلترة تخص المنتجات النهائية فقط).
  - `CONNECT_BUS = True`.
- `__init__(self, conn, on_edit_selected, on_select=None, parent=None)`: يخزن `_on_edit_cb` و `_on_select_cb`، يستدعي `super().__init__(conn, parent)`، ثم يربط `self.item_selected` (signal من `BaseListPanel`) بـ `self._on_selection_changed`.
- `_refresh_data(self, company_id=None)`: يستدعي `self.refresh()` (إعادة تحميل بيانات الجدول عند تغيّر الشركة النشطة).
- `_load_rows(self) -> list`: يستورد `get_all_pricing` من `services.pricing.pricing_service` ويرجع `list(get_all_pricing(self.conn))`، مع `try/except` يرجع `[]` عند أي استثناء.
- `_match_filter(self, row: dict, query: str) -> bool`: إن وُجد `self._filter_toolbar` يفوّض المطابقة له (`match(name, category_id)`)، وإلا يطابق `query` (lowercase) مع اسم الصف.
- `_fill_row(self, table, r: int, row: dict)`: يحسب `cost = calc_cost(conn, row['id'])`. يحدد `has_p` (هل يوجد تسعير محفوظ)، ثم `price`/`margin`/`profit`/`margin_actual` (كلها `None` إن لم يوجد تسعير). يضبط الخلايا:
  - عمود 0: ID (مع `user_data=row['id']` للاستخدام في التحديد).
  - عمود 1: اسم المنتج.
  - عمود 2: اسم التصنيف أو `tr('dash')`.
  - عمود 3: التكلفة بصيغة `.2f`.
  - عمود 4: نسبة الهامش المدخلة أو placeholder.
  - عمود 5: السعر المحفوظ أو placeholder.
  - عمود 6: الربح (`colored_item` بلون `success`/`danger` حسب القيمة) أو placeholder.
  - عمود 7: نسبة الهامش الفعلية المحسوبة أو placeholder.
- `_build_extra_header_actions(self, header)`: يضيف زر "تعديل" (`pricing_edit_selected_btn`) بستايل "normal" في هيدر الجدول، مرتبط بـ `_trigger_edit`.
- `_trigger_edit(self)`: يقرأ `self.selected_id()`؛ إن لم يوجد تحديد يعرض `QMessageBox.information` تحذيري، وإلا يستدعي `self._on_edit_cb(pid)`.
- `_on_add_clicked(self)`: `pass` — لا فعل، لأن الإضافة تتم عبر الفورم لا الجدول.
- `_on_row_double_clicked(self, item_id)`: يستدعي `self._on_edit_cb(item_id)` (نقر مزدوج = تعديل مباشر).
- `_on_selection_changed(self, item_id: int)`: يستدعي `self._on_select_cb(item_id)` إن كان مُمرَّرًا.

**ثوابت/متغيرات مستوى الملف:** لا يوجد خارج الـ class attributes أعلاه.

**ملاحظات كود:** التعليقات التوضيحية تشرح أن هذا استبدال كامل لجدول قديم مبني يدويًا؛ الحذف يبقى من داخل الفورم (`_PricingPanel`) لا من هيدر الجدول نفسه، بخلاف نمط `_OffersTable` الذي يضع زر الحذف في هيدر الجدول أيضًا.

---

## 5. `ui/tabs/pricing/pricing/_pricing_panel.py`

**الغرض:** لوحة الفورم الرئيسية لإدارة تسعير المنتجات النهائية — اختيار منتج، تحديد هامش ربح أو سعر يدوي، عرض إحصائيات (تكلفة/سعر مقترح/سعر يدوي/ربح/هامش فعلي)، مقارنة سيناريوهات، وأزرار حفظ/تعديل/حذف، مع استضافة `_PricingTable` أسفلها.

**الـ imports الخارجية المهمة:**
- `ui.widgets.panels.themed_inputs` (`ThemedComboBox`, `ThemedFrame`).
- `services.pricing.pricing_service` (`get_pricing`, `save_pricing`, `remove_pricing`, `get_final_products`, `get_item`) — كل عمليات CRUD للتسعير وجلب بيانات المنتجات.
- `models.costing.calc_cost` — حساب تكلفة المنتج.
- `ui.theme._C`.
- `ui.constants` (مجموعة كبيرة من ثوابت الأبعاد/التباعد الخاصة بلوحة التسعير).
- `ui.widgets.components.button` (`make_btn`, و`refresh_visible_buttons` مستوردة داخليًا في `_refresh_style`) — بناء أزرار موحّدة الشكل تتبع الثيم.
- `ui.widgets.panels.form_labels.section_title` — عنوان قسم فرعي (لـ "الأسعار المحفوظة").
- `ui.widgets.core.events.emit_company_data_changed` — بث إشعار تغيّر بيانات الشركة (بعد حفظ/حذف).
- `ui.widgets.core.i18n.tr`.
- `ui.tabs.costing.shared.scenario_comparison_widget.ScenarioComparisonWidget` — Widget مقارنة سيناريوهات تسعير (من مسار خارجي: `costing`، غير مُغطى في هذا المرجع).
- `ui.widgets.core.widget_mixin.WidgetMixin`.
- `._stat_box.stat_box` — بطاقات الإحصائيات.
- `._pricing_table._PricingTable` — جدول الأسعار المحفوظة.

**من يستدعي هذا الملف:** `pricing_tab.py` (يستورد `_PricingPanel` من `.pricing._pricing_panel`).

### دالة top-level: `_spin(max_=9999999, dec=2)`
تُنشئ وترجع `QDoubleSpinBox` بمدى `[0, max_]`، عدد خانات عشرية `dec`، وارتفاع أدنى `PRICING_PANEL_SPIN_MIN_H`.

### دالة top-level: `buttons_row(*widgets)`
تبني وترجع `QHBoxLayout` أفقي يضيف كل الـ widgets المُمرَّرة بتباعد `PRICING_PANEL_BTN_ROW_SPACING`، مع `addStretch()` في النهاية (بديل بسيط لدالة `buttons_row` قديمة).

### Class: `_PricingPanel(QWidget, WidgetMixin)`
- **state:** `conn`, `_editing_id` (id المنتج الجاري تعديل تسعيره أو `None`)، `_last_profit` (آخر قيمة ربح محسوبة، تُستخدم لتحديد لون بطاقة الربح عند تغيير الثيم).
- `__init__(self, conn, parent=None)`: يبني الواجهة، يحمّل قائمة المنتجات في الكومبو، يستدعي `_init_widget_mixin(theme=True, font=True, lang=False, data=True)`، ثم `_refresh_style()`.
- `_refresh_data(self, company_id=None)`: يعيد تحميل كومبو المنتجات (`_load_products_combo`) ويستدعي `self._table.refresh()`.
- `_refresh_style(self, *_)`: يعيد تلوين `form_frame` (حد `border`)، ولابلات الفورم (`lbl_mode`, `lbl_prod`, `lbl_margin`, `lbl_pct`, `lbl_price`) بألوان/أحجام خط الثيم الحالي. يستدعي `refresh_visible_buttons(self)` لتحديث ألوان الأزرار المبنية بـ `make_btn`. يستدعي `_refresh_manual_stats_style()`.
- `_refresh_manual_stats_style(self)`: يحدد لون بطاقة الربح (`lbl_stat_profit_frame`) عبر `set_value_color("success" أو "danger")` طبقًا لقيمة `self._last_profit`، بحيث يبقى اللون صحيحًا حتى بعد تبديل الثيم.
- `_build(self)`: يبني الفورم كاملاً:
  - `form_frame` (`ThemedFrame`) يحوي: `lbl_mode` (نص "وضع جديد"/تعديل)، صف أول (`row1`) فيه: كومبو اختيار منتج (`cmb_product`)، حقل هامش (`sp_margin`، افتراضي 30%)، حقل سعر نهائي يدوي (`sp_price`).
  - صف بطاقات إحصائية (`stats_row`) خمس بطاقات: التكلفة (info)، السعر المقترح (success)، السعر اليدوي (orange)، الربح (success، ومرجعها محفوظ في `lbl_stat_profit_frame`)، نسبة الهامش الفعلية (purple).
  - `ScenarioComparisonWidget(self.conn)` (`self._scenario_comparison`) يُضاف أسفل الإحصائيات.
  - صف أزرار: `btn_save` (success)، `btn_cancel` (ghost، مخفي افتراضيًا)، `btn_del` (danger، مخفي افتراضيًا).
  - عنوان قسم (`section_title`) لـ "الأسعار المحفوظة"، ثم `self._table = _PricingTable(conn, on_edit_selected=self._load_for_edit, on_select=self._on_table_select)`.
  - ربط الأحداث: `cmb_product.currentIndexChanged → _on_product_selected`، `sp_margin.valueChanged → _update_preview`، `sp_price.valueChanged → _update_profit_from_price`، `btn_save.clicked → _save`، `btn_cancel.clicked → _reset_form`، `btn_del.clicked → _delete`.
- `_load_products_combo(self)`: يحفظ التحديد الحالي (`prev`)، يمسح الكومبو، يضيف عنصر placeholder، ثم يضيف كل منتج من `get_final_products(self.conn)`. يحاول استرجاع التحديد السابق، وإلا يرجع للعنصر الأول.
- `_on_product_selected(self)`: يستدعي `_update_preview()` و `_refresh_scenario_comparison()`.
- `_update_preview(self)`: إن لم يوجد منتج محدد، يفرّغ كل بطاقات الإحصائيات. وإلا يحسب `cost = calc_cost(...)`، `price = cost * (1 + margin/100)`، يحدّث بطاقتي التكلفة والسعر المقترح. إن لم يكن في وضع تعديل (`_editing_id is None`) يضبط `sp_price` تلقائيًا على السعر المحسوب (بحجب الإشارة لمنع تكرار). يستدعي `_refresh_manual_stats(cost)`.
- `_update_profit_from_price(self)`: عند تغيير السعر اليدوي، يعيد حساب `cost` ويستدعي `_refresh_manual_stats(cost)` و `self._scenario_comparison.update_price(sp_price.value())`.
- `_refresh_manual_stats(self, cost: float)`: يحسب `manual = sp_price.value()`, `profit = manual - cost`, `margin_pct` (نسبة مئوية، صفر إن كانت التكلفة صفر). يحدّث `_last_profit`، يحدّث بطاقات السعر اليدوي/الربح/نسبة الهامش الفعلية، ويستدعي `_refresh_manual_stats_style()`.
- `_refresh_scenario_comparison(self)`: إن لم يوجد منتج محدد يستدعي `self._scenario_comparison.clear()`، وإلا `load_product(prod_id, current_price)`.
- `_save(self)`: يتحقق من وجود منتج محدد وسعر موجب (رسائل تحذير `QMessageBox` عند الفشل)، يستدعي `save_pricing(conn, prod_id, margin, price)`، يستدعي `_reset_form()` ثم `emit_company_data_changed()`.
- `_delete(self)`: إن لم يوجد `_editing_id` يتوقف. يجلب اسم المنتج (`get_item`)، يعرض `confirm_delete`-مثيل عبر `QMessageBox.question`، وعند التأكيد يستدعي `remove_pricing`، `_reset_form()`، `emit_company_data_changed()`.
- `_reset_form(self)`: يصفّر `_editing_id`، يرجّع الكومبو للعنصر الأول، `sp_margin` لـ30، `sp_price` لـ0، يفرّغ كل البطاقات لـ placeholder، يرجّع `lbl_mode` لنص "جديد"، يخفي أزرار الإلغاء/الحذف، ويمسح مقارنة السيناريوهات.
- `_on_table_select(self, prod_id: int)`: عند اختيار صف من الجدول، يحسب التكلفة ويحدّث `lbl_stat_cost` بنص لاحقة (`pricing_cost_suffix`).
- `_load_for_edit(self, prod_id: int)`: يجلب `pricing` و `item`؛ إن لم يوجد `item` يتوقف. يضبط `_editing_id`، يحدد المنتج في الكومبو، يحسب التكلفة، ويملأ `sp_margin`/`sp_price` من التسعير المحفوظ إن وُجد، أو قيم افتراضية (30%، تكلفة×1.3) إن لم يوجد. يحدّث `lbl_mode` لنص وضع التعديل، يُظهر زر الإلغاء دائمًا، ويُظهر زر الحذف فقط إن كان هناك تسعير محفوظ فعلاً. يستدعي `_refresh_manual_stats(cost)` و `load_product` لمقارنة السيناريوهات.

**ثوابت/متغيرات مستوى الملف:** لا يوجد خارج الدوال المساعدة أعلاه.

---

## 6. `ui/tabs/pricing/offers/offer_item_row.py`

**الغرض:** يمثّل صفاً واحداً (منتج واحد) داخل فورم إنشاء/تعديل عرض (`_OfferForm`) — يحتوي بحث/اختيار منتج، عرض تكلفته وسعره، حقل كمية، إجمالي السطر، تنبيه عند غياب تسعير، وزر حذف الصف.

**الـ imports الخارجية المهمة:**
- `ui.widgets.panels.themed_inputs` (`ThemedLineEdit`, `ThemedComboBox`, `ThemedFrame`).
- `services.pricing.offers_service` (`get_offer_candidate_items`, `get_priced_ids`, `get_item_price`, `get_item_cost`, `has_pricing as has_pricing_fn`) — بيانات المنتجات المؤهلة للعروض وتسعيرها.
- `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.widgets.core.i18n.tr`.
- `ui.constants` (ثوابت أبعاد كثيرة خاصة بصف عنصر العرض).

**من يستدعي هذا الملف:** `offer_form.py` (يستورد `_OfferItemRow` من `.offer_item_row` لبناء الصفوف داخل الفورم).

### دالة top-level: `_spin(max_=999999, dec=2)`
تُنشئ وترجع `QDoubleSpinBox` بمدى `[0, max_]`، `dec` خانات عشرية، ارتفاع أدنى `BTN_MIN_HEIGHT`.

### Class: `_OfferItemRow(ThemedFrame, WidgetMixin)`
- **state:** `_conn`, `_on_remove` (callback عند الحذف)، `_on_change` (callback عند تغيّر أي قيمة تؤثر على الإجماليات).
- `__init__(self, conn, on_remove, on_change, parent=None)`: يبني الصف، يستدعي `_init_widget_mixin(theme=True, font=True, lang=False, data=True)`، `_refresh_style()`، ثم `_load_products()`.
- `_live_conn(self)`: يرجع اتصال صالح دائمًا — يفحص `CompanyService.is_conn_alive(self._conn)` وإلا يجلب اتصالاً نشطًا جديدًا.
- `_refresh_data(self, company_id=None)`: يستدعي `_reload_products()` (إعادة تحميل قائمة المنتجات بنفس نص البحث الحالي).
- `_refresh_style(self, *_)`: يلوّن إطار الصف (خلفية `row_alt_bg`)، حقل البحث (`inp_search`، مع حالة `:focus` بلون `orange`)، `lbl_cost` (لون `journal_dr_accent`)، `lbl_listed` (لون `success`)، `lbl_line` (لون `orange` bold)، `lbl_warn` (لون `orange`)، و `_btn_del` (شفاف مع لون `danger` عند hover).
- `_build(self)`: صف أفقي يحتوي بالترتيب: `inp_search` (بحث نصي، عرض ثابت)، `cmb_product` (كومبو المنتج، stretch=1)، لابل "التكلفة:" + `lbl_cost`، لابل "السعر:" + `lbl_listed`، رمز "×" + `sp_qty` (كمية، افتراضي 1.0)، رمز "=" + `lbl_line` (إجمالي السطر)، `lbl_warn` (أيقونة تحذير، مخفية افتراضيًا)، وزر حذف (`btn_del`، مربوط بـ `lambda: self._on_remove(self)`).
- `_load_products(self, filter_text: str = "")`: يجلب اتصالاً صالحًا (يتوقف بصمت عند الفشل). يحفظ التحديد الحالي، يمسح الكومبو، يجلب `priced_ids` (المنتجات التي لها تسعير)، ثم لكل نوع في `("final", "semi")` يجلب `get_offer_candidate_items` ويضيف فقط العناصر: (أ) موجودة في `priced_ids`، (ب) تطابق نص البحث إن وُجد. يعيد تحديد العنصر السابق إن وُجد، وإلا يستدعي `_on_product_changed()`.
- `_reload_products(self)`: يستدعي `_load_products` بنص البحث الحالي من `inp_search`.
- `_on_product_changed(self)`: إن لم يوجد منتج محدد يفرّغ كل الحقول ويخفي التحذير. وإلا يجلب `unit_cost`, `has_pricing`, `unit_price` (0 إن لم يوجد تسعير)، يحدّث `lbl_cost`/`lbl_listed`/يُظهر التحذير عند غياب التسعير، يحسب `line_total = unit_price * qty` ويحدّث `lbl_line`. يستدعي `self._on_change()` في كل الحالات إن كان مُمرَّرًا.
- `get_item_id(self)`: يرجع `self.cmb_product.currentData()`.
- `get_qty(self) -> float`: يرجع `self.sp_qty.value()`.
- `get_values(self) -> tuple | None`: يرجع `(item_id, qty)` أو `None` إن لم يوجد منتج محدد.
- `set_values(self, item_id: int, qty: float)`: يبحث عن `item_id` في الكومبو ويحدده، يضبط `sp_qty`، ثم يستدعي `_on_product_changed()`.

**ثوابت/متغيرات مستوى الملف:** لا يوجد خارج `_spin`.

---

## 7. `ui/tabs/pricing/offers/offer_form.py`

**الغرض:** الفورم الكامل لإنشاء أو تعديل عرض (Offer) — بيانات العرض (اسم، خصم، تصنيف، ملاحظات)، إحصائيات إجمالية، منطقة صفوف منتجات قابلة للتمرير (كل صف = `_OfferItemRow`)، وأزرار إضافة صف/حفظ/إلغاء.

**الـ imports الخارجية المهمة:**
- `ui.widgets.panels.themed_inputs` (`ThemedLineEdit`, `ThemedFrame`).
- `services.pricing.offers_service` (`get_offer`, `get_offer_items`, `create_offer`, `modify_offer`, `save_offer_items`, `get_item_price`, `get_item_cost`) — كل عمليات CRUD الخاصة بالعروض.
- `ui.widgets.combo.category.CategoryCombo` — كومبو اختيار تصنيف.
- `ui.widgets.core.i18n.tr`.
- `ui.widgets.core.events.emit_company_data_changed`.
- `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.constants` (مجموعة كبيرة من ثوابت الأبعاد الخاصة بفورم العرض).
- `.offer_item_row._OfferItemRow` — صف المنتج الواحد.
- `..pricing._stat_box.stat_box` — بطاقات الإحصائيات (من مسار `pricing/pricing` الشقيق).

**من يستدعي هذا الملف:** `offers_tab.py` (يستورد `_OfferForm` من `.offer_form`).

### دالة top-level: `buttons_row(*buttons) -> QHBoxLayout`
تبني صف أزرار أفقي بتباعد `SPACING_SM`، تضيف كل الأزرار، مع `addStretch()` بالنهاية.

### دالة top-level: `_spin(max_=999999, dec=2)`
تُنشئ وترجع `QDoubleSpinBox` بمدى `[0, max_]`، `dec` خانات عشرية، ارتفاع أدنى `BTN_MIN_HEIGHT`.

### Class: `_OfferForm(QWidget, WidgetMixin)`
- **state:** `_conn`, `_editing_id` (id العرض الجاري تعديله أو `None`)، `_editing_name`، `_item_rows: list[_OfferItemRow]` (قائمة صفوف المنتجات الحالية).
- `__init__(self, conn, parent=None)`: يبني الفورم، `_init_widget_mixin(theme=True, font=True, lang=True, data=False)`، `_refresh_style()`.
- `_live_conn(self)`: نفس نمط الاتصال الصالح دائمًا (فحص حيوية الاتصال ثم استرجاع اتصال نشط عند الحاجة).
- `_refresh_style(self, *_)`: يلوّن `_header_frame` (حد `orange_border`)، `lbl_mode` (لون `orange` bold)، `_lbl_disc_pct`، كل عناصر `_hdr_labels` (رؤوس أعمدة صفوف المنتجات، لون `text_muted` مع حد سفلي)، `_scroll` (منطقة التمرير، خلفية `scroll_warm_bg`)، `_btn_add_row` (خلفية `orange_bg` مع hover)، `btn_save` (خلفية `orange` بارزة).
- `_build(self)`: يبني:
  - `header` (`ThemedFrame`) يحوي `lbl_mode`، صف معلومات (`info_row`): اسم العرض (`inp_name`)، نسبة خصم (`sp_discount`)، تصنيف (`cmb_category` عبر `CategoryCombo(scope="all")`)، ملاحظات (`inp_notes`). ثم صف بطاقات إحصائية خمس: الإجمالي قبل الخصم، قيمة الخصم، سعر البيع، التكلفة الإجمالية، الربح (`lbl_profit_frame` محفوظ للمرجع).
  - رؤوس أعمدة صفوف المنتجات (`ch`) — بحث، منتج (stretch)، تكلفة، سعر، كمية، إجمالي، وعمودين فارغين (أيقونة تحذير + حذف).
  - منطقة تمرير (`scroll`) تحوي `_rows_container` (بـ `_rows_layout` رأسي ينتهي بـ `addStretch()`).
  - صف أزرار: "إضافة منتج" (`_btn_add_row`)، "حفظ" (`btn_save`)، "إلغاء" (`btn_cancel`، مخفي افتراضيًا).
  - يستدعي `_add_item_row()` مرة واحدة كبداية (صف فاضي واحد).
  - يربط: `sp_discount.valueChanged → _update_totals`، أزرار الإضافة/الحفظ/الإلغاء بدوالها.
- `_refresh_lang(self, *_)`: يعيد ضبط `lbl_mode` (حسب كون فيه تعديل جارٍ أم لا)، placeholders لحقول الاسم/الملاحظات، ونصوص أزرار الحفظ/الإلغاء.
- `_add_item_row(self, item_id=None, qty=1.0)`: يُنشئ `_OfferItemRow` جديد (بربط `on_remove`/`on_change`)، يضيفه لـ `_item_rows` وللـ layout قبل الـ stretch الأخير. إن مُرِّر `item_id` يضبط قيمه عبر `set_values`. يستدعي `_update_totals()`.
- `_remove_item_row(self, row_widget)`: يزيل الصف من `_item_rows` والـ layout، يستدعي `deleteLater()`، ثم `_update_totals()`.
- `_clear_rows(self)`: يحذف كل الصفوف الحالية ويُفرغ `_item_rows`.
- `_update_totals(self)`: يمر على كل صف صالح (له `item_id`)، يجمع `total_listed` (سعر × كمية) و `total_cost` (تكلفة × كمية) عبر استدعاءات `get_item_price`/`get_item_cost` (مع `try/except` لتجاهل صف فاشل). يحسب `disc_amt = total_listed * disc_pct`، `sell_price = total_listed - disc_amt`، `profit = sell_price - total_cost`. يحدّث كل بطاقات الإحصائيات، ويضبط لون بطاقة الربح عبر `set_value_color`.
- `_save(self)`: يتحقق من اسم العرض غير الفارغ وواجود عنصر واحد صالح على الأقل (رسائل تحذير عند الفشل). يجلب اتصالاً صالحًا. إن كان `_editing_id` موجوداً يستدعي `modify_offer` + `save_offer_items`، وإلا `create_offer` (يرجع `oid` جديد) + `save_offer_items`. يستدعي `self.reset()` ثم `emit_company_data_changed()`.
- `load_offer(self, offer_id: int)`: يجلب بيانات العرض (`get_offer`)؛ إن لم يوجد يتوقف. يضبط `_editing_id`/`_editing_name`، يعبّئ الحقول (`inp_name`, `sp_discount`, `inp_notes`, `cmb_category`)، يمسح الصفوف الحالية ويعيد بناء صف لكل عنصر في `get_offer_items(conn, offer_id)`. يحدّث `lbl_mode`، يُظهر `btn_cancel`، ويستدعي `_update_totals()`.
- `reset(self)`: يصفّر `_editing_id`/`_editing_name`، يفرغ كل الحقول (اسم/خصم/ملاحظات/تصنيف)، يمسح الصفوف ويضيف صفاً فارغاً واحداً، يرجّع `lbl_mode` لوضع "جديد"، يخفي `btn_cancel`، ويفرّغ كل بطاقات الإحصائيات لـ placeholder.

**ثوابت/متغيرات مستوى الملف:** لا يوجد خارج الدوال المساعدة أعلاه.

---

## 8. `ui/tabs/pricing/offers/offer_details.py`

**الغرض:** لوحة عرض تفاصيل عرض مختار من الجدول — عنوان العرض، بطاقات إحصائية (إجمالي قبل خصم، قيمة الخصم، سعر البيع، التكلفة، الربح)، جدول بنود العرض بالتفصيل، وملاحظات.

**الـ imports الخارجية المهمة:**
- `ui.widgets.panels.themed_inputs.ThemedFrame`.
- `services.pricing.offers_service.get_offer_summary` — دالة الخدمة التي تجمع كل بيانات العرض المطلوبة للعرض.
- `ui.widgets.core.i18n.tr`.
- `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.widgets.tables.tables` (`make_item`, `colored_item`, `make_splitter_table_guarded`, `fit_splitter_table`, `refresh_table_styles`, `ROW_HEIGHT_NORMAL`) — أدوات بناء جدول splitter موحّد.
- `ui.constants` (ثوابت أبعاد/أعمدة الجدول الخاصة بتفاصيل العرض).
- `..pricing._stat_box.stat_box`.

**من يستدعي هذا الملف:** `offers_tab.py` (يستورد `_OfferDetails` من `.offer_details`).

### Class: `_OfferDetails(ThemedFrame, WidgetMixin)`
- `__init__(self, conn, parent=None)`: يخزن `conn`، `_init_widget_mixin(lang=True, data=False)`، `_build()`، `_refresh_style()`.
- `_refresh_style(self, *_)`: يلوّن الإطار الرئيسي (حد `orange_border`)، `lbl_title` (لون `orange` bold)، `lbl_notes` (لون `text_muted` صغير). يستدعي `refresh_table_styles(self)` — المصدر المركزي الوحيد لإعادة تطبيق ستايل الجدول (`_table_variant` property) مع كل تغيير ثيم، بدل أن يبقى الجدول بستايل قديم من وقت الإنشاء.
- `_live_conn(self)`: نمط الاتصال الصالح دائمًا القياسي (فحص حيوية الاتصال).
- `_build(self)`: `QVBoxLayout` بهوامش `FORM_LAYOUT_MARGIN`. يضيف `lbl_title` (placeholder افتراضي)، صف بطاقات إحصائية خمس (نفس أعمدة `offer_form.py`: قبل الخصم/الخصم/سعر البيع/التكلفة/الربح — `lbl_profit_frame` محفوظ)، ثم جدولاً (`make_splitter_table_guarded`) بأعمدة: منتج، تصنيف، كمية، تكلفة الوحدة، سعر الوحدة، إجمالي السطر، ربح السطر — بعرض أعمدة محدد من ثوابت `OFFER_DET_COL*_W` و `stretch_col=-1`. أخيرًا `lbl_notes` (ملاحظات، word-wrap).
- `load(self, offer_id: int)`: يجلب `s = get_offer_summary(conn, offer_id)` (مع `try/except` يتوقف بصمت عند الفشل، أو إن كانت `s` فاضية). يبني نص العنوان (`offer_details_title`) مع جزء تصنيف اختياري. يمسح صفوف الجدول ويعيد تعبئتها من `s["lines"]`: أيقونة نوع العنصر (نهائي/نصف مصنّع)، اسم الفئة، الكمية (`.4g`)، تكلفة الوحدة (`colored_item` بلون `journal_dr_accent`)، سعر الوحدة (لون `success` إن وُجد تسعير وإلا نص تحذيري بلون `orange`)، إجمالي السطر (لون `orange` إن وُجد تسعير وإلا `dash`)، وربح السطر (محسوب `(price - cost) * qty`، لون `success`/`danger` حسب القيمة، أو `dash` إن لم يوجد تسعير). يستدعي `fit_splitter_table` لضبط ارتفاع الجدول. يحدّث كل بطاقات الإحصائيات (`sl_listed`, `sl_disc`, `sl_sell`, `sl_cost`, `sl_profit`) ويضبط لون بطاقة الربح عبر `set_value_color`. يحدّث `lbl_notes` إن وُجدت ملاحظات.
- `clear(self)`: يرجّع `lbl_title` لـ placeholder، يمسح صفوف الجدول، يفرّغ كل بطاقات الإحصائيات لـ placeholder، ويمسح `lbl_notes`.

**ثوابت/متغيرات مستوى الملف:** لا يوجد.

---

## 9. `ui/tabs/pricing/offers/offers_table.py`

**الغرض:** جدول العروض المحفوظة، مع فلتر وأزرار تعديل/حذف في الهيدر، مُعاد هيكلته بالكامل ليرث `BaseListPanel` (بدل بناء يدوي سابق بـ `QWidget + WidgetMixin`).

**الـ imports الخارجية المهمة:**
- `services.pricing.offers_service` (`get_all_offers`, `get_offer_summary`).
- `ui.widgets.base.list_panel.BaseListPanel`.
- `ui.widgets.tables.tables` (`make_item`, `colored_item`).
- `ui.widgets.core.i18n.tr`.
- `ui.theme._C`.

**من يستدعي هذا الملف:** `offers_tab.py` (يستورد `_OffersTable` من `.offers_table`).

### Class: `_OffersTable(BaseListPanel)`
- **Class-level attributes:**
  - `COLUMNS`: ID، منتج، تصنيف، عدد البنود، نسبة الخصم، الإجمالي قبل الخصم، سعر البيع، التكلفة، الربح، تاريخ الإنشاء.
  - `STRETCH_COL = -1`.
  - `EMPTY_TITLE = "no_offers"`.
  - `LIST_TITLE = tr("offer_saved_list")`.
  - `ADD_TEXT = ""` (الإضافة عبر فورم منفصل `_OfferForm`، لا من الجدول).
  - `SHOW_CATEGORY = True`.
  - `FILTER_SCOPE = "all"`.
  - `CONNECT_BUS = True`.
- `__init__(self, conn, on_edit, on_delete, on_select, parent=None)`: يخزن الـ callbacks الثلاثة، `super().__init__(conn, parent)`، يربط `item_selected → _on_selection_changed`.
- `_live_conn(self)`: نمط الاتصال الصالح دائمًا القياسي.
- `_refresh_data(self, company_id=None)`: `self.refresh()`.
- `_load_rows(self) -> list`: يرجع `list(get_all_offers(conn))` (مع `try/except` يرجع `[]`).
- `_match_filter(self, row: dict, query: str) -> bool`: يفوّض لـ `_filter_toolbar.match` إن وُجد، وإلا مطابقة بسيطة بالاسم.
- `_fill_row(self, table, r: int, row: dict)`: يجلب `s = get_offer_summary(conn, row['id'])` (مع `try/except` يرجع `{}` عند الفشل). يحدد لون الربح (`success`/`danger`). يعبّئ الأعمدة: ID (مع `user_data`)، اسم، تصنيف أو `dash`، عدد بنود العرض (`len(s.get('lines', []))`)، نسبة الخصم `.1f %`، الإجمالي قبل الخصم، سعر البيع، التكلفة، الربح (`colored_item`)، تاريخ الإنشاء.
- `_build_extra_header_actions(self, header)`: يضيف زرين في هيدر الجدول: "تعديل" (normal) و "حذف" (danger).
- `_trigger_edit(self)`: يقرأ `selected_id()`، إن وُجد يستدعي `_on_edit_cb(oid)`.
- `_trigger_delete(self)`: نفس المنطق لكن يستدعي `_on_delete_cb(oid)`.
- `_on_add_clicked(self)`: `pass` (الإضافة من فورم منفصل).
- `_on_row_double_clicked(self, item_id)`: يستدعي `_on_edit_cb(item_id)` (نقر مزدوج = تعديل).
- `_on_selection_changed(self, item_id: int)`: يستدعي `_on_select_cb(item_id)` إن كان مُمرَّرًا.

**ثوابت/متغيرات مستوى الملف:** لا يوجد خارج الـ class attributes.

**ملاحظات كود:** تعليق توضيحي طويل بالأعلى يشرح كل خطوات إعادة الهيكلة: حذف البناء اليدوي القديم بالكامل، التحويل لجدول splitter، توحيد `STRETCH_COL=-1`، استخدام `make_item`/`colored_item` بدل `QTableWidgetItem` خام، نقل أزرار تعديل/حذف من أسفل الجدول لهيدره، حذف `_refresh_style` اليدوي بالكامل (يتكفل به `BaseListPanel`/`refresh_table_styles` مركزيًا)، مع الحفاظ الكامل على توقيع الـ API الخارجي `(conn, on_edit, on_delete, on_select)`.

---

## 10. `ui/tabs/pricing/offers/offers_tab.py`

**الغرض:** الـ Widget الرئيسي لتبويب "العروض" بالكامل — يجمع فورم العرض (`_OfferForm`) فوق splitter أفقي يحوي جدول العروض (`_OffersTable`) وتفاصيل العرض المختار (`_OfferDetails`)، بالإضافة لتاب فرعي لإدارة تصنيفات العروض.

**الـ imports الخارجية المهمة:**
- `services.pricing.offers_service` (`get_offer`, `remove_offer`).
- `ui.widgets.dialogs.confirm.confirm_delete` — نافذة تأكيد حذف موحّدة.
- `ui.widgets.managers.category.CategoryManager` — لإدارة تصنيفات العروض (scope="all").
- `ui.widgets.core.i18n.tr`.
- `ui.widgets.core.events.emit_company_data_changed`.
- `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.widgets.theme.layout_styles` (`tab_style`, `apply_tab_widths`, `normalize_tab_widget`).
- `ui.constants` (ثوابت أحجام splitters والتابات).
- `.offer_form._OfferForm`.
- `.offer_details._OfferDetails`.
- `.offers_table._OffersTable`.

**من يستدعي هذا الملف:** `pricing_section.py` (يستورد `OffersTab` من `.pricing.offers.offers_tab`).

### Class: `OffersTab(QWidget, WidgetMixin)`
- `__init__(self, parent=None)`: `_init_widget_mixin(theme=True, font=False, lang=True, data=False)`، `_build()`، `_refresh_style()`.
- `_live_conn(self)`: يرجع مباشرة `CompanyService.get_active_erp_conn()` (بدون فحص حيوية اتصال قديم — أبسط من النمط المستخدم في الملفات الأخرى).
- `_refresh_style(self, *_)`: يطبّق `tab_style()` و `apply_tab_widths` على `_tabs_widget`. يبني ستايل مشترك لمقابض الـ splitters (`_splitter`, `_bottom_splitter`) بلون `border`/`border_light`، مع تمييز عند hover بلون `orange_bg`.
- `_refresh_lang(self, *_)`: يعيد ضبط نصوص التابين (منتجات العروض/تصنيفات العروض) عند تغيير اللغة، مع حارس `hasattr`. تعليق يوضح أن هذا إصلاح لخلل سابق: القسم لم يكن مسجلاً على `lang_changed` (كان `lang=False`) فيفضل بلغة قديمة.
- `_build(self)`: `QVBoxLayout` بلا حواف. ينشئ `tabs` (`QTabWidget` بعد `normalize_tab_widget`). التاب الأول (`main_widget`) يحوي:
  - `splitter` عمودي (`QSplitter(Qt.Vertical)`) يضيف: `self._form = _OfferForm(conn)` أعلاه، و `bottom` (splitter أفقي) أسفله يحوي `self._offers_table = _OffersTable(conn, on_edit=..., on_delete=..., on_select=self._show_details)` و `self._details = _OfferDetails(conn)`.
  - أحجام الـ splitters مضبوطة من ثوابت `OFFERS_TAB_*_SIZE`، مع `setCollapsible(0, True)` (يمكن طي الفورم بالكامل).
  التاب الثاني: `CategoryManager(conn, scope="all")` بعنوان "تصنيفات العروض".
- `_edit_offer(self, offer_id)`: إن لم يوجد `offer_id` يعرض رسالة تحذير "اختر أولاً"، وإلا يستدعي `self._form.load_offer(offer_id)`.
- `_delete_offer(self, offer_id)`: إن لم يوجد `offer_id` يعرض تحذيراً. وإلا يجلب بيانات العرض؛ إن لم يوجد يتوقف. عند تأكيد `confirm_delete`: إن كان العرض المحذوف هو نفسه الجاري تعديله في الفورم (`_form._editing_id == offer_id`) يستدعي `_form.reset()` أولاً، ثم `remove_offer`، `self._details.clear()`، `emit_company_data_changed()`.
- `_show_details(self, offer_id)`: يستدعي `self._details.load(offer_id)`.

**ثوابت/متغيرات مستوى الملف:** لا يوجد.

---

## قسم علاقات الملفات

**تسلسل الاستدعاء الكامل (من الأعلى للأسفل):**
```
pricing_section.py
 ├─ pricing_tab.py (PricingTab)
 │   └─ pricing/_pricing_panel.py (_PricingPanel)
 │       ├─ pricing/_stat_box.py (stat_box)
 │       └─ pricing/_pricing_table.py (_PricingTable)
 └─ offers/offers_tab.py (OffersTab)
     ├─ offers/offer_form.py (_OfferForm)
     │   ├─ offers/offer_item_row.py (_OfferItemRow)
     │   └─ pricing/_stat_box.py (stat_box)  ← تبعية عابرة للمجلد الفرعي
     ├─ offers/offers_table.py (_OffersTable)
     └─ offers/offer_details.py (_OfferDetails)
         └─ pricing/_stat_box.py (stat_box)
```

**نمط بناء مشترك:**
- كل الجداول (`_PricingTable`, `_OffersTable`) ترث من `BaseListPanel` (خارج هذا المسار، من `ui/widgets/base/list_panel.py`) وتتبع نمطاً موحّداً: `COLUMNS`, `STRETCH_COL = -1`, `_load_rows`, `_match_filter`, `_fill_row`, `_build_extra_header_actions`، بدل بناء `QTableWidget` يدوي.
- `offer_details.py` يستخدم نمط جدول splitter مختلف (`make_splitter_table_guarded` + `refresh_table_styles` + `fit_splitter_table` مباشرة من `ui.widgets.tables.tables`) لأنه جدول عرض فقط (read-only) لا يرث `BaseListPanel`.
- كل بطاقات الإحصائيات في الثلاث فورمات (`_pricing_panel.py`, `offer_form.py`, `offer_details.py`) تُبنى حصرياً عبر `stat_box()` من `pricing/_stat_box.py` — لا يوجد بناء بطاقات يدوي منفصل.
- كل الـ Widgets الرئيسية (`PricingSection`, `PricingTab`, `_PricingPanel`, `_OfferForm`, `_OfferDetails`, `OffersTab`) ترث `WidgetMixin` وتوفر `_refresh_style`/`_refresh_lang`/`_refresh_data` بحسب الحاجة، بدل الاستماع اليدوي لإشارات bus مباشرة.
- نمط "اتصال صالح دائمًا" (`_live_conn`) يتكرر في `_PricingPanel` (ضمنيًا عبر `_load_for_edit` وغيرها لا تستخدمه مباشرة لكن الملفات الأخرى تستخدمه)، `_OfferItemRow`, `_OfferForm`, `_OfferDetails`, `_OffersTable` — فحص `CompanyService.is_conn_alive` ثم fallback لـ `get_active_erp_conn()`. `OffersTab` يستثنى من هذا النمط ويستخدم `get_active_erp_conn()` مباشرة بدون فحص حيوية.

**تبعيات خارج هذا المسار (بدون تفصيل محتواها):**
- `services.pricing.pricing_service`, `services.pricing.offers_service` (منطق الخدمة/DB).
- `models.costing.calc_cost` (حساب التكلفة).
- `ui.widgets.base.list_panel.BaseListPanel`.
- `ui.widgets.tables.tables` (أدوات جدول splitter موحّدة).
- `ui.widgets.core.widget_mixin.WidgetMixin`, `ui.widgets.core.i18n.tr`, `ui.widgets.core.events.emit_company_data_changed`.
- `ui.widgets.panels.themed_inputs` (`ThemedFrame`, `ThemedComboBox`, `ThemedLineEdit`).
- `ui.widgets.managers.category.CategoryManager`, `ui.widgets.combo.category.CategoryCombo`.
- `ui.widgets.dialogs.confirm.confirm_delete`.
- `ui.widgets.components.button` (`make_btn`, `refresh_visible_buttons`).
- `ui.widgets.panels.form_labels.section_title`.
- `ui.widgets.theme.layout_styles` (`tab_style`, `apply_tab_widths`, `normalize_tab_widget`).
- `ui.tabs.costing.shared.scenario_comparison_widget.ScenarioComparisonWidget` (من مسار `costing`، خارج نطاق هذا المرجع).
- `ui.theme._C`, `ui.font` (ثوابت الألوان/الخطوط).
- `ui.constants` (كل ثوابت الأبعاد/التباعد المستخدمة).
- `services.companies.company_service.CompanyService` (لإدارة اتصال قاعدة البيانات النشط).
