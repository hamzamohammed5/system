"""
services/inventory/inventory_service.py
=========================================
InventoryService — طبقة الخدمة لمخزن الشركة (inventory_items + inventory_moves).

يغطي:
  - تصنيفات المخزن (inventory_categories)
  - أصناف المخزن (inventory_items): CRUD + الرصيد والقيمة
  - حركات المخزن (inventory_moves): وارد / صادر / تسوية، بمنطق WACC
  - تقرير مخزون شامل (إجمالي، قيمة، أصناف منخفضة/منتهية)

مبدأ العزل المعماري:
  - هذا الملف هو الوحيد المسموح له باستدعاء db.inventory.inventory_repo.
  - أي ربط بدومين آخر يمر عبر service ذلك الدومين — لا نكلم repo تابع
    لدومين آخر من هنا مباشرة:
      * الأصناف (items.id, name, type)  → services.shared.item_service.ItemService
      * الحسابات (accounts.code, name)  → services.accounting.accounts_service.AccountsService
      * اتصال erp.db للشركة النشطة      → services.companies.company_service.CompanyService
  - أي حركة مخزون (وارد/صادر) تحتاج بيانات إضافية (اسم الصنف مثلاً)
    تُنفَّذ عبر دالة مخصصة في db.inventory.inventory_repo، لا SQL خام هنا.

هذا الـ service هو نقطة الدخول الوحيدة لطبقة الـ UI لكل ما يخص المخزون:
  from services.inventory.inventory_service import InventoryService
  svc = InventoryService(inv_conn, acc_conn=acc_conn)
"""
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

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════
# Dataclasses
# ══════════════════════════════════════════════════════════

@dataclass
class InventoryReport:
    items           : list  = field(default_factory=list)
    total_items     : int   = 0
    total_value     : float = 0.0
    low_stock_count : int   = 0
    zero_stock_count: int   = 0
    low_stock_items : list  = field(default_factory=list)


# ══════════════════════════════════════════════════════════
# InventoryService
# ══════════════════════════════════════════════════════════

class InventoryService:
    """
    طبقة خدمة المخزون — نقطة الدخول الوحيدة لطبقة الـ UI.

    المعاملات:
        inv_conn : اتصال قاعدة بيانات المخزون (نفس قاعدة الشركة)
        acc_conn : اتصال قاعدة بيانات المحاسبة (اختياري — لازم فقط
                   للدوال اللي بتجيب قوائم حسابات)
    """

    def __init__(self, inv_conn, acc_conn=None, erp_conn=None):
        self.conn     = inv_conn
        self._acc_conn = acc_conn
        self._acc_svc  = AccountsService(acc_conn) if acc_conn is not None else None
        if erp_conn is None:
            # جدول items موجود في قاعدة الـ erp وليس قاعدة المخزون —
            # لازم اتصال منفصل حتى لو لم يُمرَّر صراحة من الـ UI.
            #
            # [إصلاح هيكلي] كان الاستدعاء db.companies.company_state
            # مباشرة (كسر مبدأ العزل — inventory_service من حقه
            # يستدعي db.inventory فقط). CompanyService.get_active_erp_conn()
            # هو نقطة الدخول الرسمية لهذا الغرض من أي service آخر.
            from services.companies.company_service import CompanyService
            erp_conn = CompanyService.get_active_erp_conn()
        self._erp_conn = erp_conn
        self._item_svc = ItemService(erp_conn)

    # ────────────────────────────────────────────────────
    # تصنيفات المخزن
    # ────────────────────────────────────────────────────

    def list_categories(self) -> list:
        return fetch_all_inv_categories(self.conn)

    def add_category(self, name: str, color: str = "#607d8b",
                      notes: str = None) -> int:
        return insert_inv_category(self.conn, name, color, notes)

    def delete_category(self, category_id: int) -> None:
        delete_inv_category(self.conn, category_id)

    # ────────────────────────────────────────────────────
    # أصناف المخزن — قراءة
    # ────────────────────────────────────────────────────

    def list_items(self) -> list:
        """كل أصناف المخزن مع الرصيد والقيمة الإجمالية."""
        return fetch_all_inventory(self.conn)

    def get_item(self, inv_id: int) -> Optional[dict]:
        return fetch_inventory_item(self.conn, inv_id)

    # ────────────────────────────────────────────────────
    # أصناف المخزن — كتابة
    # ────────────────────────────────────────────────────

    def add_item(self, name: str, unit: str = "قطعة",
                 qty_min: float = 0,
                 account_code: str = "114",
                 category_id: int = None,
                 costing_item_id: int = None,
                 notes: str = None) -> int:
        if not name.strip():
            raise ValueError("اسم الصنف مطلوب")
        return insert_inventory_item(
            self.conn, name.strip(), unit, qty_min,
            account_code, category_id, costing_item_id, notes,
        )

    def update_item(self, inv_id: int, name: str, unit: str,
                     qty_min: float,
                     account_code: str = "114",
                     category_id: int = None,
                     notes: str = None) -> None:
        if not name.strip():
            raise ValueError("اسم الصنف مطلوب")
        update_inventory_item(
            self.conn, inv_id, name.strip(), unit, qty_min,
            account_code, category_id, notes,
        )

    def delete_item(self, inv_id: int) -> None:
        delete_inventory_item(self.conn, inv_id)

    def add_item_by_account_id(self, name: str, unit: str, qty_min: float,
                                account_id: int = None, item_id: int = None,
                                notes: str = None) -> int:
        """
        نسخة من add_item تستخدم account_id/item_id مباشرة بدل
        account_code/costing_item_id — مطابقة لتوقيع
        insert_inventory_item الفعلي المستخدم في _ItemForm.
        """
        if not name.strip():
            raise ValueError("اسم الصنف مطلوب")
        return insert_inventory_item(
            self.conn, name=name.strip(), unit=unit, qty_min=qty_min,
            account_id=account_id, item_id=item_id, notes=notes,
        )

    def update_item_by_account_id(self, inv_id: int, name: str, unit: str,
                                   qty_min: float, account_id: int = None,
                                   notes: str = None) -> None:
        """
        نسخة من update_item تستخدم account_id مباشرة بدل account_code —
        مطابقة لتوقيع update_inventory_item الفعلي المستخدم في _ItemForm.
        """
        if not name.strip():
            raise ValueError("اسم الصنف مطلوب")
        update_inventory_item(
            self.conn, inv_id, name.strip(), unit, qty_min,
            account_id, notes,
        )

    # ────────────────────────────────────────────────────
    # حركات المخزن
    # ────────────────────────────────────────────────────

    def list_moves_for_item(self, inv_id: int) -> list:
        return fetch_inventory_moves(self.conn, inv_id)

    def list_recent_moves(self, move_type: str = None, limit: int = 100) -> list:
        return fetch_recent_moves(self.conn, move_type=move_type, limit=limit)

    def list_recent_moves_with_names(self, move_type: str, limit: int = 100) -> list:
        """
        حركات المخزون (وارد/صادر) مع اسم الصنف — تُستخدم في جداول
        'آخر الحركات' بتبويبات الوارد والصادر.

        [إصلاح هيكلي] كان الاستعلام SQL خام هنا (self.conn.execute مباشرة)
        بدلاً من دالة في db.inventory.inventory_repo. انتقل إلى
        fetch_recent_moves_with_item_names — كل SQL يجب أن يعيش في db/ فقط.
        """
        return fetch_recent_moves_with_item_names(self.conn, move_type, limit)

    def record_move(self, inv_id: int, move_type: str,
                     qty: float, unit_cost: float, date: str,
                     notes: str = None,
                     ref_entry_id: int = None,
                     ref_entry_no: str = None) -> int:
        """
        يسجل حركة مخزن (in / out / adjust) ويحدث الرصيد والتكلفة
        المتوسطة (WACC) عبر inventory_repo.record_inventory_move.
        """
        return record_inventory_move(
            self.conn, inv_id, move_type, qty, unit_cost, date,
            notes=notes, ref_entry_id=ref_entry_id, ref_entry_no=ref_entry_no,
        )

    def record_inbound(self, inv_id: int, qty: float, unit_cost: float,
                        date: str, notes: str = None,
                        ref_entry_id: int = None, ref_entry_no: str = None) -> int:
        if qty <= 0:
            raise ValueError("الكمية يجب أن تكون أكبر من صفر")
        return self.record_move(
            inv_id, "in", qty, unit_cost, date,
            notes=notes, ref_entry_id=ref_entry_id, ref_entry_no=ref_entry_no,
        )

    def record_outbound(self, inv_id: int, qty: float, date: str,
                         notes: str = None) -> int:
        if qty <= 0:
            raise ValueError("الكمية يجب أن تكون أكبر من صفر")
        return self.record_move(inv_id, "out", qty, 0.0, date, notes=notes)

    # ────────────────────────────────────────────────────
    # تقرير المخزون
    # ────────────────────────────────────────────────────

    def get_report(self) -> InventoryReport:
        items = self.list_items()
        total_value, low_items = 0.0, []
        low_count = zero_count = 0

        for inv in items:
            qty      = float(inv["qty_on_hand"])
            qty_min  = float(inv["qty_min"])
            total_value += float(inv["total_value"])
            if qty == 0:
                zero_count += 1
            elif qty_min > 0 and qty <= qty_min:
                low_count += 1
                low_items.append(inv)

        return InventoryReport(
            items=items, total_items=len(items), total_value=total_value,
            low_stock_count=low_count, zero_stock_count=zero_count,
            low_stock_items=low_items,
        )

    # ────────────────────────────────────────────────────
    # تكامل مع دومينات أخرى (facade)
    # ────────────────────────────────────────────────────

    def list_costing_items(self, item_type: str = None) -> list:
        """
        أصناف نظام التكلفة (costing) القابلة للربط بصنف مخزون
        عبر costing_item_id — تُجلب من ItemService وليس مباشرة من repo.
        """
        if item_type:
            return [
                {"id": r.id, "name": r.name}
                for r in self._item_svc.list_by_type(item_type)
            ]
        # لا يوجد list_all في ItemService حالياً — نجمع الأنواع الشائعة
        all_items = []
        for t in ("raw", "semi", "final"):
            all_items.extend(self._item_svc.list_by_type(t))
        return [{"id": r.id, "name": r.name, "item_type": r.item_type} for r in all_items]

    def list_payment_accounts(self, acc_type: str) -> list:
        """
        قوائم حسابات للاختيار (دفع/أصول) — عبر AccountsService
        (services.accounting) بدل استدعاء db.accounting مباشرة.
        """
        if self._acc_svc is None:
            raise RuntimeError("acc_conn غير متاح لهذا الـ InventoryService")
        return self._acc_svc.list_leaf_accounts(acc_types=[acc_type])

    def get_account_by_code(self, code: str) -> Optional[dict]:
        if self._acc_svc is None:
            raise RuntimeError("acc_conn غير متاح لهذا الـ InventoryService")
        return self._acc_svc.get_account_by_code(code)