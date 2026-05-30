# دليل الكود — UI / Widgets (9): Button & Theme Utilities

> ملف مرجع لمكونات الأزرار، ومساعدات الثيم، وصف الـ settings dialog.

---

## فهرس هذا الجزء

| القسم | الملفات |
|-------|---------|
| [Button](#button) | `components/button` |
| [SettingsDialog](#settingsdialog) | `settings_dialog` |
| [MainWindow](#mainwindow) | `main_window` |

---

## Button

### `ui/widgets/components/button.py`

```python
make_btn(text: str, style: str = "normal", fixed_size: bool = True) -> QPushButton
# style: "primary" | "success" | "danger" | "ghost" | "normal"
# يحفظ style على الزر كـ Qt property ("_btn_style") لاستخدامها في refresh_visible_buttons
# fixed_size=True → setFixedWidth | False → setMinimumWidth (قابل للتمدد)
# ألوان الأزرار تُقرأ من _C تلقائياً — تتغير مع الثيم

invalidate_stylesheet_cache()
# يمسح _stylesheet_cache — يُستدعى من apply_font() وعند تغيير الثيم

refresh_visible_buttons(root_widget) -> int
# يُعيد تطبيق stylesheet على كل QPushButton في الـ widget tree
# يعتمد على property("_btn_style") — يتجاهل الأزرار بدون هذا الـ property
# يمسح _stylesheet_cache قبل التطبيق لضمان استخدام الألوان الجديدة
# يرجع عدد الأزرار المحدثة
# مثال: bus.theme_changed.connect(lambda _: refresh_visible_buttons(main_window))

calc_btn_width(text: str, font_size: int, padding: int = 32) -> int
```

**أنماط الأزرار:**

| style | الوصف | الألوان |
|-------|-------|---------|
| `"primary"` | الإجراء الرئيسي — غامق | من `accent_light / accent_text` |
| `"success"` | حفظ / إضافة — أخضر | من `success_bg / success` |
| `"danger"` | حذف / خطأ — أحمر | من `danger_bg / danger` |
| `"ghost"` | ثانوي / إلغاء — شفاف | من `border_med / text_sec` |
| `"normal"` | عادي — رمادي فاتح | من `bg_surface_2 / text_sec` |

**مثال مع الثيم واللغة:**
```python
from ui.widgets.components.button import make_btn
from ui.widgets.core.i18n import tr

btn_save   = make_btn(tr("btn_save"),   "success")
btn_cancel = make_btn(tr("btn_cancel"), "ghost")
btn_delete = make_btn(tr("btn_delete"), "danger")

def _on_language_changed(self, lang_code: str):
    self.btn_save.setText(tr("btn_save"))
    self.btn_cancel.setText(tr("btn_cancel"))
```

**ملاحظة الـ cache:**
`_stylesheet_cache` key هو `(style_name, font_size)`.
يُمسح تلقائياً عند:
- تغيير حجم الخط (عبر `apply_font()`)
- تغيير الثيم (عبر `apply_theme()` → `invalidate_stylesheet_cache()`)
- استدعاء `refresh_visible_buttons()` مباشرة

---

## SettingsDialog

### `ui/settings_dialog.py` — `SettingsDialog`

```python
SettingsDialog(app: QApplication, parent=None)
# تبويبات: الخط | المظهر | اللغة | الوحدات | GIMP
```

**التبويبات:**

| التبويب | المحتوى |
|---------|---------|
| 🔤 الخط | Slider لحجم الخط (8-20) + معاينة نصية |
| 🎨 المظهر | Radio buttons: فاتح / داكن + معاينة الألوان |
| 🌐 اللغة | Radio buttons: العربية / English |
| 📏 الوحدات | قائمة وحدات القياس + إضافة/حذف/استعادة |
| 🖼️ GIMP | مسار ملف GIMP التنفيذي |

**حفظ (_save):**
```python
# حجم الخط:
set_font_size(size)
apply_font(app, size)
bus.font_changed.emit(size)

# الثيم:
theme_manager.set_theme(selected_theme, save=True)
# → يُطلق bus.theme_changed تلقائياً داخل set_theme()

# اللغة:
i18n_manager.set_language(selected_lang, save=True)
app.setLayoutDirection(i18n_manager.qt_direction)
bus.language_changed.emit(selected_lang)

# GIMP path:
set_setting(conn, "gimp_path", path)
```

**مساعدات داخلية:**
```python
_get_settings_conn_and_status() -> tuple[conn, has_company]
# [A-05] يقرأ company_state.is_ready مرة واحدة فقط
# يرجع (conn, True) | (None, False)

_get_settings_conn() -> conn | None
# للتوافق مع الكود القديم — يستخدم _get_settings_conn_and_status() داخلياً

_has_active_company() -> bool
# للتوافق مع الكود القديم
```

---

## MainWindow

### `ui/main_window.py` — `MainWindow`

```python
MainWindow(app: QApplication)
# resize: WINDOW_DEFAULT_W × 820
# setLayoutDirection: Qt.RightToLeft
# setMinimumSize: (SIDEBAR_COLLAPSED_WIDTH + 400, 500)
```

**index_map للـ Navigation:**
```python
{
    "costing":    1,   # CostingSection
    "pricing":    2,   # PricingSection
    "accounting": 3,   # AccountingTab
    "inventory":  4,   # InventoryTab
    "design":     5,   # DesignSection
    "orders":     6,   # OrdersSection
}
# index 0 → NoCompanyScreen (دائماً موجود)
```

**سلوكيات خاصة:**
```python
# "settings"     → SettingsDialog (لا يغير الـ stack index)
# "shared_items" → SharedItemsManagerDialog مباشرة

# تغيير الشركة:
def _on_company_changed(company_id: int):
    AppState.invalidate()           # مسح font_size cache
    self._refresh_tabs()            # إعادة بناء الـ tabs
    bus.company_data_changed.emit(company_id)
```

**حماية من فشل الـ import:**
```python
_try_build_section(builder_fn, section_name) -> QWidget
# يرجع placeholder مع رسالة خطأ واضحة لو فشل الـ import
# يضمن أن فشل section واحد لا يمنع بقية الـ sections

_make_placeholder_tab(section_name, error="") -> QWidget
# placeholder مؤقت بـ "🚧" + رسالة الخطأ
```

**إضافة Tab جديدة:**
```python
# في MainWindow._build_tabs():
def _build_my_section():
    from ui.tabs.my_section import MySection
    return MySection(conn_fn=lambda: conn)

_builders.append((_build_my_section, tr("my_section_name")))
# الـ index تلقائي حسب ترتيب الـ _builders list

# في index_map:
"my_key": N   # N = index المناسب

# في _sidebar._build():
("🔑", tr("my_section_name"), "my_key", "")
```