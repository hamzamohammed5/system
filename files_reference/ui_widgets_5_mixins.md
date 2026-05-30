# دليل الكود — UI / Widgets (5): Mixins

> الجزء الخامس — كل الـ Mixins: bus، refresh، edit، rebuild، select، validate، service، shared_ops.

---

## فهرس هذا الجزء

| القسم | الملفات |
|-------|---------|
| [BusConnectedMixin](#busconnectedmixin) | `mixins/bus` |
| [RefreshableMixin](#refreshablemixin) | `mixins/refresh` |
| [EditModeMixin](#editmodemixin) | `mixins/edit` |
| [RebuildMixin](#rebuildmixin) | `mixins/rebuild` |
| [SelectionMixin](#selectionmixin) | `mixins/select` |
| [FormValidationMixin](#formvalidationmixin) | `mixins/validate` |
| [ServiceMixin](#servicemixin) | `mixins/service` |
| [SharedOpsMixin](#sharedopsmixin) | `mixins/shared_ops` |

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
# [P-04] مقارنة مباشرة بـ _cached_company_id بدل استدعاء is_same_company()
# المرة الأولى (cache=None): يُضبط _cached_company_id من company_state
# لو شركة مختلفة → تجاهل + تحديث الـ cache + debug log
# لو نفس الشركة → _on_data_changed() + _refresh_guard=True + QTimer.singleShot(clear)

def _on_data_changed_guarded()
# [تحسين 24] يتجاهل لو _refresh_guard=True (يمنع data_changed المكرر بعد company_data_changed)
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
# عند استدعائه، _C تكون مُحدَّثة بالفعل من apply_theme()

def _on_language_changed(lang_code: str)
# Override — يُحدّث النصوص بـ tr() عند تغيير اللغة
# يُستدعى فقط لو _connect_bus(lang=True)

# ── Cache management ──

def invalidate_company_cache()
# [P-04] يُعيد ضبط _cached_company_id = None
# استدعه لو الشركة تغيرت من خارج الـ bus العادي
```

**[P-04] لماذا _cached_company_id أسرع من is_same_company():**
مع مئات الـ widgets المشتركة، كل `company_data_changed` كان يستدعي `is_same_company()` التي تقرأ من `company_state.company_id`. الآن المقارنة `int == int` مباشرة بدون أي استدعاء خارجي.

**مثال كامل مع theme وlanguage:**
```python
from ui.widgets.mixins.bus import BusConnectedMixin
from ui.widgets.core.i18n import tr
from ui.app_settings import _C

class MyPanel(QWidget, BusConnectedMixin):
    EMPTY_TITLE = "no_data"  # مفتاح tr()

    def __init__(self):
        super().__init__()
        self._connect_bus(data=True, theme=True, lang=True)

    def _on_data_changed(self):
        self.refresh()

    def _on_theme_changed(self, theme_name: str):
        # إعادة تطبيق الألوان من _C (تم تحديثها بالفعل من apply_theme)
        self.setStyleSheet(f"background:{_C['bg_input']};")
        self._empty_state.setStyleSheet(
            f"QFrame {{ background:{_C['bg_input']}; border:none; }}"
        )

    def _on_language_changed(self, lang_code: str):
        self.btn_add.setText(tr("btn_add"))
        self._empty_state.set_title(tr(self.EMPTY_TITLE))
        self._header.search_bar.set_placeholder(tr("list_search_placeholder"))

    def closeEvent(self, event):
        self._disconnect_bus()
        super().closeEvent(event)
```

---

## RefreshableMixin

### `ui/widgets/mixins/refresh.py` — `RefreshableMixin`

```python
def refresh()
# يستدعي _load_data() ثم _fill_ui() مع try/except
def _load_data() -> []    # Override — يجلب البيانات
def _fill_ui(data)        # Override — يملأ الـ UI
def _on_refresh_error(error: Exception)
# افتراضياً: print — Override لعرض رسالة للمستخدم
```

---

## EditModeMixin

### `ui/widgets/mixins/edit.py` — `EditModeMixin`

```python
def init_edit_mode(btn_add, btn_save, btn_cancel, lbl_mode=None)
def enter_edit_mode(item_id: int, mode_text: str = "")
# يُخفي btn_add ويُظهر btn_save + btn_cancel
def exit_edit_mode(add_text: str = "")
# يُعيد للحالة الابتدائية
def _set_add_state()   # يُظهر btn_add ويُخفي btn_save/btn_cancel
def is_edit_mode -> bool   # property — True لو _editing_id ≠ None
# _editing_id: int | None
```

---

## RebuildMixin

### `ui/widgets/mixins/rebuild.py` — `RebuildMixin`

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

### `ui/widgets/mixins/select.py` — `SelectionMixin`

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

## FormValidationMixin

### `ui/widgets/mixins/validate.py` — `FormValidationMixin`

```python
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

## ServiceMixin

### `ui/widgets/mixins/service.py` — `ServiceMixin`

```python
# Properties كسولة — instance جديد في كل وصول (لأن conn ممكن يتغير بعد تغيير الشركة)
# يفترض: self.conn موجود ويشير لـ DB connection صالح
._item_service     -> ItemService(self.conn)
._category_service -> CategoryService(self.conn)
._product_service  -> ProductService(self.conn)
._order_service    -> OrderService(self.conn)
._journal_service  -> JournalService(self.conn)
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
# كل العمليات تستخدم emit_company_data_changed() بعد نجاحها
```