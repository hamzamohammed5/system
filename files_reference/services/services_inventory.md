# دليل الكود — Service المخزون (services/inventory/)

> `services/inventory/` — طبقة الخدمة لمخزن الشركة (`inventory_items` + `inventory_moves`).
> **الملفات الفعلية:** `inventory_service.py`

---

## فهرس

| الملف | الوصف |
|-------|-------|
| [inventory_service.py](#inventory_servicepy) | InventoryService — تصنيفات، أصناف، حركات (WACC)، وتقرير المخزون |

---

## inventory_service.py

### `services/inventory/inventory_service.py`

**الغرض:** طبقة الخدمة الكاملة لمخزن الشركة النشطة — تصنيفات المخزن، أصناف المخزن (CRUD + الرصيد والقيمة)، حركات المخزن (وارد/صادر/تسوية بمنطق WACC)، وتقرير مخزون شامل.

**Imports (top-level):**
```python
from __future__ import annotations
import logging
import datetime
from dataclasses import dataclass, field
from typing import Optional

from db.inventory.inventory_repo import (
    fetch_all_inv_categories, insert_inv_category, delete_inv_category,
    fetch_all_inventory, fetch_inventory_item,
    insert_inventory_item, update_inventory_item, delete_inventory_item,
    fetch_inventory_moves, fetch_recent_moves, record_inventory_move,
    fetch_recent_moves_with_item_names,
)
from services.shared.item_service import ItemService
from services.accounting.accounts_service import AccountsService
```

**من يستدعي هذا الملف:** غير محدد بثقة أي ملف UI مباشرة من المرفقات الحالية (متوقع من `ui/tabs/inventory/items/_item_form.py`, `_items_tab.py`, `inventory_inbound_tab.py`, `inventory_outbound_tab.py`, `inventory_report_tab.py` حسب `system_arch.txt` — لكن محتواها غير مرفق).

**⚠️ لا يوجد تناقض في جدول الحركات في هذا الكود:** هذا الملف يستدعي `db.inventory.inventory_repo` مباشرة بكل دواله (`fetch_all_inventory`, `record_inventory_move`, إلخ) بدون أي SQL مضمّن بديل أو أسماء جداول مختلفة — لا يوجد `inventory_movements` مذكور في هذا الملف.

**مبدأ العزل المعماري الموثّق في الكود:**
- هذا الملف هو **الوحيد** المسموح له استدعاء `db.inventory.inventory_repo`.
- أي ربط بدومين آخر يمر عبر service ذلك الدومين — لا يُستدعى repo تابع لدومين آخر من هنا مباشرة:
  - الأصناف (`items.id, name, type`) → `services.shared.item_service.ItemService`.
  - الحسابات (`accounts.code, name`) → `services.accounting.accounts_service.AccountsService`.
  - اتصال `erp.db` للشركة النشطة → `services.companies.company_service.CompanyService`.
- أي حركة مخزون (وارد/صادر) تحتاج بيانات إضافية (اسم الصنف مثلاً) تُنفَّذ عبر دالة مخصصة في `db.inventory.inventory_repo` — لا SQL خام هنا.

### Dataclass

```python
@dataclass
class InventoryReport:
    items            : list  = field(default_factory=list)
    total_items      : int   = 0
    total_value      : float = 0.0
    low_stock_count  : int   = 0
    zero_stock_count : int   = 0
    low_stock_items  : list  = field(default_factory=list)
```

### Class: `InventoryService`
لا يرث من شيء.

```python
InventoryService(inv_conn, acc_conn=None, erp_conn=None)
```
- `inv_conn`: اتصال قاعدة بيانات المخزون (نفس قاعدة الشركة).
- `acc_conn`: اتصال قاعدة بيانات المحاسبة (اختياري — لازم فقط للدوال التي تجيب قوائم حسابات). يُبنى منه `self._acc_svc = AccountsService(acc_conn)` لو مُمرَّر، وإلا `None`.
- `erp_conn`: اتصال `erp.db` (اختياري). **لو `None`**: جدول `items` موجود في قاعدة الـ erp وليس قاعدة المخزون — يحتاج اتصالاً منفصلاً حتى لو لم يُمرَّر صراحة، فيُجلب عبر `services.companies.company_service.CompanyService.get_active_erp_conn()`. **[إصلاح هيكلي] موثّق في الكود:** كان الاستدعاء `db.companies.company_state` مباشرة (كسر مبدأ العزل — `inventory_service` من حقه يستدعي `db.inventory` فقط)؛ `CompanyService.get_active_erp_conn()` هو نقطة الدخول الرسمية لهذا الغرض من أي service آخر.
- يبني `self._item_svc = ItemService(erp_conn)` دائماً.

**Methods — تصنيفات المخزن:**
- **`list_categories(self) -> list`**: عبر `fetch_all_inv_categories`.
- **`add_category(self, name, color="#607d8b", notes=None) -> int`**: عبر `insert_inv_category`.
- **`delete_category(self, category_id)`**: عبر `delete_inv_category`.

**Methods — أصناف المخزن (قراءة):**
- **`list_items(self) -> list`**: كل أصناف المخزن مع الرصيد والقيمة الإجمالية، عبر `fetch_all_inventory`.
- **`get_item(self, inv_id) -> Optional[dict]`**: عبر `fetch_inventory_item`.

**Methods — أصناف المخزن (كتابة):**
- **`add_item(self, name, unit="قطعة", qty_min=0, account_code="114", category_id=None, costing_item_id=None, notes=None) -> int`**: يتحقق `name.strip()` غير فارغ (`ValueError`). عبر `insert_inventory_item` باستخدام `account_code`/`costing_item_id`.
- **`update_item(self, inv_id, name, unit, qty_min, account_code="114", category_id=None, notes=None)`**: نفس التحقق، عبر `update_inventory_item`.
- **`delete_item(self, inv_id)`**: عبر `delete_inventory_item`.
- **`add_item_by_account_id(self, name, unit, qty_min, account_id=None, item_id=None, notes=None) -> int`**: نسخة بديلة تستخدم `account_id`/`item_id` مباشرة بدل `account_code`/`costing_item_id` — **مطابقة لتوقيع `insert_inventory_item` الفعلي المستخدم في `_ItemForm`** (توقيعان مختلفان لنفس الدالة الأساسية حسب طريقة الاستدعاء).
- **`update_item_by_account_id(self, inv_id, name, unit, qty_min, account_id=None, notes=None)`**: نظير `update_item` بنفس منطق `account_id` بدل `account_code`.

**Methods — حركات المخزن:**
- **`list_moves_for_item(self, inv_id) -> list`**: عبر `fetch_inventory_moves`.
- **`list_recent_moves(self, move_type=None, limit=100) -> list`**: عبر `fetch_recent_moves`.
- **`list_recent_moves_with_names(self, move_type, limit=100) -> list`**: حركات المخزون (وارد/صادر) مع اسم الصنف — تُستخدم في جداول "آخر الحركات" بتبويبات الوارد والصادر. **[إصلاح هيكلي] موثّق في الكود:** كان الاستعلام SQL خام هنا (`self.conn.execute` مباشرة) بدلاً من دالة في `db.inventory.inventory_repo`؛ انتقل إلى `fetch_recent_moves_with_item_names` — كل SQL يجب أن يعيش في `db/` فقط.
- **`record_move(self, inv_id, move_type, qty, unit_cost, date, notes=None, ref_entry_id=None, ref_entry_no=None) -> int`**: يسجل حركة مخزن (`in`/`out`/`adjust`) ويحدث الرصيد والتكلفة المتوسطة (WACC) عبر `inventory_repo.record_inventory_move`.
- **`record_inbound(self, inv_id, qty, unit_cost, date, notes=None, ref_entry_id=None, ref_entry_no=None) -> int`**: يتحقق `qty > 0` (`ValueError`)، يستدعي `record_move(move_type="in", ...)`.
- **`record_outbound(self, inv_id, qty, date, notes=None) -> int`**: يتحقق `qty > 0` (`ValueError`)، يستدعي `record_move(move_type="out", unit_cost=0.0, ...)` — **لا يتحقق من الرصيد الحالي قبل الصرف** في هذا الملف (التحقق من الرصيد الكافي، إن وُجد، يقع داخل `record_inventory_move` في الـ repo).

**Methods — تقرير المخزون:**
- **`get_report(self) -> InventoryReport`**: يستدعي `list_items()` ثم يحسب لكل صنف: `total_value` تراكمي (`SUM(inv["total_value"])`)، `zero_stock_count` (لو `qty_on_hand == 0`)، `low_stock_count` + `low_stock_items` (لو `qty_min > 0 and qty_on_hand <= qty_min`).

**Methods — تكامل مع دومينات أخرى (facade):**
- **`list_costing_items(self, item_type=None) -> list`**: أصناف نظام التكلفة (costing) القابلة للربط بصنف مخزون عبر `costing_item_id` — تُجلب من `ItemService` وليس مباشرة من repo. لو `item_type` محدد → `[{"id", "name"}]` لهذا النوع فقط. لو غير محدد → يجمع الأنواع الشائعة (`raw`, `semi`, `final`) في قائمة واحدة `[{"id", "name", "item_type"}]` (لا يوجد `list_all` في `ItemService` حالياً).
- **`list_payment_accounts(self, acc_type) -> list`**: قوائم حسابات للاختيار (دفع/أصول) عبر `AccountsService.list_leaf_accounts(acc_types=[acc_type])`. يرمي `RuntimeError` لو `self._acc_svc is None` (يعني `acc_conn` لم يُمرَّر لهذا الـ `InventoryService`).
- **`get_account_by_code(self, code) -> Optional[dict]`**: عبر `AccountsService.get_account_by_code`. نفس فحص `RuntimeError` لو `acc_conn` غير متاح.

**ملاحظات مهمة من التعليقات:**
- الملف يذكّر صراحة أن أي عملية مخزون تحتاج ترحيلاً محاسبياً مرتبطاً (قيد + حركة) — مثل الشراء — **لا** تُنفَّذ هنا، بل في `services/accounting/inventory_posting_service.py` (`InventoryPostingService.purchase`) لأن ذلك يعبر لدومين المحاسبة (`accounting.db`) وليس فقط `inventory_repo`.

---

## علاقات الملفات

- ملف واحد فقط في هذا المسار — لا توجد علاقات داخلية.
- تبعية خارج هذا المسار: يعتمد على `db/inventory/inventory_repo.py` (الوحيد المسموح له استدعاءه من هذا الدومين)، `services/shared/item_service.py` (`ItemService`)، `services/accounting/accounts_service.py` (`AccountsService`، راجع `services_accounting.md`)، و `services/companies/company_service.py` (`CompanyService.get_active_erp_conn`، راجع `services_companies.md`).
- `services/accounting/inventory_posting_service.py` (خارج هذا المسار) **لا يستورد** هذا الملف مباشرة رغم الترابط المنطقي بينهما — يعمل بشكل مستقل عبر `db.accounting.accounting_inventory_repo.purchase_inventory` الذي يتعامل مع اتصالي المخزون والمحاسبة معاً بنفسه.
