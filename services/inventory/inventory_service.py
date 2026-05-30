"""
services/inventory/inventory_service.py
=========================================
InventoryService — طبقة الخدمة للمخزون.

يوفر:
  - جلب العناصر مع الرصيد الحالي (SQL مباشر)
  - تسجيل حركات الوارد والصادر
  - تقرير المخزون
  - فحص المخزون المنخفض

يستدعي db/inventory/inventory_repo.py مباشرةً مع fallback لـ SQL مضمّن
لضمان عمل الـ service حتى لو الـ repo لم يُنشأ بعد.
"""
from __future__ import annotations

import logging
import datetime
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class InventoryReport:
    items           : list = field(default_factory=list)
    total_items     : int  = 0
    total_value     : float = 0.0
    low_stock_count : int  = 0
    low_stock_items : list = field(default_factory=list)


_SQL_ITEMS_WITH_STOCK = """
    SELECT
        i.id,
        i.name,
        i.type         AS item_type,
        i.unit,
        i.price,
        i.category_id,
        c.name         AS category_name,
        COALESCE(i.min_stock, 0) AS min_stock,
        COALESCE(
            (SELECT SUM(CASE WHEN m.movement_type='in'  THEN m.quantity
                             WHEN m.movement_type='out' THEN -m.quantity
                             ELSE 0 END)
               FROM inventory_movements m
              WHERE m.item_id = i.id), 0
        ) AS current_stock,
        COALESCE(
            (SELECT AVG(m.unit_cost)
               FROM inventory_movements m
              WHERE m.item_id = i.id AND m.movement_type = 'in'
                AND m.unit_cost > 0), 0
        ) AS avg_unit_cost
    FROM items i
    LEFT JOIN categories c ON c.id = i.category_id
    WHERE 1=1
"""

_SQL_MOVEMENTS = """
    SELECT
        m.id,
        m.item_id,
        i.name    AS item_name,
        m.movement_type,
        m.quantity,
        m.unit_cost,
        (m.quantity * m.unit_cost) AS total_cost,
        m.date,
        m.reference,
        m.notes
    FROM inventory_movements m
    JOIN items i ON i.id = m.item_id
    WHERE 1=1
"""


class InventoryService:
    """
    طبقة خدمة المخزون.

    يحاول أولاً استدعاء inventory_repo مباشرة.
    إذا لم تكن الدالة موجودة في الـ repo، ينفذ SQL مباشرة.
    """

    def __init__(self, conn):
        self.conn = conn

    def list_items(self, category_id: int = None,
                   item_type: str = None,
                   search: str = "") -> list[dict]:
        try:
            from db.inventory.inventory_repo import fetch_items_with_stock
            return fetch_items_with_stock(
                self.conn, category_id=category_id,
                item_type=item_type, search=search,
            )
        except (ImportError, AttributeError):
            return self._list_items_sql(category_id, item_type, search)
        except Exception as e:
            logger.error("InventoryService.list_items: %s", e)
            return []

    def _list_items_sql(self, category_id, item_type, search) -> list[dict]:
        try:
            sql, params = _SQL_ITEMS_WITH_STOCK, []
            if category_id is not None:
                sql += " AND i.category_id = ?"
                params.append(category_id)
            if item_type:
                sql += " AND i.type = ?"
                params.append(item_type)
            if search:
                sql += " AND i.name LIKE ?"
                params.append(f"%{search}%")
            sql += " ORDER BY i.name"
            return [dict(r) for r in self.conn.execute(sql, params).fetchall()]
        except Exception as e:
            logger.error("InventoryService._list_items_sql: %s", e)
            return []

    def get_item(self, item_id: int) -> Optional[dict]:
        try:
            from db.inventory.inventory_repo import fetch_item_with_stock
            return fetch_item_with_stock(self.conn, item_id)
        except (ImportError, AttributeError):
            for r in self._list_items_sql(None, None, ""):
                if r.get("id") == item_id:
                    return r
            return None
        except Exception as e:
            logger.error("InventoryService.get_item: %s", e)
            return None

    def get_current_stock(self, item_id: int) -> float:
        try:
            row = self.conn.execute(
                """SELECT COALESCE(
                       SUM(CASE WHEN movement_type='in'  THEN quantity
                                WHEN movement_type='out' THEN -quantity
                                ELSE 0 END), 0)
                   FROM inventory_movements WHERE item_id = ?""",
                (item_id,)
            ).fetchone()
            return float(row[0]) if row else 0.0
        except Exception as e:
            logger.error("InventoryService.get_current_stock: %s", e)
            return 0.0

    def list_movements(self, item_id: int = None,
                       movement_type: str = None,
                       date_from: str = None,
                       date_to: str = None,
                       limit: int = 500) -> list[dict]:
        try:
            from db.inventory.inventory_repo import fetch_movements
            return fetch_movements(
                self.conn, item_id=item_id, movement_type=movement_type,
                date_from=date_from, date_to=date_to, limit=limit,
            )
        except (ImportError, AttributeError):
            return self._list_movements_sql(item_id, movement_type, date_from, date_to, limit)
        except Exception as e:
            logger.error("InventoryService.list_movements: %s", e)
            return []

    def _list_movements_sql(self, item_id, movement_type,
                             date_from, date_to, limit) -> list[dict]:
        try:
            sql, params = _SQL_MOVEMENTS, []
            if item_id is not None:
                sql += " AND m.item_id = ?"
                params.append(item_id)
            if movement_type:
                sql += " AND m.movement_type = ?"
                params.append(movement_type)
            if date_from:
                sql += " AND m.date >= ?"
                params.append(date_from)
            if date_to:
                sql += " AND m.date <= ?"
                params.append(date_to)
            sql += " ORDER BY m.date DESC, m.id DESC LIMIT ?"
            params.append(limit)
            return [dict(r) for r in self.conn.execute(sql, params).fetchall()]
        except Exception as e:
            logger.error("InventoryService._list_movements_sql: %s", e)
            return []

    def record_inbound(self, item_id: int, quantity: float,
                       unit_cost: float = 0.0, date: str = None,
                       reference: str = "", notes: str = "") -> int:
        if quantity <= 0:
            raise ValueError("الكمية يجب أن تكون أكبر من صفر")
        return self._record_movement(item_id, "in", quantity, unit_cost, date, reference, notes)

    def record_outbound(self, item_id: int, quantity: float,
                        unit_cost: float = 0.0, date: str = None,
                        reference: str = "", notes: str = "") -> int:
        if quantity <= 0:
            raise ValueError("الكمية يجب أن تكون أكبر من صفر")
        current = self.get_current_stock(item_id)
        if current < quantity:
            raise ValueError(
                f"الكمية المطلوبة ({quantity:.4g}) تتجاوز الرصيد الحالي ({current:.4g})"
            )
        return self._record_movement(item_id, "out", quantity, unit_cost, date, reference, notes)

    def _record_movement(self, item_id, movement_type, quantity,
                          unit_cost, date, reference, notes) -> int:
        _date = date or datetime.date.today().isoformat()
        try:
            from db.inventory.inventory_repo import insert_movement
            return insert_movement(
                self.conn, item_id=item_id, movement_type=movement_type,
                quantity=quantity, unit_cost=unit_cost,
                date=_date, reference=reference, notes=notes,
            )
        except (ImportError, AttributeError):
            try:
                self.conn.execute(
                    """INSERT INTO inventory_movements
                       (item_id, movement_type, quantity, unit_cost, date, reference, notes)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (item_id, movement_type, quantity, unit_cost, _date, reference, notes)
                )
                self.conn.commit()
                row = self.conn.execute("SELECT last_insert_rowid()").fetchone()
                return row[0] if row else 0
            except Exception as e:
                logger.error("InventoryService._insert_movement_sql: %s", e)
                raise
        except Exception as e:
            logger.error("InventoryService._record_movement: %s", e)
            raise

    def delete_movement(self, movement_id: int) -> bool:
        try:
            from db.inventory.inventory_repo import delete_movement
            delete_movement(self.conn, movement_id)
            return True
        except (ImportError, AttributeError):
            try:
                self.conn.execute(
                    "DELETE FROM inventory_movements WHERE id = ?", (movement_id,)
                )
                self.conn.commit()
                return True
            except Exception as e:
                logger.error("InventoryService.delete_movement SQL: %s", e)
                return False
        except Exception as e:
            logger.error("InventoryService.delete_movement: %s", e)
            return False

    def get_report(self, category_id: int = None, item_type: str = None) -> InventoryReport:
        items = self.list_items(category_id=category_id, item_type=item_type)
        total_value, low_stock_list = 0.0, []
        for item in items:
            stock    = float(item.get("current_stock", 0) or 0)
            avg_cost = float(item.get("avg_unit_cost", 0) or 0)
            total_value += stock * avg_cost
            min_s = float(item.get("min_stock", 0) or 0)
            if min_s > 0 and stock <= min_s:
                low_stock_list.append(item)
        return InventoryReport(
            items=items, total_items=len(items), total_value=total_value,
            low_stock_count=len(low_stock_list), low_stock_items=low_stock_list,
        )

    def get_item_summary(self, item_id: int) -> dict:
        try:
            from db.inventory.inventory_repo import fetch_item_summary
            return fetch_item_summary(self.conn, item_id)
        except (ImportError, AttributeError):
            try:
                row = self.conn.execute(
                    """SELECT
                           COALESCE(SUM(CASE WHEN movement_type='in'  THEN quantity ELSE 0 END), 0),
                           COALESCE(SUM(CASE WHEN movement_type='out' THEN quantity ELSE 0 END), 0),
                           COALESCE(SUM(CASE WHEN movement_type='in'  THEN quantity
                                             WHEN movement_type='out' THEN -quantity
                                             ELSE 0 END), 0),
                           COALESCE(AVG(CASE WHEN movement_type='in' AND unit_cost>0
                                             THEN unit_cost END), 0)
                       FROM inventory_movements WHERE item_id = ?""",
                    (item_id,)
                ).fetchone()
                return {
                    "total_in": float(row[0]), "total_out": float(row[1]),
                    "current_stock": float(row[2]), "avg_unit_cost": float(row[3]),
                    "movements": self.list_movements(item_id=item_id),
                }
            except Exception as e:
                logger.error("InventoryService.get_item_summary SQL: %s", e)
                return {"total_in": 0.0, "total_out": 0.0,
                        "current_stock": 0.0, "avg_unit_cost": 0.0, "movements": []}
        except Exception as e:
            logger.error("InventoryService.get_item_summary: %s", e)
            return {"total_in": 0.0, "total_out": 0.0,
                    "current_stock": 0.0, "avg_unit_cost": 0.0, "movements": []}

    def update_min_stock(self, item_id: int, min_stock: float) -> bool:
        try:
            from db.inventory.inventory_repo import update_item_min_stock
            update_item_min_stock(self.conn, item_id, min_stock)
            return True
        except (ImportError, AttributeError):
            try:
                self.conn.execute(
                    "UPDATE items SET min_stock = ? WHERE id = ?",
                    (min_stock, item_id)
                )
                self.conn.commit()
                return True
            except Exception as e:
                logger.error("InventoryService.update_min_stock SQL: %s", e)
                return False
        except Exception as e:
            logger.error("InventoryService.update_min_stock: %s", e)
            return False

    def get_low_stock_items(self) -> list[dict]:
        try:
            from db.inventory.inventory_repo import fetch_low_stock_items
            return fetch_low_stock_items(self.conn)
        except (ImportError, AttributeError):
            items = self._list_items_sql(None, None, "")
            return [
                i for i in items
                if float(i.get("min_stock", 0) or 0) > 0
                and float(i.get("current_stock", 0) or 0)
                <= float(i.get("min_stock", 0) or 0)
            ]
        except Exception as e:
            logger.error("InventoryService.get_low_stock_items: %s", e)
            return []
