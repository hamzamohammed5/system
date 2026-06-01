# دليل الكود — DB: التسعير (db/pricing/)

> جداول التسعير والعروض في `erp.db`.

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
# [تحسين 23b] يدعم pagination — القيمة الافتراضية limit=500 تحمي من تحميل آلاف الصفوف
# يرجع المنتجات النهائية مع بيانات التسعير
# الأعمدة: id, name, category_id, category_name, category_color,
#           pricing_id, margin, price

fetch_pricing_count(conn) -> int
# [تحسين 23b] إجمالي عدد المنتجات النهائية — للـ UI pagination

fetch_all_pricing_paginated(conn, limit=200, offset=0,
                             category_id=None, search=None,
                             only_priced=False) -> list
# [تحسين 23b] pagination كاملة مع فلترة
# only_priced=True → المنتجات التي لها سعر فقط

fetch_pricing(conn, item_id) -> row | None
# id, item_id, margin, price

upsert_pricing(conn, item_id, margin, price)
# [تحسين 23] يتحقق أن المنتج موجود ونوعه 'final' قبل الحفظ
# Raises: ValueError لو غير موجود أو نوعه ليس final

delete_pricing(conn, item_id)
```

**مثال pagination في الـ UI:**
```python
total   = fetch_pricing_count(conn)
rows    = fetch_all_pricing(conn, limit=200, offset=0)
if total > len(rows):
    label.setText(f"يعرض {len(rows)} من أصل {total} منتج")
```

---

## offers_repo.py

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

#### CRUD — offers

```python
fetch_all_offers(conn) -> list
# مع category_name و category_color من JOIN
fetch_offer(conn, offer_id) -> row
insert_offer(conn, name, discount, notes="", category_id=None) -> int
update_offer(conn, offer_id, name, discount, notes="", category_id=None)
delete_offer(conn, offer_id)
```

#### CRUD — offer_items

```python
fetch_offer_items(conn, offer_id) -> list
# مع item_name, item_type, category_name من JOIN
replace_offer_items(conn, offer_id, items: list[tuple])
# items: [(item_id, qty), ...]
```

#### حساب ملخص العرض

```python
calc_offer_summary(conn, offer_id) -> dict
```

**المنطق:**
- `listed_price` = سعر التسعير × الكمية
- `sell_price` = listed_price × (1 - discount/100)
- `cost` = تكلفة الإنتاج × الكمية
- `profit` = sell_price - cost

**التحسينات:**
- **[تحسين 14]** cost_cache — كل item_id يُحسب مرة واحدة فقط
- **[P-02]** central_conn مشترك لكل الحسابات — لا فتح/غلق متكرر، يُغلق في finally

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

- التسعير مخصص للمنتجات النهائية فقط (`type='final'`) — `upsert_pricing` يرفض غيرها.
- `calc_offer_summary` يستخدم `models.costing.calc_cost` داخلياً.
- استخدم `fetch_all_pricing_paginated` للتحكم الكامل في الصفحات والفلترة.