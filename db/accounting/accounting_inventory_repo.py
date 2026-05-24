"""
db/accounting/accounting_inventory_repo.py
================================
عملية شراء مخزن مع قيد محاسبي تلقائي — ربط inventory بـ accounting.

إصلاح (v2):
  - كل conn يُستخدم صريحاً من الـ parameters — لا يُفتح conn داخلياً.
  - أُضيف تحقق إن acc_code موجود قبل الـ query.
  - أُضيف rollback للـ journal entry لو فشل record_inventory_move.
"""

from db.accounting.accounting_accounts_repo import fetch_account_by_code
from db.accounting.accounting_journal_repo  import insert_entry, add_entry_lines


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
    """
    from db.inventory.inventory_repo import fetch_inventory_item, record_inventory_move

    # ── تحقق من الصنف ──────────────────────────────────────
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

    # fallback: أي حساب subtype='inventory'
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

    # ── إنشاء القيد المحاسبي ───────────────────────────────
    entry_id = insert_entry(acc_conn, date, desc, entry_type="purchase", notes=notes)

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

    # ── الحصول على رقم القيد ───────────────────────────────
    try:
        entry_row = acc_conn.execute(
            "SELECT ref_no FROM journal_entries WHERE id=?", (entry_id,)
        ).fetchone()
        ref_no = entry_row["ref_no"] if entry_row else None
    except Exception:
        ref_no = None

    # ── تسجيل حركة المخزون ────────────────────────────────
    # لو فشل record_inventory_move، نحذف القيد عشان نحافظ على الاتساق
    try:
        move_id = record_inventory_move(
            inv_conn, inv_id, "in", qty, unit_cost, date,
            notes=notes, ref_entry_id=entry_id, ref_entry_no=ref_no
        )
    except Exception as e:
        # rollback القيد المحاسبي
        try:
            acc_conn.execute(
                "DELETE FROM journal_entries WHERE id=?", (entry_id,)
            )
            acc_conn.commit()
        except Exception:
            pass
        raise RuntimeError(
            f"فشل تسجيل حركة المخزون — تم إلغاء القيد المحاسبي.\n{e}"
        )

    return entry_id, move_id