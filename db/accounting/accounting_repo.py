"""
db/accounting/accounting_repo.py
======================
Facade للتوافق مع الكود القديم — يُعيد تصدير كل الدوال من الملفات المقسّمة.

الملفات الفعلية:
  accounting_accounts_repo.py   → CRUD الحسابات والتصنيفات
  accounting_journal_repo.py    → CRUD القيود ودفتر الأستاذ
  accounting_statements_repo.py → القوائم المالية وميزان المراجعة
  accounting_inventory_repo.py  → ربط الشراء بالقيود
  accounting_audit_repo.py      → Audit Log للعمليات الحساسة [مقترح 52]

تحسين 14: حذف _get_group_descendants من الـ __all__ وقائمة الـ imports
           لأنها private function (تبدأ بـ _) ولا يجب تصديرها من الـ facade.
           الكود الذي يحتاجها يجب أن يستوردها مباشرة من accounting_accounts_repo.
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
    # [تحسين 14] _get_group_descendants محذوفة من هنا — هي private function.
    # الكود الذي يحتاجها يستوردها مباشرة من accounting_accounts_repo:
    #   from db.accounting.accounting_accounts_repo import _get_group_descendants
    build_group_tree,
)

# ── القيود ودفتر الأستاذ ─────────────────────────────────
from db.accounting.accounting_journal_repo import (
    next_ref_no,
    fetch_all_entries,
    fetch_entries_count,
    fetch_all_entries_paginated,
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

# ── Audit Log [مقترح 52] ─────────────────────────────────
from db.accounting.accounting_audit_repo import (
    create_audit_log_table,
    log_action,
    log_delete,
    log_update,
    log_create,
    snapshot_journal_entry,
    snapshot_account,
    snapshot_row,
    fetch_audit_log,
    fetch_audit_log_count,
    fetch_record_history,
)

__all__ = [
    # accounts
    "fetch_all_accounts", "fetch_account", "fetch_account_by_code",
    "fetch_leaf_accounts", "insert_account", "update_account", "delete_account",
    "get_account_balance", "get_account_natural_balance", "get_normal_balance",
    "calc_signed_amount", "get_balances_by_type",
    # groups
    "fetch_all_groups", "fetch_group", "insert_group", "update_group",
    "delete_group",
    # [تحسين 14] "_get_group_descendants" محذوفة — private function لا تُصدَّر
    "build_group_tree",
    # journal
    "next_ref_no", "fetch_all_entries", "fetch_entries_count",
    "fetch_all_entries_paginated",
    "fetch_entry", "fetch_entry_lines",
    "insert_entry", "add_entry_lines", "delete_entry", "validate_entry_balance",
    "fetch_t_account",
    # statements
    "trial_balance", "income_statement", "balance_sheet", "owners_equity_statement",
    # inventory
    "purchase_inventory",
    # audit log [مقترح 52]
    "create_audit_log_table",
    "log_action", "log_delete", "log_update", "log_create",
    "snapshot_journal_entry", "snapshot_account", "snapshot_row",
    "fetch_audit_log", "fetch_audit_log_count", "fetch_record_history",
]