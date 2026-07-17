# دليل الكود — UI / Widgets: Shared

> `ui/widgets/shared/` — قاعدة مشتركة للجداول التي تدعم العناصر المشتركة/المنشورة بين الشركات.
>
> ⚠️ **[تصحيح تسمية/تقسيم]** كان هذا المسار موثّقاً سابقاً مدموجاً مع
> `managers/` في ملف واحد (`ui_widgets_managers.md`) — مخالفة لقاعدة "مرجع
> واحد = مسار واحد". تم فصله هنا ليغطي `ui/widgets/shared/` فقط.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [SharedItemsListPanel](#shareditemslistpanel) | `shared/list_panel_with_shared.py` |

---

## SharedItemsListPanel

### `ui/widgets/shared/list_panel_with_shared.py`

**الغرض:** قاعدة مشتركة (base class) لكل الجداول التي تدعم العناصر
المشتركة/المنشورة بين الشركات (خامات، مكن، عمليات تشغيل، عمليات عمالة) —
تدمج الصفوف المحلية مع الصفوف المشتركة من قاعدة البيانات المركزية،
وتُضيف أزرار تعديل/حذف/استبدال شامل/تعديل مشترك/نشر كمشترك، مع تلوين
مميّز للصفوف حسب حالتها (عادي/مشترك/منشور).

**Imports:**
```python
from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox
from PyQt5.QtGui     import QColor

from ui.widgets.base.list_panel       import BaseListPanel     # القاعدة الأساسية للقوائم
from ui.widgets.mixins.shared_ops     import SharedOpsMixin    # منطق نشر/تعديل العناصر المشتركة
from ui.widgets.core.conn             import LiveConnMixin     # _live_conn() موحّد
from ui.widgets.dialogs.confirm       import confirm_delete
from ui.tabs.costing.shared._utils    import (                 # خارج ui/widgets/ — ألوان التلوين
    SHARED_COLOR, SHARED_BG, PUBLISHED_COLOR, PUBLISHED_BG,
)
from ui.tabs.companies.shared_items_mixin import get_published_local_names  # خارج ui/widgets/
from ui.widgets.core.i18n             import tr
```

**من يستدعي هذا الملف:** غير محدد بثقة من المرفقات الحالية — لا يوجد ملف
آخر ظاهر في نفس الدفعة يستورد `SharedItemsListPanel` صراحةً. حسب البنية
المتوقعة من `system_arch.txt` (`ui/tabs/costing/raw/raw_table_panel.py`
وملفات مشابهة تحت `machine/`, `labor/`) من المرجّح أنها الجهة المستهلكة
الفعلية، لكن هذا غير مؤكَّد من الكود المرفق نفسه.

---

### `SharedItemsListPanel(BaseListPanel, SharedOpsMixin, LiveConnMixin)`

```python
SharedItemsListPanel(conn=None, parent=None)
```

**ملاحظة هيكلية مهمة:** لا يوجد override لـ `_live_conn()` في هذا
الكلاس — تم حذف نسخة قديمة خاطئة كانت تستدعي `get_connection()` مباشرة
متجاهلة `company_state`. الآن يعتمد بالكامل على `LiveConnMixin._live_conn()`
الموروثة (تجرب `self.conn` أولاً، ثم `company_state` كـ fallback).

**Class-level attribute صريح:**
```python
_conn_attr = "conn"
# [إصلاح] يُحدَّد صراحةً لإسكات false-positive warning من LiveConnMixin.
# السبب: __init_subclass__ في LiveConnMixin يفحص substring "conn" في أسماء
# الـ class attributes، و"CONNECT_BUS" تحتوي "conn" (من Connect) بالغلط
# رغم أنها بوليني غير متعلق بـ DB connection إطلاقاً. القيمة "conn" هنا
# صحيحة فعلياً (موروثة من BaseListPanel وتُستخدم في self.conn بكل الكود)
# لكن لازم تُذكر صراحةً في cls.__dict__ لإيقاف الفحص قبل ما يصل لـ CONNECT_BUS.
```

**إعدادات الـ subclass (Class-level attributes — override في الوريث):**

| الاسم | النوع | الافتراضي | الغرض |
|---|---|---|---|
| `SHARED_TYPE` | `str` | `"raw"` | نوع العنصر المشترك (`"raw"` / `"machine"` / `"labor_op"` / `"machine_op"`) |
| `TABLE_COLS` | `list` | `[]` | أسماء أعمدة الجدول |
| `TABLE_TITLE` | `str` | `""` | عنوان الجدول |
| `HAS_BULK_REPLACE` | `bool` | `False` | هل يدعم زر "استبدال شامل" |
| `SHOW_CATEGORY` | `bool` | `True` | (من `BaseListPanel`) — إظهار فلتر التصنيف |
| `CONNECT_BUS` | `bool` | `True` | (من `BaseListPanel`) — الاستماع لـ `bus.company_data_changed` |
| `ADD_TEXT` | `str` | `""` | (من `BaseListPanel`) — فارغ لأن الإضافة تتم عبر فورم منفصل خارجي |
| `FILTER_SCOPE` | `str` | `""` | فارغ = استخدم `SHARED_TYPE` تلقائياً كـ scope للفلتر (انظر `_build_filter`) |

**`__init__(conn=None, parent=None)`:**
```python
# 1. self.COLUMNS = self.TABLE_COLS ; self.LIST_TITLE = self.TABLE_TITLE
#    (تحويل تسمية الـ subclass إلى ما يتوقعه BaseListPanel)
# 2. self.STRETCH_COL = -1
#    [توحيد الجداول] بدل 1 — نفس تصحيح raw_table_panel.py، يضمن تناسق
#    كل الجداول الوارثة (machine, machine_op, labor_op وأي جدول مستقبلي)
#    بتعديل واحد مركزي بدل تكراره في كل subclass لوحده.
# 3. self._published_names: set = set()
# 4. super().__init__(conn, parent)   ← يبني كل واجهة BaseListPanel
# 5. self._setup_column_widths(self.table)   ← hook اختياري لضبط عرض الأعمدة
# 6. self.table.setColumnHidden(0, True)     ← عمود الـ ID مخفي دائماً
```

---

#### Hooks المطلوبة (يجب override في الوريث — ترمي `NotImplementedError` افتراضياً)

```python
._fetch_local_rows() -> list
# يرجع الصفوف المحلية للشركة النشطة (raw/machine/... حسب SHARED_TYPE)

._fill_table_row(r: int, item: dict)
# يملأ صف الجدول رقم r من بيانات item

._edit_item(item_id: int)
# يفتح فورم/دايالوج تعديل العنصر المحلي

._delete_item(item_id: int, item_name: str)
# يحذف العنصر المحلي (مع تأكيد عادةً)
```

#### Hooks لها تنفيذ افتراضي (يمكن override):

```python
._get_shared_rows(local_rows: list) -> list
# افتراضياً: يرجع [] — override لجلب صفوف مشتركة من قاعدة البيانات المركزية

._get_item_data_for_publish(row: dict) -> dict
# افتراضياً: يرجع {} — override لبناء dict البيانات المطلوب نشرها كعنصر مشترك

._bulk_replace_item(item_id: int, item_name: str)
# افتراضياً: تمرير (pass) — override لإضافة منطق الاستبدال الشامل

._setup_column_widths(table)
# افتراضياً: تمرير (pass) — override لضبط عرض أعمدة محدد
```

---

#### تنفيذ واجهة `BaseListPanel`

```python
._load_rows() -> list
# 1. self._published_names = get_published_local_names(self.SHARED_TYPE)
# 2. local_rows  = self._fetch_local_rows()
# 3. shared_rows = self._get_shared_rows(local_rows)
# 4. يرجع local_rows + shared_rows  (دمج مباشر — القائمة المشتركة تُلحَق بالمحلية)

._fill_row(table, r: int, row: dict)
# يستدعي self._fill_table_row(r, row) ثم self._apply_row_colors(r, row)
# (يفصل بين منطق ملء المحتوى الخاص بالـ subclass ومنطق التلوين المشترك)
```

---

#### `_build_filter()` — override كامل لبناء `FilterToolbar`

```python
# [إصلاح FILTER_SCOPE] القديم: FILTER_SCOPE="all" ثابت → يُظهر كل
# التصنيفات بغض النظر عن SHARED_TYPE (خطأ منطقي — خامات كانت تعرض
# تصنيفات المكن مثلاً).
# الجديد:
#   لو not self.SHOW_CATEGORY → يرجع None (لا فلتر إطلاقاً)
#   scope = self.FILTER_SCOPE if self.FILTER_SCOPE else self.SHARED_TYPE
#   يبني FilterToolbar(conn=self.conn, scope=scope,
#                       show_category=self.SHOW_CATEGORY,
#                       show_date=self.SHOW_DATE,
#                       placeholder=self.SEARCH_PLACEHOLDER)
#   يربط toolbar.filter_changed → self._timer.start()
#   self.inp_search = toolbar.inp_search
# النتيجة: كل subclass يعرض تصنيفات SHARED_TYPE الخاصة به فقط ما لم
# يُحدِّد FILTER_SCOPE صراحةً.
```

---

#### التلوين — `_apply_row_colors(r: int, item: dict)`

```python
# is_shared    = item.get("_is_shared", False)
# is_published = item.get("_is_published", False)
# لو not is_shared and not is_published:
#     name = str(item.get("name", "")).strip().lower()
#     is_published = name in self._published_names
#     (اكتشاف احتياطي: عنصر محلي اسمه يطابق عنصراً منشوراً بالفعل)
#
# لو is_shared    → (fg, bg) = (SHARED_COLOR, SHARED_BG)
# لو is_published → (fg, bg) = (PUBLISHED_COLOR, PUBLISHED_BG)
# غير ذلك          → return (بدون تلوين، الصف يبقى بلون افتراضي)
#
# يُطبَّق fg/bg على foreground/background لكل خلية في الصف عبر QColor
```

---

#### أزرار الهيدر — `_build_extra_header_actions(header)`

```python
# لو self.HAS_BULK_REPLACE:
#     header.add_action(tr("shared_bulk_replace_btn"), self._on_bulk_replace, "primary")
# header.add_action(tr("edit_selected_btn"),          self._on_edit_selected)
# header.add_action(tr("delete_selected_btn"),        self._on_delete_selected, "danger")
# header.add_action(tr("shared_edit_shared_btn"),     self._on_edit_shared)
# header.add_action(tr("shared_publish_as_shared_btn"), self._on_publish_selected)
```

**معالجات الأزرار (كلها تتحقق من وجود عنصر مُحدَّد أولاً، وإلا `QMessageBox.information`):**

```python
._on_edit_selected()
# item_id = _selected_row_data()[0] ; لو None → تنبيه ; وإلا self._edit_item(item_id)

._on_delete_selected()
# item_id, item_name = _selected_row_data() ; self._delete_item(item_id, item_name)

._on_bulk_replace()
# item_id, item_name = _selected_row_data() ; self._bulk_replace_item(item_id, item_name)

._on_edit_shared()
# item_id = _selected_row_data()[0]
# self._edit_shared_item(item_id, self.SHARED_TYPE, self)   ← من SharedOpsMixin

._on_publish_selected()
# item_id = _selected_row_data()[0]
# row = self._get_current_row_dict() ; لو not row → return
# self._publish_item(row, self.SHARED_TYPE,
#                    self._get_item_data_for_publish(row), self)   ← من SharedOpsMixin
```

---

#### Hooks إضافية من `BaseListPanel` (تنفيذ تفويضي بسيط)

```python
._on_add_clicked()          # pass — الإضافة تتم عبر فورم منفصل خارج هذا الـ panel
._on_edit_item(item_id)     # يفوّض إلى self._edit_item(item_id)
._on_delete_item(item_id, item_name)  # يفوّض إلى self._delete_item(item_id, item_name)
._on_row_double_clicked(item_id)      # يفوّض إلى self._edit_item(item_id)
```

---

#### مساعدات داخلية

```python
._selected_row_data() -> tuple[int | None, str]
# item_id = self.selected_id() ; لو None → (None, "")
# row = self._get_current_row_dict()
# name = row.get("name", f"ID:{item_id}") if row else f"ID:{item_id}"
# يرجع (item_id, name)

._get_current_row_dict() -> dict | None
# item_id = self.selected_id() ; لو None → None
# يبحث في self._all_rows عن صف بـ str(row.get("id")) == str(item_id)
# يرجع الصف أو None
```

---

## ملاحظات عامة

- **[إصلاح]** حُذف بالكامل الـ override القديم الخاطئ لـ `_live_conn()` الذي كان يتجاهل `company_state`/`LiveConnMixin` عبر استدعاء `get_connection()` مباشرة. الكلاس الآن يعتمد حصرياً على السلوك الموروث من `LiveConnMixin`.
- **[إصلاح FILTER_SCOPE]** أهم تصحيح في هذا الملف — قبل الإصلاح كان كل subclass (raw/machine/labor_op/machine_op) يعرض **كل** التصنيفات بغض النظر عن نوعه الفعلي، بسبب `FILTER_SCOPE = "all"` الثابت القديم.
- **[توحيد الجداول]** `STRETCH_COL = -1` بدل `1` — تصحيح مركزي واحد ينعكس تلقائياً على كل الجداول الوارثة (بدل تكراره يدوياً في كل subclass).
- الكلاس يعتمد على وجود عمود أول (index 0) يحمل الـ ID دائماً، ويُخفيه تلقائياً بعد البناء (`setColumnHidden(0, True)`) — الـ `TABLE_COLS` في الوريث يجب أن يتضمن عمود ID وهمي في البداية.
- التلوين (مشترك/منشور) مستقل تماماً عن منطق `_fill_table_row` الخاص بالوريث — لا حاجة أن يتعامل الوريث مع الألوان بنفسه، `_apply_row_colors` تُستدعى تلقائياً بعد `_fill_table_row` في كل صف.

---

## علاقات الملفات

- `list_panel_with_shared.py` (`SharedItemsListPanel`) يرث من ثلاثة مصادر:
  - `BaseListPanel` من `base/list_panel.py` (مرجع: `ui_widgets_base.md`) — القاعدة الأساسية لكل منطق الجدول/الفلترة/الـ pagination.
  - `SharedOpsMixin` من `mixins/shared_ops.py` (مرجع: `ui_widgets_mixins.md`) — يوفّر `_edit_shared_item`, `_edit_published_item`, `_publish_item` المُستخدَمة مباشرة في معالجات الأزرار هنا.
  - `LiveConnMixin` من `core/conn.py` (مرجع: `ui_widgets_core.md`) — يوفّر `_live_conn()` الموروثة بدون أي override محلي.
- يستورد `confirm_delete` من `dialogs/confirm.py` (مرجع: `ui_widgets_dialogs.md`) — وإن لم يظهر استخدام مباشر له داخل الكود المرفق نفسه (متاح للوريث عبر `self`).
- يستورد `FilterToolbar` من `panels/filter.py` (مرجع: `ui_widgets_panels.md`) داخل `_build_filter()` (استيراد محلي داخل الدالة).
- يعتمد على `ui/tabs/costing/shared/_utils.py` (`SHARED_COLOR`, `SHARED_BG`, `PUBLISHED_COLOR`, `PUBLISHED_BG`) و `ui/tabs/companies/shared_items_mixin.py` (`get_published_local_names`) — كلاهما خارج نطاق `ui/widgets/` بالكامل (تحت `ui/tabs/`)، وليسا موثَّقين في أي مرجع من مراجع `ui/widgets/*`.
- لا علاقة استيراد مباشرة بين هذا الملف و `managers/category.py` (مرجع: `ui_widgets_managers.md`) رغم القرب الوظيفي (كلاهما يتعامل مع بيانات مشتركة/تصنيفات) — كل منهما يعتمد على `CategoryService`/`FilterToolbar` بشكل مستقل تماماً.
