# دليل الكود — Services الشركات (services/companies/)

> `services/companies/` — إدارة الشركات (companies.db) والعناصر المشتركة بينها.
> **الملفات الفعلية:** `company_service.py`, `shared_items_service.py`

---

## فهرس

| الملف | الوصف |
|-------|-------|
| [company_service.py](#company_servicepy) | CompanyService — CRUD الشركات + حالة الشركة النشطة + اتصالاتها |
| [shared_items_service.py](#shared_items_servicepy) | SharedItemsService — العناصر المشتركة بين الشركات ونشرها/ربطها |

---

## company_service.py

### `services/companies/company_service.py`

**الغرض:** الوسيط الوحيد بين طبقة الـ UI وقاعدة البيانات لكل عمليات إدارة الشركات (`companies.db`) — CRUD كامل + توفير اتصال central جاهز + الوصول لحالة الشركة النشطة (`company_state`) واتصالات قواعد بياناتها (`erp`/`accounting`/`inventory`).

**Imports (top-level):**
```python
from __future__ import annotations
import logging
from dataclasses import dataclass

from db.companies.companies_schema import (
    get_central_connection, create_central_tables,
)
from db.companies.companies_repo import (
    fetch_all_companies, fetch_company,
    insert_company as _repo_insert_company,
    update_company as _repo_update_company,
    delete_company as _repo_delete_company,
    toggle_company_active as _repo_toggle_company_active,
)
# استيراد داخلي (lazy) في كل classmethod يلمس company_state:
from db.companies.company_state import company_state
```

**من يستدعي هذا الملف:** `services/costing/catalog_service.py` (`_fetch_shared` — `is_company_ready`, `get_current_company_id`, `get_central_conn_and_init`)، `services/companies/shared_items_service.py` (مثال استخدام موثّق في الـ docstring، وليس استيراداً فعلياً)، `services/inventory/inventory_service.py` (`get_active_erp_conn`). متوقع أيضاً من `ui/tabs/companies/*` حسب `system_arch.txt`.

**لماذا service وليس تواصل مباشر؟ (موثّق في الكود):** يحقق هذا الملف الهيكلة `ui/tabs/... → CompanyService → companies_repo → companies_schema → DB` — طبقة الـ UI لا تعرف شيئاً عن `db.companies` مباشرة. أي تغيير مستقبلي في طريقة التخزين (تحويل النظام لـ online) يحدث هنا فقط دون لمس أي ملف في `ui/`.

### Dataclass

```python
@dataclass
class CompanyResult:
    id         : int
    name       : str
    short_name : str
    logo_path  : str | None
    color      : str
    is_active  : bool
    notes      : str
```

### Class: `CompanyService`
لا يرث من شيء.

```python
CompanyService(conn)
```
- `self._conn = conn`.

**Classmethods — اتصال جاهز ومهيّأ (نقطة الدخول من UI):**
- **`get_central_conn_and_init(cls)`**: يرجع اتصال `companies.db` جاهزاً بعد التأكد من إنشاء جداوله (`get_central_connection()` + `create_central_tables(conn)`). نقطة الدخول الوحيدة الموصى بها من `tabs/` — بنفس نمط `get_designs_conn_and_init` في دومين التصميم.
- **`get_current_company_id(cls) -> int | None`**: يرجع `id` الشركة النشطة حالياً عبر `company_state.company_id`. `None` لو مفيش شركة نشطة أو حصل خطأ (بصمت).
- **`get_current_company_name(cls) -> str`**: يرجع اسم الشركة النشطة عبر `company_state.company_name`. سلسلة فارغة عند أي خطأ.
- **`is_company_ready(cls) -> bool`**: `bool(company_state.is_ready)`. `False` عند أي خطأ.
- **`set_active_company(cls, company_id, name, color)`**: يستدعي `company_state.set_active(company_id, name, color)`. يبتلع أي استثناء بصمت.
- **`refresh_connections(cls)`**: يستدعي `company_state.refresh_connections()` — يعيد ضبط اتصالات قواعد بيانات الشركة النشطة. بصمت عند الفشل.
- **`is_conn_alive(cls, conn) -> bool`**: فحص بسيط لحيوية اتصال (`conn.execute("SELECT 1")`). `False` لو `conn is None` أو الاتصال مقطوع.
- **`get_active_erp_conn(cls)`**: يرجع اتصال `erp.db` الخاص بالشركة النشطة عبر `company_state.get_erp_conn()` (فقط لو `company_state.is_ready`). `None` بصمت عند أي مشكلة.
- **`get_active_accounting_conn(cls)`**: نفس النمط لـ `accounting.db` عبر `company_state.get_accounting_conn()`.
- **`get_active_inventory_conn(cls)`**: نفس النمط لـ `inventory.db` عبر `company_state.get_inventory_conn()`.

**Methods — Validation:**
- **`validate(self, name) -> str | None`**: يرجع رسالة خطأ "اسم الشركة مطلوب" لو `name.strip()` فارغ، وإلا `None`.

**Methods — قراءة:**
- **`list_companies(self, active_only=False) -> list[CompanyResult]`**: عبر `fetch_all_companies`.
- **`get_company(self, company_id) -> CompanyResult | None`**: عبر `fetch_company`.
- **`_to_result(self, row) -> CompanyResult`**: يحوّل صف DB إلى `CompanyResult`؛ `color` تُعطى قيمة افتراضية `"#1565c0"` لو فارغة، `short_name`/`notes` سلاسل فارغة كـ fallback.

**Methods — كتابة:**
- **`add_company(self, name, short_name="", color="#1565c0", notes="") -> int`**: يتحقق `validate()` أولاً (`ValueError` لو فشل). ينشئ شركة جديدة (ويهيّئ كل قواعد بياناتها الخاصة تلقائياً عبر `companies_repo.insert_company`).
- **`update_company(self, company_id, name, short_name="", color="#1565c0", notes="", is_active=True)`**: نفس التحقق، عبر `update_company` من الـ repo.
- **`delete_company(self, company_id) -> bool`**: يحذف الشركة من `companies.db` فقط — **ملفات DB الخاصة بها تبقى على الديسك** (سلوك موثّق صراحة في الـ repo).
- **`toggle_active(self, company_id)`**: عبر `toggle_company_active`.

---

## shared_items_service.py

### `services/companies/shared_items_service.py`

**الغرض:** الوسيط الوحيد بين طبقة الـ UI وقاعدة البيانات لكل عمليات العناصر المشتركة بين الشركات (`companies.db → shared_items`). يوفّر CRUD للعناصر المشتركة، بالإضافة لنشر عنصر من شركة كعنصر مشترك وربطه/فك ربطه بشركات أخرى.

**Imports (top-level):**
```python
from __future__ import annotations
import logging
from dataclasses import dataclass

from db.companies.shared_items_repo import (
    create_shared_items_tables,
    fetch_all_shared_items, fetch_shared_item,
    insert_shared_item, update_shared_item,
    fetch_linked_companies, fetch_shared_items_for_company,
    is_company_linked, set_linked_companies,
    get_item_data, get_item_as_raw, get_item_as_machine, get_item_as_labor_op,
)
from db.companies.companies_repo import (
    publish_item_as_shared, link_shared_item_to_company,
    unlink_shared_item as _repo_unlink_shared_item,
    delete_shared_item as _repo_delete_shared_item_cascade,
)
```

**من يستدعي هذا الملف:** `services/costing/catalog_service.py` (`_fetch_shared` — `list_for_company`). متوقع أيضاً من `ui/tabs/companies/shared_items_dialog.py`, `shared_items_manager.py`, `shared_items_mixin.py` حسب `system_arch.txt`.

**لماذا service وليس تواصل مباشر؟ (موثّق في الكود):** يحقق هذا الملف الهيكلة `ui/tabs/... → SharedItemsService → shared_items_repo / companies_repo → companies_schema → DB`. طبقة الـ UI (`tabs/`, `widgets/`) لا تستدعي `db.companies` مباشرة أبداً.

### Dataclass

```python
@dataclass
class SharedItemResult:
    id          : int
    name        : str
    shared_type : str
    data        : dict
    updated_at  : str
```

### Class: `SharedItemsService`
لا يرث من شيء.

```python
SharedItemsService(conn)
```
- `_VALID_TYPES = ("raw", "machine", "labor_op", "machine_op")` — ثابت class-level.
- الـ constructor يستدعي `create_shared_items_tables(self._conn)` مباشرة عند الإنشاء (ضمان جاهزية الجداول قبل أي استخدام).

**Methods — Validation:**
- **`validate(self, name, shared_type) -> str | None`**: يرجع رسالة خطأ لو `name.strip()` فارغ ("اسم العنصر مطلوب") أو `shared_type` غير ضمن `_VALID_TYPES` ("نوع العنصر المشترك غير صالح: {shared_type}"). وإلا `None`.

**Methods — قراءة (عناصر مشتركة):**
- **`list_items(self, shared_type=None) -> list[SharedItemResult]`**: عبر `fetch_all_shared_items`.
- **`get_item(self, item_id) -> SharedItemResult | None`**: عبر `fetch_shared_item`.
- **`get_item_data(self, item_id) -> dict`**: عبر `get_item_data`.
- **`get_item_as_raw(self, item_id) -> dict | None`**: عبر `get_item_as_raw`.
- **`get_item_as_machine(self, item_id) -> dict | None`**: عبر `get_item_as_machine`.
- **`get_item_as_labor_op(self, item_id) -> dict | None`**: عبر `get_item_as_labor_op`.
- **`_to_result(self, row) -> SharedItemResult`**: يحوّل صف DB إلى `SharedItemResult`، مع جلب `data` عبر استدعاء إضافي لـ `get_item_data(self._conn, row["id"])` (وليس من نفس الصف مباشرة).

**Methods — كتابة (عناصر مشتركة):**
- **`add_item(self, name, shared_type, data=None) -> int`**: يتحقق `validate()` أولاً. عبر `insert_shared_item(name.strip(), shared_type, data)`.
- **`update_item(self, item_id, name, data)`**: يتحقق `name.strip()` غير فارغ (`ValueError`). عبر `update_shared_item`.
- **`delete_item(self, item_id)`**: حذف العنصر المشترك **وكل روابطه** (cascade عبر FK) — عبر `_repo_delete_shared_item_cascade`.

**Methods — نشر وربط بين الشركات:**
- **`publish_from_company(self, source_company_id, source_item_id, shared_type, name, notes="") -> int`**: ينشر عنصر من شركة كعنصر مشترك (أو يربط بعنصر موجود بنفس الاسم). يتحقق `validate()` أولاً. عبر `publish_item_as_shared`.
- **`link_to_company(self, shared_item_id, company_id) -> int`**: عبر `link_shared_item_to_company(self._conn, self._conn, ...)` — **ملاحظة:** يمرر `self._conn` مرتين (نفس الاتصال في الموضعين المتوقع أن يكونا central+target).
- **`unlink_from_company(self, shared_item_id, company_id)`**: عبر `_repo_unlink_shared_item`.
- **`is_linked(self, shared_item_id, company_id) -> bool`**: عبر `is_company_linked`.
- **`set_linked_companies(self, shared_item_id, company_ids: list)`**: عبر `set_linked_companies` من الـ repo.
- **`list_linked_companies(self, shared_item_id) -> list`**: عبر `fetch_linked_companies`.
- **`list_for_company(self, company_id, shared_type=None) -> list[SharedItemResult]`**: عبر `fetch_shared_items_for_company` — **هذه الدالة تحديداً هي التي يستدعيها `services/costing/catalog_service.py._fetch_shared`**.

---

## علاقات الملفات

- لا يوجد استيراد مباشر بين `company_service.py` و `shared_items_service.py` — كل منهما مستقل، لكن الاستخدام النموذجي الموثّق في docstring `shared_items_service.py` هو الحصول على الاتصال أولاً عبر `CompanyService.get_central_conn_and_init()` ثم تمريره لـ `SharedItemsService(conn)`.
- **نمط مشترك:** كلاهما يوفّر Dataclass نتيجة بسيط (`CompanyResult`, `SharedItemResult`) مع `_to_result` داخلي لتحويل صف DB.
- تبعية خارج هذا المسار: `company_service.py` يعتمد على `db/companies/companies_schema.py`, `db/companies/companies_repo.py`, `db/companies/company_state.py`. `shared_items_service.py` يعتمد على `db/companies/shared_items_repo.py`, `db/companies/companies_repo.py`.
- **يُستخدم هذا المسار بكثافة من خارج نفسه:** `services/costing/catalog_service.py` يعتمد على كليهما معاً (`CompanyService` + `SharedItemsService`) لبناء قائمة العناصر المشتركة في الكتالوج (راجع `services_costing.md`). `services/inventory/inventory_service.py` يعتمد على `CompanyService.get_active_erp_conn` فقط (راجع `services_inventory.md`). `services/orders/order_service.py` **لا** يعتمد على هذا المسار (يستخدم `db.shared.items_repo.fetch_item` مباشرة لجلب بيانات المنتج، وليس عبر `CompanyService`).
