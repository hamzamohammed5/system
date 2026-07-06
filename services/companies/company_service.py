"""
services/companies/company_service.py
=======================================
CompanyService — الوسيط الوحيد بين طبقة الـ UI وقاعدة البيانات
لكل عمليات إدارة الشركات (companies.db).

المسؤولية:
  - CRUD كامل للشركات عبر db.companies.companies_repo
  - توفير اتصال central جاهز ومهيّأ بالجداول (نمط get_x_conn_and_init
    المستخدم في باقي الدومينات، مثل services.design.get_designs_conn_and_init)

لماذا service وليس تواصل مباشر؟
  يحقق هذا الملف الهيكلة المطلوبة:
    ui/tabs/...  →  CompanyService  →  companies_repo  →  companies_schema  →  DB
  أي أن طبقة الـ UI (tabs/, widgets/) لا تعرف شيئاً عن db.companies مباشرة.
  كل تغيير مستقبلي في طريقة التخزين (تحويل النظام لـ online) يحدث
  هنا فقط دون لمس أي ملف في ui/.

الاستخدام:
    from services.companies.company_service import CompanyService

    conn = CompanyService.get_central_conn_and_init()
    svc  = CompanyService(conn)
    companies = svc.list_companies()
"""

from __future__ import annotations
import logging
from dataclasses import dataclass

from db.companies.companies_schema import (
    get_central_connection,
    create_central_tables,
)
from db.companies.companies_repo import (
    fetch_all_companies,
    fetch_company,
    insert_company as _repo_insert_company,
    update_company as _repo_update_company,
    delete_company as _repo_delete_company,
    toggle_company_active as _repo_toggle_company_active,
)

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════
# Dataclasses
# ══════════════════════════════════════════════════════════

@dataclass
class CompanyResult:
    id         : int
    name       : str
    short_name : str
    logo_path  : "str | None"
    color      : str
    is_active  : bool
    notes      : str


# ══════════════════════════════════════════════════════════
# CompanyService
# ══════════════════════════════════════════════════════════

class CompanyService:
    """
    Business Logic لإدارة الشركات.

    الاستخدام:
        conn = CompanyService.get_central_conn_and_init()
        svc  = CompanyService(conn)
    """

    def __init__(self, conn):
        self._conn = conn

    # ────────────────────────────────────────────────────
    # اتصال جاهز ومهيّأ — نقطة الدخول من UI
    # ────────────────────────────────────────────────────

    @classmethod
    def get_central_conn_and_init(cls):
        """
        يرجع اتصال companies.db جاهزاً بعد التأكد من إنشاء جداوله.
        نقطة الدخول الوحيدة الموصى بها من tabs/ — بنفس نمط
        get_designs_conn_and_init في دومين التصميم.
        """
        conn = get_central_connection()
        create_central_tables(conn)
        return conn

    @classmethod
    def get_current_company_id(cls) -> "int | None":
        """
        يرجع id الشركة النشطة حالياً.
        نقطة الدخول الوحيدة من tabs/ لمعرفة الشركة الحالية —
        بدلاً من استدعاء db.companies.company_state مباشرة من UI.
        يرجع None لو مفيش شركة نشطة أو حصل خطأ.
        """
        try:
            from db.companies.company_state import company_state
            return company_state.company_id
        except Exception:
            return None

    @classmethod
    def is_company_ready(cls) -> bool:
        """
        يرجع True لو فيه شركة نشطة محددة حالياً.
        بديل لقراءة company_state.is_ready مباشرة من UI.
        """
        try:
            from db.companies.company_state import company_state
            return bool(company_state.is_ready)
        except Exception:
            return False

    @classmethod
    def set_active_company(cls, company_id: int, name: str, color: str) -> None:
        """
        يعيّن الشركة النشطة حالياً.
        بديل لاستدعاء company_state.set_active(...) مباشرة من UI.
        """
        try:
            from db.companies.company_state import company_state
            company_state.set_active(company_id, name, color)
        except Exception:
            pass

    # ────────────────────────────────────────────────────
    # Validation
    # ────────────────────────────────────────────────────

    def validate(self, name: str) -> "str | None":
        """يرجع رسالة الخطأ لو فيه مشكلة، وإلا None."""
        if not name.strip():
            return "اسم الشركة مطلوب"
        return None

    # ────────────────────────────────────────────────────
    # Read
    # ────────────────────────────────────────────────────

    def list_companies(self, active_only: bool = False) -> list[CompanyResult]:
        rows = fetch_all_companies(self._conn, active_only=active_only)
        return [self._to_result(r) for r in rows]

    def get_company(self, company_id: int) -> "CompanyResult | None":
        row = fetch_company(self._conn, company_id)
        if not row:
            return None
        return self._to_result(row)

    def _to_result(self, row) -> CompanyResult:
        return CompanyResult(
            id         = row["id"],
            name       = row["name"],
            short_name = row["short_name"] or "",
            logo_path  = row["logo_path"],
            color      = row["color"] or "#1565c0",
            is_active  = bool(row["is_active"]),
            notes      = row["notes"] or "",
        )

    # ────────────────────────────────────────────────────
    # Write
    # ────────────────────────────────────────────────────

    def add_company(self, name: str, short_name: str = "",
                     color: str = "#1565c0", notes: str = "") -> int:
        """
        ينشئ شركة جديدة (ويهيّئ كل قواعد بياناتها الخاصة تلقائياً
        عبر companies_repo.insert_company).
        """
        err = self.validate(name)
        if err:
            raise ValueError(err)
        return _repo_insert_company(
            self._conn, name.strip(), short_name, color, notes
        )

    def update_company(self, company_id: int, name: str,
                        short_name: str = "", color: str = "#1565c0",
                        notes: str = "", is_active: bool = True) -> None:
        err = self.validate(name)
        if err:
            raise ValueError(err)
        _repo_update_company(
            self._conn, company_id, name.strip(), short_name,
            color, notes, int(is_active),
        )

    def delete_company(self, company_id: int) -> bool:
        """
        يحذف الشركة من companies.db.
        ملفات DB الخاصة بها تبقى على الديسك (سلوك موثّق في الـ repo).
        """
        return delete_company(self._conn, company_id)

    def toggle_active(self, company_id: int) -> None:
        toggle_company_active(self._conn, company_id)
