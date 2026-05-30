# دليل الكود — DB (7): أدوات مشتركة

> `db/shared/` — الاتصالات، JSON، جسر العناصر المشتركة.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [connection](#connection) | `db/shared/connection.py` |
| [json_utils](#json_utils) | `db/shared/json_utils.py` |
| [shared_items_bridge](#shared_items_bridge) | `db/shared/shared_items_bridge.py` |

---

## connection

### `db/shared/connection.py`

```python
get_central_connection() -> sqlite3.Connection

get_connection(db="erp") -> ProtectedConnection
# db: "erp" | "accounting" | "inventory" | "orders" | "designs"
# ⚠️ يرمي RuntimeError لو لا توجد شركة نشطة
# "costing" مُهمَل [إصلاح 10] → DeprecationWarning + يُحوَّل لـ "erp"
```

> ⚠️ **[T-03]** `get_costing_connection()` محذوفة — ImportError واضح.
> البديل: `company_state.get_erp_conn()` أو `get_connection("erp")`

```python
get_accounting_connection() -> ProtectedConnection
get_inventory_connection() -> ProtectedConnection

get_linked_connection(primary="inventory", attach=None) -> sqlite3.Connection
# connection مع ATTACH لـ DBs إضافية للـ JOIN
```

---

## json_utils

### `db/shared/json_utils.py`

```python
decode_json(data_str: str) -> dict        # JSON → dict | {} عند الفشل
encode_json(data: dict) -> str            # dict → JSON | "{}"
decode_json_list(data_str: str) -> list   # JSON → list | []
encode_json_list(data: list) -> str       # list → JSON | "[]"
# [تحسين 13] مُستخدمة في categories_repo لـ template_fields
```

---

## shared_items_bridge

### `db/shared/shared_items_bridge.py`

```python
SharedItemsBridge(company_id: int)
# [إصلاح 33] يستخدم decode_json/encode_json من json_utils
# [A-02] is_shared_id و extract_shared_id مُعادان تصديرهما من items_repo

bridge.fetch_shared_items_for_type(shared_type) -> list
bridge.fetch_items_by_type_with_shared(item_type) -> list
bridge.fetch_shared_item_as_row(shared_item_id, shared_type=None) -> dict | None
bridge.update_shared_item(shared_item_id, name, data: dict)
bridge.link_shared_item(shared_item_id)
bridge.unlink_shared_item(shared_item_id)
bridge.is_linked(shared_item_id) -> bool
bridge.batch_link(shared_item_ids: list)
bridge.batch_unlink(shared_item_ids: list)
bridge.calc_shared_raw_unit_price(shared_item_id) -> float

get_bridge() -> SharedItemsBridge | None

# re-exports من items_repo [A-02]:
is_shared_id(item_id) -> bool
extract_shared_id(item_id) -> int | None
```

---

## ملاحظات عامة DB

**1. ترتيب الإنشاء:** `categories` يجب أن يُنشأ أولاً في schema [إصلاح 4].

**2. العناصر المشتركة:** IDs بصيغة `"shared:{n}"` (string) — تحقق دائماً بـ `is_shared_id()` من `db.shared.items_repo` [A-02].

**3. الـ connections:** لا تُغلق `ProtectedConnection` مباشرة — اتركها للـ `company_state`. فقط `get_central_connection()` تحتاج `.close()`.

**4. BOM columns cache:** استدعِ `invalidate_bom_cols_cache(conn)` بعد أي migration يضيف أعمدة لجدول bom.

**5. SQLite type affinity:** جدول `settings` يخزن كل القيم كـ TEXT — استخدم `float(get_setting(...))` عند الحاجة [إصلاح 5].

**6. الـ accounting.db:** تحقق من `_verify_conn_is_accounting()` قبل أي seed أو write لتجنب الكتابة على `erp.db` بالخطأ [إصلاح 9 + 11 + Q-01].

**7. الـ WACC:** حساب `avg_cost` في المخزن تلقائي في `record_inventory_move()` — لا تحسبه يدوياً.

**8. Thread Safety:** `CompanyState.set_active()` آمن للـ threads عبر `_invalidate_pending` Event [C-03]. استخدم `company_state.wait_for_invalidate()` من AppState قبل قراءة الـ cache.

**9. Central Connection Cache:** `_get_central_conn_cached()` في `items_repo` يُقلّص فتح/غلق connections المتكرر. يُبطَل تلقائياً عند تغيير الشركة [تحسين 8].

**10. Migration Framework (orders.db):** كل migration يجب أن يكون idempotent. يُسجَّل في `schema_migrations` ويتخطى المُطبَّق [تحسين 25].