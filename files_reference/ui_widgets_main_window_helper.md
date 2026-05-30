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

### `ui/main_window_helper/_sidebar.py`

Sidebar التطبيق الرئيسية — تحتوي على أزرار التنقل وزر الإعدادات وزر التبديل.

```python
Sidebar(on_navigate: callable, on_toggle: callable)
# on_navigate(key: str) — يُستدعى عند الضغط على أي زر تنقل
# on_toggle()           — يُستدعى عند الضغط على زر التبديل

sidebar.set_active(key: str)
# يُحدّث الزر النشط بصرياً

sidebar.set_expanded(expanded: bool)
# يُبدِّل بين الوضع الموسع (224px) والمُصغَّر (56px)
# يُخفي/يُظهر النصوص تلقائياً

sidebar.is_expanded -> bool
```

**الأزرار المُعرَّفة (بالترتيب):**
```python
# (icon, label_key, nav_key, badge)
("🏠", "home",       "",            "")
("💰", "costing",    "costing",     "")
("🏷️", "pricing",    "pricing",     "")
("📒", "accounting", "accounting",  "")
("📦", "inventory",  "inventory",   "")
("🎨", "design",     "design",      "")
("📋", "orders",     "orders",      "")
# ثم separator
("🔗", "shared_items", "shared_items", "")
("⚙️", "settings",    "settings",     "")
```

---

## _nav_button

### `ui/main_window_helper/_nav_button.py`

```python
NavButton(icon: str, label: str, key: str, badge: str = "",
          on_click: callable = None)
# زر تنقل واحد في الـ sidebar

NavButton.set_active(active: bool)
# يُطبّق لون sidebar_active أو sidebar_hover من _C

NavButton.set_expanded(expanded: bool)
# يُظهر/يُخفي النص (label) حسب حالة الـ sidebar

NavButton.set_badge(text: str)
# يُظهر badge صغير فوق الأيقونة (للإشعارات)

NavButton.key -> str
```

---

## _section_label

### `ui/main_window_helper/_section_label.py`

```python
SectionLabel(text: str)
# عنوان قسم مُصغَّر داخل الـ sidebar (مثلاً "الإدارة")
# يُخفى تلقائياً عندما يكون الـ sidebar مُصغَّراً

SectionLabel.set_expanded(expanded: bool)
```

---

## _toggle_button

### `ui/main_window_helper/_toggle_button.py`

```python
ToggleButton(on_click: callable)
# زر تبديل الـ sidebar بين الموسع والمُصغَّر
# الأيقونة تتغير: "◀" (موسع) | "▶" (مُصغَّر)

ToggleButton.set_expanded(expanded: bool)
# يُحدّث أيقونة الزر حسب الحالة
```