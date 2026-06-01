# دليل الكود — UI / Widgets (8): Dialogs

> `ui/widgets/dialogs/` — نوافذ الحوار الموحدة: قواعد، رسائل، تأكيدات، إعدادات.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [DialogShell + BaseDialog](#dialogshell--basedialog) | `dialogs/dialogs_base.py` |
| [Message Dialogs](#message-dialogs) | `dialogs/message.py` |
| [Confirm Dialogs](#confirm-dialogs) | `dialogs/confirm.py` |
| [SettingsDialog](#settingsdialog) | `dialogs/settings_dialog.py` |

---

## DialogShell + BaseDialog

### `ui/widgets/dialogs/dialogs_base.py`

#### DialogShell

```python
DialogShell(parent=None, title="", icon="📋", subtitle="",
            accent=None, min_width=380, min_height=0)
# QDialog موحد: هيدر ملون + body + شريط أزرار
# RTL + modal تلقائي
# accent افتراضي من _C["accent"]
```

**الهيكل:**
```
┌─────────────────────────────┐
│  [icon]  title              │  ← هيدر gradient
│          subtitle           │
├─────────────────────────────┤
│         body_layout         │  ← QVBoxLayout للمحتوى
├─────────────────────────────┤
│      [btn] [btn]  ...       │  ← شريط أزرار
└─────────────────────────────┘
```

```python
.body_layout -> QVBoxLayout   # property — أضف المحتوى هنا
.btn_layout  -> QHBoxLayout   # property — أضف الأزرار هنا
```

**[تحسين 21]** `_make_header` يستخدم `accent_transparent = accent + "cc"` بدل `{a}dd`.

#### BaseDialog

```python
BaseDialog(parent=None, title="", icon="📋", subtitle="",
           min_size=(500, 400), accent=None, show_btns=True)
# يرث من DialogShell
# يُضيف تلقائياً: زر "✖ إلغاء" + زر "✅ حفظ"
```

**Hooks للـ subclass:**
```python
._build_content(lay: QVBoxLayout)   # افتراضياً: pass — override لإضافة المحتوى
._on_accept()                        # افتراضياً: self.accept()
```

**API:**
```python
.set_ok_enabled(enabled: bool)
.set_ok_text(text: str)
```

**مثال:**
```python
class MyDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__(parent, title="بياناتي", icon="📋",
                         min_size=(500, 400))

    def _build_content(self, lay):
        lay.addWidget(QLabel("محتوى النافذة"))

    def _on_accept(self):
        # منطق الحفظ
        self.accept()
```

---

## Message Dialogs

### `ui/widgets/dialogs/message.py`

نوافذ رسائل موحدة تستخدم مفاتيح tr() للأزرار.

```python
class MessageDialog(DialogShell):
    # kind: "info" | "warning" | "critical" | "question"
    # yes_no=True → زرا "نعم" + "لا" | False → زر "حسناً" فقط
    .result_yes() -> bool
```

**أيقونات الـ kinds:**
```
"question" → ❓  accent
"info"     → ℹ️  accent
"warning"  → ⚠️  _C["warning"]
"critical" → ❌  _C["danger"]
```

**API السريع:**
```python
msg_question(parent, title: str, text: str) -> bool
# يعرض نافذة سؤال ويرجع True لو الجواب "نعم"

msg_info(parent, title: str, text: str)
msg_warning(parent, title: str, text: str)
msg_critical(parent, title: str, text: str)
```

---

## Confirm Dialogs

### `ui/widgets/dialogs/confirm.py`

نوافذ تأكيد موحدة تستخدم مفاتيح tr().

```python
class ConfirmDialog(DialogShell):
    # danger=True → accent = _C["danger"]
    # accent مخصص لو محدد صراحةً
    .result_confirmed() -> bool
```

**API السريع:**
```python
confirm_delete(parent, item_name: str, extra_msg: str = "") -> bool
# عنوان: tr("confirm_delete")
# رسالة: tr("delete_confirm_msg", name=item_name)
# زر التأكيد: tr("delete") — بلون danger

confirm_action(parent, title: str, message: str,
               icon="❓", confirm_text="", cancel_text="",
               danger=False, accent=None) -> bool
# نافذة تأكيد عامة قابلة للتخصيص الكامل

confirm_save(parent, item_name: str = "", extra_msg: str = "") -> bool
# عنوان: tr("confirm_save")
# زر التأكيد: tr("save") — بلون success
```

**مثال:**
```python
from ui.widgets.dialogs.confirm import confirm_delete, confirm_action

# حذف عنصر
if confirm_delete(self, item["name"]):
    service.delete(item["id"])

# تأكيد إجراء مخصص
if confirm_action(self, "تأكيد الإرسال",
                  "هل تريد إرسال هذا التقرير؟",
                  icon="📤", confirm_text="إرسال"):
    send_report()
```

---

## SettingsDialog

### `ui/widgets/dialogs/settings_dialog.py`

```python
class SettingsDialog(QDialog):
    def __init__(self, app: QApplication, parent=None)
```

**التبويبات:**

| الفهرس | التبويب | المحتوى |
|--------|---------|---------|
| 0 | 🔤 الخط | QSlider لحجم الخط (8-20) + معاينة نصية |
| 1 | 🎨 المظهر | Radio buttons: فاتح / داكن + معاينة ألوان |
| 2 | 🌐 اللغة | Radio buttons: العربية / English |
| 3 | 📏 الوحدات | QListWidget + إضافة/حذف/استعادة |
| 4 | 🖼️ GIMP | QLineEdit + زر تصفح لمسار gimp.exe |

**إجراءات الحفظ:**
```python
._save()
# 1. set_font_size(size) + apply_font() + bus.font_changed.emit()
# 2. theme_manager.set_theme() لو تغير الثيم
# 3. i18n_manager.set_language() + bus.language_changed.emit() لو تغيرت اللغة
# 4. set_setting(conn, "gimp_path", ...)
```

**إدارة الوحدات:**
```python
# يستخدم unit_service مباشرة (لا unit.py widget)
from ui.widgets.combo.unit_service import (
    load_units, add_unit, remove_unit,
    reset_units_to_default, _DEFAULT_UNITS,
)
```

**[A-05]** `_get_settings_conn_and_status()` يرجع `(conn, has_active_company)` في استدعاء واحد بدل استدعاءين منفصلين.

**ملاحظات:**
- الوحدات الافتراضية (`_DEFAULT_UNITS`) معروضة بلون `_C['text_muted']` ولا يمكن حذفها.
- لو لا توجد شركة نشطة، تظهر رسالة تنبيه في تبويبي الوحدات وGIMP.