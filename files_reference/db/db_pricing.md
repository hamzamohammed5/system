# دليل الكود — DB: التسعير (db/pricing/) — نسخة محدَّثة

> جداول التسعير والعروض في `erp.db`.
> **الملفات الفعلية:** `pricing_repo.py`, `offers_repo.py`
> **آخر تحديث:** يعكس الكود الفعلي في السياق.

---

## فهرس

| الملف | الوصف |
|-------|-------|
| [pricing_repo.py](#pricing_repopy) | CRUD التسعير مع pagination [تحسين 23b] |
| [offers_repo.py](#offers_repopy) | CRUD العروض وحساب ملخصها |

---

## pricing_repo.py

### قراءة التسعير

```python
fetch_all_pricing(conn, limit: int = 500, offset: int = 0) -> list
# [تحسين 23b] يدعم pagination — القيمة الافتراضية limit=500
# WHERE i.type = 'final' | ORDER BY i.name
# الأعمدة: id, name, category_id, category_name, category_color,
#           pricing_id, margin, price
# pricing_id/margin/price = NULL لو لم يُسعَّر المنتج بعد

fetch_pricing_count(conn) -> int
# [تحسين 23b] SELECT COUNT(*) FROM items WHERE type='final'
# للـ UI pagination — يُعيد إجمالي المنتجات النهائية

fetch_all_pricing_paginated(conn,
                             limit: int = 200,
                             offset: int = 0,
                             category_id: int = None,
                             search: str = None,
                             only_priced: bool = False) -> list
# [تحسين 23b] pagination كاملة مع فلترة ديناميكية
# category_id: فلتر على i.category_id
# search:      LIKE %search% على i.name
# only_priced: لو True → WHERE p.id IS NOT NULL (مسعَّرة فقط)

fetch_pricing(conn, item_id: int) -> row | None
# SELECT id, item_id, margin, price FROM pricing WHERE item_id=?
```

**مثال pagination في الـ UI:**
```python
total = fetch_pricing_count(conn)
rows  = fetch_all_pricing(conn, limit=200, offset=0)
if total > len(rows):
    label.setText(f"يعرض {len(rows)} من أصل {total} منتج")

# للبحث والفلترة:
rows = fetch_all_pricing_paginated(conn,
    limit=100, offset=page*100,
    search=search_text,
    only_priced=True)
```

### كتابة التسعير

```python
upsert_pricing(conn, item_id: int, margin: float, price: float)
# [تحسين 23] يتحقق أن المنتج موجود ونوعه 'final' قبل الحفظ
# INSERT INTO pricing (item_id, margin, price)
# ON CONFLICT(item_id) DO UPDATE SET margin=..., price=...
# Raises: ValueError لو المنتج غير موجود
# Raises: ValueError لو item["type"] != 'final'
#   رسالة: "التسعير متاح للمنتجات النهائية فقط (المنتج رقم N نوعه 'raw')"

delete_pricing(conn, item_id: int)
# DELETE FROM pricing WHERE item_id=?
```

---

## offers_repo.py

### إنشاء الجداول

```python
create_offers_tables(conn)
# CREATE TABLE IF NOT EXISTS offers
# CREATE TABLE IF NOT EXISTS offer_items
# يُشغّل _migrate_offers_schema() تلقائياً

_migrate_offers_schema(conn)
# يضيف "discount" لـ offers لو ناقص
# يضيف "category_id" لـ offers لو ناقص
```

**هيكل الجداول:**

| الجدول | الأعمدة الرئيسية |
|--------|-----------------|
| `offers` | `id, name, discount DEFAULT 0, notes, created_at TEXT, category_id→SET NULL` |
| `offer_items` | `id, offer_id→CASCADE, item_id→CASCADE, qty DEFAULT 1` |

### CRUD — offers

```python
fetch_all_offers(conn) -> list
# مع category_name و category_color من LEFT JOIN categories
# ORDER BY o.created_at DESC
# الأعمدة: id, name, discount, notes, created_at,
#           category_id, category_name, category_color

fetch_offer(conn, offer_id: int) -> row
# مع category_name من LEFT JOIN

insert_offer(conn, name: str, discount: float,
             notes: str = '', category_id: int = None) -> int
# created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

update_offer(conn, offer_id: int, name: str, discount: float,
             notes: str = '', category_id: int = None)

delete_offer(conn, offer_id: int)
# CASCADE على offer_items
```

### CRUD — offer_items

```python
fetch_offer_items(conn, offer_id: int) -> list
# مع item_name, item_type, category_name من JOIN
# ORDER BY oi.id

replace_offer_items(conn, offer_id: int, items: list[tuple])
# items: [(item_id, qty), ...]
# DELETE القديم → INSERT الجديد دفعة واحدة
```

### حساب ملخص العرض

```python
calc_offer_summary(conn, offer_id: int) -> dict
```

**المنطق الحسابي:**
```python
listed_price  = unit_price × qty             # سعر التسعير × الكمية
sell_price    = total_listed × (1 - disc%)   # بعد الخصم
cost          = unit_cost × qty              # تكلفة الإنتاج × الكمية
profit        = sell_price - total_cost      # الربح الصافي
```

**التحسينات:**

**[تحسين 14] cost_cache:**
```python
# كل item_id فريد يُحسَب مرة واحدة فقط:
unique_item_ids = {row["item_id"] for row in items}
cost_cache = {}
for item_id in unique_item_ids:
    cost_cache[item_id] = calc_cost(conn, item_id)
# ثم يُستخدم cost_cache[item_id] لكل صف
```

**[P-02] central_conn مشترك:**
```python
# يُفتح central connection واحد قبل الحلقة
central_conn = get_central_connection()
# يُمرَّر لـ calc_cost كـ central_conn اختياري
# يُغلق في finally بعد انتهاء كل الحسابات
# يُلغي عشرات فتح/غلق connections في العروض الكبيرة

# تحقق من توافق calc_cost مع central_conn:
import inspect
sig = inspect.signature(calc_cost)
if "central_conn" in sig.parameters:
    cost = calc_cost(conn, item_id, central_conn=central_conn)
else:
    cost = calc_cost(conn, item_id)  # backward-compatible
```

**المُخرج الكامل:**
```python
{
    "offer_id":      int,
    "offer_name":    str,
    "discount":      float,   # نسبة مئوية (مثلاً: 10 = 10%)
    "notes":         str,
    "created_at":    str,
    "category_name": str | None,
    "lines": [
        {
            "item_id":       int,
            "item_name":     str,
            "item_type":     str,
            "category_name": str | None,
            "qty":           float,
            "unit_cost":     float,   # من calc_cost
            "unit_price":    float,   # من pricing
            "line_cost":     float,   # unit_cost × qty
            "line_listed":   float,   # unit_price × qty
            "has_pricing":   bool,    # هل المنتج له سعر في جدول pricing
        }
    ],
    "total_listed":  float,  # مجموع line_listed
    "sell_price":    float,  # total_listed × (1 - discount/100)
    "total_cost":    float,  # مجموع line_cost
    "profit":        float,  # sell_price - total_cost
}
```

---

## ملاحظات مهمة

- التسعير مخصص للمنتجات النهائية فقط (`type='final'`) — `upsert_pricing` يرفض غيرها [تحسين 23].
- `fetch_all_pricing_paginated` للتحكم الكامل في الصفحات والفلترة [تحسين 23b].
- `fetch_all_pricing(limit=500)` للتوافق القديم — يُعيد أول 500 فقط.
- `calc_offer_summary` يستخدم `models.costing.calc_cost` داخلياً.
- `offers` مخزَّن في `erp.db` (نفس قاعدة البيانات الرئيسية للشركة).
- `offer_items.item_id` → REFERENCES `items.id` CASCADE — يحذف بنود العرض عند حذف المنتج.
---

## من يستخدم هذا المسار (db/pricing/) من خارجه

- `services/pricing/pricing_service.py` — المستهلك الرئيسي لـ `pricing_repo.py` (القاعدة: `tabs/` ممنوعة من استدعاء `pricing_repo` مباشرة)
- `services/pricing/offers_service.py` — يستورد `offers_repo.py` مباشرة، ويستورد أيضاً `fetch_pricing` من `pricing_repo` مباشرة (تجاوز جزئي موثّق)
- لا يجوز لـ `ui/tabs/` استدعاء أي repo في هذا المسار مباشرة (قاعدة معمارية صارمة موثّقة في رأس كل service)
