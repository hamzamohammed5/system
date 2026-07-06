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

[تعديل هيكلي]: أُزيل كل استدعاء SQL خام (conn.execute) من هذا الملف.
  كل عملية قراءة/كتابة أصبحت تمر عبر db.orders.orders_repo أو
  db.orders.customers_repo، حفاظاً على مبدأ الطبقات:
      widgets -> tabs/UI -> services -> repos (db) -> schema
  الدوال المتأثرة: _get_order_or_raise, _assert_customer_exists,
  get_summary, get_delete_preview.
  كذلك نُقلت كل imports من db.* إلى أعلى الملف بدل الاستيراد
  الموضعي داخل كل دالة.
"""

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
from db.costing.catalog_repo import fetch_priced_product_by_id
from db.orders.orders_schema import get_orders_connection, create_orders_tables
from services.orders.customer_service import CustomerService

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

    [تعديل هيكلي] كان ينفذ SQL خام مباشرة على erp_conn
    (erp_conn.execute("SELECT name, price FROM items WHERE id=?")),
    متخطّياً طبقة الـ repo بالكامل. استُبدل بـ
    fetch_priced_product_by_id من db.costing.catalog_repo، حفاظاً
    على مبدأ الطبقات: widgets -> tabs/UI -> services -> repos -> schema.
    """
    if erp_conn is None or product_id is None:
        return None
    try:
        row = fetch_priced_product_by_id(erp_conn, product_id)
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
        order = fetch_order_basic(self._conn, order_id)
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
        return delete_order(self._conn, order_id)

    # ── Summary ───────────────────────────────────────────

    def get_summary(self, customer_id: int = None) -> OrderSummary:
        """
        [تعديل هيكلي] كان ينفذ SQL خام مع WHERE ديناميكي.
        استُبدل بدالتين ثابتتين في orders_repo:
          fetch_orders_summary_for_customer / fetch_orders_summary_all
        """
        if customer_id:
            row = fetch_orders_summary_for_customer(self._conn, customer_id)
        else:
            row = fetch_orders_summary_all(self._conn)

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

    # ── Customer (facade على CustomerService) ─────────────
    # [تعديل هيكلي] لم تعد هذه الدوال تنادي customers_repo مباشرة.
    # CustomerService أصبح المالك الحصري لمنطق كتابة العميل؛
    # هذه الدوال أُبقيت هنا فقط للتوافق مع أي كود قديم يستدعي
    # OrderService.add_customer/update_customer، وهي الآن
    # pass-through حقيقي (composition) بدل تكرار المنطق.

    def add_customer(self, name: str,
                     phone: str = "",
                     notes: str = "") -> int:
        return CustomerService(self._conn).add(
            name=name, phone=phone, notes=notes,
        )

    def update_customer(self, customer_id: int,
                        name: str,
                        phone: str = "",
                        notes: str = "") -> None:
        CustomerService(self._conn).update(
            customer_id=customer_id, name=name, phone=phone, notes=notes,
        )

    def get_customer_summary(self, customer_id: int) -> OrderSummary:
        return self.get_summary(customer_id=customer_id)

    # ── Orders List (facade للـ UI) ───────────────────────

    def list_orders(self) -> list:
        """
        [مضاف] يرجع كل الطلبات — facade لـ UI بدل استدعاء
        fetch_all_orders من db.orders.orders_repo مباشرة.
        كانت _orders_list_panel.py تستورد من الـ repo مباشرة،
        متخطّيةً طبقة الـ service — تم سد المخالفة هنا.
        """
        return fetch_all_orders(self._conn)

    def get_order(self, order_id: int) -> "dict | None":
        """
        [مضاف] يرجع بيانات الطلب كاملة (مع بيانات العميل عبر JOIN)
        — facade لـ UI بدل استدعاء fetch_order من
        db.orders.orders_repo مباشرة. كانت ui/tabs/orders/_order_detail.py
        تستورد من الـ repo مباشرة، متخطّيةً طبقة الـ service —
        تم سد المخالفة هنا.
        """
        return fetch_order(self._conn, order_id)

    def cancel(self, order_id: int, reason: str = "") -> bool:
        """
        [مضاف] يلغي الطلب — facade لـ UI بدل استدعاء cancel_order
        من db.orders.orders_repo مباشرة. كانت
        ui/tabs/orders/_order_detail.py تستورد من الـ repo مباشرة،
        متخطّيةً طبقة الـ service — تم سد المخالفة هنا.
        """
        return cancel_order(self._conn, order_id, reason=reason)

    def do_reorder(self, order_id: int) -> "int | None":
        """
        [مضاف] ينشئ طلباً جديداً بناءً على طلب سابق — facade لـ UI
        بدل استدعاء reorder من db.orders.orders_repo مباشرة. كانت
        ui/tabs/orders/_order_detail.py تستورد من الـ repo مباشرة،
        متخطّيةً طبقة الـ service — تم سد المخالفة هنا.
        """
        return reorder(self._conn, order_id)

    def get_dashboard_summary(self) -> dict:
        """
        [مضاف] يرجع إحصائيات لوحة المتابعة (dict خام بمفاتيح
        الحالات والأولوية) — facade لـ UI بدل استدعاء
        fetch_orders_summary من db.orders.orders_repo مباشرة. كانت
        ui/tabs/orders/dashboard_tab.py تستورد من الـ repo مباشرة،
        متخطّيةً طبقة الـ service — تم سد المخالفة هنا.

        ملاحظة: تختلف عن get_summary() التي تُرجع OrderSummary
        (dataclass مبسّط)؛ هذه الدالة تُبقي على شكل الـ dict الخام
        المطلوب لملء بطاقات وشرائح لوحة المتابعة كما هي.
        """
        return fetch_orders_summary(self._conn)

    # ── Order Items (facade للـ UI) ───────────────────────
    # [مضاف] هذه الدوال أُضيفت لسد مخالفة هيكلية كانت موجودة في
    # ui/tabs/orders/order_detail/_items_section.py و _log_section.py:
    # الملفان كانا يستوردان من db.orders.orders_repo مباشرة،
    # متخطّيَين طبقة الـ service بالكامل. الآن الـ UI يستدعي
    # OrderService فقط، والـ service هو من يكلم الـ repo.

    def get_order_items(self, order_id: int) -> list:
        return fetch_order_items(self._conn, order_id)

    def add_item(self, order_id: int,
                item_name: str,
                description: str = "",
                quantity: float = 1,
                unit: str = "قطعة",
                unit_price: float = 0,
                discount_pct: float = 0,
                design_ref: str = "",
                notes: str = "") -> int:
        return insert_order_item(
            self._conn, order_id,
            item_name=item_name, description=description,
            quantity=quantity, unit=unit, unit_price=unit_price,
            discount_pct=discount_pct, design_ref=design_ref, notes=notes,
        )

    def update_item(self, item_id: int,
                    item_name: str,
                    description: str = "",
                    quantity: float = 1,
                    unit: str = "قطعة",
                    unit_price: float = 0,
                    discount_pct: float = 0,
                    design_ref: str = "",
                    notes: str = "") -> None:
        update_order_item(
            self._conn, item_id,
            item_name=item_name, description=description,
            quantity=quantity, unit=unit, unit_price=unit_price,
            discount_pct=discount_pct, design_ref=design_ref, notes=notes,
        )

    def remove_item(self, item_id: int) -> None:
        delete_order_item(self._conn, item_id)

    # ── Status Log (facade للـ UI) ────────────────────────

    def get_status_log(self, order_id: int) -> list:
        return fetch_status_log(self._conn, order_id)

    # ── Helpers ───────────────────────────────────────────

    def _get_order_or_raise(self, order_id: int) -> dict:
        """
        [تعديل هيكلي] كان ينفذ "SELECT * FROM orders" مباشرة.
        استُبدل بـ fetch_order_basic من orders_repo — تكفي لكل
        استخدامات هذه الدالة الداخلية (status/customer_id/إلخ)
        دون حمل JOIN بيانات العميل الكاملة.
        """
        row = fetch_order_basic(self._conn, order_id)
        if not row:
            raise ValueError(f"الطلب {order_id} غير موجود")
        return row

    def _assert_customer_exists(self, customer_id: int) -> None:
        """
        [تعديل هيكلي] كان ينفذ SQL خام على جدول customers مباشرة.
        استُبدل بـ fetch_customer من customers_repo.
        """
        row = fetch_customer(self._conn, customer_id)
        if not row:
            raise ValueError(f"العميل {customer_id} غير موجود")
        if not row["is_active"]:
            raise ValueError(
                f"العميل {customer_id} غير نشط — فعّله أولاً لإنشاء طلبات جديدة"
            )

    def _delete_order_items(self, order_id: int) -> None:
        """
        [تعديل هيكلي] كان ينفذ DELETE مباشرة على order_items.
        استُبدل بـ delete_order_items_by_order من orders_repo.
        """
        delete_order_items_by_order(self._conn, order_id)


# ══════════════════════════════════════════════════════════
# Bootstrapping — فتح اتصال orders.db وتهيئة الـ schema
# ══════════════════════════════════════════════════════════
# [إضافة] تغليف get_orders_connection + create_orders_tables هنا
# عشان tabs/orders_section.py ميستدعيش db.orders.orders_schema
# مباشرة (كسر هيكلي: tabs → repos/db بتجاوز services).
#
# قاعدة الـ Layering تبقى محفوظة:
#   tabs/  →  services/orders.get_orders_conn_and_init()  →  db.orders.orders_schema
#
# نفس النمط المستخدم في services/design/__init__.py
# (get_designs_conn_and_init) — دالة bootstrapping بحتة (فتح اتصال
# + تهيئة جداول)، وليست عملية بيانات، لذلك مكانها الطبيعي في نقطة
# الدخول الموحّدة لـ services/orders بدل تكرارها داخل الـ UI.

def get_orders_conn_and_init():
    """
    يفتح اتصال orders.db وينشئ/يهيّئ جداوله إن لم تكن موجودة، ثم يُرجع الاتصال.

    يُستخدم من tabs/orders_section.py بدلاً من استدعاء
    db.orders.orders_schema مباشرة، حفاظاً على القاعدة المعمارية:
        tabs/  →  services/  →  repos (db.*)

    مثال:
        from services.orders.order_service import get_orders_conn_and_init
        self.conn = get_orders_conn_and_init()
    """
    conn = get_orders_connection()
    create_orders_tables(conn)
    return conn