"""
ui/widgets/shared/core/events.py
==================================
أدوات مساعدة موحدة للـ event bus.
"""
import logging

logger = logging.getLogger(__name__)


def get_active_company_id() -> int | None:
    """يرجع company_id النشط أو None."""
    try:
        from db.companies.company_state import company_state
        return company_state.company_id if company_state.is_ready else None
    except Exception as e:
        logger.debug("get_active_company_id: %s", e)
        return None


def emit_company_data_changed():
    """يطلق bus.company_data_changed(cid) أو bus.data_changed()."""
    try:
        from ui.events import bus
        cid = get_active_company_id()
        if cid is not None:
            bus.company_data_changed.emit(cid)
        else:
            bus.data_changed.emit()
    except Exception as e:
        logger.warning("emit_company_data_changed: %s", e)


def is_same_company(company_id: int) -> bool:
    """يتحقق لو company_id هو نفس الشركة النشطة."""
    return get_active_company_id() == company_id