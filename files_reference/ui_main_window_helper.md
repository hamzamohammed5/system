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
# [تحسين 20] يُحدّث أحجام كل الأزرار + يستدعي _apply_style() على كل _SectionLabel
# يُستدعى من MainWindow._on_nav() بعد SettingsDialog

sidebar.get_buttons() -> list[_NavButton]
sidebar.get_company_selector() -> CompanySelector
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

**Animation عند Toggle:**
- `QPropertyAnimation` على `minimumWidth` و `maximumWidth`
- مدة 200ms، `QEasingCurve.InOutCubic`
- يُخفي/يُظهر `CompanySelector` و `_SectionLabel`s عند الطي

---

## _nav_button

### `ui/main_window_helper/_nav_button.py` — `_NavButton`

```python
_NavButton(icon: str, label: str, badge: str = "", parent=None)
# QPushButton — checkable
# يحمل nav_key عبر setProperty("nav_key", key)

btn.set_badge(text: str)
btn.set_collapsed(collapsed: bool)
# collapsed=True  → عرض SIDEBAR_COLLAPSED_WIDTH، يُخفي النص والـ badge
# collapsed=False → عرض SIDEBAR_EXPANDED_WIDTH - 16، يُظهر النص والـ badge

btn.setChecked(v: bool)
# يُعيد تطبيق _update_style() تلقائياً

btn.refresh_sizes()
# يُحدّث font-size الأيقونة والنص من get_font_size()
# يُعيد حساب الارتفاع: max(38, base*2+14)
# يُعيد تطبيق _apply_badge_style()
```

**الألوان:**
- كل الألوان من `_C` — تتغير مع الثيم
- `_apply_badge_style()`: `_C['danger']` و `_C['bg_input']` بدل hardcoded

**الثوابت (من `ui.constants`):**
```python
SIDEBAR_EXPANDED_WIDTH  = 224
SIDEBAR_COLLAPSED_WIDTH = 56
CONTENT_MIN_WIDTH       = 820
WINDOW_DEFAULT_W        = SIDEBAR_EXPANDED_WIDTH + CONTENT_MIN_WIDTH
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

lbl._apply_style()
# يُطبّق stylesheet من _C و get_font_size() الحالي
# يُستدعى تلقائياً من __init__
# يُستدعى من _Sidebar.refresh_all_buttons() [تحسين 20]

lbl.set_collapsed(collapsed: bool)
# setVisible(not collapsed)
```

**Style:**
```python
# color:   _C['sidebar_muted']
# font-size: fs(base, -2)pt
# font-weight: 700, letter-spacing: 1.5px
# padding: 12px 16px 4px 16px
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
# يرجع الحالة الجديدة
```

**Style (من `_C`):**
```python
# background: transparent، border-top: sidebar_border
# color: sidebar_muted
# hover: sidebar_hover، sidebar_text
```