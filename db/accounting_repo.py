"""
db/accounting_repo.py
======================
Facade للتوافق مع الكود القديم — يُعيد تصدير كل الدوال من الملفات المقسّمة.

الملفات الفعلية:
  accounting_accounts_repo.py   → CRUD الحسابات والتصنيفات
  accounting_journal_repo.py    → CRUD القيود ودفتر الأستاذ
  accounting_statements_repo.py → القوائم المالية وميزان المراجعة
  accounting_inventory_repo.py  → ربط الشراء بالقيود
"""

# ── الحسابات وتصنيفاتها ──────────────────────────────────
from db.accounting.accounting_accounts_repo import (
    fetch_all_accounts,
    fetch_account,
    fetch_account_by_code,
    fetch_leaf_accounts,
    insert_account,
    update_account,
    delete_account,
    get_account_balance,
    get_account_natural_balance,
    get_normal_balance,
    calc_signed_amount,
    get_balances_by_type,
    fetch_all_groups,
    fetch_group,
    insert_group,
    update_group,
    delete_group,
    _get_group_descendants,
    build_group_tree,
)

# ── القيود ودفتر الأستاذ ─────────────────────────────────
from db.accounting.accounting_journal_repo import (
    next_ref_no,
    fetch_all_entries,
    fetch_entry,
    fetch_entry_lines,
    insert_entry,
    add_entry_lines,
    delete_entry,
    validate_entry_balance,
    fetch_t_account,
)

# ── القوائم المالية ──────────────────────────────────────
from db.accounting.accounting_statements_repo import (
    trial_balance,
    income_statement,
    balance_sheet,
    owners_equity_statement,
)

# ── ربط المخزن بالمحاسبة ────────────────────────────────
from db.accounting.accounting_inventory_repo import purchase_inventory

__all__ = [
    # accounts
    "fetch_all_accounts", "fetch_account", "fetch_account_by_code",
    "fetch_leaf_accounts", "insert_account", "update_account", "delete_account",
    "get_account_balance", "get_account_natural_balance", "get_normal_balance",
    "calc_signed_amount", "get_balances_by_type",
    # groups
    "fetch_all_groups", "fetch_group", "insert_group", "update_group",
    "delete_group", "_get_group_descendants", "build_group_tree",
    # journal
    "next_ref_no", "fetch_all_entries", "fetch_entry", "fetch_entry_lines",
    "insert_entry", "add_entry_lines", "delete_entry", "validate_entry_balance",
    "fetch_t_account",
    # statements
    "trial_balance", "income_statement", "balance_sheet", "owners_equity_statement",
    # inventory
    "purchase_inventory",
]