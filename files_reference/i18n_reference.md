# دليل الكود — نظام الترجمة (i18n)

> مرجع كامل لنظام الترجمة: الملفات، المفاتيح، وكيفية الاستخدام.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [المكونات الرئيسية](#المكونات-الرئيسية) | `ui/i18n.py`, `ui/i18n/ar.py`, `ui/i18n/en.py`, `ui/widgets/core/i18n.py` |
| [الاستخدام السريع](#الاستخدام-السريع) | أمثلة عملية |
| [فهرس المفاتيح](#فهرس-المفاتيح) | جميع المفاتيح المتاحة مقسمة حسب القسم |
| [إضافة مفاتيح جديدة](#إضافة-مفاتيح-جديدة) | تعليمات التوسعة |

---

## المكونات الرئيسية

### `ui/i18n.py` — `I18nManager` + `tr()`

```python
i18n_manager = I18nManager()   # Singleton

i18n_manager.language -> str          # "ar" | "en"
i18n_manager.is_rtl -> bool
i18n_manager.qt_direction -> Qt.LayoutDirection
i18n_manager.set_language(lang, save=True)
i18n_manager.translate(key, lang=None, **kwargs) -> str
i18n_manager.load_from_db()
i18n_manager.get_available_languages() -> list[{code, name, active, is_rtl}]
i18n_manager.add_translations(lang_code, translations: dict)

def tr(key: str, lang=None, **kwargs) -> str
# الدالة السريعة للترجمة
# مثال: tr("save")                           → "حفظ" | "Save"
# مثال: tr("delete_confirm_msg", name="X")   → "هل تريد حذف «X»؟"
# مثال: tr("showing_of", shown=5, total=100) → "5 / 100"
```

**آلية التحميل:**
يقرأ `_load_external_translations()` تلقائياً من `ui/i18n/ar.py` و `ui/i18n/en.py` عند استيراد الملف.
الملفات الخارجية لها **الأولوية** على القاموس الداخلي `_TRANSLATIONS`.

---

### `ui/i18n/ar.py` — `AR_STRINGS`

القاموس العربي الكامل (281 مفتاح). اللغة الأم للتطبيق.

```python
from ui.i18n.ar import AR_STRINGS
```

---

### `ui/i18n/en.py` — `EN_STRINGS`

القاموس الإنجليزي الكامل (281 مفتاح). يجب أن يحتوي على **نفس** مفاتيح `AR_STRINGS` تماماً.

```python
from ui.i18n.en import EN_STRINGS
```

---

### `ui/widgets/core/i18n.py` — `tr()` للـ widgets

دالة `tr()` موحدة تقبل نوعين من المدخلات:

```python
from ui.widgets.core.i18n import tr

tr("save")                         # key مباشر
tr("حفظ")                          # نص عربي → يُحوَّل تلقائياً لـ key عبر _AR_TO_KEY
tr("delete_confirm_msg", name="X") # key مع format
tr("أدخل {label}", label="الاسم")  # نص عربي مع format (عبر _FORMAT_KEYS)
```

**الفرق عن `ui/i18n.tr`:** تدعم تحويل النصوص العربية المباشرة إلى مفاتيح — مفيدة للتوافق مع الكود القديم.

---

## الاستخدام السريع

```python
# الاستيراد الموصى به في الـ widgets
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
from ui.i18n import tr
confirm_delete(self, tr("name"))
```

---

##  المفاتيح
تقدر تعرفها او تضيف عليها من ملفات ui/i18n/
---

## إضافة مفاتيح جديدة

**القاعدة:** كل مفتاح جديد يجب إضافته في **ثلاثة أماكن**:

1. **`ui/i18n/ar.py`** — القيمة العربية
2. **`ui/i18n/en.py`** — القيمة الإنجليزية
3. **`ui/i18n.py`** قسم `"ar"` في `_TRANSLATIONS` — كـ fallback (اختياري لكن موصى به)

```python
# مثال: إضافة مفتاح "invoice"

# في ar.py:
"invoice": "فاتورة",

# في en.py:
"invoice": "Invoice",

# لو النص عربي يُستخدم مباشرة في كود قديم، أضفه في ui/widgets/core/i18n.py:
_AR_TO_KEY["فاتورة"] = "invoice"
```

**قاعدة المفاتيح ذات الـ format:**
```python
# المفتاح يحتوي على {placeholder}
"invoice_total": "إجمالي الفاتورة: {amount} {currency}",

# الاستخدام:
tr("invoice_total", amount="500.00", currency=tr("currency_abbr"))
```

---

## ملاحظات مهمة

**1. تطابق المفاتيح:** `AR_STRINGS` و`EN_STRINGS` يجب أن يحتويا على **نفس المفاتيح** تماماً — أي اختلاف يُسبب `KeyError` صامتاً عند التبديل للإنجليزية.

**2. أولوية التحميل:** `ui/i18n/ar.py` و`ui/i18n/en.py` لهما أولوية على `_TRANSLATIONS` الداخلي في `ui/i18n.py` — عند التعارض يُطبَّق الملف الخارجي.

**3. مفاتيح مكررة في نفس الملف:** Python تحتفظ بآخر قيمة فقط — المفاتيح المكررة تُسبب سلوكاً غير متوقع. كل مفتاح يجب أن يظهر **مرة واحدة فقط** في كل ملف.

**4. `_AR_TO_KEY` في `ui/widgets/core/i18n.py`:** يُستخدم للتوافق مع الكود القديم الذي يمرر نصاً عربياً بدلاً من مفتاح. لا تضف إليه مفاتيح جديدة — الكود الجديد يستخدم المفاتيح مباشرة.

**5. `notice` vs `info`:** مفتاحان منفصلان — `notice` = "ملاحظة" (للرسائل الإعلامية الاختيارية)، `info` = "معلومة" (لمستوى الـ notification).