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
# theme=True   → يربط theme_changed لـ _on_theme_changed
# lang=True    → يربط language_changed لـ _on_language_changed
# guard يمنع double-connect (عبر _bus_connected flag)

def _disconnect_bus()
# يفصل كل الـ signals المرتبطة (data + company + theme + lang)
# يُعيد ضبط _bus_connected = False
# يمسح _cached_company_id = None

# Data changed handlers:
def _on_company_data_changed(company_id: int)
# مقارنة مباشرة بـ _cached_company_id بدل استدعاء is_same_company()
# المرة الأولى: يُضبط _cached_company_id من company_state
# لو شركة مختلفة → تجاهل + تحديث الـ cache
# لو نفس الشركة → _on_data_changed() + _refresh_guard
def _on_data_changed_guarded()
# يتجاهل لو _refresh_guard=True (يمنع data_changed المكرر)
def _on_data_changed()            # Override

# Company changed handler:
def _on_company_changed(company_id: int)
# تلقائياً يُحدث _cached_company_id بالشركة الجديدة
# Override لإعادة البناء عند تغيير الشركة

# Theme & language handlers:
def _on_theme_changed(theme_name: str)    # Override — يُعيد بناء الـ styles
def _on_language_changed(lang_code: str)  # Override — يُحدّث النصوص بـ tr()

def invalidate_company_cache()
# يُعيد ضبط _cached_company_id = None
```

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
        self.setStyleSheet(f"background:{_C['bg_page']};")
        self._empty_state.setStyleSheet(
            f"QFrame {{ background:{_C['bg_input']}; border:none; }}"
        )

    def _on_language_changed(self, lang_code: str):
        self.btn_add.setText(tr("btn_add"))
        self._empty_state.set_title(tr(self.EMPTY_TITLE))
        self._header.search_bar.set_placeholder(tr("list_search_placeholder"))
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
def exit_edit_mode(add_text: str = "")
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
# عنوان من tr("warning") + رسالة افتراضية من tr("select_item_first")
def _require_selection(msg: str = "") -> int | None
# يستدعي _warn_no_selection لو مفيش اختيار
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
# Properties كسولة — instance جديد في كل وصول (لأن conn ممكن يتغير)
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
def _edit_published_item(row: dict, shared_type: str, parent=None)
def _publish_item(row: dict, shared_type: str, item_data: dict, parent=None)
# كل العمليات تستخدم emit_company_data_changed() بعد نجاحها
```