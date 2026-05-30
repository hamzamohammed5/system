"""
services/inventory/inventory_service.py
=========================================
InventoryService — الطبقة الوسيطة بين tabs/inventory وقاعدة بيانات المخزون.

يستخدم مباشرة:
    db/inventory/inventory_repo.py
    db/inventory/inventory_schema.py

لا تضع أي منطق UI هنا — فقط business logic ومنطق البيانات.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class InventoryService:
    """
    Service للمخزون — يتوسط بين UI وقاعدة البيانات.

    الاستخدام:
        svc = InventoryService(conn)
        items = svc.get_items()
        svc.record_inbound(item_id=5, qty=100, date="2025-01-01", ref="PO-001")
    """

    def __init__(self, conn):
        self.conn = conn

    # ── عناصر المخزون ──────────────────────────────────────────

    def get_items(self, filters: dict = None) -> list[dict]:
        """
        يجلب قائمة عناصر المخزون مع الرصيد الحالي لكل عنصر.

        filters: dict اختياري مع مفاتيح:
            name      : str  — بحث بالاسم (LIKE)
            item_type : str  — نوع العنصر
            category_id: int — تصنيف
            low_stock : bool — العناصر التي وصلت للحد الأدنى فقط
        """
        from db.inventory.inventory_repo import fetch_inventory_items
        try:
            return fetch_inventory_items(self.conn, filters or {})
        except Exception as e:
            logger.error("InventoryService.get_items: %s", e)
            return []

    def get_item(self, item_id: int) -> dict | None:
        """يجلب تفاصيل عنصر مخزون واحد مع رصيده الحالي."""
        from db.inventory.inventory_repo import fetch_inventory_item
        try:
            return fetch_inventory_item(self.conn, item_id)
        except Exception as e:
            logger.error("InventoryService.get_item(%d): %s", item_id, e)
            return None

    def get_current_stock(self, item_id: int) -> float:
        """يرجع الرصيد الحالي لعنصر معين."""
        from db.inventory.inventory_repo import get_item_current_stock
        try:
            return float(get_item_current_stock(self.conn, item_id) or 0)
        except Exception as e:
            logger.error("InventoryService.get_current_stock(%d): %s", item_id, e)
            return 0.0

    # ── حركات المخزون ──────────────────────────────────────────

    def record_inbound(
        self,
        item_id: int,
        qty: float,
        date: str,
        ref: str = "",
        notes: str = "",
        unit_cost: float = 0.0,
    ) -> int:
        """
        يسجل حركة وارد للمخزون.

        Returns:
            ID الحركة الجديدة.

        Raises:
            ValueError: إذا كانت الكمية <= 0.
        """
        if qty <= 0:
            raise ValueError(f"الكمية يجب أن تكون أكبر من صفر (القيمة المُدخلة: {qty})")
        from db.inventory.inventory_repo import record_inventory_movement
        return record_inventory_movement(
            self.conn,
            item_id=item_id,
            movement_type="inbound",
            qty=qty,
            date=date,
            ref=ref,
            notes=notes,
            unit_cost=unit_cost,
        )

    def record_outbound(
        self,
        item_id: int,
        qty: float,
        date: str,
        ref: str = "",
        notes: str = "",
    ) -> int:
        """
        يسجل حركة صادر من المخزون.

        Raises:
            ValueError: إذا كانت الكمية <= 0 أو لا يوجد رصيد كافٍ.
        """
        if qty <= 0:
            raise ValueError(f"الكمية يجب أن تكون أكبر من صفر (القيمة المُدخلة: {qty})")

        current = self.get_current_stock(item_id)
        if qty > current:
            raise ValueError(
                f"الكمية المطلوبة ({qty}) أكبر من الرصيد الحالي ({current})"
            )

        from db.inventory.inventory_repo import record_inventory_movement
        return record_inventory_movement(
            self.conn,
            item_id=item_id,
            movement_type="outbound",
            qty=qty,
            date=date,
            ref=ref,
            notes=notes,
        )

    def get_movements(
        self,
        item_id: int = None,
        date_from: str = None,
        date_to: str = None,
        movement_type: str = None,
    ) -> list[dict]:
        """
        يجلب حركات المخزون مع إمكانية الفلترة.

        movement_type: "inbound" | "outbound" | None (كل الحركات)
        """
        from db.inventory.inventory_repo import fetch_inventory_movements
        try:
            return fetch_inventory_movements(
                self.conn,
                item_id=item_id,
                date_from=date_from,
                date_to=date_to,
                movement_type=movement_type,
            )
        except Exception as e:
            logger.error("InventoryService.get_movements: %s", e)
            return []

    def delete_movement(self, movement_id: int) -> bool:
        """
        يحذف حركة مخزون.

        Raises:
            ValueError: إذا كان الحذف سيجعل الرصيد سالباً.
        """
        from db.inventory.inventory_repo import delete_inventory_movement, check_movement_deletable
        try:
            can_delete, reason = check_movement_deletable(self.conn, movement_id)
            if not can_delete:
                raise ValueError(reason or "لا يمكن حذف هذه الحركة")
            delete_inventory_movement(self.conn, movement_id)
            return True
        except ValueError:
            raise
        except Exception as e:
            logger.error("InventoryService.delete_movement(%d): %s", movement_id, e)
            return False

    # ── تقرير المخزون ──────────────────────────────────────────

    def get_report(
        self,
        date_from: str = None,
        date_to: str = None,
        category_id: int = None,
    ) -> list[dict]:
        """
        يجلب تقرير المخزون: كل عنصر مع الوارد والصادر والرصيد للفترة.

        كل عنصر في النتيجة يحتوي:
            id, name, category, unit,
            opening_balance, total_inbound, total_outbound, closing_balance
        """
        from db.inventory.inventory_repo import fetch_inventory_report
        try:
            return fetch_inventory_report(
                self.conn,
                date_from=date_from,
                date_to=date_to,
                category_id=category_id,
            )
        except Exception as e:
            logger.error("InventoryService.get_report: %s", e)
            return []

    def get_low_stock_items(self) -> list[dict]:
        """يجلب العناصر التي وصل رصيدها للحد الأدنى أو أقل."""
        from db.inventory.inventory_repo import fetch_low_stock_items
        try:
            return fetch_low_stock_items(self.conn)
        except Exception as e:
            logger.error("InventoryService.get_low_stock_items: %s", e)
            return []