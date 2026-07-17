# ui_tabs_orders — ملف مرجعي

يغطي: `ui/tabs/orders_section.py` + مجلد `ui/tabs/orders/` وكل ملفاته الفرعية.

---

## `ui/tabs/orders_section.py`

**الغرض:** القسم الرئيسي (top-level section) لإدارة الطلبات والعملاء؛ يبني هيدر القسم وتاب ويدجت يحتوي 3 تابات فرعية: لوحة المتابعة (Dashboard)، الطلبات (Orders)، العملاء (Customers).

**Imports داخلية مهمة:**
- `services.orders.order_service.get_orders_conn_and_init` — يفتح/يهيئ اتصال قاعدة بيانات orders.db.
- `ui.tabs.orders.orders_tab.OrdersTab`, `ui.tabs.orders.customers_tab.CustomersTab`, `ui.tabs.orders.dashboard_tab.OrdersDashboardTab` — التابات الفرعية الثلاثة.
- `ui.widgets.theme.layout_styles` (`tab_style`, `apply_tab_widths`, `normalize_tab_widget`) — ستايل وتوحيد شكل QTabWidget.
- `ui.widgets.core.widget_mixin.WidgetMixin` — آلية الاشتراك المركزية في تغييرات الثيم/الخط/اللغة/الداتا.

**من يستدعيه:** غير محدد من المرفقات الحالية (على الأغلب main_window أو ملف تجميع الأقسام الرئيسي، لكن غير مؤكد من المرفقات).

### Class: `OrdersSection(QWidget, WidgetMixin)`
- **Attributes:** `self.conn` (اتصال orders.db)، `self._header` (QLabel)، `self._tabs` (QTabWidget)، `self._dashboard_tab`, `self._orders_tab`, `self._customers_tab`.
- **`__init__(self, parent=None)`**: يفتح الاتصال عبر `get_orders_conn_and_init()`، يبني الواجهة، يفعّل WidgetMixin بـ `theme=True, font=False, lang=True, data=False`، ثم يستدعي `_refresh_style()`.
- **`_refresh_style(self, *_)`**: يعيد تطبيق ستايل الهيدر (لون `_C['success']`) وستايل التابات (`tab_style()` + `apply_tab_widths`). ملاحظة كود: [إصلاح dark-theme] — كان القسم غير مشترك في `bus.theme_changed` قبل هذا الإصلاح (theme=False)، فكان التاب بار يفضل بالستايل الفاتح القديم بعد التحويل لـ dark.
- **`_build(self)`**: يبني `QVBoxLayout` بلا هوامش، يضيف هيدر (`QLabel` بارتفاع ثابت `SECTION_HEADER_HEIGHT`)، ثم `QTabWidget` مطبَّع عبر `normalize_tab_widget`، يضيف 3 تابات (Dashboard, Orders, Customers) بالترتيب، ويربط `currentChanged` بـ `_on_tab_changed`.
- **`_refresh_lang(self, *_)`**: يحدّث نص الهيدر وعناوين التابات الثلاثة عبر `tr()`، ثم `apply_tab_widths`.
- **`_on_tab_changed(self, index)`**: عند التبديل، يستدعي `refresh()` على التاب المطابق (0=dashboard, 1=orders, 2=customers).
- **`closeEvent(self, event)`**: يغلق `self.conn` بأمان (try/except) قبل تمرير الحدث لـ super.

**ملاحظات مهمة:** تعليق صريح يشرح إصلاح مشكلة الثيم القديمة بسبب عدم الاشتراك في bus.theme_changed.

---

## `ui/tabs/orders/orders_tab.py`

**الغرض:** تبويب "الطلبات" — يجمع قائمة الطلبات ولوحة تفاصيل الطلب في splitter واحد عبر النمط الموحّد `BaseSection`.

**Imports داخلية:**
- `ui.tabs.orders._order_detail._OrderDetail` — لوحة تفاصيل الطلب.
- `ui.tabs.orders.orders._orders_list_panel._OrdersListPanel` — قائمة الطلبات.
- `ui.widgets.base.section.BaseSection` — الكلاس الأب الموحّد (list+detail+splitter).
- `ui.constants.ORDERS_LIST_MIN_W`, `ORDERS_SPLITTER_FIT_DELAY_MS`.

**من يستدعيه:** `ui/tabs/orders_section.py` (يبنيه كأحد التابات الثلاثة).

### Class: `OrdersTab(BaseSection)`
- **Class attribute:** `LIST_MIN_W = ORDERS_LIST_MIN_W`.
- **`__init__(self, conn, parent=None)`**: يحفظ `self._conn`، يستدعي `super().__init__(conn=conn, parent=parent)`.
- **`_create_list(self)`**: يرجع `_OrdersListPanel(self._conn)`.
- **`_create_detail(self)`**: يرجع `_OrderDetail(self._conn)`.
- **`_connect_signals(self)`**: يربط: `order_selected`→`_on_order_selected`, `new_order`→`_on_new_order`, `detail.saved`→`_on_saved`, `detail.deleted`→`_on_deleted`, `detail.status_changed`→`_on_status_changed`، وكمان `_list._filter_bar.changed`→`_fit_splitter_delayed` (لضبط عرض الـ splitter عند تغيير الفلتر).
- **`_on_order_selected(self, order_id: int)`**: يحمّل تفاصيل الطلب في اللوحة (`self._detail.load_order`).
- **`_on_new_order(self)`**: يفتح فورم طلب جديد عبر `self._detail.new_order()`.
- **`_on_saved(self, order_id: int)`**: يعيد تحميل القائمة، يحدد الطلب المحفوظ، يضبط الـ splitter.
- **`_on_deleted(self)`**: يعيد تحميل القائمة، يمسح تفاصيل اللوحة، يضبط الـ splitter.
- **`_on_status_changed(self, order_id: int)`**: يعيد تحميل القائمة، يحدد الطلب، يعيد تحميل تفاصيله.
- **`_fit_splitter_delayed(self, *args)`**: wrapper يتجاهل أي arguments قادمة من الإشارات، وينفذ `QTimer.singleShot(ORDERS_SPLITTER_FIT_DELAY_MS, self._apply_sizes)`.

**ملاحظات مهمة:** [إصلاح] `BaseSection` لا توفر `_fit_splitter_delayed` أصلاً؛ الكود القديم كان يستدعي `super()._fit_splitter_delayed()` بافتراض وجودها في الأب فيسبب `AttributeError` عند أي حفظ/حذف/تغيير حالة. الأب يوفر فقط `_apply_sizes()` بدون تأخير قابل للتخصيص، فتم تعريف الدالة محلياً هنا عبر `QTimer` مباشرة.

---

## `ui/tabs/orders/dashboard_tab.py`

**الغرض:** تبويب "لوحة المتابعة" — يعرض بطاقات إحصائية علوية، شبكة توزيع الحالات، وجدول آخر الطلبات، مع زر تحديث.

**Imports داخلية:**
- `services.orders.order_service.OrderService` — جلب ملخص الداشبورد وقائمة الطلبات.
- `ui.widgets.core.widget_mixin.WidgetMixin`.
- `.dashboard._top_cards.build_top_cards`, `.dashboard._status_grid.build_status_grid`, `.dashboard._recent_table.build_recent_table`/`fill_recent_table` — دوال بناء منفصلة لكل قسم من الداشبورد.

**من يستدعيه:** `ui/tabs/orders_section.py`.

### Class: `OrdersDashboardTab(QWidget, WidgetMixin)`
- **`__init__(self, conn, parent=None)`**: يحفظ `self.conn`، ينشئ `OrderService`، يبني الواجهة، يفعّل WidgetMixin بـ `theme=True, font=False, lang=True, data=False`.
- **`_refresh_style(self, *_)`**: يستدعي `refresh_table_styles(self)` من `ui.widgets.tables.tables` لإعادة تطبيق ستايل الجدول. ملاحظة: [إصلاح dark-theme] الجدول مبني عبر `make_table()` التي تطبّق `table_style()` مرة واحدة فقط وقت الإنشاء؛ بدون هذا الاستدعاء يبقى الجدول بالستايل الفاتح القديم بعد تغيير الثيم، لأن الكلاس أصلاً لم يكن مشتركاً في bus (theme=False قديماً) ولا يملك `_refresh_style()`.
- **`_refresh_lang(self, *_)`**: يحدّث نصوص عناوين الحالة، الطلبات الحديثة، وزر التحديث.
- **`_build(self)`**: يبني `QVBoxLayout` جذري، `QScrollArea` علوي (يحتوي البطاقات + شبكة الحالات) بارتفاع أقصى `DASHBOARD_SCROLL_MAX_H`، ثم هيدر "آخر الطلبات" مع زر تحديث، ثم حاوية الجدول.
- **`refresh(self)`**: يجلب `self._svc.get_dashboard_summary()`، يحدّث بطاقات (الإجمالي، العاجل، القيمة الإجمالية، المدفوع)، يحدّث شرائح الحالة (`chip.set_count`)، ويملأ الجدول عبر `fill_recent_table` بأول `DASHBOARD_RECENT_LIMIT` طلب من `self._svc.list_orders()`.

**Attributes مضافة ديناميكياً من دوال البناء الخارجية (عبر `build_top_cards`/`build_status_grid`/`build_recent_table`):** `_lbl_total`, `_lbl_urgent`, `_lbl_total_value`, `_lbl_total_paid`, `_status_chips` (dict), `recent_table`, `_lbl_status_hdr`, `_lbl_recent_hdr`, `_btn_refresh`.

---

## `ui/tabs/orders/dashboard/_config.py`

**الغرض:** دوال إعدادات (config) خاصة بلوحة المتابعة — تعيد قواميس الحالات، الأولويات، الأنواع، وأعمدة الجدول، كلها معتمدة على `tr()` و`_C` بحيث تكون ديناميكية مع تغيير اللغة/الثيم.

**Imports داخلية:** `ui.theme._C`, `ui.widgets.core.i18n.tr`, `ui.constants` (`DASHBOARD_RECENT_TABLE_COL_WIDTHS`, `DASHBOARD_TABLE_BORDER_PAD`).

**من يستدعيه:** `ui/tabs/orders/dashboard/_recent_table.py` (يستخدم `get_status_map`, `get_status_color`, `get_type_map`, `get_priority_map`, `get_table_cols`, `COL_WIDTHS`)، و`ui/tabs/orders/dashboard/_status_grid.py` (يستخدم `get_status_config`).

### دوال top-level:
- **`get_status_config() -> dict`**: يرجع لكل حالة طلب (pending, confirmed, in_progress, ready, delivered, cancelled, on_hold) tuple بشكل `(أيقونة_إيموجي, نص_مترجم, لون_رئيسي, لون_خلفية, لون_حدود)`.
- **`get_status_map() -> dict`**: يرجع لكل حالة نص واحد "أيقونة + نص مترجم" مدمج.
- **`get_status_color() -> dict`**: يرجع لكل حالة اللون الرئيسي فقط من `_C`.
- **`get_type_map() -> dict`**: يرجع أنواع الطلب (new, reorder, custom) مترجمة.
- **`get_priority_map() -> dict`**: يرجع الأولويات (low, normal, high, urgent) مترجمة.
- **`get_table_cols() -> list`**: يرجع قائمة عناوين أعمدة جدول "آخر الطلبات" مترجمة (رقم، عميل، نوع، حالة، أولوية، إجمالي، تاريخ).

**ثوابت module-level:** `COL_WIDTHS = DASHBOARD_RECENT_TABLE_COL_WIDTHS`، `TABLE_TOTAL_W = sum(COL_WIDTHS.values()) + DASHBOARD_TABLE_BORDER_PAD` (مجموع عرض الأعمدة + حشو الحدود).

---

## `ui/tabs/orders/dashboard/_top_cards.py`

**الغرض:** يبني صف البطاقات الإحصائية العلوية الأربعة (إجمالي الطلبات، العاجل، القيمة الإجمالية، المدفوع) للوحة المتابعة.

**Imports داخلية:** `ui.widgets.components.stat_card.make_stat_card_simple`, `ui.widgets.core.i18n.tr`, `ui.theme._C`, `ui.constants.DASHBOARD_TOP_CARDS_SPACING`.

**من يستدعيه:** `ui/tabs/orders/dashboard_tab.py` (`_build`).

### دالة top-level:
- **`build_top_cards(dashboard) -> QHBoxLayout`**: يبني `QHBoxLayout`، ينشئ 4 بطاقات (`make_stat_card_simple`) بألوان وأيقونات مختلفة (📋 accent, 🔴 danger, 💰 success, ✅ accent)، يحفظ الـ value labels الخاصة بكل بطاقة كـ attributes على `dashboard` (`_lbl_total`, `_lbl_urgent`, `_lbl_total_value`, `_lbl_total_paid`)، يضيف كل بطاقة للصف بـ `stretch=1`، يرجع الصف.

---

## `ui/tabs/orders/dashboard/_status_grid.py`

**الغرض:** يبني شبكة (grid) من شرائح (chips) توزيع حالات الطلبات للوحة المتابعة.

**Imports داخلية:** `ui.widgets.panels.layout_widgets.CardGrid`, `ui.widgets.components.status_chip.make_status_chip`, `ui.constants` (`CARD_GRID_DEFAULT_COLS`, `CARD_GRID_DEFAULT_SPACING`), `._config.get_status_config`.

**من يستدعيه:** `ui/tabs/orders/dashboard_tab.py` (`_build`).

### دالة top-level:
- **`build_status_grid(dashboard) -> CardGrid`**: يهيئ `dashboard._status_chips = {}`، ينشئ `CardGrid` بعدد أعمدة/تباعد افتراضيين، يمر على `get_status_config()` وينشئ لكل حالة `chip` عبر `make_status_chip(icon, label, 0, color)` ويحفظه في `dashboard._status_chips[status]`، يرجع الشبكة.

---

## `ui/tabs/orders/dashboard/_recent_table.py`

**الغرض:** بناء وتعبئة جدول "آخر الطلبات" في لوحة المتابعة.

**Imports داخلية:** `ui.widgets.tables.tables` (`make_table`, `insert_row`, `ROW_HEIGHT_NORMAL`, `auto_fit_columns`), `ui.widgets.core.i18n.tr`, `ui.theme._C`, `ui.font.FS_BASE`, `._config` (`get_status_map`, `get_status_color`, `get_type_map`, `get_priority_map`, `get_table_cols`, `COL_WIDTHS`).

**من يستدعيه:** `ui/tabs/orders/dashboard_tab.py` (`_build` يستدعي `build_recent_table`, `refresh` يستدعي `fill_recent_table`).

### دوال top-level:
- **`build_recent_table(dashboard)`**: ينشئ الجدول عبر `make_table(get_table_cols(), stretch_col=-1, col_widths=COL_WIDTHS)`، يحفظه في `dashboard.recent_table`، يرجعه.
- **`fill_recent_table(dashboard, orders: list)`**: يفرّغ الجدول، ولكل طلب: يضيف صف برقم الطلب (خط متوسط الوزن)، اسم العميل، نوع الطلب (مترجم)، الحالة (بلون من `status_color`، محاذاة وسط)، الأولوية (محاذاة وسط)، المبلغ الصافي منسّقاً مع رمز العملة، وتاريخ الطلب. في النهاية يستدعي `auto_fit_columns`.

**ملاحظة:** يستخدم `QTableWidgetItem` خام مباشرة (وليس `make_item`/`colored_item` الموحّدة المستخدمة في ملفات أخرى بالمشروع).

---

## `ui/tabs/orders/order_detail/_status_config.py`

**الغرض:** مصدر مركزي لكل تسميات وألوان وانتقالات حالات/أولويات/أنواع الطلبات، تُستخدم عبر كل ملفات order_detail وorders.

**Imports داخلية:** `ui.theme._C`, `ui.widgets.core.i18n.tr`.

**من يستدعيه:** عدد كبير من الملفات: `_status_dialog.py`, `_log_section.py`, `_header_fill.py`, `_order_detail.py` (يستورد `STATUS_TRANSITIONS`)، `_order_form.py`، `customer_detail_panel.py`، `_filter_toolbar.py`، `_orders_list_panel.py`، `_status_delegate.py`.

### دوال top-level:
- **`get_status_labels() -> dict`**: يرجع لكل حالة (7 حالات) tuple: `(نص "أيقونة+تسمية" مترجم, لون_نص, لون_خلفية, لون_حدود)` — الألوان من `_C` حسب نوع الحالة (warning/accent/purple/success/text_sec/danger/orange).
- **`get_status_transitions() -> dict`**: يرجع لكل حالة قائمة الحالات المسموح الانتقال إليها منها (مثال: pending → confirmed/cancelled/on_hold). delivered ليس له انتقالات، cancelled يمكن إعادته لـ pending فقط.
- **`get_priority_labels() -> dict`**: يرجع لكل أولوية (low, normal, high, urgent) tuple `(نص مترجم, لون)`.
- **`get_type_labels() -> dict`**: يرجع أنواع الطلب (new, reorder, custom) مترجمة كنصوص فقط.
- **`get_status_labels_short() -> dict`**: يرجع فقط الجزء الأول (النص) من `get_status_labels()` لكل حالة.
- **`get_status_colors() -> dict`**: يرجع لكل حالة الألوان الثلاثة فقط (بدون النص) من `get_status_labels()`.

**ثوابت module-level:** `STATUS_TRANSITIONS = get_status_transitions()` — للتوافق مع كود قديم يستورد الثابت مباشرة بدل استدعاء الدالة.

---

## `ui/tabs/orders/order_detail/_status_dialog.py`

**الغرض:** دايلوج تغيير حالة الطلب — يعرض الحالة الحالية، قائمة منسدلة بالحالات التالية الممكنة، وحقل ملاحظة اختياري.

**Imports داخلية:** `ui.widgets.panels.themed_inputs` (`ThemedLineEdit`, `ThemedComboBox`), `ui.theme._C`, `ui.font` (`FS_MD`, `FS_BASE`), `ui.widgets.components.button.make_btn`, `ui.widgets.theme.input_styles.input_style`, `ui.widgets.core.i18n.tr`, `ui.widgets.core.widget_mixin.WidgetMixin`, `._status_config` (`get_status_labels`, `get_status_labels_short`, `get_status_colors`).

**من يستدعيه:** `ui/tabs/orders/_order_detail.py` (`_change_status_dialog`).

### Class: `_StatusDialog(QDialog, WidgetMixin)`
- **Attributes:** `_current_status`, `_next_statuses` (list)، `_result` (tuple `(status, note)`، افتراضياً أول حالة تالية أو الحالة الحالية مع ملاحظة فارغة).
- **`__init__(self, current_status: str, next_statuses: list, parent=None)`**: يضبط الحد الأدنى للعرض، modal، يبني الواجهة، يطبق الستايل واللغة.
- **`_build(self, current, nexts)`**: يبني عناصر: `_lbl_hdr` (عنوان)، `_lbl_cur` (الحالة الحالية)، `_lbl_new_hint`، `_cmb` (ComboBox بالحالات التالية)، `_lbl_note_hint`، `_note` (ThemedLineEdit)، أزرار `_btn_cancel`/`_btn_ok`.
- **`_refresh_style(self, *_)`**: يطبق `input_style()` على الكومبو والملاحظة (**ملاحظة كود صريحة: لا تستخدم `self.setStyleSheet()` هنا لأنها تُخفي الأزرار**)، يلوّن الهيدر بلون accent، ويلوّن `_lbl_cur` حسب لون الحالة الحالية من `get_status_colors()`.
- **`_refresh_lang(self, *_)`**: يعيد ضبط عنوان النافذة، نص الحالة الحالية، محتوى الكومبو (مع الحفاظ على التحديد الحالي)، نصوص الملاحظة والأزرار، ويعيد حساب أقل عرض للأزرار عبر `calc_btn_width`.
- **`_save(self)`**: يخزّن `self._result = (self._cmb.currentData(), self._note.text().strip())` وينفّذ `accept()`.
- **`get_result(self)`**: يرجع `self._result`.

---

## `ui/tabs/orders/order_detail/_items_section.py`

**الغرض:** يبني ويعبّئ قسم "عناصر الطلب" داخل لوحة تفاصيل الطلب (`_OrderDetail`) — جدول العناصر + حالة فارغة + شريط أدوات تعديل/حذف.

**Imports داخلية:** `ui.widgets.panels.themed_inputs.ThemedFrame`, `ui.widgets.components.headers_page.SectionHeader`, `ui.widgets.panels.state.EmptyState`, `ui.widgets.components.button.make_btn`, `ui.widgets.tables.tables` (`make_table`, `insert_row`, `auto_fit_columns`, `make_item`, `bold_item`, `colored_item`, `muted_item`, `ROW_HEIGHT_NORMAL`), `ui.widgets.core.i18n.tr`, `ui.theme._C`.

**من يستدعيه:** `ui/tabs/orders/_order_detail.py` (`_build_content` يستدعي `_build_items_section`؛ `_fill_data`, `_add_item`, `_edit_item`, `_del_item` تستدعي `_fill_items`).

### دوال top-level (تأخذ `detail` — نسخة `_OrderDetail` — كمعامل وتضيف عليها attributes مباشرة):
- **`_build_items_section(detail)`**: يبني `SectionHeader` مع زر "إضافة عنصر" (`detail.btn_add_item`)، جدول عناصر (`detail.items_table`) بأعمدة (اسم، وصف، كمية، وحدة، سعر، خصم، إجمالي)، حالة فارغة (`detail._empty_items`) مربوطة بـ `action_clicked` لاستدعاء `detail._add_item`، وشريط أدوات (`detail._item_toolbar`) بزري تعديل/حذف (`detail.btn_edit_item`, `detail.btn_del_item`).
- **`_fill_items(detail)`**: يجلب عناصر الطلب عبر `detail._svc.get_order_items`، يفرّغ الجدول، يتحكم في ظهور الجدول/الحالة الفارغة/الأزرار حسب وجود عناصر، ولكل عنصر يضيف صفاً: اسم (bold، مع `user_data=item id`)، وصف، كمية (محاذاة وسط)، وحدة (muted)، سعر الوحدة، نسبة الخصم (muted)، والإجمالي المحسوب `qty * unit_price * (1 - discount/100)` بلون accent وbold. يستدعي `auto_fit_columns` في النهاية إن وُجدت عناصر.

---

## `ui/tabs/orders/order_detail/_log_section.py`

**الغرض:** يبني ويعبّئ قسم "سجل تغييرات الحالة" (قابل للطي) داخل لوحة تفاصيل الطلب.

**Imports داخلية:** `ui.widgets.panels.layout_widgets.CollapsibleCard`, `ui.widgets.tables.tables` (`make_table`, `insert_row`, `auto_fit_columns`, `make_item`, `colored_item`, `bold_item`, `muted_item`, `ROW_HEIGHT_COMPACT`), `ui.widgets.core.i18n.tr`, `ui.theme._C`, `._status_config.get_status_labels`.

**من يستدعيه:** `ui/tabs/orders/_order_detail.py` (`_build_content` يستدعي `_build_log_section`؛ `_fill_data` تستدعي `_fill_log`).

### دوال top-level:
- **`_build_log_section(detail)`**: ينشئ `CollapsibleCard` غير موسّع افتراضياً (`expanded=False`) بعنوان "سجل"، يبني جدول سجل (`detail.log_table`) بأعمدة (من، إلى، ملاحظات، وقت)، يضيفه لمحتوى الكارد.
- **`_fill_log(detail)`**: يجلب سجل الحالة عبر `detail._svc.get_status_log`، يفرّغ الجدول، ولكل سجل: يضيف الحالة القديمة (muted)، الحالة الجديدة (bold بلونها الصحيح عبر `bold_item(new_lbl, color=new_color)`)، الملاحظات، ووقت التغيير (أول 16 حرفاً فقط، muted). يستدعي `auto_fit_columns` إن وُجدت سجلات.

**ملاحظات مهمة (إصلاحات موثّقة بالتعليقات):**
- [إصلاح] الكود القديم كان يمرر نتيجة `make_item()` (كائن QTableWidgetItem) إلى `muted_item()`/`bold_item()`/`colored_item()` ظناً أنها تقبل item جاهز، بينما هذه الدوال تتوقع **نص (str)** وتُرجع item جديد. النتيجة كانت طباعة `repr` الكائن نفسه بدل النص الفعلي، والقيم المُرجَعة من `bold_item`/`colored_item` كانت تُرمى فوراً دون استخدام (فيبقى العنصر القديم plain بلا bold أو لون). تم الإصلاح بتمرير النص مباشرة وبناء item واحد صحيح فوراً.

---

## `ui/tabs/orders/order_detail/_header_fill.py`

**الغرض:** دالة واحدة تملأ هيدر لوحة تفاصيل الطلب بكل بيانات الطلب (عنوان، شارات، بطاقات، وحالة تفعيل الأزرار).

**Imports داخلية:** `ui.widgets.core.i18n.tr`, `._status_config` (`get_status_labels`, `get_priority_labels`, `get_type_labels`, `get_status_transitions`), `ui.theme._C`.

**من يستدعيه:** `ui/tabs/orders/_order_detail.py` (`_fill_data` تستدعي `_fill_header`).

### دالة top-level:
- **`_fill_header(detail)`**: يقرأ `detail._order_data`، يضبط: عنوان الهيدر (رقم الطلب)، شارة النوع، شارة الحالة (نص+3 ألوان)، شارة الأولوية، سطر بيانات العميل (اسم+كود) ومعلومات إضافية (هاتف/مدينة إن وُجدت)، بطاقات الإحصائيات الأربع (الإجمالي، المدفوع، المتبقي بلون أحمر/أخضر حسب الإيجابية، تاريخ الاستحقاق). كذلك يحسب حالة تفعيل الأزرار: `can_edit`/`can_cancel` (الحالة ليست delivered/cancelled)، `can_delete` (الحالة pending أو cancelled فقط)، `can_change` (توجد انتقالات متاحة من `STATUS_TRANSITIONS`)، ويطبقها على أزرار التعديل/الإلغاء/الحذف/تغيير الحالة/إضافة عنصر.

---

## `ui/tabs/orders/order_form/_item_row_widget.py`

**الغرض:** صف عنصر واحد قابل للتكرار داخل فورم الطلب (`_OrderForm`) — يسمح باختيار منتج من كتالوج ERP، تحديد كمية، عرض السعر/الخصم المحسوبين، وحساب الإجمالي.

**Imports داخلية:**
- `ui.widgets.panels.themed_inputs` (`ThemedLineEdit`, `ThemedComboBox`, `ThemedFrame`).
- `ui.theme._C`, `ui.widgets.core.i18n.tr`, `ui.font` (`FS_SM`, `FS_BASE`), `ui.widgets.core.widget_mixin.WidgetMixin`.
- `services.companies.company_service.CompanyService` — للحصول على اتصال erp.db النشط.
- `services.orders.catalog_service.CatalogService` — جلب المنتجات المسعّرة (caching داخلي).

**من يستدعيه:** `ui/tabs/orders/_order_form.py` (`_add_item_row`).

### Signals: `changed = pyqtSignal()`, `removed = pyqtSignal(object)`

### Class: `_ItemRowWidget(ThemedFrame, WidgetMixin)`
- **`__init__(self, conn, parent=None)`**: `conn` هو اتصال orders.db (لحفظ الطلب من الأب) لكنه غير كافٍ لـ CatalogService لأن جداول items/pricing عايشة في erp.db منفصلة؛ لذا يحصل على `erp_conn` عبر `CompanyService.get_active_erp_conn()` ويرفع `RuntimeError` إن لم توجد شركة نشطة. ينشئ `self._catalog = CatalogService(erp_conn)`.
- **`_get_products(self) -> list`**: يفوّض إلى `self._catalog.get_priced_products()` (بدل كلاس-كاش قديم على مستوى الـ class).
- **`invalidate_cache(self)`**: يستدعي `self._catalog.invalidate_products_cache()` على نسخة هذا الـ widget فقط (بدل تصفير كاش مشترك بين كل النسخ).
- **`_build(self)`**: يبني 3 صفوف: (1) بحث + combo منتج، (2) سعر/خصم/كمية/وحدة/إجمالي، (3) ملاحظات + زر حذف.
- **`_refresh_style(self, *_)`**: يطبق ستايلات مفصّلة لكل عنصر (إطار، بحث، combo، تسميات السعر/الخصم بخلفيات ملوّنة، spinbox الكمية، تسمية الإجمالي، زر الحذف).
- **`_refresh_lang(self, *_)`**: يحدّث كل النصوص المترجمة ويعيد ملء الكومبو (`_populate_combo`) بمراعاة نص البحث الحالي.
- **`_populate_combo(self, filter_text: str = "")`**: يفرّغ الكومبو، يضيف عنصر افتراضي "اختر منتج"، يمر على المنتجات (مفلترة بالاسم إن وُجد نص بحث)، يضيف فاصل غير قابل للاختيار لكل تصنيف جديد (bold، لون فاتح مميز)، ثم يضيف كل منتج بأيقونة حسب نوعه (نهائي/شبه مصنّع). يحافظ على التحديد السابق إن أمكن.
- **`_on_search(self, text: str)`**: يعيد الملء بفلتر البحث الجديد.
- **`_on_product_changed(self)`**: عند تغيير المنتج المحدد، يجلب سعره من الكاش، يحدّث تسميات السعر/الخصم، يستدعي `_recalc()`.
- **`_recalc(self)`**: يحسب `total = qty * unit_price * (1 - discount_pct/100)` ويحدّث `lbl_total`، يصدر `changed`.
- **`set_offer_discount(self, discount_pct: float)`**: يضبط نسبة الخصم يدوياً (عند استيراد عرض) ويعيد الحساب.
- **`get_product_id(self)`**: يرجع الـ ID المحدد حالياً أو `None` (يتجاهل فواصل التصنيف النصية).
- **`get_product_name(self) -> str`**: يبحث عن اسم المنتج المطابق للـ ID المحدد.
- **`get_data(self) -> dict | None`**: يرجع dict كامل ببيانات العنصر (الاسم، الكمية، الوحدة، السعر، الخصم، الملاحظات) أو `None` إن لم يُحدَّد منتج.
- **`get_total(self) -> float`**: يحسب ويرجع الإجمالي الحالي.
- **`load_from_order_item(self, item: dict)`**: يحمّل بيانات عنصر موجود مسبقاً (عند تعديل طلب) ويضبط كل الحقول المطابقة.
- **`db_item_id` (property)**: يرجع `self._db_item_id`.

**ملاحظات مهمة:** تعليقات صريحة عن [تعديل هيكلي] فصل الطبقات — الـ widget لا يفتح اتصال DB خاماً بنفسه، بل يستخدم `CompanyService` كوسيط للحصول على اتصال erp.db، و`CatalogService` (في `services/orders/`، بعد نقلها من تصادم اسم سابق مع نسخة `services/costing/`) للسحب/الكاش.

---

## `ui/tabs/orders/orders/_filter_toolbar.py`

**الغرض:** شريط أدوات فلترة وبحث لقائمة الطلبات — يحتوي زر "طلب جديد"، حقل بحث (debounced)، وكومبو حالة/أولوية مع زر إعادة تعيين.

**Imports داخلية:** `ui.widgets.panels.themed_inputs` (`ThemedLineEdit`, `ThemedComboBox`, `ThemedFrame`), `ui.theme._C`, `ui.widgets.components.button.make_btn`, `ui.widgets.core.i18n.tr`, `ui.font.FS_BASE`, `ui.widgets.core.widget_mixin.WidgetMixin`, `..order_detail._status_config` (`get_status_labels`, `get_priority_labels`).

**من يستدعيه:** `ui/tabs/orders/orders/_orders_list_panel.py` (ينشئه في `__init__` قبل `super().__init__`، ثم يستخدمه في `_build_toolbar`).

### Signal: `changed = pyqtSignal()`

### دوال module-level مساعدة (غير methods):
- **`_combo_ss() -> str`**: يرجع stylesheet للكومبو بوكس.
- **`_new_btn_ss() -> str`**: يرجع stylesheet لزر "جديد".
- **`_fixed_btn(text: str, h: int) -> QPushButton`**: ينشئ زراً بعرض محسوب ديناميكياً من عرض النص (`QFontMetrics`) بحد أدنى `FILTER_TB_NEW_BTN_MIN_W`.

### Class: `_FilterToolbar(ThemedFrame, WidgetMixin)`
- **`__init__(self, parent=None)`**: يهيئ `QTimer` singleShot للـ debounce (`FILTER_DEBOUNCE_MS`)، يربط `timeout`→`changed.emit`.
- **`_build(self)`**: صف 0: زر "طلب جديد" (`btn_new`). صف 1: حقل بحث (`inp_search`) مع debounce عبر التايمر. صف 2: كومبو الحالة (`cmb_status`)، كومبو الأولوية (`cmb_priority`، يعرض الأيقونة فقط)، زر إعادة تعيين (`btn_reset`).
- **`_refresh_style(self, *_)`**: يطبق ستايل الإطار (خلفية + حدود سفلية)، حقل البحث، وكومبوهات الحالة/الأولوية.
- **`_refresh_lang(self, *_)`**: يحدّث نصوص الزر والبحث، ويعيد بناء عناصر الكومبو مع الحفاظ على التحديد الحالي.
- **Properties:** `search_text` (نص البحث مُنظَّف ومُصغَّر)، `status_filter` (currentData لكومبو الحالة)، `priority_filter` (currentData لكومبو الأولوية).
- **`reset(self)`**: يعيد كل الفلاتر (حالة، أولوية، بحث) لوضعها الافتراضي.

---

## `ui/tabs/orders/orders/_status_delegate.py`

**الغرض:** delegate مخصص (`QStyledItemDelegate`) لرسم badge ملوّن وواضح لخلية عمود الحالة في جدول الطلبات، بدل نص عادي.

**Imports داخلية:** `ui.widgets.tables.tables.ROW_HEIGHT_LARGE`, `ui.font` (`get_font_size`, `fs`), `ui.theme._C`, `..order_detail._status_config.get_status_labels`.

**من يستدعيه:** `ui/tabs/orders/orders/_orders_list_panel.py` (`self.table.setItemDelegateForColumn(2, self._status_delegate)`).

### Class: `_StatusDelegate(QStyledItemDelegate)`
- **`paint(self, painter: QPainter, option, index)`**: يرسم خلفية العنصر القياسية أولاً، يقرأ `status_key` من `Qt.UserRole+1` والنص من `DisplayRole`، يجلب الألوان من `get_status_labels()` (أو ألوان افتراضية إن لم توجد الحالة)، يحسب مستطيل badge بحشو وحدود قصوى/دنيا، يرسمه بخلفية وحدود ملوّنة (antialiased)، ثم يكتب النص فوقه bold بلون النص المناسب.
- **`sizeHint(self, option, index) -> QSize`**: يرجع `QSize(STATUS_DELEGATE_SIZE_HINT_W, ROW_HEIGHT_LARGE)`.

---

## `ui/tabs/orders/orders/_orders_list_panel.py`

**الغرض:** لوحة قائمة الطلبات — تعرض جدول الطلبات مع فلترة وبحث، ترث من `BaseListPanel`.

**Imports داخلية:** `services.orders.order_service.OrderService`, `ui.widgets.base.list_panel.BaseListPanel`, `ui.widgets.tables.tables` (`make_item`, `muted_item`, `auto_fit_columns`), `ui.widgets.core.i18n.tr`, `ui.theme._C`, `._filter_toolbar._FilterToolbar`, `._status_delegate._StatusDelegate`, `..order_detail._status_config` (`get_status_labels`, `get_priority_labels`).

**من يستدعيه:** `ui/tabs/orders/orders_tab.py` (`_create_list`).

### Signals: `order_selected = pyqtSignal(int)`, `new_order = pyqtSignal()`

### Class: `_OrdersListPanel(BaseListPanel)`
- **Class attributes:** `COLUMNS = []` (تُبنى ديناميكياً)، `STRETCH_COL = -1`، `COL_WIDTHS = ORDERS_LIST_COL_WIDTHS`، `MIN_W`/`MAX_W`، `EMPTY_TITLE = "no_orders"`.
- **`EMPTY_ICON` (property)**: يرجع `tr("empty_icon_table")` — تعديل هيكلي من class attribute ثابتة إلى property تستدعي `tr()` في كل قراءة.
- **`__init__(self, conn, parent=None)`**: يبني `self.COLUMNS` من `tr()` قبل استدعاء `super().__init__`، ينشئ `self._filter_bar`، بعد `super().__init__` يستدعي `_insert_toolbar()`، يربط `item_selected`→`order_selected.emit`، ينشئ `_StatusDelegate` ويضبطه على العمود 2.
- **`_insert_toolbar(self)`**: يبني QWidget منفصل بلايوت، يستدعي `_build_toolbar` عليه، يدرجه في layout الأساسي عند index 1 (فوق الـ splitter مباشرة بعد الهيدر).
- **`_build_toolbar(self, lay)`**: يربط `_filter_bar.btn_new.clicked`→`new_order.emit`، `_filter_bar.changed`→`_apply_filter`، يضيف `_filter_bar` للـ layout.
- **`_load_rows(self) -> list`**: يرجع `OrderService(self.conn).list_orders()`.
- **`_match_filter(self, row, q: str) -> bool`**: يطابق الصف بفلتر الحالة/الأولوية من `_filter_bar`، وبنص البحث ضد رقم الطلب واسم العميل.
- **`_fill_row(self, table, r, row)`**: يملأ صف: رقم الطلب (bold، لون accent، `user_data=id`)، اسم العميل، الحالة (نص + `Qt.UserRole+1`=مفتاح الحالة للـ delegate)، الأولوية (أيقونة فقط، لون حسب الأولوية، bold إن high/urgent، يخزن مفتاح الأولوية وليس اللون في UserRole+1 لإعادة الحساب لاحقاً)، تاريخ الطلب (أول 10 أحرف، muted).
- **`_refresh_style(self, *_)`**: يعيد تلوين الصفوف الموجودة فعلياً في الجدول (رقم الطلب، الأولوية) بقراءة المفتاح المخزّن في `UserRole+1` وإعادة حساب اللون الصحيح من `get_priority_labels()` الحالية — بدل الاعتماد على لون الثيم القديم المحفوظ وقت التعبئة.
- **`_auto_resize(self)`**: يستدعي `auto_fit_columns` بأعمدة ثابتة من `COL_WIDTHS` وحدود دنيا/قصوى مخصصة.
- **`select_order(self, order_id: int)`**: يستدعي `self.select_item(order_id)`.

**ملاحظات مهمة:** [إصلاح] `_build_toolbar()` لم تكن تُستدعى أبداً من `BaseListPanel._build()` (نفس الباج بالضبط في `CustomersListPanel`)، فكان زر "طلب جديد" يُبنى ويُربط برمجياً لكنه غير مرئي أبداً؛ تم الحل بـ `_insert_toolbar()` اليدوية.

---

## `ui/tabs/orders/customers/customers_list_panel.py`

**الغرض:** لوحة قائمة العملاء — جدول عملاء مع فلترة بالنوع والحالة (نشط/غير نشط) وبحث، ترث من `BaseListPanel`.

**Imports داخلية:** `services.orders.customer_service.CustomerService`, `ui.widgets.base.list_panel.BaseListPanel`, `ui.widgets.core.widget_mixin.WidgetMixin`, `ui.widgets.tables.tables` (`make_item`, `muted_item`), `ui.widgets.core.i18n.tr`, `ui.widgets.panels.themed_inputs.ThemedComboBox`.

**من يستدعيه:** `ui/tabs/orders/customers_tab.py` (`_create_list`).

### Signals: `customer_selected = pyqtSignal(int)`, `new_customer = pyqtSignal()`

### Class: `CustomersListPanel(BaseListPanel, WidgetMixin)`
- **Class attributes:** `COLUMNS = []`، `STRETCH_COL = -1`، `COL_WIDTHS` (5 أعمدة: كود، اسم، هاتف، مدينة، عدد الطلبات)، `MIN_W`/`MAX_W`، `EMPTY_ICON = "👥"`، `EMPTY_TITLE = "no_customers"`.
- **`__init__(self, conn, parent=None)`**: ينشئ `CustomerService`، يهيئ فلاتر النوع/النشاط، **يملأ `self.COLUMNS` قبل `super().__init__()` بالضرورة** (لأن `_build()` تُستدعى فوراً داخل `super().__init__` وتحتاج الأعمدة جاهزة)، بعدها يفعّل WidgetMixin، يستدعي `_insert_toolbar()`، `_refresh_lang()`، `_refresh_style()`، ويربط `item_selected`→`customer_selected.emit`.
- **`_insert_toolbar(self)`**: نفس نمط `_OrdersListPanel` — يبني widget منفصل ويدرجه عند index 1.
- **`_refresh_style(self, *_)`**: يطبق ستايلات الكومبوهات والزر.
- **`_refresh_lang(self, *_)`**: يحدّث نص زر الجديد، يملأ الكومبوهات لأول مرة فقط (`count() == 0`)، يعيد بناء `self.COLUMNS`.
- **`_build_toolbar(self, lay)`**: يبني صف فلاتر (كومبو نوع، كومبو نشاط) + زر "عميل جديد"، يربط `currentIndexChanged`→`_on_combo_changed` للكومبوهات، الزر→`new_customer.emit`.
- **`_on_combo_changed(self)`**: يحدّث `_type_filter`/`_active_filter` من الكومبوهات، يستدعي `_apply_filter()`.
- **`_load_rows(self) -> list`**: يرجع `self._svc.list_customers()`.
- **`_match_filter(self, row, q: str) -> bool`**: يطابق بنوع العميل، حالة النشاط، ونص البحث (اسم/هاتف/كود).
- **`_fill_row(self, table, r, row)`**: يملأ: كود (muted، `Qt.UserRole`=id)، اسم (يخزن `is_active` في `UserRole+1`، رمادي إن غير نشط وbold إن نشط)، هاتف، مدينة، عدد الطلبات (لون accent).
- **`_refresh_style(self, *_)`** (تعريف مكرر لاحقاً في نفس الكلاس — الفعلي المستخدم): يعيد تلوين الصفوف الموجودة (اسم العميل حسب `is_active` المخزّن، عدد الطلبات بلون accent) دون إعادة استعلام DB.

**ملاحظات مهمة:** [إصلاح] نفس مشكلة toolbar غير المستدعاة الموجودة في `_OrdersListPanel`. أيضاً حُذف صف بحث مكرر كان موجوداً سابقاً (غير مربوط فعلياً بمنطق الفلترة) لصالح البحث المدمج في `ListHeader` المبني داخل `BaseListPanel._build_header`.

---

## `ui/tabs/orders/customers/customer_detail_panel.py`

**الغرض:** لوحة تفاصيل العميل — تعرض بيانات العميل، جهات الاتصال، وآخر طلباته، مع أزرار تعديل/تبديل نشاط/حذف. ترث من `BaseDetailPanel`.

**Imports داخلية:** `services.orders.customer_service.CustomerService`, `ui.tabs.orders._customer_form._CustomerForm`, `ui.widgets.base.detail_panel.BaseDetailPanel`, `ui.widgets.tables.tables` (`make_table`, `make_compact_table`, `insert_row`, `auto_fit_columns`, `make_item`, `bold_item`, `colored_item`, `muted_item`, `ROW_HEIGHT_COMPACT`), `ui.widgets.components.headers_page.SectionHeader`, `ui.widgets.components.button.make_btn`, `ui.widgets.core.i18n.tr`, `ui.theme._C`, `..order_detail._status_config` (`get_status_labels`, `get_priority_labels`).

**من يستدعيه:** `ui/tabs/orders/customers_tab.py` (`_create_detail`).

### Signals: `edited = pyqtSignal(int)`, `deleted = pyqtSignal()`

### Class: `CustomerDetailPanel(BaseDetailPanel)`
- **Class attributes:** `EMPTY_ICON = "👤"`, `EMPTY_TITLE = "customer_select_first"`, `EMPTY_SUBTITLE = "customer_select_subtitle"`.
- **`__init__(self, conn, parent=None)`**: ينشئ `CustomerService`.
- **`_build_header_cards(self)`**: 4 بطاقات إحصائية (إجمالي الطلبات، الطلبات النشطة، القيمة الإجمالية، الرصيد).
- **`_build_header_buttons(self)`**: أزرار تعديل، تبديل نشاط، حذف؛ يربط كل زر بمعالجه.
- **`_build_content(self, lay)`**: يبني جدول جهات اتصال (compact) وجدول آخر الطلبات.
- **`_load_data(self, item_id: int)`**: يرجع `self._svc.get_customer(item_id)`.
- **`_fill_data(self, data: dict)`**: يملأ عنوان، شارة نوع، شارة كود، معلومات (هاتف/مدينة/إيميل)، إحصائيات (طلبات/نشط/قيمة/رصيد بلون أحمر/أخضر حسب الرصيد)، نص زر التبديل، جدول جهات الاتصال، وجدول آخر 20 طلب (رقم بلون accent، حالة، أولوية، قيمة صافية بلون accent، تاريخ).
- **`_refresh_style(self, *_)`**: يستدعي `super()._refresh_style`، ثم يعيد تلوين خلايا رقم الطلب وقيمته في `orders_table` بلون accent الحالي (لأنها لم تكن جزءاً من stylesheet عام، بل `setForeground` وقت التعبئة فقط).
- **`load_customer(self, cid: int)`**: يستدعي `self.load_item(cid)`.
- **`_edit(self)`**: يفتح `_CustomerForm` لتعديل العميل الحالي، يربط `saved` لإعادة التحميل وإصدار `edited`.
- **`_delete(self)`**: يؤكد الحذف عبر `QMessageBox`، يستدعي `self._svc.delete`، يصدر `deleted` أو يعرض تحذير فشل.
- **`_toggle_active(self)`**: يستدعي `self._svc.toggle_active`، يعيد التحميل، يصدر `edited`.

---

## `ui/tabs/orders/customers_tab.py`

**الغرض:** تبويب "العملاء" — يجمع قائمة العملاء ولوحة تفاصيل العميل في splitter عبر `BaseSection`.

**Imports داخلية:** `ui.tabs.orders._customer_form._CustomerForm`, `ui.tabs.orders.customers.customers_list_panel.CustomersListPanel`, `ui.tabs.orders.customers.customer_detail_panel.CustomerDetailPanel`, `ui.widgets.base.section.BaseSection`, `ui.constants` (`CUSTOMERS_LIST_MIN_W`, `ORDERS_SPLITTER_FIT_DELAY_MS`).

**من يستدعيه:** `ui/tabs/orders_section.py`.

### Class: `CustomersTab(BaseSection)`
- **Class attribute:** `LIST_MIN_W = CUSTOMERS_LIST_MIN_W`.
- **`__init__(self, conn, parent=None)`**: يستدعي `super().__init__`، ثم `self._list.refresh()` فوراً — [إصلاح] القائمة كانت فاضية عند فتح التاب لأول مرة.
- **`_fit_splitter_delayed(self, delay_ms: int)`**: [إصلاح] `BaseSection` لا توفر هذه الدالة رغم استدعائها في `_on_edited`/`_on_saved`، ما كان يسبب `AttributeError`؛ الحل يستدعي `QTimer.singleShot(delay_ms, self._apply_sizes)` (يأخذ `delay_ms` كمعامل، بخلاف `orders_tab.py` حيث الدالة بلا معامل).
- **`_create_list(self)`**: يرجع `CustomersListPanel(self._conn)`.
- **`_create_detail(self)`**: يرجع `CustomerDetailPanel(self._conn)`.
- **`_connect_signals(self)`**: يربط `customer_selected`→`_detail.load_customer`، `new_customer`→`_new_customer`، `detail.edited`→`_on_edited`، `detail.deleted`→`_list.refresh`.
- **`_on_edited(self, cid: int)`**: يعيد تحميل القائمة، يضبط الـ splitter بتأخير.
- **`_new_customer(self)`**: يفتح `_CustomerForm` جديد، يربط `saved`→`_on_saved`.
- **`_on_saved(self, cid: int)`**: يعيد تحميل القائمة، يحدد العميل، يحمّل تفاصيله، يضبط الـ splitter بتأخير.

---

## `ui/tabs/orders/_customer_form.py`

**الغرض:** دايلوج إنشاء/تعديل عميل كامل، متضمناً بيانات أساسية (اسم، نوع، هواتف، إيميل، عنوان، ملاحظات) وجدول جهات اتصال قابل للإضافة/الحذف.

**Imports داخلية:** `services.orders.customer_service.CustomerService`, `ui.widgets.tables.tables` (`make_compact_table`, `make_item`, `insert_row`, `ROW_HEIGHT_COMPACT`), `ui.widgets.components.button.make_btn`, `ui.widgets.theme.input_styles.input_style`, `ui.widgets.core.widget_mixin.WidgetMixin`, `ui.widgets.core.i18n.tr`, `ui.theme._C`, `ui.font` (`FS_BASE`, `FS_SM`, `fs`).

**من يستدعيه:** `ui/tabs/orders/customers_tab.py` (`_new_customer`)، `ui/tabs/orders/customers/customer_detail_panel.py` (`_edit`)، `ui/tabs/orders/_order_form.py` (`_new_customer`).

### دالة module-level: `_group_ss() -> str` — stylesheet ثابت لـ `QGroupBox` (غير مستخدم فعلياً داخل الكلاس؛ الكلاس يبني نسخة مكافئة ديناميكياً في `_refresh_style`).

### ثابت module-level: `CUSTOMER_FORM_LBL_W = 110` — عرض ثابت (px) لتسميات صفوف البيانات الأساسية، لحل مشكلة تراكب `QFormLayout` مع RTL.

### Signal: `saved = pyqtSignal(int)`

### Class: `_CustomerForm(QDialog, WidgetMixin)`
- **`__init__(self, conn, customer_id: int = None, parent=None)`**: يحسب حجم النافذة نسبةً لحجم الشاشة المتاحة (92%/90%) مع حد أقصى، modal، يبني ويطبّق الستايل، يحمّل بيانات العميل إن `customer_id` موجود.
- **`_refresh_style(self, *_)`**: يبني cache لستايل `QGroupBox` ويطبقه على المجموعتين (بيانات أساسية، جهات اتصال)، يلوّن هيدر العنوان، يطبق `input_style()` على النافذة كلها.
- **`_build(self)`**: `QScrollArea` غير resizable (عرض ثابت `CUSTOMER_FORM_MIN_W - 40`) يحتوي: هيدر، مجموعة البيانات الأساسية (صفوف يدوية `QHBoxLayout` بدل `QFormLayout` — تعليق: [إصلاح] نفس مشكلة `_order_form.py` مع RTL)، مجموعة جهات الاتصال (جدول + أزرار إضافة/حذف)، أزرار حفظ/إلغاء.
- **دالة محلية `_row(label_text, field_widget)` داخل `_build`**: تبني صفاً يدوياً بعرض تسمية ثابت (`CUSTOMER_FORM_LBL_W`) لتفادي مشكلة QFormLayout+RTL.
- **`_load(self)`**: يجلب بيانات العميل، يملأ كل الحقول، يحمّل جهات الاتصال عبر `self._svc.list_contacts`، يستدعي `_refresh_contacts_table`.
- **`_refresh_contacts_table(self)`**: يعيد بناء جدول جهات الاتصال بالكامل من `self._contacts`.
- **`_add_contact_dialog(self)`**: يفتح `_ContactDialog`، عند القبول يضيف بيانات جهة الاتصال الجديدة (بدون `id`) للقائمة المحلية ويعيد رسم الجدول.
- **`_del_contact(self)`**: يحذف جهة الاتصال المحددة من القائمة المحلية؛ إن كان لها `id` فعلي يضيفه لـ `_deleted_contact_ids` (للحذف الفعلي عند الحفظ).
- **`_save(self)`**: يتحقق من الاسم، يجمع كل الحقول، يستدعي `update` أو `add` في `CustomerService` حسب وجود `customer_id`، ثم يمرّ على `_deleted_contact_ids` لحذف جهات الاتصال المحذوفة فعلياً، ويحفظ/يحدّث كل جهة اتصال حالية (بحسب وجود `id`)، يصدر `saved` ويقبل الدايلوج.

**ملاحظة كود:** [مفعّل] `CustomerService` أصبح يوفر `add_contact`/`update_contact`/`delete_contact` مباشرة، فلم تعد الواجهة تحتاج استدعاء `db.orders.customers_repo` مباشرة (التزام بمبدأ الطبقات).

### Class: `_ContactDialog(QDialog, WidgetMixin)`
- **`__init__(self, data: dict = None, parent=None)`**: modal، يبني الفورم، يحمّل بيانات جهة اتصال موجودة إن أُرسلت.
- **`_refresh_style(self, *_)`**: يطبق `input_style()`.
- **`_build(self)`**: `QFormLayout` بحقول (اسم، دور، هاتف، إيميل، ملاحظات) + أزرار إلغاء/موافق.
- **`_load(self, data: dict)`**: يملأ الحقول من dict.
- **`_ok(self)`**: يتحقق من الاسم قبل `accept()`.
- **`get_data(self) -> dict`**: يرجع dict ببيانات جهة الاتصال (بـ `id: None` دائماً لأنها إما جديدة أو تُدار عبر القائمة الأب).

---

## `ui/tabs/orders/_order_form.py`

**الغرض:** دايلوج إنشاء/تعديل طلب كامل — يشمل اختيار/إنشاء عميل، تفاصيل الطلب (نوع، حالة، أولوية، تاريخ استحقاق، خصم، مدفوع)، صفوف عناصر ديناميكية، استيراد من عرض جاهز، ملاحظات، وحفظ.

**Imports داخلية:**
- `services.orders.customer_service.CustomerService`, `services.orders.order_service.OrderService`.
- `.order_form._item_row_widget._ItemRowWidget`.
- `services.orders.catalog_service.CatalogService`.
- `ui.widgets.components.button.make_btn`, `ui.widgets.theme.input_styles.input_style`, `ui.widgets.core.i18n.tr`, `ui.font` (`FS_BASE`, `FS_SM`).

**من يستدعيه:** `ui/tabs/orders/_order_detail.py` (`new_order`, `_edit_order`).

### ثابت module-level: `ORDER_FORM_DETAILS_LBL_W = 110` — عرض ثابت لتسمية صف "تفاصيل الطلب"، يحل مشكلة QFormLayout+RTL.

### دوال module-level:
- **`_group_ss(accent=None) -> str`**: stylesheet لـ `QGroupBox` بلون تمييز اختياري.
- **`_get_status_options() -> list`**: يرجع 4 حالات فقط قابلة للاختيار من الفورم مباشرة (pending, confirmed, in_progress, ready) — الحالات النهائية (delivered/cancelled/on_hold) تُدار عبر دايلوج تغيير الحالة المنفصل.
- **`_get_priority_options() -> list`**: كل الأولويات من `get_priority_labels()`.
- **`_get_type_options() -> list`**: كل الأنواع من `get_type_labels()`.

### Signal: `saved = pyqtSignal(int)`

### Class: `_OrderForm(QDialog)`
- **`__init__(self, conn, order_id: int = None, parent=None, erp_conn=None)`**: يحسب حجم النافذة نسبة للشاشة (92%/90%)، ينشئ `CatalogService` إن وُجد `erp_conn`، `OrderService`، `CustomerService`، modal، يبني الواجهة، يحمّل بيانات الطلب إن `order_id` موجود.
- **`_build(self)`**: `QScrollArea` غير resizable (عرض ثابت)، هيدر، ثم يستدعي بالترتيب: `_build_customer_section`, `_build_order_details`, `_build_items_section`, `_build_notes_section`, `_build_save_buttons`, ويضيف صف عنصر افتراضي واحد (`_add_item_row`).
- **`_build_customer_section(self, root)`**: بحث عملاء (نتائج بعد حرفين)، زر عميل جديد، كومبو اختيار عميل، تسمية معلومات العميل (تظهر عند التحديد).
- **`_build_order_details(self, root)`**: صفوف يدوية (نفس نمط `_row` في `_customer_form.py`) لـ: نوع الطلب، حالة (مخفية عند الإنشاء الجديد)، أولوية (افتراضي index=1)، تاريخ استحقاق (افتراضي +`ORDER_FORM_DUE_DATE_DEFAULT` يوم)، خصم إجمالي، مبلغ مدفوع.
- **`_build_items_section(self, root)`**: شريط أدوات (زر إضافة عنصر، كومبو عروض جاهزة + زر استيراد)، حاوية صفوف ديناميكية (`_rows_layout`)، شريط إجمالي (عدد العناصر الصحيحة، الإجمالي الفرعي).
- **`_build_notes_section(self, root)`**: حقلا ملاحظات (للعميل وداخلية).
- **`_build_save_buttons(self, root)`**: أزرار إلغاء/حفظ.
- **`_add_item_row(self, prefill: dict = None) -> _ItemRowWidget`**: ينشئ صفاً جديداً، يربط `changed`→`_update_totals`، `removed`→`_remove_item_row`، يضيفه للقائمة والـ layout، يحمّل بيانات مسبقة إن وُجدت.
- **`_remove_item_row(self, row_widget)`**: يزيل الصف من القائمة والـ layout، `deleteLater()`، يعيد حساب الإجماليات.
- **`_update_totals(self)`**: يحسب مجموع كل الصفوف الصحيحة (لها منتج محدد) ويحدّث تسميات العدد والإجمالي الفرعي.
- **`_load_offers_combo(self)`**: يملأ كومبو العروض من `self._catalog.get_offers()` إن وُجد catalog.
- **`_import_offer(self)`**: عند اختيار عرض، يحذف الصفوف الفارغة الحالية، يضيف صفاً لكل سطر في العرض (يحدد المنتج ويعيد ضبط سعره من الكاش الداخلي للصف)، يضبط الكمية ونسبة خصم العرض لكل صف.
- **`_search_customers(self, text: str)`**: بحث ديناميكي (بعد حرفين)، يعيد ملء كومبو العملاء بالنتائج ويحدد أول نتيجة تلقائياً.
- **`_on_customer_changed(self, idx: int)`**: يحدّث `self._customer_id` وتسمية معلومات العميل (هاتف/مدينة/إيميل).
- **`_new_customer(self)`**: يفتح `_CustomerForm`، يربط `saved`→`_on_customer_created`.
- **`_on_customer_created(self, customer_id: int)`**: يضيف العميل الجديد في أول الكومبو ويحدده.
- **`_load(self)`**: يحمّل بيانات طلب موجود بالكامل (عميل، نوع، أولوية، حالة، تاريخ استحقاق، خصم، مدفوع، ملاحظات) وعناصره كصفوف.
- **`_save(self)`**: يتحقق من وجود عميل وعنصر واحد صحيح على الأقل، يجمع كل الحقول، ثم إما يحدّث طلباً موجوداً (`update_order_header` + `replace_order_items`) أو ينشئ طلباً جديداً (`create_order_header` + `replace_order_items`)، يصدر `saved`، يقبل الدايلوج.

---

## `ui/tabs/orders/_item_form.py`

**الغرض:** دايلوج إضافة/تعديل عنصر واحد داخل طلب (بشكل مستقل عن فورم الطلب الكامل — يُستخدم من لوحة التفاصيل مباشرة).

**Imports داخلية:** `services.orders.order_service.OrderService`, `ui.widgets.components.button.make_btn`, `ui.widgets.theme.input_styles.input_style`, `ui.widgets.core.widget_mixin.WidgetMixin`, `ui.widgets.core.i18n.tr`, `ui.theme._C`, `ui.font` (`FS_BASE`, `fs`).

**من يستدعيه:** `ui/tabs/orders/_order_detail.py` (`_add_item`, `_edit_item`).

### دالة module-level: `_spin(min_=0, max_=ITEM_FORM_SPIN_MAX, dec=2, suffix="") -> QDoubleSpinBox` — تنشئ QDoubleSpinBox موحّد الإعدادات.

### Class: `_ItemForm(QDialog, WidgetMixin)`
- **`__init__(self, conn, order_id: int, item_id: int = None, parent=None)`**: modal، يربط تغييرات الكمية/السعر/الخصم بـ `_update_total` بعد بناء الواجهة، يحمّل بيانات العنصر إن `item_id` موجود.
- **`_refresh_style(self, *_)`**: يطبق `input_style()`، ستايل هيدر العنوان، وستايل تسمية الإجمالي.
- **`_build(self)`**: `QFormLayout` بحقول: اسم العنصر، الوصف، الكمية، الوحدة (افتراضي "قطعة")، سعر الوحدة، نسبة الخصم، تسمية الإجمالي (محسوبة تلقائياً)، مرجع تصميم، ملاحظات؛ أزرار إلغاء/حفظ.
- **`_update_total(self)`**: يحسب `total = qty * price * (1 - discount/100)` ويحدّث `lbl_total`.
- **`_load(self)`**: يجلب عناصر الطلب، يجد العنصر المطابق لـ `item_id`، يملأ كل الحقول.
- **`_save(self)`**: يتحقق من وجود اسم، يجمع الحقول، يستدعي `update_item` أو `add_item` في `OrderService` حسب وجود `item_id`، يقبل الدايلوج.

---

## `ui/tabs/orders/_order_detail.py`

**الغرض:** لوحة تفاصيل الطلب الرئيسية — تجمع الهيدر (بطاقات + أزرار)، قسم العناصر، وقسم السجل، وتدير كل عمليات CRUD وتغيير الحالة على مستوى الطلب. ترث من `BaseDetailPanel`.

**Imports داخلية:**
- `services.orders.order_service.OrderService`.
- `ui.tabs.orders._order_form._OrderForm`, `ui.tabs.orders._item_form._ItemForm`.
- `ui.widgets.base.detail_panel.BaseDetailPanel`, `ui.widgets.core.widget_mixin.WidgetMixin`.
- `.order_detail._items_section` (`_build_items_section`, `_fill_items`), `.order_detail._log_section` (`_build_log_section`, `_fill_log`), `.order_detail._header_fill._fill_header`, `.order_detail._status_config.STATUS_TRANSITIONS`, `.order_detail._status_dialog._StatusDialog`.

**من يستدعيه:** `ui/tabs/orders/orders_tab.py` (`_create_detail`).

### Signals: `saved = pyqtSignal(int)`, `deleted = pyqtSignal()`, `status_changed = pyqtSignal(int)`

### Class: `_OrderDetail(BaseDetailPanel, WidgetMixin)`
- **Class attributes:** `EMPTY_TITLE = "order_select_first"`, `EMPTY_SUBTITLE = "order_select_subtitle"`.
- **`EMPTY_ICON` (property)**: يرجع `tr("empty_icon_table")`.
- **`__init__(self, conn, parent=None)`**: يهيئ `_order_id`, `_order_data`, `OrderService`، بعد `super().__init__` يفعّل WidgetMixin بـ `font=False, lang=False, data=False` ويستدعي `_refresh_style()`.
- **`_refresh_style(self, *_)`**: إن وُجدت بيانات طلب محمّلة، يعيد حساب لون بطاقة الرصيد المتبقي (أحمر/أخضر) حسب `net_amount - paid_amount`.
- **`_build_header_cards(self)`**: 4 بطاقات (إجمالي، مدفوع، رصيد بلون danger، تاريخ استحقاق بلون warning).
- **`_build_header_buttons(self)`**: أزرار تعديل، تغيير حالة، إعادة طلب، إلغاء (danger)، حذف (danger)؛ يربط كل زر بمعالجه.
- **`_build_content(self, lay)`**: يستدعي `_build_items_section(self)` و`_build_log_section(self)` (الدوال الخارجية من الملفات الفرعية، تُمرَّر `self` كـ `detail`).
- **`_load_data(self, item_id: int)`**: يرجع `self._svc.get_order(item_id)`.
- **`_fill_data(self, data: dict)`**: يضبط `_order_id`/`_order_data`، يستدعي `_fill_header(self)`, `_fill_items(self)`, `_fill_log(self)`.
- **`load_order(self, order_id: int)`**: يستدعي `self.load_item(order_id)`.
- **`clear(self)`**: يصفّر `_order_id`/`_order_data`/`_item_id`/`_item_data` ويستدعي `_show_empty()`.
- **`new_order(self)`**: يفتح `_OrderForm` جديد، يربط `saved`→`_on_form_saved`.
- **`_edit_order(self)`**: يفتح `_OrderForm` بوضع تعديل لهذا الطلب.
- **`_on_form_saved(self, order_id: int)`**: يعيد تحميل الطلب، يصدر `saved`.
- **`_change_status_dialog(self)`**: يجلب الانتقالات الممكنة من `STATUS_TRANSITIONS`، إن وُجدت يفتح `_StatusDialog`، عند القبول يستدعي `self._svc.change_status` ويصدر `status_changed`.
- **`_cancel_order(self)`**: يمنع الإلغاء إن كانت الحالة delivered/cancelled، يطلب سبب الإلغاء عبر `QInputDialog` (دالة مساعدة `_get_text_input`)، عند التأكيد يستدعي `self._svc.cancel` ويصدر `status_changed`.
- **`_delete_order(self)`**: يؤكد الحذف، يستدعي `self._svc.delete`، يصدر `deleted` أو يعرض تحذير فشل.
- **`_do_reorder(self)`**: يؤكد إعادة الطلب، يستدعي `self._svc.do_reorder`، إن نجح يحمّل الطلب الجديد ويصدر `saved`.
- **`_add_item(self)`**: يمنع الإضافة إن كانت الحالة delivered/cancelled، يفتح `_ItemForm`، عند القبول يعيد ملء العناصر ومبالغ الهيدر.
- **`_edit_item(self)`**: يجلب `item_id` من الصف المحدد في `items_table` (عبر `Qt.UserRole`)، يفتح `_ItemForm` بوضع تعديل، عند القبول يحدّث العرض.
- **`_del_item(self)`**: يؤكد الحذف، يستدعي `self._svc.remove_item`، يحدّث العرض.
- **`_fill_header_amounts(self)`**: يعيد جلب الطلب من DB، يحدّث بطاقات الإجمالي/المدفوع/الرصيد (مع اللون المناسب) دون إعادة تحميل الصفحة كاملة.

### دالة module-level خارج الكلاس: `_get_text_input(parent, title, prompt)` — wrapper حول `QInputDialog.getText`.

---

## قسم علاقات الملفات

- **`orders_section.py`** هو نقطة الدخول: يستورد ويجمع `orders_tab.py`, `customers_tab.py`, `dashboard_tab.py` كتابات فرعية داخل `QTabWidget` واحد، ويفتح اتصال DB مشترك (`conn`) يُمرَّر للثلاثة.
- **`orders_tab.py`** و **`customers_tab.py`** يتبعان نفس النمط: يرثان `BaseSection` (من `ui.widgets.base.section`، خارج هذا المسار)، وكل منهما يبني list+detail عبر `_create_list`/`_create_detail`، ويربط الإشارات في `_connect_signals`. كلاهما يعاني/عالج نفس الباج (غياب `_fit_splitter_delayed` في `BaseSection`).
- **`_status_config.py`** هو المصدر المركزي الوحيد لكل تسميات/ألوان/انتقالات الحالات، وتعتمد عليه مباشرة: `_status_dialog.py`, `_log_section.py`, `_header_fill.py`, `_order_detail.py` (`STATUS_TRANSITIONS`), `_order_form.py`, `customer_detail_panel.py`, `_filter_toolbar.py`, `_orders_list_panel.py`, `_status_delegate.py`.
- **`_orders_list_panel.py`** يجمع `_filter_toolbar.py` (شريط الفلترة) و`_status_delegate.py` (رسم badge الحالة) معاً كمكوّنات فرعية.
- **`_order_detail.py`** يجمع `_items_section.py`, `_log_section.py`, `_header_fill.py`, `_status_dialog.py` كدوال/كلاسات بناء وتعبئة منفصلة تُستدعى عليه كـ `detail`.
- **`_order_form.py`** يستخدم `order_form/_item_row_widget.py` (`_ItemRowWidget`) كصف متكرر، ويستخدم `_customer_form.py` (`_CustomerForm`) لإنشاء عميل جديد أثناء تعبئة الطلب.
- **`_item_row_widget.py`** يعتمد على `services.orders.catalog_service.CatalogService` (خارج هذا المسار) وليس على أي ملف داخل `ui/tabs/orders/` مباشرة لجلب المنتجات.
- **`customers_list_panel.py`** و **`_orders_list_panel.py`** يشتركان في نفس نمط الإصلاح (toolbar غير مُستدعاة من `BaseListPanel._build()`، حُلَّت بـ `_insert_toolbar()` يدوية) رغم أنهما ملفان مختلفان بدون استيراد مباشر بينهما.
- **نمط عام مشترك في كل الملفات:** الاعتماد الكامل على `WidgetMixin` (من `ui.widgets.core.widget_mixin`، خارج هذا المسار) لإدارة `_refresh_style`/`_refresh_lang`/`_refresh_data` تلقائياً عبر bus مركزي، بدل استدعاءات يدوية متفرقة.
- **تبعيات خارج هذا المسار (بلا تفصيل محتواها هنا):** `ui.widgets.base.section.BaseSection`, `ui.widgets.base.list_panel.BaseListPanel`, `ui.widgets.base.detail_panel.BaseDetailPanel`, `ui.widgets.tables.tables`, `ui.widgets.panels.themed_inputs`, `ui.widgets.components.*`, `ui.theme._C`, `ui.font`, `ui.constants`, `ui.widgets.core.i18n.tr`, `services.orders.*`, `services.companies.company_service.CompanyService`.

---

## بانتظار ملفات ناقصة

| اسم الملف | المسار الكامل | الحالة |
|---|---|---|
| (لا يوجد) | — | كل الملفات الموجودة في `system_arch.txt` تحت `ui/tabs/orders/` و`ui/tabs/orders_section.py` مرفقة محتواها بالكامل في هذه الدفعة. |
