# دليل الكود — UI / Widgets (7): Mixins

> `ui/widgets/mixins/` — كل الـ mixins المشتركة بين الـ widgets.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [BusConnectedMixin](#busconnectedmixin) | `mixins/bus.py` |
| [EditModeMixin + FormValidationMixin](#editmodemixin--formvalidationmixin) | `mixins/form_mixins.py` |
| [RefreshableMixin](#refreshablemixin) | `mixins/refresh_mixin.py` |
| [RebuildMixin](#rebuildmixin) | `mixins/rebuild_mixin.py` |
| [SelectionMixin](#selectionmixin) | `mixins/selection_mixin.py` |
| [ServiceMixin](#servicemixin) | `mixins/service.py` |
| [SharedOpsMixin](#sharedopsmixin) | `mixins/shared_ops.py` |

---

## BusConnectedMixin

### `ui/widgets/mixins/bus.py`

```python
class BusConnectedMixin:
    """
    Mixin يوفر ربطاً موحداً بـ event bus.

    [Phase 6] إصلاح حالة أول إشعار: لو _cached_company_id لا يزال None
    بعد محاولة قراءته من company_state، يُضبط من company_id الواصل
    ويتابع بدل إسقاط الإشعار.
    """
```

#### الربط والفصل

```python
._connect_bus(data=True, company=False, theme=False, lang=False)
# [تحسين 39] Guard يمنع double-connect عبر _bus_connected flag
# [P-04] يُهيّئ _cached_company_id=None عند الاشتراك
# يربط:
#   data=True    → company_data_changed + data_changed
#   company=True → company_data_changed (لـ _on_company_changed)
#   theme=True   → theme_changed
#   lang=True    → language_changed

._disconnect_bus()
# يفصل كل الـ slots — يُستدعى من closeEvent
# يُعيد ضبط _bus_connected + _cached_company_id
```

#### Signal handlers — Override هنا

```python
._on_data_changed()
# يُستدعى عند company_data_changed (نفس الشركة) أو data_changed
# افتراضياً: pass — override لتحديث الـ widget

._on_company_changed(company_id: int)
# يُستدعى عند تغيير الشركة النشطة
# افتراضياً: يُحدّث _cached_company_id فقط

._on_theme_changed(theme_name: str)
# افتراضياً: pass — override لإعادة تطبيق الـ styles

._on_language_changed(lang_code: str)
# افتراضياً: pass — override لتحديث النصوص
```

#### مساعدات

```python
._get_active_company_id() -> int | None   # static method
# يقرأ company_id النشط من company_state

.invalidate_company_cache()
# يُعيد ضبط _cached_company_id لإجبار إعادة القراءة
```

**[Phase 6] منطق _on_company_data_changed:**
1. لو `_cached_company_id = None` → جرب القراءة من company_state
2. لو لا يزال `None` → اضبطه من company_id الواصل وتابع
3. لو `company_id != _cached_company_id` → شركة مختلفة → تجاهل
4. نفس الشركة → تنفيذ `_on_data_changed()`

**[تحسين 24]** `_on_data_changed_guarded` يُسجّل debug log عند التخطي بسبب refresh_guard.

---

## EditModeMixin + FormValidationMixin

### `ui/widgets/mixins/form_mixins.py`

#### EditModeMixin

```python
class EditModeMixin:
    """
    يدير الـ Add/Edit mode للفورمات.
    _editing_id: int | None = None
    """

.init_edit_mode(btn_add, btn_save, btn_cancel, lbl_mode=None)
# يحفظ references للأزرار — يُستدعى في __init__

.enter_edit_mode(item_id: int, mode_text: str = "")
# يُخفي btn_add، يُظهر btn_save + btn_cancel
# يضبط النص على lbl_mode

.exit_edit_mode(add_text: str = "")
# يُعيد الـ add state — يُستدعى بعد حفظ أو إلغاء

.is_edit_mode -> bool   # property
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
    """يوفر دوال تحقق موحدة."""

._warn(msg: str)
# يعرض msg_warning — يستخدم tr("warning") كعنوان

.validate_required(fields: list, parent=None) -> bool
# fields: [(widget, label), ...]
# QLineEdit → يتحقق من text().strip()
# QComboBox → يتحقق من currentData() is not None
# يُركّز على الحقل الفارغ ويرجع False

.validate_amount(spinbox, label="", min_val=0.01, parent=None) -> bool
# يتحقق أن spinbox.value() >= min_val

.validate_positive(value: float, label="", parent=None) -> bool
# يتحقق أن value > 0
```

---

## RefreshableMixin

### `ui/widgets/mixins/refresh_mixin.py`

```python
class RefreshableMixin:
    """Mixin لأي widget يحتاج تحديث دوري."""

.refresh()
# يستدعي _load_data() ثم _fill_ui(data)
# يُعالج الأخطاء عبر _on_refresh_error()

._load_data() -> list   # افتراضياً: []
._fill_ui(data)         # افتراضياً: pass
._on_refresh_error(error: Exception)
# افتراضياً: print — override للـ logging المخصص
```

---

## RebuildMixin

### `ui/widgets/mixins/rebuild_mixin.py`

```python
class RebuildMixin:
    """
    يوفر _replace_widget() لإعادة بناء محتوى الـ tab.
    يفترض: self._root_layout (QVBoxLayout)
    """

._replace_widget(new_widget: QWidget)
# يُزيل الـ widget القديم (deleteLater) ويُضيف الجديد
# يحفظ reference في self._current_widget

._schedule_rebuild(delay_ms: int = 0)
# QTimer.singleShot → self._rebuild()

._rebuild()   # افتراضياً: pass — override للمنطق الفعلي
```

---

## SelectionMixin

### `ui/widgets/mixins/selection_mixin.py`

```python
class SelectionMixin:
    """
    منطق اختيار الصفوف في الجداول.

    _id_col: int  = 0         # عمود الـ ID
    _id_role: int = Qt.UserRole
    """

._selected_id(table=None) -> int | None
# يحاول Qt.UserRole أولاً، ثم int(item.text()) كـ fallback
# table=None → يستخدم self.table

._selected_row(table=None) -> int
# يرجع currentRow() أو -1

._warn_no_selection(msg="")
# يعرض msg_info — رسالة من tr("select_item_first") لو msg فارغ

._require_selection(msg="") -> int | None
# = _selected_id() مع تحذير تلقائي لو None
```

**مثال:**
```python
class MyPanel(QWidget, SelectionMixin):
    def _edit(self):
        item_id = self._require_selection()
        if item_id is None:
            return
        # ...
```

---

## ServiceMixin

### `ui/widgets/mixins/service.py`

```python
class ServiceMixin:
    """
    Lazy-loaded services للـ widgets.
    يفترض: self.conn موجود ويشير لـ DB connection صالح.

    ⚠️ كل property تُنشئ instance جديد عند كل وصول.
    لاستدعاءات متعددة في نفس الـ method، احفظ في متغير:
        svc = self._item_service
        svc.add(...)
        svc.list_by_type(...)
    """

._item_service    → ItemService(self.conn)
._category_service → CategoryService(self.conn)
._product_service  → ProductService(self.conn)
._order_service    → OrderService(self.conn)
._journal_service  → JournalService(self.conn)
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

._edit_published_item(row: dict, shared_type: str, parent=None)
# يبحث في companies.db عن shared_item بنفس الاسم
# يفتح SharedItemsDialog
# يُطلق emit_company_data_changed() بعد النجاح

._publish_item(row: dict, shared_type: str, item_data: dict, parent=None)
# لو العنصر منشور → _edit_published_item
# لو جديد → PublishAsSharedDialog
# [FIX] يُطلق emit_company_data_changed() بعد النشر
```

#### مساعدات

```python
._check_shared_id(item_id) -> bool
._extract_shared_id(item_id) -> int | None
._is_published(row: dict) -> bool
._find_row_by_id(item_id) -> dict | None
```

**ملاحظة [FIX]:** `_publish_item` كانت تنتهي صامتة بدون إطلاق الإشعار — أُصلح ليطلق `emit_company_data_changed()` دائماً.