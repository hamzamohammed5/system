"""
db/accounting/accounting_inventory_repo.py
==========================================
عملية شراء مخزن مع قيد محاسبي تلقائي — ربط inventory بـ accounting.

إصلاح 32: rollback محصّن بالكامل:
  - لو فشل record_inventory_move → نحاول حذف القيد
  - لو فشل الـ rollback نفسه → نسجّل CRITICAL log (بيانات غير متسقة)
    بدلاً من إخفاء الخطأ أو رفع exception غامض
  - entry_id=None guard يمنع rollback بدون قيد حقيقي
"""

import logging

from db.accounting.accounting_accounts_repo import fetch_account_by_code
from db.accounting.accounting_journal_repo  import insert_entry, add_entry_lines

logger = logging.getLogger(__name__)


def purchase_inventory(inv_conn, acc_conn,
                       inv_id: int, qty: float, unit_cost: float,
                       date: str, payment_account_id: int,
                       notes: str = None) -> tuple:
    """
    يسجل عملية شراء مخزن وقيدها المحاسبي في نفس الوقت.

    Parameters:
        inv_conn           : connection لـ inventory.db
        acc_conn           : connection لـ accounting.db
        inv_id             : ID الصنف في inventory
        qty                : الكمية
        unit_cost          : سعر الوحدة
        date               : تاريخ العملية (YYYY-MM-DD)
        payment_account_id : حساب الدفع (صندوق / بنك)
        notes              : ملاحظات اختيارية

    Returns:
        (entry_id, move_id)

    Raises:
        ValueError  : لو البيانات غير صحيحة (صنف غير موجود، حساب غير موجود)
        RuntimeError: لو فشل التسجيل — يحاول rollback القيد المحاسبي
    """
    from db.inventory.inventory_repo import fetch_inventory_item, record_inventory_move

    # ── تحقق من المدخلات ────────────────────────────────────
    if qty <= 0:
        raise ValueError(f"الكمية يجب أن تكون أكبر من صفر (المُدخل: {qty})")
    if unit_cost < 0:
        raise ValueError(f"سعر الوحدة لا يمكن أن يكون سالباً (المُدخل: {unit_cost})")

    inv = fetch_inventory_item(inv_conn, inv_id)
    if not inv:
        raise ValueError(f"الصنف {inv_id} غير موجود في المخزن")

    total_cost = qty * unit_cost
    inv_name   = inv["name"]
    inv_unit   = inv.get("unit", "وحدة")
    acc_code   = inv.get("account_code") or "114"

    desc = f"شراء {qty:.4g} {inv_unit} من «{inv_name}»"

    # ── إيجاد حساب المخزون ─────────────────────────────────
    inv_acc_id = None
    if acc_code:
        inv_account = fetch_account_by_code(acc_conn, acc_code)
        if inv_account:
            inv_acc_id = inv_account["id"]

    if not inv_acc_id:
        try:
            row = acc_conn.execute(
                "SELECT id FROM accounts WHERE subtype='inventory' AND is_leaf=1 LIMIT 1"
            ).fetchone()
            inv_acc_id = row["id"] if row else None
        except Exception:
            pass

    if not inv_acc_id:
        raise ValueError(
            f"لم يُعثر على حساب مخزون مناسب (كود: {acc_code})\n"
            "تأكد من وجود حساب subtype='inventory' في شجرة الحسابات."
        )

    if not payment_account_id:
        raise ValueError("يجب تحديد حساب الدفع (صندوق / بنك)")

    # ── المرحلة 1: إنشاء القيد المحاسبي ────────────────────
    entry_id: int | None = None
    try:
        entry_id = insert_entry(acc_conn, date, desc,
                                entry_type="purchase", notes=notes)
        lines = [
            {
                "account_id":  inv_acc_id,
                "debit":       total_cost,
                "credit":      0,
                "description": desc,
            },
            {
                "account_id":  payment_account_id,
                "debit":       0,
                "credit":      total_cost,
                "description": desc,
            },
        ]
        add_entry_lines(acc_conn, entry_id, lines)
    except Exception as e:
        # فشل قبل أي كتابة في inventory → لا يحتاج rollback
        raise ValueError(f"فشل إنشاء القيد المحاسبي: {e}") from e

    # ── الحصول على رقم القيد ────────────────────────────────
    ref_no: str | None = None
    try:
        entry_row = acc_conn.execute(
            "SELECT ref_no FROM journal_entries WHERE id=?", (entry_id,)
        ).fetchone()
        ref_no = entry_row["ref_no"] if entry_row else None
    except Exception:
        pass  # ref_no اختياري — لا يوقف العملية

    # ── المرحلة 2: تسجيل حركة المخزون ──────────────────────
    # لو هذه المرحلة فشلت نُلغي القيد المحاسبي
    try:
        move_id = record_inventory_move(
            inv_conn, inv_id, "in", qty, unit_cost, date,
            notes=notes, ref_entry_id=entry_id, ref_entry_no=ref_no
        )
    except Exception as inv_err:
        # ── محاولة rollback القيد المحاسبي ──────────────────
        rollback_ok = False
        try:
            acc_conn.execute(
                "DELETE FROM journal_entries WHERE id=?", (entry_id,)
            )
            acc_conn.commit()
            rollback_ok = True
        except Exception as rb_err:
            # الحالة الأسوأ: فشل الـ rollback → بيانات غير متسقة
            logger.critical(
                "CRITICAL DATA INCONSISTENCY: "
                "journal_entry id=%d orphaned after inventory move failure. "
                "inventory_error=%s | rollback_error=%s | "
                "inv_id=%d qty=%s unit_cost=%s date=%s",
                entry_id, inv_err, rb_err,
                inv_id, qty, unit_cost, date,
            )
            raise RuntimeError(
                f"فشل تسجيل حركة المخزون وفشل إلغاء القيد المحاسبي.\n"
                f"القيد رقم {entry_id} يحتاج مراجعة يدوية.\n"
                f"خطأ المخزون: {inv_err}\n"
                f"خطأ الإلغاء: {rb_err}"
            ) from rb_err

        if rollback_ok:
            raise RuntimeError(
                f"فشل تسجيل حركة المخزون — تم إلغاء القيد المحاسبي تلقائياً.\n"
                f"السبب: {inv_err}"
            ) from inv_err

    return entry_id, move_id