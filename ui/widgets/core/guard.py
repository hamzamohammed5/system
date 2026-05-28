"""
ui/widgets/core/guard.py
=====================================
requires_company — decorator يتحقق من وجود شركة نشطة.

التحسينات:
  - [i18n] رسالة "اختر شركة نشطة أولاً" تستخدم tr("select_company").
  - باقي الكود بدون تغيير.

[مقترح 2] return_value مدعوم بشكل كامل لكل الأنواع.

الاستخدام:

    from ui.widgets.core.guard import requires_company

    class MyPanel(BaseListPanel):
        @requires_company
        def _load_rows(self):
            return ItemService(self.conn).list_by_type("raw")

        @requires_company(return_value=[])
        def _load_rows(self) -> list:
            return ItemService(self.conn).list_by_type("raw")
"""

import logging
import functools

logger = logging.getLogger(__name__)

_SENTINEL = object()


def _default_msg() -> str:
    """رسالة افتراضية قابلة للترجمة."""
    try:
        from ui.widgets.core.i18n import tr
        return tr("select_company")
    except Exception:
        return "اختر شركة نشطة أولاً"


def requires_company(method=None, *,
                     message: str        = "",
                     return_value                       = None,
                     return_value_factory: "type | None" = None):
    """
    Decorator يتحقق من وجود شركة نشطة قبل تنفيذ الـ method.

    يقبل أربعة أنماط:

    1. بدون أقواس:
        @requires_company
        def my_method(self): ...

    2. بأقواس مع رسالة مخصصة:
        @requires_company(message="رسالة مخصصة")
        def my_method(self): ...

    3. [مقترح 2] بأقواس مع قيمة افتراضية:
        @requires_company(return_value=[])
        def _load_rows(self) -> list: ...

    4. [مقترح 2] مع factory لتجنب mutable default sharing:
        @requires_company(return_value_factory=list)
        def _load_rows(self) -> list: ...
    """
    if method is not None:
        return _wrap(method, message, return_value, return_value_factory)

    def decorator(fn):
        return _wrap(fn, message, return_value, return_value_factory)
    return decorator


def _wrap(fn, message: str, return_value, return_value_factory):
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        if not _is_company_ready():
            _msg = message or _default_msg()
            logger.debug(
                "%s.%s: شركة غير نشطة — تخطي (return_value=%r, factory=%r)",
                type(self).__name__, fn.__name__,
                return_value, return_value_factory,
            )
            _show_warning(self, _msg)
            if return_value_factory is not None:
                return return_value_factory()
            return return_value
        return fn(self, *args, **kwargs)
    return wrapper


def _is_company_ready() -> bool:
    """يتحقق من جاهزية company_state."""
    try:
        from db.companies.company_state import company_state
        return company_state.is_ready
    except Exception:
        return False


def _show_warning(widget, message: str):
    """
    يعرض رسالة التحذير لو الـ widget يدعمها.

    يفحص الـ widget بالترتيب:
      1. show_warning()  — BaseDetailPanel
      2. _warn()         — FormValidationMixin
      3. _notif.show()   — BaseCrudForm
      4. صامت            — لو مفيش طريقة معروفة
    """
    if hasattr(widget, "show_warning"):
        widget.show_warning(message)
    elif hasattr(widget, "_warn"):
        widget._warn(message)
    elif hasattr(widget, "_notif"):
        widget._notif.show(message, "warning")
    else:
        logger.debug("requires_company: %s — no warning method found", message)