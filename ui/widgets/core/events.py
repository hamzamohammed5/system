"""
ui/widgets/core/events.py
=========================
المصدر الوحيد لنظام الأحداث (Event Bus) في التطبيق.
"""
import logging
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class _EventBus(QObject):
    company_data_changed = pyqtSignal(int)
    font_changed         = pyqtSignal(int)
    theme_changed        = pyqtSignal(str)
    language_changed     = pyqtSignal(str)


bus = _EventBus()


def get_active_company_id() -> int | None:
    """يرجع company_id النشط أو None."""
    try:
        from db.companies.company_state import company_state
        return company_state.company_id if company_state.is_ready else None
    except Exception as e:
        logger.debug("get_active_company_id: %s", e)
        return None


def emit_company_data_changed():
    """يطلق bus.company_data_changed(cid) — لو مفيش شركة نشطة لا يطلق شيء."""
    try:
        cid = get_active_company_id()
        if cid is not None:
            bus.company_data_changed.emit(cid)
    except Exception as e:
        logger.warning("emit_company_data_changed: %s", e)


def is_same_company(company_id: int) -> bool:
    """يتحقق لو company_id هو نفس الشركة النشطة."""
    return get_active_company_id() == company_id