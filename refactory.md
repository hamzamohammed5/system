# خطة إصلاح الألوان الـ Hardcoded — المصدر الوحيد

## الهدف
كل لون في التطبيق يجي من `ui/theme_manager.py` فقط.
لو غيّرت الثيم من light لـ dark — كل الألوان تتغير تلقائياً.

---

## الوضع الحالي

### 🔴 ملفات تحتاج إصلاح (4 ملفات)

---

### 1. `ui/widgets/core/colors.py`

#### المشكلة أ — Fallbacks مكررة من الثيم
```python
# ❌ حالياً — مكرر من theme_manager.py
_PURPLE_FALLBACK        = "#6a1b9a"   # = _C['purple']
_PURPLE_BG_FALLBACK     = "#f3e5f5"   # = _C['purple_bg']
_PURPLE_BORDER_FALLBACK = "#ce93d8"   # = _C['purple_border']
_ORANGE_FALLBACK        = "#e65100"   # = _C['orange']
_ORANGE_BG_FALLBACK     = "#fff3e0"   # = _C['orange_bg']
_ORANGE_BORDER_FALLBACK = "#ffcc80"   # = _C['orange_border']
```

**الإصلاح:** احذفها — `status_colors()` تستخدم `_C.get("purple", _C["text_sec"])` مباشرة.

---

#### المشكلة ب — Waste colors hardcoded
```python
# ❌ حالياً
WASTE_ZERO_BG     = "#f5f5f5"
WASTE_ZERO_BORDER = "#e0e0e0"
WASTE_ZERO_COLOR  = "#999"
WASTE_TEXT_COLOR  = "#e65100"   # = _C['orange']
```

**الإصلاح:** تُضاف لـ `theme_manager.py` كمفاتيح جديدة:
```python
# في _LIGHT_THEME و _DARK_THEME
"waste_zero_bg":     "#f5f5f5",   # dark: "#2a2a2a"
"waste_zero_border": "#e0e0e0",   # dark: "#3a3a3a"
"waste_zero_color":  "#999999",   # dark: "#666666"
# waste_text_color يُستبدل بـ _C['orange'] الموجود
```

---

#### المشكلة ج — `CARD_PALETTE` (30+ hardcoded hex pairs)
```python
CARD_PALETTE: dict[str, tuple[str, str]] = {
    "#1565c0": ("#e8f0fe", "#90caf9"),
    "#0d47a1": ("#e3f2fd", "#64b5f6"),
    # ... 30+ entries
}
```

**القرار:** يبقى في `colors.py` — لكن يُضاف `_DARK_CARD_PALETTE` بديل للـ dark theme.

**الإصلاح:** `card_colors()` تتحقق من الثيم الحالي:
```python
def card_colors(color: str) -> tuple[str, str]:
    from ui.theme_manager import theme_manager
    palette = _DARK_CARD_PALETTE if theme_manager.is_dark else CARD_PALETTE
    return palette.get(color, _FALLBACK)
```

---

### 2. `ui/widgets/theme/input_styles.py`

#### المشكلة — ألوان error و positive hardcoded
```python
# ❌ حالياً
def input_style(error=False):
    bg     = "#fef2f2" if error else _C["bg_input"]   # hardcoded
    border = "#f87171" if error else _C["border_med"] # hardcoded

def spinbox_style(positive=False):
    if positive:
        bg, border, color = "#f0fdf4", "#86efac", "#15803d"  # hardcoded
```

**الإصلاح:** تُضاف لـ `theme_manager.py` كمفاتيح جديدة:
```python
# في _LIGHT_THEME
"input_error_bg":      "#fef2f2",   # dark: "#2a1010"
"input_error_border":  "#f87171",   # dark: "#e57373"
"input_positive_bg":   "#f0fdf4",   # dark: "#0a2018"
"input_positive_border":"#86efac",  # dark: "#66bb8a"
"input_positive_color": "#15803d",  # dark: "#66bb8a"
```

ثم `input_styles.py` تستخدم `_C` مباشرة:
```python
bg     = _C["input_error_bg"]     if error    else _C["bg_input"]
border = _C["input_error_border"]  if error    else _C["border_med"]

if positive:
    bg, border, color = _C["input_positive_bg"], _C["input_positive_border"], _C["input_positive_color"]
```

---

### 3. `ui/widgets/components/component_row/ui.py`

#### المشكلة — نفس ألوان positive مكررة
```python
# ❌ في _variant_cost_style و spinbox داخل الـ widget
"#f0fdf4", "#86efac", "#15803d"
```

**الإصلاح:** بعد إضافة المفاتيح للثيم، يستخدم `_C` مباشرة — نفس إصلاح `input_styles.py`.

---

### 4. `ui/main_window_helper/_nav_button.py`

#### المشكلة — badge color hardcoded في QSS string
```python
# ❌ حالياً
self._badge_lbl.setStyleSheet(
    "QLabel{background:#C0392B;color:#FFF;...}"   # hardcoded
)
```

**الإصلاح:**
```python
# ✅ بعد
from ui.theme import _C
self._badge_lbl.setStyleSheet(
    f"QLabel{{background:{_C['danger']};color:{_C['bg_input']};...}}"
)
```

---

### 🟡 إصلاح طفيف

### 5. `ui/widgets/theme/builders.py`

```python
# حالياً — fallback في get() مقبول لكن أفضل يكون من _C
sep.setStyleSheet(f"background:{color or _C.get('border','#e0e0e0')}; ...")
```

**الإصلاح:** `_C['border']` بدل `_C.get('border','#e0e0e0')` — الـ key دايماً موجود في الثيم.

---

## المفاتيح الجديدة تُضاف لـ `theme_manager.py`

### في `_LIGHT_THEME`:
```python
# Waste colors
"waste_zero_bg":        "#f5f5f5",
"waste_zero_border":    "#e0e0e0",
"waste_zero_color":     "#999999",

# Input states
"input_error_bg":       "#fef2f2",
"input_error_border":   "#f87171",
"input_positive_bg":    "#f0fdf4",
"input_positive_border":"#86efac",
"input_positive_color": "#15803d",
```

### في `_DARK_THEME`:
```python
# Waste colors
"waste_zero_bg":        "#2a2a2a",
"waste_zero_border":    "#3a3a3a",
"waste_zero_color":     "#666666",

# Input states
"input_error_bg":       "#2a1010",
"input_error_border":   "#e57373",
"input_positive_bg":    "#0a2018",
"input_positive_border":"#66bb8a",
"input_positive_color": "#66bb8a",
```

---

## `CARD_PALETTE` — قرار منفصل

`CARD_PALETTE` ليس UI theme — هو palette لتعيين خلفية وحدود الكروت الملونة
بناءً على لون accent العنصر (مثلاً لون التصنيف).

### الحل المقترح — `_DARK_CARD_PALETTE` في نفس الملف:
```python
# في colors.py — palette مستقل للـ dark theme
_DARK_CARD_PALETTE: dict[str, tuple[str, str]] = {
    "#1565c0": ("#1a2a3a", "#2a4a6a"),
    "#0d47a1": ("#152030", "#1e3a5f"),
    # ... نفس الألوان بـ dark variants
}

def card_colors(color: str) -> tuple[str, str]:
    from ui.theme_manager import theme_manager
    palette = _DARK_CARD_PALETTE if theme_manager.is_dark else CARD_PALETTE
    return palette.get(color, _FALLBACK)
```

---

## ترتيب التنفيذ

| الخطوة | الملف | العمل |
|--------|-------|-------|
| 1 | `ui/theme_manager.py` | إضافة المفاتيح الجديدة لـ light و dark |
| 2 | `ui/widgets/core/colors.py` | حذف الـ fallbacks + waste vars + تحديث `status_colors()` + إضافة `_DARK_CARD_PALETTE` |
| 3 | `ui/widgets/theme/input_styles.py` | استبدال hardcoded بـ `_C` |
| 4 | `ui/widgets/components/component_row/ui.py` | استبدال hardcoded بـ `_C` |
| 5 | `ui/main_window_helper/_nav_button.py` | استبدال hardcoded badge colors بـ `_C` |
| 6 | `ui/widgets/theme/builders.py` | حذف fallback strings من `get()` |

---

## النتيجة النهائية

```
مصدر الألوان الوحيد:  ui/theme_manager.py
                              ↓
الألوان النشطة:        ui/theme.py (_C dict)
                              ↓
كل الملفات الأخرى:    تقرأ من _C فقط — لا hardcoded
```

لو غيّرت الثيم لـ dark:
- `_C` يُحدَّث بـ `_DARK_THEME`
- `input_error_bg` يصبح `#2a1010` بدل `#fef2f2`
- `waste_zero_bg` يصبح `#2a2a2a` بدل `#f5f5f5`
- `card_colors()` ترجع dark palette
- كل شيء يتغير تلقائياً ✅

---

## ملفات نظيفة — لا تحتاج تغيير

| الملف | السبب |
|-------|-------|
| `ui/theme_manager.py` | المصدر — بنضيف إليه فقط |
| `ui/theme.py` | ✅ تم إصلاحه |
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