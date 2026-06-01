# دليل الكود — UI / Main Window Helper

> `ui/main_window_helper/` — مكونات الـ Sidebar والـ Navigation.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [_sidebar](#_sidebar) | `ui/main_window_helper/_sidebar.py` |
| [_nav_button](#_nav_button) | `ui/main_window_helper/_nav_button.py` |
| [_section_label](#_section_label) | `ui/main_window_helper/_section_label.py` |
| [_toggle_button](#_toggle_button) | `ui/main_window_helper/_toggle_button.py` |

---

## _sidebar

### `ui/main_window_helper/_sidebar.py` — `_Sidebar`

```python
_Sidebar(on_company_changed: callable, parent=None)
# QFrame — الشريط الجانبي الرئيسي للتطبيق
# الحجم الابتدائي: SIDEBAR_EXPANDED_WIDTH
# يحتوي: CompanySelector (هيدر) + Nav Scroll + Footer

sidebar.refresh_all_buttons()
# [تحسين 20] يُحدّث أحجام كل الأزرار عبر btn.refresh_sizes()
#             ثم يستدعي lbl._apply_style() على كل _SectionLabel
# يُستدعى من MainWindow._on_nav() بعد SettingsDialog
# القديم: كان يُحدّث الأزرار فقط ويتجاهل الـ section labels
# الجديد: يضمن أن الـ section labels تتحدث مع الأزرار عند تغيير حجم الخط

sidebar.get_buttons() -> list[_NavButton]
sidebar.get_company_selector() -> CompanySelector
```

**State الداخلي:**
```python
self._buttons: list         # كل _NavButton في الـ nav + footer
self._section_labels: list  # كل _SectionLabel (الإنتاج / المالية / العمل)
self._collapsed: bool       # حالة الطي الحالية
self._company_selector      # CompanySelector في الهيدر
self._toggle_btn            # _ToggleButton في الفوتر
```

**أقسام Nav (بالترتيب):**
```python
# section "الإنتاج"
("📊", "حساب التكلفة", "costing",    "")
("💰", "التسعير",       "pricing",    "")

# section "المالية"
("🏦", "الحسابات",     "accounting", "")
("📦", "المخزن",        "inventory",  "")

# section "العمل"
("🎨", "التصميمات",    "design",     "")
("📋", "الطلبات",       "orders",     "")

# Footer (بعد divider)
("🔗", "العناصر المشتركة", "shared_items", "")
("⚙️", "الإعدادات",        "settings",     "")
# + _ToggleButton
```

**`_on_toggle()` — Animation عند الطي/الفرد:**
```python
# يُشغّل QPropertyAnimation على minimumWidth و maximumWidth
# مدة 200ms، QEasingCurve.InOutCubic
# يُخفي/يُظهر _company_selector و كل _SectionLabel
# يستدعي btn.set_collapsed() على كل الأزرار
# يُعدّل عرض _toggle_btn للـ target width
```

**`refresh_all_buttons()` — التدفق الكامل:**
```python
for btn in self._buttons:
    btn.refresh_sizes()
    if self._collapsed:
        btn.set_collapsed(True)

# [تحسين 20] تحديث section labels بعد الأزرار
for lbl in self._section_labels:
    lbl._apply_style()
```

---

## _nav_button

### `ui/main_window_helper/_nav_button.py` — `_NavButton`

```python
_NavButton(icon: str, label: str, badge: str = "", parent=None)
# QPushButton — checkable
# يحمل nav_key عبر setProperty("nav_key", key)
# الألوان: كل الألوان من _C — تتغير مع الثيم
# badge colors: _C['danger'] و _C['bg_input'] بدل hardcoded "#C0392B" و "#FFF"

btn.set_badge(text: str)
btn.set_collapsed(collapsed: bool)
# collapsed=True  → عرض SIDEBAR_COLLAPSED_WIDTH، يُخفي النص والـ badge
#                   margins: (0,0,0,0)، alignment: AlignCenter
# collapsed=False → عرض SIDEBAR_EXPANDED_WIDTH - 16، يُظهر النص والـ badge
#                   margins: (10,0,10,0)، alignment: AlignVCenter

btn.setChecked(v: bool)
# يُعيد تطبيق _update_style() تلقائياً

btn.refresh_sizes()
# يُحدّث font-size الأيقونة من get_font_size() + 4
# يُحدّث font-size النص من get_font_size()
# يُعيد حساب الارتفاع: max(38, base*2+14)
# يُعيد ضبط العرض = SIDEBAR_EXPANDED_WIDTH - 16 لو غير مطوي
# يستدعي _apply_badge_style() لإعادة تطبيق badge colors من _C الحالي

btn._apply_badge_style()
# يُطبّق badge stylesheet من _C الحالي
# يُستدعى من: _build_content() عند الإنشاء
#              refresh_sizes() عند تغيير حجم الخط (قد يتغير الثيم أيضاً)
```

**هيكل المحتوى الداخلي (HBoxLayout — RTL):**
```
[ _txt_lbl (stretch=1) | _badge_lbl | _ico_lbl (22px) ]
```

**الثوابت (من `ui.constants` — مُعادة تصديرها من `_nav_button.py` للتوافق):**
```python
SIDEBAR_EXPANDED_WIDTH  = 224
SIDEBAR_COLLAPSED_WIDTH = 56
CONTENT_MIN_WIDTH       = 820
WINDOW_DEFAULT_W        = SIDEBAR_EXPANDED_WIDTH + CONTENT_MIN_WIDTH  # 1044
```

> ⚠️ `SIDEBAR_EXPANDED_WIDTH`, `SIDEBAR_COLLAPSED_WIDTH`, `CONTENT_MIN_WIDTH`, `WINDOW_DEFAULT_W`
> مُعرَّفة في `ui/constants.py` ومُعادة تصديرها من `_nav_button.py` للتوافق مع الكود القديم.

---

## _section_label

### `ui/main_window_helper/_section_label.py` — `_SectionLabel`

```python
_SectionLabel(text: str, parent=None)
# QLabel — عنوان قسم مُصغَّر (uppercase) داخل الـ sidebar
# مثال: "الإنتاج" → "الإنتاج"
# يستدعي _apply_style() تلقائياً في __init__

lbl._apply_style()
# يقرأ get_font_size() الحالي ويُعيد بناء الـ stylesheet
# يُستدعى من __init__ عند الإنشاء
# يُستدعى من _Sidebar.refresh_all_buttons() [تحسين 20] عند تغيير حجم الخط
# يضمن التزامن مع الـ font size الجديد بعد تغيير الإعدادات

lbl.set_collapsed(collapsed: bool)
# setVisible(not collapsed)
```

**Style (يُحسب في كل استدعاء لـ `_apply_style()`):**
```python
base = get_font_size()   # يُقرأ في كل استدعاء — يعكس الحجم الحالي دائماً
# color:        _C['sidebar_muted']
# font-size:    fs(base, -2)pt
# font-weight:  700
# letter-spacing: 1.5px
# padding:      12px 16px 4px 16px
# background:   transparent
# border:       none
```

**Imports:**
```python
from ui.theme import _C
from ui.font  import fs, get_font_size
```

---

## _toggle_button

### `ui/main_window_helper/_toggle_button.py` — `_ToggleButton`

```python
_ToggleButton(parent=None)
# QPushButton — زر طي/فرد الـ sidebar
# ارتفاع ثابت: 36px
# يشغّل animation عبر _Sidebar._on_toggle()

btn.toggle_state() -> bool
# يعكس الحالة الداخلية (_collapsed)
# يُحدّث النص: "◀" (مفرود) | "▶" (مطوي)
# يُحدّث Tooltip: "طي الشريط الجانبي" | "فرد الشريط الجانبي"
# يرجع الحالة الجديدة
```

**Style (من `_C` — يُطبّق في `__init__` مرة واحدة):**
```python
# background: transparent
# border-top: 1px solid _C['sidebar_border']
# color:      _C['sidebar_muted']، font-size: 11pt
# hover: background _C['sidebar_hover']، color _C['sidebar_text']
```

**Imports:**
```python
from ui.theme import _C   # [Refactor V3] إصلاح: ui.app_settings → ui.theme
```