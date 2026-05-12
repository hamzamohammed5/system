"""
db/accounting/accounting_inventory_repo.py
================================
عملية شراء مخزن مع قيد محاسبي تلقائي — ربط inventory بـ accounting.
"""

from db.accounting.accounting_accounts_repo import fetch_account_by_code
from db.accounting.accounting_journal_repo  import insert_entry, add_entry_lines


def purchase_inventory(inv_conn, acc_conn,
                       inv_id: int, qty: float, unit_cost: float,
                       date: str, payment_account_id: int,
                       notes: str = None) -> tuple:
    from db.inventory_repo import fetch_inventory_item, record_inventory_move

    inv = fetch_inventory_item(inv_conn, inv_id)
    if not inv:
        raise ValueError(f"الصنف {inv_id} غير موجود")

    total_cost = qty * unit_cost
    inv_name   = inv["name"]
    inv_unit   = inv["unit"]
    acc_code   = inv.get("account_code") or "114"

    desc     = f"شراء {qty:.4g} {inv_unit} من «{inv_name}»"
    entry_id = insert_entry(acc_conn, date, desc, entry_type="purchase", notes=notes)

    inv_account = fetch_account_by_code(acc_conn, acc_code)
    inv_acc_id  = inv_account["id"] if inv_account else None
    if not inv_acc_id:
        row = acc_conn.execute(
            "SELECT id FROM accounts WHERE subtype='inventory' AND is_leaf=1 LIMIT 1"
        ).fetchone()
        inv_acc_id = row["id"] if row else None

    lines = [
        {"account_id": inv_acc_id,         "debit": total_cost, "credit": 0,          "description": desc},
        {"account_id": payment_account_id,  "debit": 0,          "credit": total_cost, "description": desc},
    ]
    add_entry_lines(acc_conn, entry_id, lines)

    entry_row = acc_conn.execute(
        "SELECT ref_no FROM journal_entries WHERE id=?", (entry_id,)
    ).fetchone()
    ref_no = entry_row["ref_no"] if entry_row else None

    move_id = record_inventory_move(
        inv_conn, inv_id, "in", qty, unit_cost, date,
        notes=notes, ref_entry_id=entry_id, ref_entry_no=ref_no
    )
    return entry_id, move_id