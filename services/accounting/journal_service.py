"""
services/accounting/journal_service.py
========================================
Business Logic للقيود المحاسبية.

إصلاح 35: مزامنة الـ imports مع الدوال الفعلية في accounting_journal_repo:
  - insert_journal_entry → insert_entry
  - insert_journal_line  → add_entry_lines (batch)
  - update_journal_entry → update_entry (أُضيفت في repo)
  - delete_journal_lines → دالة مساعدة داخلية
  - delete_journal_entry → delete_entry

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

    إصلاح 35: كل الـ imports مزامَنة مع الأسماء الفعلية في accounting_journal_repo:
      insert_entry, add_entry_lines, delete_entry, fetch_entry, fetch_entry_lines
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
                COALESCE(SUM(jl.debit),  0) AS total_dr,
                COALESCE(SUM(jl.credit), 0) AS total_cr
            FROM journal_lines jl
            JOIN journal_entries je ON je.id = jl.entry_id
            JOIN accounts a ON a.id = jl.account_id
            {where}
            GROUP BY a.id, a.name
        """, params).fetchone()

        if not row:
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

    def get_entry_by_ref(self, ref_no: str):
        """يجلب قيداً برقمه المرجعي — يعيد استخدام repo helper الجاهزة."""
        from db.accounting.accounting_repo_ui_helpers import fetch_entry_by_ref
        return fetch_entry_by_ref(self._conn, ref_no)

    def get_line_id(self, entry_id: int, side: str) -> int:
        """
        يرجع id أول سطر من الجانب المطلوب في قيد معيّن.
        side: 'credit' → أول سطر دائن (لقيود رأس المال)
              'debit'  → أول سطر مدين (لقيود المسحوبات)
        """
        from db.accounting.accounting_repo_ui_helpers import (
            fetch_capital_line_for_entry, fetch_drawings_line_for_entry,
        )
        if side == "credit":
            return fetch_capital_line_for_entry(self._conn, entry_id)
        if side == "debit":
            return fetch_drawings_line_for_entry(self._conn, entry_id)
        raise ValueError("side يجب أن يكون 'credit' أو 'debit'")

    def get_entry_ids_for_groups(self, group_ids) -> set:
        """
        يرجع مجموعة entry_id لكل القيود التي تحتوي سطراً على حساب
        منتمٍ لأي من group_ids المُعطاة.
        منقولة من _tree_group_combo.py._update_selection (كانت SQL خام في tabs/).
        """
        group_ids = list(group_ids)
        if not group_ids:
            return set()
        placeholders = ",".join("?" * len(group_ids))
        rows = self._conn.execute(f"""
            SELECT DISTINCT jl.entry_id
            FROM journal_lines jl
            JOIN accounts a ON a.id = jl.account_id
            WHERE a.group_id IN ({placeholders})
        """, group_ids).fetchall()
        return {r["entry_id"] for r in rows}

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

        [إصلاح 35] يستخدم insert_entry + add_entry_lines (الأسماء الفعلية).
        """
        errors = self.validate_lines(lines)
        if errors:
            raise ValueError("\n".join(errors))

        date = entry_data.get("date") or \
               datetime.now().strftime("%Y-%m-%d")
        desc = entry_data.get("description", "").strip()
        ref  = entry_data.get("ref", "").strip()

        if not desc:
            raise ValueError("وصف القيد مطلوب")

        # [إصلاح 35] الأسماء الفعلية في accounting_journal_repo
        from db.accounting.accounting_journal_repo import (
            insert_entry,
            add_entry_lines,
        )

        entry_id = insert_entry(
            self._conn,
            date        = date,
            description = desc,
            entry_type  = entry_data.get("entry_type", "manual"),
            notes       = entry_data.get("notes"),
        )

        # تحويل JournalLine → dict format لـ add_entry_lines
        lines_dicts = [
            {
                "account_id":  line.account_id,
                "debit":       line.dr,
                "credit":      line.cr,
                "description": line.note,
            }
            for line in lines
        ]
        add_entry_lines(self._conn, entry_id, lines_dicts)

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

        [إصلاح 35] يستخدم الدوال الفعلية بدل update_journal_entry / delete_journal_lines.
        """
        entry = self._get_entry_or_raise(entry_id)
        if entry.get("status") == "reversed":
            raise ValueError("القيد مُعكوس ولا يمكن تعديله")

        errors = self.validate_lines(lines)
        if errors:
            raise ValueError("\n".join(errors))

        # [إصلاح 35] تحديث القيد يدوياً (update_journal_entry غير موجودة في repo)
        date = entry_data.get("date") or entry["date"]
        desc = entry_data.get("description", "").strip() or entry["description"]

        self._conn.execute(
            "UPDATE journal_entries SET date=?, description=? WHERE id=?",
            (date, desc, entry_id)
        )
        self._conn.commit()

        # حذف الصفوف القديمة ثم إضافة الجديدة
        self._delete_entry_lines(entry_id)

        from db.accounting.accounting_journal_repo import add_entry_lines
        lines_dicts = [
            {
                "account_id":  line.account_id,
                "debit":       line.dr,
                "credit":      line.cr,
                "description": line.note,
            }
            for line in lines
        ]
        add_entry_lines(self._conn, entry_id, lines_dicts)

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

        # [إصلاح 35] يستخدم fetch_entry_lines (الاسم الفعلي)
        from db.accounting.accounting_journal_repo import fetch_entry_lines
        lines_rows = fetch_entry_lines(self._conn, entry_id)

        if not lines_rows:
            raise ValueError("القيد لا يحتوي على صفوف")

        # اعكس debit و credit
        reversed_lines = [
            JournalLine(
                account_id = r["account_id"],
                dr         = r["credit"],   # الدائن يصبح مدين
                cr         = r["debit"],    # المدين يصبح دائن
                note       = r["description"] or "",
            )
            for r in lines_rows
        ]

        desc = f"عكس القيد رقم {entry.get('ref_no', entry_id)}"
        if note:
            desc += f" — {note}"

        return self.post_entry(
            entry_data = {
                "date":        datetime.now().strftime("%Y-%m-%d"),
                "description": desc,
                "entry_type":  "manual",
            },
            lines = reversed_lines,
        )

    # ── Delete ────────────────────────────────────────────

    def get_delete_preview(self,
                           entry_id: int) -> DeletePreview | None:
        """يرجع معلومات الحذف قبل التنفيذ."""
        entry = self._conn.execute(
            "SELECT id, ref_no, description, status "
            "FROM journal_entries WHERE id=?",
            (entry_id,)
        ).fetchone()

        if not entry:
            return None

        ref       = entry["ref_no"] or entry["description"] or f"#{entry_id}"
        is_posted = entry["status"] == "posted"

        # القيود المعكوسة لا يمكن حذفها
        if entry["status"] == "reversed":
            return DeletePreview(
                entry_id   = entry_id,
                entry_ref  = ref,
                is_posted  = is_posted,
                can_delete = False,
                reason     = "القيد مُعكوس",
            )

        return DeletePreview(
            entry_id   = entry_id,
            entry_ref  = ref,
            is_posted  = is_posted,
            can_delete = True,
        )

    def delete(self, entry_id: int) -> bool:
        """
        يحذف القيد وكل صفوفه.
        يرجع True لو نجح، False لو مقفول/معكوس.

        [إصلاح 35] يستخدم delete_entry (الاسم الفعلي).
        """
        preview = self.get_delete_preview(entry_id)
        if not preview or not preview.can_delete:
            return False

        from db.accounting.accounting_journal_repo import delete_entry
        delete_entry(self._conn, entry_id)
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

    def _delete_entry_lines(self, entry_id: int) -> None:
        """
        [إصلاح 35] دالة مساعدة داخلية لحذف صفوف القيد.
        بديل عن delete_journal_lines الغير موجودة في repo.
        journal_lines لديها CASCADE على entry_id، لكن نستخدم DELETE المباشر.
        """
        self._conn.execute(
            "DELETE FROM journal_lines WHERE entry_id=?", (entry_id,)
        )
        self._conn.commit()