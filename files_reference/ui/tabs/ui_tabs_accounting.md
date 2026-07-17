# ui/tabs/accounting — ملف مرجعي

يغطي هذا الملف كل الملفات الموجودة مباشرة تحت `ui/tabs/accounting/` بالإضافة إلى الـ subfolders الظاهرة تحته في `system_arch.txt`:
`financial/`, `investors/`, `journal/` (وتفرعاته `account_picker/`, `form/`, `group_combo/`, `lines/`), `ledger/`, `tree/`.

**استثناء مقصود بطلب صريح من المستخدم:** يضم هذا المرجع أيضاً ملف `ui/tabs/accounting_section.py` رغم أن مساره الفعلي في `system_arch.txt` هو مباشرة تحت `ui/tabs/` (شقيق لمجلد `accounting/` وليس داخله) — لأنه نقطة الدخول الرئيسية التي تجمع كل تبويبات هذا القسم. أُدرِج كقسم "0" منفصل قبل الجذر لتوضيح أنه خارج حدود `ui/tabs/accounting/` جغرافياً.

---

## 0. `ui/tabs/accounting_section.py` *(خارج مسار `ui/tabs/accounting/` — مُضاف بطلب صريح)*

**الغرض:** `AccountingTab` — النافذة/الويدجت الرئيسي لقسم المحاسبة بالكامل؛ يبني هيدر القسم، يتحقق من جاهزية الشركة النشطة واتصالاتها (accounting + ERP)، ثم يبني `QTabWidget` رئيسي يجمع كل التبويبات الفرعية الخمسة (الحسابات، اليومية، الأستاذ، القوائم المالية، المستثمرين). يدعم تعدد الشركات بالكامل (إعادة بناء عند تبديل الشركة).

**Imports مهمة:**
- `ui.widgets.theme.layout_styles.tab_style` — ستايل التبويبات (غير مستخدم مباشرة بعد التحويل لـ `ThemedTabWidget`، لكنه لا يزال مستورداً).
- `ui.theme._C`, `ui.widgets.core.i18n.tr`, `ui.font` (`FS_BASE`, `FS_MD`), `ui.constants` (`ACCOUNTING_TAB_MSG_PAD`, `ACCOUNTING_TAB_ERR_RADIUS`, `ACCOUNTING_TAB_ERR_MARGIN`, `SECTION_HEADER_HEIGHT`, `SECTION_HEADER_BORDER_W`, `SECTION_HEADER_PAD_RIGHT`).
- `ui.widgets.core.widget_mixin.WidgetMixin` — تسجيل تلقائي على تغييرات الثيم/الخط/اللغة.
- `.accounting.journal_tab.JournalTab`, `.accounting.ledger_tab.LedgerTab`, `.accounting.investors_tab.InvestorsTab`.
- `.accounting.accounting_tabs_builder` (`build_accounts_tabs`, `build_financial_tab`, `ThemedTabWidget`).
- `services.companies.company_service.CompanyService` (يُستورد داخل `_build()` مباشرة) — للتحقق من جاهزية الشركة وجلب اتصالي accounting/ERP النشطين.

**من يستدعي هذا الملف:** غير محدد من المرفقات الحالية (هو غالباً يُستورد من نافذة رئيسية أعلى مثل `ui/main_window.py`، لكن لا يوجد ملف مرفق في هذه الدفعة يستورده صراحة).

**Class: `AccountingTab(QWidget, WidgetMixin)`**
- `__init__(self, parent=None)`: يهيئ `_main_tabs`/`_header` إلى `None`، يبني الواجهة، ويهيئ `WidgetMixin` (theme+font+lang، بدون data).
- `_cleanup_layout(self)`: يفرّغ الـ layout الحالي للويدجت بالكامل (يخفي ويحذف كل عنصر فيه) استعداداً لإعادة البناء الكامل، عبر إسناد الـ layout القديم لويدجت وهمي (`dummy`) ثم حذفه.
- `_build(self)`:
  1. ينظف الـ layout القديم (`_cleanup_layout`) ويصفّر `_main_tabs`.
  2. يبني هيدر القسم (`QLabel` بأيقونة + اسم "المحاسبة") ويضيفه أولاً — **قبل** أي `return` مبكر، لضمان ظهوره في كل الحالات (لا شركة / خطأ اتصال / نجاح).
  3. يتحقق عبر `CompanyService.is_company_ready()`: إذا لا توجد شركة جاهزة، يعرض رسالة "اختر شركة" (`accounting_no_company_msg`) ويتوقف.
  4. يحاول جلب `CompanyService.get_active_accounting_conn()` و`get_active_erp_conn()`؛ عند فشل أو `None` يعرض رسالة خطأ اتصال منسّقة (خلفية حمراء) ويتوقف.
  5. عند النجاح: يبني `ThemedTabWidget(size="normal")` ويضيف خمسة تبويبات بالترتيب: `build_accounts_tabs(acc)` ("الحسابات")، `JournalTab(acc, erp)` ("اليومية")، `LedgerTab(acc)` ("الأستاذ")، `build_financial_tab(acc)` ("القوائم المالية")، `InvestorsTab(erp, acc)` ("المستثمرين").
- `_refresh_header_style(self, *_)`: يعيد تلوين/تنسيق هيدر القسم (خلفية، حد سفلي، حجم خط، لون accent) من `_C`/`FS_MD`/ثوابت الهيدر.
- `_refresh_style(self, *_)`: يستدعي `_refresh_header_style()`، ثم يستدعي `_main_tabs._refresh_style()` كطبقة أمان إضافية (رغم أن `ThemedTabWidget` مسجل بالفعل على `bus.theme_changed` بمفرده).
- `_refresh_lang(self, *_)`: يحدّث نص هيدر القسم، وإذا كان `_main_tabs` يحتوي بالضبط 5 تبويبات يحدّث نصوصها الخمسة (`setTabText`) ثم يعيد حساب عرضها (`apply_tab_widths`).
- `refresh_for_company(self)`: يستدعي `_build()` لإعادة بناء التبويب بالكامل (يُستخدم عند تبديل الشركة من الخارج).
- `closeEvent(self, event)`: يستدعي `super().closeEvent(event)` فقط — لا منطق تنظيف إضافي حالياً.

**ملاحظات من التعليقات:**
- [تحديث v13]: حُذف ملف `_conn_guard.py` بالكامل لأنه كان يكرر منطقاً موجوداً فعلاً وموثوقاً في `db.companies.company_state` (`path_matches`/`_get_conn`) وفي `companies_repo._init_company_databases()`؛ الاتصالات تُجلب الآن مباشرة عبر `CompanyService.get_active_accounting_conn()`/`get_active_erp_conn()` بدل طبقة وسيطة `db.shared.connection`.
- لا حاجة لـ `verify_conn_belongs_to_company`: `company_state` يغلق ويعيد فتح أي اتصال لا يطابق مسار الشركة النشطة تلقائياً.
- لا حاجة لتهيئة schemas هنا؛ تتم مرة واحدة عند إنشاء الشركة في `companies_repo`.
- لا حاجة لحلقة إعادة محاولة (retry) عبر `QTimer`: `MainWindow._on_company_changed()` يستدعي إعادة بناء كامل للتبويبات عند كل تغيير شركة، فهذا التبويب يُعاد بناؤه تلقائياً من الخارج.
- [v12 محفوظ]: توحيد كامل عبر `tab_style()`, `tr()` لكل النصوص, `_C` لكل الألوان, `font.py` لكل أحجام الخط, وتحديث الثيم الديناميكي عبر `bus.theme_changed`.

---

## 1. الجذر: `ui/tabs/accounting/`

### 1.1 `ui/tabs/accounting/helpers.py`

**الغرض:** أدوات مساعدة صغيرة مشتركة بين تبويبات الحسابات: ألوان أنواع الحسابات، بناء spinbox موحد، تنسيق مبالغ مالية، وبطاقات إحصائية.

**Imports مهمة:**
- `ui.widgets.components.stat_card.stat_card_pair` — لبناء بطاقة إحصائية موحدة.
- `ui.widgets.panels.form_fields.spin_field` — لبناء QDoubleSpinBox موحد.
- `ui.theme._C` — قاموس ألوان الثيم الحالي.
- `ui.widgets.core.i18n.tr` — الترجمة.

**من يستدعي هذا الملف:** `account_combo.py`, `accounts_tree.py` (عبر `.helpers`), `tree/_tree_nodes.py`, `tree/_tree_headers.py`, `journal/lines/_smart_line.py` (عبر `TYPE_COLORS`), `journal/journal_tree_table.py`, `journal/account_picker/_account_tree_popup.py`, `journal/group_combo/_tree_group_combo.py`, `ledger/ledger_t_account.py`.

**دوال top-level:**
- `_get_type_colors() -> dict`: يرجع قاموس ألوان أنواع الحسابات (asset/liability/capital/revenue/expense/drawings) مقروءة من `_C` مباشرة في كل استدعاء لدعم تغيّر الثيم لايف.
- `_spin(max_=999_999_999, dec=2, min_height=30)`: wrapper حول `spin_field` لإرجاع QDoubleSpinBox موحد — للتوافق مع كود قديم.
- `_money(val: float) -> str`: ينسّق قيمة كـ `"{val:,.2f}  {currency_abbr}"`.
- `_stat_card(label: str, color: str = None)`: يرجع `(QFrame, QLabel_value)` عبر `stat_card_pair`، افتراضي اللون هو `_C["accent"]`.

**ثوابت module-level:**
- `TYPE_COLORS`: قاموس يُبنى مرة واحدة عند الاستيراد عبر استدعاء `_get_type_colors()` — **ملاحظة:** هذا snapshot ثابت وقت import، لا يتحدث تلقائياً مع الثيم؛ الكود الجديد يجب أن يستخدم `_get_type_colors()` مباشرة بدل الاعتماد على `TYPE_COLORS`.

**ملاحظات من التعليقات:**
- [تحديث v4]: `_get_type_colors` تقرأ دائماً من `_C` (لا قيم hardcoded) لدعم الثيمات، و`TYPE_COLORS` يُحدَّث فقط عند كل استدعاء صريح للدالة.

---

### 1.2 `ui/tabs/accounting/_state_widgets.py`

**الغرض:** دوال بناء widgets لعرض حالات الانتظار/الخطأ/الفراغ في `AccountingTab` (تحميل، خطأ اتصال، لا توجد شركة، حالة فارغة).

**Imports مهمة:**
- `ui.widgets.panels.state.EmptyState` — لبناء حالة "لا توجد بيانات" موحدة.
- `ui.theme._C`, `ui.font.FS_BASE/FS_LG`, `ui.constants` (STATE_LABEL_PADDING, STATE_ERROR_BORDER_RADIUS, STATE_ERROR_MARGIN).
- `ui.widgets.core.i18n.tr`.

**من يستدعي هذا الملف:** غير محدد من المرفقات الحالية — `ui/tabs/accounting_section.py` (القسم 0) لا يستورد هذا الملف فعلياً رغم التشابه في الدور؛ يبني رسائله الخاصة (لا شركة/خطأ اتصال) بشكل مباشر داخل `_build()` دون استخدام `make_no_company_widget`/`make_error_widget`.

**دوال top-level:**
- `make_no_company_widget() -> QLabel`: يبني QLabel بنص "اختر شركة أولاً" (`accounting_no_company_msg`) بستايل محايد.
- `make_error_widget(message: str, bg: str = None, color: str = None) -> QLabel`: دالة عامة موحدة لعرض رسالة خطأ بخلفية/لون قابلين للتخصيص (افتراضياً ألوان `badge_cr_bg`/`badge_cr_text`)؛ تحل محل الدالتين القديمتين `make_conn_error_widget` و`make_init_failed_widget`.
- `make_conn_error_widget(error: Exception) -> QLabel`: للتوافق مع كود قديم — تستدعي `make_error_widget` برسالة `conn_error_msg`.
- `make_init_failed_widget() -> QLabel`: للتوافق مع كود قديم — تستدعي `make_error_widget` برسالة `init_failed_msg`.
- `make_loading_widget(attempt: int, max_attempts: int = 5, text: str = None) -> QLabel`: يبني QLabel بنص تحميل مع عداد محاولات.
- `make_empty_state(icon=None, title=None, subtitle="", action_text="") -> EmptyState`: يبني `EmptyState` موحد (قابل للتوسعة `expandable=True`) من `ui.widgets.panels.state`.

**ملاحظات من التعليقات:**
- [تحديث v3]: توحيد استخدام `EmptyPanelState`/`EmptyState`، ودمج دالتي خطأ الاتصال والتهيئة في `make_error_widget` واحدة.

---

### 1.3 `ui/tabs/accounting/account_combo.py`

**الغرض:** ويدجت `_AccountCombo` — Combo قابل للبحث والفلترة (بالتصنيف والنص) لاختيار حساب محاسبي واحد، مع عرض شارة DR/CR للحساب المختار.

**Imports مهمة:**
- `services.accounting.accounts_service.AccountsService` — لجلب المجموعات والحسابات وحساب الرصيد الطبيعي.
- `ui.widgets.core.conn.SafeConnMixin` — لإدارة اتصال قاعدة بيانات آمن (`_get_safe_conn`, `_get_company_id`, `_on_company_event_safe`).
- `ui.widgets.core.widget_mixin.WidgetMixin` — لتسجيل الويدجت تلقائياً على تغييرات الثيم/اللغة/الشركة.
- `.helpers._get_type_colors` — ألوان أنواع الحسابات.

**من يستدعي هذا الملف:** غير محدد من المرفقات الحالية.

**دوال top-level:**
- `_badge_style(side: str = "") -> str`: يبني CSS لشارة DR ("dr")/CR ("cr")/محايدة بناءً على `_C` الحالي.

**Class: `_AccountCombo(SafeConnMixin, QWidget, WidgetMixin)`**
- `__init__(self, conn, acc_types: list = None, parent=None)`: يهيئ الاتصال الآمن، يبني الواجهة، ويحمّل البيانات أول مرة.
- `_refresh_style(self, *_)`: يعيد تلوين `lbl_nb` (شارة الرصيد الطبيعي) عند تغيّر الثيم.
- `_refresh_data(self, company_id=None)`: يُستدعى عند حدث تغيير بيانات الشركة؛ إذا الحدث يخص شركتنا (`_on_company_event_safe`) يجدول `refresh()` عبر `QTimer.singleShot(0, ...)`.
- `_build(self)`: يبني الصف الأفقي: `cmb_group` (فلتر تصنيف، عرض ثابت)، `inp_search` (بحث نصي)، `cmb_account` (القائمة الفعلية للحسابات، stretch=1)، `lbl_nb` (شارة DR/CR).
- `refresh(self)`: يستدعي `_load_groups()` ثم `_load_accounts()`.
- `_load_groups(self)`: يجلب كل التصنيفات المرتبطة بـ `acc_types` (أو كل الأنواع لو `None`)، يبني شجرة عبر `build_group_tree`، ويملأ `cmb_group` مع الحفاظ على الاختيار السابق.
- `_add_group_nodes(self, nodes, depth)`: يضيف عقد شجرة التصنيف لـ `cmb_group` بشكل متكرر مع indent ولون كل عقدة.
- `_load_accounts(self)`: يجلب كل الحسابات الورقية (`list_leaf_accounts`) المطابقة لـ `acc_types` ويخزنها في `_all_accs`، ثم يستدعي `_apply_filter()`.
- `_apply_filter(self)`: يعيد بناء `cmb_account` بالكامل حسب فلتر التصنيف (`gid`) والنص (`q`)، يضيف فواصل (separator) بعنوان كل نوع حساب، يعطل الفواصل، يلوّن كل حساب حسب نوعه، ثم يستعيد الاختيار السابق أو يختار أول حساب حقيقي.
- `_disable_item(self, idx: int)`: يعطّل عنصر combo (يستخدم للفواصل) ويجعله غير قابل للاختيار بخط bold ولون فاتح.
- `_remove_trailing_separators(self)`: يحذف أي separator زائد في نهاية القائمة أو متتالي مع separator آخر.
- `_select_first_real(self)`: يختار أول عنصر حقيقي (ليس separator وليس None) في `cmb_account`.
- `_update_nb_label(self)`: يحدّث نص/ستايل `lbl_nb` حسب الرصيد الطبيعي (DR/CR) للحساب المختار حالياً.
- `current_account_id(self)`: يرجع معرف الحساب المختار حالياً أو `None` (يستثني قيمة `"__sep__"`).
- `set_account(self, acc_id)`: يبحث عن `acc_id` في `cmb_account` ويحدده كاختيار حالي.

**ملاحظات من التعليقات:**
- [إصلاح v5/v6]: إزالة `_on_company_event` الفارغة القديمة، واستبدال القيم الثابتة (الفاصل البصري، spacing) بـ `tr("dash")` وثابت `ACCOUNT_COMBO_LAYOUT_SPACING`.

---

### 1.4 `ui/tabs/accounting/accounting_tabs_builder.py`

**الغرض:** دوال ومكوّن `ThemedTabWidget` لبناء التبويبات الفرعية للقسم المحاسبي (تبويبات الحسابات، حقوق الملكية، القوائم المالية).

**Imports مهمة:**
- `.accounts_tree.AccountsTreePanel`, `.group_manager._GroupManagerPanel` — لبناء تبويب شجرة الحسابات وتبويب إدارة التصنيفات.
- `.financial.trial_balance_tab.TrialBalanceTab`, `.financial.income_statement_tab.IncomeStatementTab`, `.financial.owners_equity_tab.OwnersEquityTab`, `.financial.balance_sheet_tab.BalanceSheetTab` — تبويبات القوائم المالية.
- `ui.widgets.theme.layout_styles` (`tab_style`, `apply_tab_widths`, `normalize_tab_widget`) — لستايل وأحجام التبويبات.
- `ui.widgets.theme.table_styles.splitter_style`.
- `ui.widgets.core.widget_mixin.WidgetMixin`.

**من يستدعي هذا الملف:** `ui/tabs/accounting_section.py` (القسم 0 — يستورد `build_accounts_tabs`, `build_financial_tab`, `ThemedTabWidget`)، `investors/_investors_layout.py` (يستورد `ThemedTabWidget`).

**Class: `ThemedTabWidget(QTabWidget, WidgetMixin)`**
- بديل مباشر لـ `QTabWidget()` + `setStyleSheet()` ثابت — يتابع الثيم تلقائياً عبر `WidgetMixin`.
- `__init__(self, size: str = "inner", parent=None)`: يضبط اتجاه RTL، يطبّع التبويب (`normalize_tab_widget`)، يهيئ `WidgetMixin` بدون lang/data، ويستدعي `_refresh_style()`.
- `_refresh_style(self, *_)`: يطبّق `tab_style(size=self._size)` ويستدعي `apply_tab_widths`.
- `addTab(self, widget, *args, **kwargs)`: override يستدعي `super().addTab` ثم `_refresh_style()` تلقائياً بعد كل إضافة تبويب (لضمان حساب العرض الصحيح لكل التبويبات).
- `insertTab(self, index, widget, *args, **kwargs)`: نفس فكرة `addTab` لكن للإدراج في موضع محدد.

**دوال top-level:**
- `_make_tab_widget(size: str = "inner") -> QTabWidget`: مصنع بسيط يرجع `ThemedTabWidget(size=size)`.
- `build_accounts_tabs(acc)`: يبني تبويب خارجي فيه 3 تبويبات: "الأصول" (شجرة أصول + إدارة تصنيفات)، "الخصوم" (نفس النمط)، وتبويب حقوق الملكية عبر `build_equity_tab(acc)`.
- `build_equity_tab(acc) -> QWidget`: يبني splitter أفقي: يسار = `AccountsTreePanel` لأنواع (`capital`, `drawings`, `revenue`, `expense`) معاً، يمين = تبويبات فرعية لإدارة تصنيفات كل نوع من الأربعة على حدة.
- `build_financial_tab(acc)`: يبني تبويب بحجم "small" فيه 4 تبويبات فرعية: قائمة الدخل، حقوق الملكية، الميزانية العمومية، ميزان المراجعة.

**ملاحظات من التعليقات:**
- [إصلاح dark-mode]: حُذف الثابت القديم `_INNER_TAB_STYLE` (كان snapshot ثابت من `_C` وقت الـ import فقط) نهائياً؛ الاستخدام الحالي أو المستقبلي يجب أن يكون عبر `ThemedTabWidget` أو `tab_style()` وقت الحاجة مباشرة.

---

### 1.5 `ui/tabs/accounting/accounts_combo_widget.py`

**الغرض:** ويدجت `AccountTypeFilter` — شريط فلتر موحد لاختيار نوع حساب محاسبي (Combo بأيقونة)، يوحّد كوداً كان مكرراً في عدة تبويبات مالية.

**Imports مهمة:**
- `ui.widgets.panels.themed_inputs.ThemedComboBox`.
- `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.widgets.core.i18n.tr`.

**من يستدعي هذا الملف:** `ledger/ledger_accounts_panel.py` (`_AccountsPanel` يستخدم `AccountTypeFilter`).

**Class: `AccountTypeFilter(QWidget, WidgetMixin)`**
- **Signal:** `type_changed = pyqtSignal(object)` — يُطلق بالنوع المختار (`str` أو `None`) عند التغيير.
- `__init__(self, type_map: dict, include_all: bool = True, parent=None)`: `type_map` قاموس `{key: label}`. يبني الواجهة ويهيئ `WidgetMixin` (theme+font فقط، بدون lang/data).
- `_build(self, include_all: bool)`: يبني صفاً أفقياً: أيقونة تصنيف + `ThemedComboBox` (مع خيار "كل الأنواع" اختياري) يربط `currentIndexChanged` بإطلاق `type_changed`.
- `_refresh_style(self, *_)`: يعيد تلوين الـ combo حسب الثيم الحالي.
- `current_type(self)`: يرجع `currentData()` للـ combo.
- `set_type(self, key: str)`: يبحث عن `key` في عناصر الـ combo ويحدده.
- `block_signals(self, val: bool)`: يمرر `blockSignals` مباشرة للـ combo الداخلي.

---

### 1.6 `ui/tabs/accounting/accounts_tree.py`

**الغرض:** `AccountsTreePanel` — اللوحة الرئيسية لعرض شجرة الحسابات (مع فلتر تصنيف) بجانب فورم الإضافة/التعديل، داخل splitter أفقي.

**Imports مهمة:**
- `services.accounting.accounts_service.AccountsService`.
- `ui.widgets.core.conn.SafeConnMixin`, `ui.widgets.core.widget_mixin.WidgetMixin`.
- `ui.widgets.components.headers_page.SectionHeader`, `ui.widgets.components.button.make_btn`.
- `ui.widgets.theme.table_styles.splitter_style`, `ui.widgets.theme.layout_styles.tree_style`.
- `ui.widgets.dialogs.confirm.confirm_delete`.
- `.tree._tree_nodes` (`rows_to_tree`, `filter_by_group`, `add_acc_nodes`), `.tree._tree_headers.add_type_header`, `.tree._account_form._AccountForm`, `.tree._group_filter._GroupFilterCombo`.

**من يستدعي هذا الملف:** `accounting_tabs_builder.py` (`build_accounts_tabs`, `build_equity_tab`).

**Class: `AccountsTreePanel(SafeConnMixin, QWidget, WidgetMixin)`**
- `__init__(self, conn, acc_types: list, title: str, parent=None)`: يهيئ الاتصال الآمن، يحفظ `acc_types`/`title`، يبني الواجهة، يهيئ `WidgetMixin` (theme+data)، ثم يحمّل البيانات.
- `_refresh_data(self, company_id=None)`: عند حدث تغيير الشركة (عبر data mixin)، يعيد التحميل إن كان الحدث يخصنا.
- `_refresh_style(self, *_)`: يعيد تطبيق `tree_style()` على الشجرة (إصلاح dark-mode: كانت الشجرة تأخذ الستايل مرة واحدة فقط ولا تتبع الثيم لأن `theme=False` سابقاً)، ويستدعي `refresh_visible_buttons`.
- `_build(self)`: يبني splitter أفقي؛ اليسار = هيدر القسم + صف فلتر التصنيف (`_GroupFilterCombo`) + شجرة الحسابات (3 أعمدة: رمز/اسم/رصيد) + صف أزرار تعديل/حذف؛ اليمين = `_AccountForm`.
- `_on_filter_changed(self)`: يعيد بناء الشجرة عند تغيير فلتر التصنيف (إن لم يكن قيد التحميل).
- `_load(self)`: يمنع إعادة الدخول (`_loading` flag)، يحدّث فلتر التصنيف وفورم الحسابات بـ conn حي، ثم يبني الشجرة.
- `_build_tree(self)`: يجلب كل الحسابات لكل نوع في `acc_types`، يحوّلها لشجرة (`rows_to_tree`)، يفلترها بالتصنيف إن وُجد فلتر، ثم يبني الشجرة النهائية: الأنواع غير-حقوق-الملكية تُعرض مباشرة برأس نوع (`add_type_header`)، وأنواع حقوق الملكية (`capital/drawings/revenue/expense`) تُجمع تحت عقدة أب واحدة "حقوق الملكية" مقسّمة لعقد فرعية لكل نوع، مع لون مأخوذ من `TYPE_COLORS`. تنتهي بعرض الشجرة حتى عمق محدد (`ACCOUNTS_TREE_EXPAND_DEPTH`).
- `_selected_id(self)`: يرجع `UserRole` data للعنصر المحدد في الشجرة، أو `None`.
- `_edit(self)`: يحمّل الحساب المحدد في فورم التعديل، أو ينبّه المستخدم إن لم يوجد تحديد.
- `_delete(self)`: يجلب معاينة حذف (`get_delete_preview`)؛ يرفض الحذف إن كان للحساب قيود (`has_lines`)؛ يعرض تحذيراً إن كان له حسابات فرعية؛ عند التأكيد يستدعي `delete_account_cascade` ويطلق `bus.company_data_changed`.

---

### 1.7 `ui/tabs/accounting/audit_log_tab.py`

**الغرض:** `AuditLogTab` — تبويب [E-04] لعرض سجل العمليات الحساسة (audit log) مع فلترة حسب الجدول/النوع، ترقيم صفحات (pagination)، وdialog تفاصيل لكل سجل.

**Imports مهمة:**
- `services.accounting.audit_service.AuditService` — لجلب صفحات السجل (`get_page`).
- `ui.font` (`get_font_size`, `fs`, `FS_SM`, `FS_BASE`, `FS_MD`).
- `ui.widgets.theme.table_styles` (`table_style`, `splitter_style`).
- `ui.widgets.components.headers_list.StatusBar`, `ui.widgets.components.button.make_btn`, `ui.widgets.panels.state.EmptyState`.
- `ui.widgets.core.conn.SafeConnMixin`, `ui.widgets.core.widget_mixin.WidgetMixin`.

**من يستدعي هذا الملف:** غير محدد من المرفقات الحالية (التعليق الداخلي يقترح استخدامه من `accounting_tabs_builder.py` أو `accounting_section.py`، لكن لا استيراد فعلي لـ `AuditLogTab` ظاهر في محتوى `accounting_section.py` (القسم 0) ولا أي ملف آخر مرفق في هذه الدفعة).

**دوال top-level:**
- `_action_colors() -> dict`: يرجع قاموس `action → (fg, bg)` لأنواع العمليات (delete/update/create) مقروء من `_C['audit_*']`.
- `_table_labels() -> dict`: يرجع قاموس `table_key → label` مترجم (`journal_entries`, `journal_lines`, `accounts`, `inventory_moves`, `investor_entries`).

**ثوابت module-level:**
- `_ACTION_ICONS`: قاموس أيقونات لكل عملية (delete/update/create) مقروءة من `tr()`.
- `_PAGE_SIZE = AUDIT_PAGE_SIZE`: حجم الصفحة الواحدة من ثوابت التطبيق.

**Class: `_AuditDetailDialog(QDialog)`**
- Dialog يعرض تفاصيل سجل واحد بالكامل.
- `__init__(self, record: dict, parent=None)`: يضبط عنوان النافذة، الحجم الأدنى، اتجاه RTL، ويبني المحتوى.
- `_build(self, r: dict)`: يبني هيدر ملون حسب نوع العملية (أيقونة + وقت الإنشاء)، سطر meta (اسم الجدول، معرف السجل، من قام بالتغيير)، منطقة `old_data` معروضة كـ JSON منسّق (`json.dumps(..., indent=2)`) داخل `ThemedTextEdit` للقراءة فقط، وزر إغلاق.

**Class: `AuditLogTab(SafeConnMixin, QWidget, WidgetMixin)`**
- `__init__(self, conn, parent=None)`: يهيئ الاتصال الآمن، يبني الواجهة، يهيئ `WidgetMixin` (theme+font)، ويؤجل التحميل الأول (`QTimer.singleShot(AUDIT_LOAD_DELAY, self._load)`).
- `_build(self)`: يجمع: هيدر (`_build_header`) + شريط فلاتر (`_build_filter_bar`) + الجدول (`_build_table`, stretch) + شريط ترقيم صفحات (`_build_pagination`) + شريط حالة.
- `_refresh_style(self, *_)`: يعيد تلوين كل عناصر الهيدر، الفلاتر، الجدول، وشريط الترقيم حسب الثيم الحالي.
- `_build_header(self) -> QWidget`: عنوان الصفحة + زر تحديث (`btn_refresh` يستدعي `_load`).
- `_build_filter_bar(self) -> QWidget`: فلتر الجدول (`_cmb_table`) وفلتر نوع العملية (`_cmb_action`)، كلاهما يستدعي `_on_filter_changed` عند التغيير.
- `_build_table(self) -> QWidget`: جدول بـ 6 أعمدة (index/type/table/record_id/changed_by/date)، بدون تحديد صفوف عمودي، مع `EmptyState` و`StatusBar` مدمجين في container واحد.
- `_build_pagination(self) -> QWidget`: شريط سفلي فيه `_lbl_page` وزر "تحميل المزيد" (`_btn_load_more`) يستدعي `_load_more`.
- `_load(self)`: يصفّر `_offset` و`_all_records` ويعيد التحميل من الصفر عبر `_fetch_and_fill`.
- `_load_more(self)`: يحمّل الصفحة التالية (بدون تصفير offset).
- `_on_filter_changed(self)`: يستدعي `_load()` عند تغيّر أي فلتر.
- `_fetch_and_fill(self)`: يستدعي `AuditService(conn).get_page(table_name, action, limit=_PAGE_SIZE, offset=self._offset)`، يحدّث `_total_count` عند الصفحة الأولى فقط، يضيف الصفوف الجديدة لـ `_all_records`، يملأ الجدول ويحدّث الترقيم.
- `_fill_table(self, rows: list)`: يملأ صفوف جدول الأودت (رقم، نوع بلون وأيقونة، اسم جدول مترجم، معرف السجل، من قام بالتغيير، التاريخ)، ويحفظ السجل الكامل في `Qt.UserRole` للعمود الأول لاستخدامه لاحقاً في الـ dialog.
- `_update_pagination(self)`: يحدّث `StatusBar` ونص/رؤية زر "تحميل المزيد" حسب عدد السجلات المتبقية.
- `_on_row_double_clicked(self, item)`: يفتح `_AuditDetailDialog` بالسجل الكامل المخزّن في العمود الأول.

**ملاحظات من التعليقات:**
- [إصلاح v2]: كل النصوص/الألوان/الخطوط أصبحت تُقرأ من `tr()`/`_C`/`font.py` بدل قيم مكتوبة مباشرة.

---

### 1.8 `ui/tabs/accounting/financial_statements.py`

**الغرض:** `FinancialStatementsTab` — يجمع تبويبات القوائم المالية الأربعة (دخل، حقوق ملكية، ميزانية عمومية، ميزان مراجعة) في `QTabWidget` واحد، مع إعادة بناء كاملة عند تغيير الشركة.

**Imports مهمة:**
- `.financial.trial_balance_tab.TrialBalanceTab`, `.financial.income_statement_tab.IncomeStatementTab`, `.financial.owners_equity_tab.OwnersEquityTab`, `.financial.balance_sheet_tab.BalanceSheetTab`.
- `ui.widgets.core.conn.SafeConnMixin`.
- `ui.widgets.theme.layout_styles` (`tab_style`, `apply_tab_widths`, `normalize_tab_widget`).

**من يستدعي هذا الملف:** غير محدد من المرفقات الحالية (لا يظهر استيراد له في أي ملف آخر مرفق؛ ملاحظة: `accounting_section.py` يستخدم بدلاً منه `build_financial_tab` من `accounting_tabs_builder.py` مباشرة).

**Class: `FinancialStatementsTab(SafeConnMixin, QWidget)`**
- `__init__(self, conn, parent=None)`: يهيئ الاتصال الآمن، يجهّز layout جذري فارغ، يبني التبويبات، ويربط `bus.company_data_changed`.
- `_on_company_event(self, company_id: int)`: عند حدث يخص شركتنا، يجدول `_rebuild()` عبر `QTimer.singleShot(0, ...)`.
- `_build(self)`: ينشئ `QTabWidget` جديد (RTL، ستايل "small")، يضيف 4 تبويبات (دخل/حقوق ملكية/ميزانية/ميزان مراجعة) بـ conn حي، ويطبّق أحجام التبويبات.
- `_rebuild(self)`: يزيل التبويب القديم بالكامل (`removeWidget`, `hide`, `deleteLater`) ثم يستدعي `_build()` من جديد بـ conn جديد.

---

### 1.9 `ui/tabs/accounting/group_manager.py`

**الغرض:** `_GroupManagerPanel` — لوحة إدارة تصنيفات الحسابات (إضافة/تعديل/حذف تصنيف) لنوع حساب واحد محدد، مع شجرة عرض وفورم أسفلها.

**Imports مهمة:**
- `services.accounting.accounts_service.AccountsService`.
- `ui.widgets.core.events.bus`, `ui.widgets.core.conn.SafeConnMixin`.
- `ui.widgets.helpers.color_picker.ColorPickerWidget` — منتقي لون موحد.
- `ui.widgets.components.headers_page.SectionHeader`, `ui.widgets.components.button.make_btn`, `ui.widgets.components.headers_list.StatusBar`.
- `ui.widgets.theme.layout_styles.tree_style`, `ui.widgets.dialogs.confirm.confirm_delete`.
- `ui.widgets.panels.form_group.FormGroup`, `ui.widgets.components.label.ModeLabel`.

**من يستدعي هذا الملف:** `accounting_tabs_builder.py` (`build_accounts_tabs`, `build_equity_tab`).

**Class: `_GroupManagerPanel(SafeConnMixin, QWidget)`**
- `__init__(self, conn, acc_type: str, parent=None)`: يحفظ `acc_type`، يبني الواجهة، يحمّل البيانات، ويربط `bus.company_data_changed`.
- `_on_company_event(self, company_id: int)`: يعيد التحميل عند حدث يخص شركتنا.
- `_build(self)`: يبني: هيدر قسم (بعنوان يشمل اسم نوع الحساب) + شجرة تصنيفات (عمودان: الاسم وعدد الحسابات) + أزرار تعديل/حذف + شريط حالة + `FormGroup` للإضافة/التعديل يحتوي: `ModeLabel`، حقل الاسم، combo التصنيف الأب، `ColorPickerWidget`، وأزرار إضافة/حفظ/إلغاء.
- `_load(self)`: يجلب كل تصنيفات `acc_type`، يبني شجرة (`build_group_tree`)، يملأ شجرة العرض، يوسّعها بالكامل، يحدّث combo الأب، ويحدّث شريط الحالة بالعدد الكلي.
- `_add_tree_nodes(self, nodes, parent)`: يضيف عقد التصنيف للشجرة بشكل متكرر، مع عدد الحسابات المرتبطة بكل تصنيف (`count_accounts_in_group`) ولون كل عقدة.
- `_refresh_parent_combo(self, exclude_id=None)`: يعيد بناء combo اختيار التصنيف الأب (يستثني `exclude_id` عند التعديل لمنع اختيار الابن كأب لنفسه).
- `_add_parent_nodes(self, nodes, depth, exclude_id)`: يضيف عقد التصنيف الأب للـ combo بشكل متكرر مع indent، ويتجاهل `exclude_id`.
- `_selected_id(self)`: يرجع معرف التصنيف المحدد في الشجرة أو `None`.
- `_add(self)`: يتحقق من إدخال اسم، يضيف تصنيفاً جديداً عبر `AccountsService.add_group`، يصفّر الفورم، ويطلق `bus.company_data_changed`.
- `_edit(self)`: يحمّل بيانات التصنيف المحدد في الفورم (اسم، لون، أب)، ويتحول الفورم لوضع التعديل.
- `_save_edit(self)`: يحدّث التصنيف قيد التعديل (`update_group`)، يصفّر الفورم، ويطلق الحدث.
- `_delete(self)`: يعرض تحذيراً إن كان هناك حسابات مرتبطة (بما فيها الفرعية)، وعند التأكيد يحذف التصنيف ويطلق الحدث.
- `_reset(self)`: يصفّر وضع التعديل والحقول ويعيد بناء combo الأب.

---

### 1.10 `ui/tabs/accounting/journal_tab.py`

**الغرض:** نقطة دخول موحدة تعيد تصدير `JournalTab` (من `journal/journal_tab_widget.py`) و`_JournalTreeTable` و`_JournalForm` فقط، دون منطق إضافي — طبقة توافق بعد تقسيم الملف الأصلي الكبير لعدة ملفات فرعية داخل `journal/`.

**Imports مهمة:**
- `.journal.journal_tab_widget.JournalTab`
- `.journal.journal_tree_table._JournalTreeTable`
- `.journal.journal_form._JournalForm`

**من يستدعي هذا الملف:** `ui/tabs/accounting_section.py` (القسم 0 — يستورد `JournalTab` من `.accounting.journal_tab` صراحةً).

**لا يحتوي على أي class أو دالة خاصة به** — مجرد إعادة تصدير (`# noqa: F401`).

---

### 1.11 `ui/tabs/accounting/ledger_tab.py`

**الغرض:** `LedgerTab` — التبويب الرئيسي لدفتر الأستاذ، يجمع قائمة الحسابات (يسار) مع لوحة حساب T التفصيلية (يمين) في splitter أفقي.

**Imports مهمة:**
- `.ledger.ledger_accounts_panel._AccountsPanel`, `.ledger.ledger_t_account._TAccountPanel`.
- `ui.widgets.core.conn.SafeConnMixin`, `ui.widgets.core.events.bus`.
- `ui.widgets.theme.table_styles.splitter_style`.

**من يستدعي هذا الملف:** `ui/tabs/accounting_section.py` (القسم 0 — استيراد `LedgerTab`).

**Class: `LedgerTab(SafeConnMixin, QWidget)`**
- `__init__(self, conn, parent=None)`: يهيئ الاتصال الآمن، يبني الواجهة، ويربط `bus.company_data_changed`.
- `_on_company_event(self, company_id: int)`: عند حدث يخص شركتنا، يعيد تحميل قائمة الحسابات (`_accounts_panel._refresh_accounts()`) ويصفّر لوحة الحساب T (`_t_panel.clear()`).
- `_build(self)`: splitter أفقي؛ اليسار = `_AccountsPanel(conn, on_select=self._on_account_selected)`؛ اليمين = `_TAccountPanel()` **بدون** تمرير conn في البناء (يُمرَّر لاحقاً في كل `load()` لضمان استخدام اتصال حي دائماً).
- `_on_account_selected(self, acc_id: int)`: يستدعي `self._t_panel.load(self._get_safe_conn(), acc_id)` بـ conn حي في كل مرة (لا يُعاد استخدام conn قديم محفوظ).

**ملاحظات من التعليقات:**
- [v5 — conn isolation]: `_TAccountPanel` لا تحتفظ بـ conn داخلياً بين الاستدعاءات، لضمان أن كل استعلام يستخدم اتصال الشركة النشطة حتى بعد تبديل الشركة.

---

### 1.12 `ui/tabs/accounting/investors_tab.py`

**الغرض:** `InvestorsTab` — التبويب الرئيسي للمستثمرين؛ يشغّل migration، يبني تبويبات المستثمرين (جدول+فورم+تفاصيل وربط بقيد)، ويعيد البناء الكامل عند تغيير الشركة.

**Imports مهمة:**
- `services.accounting.investors_service.InvestorsService` — لتشغيل `migrate()`.
- `.investors._investors_layout.build_investors_tabs`, `.investors._investor_details._InvestorDetails`.
- `ui.widgets.core.conn.DualConnMixin` — يدير اتصالي المحاسبة والـ ERP معاً.
- `ui.widgets.core.events.bus`.

**من يستدعي هذا الملف:** `ui/tabs/accounting_section.py` (القسم 0 — استيراد `InvestorsTab`).

**Class: `InvestorsTab(DualConnMixin, QWidget)`**
- `__init__(self, erp_conn, acc_conn, parent=None)`: يهيئ الاتصال المزدوج، يشغّل الـ migration، يبني الواجهة، ويربط `bus.company_data_changed`.
- `_migrate(self)`: يستدعي `InvestorsService(erp_conn).migrate()` مع التقاط أي استثناء وطباعته فقط (لا يوقف التطبيق).
- `_on_company_event(self, company_id: int)`: عند حدث يخص شركتنا (عبر `DualConnMixin`)، يجدول `_rebuild()`.
- `_build(self)`: يستدعي `build_investors_tabs(acc_conn, erp_conn, self._on_investor_selected)` ويضيف الناتج (`_tabs_widget`) لـ layout الجذر، ويحفظ `_details`.
- `_rebuild(self)`: يزيل التبويب القديم بالكامل، يعيد تشغيل الـ migration، ثم يبني من جديد.
- `_on_investor_selected(self, inv_id)`: يحمّل تفاصيل المستثمر المحدد في `_details`، أو يصفّرها إن لم يوجد اختيار.

---

## 2. `ui/tabs/accounting/financial/`

### 2.1 `ui/tabs/accounting/financial/_financial_helpers.py`

**الغرض:** دالة مساعدة واحدة مشتركة بين تبويبات القوائم المالية لتنسيق المبالغ.

**Imports مهمة:** `ui.widgets.core.i18n.tr` (يُستورد داخل الدالة فقط عند الحاجة لتفادي circular import محتمل).

**من يستدعي هذا الملف:** `owners_equity_tab.py`, `income_statement_tab.py`, `balance_sheet_tab.py` (جميعها تستورد `_money`).

**دوال top-level:**
- `_money(value: float) -> str`: يرجع `tr("amount_dash_placeholder")` إذا كانت القيمة صفراً، وإلا `f"{value:,.2f}"`.

---

### 2.2 `ui/tabs/accounting/financial/trial_balance_tab.py`

**الغرض:** `TrialBalanceTab` — تبويب ميزان المراجعة: جدول بكل الحسابات (رمز/اسم/نوع/مدين/دائن/رصيد) وشريط إجماليات أسفله يوضح إن كان الميزان متوازناً.

**Imports مهمة:**
- `services.accounting.statements_service.StatementsService` — `get_trial_balance()`, `get_type_label()`, `get_normal_balance()`.
- `ui.widgets.tables.tables` (`make_list_table`, `colored_item`).
- `ui.widgets.components.headers_page.PageHeader`.
- `ui.widgets.core.conn.SafeConnMixin`, `ui.widgets.core.widget_mixin.WidgetMixin`.

**من يستدعي هذا الملف:** `accounting_tabs_builder.py` (`build_financial_tab`), `financial_statements.py`.

**Class: `TrialBalanceTab(SafeConnMixin, QWidget, WidgetMixin)`**
- `__init__(self, conn, parent=None)`: يهيئ الاتصال الآمن، يبني الواجهة، يحمّل البيانات، يربط `bus.company_data_changed`، ويهيئ `WidgetMixin` (theme+lang).
- `_on_company_event(self, company_id: int)`: يعيد التحميل عند حدث يخص شركتنا.
- `_refresh_lang(self, *_)`: `pass` — النصوص تُبنى داخل `_build()` وتحتاج إعادة بناء كاملة لتحديثها (غير مطبّق حالياً بشكل جزئي).
- `_build(self)`: `PageHeader` (عنوان + أيقونة ⚖️) + شريط توضيحي (legend) + جدول (`make_list_table`, 6 أعمدة: رمز/اسم/نوع/إجمالي مدين/إجمالي دائن/رصيد) + إطار إجماليات أسفل الجدول (مجموع مدين، مجموع دائن، حالة التوازن).
- `_load(self)`: يجلب صفوف ميزان المراجعة من `StatementsService`، يملأ الجدول صفاً صفاً، يلوّن عمود الرصيد حسب الرصيد الطبيعي للحساب (أخضر/برتقالي حسب كونه مديناً أو دائناً بالإضافة لعلامة الرصيد)، يجمع إجمالي المدين والدائن، ويحدّث نص/لون حالة التوازن (متوازن أخضر / غير متوازن أحمر مع الفرق).

---

### 2.3 `ui/tabs/accounting/financial/income_statement_tab.py`

**الغرض:** `IncomeStatementTab` — تبويب قائمة الدخل: جدولان (إيرادات/مصروفات) جنباً إلى جنب مع بطاقات إحصائية للإجماليات وصافي الربح/الخسارة.

**Imports مهمة:**
- `services.accounting.statements_service.StatementsService` — `get_income_statement()`.
- `ui.widgets.tables.tables.make_table`.
- `ui.widgets.components.headers_page.PageHeader`, `ui.widgets.components.stat_card.StatRow/StatItem`.
- `._financial_helpers._money`.

**من يستدعي هذا الملف:** `accounting_tabs_builder.py` (`build_financial_tab`), `financial_statements.py`.

**Class: `IncomeStatementTab(SafeConnMixin, QWidget, WidgetMixin)`**
- `__init__(self, conn, parent=None)`: نفس نمط `TrialBalanceTab` (بناء، تحميل، ربط الحدث، `WidgetMixin` theme+lang).
- `_on_company_event(self, company_id: int)`: يعيد التحميل عند الحدث المناسب.
- `_build(self)`: `PageHeader` (📊) + `StatRow` (3 عناصر: إجمالي الإيرادات، إجمالي المصروفات، صافي الربح/الخسارة) + splitter أفقي فيه جدولين (إيرادات ومصروفات، كل منهما 3 أعمدة: رمز/بند/مبلغ) مبنيين بنفس الحلقة (`for attr_name, title, color_key in [...]`) لتفادي التكرار.
- `_refresh_style(self, *_)`: يعيد تطبيق ستايل الجداول (`refresh_table_styles`) وتلوين عناوين الأقسام حسب الثيم — إصلاح لمشكلة كانت الجداول تحتفظ بستايل الثيم الأول فقط.
- `_refresh_lang(self, *_)`: يحدّث نصوص عناوين قسم الإيرادات/المصروفات فقط دون إعادة بناء كاملة.
- `_load(self)`: يجلب بيانات قائمة الدخل، يملأ كلا الجدولين (حلقة موحدة لكل من `table_rev`/`table_exp`)، ويحدّث `StatRow` بالإجماليات وصافي الربح (لون أخضر/أحمر حسب الإشارة).

---

### 2.4 `ui/tabs/accounting/financial/owners_equity_tab.py`

**الغرض:** `OwnersEquityTab` — تبويب قائمة حقوق الملكية: جدولا زيادات (رأس مال + صافي دخل) ونقصان (مسحوبات) جنباً لجنب، مع بطاقات إحصائية ومعادلة نصية نهائية لحقوق الملكية الصافية.

**Imports مهمة:**
- `services.accounting.statements_service.StatementsService` — `get_owners_equity_statement()`.
- `ui.widgets.tables.tables.make_table`, `ui.widgets.components.headers_page.PageHeader`, `ui.widgets.components.stat_card.StatRow/StatItem`.
- `ui.widgets.panels.themed_inputs.ThemedFrame`.
- `._financial_helpers._money`.

**من يستدعي هذا الملف:** `accounting_tabs_builder.py` (`build_financial_tab`), `financial_statements.py`.

**Class: `OwnersEquityTab(SafeConnMixin, QWidget, WidgetMixin)`**
- `__init__(self, conn, parent=None)`: نفس النمط العام (بناء/تحميل/ربط حدث/`WidgetMixin` theme+lang).
- `_on_company_event(self, company_id: int)`: يعيد التحميل عند الحدث المناسب.
- `_refresh_lang(self, *_)`: `pass` (نفس ملاحظة `TrialBalanceTab`).
- `_build(self)`: `PageHeader` (👑) + `StatRow` (رأس المال، صافي الدخل، المسحوبات، صافي حقوق الملكية) + splitter أفقي (جدول زيادات `table_cr` يسار، جدول نقصان `table_dr` يمين، كل منهما 4 أعمدة: رمز/بند/نوع/مبلغ) + إطار سفلي لعرض معادلة حقوق الملكية النصية الكاملة.
- `_load(self)`: يملأ `table_cr` بحسابات رأس المال + صف صافي الدخل، يملأ `table_dr` بحسابات المسحوبات، يحدّث `StatRow` (4 قيم)، ويحدّث نص المعادلة (`equity_equation`) بكل القيم منسّقة.

---

### 2.5 `ui/tabs/accounting/financial/balance_sheet_tab.py`

**الغرض:** `BalanceSheetTab` — تبويب الميزانية العمومية: جدول أصول يسار، جدول (خصوم+حقوق ملكية+صافي دخل) يمين، مع بطاقات إحصائية وزر/شارة يوضح إن كانت الميزانية متوازنة.

**Imports مهمة:**
- `services.accounting.statements_service.StatementsService` — `get_balance_sheet()`.
- `ui.widgets.tables.tables.make_table`, `ui.widgets.components.headers_page.PageHeader`, `ui.widgets.components.stat_card.StatRow/StatItem`.
- `._financial_helpers._money`.

**من يستدعي هذا الملف:** `accounting_tabs_builder.py` (`build_financial_tab`), `financial_statements.py`.

**Class: `BalanceSheetTab(SafeConnMixin, QWidget, WidgetMixin)`**
- `__init__(self, conn, parent=None)`: نفس النمط العام (theme+lang في `WidgetMixin`).
- `_on_company_event(self, company_id: int)`: يعيد التحميل عند الحدث المناسب.
- `_build(self)`: `PageHeader` (🏛️) مع زر إجراء إضافي `_btn_balanced` (معطل، يُستخدم كشارة حالة توازن) + `StatRow` (إجمالي أصول، إجمالي خصوم، حقوق ملكية) + splitter أفقي: جدول أصول (3 أعمدة) يسار، جدول خصوم+حقوق ملكية (4 أعمدة يتضمن عمود "نوع") يمين.
- `_refresh_lbl_style(self, lbl: QLabel, color: str)`: دالة مساعدة صغيرة لتلوين عناوين الأقسام.
- `_refresh_style(self, *_)`: يعيد تلوين عناوين الأصول/الخصوم حسب الثيم.
- `_refresh_lang(self, *_)`: يحدّث نصوص عناوين الأصول/الخصوم فقط.
- `_load(self)`: يملأ جدول الأصول، يملأ جدول الخصوم بثلاث مجموعات مدمجة (خصوم، رأس مال، مسحوبات) عبر list comprehension موحدة، يضيف صف صافي الدخل إن لم يكن صفراً، يحدّث `StatRow`، ويحسب الفرق بين (الأصول) و(الخصوم+حقوق الملكية) لتحديد نص/لون شارة `_btn_balanced` (أخضر متوازن / أحمر مع الفرق).

---

## 3. `ui/tabs/accounting/investors/`

### 3.1 `ui/tabs/accounting/investors/_helpers.py`

**الغرض:** دوال مساعدة مشتركة لنظام المستثمرين: جلب حسابات (رأس مال/مسحوبات/أصول)، ملء combos، وتسجيل قيود رأس المال/المسحوبات محاسبياً مع ربطها بالمستثمر.

**Imports مهمة:**
- `ui.widgets.panels.form_fields.spin_field` (يُعاد تصديره كـ `_spin`), `ui.widgets.components.stat_card.stat_card_pair` (يُعاد تصديره كـ `_stat_card`) — إعادة تصدير فقط بدون منطق مكرر.
- `services.accounting.journal_service.JournalService, JournalLine`.
- `services.accounting.accounts_service.AccountsService`.
- `services.accounting.investors_service.InvestorsService`.

**من يستدعي هذا الملف:** `_movement_dialog.py`, `_investor_form.py` (يستوردان `_fill_capital_combo`, `_fill_asset_combo`, `_post_capital_entry`, `_post_drawings_entry`؛ `_investor_form.py` يستخدم أيضاً `_fill_capital_combo`/`_fill_asset_combo`/`_post_capital_entry` فقط).

**دوال top-level:**
- `_fetch_capital_accounts(acc_conn)`: يرجع الحسابات الورقية من نوع `capital` أو `[]` عند الخطأ.
- `_fetch_drawings_accounts(acc_conn)`: نفس الفكرة لنوع `drawings`.
- `_fetch_asset_accounts(acc_conn)`: نفس الفكرة لنوع `asset`.
- `_fill_asset_combo(cmb, acc_conn, prev_id=None)`: يملأ combo بحسابات الأصول مع أيقونة حسب `subtype` (بنك/صندوق/أخرى)؛ يحاول استعادة الاختيار السابق، وإلا يبحث تلقائياً عن حساب يحتوي "111"/"112"/"صندوق"/"بنك" في نصه ليختاره افتراضياً.
- `_fill_capital_combo(cmb, acc_conn, prev_id=None)`: يملأ combo بحسابات رأس المال (رمز — اسم) مع استعادة الاختيار السابق إن وُجد.
- `_fill_drawings_combo(cmb, acc_conn, prev_id=None)`: نفس الفكرة لحسابات المسحوبات.
- `_post_capital_entry(acc_conn, erp_conn, investor_id, investor_name, capital_acc_id, asset_acc_id, amount, date, notes=None)`: ينشئ قيداً محاسبياً (مدين=أصل، دائن=رأس مال) عبر `JournalService.post_entry`، يجلب `line_id` لجانب "credit"، ويربطه بالمستثمر عبر `InvestorsService.link_to_line(..., "capital", ...)`. يرجع `entry_id`.
- `_post_drawings_entry(acc_conn, erp_conn, investor_id, investor_name, drawings_acc_id, asset_acc_id, amount, date, notes=None)`: نفس الفكرة لكن مدين=مسحوبات، دائن=أصل، وربط بجانب "debit" ونوع "drawings". يرجع `entry_id`.

---

### 3.2 `ui/tabs/accounting/investors/_details_table.py`

**الغرض:** دوال بناء وملء جدول الحركات المالية لمستثمر واحد؛ مستخرجة من `_investor_details.py` لفصل منطق بناء الجدول.

**Imports مهمة:**
- `ui.widgets.tables.tables.make_table`, `ui.theme._C`.

**من يستدعي هذا الملف:** `_investor_details.py` فقط (حسب التعليق الداخلي).

**دوال top-level:**
- `build_movements_table()`: يبني جدول بـ 6 أعمدة (رقم ربط [مخفي]، تاريخ، نوع الحركة، مبلغ، رقم مرجعي، وصف)، يضبط عرض الأعمدة، ويفعّل تلوين الصفوف بالتناوب.
- `_type_ar(move_type: str) -> str`: يرجع النص المترجم "حركة رأس مال" أو "حركة مسحوبات".
- `_type_color(move_type: str) -> str`: يرجع لون `_C['investor_capital_text']` أو `_C['investor_drawings_text']` حسب النوع.
- `fill_movement_row(table, r: int, entry: dict)`: يملأ صفاً واحداً بجدول الحركات (المعرف، التاريخ، النوع الملون، المبلغ الملون، الرقم المرجعي، الوصف/الملاحظات).

---

### 3.3 `ui/tabs/accounting/investors/_investor_details.py`

**الغرض:** `_InvestorDetails` — لوحة تعرض تفاصيل مستثمر واحد: بطاقات إحصائية (رأس مال/مسحوبات/صافي استثمار) + جدول حركات مالية + زر حذف حركة.

**Imports مهمة:**
- `services.accounting.investors_service.InvestorsService`, `services.accounting.journal_service.JournalService`.
- `ui.widgets.core.conn.DualConnMixin`.
- `ui.widgets.components.stat_card.StatRow, StatItem`.
- `ui.widgets.dialogs.confirm.confirm_action`.
- `._details_table.build_movements_table, fill_movement_row`.

**من يستدعي هذا الملف:** `_investors_panel.py` (`build_main_panel`), `investors_tab.py` (عبر `InvestorsTab`).

**Class: `_InvestorDetails(DualConnMixin, WidgetMixin, QWidget)`**
- `__init__(self, acc_conn, erp_conn, parent=None)`: يهيئ الاتصال المزدوج، يبني الواجهة، يربط `bus.company_data_changed`.
- `_on_company_event(self, company_id: int)`: يعيد التحديث (`_refresh`) عند حدث يخص شركتنا.
- `_build(self)`: عنوان (`lbl_title` بحالة placeholder افتراضياً) + `StatRow` (إجمالي رأس مال أخضر، إجمالي مسحوبات أحمر، صافي استثمار أزرق) + عنوان قسم الحركات + جدول الحركات (`build_movements_table`) + زر "حذف الحركة المحددة".
- `load(self, inv_id: int)`: يحفظ `_inv_id` ويستدعي `_refresh()`.
- `_refresh_style(self, *_)`: يعيد تلوين `lbl_title`، ويستدعي `refresh_table_styles`/`refresh_visible_buttons` لضمان تتبع الجدول والزر للثيم.
- `_refresh(self)`: يجلب ملخص المستثمر (`get_investor_summary`)، يحدّث نص العنوان (اسم + تاريخ الانضمام)، يحدّث قيم `StatRow` الثلاث (لون صافي الاستثمار أخضر/أحمر حسب الإشارة)، ويملأ جدول الحركات بالكامل من `s["entries"]`.
- `_delete_movement(self)`: يتحقق من وجود صف محدد، يستخرج `link_id` من العمود المخفي، يطلب تأكيداً (`confirm_action`)، وعند التأكيد: يجلب `entry_id` المرتبط بالربط ويحذف القيد المحاسبي (مع التقاط استثناء غير قاتل)، ثم يفك الربط (`unlink`) ويطلق `bus.company_data_changed`.
- `clear(self)`: يصفّر `_inv_id`، يعيد نص العنوان لـ placeholder، يفرّغ الجدول، ويصفّر `StatRow`.

---

### 3.4 `ui/tabs/accounting/investors/_investor_form.py`

**الغرض:** `_InvestorForm` — فورم إضافة/تعديل مستثمر، مع قسم اختياري لتسجيل رأس مال أولي عند الإضافة (ينشئ قيداً محاسبياً تلقائياً).

**Imports مهمة:**
- `services.accounting.investors_service.InvestorsService`.
- `ui.widgets.mixins.form_mixins.EditModeMixin` — يدير التبديل بين وضعي إضافة/تعديل.
- `ui.widgets.core.conn.DualConnMixin`.
- `ui.widgets.panels.form_group.FormGroup`, `ui.widgets.components.label.ModeLabel`.
- `ui.widgets.forms.inputs` (`NotesLineEdit`, `DateField`, `AmountSpinBox`).
- `._helpers` (`_fill_capital_combo`, `_fill_asset_combo`, `_post_capital_entry`).

**من يستدعي هذا الملف:** `_investors_panel.py` (`build_main_panel`)، `_investors_table.py` (يتسلّم `form` كمرجع لفتح وضع التعديل).

**Class: `_InvestorForm(DualConnMixin, QWidget, WidgetMixin, EditModeMixin)`**
- `__init__(self, acc_conn, erp_conn, parent=None)`: يهيئ الاتصال المزدوج، يبني الواجهة، يهيئ وضع التعديل (`init_edit_mode`) بربط أزرار الإضافة/الحفظ/الإلغاء وعنوان الوضع، ويربط `bus.company_data_changed`.
- `_on_company_event(self, company_id: int)`: يعيد ملء combos الحسابات عند حدث يخص شركتنا.
- `_refresh_style(self, *_)`: يعيد تلوين معاينة القيد المتوقع، ويستدعي `refresh_visible_buttons`.
- `_build(self)`: `FormGroup` "بيانات المستثمر" (اسم، تاريخ انضمام، ملاحظات) + `FormGroup` "رأس المال الأولي" (`_initial_grp`، بلون تمييزي) يحتوي: مبلغ (`AmountSpinBox`)، combo حساب رأس المال، combo حساب الإيداع (أصل)، ومعاينة نصية للقيد المتوقع تتحدث تلقائياً عند أي تغيير + صف أزرار إضافة/حفظ/إلغاء.
- `_refresh_account_combos(self)`: يعيد ملء combos رأس المال والأصول مع الحفاظ على الاختيار السابق، ويحدّث المعاينة.
- `_update_init_preview(self)`: يبني نص معاينة القيد (DR أصل / CR رأس مال) أو نص تلميح "أدخل مبلغاً" إن كان المبلغ صفراً.
- `_collect(self) -> dict | None`: يتحقق من إدخال الاسم (ينبّه ويرجع `None` إن كان فارغاً)، ويرجع قاموس `{name, joined_at, notes}`.
- `_add(self)`: يضيف مستثمراً جديداً، وإن كان مبلغ رأس المال الأولي > 0 وتم اختيار حسابين، يسجّل قيد رأس مال أولي عبر `_post_capital_entry` (مع معالجة فشل التسجيل بتنبيه دون فقدان المستثمر المُضاف)، ثم يصفّر الفورم ويطلق الحدث.
- `_save_edit(self)`: يحدّث بيانات المستثمر قيد التعديل فقط (لا يعيد تسجيل رأس مال)، يصفّر الفورم، ويطلق الحدث.
- `_cancel(self)`: يستدعي `_reset()`.
- `load_for_edit(self, inv_id: int)`: يحمّل بيانات المستثمر في الحقول، يخفي قسم رأس المال الأولي (`_initial_grp`)، ويدخل وضع التعديل عبر `EditModeMixin.enter_edit_mode`.
- `_reset(self)`: يمسح كل الحقول، يعيد إظهار `_initial_grp`، ويخرج من وضع التعديل عبر `EditModeMixin.exit_edit_mode`.

---

### 3.5 `ui/tabs/accounting/investors/_investors_layout.py`

**الغرض:** دالة واحدة `build_investors_tabs` تبني `QTabWidget` كامل لقسم المستثمرين (تبويب رئيسي + تبويب ربط بقيد موجود).

**Imports مهمة:**
- `..accounting_tabs_builder.ThemedTabWidget`.
- `._investors_panel.build_main_panel`, `._link_to_entry_panel._LinkToEntryPanel`.

**من يستدعي هذا الملف:** `investors_tab.py` (`InvestorsTab._build`).

**دوال top-level:**
- `build_investors_tabs(acc_conn, erp_conn, on_investor_selected) -> tuple`: يستدعي `build_main_panel` لبناء اللوحة الرئيسية، ينشئ `ThemedTabWidget` (حجم "normal") بتبويبين: اللوحة الرئيسية، ثم `_LinkToEntryPanel`. يرجع `(tabs, details)`.

---

### 3.6 `ui/tabs/accounting/investors/_investors_panel.py`

**الغرض:** دالة واحدة `build_main_panel` تبني اللوحة الرئيسية للمستثمرين: splitter رأسي بين (صف علوي = splitter أفقي فورم+جدول) و(تفاصيل المستثمر أسفل).

**Imports مهمة:**
- `ui.widgets.theme.table_styles.splitter_style`.
- `._investor_form._InvestorForm`, `._investors_table._InvestorsTable`.
- (يستورد `._investor_details._InvestorDetails` داخلياً في الدالة نفسها لتفادي circular import محتمل).

**من يستدعي هذا الملف:** `_investors_layout.py` (`build_investors_tabs`).

**دوال top-level:**
- `build_main_panel(acc_conn, erp_conn, on_investor_selected) -> tuple`: ينشئ `_InvestorForm`, `_InvestorDetails`, `_InvestorsTable` (تمرر `form` و`on_select=on_investor_selected`)؛ يضع الفورم والجدول في splitter أفقي (بنسب `INVESTOR_FORM_SPLIT_SIZES`)، ثم يضعه فوق `_InvestorDetails` في splitter رأسي (بنسب `INVESTOR_PANEL_TOP_H`/`INVESTOR_PANEL_DETAIL_H`). يرجع `(main_widget, details)`.

---

### 3.7 `ui/tabs/accounting/investors/_investors_table.py`

**الغرض:** `_InvestorsTable` — جدول يعرض كل المستثمرين مع ملخص (رأس مال/مسحوبات/صافي) لكل واحد، وأزرار تعديل/حذف/إضافة استثمار/إضافة مسحوبات.

**Imports مهمة:**
- `services.accounting.investors_service.InvestorsService`.
- `ui.widgets.tables.tables` (`make_list_table`, `auto_fit_columns`, `ROW_HEIGHT_LARGE`).
- `ui.widgets.dialogs.confirm.confirm_delete`.
- `ui.widgets.core.conn.DualConnMixin`.
- `._investor_form._InvestorForm`, `._movement_dialog._MovementDialog`.

**من يستدعي هذا الملف:** `_investors_panel.py` (`build_main_panel`).

**دوال top-level:**
- `_get_cols()`: يرجع قائمة عناوين الأعمدة الستة (مترجمة).

**ثوابت module-level:**
- `_COL_WIDTHS = {0: 40, 2: 100, 3: 110, 4: 100, 5: 120}`: عروض الأعمدة الثابتة.

**Class: `_InvestorsTable(DualConnMixin, WidgetMixin, QWidget)`**
- `__init__(self, acc_conn, erp_conn, form: _InvestorForm, on_select, parent=None)`: يهيئ الاتصال المزدوج، يحفظ مرجع الفورم ودالة `on_select`، يبني الواجهة، يحمّل البيانات، ويربط `bus.company_data_changed`.
- `_on_company_event(self, company_id: int)`: يعيد التحميل عند حدث يخص شركتنا.
- `_refresh_style(self, *_)`: يعيد تطبيق ستايل الجدول والأزرار وعنوان القائمة حسب الثيم.
- `_refresh_lang(self, *_)`: يحدّث عناوين أعمدة الجدول عند تغيير اللغة.
- `_build(self)`: عنوان قائمة المستثمرين + جدول (6 أعمدة) + صف أزرار (تعديل، حذف، إضافة استثمار، مسحوبات).
- `_selected_id(self)`: يرجع معرف المستثمر (`int`) من العمود الأول للصف المحدد، أو `None`.
- `_load(self)`: يجلب ملخصات كل المستثمرين (`get_all_investors_summary`)، يملأ الجدول صفاً صفاً (اسم، تاريخ انضمام، رأس مال ملون، مسحوبات ملونة، صافي بخط bold ولون حسب الإشارة)، ثم يضبط عرض الأعمدة تلقائياً (`auto_fit_columns`) إن وُجدت بيانات.
- `_edit(self)`: يستدعي `self._form.load_for_edit(inv_id)` بعد التحقق من وجود تحديد.
- `_delete(self)`: يطلب تأكيداً (`confirm_delete`) ثم يحذف المستثمر ويطلق الحدث.
- `_open_movement(self, move_type: str)`: يفتح `_MovementDialog` (مودال) لتسجيل حركة رأس مال أو مسحوبات للمستثمر المحدد.

---

### 3.8 `ui/tabs/accounting/investors/_link_to_entry_panel.py`

**الغرض:** `_LinkToEntryPanel` — لوحة تسمح بربط مستثمر موجود بقيد محاسبي **موجود بالفعل** (عبر رقمه المرجعي)، بدل إنشاء قيد جديد.

**Imports مهمة:**
- `services.accounting.investors_service.InvestorsService`, `services.accounting.journal_service.JournalService`.
- `ui.widgets.core.conn.DualConnMixin`.
- `ui.widgets.panels.form_group.FormGroup`, `ui.widgets.panels.form_fields.spin_field`, `ui.widgets.panels.form_labels` (`required_label`, `form_label`).
- `ui.widgets.components.notification.NotificationBar`.
- `ui.widgets.forms.inputs.NotesLineEdit`.

**من يستدعي هذا الملف:** `_investors_layout.py` (`build_investors_tabs`).

**Class: `_LinkToEntryPanel(DualConnMixin, WidgetMixin, QWidget)`**
- `__init__(self, acc_conn, erp_conn, parent=None)`: يهيئ الاتصال المزدوج، يبني الواجهة، ويربط `bus.company_data_changed`.
- `_refresh_style(self, *_)`: يعيد تلوين رسالة التنبيه العلوية (`lbl_info`).
- `_on_company_event(self, company_id: int)`: يعيد تحميل قائمة المستثمرين عند حدث يخص شركتنا.
- `_build(self)`: `NotificationBar` (قابلة للإغلاق) + رسالة توضيحية + `FormGroup` تحتوي: combo المستثمر، combo نوع الحركة (رأس مال/مسحوبات)، حقل الرقم المرجعي للقيد، مبلغ، ملاحظات + زر "ربط بالقيد" (خطر/أحمر).
- `_reload_investors(self)`: يعيد ملء combo المستثمرين مع محاولة استعادة الاختيار السابق.
- `_link(self)`: يتحقق من اختيار مستثمر، إدخال رقم مرجعي، ومبلغ موجب؛ يبحث عن القيد بالرقم المرجعي (`get_entry_by_ref`)؛ يحدد جانب الربط (credit لرأس المال، debit للمسحوبات) ويجلب `line_id`؛ يستدعي `InvestorsService.link_to_line`؛ عند النجاح يمسح الحقول، يطلق `bus.company_data_changed`، ويعرض إشعار نجاح عبر `NotificationBar`؛ عند الفشل يعرض `QMessageBox.critical`.

---

### 3.9 `ui/tabs/accounting/investors/_movement_dialog.py`

**الغرض:** `_MovementDialog` — نافذة مودال لإضافة حركة (رأس مال أو مسحوبات) لمستثمر موجود، مع معاينة حية للقيد المحاسبي المتوقع قبل الحفظ.

**Imports مهمة:**
- `ui.widgets.core.events` (`bus`, `emit_company_data_changed`).
- `ui.widgets.core.conn.DualConnMixin`.
- `ui.widgets.panels.form_group.FormGroup`.
- `ui.widgets.forms.inputs` (`NotesLineEdit`, `DateField`, `AmountSpinBox`).
- `._helpers` (`_fill_capital_combo`, `_fill_drawings_combo`, `_fill_asset_combo`, `_post_capital_entry`, `_post_drawings_entry`).

**من يستدعي هذا الملف:** `_investors_table.py` (`_open_movement`).

**Class: `_MovementDialog(DualConnMixin, WidgetMixin, QDialog)`**
- `__init__(self, acc_conn, erp_conn, investor_id, investor_name, move_type="capital", parent=None)`: يحدد العنوان ولون الثيم حسب `move_type` (رأس مال=أخضر استثماري، مسحوبات=أحمر)، ويبني الواجهة.
- `_refresh_style(self, *_)`: يعيد تلوين عنوان النافذة ومعاينة القيد حسب نوع الحركة، ويستدعي `refresh_visible_buttons`.
- `_build(self)`: عنوان (أيقونة + اسم المستثمر + نوع العملية) + `FormGroup` تحتوي: مبلغ (`AmountSpinBox`)، تاريخ (`DateField`)، combo حساب حقوق الملكية (رأس مال أو مسحوبات حسب `move_type`)، combo حساب الأصل (إيداع أو دفع)، معاينة نصية للقيد المتوقع، ملاحظات + صف أزرار تسجيل/إلغاء.
- `_update_preview(self)`: يبني نص المعاينة (DR/CR) حسب `move_type` والقيم الحالية في الحقول.
- `_accept(self)`: يتحقق من المبلغ الموجب واختيار الحسابين، ثم يستدعي `_post_capital_entry` أو `_post_drawings_entry` حسب `move_type`، يطلق `emit_company_data_changed()`، ويقبل الـ dialog (`self.accept()`)؛ عند الفشل يعرض `QMessageBox.critical`.

---

## 4. `ui/tabs/accounting/journal/`

### 4.1 `ui/tabs/accounting/journal/journal_filter.py`

**الغرض:** `_JournalFilterBar` — شريط فلاتر جدول القيود اليومية: بحث نصي، فلتر تصنيف شجري، فلتر حالة توازن، ونطاق تاريخ.

**Imports مهمة:**
- `ui.widgets.core.conn.SafeConnMixin`.
- `ui.widgets.utils.date_range.DateRangeFilter` — موحد لنطاق التاريخ.
- `ui.widgets.core.events` (`bus`, `get_active_company_id`).
- `.group_combo._tree_group_combo._TreeGroupCombo`.

**من يستدعي هذا الملف:** `journal_tree_table.py` (`_JournalTreeTable._build`).

**Class: `_JournalFilterBar(SafeConnMixin, ThemedFrame, WidgetMixin)`**
- **Signal:** `group_reloaded = pyqtSignal()` — يُطلق بعد إعادة بناء `_TreeGroupCombo` عند تغيير الشركة، ليعيد `_JournalTreeTable` ربط signal الـ click.
- `__init__(self, conn, parent=None)`: يهيئ الاتصال الآمن، يحفظ `_company_id` (عبر `get_active_company_id()`)، يبني الواجهة، يهيئ `WidgetMixin` (lang)، ويربط `bus.company_data_changed`.
- `_refresh_lang(self, *_)`: يحدّث placeholders والنصوص، ويعيد بناء عناصر `cmb_balance` (الكل/متوازن/غير متوازن) مع حفظ الاختيار الحالي.
- `_refresh_style(self, *_)`: يعيد تلوين كل عناصر الشريط (بحث، combos، فاصل، زر مسح، عداد) حسب الثيم.
- `_on_company_event(self, company_id: int)`: عند حدث يخصنا، يجدول `_reload_group_combo()`.
- `_reload_group_combo(self)`: يبني `_TreeGroupCombo` جديداً بـ conn حي، يستبدله في الـ layout مكان القديم (يحذف القديم عبر `deleteLater`)، ثم يطلق `group_reloaded`.
- `_build(self)`: صف أول (بحث + فلتر تصنيف + فلتر توازن)، صف ثاني (`DateRangeFilter` موحد + فاصل + زر مسح + عداد نتائج).
- `reset(self)`: يمسح البحث، يعيد فلتر التصنيف والتوازن للحالة الافتراضية، ويصفّر نطاق التاريخ.
- `matches(self, entry: dict) -> bool`: يفحص تطابق قيد واحد مع كل الفلاتر الحالية (نص، تصنيف عبر `get_group_entry_ids()`، حالة توازن بفارق أقل من `JOURNAL_BALANCE_EPSILON`، ونطاق تاريخ).
- `set_count(self, shown: int, total: int)`: يحدّث نص العداد (الكل أو "معروض/إجمالي").

---

### 4.2 `ui/tabs/accounting/journal/journal_form.py`

**الغرض:** `_JournalForm` — فورم إدخال قيد يومية جديد كامل: هيدر (تاريخ/نوع/وصف) + لوحة صفوف ذكية + شريط توازن + أزرار حفظ/مسح، مع دعم ربط أسطر بمستثمرين تلقائياً عند الحفظ.

**Imports مهمة:**
- `services.accounting.journal_service.JournalService, JournalLine`.
- `ui.widgets.core.conn.DualConnMixin`.
- `ui.widgets.core.events.emit_company_data_changed`.
- `.lines._lines_panel._LinesPanel`, `.form._balance_bar._BalanceBar`, `.form._journal_header._JournalHeader`.

**من يستدعي هذا الملف:** `journal_tab_widget.py` (`JournalTab._build`, `_rebuild_children`)، `journal_tab.py` (إعادة تصدير).

**Class: `_JournalForm(DualConnMixin, QWidget, WidgetMixin)`**
- `__init__(self, conn, erp_conn=None, parent=None)`: يهيئ الاتصال المزدوج، يبني الواجهة، يهيئ `WidgetMixin` (lang)، ويطبّق الستايل.
- `_refresh_lang(self, *_)`: يحدّث نص وضع الفورم وأزرار الحفظ/المسح.
- `_refresh_style(self, *_)`: يعيد تلوين عنوان الوضع وأزرار الحفظ/الإلغاء.
- `_build(self)`: عنوان الوضع + `_JournalHeader` + `_LinesPanel` + `_BalanceBar` + صف أزرار حفظ/مسح؛ يضيف سطرين ابتدائيين فارغين للفورم.
- `_on_balance_changed(self)`: يحسب إجمالي مدين/دائن من `_lines_panel`، يحدّث `_balance_bar`، ويفعّل زر الحفظ فقط إن كان القيد متوازناً وله قيمة > 0.
- `_save(self)`: يتحقق من وجود وصف، وجود أسطر، وجود مدين ودائن على الأقل؛ يتحقق من توازن القيد عبر `JournalService.check_balance`؛ يستدعي `post_entry`؛ إن وُجدت روابط مستثمرين (`get_all_investor_links`) وerp متاح، يستدعي `_post_investor_links`؛ يصفّر الفورم، يطلق `emit_company_data_changed()`، ويعرض رسالة نجاح.
- `_post_investor_links(self, conn, erp, entry_id: int, investor_links: list, desc: str)`: لكل رابط مستثمر، يحدد الجانب (credit لرأس المال، debit للمسحوبات)، يجلب `line_id` المطابق، ويستدعي `InvestorsService.link_to_line` (مع التقاط استثناء غير قاتل لكل رابط على حدة).
- `_clear(self)`: يفرّغ لوحة الأسطر، يصفّر الهيدر، يعيد نص الوضع، يعطّل زر الحفظ، ويضيف سطرين ابتدائيين جديدين.

---

### 4.3 `ui/tabs/accounting/journal/journal_tab_widget.py`

**الغرض:** `JournalTab` — التبويب الرئيسي لليومية: splitter رأسي بين `_JournalForm` (أعلى) و`_JournalTreeTable` (أسفل)، مع إعادة بناء الأبناء بالكامل عند تغيير الشركة.

**Imports مهمة:**
- `ui.widgets.core.conn.SafeConnMixin`.
- `services.companies.company_service.CompanyService` — لجلب/التحقق من اتصال ERP النشط.
- `.journal_tree_table._JournalTreeTable`, `.journal_form._JournalForm`.

**من يستدعي هذا الملف:** `journal_tab.py` (إعادة تصدير `JournalTab`).

**Class: `JournalTab(SafeConnMixin, QWidget, WidgetMixin)`**
- `__init__(self, conn, erp_conn=None, parent=None)`: يهيئ الاتصال الآمن، يحفظ `erp_conn`، يبني splitter، يهيئ `WidgetMixin`، ويربط `bus.company_data_changed`.
- `_on_company_event(self, company_id: int)`: يجدول `_rebuild_children()` عند حدث يخصنا.
- `_get_erp_conn(self)`: يرجع `self._erp_conn` إن كان حياً (`CompanyService.is_conn_alive`)، وإلا يجلب اتصالاً جديداً عبر `CompanyService.get_active_erp_conn()`.
- `_refresh_style(self, *_)`: يعيد تلوين حدود splitter (عادي + عند hover).
- `_build(self)`: ينشئ splitter رأسي، ينشئ `_JournalForm` و`_JournalTreeTable` بـ conn/erp حيّين، يضيفهما للـ splitter بنسب `JOURNAL_TAB_SPLITTER_SIZES`، ويجعل الفورم قابلاً للطي (`setCollapsible(0, True)`).
- `_rebuild_children(self)`: يحفظ أحجام الـ splitter الحالية، يخفي ويحذف (`deleteLater`) الفورم والجدول القديمين، ينشئ نسخاً جديدة بـ conn/erp حيّين، يضيفهما للـ splitter، ويستعيد الأحجام المحفوظة (أو الافتراضية إن لم تتوفر).

---

### 4.4 `ui/tabs/accounting/journal/journal_tree_table.py`

**الغرض:** `_JournalTreeTable` — جدول القيود المحاسبية بعرض شجري (كل قيد صف أب قابل للتوسيع يعرض أسطره كصفوف فرعية)، مع فلاتر وأزرار توسيع/طي/حذف.

**Imports مهمة:**
- `services.accounting.journal_service.JournalService`.
- `ui.widgets.core.events` (`bus`, `get_active_company_id`, `emit_company_data_changed`).
- `ui.widgets.components.headers_list.ListHeader, StatusBar`.
- `ui.widgets.dialogs.confirm.confirm_delete`.
- `ui.widgets.tables.tables` (`bold_item`, `colored_item`, `center_item`, `set_row_bg`).
- `..helpers.TYPE_COLORS`, `.journal_filter._JournalFilterBar`, `.journal_form._JournalForm` (مستوردة لكن غير مستخدمة مباشرة في هذا الملف حسب الظاهر من الكود).

**من يستدعي هذا الملف:** `journal_tab_widget.py` (`JournalTab._build`, `_rebuild_children`)، `journal_tab.py` (إعادة تصدير).

**Class: `_JournalTreeTable(SafeConnMixin, QWidget, WidgetMixin)`**
- `_cols()` *(staticmethod)*: يرجع قائمة عناوين الأعمدة السبعة (# / تاريخ / رقم مرجعي / وصف / مدين / دائن / حالة).
- `__init__(self, conn, parent=None)`: يهيئ الاتصال الآمن، يهيئ `_expanded` (set لمعرفات القيود الموسّعة)، يبني الواجهة، يحمّل البيانات، يهيئ `WidgetMixin` (lang)، ويربط `bus.company_data_changed`.
- `_on_company_data_changed(self, company_id: int)`: يعيد التحميل عند حدث يخصنا.
- `_refresh_style(self, *_)`: يحدّث لون خطوط الشبكة في الجدول.
- `_refresh_lang(self, *_)`: يحدّث عنوان الهيدر، نصوص أزرار التوسيع/الطي/الحذف، عناوين أعمدة الجدول، ويعيد تطبيق الفلتر لتحديث نصوص الصفوف (حالة التوازن، أيقونات الطي).
- `_build(self)`: `ListHeader` (عنوان + أزرار: توسيع الكل، طي الكل، حذف المحدد) + `_JournalFilterBar` (مع ربط signals الفلترة وoverride لدالة `reset` لتطبيق الفلتر بعدها، وربط `group_reloaded`) + الجدول نفسه (7 أعمدة، بدون تحديد صفوف عمودي، بدون تناوب ألوان) + `StatusBar`.
- `_connect_filter_signals(self)`: يربط تغييرات البحث/التصنيف الشجري/التوازن/التاريخ كلها بـ `_apply_filter`.
- `_reconnect_group_signal(self)`: يعيد ربط signal الـ click لشجرة التصنيف الجديدة بعد استبدالها (يُستدعى عند `group_reloaded`).
- `_load(self)`: يجلب كل القيود مع أسطرها (`list_entries_with_lines`) ويطبّق الفلتر.
- `_apply_filter(self)`: يفلتر `_entries_data` حسب `_filter.matches`، يحدّث عدادات الفلتر والحالة، ويعيد الرسم (`_render`).
- `_render(self, entries=None)`: يفرّغ الجدول ويعيد بناءه بالكامل: لكل قيد، صف أب (بلون خلفية مميز) بأيقونة توسيع/طي، تاريخ، رقم مرجعي، وصف، مدين، دائن، وحالة توازن (نص ولون حسب الفرق)؛ إن كان موسّعاً، يضيف صفاً فرعياً لكل سطر بالحساب الملوّن حسب نوعه ومبلغه في عمود مدين أو دائن حسب الجانب، بخلفية مختلفة حسب كون السطر مديناً أو دائناً.
- `_on_cell_clicked(self, row, col)`: إن كان النقر على عمود من (0،1،2) لصف أب، يبدّل حالة التوسيع لهذا القيد ويعيد التطبيق.
- `_expand_all(self)`/`_collapse_all(self)`: يوسّع/يطوي كل القيود دفعة واحدة.
- `_selected_entry_id(self)`: يرجع `entry_id` للصف المحدد حالياً من `_row_meta`.
- `_delete_selected(self)`: يتحقق من وجود تحديد، يطلب تأكيداً بعرض وصف القيد، وعند التأكيد يحذف القيد عبر `JournalService.delete`، يزيل معرفه من `_expanded`، ويطلق `emit_company_data_changed()`.

**ملاحظات من التعليقات:**
- [v9]: توحيد استيراد `emit_company_data_changed` من `company_utils`، وتقليل التكرار عبر استيراد أدوات الجدول من `panels` بنقطة واحدة.

---

## 5. `ui/tabs/accounting/journal/account_picker/`

### 5.1 `ui/tabs/accounting/journal/account_picker/_account_picker_button.py`

**الغرض:** `_AccountPickerButton` — زر واحد يفتح `_AccountTreePopup` لاختيار حساب، ويعرض اسم الحساب المختار مع شارة DR/CR.

**Imports مهمة:**
- `services.accounting.accounts_service.AccountsService`.
- `ui.widgets.core.conn.SafeConnMixin`.
- `._account_tree_popup._AccountTreePopup, _TYPE_ORDER`.

**من يستدعي هذا الملف:** `journal/lines/_smart_line.py` (`_SmartLine._build` ينشئ `_acc = _AccountPickerButton(...)`).

**Class: `_AccountPickerButton(SafeConnMixin, WidgetMixin, QWidget)`**
- `__init__(self, conn, acc_types=None, parent=None)`: يهيئ الاتصال الآمن، يبني الواجهة، ويطبّق الستايل.
- `_build(self)`: زر رئيسي (`btn`, stretch=1) + شارة DR/CR (`lbl_nb`, عرض ثابت).
- `_refresh_style(self, *_)`: يعيد تلوين الزر والشارة حسب الثيم.
- `_open_popup(self)`: ينشئ `_AccountTreePopup` بـ conn حي، يضعه أسفل الزر، يوسّع القيمة الافتراضية (مجموعة equity + الأنواع المطلوبة)، ويعرضه كـ modal؛ عند القبول، يجلب بيانات الحساب المختار عبر conn نفسه (**وليس أي conn محفوظ في الـ popup**)، يحدّث الحالة الداخلية، ويجدول إطلاق `_fire_changed` عبر `QTimer.singleShot`.
- `_fire_changed(self)`: يستدعي الـ callback المسجّل (`_on_changed_cb`) إن وُجد.
- `set_on_changed(self, cb)`: يسجّل callback يُستدعى عند تغيّر الاختيار.
- `_update_nb_label(self)`: يحدّث شارة DR/CR بناءً على الرصيد الطبيعي لنوع الحساب المختار حالياً.
- `current_account_id(self)`/`current_account_type(self)`: getters بسيطة.
- `set_account(self, acc_id: int, acc_name: str = None)`: يضبط الحساب المختار برمجياً (يُستخدم عند تحميل بيانات موجودة)، ويحدّث نص الزر وشارة DR/CR.
- `reset(self)`: يصفّر كل الحالة الداخلية ونص الزر والشارة.

**ملاحظات من التعليقات:**
- [إصلاح v3]: `_open_popup` تمرر conn صراحةً لأي استخدام لاحق، بدل الاعتماد على أي conn قد يكون محفوظاً في الـ popup نفسه، لتفادي استخدام اتصال قديم بعد تبديل الشركة.

---

### 5.2 `ui/tabs/accounting/journal/account_picker/_account_tree_popup.py`

**الغرض:** `_AccountTreePopup` — نافذة popup شجرية (مبنية على `QListWidget` وليس `QTreeWidget`) لاختيار حساب واحد، مع بحث نصي، توسيع/طي لكل نوع/مجموعة/تصنيف، وتمييز خاص لمجموعة "حقوق الملكية".

**Imports مهمة:**
- `services.accounting.accounts_service.AccountsService`.
- `...helpers.TYPE_COLORS` (نسبي من `ui/tabs/accounting/helpers.py`).

**من يستدعي هذا الملف:** `_account_picker_button.py` (`_AccountPickerButton._open_popup`).

**ثوابت module-level:**
- `_TYPE_ORDER`: قاموس `acc_type → مفتاح أيقونة مترجم` لكل الأنواع الستة، يُستخدم أيضاً كترتيب افتراضي عند عدم تحديد `acc_types`.

**Class: `_AccountTreePopup(QDialog, WidgetMixin)`**
- **لا تحتفظ بـ `conn` كـ attribute إطلاقاً** — يُستخدم فقط داخل `_load_accounts(conn)` وقت الإنشاء؛ أي استدعاء لاحق (مثل `get_selected_type`) يجب أن يستقبل conn صريحاً من الخارج.
- `__init__(self, conn, acc_types=None, parent=None)`: يضبط نافذة popup بلا إطار (`Qt.Popup | Qt.FramelessWindowHint`)، يهيئ حالة التوسيع الافتراضية (equity + كل الأنواع المطلوبة)، يبني الواجهة، ويحمّل الحسابات بـ conn الممرر مباشرة.
- `_build(self)`: حقل بحث + `QListWidget` (يُستخدم كشجرة مسطّحة بمسافات بادئة نصية) + تسمية تلميح أسفل.
- `_refresh_style(self, *_)`: يعيد تلوين الـ dialog، حقل البحث، والقائمة حسب الثيم.
- `_load_accounts(self, conn)`: يجلب كل الحسابات الورقية لكل نوع في `acc_types` مرة واحدة فقط عند الإنشاء، ويخزنها في `_all_accounts`، ثم يستدعي `_render()`.
- `_on_search(self, text)`: يحفظ نص البحث، يوسّع تلقائياً كل الأقسام عند وجود بحث فعّال، ويعيد الرسم.
- `_render(self)`: يعيد بناء `QListWidget` بالكامل: يجمّع الحسابات حسب النوع ثم التصنيف، يعرض الأنواع المستقلة (غير حقوق ملكية) مباشرة، ثم قسم "حقوق الملكية" الجامع (قابل للطي) الذي يحوي بدوره الأنواع الأربعة الفرعية بترتيب محدد (`capital, drawings, revenue, expense`)، مع تخطي أي قسم لا يطابق نص البحث الحالي.
- `_render_type_section(self, acc_type, groups, q, indent=0)`: يرسم قسم نوع حساب واحد (رأس قابل للطي) وتصنيفاته الفرعية (كل تصنيف رأس فرعي قابل للطي بدوره) وحساباته الورقية.
- `_on_item_clicked(self, item)`: إن كان العنصر رأساً (نوع/تصنيف/equity)، يبدّل حالة التوسيع؛ لا فعل آخر عند النقر على حساب (التحديد الفعلي يتم بالنقر المزدوج).
- `_on_item_double_clicked(self, item)`: إن كان العنصر حساباً فعلياً، يحفظ `_selected_id`/`_selected_name` ويقبل الـ dialog.
- `keyPressEvent(self, event)`: Enter/Return يحاكي نقرة مزدوجة على العنصر الحالي؛ Escape يرفض الـ dialog.
- `get_selected(self)`: يرجع `(selected_id, selected_name)`.
- `get_selected_type(self, conn)`: يستقبل conn صريحاً من المستدعي (وليس محفوظاً داخلياً)، ويرجع نوع الحساب المختار أو `None`.

**ملاحظات من التعليقات:**
- [إصلاح v3]: إزالة كاملة لأي `self._conn` محفوظ، لضمان عدم استخدام اتصال قديم بعد تبديل الشركة النشطة.

---

## 6. `ui/tabs/accounting/journal/form/`

### 6.1 `ui/tabs/accounting/journal/form/_balance_bar.py`

**الغرض:** `_BalanceBar` — شريط يعرض إجمالي مدين، إجمالي دائن، الفرق، وحالة التوازن لقيد اليومية الجاري إدخاله.

**Imports مهمة:** `ui.widgets.core.widget_mixin.WidgetMixin`.

**من يستدعي هذا الملف:** `journal_form.py` (`_JournalForm._build`).

**Class: `_BalanceBar(ThemedFrame, WidgetMixin)`**
- **Signals:** `save_clicked = pyqtSignal()`, `clear_clicked = pyqtSignal()` — معرّفة لكن غير مستخدمة فعلياً داخل هذا الملف نفسه (الحفظ/المسح يُدار من `_JournalForm` مباشرة عبر أزرار منفصلة).
- `__init__(self, parent=None)`: يبني الواجهة ويطبّق الستايل.
- `_build(self)`: صف أفقي من labels: (إجمالي مدين: قيمة) فاصل (إجمالي دائن: قيمة) فاصل (الفرق: قيمة) فاصل (حالة).
- `_badge_style` *(property)*: يرجع CSS مشترك لشارات القيم (radius, padding, margin).
- `_refresh_style(self, *_)`: يعيد تلوين كل عناصر الشريط حسب الثيم الحالي.
- `_refresh_lang(self, *_)`: يحدّث نصوص التسميات الثابتة (إجمالي مدين/دائن/الفرق/حالة البداية).
- `update(self, total_dr: float, total_cr: float) -> bool`: يحدّث القيم المعروضة؛ إن كان كلا الإجماليين صفراً يستدعي `_set_neutral()` ويرجع `False`؛ إن كان الفرق < 0.001 يستدعي `_set_balanced()` ويرجع `True`؛ وإلا يستدعي `_set_unbalanced(diff)` ويرجع `False`.
- `_set_neutral(self)`: حالة محايدة (لا مدخلات بعد) بلون رمادي.
- `_set_balanced(self)`: حالة متوازنة بلون أخضر (نص "متوازن").
- `_set_unbalanced(self, diff: float)`: حالة غير متوازنة بلون أحمر، يوضح أي جانب أكبر (مدين/دائن) وقيمة الفرق.

---

### 6.2 `ui/tabs/accounting/journal/form/_entry_meta.py`

**الغرض:** ملف يحتوي widget-ين صغيرين موحدين لعرض بيانات وصفية للقيد: `_EntryTypeBadge` (شارة نوع القيد) و`_EntryRefLabel` (تسمية الرقم المرجعي).

**Imports مهمة:** `ui.widgets.core.widget_mixin.WidgetMixin`، `ui.widgets.core.i18n.tr`.

**من يستدعي هذا الملف:** غير محدد من المرفقات الحالية (لا يوجد استيراد فعلي ظاهر لأي من الكلاسّين في باقي الملفات المرفقة من `journal/`).

**دوال top-level:**
- `_get_type_colors(entry_type: str) -> tuple`: يرجع `(fg, bg, border)` لكل نوع قيد (manual/opening/closing/transfer/auto) مقروءة من `_C`، مع fallback رمادي للأنواع غير المعروفة.
- `_get_type_label(entry_type: str) -> str`: يرجع التسمية المترجمة المختصرة لكل نوع قيد.

**Class: `_EntryTypeBadge(QLabel, WidgetMixin)`**
- `__init__(self, entry_type: str = "manual", parent=None)`: يحفظ النوع، يوسّط النص، ويطبّق الستايل.
- `_refresh_style(self, *_)`: يستدعي `set_type(self._entry_type)` لإعادة التلوين عند تغيّر الثيم.
- `set_type(self, entry_type: str)`: يحدّث النوع المخزّن، يجلب الألوان والتسمية، ويضبط نص وستايل الشارة.

**Class: `_EntryRefLabel(QLabel, WidgetMixin)`**
- `__init__(self, ref_no: str = None, parent=None)`: يعرض الرقم المرجعي أو placeholder شرطة إن لم يوجد.
- `_refresh_style(self, *_)`: يطبّق ستايل ثابت (لون accent، خط monospace) حسب الثيم.
- `set_ref(self, ref_no: str)`: يحدّث النص المعروض.

---

### 6.3 `ui/tabs/accounting/journal/form/_journal_header.py`

**الغرض:** `_JournalHeader` — صف بيانات القيد العلوي: تاريخ، نوع القيد (يدوي/افتتاحي/ختامي/تحويل)، ووصف.

**Imports مهمة:** `ui.widgets.panels.themed_inputs` (`ThemedLineEdit`, `ThemedComboBox`, `ThemedDateEdit`)، `ui.widgets.core.widget_mixin.WidgetMixin`.

**من يستدعي هذا الملف:** `journal_form.py` (`_JournalForm._build`).

**دوال top-level:**
- `_get_entry_types()`: يرجع قائمة `(key, label)` مترجمة لأربعة أنواع قيود (manual/opening/closing/transfer).

**Class: `_JournalHeader(QWidget, WidgetMixin)`**
- `__init__(self, parent=None)`: يبني الواجهة ويطبّق الستايل.
- `_build(self)`: صف أفقي: (تسمية) تاريخ (`ThemedDateEdit`, تنسيق yyyy-MM-dd) — (تسمية) نوع (`ThemedComboBox`) — (تسمية) وصف (`ThemedLineEdit`, stretch=1).
- `_refresh_style(self, *_)`: يحدّث نصوص التسميات (date/type/desc) وستايل combo النوع.
- `_refresh_lang(self, *_)`: يحدّث كل النصوص والـ placeholder، ويعيد بناء عناصر combo النوع مع حفظ الاختيار الحالي.
- `date_str(self) -> str`: يرجع التاريخ بصيغة `"yyyy-MM-dd"`.
- `description(self) -> str`: يرجع نص الوصف مجتزأ الفراغات.
- `entry_type(self) -> str`: يرجع نوع القيد المختار (افتراضي `"manual"`).
- `reset(self)`: يعيد التاريخ لليوم، يمسح الوصف، ويعيد النوع لأول عنصر (يدوي).

---

## 7. `ui/tabs/accounting/journal/group_combo/`

### 7.1 `ui/tabs/accounting/journal/group_combo/_no_select_delegate.py`

**الغرض:** `_NoSelectDelegate` — delegate يمنع تلوين عناصر الرأس (headers) في شجرة الـ combo كأنها مُختارة، حتى لو كانت تحت المؤشر أو الفوكس.

**Imports مهمة:** `PyQt5.QtWidgets` فقط (لا استيراد داخلي من المشروع).

**من يستدعي هذا الملف:** `journal/group_combo/_tree_group_combo.py` (`_TreeGroupCombo.__init__` ينشئ `_NoSelectDelegate(self._tree_view, is_header_role=_ROLE_IS_HEADER)`).

**ثوابت module-level:**
- `_ROLE_IS_HEADER = None`: placeholder — القيمة الفعلية تُمرَّر من الخارج عند الإنشاء (تُعرَّف فعلياً في `_tree_group_combo.py` كـ `Qt.UserRole + 2`) لتجنب circular import.

**Class: `_NoSelectDelegate(QStyledItemDelegate)`**
- `__init__(self, parent=None, is_header_role=None)`: يحفظ `_is_header_role` (افتراضي `Qt.UserRole + 2` إن لم يُمرَّر).
- `paint(self, painter, option, index)`: يفحص بيانات `_is_header_role` للعنصر؛ إن كان رأساً، يزيل حالة `QStyle.State_Selected` من `option.state` قبل استدعاء الرسم الأصلي — بذلك لا يظهر الرأس بلون التحديد أبداً.

---

### 7.2 `ui/tabs/accounting/journal/group_combo/_tree_group_combo.py`

**الغرض:** `_TreeGroupCombo` — `QComboBox` مخصص يعرض قائمة منسدلة كشجرة (`QTreeView`) هرمية لتصنيفات الحسابات مجمّعة حسب النوع، مع دعم فلترة القيود بحسب التصنيف المختار.

**Imports مهمة:**
- `services.accounting.accounts_service.AccountsService`, `services.accounting.journal_service.JournalService`.
- `ui.widgets.core.events` (`bus`, `get_active_company_id`).
- `ui.widgets.core.conn.SafeConnMixin`.
- `ui.tabs.accounting.helpers.TYPE_COLORS`.
- `._no_select_delegate._NoSelectDelegate`.

**من يستدعي هذا الملف:** `journal_filter.py` (`_JournalFilterBar._build`, `_reload_group_combo`).

**ثوابت module-level:**
- `_TYPE_ORDER`: ترتيب عرض الأنواع الستة في الشجرة.
- `_TYPE_ICON_KEYS`: قاموس مفاتيح أيقونات مترجمة لكل نوع.
- `_ROLE_GROUP_ID = Qt.UserRole + 1`, `_ROLE_IS_HEADER = Qt.UserRole + 2`: أدوار بيانات مخصصة على عناصر الموديل.

**دوال top-level:**
- `_equity_color() -> str`: يرجع لون حقوق الملكية من الثيم الحالي (يُقرأ في runtime وليس عند الاستيراد).

**Class: `_TreeGroupCombo(SafeConnMixin, ThemedComboBox, WidgetMixin)`**
- `__init__(self, conn, parent=None)`: ينشئ `super().__init__(parent, auto_style=False)` لمنع استدعاء `_refresh_style` قبل جهوزية `_tree_view`؛ يهيئ الاتصال الآمن، ينشئ `QStandardItemModel` و`QTreeView` مخصص (بلا رأس، delegate `_NoSelectDelegate`)، يربط `clicked` بـ `_on_tree_clicked`، ثم يهيئ `WidgetMixin` ويملأ البيانات.
- `_refresh_style(self, *_)`: يعيد تلوين `_tree_view` (حدود، خلفية، تحديد، hover) حسب الثيم.
- `_refresh_data(self, company_id=None)`: يستدعي `_reload()` دائماً عند أي حدث بيانات (لا فحص شرطي هنا، الفحص يتم بالأعلى عبر mixin).
- `_populate(self)`: يفرّغ الموديل، يضيف عنصر "كل التصنيفات" (`_ROLE_GROUP_ID=None`)، ثم لكل نوع حساب في `_TYPE_ORDER` له تصنيفات، يضيف عنصر رأس (لون + خلفية مميزة لأنواع equity) ثم يستدعي `_add_group_items` للعقد الفرعية؛ يوسّع الشجرة بالكامل ويستعيد الاختيار السابق.
- `_add_group_items(self, parent_item, nodes, acc_type)`: يضيف عقد التصنيف الفرعية بشكل متكرر تحت عنصر أب، بلون كل عقدة (أو لون النوع كـ fallback).
- `_restore_selection(self, prev_gid)`: يحاول إيجاد العنصر بمعرف `prev_gid` القديم وتحديده، أو يعود لعنصر "الكل".
- `_find_index_by_gid(self, parent, gid) -> QModelIndex`: بحث متكرر عن عنصر بمعرف تصنيف محدد.
- `_on_tree_clicked(self, index)`: إن كان العنصر رأساً، يبدّل توسيع/طي القسم؛ وإلا يحدّث الاختيار (`_update_selection`) ويغلق القائمة المنسدلة.
- `_update_selection(self, item, gid)`: إن كان `gid=None` يعتبرها "الكل" (`_group_entry_ids=None`)؛ وإلا يجلب كل التصنيفات الفرعية (`get_group_descendants`) ويستعلم عن كل معرفات القيود المرتبطة بها (`JournalService.get_entry_ids_for_groups`) ويخزنها في `_group_entry_ids`.
- `currentData(self, role=Qt.UserRole)`: **override** — لا يعتمد على `QComboBox.currentData()` العادية؛ بدلاً من ذلك يقرأ العنصر المحدد فعلياً في `_tree_view` (`selectedIndexes()`) ويرجع `_ROLE_GROUP_ID` الخاص به.
- `get_group_entry_ids(self) -> set | None`: يرجع مجموعة معرفات القيود المطابقة للتصنيف المختار حالياً، أو `None` إن كان الاختيار "الكل".
- `_reload(self)`: يستدعي `_populate()` ثم يوسّع الشجرة بالكامل.
- `reset(self)`: يمسح تحديد الشجرة، يصفّر `_group_entry_ids`، ويعيد الاختيار للعنصر الأول ("الكل").

**ملاحظات من التعليقات:**
- [v5]: توحيد `SafeConnMixin` بدل conn ثابت، واستخدام `get_active_company_id()` الموحدة بدل دالة محلية مكررة كانت موجودة في نسخة سابقة (`journal_group_combo.py` القديم قبل التقسيم).

---

## 8. `ui/tabs/accounting/journal/lines/`

### 8.1 `ui/tabs/accounting/journal/lines/_lines_panel.py`

**الغرض:** `_LinesPanel` — لوحة كاملة تدير قائمة صفوف قيد اليومية (`_SmartLine` واحدة لكل صف): رأس بعرض إجمالي مدين/دائن + منطقة scroll للصفوف + زر إضافة صف.

**Imports مهمة:**
- `ui.widgets.core.conn.DualConnMixin`.
- `._smart_line._SmartLine`.

**من يستدعي هذا الملف:** `journal_form.py` (`_JournalForm._build`).

**Class: `_LinesPanel(DualConnMixin, ThemedFrame, WidgetMixin)`**
- `__init__(self, conn, erp_conn, on_balance_changed, parent=None)`: يهيئ الاتصال المزدوج، يحفظ callback التوازن، يبني الواجهة، ويهيئ `WidgetMixin`.
- `_build(self)`: رأس (عنوان + إجمالي مدين/دائن) + رؤوس أعمدة (حساب/اتجاه/مبلغ/بيان/فراغ لزر الحذف) + منطقة scroll (`_rows_w` داخل `_scroll`) + زر "إضافة سطر".
- `_apply_inner_styles(self)`: يعيد تطبيق كل ستايلات العناصر الداخلية (الإطار، الرأس، التسميات، رؤوس الأعمدة، الـ scroll، زر الإضافة) — إصلاح دفاعي لضمان تتبع الثيم حتى لو تأخر تسجيل بعض العناصر الفرعية على `bus.theme_changed`.
- `_refresh_style(self, *_)`: يستدعي `_apply_inner_styles()`.
- `add_line(self) -> _SmartLine`: ينشئ `_SmartLine` جديدة (بـ conn/erp حيّين وربط callbacks: تغيير، حذف، تحريك لأعلى/أسفل)، يضيفها قبل الـ stretch في `_rows_lay`، يحدّث الإجماليات، ويرجعها.
- `_remove_line(self, line)`: يرفض الحذف إن كان سطراً واحداً متبقياً فقط (ينبّه المستخدم)؛ وإلا يحذف السطر من القائمة والـ layout.
- `_move_up(self, line)`/`_move_dn(self, line)`: يبدّل ترتيب السطر مع الذي يسبقه/يليه في `_lines` ثم يعيد بناء الصفوف (`_rebuild_rows`).
- `_rebuild_rows(self)`: يفرّغ الـ layout (عدا الـ stretch) ويعيد إدراج كل الأسطر بالترتيب الجديد.
- `_on_line_changed(self)`: يحدّث الإجماليات المعروضة ويستدعي callback التوازن الخارجي.
- `_refresh_totals(self)`: يحسب مجموع مدين ودائن من كل الأسطر ويحدّث التسميتين.
- `get_total_dr(self) -> float`/`get_total_cr(self) -> float`: مجموع كل الأسطر ذات الجانب المطابق.
- `get_all_values(self) -> list`: يرجع قيم كل الأسطر التي لها قيمة صالحة (`get_values()` غير `None`).
- `get_all_investor_links(self) -> list`: يرجع كل روابط المستثمرين المفعّلة عبر الأسطر (`get_investor_link()` غير `None`).
- `clear_lines(self)`: يحذف كل الأسطر من الـ layout والقائمة الداخلية ويصفّر الإجماليات.

**ملاحظات من التعليقات:**
- [إصلاح v4]: توحيد `DualConnMixin` بدل تعريف `_get_erp_conn()` يدوياً مكرراً؛ `add_line()` تمرر اتصال ERP حياً لكل سطر جديد.

---

### 8.2 `ui/tabs/accounting/journal/lines/_smart_line.py`

**الغرض:** `_SmartLine` — صف واحد ذكي في قيد اليومية: اختيار حساب، زيادة/نقص (radio)، مبلغ، بيان، وربط اختياري بمستثمر (يظهر تلقائياً لحسابات رأس المال/المسحوبات). يحسب تلقائياً هل هذا السطر مدين أم دائن بناءً على نوع الحساب والرصيد الطبيعي له.

**Imports مهمة:**
- `services.accounting.accounts_service.AccountsService`.
- `ui.widgets.core.events` (`bus`, `get_active_company_id`).
- `ui.widgets.core.conn.DualConnMixin`.
- `..account_picker._account_picker_button._AccountPickerButton`.

**من يستدعي هذا الملف:** `journal/lines/_lines_panel.py` (`add_line`).

**ثوابت module-level:**
- `_INVESTOR_TYPES = {"capital", "drawings"}`: الأنواع التي يظهر لها صف ربط المستثمر.

**دوال top-level:**
- `_resolve_side(acc_type: str, is_increase: bool) -> str`: يجلب الرصيد الطبيعي للنوع (`AccountsService(None).get_normal_balance`)، ويرجع نفس الجانب إن كانت "زيادة"، أو الجانب المعاكس إن كانت "نقص".

**Class: `_SmartLine(DualConnMixin, ThemedFrame, WidgetMixin)`**
- `__init__(self, conn, erp_conn, on_change, on_remove, on_move_up, on_move_dn, parent=None)`: يهيئ الاتصال المزدوج، يحفظ الـ callbacks الأربعة، `_cached_acc_type = None` (كاش لنوع الحساب المختار، إصلاح v7)، يبني الواجهة، ويربط `bus.company_data_changed`.
- `_on_company_event(self, company_id: int)`: يبطل الكاش (`_cached_acc_type = None`) ويعيد تحميل قائمة المستثمرين عند حدث يخصنا.
- `_build(self)`: صف رئيسي: أزرار تحريك لأعلى/أسفل + `_AccountPickerButton` (stretch=4) + إطار راديو زيادة/نقص + `QDoubleSpinBox` للمبلغ + حقل وصف (stretch=2) + زر حذف؛ صف ثانٍ مخفي افتراضياً (`_investor_row`) يظهر فقط لحسابات equity، يحتوي combo اختيار مستثمر.
- `_reload_investors(self)`: يعيد ملء `cmb_investor` من `InvestorsService(erp).list_investors()` مع استعادة الاختيار السابق إن أمكن؛ يتجاهل بصمت أي خطأ أو عدم توفر اتصال ERP.
- `_get_acc_type(self) -> str | None`: يرجع من الكاش مباشرة (`_cached_acc_type`) — لا يستعلم قاعدة البيانات مجدداً.
- `_update_side_style(self)`: يقرأ نوع الحساب من الكاش، يحدد ظهور صف المستثمر (`_INVESTOR_TYPES`)، يحسب الجانب النهائي (`_resolve_side`) ويحفظه في `_resolved_side`، ويلوّن الإطار بالكامل (أخضر=مدين/أحمر=دائن حسب الثيم) أو محايداً إن لم يُختر حساب بعد.
- `_refresh_style(self, *_)`: يستدعي `_update_side_style()`.
- `_on_acc_changed(self)`: **نقطة الكاش الوحيدة** — يجلب نوع الحساب المختار مرة واحدة فقط من `AccountsService.get_account` ويخزنه في `_cached_acc_type`، ثم يحدّث الستايل ويستدعي `on_change`.
- `_on_dir_changed(self)`: يحدّث الستايل ويستدعي `on_change` عند تبديل راديو زيادة/نقص.
- `get_values(self) -> dict | None`: يرجع `None` إن لم يُختر حساب أو كان المبلغ صفراً؛ وإلا قاموس `{account_id, debit, credit, description}` حسب `_resolved_side`.
- `get_investor_link(self) -> dict | None`: يرجع `None` إن كان صف المستثمر غير ظاهر أو لم يُختر مستثمر؛ وإلا `{investor_id, acc_type, amount}`.
- `get_amount(self) -> float`/`get_side(self) -> str`: getters بسيطة للمبلغ والجانب المحلول.

**ملاحظات من التعليقات:**
- [إصلاح v7]: إدخال `_cached_acc_type` لتفادي استعلام مزدوج لقاعدة البيانات (كان يُستدعى مرة في `_update_side_style` ومرة أخرى في `get_values`/`get_investor_link` سابقاً).

---

## 9. `ui/tabs/accounting/ledger/`

### 9.1 `ui/tabs/accounting/ledger/ledger_accounts_panel.py`

**الغرض:** `_AccountsPanel` — قائمة شجرية (مسطّحة فعلياً) لكل حسابات دفتر الأستاذ، مع بحث وفلتر نوع، لاختيار حساب لعرض حساب T الخاص به.

**Imports مهمة:**
- `services.accounting.accounts_service.AccountsService`.
- `ui.widgets.core.conn.SafeConnMixin`.
- `ui.widgets.components.headers_list.ListHeader, StatusBar`.
- `ui.widgets.theme.layout_styles.tree_style`.
- `ui.tabs.accounting.accounts_combo_widget.AccountTypeFilter`.
- `ui.tabs.accounting.helpers.TYPE_COLORS`.

**من يستدعي هذا الملف:** `ledger_tab.py` (`LedgerTab._build`).

**Class: `_AccountsPanel(SafeConnMixin, QWidget, WidgetMixin)`**
- `__init__(self, conn, on_select, parent=None)`: يهيئ الاتصال الآمن، يحفظ callback الاختيار، يبني الواجهة، ثم يحمّل الحسابات.
- `_build(self)`: `ListHeader` (بحث) + `AccountTypeFilter` + `QTreeWidget` (3 أعمدة: رمز/اسم/رصيد، مستخدم كقائمة مسطّحة top-level فقط) + `StatusBar`.
- `_refresh_style(self, *_)`: يعيد تطبيق `tree_style()` على القائمة.
- `_refresh_accounts(self)`: يجلب كل الحسابات (`list_all_accounts()` بدون فلتر نوع) في `_all`، ثم يعيد تطبيق الفلترة.
- `_filter_accounts(self, _=None)`: يفرّغ القائمة ويعيد ملأها بالحسابات الورقية فقط المطابقة لفلتر النوع والبحث النصي، بتلوين الرمز حسب `TYPE_COLORS` وتلوين الرصيد (أخضر موجب/أحمر سالب)، ويحدّث شريط الحالة بالعدد.
- `_on_selected(self)`: يستدعي `on_select(acc_id)` عند تغيّر التحديد.

---

### 9.2 `ui/tabs/accounting/ledger/ledger_filter_bar.py`

**الغرض:** `_LedgerFilterBar` — شريط فلاتر دفتر الأستاذ، يرث من `FilterToolbar` الموحد ويضيف فلتر نوع حركة (مدين/دائن) خاص بحساب T.

**Imports مهمة:**
- `ui.widgets.panels.filter.FilterToolbar` — الأساس المشترك.
- `ui.widgets.theme.builders.v_divider`, `ui.widgets.theme.input_styles.input_style`.

**من يستدعي هذا الملف:** `ledger/ledger_t_account.py` (`_TAccountPanel._build`).

**Class: `_LedgerFilterBar(FilterToolbar)`**
- `__init__(self, parent=None)`: يستدعي `super().__init__` بدون conn (فلترة محلية بالكامل)، `scope="all"`, `show_category=False`, `show_date=True`, `show_presets=False`؛ يضيف فلتر نوع الحركة بعد ذلك.
- `_add_move_type_filter(self)`: يضيف فاصل (`v_divider`) وcombo نوع الحركة (الكل/مدين/دائن) في موقع محسوب داخل الـ layout الموروث (قبل زر المسح تقريباً)؛ يكشف `dt_from`/`dt_to` من `_date_filter` الموروث للتوافق مع الكود الخارجي.
- `matches(self, line: dict) -> bool`: فلترة محلية كاملة (بدون DB): بحث نصي (وصف/مرجع/وصف القيد)، فلتر نوع حركة (`dr`/`cr`)، ونطاق تاريخ (`in_date_range` الموروثة).
- `reset(self)`: يستدعي `super().reset()` ثم يصفّر combo نوع الحركة أيضاً، ويطلق `filter_changed`.

**ملاحظات من التعليقات:**
- [إصلاح v4]: تحويل الملف بالكامل ليرث من `FilterToolbar` الموحد بدل بناء يدوي كامل مستقل.

---

### 9.3 `ui/tabs/accounting/ledger/ledger_stat_cards.py`

**الغرض:** `_StatCards` — شريط بطاقات إحصائية أفقي لدفتر الأستاذ (مدين، دائن، رصيد، عدد الحركات، الرصيد الطبيعي).

**Imports مهمة:**
- `services.accounting.accounts_service.AccountsService`.
- `ui.widgets.components.stat_card.StatRow, StatItem`.

**من يستدعي هذا الملف:** `ledger/ledger_t_account.py` (`_TAccountPanel._build`).

**Class: `_StatCards(ThemedFrame, WidgetMixin)`**
- `__init__(self, parent=None)`: يبني الواجهة ويطبّق الستايل.
- `_refresh_style(self, *_)`: يعيد تلوين الإطار الخارجي حسب الثيم.
- `_build(self)`: `StatRow` بـ 5 عناصر (إجمالي مدين، إجمالي دائن، رصيد، عدد الحركات، الرصيد الطبيعي)، مضغوطة (`compact=True`) وبفاصل بينها؛ يحفظ مراجع مباشرة لكل label قيمة للتوافق مع كود قديم (`lbl_dr`, `lbl_cr`, `lbl_bal`, `lbl_cnt`, `lbl_nb`).
- `update(self, conn, total_dr, total_cr, balance, count, normal_balance, acc_type)`: يحدّث كل القيم الخمس؛ لون الرصيد أخضر (موجب) أو أحمر (سالب)؛ نص الرصيد الطبيعي يجمع بين ترجمة "مدين/دائن" واسم نوع الحساب المترجم.
- `clear(self)`: يصفّر كل القيم عبر `StatRow.reset_all()`.

---

### 9.4 `ui/tabs/accounting/ledger/ledger_t_account.py`

**الغرض:** `_TAccountPanel` — لوحة عرض حساب على شكل "T" (جانب مدين وجانب دائن جنباً لجنب) لحساب واحد مختار في دفتر الأستاذ، مع فلترة وبطاقات إحصائية ورصيد نهائي.

**Imports مهمة:**
- `services.accounting.journal_service.JournalService` — `get_t_account(account_id)`.
- `services.accounting.accounts_service.AccountsService`.
- `ui.tabs.accounting.helpers.TYPE_COLORS`.
- `ui.widgets.components.headers_page.PageHeader`, `ui.widgets.components.amount_label.BalanceDisplay`.
- `.ledger_filter_bar._LedgerFilterBar`, `.ledger_stat_cards._StatCards`.

**من يستدعي هذا الملف:** `ledger_tab.py` (`LedgerTab._build`، بدون تمرير conn في `__init__` — يُمرَّر لاحقاً في `load()`).

**Class: `_TAccountPanel(QWidget, WidgetMixin)`**
- `__init__(self, parent=None)`: `_all_data = None` ابتدائياً، يبني الواجهة (بدون الحاجة لـ conn).
- `_refresh_style(self, *_)`: يعيد تلوين إطار الـ T بالكامل (رؤوس مدين/دائن، إجماليات، فاصل رأسي، جداول) حسب الثيم — يتحقق أولاً من وجود `_t_frame` لتفادي الاستدعاء المبكر قبل `_build`.
- `_build(self)`: `PageHeader` (📒، عنوان placeholder "اختر حساباً") + `_StatCards` + `_LedgerFilterBar` (مع ربط تغييرات البحث/النوع/التاريخ بـ `_apply_filter`، وoverride لدالة `reset` لتطبيق الفلتر بعدها) + إطار T (جانب مدين ويسار عمودي: رأس + جدول + إجمالي؛ فاصل رأسي؛ جانب دائن بنفس البنية) + `BalanceDisplay` أسفل الكل.
- `_make_t_table(self) -> QTableWidget`: يبني جدول فرعي بـ4 أعمدة (تاريخ/رقم قيد/بيان/مبلغ) بستايل موحد.
- `load(self, conn, account_id: int)`: يجلب بيانات حساب T الكاملة (`JournalService.get_t_account`)، يحفظها في `_all_data`، يحدّث عنوان `PageHeader` (رمز+اسم+نوع+الرصيد الطبيعي)، ثم يستدعي `_apply_filter()`.
- `_apply_filter(self)`: يفلتر أسطر الحساب المحفوظة حسب `_filter.matches()`؛ يملأ جدول المدين وجدول الدائن (كل سطر بحسب أي جانب له قيمة > 0)؛ يحدّث إجمالي كل جانب، `BalanceDisplay`، `_StatCards`، وعداد الفلتر.
- `_fill_t_row(self, tbl, r, line, amount, color)`: يملأ صفاً واحداً في أحد جدولي T (تاريخ موسّط، رقم قيد ملون، بيان مع tooltip، مبلغ ملون bold).
- `clear(self)`: يصفّر `_all_data`، يفرّغ الجدولين، يصفّر `BalanceDisplay` و`_StatCards`، ويعيد عنوان `PageHeader` لحالة placeholder.

**ملاحظات من التعليقات:**
- [إصلاح v4]: استبدال `lbl_title`/`lbl_balance` اليدويين بـ `PageHeader`/`BalanceDisplay` الموحدين؛ conn لا يُخزَّن في `__init__` (v3 وما بعدها) بل يُمرَّر فقط عبر `load()` في كل استدعاء لضمان عدم استخدام اتصال قديم.

---

## 10. `ui/tabs/accounting/tree/`

### 10.1 `ui/tabs/accounting/tree/_account_form.py`

**الغرض:** `_AccountForm` — فورم إضافة/تعديل حساب محاسبي واحد (رمز، اسم، نوع، تصنيف)، مع استنتاج تلقائي للحساب الأب من بادئة الرمز عند الإضافة.

**Imports مهمة:**
- `services.accounting.accounts_service.AccountsService`.
- `ui.widgets.core.events.emit_company_data_changed`.
- `ui.widgets.core.conn.SafeConnMixin`.

**من يستدعي هذا الملف:** `accounts_tree.py` (`AccountsTreePanel._build`).

**Class: `_AccountForm(SafeConnMixin, QWidget, WidgetMixin)`**
- `__init__(self, conn, acc_types: list, parent=None)`: يهيئ الاتصال الآمن، يحفظ `acc_types`، يبني الواجهة، ويطبّق الستايل.
- `_refresh_style(self, *_)`: يعيد تلوين `QGroupBox` وتسمية وضع الفورم، ويجبر كل الحقول الفرعية (`inp_code`, `inp_name`, `cmb_type`, `cmb_group`) على استدعاء `_refresh_style()` الخاصة بها دفاعياً (احتياطاً من أي تأخير في تسجيل bus).
- `_build(self)`: `QGroupBox` بفورم (`QFormLayout`): تسمية وضع الفورم، حقل رمز، حقل اسم، combo نوع الحساب (مملوء من `acc_types`)، combo تصنيف (يعتمد على النوع المختار)؛ ربط `cmb_type.currentIndexChanged` بـ `_on_type_changed`؛ صف أزرار إضافة/حفظ/إلغاء (حفظ وإلغاء مخفيان افتراضياً).
- `refresh_group_combos(self, conn=None)`: نقطة دخول عامة تُستدعى من `AccountsTreePanel` عند تغيير الشركة، تستدعي `_refresh_group_combo_for_type(conn=conn)`.
- `_on_type_changed(self)`: يعيد تحميل combo التصنيف عند تغيير نوع الحساب المختار.
- `_refresh_group_combo_for_type(self, conn=None)`: يملأ `cmb_group` بتصنيفات النوع الحالي (شجرياً مع indent)، مع خيار "بدون تصنيف" وحفظ الاختيار السابق.
- `_add_group_nodes(self, nodes, depth)`: إضافة متكررة لعقد التصنيف في الـ combo.
- `_add(self)`: يتحقق من إدخال رمز واسم؛ يستنتج الحساب الأب من بادئة الرمز (الرمز بدون آخر خانة) عبر `get_account_by_code` (بدل SQL مباشر — إصلاح v4)؛ يضيف الحساب، يمسح الحقول، ويطلق `emit_company_data_changed()`؛ عند استثناء يعرض `QMessageBox.warning`.
- `load_for_edit(self, acc_id: int)`: يحمّل بيانات الحساب في الحقول (الرمز يصبح للقراءة فقط)، يحدّث combo التصنيف حسب نوع الحساب، ويدخل وضع التعديل.
- `_save_edit(self)`: يحدّث اسم/تصنيف الحساب قيد التعديل فقط (لا الرمز ولا النوع)، يخرج من وضع التعديل، ويطلق الحدث.
- `_cancel_edit(self)`: يصفّر وضع التعديل ويمسح الحقول.

**ملاحظات من التعليقات:**
- [إصلاح v4]: استبدال SQL مباشر داخل `_add()` باستدعاء `AccountsService.get_account_by_code()` من الـ repo.

---

### 10.2 `ui/tabs/accounting/tree/_group_filter.py`

**الغرض:** `_GroupFilterCombo` — Combo بسيط (وليس شجرياً بصرياً كـ QTreeView، بل نصي بمسافات بادئة) لفلترة شجرة الحسابات حسب التصنيف.

**Imports مهمة:**
- `services.accounting.accounts_service.AccountsService`.
- `ui.widgets.core.conn.SafeConnMixin`.

**من يستدعي هذا الملف:** `accounts_tree.py` (`AccountsTreePanel._build`).

**Class: `_GroupFilterCombo(SafeConnMixin, ThemedComboBox, WidgetMixin)`**
- `__init__(self, conn, acc_types: list, parent=None)`: يهيئ الاتصال الآمن، يحفظ `acc_types`، يهيئ `WidgetMixin` (lang)، ويحمّل البيانات.
- `_refresh_lang(self, *_)`: يعيد التحميل الكامل عند تغيير اللغة.
- `refresh(self, restore_id=None, conn=None)`: يقبل conn خارجياً (يُمرَّر من `AccountsTreePanel` عند تغيير الشركة) وإلا يستخدم `_get_safe_conn()`؛ يملأ الـ combo بخيار "كل التصنيفات" ثم تصنيفات كل نوع في `acc_types` (شجرياً بـ indent ولون).
- `_add_nodes(self, nodes, depth)`: إضافة متكررة لعقد الشجرة مع indent وسهم ولون.

**ملاحظات من التعليقات:**
- [إصلاح v2]: استخدام `_get_safe_conn()` في كل استعلام بدل `self.conn` ثابت، وقبول `refresh(conn=...)` خارجي.

---

### 10.3 `ui/tabs/accounting/tree/_tree_headers.py`

**الغرض:** دالة واحدة `add_type_header` لبناء عقدة رأس نوع حساب في شجرة `AccountsTreePanel`.

**Imports مهمة:**
- `services.accounting.accounts_service.AccountsService`.
- `ui.tabs.accounting.helpers.TYPE_COLORS`.
- `._tree_nodes.add_acc_nodes`.

**من يستدعي هذا الملف:** `accounts_tree.py` (`AccountsTreePanel._build_tree`).

**دوال top-level:**
- `add_type_header(tree_widget: QTreeWidget, acc_type: str, nodes: list, conn) -> QTreeWidgetItem`: ينشئ عقدة رأس top-level بعنوان نوع الحساب المترجم، ملوّنة حسب `TYPE_COLORS` وbold وغير قابلة للتحديد؛ يضيفها للشجرة، يستدعي `add_acc_nodes` لإضافة الحسابات تحتها، ثم يوسّعها. يرجع العقدة نفسها.

---

### 10.4 `ui/tabs/accounting/tree/_tree_nodes.py`

**الغرض:** دوال بناء وفلترة عقد شجرة الحسابات (تحويل صفوف مسطّحة لشجرة، فلترة حسب تصنيف، وإضافة عقد الحسابات فعلياً للـ `QTreeWidget`).

**Imports مهمة:**
- `services.accounting.accounts_service.AccountsService`.
- `ui.tabs.accounting.helpers.TYPE_COLORS`.

**من يستدعي هذا الملف:** `accounts_tree.py` (`rows_to_tree`, `filter_by_group`, `add_acc_nodes`)، `tree/_tree_headers.py` (`add_acc_nodes`).

**دوال top-level:**
- `rows_to_tree(rows) -> list`: يحوّل صفوف مسطّحة (بها `id`, `parent_id`, إلخ) إلى شجرة nested بحقل `children`؛ يبني قاموس `nodes` أولاً، ثم يربط كل عقدة بأبيها إن وُجد وإلا يعتبرها جذراً؛ يرتّب الجذور حسب الرمز (`code`).
- `filter_by_group(conn, nodes: list, gid: int) -> list`: يفلتر الشجرة بحيث تبقى فقط العقد التي تنتمي (مباشرة أو عبر أحد أبنائها بعد الفلترة المتكررة) لتصنيف `gid` أو أحد تصنيفاته الفرعية (`get_group_descendants`).
- `add_acc_nodes(conn, tree_widget: QTreeWidget, nodes: list, parent)`: يضيف عقد الحسابات للشجرة بشكل متكرر (مرتبة حسب الرمز)؛ لكل عقدة يجلب رصيدها (`get_account_balance`)، يلوّنها حسب نوعها، يجعل الحسابات غير الورقية (`is_leaf=0`) bold، ويلوّن الرصيد أحمر (سالب) أو أخضر استثماري (موجب).

---

# قسم علاقات الملفات

## علاقات الاستدعاء الداخلية (بين ملفات هذا المرجع)

- **`accounting_section.py` (القسم 0) هو جذر الاستدعاء الفعلي لكل هذا المرجع**: يبني `AccountingTab` الذي يجمع مباشرة `accounting_tabs_builder.build_accounts_tabs`، `journal_tab.JournalTab`، `ledger_tab.LedgerTab`، `accounting_tabs_builder.build_financial_tab`، و`investors_tab.InvestorsTab` في تبويب رئيسي واحد — أي تعديل جذري في تسلسل التبويبات الخمسة يبدأ من هنا.
- **`helpers.py`** هو الأكثر اعتماداً عليه داخل `ui/tabs/accounting/`: يستورده تقريباً كل ملف يحتاج ألوان أنواع الحسابات (`TYPE_COLORS`/`_get_type_colors`) — `account_combo.py`, `accounts_tree.py`, `tree/_tree_nodes.py`, `tree/_tree_headers.py`, `journal/lines/_smart_line.py`, `journal/journal_tree_table.py`, `journal/account_picker/_account_tree_popup.py`, `journal/group_combo/_tree_group_combo.py`, `ledger/ledger_t_account.py`, `ledger/ledger_accounts_panel.py`.
- **سلسلة بناء تبويب اليومية:** `journal_tab.py` (إعادة تصدير) ← `journal/journal_tab_widget.py` (`JournalTab`) ← يجمع `journal/journal_form.py` (`_JournalForm`) و `journal/journal_tree_table.py` (`_JournalTreeTable`).
  - `_JournalForm` ← `journal/lines/_lines_panel.py` (`_LinesPanel`) ← `journal/lines/_smart_line.py` (`_SmartLine`) ← `journal/account_picker/_account_picker_button.py` (`_AccountPickerButton`) ← `journal/account_picker/_account_tree_popup.py` (`_AccountTreePopup`).
  - `_JournalForm` ← `journal/form/_balance_bar.py` (`_BalanceBar`) و `journal/form/_journal_header.py` (`_JournalHeader`).
  - `_JournalTreeTable` ← `journal/journal_filter.py` (`_JournalFilterBar`) ← `journal/group_combo/_tree_group_combo.py` (`_TreeGroupCombo`) ← `journal/group_combo/_no_select_delegate.py` (`_NoSelectDelegate`).
  - ملاحظة: `journal/form/_entry_meta.py` (`_EntryTypeBadge`, `_EntryRefLabel`) **غير مستخدم فعلياً** من أي ملف آخر في هذه الدفعة رغم وجوده في نفس مجلد `form/`.
- **سلسلة بناء تبويب المستثمرين:** `investors_tab.py` (`InvestorsTab`) ← `investors/_investors_layout.py` (`build_investors_tabs`) ← `investors/_investors_panel.py` (`build_main_panel`) + `investors/_link_to_entry_panel.py` (`_LinkToEntryPanel`).
  - `build_main_panel` ← `investors/_investor_form.py` (`_InvestorForm`) + `investors/_investors_table.py` (`_InvestorsTable`) + `investors/_investor_details.py` (`_InvestorDetails`).
  - `_InvestorsTable` ← `investors/_movement_dialog.py` (`_MovementDialog`).
  - `_InvestorForm`, `_MovementDialog` ← `investors/_helpers.py` (دوال ملء combos وتسجيل قيود).
  - `_InvestorDetails` ← `investors/_details_table.py` (بناء وملء جدول الحركات).
- **سلسلة بناء شجرة الحسابات:** `accounting_tabs_builder.py` (`build_accounts_tabs`, `build_equity_tab`) ← `accounts_tree.py` (`AccountsTreePanel`) + `group_manager.py` (`_GroupManagerPanel`).
  - `AccountsTreePanel` ← `tree/_tree_nodes.py` (`rows_to_tree`, `filter_by_group`, `add_acc_nodes`) + `tree/_tree_headers.py` (`add_type_header`) + `tree/_account_form.py` (`_AccountForm`) + `tree/_group_filter.py` (`_GroupFilterCombo`).
- **سلسلة بناء دفتر الأستاذ:** `ledger_tab.py` (`LedgerTab`) ← `ledger/ledger_accounts_panel.py` (`_AccountsPanel`) + `ledger/ledger_t_account.py` (`_TAccountPanel`).
  - `_AccountsPanel` ← `accounts_combo_widget.py` (`AccountTypeFilter`).
  - `_TAccountPanel` ← `ledger/ledger_filter_bar.py` (`_LedgerFilterBar`) + `ledger/ledger_stat_cards.py` (`_StatCards`).
- **سلسلة القوائم المالية:** `accounting_tabs_builder.py` (`build_financial_tab`) و`financial_statements.py` (`FinancialStatementsTab`) كلاهما يبني نفس التبويبات الأربعة من `financial/`: `trial_balance_tab.py`, `income_statement_tab.py`, `owners_equity_tab.py`, `balance_sheet_tab.py` — الثلاثة الأخيرة تشترك في `financial/_financial_helpers.py` (`_money`).
- **`accounting_tabs_builder.ThemedTabWidget`** يُستخدم أيضاً خارج نفس الملف من `investors/_investors_layout.py`.

## نمط بناء مشترك

- كل الويدجتس الرئيسية تقريباً تتبع نمط: `SafeConnMixin` أو `DualConnMixin` (لإدارة اتصال قاعدة البيانات مع الشركة النشطة) + `WidgetMixin` (لتسجيل تلقائي على تغييرات الثيم/اللغة/بيانات الشركة عبر `bus`) + دالة `_build()` منفصلة + `_refresh_style()`/`_refresh_lang()`/`_refresh_data()` منفصلة عن البناء.
- نمط `_on_company_event(self, company_id)` مع `_on_company_event_safe`/`_on_dual_company_event` متكرر في كل تبويب رئيسي لإعادة التحميل أو إعادة البناء الكامل عند تبديل الشركة النشطة.
- نمط الفورم بوضعين (إضافة/تعديل) متكرر (`_GroupManagerPanel`, `_AccountForm`, `_InvestorForm` — الأخير فقط يستخدم `EditModeMixin` الموحد بينما البقية تدير الحالة يدوياً بمتغير `_editing_id`).
- استخدام `bus.company_data_changed` / `emit_company_data_changed()` كآلية إشعار موحدة بعد أي عملية إضافة/تعديل/حذف تؤثر على بيانات الشركة.

## تبعيات خارج نطاق هذا المسار (مرجعية أخرى)

- `services.accounting.*` (`accounts_service`, `journal_service`, `investors_service`, `statements_service`, `audit_service`) — طبقة الخدمات، مرجعها الخاص `services_accounting.md`.
- `ui.widgets.*` بكل تفرعاته (`core`, `panels`, `components`, `theme`, `dialogs`, `forms`, `tables`, `helpers`, `mixins`, `utils`) — مرجعها `ui_widgets_*.md` (حسب `system_arch.txt`).
- `ui.theme`, `ui.font`, `ui.constants` — ملفات ثوابت/ثيم عامة على مستوى التطبيق كله.
- `services.companies.company_service.CompanyService` — يُستخدم في `journal/journal_tab_widget.py` لجلب اتصال ERP، وفي `accounting_section.py` (القسم 0) للتحقق من جاهزية الشركة (`is_company_ready`) وجلب اتصالي المحاسبة وERP النشطين (`get_active_accounting_conn`, `get_active_erp_conn`).

