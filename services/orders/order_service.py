"""
services/orders/order_service.py
==================================
Business Logic للطلبات والعملاء.

الاستخدام:
    from services.orders.order_service import OrderService
    svc = OrderService(conn)
    order_id = svc.create(customer_id, items, notes)
"""

from dataclasses import dataclass, field


# ══════════════════════════════════════════════════════════
# Dataclasses
# ══════════════════════════════════════════════════════════

@dataclass
class OrderItem:
    product_id : int
    qty        : float
    unit_price : float
    notes      : str = ""

    def total(self) -> float:
        return self.qty * self.unit_price


@dataclass
class OrderStatusChange:
    order_id   : int
    old_status : str
    new_status : str
    note       : str
    timestamp  : str


@dataclass
class OrderSummary:
    total_orders  : int
    total_amount  : float
    pending_count : int
    in_progress   : int
    done_count    : int
    cancelled     : int


@dataclass
class DeletePreview:
    order_id     : int
    order_ref    : str
    status       : str
    can_delete   : bool
    reason       : str = ""  # السبب لو مش قادر يحذف

    def warning_text(self) -> str:
        if not self.can_delete:
            return f"⚠️ لا يمكن حذف الطلب «{self.order_ref}» — {self.reason}"
        return f"هل تريد حذف الطلب «{self.order_ref}»؟"


# ══════════════════════════════════════════════════════════
# الحالات المسموح بها للانتقال بين الـ statuses
# ══════════════════════════════════════════════════════════

_ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "pending":     ["in_progress", "cancelled"],
    "in_progress": ["done", "cancelled"],
    "done":        [],           # نهائي — مفيش انتقال
    "cancelled":   ["pending"],  # إعادة فتح
}

# الـ statuses اللي ما ينفعش يتحذف فيها الطلب
_NO_DELETE_STATUSES = {"in_progress", "done"}


# ══════════════════════════════════════════════════════════
# OrderService
# ══════════════════════════════════════════════════════════

class OrderService:
    """
    Business Logic للطلبات.
    يدير: إنشاء / تعديل / حذف / تغيير الحالة / الإحصائيات.
    """

    def __init__(self, conn):
        self._conn = conn

    # ── Create ────────────────────────────────────────────

    def create(self, customer_id: int,
               items: list[OrderItem],
               notes: str = "") -> int:
        """
        ينشئ طلب جديد ويرجع الـ ID.
        يتحقق من وجود العميل ومن وجود items.
        """
        if not customer_id:
            raise ValueError("العميل مطلوب")
        if not items:
            raise ValueError("الطلب يجب أن يحتوي على منتج واحد على الأقل")

        self._assert_customer_exists(customer_id)

        total = sum(i.total() for i in items)

        from db.orders.orders_repo import insert_order, insert_order_item
        order_id = insert_order(
            self._conn,
            customer_id = customer_id,
            total       = total,
            notes       = notes.strip(),
            status      = "pending",
        )
        for item in items:
            insert_order_item(
                self._conn,
                order_id   = order_id,
                product_id = item.product_id,
                qty        = item.qty,
                unit_price = item.unit_price,
                notes      = item.notes,
            )
        return order_id

    # ── Update ────────────────────────────────────────────

    def update(self, order_id: int,
               customer_id: int,
               items: list[OrderItem],
               notes: str = "") -> None:
        """يحدث بيانات الطلب — بس لو الحالة pending."""
        order = self._get_order_or_raise(order_id)

        if order["status"] != "pending":
            raise ValueError(
                f"لا يمكن تعديل الطلب — حالته الحالية: {order['status']}"
            )
        if not items:
            raise ValueError("الطلب يجب أن يحتوي على منتج واحد على الأقل")

        self._assert_customer_exists(customer_id)

        total = sum(i.total() for i in items)

        from db.orders.orders_repo import (
            update_order, delete_order_items, insert_order_item
        )
        update_order(
            self._conn,
            order_id    = order_id,
            customer_id = customer_id,
            total       = total,
            notes       = notes.strip(),
        )
        delete_order_items(self._conn, order_id)
        for item in items:
            insert_order_item(
                self._conn,
                order_id   = order_id,
                product_id = item.product_id,
                qty        = item.qty,
                unit_price = item.unit_price,
                notes      = item.notes,
            )

    # ── Status ────────────────────────────────────────────

    def change_status(self, order_id: int,
                      new_status: str,
                      note: str = "") -> OrderStatusChange:
        """
        يغير حالة الطلب مع التحقق من صحة الانتقال.
        يسجل الحركة في الـ log.
        """
        order = self._get_order_or_raise(order_id)
        old_status = order["status"]

        allowed = _ALLOWED_TRANSITIONS.get(old_status, [])
        if new_status not in allowed:
            raise ValueError(
                f"لا يمكن الانتقال من «{old_status}» إلى «{new_status}»"
            )

        from db.orders.orders_repo import (
            update_order_status, log_order_status
        )
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        update_order_status(self._conn, order_id, new_status)
        log_order_status(
            self._conn,
            order_id   = order_id,
            old_status = old_status,
            new_status = new_status,
            note       = note.strip(),
            timestamp  = timestamp,
        )

        return OrderStatusChange(
            order_id   = order_id,
            old_status = old_status,
            new_status = new_status,
            note       = note.strip(),
            timestamp  = timestamp,
        )

    def get_allowed_transitions(self, order_id: int) -> list[str]:
        """يرجع الحالات المسموح بالانتقال إليها من الحالة الحالية."""
        order = self._get_order_or_raise(order_id)
        return _ALLOWED_TRANSITIONS.get(order["status"], [])

    # ── Delete ────────────────────────────────────────────

    def get_delete_preview(self,
                           order_id: int) -> DeletePreview | None:
        """يرجع معلومات الحذف قبل التنفيذ."""
        order = self._conn.execute(
            "SELECT id, status FROM orders WHERE id=?",
            (order_id,)
        ).fetchone()
        if not order:
            return None

        ref    = f"#{order_id}"
        status = order["status"]

        if status in _NO_DELETE_STATUSES:
            return DeletePreview(
                order_id   = order_id,
                order_ref  = ref,
                status     = status,
                can_delete = False,
                reason     = "الطلب قيد التنفيذ أو مكتمل",
            )

        return DeletePreview(
            order_id   = order_id,
            order_ref  = ref,
            status     = status,
            can_delete = True,
        )

    def delete(self, order_id: int) -> bool:
        """
        يحذف الطلب.
        يرجع True لو نجح، False لو مش مسموح.
        """
        preview = self.get_delete_preview(order_id)
        if not preview or not preview.can_delete:
            return False

        from db.orders.orders_repo import delete_order
        delete_order(self._conn, order_id)
        return True

    # ── Summary / Stats ───────────────────────────────────

    def get_summary(self,
                    customer_id: int = None) -> OrderSummary:
        """يرجع إحصائيات الطلبات — كلها أو لعميل معين."""
        where  = "WHERE customer_id=?" if customer_id else ""
        params = (customer_id,) if customer_id else ()

        row = self._conn.execute(f"""
            SELECT
                COUNT(*)                                    AS total,
                COALESCE(SUM(total), 0)                    AS amount,
                SUM(status='pending')                      AS pending,
                SUM(status='in_progress')                  AS in_prog,
                SUM(status='done')                         AS done,
                SUM(status='cancelled')                    AS cancelled
            FROM orders {where}
        """, params).fetchone()

        if not row:
            return OrderSummary(0, 0.0, 0, 0, 0, 0)

        return OrderSummary(
            total_orders  = row["total"]     or 0,
            total_amount  = row["amount"]    or 0.0,
            pending_count = row["pending"]   or 0,
            in_progress   = row["in_prog"]   or 0,
            done_count    = row["done"]      or 0,
            cancelled     = row["cancelled"] or 0,
        )

    # ── Customer ──────────────────────────────────────────

    def add_customer(self, name: str,
                     phone: str = "",
                     notes: str = "") -> int:
        """يضيف عميل جديد ويرجع الـ ID."""
        name = name.strip()
        if not name:
            raise ValueError("اسم العميل مطلوب")

        from db.orders.customers_repo import insert_customer
        return insert_customer(
            self._conn,
            name  = name,
            phone = phone.strip(),
            notes = notes.strip(),
        )

    def update_customer(self, customer_id: int,
                        name: str,
                        phone: str = "",
                        notes: str = "") -> None:
        """يحدث بيانات العميل."""
        name = name.strip()
        if not name:
            raise ValueError("اسم العميل مطلوب")

        from db.orders.customers_repo import update_customer
        update_customer(
            self._conn,
            customer_id = customer_id,
            name        = name,
            phone       = phone.strip(),
            notes       = notes.strip(),
        )

    def get_customer_summary(self,
                             customer_id: int) -> OrderSummary:
        """إحصائيات طلبات عميل معين."""
        return self.get_summary(customer_id=customer_id)

    # ── Helpers ───────────────────────────────────────────

    def _get_order_or_raise(self, order_id: int) -> dict:
        row = self._conn.execute(
            "SELECT * FROM orders WHERE id=?", (order_id,)
        ).fetchone()
        if not row:
            raise ValueError(f"الطلب {order_id} غير موجود")
        return row

    def _assert_customer_exists(self, customer_id: int) -> None:
        row = self._conn.execute(
            "SELECT id FROM customers WHERE id=?", (customer_id,)
        ).fetchone()
        if not row:
            raise ValueError(f"العميل {customer_id} غير موجود")