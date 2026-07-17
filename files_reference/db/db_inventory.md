# دليل الكود — DB: المخزن (db/inventory/) — نسخة محدَّثة

> جداول `inventory.db` — أصناف المخزن، التصنيفات، الحركات.
> **الملفات الفعلية:** `inventory_schema.py`, `inventory_repo.py`
> **آخر تحديث:** يعكس الكود الفعلي في السياق.

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
#   inventory_moves      — حركات المخزن  ← الاسم الصحيح للجدول
```

**هيكل الجداول:**

| الجدول | الأعمدة الرئيسية |
|--------|-----------------|
| `inventory_categories` | `id, name, color DEFAULT '#607d8b', notes` |
| `inventory_items` | `id, name, unit DEFAULT 'قطعة', category_id→SET NULL, qty_on_hand DEFAULT 0, qty_min DEFAULT 0, avg_cost DEFAULT 0, costing_item_id, account_code DEFAULT '114', notes, created_at` |
| `inventory_moves` | `id, inventory_id→CASCADE, move_type CHECK('in'\|'out'\|'adjust'), qty, unit_cost DEFAULT 0, total_cost DEFAULT 0, date, ref_entry_id, ref_entry_no, notes, created_at` |

**ربط المخزن بالمحاسبة:**
- `ref_entry_id` → يُشير لـ `journal_entries.id` في `accounting.db` (بدون FK عبر DBs مختلفة — يُتحقق manually)
- `ref_entry_no` → رقم القيد للعرض فقط
- `account_code` → كود الحساب في `accounting.db` (افتراضي `'114'`)
- `costing_item_id` → ربط اختياري بـ `items` في `erp.db`

**ملاحظة على ربط الجداول:**
```
inventory.db  ─── ref_entry_id ──→  accounting.db (journal_entries.id)  [بدون FK]
inventory.db  ─── costing_item_id → erp.db (items.id)                   [بدون FK]
```
لا توجد FOREIGN KEYs عبر قواعد بيانات مختلفة — التحقق يتم يدوياً في كود التطبيق.

---

## inventory_repo.py

> ⚠️ **تنبيه اسم الجدول:** `inventory_repo.py` يستخدم جدول `inventory_moves`.
> `InventoryService` في `services/inventory/inventory_service.py` يستخدم جدول `inventory_movements` (اسم مختلف).
> للوصول للبيانات الفعلية استخدم `inventory_repo.py` مباشرة.

### تصنيفات المخزن

```python
fetch_all_inv_categories(conn) -> list
# id, name, color, notes — ORDER BY name

insert_inv_category(conn, name: str, color: str = '#607d8b',
                    notes: str = None) -> int

delete_inv_category(conn, cat_id: int)
# CASCADE تلقائي: يُحدِّث category_id=NULL في inventory_items
```

### أصناف المخزن

```python
fetch_all_inventory(conn) -> list
# مع total_value = qty_on_hand × avg_cost
# مع category_name و category_color من LEFT JOIN
# الأعمدة: id, name, unit, qty_on_hand, qty_min, avg_cost, notes,
#           costing_item_id, account_code, category_id,
#           total_value, category_name, category_color

fetch_inventory_item(conn, inv_id: int) -> row
# SELECT * FROM inventory_items WHERE id=?

insert_inventory_item(conn, name: str, unit: str = 'قطعة',
                       qty_min: float = 0,
                       account_code: str = '114',
                       category_id: int = None,
                       costing_item_id: int = None,
                       notes: str = None) -> int
# qty_on_hand و avg_cost لا يُدخَلان يدوياً — تُحسب بـ record_inventory_move

update_inventory_item(conn, inv_id: int, name: str, unit: str,
                       qty_min: float,
                       account_code: str = '114',
                       category_id: int = None,
                       notes: str = None)
# لا يُعدّل qty_on_hand أو avg_cost مباشرة

delete_inventory_item(conn, inv_id: int)
# CASCADE على inventory_moves
```

### حركات المخزن

> جدول الحركات الفعلي: `inventory_moves` (وليس `inventory_movements`)

```python
fetch_inventory_moves(conn, inv_id: int) -> list
# ORDER BY date DESC, id DESC
# الأعمدة: id, inventory_id, move_type, qty, unit_cost, total_cost,
#           date, ref_entry_id, ref_entry_no, notes, created_at

fetch_recent_moves(conn, move_type: str = None, limit: int = 100) -> list
# مع item_name و unit من JOIN inventory_items
# move_type=None → كل الأنواع | مع فلتر → WHERE im.move_type=?
# ORDER BY date DESC, id DESC

fetch_recent_moves_with_item_names(conn, move_type: str, limit: int = 100) -> list
# [إصلاح هيكلي] نُقلت من services/inventory/inventory_service.py (كانت SQL خام
# self.conn.execute مباشرة داخل الـ service) إلى هنا — كل SQL يجب أن يعيش في db/ فقط.
# نسخة أضيق من fetch_recent_moves: تجلب فقط
#   date, name (اسم الصنف), qty, unit_cost, total_cost, ref_entry_no, notes
# JOIN inventory_items | WHERE move_type=? | ORDER BY date DESC, id DESC LIMIT ?
# تُستخدم في جداول "آخر الحركات" بتبويبات الوارد والصادر
# Try/except: يرجع [] بصمت عند أي خطأ

record_inventory_move(conn, inv_id: int, move_type: str,
                       qty: float, unit_cost: float, date: str,
                       notes: str = None,
                       ref_entry_id: int = None,
                       ref_entry_no: str = None) -> int
# يسجل الحركة + يُحدِّث qty_on_hand و avg_cost تلقائياً
# Raises: ValueError لو inv_id غير موجود
```

**سلوك `record_inventory_move` حسب النوع:**

| `move_type` | الحساب | الشرط |
|-------------|--------|-------|
| `'in'` | WACC: `new_avg = (old_qty×old_avg + qty×unit_cost) / new_qty` | — |
| `'out'` | `unit_cost = old_avg` (يتجاهل unit_cost المُدخَل) | `qty <= old_qty + 0.0001` وإلا ValueError |
| `'adjust'` | يضع qty مباشرة كـ qty_on_hand | **[تحسين 20] `qty < 0` → ValueError** |

**حساب `avg_cost` (WACC) للوارد بالتفصيل:**
```python
total_cost = qty * unit_cost
new_qty    = old_qty + qty
new_avg    = (old_qty * old_avg + total_cost) / new_qty  # لو new_qty > 0
# لو new_qty == 0 → new_avg = unit_cost
```

**تفاصيل حالة `'out'`:**
```python
new_qty    = max(0.0, old_qty - qty)
new_avg    = old_avg          # المتوسط لا يتغير عند الصرف
total_cost = qty * old_avg    # تكلفة الصرف بالمتوسط الحالي
unit_cost  = old_avg          # يُحدَّث تلقائياً بالمتوسط
```

**تفاصيل حالة `'adjust'`:**
```python
# [تحسين 20] إذا qty < 0 → raises ValueError:
# "كمية التسوية لا يمكن أن تكون سالبة. للتعديل لكمية أقل استخدم حركة صادر بدلاً من ذلك."
new_qty    = qty              # يضع الكمية الجديدة مباشرة (ليست تغييراً)
new_avg    = old_avg          # المتوسط يبقى كما هو
total_cost = abs(qty - old_qty) * old_avg  # فرق التسوية
```

---

## ملاحظات مهمة

- `avg_cost` يُحسب تلقائياً في `record_inventory_move()` — لا تعدّله يدوياً.
- للتعديل لكمية **أقل**: استخدم `move_type='out'` بدلاً من `adjust` بكمية سالبة [تحسين 20].
- `move_type='adjust'` يضبط الكمية مطلقاً (رصيد جديد كامل، ليس فرق).
- `inventory.db` منفصل عن `accounting.db` — الربط عبر `ref_entry_id` بدون FK.
- `costing_item_id` اختياري — للربط مع `erp.db` عند الحاجة لحساب التكاليف.
- **جدول الحركات الفعلي هو `inventory_moves`** في `inventory_repo.py`.
- `InventoryService` يستخدم `inventory_movements` (اسم مختلف) — استخدم `inventory_repo.py` مباشرة للدقة.
---

## من يستخدم هذا المسار (db/inventory/) من خارجه

- `services/inventory/inventory_service.py` — المستهلك الوحيد المسموح به (مبدأ عزل صريح موثّق)
- `db/accounting/accounting_inventory_repo.py` — يستدعي `record_inventory_move()` من `inventory_repo` مباشرة كجزء من عملية الشراء المزدوجة (`acc_conn` + `inv_conn`)
- لا يجوز لأي ملف آخر (tabs أو services أخرى) استدعاء `inventory_repo` مباشرة
