# خطة توحيد نظام الألوان

## الهدف

```
theme_manager.py  →  المصدر الوحيد لكل لون يتأثر بالثيم
       ↓
   theme.py (_C)  →  الألوان النشطة حالياً
       ↓
 كل الملفات      →  تقرأ من _C أو من دوال colors.py فقط
```

**لا يوجد لون hardcoded خارج theme_manager.py**
**لا يوجد ملفان يعرّفان نفس اللون**

---

## الوضع الحالي — المشاكل

### مشكلة 1: CARD_PALETTE في colors.py
```python
# colors.py — ألوان تتأثر بالثيم لكنها خارج theme_manager
CARD_PALETTE = { "#1565c0": ("#e8f0fe", "#90caf9"), ... }
_DARK_CARD_PALETTE = { "#1565c0": ("#1a2a3a", "#2a4a6a"), ... }
```
هذه تعريف ألوان، مش مجرد logic — لازم تكون في theme_manager.

### مشكلة 2: theme.py يبني الـ stylesheet
`build_stylesheet()` تستخدم `_C` فقط ✅ — لا مشكلة هنا.

### ما هو نظيف بالفعل ✅
- `theme.py` — كلها من `_C`
- `input_styles.py` — كلها من `_C`
- `builders.py` — كلها من `_C`
- `nav_button.py` — كلها من `_C`
- `component_row/ui.py` — كلها من `_C` أو دوال `colors.py`
- `status_colors()` في `colors.py` — كلها من `_C`
- `waste_*()` في `colors.py` — كلها من `_C`

---

## الخطة — ملفان فقط يتغيران

### الملف 1: `ui/theme_manager.py`

**إضافة `CARD_PALETTES` dict منفصل** بجانب `_LIGHT_THEME` و`_DARK_THEME`:

```python
# في theme_manager.py — بعد _DARK_THEME مباشرة

CARD_PALETTES: dict[str, dict[str, tuple[str, str]]] = {
    "light": {
        "#1565c0": ("#e8f0fe", "#90caf9"),
        "#0d47a1": ("#e3f2fd", "#64b5f6"),
        "#1d4ed8": ("#eff6ff", "#93c5fd"),
        "#1e40af": ("#eff6ff", "#93c5fd"),
        "#0891b2": ("#e0f7fa", "#80deea"),
        "#0369a1": ("#e0f2fe", "#7dd3fc"),
        "#10b981": ("#ecfdf5", "#6ee7b7"),
        "#2e7d32": ("#e8f5e9", "#a5d6a7"),
        "#065f46": ("#ecfdf5", "#a7f3d0"),
        "#15803d": ("#f0fdf4", "#86efac"),
        "#16a34a": ("#f0fdf4", "#86efac"),
        "#ef4444": ("#fef2f2", "#fca5a5"),
        "#dc2626": ("#fef2f2", "#fca5a5"),
        "#c62828": ("#ffebee", "#ef9a9a"),
        "#991b1b": ("#fef2f2", "#fecaca"),
        "#b91c1c": ("#fef2f2", "#fecaca"),
        "#f59e0b": ("#fffbeb", "#fcd34d"),
        "#e65100": ("#fff3e0", "#ffcc80"),
        "#b45309": ("#fffbeb", "#fde68a"),
        "#d97706": ("#fffbeb", "#fde68a"),
        "#ea580c": ("#fff7ed", "#fdba74"),
        "#6b7280": ("#f9fafb", "#d1d5db"),
        "#374151": ("#f9fafb", "#e5e7eb"),
        "#9ca3af": ("#f9fafb", "#e5e7eb"),
        "#555555": ("#f5f5f5", "#e0e0e0"),
        "#555":    ("#f5f5f5", "#e0e0e0"),
        "#4b5563": ("#f9fafb", "#d1d5db"),
        "#8b5cf6": ("#f5f3ff", "#c4b5fd"),
        "#6d28d9": ("#f5f3ff", "#ddd6fe"),
        "#6a1b9a": ("#f3e5f5", "#ce93d8"),
        "#7c3aed": ("#f5f3ff", "#c4b5fd"),
        "#9333ea": ("#faf5ff", "#d8b4fe"),
        "#db2777": ("#fdf2f8", "#f9a8d4"),
        "#be185d": ("#fdf2f8", "#fbcfe8"),
        "#4e342e": ("#efebe9", "#bcaaa4"),
        "#5d4037": ("#efebe9", "#bcaaa4"),
    },
    "dark": {
        "#1565c0": ("#1a2a3a", "#2a4a6a"),
        "#0d47a1": ("#152030", "#1e3a5f"),
        "#1d4ed8": ("#1a2540", "#2a4080"),
        "#1e40af": ("#1a2540", "#2a4080"),
        "#0891b2": ("#0a2830", "#1a5060"),
        "#0369a1": ("#0a2030", "#1a4060"),
        "#10b981": ("#0a2820", "#1a5040"),
        "#2e7d32": ("#0a2010", "#1a4020"),
        "#065f46": ("#0a2818", "#1a5030"),
        "#15803d": ("#0a2018", "#1a4030"),
        "#16a34a": ("#0a2018", "#1a4030"),
        "#ef4444": ("#2a1010", "#5a2020"),
        "#dc2626": ("#2a1010", "#5a2020"),
        "#c62828": ("#281010", "#4a1818"),
        "#991b1b": ("#2a1010", "#4a1818"),
        "#b91c1c": ("#2a1010", "#4a1818"),
        "#f59e0b": ("#2a2000", "#4a3800"),
        "#e65100": ("#281400", "#503000"),
        "#b45309": ("#281c00", "#4a3400"),
        "#d97706": ("#281c00", "#4a3400"),
        "#ea580c": ("#281800", "#503800"),
        "#6b7280": ("#1e2028", "#2e3040"),
        "#374151": ("#1a1c24", "#2a2e38"),
        "#9ca3af": ("#1e2028", "#2e3040"),
        "#555555": ("#1e1e1e", "#2e2e2e"),
        "#555":    ("#1e1e1e", "#2e2e2e"),
        "#4b5563": ("#1a1c24", "#2a2e38"),
        "#8b5cf6": ("#1a1028", "#3a2060"),
        "#6d28d9": ("#180c28", "#301860"),
        "#6a1b9a": ("#1a0828", "#3a1060"),
        "#7c3aed": ("#1a0c2a", "#341860"),
        "#9333ea": ("#1c0a28", "#3c1860"),
        "#db2777": ("#280a18", "#501830"),
        "#be185d": ("#280a18", "#501830"),
        "#4e342e": ("#201010", "#3a1c18"),
        "#5d4037": ("#221210", "#3c1e18"),
    },
}
```

---

### الملف 2: `ui/widgets/core/colors.py`

**يُحذف منه:** `CARD_PALETTE` و `_DARK_CARD_PALETTE` بالكامل.

**يُعدَّل:** `card_colors()` تستورد من `theme_manager` مباشرة:

```python
def card_colors(color: str) -> tuple[str, str]:
    """
    يرجع (bg, border) للون المعطى حسب الثيم الحالي.
    المصدر الوحيد: theme_manager.CARD_PALETTES
    """
    from ui.theme import _C
    from ui.theme_manager import theme_manager, CARD_PALETTES
    palette = CARD_PALETTES.get(theme_manager.current_theme, CARD_PALETTES["light"])
    return palette.get(
        color,
        (_C["card_fallback_bg"], _C["card_fallback_border"])
    )
```

---

## النتيجة النهائية

### `theme_manager.py` يحتوي على:
| القسم | ما يحتويه |
|-------|-----------|
| `_LIGHT_THEME` | كل ألوان الـ light theme (flat keys) |
| `_DARK_THEME` | كل ألوان الـ dark theme (flat keys) |
| `CARD_PALETTES["light"]` | lookup table لألوان البطاقات في light |
| `CARD_PALETTES["dark"]` | lookup table لألوان البطاقات في dark |

### `colors.py` يحتوي على:
| الدالة | تفعل ماذا |
|--------|----------|
| `card_colors(color)` | تبحث في `CARD_PALETTES` من theme_manager |
| `status_colors(level)` | تقرأ من `_C` |
| `waste_colors(pct)` | تقرأ من `_C` |
| `waste_zero_bg/border/color()` | تقرأ من `_C` |
| `waste_text_color()` | تقرأ من `_C` |
| `waste_level(pct)` | pure logic — لا ألوان |

### `theme.py` يحتوي على:
| القسم | ما يفعله |
|-------|---------|
| `_C` dict | يعكس الثيم النشط من theme_manager |
| `apply_theme()` | يُحدِّث `_C` عند تغيير الثيم |
| `build_stylesheet()` | يبني CSS من `_C` فقط |

---

## جدول المسؤوليات النهائي

```
ما تريد تعريفه          → أين يكون
─────────────────────────────────────────────────────
لون UI يتغير مع الثيم   → theme_manager._LIGHT/DARK_THEME
ألوان بطاقة بـ accent   → theme_manager.CARD_PALETTES
الألوان النشطة حالياً   → theme.py (_C) — لا تعديل يدوي
دالة تُحوّل level→ألوان → colors.py
CSS stylesheet           → theme.py (build_stylesheet)
```

---

## ترتيب التنفيذ

| # | الملف | العمل |
|---|-------|-------|
| 1 | `ui/theme_manager.py` | إضافة `CARD_PALETTES` dict بعد `_DARK_THEME` |
| 2 | `ui/widgets/core/colors.py` | حذف `CARD_PALETTE` و`_DARK_CARD_PALETTE`، تعديل `card_colors()` |

**ملفان فقط — لا تغيير في أي ملف آخر.**

---

## التحقق بعد التنفيذ

```python
# يجب أن يعمل هذا بعد التنفيذ:
from ui.theme_manager import theme_manager, CARD_PALETTES
from ui.widgets.core.colors import card_colors, status_colors, waste_colors

# كل الألوان من مصدر واحد
assert "#1565c0" in CARD_PALETTES["light"]
assert "#1565c0" in CARD_PALETTES["dark"]

# card_colors تقرأ من theme_manager
theme_manager.set_theme("dark")
bg, border = card_colors("#1565c0")
assert bg == "#1a2a3a"  # dark value

theme_manager.set_theme("light")
bg, border = card_colors("#1565c0")
assert bg == "#e8f0fe"  # light value
```