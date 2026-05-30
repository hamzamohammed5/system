# دليل الكود — نظام الترجمة (i18n)

> مرجع كامل لنظام الترجمة: الملفات، المفاتيح، وكيفية الاستخدام.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [المكونات الرئيسية](#المكونات-الرئيسية) | `ui/widgets/core/i18n.py`, `ui/i18n/ar.py`, `ui/i18n/en.py` |
| [الاستخدام السريع](#الاستخدام-السريع) | أمثلة عملية |
| [إضافة مفاتيح جديدة](#إضافة-مفاتيح-جديدة) | تعليمات التوسعة |

---

## المكونات الرئيسية

### `ui/widgets/core/i18n.py` — `I18nManager` + `tr()`

المصدر الوحيد لنظام الترجمة. يحتوي على `I18nManager` + `tr()`.
يُحمِّل الترجمات تلقائياً من `ui/i18n/ar.py` و`ui/i18n/en.py` عند الاستيراد.

```python
from ui.widgets.core.i18n import tr, i18n_manager

i18n_manager.language -> str          # "ar" | "en"
i18n_manager.is_rtl -> bool
i18n_manager.qt_direction -> Qt.LayoutDirection
i18n_manager.set_language(lang, save=True)
i18n_manager.translate(key, lang=None, **kwargs) -> str
i18n_manager.load_from_db()
i18n_manager.get_available_languages() -> list[{code, name, active, is_rtl}]
i18n_manager.add_translations(lang_code, translations: dict)

def tr(key: str, lang=None, **kwargs) -> str
# مثال: tr("save")                           → "حفظ" | "Save"
# مثال: tr("delete_confirm_msg", name="X")   → "هل تريد حذف «X»؟" | "Delete «X»?"
# مثال: tr("showing_of", shown=5, total=100) → "5 / 100"
```

> **ملاحظة:** `tr()` تقبل مفاتيح فقط (مثل `"save"`، `"delete"`).
> لا تمرر نصاً عربياً مباشرة — استخدم المفتاح المقابل دائماً.

---

### `ui/i18n/ar.py` — `AR_STRINGS`

القاموس العربي الكامل. اللغة الأم للتطبيق.

```python
from ui.i18n.ar import AR_STRINGS
```

---

### `ui/i18n/en.py` — `EN_STRINGS`

القاموس الإنجليزي الكامل. يجب أن يحتوي على **نفس** مفاتيح `AR_STRINGS` تماماً.

```python
from ui.i18n.en import EN_STRINGS
```

---

## الاستخدام السريع

```python
from ui.widgets.core.i18n import tr

# نص بسيط
btn.setText(tr("save"))              # "Save" | "حفظ"
lbl.setText(tr("name"))              # "Name" | "الاسم"

# نص مع format
msg = tr("delete_confirm_msg", name=item_name)
# EN: "Delete «المنتج»?"
# AR: "هل تريد حذف «المنتج»؟"

# رسائل التحقق
msg = tr("enter_field", label=tr("name"))
# EN: "Enter Name"
# AR: "أدخل الاسم"

# في الـ dialogs
confirm_delete(self, tr("name"))
```

---

## إضافة مفاتيح جديدة

كل مفتاح جديد يُضاف في **مكانين فقط**:

1. **`ui/i18n/ar.py`** — القيمة العربية
2. **`ui/i18n/en.py`** — القيمة الإنجليزية

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

**1. تطابق المفاتيح:** `AR_STRINGS` و`EN_STRINGS` يجب أن يحتويا على **نفس المفاتيح** — أي مفتاح ناقص في `en.py` سيُرجع النص العربي كـ fallback صامت.

**2. مفاتيح مكررة:** Python تحتفظ بآخر قيمة — كل مفتاح يجب أن يظهر **مرة واحدة فقط** في كل ملف.

**3. `notice` vs `info`:** مفتاحان منفصلان — `notice` = "ملاحظة"، `info` = "معلومة".