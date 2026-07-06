"""
services/accounting/accounts_service.py
=========================================
Business Logic لحسابات الشجرة المحاسبية (accounts) وتصنيفاتها (account_groups).

يغطي الاستخدامات الموجودة سابقاً في:
  - ui/tabs/accounting/account_combo.py
  - ui/tabs/accounting/accounts_tree.py
  - ui/tabs/accounting/helpers.py (TYPE_AR / NORMAL_BALANCE تبقى تُقرأ من schema
    مباشرة لأنها ثوابت عرض وليست بيانات — لا تحتاج service)

الاستخدام:
    from services.accounting.accounts_service import AccountsService
    svc = AccountsService(conn)
    accounts = svc.list_leaf_accounts(acc_types=["asset"])
"""

from dataclasses import dataclass, field


# ══════════════════════════════════════════════════════════
# Dataclasses
# ══════════════════════════════════════════════════════════

@dataclass
class DeleteAccountPreview:
    account_id      : int
    account_name    : str
    has_lines       : bool
    lines_count     : int
    child_ids       : list = field(default_factory=list)
    can_delete      : bool = True
    reason          : str  = ""

    @property
    def child_count(self) -> int:
        return len(self.child_ids) - 1 if self.child_ids else 0

    def warning_text(self) -> str:
        if not self.can_delete:
            return f"⚠️ لا يمكن حذف الحساب «{self.account_name}» — {self.reason}"
        return f"هل تريد حذف الحساب «{self.account_name}»؟"


@dataclass
class DeleteGroupPreview:
    group_id     : int
    group_name   : str
    linked_count : int

    def warning_text(self) -> str:
        return f"هل تريد حذف التصنيف «{self.group_name}»؟"


# ══════════════════════════════════════════════════════════
# AccountsService
# ══════════════════════════════════════════════════════════

class AccountsService:
    """
    Business Logic لحسابات الشجرة المحاسبية وتصنيفاتها.
    يدير: قراءة/كتابة الحسابات، التصنيفات (groups)، وأرصدتها.
    """

    def __init__(self, conn):
        self._conn = conn

    # ── قراءة الحسابات ────────────────────────────────────

    def list_accounts_basic(self, acc_type: str = None) -> list:
        """حسابات بدون أرصدة — للـ dropdowns والـ combos."""
        from db.accounting.accounting_accounts_repo import fetch_all_accounts_basic
        return fetch_all_accounts_basic(self._conn, acc_type)

    def list_accounts_with_balance(self, acc_type: str = None) -> list:
        """حسابات مع أرصدتها — للتقارير والقوائم المالية."""
        from db.accounting.accounting_accounts_repo import fetch_all_accounts_with_balance
        return fetch_all_accounts_with_balance(self._conn, acc_type)

    def list_all_accounts(self, acc_type: str = None) -> list:
        """للتوافق — يستخدم fetch_all_accounts (= with_balance)."""
        from db.accounting.accounting_accounts_repo import fetch_all_accounts
        return fetch_all_accounts(self._conn, acc_type)

    def get_account(self, account_id: int):
        from db.accounting.accounting_accounts_repo import fetch_account
        return fetch_account(self._conn, account_id)

    def get_account_by_code(self, code: str):
        from db.accounting.accounting_accounts_repo import fetch_account_by_code
        return fetch_account_by_code(self._conn, code)

    def list_leaf_accounts(self, acc_types: list = None) -> list:
        """
        حسابات الأوراق (is_leaf=1) — تُستخدم في combo اختيار الحساب.
        acc_types: لو أكتر من نوع، بيفلتر بعد الجلب (مطابق لسلوك account_combo.py الأصلي).
        """
        from db.accounting.accounting_accounts_repo import fetch_leaf_accounts
        rows = list(fetch_leaf_accounts(self._conn))
        if acc_types:
            rows = [r for r in rows if r["type"] in acc_types]
        return rows

    # ── كتابة الحسابات ────────────────────────────────────

    def add_account(self, code: str, name: str, acc_type: str,
                    parent_id: int = None, group_id: int = None,
                    subtype: str = None, notes: str = None) -> int:
        name = (name or "").strip()
        code = (code or "").strip()
        if not name:
            raise ValueError("اسم الحساب مطلوب")
        if not code:
            raise ValueError("كود الحساب مطلوب")

        from db.accounting.accounting_accounts_repo import insert_account
        return insert_account(
            self._conn, code, name, acc_type,
            parent_id=parent_id, group_id=group_id,
            subtype=subtype, notes=notes,
        )

    def update_account(self, account_id: int, name: str,
                       group_id: int = None, notes: str = None):
        name = (name or "").strip()
        if not name:
            raise ValueError("اسم الحساب مطلوب")

        from db.accounting.accounting_accounts_repo import update_account
        update_account(self._conn, account_id, name, group_id=group_id, notes=notes)

    def get_delete_preview(self, account_id: int) -> DeleteAccountPreview | None:
        """
        يفحص إمكانية حذف الحساب: هل عليه قيود؟ هل له حسابات فرعية؟
        [نُقل من accounts_tree.py._delete — كان منطق SQL مباشر في الـ UI]
        """
        acc = self.get_account(account_id)
        if not acc:
            return None

        all_ids = self._get_all_descendant_ids(account_id)
        placeholders = ",".join("?" * len(all_ids))
        try:
            lines_count = self._conn.execute(
                f"SELECT COUNT(*) as c FROM journal_lines WHERE account_id IN ({placeholders})",
                all_ids
            ).fetchone()["c"]
        except Exception:
            lines_count = 0

        if lines_count:
            return DeleteAccountPreview(
                account_id=account_id, account_name=acc["name"],
                has_lines=True, lines_count=lines_count,
                child_ids=all_ids, can_delete=False,
                reason=f"يوجد {lines_count} قيد مرتبط بهذا الحساب أو حساباته الفرعية",
            )

        return DeleteAccountPreview(
            account_id=account_id, account_name=acc["name"],
            has_lines=False, lines_count=0,
            child_ids=all_ids, can_delete=True,
        )

    def delete_account_cascade(self, account_id: int) -> bool:
        """
        يحذف الحساب وكل حساباته الفرعية بعد التأكد من عدم وجود قيود.
        يرجع True لو نجح الحذف، False لو كان هناك قيود مرتبطة (can_delete=False).
        """
        preview = self.get_delete_preview(account_id)
        if not preview or not preview.can_delete:
            return False

        from db.accounting.accounting_accounts_repo import delete_account
        for del_id in reversed(preview.child_ids):
            delete_account(self._conn, del_id)
        return True

    def _get_all_descendant_ids(self, account_id: int) -> list:
        result = [account_id]
        children = self._conn.execute(
            "SELECT id FROM accounts WHERE parent_id=?", (account_id,)
        ).fetchall()
        for child in children:
            result.extend(self._get_all_descendant_ids(child["id"]))
        return result

    # ── أرصدة الحسابات ────────────────────────────────────

    def get_account_balance(self, account_id: int) -> float:
        from db.accounting.accounting_accounts_repo import get_account_balance
        return get_account_balance(self._conn, account_id)

    def get_account_natural_balance(self, account_id: int) -> float:
        from db.accounting.accounting_accounts_repo import get_account_natural_balance
        return get_account_natural_balance(self._conn, account_id)

    def get_normal_balance(self, acc_type: str) -> str:
        from db.accounting.accounting_accounts_repo import get_normal_balance
        return get_normal_balance(acc_type)

    def calc_signed_amount(self, acc_type: str, increase: bool, amount: float) -> tuple:
        from db.accounting.accounting_accounts_repo import calc_signed_amount
        return calc_signed_amount(acc_type, increase, amount)

    def get_balances_by_type(self) -> dict:
        from db.accounting.accounting_accounts_repo import get_balances_by_type
        return get_balances_by_type(self._conn)

    # ── تصنيفات الحسابات (account_groups) ─────────────────

    def list_groups(self, acc_type: str = None) -> list:
        from db.accounting.accounting_accounts_repo import fetch_all_groups
        return fetch_all_groups(self._conn, acc_type)

    def get_group(self, group_id: int):
        from db.accounting.accounting_accounts_repo import fetch_group
        return fetch_group(self._conn, group_id)

    def build_group_tree(self, rows) -> list:
        from db.accounting.accounting_accounts_repo import build_group_tree
        return build_group_tree(rows)

    def get_group_descendants(self, group_id: int) -> set:
        """
        Wrapper رسمي حول الدالة الـ private في الـ repo — أي كود UI
        يحتاج descendants يستدعي هذه الدالة بدل استيراد _get_group_descendants مباشرة.
        """
        from db.accounting.accounting_accounts_repo import _get_group_descendants
        return _get_group_descendants(self._conn, group_id)

    def add_group(self, name: str, acc_type: str,
                 parent_id: int = None, color: str = "#607d8b") -> int:
        name = (name or "").strip()
        if not name:
            raise ValueError("اسم التصنيف مطلوب")

        from db.accounting.accounting_accounts_repo import insert_group
        return insert_group(self._conn, name, acc_type, parent_id=parent_id, color=color)

    def update_group(self, group_id: int, name: str,
                     parent_id: int = None, color: str = "#607d8b"):
        name = (name or "").strip()
        if not name:
            raise ValueError("اسم التصنيف مطلوب")

        from db.accounting.accounting_accounts_repo import update_group
        update_group(self._conn, group_id, name, parent_id=parent_id, color=color)

    def get_group_delete_preview(self, group_id: int) -> DeleteGroupPreview | None:
        grp = self.get_group(group_id)
        if not grp:
            return None
        try:
            count = self._conn.execute(
                "SELECT COUNT(*) as c FROM accounts WHERE group_id=?", (group_id,)
            ).fetchone()["c"]
        except Exception:
            count = 0
        return DeleteGroupPreview(group_id=group_id, group_name=grp["name"], linked_count=count)

    def delete_group(self, group_id: int):
        from db.accounting.accounting_accounts_repo import delete_group
        delete_group(self._conn, group_id)

    def count_accounts_in_group(self, group_id: int) -> int:
        """يُستخدم في group_manager.py لعرض عدد الحسابات لكل تصنيف في الشجرة."""
        try:
            return self._conn.execute(
                "SELECT COUNT(*) as c FROM accounts WHERE group_id=? AND is_leaf=1",
                (group_id,)
            ).fetchone()["c"]
        except Exception:
            return 0
