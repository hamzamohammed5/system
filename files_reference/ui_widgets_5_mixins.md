# دليل الكود — UI / Widgets (5): Mixins

> الجزء الخامس — كل الـ Mixins: bus، refresh، edit+validate، rebuild، select، service، shared_ops.

---

## فهرس هذا الجزء

| القسم | الملفات |
|-------|---------|
| [BusConnectedMixin](#busconnectedmixin) | `mixins/bus.py` |
| [RefreshableMixin](#refreshablemixin) | `mixins/refresh_mixin.py` |
| [EditModeMixin + FormValidationMixin](#editmodemixin--formvalidationmixin) | `mixins/form_mixins.py` |
| [RebuildMixin](#rebuildmixin) | `mixins/rebuild_mixin.py` |
| [SelectionMixin](#selectionmixin) | `mixins/selection_mixin.py` |
| [ServiceMixin](#servicemixin) | `mixins/service.py` |
| [SharedOpsMixin](#sharedopsmixin) | `mixins/shared_ops.py` |

---

## BusConnectedMixin

### `ui/widgets/mixins/bus.py` — `BusConnectedMixin`

```python
def _connect_bus(data=True, company=False, theme=False, lang=False)
# data=True    → يربط company_data_changed (مع _on_company_data_changed)
#              + data_changed (مع _on_data_changed_guarded)
# company=True → يربط company_data_changed لـ _on_company_changed (بدون فلتر شركة)
# theme=True   → يربط bus.theme_changed لـ _on_theme_changed
# lang=True    → يربط bus.language_changed لـ _on_language_changed
# [تحسين 39] guard يمنع double-connect (عبر _bus_connected flag)
# [P-04] يُهيّئ _cached_company_id = None عند الاشتراك

def _disconnect_bus()
# يفصل كل الـ signals المرتبطة (data + company + theme + lang)
# يُعيد ضبط _bus_connected = False
# [P-04] يمسح _cached_company_id = None

# ── Data changed handlers ──

def _on_company_data_changed(company_id: int)
# [Phase 6 إصلاح] معالجة أول إشعار صح:
#   1. لو _cached_company_id = None → جرب من company_state
#   2. لو لا يزال None → اضبطه من company_id الواصل وتابع (لا تتجاهل)
#   3. لو company_id != _cached → تجاهل + debug log
#   4. نفس الشركة → _on_data_changed() + _refresh_guard + QTimer.singleShot(clear)

def _on_data_changed_guarded()
# [تحسين 24] يتجاهل لو _refresh_guard=True (يمنع data_changed المكرر)
# يُسجّل debug log عند التخطي

def _on_data_changed()   # Override — يُنفَّذ عند تغيير البيانات

# ── Company changed handler ──

def _on_company_changed(company_id: int)
# [P-04] تلقائياً يُحدّث _cached_company_id بالشركة الجديدة
# Override لإعادة البناء الكامل عند تغيير الشركة

# ── Theme & language handlers ──

def _on_theme_changed(theme_name: str)
# Override — يُعيد تطبيق الـ styles عند تغيير الثيم
# يُستدعى فقط لو _connect_bus(theme=True)

def _on_language_changed(lang_code: str)
# Override — يُحدّث النصوص بـ tr() عند تغيير اللغة
# يُستدعى فقط لو _connect_bus(lang=True)

# ── Cache management ──

def invalidate_company_cache()
# [P-04] يُعيد ضبط _cached_company_id = None
```

**[P-04] لماذا _cached_company_id أسرع من is_same_company():**
مع مئات الـ widgets المشتركة، المقارنة `int == int` مباشرة بدون استدعاء خارجي.

**مثال كامل مع theme وlanguage:**
```python
from ui.widgets.mixins.bus import BusConnectedMixin
from ui.widgets.core.i18n import tr
from ui.app_settings import _C

class MyPanel(QWidget, BusConnectedMixin):
    def __init__(self):
        super().__init__()
        self._connect_bus(data=True, theme=True, lang=True)

    def _on_data_changed(self):
        self.refresh()

    def _on_theme_changed(self, theme_name: str):
        self.setStyleSheet(f"background:{_C['bg_input']};")

    def _on_language_changed(self, lang_code: str):
        self.btn_add.setText(tr("btn_add"))

    def closeEvent(self, event):
        self._disconnect_bus()
        super().closeEvent(event)
```

---

## RefreshableMixin

### `ui/widgets/mixins/refresh_mixin.py` — `RefreshableMixin`

> **ملاحظة:** كان اسم الملف `mixins/refresh.py` — أصبح `mixins/refresh_mixin.py`.

```python
def refresh()
# يستدعي _load_data() ثم _fill_ui() مع try/except
def _load_data() -> []    # Override — يجلب البيانات
def _fill_ui(data)        # Override — يملأ الـ UI
def _on_refresh_error(error: Exception)
# افتراضياً: print — Override لعرض رسالة للمستخدم
```

---

## EditModeMixin + FormValidationMixin

### `ui/widgets/mixins/form_mixins.py`

> **ملاحظة:** دُمج `mixins/edit.py` (EditModeMixin) و `mixins/validate.py` (FormValidationMixin) في هذا الملف.

```python
# ── EditModeMixin ──
def init_edit_mode(btn_add, btn_save, btn_cancel, lbl_mode=None)
def enter_edit_mode(item_id: int, mode_text: str = "")
# يُخفي btn_add ويُظهر btn_save + btn_cancel
def exit_edit_mode(add_text: str = "")
# يُعيد للحالة الابتدائية
def _set_add_state()   # يُظهر btn_add ويُخفي btn_save/btn_cancel
def is_edit_mode -> bool   # property — True لو _editing_id ≠ None
# _editing_id: int | None

# ── FormValidationMixin ──
def _warn(msg: str)
# msg_warning(self, tr("warning"), msg)

def validate_required(fields: list, parent=None) -> bool
# fields: [(widget, label), ...]
# QLineEdit: يتحقق من text().strip()
# QComboBox: يتحقق من currentData() ≠ None
# رسائل: tr("enter_field", label=label) | tr("select_field", label=label)

def validate_amount(spinbox, label="", min_val=0.01, parent=None) -> bool
# رسالة: tr("field_positive_enter", label=label)

def validate_positive(value: float, label="", parent=None) -> bool
# رسالة: tr("field_positive", label=label)
```

---

## RebuildMixin

### `ui/widgets/mixins/rebuild_mixin.py` — `RebuildMixin`

> **ملاحظة:** كان اسم الملف `mixins/rebuild.py` — أصبح `mixins/rebuild_mixin.py`.

```python
# يفترض: self._root_layout (QVBoxLayout)
def _replace_widget(new_widget: QWidget)
# يُزيل القديم (hide + deleteLater) ثم يُضيف الجديد
# يحفظ reference في self._current_widget
def _schedule_rebuild(delay_ms: int = 0)
# QTimer.singleShot(delay_ms, self._rebuild)
def _rebuild()   # Override
```

---

## SelectionMixin

### `ui/widgets/mixins/selection_mixin.py` — `SelectionMixin`

> **ملاحظة:** كان اسم الملف `mixins/select.py` — أصبح `mixins/selection_mixin.py`.

```python
_id_col: int  = 0
_id_role: int = Qt.UserRole

def _selected_id(table=None) -> int | None
# يقرأ من item.data(UserRole) أولاً، ثم item.text() كـ fallback
def _selected_row(table=None) -> int
def _warn_no_selection(msg: str = "")
# عنوان: tr("warning") + رسالة افتراضية: tr("select_item_first")
def _require_selection(msg: str = "") -> int | None
# يستدعي _warn_no_selection لو مفيش اختيار، يرجع None
```

---

## ServiceMixin

### `ui/widgets/mixins/service.py` — `ServiceMixin`

```python
# Properties كسولة — instance جديد في كل وصول (لأن conn ممكن يتغير)
# يفترض: self.conn موجود ويشير لـ DB connection صالح
._item_service     -> ItemService(self.conn)
._category_service -> CategoryService(self.conn)
._product_service  -> ProductService(self.conn)
._order_service    -> OrderService(self.conn)
._journal_service  -> JournalService(self.conn)
```

**ملاحظة:** لاستدعاءات متعددة في نفس الـ method، احفظ في متغير:
```python
# ✅ صح
svc = self._item_service
items = svc.list_by_type("raw")
count = svc.get_usage_count(some_id)
```

---

## SharedOpsMixin

### `ui/widgets/mixins/shared_ops.py` — `SharedOpsMixin`

```python
# يفترض: self._published_names: set[str] و self._all_rows: list[dict]
def _check_shared_id(item_id) -> bool
def _extract_shared_id(item_id) -> int | None
def _is_published(row: dict) -> bool
def _find_row_by_id(item_id) -> dict | None

def _edit_shared_item(item_id, shared_type: str, parent=None)
# لو عنصر محلي منشور → يفتح SharedItemsDialog
# لو عنصر عادي → msg_info
def _edit_published_item(row: dict, shared_type: str, parent=None)
def _publish_item(row: dict, shared_type: str, item_data: dict, parent=None)
# لو منشور → يعدّله | لو لم يُنشر → يفتح PublishAsSharedDialog
# [FIX] emit_company_data_changed() تُستدعى في نهاية _publish_item أيضاً
# كل العمليات تستخدم emit_company_data_changed() بعد نجاحها
```