# ملف مرجعي: `ui/tabs/design_section.py` + `ui/tabs/design/**`

> يغطي هذا المرجع (بطلب صريح من المستخدم بدمج المسارين):
> - `ui/tabs/design_section.py` (ملف مفرد)
> - كل ملفات `ui/tabs/design/` وفروعها الفرعية (`designs/`, `dimension_sets/`, وما تحتها)
>
> **إجمالي الملفات المُغطاة: 23** — جميعها مطابقة لـ `system_arch.txt` بتاريخ التوليد `2026-07-17 10:31:26`.

---

## 1. `ui/tabs/design_section.py`

**الغرض:** نقطة الدخول الرئيسية لقسم "التصميمات" بالكامل. يبني هيدر القسم + `QTabWidget` يحتوي تبويبين فرعيين: "المقاسات" (`DimensionSetsTab`) و"التصميمات" (`DesignsTab`)، ويدير اتصال قاعدة بيانات التصميمات المستقلة.

**الـ imports الداخلية المهمة:**
- `services.design.get_designs_conn_and_init` — ينشئ/يفتح اتصال قاعدة بيانات التصميمات ويهيئها.
- `ui.widgets.theme.layout_styles` (`tab_style`, `apply_tab_widths`, `normalize_tab_widget`) — تنسيق موحّد للتبويبات.
- `.design.dimension_sets_tab.DimensionSetsTab`
- `.design.designs_tab.DesignsTab`

**من يستدعي هذا الملف:** `ui/main_window.py` — يبنيه كقسم تنقل رئيسي (مؤكَّد من بنية `main_window_helper/_sidebar.py`).

### Class: `DesignSection(QWidget, WidgetMixin)`
- **`__init__(self, parent=None)`**: يفتح اتصال قاعدة بيانات التصميمات عبر `get_designs_conn_and_init()`, يبني الواجهة، ويفعّل `WidgetMixin` بـ `theme=True, font=True, lang=True, data=False`.
- **`_build(self)`**: ينشئ Layout رأسي يحوي: Label هيدر ثابت الارتفاع (`SECTION_HEADER_HEIGHT`) بعنوان القسم، ثم `QTabWidget` مطبَّع (`normalize_tab_widget`) يضم تبويب `DimensionSetsTab` وتبويب `DesignsTab`، ويربط `currentChanged` بـ `_on_tab_changed`.
- **`_on_tab_changed(self, index)`**: إذا كان الـ index = 1 (تبويب "التصميمات")، ينفّذ `self._designs_tab.refresh()` لإعادة تحميل أي مجموعات مقاسات جديدة.
- **`_refresh_style(self, *_)`**: يعيد تلوين الهيدر (خلفية، حدود سفلية، لون نص بنفسجي `_C['purple']`) وإعادة تطبيق `tab_style()` و`apply_tab_widths()` على `_tabs` إن وُجدت.
- **`_refresh_lang(self, *_)`**: يحدّث نص الهيدر وأسماء التبويبين عبر `tr()` عند تبديل اللغة حياً؛ ملاحظة كود: تعليق صريح يوثّق أن هذه الدالة أُضيفت لإصلاح مشكلة أن القسم لم يكن مسجَّلاً على `bus.lang_changed` (`lang=False` سابقاً) فكانت النصوص تفشل في التحديث اللحظي.
- **`closeEvent(self, event)`**: يغلق اتصال قاعدة البيانات (`self.conn.close()`) بأمان داخل `try/except`، ثم يستدعي `super().closeEvent`.

**لا توجد class-level attributes أو signals مُعرَّفة في هذا الملف بخلاف ما يرثه من `WidgetMixin`.**

**ملاحظات كود مهمة:** تعليق رأس الملف يوثّق أن هذا "تحديث لتوحيد القسم مع باقي الأقسام" — نصوص عبر `tr()`، ألوان عبر `_C`، خط عبر `font.py`، وتحديث ديناميكي للثيم عبر `bus.theme_changed`.

---

## 2. `ui/tabs/design/design_styles.py`

**الغرض:** طبقة أنماط CSS/QSS مركزية وديناميكية لكل وحدة التصميمات — توفّر كائن `_Styles` بخصائص ألوان حية (تُقرأ من `_C` في كل استدعاء وليس مرة واحدة) ودوال تُرجع stylesheet strings جاهزة للأزرار، الحقول، الليبلز، والـ badges.

**الـ imports الداخلية المهمة:**
- `ui.font` (`get_font_size`, `fs`) — لحساب أحجام الخطوط النسبية.
- `ui.theme._C as APP_COLORS` — مصدر الألوان (مستورد لكنه غير مستخدم مباشرة؛ الاستخدام الفعلي عبر `from ui.theme import _C` داخل كل property).
- `ui.constants` — عشرات الثوابت الخاصة بالـ padding/radius/spacing.

**من يستدعي هذا الملف:** `_design_detail_panel.py` (عبر `get_styles()`) و`_designs_categories_panel.py` (عبر `get_styles()`) — مؤكَّد من المرفقات الحالية.

### Class: `_Styles`
- **class attributes ثابتة:** `RADIUS`, `RADIUS_SM`, `RADIUS_XS` (قيم نصية جاهزة بوحدة `px` من الثوابت).
- **Properties ديناميكية (كل واحدة تقرأ `_C` حياً عند كل نداء):** `BG`, `BG_SURFACE`, `BG_HOVER`, `BORDER`, `BORDER_MED`, `TEXT_PRI`, `TEXT_SEC`, `TEXT_MUT`, `ACCENT`, `ACCENT_LT`, `ACCENT_BDR`, `ACCENT_DARK`, `ACCENT_TEXT`, `BTN_PRIMARY_TEXT`, `SUCCESS`, `SUCCESS_LT`, `SUCCESS_BDR`, `SUCCESS_HOVER_BG`, `DANGER`, `DANGER_LT`, `DANGER_BDR`, `DANGER_HOVER_BG`, `WARNING`. كل property تُرجع مباشرة قيمة معادلة من `_C[...]`.
- **`__init__(self, base: int)`**: يحسب أحجام خط نسبية (`tiny`, `small`, `normal`, `large`, `xlarge`) بالاعتماد على `fs(base, offset)`.
- **`_h(self, override=None) -> int`**: يرجع ارتفاعاً قياسياً للعناصر = `override` إن وُجد، وإلا `normal*2 + STYLES_BTN_HEIGHT_PAD`.
- **`label_header/label_section/label_field/label_secondary/label_muted(self) -> str`**: كل دالة تُرجع stylesheet نصي لنوع Label مختلف (حجم خط، وزن، لون) حسب الاستخدام (عنوان رئيسي، قسم، حقل، ثانوي، باهت).
- **`badge_accent(self) -> str` / `badge_count(self) -> str`**: stylesheet لشارات نصية (accent عام / شارة عدّاد بحد أدنى للعرض).
- **`btn(self, bg, fg, bdr, hover_bg, height=None, radius=None) -> str`**: زر عام بألوان مخصصة بالكامل.
- **`btn_primary(self, height=None) -> str`**: زر أساسي بلون accent، يشمل حالة `disabled`.
- **`btn_ghost(self, height=None) -> str`**: زر شفاف بحدود accent.
- **`btn_success(self, height=None) -> str`** / **`btn_danger(self, height=None) -> str`**: أزرار بألوان نجاح/خطر.
- **`input_field(self, height=None) -> str`** / **`input_search(self, height=None) -> str`**: stylesheet لحقول الإدخال العادية وحقول البحث (خلفية مختلفة عن الحقل العادي).
- **`combo_field(self, height=None) -> str`**: stylesheet لـ `QComboBox` يشمل `drop-down`.

### دالة top-level: `get_styles() -> _Styles`
تُرجع كائن `_Styles` جديد بحجم الخط الحالي المُستخرَج من `get_font_size()`.

**ملاحظات كود مهمة:** تعليق موسّع داخل الـ docstring يوثّق سبب تحويل الألوان من class attributes ثابتة إلى `@property`: القيم الثابتة كانت تُحسب مرة واحدة فقط وقت أول `import` وتتجمّد على ثيم تلك اللحظة، فكان أي `theme_manager.set_theme()` لاحق يُتجاهَل تماماً. هذا [إصلاح dark-theme] جذري يمنع "تجمّد" الألوان.

---

## 3. `ui/tabs/design/designs_tab.py`

**الغرض:** تبويب "التصميمات" (v2) — يبني تخطيطاً من 3 أعمدة: يسار (تصنيفات التصميمات)، وسط (كروت التصميمات ضمن Splitter)، يمين (لوحة تفاصيل التصميم + إضافة مقاسات)، ويربط كل الإشارات (signals) بينها.

**الـ imports الداخلية المهمة:**
- `.designs._designs_table._DesignsTable` — عمود الوسط (كروت Grid).
- `.designs._design_detail_panel._DesignDetailPanel` — عمود اليمين.
- `.designs._designs_categories_panel.DesignsCategoriesPanel` — Sidebar التصنيفات.
- `ui.widgets.panels.themed_inputs.ThemedFrame` — للفاصل العمودي (`VLine`).

**من يستدعي هذا الملف:** `design_section.py` (مؤكَّد — يستورد `DesignsTab` مباشرة).

### Class: `DesignsTab(QWidget, WidgetMixin)`
- **`__init__(self, conn, parent=None)`**: يخزّن `conn`، يبني الواجهة، يفعّل `WidgetMixin` بـ `lang=False, data=False`.
- **`_build(self)`**: يبني `_cats_panel` (Sidebar)، ثم `QSplitter` أفقي يحوي `_table` (`_DesignsTable`) و`_detail` (`_DesignDetailPanel`؛ يُبنى أولاً لأن `_DesignsTable` يحتاجه في الـ constructor). يربط الإشارات التالية:
  - `_detail.saved → self._on_detail_saved`
  - `_detail.cleared → self._table.refresh`
  - `_table.design_deleted → self._table.refresh`
  - `_table.set_filter_changed → self._detail.filter_by_set`
  - `_cats_panel.category_changed → self._on_category_changed`
  - `_detail.connect_categories_panel(self._cats_panel)` — ربط تحديث combo التصنيف في لوحة التفاصيل تلقائياً عند تغيّر تصنيفات الـ sidebar.
  - يضبط أحجام الـ splitter عبر `DESIGNS_TAB_SPLITTER_LIST_W` / `DESIGNS_TAB_SPLITTER_DETAIL_W`، ويمنع الطي (`setCollapsible(x, False)`).
  - يرتّب: `_cats_panel` ثم فاصل عمودي (`_sep`) ثم الـ `splitter` بامتداد (`stretch=1`).
- **`_on_category_changed(self, cat_id)`**: يستدعي `self._table.filter_by_category(cat_id)`.
- **`_on_detail_saved(self)`**: بعد حفظ تصميم، يحدّث كلاً من `_table.refresh()` و`_cats_panel.refresh()`.
- **`refresh(self)`**: يحدّث `_table`، ويعيد تحميل تصنيفات `_detail` (`_reload_categories`)، ويحدّث `_cats_panel`.
- **`_refresh_style(self, *_)`**: يلوّن حدود الـ `_splitter` (hover بلون `accent_mid`) ولون الفاصل العمودي `_sep`.

**لا توجد signals مُعرَّفة على مستوى هذا الـ class نفسه (يعتمد على إشارات الأبناء).**

---

## 4. `ui/tabs/design/dimension_sets_tab.py`

**الغرض:** تبويب إدارة مجموعات المقاسات — يحتوي تبويبين داخليين: "إدخال المقاسات" (`_ValuesPanel`) و"المجموعات" (`_GroupsPanel`)، ويربط تحديث قائمة المجموعات بين الاثنين.

**الـ imports الداخلية المهمة:**
- `.dimension_sets._values_panel._ValuesPanel`
- `.dimension_sets._groups_panel._GroupsPanel`
- `ui.widgets.theme.layout_styles` (`tab_style`, `apply_tab_widths`, `normalize_tab_widget`)

**من يستدعي هذا الملف:** `design_section.py` (مؤكَّد — يستورد `DimensionSetsTab` مباشرة).

### Class: `DimensionSetsTab(QWidget, WidgetMixin)`
- **`__init__(self, conn, parent=None)`**: يبني الواجهة، ثم يفعّل `WidgetMixin` بـ `theme=True, font=False, lang=True, data=False` صراحةً (تعليق كود يوضح أن هذا "طبقة أمان إضافية" لضمان التسجيل على `bus.lang_changed` بغض النظر عن الـ default)، ثم ينادي `_refresh_lang()` يدوياً فوراً.
- **`_build(self)`**: ينشئ `QTabWidget` داخلي (`_inner_tabs`) مطبَّع، يضيف تبويب "إدخال المقاسات" (`_values_panel = _ValuesPanel(conn)`) وتبويب "المجموعات" (`_groups_panel = _GroupsPanel(conn)`). يربط:
  - `_groups_panel.sets_changed → self._values_panel._sets_list.refresh`
  - `_groups_panel._cats_panel.changed → self._values_panel._sets_list.refresh`
  - `inner_tabs.currentChanged → self._on_tab_changed`
- **`_on_tab_changed(self, index)`**: إذا `index == 1` (تبويب المجموعات)، يستدعي `self._groups_panel.refresh()`.
- **`_refresh_style(self, *_)`**: يعيد تطبيق `tab_style()` و`apply_tab_widths()` على `_inner_tabs`.
- **`_refresh_lang(self, *_)`**: يحدّث نصوص التبويبين الداخليين عبر `tr()` باستخدام `indexOf()` لتحديد الفهرس الصحيح لكل تبويب.

---

## 5. `ui/tabs/design/designs/designs_categories/_row_and_form.py`

**الغرض:** ملف فرعي يوفّر مكونين مُعاد استخدامهما من `_designs_categories_panel.py`: `_CatRow` (صف عرض تصنيف واحد شجري في الـ Sidebar) و`_CatForm` (فورم إضافة/تعديل تصنيف كامل مستقل بذاته).

**الـ imports الداخلية المهمة:**
- `services.design.get_design_service`
- `ui.widgets.core.widget_mixin.WidgetMixin`

**من يستدعي هذا الملف:** `../_designs_categories_panel.py` (مؤكَّد — يستورد `_btn_ss`, `_CatForm`, `_CatRow` الثلاثة معاً).

### دالة top-level: `_btn_ss(bg, fg, bdr, hover_bg, height=CAT_FORM_BTN_DEFAULT_H) -> str`
تُرجع QSS نصياً لزر عام بألوان/ارتفاع مخصص، تستورد `_C` و`FS_BASE` محلياً داخل الدالة نفسها (وليس على مستوى الملف) لضمان قراءة حية للثيم.

### Class: `_CatRow(ThemedFrame, WidgetMixin)`
**Signal:** `clicked = pyqtSignal(object)`

- **`__init__(self, cat_id, name, color, count=0, depth=0, parent=None)`**: يخزّن `cat_id`, `_selected=False`, `_cat_color`, يضبط المؤشر وارتفاعاً أدنى، يبني Layout أفقي بمسافة بادئة تتناسب مع `depth` (`CAT_ROW_DEPTH_INDENT`). إن كان `depth > 0` يضيف "خط ربط" بصري (`_indent_line`) قبل باقي المحتوى. يضيف: نقطة لونية (`_dot`)، ليبل الاسم (`_lbl`)، وشارة عداد (`_badge`، تظهر فقط إن `count > 0`).
- **`set_selected(self, s: bool)`**: يحدّث `_selected` ويعيد تطبيق الستايل.
- **`_refresh_style(self, *_)`**: يبني ألوان ديناميكية من `_C`، يلوّن خط الربط (إن وُجد)، ثم يطبّق ستايل مختلف بالكامل حسب حالة `_selected`: محدد = خلفية accent فاتحة + حد يسار سميك بلون accent + نص عريض بلون accent؛ غير محدد = شفاف مع hover، نص عادي بلون النص الأساسي، نقطة بلون التصنيف الفعلي (`_cat_color`) بدل الـ accent.
- **`mousePressEvent(self, e)`**: يُطلق `clicked(cat_id)` قبل `super()`.

### Class: `_CatForm(QWidget, WidgetMixin)`
**Signals:** `saved = pyqtSignal()`, `canceled = pyqtSignal()`

- **`__init__(self, conn, parent=None)`**: `_editing_id = None`, `_color = None` (يُحدَّث فعلياً داخل `_build`)، يبني الواجهة.
- **`_build(self)`**: عنوان وضع (`_mode_lbl`)، حقل اسم، ليبل + combo "التصنيف الأب" (`cmb_parent`)، صف لون (ليبل + معاينة مربعة + زر اختيار لون)، فاصل، صف أزرار إلغاء/حفظ.
- **`_refresh_style(self, *_)`**: يلوّن كل عناصر الفورم (عنوان الوضع، حقل الاسم مع حالة focus، الـ combo، أزرار الحفظ/الإلغاء بألوان accent/محايدة)، ثم يستدعي `_update_color_preview()`.
- **`_refresh_lang(self, *_)`**: يحدّث كل النصوص عبر `tr()` عند تبديل اللغة (فقط إن لم يكن في وضع تعديل نشط للعنوان تحديداً).
- **`_update_color_preview(self)`**: يلوّن مربع المعاينة باللون الحالي أو `accent` الافتراضي.
- **`_reload_parent(self, exclude_id=None)`**: يبني `cmb_parent` من شجرة `list_item_categories`/`build_tree`، يستبعد العقدة الجاري تعديلها وكل أحفادها (`get_descendants`) عبر مجموعة `excl`.
- **`_add_nodes(self, nodes, depth, excl)`**: تكرارية قياسية لبناء قائمة الشجرة بمسافات بادئة، تتجاهل العقد المستبعدة.
- **`_pick_color(self)`**: يفتح `QColorDialog`، يحدّث `_color` والمعاينة.
- **`load_new(self)`**: يصفّر الفورم بالكامل لوضع "إضافة جديد" (لون افتراضي = accent الحالي).
- **`load_edit(self, cat_id)`**: يجلب بيانات التصنيف (`get_item_category`)، يملأ الحقول، يحدد الأب الصحيح في `cmb_parent` بعد استبعاد الأحفاد.
- **`_save(self)`**: يتحقق من الاسم (وإلا `setFocus` بدون رسالة تحذير منبثقة)، يستدعي `update_item_category` أو `create_item_category` حسب الحالة، يُطلق `saved`؛ يلتقط `ValueError` ويعرضه كرسالة تحذير (`QMessageBox.warning`) — مصدر مرجّح لهذا الخطأ: تكرار اسم تصنيف.

---

## 6. `ui/tabs/design/designs/_design_detail_panel.py`

**الغرض:** لوحة تفاصيل التصميم (يمين تبويب التصميمات) — تعرض/تحرر بيانات تصميم واحد (اسم، تصنيف، ملاحظات) وتدير قائمة "المقاسات" المرتبطة به عبر كروت `_SizeCard`، مع دعم فلترة المقاسات حسب مجموعة مقاسات محددة.

**الـ imports الداخلية المهمة:**
- `services.design.get_design_service`, `get_design_size_service`
- `._size_card._SizeCard` — كارت عرض مقاس واحد.
- `._size_dialog._SizeDialog` — Dialog إضافة/تعديل مقاس.
- `ui.tabs.design.design_styles.get_styles` — مصدر كل الـ stylesheets المستخدمة هنا.

**من يستدعي هذا الملف:** `designs_tab.py` (مؤكَّد — يُنشئ `_DesignDetailPanel` ويمرره لـ `_DesignsTable`).

### Class: `_DesignDetailPanel(QWidget, WidgetMixin)`
**Signals:** `saved = pyqtSignal()`, `cleared = pyqtSignal()`

- **`__init__(self, conn, parent=None)`**: يهيّئ الخدمات (`_svc`, `_size_svc`)، `_design_id=None`، `_set_filter=None`، `_size_cards=[]`، يبني الواجهة، يحمّل التصنيفات (`_reload_categories`)، يفعّل `WidgetMixin(lang=False, data=False)`.
- **`_build(self)`**: يبني: هيدر (عنوان + badge حالة "جديد/محفوظ" + حقل اسم + صف تصنيف/ملاحظات + صف أزرار "جديد"/"حفظ")، ثم هيدر قسم المقاسات (عنوان + عداد badge + زر "إضافة مقاس")، ثم `QScrollArea` يحوي كروت المقاسات + حالة فارغة (Empty State) بأيقونة ورسالتين.
- **`connect_categories_panel(self, cats_panel)`**: يربط `cats_panel.category_changed` بإعادة تحميل قائمة التصنيفات محلياً — يبقيها متزامنة مع أي تعديل من الـ sidebar الخارجي.
- **`load_design(self, design_id: int)`**: يجلب بيانات التصميم من `_svc.get_design`، يملأ الحقول، يحدّث العنوان والـ badge لحالة "محفوظ"، يحدد التصنيف الصحيح في `cmb_cat`، وينادي `_load_sizes()`.
- **`reset(self)`**: يفرغ كل الحقول، يعيد العنوان لحالة "جديد"، يخفي الـ badge، يمسح كروت المقاسات، ويُطلق `cleared`.
- **`filter_by_set(self, set_id)`**: يخزّن `_set_filter` ويعيد تحميل المقاسات إن كان هناك تصميم محمَّل حالياً.
- **`_reload_categories(self)`**: يعيد بناء `cmb_cat` من شجرة التصنيفات (`build_tree`) مع حفظ الاختيار السابق إن أمكن.
- **`_add_cat_nodes(self, nodes, depth)`**: دالة تكرارية (recursive) تضيف عناصر الشجرة للـ combo مع مسافة بادئة (`indent`) وسهم (`arrow`) حسب العمق.
- **`_save(self)`**: يتحقق من وجود اسم (وإلا يلوّن الحقل بلون خطر ويعرض تحذير)، ثم يستدعي `update_design` أو `create_design` حسب الحالة، ويحدّث العنوان/الـ badge، ويُطلق `saved`.
- **`_load_sizes(self)`**: يمسح الكروت القديمة، يجلب `list_sizes(design_id)`، يفلترها حسب `_set_filter` إن كان محدداً، يحدّث عداد المقاسات وحالة الفراغ، ثم ينشئ `_SizeCard` لكل مقاس ويربط `edit_requested`, `delete_requested`, `path_changed`.
- **`_clear_size_cards(self)`**: يحذف كل كروت المقاسات الحالية من الـ layout ويظهر الحالة الفارغة.
- **`_add_size(self)`**: إذا لم يكن هناك `_design_id` بعد، يحفظ التصميم أولاً تلقائياً (بشرط وجود اسم)، ثم يفتح `_SizeDialog` كـ modal، وعند القبول يعيد تحميل المقاسات.
- **`_edit_size(self, size_id: int)`**: يجلب بيانات المقاس المحدد، يفتح `_SizeDialog` بوضع تعديل، ويحدّث القائمة عند القبول.
- **`_delete_size(self, size_id: int)`**: يعرض تأكيد حذف، وعند الموافقة يستدعي `_size_svc.delete_size` ويحدّث القائمة.
- **`_refresh_style(self, *_)`**: يطبّق كل stylesheets من `get_styles()` على كل العناصر (هيدر، أزرار، حقول، labels)، ويحدّث خلفيات الأطر الداخلية (`_hdr`, `_sizes_hdr`, `_sizes_scroll`, `_sizes_widget`) — تعليق كود يوثّق أن هذه كانت السبب المباشر في "المنطقة الفاتحة يسار تبويب التصميمات" قبل الإصلاح.

**module-level constants:** `_RADIUS_SM = "6px"`, `_RADIUS_XS = "4px"` (غير مستخدمة مباشرة داخل هذا الملف نفسه بشكل بارز، محجوزة كقيم احتياطية).

---

## 7. `ui/tabs/design/designs/_designs_categories_panel.py`

**الغرض:** لوحة جانبية (Sidebar) ثابتة العرض لعرض/إدارة تصنيفات التصميمات الشجرية (منفصلة عن تصنيفات مجموعات المقاسات)، مع بحث، فورم مدمج (Inline) لإضافة/تعديل، وأزرار حذف.

**الـ imports الداخلية المهمة:**
- `services.design.get_design_service`
- `ui.tabs.design.design_styles.get_styles`
- `.designs_categories._row_and_form` (`_btn_ss`, `_CatForm`, `_CatRow`) — عناصر الصف والفورم المُعاد استخدامها من ملف فرعي.

**من يستدعي هذا الملف:** `designs_tab.py` (مؤكَّد — يستورد `DesignsCategoriesPanel`).

### Class: `DesignsCategoriesPanel(QWidget, WidgetMixin)`
**Signals:** `category_changed = pyqtSignal(object)`

- **`__init__(self, conn, parent=None)`**: `_active_id = "ALL"`، `_items = []`، يبني الواجهة، يحمّل البيانات (`_load`)، يفعّل `WidgetMixin(lang=False, data=False)`.
- **`_build(self)`**: عرض ثابت (`DESIGN_CATS_SIDEBAR_W`). يبني: هيدر (عنوان + زر "+" دائري لإضافة)، شريط بحث (حقل + زر مسح)، `QScrollArea` لقائمة الصفوف الشجرية، شريط إجراءات سفلي (تعديل/حذف)، وفورم `_CatForm` مدمج مخفي افتراضياً.
- **`_load(self, query="")`**: يمسح كل الصفوف القديمة، يضيف صف "الكل" ثابت (`_CatRow(None, ...)`) ثم فاصل، ثم يبني الشجرة الفعلية عبر `_add_tree` بالاعتماد على `list_item_categories`, `build_tree`, `count_designs_per_category`. يفعّل/يعطّل أزرار تعديل/حذف حسب وجود اختيار فعلي (غير "ALL").
- **`_add_tree(self, nodes, depth, counts, query)`**: دالة تكرارية تبني صفوف `_CatRow` لكل عقدة، تحسب العدد الكلي للتصميمات شاملاً كل الأحفاد (`get_descendants` + جمع `counts`)، وتُخفي العقد التي لا تطابق نص البحث (إلا إذا كان لها أبناء).
- **`_on_search(self, text)`**: يعيد `_load` بنص البحث الجديد.
- **`_clear_search(self)`**: يفرّغ حقل البحث.
- **`_on_clicked(self, cat_id)`**: يحدّث `_active_id`، يعيد تلوين كل الصفوف حسب التحديد، يفعّل أزرار تعديل/حذف، ويُطلق `category_changed`.
- **`_show_add_form(self) / _show_edit_form(self)`**: يعرضان `_CatForm` في وضع إضافة/تعديل عبر `load_new()`/`load_edit(id)`.
- **`_on_form_saved(self)`**: يخفي الفورم، يعيد التحميل، ويُطلق `category_changed` بالتصنيف الحالي.
- **`_delete(self)`**: يحسب عدد الأحفاد والتصميمات المرتبطة، يعرض رسالة تأكيد تفصيلية، وعند الموافقة يحذف كل الأحفاد بترتيب عكسي (`sorted(desc, reverse=True)`) قبل حذف الأصل، ثم يعيد التعيين لـ "ALL".
- **`refresh(self)`**: يعيد `_load` بنص البحث الحالي.
- **`current_category_id(self)`**: يرجع `None` إذا كان `_active_id == "ALL"` وإلا يرجع القيمة الفعلية.
- **`_refresh_style(self, *_)`**: يعيد تلوين كل العناصر الثابتة والديناميكية، وتعليق كود يوثّق أن الصفوف والفاصل يُعاد تحميلهم بالكامل هنا (`_load`) لأنهم يتلوّنون فقط وقت الإنشاء.

---

## 8. `ui/tabs/design/designs/_designs_table.py`

**الغرض:** المنطقة الوسطى لتبويب التصميمات — تعرض التصميمات ككروت Grid قابلة للفلترة (بحث نصي + فلتر مجموعة مقاسات)، مع تحميل غير متزامن (Background Thread) لصور الـ thumbnails ومراقبة تغييرات ملفات XCF حياً.

**الـ imports الداخلية المهمة:**
- `services.design.get_design_size_service`, `get_design_service`
- `._xcf_thumbnail` (`get_watcher`, `clear_cache`) — مراقب ملفات XCF المشترك.
- `._design_detail_panel._DesignDetailPanel`
- `.designs_table._design_card` (`_DesignCard`, `_ThumbWorker`)

**من يستدعي هذا الملف:** `designs_tab.py` (مؤكَّد — يستورد `_DesignsTable` ويمرر له `_DesignDetailPanel`).

### دالة top-level: `_btn_ss(bg, fg, bdr, hover_bg, radius=_RADIUS_SM, height=INPUT_HEIGHT) -> str`
تُرجع QSS نصي لزر عام بألوان/أبعاد مخصصة، تعتمد داخلياً على `get_font_size()`.

### Class: `_DesignsTable(QWidget, WidgetMixin)`
**Signals:** `design_selected = pyqtSignal(int)`, `design_deleted = pyqtSignal()`, `set_filter_changed = pyqtSignal(object)`

- **`__init__(self, conn, detail_panel, parent=None)`**: يهيّئ الخدمات، قواميس التتبع (`_cards`, `_workers`, `_xcf_card_map`)، حالة الفلاتر (`_cat_filter`, `_set_filter`)، مؤقّت بحث مؤجَّل (`_search_timer` بـ `DESIGNS_TABLE_SEARCH_DELAY`)، يربط `get_watcher().file_changed → self._on_xcf_changed`، يبني الواجهة ويحمّل البيانات.
- **`_build(self)`**: يبني Toolbar (صف بحث+زر جديد، وصف فلتر مجموعة+عداد+زر Reset)، ثم `QScrollArea` بشبكة (`QGridLayout`) للكروت، ثم إطار "حالة فارغة" (أيقونة + رسالتان قابلتان للتغيير حسب وجود فلاتر نشطة).
- **`_reload_set_combo(self)`**: يعيد تحميل قائمة مجموعات المقاسات في `cmb_set` مع حفظ الاختيار السابق.
- **`_load(self)`**: يعيد تحميل الـ combo ثم يطبّق الفلتر.
- **`_on_set_changed(self)`**: يحدّث `_set_filter`، يطبّق فلترة كاملة (لإعادة حساب `first_xcf` عبر SQL)، ويُطلق `set_filter_changed`.
- **`filter_by_category(self, cat_id)`**: يُستدعى من `DesignsCategoriesPanel` — يحدّث `_cat_filter` ويطبّق الفلترة.
- **`_apply_filter(self)`**: يوقف الـ workers القديمة، يوقف مراقبة ملفات XCF القديمة، يجلب `list_designs_filtered(name_q, cat_filter, set_filter)`، يحذف كل الكروت القديمة، يتعامل مع حالة النتائج الفارغة (برسائل مختلفة حسب وجود فلاتر أم لا)، ثم يبني الكروت الجديدة في شبكة (يحسب `cols` ديناميكياً حسب عرض النافذة)، ولكل كارت: يبدأ `_ThumbWorker` لتحميل الصورة في الخلفية إن وُجد ملف XCF صالح، ويسجّله في `watcher`.
- **`_on_thumb_ready(self, xcf_path, pixmap)`**: يحدّث صورة الكارت المطابق بعد انتهاء التحميل غير المتزامن.
- **`_on_xcf_changed(self, path)`**: عند تغيّر ملف XCF مراقَب، يمسح الكاش ويعيد تشغيل `_ThumbWorker` له.
- **`_on_card_selected(self, did)`**: يلغي تحديد الكارت السابق، يحدد الكارت الجديد، يحمّل تفاصيله في `_panel`، ويُطلق `design_selected`.
- **`_new_design(self)`**: يلغي أي تحديد حالي ويستدعي `_panel.reset()`.
- **`_reset_filters(self)`**: يفرّغ حقل البحث ويعيد `cmb_set` لأول عنصر، يصفّر `_set_filter`، يطبّق الفلترة، ويُطلق `set_filter_changed(None)`.
- **`resizeEvent(self, event)`**: يجدول إعادة توزيع الشبكة (`_reflow_grid`) بعد تأخير (`DESIGNS_TABLE_REFLOW_DELAY`) لتفادي إعادة الحساب المتكررة أثناء السحب.
- **`_reflow_grid(self)`**: يعيد ترتيب الكروت الموجودة فعلياً في شبكة جديدة بعدد أعمدة محسوب من العرض الحالي دون إعادة الجلب من قاعدة البيانات.
- **`refresh(self)`**: يعيد `_load()`.
- **`selected_id(self)`**: يرجع `_active_did`.
- **`_refresh_style(self, *_)`**: تلوين شامل للـ toolbar، حقول البحث، الأزرار، الـ combo، عداد النتائج، حالة الفراغ، وخلفيات الأطر الداخلية (`_toolbar`, `_scroll`, `_grid_widget`, `_empty_frame`) — بنفس نمط "إصلاح dark-theme" الموثّق في باقي ملفات الوحدة.

**module-level constant:** `_RADIUS_SM = f"{INPUT_BORDER_RADIUS}px"`.

---

## 9. `ui/tabs/design/designs/designs_table/_design_card.py`

**الغرض:** يعرّف كارت عرض تصميم واحد ضمن شبكة `_DesignsTable` (v3) — يحمّل الـ thumbnail في خلفية منفصلة (Thread)، يعرض اسم التصميم، تصنيفه، وشارة حالة ملفات المقاسات (كامل/جزئي/بلا ملفات)، ويدعم تحديث فلتر المجموعة حياً لإعادة حساب الـ thumbnail المعروض.

**الـ imports الداخلية المهمة:**
- `services.design.get_design_service`
- `..._xcf_thumbnail.get_xcf_thumbnail` (من مسارين للأعلى — `designs/_xcf_thumbnail.py`)

**من يستدعي هذا الملف:** `../_designs_table.py` (مؤكَّد — يستورد `_DesignCard` و`_ThumbWorker` معاً).

### Class: `_ThumbWorker(QThread)`
**Signal:** `done = Signal(str, object)` (xcf_path, `QPixmap` أو `None`)

- **`__init__(self, xcf_path: str, size: int = _CARD_THUMB)`**: يخزّن المسار والحجم.
- **`run(self)`**: ينفّذ `get_xcf_thumbnail` داخل `try/except` (لتفادي كسر الـ Thread عند أي خطأ غير متوقع)، ويُطلق `done` بالنتيجة (أو `None` عند الفشل).

### Class: `_DesignCard(ThemedFrame, WidgetMixin)`
**Signals:** `selected = pyqtSignal(int)`, `deleted = pyqtSignal(int)`

- **`__init__(self, conn, design_data, set_id=None, parent=None)`**: يخزّن نسخة من بيانات التصميم (`dict(design_data)`)، `_did`, `_set_id`, `_selected=False`, `_worker=None`، يضبط عرضاً ثابتاً (`_CARD_W`)، يبني الواجهة.
- **`_refresh_style(self, *_)`**: يعيد بناء ستايل الكارت (`_update_style`)، خط اسم التصميم، ستايل إطار الـ thumbnail، وستايل ليبل الـ thumbnail — كل هذا عند تغيّر الثيم/الخط.
- **`_apply_name_font(self, size=None)`**: يبني `QFont` جديداً بحجم `fs(size,-2)` ووزن `Medium` لاسم التصميم.
- **`_apply_thumb_style(self)`**: يلوّن إطار الـ thumbnail بخلفية وحواف علوية مدوّرة فقط (لتتناسق مع باقي الكارت).
- **`_apply_thumb_lbl_style(self)`**: يلوّن ليبل الـ thumbnail (شفاف، لون نص باهت لحالة placeholder).
- **`_apply_badge_style(self, badge)`**: يلوّن شارة عدد المقاسات (خلفية accent، نص بلون خلفية الحقل، دائرية).
- **`_build(self)`**: يبني: إطار thumbnail بحجم ثابت (مع ليبل placeholder نصي افتراضياً)، شارة عدد المقاسات فوقه (`QLabel` بأبعاد مطلقة عبر `setGeometry` إن كان `sizes_count > 0`)، ثم قسم معلومات: اسم (Wrap)، تصنيف (إن وُجد)، وسطر حالة ملفات ملوّن حسب النسبة (أخضر=الكل موجود، أصفر=جزئي، رمادي=لا ملفات) — يظهر فقط إن كان `sizes_count > 0`.
- **`set_thumbnail(self, pixmap)`**: يعرض الصورة المصغّرة (بعد `scale` بـ `KeepAspectRatioByExpanding`) أو يعيد نص الـ placeholder إن كانت `None`/فارغة.
- **`load_thumbnail(self, xcf_path=None)`**: إن لم يُمرَّر مسار، يحسبه من الخدمة (`get_first_xcf_for_design(did, _set_id)`)؛ إن لم يوجد ملف صالح على القرص يعرض placeholder مباشرة؛ وإلا يوقف أي Worker سابق قيد التشغيل ثم يبدأ `_ThumbWorker` جديداً.
- **`update_set_filter(self, set_id)`**: يُستدعى عند تغيّر فلتر المجموعة خارجياً — يحدّث `_set_id` ويعيد تحميل الـ thumbnail (لأن أول ملف XCF مرتبط قد يختلف باختلاف المجموعة المفلترة).
- **`set_selected(self, sel: bool)`**: يحدّث `_selected` ويعيد `_update_style()`.
- **`_update_style(self)`**: يبني ستايل الإطار الخارجي بالكامل حسب `_selected` (محدد = خلفية accent فاتحة + حد accent سميك 2px؛ غير محدد = خلفية عادية + حد رفيع + hover).
- **`mousePressEvent(self, event)`**: يُطلق `selected(_did)` قبل `super()`.

**module-level constants:** `_CARD_W`, `_CARD_THUMB`, `_RADIUS`, `_RADIUS_SM` — كلها أسماء مختصرة مأخوذة مباشرة من ثوابت `ui.constants` (`DESIGN_CARD_*`) لتسهيل القراءة داخل الملف.

---

## 10. `ui/tabs/design/designs/size_card/helper.py`

**الغرض:** ملف مساعد (v3) يحوي كل منطق GIMP الفعلي (البحث عن تنفيذي GIMP، فتحه، إنشاء كانفاس جديد)، تحويلات الوحدات إلى بكسل، وWidget مستقل لعرض الـ thumbnail (`_ThumbnailWidget`) — يُستخدم بالكامل من `_size_card.py` لفصل منطق "الحساب/التشغيل الخارجي" عن منطق "عرض الكارت".

**الـ imports الداخلية المهمة:**
- `..._xcf_thumbnail.get_xcf_thumbnail` (من `designs/_xcf_thumbnail.py`)
- `ui.widgets.core.widget_mixin.WidgetMixin`
- استيراد مشروط داخل الدوال: `services.shared.item_service.ItemService` (خارج نطاق هذا المرجع — للحصول على مسار GIMP المحفوظ من الإعدادات)

**من يستدعي هذا الملف:** `../_size_card.py` (مؤكَّد — يستورد `_ThumbnailWidget`, `_to_px`, `_unit_for_set`, `_btn_ss`, `_open_gimp`).

### دالة top-level: `_btn_ss(bg, fg, bdr, hover_bg, height=SIZE_CARD_BTN_HEIGHT, radius=SIZE_CARD_BTN_RADIUS) -> str`
QSS نصي عام لزر مخصص الألوان/الأبعاد.

### Class: `_ThumbWorker(QThread)`
**Signal:** `done = Signal(object)`

- **`__init__(self, xcf_path: str, size: int = _THUMB_SIZE)`**: يخزّن المسار والحجم.
- **`run(self)`**: ينفّذ `get_xcf_thumbnail` ويُطلق `done` بالنتيجة (بدون `try/except` هنا، بخلاف `_ThumbWorker` في `_design_card.py`).

### دالة top-level: `_to_px(value: float, unit: str, dpi: float = _DEFAULT_DPI) -> int`
تحويل قيمة رقمية بوحدة (`px`, `mm`, `cm`, `m`/"متر", `inch`/`in`/"انش"/"بوصة") إلى بكسل حسب الـ DPI، بحد أدنى دائماً 1 بكسل.

### دالة top-level: `_unit_for_set(conn, set_id: int) -> str`
يستعلم مباشرة عن `default_unit` لمجموعة مقاسات معينة من جدول `dimension_sets`؛ يرجع `"px"` كـ fallback آمن عند أي خطأ أو عدم وجود قيمة.

### دالة top-level: `_find_gimp() -> str | None`
يبحث عن تنفيذي GIMP بالترتيب: مسار محفوظ مسبقاً في الإعدادات (`ItemService.get_gimp_path()`) → أسماء شائعة في `PATH` (`gimp`, `gimp-2.10`, `gimp-2.99`, `gimp-3.0`) → مسارات Windows الثابتة المعروفة (Program Files وx86) عبر `glob`، مع اختيار آخر تطابق مُرتَّب أبجدياً (يُفترض أنه الأحدث إصداراً).

### دالة top-level: `_open_gimp(xcf_path=None, width_val=None, height_val=None, unit="px", dpi=_DEFAULT_DPI) -> bool`
منطق مركزي لثلاث حالات: (1) فتح ملف XCF موجود مباشرة إن كان `xcf_path` صالحاً، (2) إنشاء صورة PNG شفافة مؤقتة بأبعاد محسوبة من `width_val`/`height_val`/`unit`/`dpi` عبر `PIL.Image` ثم فتحها بـ GIMP (يستخدم DPI الشاشة الفعلي إن كانت الوحدة `px`)، (3) فتح GIMP فارغاً كـ fallback أخير. يعرض `QMessageBox` عند عدم إيجاد GIMP أو فشل استيراد `Pillow` أو أي استثناء عام أثناء `subprocess.Popen`.

### Class: `_ThumbnailWidget(QLabel, WidgetMixin)`
- **`__init__(self, xcf_path: str, size: int = _THUMB_SIZE, parent=None)`**: `_thumb_loaded=False`, `_thumb_pixmap=None`, يضبط حجماً ثابتاً ومحاذاة مركزية، يعرض placeholder فوراً، ثم يبدأ تحميلاً غير متزامن إن كان الملف موجوداً فعلياً.
- **`_refresh_style(self, *_)`**: يبدّل الستايل حسب حالة التحميل الحالية: صورة محمَّلة بنجاح = خلفية + حد accent + زوايا مدورة؛ محمَّلة لكن فارغة (لا صورة) = حدود متقطعة (dashed) بلون محايد؛ لم تُحمَّل بعد = يستدعي `_show_placeholder()`.
- **`_show_placeholder(self)`**: يعرض أيقونة placeholder نصية بستايل بسيط.
- **`_load_async(self, path: str)`**: يبدأ `_ThumbWorker` جديداً ويربط `done → _on_thumb_ready`.
- **`_on_thumb_ready(self, pixmap)`**: يحدّث `_thumb_loaded=True` و`_thumb_pixmap`؛ إن كانت الصورة صالحة يعرضها مُصغَّرة (`KeepAspectRatioByExpanding`) بستايل النجاح؛ وإلا يعرض أيقونة "لا يوجد ملف" بستايل الحدود المتقطعة.
- **`refresh(self, xcf_path: str = None)`**: يمسح الكاش الخاص بالمسار (`clear_cache`)، يعيد ضبط `_xcf_path` إن مُرِّر مسار جديد، يعرض placeholder فوراً، ثم يعيد التحميل غير المتزامن إن كان الملف موجوداً — يُستخدم عند ربط ملف جديد أو عند اكتشاف تغيّر في الملف عبر المراقب.

**module-level constants:** `_DEFAULT_DPI = SIZE_CARD_DEFAULT_DPI`, `_THUMB_SIZE = SIZE_CARD_THUMB_SIZE`, `_GIMP_UNIT_MAP` (قاموس تحويل رموز الوحدات لمعرّفات وحدات GIMP الداخلية — **ملاحظة:** هذا القاموس معرَّف لكنه غير مُستخدَم فعلياً في أي دالة ضمن هذا الملف المرفق، ربما بقايا من تكامل مخطَّط له مع سكريبت GIMP مباشر لم يُستكمل).

---

## 11. `ui/tabs/design/designs/_size_card.py`

**الغرض:** بطاقة عرض مقاس واحد (v3) ضمن لوحة تفاصيل التصميم — تعرض thumbnail، اسم المقاس ومجموعته، الأبعاد (بالوحدة وبالـ px عند وجود DPI)، أزرار فتح/إنشاء في GIMP، ربط ملف، تعديل، حذف، وشريط حالة سفلي يوضّح إن كان الملف موجوداً/مفقوداً/غير مربوط.

**الـ imports الداخلية المهمة:**
- `services.design.get_design_size_service`
- `._xcf_thumbnail.get_watcher`
- `.size_card.helper` (`_ThumbnailWidget`, `_to_px`, `_unit_for_set`, `_btn_ss`, `_open_gimp`) — كل منطق GIMP والـ thumbnail الفعلي مُفوَّض لهذا الملف المساعد.

**من يستدعي هذا الملف:** `_design_detail_panel.py` (مؤكَّد — ينشئ `_SizeCard` لكل مقاس).

### Class: `_SizeCard(ThemedFrame, WidgetMixin)`
**Signals:** `edit_requested = pyqtSignal(int)`, `delete_requested = pyqtSignal(int)`, `path_changed = pyqtSignal()`

- **`__init__(self, conn, size_data, parent=None)`**: يبني الواجهة، يفعّل `WidgetMixin(theme=False, font=True, lang=False, data=False)`، وإذا كان هناك مسار XCF موجود فعلياً على القرص، يبدأ مراقبته عبر `get_watcher().watch()` ويربط `file_changed → _on_xcf_changed`.
- **`_refresh_style(self, *_)`**: يحدّث فقط خط اسم المقاس (`_lbl_name`) ديناميكياً عند تغيّر حجم الخط.
- **`_on_xcf_changed(self, path)`**: إذا كان المسار المتغيّر مطابقاً لملف هذا الكارت، يستدعي `self._thumb.refresh(path)`.
- **`closeEvent(self, event)` / `hideEvent(self, event)`**: يستدعيان `_stop_watching()` قبل `super()`.
- **`_stop_watching(self)`**: يفصل اتصال `file_changed` بأمان (`try/except`).
- **`_build(self)`**: يبني: قسم رئيسي أفقي (Thumbnail + عمود معلومات [اسم، مجموعة، أبعاد] + عمود أزرار [زر رئيسي GIMP + صف أزرار تعديل/حذف])، ثم `_build_status_bar`. يحسب الأبعاد عبر `_svc.get_canvas_size` و`_unit_for_set` و`_svc.get_canvas_dpi`، ويبني نص العرض المناسب (مع DPI أو بدونه أو "غير معروف"). الزر الرئيسي يتغيّر نصاً/لوناً حسب وجود الملف فعلياً على القرص (فتح GIMP أخضر/إنشاء ملف جديد).
- **`_build_status_bar(self, root, file_exists, has_file, unit, dpi)`**: يبني شريطاً سفلياً بثلاث حالات لونية: أخضر (الملف موجود)، أصفر/تحذير (مسار محفوظ لكن الملف غير موجود فعلياً)، رمادي محايد (لا يوجد مسار مربوط إطلاقاً) — مع "chips" صغيرة تعرض الوحدة والـ DPI.
- **`_open_in_gimp(self)`**: يتحقق من وجود الملف فعلياً، يراقبه، ويستدعي `_open_gimp(xcf_path=xcf)`؛ وإلا يعرض تحذير "ملف غير موجود".
- **`_create_in_gimp(self)`**: يفتح `QFileDialog.getSaveFileName` لاختيار مسار حفظ جديد (يقترح اسم افتراضي من `instance_name`)، يحدّث المسار في القاعدة (`_svc.update_path`)، يراقب الملف الجديد، يحسب أبعاد px من القيم الفعلية والوحدة والـ DPI، يعرض رسالة تأكيد بالتفاصيل الكاملة، ثم يستدعي `_open_gimp` بمعاملات إنشاء الكانفاس، ويحدّث الـ thumbnail، ويُطلق `path_changed`.
- **`_set_path(self)`**: يفتح `QFileDialog.getOpenFileName` لربط ملف XCF موجود مسبقاً، يوقف مراقبة المسار القديم إن وُجد، يحدّث القاعدة والمسار المحلي، يبدأ مراقبة المسار الجديد، يحدّث الـ thumbnail، ويُطلق `path_changed`.

**module-level constants:** `_RADIUS`, `_RADIUS_XS` (من `SIZE_CARD_RADIUS*`), `_DEFAULT_DPI` (float من `SIZE_CARD_DEFAULT_DPI`), `_THUMB_SIZE` (من `SIZE_CARD_THUMB_W`)، ومجموعة متغيرات لونية module-level ثابتة (`_BG`, `_BG_SURFACE`, `_BORDER`, `_ACCENT`, `_SUCCESS*`, `_DANGER*`, `_WARNING*`) مُستخرَجة من `_C` مباشرة عند الـ import — **ملاحظة مهمة:** هذه المتغيرات لم تُحوَّل بعد لنمط الـ property الديناميكي الموثّق في `design_styles.py`، أي أنها عرضة لنفس مشكلة "تجمّد الثيم" وقت الاستيراد الأول إن لم تُستخدم فقط داخل `_build` الذي يُعاد استدعاؤه، بل هي تُستخدم مباشرة كـ f-string ثابتة في القيم اللونية.

---

## 12. `ui/tabs/design/designs/_size_dialog.py`

**الغرض:** Dialog لإضافة أو تعديل مقاس واحد لتصميم — يختار المستخدم: مجموعة مقاسات → instance (نسخة قيم) → حقل العرض → حقل الطول → حقل DPI (اختياري) → مسار ملف GIMP، مع معاينة حية لمقاس الكانفاس الناتج بالوحدة وبالـ px.

**الـ imports الداخلية المهمة:**
- `services.design.dimension_set_service.DimensionSetService`

**من يستدعي هذا الملف:** `_design_detail_panel.py` (مؤكَّد — يفتحه في `_add_size` و`_edit_size`).

### دالة top-level: `_to_px_preview(value: float, unit: str, dpi: float) -> int`
تحوّل قيمة رقمية بوحدة معينة (`px`, `mm`, `cm`, `m`, `inch`/`in`) إلى بكسل بالاعتماد على الـ DPI، بحد أدنى 1 بكسل دائماً؛ الوحدات غير المعروفة تُعامَل كـ px مباشرة.

### Class: `_SizeDialog(QDialog, WidgetMixin)`
- **`__init__(self, conn, design_id, size_data=None, parent=None)`**: يحدد وضع إضافة/تعديل حسب وجود `size_data`، يبني الواجهة، وإن كان تعديلاً يحمّل البيانات عبر `_load`.
- **`_build(self)`**: `QFormLayout` يحوي: `cmb_set` (مجموعة مقاسات)، `cmb_instance` (نسخة القيم)، `cmb_width`، `cmb_height`، `cmb_dpi` (اختياري)، ليبل معاينة الكانفاس (`lbl_canvas`، لون يتغيّر حسب اكتمال البيانات)، صف مسار GIMP (حقل + زر تصفّح)، حقل ملاحظات، وأزرار حفظ/إلغاء عبر `QDialogButtonBox`.
- **`_load_sets_combo(self)`**: يملأ `cmb_set` بكل المجموعات المتاحة.
- **`_on_set_changed(self)`**: عند تغيير المجموعة، يعيد بناء `cmb_instance` وحقول العرض/الطول/DPI (فقط الحقول من نوع `number`)، ويصفّر معاينة الكانفاس.
- **`_on_instance_changed(self)`**: يستدعي `_update_canvas_preview()`.
- **`_update_canvas_preview(self)`**: يجلب قيم العرض/الطول (وDPI إن وُجد) من `_svc.get_field_value`، يحسب px عبر `_to_px_preview` إذا توفّر DPI، ويعرض رسالة ملوّنة (أخضر=مكتمل مع DPI، أصفر=مكتمل بدون DPI أو بيانات ناقصة).
- **`_browse_xcf(self)`**: يفتح `QFileDialog.getOpenFileName` لاختيار ملف GIMP وتعبئة الحقل.
- **`_load(self, d)`**: يحدد كل الـ combos بالقيم المخزّنة مسبقاً (`set_id`, `instance_id`, `width_field_id`, `height_field_id`, `dpi_field_id` الاختياري)، يملأ المسار والملاحظات، ويحدّث المعاينة.
- **`_save(self)`**: يتحقق من اختيار مجموعة و instance (وإلا تحذير)، يتحقق من عدم تكرار استخدام نفس الـ instance لنفس التصميم (`is_instance_used`)، ثم يستدعي `update_size` أو `create_size` حسب الحالة، ويقبل الـ Dialog (`accept()`).

---

## 13. `ui/tabs/design/designs/_xcf_thumbnail.py`

**الغرض:** استخراج thumbnail من ملفات XCF (GIMP) بخمس استراتيجيات متتالية (fallback chain)، مع كاش بالذاكرة مبني على `mtime`، وclass مراقبة (`XcfWatcher`) singleton لملفات XCF يطلق إشارة عند التغيير الفعلي بعد فترة "debounce".

**الـ imports الداخلية المهمة:** لا يستورد أي ملف آخر من نفس المرجع (`ui.tabs.design.*`) — فقط `ui.theme._C`, `ui.widgets.core.i18n.tr`, `ui.constants` (خارج نطاق هذا المرجع لكن تابعة للمشروع).

**من يستدعي هذا الملف:** `_designs_table.py`, `_design_card.py` (عبر `get_watcher`, `clear_cache`)، و`size_card/helper.py` (عبر `get_xcf_thumbnail`) — كلها مؤكَّدة من المرفقات الحالية.

### Class: `XcfWatcher(QObject)` — Singleton
**Signal:** `file_changed = pyqtSignal(str)`
**Class attribute:** `_DEBOUNCE_MS = XCF_WATCHER_DEBOUNCE_MS`

- **`__init__(self, parent=None)`**: ينشئ `QFileSystemWatcher` داخلي، يربط `fileChanged → _on_raw`، يهيّئ `_timers: dict` و`_watched: set`.
- **`watch(self, path: str)`**: يضيف مسار للمراقبة (بعد `os.path.normpath`) إن كان موجوداً فعلياً وغير مراقَب بالفعل.
- **`unwatch(self, path: str)`**: يزيل المسار من المراقبة ويوقف/يحذف المؤقّت (Timer) المرتبط به إن وُجد.
- **`_on_raw(self, path: str)`**: يتعامل مع "atomic save" (GIMP يحذف الملف ويعيد كتابته) بإعادة إضافة المسار للمراقب إن اختفى مؤقتاً، ثم يبدأ/يعيد ضبط مؤقّت debounce (1.5 ثانية تقريباً حسب `_DEBOUNCE_MS`) قبل إطلاق الإشارة الفعلية.
- **`_emit(self, path: str)`**: يتحقق من وجود الملف فعلياً، يمسح الكاش (`clear_cache`)، يحذف المؤقّت، ويُطلق `file_changed`.

### دالة top-level: `get_watcher() -> XcfWatcher`
تُرجع نسخة singleton وحيدة من `XcfWatcher` (تُنشئها عند أول استدعاء فقط عبر متغير module-level `_watcher_instance`).

### دالة top-level: `get_xcf_thumbnail(xcf_path: str, size: int = 80) -> QPixmap | None`
يتحقق من وجود الملف، يقارن `mtime` مع الكاش (`_CACHE`)؛ إن كان مطابقاً يرجع النسخة المُصغَّرة من الكاش مباشرة. وإلا يجرّب بالترتيب: `_try_wand` → `_try_magick_subprocess` → `_try_gimp_cache` → `_try_xcf_native` → `_make_placeholder` (آخر واحد لا يفشل أبداً)، ويخزّن النتيجة في الكاش.

### دالة top-level: `clear_cache(xcf_path: str = None)`
يمسح مدخلاً واحداً من الكاش إن مُرِّر مسار، أو الكاش بالكامل إن لم يُمرَّر شيء.

### دالة top-level: `_find_magick() -> str | None`
يبحث عن تنفيذي ImageMagick (`magick.exe`) بالترتيب: مسارات Windows الثابتة المعروفة → `PATH` عبر `shutil.which("magick")` → fallback لـ `convert` (مع استبعاد `system32` تجنباً لتعارض أمر Windows المدمج). يخزّن النتيجة في متغير module-level `_MAGICK_EXE` (Cache على مستوى العملية، بقيمة أولية خاصة `"UNSET"` للتمييز عن `None`).

### دالة top-level: `_try_wand(xcf_path: str) -> QPixmap | None`
يستخدم مكتبة `Wand` (ImageMagick binding) لدمج الطبقات (`merge_layers("flatten")`) وتصغيرها وتحويلها لـ PNG blob ثم `QImage`/`QPixmap`. يضبط متغيرات بيئة `PATH`/`MAGICK_HOME` تلقائياً إن لزم.

### دالة top-level: `_try_magick_subprocess(xcf_path: str) -> QPixmap | None`
Fallback عبر استدعاء `magick` كـ subprocess مباشرة (بديل عن Wand)، يحوّل أول layer (`[0]`) لملف PNG مؤقت بحجم 256×256 على خلفية بيضاء، مع timeout 20 ثانية.

### دالة top-level: `_try_gimp_cache(xcf_path: str) -> QPixmap | None`
يبحث في مجلدات كاش GIMP/thumbnails القياسية (Linux-style `.cache/thumbnails` و`.thumbnails`، بالإضافة لمسارات GIMP على Windows عبر `APPDATA` لعدة إصدارات)، معتمداً على معرّف MD5 لـ URI الملف (بحساسية حالة أول حرف من مسار Windows).

### دالة top-level: `_try_xcf_native(xcf_path: str) -> QPixmap | None`
يقرأ رأس ملف XCF يدوياً (Magic bytes، رقم الإصدار)، ويستدعي `_scan_for_thumbnail` لدعم إصدارات XCF من v1 إلى v9 فقط.

### دالة top-level: `_scan_for_thumbnail(f) -> QPixmap | None`
يمسح Properties الملف (حتى `_MAX_PROPS = 300` خاصية) بحثاً عن property من نوع `_PROP_THUMBNAIL` (=1028)، ويستدعي `_decode_thumbnail` عند إيجاده.

### دالة top-level: `_decode_thumbnail(f, payload_len: int) -> QPixmap | None`
يفكّ ترميز بيانات الصورة المصغّرة الخام (raw RGB/RGBA) من صيغة XCF الداخلية، يجرّب عدة تركيبات أبعاد محتملة (`width, height`) للتحقق من صحة حجم البيانات، ويبني `QImage` مباشرة من البايتات الخام.

### دالة top-level: `_make_placeholder(xcf_path: str, size: int = 80) -> QPixmap`
يُنشئ صورة بديلة جمالية (Gradient خلفية + حدود مدورة + أيقونة + اسم الملف مختصراً) تُستخدم كـ fallback نهائي لا يفشل أبداً — تضمن ظهور شيء دائماً حتى لو فشلت كل الطرق الأخرى.

### دالة top-level: `_scale(pixmap: QPixmap, size: int) -> QPixmap`
يُصغّر/يكبّر `QPixmap` مع الحفاظ على نسبة الأبعاد (`KeepAspectRatio`) بجودة `SmoothTransformation`.

**module-level constants:** `_CACHE: dict[str, tuple[float, QPixmap]] = {}` (كاش الذاكرة الرئيسي)، `_XCF_MAGIC = b"gimp xcf "`, `_PROP_END = 0`, `_PROP_THUMBNAIL = 1028`, `_MAX_PROPS = 300`, `_MAGICK_EXE: str | None = "UNSET"`, `_watcher_instance: XcfWatcher | None = None`.

**ملاحظات كود مهمة:** هذا أكبر ملف تقنياً في المرجع — منطق تحليل صيغة ملفات ثنائية (Binary format parsing) يدوي بالكامل للـ fallback الأخير، وسلسلة fallback من 5 مستويات موثّقة بوضوح في رأس الملف (v5).

---

## 14. `ui/tabs/design/dimension_sets/_categories_panel.py`

**الغرض:** لوحة إدارة كاملة لتصنيفات "مجموعات المقاسات" (منفصلة تماماً عن تصنيفات التصميمات) — شجرة عرض هرمية، فورم إضافة/تعديل (اسم، لون، تصنيف أب)، وحذف مع تحذيرات تفصيلية. تُستخدم داخل `_GroupsPanel`.

**الـ imports الداخلية المهمة:**
- `services.design.dimension_set_service.DimensionSetService`
- `ui.widgets.components.button.make_btn`

**من يستدعي هذا الملف:** `_groups_panel.py` (مؤكَّد — `_GroupsPanel` يُنشئ `_CategoriesPanel` مباشرة).

### دالة top-level: `buttons_row(*buttons) -> QHBoxLayout`
يبني صف أزرار أفقي بمسافة ثابتة (`DIM_CAT_PANEL_BTN_ROW_SPACING`) مع `addStretch()` نهائي.

### Class: `_CategoriesPanel(QWidget, WidgetMixin)`
**Signal:** `changed = pyqtSignal()` — يُطلق بعد أي تغيير فعلي للتصنيفات (إضافة/تعديل/حذف).

- **`__init__(self, conn, parent=None)`**: `_editing_id = None`، `_color = _C["accent"]` افتراضياً، يبني الواجهة، يحمّل الشجرة، يفعّل `WidgetMixin(lang=False, data=False)`.
- **`_build(self)`**: هيدر + `QTreeWidget` بعمودين (اسم، عدد) + أزرار تعديل/حذف تحت الشجرة + `QGroupBox` فورم (وضع الحالة + اسم + تصنيف أب + صف لون [مربع معاينة + زر اختيار] + أزرار إضافة/حفظ/إلغاء).
- **`_load_tree(self)`**: يحفظ حالة التوسّع (`isExpanded`) الحالية لكل عقدة قبل المسح (بدالة داخلية متداخلة `_collect` تكرارية)، يعيد بناء الشجرة من `list_categories`/`build_tree`، ثم `expandAll()` مع استعادة التوسّع المحفوظ.
- **`_add_tree_nodes(self, nodes, parent, expanded)`**: يبني عناصر `QTreeWidgetItem` تكرارياً، يلوّن اسم العقدة بلونها المخزَّن، ويعرض عدد المجموعات ("لا يوجد" إن كان صفراً).
- **`_selected_cat_id(self)`**: يرجع `id` العنصر المحدد في الشجرة أو `None`.
- **`_reload_parent_combo(self, exclude_id=None)`**: يبني `cmb_parent` من الشجرة، يستبعد العقدة الجاري تعديلها وكل أحفادها (`get_descendants`) لمنع اختيار تصنيف كأب لنفسه أو لأحد أحفاده.
- **`_add_parent_nodes(self, nodes, depth, excluded)`**: تكرارية، تبني قائمة combo بمسافات بادئة، تتجاهل العقد المستبعدة.
- **`_pick_color(self)`**: يفتح `QColorDialog`، يحدّث `_color` والمعاينة عند الاختيار الصالح.
- **`_update_color_preview(self)`**: يلوّن مربع المعاينة (`lbl_color`) باللون الحالي.
- **`_add_category(self)`**: يتحقق من الاسم (تحذير إن فارغ)، يستدعي `create_category`، يصفّر الفورم، يعيد تحميل الشجرة، ويُطلق `changed`.
- **`_edit_category(self)`**: يتحقق من وجود تحديد، يحمّل بيانات التصنيف في الفورم (اسم، لون، أب مع استبعاد الأحفاد)، يبدّل الأزرار لوضع "حفظ/إلغاء".
- **`_save_category(self)`**: يتحقق من الاسم، يستدعي `update_category`، يصفّر الفورم، يعيد التحميل، ويُطلق `changed`.
- **`_delete_category(self)`**: يحسب عدد الأحفاد والمجموعات المرتبطة، يبني رسالة تحذير تفصيلية (تحذير أحفاد + تحذير مجموعات مرتبطة إن وُجدت)، وعند التأكيد يحذف كل الأحفاد بترتيب عكسي.
- **`_reset_form(self)`**: يعيد الفورم لحالة "إضافة جديد" الافتراضية.
- **`refresh(self)`**: يعيد تحميل الشجرة و`cmb_parent`.
- **`_refresh_style(self, *_)`**: يلوّن الهيدر ولون وضع الفورم، يحدّث معاينة اللون، ويعيد تطبيق ستايل الأزرار المبنية بـ `make_btn` عبر `refresh_visible_buttons` (تعليق كود يوثّق أن هذا إصلاح مطابق لمشكلة مماثلة في `_groups_panel.py`).

---

## 15. `ui/tabs/design/dimension_sets/_field_dialog.py`

**الغرض:** Dialog إضافة/تعديل حقل واحد ضمن مجموعة مقاسات — يدعم تحديد نوع الحقل (رقم/نص)، الوحدة، والأهم: اعتمادية (dependency) اختيارية يمكن أن تكون على حقل من نفس المجموعة أو من مجموعة مقاسات مختلفة تماماً (Cross-set)، مع معاينة حية للنتيجة المحسوبة.

**الـ imports الداخلية المهمة:**
- `services.design.dimension_set_service.DimensionSetService`
- `ui.widgets.combo.unit.UnitCombo` — combo وحدات مع تذكّر آخر اختيار.

**من يستدعي هذا الملف:** `_fields_panel.py` (مؤكَّد — يستخدمه في `_add_field` و`_edit_field`).

### دالة top-level: `_spin(min_=None, max_=DIM_FIELD_DLG_SPIN_DEFAULT_MAX, dec=DIM_FIELD_DLG_SPIN_DEFAULT_DEC) -> QDoubleSpinBox`
ينشئ `QDoubleSpinBox` بنطاق وارتفاع موحّدين حسب الثوابت الافتراضية.

### Class: `_FieldDialog(QDialog, WidgetMixin)`
- **`__init__(self, conn, set_id, field_data=None, parent=None)`**: يحدد وضع إضافة/تعديل، يبني الواجهة، وإن وُجد `field_data` يحمّله عبر `_load`.
- **`_build(self)`**: فورم أساسي (اسم إنجليزي، تسمية عربية، `UnitCombo`، نوع [رقم/نص]، checkbox "مطلوب")، ثم `QGroupBox` قابل للتفعيل (`setCheckable(True)`) لقسم "الاعتمادية" يحوي: `cmb_source_set` (المجموعة المصدر — يضيف المجموعة الحالية أولاً بعنوان مميّز "نفس المجموعة")، `cmb_source` (الحقل المصدر)، `sp_offset` (قيمة إضافة/خصم)، معاينة نصية، وتلميح إرشادي.
- **`_on_type_changed(self, idx)`**: يعطّل قسم الاعتمادية بالكامل تلقائياً إذا تغيّر النوع لغير "رقم" (لأن الاعتمادية تخص الحقول الرقمية فقط).
- **`_reload_source_fields(self)`**: عند تغيير المجموعة المصدر، يعيد ملء `cmb_source` بالحقول الرقمية فقط من تلك المجموعة (يستبعد الحقل الجاري تعديله نفسه لمنع الاعتمادية الذاتية)؛ إذا لم توجد حقول رقمية يعرض رسالة بديلة.
- **`_update_preview(self)`**: يجلب قيمة الحقل المصدر مباشرة عبر استعلام SQL خام (JOIN بين `dimension_set_values`, `dimension_fields`, `dimension_sets`)، يحسب `القيمة + offset`، ويعرض نصاً منسقاً بالصيغة الموحّدة (`dim_src_preview_fmt`)؛ إن لم توجد قيمة يعرض رسالة "لا توجد قيمة".
- **`_load(self, field_data)`**: يملأ الحقول الأساسية والوحدة والنوع، وإن كان للحقل اعتمادية مسجَّلة (`get_field_dep`) يفعّل القسم ويحدد المجموعة/الحقل المصدر والـ offset، ويحدّث المعاينة.
- **`_save(self)`**: يتحقق من الاسم والتسمية، يستدعي `update_field` أو `create_field` (بترتيب `sort_order` تلقائي للحقل الجديد = عدد الحقول الحالية)، ثم إن كان قسم الاعتمادية مفعَّلاً يستدعي `set_field_dep` (مع `actual_src_set = None` إذا كانت المجموعة المصدر هي نفس المجموعة الحالية — تمييز "نفس المجموعة" عن "مجموعة أخرى" في التخزين)، وإلا يستدعي `remove_field_dep`.

---

## 16. `ui/tabs/design/dimension_sets/_fields_panel.py`

**الغرض:** محرر جدولي لحقول مجموعة مقاسات محددة — إضافة/تعديل/حذف/إعادة ترتيب (نقل لأعلى/أسفل)، مع عرض عمود "الاعتمادية" الذي يلخّص أي ربط cross-set أو same-set لكل حقل.

**الـ imports الداخلية المهمة:**
- `services.design.dimension_set_service.DimensionSetService`
- `._field_dialog._FieldDialog`
- `ui.widgets.components.button.make_btn`
- `ui.widgets.tables.tables.make_table`
- `ui.widgets.dialogs.confirm.confirm_delete`

**من يستدعي هذا الملف:** `_groups_panel.py` (مؤكَّد — `_SetsManagerPanel` يُنشئ `_FieldsPanel` ويستدعي `load_set`/`clear` عليه).

### Class: `_FieldsPanel(QWidget, WidgetMixin)`
**Signals:** `fields_changed = pyqtSignal()`, `set_selected = pyqtSignal(int)`

- **`__init__(self, conn, parent=None)`**: `_set_id = None`، يبني الواجهة، يفعّل `WidgetMixin(lang=False, data=False)`.
- **`_build(self)`**: هيدر + جدول (`make_table`) بأعمدة: ترتيب، اسم إنجليزي، تسمية، وحدة، نوع، مطلوب، اعتمادية — بعرض أعمدة مضبوط يدوياً؛ صف أزرار: إضافة (success)، تعديل، حذف (danger)، ثم مسافة، ثم نقل لأعلى/أسفل (ghost).
- **`load_set(self, set_id: int)`**: يخزّن `_set_id`، يستدعي `_refresh()`، ويُطلق `set_selected`.
- **`clear(self)`**: يصفّر `_set_id` ويفرّغ الجدول.
- **`_refresh(self)`**: يعيد بناء الجدول بالكامل من `list_fields(_set_id)`؛ **منطق مهم:** عمود الاعتمادية يُبنى بحذر شديد باستخدام `try/except` منفصلة لكل قيمة (`source_field_id`, `dep_offset`, `source_label`, `source_set_name`) لأن `sqlite3.Row` لا يدعم `.get()` — إن وُجدت اعتمادية يبني نصاً بصيغة `"التسمية (اسم المجموعة) +/-القيمة"` أو `"التسمية +/-القيمة"` إن كانت نفس المجموعة.
- **`_selected_field_id(self)`**: يرجع `id` الحقل المحدد بالصف الحالي أو `None`.
- **`_add_field(self)`**: يتحقق من وجود `_set_id` (وإلا رسالة معلوماتية)، يفتح `_FieldDialog`، وعند القبول يحدّث الجدول ويُطلق `fields_changed`.
- **`_edit_field(self)`**: يتحقق من وجود تحديد، يفتح `_FieldDialog` بوضع تعديل مع بيانات الحقل، وعند القبول يحدّث ويُطلق `fields_changed`.
- **`_del_field(self)`**: يتحقق من التحديد، يعرض تأكيد عبر `confirm_delete` باستخدام تسمية الحقل، وعند التأكيد يحذف ويحدّث ويُطلق `fields_changed`.
- **`_move_up(self)` / `_move_down(self)`**: يستدعيان `_move(-1)` / `_move(1)`.
- **`_move(self, direction: int)`**: يتحقق من صلاحية الصف الجديد ضمن الحدود، يبني قائمة IDs الحالية بترتيب الصفوف، يبدّل موضعي الحقل المحدد والمجاور، يستدعي `reorder_fields`، يحدّث الجدول، يعيد التحديد للصف الجديد، ويُطلق `fields_changed`.
- **`_refresh_style(self, *_)`**: يلوّن الهيدر، يعيد تطبيق ستايل الجدول عبر `refresh_table_styles`، وستايل الأزرار عبر `refresh_visible_buttons` — كلاهما موثّق بتعليقات كإصلاحات dark-theme.

---

## 17. `ui/tabs/design/dimension_sets/_groups_panel.py`

**الغرض:** الملف الأكبر منطقياً في وحدة "المجموعات" — يحوي كلاسين: `_SetsManagerPanel` (إدارة كاملة لمجموعات المقاسات + دمج `_FieldsPanel` أسفلها في Splitter رأسي) و`_GroupsPanel` (الحاوي الأعلى الذي يجمع `_CategoriesPanel` يساراً و`_SetsManagerPanel` يميناً في Splitter أفقي).

**الـ imports الداخلية المهمة:**
- `services.design.dimension_set_service.DimensionSetService`
- `._categories_panel._CategoriesPanel`
- `._fields_panel._FieldsPanel`
- `ui.widgets.components.button.make_btn`
- `ui.widgets.tables.tables.make_table`
- `ui.widgets.combo.unit.UnitCombo`

**من يستدعي هذا الملف:** `dimension_sets_tab.py` (مؤكَّد — يستورد `_GroupsPanel` مباشرة ويربط `sets_changed`).

### دالة top-level: `buttons_row(*buttons) -> QHBoxLayout`
مطابقة تماماً لنظيرتها في `_categories_panel.py` (تكرار نمط، لا استيراد مشترك بينهما).

### Class: `_SetsManagerPanel(QWidget, WidgetMixin)`
**Signal:** `sets_changed = pyqtSignal()`

- **`__init__(self, conn, parent=None)`**: `_editing_id = None`، `_all_rows = []`، يبني، يحمّل، يفعّل `WidgetMixin(lang=False, data=False)`.
- **`_build(self)`**: فلتر (بحث + تصنيف)، ثم `QSplitter` رأسي (`_v_splitter`) بجزئين: الجزء العلوي (جدول مجموعات + أزرار تعديل/حذف + `QGroupBox` فورم كامل [اسم، تصنيف، وحدة افتراضية عبر `UnitCombo`، ملاحظات، أزرار إضافة/حفظ/إلغاء])، والجزء السفلي (هيدر + `_FieldsPanel` كاملة مدمجة).
- **`_reload_cat_combos(self)`**: يبني `cmb_cat_filter` و`cmb_category` معاً من نفس شجرة التصنيفات، مع حفظ الاختيار السابق لكل واحد على حدة.
- **`_add_cat_nodes(self, combo, nodes, depth)`**: تكرارية عامة تقبل أي combo كمعامل (يُعاد استخدامها للفلتر ولفورم الإضافة).
- **`_load(self)`**: يحمّل كل الصفوف، يعيد بناء الـ combos، يطبّق الفلتر.
- **`_apply_filter(self)`**: يفلتر حسب نص البحث والتصنيف، يحسب عدد الحقول لكل مجموعة عبر استعلام SQL مباشر (`COUNT(*) FROM dimension_fields WHERE set_id=?`)، يعيد بناء الجدول، ويحافظ على التحديد السابق إن أمكن؛ **ملاحظة سلوك:** إذا لم يبقَ تحديد صالح بعد الفلترة، يستدعي `self._fields_panel.clear()` صراحة لتفادي عرض حقول مجموعة لم تعد ظاهرة.
- **`_selected_id(self)`**: نمط متكرر مطابق لباقي الملفات (`id` من `Qt.UserRole` للعمود صفر بالصف المحدد).
- **`_on_set_select(self)`**: عند تغيّر التحديد، يستدعي `_fields_panel.load_set(sid)` أو `.clear()`.
- **`_add_set(self)`**: يتحقق من الاسم، يستدعي `create_set`، يصفّر الفورم، يعيد التحميل، يعيد تحديد الصف الجديد بالبحث عن `new_id`، ويُطلق `sets_changed`.
- **`_edit_set(self)`**: يتحقق من التحديد، يحمّل البيانات في الفورم (بما فيها `UnitCombo.set_unit`)، يبدّل الأزرار لوضع حفظ/إلغاء.
- **`_save_set(self)`**: يتحقق من الاسم، يستدعي `update_set`، يصفّر، يعيد التحميل، ويُطلق `sets_changed`.
- **`_delete_set(self)`**: **منطق حماية مهم:** إذا كانت المجموعة مرتبطة بأي تصميمات فعلية (`count_designs_for_set > 0`)، **يمنع الحذف تماماً** برسالة تحذير (لا خيار تجاوز) — بخلاف حذف التصنيفات الذي يسمح بالحذف مع تحذير فقط. إن لم تكن مرتبطة بتصميمات، يعرض تأكيداً عادياً (مع تحذير عدد الحقول إن وُجدت) وعند القبول يمسح `_fields_panel` أولاً ثم يحذف المجموعة.
- **`_reset_form(self)`**: يعيد الفورم لوضع "جديد" (الوحدة تُترك لآخر قيمة محفوظة تلقائياً عبر `UnitCombo`).
- **`refresh_categories(self)`**: يعيد `_reload_cat_combos` و`_load`.
- **`refresh(self)`**: يحافظ على التحديد الحالي، يعيد التحميل، ويعيد تحميل حقول المجموعة المحددة إن وُجدت.
- **`refresh_unit_combo(self)`**: يُستدعى خارجياً (موثّق أنه من `SettingsDialog`) بعد تعديل الوحدات — ينادي `cmb_unit.refresh()`.
- **`_refresh_style(self, *_)`**: يلوّن الهيدر، حدود الـ splitter، هيدر قسم الحقول، ثم يستدعي `refresh_table_styles` و`refresh_visible_buttons` (لزر الحذف تحديداً) — موثّقة كإصلاحات dark-theme مطابقة لأنماط الملفات الأخرى.

### Class: `_GroupsPanel(QWidget, WidgetMixin)`
**Signal:** `sets_changed = pyqtSignal()`

- **`__init__(self, conn, parent=None)`**: يبني الواجهة، يفعّل `WidgetMixin(lang=False, data=False)`.
- **`_build(self)`**: `QSplitter` أفقي يحوي `_cats_panel` (`_CategoriesPanel`) و`_sets_manager` (`_SetsManagerPanel`)؛ يربط `_cats_panel.changed → self._on_categories_changed` و`_sets_manager.sets_changed → self.sets_changed.emit` (إعادة بث/Re-emit للأعلى).
- **`_on_categories_changed(self)`**: يستدعي `self._sets_manager.refresh_categories()`.
- **`refresh(self)`**: يحدّث كلاً من `_cats_panel` و`_sets_manager`.
- **`refresh_unit_combos(self)`**: موثّق أنه يُستدعى من `SettingsDialog` — ينادي `_sets_manager.refresh_unit_combo()`.
- **`_refresh_style(self, *_)`**: يلوّن حدود splitter الأفقي فقط.

---

## 18. `ui/tabs/design/dimension_sets/_sets_panel.py`

**الغرض:** قائمة اختيار (Read-only Selection List) لمجموعات المقاسات فقط — بدون أي إمكانية إضافة/تعديل/حذف (تلك المسؤوليات انتقلت بالكامل لـ `_GroupsPanel`). تُستخدم كمكوّن اختيار بسيط في سياقات أخرى.

**الـ imports الداخلية المهمة:**
- `services.design.get_dimension_set_service`
- `ui.widgets.tables.tables.make_table`

**من يستدعي هذا الملف:** غير محدد بثقة من المرفقات الحالية (لم يظهر أي استيراد مباشر له في باقي الملفات المرفقة ضمن هذه الدفعة رغم وجوده في `system_arch.txt` تحت نفس المسار — الاستخدام الفعلي قد يكون من ملف خارج نطاق هذا المرجع، أو أنه مكوّن بديل/قديم عن `_sets_list_panel.py`).

### Class: `_SetsPanel(QWidget, WidgetMixin)`
**Signal:** `set_selected = pyqtSignal(int)`

- **`__init__(self, conn, parent=None)`**: `_all_rows = []`، يبني، يحمّل، يفعّل `WidgetMixin(lang=False, data=False)`.
- **`_build(self)`**: هيدر + تلميح (Hint) + صف فلتر (بحث + تصنيف) + جدول (`make_table`) بأعمدة: معرّف، اسم، تصنيف، وحدة، عدد حقول — بدون أي أزرار إدارة.
- **`_reload_cat_filter(self)`**: يبني `cmb_cat_filter` من شجرة التصنيفات مع حفظ الاختيار السابق.
- **`_add_cat_nodes(self, nodes, depth)`**: تكرارية قياسية لبناء قائمة الشجرة في الـ combo.
- **`_load(self)`**: يحمّل كل الصفوف من `list_sets()`، يعيد بناء فلتر التصنيف، يطبّق الفلترة.
- **`_apply_filter(self)`**: يفلتر حسب البحث والتصنيف، يبني الجدول (بحساب عدد الحقول لكل صف عبر `count_fields_for_set`)، يحافظ على التحديد السابق.
- **`_selected_id(self)`**: نمط قياسي — `id` من `Qt.UserRole`.
- **`_on_select(self)`**: عند تغيّر التحديد في الجدول، يُطلق `set_selected(sid)` إن كان هناك تحديد فعلي.
- **`refresh(self)`**: يعيد `_load()`.
- **`_refresh_style(self, *_)`**: يلوّن الهيدر والتلميح (Hint، بخلفية/حدود مخصصة من ألوان "investor_link")، ويستدعي `refresh_table_styles` (موثّق كإصلاح dark-theme).

---

## 19. `ui/tabs/design/dimension_sets/_source_picker_dialog.py`

**الغرض:** Dialog لاختيار الـ instance المصدر (Cross-set) قبل تنفيذ حساب تلقائي لحقل معتمِد على مجموعة مقاسات أخرى — يُستدعى فقط من `_instance_popup.py` عند الضغط على زر الحساب التلقائي لحقل ذي اعتمادية cross-set. يعرض قائمة كل الـ instances في المجموعة المصدر مع قيمة الحقل المصدر ومعاينة النتيجة (`قيمة + offset`) لكل منها، ويُظهَر دائماً (حتى لو كان هناك instance واحد فقط) لإجبار المستخدم على تأكيد صريح.

**الـ imports الداخلية المهمة:**
- `services.design.dimension_set_service.DimensionSetService`

**من يستدعي هذا الملف:** `_instance_popup.py` (مؤكَّد — يستورده ويستدعيه في `_pick_source_instance`).

### دالة top-level: `_btn_primary_ss() -> str` / `_btn_ghost_ss() -> str`
دالتان تُرجعان QSS نصياً ثابت البنية لزر أساسي/شفاف بألوان من `_C`.

### Class: `_SourcePickerDialog(QDialog, WidgetMixin)`
- **`__init__(self, conn, source_set_id, source_field_id, offset=0.0, target_field_label="", parent=None)`**: يخزّن كل المعاملات، `selected_instance_id = None`، `_instance_names: dict[int, str] = {}` (لتخزين أسماء الـ instances بمعزل عن هرمية الـ widgets — لتفادي الاعتماد على البحث في شجرة الويدجت لاحقاً)، يبني الواجهة، يفعّل `WidgetMixin(data=False)`.
- **`_build(self)`**: هيدر بإطار مميّز (عنوان + معلومات المجموعة/الحقل المصدر + معادلة نصية توضيحية `"حقل المصدر [+/-offset] → الحقل الهدف"`)، تلميح إرشادي، `QScrollArea` بقائمة صفوف (`QButtonGroup` من `QRadioButton`)؛ لكل instance في المجموعة المصدر يبني صفاً عبر `_add_instance_row`. **سلوك خاص:** إذا كان هناك instance واحد فقط متاح (وله قيمة صالحة)، يُحدَّد تلقائياً لكن الـ Dialog يبقى مفتوحاً وينتظر ضغط المستخدم الصريح على "تطبيق". إطار معاينة نتيجة (مخفي افتراضياً حتى الاختيار)، ثم أزرار إلغاء/تطبيق (`btn_ok` معطّل حتى يتم اختيار صف صالح).
- **`_add_instance_row(self, inst)`**: يبني صفاً بإطار قابل للنقر (`mousePressEvent` مُعاد تعريفه على مستوى الـ instance عبر دالة متداخلة `_frame_click`) يحوي: Radio button (معطّل تلقائياً إن لم توجد قيمة فعلية للحقل المصدر لهذا الـ instance)، اسم الـ instance، قيمة الحقل المصدر (أو رسالة "لا توجد قيمة")، وليبل نتيجة محسوبة (`= النتيجة` أو `+/-offset = النتيجة`). يخزّن `instance_id` و`src_val` كـ Qt Properties مباشرة على الـ radio نفسه (وليس فقط في القاموس) لتبسيط الوصول لاحقاً من `_on_instance_selected`.
- **`_on_instance_selected(self, btn)`**: يستخرج `instance_id`/`src_val` من الـ properties، يحدّث `selected_instance_id`، يفعّل `btn_ok`، ويبني نص معاينة النتيجة النهائية (بصيغة `dim_src_preview_fmt` أو صيغة مبسطة إن كان `offset == 0`).
- **`get_selected(self) -> int | None`**: API عام يرجع `selected_instance_id` النهائي بعد إغلاق الـ Dialog بنجاح — هذه هي نقطة الاستدعاء الوحيدة التي يستخدمها المستدعي الخارجي (`_instance_popup.py`).
- **`_refresh_style(self, *_)`**: تلوين بسيط لخلفية الـ Dialog فقط.

---

## 20. `ui/tabs/design/dimension_sets/_values_panel.py`

**الغرض:** اللوحة الحاوية الرئيسية لتبويب "إدخال المقاسات" — تجمع `_SetsListPanel` (يسار، قائمة كروت المجموعات) و`_InstancesTable` (يمين، جدول القيم) في `QSplitter` أفقي، وتنسّق التنقل بينهما.

**الـ imports الداخلية المهمة:**
- `.values_panel._sets_list_panel._SetsListPanel`
- `.values_panel._instances_table._InstancesTable`

**من يستدعي هذا الملف:** `dimension_sets_tab.py` (مؤكَّد — `DimensionSetsTab` يستورد `_ValuesPanel` مباشرة ويصل لـ `_values_panel._sets_list` من خارج الكلاس أيضاً).

### Class: `_ValuesPanel(QWidget, WidgetMixin)`
- **`__init__(self, conn, parent=None)`**: `_set_id = None`، يبني، يفعّل `WidgetMixin(lang=False, data=False)`.
- **`showEvent(self, event)`**: يستدعي `super()` ثم `_refresh_style()` صراحة — تعليق كود يشير لنفس مشكلة "stale repaint" الموثّقة تفصيلياً في `_InstancesTable.showEvent`.
- **`_refresh_style(self, *_)`**: يستدعي `_on_font_changed` على كل من `_sets_list` و`_table`، يلوّن حدود الـ splitter، وخلفية/حدود `_sets_list`؛ تعليق كود يوضّح أن التلوين الخارجي المفروض على `_table` (`_InstancesTable`) أُزيل عمداً من هنا لأن ذلك المكوّن يدير خلفيته الداخلية بالكامل بنفسه.
- **`_build(self)`**: `QSplitter` أفقي يحوي `_sets_list` (`_SetsListPanel`، بعرض أدنى/أقصى محدد) و`_table` (`_InstancesTable`)؛ يربط `_sets_list.set_selected → self._on_set_selected`؛ يضبط أحجام الـ splitter ويمنع الطي على الجانبين.
- **`load_set(self, set_id: int)`**: يخزّن `_set_id` ويستدعي `self._sets_list._on_card_click(set_id)` (محاكاة نقرة برمجية على الكارت المطابق).
- **`_on_set_selected(self, set_id: int)`**: يخزّن `_set_id` ويستدعي `self._table.load_set(set_id)`.
- **`clear(self)`**: يصفّر `_set_id` ويستدعي `self._table.clear()`.

---

## 21. `ui/tabs/design/dimension_sets/values_panel/_instance_popup.py`

**الغرض:** Dialog Popup لإدخال/تعديل قيم instance واحد ضمن مجموعة مقاسات — يبني `QDoubleSpinBox` ديناميكياً لكل حقل رقمي في المجموعة، مع دعم "حساب تلقائي" (⟳) لأي حقل له اعتمادية معرَّفة (سواء same-set أو cross-set عبر `_SourcePickerDialog`)، وزر "حساب الكل" يحسب كل الحقول التلقائية دفعة واحدة بذكاء (يسأل عن المصدر مرة واحدة فقط لكل مجموعة مصدر فريدة).

**الـ imports الداخلية المهمة:**
- `services.design.dimension_set_service.DimensionSetService`
- `ui.tabs.design.dimension_sets._source_picker_dialog._SourcePickerDialog`

**من يستدعي هذا الملف:** `values_panel/_instances_table.py` (مؤكَّد — يستدعيه في `_add_instance` و`_edit_instance`).

### دالة top-level: `_row_val(row, key, default=None)`
دالة مساعدة آمنة تستخرج قيمة من `sqlite3.Row` عبر مفتاح، وترجع `default` عند `IndexError`/`KeyError` أو إن كانت القيمة `None` — تحل مشكلة عدم دعم `sqlite3.Row.get()`.

### Class: `_InstancePopup(QDialog, WidgetMixin)`
**Signal:** `saved = pyqtSignal(int)` (يحمل `instance_id`)

- **`__init__(self, conn, set_id, instance_id=None, parent=None)`**: `_spins: dict = {}` (field_id → QDoubleSpinBox)، يحدد عنوان النافذة حسب وضع إضافة/تعديل، يبني الواجهة، وإن كان تعديلاً يستدعي `_load_values()`.
- **`_build(self)`**: هيدر + صف اسم الـ instance + فاصل + عنوان "قيم" + `QScrollArea` بشبكة (`QGridLayout`) تحوي: لكل حقل رقمي (`field_type == "number"`) — ليبل، `QDoubleSpinBox`، ليبل وحدة، وزر "⟳" حساب تلقائي إضافي فقط إن كان للحقل `source_field_id` (اعتمادية معرَّفة). إن لم توجد حقول رقمية إطلاقاً، يعرض رسالة فارغة. أسفل ذلك: زر "حساب الكل" (يظهر فقط إن وُجد حقل تلقائي واحد على الأقل)، ثم زري إلغاء/حفظ.
- **`_load_values(self)`**: يجلب `get_instance_values(instance_id)` ويملأ كل `QDoubleSpinBox` بالقيمة المخزَّنة إن وُجدت.
- **`_pick_source_instance(self, field_id: int) -> int | None`**: دالة مساعدة مركزية — تجلب `get_field_dependency(field_id)`؛ إن لم توجد اعتمادية ترجع `None`؛ إن كانت same-set (`source_set_id is None`) ترجع `self.instance_id` مباشرة بدون أي حوار؛ إن كانت cross-set تفتح `_SourcePickerDialog` **دائماً** (حتى لو كان هناك instance واحد فقط في المصدر — تصريح صريح في التعليقات بأن المستخدم يجب أن يؤكد يدوياً كل مرة)، وترجع `dlg.get_selected()` أو `None` إن أُلغي.
- **`_calc_one(self, field_id: int, spin)`**: يضمن حفظ instance مؤقت أولاً إن لم يكن محفوظاً بعد (`_save_temp`) لأن الحساب same-set يحتاج `instance_id` فعلياً موجوداً؛ same-set: يحسب مباشرة عبر `calc_same_set_auto` (أو يعرض رسالة "لا توجد قيمة مصدر")؛ cross-set: يستدعي `_pick_source_instance`، ثم `get_field_value(source_instance_id, source_field_id)`، يجمع مع `offset` ويضبط قيمة الـ spin (أو رسالة "لا توجد قيمة عبر المجموعات").
- **`_calc_all_auto(self)`**: يضمن حفظ instance مؤقت أولاً؛ يمرّ على كل الحقول الرقمية ذات اعتمادية: same-set تُحسب مباشرة بدون أي حوار؛ cross-set تُجمَّع في `source_instance_map: dict` بحيث يُسأل المستخدم **مرة واحدة فقط** لكل `source_set_id` فريد (وليس لكل حقل)، وتُستخدم نفس الإجابة لكل الحقول التي تعتمد على نفس المجموعة المصدر؛ إن ألغى المستخدم اختيار مجموعة معينة، تُتخطى كل حقولها بصمت (`continue`) دون إيقاف باقي العملية.
- **`_save_temp(self)`**: يحفظ instance جديداً إن لم يكن موجوداً (بالاسم الحالي في الحقل)، ويحفظ كل القيم الحالية من الـ spins — يُستخدم فقط داخلياً لتمكين الحساب التلقائي قبل الحفظ النهائي الصريح.
- **`_save(self)`**: يحفظ الاسم (تحديث أو إنشاء)، يحفظ كل قيم الـ spins، يُطلق `saved(instance_id)`، ويقبل الـ Dialog.

---

## 22. `ui/tabs/design/dimension_sets/values_panel/_instances_table.py`

**الغرض:** جدول عرض/إدارة كل instances مجموعة مقاسات معينة (يمين تبويب إدخال المقاسات) — يعرض كل instance كصف مع قيم كل حقولها الرقمية كأعمدة، بأزرار إضافة/تعديل/نسخ/حذف، وحالة فارغة عند عدم اختيار مجموعة.

**الـ imports الداخلية المهمة:**
- `services.design.get_dimension_set_service`
- `._instance_popup._InstancePopup`

**من يستدعي هذا الملف:** `_values_panel.py` (مؤكَّد — يُنشئ `_InstancesTable` ويستدعي `load_set`/`clear`/`_on_font_changed`).

### دوال top-level: `_btn_danger_ss(base)`, `_btn_ghost_ss(base)`, `_btn_primary_ss(base)` — كلها `-> str`
ثلاث دوال تبني QSS نصياً لأنماط أزرار مختلفة (خطر/شفاف/أساسي)، تقرأ `_C` مباشرة عند كل استدعاء (لا تجميد) وتأخذ `base` (حجم الخط) كمعامل لحساب الأحجام النسبية عبر `fs()`.

### Class: `_InstancesTable(QWidget, WidgetMixin)`
- **`__init__(self, conn, parent=None)`**: `_set_id = None`، `_fields = []`، يبني، يفعّل `WidgetMixin(lang=False, data=False)`.
- **`showEvent(self, event)`**: يستدعي `_refresh_style()` صراحة عند الظهور الفعلي — تعليق كود مُفصَّل جداً يشرح مشكلة Qt الشهيرة: الـ stylesheet يتحدث في الذاكرة حتى لو الـ widget مخفية، لكن الرسم الفعلي (repaint) قد يبقى بحالة قديمة (cached) حتى تظهر الـ widget فعلياً — لذا يُجبَر إعادة التطبيق الكامل هنا.
- **`_refresh_style(self, *_)`**: يلوّن `self` نفسها مباشرة (`background: bg_input` — موثّق كـ "[إصلاح dark-theme الجذري]" لأن الـ QWidget الأب بدون stylesheet خاص كان يأخذ الخلفية الافتراضية لنظام التشغيل)، يلوّن ليبل اسم المجموعة، الأزرار الأربعة، الجدول (`_table_ss()`)، شريط الحالة، وحالة الفراغ (مع إجبار `unpolish`/`polish`/`update()` لضمان إعادة الرسم الفعلي — موثّق بتعليق "[إصلاح repaint]" منفصل)، ثم إجبار إعادة رسم شاملة على مستوى الـ widget بالكامل كحماية إضافية.
- **`_on_font_changed(self, size=None)`**: يبقيها متوافقة مع نداءات خارجية قديمة من `_ValuesPanel` — تستدعي `_refresh_style()`.
- **`_table_ss(self) -> str`**: يبني QSS كامل للجدول (خلفية، تناوب صفوف، خطوط شبكة، تحديد، رأس الجدول) — قراءة حية لـ `_C`.
- **`_build(self)`**: Toolbar (ليبل اسم المجموعة + 4 أزرار: إضافة/تعديل/نسخ/حذف — كلها معطّلة افتراضياً حتى تحميل مجموعة)، `QTableWidget` (اختيار صفوف كاملة، بدون تحرير مباشر، تناوب ألوان، رأس أفقي بمحاذاة يمين، آخر عمود Stretch)، شريط حالة سفلي، وحالة فراغة (أيقونة + رسالة + تلميح) — الجدول وشريط الحالة يبدآن مخفيين والحالة الفارغة ظاهرة.
- **`load_set(self, set_id: int)`**: يفعّل زر الإضافة، يجلب اسم المجموعة (مع fallback باسم افتراضي عند الخطأ)، يجلب الحقول الرقمية فقط (`_fields`)، يخفي حالة الفراغ ويظهر الجدول/الشريط، يستدعي `_refresh_table()`.
- **`_refresh_table(self)`**: يحفظ الصف المحدد سابقاً، يعيد بناء الأعمدة (اسم + كل حقل رقمي)، يضبط أوضاع تحجيم الأعمدة (تفاعلي لكل الأعمدة عدا الأخير Stretch)، يبني صفاً لكل instance مع ارتفاع محسوب من حجم الخط (`fs(base,0)*3 + padding`)، يلوّن اسم الـ instance بلون مميّز وخط عريض، ولكل حقل رقمي: يعرض القيمة منسّقة مع الوحدة أو نص "فارغ" بلون باهت إن لم توجد قيمة. يحدّث شريط الحالة بالعدد، يستعيد التحديد السابق إن كان لا يزال صالحاً، ويحدّث حالة تفعيل الأزرار.
- **`_selected_instance_id(self)`**: نمط قياسي — `id` من `Qt.UserRole` بالعمود صفر للصف المحدد.
- **`_on_select(self)`**: يستدعي `_update_action_btns()`.
- **`_update_action_btns(self)`**: يفعّل/يعطّل أزرار تعديل/نسخ/حذف حسب وجود تحديد فعلي.
- **`_add_instance(self)`**: يتحقق من وجود `_set_id`، يفتح `_InstancePopup` (وضع إضافة)، يربط `saved → _on_saved`.
- **`_edit_instance(self)`**: يتحقق من وجود تحديد، يفتح `_InstancePopup` بوضع تعديل، يربط `saved → _on_saved`.
- **`_copy_instance(self)`**: يجلب اسم الـ instance المحدد، يعرض `QInputDialog.getText` باسم مقترح افتراضي (`"نسخة من {الاسم}"`)، وعند التأكيد يستدعي `duplicate_instance` ويحدّث الجدول.
- **`_delete_instance(self)`**: يعرض تأكيد حذف مخصص باسم الـ instance (أو `#id` إن لم يكن له اسم)، وعند الموافقة يحذف ويحدّث الجدول.
- **`_on_saved(self, instance_id: int)`**: يحدّث الجدول بالكامل، ثم يبحث عن الصف المطابق لـ `instance_id` المحفوظ حديثاً ويحدّده تلقائياً (تجربة مستخدم سلسة بعد الحفظ).
- **`clear(self)`**: يصفّر كل الحالة (`_set_id`, `_fields`)، يفرّغ الجدول تماماً (صفوف وأعمدة)، يخفي الجدول/الشريط، يظهر حالة الفراغ، يعطّل كل الأزرار.

---

## 23. `ui/tabs/design/dimension_sets/values_panel/_sets_list_panel.py`

**الغرض:** قائمة كروت (وليس جدولاً) لمجموعات المقاسات — يسار تبويب "إدخال المقاسات" — كل كارت يعرض اسم المجموعة، تصنيفها، وحدتها، عدد حقولها، وعدد الـ instances المسجلة كـ badge، مع بحث وفلتر تصنيف.

**الـ imports الداخلية المهمة:**
- `services.design.get_dimension_set_service`

**من يستدعي هذا الملف:** `_values_panel.py` (مؤكَّد — يُنشئ `_SetsListPanel` ويستدعي `set_selected`, `_on_font_changed`, `refresh`).

### دوال top-level: `_card_normal_ss() -> str` / `_card_selected_ss() -> str`
تُرجعان QSS لحالتي الكارت (عادي بـ hover، أو محدد بحدود accent أثخن) — كلتاهما تقرأ `_C` حياً؛ تعليق كود مطوّل يوثّق أن هذه كانت module-level constants ثابتة سابقاً وتسببت في مشكلة "تجمّد الثيم" المطابقة لمشاكل ملفات أخرى، وتم تحويلها لدوال.

### Class: `_SetCard(ThemedFrame)`
**Signal:** `clicked = pyqtSignal(int)`

- **`__init__(self, set_id, name, category, unit, fields_cnt, instances_cnt, parent=None)`**: يخزّن `set_id`، `_selected=False`، يضبط المؤشر (Pointing Hand)، يطبّق الستايل العادي، يبني المحتوى عبر `_build`.
- **`_build(self, name, category, unit, fields_cnt, instances_cnt)`**: أيقونة + عمود نصي (اسم بخط عريض + سطر معلومات ثانوي "تصنيف • وحدة • عدد حقول") + شارة (badge) دائرية بعدد الـ instances.
- **`refresh_font(self)`**: يُستدعى عند تغيّر حجم الخط أو الثيم — يعيد بناء كل الأنماط النصية الداخلية (اسم، معلومات، badge) **و** يعيد تطبيق ستايل الكارت نفسه (`_card_selected_ss()` أو `_card_normal_ss()` حسب `_selected`) — تعليق كود يوثّح أن هذا ضروري لأن الكارت كان يتلون فقط وقت `__init__`.
- **`set_selected(self, sel: bool)`**: يحدّث `_selected` ويعيد تطبيق الستايل المطابق فوراً.
- **`mousePressEvent(self, event)`**: يُطلق `clicked(set_id)` قبل تمرير الحدث لـ `super()`.

### Class: `_SetsListPanel(QWidget, WidgetMixin)`
**Signal:** `set_selected = pyqtSignal(int)`

- **`__init__(self, conn, parent=None)`**: `_cards: dict = {}`، `_active_id = None`، `_all_rows = []`، يبني، يحمّل، يفعّل `WidgetMixin(lang=False, data=False)`.
- **`showEvent(self, event)`**: مطابق تماماً لـ `_InstancesTable.showEvent` — يستدعي `_refresh_style()` صراحة عند الظهور الفعلي.
- **`_refresh_style(self, *_)`**: يلوّن الهيدر، حقل البحث، عداد النتائج، **وكل الكروت الموجودة حالياً** عبر استدعاء `card.refresh_font()` لكل واحد منها، بالإضافة لخلفيات `_search_frame`, `_cmb_cat`, `_scroll`, `_cards_widget`.
- **`_on_font_changed(self, size=None)`**: يبقيها متوافقة مع نداءات خارجية قديمة من `_ValuesPanel` — تستدعي `_refresh_style()`.
- **`_build(self)`**: هيدر ثابت، إطار بحث (حقل بحث + `cmb_cat` فلتر تصنيف بعرض أقصى محدود)، `QScrollArea` بعمود رأسي من الكروت (`_cards_layout` مع `addStretch()` نهائي لدفع الكروت لأعلى)، وليبل عداد نتائج سفلي.
- **`_reload_cat_filter(self)`**: يبني `_cmb_cat` من شجرة التصنيفات مع حفظ الاختيار السابق.
- **`_add_cat_nodes(self, nodes, depth)`**: تكرارية قياسية.
- **`_load(self)`**: يحمّل `_all_rows` من `list_sets()`، يعيد الفلتر، يطبّق العرض.
- **`_apply_filter(self)`**: يمسح كل الكروت الحالية، يمرّ على `_all_rows` مطبقاً فلتري البحث والتصنيف، لكل مجموعة مطابقة يحسب `count_fields_for_set` و`count_instances_for_set` ثم ينشئ `_SetCard` جديداً، يربط `clicked → _on_card_click`، يحافظ على حالة التحديد السابقة (`_active_id`)، ويُدرجه قبل الـ `addStretch()` الأخير في الـ layout. يحدّث نص العداد (صيغة "الكل" إن تساوى المعروض بالإجمالي، أو صيغة "مفلتر" بعرض العددين).
- **`_on_card_click(self, set_id: int)`**: يلغي تحديد الكارت النشط السابق، يحدد الكارت الجديد، ويُطلق `set_selected`.
- **`refresh(self)`**: يعيد `_load()`، وإن كان هناك `_active_id` محفوظ يعيد إطلاق `set_selected` به (لإعادة مزامنة الجدول المرتبط).
- **`refresh_card(self, set_id: int)`**: يعيد `_load()` بالكامل (تعليق يشير لكونها بديلاً بسيطاً غير محسَّن — لا تحدّث كارتاً واحداً فقط رغم التوقيع الذي يوحي بذلك).

---

## قسم علاقات الملفات

### تسلسل البناء الهرمي (Composition Tree)
```
design_section.py
 ├── DimensionSetsTab (dimension_sets_tab.py)
 │    ├── _ValuesPanel (dimension_sets/_values_panel.py)
 │    │    ├── _SetsListPanel (dimension_sets/values_panel/_sets_list_panel.py)
 │    │    │    └── _SetCard (نفس الملف)
 │    │    └── _InstancesTable (dimension_sets/values_panel/_instances_table.py)
 │    │         └── _InstancePopup (dimension_sets/values_panel/_instance_popup.py)
 │    │              └── _SourcePickerDialog (dimension_sets/_source_picker_dialog.py)
 │    └── _GroupsPanel (dimension_sets/_groups_panel.py)
 │         ├── _CategoriesPanel (dimension_sets/_categories_panel.py)
 │         └── _SetsManagerPanel (نفس ملف _groups_panel.py)
 │              └── _FieldsPanel (dimension_sets/_fields_panel.py)
 │                   └── _FieldDialog (dimension_sets/_field_dialog.py)
 └── DesignsTab (designs_tab.py)
      ├── DesignsCategoriesPanel (designs/_designs_categories_panel.py)
      │    └── _CatRow, _CatForm (designs/designs_categories/_row_and_form.py)
      ├── _DesignsTable (designs/_designs_table.py)
      │    └── _DesignCard, _ThumbWorker (designs/designs_table/_design_card.py)
      └── _DesignDetailPanel (designs/_design_detail_panel.py)
           └── _SizeCard (designs/_size_card.py)
                └── _ThumbnailWidget وأدوات GIMP (designs/size_card/helper.py)
           └── _SizeDialog (designs/_size_dialog.py)
```

### استيرادات مباشرة بين ملفات هذا المرجع
- `design_section.py` → `dimension_sets_tab.DimensionSetsTab`, `designs_tab.DesignsTab`
- `dimension_sets_tab.py` → `dimension_sets/_values_panel._ValuesPanel`, `dimension_sets/_groups_panel._GroupsPanel`
- `dimension_sets/_values_panel.py` → `values_panel/_sets_list_panel._SetsListPanel`, `values_panel/_instances_table._InstancesTable`
- `dimension_sets/values_panel/_instances_table.py` → `values_panel/_instance_popup._InstancePopup`
- `dimension_sets/values_panel/_instance_popup.py` → `dimension_sets/_source_picker_dialog._SourcePickerDialog`
- `dimension_sets/_groups_panel.py` → `dimension_sets/_categories_panel._CategoriesPanel`, `dimension_sets/_fields_panel._FieldsPanel`
- `dimension_sets/_fields_panel.py` → `dimension_sets/_field_dialog._FieldDialog`
- `designs_tab.py` → `designs/_designs_table._DesignsTable`, `designs/_design_detail_panel._DesignDetailPanel`, `designs/_designs_categories_panel.DesignsCategoriesPanel`
- `designs/_designs_table.py` → `designs/_design_detail_panel._DesignDetailPanel`, `designs/_xcf_thumbnail` (`get_watcher`, `clear_cache`), `designs/designs_table/_design_card` (`_DesignCard`, `_ThumbWorker`)
- `designs/_design_detail_panel.py` → `designs/_size_card._SizeCard`, `designs/_size_dialog._SizeDialog`, `design_styles.get_styles`
- `designs/_size_card.py` → `designs/_xcf_thumbnail.get_watcher`, `designs/size_card/helper` (عدة رموز)
- `designs/_designs_categories_panel.py` → `designs/designs_categories/_row_and_form` (`_btn_ss`, `_CatForm`, `_CatRow`)، `design_styles.get_styles`

**ملاحظة:** `dimension_sets/_sets_panel.py` هو الملف الوحيد في هذا المرجع الذي لم يظهر أي استدعاء مباشر له من باقي الـ 22 ملفاً المرفقة — استخدامه الفعلي غير مؤكَّد من هذه الدفعة.

### نمط بناء مشترك (Shared Patterns)
- **نمط `WidgetMixin` الموحّد:** كل الكلاسات الرئيسية (تقريباً بدون استثناء) ترث `WidgetMixin` وتستدعي `self._init_widget_mixin(lang=False, data=False)` (أو مع `theme=True/font=True` صراحة عند الحاجة لتحديثات لغة/خط) في نهاية `__init__`، مع دالة `_refresh_style(self, *_)` منفصلة تُستدعى تلقائياً عند تغيّر الثيم.
- **نمط "إصلاح dark-theme":** تعليقات كود متكررة عبر كل الملفات تقريباً توثّق مشكلة واحدة جوهرية متكررة: عناصر واجهة كانت تُلوَّن مرة واحدة فقط وقت `_build`/`__init__` (أو حتى كـ module-level constants ثابتة وقت الـ import الأول)، فتتجمّد على ألوان الثيم الأول ولا تستجيب لتبديل الثيم اللاحق. الحل المتكرر: تحويل الألوان لدوال/properties تُقرأ حياً من `_C`، وإعادة تطبيقها صراحة داخل `_refresh_style`.
- **نمط `_selected_id()` / `Qt.UserRole`:** يتكرر حرفياً في `_sets_panel.py`, `_groups_panel.py` (`_SetsManagerPanel`), `_categories_panel.py` — تخزين المعرّف الفعلي في العمود الأول من الجدول عبر `Qt.UserRole` واستخراجه لاحقاً بدل الاعتماد على النص المعروض.
- **نمط بناء شجرة تصنيفات تكراري:** دالة `_add_*_nodes(nodes, depth, ...)` تتكرر بنفس البنية تقريباً (مسافة بادئة + سهم حسب العمق) في: `_sets_panel.py`, `_categories_panel.py`, `_field_dialog.py`, `_groups_panel.py`, `_design_detail_panel.py`, `_designs_categories_panel.py`, `_sets_list_panel.py`.
- **نمط فورم "إضافة/حفظ/إلغاء" مدمج:** يتكرر في `_categories_panel.py`, `_groups_panel.py` (`_SetsManagerPanel`) — Label "وضع" يتغيّر نصه، وأزرار تتبادل الظهور (`setVisible`) بين وضعي "إضافة" (زر واحد) و"تعديل" (زران: حفظ/إلغاء).
- **نمط Cross-set Dependency:** منطق الاعتمادية بين حقول مجموعات مختلفة يتكرر بثبات عبر `_field_dialog.py` (تعريف الاعتمادية)، `_instance_popup.py` (تنفيذ الحساب)، و`_source_picker_dialog.py` (اختيار المصدر) — كلها تتفق على نفس المعنى: `source_set_id = None` يعني "نفس المجموعة".

### تبعيات على ملفات خارج نطاق هذا المرجع (تفصيلها من مسؤولية مرجعها الخاص)
- `services.design` (`get_design_service`, `get_design_size_service`, `get_dimension_set_service`, `dimension_set_service.DimensionSetService`, `get_designs_conn_and_init`)
- `ui.theme._C`, `ui.theme_manager`
- `ui.font` (`get_font_size`, `fs`, `FS_*`)
- `ui.widgets.core.i18n.tr`
- `ui.widgets.core.widget_mixin.WidgetMixin`
- `ui.widgets.panels.themed_inputs` (`ThemedLineEdit`, `ThemedComboBox`, `ThemedFrame`)
- `ui.widgets.tables.tables` (`make_table`, `refresh_table_styles`)
- `ui.widgets.components.button` (`make_btn`, `refresh_visible_buttons`)
- `ui.widgets.combo.unit.UnitCombo`
- `ui.widgets.dialogs.confirm.confirm_delete`
- `ui.widgets.theme.layout_styles` (`tab_style`, `apply_tab_widths`, `normalize_tab_widget`)
- `ui.constants` (عشرات الثوابت الرقمية عبر كل الملفات)
