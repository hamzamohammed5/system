"""
services/orders/order_service.py
==================================
Business Logic للطلبات والعملاء.

إصلاح 34: مزامنة الـ imports مع الدوال الفعلية في orders_repo.
الدوال المُصلَحة:
  - update_order_status → change_order_status (الاسم الفعلي)
  - log_order_status    → _log_status (private في repo، نستخدم change_order_status مباشرة)
  - delete_order_items  → أُضيفت كدالة مساعدة داخلية هنا
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
    reason       : str = ""

    def warning_text(self) -> str:
        if not self.can_delete:
            return f"⚠️ لا يمكن حذف الطلب «{self.order_ref}» — {self.reason}"
        return f"هل تريد حذف الطلب «{self.order_ref}»؟"


# ══════════════════════════════════════════════════════════
# الحالات المسموح بها للانتقال بين الـ statuses
# ══════════════════════════════════════════════════════════

_ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "pending":     ["confirmed", "in_progress", "cancelled", "on_hold"],
    "confirmed":   ["in_progress", "cancelled", "on_hold"],
    "in_progress": ["ready", "cancelled", "on_hold"],
    "ready":       ["delivered", "cancelled"],
    "delivered":   [],
    "cancelled":   ["pending"],
    "on_hold":     ["pending", "confirmed", "in_progress"],
}

# الـ statuses اللي ما ينفعش يتحذف فيها الطلب
_NO_DELETE_STATUSES = {"in_progress", "ready", "delivered"}


# ══════════════════════════════════════════════════════════
# OrderService
# ══════════════════════════════════════════════════════════

class OrderService:
    """
    Business Logic للطلبات.
    يدير: إنشاء / تعديل / حذف / تغيير الحالة / الإحصائيات.

    إصلاح 34: كل الـ imports مزامَنة مع الدوال الفعلية في orders_repo.
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

        # [إصلاح 34] استخدام الدوال الفعلية الموجودة في orders_repo
        from db.orders.orders_repo import insert_order, insert_order_item
        order_id = insert_order(
            self._conn,
            customer_id  = customer_id,
            total_amount = total,
            notes        = notes.strip(),
            status       = "pending",
        )
        for item in items:
            insert_order_item(
                self._conn,
                order_id    = order_id,
                item_name   = self._resolve_item_name(item.product_id),
                quantity    = item.qty,
                unit_price  = item.unit_price,
                notes       = item.notes,
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

        # [إصلاح 34] استخدام update_order الفعلية + حذف يدوي للبنود
        from db.orders.orders_repo import update_order, insert_order_item
        update_order(
            self._conn,
            order_id     = order_id,
            total_amount = total,
            notes        = notes.strip(),
        )
        # حذف البنود القديمة ثم إضافة الجديدة
        self._delete_order_items(order_id)
        for item in items:
            insert_order_item(
                self._conn,
                order_id    = order_id,
                item_name   = self._resolve_item_name(item.product_id),
                quantity    = item.qty,
                unit_price  = item.unit_price,
                notes       = item.notes,
            )

    # ── Status ────────────────────────────────────────────

    def change_status(self, order_id: int,
                      new_status: str,
                      note: str = "") -> OrderStatusChange:
        """
        يغير حالة الطلب مع التحقق من صحة الانتقال.

        [إصلاح 34] يستخدم change_order_status الفعلية بدل update_order_status.
        """
        order = self._get_order_or_raise(order_id)
        old_status = order["status"]

        allowed = _ALLOWED_TRANSITIONS.get(old_status, [])
        if new_status not in allowed:
            raise ValueError(
                f"لا يمكن الانتقال من «{old_status}» إلى «{new_status}»"
            )

        from db.orders.orders_repo import change_order_status
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # change_order_status يتولى تحديث الحالة وتسجيل الـ log داخلياً
        change_order_status(
            self._conn,
            order_id   = order_id,
            new_status = new_status,
            notes      = note.strip(),
            changed_by = "system",
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
            "SELECT id, status, order_number FROM orders WHERE id=?",
            (order_id,)
        ).fetchone()
        if not order:
            return None

        ref    = order["order_number"] or f"#{order_id}"
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

        # [إصلاح 34] delete_order موجودة فعلاً في orders_repo
        from db.orders.orders_repo import delete_order
        return delete_order(self._conn, order_id)

    # ── Summary / Stats ───────────────────────────────────

    def get_summary(self,
                    customer_id: int = None) -> OrderSummary:
        """يرجع إحصائيات الطلبات — كلها أو لعميل معين."""
        where  = "WHERE customer_id=?" if customer_id else ""
        params = (customer_id,) if customer_id else ()

        row = self._conn.execute(f"""
            SELECT
                COUNT(*)                                        AS total,
                COALESCE(SUM(net_amount), 0)                   AS amount,
                SUM(CASE WHEN status='pending'     THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN status='in_progress' THEN 1 ELSE 0 END) AS in_prog,
                SUM(CASE WHEN status='delivered'   THEN 1 ELSE 0 END) AS done,
                SUM(CASE WHEN status='cancelled'   THEN 1 ELSE 0 END) AS cancelled
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
            "SELECT id, is_active FROM customers WHERE id=?", (customer_id,)
        ).fetchone()
        if not row:
            raise ValueError(f"العميل {customer_id} غير موجود")
        if not row["is_active"]:
            raise ValueError(
                f"العميل {customer_id} غير نشط — فعّله أولاً لإنشاء طلبات جديدة"
            )

    def _resolve_item_name(self, product_id: int) -> str:
        """يجيب اسم المنتج من erp.db — fallback لو مش موجود."""
        try:
            from db.companies.company_state import company_state
            if company_state.is_ready:
                erp = company_state.get_erp_conn()
                row = erp.execute(
                    "SELECT name FROM items WHERE id=?", (product_id,)
                ).fetchone()
                if row:
                    return row["name"]
        except Exception:
            pass
        return f"منتج #{product_id}"

    def _delete_order_items(self, order_id: int) -> None:
        """
        [إصلاح 34] دالة مساعدة داخلية لحذف بنود الطلب.
        بديل عن delete_order_items الغير موجودة في orders_repo.
        delete_order_item موجودة للبند الواحد، نستخدم DELETE مباشر هنا.
        """
        self._conn.execute(
            "DELETE FROM order_items WHERE order_id=?", (order_id,)
        )
        self._conn.commit()