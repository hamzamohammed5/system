# دليل الكود — UI / Widgets (7): Mixins

> `ui/widgets/mixins/` — كل الـ mixins المشتركة بين الـ widgets.
>
> ⚠️ **[تغيير هيكلي كبير]** حسب `system_arch.txt` الحالي، هذا المسار يحتوي
> الآن على **ملفين فقط**: `form_mixins.py` و `shared_ops.py`. الملفات
> التالية من النسخة القديمة **لم تعد موجودة وحُذفت من هذا المرجع**:
> `bus.py` (BusConnectedMixin), `refresh_mixin.py` (RefreshableMixin),
> `rebuild_mixin.py` (RebuildMixin), `selection_mixin.py` (SelectionMixin),
> `service.py` (ServiceMixin). وظيفة `BusConnectedMixin` القديمة استُبدلت
> بالكامل بـ `WidgetMixin` الموحد في `ui/widgets/core/widget_mixin.py`
> (راجع `ui_widgets_core.md`) — وهو المصدر الوحيد الآن لربط الـ widgets
> بأحداث الـ bus (`theme_changed`, `font_changed`, `language_changed`,
> `company_data_changed`) عبر `_init_widget_mixin()` + `_refresh_style()` /
> `_refresh_lang()` / `_refresh_data()`.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [EditModeMixin + FormValidationMixin](#editmodemixin--formvalidationmixin) | `mixins/form_mixins.py` |
| [SharedOpsMixin](#sharedopsmixin) | `mixins/shared_ops.py` |

---

## EditModeMixin + FormValidationMixin

### `ui/widgets/mixins/form_mixins.py`

> **[إصلاح 2.4]** الملف الصحيح:
> `from ui.widgets.mixins.form_mixins import EditModeMixin`
> (بدل `from ui.widgets.mixins.edit import EditModeMixin` المحذوف)

#### EditModeMixin

```python
class EditModeMixin:
    _editing_id: int | None = None

.init_edit_mode(btn_add, btn_save, btn_cancel, lbl_mode=None)
# يحفظ references للأزرار — يُستدعى في __init__

.enter_edit_mode(item_id: int, mode_text: str = "")
# يُخفي btn_add، يُظهر btn_save + btn_cancel
# يضبط النص على lbl_mode
# يُسند self._editing_id = item_id

.exit_edit_mode(add_text: str = "")
# يُعيد الـ add state — يُستدعى بعد حفظ أو إلغاء
# يُعيد ضبط self._editing_id = None

.is_edit_mode -> bool   # property: self._editing_id is not None
```

**مثال:**
```python
class MyForm(QWidget, EditModeMixin):
    def __init__(self):
        self.init_edit_mode(self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode)

    def load_for_edit(self, item_id):
        self.enter_edit_mode(item_id, f"─── تعديل: {name} ───")

    def _on_cancel(self):
        self.exit_edit_mode("─── إضافة جديدة ───")
```

#### FormValidationMixin

```python
class FormValidationMixin:
    """يوفر دوال تحقق موحدة — يستخدم tr() للرسائل."""

._warn(msg: str)
# يعرض msg_warning — يستخدم tr("warning") كعنوان

.validate_required(fields: list, parent=None) -> bool
# fields: [(widget, label), ...]
# QLineEdit → يتحقق من text().strip()
# QComboBox → يتحقق من currentData() is not None
# يُركّز على الحقل الفارغ ويرجع False

.validate_amount(spinbox, label="", min_val=0.01, parent=None) -> bool
# يتحقق أن spinbox.value() >= min_val
# رسالة الخطأ: tr("field_positive_enter", label=label)

.validate_positive(value: float, label="", parent=None) -> bool
# يتحقق أن value > 0
# رسالة الخطأ: tr("field_positive", label=label)
```

---

## SharedOpsMixin

### `ui/widgets/mixins/shared_ops.py`

```python
class SharedOpsMixin:
    """
    يوحّد منطق عمليات العناصر المشتركة.

    يفترض:
        self._published_names: set[str]
        self._all_rows: list[dict]
    """
```

#### الدوال الرئيسية

```python
._edit_shared_item(item_id, shared_type: str, parent=None)
# لو العنصر مشترك → SharedItemsDialog
# لو منشور → _edit_published_item
# لو عادي → msg_info "استخدم «✏️ تعديل»"
# يُطلق emit_company_data_changed() بعد النجاح

._edit_published_item(row: dict, shared_type: str, parent=None)
# يبحث في companies.db عن shared_item بنفس الاسم
# يفتح SharedItemsDialog
# يُطلق emit_company_data_changed() بعد النجاح

._publish_item(row: dict, shared_type: str, item_data: dict, parent=None)
# لو العنصر منشور → _edit_published_item
# لو جديد → PublishAsSharedDialog
# [FIX] يُطلق emit_company_data_changed() بعد النشر دائماً
# القديم: كانت تنتهي صامتة بدون إطلاق الإشعار → الـ UI لا يتحدث بعد النشر
# السبب: _edit_shared_item و _edit_published_item كانتا يُطلقانه
#          لكن _publish_item كانت لا تُطلقه — فجوة في التغطية
```

#### مساعدات

```python
._check_shared_id(item_id) -> bool
._extract_shared_id(item_id) -> int | None
._is_published(row: dict) -> bool
._find_row_by_id(item_id) -> dict | None
```

**الـ import المستخدم:**
```python
from ui.widgets.core.events import emit_company_data_changed
# يُستدعى في _edit_shared_item, _edit_published_item, _publish_item
```

**[إصلاح هيكلة]** استُبدلت الاستدعاءات المباشرة لـ `db.companies.companies_schema`
(`get_central_connection`, `create_central_tables`) و SQL خام على `shared_items`
بـ:
```python
from services.companies.company_service import CompanyService
from services.companies.shared_items_service import SharedItemsService

central = CompanyService.get_central_conn_and_init()
svc     = SharedItemsService(central)   # ينشئ جداول shared_items تلقائياً في __init__
svc.list_items(shared_type)             # بدل استعلام SQL خام بالاسم
```
المسار الصحيح: `widget → service → repo (db/)`.
---

## علاقات الملفات

- `form_mixins.py` و `shared_ops.py` مستقلان تماماً عن بعضهما — لا استيراد متبادل بينهما.
- `shared_ops.py` يعتمد على `ui.widgets.core.events.emit_company_data_changed` (مرجع: `ui_widgets_core.md`)، وعلى `services.companies.company_service.CompanyService` و `services.companies.shared_items_service.SharedItemsService` (خارج نطاق هذا المرجع).
- `form_mixins.py` (`FormValidationMixin`) يعتمد على `ui.widgets.panels.themed_inputs.ThemedLineEdit/ThemedComboBox` (مرجع الملفات في `panels/`) و `ui.widgets.dialogs.message.msg_warning` (مرجع: `dialogs/`).
- `EditModeMixin` و `FormValidationMixin` يُستخدمان معاً غالباً في نفس الفورم (مثال: `BaseCrudForm` في `base/crud_form.py`) لكن لا علاقة مباشرة بينهما داخل الملف.
