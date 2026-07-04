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
  - أي ربط بدومين آخر (الأصناف من costing عبر items، أو الحسابات
    المحاسبية) يمر عبر service ذلك الدومين — لا نكلم repo تابع
    لدومين آخر من هنا مباشرة:
      * الأصناف (items.id, name, type)  → services.shared.item_service.ItemService
      * الحسابات (accounts.code, name)  → db.accounting.accounting_accounts_repo
        (لا يوجد accounting service عام بعد؛ هذه الدوال قراءة فقط
        وتُستخدم فقط لتوفير قوائم اختيار — عند إنشاء AccountService
        مستقبلاً تُستبدل هذه الاستدعاءات بنداء إليه دون تغيير في UI).

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
)
from db.accounting.accounting_accounts_repo import (
    fetch_leaf_accounts, fetch_account_by_code,
)
from services.shared.item_service import ItemService

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

    def __init__(self, inv_conn, acc_conn=None):
        self.conn     = inv_conn
        self._acc_conn = acc_conn
        self._item_svc = ItemService(inv_conn)

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

    # ────────────────────────────────────────────────────
    # حركات المخزن
    # ────────────────────────────────────────────────────

    def list_moves_for_item(self, inv_id: int) -> list:
        return fetch_inventory_moves(self.conn, inv_id)

    def list_recent_moves(self, move_type: str = None, limit: int = 100) -> list:
        return fetch_recent_moves(self.conn, move_type=move_type, limit=limit)

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
        قوائم حسابات للاختيار (دفع/أصول) — قراءة فقط عبر
        accounting_accounts_repo. للكتابة على الحسابات استخدم
        الـ accounting service المخصص وقت توفره.
        """
        if self._acc_conn is None:
            raise RuntimeError("acc_conn غير متاح لهذا الـ InventoryService")
        return fetch_leaf_accounts(self._acc_conn, acc_type)

    def get_account_by_code(self, code: str) -> Optional[dict]:
        if self._acc_conn is None:
            raise RuntimeError("acc_conn غير متاح لهذا الـ InventoryService")
        return fetch_account_by_code(self._acc_conn, code)