# دليل الكود — DB: التسعير (db/pricing/)

> جداول التسعير والعروض في `erp.db`.
> **الملفات الفعلية:** `pricing_repo.py`, `offers_repo.py`

---

## فهرس

| الملف | الوصف |
|-------|-------|
| [pricing_repo.py](#pricing_repopy) | CRUD التسعير مع pagination |
| [offers_repo.py](#offers_repopy) | CRUD العروض وحساب ملخصها |

---

## pricing_repo.py

```python
fetch_all_pricing(conn, limit=500, offset=0) -> list
# [تحسين 23b] pagination — القيمة الافتراضية limit=500
# WHERE i.type = 'final' | ORDER BY i.name
# الأعمدة: id, name, category_id, category_name, category_color,
#           pricing_id, margin, price

fetch_pricing_count(conn) -> int
# [تحسين 23b] COUNT(*) WHERE type = 'final' — للـ UI pagination

fetch_all_pricing_paginated(conn, limit=200, offset=0,
                             category_id=None, search=None,
                             only_priced=False) -> list
# فلترة ديناميكية: category_id, search LIKE, only_priced

fetch_pricing(conn, item_id) -> row | None
# id, item_id, margin, price

upsert_pricing(conn, item_id, margin, price)
# [تحسين 23] يتحقق أن المنتج موجود ونوعه 'final'
# INSERT OR REPLACE INTO pricing
# Raises: ValueError لو غير موجود أو نوعه ليس final

delete_pricing(conn, item_id)
```

**مثال pagination في الـ UI:**
```python
total = fetch_pricing_count(conn)
rows  = fetch_all_pricing(conn, limit=200, offset=0)
if total > len(rows):
    label.setText(f"يعرض {len(rows)} من أصل {total} منتج")
```

---

## offers_repo.py

### إنشاء الجداول

```python
create_offers_tables(conn)
# ينشئ: offers, offer_items
# يُشغّل _migrate_offers_schema() تلقائياً
```

**هيكل الجداول:**

| الجدول | الأعمدة الرئيسية |
|--------|-----------------|
| `offers` | `id, name, discount DEFAULT 0, notes, created_at, category_id→SET NULL` |
| `offer_items` | `id, offer_id→CASCADE, item_id→CASCADE, qty DEFAULT 1` |

**`_migrate_offers_schema(conn)`:**
```python
# يضيف "discount" لو ناقص
# يضيف "category_id" لو ناقص
```

### CRUD — offers

```python
fetch_all_offers(conn) -> list
# مع category_name و category_color من LEFT JOIN | ORDER BY created_at DESC

fetch_offer(conn, offer_id) -> row
insert_offer(conn, name, discount, notes="", category_id=None) -> int
# created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
update_offer(conn, offer_id, name, discount, notes="", category_id=None)
delete_offer(conn, offer_id)
```

### CRUD — offer_items

```python
fetch_offer_items(conn, offer_id) -> list
# مع item_name, item_type, category_name من JOIN

replace_offer_items(conn, offer_id, items: list[tuple])
# items: [(item_id, qty), ...]
# DELETE القديم → INSERT الجديد
```

### حساب ملخص العرض

```python
calc_offer_summary(conn, offer_id) -> dict
```

**المنطق:**
```python
listed_price = unit_price × qty
sell_price   = listed_price × (1 - discount/100)
cost         = unit_cost × qty  (من calc_cost)
profit       = sell_price - cost
```

**التحسينات:**
- **[تحسين 14]** `cost_cache` — كل `item_id` يُحسب مرة واحدة فقط: `{item_id: cost}`
- **[P-02]** `central_conn` مشترك لكل الحسابات — يُفتح مرة واحدة ويُغلق في finally
- يستخدم `inspect.signature(calc_cost)` للتحقق من دعم `central_conn` قبل تمريره (backward-compatible)

**المُخرج:**
```python
{
    "offer_id", "offer_name", "discount", "notes", "created_at",
    "category_name",
    "lines": [{
        "item_id", "item_name", "item_type", "category_name",
        "qty", "unit_cost", "unit_price",
        "line_cost", "line_listed", "has_pricing"
    }],
    "total_listed", "sell_price", "total_cost", "profit"
}
```

---

## ملاحظات

- التسعير مخصص للمنتجات النهائية فقط (`type='final'`) — `upsert_pricing` يرفض غيرها [تحسين 23].
- `calc_offer_summary` يستخدم `models.costing.calc_cost` داخلياً.
- استخدم `fetch_all_pricing_paginated` للتحكم الكامل في الصفحات والفلترة [تحسين 23b].
- `offers` مخزّن في `erp.db` (نفس قاعدة البيانات الرئيسية للشركة).