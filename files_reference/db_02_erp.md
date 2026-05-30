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
# يُهيئ companies.db فقط الآن

_init_erp_db(conn)
# يُهيئ erp.db — ينشئ: categories, items, machines, labor_ops,
#   machine_ops, bom, settings
```

**القيم الافتراضية في `settings` (كلها TEXT):**

| المفتاح | القيمة |
|---------|--------|
| `monthly_salary` | 3000 |
| `working_days` | 25 |
| `holiday_days` | 4 |
| `working_hours_day` | 8 |
| `overhead_factor` | 1.10 |
| `font_size` | 11 |

**جداول erp.db:**

| الجدول | الأعمدة الرئيسية |
|--------|-----------------|
| `categories` | `id, name, scope, color, parent_id, template_fields, default_unit` |
| `items` | `id, name, type["raw"\|"semi"\|"final"], price, total_qty, category_id` |
| `machines` | `id, name, rate_per_hour, rate_per_unit, category_id` |
| `labor_ops` | `id, name, minutes, category_id` |
| `machine_ops` | `id, machine_id, name, mode["time"\|"unit"], value, category_id` |
| `bom` | `id, parent_id, child_type, child_id, qty, child_name, waste_pct?, variant_id?, machine_op_row_id?, scenario_id?` |
| `settings` | `key TEXT PK, value TEXT` ← value كـ TEXT (ليس REAL) |

> ⚠️ `settings` يخزن كل القيم كـ TEXT — استخدم `float(get_setting(...))` عند قراءة الأرقام.