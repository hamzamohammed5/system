"""
services/accounting/inventory_posting_service.py
===================================================
Business Logic لعمليات المخزون التي تتطلب ترحيل قيد محاسبي معاً
(دومين عابر: مخزون + محاسبة في معاملة واحدة).

لماذا service منفصل عن InventoryService؟
  InventoryService (services/inventory/) هو الوحيد المسموح له استدعاء
  db.inventory.inventory_repo — مبدأ عزل صريح موثّق في رأس ذلك الملف.
  عمليات مثل الشراء (purchase) تُنشئ قيداً محاسبياً كاملاً (accounting.db)
  بالإضافة لحركة المخزون، عبر دالة واحدة في db.accounting.accounting_inventory_repo
  (وليس db.inventory) — فمكانها الطبيعي طبقة service محاسبية مستقلة،
  لا داخل InventoryService ولا مقحمة في AccountsService/JournalService
  (كلاهما لا يغطي منطقياً "شراء صنف مخزون + قيد" كوحدة واحدة).

الاستخدام:
    from services.accounting.inventory_posting_service import InventoryPostingService
    svc = InventoryPostingService(inv_conn, acc_conn)
    svc.purchase(inv_id, qty, unit_cost, date, payment_account_id, notes)
"""

from dataclasses import dataclass


@dataclass
class PurchaseResult:
    inv_id      : int
    qty         : float
    unit_cost   : float
    total_cost  : float


class InventoryPostingService:
    """
    Business Logic لعمليات مخزون تحتاج ترحيل محاسبي مرتبط (قيد + حركة).
    يقبل اتصالي المخزون والمحاسبة معاً، بنفس منطق InventoryService.
    """

    def __init__(self, inv_conn, acc_conn):
        self._inv_conn = inv_conn
        self._acc_conn = acc_conn

    def purchase(self, inv_id: int, qty: float, unit_cost: float,
                 date: str, payment_account_id: int,
                 notes: str = None) -> PurchaseResult:
        """
        يسجل عملية شراء/استلام مخزن: قيد محاسبي (مدين مخزون / دائن حساب
        الدفع) + حركة وارد في المخزون معاً، عبر
        db.accounting.accounting_inventory_repo.purchase_inventory —
        نقطة الدخول الوحيدة الموصى بها من tabs/ لهذه العملية، بدلاً من
        استدعاء db.accounting.accounting_inventory_repo مباشرة من UI.
        """
        if qty <= 0:
            raise ValueError("الكمية يجب أن تكون أكبر من صفر")
        if unit_cost < 0:
            raise ValueError("سعر الوحدة لا يكون سالباً")
        if not payment_account_id:
            raise ValueError("حساب الدفع مطلوب")

        from db.accounting.accounting_inventory_repo import purchase_inventory
        purchase_inventory(
            self._inv_conn, self._acc_conn,
            inv_id, qty, unit_cost, date, payment_account_id, notes,
        )

        return PurchaseResult(
            inv_id=inv_id, qty=qty, unit_cost=unit_cost,
            total_cost=qty * unit_cost,
        )
