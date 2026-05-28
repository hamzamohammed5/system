"""
services/accounting/journal_service.py
========================================
Business Logic للقيود المحاسبية.

إصلاح 35: توحيد أسماء الاستيراد مع الدوال الفعلية في accounting_journal_repo:
  - insert_journal_entry  → insert_entry
  - insert_journal_line   → add_entry_lines  (تقبل list مش سطر واحد)
  - update_journal_entry  → دالة جديدة update_entry في الـ repo
  - delete_journal_lines  → دالة جديدة delete_entry_lines في الـ repo
  - delete_journal_entry  → delete_entry
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

    def check_balance(self, lines: list[JournalLine]) -> BalanceCheck:
        total_dr = sum(l.dr for l in lines)
        total_cr = sum(l.cr for l in lines)
        return BalanceCheck(total_dr=total_dr, total_cr=total_cr)

    def validate_lines(self, lines: list[JournalLine]) -> list[str]:
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
                COALESCE(SUM(jl.debit), 0)  AS total_dr,
                COALESCE(SUM(jl.credit), 0) AS total_cr
            FROM journal_lines jl
            JOIN journal_entries je ON je.id = jl.entry_id
            JOIN accounts a ON a.id = jl.account_id
            {where}
            GROUP BY a.id, a.name
        """, params).fetchone()

        if not row:
            acc = self._conn.execute(
                "SELECT id, name FROM accounts WHERE id=?", (account_id,)
            ).fetchone()
            name = acc["name"] if acc else f"حساب {account_id}"
            return AccountBalance(
                account_id=account_id, account_name=name,
                total_dr=0.0, total_cr=0.0,
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

        entry_data: {"date": str, "description": str, "notes": str (optional)}
        """
        errors = self.validate_lines(lines)
        if errors:
            raise ValueError("\n".join(errors))

        date = entry_data.get("date") or datetime.now().strftime("%Y-%m-%d")
        desc = entry_data.get("description", "").strip()
        notes = entry_data.get("notes", "")

        if not desc:
            raise ValueError("وصف القيد مطلوب")

        # [إصلاح 35] استخدام الأسماء الفعلية من accounting_journal_repo
        from db.accounting.accounting_journal_repo import insert_entry, add_entry_lines

        entry_id = insert_entry(
            self._conn,
            date=date,
            description=desc,
            entry_type="manual",
            notes=notes or None,
        )

        # add_entry_lines تقبل list من dicts
        line_dicts = [
            {
                "account_id":  line.account_id,
                "debit":       line.dr,
                "credit":      line.cr,
                "description": line.note,
            }
            for line in lines
        ]
        add_entry_lines(self._conn, entry_id, line_dicts)

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
        يحدث قيد موجود — يمسح الـ lines القديمة ويكتب الجديدة.
        """
        entry = self._get_entry_or_raise(entry_id)
        if entry.get("status") == "reversed":
            raise ValueError("القيد معكوس ولا يمكن تعديله")

        errors = self.validate_lines(lines)
        if errors:
            raise ValueError("\n".join(errors))

        date  = entry_data.get("date", entry["date"])
        desc  = entry_data.get("description", entry["description"]).strip()
        notes = entry_data.get("notes", entry["notes"] or "")

        if not desc:
            raise ValueError("وصف القيد مطلوب")

        # [إصلاح 35] استخدام الدوال الفعلية
        # تحديث بيانات القيد الأساسية
        self._conn.execute(
            """UPDATE journal_entries
               SET date=?, description=?, notes=?
               WHERE id=?""",
            (date, desc, notes, entry_id)
        )
        # حذف الـ lines القديمة
        self._conn.execute(
            "DELETE FROM journal_lines WHERE entry_id=?", (entry_id,)
        )
        # إضافة الـ lines الجديدة
        from db.accounting.accounting_journal_repo import add_entry_lines
        line_dicts = [
            {
                "account_id":  line.account_id,
                "debit":       line.dr,
                "credit":      line.cr,
                "description": line.note,
            }
            for line in lines
        ]
        add_entry_lines(self._conn, entry_id, line_dicts)

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
        """ينشئ قيد عكسي للقيد المحدد."""
        entry = self._get_entry_or_raise(entry_id)

        lines_rows = self._conn.execute(
            "SELECT account_id, debit, credit, description "
            "FROM journal_lines WHERE entry_id=?",
            (entry_id,)
        ).fetchall()

        if not lines_rows:
            raise ValueError("القيد لا يحتوي على صفوف")

        reversed_lines = [
            JournalLine(
                account_id = r["account_id"],
                dr         = r["credit"],
                cr         = r["debit"],
                note       = r["description"] or "",
            )
            for r in lines_rows
        ]

        desc = f"عكس القيد #{entry_id}"
        if note:
            desc += f" — {note}"

        result = self.post_entry(
            entry_data={"date": datetime.now().strftime("%Y-%m-%d"), "description": desc},
            lines=reversed_lines,
        )

        # علّم القيد الأصلي كـ reversed
        self._conn.execute(
            "UPDATE journal_entries SET status='reversed' WHERE id=?",
            (entry_id,)
        )
        self._conn.commit()

        return result

    # ── Delete ────────────────────────────────────────────

    def get_delete_preview(self, entry_id: int) -> DeletePreview | None:
        entry = self._conn.execute(
            "SELECT id, description, status FROM journal_entries WHERE id=?",
            (entry_id,)
        ).fetchone()

        if not entry:
            return None

        ref    = entry["description"] or f"#{entry_id}"
        status = entry["status"]

        if status == "reversed":
            return DeletePreview(
                entry_id=entry_id, entry_ref=ref,
                is_posted=True, can_delete=False,
                reason="القيد معكوس",
            )

        return DeletePreview(
            entry_id=entry_id, entry_ref=ref,
            is_posted=(status == "posted"), can_delete=True,
        )

    def delete(self, entry_id: int) -> bool:
        preview = self.get_delete_preview(entry_id)
        if not preview or not preview.can_delete:
            return False

        # [إصلاح 35] استخدام الاسم الفعلي
        from db.accounting.accounting_journal_repo import delete_entry
        delete_entry(self._conn, entry_id)
        return True

    # ── Helpers ───────────────────────────────────────────

    def _get_entry_or_raise(self, entry_id: int):
        row = self._conn.execute(
            "SELECT * FROM journal_entries WHERE id=?", (entry_id,)
        ).fetchone()
        if not row:
            raise ValueError(f"القيد {entry_id} غير موجود")
        return row