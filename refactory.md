# خطة إصلاح الألوان الـ Hardcoded + إزالة الـ Re-exports

## الهدف المزدوج

1. **كل لون** في التطبيق يجي من `ui/theme_manager.py` فقط — تغيير الثيم يغير كل شيء تلقائياً.
2. **لا re-exports** — كل `import` يكون من الملف الأصلي اللي فيه الكود فعلاً، مش من وسيط بيعيد التصدير.

---

## أولاً — إزالة الـ Re-exports الموجودة

### 1. `ui/widgets/combo/unit.py`

#### المشكلة
```python
# ❌ حالياً — re-exports من unit_service.py
from .unit_service import (  # noqa: F401
    _DEFAULT_UNITS, _cache_key, invalidate_units_cache,
    load_units, save_units, get_last_unit, set_last_unit,
    add_unit, remove_unit, get_all_units, reset_units_to_default,
)
```

#### الإصلاح
- احذف كل الـ re-exports من `unit.py`.
- كل ملف يستورد هذه الدوال يغير الـ import مباشرة:

```python
# ✅ بعد — في كل ملف يحتاجها
from ui.widgets.combo.unit_service import (
    load_units, add_unit, remove_unit, ...
)
```

#### الملفات المتأثرة التي تحتاج تحديث import
| الملف | الاستيراد الحالي | الاستيراد الجديد |
|-------|-----------------|-----------------|
| `ui/widgets/dialogs/settings_dialog.py` | `from ui.widgets.combo.unit import load_units, ...` | `from ui.widgets.combo.unit_service import load_units, ...` |
| أي ملف آخر يستورد من `combo/unit.py` | نفس التغيير | نفس التغيير |

---

### 2. `ui/widgets/components/label.py`

#### المشكلة
```python
# ❌ حالياً — re-exports من ملفات منفصلة
from .progress import ProgressBar, MultiProgressBar          # noqa: F401
from .amount_label import (                                  # noqa: F401
    AmountLabel, DebitCreditDisplay, BalanceDisplay,
    format_amount, amount_color, dr_cr_color,
)
```

#### الإصلاح
- احذف الـ re-exports من `label.py`.
- كل ملف يستورد من `label.py` يغير الـ import مباشرة:

```python
# ✅ بعد
from ui.widgets.components.progress     import ProgressBar, MultiProgressBar
from ui.widgets.components.amount_label import AmountLabel, format_amount, ...
```

#### الملفات المتأثرة
ابحث عن كل ملف يعمل:
```python
from ..components.label import ProgressBar        # → progress.py
from ..components.label import AmountLabel        # → amount_label.py
from ..components.label import format_amount      # → amount_label.py
from ..components.label import dr_cr_color        # → amount_label.py
```

---

### 3. `ui/widgets/components/headers_page.py`

#### المشكلة
```python
# ❌ في DetailHeader._ensure_toolbar()
from .action_toolbar import ActionToolbar  # داخل دالة — مقبول لكن يُنقل للأعلى
```

هذا مقبول لتفادي circular import — **يُترك كما هو** مع تعليق يوضح السبب.

---

### 4. فحص شامل للـ Re-exports المتبقية

قبل التنفيذ، نبحث في كل الملفات عن:
```python
# noqa: F401   ← علامة re-export
```
وعن:
```python
from .xyz import something  # في أول الملف بدون استخدام محلي
```

كل واحدة يُقرر: هل تُحذف أم لها مبرر (مثل circular import).

---

## ثانياً — إصلاح الألوان الـ Hardcoded

### الملف 1: `ui/theme_manager.py`

**العمل:** إضافة المفاتيح الجديدة فقط — لا تغيير للموجود.

#### إضافة في `_LIGHT_THEME`:
```python
# Waste (input نسبة الهادر)
"waste_zero_bg":         "#f5f5f5",
"waste_zero_border":     "#e0e0e0",
"waste_zero_color":      "#999999",
# waste_text_color → يُستخدم _C['orange'] الموجود فعلاً

# Input states
"input_error_bg":        "#fef2f2",
"input_error_border":    "#f87171",
"input_positive_bg":     "#f0fdf4",
"input_positive_border": "#86efac",
"input_positive_color":  "#15803d",
```

#### إضافة في `_DARK_THEME`:
```python
# Waste
"waste_zero_bg":         "#2a2a2a",
"waste_zero_border":     "#3a3a3a",
"waste_zero_color":      "#666666",

# Input states
"input_error_bg":        "#2a1010",
"input_error_border":    "#e57373",
"input_positive_bg":     "#0a2018",
"input_positive_border": "#66bb8a",
"input_positive_color":  "#66bb8a",
```

---

### الملف 2: `ui/widgets/core/colors.py`

#### التغيير أ — حذف الـ Fallback Constants
```python
# ❌ احذف هذه الثوابت كلها
_PURPLE_FALLBACK        = "#6a1b9a"
_PURPLE_BG_FALLBACK     = "#f3e5f5"
_PURPLE_BORDER_FALLBACK = "#ce93d8"
_ORANGE_FALLBACK        = "#e65100"
_ORANGE_BG_FALLBACK     = "#fff3e0"
_ORANGE_BORDER_FALLBACK = "#ffcc80"
```

```python
# ✅ في status_colors() — استخدم _C مباشرة مع fallback من نفس الـ dict
"purple": {
    "fg":     _C.get("purple",        _C["text_sec"]),
    "bg":     _C.get("purple_bg",     _C["bg_surface_2"]),
    "border": _C.get("purple_border", _C["border"]),
},
"orange": {
    "fg":     _C.get("orange",        _C["warning"]),
    "bg":     _C.get("orange_bg",     _C["warning_bg"]),
    "border": _C.get("orange_border", _C["warning_border"]),
},
```

#### التغيير ب — Waste Constants تصبح دوال
```python
# ❌ احذف
WASTE_ZERO_BG     = "#f5f5f5"
WASTE_ZERO_BORDER = "#e0e0e0"
WASTE_ZERO_COLOR  = "#999"
WASTE_TEXT_COLOR  = "#e65100"

# ✅ استبدل بدوال تقرأ من _C
def waste_zero_bg()     -> str: from ui.theme import _C; return _C["waste_zero_bg"]
def waste_zero_border() -> str: from ui.theme import _C; return _C["waste_zero_border"]
def waste_zero_color()  -> str: from ui.theme import _C; return _C["waste_zero_color"]
def waste_text_color()  -> str: from ui.theme import _C; return _C["orange"]
```

> **ملاحظة:** الملفات التي تستورد `WASTE_ZERO_BG` وغيره تحتاج تحديث
> لاستدعاء الدالة بدل الثابت. ابحث عن كل مكان يستورد هذه الأسماء.

#### التغيير ج — `card_colors()` تتحقق من الثيم
```python
# ✅ بعد
def card_colors(color: str) -> tuple[str, str]:
    from ui.theme_manager import theme_manager
    palette = _DARK_CARD_PALETTE if theme_manager.is_dark else CARD_PALETTE
    return palette.get(color, _FALLBACK)
```

#### التغيير د — إضافة `_DARK_CARD_PALETTE`
```python
_DARK_CARD_PALETTE: dict[str, tuple[str, str]] = {
    # أزرق
    "#1565c0": ("#1a2a3a", "#2a4a6a"),
    "#0d47a1": ("#152030", "#1e3a5f"),
    "#1d4ed8": ("#1a2540", "#2a4080"),
    "#1e40af": ("#1a2540", "#2a4080"),
    "#0891b2": ("#0a2830", "#1a5060"),
    "#0369a1": ("#0a2030", "#1a4060"),
    # أخضر
    "#10b981": ("#0a2820", "#1a5040"),
    "#2e7d32": ("#0a2010", "#1a4020"),
    "#065f46": ("#0a2818", "#1a5030"),
    "#15803d": ("#0a2018", "#1a4030"),
    "#16a34a": ("#0a2018", "#1a4030"),
    # أحمر
    "#ef4444": ("#2a1010", "#5a2020"),
    "#dc2626": ("#2a1010", "#5a2020"),
    "#c62828": ("#281010", "#4a1818"),
    "#991b1b": ("#2a1010", "#4a1818"),
    "#b91c1c": ("#2a1010", "#4a1818"),
    # برتقالي / أصفر
    "#f59e0b": ("#2a2000", "#4a3800"),
    "#e65100": ("#281400", "#503000"),
    "#b45309": ("#281c00", "#4a3400"),
    "#d97706": ("#281c00", "#4a3400"),
    "#ea580c": ("#281800", "#503800"),
    # رمادي
    "#6b7280": ("#1e2028", "#2e3040"),
    "#374151": ("#1a1c24", "#2a2e38"),
    "#9ca3af": ("#1e2028", "#2e3040"),
    "#555555": ("#1e1e1e", "#2e2e2e"),
    "#555":    ("#1e1e1e", "#2e2e2e"),
    "#4b5563": ("#1a1c24", "#2a2e38"),
    # بنفسجي / وردي
    "#8b5cf6": ("#1a1028", "#3a2060"),
    "#6d28d9": ("#180c28", "#301860"),
    "#6a1b9a": ("#1a0828", "#3a1060"),
    "#7c3aed": ("#1a0c2a", "#341860"),
    "#9333ea": ("#1c0a28", "#3c1860"),
    "#db2777": ("#280a18", "#501830"),
    "#be185d": ("#280a18", "#501830"),
    # بني
    "#4e342e": ("#201010", "#3a1c18"),
    "#5d4037": ("#221210", "#3c1e18"),
}
```

---

### الملف 3: `ui/widgets/theme/input_styles.py`

```python
# ❌ حالياً
def input_style(height=32, error=False):
    bg     = "#fef2f2" if error else _C["bg_input"]
    border = "#f87171" if error else _C["border_med"]

def spinbox_style(height=32, positive=False, widget="QDoubleSpinBox"):
    if positive:
        bg, border, color, weight = "#f0fdf4", "#86efac", "#15803d", "bold"

# ✅ بعد
def input_style(height=32, error=False):
    bg     = _C["input_error_bg"]     if error else _C["bg_input"]
    border = _C["input_error_border"] if error else _C["border_med"]

def spinbox_style(height=32, positive=False, widget="QDoubleSpinBox"):
    if positive:
        bg     = _C["input_positive_bg"]
        border = _C["input_positive_border"]
        color  = _C["input_positive_color"]
        weight = "bold"
```

---

### الملف 4: `ui/widgets/components/component_row/ui.py`

```python
# ❌ حالياً — في _variant_cost_style و_waste_zero_style
# نفس ألوان positive وwaste مكررة

# ✅ بعد — استخدام _C مباشرة بعد إضافة المفاتيح للثيم
def _waste_zero_style() -> str:
    base = get_font_size()
    return f"""
        QDoubleSpinBox {{
            background: {_C['waste_zero_bg']};
            border: 1px solid {_C['waste_zero_border']};
            border-radius: 4px; padding: 1px 4px;
            font-size: {fs(base, -1)}pt;
            color: {_C['waste_zero_color']};
        }}
        ...
    """
```

كذلك تحديث `update_waste_style()`:
```python
# ❌ يستورد حالياً
from ui.widgets.core.colors import (
    WASTE_TEXT_COLOR, WASTE_ZERO_BG, WASTE_ZERO_BORDER, WASTE_ZERO_COLOR, ...
)

# ✅ بعد — لا استيراد لثوابت الـ waste، تُقرأ من _C مباشرة
# أو استدعاء دوال waste_zero_bg() وغيرها لو بقيت دوال
```

---

### الملف 5: `ui/main_window_helper/_nav_button.py`

```python
# ❌ حالياً
self._badge_lbl.setStyleSheet(
    "QLabel{background:#C0392B;color:#FFF;font-size:8pt;font-weight:700;"
    "padding:1px 6px;border-radius:8px;border:none;}"
)

# ✅ بعد
from ui.theme import _C

self._badge_lbl.setStyleSheet(
    f"QLabel{{background:{_C['danger']};color:{_C['bg_input']};"
    f"font-size:8pt;font-weight:700;"
    "padding:1px 6px;border-radius:8px;border:none;}"
)
```

> **تنبيه:** `_badge_lbl` stylesheet يُحدَّث في `__init__` فقط، ومش بيتحدث عند تغيير الثيم.
> لو الـ dynamic theme switching مهم — يُضاف `_update_badge_style()` يُستدعى
> من `bus.theme_changed` أو من `refresh_sizes()`.

---

### الملف 6: `ui/widgets/theme/builders.py`

```python
# ❌ حالياً — fallback strings غير ضرورية
sep.setStyleSheet(f"background:{color or _C.get('border','#e0e0e0')}; border:none;")
sep.setStyleSheet(f"background:{color or _C.get('border_med','#bdbdbd')}; border:none;")

# ✅ بعد — _C دايماً يحتوي على هذه المفاتيح
sep.setStyleSheet(f"background:{color or _C['border']}; border:none;")
sep.setStyleSheet(f"background:{color or _C['border_med']}; border:none;")
```

---

## ترتيب التنفيذ

| الخطوة | الملف | العمل | أثر على الـ Re-exports |
|--------|-------|-------|------------------------|
| 1 | `ui/theme_manager.py` | إضافة 10 مفاتيح جديدة للـ light و dark | لا |
| 2 | `ui/widgets/core/colors.py` | حذف fallback constants، تحويل waste لدوال، إضافة `_DARK_CARD_PALETTE`، تحديث `card_colors()` | لا |
| 3 | `ui/widgets/theme/input_styles.py` | استبدال hardcoded بـ `_C` | لا |
| 4 | `ui/widgets/components/component_row/ui.py` | استبدال hardcoded بـ `_C` / دوال colors | لا |
| 5 | `ui/main_window_helper/_nav_button.py` | استبدال badge colors بـ `_C` | لا |
| 6 | `ui/widgets/theme/builders.py` | حذف fallback strings من `_C.get()` | لا |
| 7 | `ui/widgets/combo/unit.py` | حذف كل الـ re-exports | نعم |
| 8 | `ui/widgets/dialogs/settings_dialog.py` | تحديث import لـ `unit_service` مباشرة | نعم |
| 9 | `ui/widgets/components/label.py` | حذف re-exports لـ `progress` و `amount_label` | نعم |
| 10 | كل الملفات التي تستورد من `label.py` | تحديث import للمصدر المباشر | نعم |
| 11 | فحص شامل | بحث عن كل `# noqa: F401` متبقي وقرار لكل واحدة | نعم |

---

## قاعدة الـ Import بعد التنفيذ

```
# ✅ صح دايماً — import من المصدر الأصلي
from ui.widgets.combo.unit_service   import load_units
from ui.widgets.components.progress  import ProgressBar
from ui.widgets.components.amount_label import AmountLabel

# ❌ غلط — import من وسيط بيعيد التصدير
from ui.widgets.combo.unit           import load_units      # unit.py مش المصدر
from ui.widgets.components.label     import ProgressBar     # label.py مش المصدر
```

---

## النتيجة النهائية

```
مصدر الألوان الوحيد:    ui/theme_manager.py
                                ↓
الألوان النشطة:          ui/theme.py (_C dict)
                                ↓
كل الملفات الأخرى:      تقرأ من _C مباشرة — لا hardcoded، لا re-exports
```

**لو غيّرت الثيم لـ dark:**
- `input_error_bg` → `#2a1010` بدل `#fef2f2`
- `waste_zero_bg`  → `#2a2a2a` بدل `#f5f5f5`
- `card_colors()`  → ترجع dark palette
- badge color      → `_C['danger']` النسخة الداكنة
- كل شيء يتغير تلقائياً ✅

**لو حد حاول import من ملف re-export:**
- الملف مش موجود فيه الدالة → ImportError فوري → يُصلح المكان الصح
- مش هيعدي بصامت ✅

---

## ملفات نظيفة — لا تحتاج تغيير

| الملف | السبب |
|-------|-------|
| `ui/theme_manager.py` | المصدر — بنضيف إليه فقط |
| `ui/theme.py` | ✅ نظيف |
| `ui/font.py` | لا ألوان |
| `ui/events.py` | لا ألوان |
| `ui/constants.py` | لا ألوان |
| `ui/widgets/theme/table_styles.py` | كلها من `_C` |
| `ui/widgets/theme/card_styles.py` | كلها من `_C` |
| `ui/widgets/theme/label_styles.py` | كلها من `_C` |
| `ui/widgets/theme/layout_styles.py` | كلها من `_C` |
| `ui/widgets/panels/state.py` | كلها من `_C` |
| `ui/widgets/components/notification.py` | كلها من `status_colors()` |
| `ui/widgets/components/badge.py` | كلها من `_C` |
| `ui/widgets/combo/unit_service.py` | المصدر الأصلي — لا re-exports |
| `ui/widgets/components/progress.py` | المصدر الأصلي — لا re-exports |
| `ui/widgets/components/amount_label.py` | المصدر الأصلي — لا re-exports |