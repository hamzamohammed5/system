# خطة إصلاح الألوان الـ Hardcoded + إزالة الـ Re-exports بالكامل

## الهدف المزدوج

1. **كل لون** في التطبيق يجي من `ui/theme_manager.py` فقط — تغيير الثيم يغير كل شيء تلقائياً.
2. **صفر re-exports** — كل `import` يكون من الملف الأصلي اللي فيه الكود فعلاً، مش من وسيط بيعيد التصدير. أي ملف يعيد تصدير حاجة يتحذف منه الـ re-export تماماً.

---

## القاعدة الثابتة: Import من المصدر مباشرة

```python
# ✅ صح دايماً
from ui.widgets.combo.unit_service      import load_units, add_unit
from ui.widgets.components.progress     import ProgressBar, MultiProgressBar
from ui.widgets.components.amount_label import AmountLabel, format_amount, dr_cr_color

# ❌ غلط — import من وسيط
from ui.widgets.combo.unit           import load_units       # unit.py مش المصدر
from ui.widgets.components.label     import ProgressBar      # label.py مش المصدر
from ui.widgets.components.label     import AmountLabel      # label.py مش المصدر
```

---

## أولاً — جرد كل الـ Re-exports الموجودة وخطة إزالتها

### 1. `ui/widgets/combo/unit.py`

#### المشكلة الحالية
```python
# ❌ re-exports موجودة حالياً
from .unit_service import (  # noqa: F401
    _DEFAULT_UNITS, _cache_key, invalidate_units_cache,
    load_units, save_units, get_last_unit, set_last_unit,
    add_unit, remove_unit, get_all_units, reset_units_to_default,
)
```

#### الإصلاح
احذف **كل** هذه الـ re-exports من `unit.py`. الملف يبقى مسؤول عن `UnitCombo` و`make_unit_combo` فقط.

#### الملفات المتأثرة — تحديث الـ imports
| الملف | قبل | بعد |
|-------|-----|-----|
| `ui/widgets/dialogs/settings_dialog.py` | `from ui.widgets.combo.unit import load_units, add_unit, remove_unit, reset_units_to_default, _DEFAULT_UNITS` | `from ui.widgets.combo.unit_service import load_units, add_unit, remove_unit, reset_units_to_default, _DEFAULT_UNITS` |
| أي ملف آخر يستورد الدوال من `combo/unit.py` | نفس النمط | يستورد من `unit_service` مباشرة |

> **ملاحظة:** `UnitCombo` و`make_unit_combo` يبقوا في `unit.py` — ده مش re-export، ده الكود الأصلي.

---

### 2. `ui/widgets/components/label.py`

#### المشكلة الحالية
```python
# ❌ re-exports موجودة حالياً
from .progress import ProgressBar, MultiProgressBar          # noqa: F401
from .amount_label import (                                  # noqa: F401
    AmountLabel, DebitCreditDisplay, BalanceDisplay,
    format_amount, amount_color, dr_cr_color,
)
```

#### الإصلاح
احذف **كل** هذه الـ re-exports من `label.py`. الملف يبقى مسؤول عن `InfoRow` و`ModeLabel` فقط.

#### الملفات المتأثرة — تحديث الـ imports
ابحث في المشروع عن كل ملف يعمل:
```python
from ..components.label import ProgressBar        # → from ..components.progress import ProgressBar
from ..components.label import MultiProgressBar   # → from ..components.progress import MultiProgressBar
from ..components.label import AmountLabel        # → from ..components.amount_label import AmountLabel
from ..components.label import DebitCreditDisplay # → from ..components.amount_label import DebitCreditDisplay
from ..components.label import BalanceDisplay     # → from ..components.amount_label import BalanceDisplay
from ..components.label import format_amount      # → from ..components.amount_label import format_amount
from ..components.label import amount_color       # → from ..components.amount_label import amount_color
from ..components.label import dr_cr_color        # → from ..components.amount_label import dr_cr_color
```

---

### 3. فحص شامل لأي re-exports متبقية

بعد تنفيذ الخطوتين السابقتين، ابحث في كل الملفات عن:
```python
# noqa: F401
```
كل نتيجة يُقرر لها: هل هي re-export تُحذف؟ أم لها مبرر تقني مثل circular import — وفي هذه الحالة يُضاف تعليق يوضح السبب صراحةً.

---

## ثانياً — إصلاح الألوان الـ Hardcoded

### الملف 1: `ui/theme_manager.py`

**العمل:** إضافة 10 مفاتيح جديدة فقط — لا تغيير لأي شيء موجود.

#### إضافة في `_LIGHT_THEME`:
```python
# ── Waste (نسبة الهادر) ──────────────────────────────
"waste_zero_bg":         "#f5f5f5",
"waste_zero_border":     "#e0e0e0",
"waste_zero_color":      "#999999",
# waste_text_color → يُستخدم _C['orange'] الموجود فعلاً

# ── Input states ─────────────────────────────────────
"input_error_bg":        "#fef2f2",
"input_error_border":    "#f87171",
"input_positive_bg":     "#f0fdf4",
"input_positive_border": "#86efac",
"input_positive_color":  "#15803d",
```

#### إضافة في `_DARK_THEME`:
```python
# ── Waste (نسبة الهادر) ──────────────────────────────
"waste_zero_bg":         "#2a2a2a",
"waste_zero_border":     "#3a3a3a",
"waste_zero_color":      "#666666",

# ── Input states ─────────────────────────────────────
"input_error_bg":        "#2a1010",
"input_error_border":    "#e57373",
"input_positive_bg":     "#0a2018",
"input_positive_border": "#66bb8a",
"input_positive_color":  "#66bb8a",
```

---

### الملف 2: `ui/widgets/core/colors.py`

#### التغيير أ — حذف الـ Fallback Constants الـ Hardcoded
```python
# ❌ احذف هذه الثوابت كلها إن وُجدت
_PURPLE_FALLBACK        = "#6a1b9a"
_PURPLE_BG_FALLBACK     = "#f3e5f5"
_PURPLE_BORDER_FALLBACK = "#ce93d8"
_ORANGE_FALLBACK        = "#e65100"
_ORANGE_BG_FALLBACK     = "#fff3e0"
_ORANGE_BORDER_FALLBACK = "#ffcc80"
```

وفي `status_colors()` استخدم `_C` مباشرة مع fallback من نفس الـ dict:
```python
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

#### التغيير ب — Waste Constants تصبح دوال (بدل ثوابت تتجمد عند import)
```python
# ❌ احذف
WASTE_ZERO_BG     = "#f5f5f5"
WASTE_ZERO_BORDER = "#e0e0e0"
WASTE_ZERO_COLOR  = "#999"
WASTE_TEXT_COLOR  = "#e65100"

# ✅ استبدل بدوال — تقرأ من _C الحالي في كل استدعاء
def waste_zero_bg()     -> str: from ui.theme import _C; return _C["waste_zero_bg"]
def waste_zero_border() -> str: from ui.theme import _C; return _C["waste_zero_border"]
def waste_zero_color()  -> str: from ui.theme import _C; return _C["waste_zero_color"]
def waste_text_color()  -> str: from ui.theme import _C; return _C["orange"]
```

> **الملفات المتأثرة:** كل ملف يستورد `WASTE_ZERO_BG` أو أي ثابت waste آخر يحتاج تحديث
> لاستدعاء الدالة بدل الثابت. ابحث عن كل مكان يستورد هذه الأسماء وحدّثه.

#### التغيير ج — `card_colors()` تتحقق من الثيم الحالي تلقائياً
```python
_FALLBACK_DARK: tuple[str, str] = ("#2a2a2a", "#3a3a3a")

def card_colors(color: str) -> tuple[str, str]:
    from ui.theme_manager import theme_manager
    if theme_manager.is_dark:
        return _DARK_CARD_PALETTE.get(color, _FALLBACK_DARK)
    return CARD_PALETTE.get(color, _FALLBACK)
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
# ❌ حالياً — hardcoded
def input_style(height=32, error=False):
    bg     = "#fef2f2" if error else _C["bg_input"]
    border = "#f87171" if error else _C["border_med"]

def spinbox_style(height=32, positive=False, widget="QDoubleSpinBox"):
    if positive:
        bg, border, color, weight = "#f0fdf4", "#86efac", "#15803d", "bold"

# ✅ بعد — من _C
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

#### أ — `_waste_zero_style()` تستخدم دوال `waste_zero_*()` بدل ثوابت hardcoded
```python
# ❌ حالياً — ثوابت hardcoded أو مستوردة كثوابت
# ✅ بعد — استدعاء دوال من colors.py
from ui.widgets.core.colors import (
    waste_colors, waste_level,
    waste_zero_bg, waste_zero_border, waste_zero_color, waste_text_color,
    status_colors as _status_colors, card_colors as _card_colors,
)

def _waste_zero_style() -> str:
    base = get_font_size()
    return f"""
        QDoubleSpinBox {{
            background: {waste_zero_bg()};
            border: 1px solid {waste_zero_border()};
            border-radius: 4px; padding: 1px 4px;
            font-size: {fs(base, -1)}pt;
            color: {waste_zero_color()};
        }}
        QDoubleSpinBox:focus {{
            border-color: {_C['border_focus']}; background: {_C['bg_surface_2']};
            color: {waste_text_color()};
        }}
    """
```

#### ب — `_variant_cost_style()` و`_variant_combo_style()` تستخدمان `_C`
```python
# ✅ بعد — _C["input_positive_*"] بدل hardcoded green
def _variant_combo_style() -> str:
    base = get_font_size()
    return f"""
        QComboBox {{
            background: {_C['input_positive_bg']};
            border: 1px solid {_C['input_positive_border']};
            border-radius: 4px; padding: 1px 6px;
            font-size: {fs(base, -1)}pt;
            color: {_C['input_positive_color']};
        }}
        QComboBox:focus {{ border-color: {_C['input_positive_color']}; }}
        QComboBox::drop-down {{ border: none; }}
    """

def _variant_cost_style() -> str:
    base = get_font_size()
    fg   = _C["input_positive_color"]
    bg, border = _card_colors(fg)
    return (
        f"font-size:{fs(base, -1)}pt; color:{fg}; font-weight:bold;"
        f"background:{bg}; border:1px solid {border};"
        "border-radius:3px; padding:1px 5px;"
    )
```

#### ج — `update_waste_style()` تستدعي الدوال بدل الثوابت
```python
def update_waste_style(widget, val: float):
    base = get_font_size()
    if val > 0:
        widget.lbl_waste.setVisible(True)
        bg, border = waste_colors(val)
        widget.waste_spin.setStyleSheet(f"""
            QDoubleSpinBox {{
                background: {bg}; border: 1px solid {border};
                border-radius: 4px; padding: 1px 4px;
                font-size: {fs(base, -1)}pt;
                color: {waste_text_color()}; font-weight: bold;
            }}
            QDoubleSpinBox:focus {{ border-color: {_C['warning']}; }}
        """)
    else:
        widget.lbl_waste.setVisible(False)
        widget.waste_spin.setStyleSheet(_waste_zero_style())
```

---

### الملف 5: `ui/main_window_helper/_nav_button.py`

#### أ — Badge colors من `_C` بدل hardcoded
```python
# ❌ حالياً
self._badge_lbl.setStyleSheet(
    "QLabel{background:#C0392B;color:#FFF;font-size:8pt;font-weight:700;"
    "padding:1px 6px;border-radius:8px;border:none;}"
)

# ✅ بعد
def _apply_badge_style(self):
    self._badge_lbl.setStyleSheet(
        f"QLabel{{background:{_C['danger']};color:{_C['bg_input']};"
        "font-size:8pt;font-weight:700;"
        "padding:1px 6px;border-radius:8px;border:none;}"
    )
```

#### ب — استدعاء `_apply_badge_style()` في كل مكان يُضبط فيه الـ badge
استدعها من:
- `_build_content()` عند الإنشاء الأول
- `refresh_sizes()` عند تغيير حجم الخط أو الثيم

هذا يضمن تحديث الألوان تلقائياً عند تبديل الثيم بدون الحاجة لـ `bus.theme_changed` منفصل.

---

### الملف 6: `ui/widgets/theme/builders.py`

```python
# ❌ حالياً — fallback strings غير ضرورية داخل _C.get()
sep.setStyleSheet(f"background:{color or _C.get('border','#e0e0e0')}; border:none;")
sep.setStyleSheet(f"background:{color or _C.get('border_med','#bdbdbd')}; border:none;")

# ✅ بعد — _C دايماً يحتوي على هذه المفاتيح (مضمونة من theme_manager)
sep.setStyleSheet(f"background:{color or _C['border']}; border:none;")
sep.setStyleSheet(f"background:{color or _C['border_med']}; border:none;")
```

---

## ترتيب التنفيذ

| # | الملف | العمل | نوع التغيير |
|---|-------|-------|-------------|
| 1 | `ui/theme_manager.py` | إضافة 10 مفاتيح جديدة للـ light و dark | إضافة ألوان |
| 2 | `ui/widgets/core/colors.py` | حذف fallback constants، تحويل waste لدوال، إضافة `_DARK_CARD_PALETTE`، تحديث `card_colors()` | إصلاح ألوان |
| 3 | `ui/widgets/theme/input_styles.py` | استبدال hardcoded بـ `_C` | إصلاح ألوان |
| 4 | `ui/widgets/components/component_row/ui.py` | استبدال hardcoded بـ `_C` / دوال colors | إصلاح ألوان |
| 5 | `ui/main_window_helper/_nav_button.py` | استبدال badge colors بـ `_C`، إضافة `_apply_badge_style()` | إصلاح ألوان |
| 6 | `ui/widgets/theme/builders.py` | حذف fallback strings من `_C.get()` | إصلاح ألوان |
| 7 | `ui/widgets/combo/unit.py` | **حذف كل الـ re-exports** — الملف يبقى لـ `UnitCombo` فقط | إزالة re-export |
| 8 | `ui/widgets/dialogs/settings_dialog.py` | تحديث import لـ `unit_service` مباشرة | تحديث import |
| 9 | كل ملف يستورد من `combo/unit.py` (دوال) | يستورد من `unit_service` مباشرة | تحديث import |
| 10 | `ui/widgets/components/label.py` | **حذف كل الـ re-exports** — الملف يبقى لـ `InfoRow` و`ModeLabel` فقط | إزالة re-export |
| 11 | كل ملف يستورد `ProgressBar` أو `AmountLabel` من `label.py` | يستورد من `progress.py` أو `amount_label.py` مباشرة | تحديث import |
| 12 | فحص شامل للمشروع | بحث عن كل `# noqa: F401` — كل واحدة إما تُحذف أو تُعلَّق بمبرر صريح | تنظيف نهائي |

---

## جدول مصادر الـ Import — المرجع النهائي

| ما تريد استيراده | المصدر الصحيح |
|-----------------|---------------|
| `load_units`, `add_unit`, `remove_unit`, `save_units`, `get_last_unit`, `set_last_unit`, `get_all_units`, `reset_units_to_default`, `_DEFAULT_UNITS`, `_cache_key`, `invalidate_units_cache` | `ui.widgets.combo.unit_service` |
| `UnitCombo`, `make_unit_combo` | `ui.widgets.combo.unit` |
| `ProgressBar`, `MultiProgressBar` | `ui.widgets.components.progress` |
| `AmountLabel`, `DebitCreditDisplay`, `BalanceDisplay`, `format_amount`, `amount_color`, `dr_cr_color` | `ui.widgets.components.amount_label` |
| `InfoRow`, `ModeLabel` | `ui.widgets.components.label` |
| `waste_zero_bg`, `waste_zero_border`, `waste_zero_color`, `waste_text_color` | `ui.widgets.core.colors` (دوال) |
| `waste_colors`, `waste_level`, `card_colors`, `status_colors` | `ui.widgets.core.colors` |

---

## ملفات نظيفة — لا تحتاج تغيير

| الملف | السبب |
|-------|-------|
| `ui/theme_manager.py` | المصدر الأصلي — نضيف إليه فقط |
| `ui/theme.py` | ✅ نظيف بالكامل |
| `ui/font.py` | لا ألوان |
| `ui/events.py` | لا ألوان |
| `ui/constants.py` | لا ألوان |
| `ui/widgets/theme/table_styles.py` | كلها من `_C` ✅ |
| `ui/widgets/theme/card_styles.py` | كلها من `_C` ✅ |
| `ui/widgets/theme/label_styles.py` | كلها من `_C` ✅ |
| `ui/widgets/theme/layout_styles.py` | كلها من `_C` ✅ |
| `ui/widgets/panels/state.py` | كلها من `_C` ✅ |
| `ui/widgets/components/notification.py` | كلها من `status_colors()` ✅ |
| `ui/widgets/components/badge.py` | كلها من `_C` ✅ |
| `ui/widgets/combo/unit_service.py` | المصدر الأصلي — لا re-exports ✅ |
| `ui/widgets/components/progress.py` | المصدر الأصلي — لا re-exports ✅ |
| `ui/widgets/components/amount_label.py` | المصدر الأصلي — لا re-exports ✅ |

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
- `input_error_bg`  → `#2a1010` بدل `#fef2f2`
- `waste_zero_bg`   → `#2a2a2a` بدل `#f5f5f5`
- `card_colors()`   → ترجع dark palette تلقائياً
- badge color       → `_C['danger']` النسخة الداكنة
- كل شيء يتغير تلقائياً ✅

**لو حد حاول import من ملف كان فيه re-export:**
- الدالة مش موجودة فيه → `ImportError` فوري → يُصلح المكان الصح
- مش هيعدي بصامت ✅