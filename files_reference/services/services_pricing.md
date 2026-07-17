# دليل الكود — Services التسعير (services/pricing/)

> `services/pricing/` — تسعير المنتجات النهائية والعروض المبنية عليها.
> **الملفات الفعلية:** `pricing_service.py`, `offers_service.py`

---

## فهرس

| الملف | الوصف |
|-------|-------|
| [pricing_service.py](#pricing_servicepy) | طبقة service للتسعير — CRUD أسعار المنتجات النهائية |
| [offers_service.py](#offers_servicepy) | طبقة service للعروض — CRUD العروض وبنودها وملخصها |

---

## pricing_service.py

### `services/pricing/pricing_service.py`

**الغرض:** طبقة الـ service للتسعير — الوسيط الوحيد بين `tabs/` و`db/pricing/pricing_repo.py`. القاعدة المعمارية الموثّقة صراحة في رأس الملف: `tabs/ → pricing_service → pricing_repo → DB`. **لا يجوز لـ `tabs/` استدعاء `pricing_repo` مباشرةً أبداً** (موثّق كقاعدة صارمة في الكود).

**Imports (top-level):**
```python
from db.pricing.pricing_repo import (
    fetch_all_pricing, fetch_pricing, upsert_pricing, delete_pricing,
)
from db.shared.items_repo import fetch_items_by_type, fetch_item
```

**من يستدعي هذا الملف:** `services/pricing/offers_service.py` (يستورد `fetch_pricing` من `db.pricing.pricing_repo` مباشرة — **لا** يستورد هذا الملف نفسه، راجع قسم علاقات الملفات). متوقع أيضاً من `ui/tabs/pricing/pricing_tab.py`, `ui/tabs/pricing/pricing/_pricing_panel.py` حسب `system_arch.txt` — لكن محتواها غير مرفق.

**ملاحظة بنائية:** هذا الملف **مجموعة دوال top-level مستقلة** — لا يوجد class أو dataclass فيه على الإطلاق، بعكس معظم ملفات `services/` الأخرى.

### دوال top-level مستقلة

- **`get_all_pricing(conn, limit: int = 500, offset: int = 0) -> list`**: يرجع المنتجات النهائية مع بيانات التسعير — عبر `fetch_all_pricing(conn, limit=limit, offset=offset)`.
- **`get_pricing(conn, item_id: int)`**: يرجع سعر منتج واحد أو `None` — عبر `fetch_pricing`.
- **`save_pricing(conn, item_id: int, margin: float, price: float)`**: يحفظ أو يحدّث سعر منتج — عبر `upsert_pricing(conn, item_id, margin, price)`.
- **`remove_pricing(conn, item_id: int)`**: يحذف سعر منتج — عبر `delete_pricing`.
- **`get_final_products(conn) -> list`**: يرجع المنتجات النهائية للـ combo — عبر `fetch_items_by_type(conn, "final")`.
- **`get_item(conn, item_id: int)`**: يرجع بيانات صنف واحد — عبر `fetch_item`.
- **`get_priced_item_ids(conn) -> set`**: يرجع `set` من `item_id` التي لها سعر في جدول `pricing` — **SQL مباشر**: `SELECT item_id FROM pricing` ثم `{r["item_id"] for r in rows}` (الدالة الوحيدة في هذا الملف التي تنفذ SQL مباشرة بدل استدعاء دالة من `pricing_repo`).
- **`get_products_by_type(conn, item_type: str) -> list`**: يرجع الأصناف حسب النوع (`final`/`semi`) — عبر `fetch_items_by_type(conn, item_type)`.

**ملاحظات مهمة من التعليقات:**
- رأس الملف يكرر التحذير المعماري صراحة أن `tabs/` ممنوعة من استدعاء `pricing_repo` مباشرة — هذا الملف هو البوابة الوحيدة.

---

## offers_service.py

### `services/pricing/offers_service.py`

**الغرض:** طبقة الـ service للعروض — الوسيط الوحيد بين `tabs/` و`db/pricing/offers_repo.py`. نفس القاعدة المعمارية الموثّقة صراحة: `tabs/ → offers_service → offers_repo → DB`. **لا يجوز لـ `tabs/` استدعاء `offers_repo` أو `pricing_repo` مباشرةً أبداً** (موثّق كقاعدة صارمة في رأس الملف).

**Imports (top-level):**
```python
from db.pricing.offers_repo import (
    fetch_all_offers, fetch_offer, insert_offer, update_offer, delete_offer,
    fetch_offer_items, replace_offer_items, calc_offer_summary,
)
from db.pricing.pricing_repo import fetch_pricing
from db.shared.items_repo import fetch_items_by_type
from services.pricing.pricing_service import get_priced_item_ids
```

**من يستدعي هذا الملف:** غير محدد بثقة أي ملف UI مباشرة من المرفقات الحالية (متوقع من `ui/tabs/pricing/offers/offers_tab.py`, `offer_form.py`, `offer_details.py`, `offer_item_row.py`, `offers_table.py` حسب `system_arch.txt` — لكن محتواها غير مرفق).

**ملاحظة معمارية:** هذا الملف **يعتمد فعلياً** على `services/pricing/pricing_service.py` — يستورد `get_priced_item_ids` منه مباشرة (composition عبر دالة top-level، وليس عبر class)، بالإضافة لاستيراد `fetch_pricing` مباشرة من `db.pricing.pricing_repo` (تجاوز جزئي لـ `pricing_service.get_pricing` — الملف يصل لنفس الـ repo مباشرة في بعض الحالات بدل المرور عبر `pricing_service`).

**ملاحظة بنائية:** نفس بنية `pricing_service.py` — **مجموعة دوال top-level مستقلة**، لا يوجد class أو dataclass.

### دوال top-level مستقلة

- **`get_all_offers(conn) -> list`**: يرجع كل العروض المحفوظة — عبر `fetch_all_offers`.
- **`get_offer(conn, offer_id: int)`**: يرجع بيانات عرض واحد أو `None` — عبر `fetch_offer`.
- **`create_offer(conn, name: str, discount: float, notes: str = "", category_id: int = None) -> int`**: ينشئ عرضاً جديداً ويرجع الـ `id` — عبر `insert_offer`.
- **`modify_offer(conn, offer_id: int, name: str, discount: float, notes: str = "", category_id: int = None)`**: يحدّث بيانات عرض موجود — عبر `update_offer`.
- **`remove_offer(conn, offer_id: int)`**: يحذف عرضاً بالكامل — عبر `delete_offer`.
- **`get_offer_items(conn, offer_id: int) -> list`**: يرجع بنود عرض معيّن — عبر `fetch_offer_items`.
- **`save_offer_items(conn, offer_id: int, items: list)`**: يستبدل بنود عرض بقائمة جديدة (`item_id`, `qty`) — عبر `replace_offer_items`.
- **`get_offer_summary(conn, offer_id: int) -> dict`**: يرجع ملخص كامل للعرض (تكلفة/سعر/ربح لكل بند + إجماليات) — عبر `calc_offer_summary`.
- **`get_item_price(conn, item_id: int) -> float`**: يرجع سعر عنصر واحد من جدول `pricing`، أو `0.0` لو غير مُسعّر — عبر `fetch_pricing(conn, item_id)` (استيراد مباشر من `pricing_repo`، **وليس** عبر `pricing_service.get_pricing`).
- **`has_pricing(conn, item_id: int) -> bool`**: يتحقق إن كان العنصر له سعر في جدول `pricing` — `fetch_pricing(conn, item_id) is not None`.
- **`get_priced_ids(conn) -> set`**: يرجع `set` من `item_id` التي لها سعر — **facade على `get_priced_item_ids` من `pricing_service.py`** (وليس استدعاءً مباشراً لـ `pricing_repo`).
- **`get_offer_candidate_items(conn, item_type: str) -> list`**: يرجع الأصناف حسب النوع (`final`/`semi`) لعرضها في اختيار منتجات العرض — عبر `fetch_items_by_type`.
- **`get_item_cost(conn, item_id: int) -> float`**: يرجع تكلفة الإنتاج لعنصر واحد — عبر `models.costing.calc_cost` (استيراد **lazy** داخل الدالة، الاستيراد الوحيد غير top-level في هذا الملف).

**ملاحظات مهمة من التعليقات:**
- رأس الملف يكرر التحذير المعماري صراحة أن `tabs/` ممنوعة من استدعاء `offers_repo` أو `pricing_repo` مباشرة.
- `get_item_cost` هو النقطة الوحيدة في هذا الملف التي تعبر لدومين `costing` (عبر `models.costing.calc_cost`، وليس عبر أي `service` في `services/costing/`) — استيراد lazy داخل الدالة لتفادي اعتماد دائري محتمل.

---

## علاقات الملفات

- `offers_service.py` يستورد دالة واحدة من `pricing_service.py` مباشرة: `get_priced_item_ids` (composition على مستوى دالة top-level، وليس عبر instance من class — لأنه لا يوجد class في الأساس في هذا المسار).
- **نمط مشترك:** كلا الملفين لا يحتويان أي class أو dataclass — مجرد دوال top-level تستقبل `conn` كأول معامل صريح في كل استدعاء (بعكس أغلب ملفات `services/` الأخرى التي تتبع نمط `Service(conn)` + methods).
- **نمط مشترك آخر:** كلاهما يكرر نفس التحذير المعماري الصريح في رأس الملف (`tabs/ → service → repo → DB`، ممنوع تجاوز الطبقة).
- تبعية خارج هذا المسار:
  - `pricing_service.py` يعتمد على `db/pricing/pricing_repo.py` و`db/shared/items_repo.py` فقط.
  - `offers_service.py` يعتمد على `db/pricing/offers_repo.py`, `db/pricing/pricing_repo.py` (استيراد جزئي مباشر لـ `fetch_pricing`), `db/shared/items_repo.py`, و`models/costing.py` (lazy، لـ `get_item_cost`).
- لا يوجد ملف مرجعي آخر معروف من المرفقات الحالية يستورد من هذا المسار مباشرة (عدا التوقع المنطقي أن `ui/tabs/pricing/*` يستدعي كليهما — محتواها غير مرفق).
