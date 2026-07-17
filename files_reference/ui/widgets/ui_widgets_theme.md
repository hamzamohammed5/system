# دليل الكود — UI / Widgets (4): Theme Styles

> `ui/widgets/theme/` — كل الـ stylesheet generators والـ builders للواجهة.
> المصدر الوحيد لألوان الألوان هو `ui/theme_manager.py` عبر `_C`.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [Table Styles](#table-styles) | `theme/table_styles.py` |
| [Input Styles](#input-styles) | `theme/input_styles.py` |
| [Label Styles](#label-styles) | `theme/label_styles.py` |
| [Card Styles](#card-styles) | `theme/card_styles.py` |
| [Layout Styles](#layout-styles) | `theme/layout_styles.py` |
| [Builders](#builders) | `theme/builders.py` |

---

## Table Styles

### `ui/widgets/theme/table_styles.py`

```python
table_style(variant="normal") -> str
# variant: "normal" | "compact" | "large"
# كل الألوان من _C

splitter_style() -> str
# المصدر الوحيد — لا تكرار في أي ملف آخر
# يُستخدم في BaseSection._build()

ROW_HEIGHT_COMPACT = 34
ROW_HEIGHT_NORMAL  = 40
ROW_HEIGHT_LARGE   = 48
```

---

## Input Styles

### `ui/widgets/theme/input_styles.py`

```python
input_style(height=32, error=False) -> str
# للـ QLineEdit / QComboBox / QDateEdit
# [إصلاح ألوان] error colors من _C بدل hardcoded:
#   القديم: "#fef2f2", "#f87171"
#   الجديد: _C["input_error_bg"], _C["input_error_border"]
# يضمن تغيير الألوان تلقائياً عند التبديل بين light و dark

spinbox_style(height=32, positive=False, widget="QDoubleSpinBox") -> str
# [إصلاح ألوان] positive colors من _C بدل hardcoded:
#   القديم: "#f0fdf4", "#86efac", "#15803d"
#   الجديد: _C["input_positive_bg"], _C["input_positive_border"], _C["input_positive_color"]
# يضمن تغيير الألوان تلقائياً عند التبديل بين light و dark

search_input_style(height=34) -> str
```

---

## Label Styles

### `ui/widgets/theme/label_styles.py`

```python
status_label_style(status="info", font_offset=0) -> str
# يستخدم status_colors() من core/colors

muted_label_style(font_offset=-1) -> str
section_title_style(color=None, font_offset=0) -> str
icon_btn_style(color="#aaa", hover_color="#e53935") -> str
link_btn_style(color=None) -> str
```

---

## Card Styles

### `ui/widgets/theme/card_styles.py`

```python
card_style(bg=None, border=None, radius=10) -> str
status_card_style(status="info", radius=8) -> str
# يستخدم status_colors() من core/colors
group_box_style(accent=None) -> str
```

---

## Layout Styles

### `ui/widgets/theme/layout_styles.py`

```python
tab_style(accent=None, size="normal") -> str
# size: "normal" | "inner" | "small"
# يُستخدم في TabSectionBase._setup()

calc_tab_width(text: str, size="normal", extra_pad=0) -> int
# [إضافة] يحسب العرض اللازم لتبويب نصه text بحيث يبان كامل بدون قص.
# نفس فلسفة _calc_btn_width_for_text في components/button.py: القياس
# الحقيقي للنص (QFontMetrics) + الـ "chrome" الفعلي (padding + border +
# سمك مؤشر التاب النشط) اللي tab_style() بترسمه، بدل min-width ثابت
# في constants.py قد يكون أصغر من نصوص عربية/طويلة.
# size لازم يطابق نفس size المستخدم في tab_style() لنفس QTabWidget.

apply_tab_widths(tab_widget, size="normal", extra_pad=6) -> None
# [حل مركزي لقص نص التبويبات] يضبط min-width الفعلي لتبويبات QTabWidget
# حسب أطول نص موجود فعلياً بين كل التبويبات — عبر bar.setStyleSheet()
# إضافي (QTabBar::tab { min-width:{max}px; }).
# قيد Qt: لا يوجد API لعرض مختلف لكل تاب لوحده عبر QSS (::tab بينطبق
# بنفس القاعدة على الكل) — الحل المضمون: رفع min-width العام لأكبر
# عرض نص فعلي بين كل التبويبات.
# يُستدعى بعد إضافة كل التبويبات، وكل ما تتغير عناوين التبويبات (بناء
# أولي، تغيير لغة، تغيير حجم خط).

normalize_tab_widget(tab_widget) -> None
# [حل مركزي لتناسق شكل التبويبات] يوحّد إعدادات العرض الأساسية لأي
# QTabWidget (خصائص لا يمكن التحكم فيها عبر QSS، مكمّل لـ tab_style()):
#   setTabPosition(QTabWidget.North)
#   setUsesScrollButtons(True)
#   setElideMode(Qt.ElideNone)
#   tabBar().setExpanding(False)
#   tabBar().setDrawBase(True)
# يُستدعى مرة واحدة بعد إنشاء الـ QTabWidget مباشرة (قبل أو بعد إضافة
# التبويبات — لا فرق). يُستخدم في TabSectionBase._setup().

scroll_style(width=6) -> str
# المصدر الوحيد لـ QScrollArea / QScrollBar — لا تكرار
# يُستخدم في BaseDetailPanel._build()

filter_bar_style() -> str
toolbar_style() -> str
tree_style() -> str
list_style() -> str
```

---

## Builders

### `ui/widgets/theme/builders.py`

```python
h_divider(color=None, height=1) -> QFrame
# فاصل أفقي موحد
# color افتراضي: _C['border']

v_divider(color=None, width=1, margin_v=4) -> QFrame
# فاصل عمودي موحد — للـ toolbars
# color افتراضي: _C['border_med']

wrap_in_scroll(widget: QWidget, min_height=0, horizontal=False) -> QScrollArea
# يلف أي widget في QScrollArea موحد مع scroll_style()
# يُستخدم في BaseCrudForm._build()
```

---

## ملاحظات عامة

- **لا hardcoded colors** في أي دالة — كل الألوان تُقرأ من `_C` عند الاستدعاء.
- `_C` يُحدَّث تلقائياً عند تغيير الثيم عبر `apply_theme()`.
- `splitter_style()` و `scroll_style()` — كل منهما مصدر وحيد، لا تنسخهما في ملفات أخرى.
- عند تغيير الثيم: استدعِ `invalidate_stylesheet_cache()` من `components/button.py` لمسح الـ cache.
- `input_style` و `spinbox_style` يُستوردان في `forms/inputs.py` بالمسار الصحيح: `from ..theme.input_styles import input_style, spinbox_style`.
- `input_style(error=True)` و `spinbox_style(positive=True)` يستخدمان مفاتيح `_C` — لا ألوان hardcoded — لضمان التزامن مع الثيم الحالي.