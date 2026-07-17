# دليل الكود — نظام الترجمة (i18n)

> مرجع كامل لنظام الترجمة: الملفات، الاستخدام، وكيفية الإضافة.
> يغطي `ui/i18n/ar.py`, `ui/i18n/en.py` (المُجمِّعان) + كل ملفات `ui/i18n/ar_data/` و `ui/i18n/en_data/` (18 ملف دومين).
>
> ⚠️ **[تحديث جذري في البنية]** `ar.py` و `en.py` لم يعودا يحتويان القواميس مباشرة —
> أصبحا **مُجمِّعَين (aggregators)** فقط، وكل الترجمات الفعلية مقسّمة حسب الدومين
> (accounting, companies, costing, design, general, inventory, orders, pricing, shared_items)
> داخل `ar_data/` و `en_data/`. راجع تحذير "قاعدة المطابقة" في الأسفل عند الإضافة.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [المكونات الرئيسية](#المكونات-الرئيسية) | `ui/widgets/core/i18n.py`, `ui/i18n/ar.py`, `ui/i18n/en.py` |
| [ملفات الدومين — عربي](#ملفات-الدومين--عربي-ar_data) | `ui/i18n/ar_data/*.py` (9 ملفات) |
| [ملفات الدومين — إنجليزي](#ملفات-الدومين--إنجليزي-en_data) | `ui/i18n/en_data/*.py` (9 ملفات) |
| [الاستخدام السريع](#الاستخدام-السريع) | أمثلة عملية |
| [إضافة مفاتيح جديدة](#إضافة-مفاتيح-جديدة) | تعليمات التوسعة |
| [ربط اللغة بالـ bus](#ربط-اللغة-بالـ-bus) | التحديث التلقائي |

---

## المكونات الرئيسية

### `ui/widgets/core/i18n.py` — `I18nManager` + `tr()`

المصدر الوحيد لنظام الترجمة. يُحمِّل الترجمات تلقائياً من `ui/i18n/ar.py` و`ui/i18n/en.py` عند الاستيراد. **[بانتظار ملفات ناقصة — محتواه غير مرفق فعلياً في هذه الدفعة]**، لذا الوصف التالي مبني على السلوك الموصوف في المرجع السابق ولم يُعَد التحقق منه من الكود الفعلي:

```python
from ui.widgets.core.i18n import tr, i18n_manager

i18n_manager.language -> str          # "ar" | "en"
i18n_manager.is_rtl -> bool
i18n_manager.qt_direction -> Qt.LayoutDirection
i18n_manager.set_language(lang, save=True)
# يُحدّث _language + يُطبّق اتجاه Layout + يحفظ في DB + يُطلق language_changed

i18n_manager.translate(key, lang=None, **kwargs) -> str
# fallback للعربية لو المفتاح ناقص في اللغة المطلوبة

i18n_manager.load_from_db()
# يحمّل اللغة المحفوظة + يُطبّق الاتجاه — يُستدعى عند بدء التطبيق

i18n_manager.get_available_languages() -> list[{code, name, active, is_rtl}]
i18n_manager.add_translations(lang_code, translations: dict)
# يضيف/يحدث ترجمات برمجياً بدون تعديل الملفات

def tr(key: str, lang=None, **kwargs) -> str
# دالة الترجمة الرئيسية — تُرجع المفتاح نفسه لو غير موجود (fallback صامت)
```

> **ملاحظة:** `tr()` تقبل مفاتيح فقط (مثل `"save"`، `"delete"`).
> لا تمرر نصاً عربياً مباشرة — استخدم المفتاح المقابل دائماً.

---

### `ui/i18n/ar.py` — `AR_STRINGS` (مُجمِّع)

**[تحديث]** لم يعد يحتوي القاموس مباشرة — يجمّع 9 ملفات دومين من `ar_data/` في `dict` واحد بنفس واجهة الاستيراد القديمة.

```python
from ui.i18n.ar_data.ar_general      import AR_STRINGS_GENERAL
from ui.i18n.ar_data.ar_accounting   import AR_STRINGS_ACCOUNTING
from ui.i18n.ar_data.ar_costing      import AR_STRINGS_COSTING
from ui.i18n.ar_data.ar_design       import AR_STRINGS_DESIGN
from ui.i18n.ar_data.ar_inventory    import AR_STRINGS_INVENTORY
from ui.i18n.ar_data.ar_orders       import AR_STRINGS_ORDERS
from ui.i18n.ar_data.ar_pricing      import AR_STRINGS_PRICING
from ui.i18n.ar_data.ar_companies    import AR_STRINGS_COMPANIES
from ui.i18n.ar_data.ar_shared_items import AR_STRINGS_SHARED_ITEMS

AR_STRINGS: dict[str, str] = {}
AR_STRINGS.update(AR_STRINGS_GENERAL)
AR_STRINGS.update(AR_STRINGS_ACCOUNTING)
AR_STRINGS.update(AR_STRINGS_COSTING)
AR_STRINGS.update(AR_STRINGS_DESIGN)
AR_STRINGS.update(AR_STRINGS_INVENTORY)
AR_STRINGS.update(AR_STRINGS_ORDERS)
AR_STRINGS.update(AR_STRINGS_PRICING)
AR_STRINGS.update(AR_STRINGS_COMPANIES)
AR_STRINGS.update(AR_STRINGS_SHARED_ITEMS)
```
يُصدِّر `AR_STRINGS: dict[str, str]` النهائي — يُستورد تلقائياً من `I18nManager`. **ترتيب الـ `.update()` مهم:** أي مفتاح مكرر بين ملفين يفوز فيه آخر ملف بالترتيب أعلاه.

---

### `ui/i18n/en.py` — `EN_STRINGS` (مُجمِّع)

**[تحديث]** نفس نمط `ar.py` بالضبط — يجمّع 9 ملفات دومين من `en_data/` بنفس الترتيب والأسماء:
```python
from ui.i18n.en_data.en_general      import EN_STRINGS_GENERAL
from ui.i18n.en_data.en_accounting   import EN_STRINGS_ACCOUNTING
from ui.i18n.en_data.en_costing      import EN_STRINGS_COSTING
from ui.i18n.en_data.en_design       import EN_STRINGS_DESIGN
from ui.i18n.en_data.en_inventory    import EN_STRINGS_INVENTORY
from ui.i18n.en_data.en_orders       import EN_STRINGS_ORDERS
from ui.i18n.en_data.en_pricing      import EN_STRINGS_PRICING
from ui.i18n.en_data.en_companies    import EN_STRINGS_COMPANIES
from ui.i18n.en_data.en_shared_items import EN_STRINGS_SHARED_ITEMS

EN_STRINGS: dict[str, str] = {}
# نفس تسلسل .update() أعلاه بالضبط
```
يُصدِّر `EN_STRINGS: dict[str, str]` — يجب أن يحتوي على **نفس** مفاتيح `AR_STRINGS` تماماً (عبر كل ملفات الدومين المقابلة).

> **قاعدة:** أي مفتاح ناقص في أي ملف `en_data/*.py` يُرجع النص العربي المقابل كـ fallback صامت (عبر `I18nManager.translate`).

---

## ملفات الدومين — عربي (`ar_data/`)

كل ملف يُصدِّر `dict[str, str]` باسم `AR_STRINGS_<DOMAIN>` ويُجمَّع في `ar.py`. **القاعدة الذهبية لكل ملفات هذا القسم:** لا منطق، لا imports خارجية (غير `dict` type hint) — قاموس ثابت فقط.

### `ui/i18n/ar_data/ar_general.py` — `AR_STRINGS_GENERAL`
أكبر ملف دومين — يغطي: أزرار وإجراءات عامة (`save`, `add`, `edit`, `delete`...)، أزرار فورم بأيقونات (`btn_add`, `btn_save`...)، أيقونات جداول العناصر المشتركة/المنشورة، تنقل الـ sidebar الكامل (`nav_costing`...`nav_settings`, `nav_section_production/finance/work`, أيقونات nav، أيقونات تبويبات)، نصوص `SettingsDialog` بالكامل (تبويبات، خط، ثيم، لغة، وحدات، GIMP)، حالات فارغة، رسائل تأكيد ونجاح/خطأ، رسائل تحقق حقول، حقول عامة مشتركة (`name`, `code`, `amount`...)، وحدات زمنية، فلاتر، شريط حالة، تصنيفات، عمليات عامة، **أسماء تبويبات كل الأقسام** (costing/accounting/inventory/orders/design/pricing tabs)، عنوان التطبيق، pagination.

### `ui/i18n/ar_data/ar_accounting.py` — `AR_STRINGS_ACCOUNTING`
قسم المحاسبة الكامل: دفتر الأستاذ (`ledger`, T-Account)، فورم القيد (`journal_*`)، Audit Log، المستثمرون (`investor_*`)، فلاتر ورسائل الحسابات، تبويبات القسم (assets/liabilities/equity...)، شجرة الحسابات ومدير التصنيفات، القوائم المالية الثلاث (`balance_sheet_*`, `income_statement_*`, `owners_equity_*`, `trial_balance_*`)، جدول القيود الشجري (`journal_tree_table`)، صفوف القيد الذكية (`_smart_line`)، مكوّنات مشتركة (`AmountLabel`, `DebitCreditDisplay`, `BalanceDisplay`)، أيقونات متنوعة (company selector, account tree popup, حالات محاسبية).

### `ui/i18n/ar_data/ar_costing.py` — `AR_STRINGS_COSTING`
قسم حساب التكلفة: أنواع مكونات BOM، `ComponentRow` (نصوص orphan، tooltips التكلفة)، المنتجات، BOM Tree (توسيع/طي/حذف، tooltips)، السيناريوهات ومقارنتها، الاستبدال الشامل (`bulk_replace_*`)، صفوف عمليات التشغيل (`op_rows_*`)، Variants الخامة (`raw_variants_*`)، الخامات (بما فيها العناصر المشتركة `raw_shared_*`/`shared_publish_*`)، العمالة والتشغيل، إعدادات تكلفة العمالة، تبويبات القسم، فورم الماكينة وعملية التشغيل وعملية العمالة والخامة (كل منهم بمفاتيح `*_form_title`, placeholders, رسائل تحقق).

### `ui/i18n/ar_data/ar_design.py` — `AR_STRINGS_DESIGN`
قسم التصميمات: تبويب مجموعات المقاسات (orchestrator)، Source Picker (`dim_src_picker_*`)، تصنيفات مجموعات المقاسات (`dim_cat_*`)، لوحة مجموعات المقاسات (`dim_sets_*`)، Instance Popup لإدخال القيم (`dim_inst_*`)، حقول المجموعة والـ Field Dialog (`dim_field_*`)، قائمة مجموعات المقاسات وبطاقاتها (`dim_sets_list_*`)، جدول قيم المقاسات، نافذة إضافة/تعديل مقاس (`design_size_*` بما فيها تكامل GIMP وحساب canvas بالـ DPI)، بطاقة المقاس، قائمة التصميمات وبطاقاتها، لوحة تفاصيل التصميم، تصنيفات التصميمات (sidebar).

### `ui/i18n/ar_data/ar_inventory.py` — `AR_STRINGS_INVENTORY`
قسم المخزون: حركات وارد/صادر، تقرير المخزون، رسائل الشراء والصرف، فورم الصنف الجديد، بطاقات إحصاء المخزون (عدد أصناف، قيمة إجمالية، تحت الحد الأدنى، نفدت)، حالات الصنف (نفد/منخفض/متوفر)، حركات صنف معيّن.

### `ui/i18n/ar_data/ar_orders.py` — `AR_STRINGS_ORDERS`
قسم الطلبات: حالات الطلب الكاملة (pending→cancelled بأيقوناتها)، لوحة التحكم (Dashboard)، تبويبات القسم، فورم الطلب الكامل (بيانات عميل، تفاصيل، بنود، ملاحظات)، فورم البند، فورم جهة الاتصال، فورم العميل (فردي/شركة)، تغيير الحالة، سجل تغييرات الحالة، أعمدة الجداول (بنود/عملاء/طلبات)، تفاصيل العميل (إجمالي طلبات، رصيد، جهات اتصال).

### `ui/i18n/ar_data/ar_pricing.py` — `AR_STRINGS_PRICING`
قسم التسعير: تسعير منتج فردي (هامش ربح، سعر مقترح/يدوي)، العروض الكاملة (`offer_*` — إضافة منتج للعرض، خصم، تكلفة/ربح، تفاصيل العرض، أعمدة الجدول)، تبويبات (عروض/تصنيفات عروض/أسعار/تصنيفات).

### `ui/i18n/ar_data/ar_companies.py` — `AR_STRINGS_COMPANIES`
قسم الشركات والعناصر المشتركة بين الشركات: إدارة الشركات (`company_*`)، العناصر المشتركة الكاملة (`shared_*` — نشر، ربط/فك ربط شركات، تحديد سريع)، فورم عناصر خامة/ماكينة/عملية عمالة/عملية تشغيل مشتركة، `CompaniesDialog` (جدول + فورم)، `LinkItemPicker`، أيقونات محدد الشركة.

### `ui/i18n/ar_data/ar_shared_items.py` — `AR_STRINGS_SHARED_ITEMS`
أصغر ملف — العملة والوحدات (`currency_*`, `unit_label_*`)، حالة النشر العامة (`shared_items`, `publish`, `published`, `not_published`)، رموز أسهم/أشجار عامة.

---

## ملفات الدومين — إنجليزي (`en_data/`)

نفس البنية والتقسيم تماماً مثل `ar_data/` أعلاه (9 ملفات، نفس الأسماء بحرف `EN_` بدل `AR_`، ونفس المفاتيح إلزامياً). **لا يُعاد سرد المحتوى هنا لتفادي التكرار** — كل ملف `en_data/en_<domain>.py` يقابل تماماً `ar_data/ar_<domain>.py` الموصوف أعلاه، بنفس المفاتيح وقيم إنجليزية مقابلة.

الملفات: `en_general.py`, `en_accounting.py`, `en_costing.py`, `en_design.py`, `en_inventory.py`, `en_orders.py`, `en_pricing.py`, `en_companies.py`, `en_shared_items.py`.

**ملاحظات فروقات ملحوظة عن النسخة العربية (من الكود الفعلي):**
- `en_companies.py`: نص `company_delete_confirm` بالإنجليزية "Delete company «{name}»?\n\nNote: Database files will remain on disk." — نفس البنية الدلالية للعربي.
- `en_pricing.py` / `ar_pricing.py`: مفتاح `pricing_cost_suffix` يختلف تنسيق العملة: EN = `"{cost:.2f}  EGP (cost)"`، AR = `"{cost:.2f}  ج (تكلفة)"`.
- كل الأيقونات (رموز إيموجي مثل `🧱`, `⚙️`, `💰`) **مطابقة حرفياً** بين النسخة العربية والإنجليزية — فقط النص المصاحب يتغير.

---

## الاستخدام السريع

```python
from ui.widgets.core.i18n import tr

# نص بسيط
btn.setText(tr("save"))           # "Save" | "حفظ"
lbl.setText(tr("name"))           # "Name" | "الاسم"

# نص مع format placeholders
msg = tr("delete_confirm_msg", name=item_name)
# EN: "Delete «المنتج»?"  |  AR: "هل تريد حذف «المنتج»؟"

# نص مع عدة متغيرات
msg = tr("showing_of", shown=5, total=100)
# EN/AR: "5 / 100"

# في الـ dialogs
from ui.widgets.dialogs.confirm import confirm_delete
confirm_delete(self, tr("name"))

# أزرار
btn_save   = make_btn(tr("btn_save"),   "success")
btn_cancel = make_btn(tr("btn_cancel"), "ghost")
btn_delete = make_btn(tr("btn_delete"), "danger")
```

---

## ربط اللغة بالـ bus

عند تغيير اللغة من الإعدادات يُطلق `bus.language_changed(lang_code)`.
الـ widgets التي تحتاج تحديث النصوص تشترك عبر `BusConnectedMixin`:

```python
class MyPanel(QWidget, BusConnectedMixin):
    def __init__(self):
        super().__init__()
        self._connect_bus(data=True, lang=True)

    def _on_language_changed(self, lang_code: str):
        self.btn_add.setText(tr("btn_add"))
        self.btn_delete.setText(tr("btn_delete"))
        self._header.search_bar.set_placeholder(tr("list_search_placeholder"))
        self._empty_state.set_title(tr(self.EMPTY_TITLE))
```

**الـ widgets التي تشترك تلقائياً في `language_changed`:**
- `ListHeader` — يُحدّث placeholder البحث
- `StatusBar` — يُحدّث نصوص العداد
- `CrudButtonsBar` — يُحدّث نصوص الأزرار
- `CategoryForm` / `CategoryManager` — يُحدّث عناوين وأزرار التصنيفات
- `BaseListPanel` — يُحدّث placeholder وnص empty state وأزرار pagination
- `BaseDetailPanel` — يُحدّث نص empty state

---

## إضافة مفاتيح جديدة

**[تحديث]** كل مفتاح جديد يُضاف الآن في **ملف الدومين المناسب** (وليس `ar.py`/`en.py` مباشرة، لأنهما مُجمِّعان فقط):

1. اختر الدومين المناسب (accounting, costing, design, inventory, orders, pricing, companies, shared_items, أو general للمشترك).
2. أضف المفتاح في `ui/i18n/ar_data/ar_<domain>.py` داخل `AR_STRINGS_<DOMAIN>` — القيمة العربية.
3. أضف نفس المفتاح في `ui/i18n/en_data/en_<domain>.py` داخل `EN_STRINGS_<DOMAIN>` — القيمة الإنجليزية.
4. **لا تعدّل `ar.py`/`en.py` نفسيهما** — هما فقط `.update()` تسلسلية، أي مفتاح جديد في ملف دومين موجود يظهر تلقائياً في `AR_STRINGS`/`EN_STRINGS` النهائي دون أي تعديل إضافي.

```python
# مثال: إضافة مفتاح "invoice" (دومين orders)

# في ui/i18n/ar_data/ar_orders.py داخل AR_STRINGS_ORDERS:
"invoice": "فاتورة",

# في ui/i18n/en_data/en_orders.py داخل EN_STRINGS_ORDERS:
"invoice": "Invoice",
```

**مفاتيح بـ format placeholders:**
```python
# في ar_orders.py:
"invoice_total": "إجمالي الفاتورة: {amount} {currency}",

# في en_orders.py:
"invoice_total": "Invoice Total: {amount} {currency}",

# الاستخدام:
tr("invoice_total", amount="500.00", currency=tr("currency_abbr"))
```

**تحذير مهم عن ترتيب `.update()`:** لو أضفت نفس المفتاح في أكثر من ملف دومين بالخطأ، آخر ملف بترتيب `.update()` في `ar.py`/`en.py` (general → accounting → costing → design → inventory → orders → pricing → companies → shared_items) هو اللي يفوز. تجنّب تكرار نفس المفتاح بين ملفين.

---

## ملاحظات مهمة

**1. تطابق المفاتيح:** `AR_STRINGS` و`EN_STRINGS` النهائيان (بعد تجميع كل ملفات الدومين) يجب أن يحتويا على **نفس المفاتيح** — أي مفتاح ناقص في أي ملف `en_data/*.py` سيُرجع النص العربي المقابل كـ fallback صامت بدون خطأ.

**2. مفاتيح مكررة:** يجب ألا يظهر نفس المفتاح في أكثر من ملف دومين واحد لنفس اللغة (راجع تحذير ترتيب `.update()` أعلاه) — Python تحتفظ بآخر قيمة بصمت بدون تحذير.

**3. `notice` vs `info`:** مفتاحان منفصلان (كلاهما في `ar_general.py`/`en_general.py`) — `notice` = "ملاحظة"/"Notice"، `info` = "معلومة"/"Info".

**4. مفاتيح أسماء التبويبات:** موجودة في `ar_general.py`/`en_general.py` تحت قسم "أسماء تبويبات الأقسام" (يغطي كل الأقسام: costing, accounting, inventory, orders, design, pricing) — استخدمها في `_build_tabs()` بدل النصوص المباشرة (راجع `ui_root.md` لتفاصيل `_INDEX_MAP`).

**5. لا تمرر النص مباشرة لـ `tr()`:**
```python
# ❌ خطأ
lbl.setText(tr("حفظ"))

# ✅ صح
lbl.setText(tr("save"))
```

**6. الفصل بحسب الدومين وليس المكوّن:** التقسيم الحالي منطقي حسب قسم العمل (accounting/costing/...) وليس حسب نوع الـ widget — أي مفتاح خاص بمكوّن مشترك عابر للأقسام (مثل `AmountLabel` أو `ColorPickerWidget`) يوضع في ملف الدومين الأقرب لاستخدامه الأساسي (مثال: مكوّنات المحاسبة المشتركة موجودة داخل `ar_accounting.py`/`en_accounting.py` رغم أنها widgets عامة، لأنها ظهرت أول مرة هناك).

---

## علاقات الملفات

- `ui/i18n/ar.py` يستورد ويُجمِّع كل ملفات `ui/i18n/ar_data/*.py` (9 ملفات) — لا يوجد أي ملف آخر يستورد من `ar_data/` مباشرة (الاستيراد الوحيد المتوقع هو عبر `ar.py`).
- `ui/i18n/en.py` نفس النمط مع `ui/i18n/en_data/*.py`.
- `ui/widgets/core/i18n.py` (`I18nManager`) يستورد `AR_STRINGS` من `ar.py` و`EN_STRINGS` من `en.py` فقط — لا علاقة مباشرة بملفات الدومين الفردية.
- كل ملفات `ar_data/*.py` و `en_data/*.py` **مستقلة تماماً عن بعضها البعض** — لا استيراد متبادل بينها؛ كل ملف يُصدِّر `dict` واحد فقط بلا أي تبعية خارجية غير `dict` type hint.
- أي كود UI في `ui/tabs/` أو `ui/widgets/` يستدعي `tr()` من `ui.widgets.core.i18n` فقط — لا يستورد أبداً من `ar.py`/`en.py`/`ar_data`/`en_data` مباشرة.

---

## بانتظار ملفات ناقصة

| اسم الملف | المسار الكامل | الحالة |
|---|---|---|
| `i18n.py` | `ui/widgets/core/i18n.py` | غير مرفق محتواه في هذه الدفعة — القسم "المكونات الرئيسية" أعلاه مبني على وصف سابق غير مُتحقَّق منه حديثاً |