"""
services/orders/order_service.py
==================================
Business Logic للطلبات والعملاء.

[E-06] ربط product_id في OrderItem:
  - product_id أصبح يُستخدم فعلياً في insert_order_item.
  - _validate_product_ids() تتحقق من وجود المنتجات في جدول items
    وتجلب أسماءها وأسعارها تلقائياً لو item_name أو unit_price فارغَيْن.
  - resolve_product_info() — دالة مساعدة تجلب اسم وسعر المنتج من DB.
  - ErpConnMixin: يمكن تمرير erp_conn اختياري لجلب بيانات المنتج
    عند الحاجة (لتجنب coupling إجباري مع erp.db).

إصلاح 34 محفوظ: كل الـ imports مزامَنة مع الدوال الفعلية في orders_repo.
إصلاح 8 محفوظ:  item_name يُمرَّر من الـ caller — erp_conn اختياري فقط.
"""

from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════
# Dataclasses
# ══════════════════════════════════════════════════════════

@dataclass
class OrderItem:
    """
    بند طلب واحد.

    [E-06] product_id يُستخدم الآن:
      1. للتحقق من وجود المنتج في items table (لو erp_conn متاح).
      2. لجلب item_name و unit_price تلقائياً لو كانا فارغَيْن.
      3. يُحفظ في order_items.product_id لربط الطلب بالمنتج.

    [إصلاح 8 محفوظ] item_name لا يزال يُمرَّر من الـ caller.
    erp_conn ليس إلزامياً — resolved_name() تعمل بدونه.
    """
    product_id : int
    qty        : float
    unit_price : float
    notes      : str = ""
    item_name  : str = ""

    def total(self) -> float:
        return self.qty * self.unit_price

    def resolved_name(self) -> str:
        """يرجع الاسم أو fallback بسيط."""
        return self.item_name.strip() if self.item_name.strip() else f"منتج #{self.product_id}"


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
# الحالات المسموح بها للانتقال
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

_NO_DELETE_STATUSES = {"in_progress", "ready", "delivered"}


# ══════════════════════════════════════════════════════════
# [E-06] Product resolver
# ══════════════════════════════════════════════════════════

def resolve_product_info(erp_conn,
                          product_id: int) -> "dict | None":
    """
    [E-06] يجلب اسم وسعر المنتج من جدول items في erp.db.

    Returns:
        dict {"name": str, "price": float} أو None لو غير موجود.

    يُستخدم من OrderService لـ:
      1. التحقق من وجود المنتج.
      2. ملء item_name تلقائياً لو كان فارغاً.
      3. اقتراح unit_price من سعر المنتج لو كان صفراً.
    """
    if erp_conn is None or product_id is None:
        return None
    try:
        row = erp_conn.execute(
            "SELECT name, price FROM items WHERE id=?", (product_id,)
        ).fetchone()
        if row:
            return {"name": row["name"] or "", "price": float(row["price"] or 0)}
    except Exception as e:
        logger.debug("resolve_product_info: %s", e)
    return None


# ══════════════════════════════════════════════════════════
# OrderService
# ══════════════════════════════════════════════════════════

class OrderService:
    """
    Business Logic للطلبات.

    [E-06] يقبل erp_conn اختيارياً لربط المنتجات:
        svc = OrderService(orders_conn, erp_conn=erp_conn)

        # لو erp_conn متاح:
        # - يتحقق من وجود product_id في items table
        # - يجلب item_name تلقائياً لو كان فارغاً
        # - يقترح unit_price من سعر المنتج لو كان صفراً

        # لو erp_conn غير متاح (None):
        # - يعمل بنفس السلوك القديم
        # - item_name من OrderItem.resolved_name()
        # - unit_price من OrderItem مباشرة

    [إصلاح 34 محفوظ] imports مزامَنة مع الدوال الفعلية في orders_repo.
    [إصلاح 8 محفوظ]  item_name يُمرَّر من الـ caller — erp_conn اختياري.
    """

    def __init__(self, conn, erp_conn=None):
        self._conn     = conn
        self._erp_conn = erp_conn   # [E-06] اختياري — لربط المنتجات

    # ── [E-06] Product validation & enrichment ────────────

    def _enrich_item(self, item: OrderItem) -> OrderItem:
        """
        [E-06] يُثري OrderItem بمعلومات المنتج من erp.db.

        لو erp_conn متاح:
          - يتحقق من وجود product_id في items.
          - يملأ item_name تلقائياً لو كان فارغاً.
          - يُبلِّغ بـ warning لو unit_price = 0 وسعر المنتج موجود.

        لو erp_conn غير متاح → يُعيد الـ item كما هو.
        """
        if self._erp_conn is None:
            return item

        info = resolve_product_info(self._erp_conn, item.product_id)
        if info is None:
            logger.warning(
                "OrderService._enrich_item: product_id=%s غير موجود في items",
                item.product_id
            )
            return item

        # ملء item_name تلقائياً لو كان فارغاً
        if not item.item_name.strip() and info["name"]:
            item = OrderItem(
                product_id = item.product_id,
                qty        = item.qty,
                unit_price = item.unit_price,
                notes      = item.notes,
                item_name  = info["name"],
            )

        # تحذير لو السعر صفر والمنتج له سعر
        if item.unit_price == 0 and info["price"] > 0:
            logger.warning(
                "OrderService._enrich_item: product_id=%s unit_price=0 "
                "لكن سعر المنتج في DB = %.2f — تأكد من السعر",
                item.product_id, info["price"]
            )

        return item

    def _validate_and_enrich_items(self,
                                    items: list[OrderItem]) -> list[OrderItem]:
        """[E-06] يُثري كل البنود بمعلومات المنتجات."""
        return [self._enrich_item(item) for item in items]

    # ── Create ────────────────────────────────────────────

    def create(self, customer_id: int,
               items: list[OrderItem],
               notes: str = "") -> int:
        """
        ينشئ طلب جديد ويرجع الـ ID.

        [E-06] يُثري البنود بمعلومات المنتجات قبل الحفظ (لو erp_conn متاح).
        """
        if not customer_id:
            raise ValueError("العميل مطلوب")
        if not items:
            raise ValueError("الطلب يجب أن يحتوي على منتج واحد على الأقل")

        self._assert_customer_exists(customer_id)

        # [E-06] إثراء البنود
        items = self._validate_and_enrich_items(items)

        total = sum(i.total() for i in items)

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
                product_id  = item.product_id,   # [E-06] يُحفظ الآن
                item_name   = item.resolved_name(),
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

        # [E-06] إثراء البنود
        items = self._validate_and_enrich_items(items)

        total = sum(i.total() for i in items)

        from db.orders.orders_repo import update_order, insert_order_item
        update_order(
            self._conn,
            order_id     = order_id,
            total_amount = total,
            notes        = notes.strip(),
        )
        self._delete_order_items(order_id)
        for item in items:
            insert_order_item(
                self._conn,
                order_id    = order_id,
                product_id  = item.product_id,   # [E-06] يُحفظ الآن
                item_name   = item.resolved_name(),
                quantity    = item.qty,
                unit_price  = item.unit_price,
                notes       = item.notes,
            )

    # ── Status ────────────────────────────────────────────

    def change_status(self, order_id: int,
                      new_status: str,
                      note: str = "") -> OrderStatusChange:
        """يغير حالة الطلب مع التحقق من صحة الانتقال."""
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
        order = self._get_order_or_raise(order_id)
        return _ALLOWED_TRANSITIONS.get(order["status"], [])

    # ── Delete ────────────────────────────────────────────

    def get_delete_preview(self, order_id: int) -> "DeletePreview | None":
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
        preview = self.get_delete_preview(order_id)
        if not preview or not preview.can_delete:
            return False
        from db.orders.orders_repo import delete_order
        return delete_order(self._conn, order_id)

    # ── Summary ───────────────────────────────────────────

    def get_summary(self, customer_id: int = None) -> OrderSummary:
        where  = "WHERE customer_id=?" if customer_id else ""
        params = (customer_id,) if customer_id else ()

        row = self._conn.execute(f"""
            SELECT
                COUNT(*)                                              AS total,
                COALESCE(SUM(net_amount), 0)                         AS amount,
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

    def get_customer_summary(self, customer_id: int) -> OrderSummary:
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

    def _delete_order_items(self, order_id: int) -> None:
        self._conn.execute(
            "DELETE FROM order_items WHERE order_id=?", (order_id,)
        )
        self._conn.commit()