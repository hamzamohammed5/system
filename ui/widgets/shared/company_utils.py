"""
ui/widgets/shared/company_utils.py
====================================
أدوات مساعدة للشركة النشطة — توحيد الكود المكرر.

تحل محل الدوال المكررة في:
  - journal_form.py
  - _smart_line.py
  - journal_group_combo.py
  - _tree_group_combo.py
  - _journal_filter.py
  - وأي ملف آخر يحتاج company_id أو emit

الاستخدام:
    from ui.widgets.shared.company_utils import (
        get_active_company_id,
        emit_company_data_changed,
    )

    cid = get_active_company_id()   # → int | None
    emit_company_data_changed()     # يطلق bus.company_data_changed أو bus.data_changed
"""

import logging
logger = logging.getLogger(__name__)


def get_active_company_id() -> int | None:
    """يرجع company_id النشط أو None."""
    try:
        from db.companies.company_state import company_state
        return company_state.company_id if company_state.is_ready else None
    except Exception as e:
        logger.debug("get_active_company_id failed: %s", e)
        return None


def emit_company_data_changed():
    """
    يطلق bus.company_data_changed(cid) لو فيه شركة نشطة،
    وإلا يطلق bus.data_changed().
    """
    try:
        from ui.events import bus
        cid = get_active_company_id()
        if cid is not None:
            bus.company_data_changed.emit(cid)
        else:
            bus.data_changed.emit()
    except Exception as e:
        logger.warning("emit_company_data_changed failed: %s", e)


def is_same_company(company_id: int) -> bool:
    """يتحقق لو company_id هو نفس الشركة النشطة."""
    return get_active_company_id() == company_id