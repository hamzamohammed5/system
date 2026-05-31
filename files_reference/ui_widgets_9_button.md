# دليل الكود — UI / Widgets (9): Button

> `ui/widgets/components/button.py` — مكوّن الأزرار.
> لـ SettingsDialog و MainWindow → راجع `ui_widgets_ui_root.md`

---

## فهرس هذا الجزء

| القسم | الملفات |
|-------|---------|
| [Button](#button) | `components/button.py` |

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