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
class SettingsDialog(QDialog, WidgetMixin):
    def __init__(self, app, parent=None)
# _init_widget_mixin(theme=True, font=True, lang=True) — بدون data (لا يستمع لتغيير الشركة)
# [إصلاح ثيم] كانت كل الـ stylesheets تُبنى مرة واحدة وقت الإنشاء فقط —
# بما أنها QDialog طويلة العمر نسبياً، الستايل كان يتجمد لو المستخدم غيّر
# الثيم من نافذة أخرى والنافذة هذه لا تزال مفتوحة. الحل: WidgetMixin +
# فصل بناء كل widget (مرة واحدة، _build_*_tab) عن تطبيق الستايل (_refresh_style مركزية)
```

**التبويبات (QTabWidget):**

| الفهرس | التبويب | المحتوى |
|--------|---------|---------|
| 0 | tr("settings_tab_font") | QSlider لحجم الخط (MIN_FONT_SIZE–MAX_FONT_SIZE) + معاينة نصية حيّة |
| 1 | tr("settings_tab_theme") | بطاقات Radio buttons: فاتح/داكن + معاينة ألوان (6 swatches) |
| 2 | tr("settings_tab_lang") | بطاقات Radio buttons: العربية/English |
| 3 | tr("settings_tab_units") | QListWidget + إضافة/حذف/استعادة افتراضي |
| 4 | tr("settings_tab_gimp") | ThemedLineEdit + زر تصفح (QFileDialog) لمسار gimp |

**`_refresh_style(*_)` — مركزية تستدعي كل تبويب:**
```python
# self._tabs.setStyleSheet(...) (QTabBar مخصص) + self._btn_bar.setStyleSheet(...)
# ثم بالترتيب: _refresh_font_tab_style() + _refresh_theme_tab_style()
#   + _refresh_lang_tab_style() + _refresh_units_tab_style()
#   + _refresh_gimp_tab_style() + _refresh_notice_labels_style()
# وأخيراً refresh_visible_buttons(self) — لأزرار الوحدات/GIMP (btn_add,
#   btn_del, btn_reset, btn_browse, btn_clear) المبنية بـ make_btn()
```

**إجراءات الحفظ `_save()`:**
```python
# 1. size = self._slider.value(); set_font_size(size); apply_font(app, size)
#    bus.font_changed.emit(size)
# 2. لو selected_theme != theme_manager.current_theme → theme_manager.set_theme(selected_theme, save=True)
# 3. لو selected_lang != i18n_manager.language → i18n_manager.set_language(selected_lang, save=True)
#    + app.setLayoutDirection(...) + bus.language_changed.emit(selected_lang)
# 4. لو CompanyService.is_company_ready() → SettingsService.set("gimp_path", ...)
# 5. self.accept()
```

**إدارة الوحدات — [تصحيح مسار]:**
```python
# الاستيراد الفعلي من services/shared/unit_service.py (وليس combo/unit_service.py
# الذي لا وجود له):
from services.shared.unit_service import (
    load_units, add_unit, remove_unit,
    reset_units_to_default, _default_units, _DEFAULT_UNIT_KEYS,
)
from services.shared.settings_service import SettingsService
from services.companies.company_service import CompanyService
```

**دوال مساعدة على مستوى الموديول:**
```python
_get_settings_conn_and_status() -> tuple[Connection | None, bool]
# [A-05] يرجع (conn, has_active_company) في استدعاء واحد
# لو CompanyService.is_company_ready() == False → (None, False)
# وإلا (CompanyService.get_active_erp_conn(), conn is not None)

_get_settings_conn()          # للتوافق القديم — يرجع الـ conn فقط
_has_active_company() -> bool # للتوافق القديم — يرجع has_company فقط
```

**ملاحظات:**
- الوحدات الافتراضية (`_DEFAULT_UNIT_KEYS`) معروضة بلون `_C['text_muted']` مع tooltip، ولا يمكن حذفها (`_del_unit` يرفض بـ msg_warning).
- لو لا توجد شركة نشطة (`_load_settings`)، تظهر رسالة تنبيه (`_show_no_company_notice`) في تبويبي الوحدات وGIMP، محفوظة في `self._notice_labels` لإعادة تلوينها عند تغيير الثيم.
- `_refresh_lang(*_)` يحدّث: عنوان النافذة، نصوص كل التبويبات، نصوص الأزرار، وكل التلميحات (hints) في التبويبات الخمسة.

---

## علاقات الملفات

- `message.py` (`MessageDialog`) و `confirm.py` (`ConfirmDialog`) كلاهما يرث من `DialogShell` المعرّفة في `dialogs_base.py` — يستخدمان `body_layout`/`btn_layout` properties و `_refresh_style()` الأساسية عبر `super()._refresh_style()`.
- `dialogs_base.py` (`DialogShell`, `BaseDialog`) يستورد `ThemedFrame` من `panels/themed_inputs.py` (مرجع: `ui_widgets_panels.md`) و `make_btn` من `components/button.py` (مرجع: `ui_widgets_components.md`).
- `confirm.py` يستورد `make_btn` من `components/button.py` مباشرة (لبناء `_confirm_btn`) بالإضافة لوراثة `DialogShell`.
- `settings_dialog.py` (`SettingsDialog`) يرث `QDialog + WidgetMixin` مباشرة (**لا** يرث من `DialogShell`/`BaseDialog` — الوحيد في هذا المرجع الذي يبني هيكله الخاص بالكامل). يستورد `ThemedLineEdit` من `panels/themed_inputs.py`، `make_btn` من `components/button.py`، `list_style` من `theme/layout_styles.py` (مرجع: `ui_widgets_theme.md`)، و `refresh_visible_buttons` من `components/button.py`.
- `settings_dialog.py` هو الوحيد في هذا المرجع الذي يستورد من طبقة `services/` مباشرة (`services/shared/unit_service.py`, `services/shared/settings_service.py`, `services/companies/company_service.py`) — خارج نطاق `ui/widgets/`.
- كل الملفات الأربعة تستخدم `tr()` من `core/i18n.py` ومفاتيح `_C` من `ui/theme.py` بشكل مكثف (مرجع: `ui_widgets_core.md`).
- `message.py`/`confirm.py`/`dialogs_base.py` مترابطة بعلاقة وراثة مباشرة؛ `settings_dialog.py` مستقل تماماً عنها الثلاثة.