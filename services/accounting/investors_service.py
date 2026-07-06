"""
services/accounting/investors_service.py
==========================================
Business Logic للمستثمرين — يغطي ui/tabs/accounting/investors_tab.py
وكل ملفات ui/tabs/accounting/investors/*.

يدير: CRUD مستثمرين، ربط/فك ربط بالقيود، وتقارير الملخص.

الاستخدام:
    from services.accounting.investors_service import InvestorsService
    svc = InvestorsService(erp_conn, acc_conn)
    svc.migrate()
    investors = svc.list_investors()
"""

from dataclasses import dataclass


@dataclass
class InvestorSaveResult:
    investor_id : int
    is_new      : bool
    name        : str


class InvestorsService:
    """
    Business Logic للمستثمرين.

    ملاحظة معمارية: investors_repo.py يعيش في db/accounting/ لأن جداوله
    (investors, investor_entries) مرتبطة بـ journal_entries في accounting.db،
    لكن بعض القراءات (تفاصيل القيد والسطر) تحتاج acc_conn منفصل — لذلك
    هذا الـ service يقبل الاثنين، تمامًا كما كان في investors_tab.py القديم.
    """

    def __init__(self, conn, acc_conn=None):
        """
        conn     : connection على القاعدة التي تحوي جداول investors/investor_entries
        acc_conn : connection على accounting.db لجلب تفاصيل القيود (اختياري)
        """
        self._conn = conn
        self._acc_conn = acc_conn

    # ── Migration ─────────────────────────────────────────

    def migrate(self):
        """يُنشئ/يُحدّث جداول المستثمرين لو لزم — استدعها مرة عند بناء التبويب."""
        try:
            from db.accounting.investors_repo import _migrate_investors
            _migrate_investors(self._conn)
        except Exception as e:
            print(f"[InvestorsService] migrate error: {e}")

    # ── CRUD مستثمرين ─────────────────────────────────────

    def list_investors(self) -> list:
        from db.accounting.investors_repo import fetch_all_investors
        return fetch_all_investors(self._conn)

    def get_investor(self, investor_id: int):
        from db.accounting.investors_repo import fetch_investor
        return fetch_investor(self._conn, investor_id)

    def investor_exists(self, name: str):
        from db.accounting.investors_repo import investor_exists
        return investor_exists(self._conn, name)

    def add_investor(self, name: str, notes: str = None,
                     joined_at: str = None) -> InvestorSaveResult:
        name = (name or "").strip()
        if not name:
            raise ValueError("اسم المستثمر مطلوب")
        if self.investor_exists(name):
            raise ValueError(f"يوجد مستثمر بنفس الاسم «{name}» بالفعل")

        from db.accounting.investors_repo import insert_investor
        inv_id = insert_investor(self._conn, name, notes=notes, joined_at=joined_at)
        return InvestorSaveResult(investor_id=inv_id, is_new=True, name=name)

    def update_investor(self, investor_id: int, name: str,
                        notes: str = None, joined_at: str = None) -> InvestorSaveResult:
        name = (name or "").strip()
        if not name:
            raise ValueError("اسم المستثمر مطلوب")

        from db.accounting.investors_repo import update_investor
        update_investor(self._conn, investor_id, name, notes=notes, joined_at=joined_at)
        return InvestorSaveResult(investor_id=investor_id, is_new=False, name=name)

    def delete_investor(self, investor_id: int):
        """
        [ملاحظة] الحذف هنا لا يفحص وجود روابط investor_entries قبل الحذف —
        نفس سلوك delete_investor في الـ repo الأصلي (حذف مباشر، بدون CASCADE فحص).
        لو محتاج منع الحذف عند وجود روابط، استخدم get_investor_links_count أولاً.
        """
        from db.accounting.investors_repo import delete_investor
        delete_investor(self._conn, investor_id)

    def get_investor_links_count(self, investor_id: int) -> int:
        """يساعد الـ UI على تحذير المستخدم قبل حذف مستثمر له حركات مسجلة."""
        try:
            row = self._conn.execute(
                "SELECT COUNT(*) as c FROM investor_entries WHERE investor_id=?",
                (investor_id,)
            ).fetchone()
            return row["c"] if row else 0
        except Exception:
            return 0

    # ── ربط المستثمر بالقيود ──────────────────────────────

    def link_to_line(self, investor_id: int, entry_id: int, line_id: int,
                     move_type: str, amount: float, notes: str = None) -> int:
        if move_type not in ("capital", "drawings"):
            raise ValueError("move_type يجب أن يكون 'capital' أو 'drawings'")
        if amount <= 0:
            raise ValueError("المبلغ يجب أن يكون أكبر من صفر")

        from db.accounting.investors_repo import link_investor_to_line
        return link_investor_to_line(
            self._conn, investor_id, entry_id, line_id, move_type, amount, notes=notes
        )

    def get_entry_investor_links(self, entry_id: int) -> list:
        from db.accounting.investors_repo import fetch_entry_investor_links
        return fetch_entry_investor_links(self._conn, entry_id)

    def unlink(self, link_id: int):
        from db.accounting.investors_repo import delete_investor_link
        delete_investor_link(self._conn, link_id)

    def unlink_entry(self, entry_id: int):
        """يفك كل روابط المستثمرين بقيد معين — يُستخدم قبل حذف القيد نفسه."""
        from db.accounting.investors_repo import delete_entry_investor_links
        delete_entry_investor_links(self._conn, entry_id)

    # ── التقارير ───────────────────────────────────────────

    def get_investor_summary(self, investor_id: int) -> dict:
        """ملخص مستثمر واحد (رأس مال / مسحوبات / صافي) + حركاته."""
        from db.accounting.investors_repo import calc_investor_summary
        return calc_investor_summary(self._conn, investor_id, acc_conn=self._acc_conn)

    def get_all_investors_summary(self) -> list:
        """ملخص كل المستثمرين مرتبين تنازليًا حسب صافي الاستثمار."""
        from db.accounting.investors_repo import calc_all_investors_summary
        return calc_all_investors_summary(self._conn, acc_conn=self._acc_conn)

    def get_investor_entries(self, investor_id: int) -> list:
        from db.accounting.investors_repo import fetch_investor_entries
        return fetch_investor_entries(self._conn, investor_id, acc_conn=self._acc_conn)
