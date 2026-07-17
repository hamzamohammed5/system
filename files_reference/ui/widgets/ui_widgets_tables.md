# دليل الكود — UI / Widgets (6): Tables

> `ui/widgets/tables/` — أدوات بناء الجداول الموحدة.
>
> ⚠️ **[تقسيم]** هذا المرجع كان يغطي سابقاً `tables/` و `utils/` معاً في
> ملف واحد. حسب قاعدة "مرجع واحد = مسار واحد"، تم فصل `utils/` إلى مرجع
> مستقل: **`ui_widgets_utils.md`**.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [Tables](#tables) | `tables/tables.py` |
| [Tables — Flexible](#tables--flexible) | `tables/flexible.py` |

---

## Tables

### `ui/widgets/tables/tables.py`

> دُمج `tables/builders.py` و `tables/items.py` في هذا الملف.

```python
# ── أدوات خلايا الجداول ──
make_item(text="", user_data=None, align=None, tooltip=None) -> QTableWidgetItem
bold_item(text, color=None, align=None, user_data=None, tooltip=None) -> QTableWidgetItem
colored_item(text, color, align=None, user_data=None, tooltip=None) -> QTableWidgetItem
center_item(text, color=None, bold=False, user_data=None) -> QTableWidgetItem
muted_item(text: str) -> QTableWidgetItem   # لون _C['text_muted']

insert_row(table, height=ROW_HEIGHT_NORMAL) -> int
set_row_bg(table, row, color)
apply_row_height(table, height=ROW_HEIGHT_NORMAL)
calc_width(table, extra_pad=4) -> int
auto_fit_columns(table, fixed_cols=None, stretch_col=-1, min_width=40, max_width=300)
apply_tooltips(table, cols=None)

# ── بناء الجداول ──
make_table(columns, stretch_col=-1, col_widths=None,
           max_height=None, min_height=100,
           row_height=ROW_HEIGHT_NORMAL) -> QTableWidget

make_compact_table(columns, stretch_col=-1, col_widths=None,
                   max_height=200) -> QTableWidget

make_list_table(columns, stretch_col=-1, col_widths=None) -> QTableWidget
# border:none, border-radius:0 — للـ panels

make_fixed_table(columns, col_widths: dict, max_height=None,
                 min_height=60, row_height=ROW_HEIGHT_NORMAL) -> QTableWidget

make_splitter_table(columns, ..., extra_pad=20) -> tuple[QSplitter, QTableWidget]
make_splitter_table_guarded(columns, ...) -> tuple[QSplitter, QTableWidget, SplitterScrollGuard]

fit_splitter_table(splitter, table, extra_pad=20, delay_ms=0)
# المصدر الوحيد لمنطق ضبط عرض الـ splitter حسب عرض الجدول

refresh_table_styles(root_widget) -> int
# [Fix - dark theme tables] يُعيد تطبيق table_style() على كل QTableWidget
# في شجرة الـ widget اللي عليها Qt property "_table_variant" (أي جدول
# مبني عبر make_table/make_list_table/make_fixed_table/make_splitter_table).
# المشكلة: _build_table() كانت تطبّق table_style(variant) مرة واحدة فقط
# وقت الإنشاء؛ أي widget أب لا يعمل setStyleSheet(table_style()) بنفسه
# داخل _refresh_style() الخاصة به كان يبقى بستايل الثيم القديم (غالباً
# فاتح) حتى بعد التحويل لـ dark.
# الحل: يُستدعى من _refresh_style() الخاصة بأي widget أب بدل ما كل
# widget يكرر الكود يدوياً:
#     def _refresh_style(self, *_):
#         from ui.widgets.tables.tables import refresh_table_styles
#         refresh_table_styles(self)
# يرجع عدد الجداول المُحدَّثة. يتجاهل RuntimeError (widget محذوف) بصمت.

ROW_HEIGHT_COMPACT = 34
ROW_HEIGHT_NORMAL  = 40
ROW_HEIGHT_LARGE   = 48
```

---

## Tables — Flexible

### `ui/widgets/tables/flexible.py`

```python
make_flexible_table(columns, stretch_col=-1, wrap_cols=None,
                    min_row_height=32) -> QTableWidget

set_flexible_columns(table, wrap_cols=None, min_row_height=32)

FlexItem(text="", tooltip=None) -> QTableWidgetItem
# tooltip تلقائي = النص

WrapDelegate(parent=None, min_row_height=28, padding=6)
# word-wrap في خلايا الجدول

AutoTooltipDelegate(parent=None)
# tooltip تلقائي بالنص الكامل

FlexibleTreeWidget(parent=None)
  .setWrapColumn(col: int)
  .addFlexibleItem(parent_item, texts: list, tooltips: list = None) -> QTreeWidgetItem
```

> **ملاحظة:** `refresh_tooltips` لا يُعاد تصديره من هنا — استورد مباشرة:
> `from ui.widgets.utils.tooltip import refresh_tooltips`

## علاقات الملفات

- `tables.py` هو المصدر الوحيد لمنطق ضبط عرض الـ splitter حسب عرض الجدول (`fit_splitter_table`) — `flexible.py` لا يعتمد عليه.
- `flexible.py` مستقل عن `tables.py` — يوفر Delegates إضافية (`WrapDelegate`, `AutoTooltipDelegate`) تُستخدم فوق جداول مبنية بـ `tables.py` عبر `set_flexible_columns()`.
- `tables.py` يستخدم `refresh_table_styles()` (دالة مركزية) لإعادة تطبيق `table_style()` على كل QTableWidget في شجرة widget عند تغيير الثيم — بديل عن كل widget يكتب `self.table.setStyleSheet(table_style())` يدوياً في `_refresh_style()` الخاصة به.
- كلا الملفين يعتمدان على `theme/table_styles.py` (مرجع: `ui_widgets_theme.md`) لكل الألوان.
- `utils/splitter.py` (مرجع: `ui_widgets_utils.md`) يستورد `calc_width` من هذا الملف (`tables.py`) — تبعية عكسية من `utils/` على `tables/`.
