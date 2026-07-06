"""
services/accounting/audit_service.py
======================================
Business Logic لسجل التدقيق (Audit Log) — يغطي
ui/tabs/accounting/audit_log_tab.py.

الاستخدام:
    from services.accounting.audit_service import AuditService
    svc = AuditService(conn)
    total = svc.count(table_name=filter_table, action=filter_action)
    rows  = svc.list(table_name=filter_table, action=filter_action,
                     limit=PAGE_SIZE, offset=offset)
"""

from dataclasses import dataclass


@dataclass
class AuditPage:
    rows        : list
    total_count : int
    offset      : int
    limit       : int

    @property
    def has_more(self) -> bool:
        return self.offset + len(self.rows) < self.total_count


class AuditService:
    """Business Logic لقراءة سجل التدقيق (audit_log) — قراءة فقط، بدون كتابة مباشرة من الـ UI."""

    def __init__(self, conn):
        self._conn = conn

    def count(self, table_name: str = None, action: str = None) -> int:
        from db.accounting.accounting_audit_repo import fetch_audit_log_count
        return fetch_audit_log_count(self._conn, table_name=table_name, action=action)

    def list(self, table_name: str = None, action: str = None,
             limit: int = 200, offset: int = 0) -> list:
        from db.accounting.accounting_audit_repo import fetch_audit_log
        return fetch_audit_log(
            self._conn, table_name=table_name, action=action,
            limit=limit, offset=offset,
        )

    def get_page(self, table_name: str = None, action: str = None,
                limit: int = 200, offset: int = 0) -> AuditPage:
        """
        يجمع count + list في نداء واحد — يُستخدم في audit_log_tab._fetch_and_fill
        بدل استدعاءين منفصلين مع منطق "لو offset == 0" يدوي في الـ UI.
        """
        total = self.count(table_name=table_name, action=action) if offset == 0 else None
        rows = self.list(table_name=table_name, action=action, limit=limit, offset=offset)
        return AuditPage(
            rows=rows,
            total_count=total if total is not None else -1,
            offset=offset,
            limit=limit,
        )

    def get_record_history(self, table_name: str, record_id: int) -> list:
        from db.accounting.accounting_audit_repo import fetch_record_history
        return fetch_record_history(self._conn, table_name, record_id)
