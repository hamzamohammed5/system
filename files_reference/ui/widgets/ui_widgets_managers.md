# دليل الكود — UI / Widgets (9): Managers

> `ui/widgets/managers/` — مدير التصنيفات الهرمية.
>
> ⚠️ **[تصحيح تسمية/تقسيم]** كان هذا المرجع يغطي سابقاً `managers/` و
> `shared/` معاً في ملف واحد — مخالفة لقاعدة "مرجع واحد = مسار واحد". تم
> فصل `shared/` إلى **`ui_widgets_shared.md`** المنفصل. هذا الملف يغطي
> `ui/widgets/managers/` فقط.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [CategoryManager + CategoryForm](#categorymanager--categoryform) | `managers/category.py` |

---

## CategoryManager + CategoryForm

### `ui/widgets/managers/category.py`

#### CategoryForm

```python
CategoryForm(conn, scope: str, tree_widget, parent=None)
# QGroupBox — فورم إضافة/تعديل تصنيف واحد
# يشترك في bus.language_changed لتحديث نصوص الـ groupbox والأزرار
# يستخدم CategoryService بدل db imports مباشرة [إصلاح هيكلة]
# [Q-03] _live_conn() مرة واحدة لكل action
```

**API:**
```python
.load_for_edit(cat_id: int)
# يملأ الحقول + يُحدّث cmb_parent (مع استثناء التصنيف وفروعه)
# يُبدّل الأزرار لـ edit mode
# يستخدم: svc.get_one(cat_id) + svc.get_descendants(cat_id)
```

**الحقول:**
- `inp_name` — اسم التصنيف
- `cmb_parent` — التصنيف الأب (هرمي)
- `_color_picker` — `ColorPickerWidget` للاختيار اللوني
- `lbl_mode` — `ModeLabel` يعرض وضع الإضافة/التعديل

**`_refresh_parent_combo(conn=None, exclude_id=None)`:**
```python
# [Q-03] يستقبل conn اختياري بدل استدعاء _live_conn() داخلياً
# لو conn=None → يستدعي self._live_conn() كـ fallback
# [إصلاح هيكلة] يستخدم:
svc   = CategoryService(conn)
rows  = svc.get_all(scope)
tree  = svc.build_tree(rows)
# استبعاد التصنيف وفروعه:
excluded = svc.get_descendants(exclude_id)
```

**العمليات:**
```python
# إضافة (_add) — يستخدم:
CategoryService(conn).add(name, scope, color, parent_id)

# تعديل (_save) — يستخدم:
CategoryService(conn).update(cat_id, name, scope, color, parent_id)

# كل عملية تستدعي _live_conn() مرة واحدة ثم تُطلق emit_company_data_changed()
# لو فشل التحقق (name فارغ) → msg_warning بدون إطلاق إشعار
```

**`_reset(conn=None)`:**
```python
# يمسح الحقول، يُعيد lbl_mode لوضع الإضافة، يُظهر btn_add ويُخفي btn_save/btn_cancel
# يستدعي _refresh_parent_combo(conn=conn) — يمرر نفس الـ conn لتجنب استدعاء _live_conn مرة ثانية
```

#### CategoryManager

```python
CategoryManager(conn, scope="all", parent=None)
# QWidget — شجرة QTreeWidget كاملة لإدارة التصنيفات
# يستمع لـ bus.company_data_changed + bus.language_changed
# يستخدم CategoryService بدل db imports مباشرة [إصلاح هيكلة]
```

**الأعمدة:**
| العمود | المحتوى |
|--------|---------|
| 0 | اسم التصنيف (بلون التصنيف) |
| 1 | عدد التصنيفات الفرعية المباشرة |
| 2 | إجمالي العناصر في التصنيف |

**الأزرار:**
- `btn_edit` — يفتح التصنيف المحدد في CategoryForm
- `btn_del` — يحذف مع تأكيد (confirm_delete) + إظهار warning_text من DeletePreview

**`_load()` — [Q-03] منطق التحميل:**
```python
# _live_conn() مرة واحدة
conn = self._live_conn()

# [إصلاح هيكلة] يستخدم CategoryService:
svc  = CategoryService(conn)
rows = svc.get_all(scope)
tree = svc.build_tree(rows)
```

**`_add_items(nodes, parent, expanded, conn)` — [إصلاح هيكلة]:**
```python
# conn يُمرَّر كـ parameter (نفس الـ connection الذي فتحه _load())
# لا يفتح connection جديد في كل node — تحسين أداء مهم
# يستخدم CategoryService(conn).count_items(node["id"]) لعدد العناصر
```

**`_delete()` — يستخدم:**
```python
svc     = CategoryService(conn)
preview = svc.get_delete_preview(cat_id)
# preview.cat_name, preview.warning_text()
svc.delete_cascade(cat_id)
emit_company_data_changed()
```

**ملاحظات:**
- يحفظ حالة التوسع قبل reload ويُعيدها بعده.
- كل عملية تستدعي `_live_conn()` مرة واحدة وتُمررها للدوال الفرعية [Q-03].
- الـ tree يستخدم `tree_style()` من `..theme.layout_styles`.

---

## علاقات الملفات

- `managers/category.py` (`CategoryForm`, `CategoryManager`) يستخدم `CategoryService` من `services/shared/category_service.py` (خارج نطاق هذا المرجع) لكل عمليات DB — لا استيراد مباشر من `db/`.
- يستخدم `emit_company_data_changed` من `core/events.py` (مرجع: `ui_widgets_core.md`)، `LiveConnMixin` من `core/conn.py`، `ColorPickerWidget` من `helpers/color_picker.py` و `ModeLabel` من `components/label.py` (مرجع: `ui_widgets_components.md`)، و `tree_style()` من `theme/layout_styles.py` (مرجع: `ui_widgets_theme.md`).
- `ui/widgets/shared/list_panel_with_shared.py` (مسار مختلف — مرجع منفصل: `ui_widgets_shared.md`) لا علاقة مباشرة له بـ `managers/category.py`، لكن كلاهما يعتمد على `CategoryService`/`FilterToolbar` بشكل مستقل.