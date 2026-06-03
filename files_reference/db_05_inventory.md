# دليل الكود — DB: المخزن (db/inventory/)

> جداول `inventory.db` — أصناف المخزن، التصنيفات، الحركات.
> **الملفات الفعلية:** `inventory_schema.py`, `inventory_repo.py`

---

## فهرس

| الملف | الوصف |
|-------|-------|
| [inventory_schema.py](#inventory_schemapy) | إنشاء جداول inventory.db |
| [inventory_repo.py](#inventory_repopy) | CRUD الأصناف والحركات |

---

## inventory_schema.py

```python
create_inventory_tables(conn)
# ينشئ في inventory.db:
#   inventory_categories — تصنيفات المخزن
#   inventory_items      — أصناف المخزن
#   inventory_moves      — حركات المخزن
```

**هيكل الجداول:**

| الجدول | الأعمدة الرئيسية |
|--------|-----------------|
| `inventory_categories` | `id, name, color DEFAULT "#607d8b", notes` |
| `inventory_items` | `id, name, unit DEFAULT "قطعة", category_id→SET NULL, qty_on_hand DEFAULT 0, qty_min DEFAULT 0, avg_cost DEFAULT 0, costing_item_id, account_code DEFAULT "114", notes, created_at` |
| `inventory_moves` | `id, inventory_id→CASCADE, move_type CHECK("in"\|"out"\|"adjust"), qty, unit_cost DEFAULT 0, total_cost DEFAULT 0, date, ref_entry_id, ref_entry_no, notes, created_at` |

**ربط المخزن بالمحاسبة:**
- `ref_entry_id` → يُشير لـ `journal_entries.id` في `accounting.db` (بدون FK عبر DBs مختلفة — يُتحقق manually)
- `ref_entry_no` → رقم القيد للعرض فقط
- `account_code` → كود الحساب في `accounting.db` (افتراضي `"114"`)
- `costing_item_id` → ربط اختياري بـ `items` في `erp.db`

---

## inventory_repo.py

### تصنيفات المخزن

```python
fetch_all_inv_categories(conn) -> list
# id, name, color, notes — ORDER BY name

insert_inv_category(conn, name, color="#607d8b", notes=None) -> int
delete_inv_category(conn, cat_id)
```

### أصناف المخزن

```python
fetch_all_inventory(conn) -> list
# مع total_value = qty_on_hand × avg_cost
# مع category_name و category_color من JOIN

fetch_inventory_item(conn, inv_id) -> row
# SELECT * FROM inventory_items

insert_inventory_item(conn, name, unit="قطعة", qty_min=0,
                      account_code="114", category_id=None,
                      costing_item_id=None, notes=None) -> int

update_inventory_item(conn, inv_id, name, unit, qty_min,
                      account_code="114", category_id=None, notes=None)

delete_inventory_item(conn, inv_id)
# CASCADE على inventory_moves
```

### حركات المخزن

```python
fetch_inventory_moves(conn, inv_id: int) -> list
# ORDER BY date DESC, id DESC

fetch_recent_moves(conn, move_type: str = None, limit: int = 100) -> list
# مع item_name و unit من JOIN
# move_type=None → كل الأنواع

record_inventory_move(conn, inv_id, move_type, qty, unit_cost, date,
                      notes=None, ref_entry_id=None, ref_entry_no=None) -> int
```

**سلوك `record_inventory_move` حسب النوع:**

| `move_type` | السلوك |
|-------------|--------|
| `"in"` | يحسب `avg_cost` الجديد بـ WACC: `(old_qty × old_avg + total_cost) / new_qty` |
| `"out"` | يتحقق `qty <= old_qty + 0.0001` — ValueError لو تجاوز — `unit_cost = old_avg` |
| `"adjust"` | يضع `qty` مباشرة كـ qty_on_hand — **[تحسين 20] ValueError لو `qty < 0`** |

**حساب `avg_cost` (WACC) للوارد:**
```python
new_qty = old_qty + qty
new_avg = ((old_qty * old_avg) + (qty * unit_cost)) / new_qty
# لو new_qty == 0 → new_avg = unit_cost
```

---

## ملاحظات

- `avg_cost` يُحسب تلقائياً في `record_inventory_move()` — لا تحسبه يدوياً.
- للتعديل لكمية أقل في `adjust`: استخدم `move_type="out"` بدلاً من كمية سالبة [تحسين 20].
- `inventory.db` منفصل عن `accounting.db` — الربط عبر `ref_entry_id` بدون FK.
- `move_type="adjust"` يضبط الكمية مطلقاً (ليست تغييراً نسبياً).