# دليل الكود — نظام الترجمة (i18n)

> مرجع كامل لنظام الترجمة: الملفات، الاستخدام، وكيفية الإضافة.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [المكونات الرئيسية](#المكونات-الرئيسية) | `ui/widgets/core/i18n.py`, `ui/i18n/ar.py`, `ui/i18n/en.py` |
| [الاستخدام السريع](#الاستخدام-السريع) | أمثلة عملية |
| [إضافة مفاتيح جديدة](#إضافة-مفاتيح-جديدة) | تعليمات التوسعة |
| [ربط اللغة بالـ bus](#ربط-اللغة-بالـ-bus) | التحديث التلقائي |

---

## المكونات الرئيسية

### `ui/widgets/core/i18n.py` — `I18nManager` + `tr()`

المصدر الوحيد لنظام الترجمة. يُحمِّل الترجمات تلقائياً من `ui/i18n/ar.py` و`ui/i18n/en.py` عند الاستيراد.

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

### `ui/i18n/ar.py` — `AR_STRINGS`

القاموس العربي الكامل. اللغة الأم للتطبيق.
يُصدِّر `AR_STRINGS: dict[str, str]` — يُستورد تلقائياً من `I18nManager`.

---

### `ui/i18n/en.py` — `EN_STRINGS`

القاموس الإنجليزي الكامل.
يُصدِّر `EN_STRINGS: dict[str, str]` — يجب أن يحتوي على **نفس** مفاتيح `AR_STRINGS` تماماً.

> **قاعدة:** أي مفتاح ناقص في `en.py` يُرجع النص العربي كـ fallback صامت.

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

كل مفتاح جديد يُضاف في **مكانين فقط**:

1. **`ui/i18n/ar.py`** — القيمة العربية (داخل `AR_STRINGS`)
2. **`ui/i18n/en.py`** — القيمة الإنجليزية (داخل `EN_STRINGS`)

```python
# مثال: إضافة مفتاح "invoice"

# في ar.py:
"invoice": "فاتورة",

# في en.py:
"invoice": "Invoice",
```

**مفاتيح بـ format placeholders:**
```python
# في ar.py:
"invoice_total": "إجمالي الفاتورة: {amount} {currency}",

# في en.py:
"invoice_total": "Invoice Total: {amount} {currency}",

# الاستخدام:
tr("invoice_total", amount="500.00", currency=tr("currency_abbr"))
```

---

## ملاحظات مهمة

**1. تطابق المفاتيح:** `AR_STRINGS` و`EN_STRINGS` يجب أن يحتويا على **نفس المفاتيح** — أي مفتاح ناقص في `en.py` سيُرجع النص العربي كـ fallback صامت بدون خطأ.

**2. مفاتيح مكررة:** Python تحتفظ بآخر قيمة — كل مفتاح يجب أن يظهر **مرة واحدة فقط** في كل ملف.

**3. `notice` vs `info`:** مفتاحان منفصلان — `notice` = "ملاحظة"، `info` = "معلومة".

**4. مفاتيح أسماء التبويبات:** موجودة في نهاية القاموسين تحت قسم "أسماء تبويبات الـ Sections" — استخدمها في `_build_tabs()` بدل النصوص المباشرة.

**5. لا تمرر النص مباشرة لـ `tr()`:**
```python
# ❌ خطأ
lbl.setText(tr("حفظ"))

# ✅ صح
lbl.setText(tr("save"))
```