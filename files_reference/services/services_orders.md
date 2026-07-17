# دليل الكود — Services الطلبات (services/orders/)

> `services/orders/` — الطلبات، العملاء، وكتالوج المنتجات المسعّرة والعروض الخاص بالطلبات.
> **الملفات الفعلية:** `catalog_service.py`, `customer_service.py`, `order_service.py`

---

## فهرس

| الملف | الوصف |
|-------|-------|
| [order_service.py](#order_servicepy) | OrderService — إنشاء/تعديل/حذف الطلبات، الحالات، البنود، رأس الطلب |
| [customer_service.py](#customer_servicepy) | CustomerService — CRUD العملاء وجهات الاتصال والإحصائيات |
| [catalog_service.py](#catalog_servicepy) | CatalogService — كتالوج المنتجات المسعّرة والعروض (مع caching) |

---

## order_service.py

### `services/orders/order_service.py`

**الغرض:** Business Logic كاملة للطلبات — إنشاء/تعديل/حذف، انتقالات الحالة، إدارة البنود، رأس الطلب، وربط اختياري بمنتجات `erp.db`.

**Imports (top-level):**
```python
from dataclasses import dataclass, field
import logging
from datetime import datetime

from db.orders.orders_repo import (
    insert_order, update_order, insert_order_item,
    update_order_item, delete_order_item,
    change_order_status, delete_order, reorder,
    fetch_order, fetch_order_basic, delete_order_items_by_order,
    fetch_order_items, fetch_status_log,
    fetch_orders_summary_for_customer, fetch_orders_summary_all,
    fetch_all_orders, cancel_order, fetch_orders_summary,
)
from db.orders.customers_repo import fetch_customer
from db.shared.items_repo import fetch_item
from db.orders.orders_schema import get_orders_connection, create_orders_tables
from services.orders.customer_service import CustomerService
```

**من يستدعي هذا الملف:** غير محدد بثقة أي ملف UI مباشرة من المرفقات الحالية (متوقع من `ui/tabs/orders/_order_form.py`, `_order_detail.py`, `dashboard_tab.py`, `orders_section.py` حسب `system_arch.txt` وحسب توثيق الملف نفسه — لكن محتواها غير مرفق).

**[تعديل هيكلي] موثّق في الكود:** أُزيل كل استدعاء SQL خام (`conn.execute`) من هذا الملف — كل عملية قراءة/كتابة تمر الآن عبر `db.orders.orders_repo` أو `db.orders.customers_repo`، حفاظاً على `widgets → tabs/UI → services → repos (db) → schema`. الدوال المتأثرة: `_get_order_or_raise`, `_assert_customer_exists`, `get_summary`, `get_delete_preview`.

**[E-06] ربط `product_id`:** `product_id` يُستخدم فعلياً الآن في `insert_order_item`. `_validate_and_enrich_items()` تتحقق من وجود المنتجات في جدول `items` وتجلب أسماءها/أسعارها تلقائياً لو `item_name`/`unit_price` فارغَين. `ErpConnMixin` (اسم مفهومي فقط، وليس class فعلي): يمكن تمرير `erp_conn` اختياري لجلب بيانات المنتج عند الحاجة.

### Dataclasses

```python
@dataclass
class OrderItem:
    product_id : int
    qty        : float
    unit_price : float
    notes      : str = ""
    item_name  : str = ""
```
- `.total() -> float` — `qty × unit_price`.
- `.resolved_name() -> str` — يرجع `item_name.strip()` أو `f"منتج #{product_id}"` كـ fallback.
- **[E-06]** `product_id` يُستخدم للتحقق من وجود المنتج (لو `erp_conn` متاح)، لجلب `item_name`/`unit_price` تلقائياً لو فارغَين، ويُحفظ في `order_items.product_id` لربط الطلب بالمنتج. `item_name` لا يزال يُمرَّر من الـ caller — `erp_conn` ليس إلزامياً.

```python
@dataclass
class OrderStatusChange:
    order_id   : int
    old_status : str
    new_status : str
    note       : str
    timestamp  : str
```

```python
@dataclass
class OrderSummary:
    total_orders  : int
    total_amount  : float
    pending_count : int
    in_progress   : int
    done_count    : int
    cancelled     : int
```

```python
@dataclass
class DeletePreview:
    order_id     : int
    order_ref    : str
    status       : str
    can_delete   : bool
    reason       : str = ""
```
- `.warning_text() -> str` — يرجع رسالة "⚠️ لا يمكن حذف الطلب «{ref}» — {reason}" لو `not can_delete`، وإلا "هل تريد حذف الطلب «{ref}»؟".

### ثوابت module-level

```python
_ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "pending":     ["confirmed", "in_progress", "cancelled", "on_hold"],
    "confirmed":   ["in_progress", "cancelled", "on_hold"],
    "in_progress": ["ready", "cancelled", "on_hold"],
    "ready":       ["delivered", "cancelled"],
    "delivered":   [],
    "cancelled":   ["pending"],
    "on_hold":     ["pending", "confirmed", "in_progress"],
}

_NO_DELETE_STATUSES = {"in_progress", "ready", "delivered"}
```

### دالة top-level مستقلة

```python
resolve_product_info(erp_conn, product_id: int) -> dict | None
```
- **[E-06]** يجلب اسم وسعر المنتج من جدول `items` في `erp.db` عبر `fetch_item` من `db.shared.items_repo` (وليس SQL خام كما كان سابقاً — **[تعديل هيكلي]**).
- يرجع `{"name": str, "price": float}` أو `None` لو غير موجود.
- `erp_conn is None` أو `product_id is None` → يرجع `None` بأمان (بدون استثناء).
- تُستخدم من `OrderService` للتحقق من وجود المنتج، ملء `item_name` تلقائياً، واقتراح `unit_price` من سعر المنتج.

### Class: `OrderService`
لا يرث من شيء.

```python
OrderService(conn, erp_conn=None)
```
- `erp_conn` اختياري تماماً — بدونه يعمل الـ service بالسلوك القديم دون أي إثراء.

**Methods — إثراء المنتجات [E-06]:**
- **`_enrich_item(self, item: OrderItem) -> OrderItem`**: لو `erp_conn is None` → يرجع `item` كما هو. يستدعي `resolve_product_info`؛ لو `None` → `logger.warning` ويرجع `item` كما هو. لو `item_name` فارغ و`info["name"]` موجود → ينشئ `OrderItem` جديد بنفس البيانات + الاسم من DB. لو `unit_price == 0` و`info["price"] > 0` → `logger.warning` فقط (**لا يُعدّل السعر تلقائياً**).
- **`_validate_and_enrich_items(self, items) -> list[OrderItem]`**: تُطبّق `_enrich_item` على كل بند.

**Methods — Create/Update:**
- **`create(self, customer_id, items, notes="") -> int`**: يتحقق `customer_id` و`items` غير فارغين، يستدعي `_assert_customer_exists`، يُثري البنود، يحسب `total = sum(i.total())`، يستدعي `insert_order(status="pending")` ثم `insert_order_item(..., product_id=item.product_id)` لكل بند.
- **`update(self, order_id, customer_id, items, notes="")`**: يرفض لو `order["status"] != "pending"`. يتحقق `items` غير فارغة، يستدعي `_assert_customer_exists`، يُثري البنود، يستدعي `update_order`، ثم `_delete_order_items(order_id)` وإعادة إدراج البنود الجديدة.

**Methods — Status:**
- **`change_status(self, order_id, new_status, note="") -> OrderStatusChange`**: يتحقق أن `new_status` ضمن `_ALLOWED_TRANSITIONS[old_status]` وإلا `ValueError`. يستدعي `change_order_status(changed_by="system")`. يرجع `OrderStatusChange` بـ timestamp حالي (`"%Y-%m-%d %H:%M:%S"`).
- **`get_allowed_transitions(self, order_id) -> list[str]`**.

**Methods — Delete:**
- **`get_delete_preview(self, order_id) -> DeletePreview | None`**: `status in _NO_DELETE_STATUSES` → `can_delete=False` مع سبب "الطلب قيد التنفيذ أو مكتمل".
- **`delete(self, order_id) -> bool`**: يتحقق من `get_delete_preview` أولاً، وإلا يرجع `False` بدون حذف.

**Methods — Summary:**
- **`get_summary(self, customer_id=None) -> OrderSummary`**: **[تعديل هيكلي]** لم يعد SQL ديناميكي — يستدعي `fetch_orders_summary_for_customer` أو `fetch_orders_summary_all` من `orders_repo` حسب وجود `customer_id`. يقرأ من الصف: `total`, `amount`, `pending`, `in_prog`, `done`, `cancelled` (بأسماء أعمدة الـ repo مباشرة، مع `or 0`/`or 0.0` fallback). يرجع `OrderSummary(0,0.0,0,0,0,0)` لو الصف `None`.

**Methods — Customer (facade على `CustomerService`):**
- **`add_customer(self, name, phone="", notes="") -> int`**: pass-through حقيقي — يستدعي `CustomerService(self._conn).add(...)`.
- **`update_customer(self, customer_id, name, phone="", notes="")`**: pass-through على `CustomerService(self._conn).update(...)`.
- **`get_customer_summary(self, customer_id) -> OrderSummary`**: alias لـ `self.get_summary(customer_id=customer_id)`.
- **ملاحظة معمارية موثّقة:** `CustomerService` أصبح المالك الحصري لمنطق كتابة العميل؛ هذه الدوال أُبقيت هنا فقط للتوافق مع كود قديم يستدعي `OrderService.add_customer/update_customer`، وهي الآن composition حقيقي بدل تكرار المنطق.

**Methods — Orders List (facade — [مضاف]):**
- **`list_orders(self) -> list`**: facade على `fetch_all_orders` — كانت `_orders_list_panel.py` تستورد من الـ repo مباشرة (كسر هيكلي)، تم سدّه هنا.
- **`get_order(self, order_id) -> dict | None`**: facade على `fetch_order` (مع JOIN بيانات العميل).
- **`cancel(self, order_id, reason="") -> bool`**: facade على `cancel_order`.
- **`do_reorder(self, order_id) -> int | None`**: facade على `reorder` — ينشئ طلباً جديداً بناءً على طلب سابق.
- **`get_dashboard_summary(self) -> dict`**: facade على `fetch_orders_summary` — dict خام بمفاتيح الحالات والأولوية لملء بطاقات لوحة المتابعة، **مختلف** عن `get_summary()` (التي ترجع `OrderSummary` مبسّط).

**Methods — Order Items (facade — [مضاف]):**
سدّ مخالفة هيكلية كانت في `ui/tabs/orders/order_detail/_items_section.py` و `_log_section.py` (استيراد مباشر من `orders_repo`):
- **`get_order_items(self, order_id) -> list`**.
- **`add_item(self, order_id, item_name, description="", quantity=1, unit="قطعة", unit_price=0, discount_pct=0, design_ref="", notes="") -> int`**.
- **`update_item(self, item_id, item_name, description="", quantity=1, unit="قطعة", unit_price=0, discount_pct=0, design_ref="", notes="")`**.
- **`remove_item(self, item_id)`**.

**Methods — Order Header (facade كامل — [مضاف]):**
`create()`/`update()` أعلاه مبنيتان على `OrderItem` وتفترض استبدال كل البنود دفعة واحدة، ولا تغطي حقول رأس الطلب الفعلية (`order_type`, `priority`, `due_date`, `discount`, `paid_amount`, `internal_notes`) ولا التعديل بند-بند. هذه الدوال تغلّف `insert_order`/`update_order` بتوقيعهما الفعلي لتُستخدم من `_order_form.py`:
- **`create_order_header(self, customer_id, order_type, priority, due_date, discount=0, paid_amount=0, notes="", internal_notes="") -> int`**: يتحقق العميل موجود، ينشئ رأس طلب بدون بنود.
- **`update_order_header(self, order_id, priority, due_date, discount=0, paid_amount=0, notes="", internal_notes="")`**: يُحدّث رأس الطلب بدون لمس البنود.
- **`replace_order_items(self, order_id, items_data: list[dict])`**: يمسح كل بنود الطلب الحالية (`{i["id"] for i in existing}`) ويعيد إدراجها من قائمة `dicts` (مفاتيح: `item_name, description, quantity, unit, unit_price, discount_pct, design_ref, notes`) مع `sort_order=idx`.

**Methods — Status Log (facade):**
- **`get_status_log(self, order_id) -> list`**: facade على `fetch_status_log`.

**Methods — Helpers (داخلية):**
- **`_get_order_or_raise(self, order_id) -> dict`**: **[تعديل هيكلي]** يستخدم `fetch_order_basic` (كان SQL مباشر) — يكفي للحقول الداخلية (`status`/`customer_id`) دون تحميل JOIN كامل. يرمي `ValueError` لو غير موجود.
- **`_assert_customer_exists(self, customer_id)`**: **[تعديل هيكلي]** يستخدم `fetch_customer` من `customers_repo` (كان SQL مباشر). يرمي `ValueError` لو غير موجود أو `is_active=0`.
- **`_delete_order_items(self, order_id)`**: **[تعديل هيكلي]** يستخدم `delete_order_items_by_order` من `orders_repo` (كان `DELETE` مباشر).

### دالة top-level مستقلة (bootstrapping)

```python
get_orders_conn_and_init()
```
- **[إضافة]** تغليف `get_orders_connection()` + `create_orders_tables()` لتفادي استدعاء `db.orders.orders_schema` مباشرة من `tabs/orders_section.py` (كسر هيكلي: `tabs → repos/db` بتجاوز `services`).
- يفتح اتصال `orders.db`، يهيّئ جداوله، ويرجع الاتصال. نفس نمط `get_designs_conn_and_init()` في `services/design/__init__.py`.

---

## customer_service.py

### `services/orders/customer_service.py`

**الغرض:** طبقة الخدمة لعملاء نظام الطلبات (جدول `customers`) — قراءة، إحصائيات، جهات اتصال، تفعيل/تعطيل، حذف، وطلبات العميل (facade على دومين الطلبات).

**Imports (top-level):**
```python
from __future__ import annotations
import logging
from typing import Optional

from db.orders.customers_repo import (
    fetch_customer, fetch_all_customers, search_customers,
    delete_customer, toggle_customer_active,
    fetch_customer_stats, fetch_contacts,
    insert_customer, update_customer,
    insert_contact as _insert_contact,
    update_contact as _update_contact,
    delete_contact as _delete_contact,
)
from db.orders.orders_repo import fetch_customer_orders
```

**من يستدعي هذا الملف:** `services/orders/order_service.py` (composition عبر `add_customer`/`update_customer`). متوقع أيضاً من `ui/tabs/orders/customers/customer_detail_panel.py`, `customers_list_panel.py`, `_customer_form.py`, `customers_tab.py` حسب `system_arch.txt` — لكن محتواها غير مرفق.

**[تعديل هيكلي] موثّق في الكود:** `add`/`update` نُقلا فعلياً إلى هذا الملف (لم يعودا pass-through على `OrderService`). النسخة القديمة كانت تعتمد على أن يذهب أي مستخدم لـ `CustomerService` لإنشاء عميل جديد إلى `OrderService` بدلاً منه، رغم أن `CustomerService` يدّعي أنه "نقطة الدخول الوحيدة" — تناقض تم حله بجعل هذا الملف المالك الحصري لعمليات كتابة العميل، بينما `OrderService` أصبح يستدعي `CustomerService` (composition) بدل تكرار المنطق.

### Class: `CustomerService`
لا يرث من شيء.

```python
CustomerService(conn)
```

**Methods — قراءة:**
- **`get_customer(self, customer_id) -> Optional[dict]`**: facade على `fetch_customer`.
- **`list_customers(self) -> list`**: facade على `fetch_all_customers`.
- **`search(self, query: str) -> list`**: بحث بالاسم/الكود/الهاتف — تُستخدم في حقل البحث السريع بنموذج الطلب بدل استدعاء `search_customers` مباشرة.
- **`get_stats(self, customer_id) -> dict`**: facade على `fetch_customer_stats`.
- **`list_contacts(self, customer_id) -> list`**: facade على `fetch_contacts`.

**Methods — كتابة:**
- **`add(self, name, customer_type="individual", phone="", phone2="", email="", address="", city="", notes="") -> int`**: يتحقق `name.strip()` غير فارغ (وإلا `ValueError`)، يُنظّف (`.strip()`) كل الحقول النصية، يستدعي `insert_customer`.
- **`update(self, customer_id, name, customer_type="individual", phone="", phone2="", email="", address="", city="", notes="", is_active=1)`**: نفس التحقق والتنظيف، يستدعي `update_customer`.
- **`delete(self, customer_id) -> bool`**: facade على `delete_customer`.
- **`toggle_active(self, customer_id)`**: facade على `toggle_customer_active`.

**Methods — تكامل مع دومين الطلبات (facade):**
- **`list_orders(self, customer_id) -> list`**: طلبات عميل معيّن — تُجلب من `db.orders.orders_repo.fetch_customer_orders` (دومين مختلف)، موجودة هنا فقط كـ facade لتوفير نقطة دخول واحدة من UI بدل استيراد `orders_repo` مباشرة.

**Methods — جهات الاتصال (كتابة):**
- **`add_contact(self, customer_id, name, role="", phone="", email="", notes="") -> int`**: يتحقق `name.strip()` غير فارغ. **ملاحظة موثّقة:** `insert_contact` كانت موجودة فعلاً في `customers_repo` لكن بدون غلاف في `CustomerService`، مما اضطر `_customer_form.py` لتعطيل حفظ جهات الاتصال بالكامل — تم حل ذلك هنا.
- **`update_contact(self, contact_id, name, role="", phone="", email="", notes="")`**: نفس التحقق.
- **`delete_contact(self, contact_id)`**: facade على `_delete_contact`.

---

## catalog_service.py

### `services/orders/catalog_service.py`

**الغرض:** طبقة الخدمة لكتالوج المنتجات المسعّرة (final/semi) والعروض المستخدمة في نموذج الطلب. **نقطة الدخول الوحيدة المسموح لها استدعاء `db.orders.catalog_repo` (تحديداً `db.costing.catalog_repo` كما هو مستورد فعلياً)**.

**Imports (top-level):**
```python
from __future__ import annotations
import logging
from typing import Optional

from db.orders.catalog_repo import (
    fetch_priced_products, fetch_offers, fetch_offer_lines,
)
```

**من يستدعي هذا الملف:** `ui/tabs/orders/order_form/_item_row_widget.py` (حسب توثيق الملف نفسه — كان يحتوي المنطق والـ caching سابقاً مباشرة قبل النقل هنا).

**[مضاف حديثاً] موثّق في الكود:**
- كان المنطق (SQL + فتح اتصال) موجوداً مباشرة داخل `ui/tabs/orders/order_form/_products_fetcher.py` — نُقل بالكامل هنا. الاتصال (`conn`) لم يعد يُفتح ضمنياً داخل الدالة، بل يُمرَّر للـ constructor بنفس نمط باقي الـ services في المشروع (مثل `CustomerService(conn)`).
- الـ caching الذي كان **class-level** على `ui.tabs.orders.order_form._item_row_widget._ItemRowWidget` (`_products_cache`) نُقل بالكامل لهذا الملف، على مستوى **instance** من `CatalogService` — لأن الـ service (وليس الـ UI) هو من يعرف متى تنتهي صلاحية البيانات المخزَّنة.

> ⚠️ **ملاحظة تسمية مهمة:** هذا الملف يحمل نفس اسم الـ class `CatalogService` الموجود في `services/costing/catalog_service.py` — لكنه ملف مختلف تماماً بمسؤولية مختلفة (منتجات مسعّرة + عروض للطلبات، وليس كتالوج مكوّنات BOM). انتبه عند الاستيراد لتحديد المسار الصحيح: `services.orders.catalog_service.CatalogService` مقابل `services.costing.catalog_service.CatalogService`.

### Class: `CatalogService`
لا يرث من شيء.

```python
CatalogService(conn)
```
- `self.conn = conn`, `self._products_cache: Optional[list] = None`, `self._offers_cache: Optional[list] = None`.

**Methods — المنتجات المسعّرة:**
- **`get_priced_products(self, force_refresh: bool = False) -> list`**: يرجع المنتجات المسعّرة (final/semi) مع تصنيفاتها. `force_refresh=True` يتجاوز الكاش ويعيد الجلب من DB عبر `fetch_priced_products`. الـ caching نُقل هنا من `_ItemRowWidget` (كان class-level cache على الـ widget نفسه).
- **`invalidate_products_cache(self)`**: يقابل الدالة القديمة `_ItemRowWidget.invalidate_cache()` — تُستدعى بعد أي تعديل على المنتجات/الأسعار في مكان آخر من التطبيق حتى لا يعمل الـ UI ببيانات قديمة.

**Methods — العروض:**
- **`get_offers(self, force_refresh: bool = False) -> list`**: نفس نمط الـ caching، عبر `fetch_offers`.
- **`get_offer_lines(self, offer_id) -> list`**: بنود عرض معيّن — **لا تُخزَّن مؤقتاً** لأنها تُطلب لكل عرض بمعرفه الخاص، عبر `fetch_offer_lines`.
- **`invalidate_offers_cache(self)`**.

---

## علاقات الملفات

- `order_service.py` يستورد `services/orders/customer_service.py` مباشرة (composition — `CustomerService(self._conn)`) لدوال `add_customer`/`update_customer`. هذه هي العلاقة الوحيدة بين ملفات هذا المسار.
- `catalog_service.py` مستقل تماماً عن `order_service.py` و `customer_service.py` — لا استيراد متبادل.
- تبعية خارج هذا المسار: `order_service.py` يعتمد على `db/shared/items_repo.py` (لـ `resolve_product_info`)؛ `catalog_service.py` يعتمد على `db/costing/catalog_repo.py` (رغم أن اسم الموديول في الاستيراد الفعلي هو `db.orders.catalog_repo` — راجع ملاحظة التسمية أعلاه).
- **تحذير تسمية:** يوجد ملفان مختلفان باسم class `CatalogService` في المشروع: `services/orders/catalog_service.py` (هذا الملف) و `services/costing/catalog_service.py` (راجع `services_costing.md`) — مسؤوليتان مختلفتان تماماً رغم الاسم المتطابق.
