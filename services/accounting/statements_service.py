"""
services/accounting/statements_service.py
============================================
Business Logic للقوائم المالية — يغطي:
  - ui/tabs/accounting/financial/income_statement_tab.py
  - ui/tabs/accounting/financial/owners_equity_tab.py
  - ui/tabs/accounting/financial/trial_balance_tab.py

لماذا service وليس تواصل مباشر؟
  يحقق هذا الملف الهيكلة المطلوبة:
    ui/tabs/...  →  StatementsService  →  accounting_statements_repo
                 →  accounting_schema  →  DB
  طبقة الـ UI (tabs/, widgets/) لا تستدعي db.accounting.accounting_repo
  أو db.accounting.accounting_statements_repo مباشرة.

ملاحظة معمارية (بنفس منطق accounts_service.py):
  TYPE_AR ثابت عرض (dict ثابت لا يُقرأ من DB) وليس بيانات — لذلك
  يُعرَض هنا كدالة get_type_label بدل تحويله لاستعلام، حتى لا تحتاج
  tabs/ لاستيراد accounting_schema_constants مباشرة.

الاستخدام:
    from services.accounting.statements_service import StatementsService
    svc = StatementsService(conn)
    data = svc.get_income_statement()
    rows = svc.get_trial_balance()
"""

from dataclasses import dataclass, field


# ══════════════════════════════════════════════════════════
# Dataclasses
# ══════════════════════════════════════════════════════════

@dataclass
class TrialBalanceRow:
    code         : str
    name         : str
    type         : str
    total_debit  : float
    total_credit : float
    balance      : float


@dataclass
class IncomeStatementResult:
    revenues   : list = field(default_factory=list)
    expenses   : list = field(default_factory=list)
    total_rev  : float = 0.0
    total_exp  : float = 0.0
    net_income : float = 0.0


@dataclass
class OwnersEquityResult:
    capital_accounts  : list = field(default_factory=list)
    drawings_accounts : list = field(default_factory=list)
    net_income        : float = 0.0
    total_capital     : float = 0.0
    total_drawings    : float = 0.0
    total_equity      : float = 0.0


@dataclass
class BalanceSheetResult:
    assets       : list = field(default_factory=list)
    liabilities  : list = field(default_factory=list)
    capital      : list = field(default_factory=list)
    drawings     : list = field(default_factory=list)
    net_income   : float = 0.0
    total_assets : float = 0.0
    total_liab   : float = 0.0
    total_equity : float = 0.0


# ══════════════════════════════════════════════════════════
# StatementsService
# ══════════════════════════════════════════════════════════

class StatementsService:
    """
    Business Logic للقوائم المالية.
    يدير: ميزان المراجعة، قائمة الدخل، الميزانية العمومية، قائمة حقوق الملكية.
    """

    def __init__(self, conn):
        self._conn = conn

    # ── ميزان المراجعة ────────────────────────────────────

    def get_trial_balance(self) -> list:
        """
        يرجع list من dict بنفس شكل accounting_statements_repo.trial_balance
        (code, name, type, total_debit, total_credit, balance).
        شكل الإرجاع dict وليس TrialBalanceRow حفاظاً على توافق الـ UI الحالي
        الذي يقرأ row["code"], row["balance"] ... مباشرة.
        """
        from db.accounting.accounting_statements_repo import trial_balance
        return trial_balance(self._conn)

    def get_normal_balance(self, acc_type: str) -> str:
        """يرجع 'dr' أو 'cr' — بديل لاستدعاء get_normal_balance من repo مباشرة."""
        from db.accounting.accounting_accounts_repo import get_normal_balance
        return get_normal_balance(acc_type)

    # ── قائمة الدخل ───────────────────────────────────────

    def get_income_statement(self) -> dict:
        """
        يرجع dict: revenues, expenses, total_rev, total_exp, net_income.
        نفس شكل accounting_statements_repo.income_statement.
        """
        from db.accounting.accounting_statements_repo import income_statement
        return income_statement(self._conn)

    # ── الميزانية العمومية ────────────────────────────────

    def get_balance_sheet(self) -> dict:
        """
        يرجع dict: assets, liabilities, capital, drawings, net_income,
        total_assets, total_liab, total_equity.
        """
        from db.accounting.accounting_statements_repo import balance_sheet
        return balance_sheet(self._conn)

    # ── قائمة حقوق الملكية ────────────────────────────────

    def get_owners_equity_statement(self) -> dict:
        """
        يرجع dict: capital_accounts, drawings_accounts, net_income,
        total_capital, total_drawings, total_equity.
        """
        from db.accounting.accounting_statements_repo import owners_equity_statement
        return owners_equity_statement(self._conn)

    # ── ثوابت عرض (لا تحتاج DB) ───────────────────────────

    def get_type_label(self, acc_type: str) -> str:
        """
        يرجع التسمية العربية لنوع الحساب (أصول/خصوم/...).
        بديل لاستيراد TYPE_AR من accounting_schema مباشرة في tabs/ —
        نفس منطق accounts_service.py: هذا ثابت عرض وليس بيانات، لكنه
        يُعرَض هنا كطريقة موحّدة بدل استيراد db.accounting.accounting_schema
        من داخل ملف tab.
        """
        from db.accounting.accounting_schema_constants import TYPE_AR
        return TYPE_AR.get(acc_type, acc_type)
