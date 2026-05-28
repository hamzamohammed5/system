"""
services/accounting/journal_service.py
========================================
Business Logic للقيود المحاسبية.

الاستخدام:
    from services.accounting.journal_service import JournalService
    svc = JournalService(conn)
    entry_id = svc.post_entry(entry_data, lines)
"""

from dataclasses import dataclass, field
from datetime import datetime


# ══════════════════════════════════════════════════════════
# Dataclasses
# ══════════════════════════════════════════════════════════

@dataclass
class JournalLine:
    account_id : int
    dr         : float = 0.0
    cr         : float = 0.0
    note       : str   = ""

    def is_valid(self) -> bool:
        """صف واحد فيه dr أو cr — مش الاتنين مع بعض."""
        return (self.dr > 0) != (self.cr > 0)

    def amount(self) -> float:
        return self.dr if self.dr > 0 else self.cr

    def side(self) -> str:
        return "dr" if self.dr > 0 else "cr"


@dataclass
class BalanceCheck:
    total_dr    : float
    total_cr    : float

    @property
    def is_balanced(self) -> bool:
        return abs(self.total_dr - self.total_cr) < 0.001

    @property
    def diff(self) -> float:
        return abs(self.total_dr - self.total_cr)

    def error_text(self) -> str | None:
        if not self.is_balanced:
            return (
                f"الفرق = {self.diff:,.2f} — "
                "المدين والدائن غير متساويين"
            )
        return None


@dataclass
class EntryResult:
    entry_id    : int
    is_new      : bool
    total_dr    : float
    total_cr    : float
    lines_count : int


@dataclass
class DeletePreview:
    entry_id   : int
    entry_ref  : str
    is_posted  : bool
    can_delete : bool
    reason     : str = ""

    def warning_text(self) -> str:
        if not self.can_delete:
            return f"⚠️ لا يمكن حذف القيد «{self.entry_ref}» — {self.reason}"
        return f"هل تريد حذف القيد «{self.entry_ref}»؟"


@dataclass
class AccountBalance:
    account_id   : int
    account_name : str
    total_dr     : float
    total_cr     : float

    @property
    def balance(self) -> float:
        return self.total_dr - self.total_cr

    @property
    def side(self) -> str:
        return "dr" if self.balance >= 0 else "cr"


# ══════════════════════════════════════════════════════════
# JournalService
# ══════════════════════════════════════════════════════════

class JournalService:
    """
    Business Logic للقيود المحاسبية.
    يدير: إنشاء / تعديل / حذف / عكس القيود + حساب الأرصدة.
    """

    def __init__(self, conn):
        self._conn = conn

    # ── Validation ────────────────────────────────────────

    def check_balance(self,
                      lines: list[JournalLine]) -> BalanceCheck:
        """يتحقق من توازن القيد."""
        total_dr = sum(l.dr for l in lines)
        total_cr = sum(l.cr for l in lines)
        return BalanceCheck(total_dr=total_dr, total_cr=total_cr)

    def validate_lines(self,
                       lines: list[JournalLine]) -> list[str]:
        """
        يتحقق من صحة الصفوف.
        يرجع list من رسائل الخطأ — فاضية لو كل شيء تمام.
        """
        errors = []

        if not lines:
            errors.append("القيد يجب أن يحتوي على صف واحد على الأقل")
            return errors

        for i, line in enumerate(lines, 1):
            if not line.account_id:
                errors.append(f"الصف {i}: الحساب مطلوب")
            if line.dr < 0 or line.cr < 0:
                errors.append(f"الصف {i}: المبالغ لا تكون سالبة")
            if line.dr == 0 and line.cr == 0:
                errors.append(f"الصف {i}: أدخل مدين أو دائن")
            if line.dr > 0 and line.cr > 0:
                errors.append(f"الصف {i}: لا يمكن إدخال مدين ودائن معاً")

        balance = self.check_balance(lines)
        if not balance.is_balanced:
            errors.append(balance.error_text())

        return errors

    # ── Read ──────────────────────────────────────────────

    def get_account_balance(self, account_id: int,
                            date_from: str = None,
                            date_to: str = None) -> AccountBalance:
        """يحسب رصيد حساب في نطاق تاريخ."""
        where  = "WHERE jl.account_id = ?"
        params = [account_id]

        if date_from:
            where  += " AND je.date >= ?"
            params.append(date_from)
        if date_to:
            where  += " AND je.date <= ?"
            params.append(date_to)

        row = self._conn.execute(f"""
            SELECT
                a.id,
                a.name,
                COALESCE(SUM(jl.dr), 0) AS total_dr,
                COALESCE(SUM(jl.cr), 0) AS total_cr
            FROM journal_lines jl
            JOIN journal_entries je ON je.id = jl.entry_id
            JOIN accounts a ON a.id = jl.account_id
            {where}
            GROUP BY a.id, a.name
        """, params).fetchone()

        if not row:
            # الحساب موجود بس ما فيش حركات
            acc = self._conn.execute(
                "SELECT id, name FROM accounts WHERE id=?",
                (account_id,)
            ).fetchone()
            name = acc["name"] if acc else f"حساب {account_id}"
            return AccountBalance(
                account_id   = account_id,
                account_name = name,
                total_dr     = 0.0,
                total_cr     = 0.0,
            )

        return AccountBalance(
            account_id   = row["id"],
            account_name = row["name"],
            total_dr     = float(row["total_dr"]),
            total_cr     = float(row["total_cr"]),
        )

    # ── Post Entry ────────────────────────────────────────

    def post_entry(self, entry_data: dict,
                   lines: list[JournalLine]) -> EntryResult:
        """
        يسجل قيد محاسبي جديد.

        entry_data: {
            "date":        str,   ← "YYYY-MM-DD"
            "description": str,
            "ref":         str,   ← اختياري
        }
        """
        # تحقق من الصفوف
        errors = self.validate_lines(lines)
        if errors:
            raise ValueError("\n".join(errors))

        date = entry_data.get("date") or \
               datetime.now().strftime("%Y-%m-%d")
        desc = entry_data.get("description", "").strip()
        ref  = entry_data.get("ref", "").strip()

        if not desc:
            raise ValueError("وصف القيد مطلوب")

        from db.accounting.accounting_journal_repo import (
            insert_journal_entry,
            insert_journal_line,
        )

        entry_id = insert_journal_entry(
            self._conn,
            date        = date,
            description = desc,
            ref         = ref,
        )

        for line in lines:
            insert_journal_line(
                self._conn,
                entry_id   = entry_id,
                account_id = line.account_id,
                dr         = line.dr,
                cr         = line.cr,
                note       = line.note,
            )

        balance = self.check_balance(lines)
        return EntryResult(
            entry_id    = entry_id,
            is_new      = True,
            total_dr    = balance.total_dr,
            total_cr    = balance.total_cr,
            lines_count = len(lines),
        )

    def update_entry(self, entry_id: int,
                     entry_data: dict,
                     lines: list[JournalLine]) -> EntryResult:
        """
        يحدث قيد موجود — بيمسح الصفوف القديمة ويكتب الجديدة.
        بيتحقق إن القيد مش مقفول.
        """
        entry = self._get_entry_or_raise(entry_id)
        if entry.get("is_locked"):
            raise ValueError("القيد مقفول ولا يمكن تعديله")

        errors = self.validate_lines(lines)
        if errors:
            raise ValueError("\n".join(errors))

        from db.accounting.accounting_journal_repo import (
            update_journal_entry,
            delete_journal_lines,
            insert_journal_line,
        )

        update_journal_entry(
            self._conn,
            entry_id    = entry_id,
            date        = entry_data.get("date"),
            description = entry_data.get("description", "").strip(),
            ref         = entry_data.get("ref", "").strip(),
        )

        delete_journal_lines(self._conn, entry_id)
        for line in lines:
            insert_journal_line(
                self._conn,
                entry_id   = entry_id,
                account_id = line.account_id,
                dr         = line.dr,
                cr         = line.cr,
                note       = line.note,
            )

        balance = self.check_balance(lines)
        return EntryResult(
            entry_id    = entry_id,
            is_new      = False,
            total_dr    = balance.total_dr,
            total_cr    = balance.total_cr,
            lines_count = len(lines),
        )

    # ── Reverse ───────────────────────────────────────────

    def reverse_entry(self, entry_id: int,
                      note: str = "") -> EntryResult:
        """
        ينشئ قيد عكسي للقيد المحدد.
        يرجع EntryResult للقيد الجديد.
        """
        entry = self._get_entry_or_raise(entry_id)

        # جيب صفوف القيد الأصلي
        lines_rows = self._conn.execute(
            "SELECT account_id, dr, cr, note "
            "FROM journal_lines WHERE entry_id=?",
            (entry_id,)
        ).fetchall()

        if not lines_rows:
            raise ValueError("القيد لا يحتوي على صفوف")

        # اعكس DR و CR
        reversed_lines = [
            JournalLine(
                account_id = r["account_id"],
                dr         = r["cr"],   # الدائن يصبح مدين
                cr         = r["dr"],   # المدين يصبح دائن
                note       = r["note"],
            )
            for r in lines_rows
        ]

        desc = f"عكس القيد #{entry_id}"
        if note:
            desc += f" — {note}"

        return self.post_entry(
            entry_data = {
                "date":        datetime.now().strftime("%Y-%m-%d"),
                "description": desc,
                "ref":         entry.get("ref", ""),
            },
            lines = reversed_lines,
        )

    # ── Delete ────────────────────────────────────────────

    def get_delete_preview(self,
                           entry_id: int) -> DeletePreview | None:
        """يرجع معلومات الحذف قبل التنفيذ."""
        entry = self._conn.execute(
            "SELECT id, description, is_locked "
            "FROM journal_entries WHERE id=?",
            (entry_id,)
        ).fetchone()

        if not entry:
            return None

        ref       = entry["description"] or f"#{entry_id}"
        is_locked = bool(entry["is_locked"])

        if is_locked:
            return DeletePreview(
                entry_id   = entry_id,
                entry_ref  = ref,
                is_posted  = True,
                can_delete = False,
                reason     = "القيد مقفول",
            )

        return DeletePreview(
            entry_id   = entry_id,
            entry_ref  = ref,
            is_posted  = False,
            can_delete = True,
        )

    def delete(self, entry_id: int) -> bool:
        """
        يحذف القيد وكل صفوفه.
        يرجع True لو نجح، False لو مقفول.
        """
        preview = self.get_delete_preview(entry_id)
        if not preview or not preview.can_delete:
            return False

        from db.accounting.accounting_journal_repo import (
            delete_journal_entry
        )
        delete_journal_entry(self._conn, entry_id)
        return True

    # ── Helpers ───────────────────────────────────────────

    def _get_entry_or_raise(self, entry_id: int) -> dict:
        row = self._conn.execute(
            "SELECT * FROM journal_entries WHERE id=?",
            (entry_id,)
        ).fetchone()
        if not row:
            raise ValueError(f"القيد {entry_id} غير موجود")
        return row