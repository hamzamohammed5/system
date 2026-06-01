# دليل الكود — DB (2): ERP (erp.db)

> جداول `erp.db` — التكلفة، الأصناف، التصنيفات، الإعدادات.
> ملفات `db/shared/` (items_repo, categories_repo, settings_repo) → راجع `db_07_shared.md`

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [schema](#schema) | `db/costing/schema.py` |

---

## schema

### `db/costing/schema.py`

```python
init_db()
# يُهيئ companies.db فقط (للتوافق) — يستدعي create_central_tables
# لا ينشئ erp.db مباشرة في وضع multi-company

_init_erp_db(conn)
# يُهيئ erp.db من connection جاهز
# يُستدعى من companies_repo._init_company_databases() عند إنشاء شركة جديدة

_migrate_erp_db(conn)
# Migrations آمنة للشركات الموجودة:
#   [إصلاح 3] يضيف total_qty لجدول items لو ناقص
#   [إصلاح 4] يُنشئ جدول categories لو ناقص
#   [إصلاح 5] لا يغير نوع value في settings (SQLite يقبل TEXT لكل القيم)
```

**القيم الافتراضية في `settings` (كلها TEXT):**

| المفتاح | القيمة الافتراضية |
|---------|-----------------|
| `monthly_salary` | `"3000.0"` |
| `working_days` | `"25.0"` |
| `holiday_days` | `"4.0"` |
| `working_hours_day` | `"8.0"` |
| `overhead_factor` | `"1.10"` |
| `font_size` | `"11.0"` |

> ⚠️ القيم تُدرج بـ `INSERT OR IGNORE` — لن تُعيد كتابة قيم موجودة.

**جداول erp.db:**

| الجدول | الأعمدة الرئيسية |
|--------|-----------------|
| `categories` | `id, name, scope DEFAULT "all", color DEFAULT "#607d8b", parent_id→SET NULL, template_fields TEXT, default_unit DEFAULT "mm"` |
| `items` | `id, name, type CHECK("raw"\|"semi"\|"final"), price DEFAULT 0, total_qty REAL, category_id→SET NULL` |
| `machines` | `id, name, rate_per_hour DEFAULT 0, rate_per_unit DEFAULT 0, category_id→SET NULL` |
| `labor_ops` | `id, name, minutes DEFAULT 0, category_id→SET NULL` |
| `machine_ops` | `id, machine_id→CASCADE, name, mode CHECK("time"\|"unit"), value DEFAULT 0, category_id→SET NULL` |
| `bom` | `id, parent_id→CASCADE, child_type CHECK("raw"\|"semi"\|"labor_op"\|"machine_op"), child_id, qty DEFAULT 1, child_name TEXT` |
| `settings` | `key TEXT PRIMARY KEY, value TEXT NOT NULL DEFAULT ""` |

> ⚠️ **ترتيب الإنشاء مهم [إصلاح 4]:** `categories` يُنشأ أولاً لأن بقية الجداول تحتوي `REFERENCES categories(id)`.

> ⚠️ `settings.value` عمود TEXT — استخدم `float(get_setting(...))` عند قراءة الأرقام [إصلاح 5].

> ⚠️ جدول `bom` الأساسي لا يحتوي أعمدة `waste_pct`, `variant_id`, `machine_op_row_id`, `scenario_id` — تُضاف عبر migrations في `bom_scenarios_repo.py`. استخدم `_get_bom_cols(conn)` للتحقق.