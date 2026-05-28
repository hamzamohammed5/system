"""
ui/widgets/core/guard.py
=====================================
requires_company — decorator يتحقق من وجود شركة نشطة.

المشكلة: كل tab تتحقق من company_state.is_ready بطريقتها المختلفة:
    if not company_state.is_ready:
        return
    ...
بعضها ينسى التحقق فيكسر عند تشغيل التطبيق بدون شركة.

الحل: decorator موحد يُلف الـ methods الحساسة.

الاستخدام:

    from ui.widgets.core.guard import requires_company

    class MyPanel(BaseListPanel):
        @requires_company
        def _load_rows(self):
            return ItemService(self.conn).list_by_type("raw")

        @requires_company
        def _on_add_clicked(self):
            ...

    # لو الـ widget يورث من BaseDetailPanel (فيها show_warning):
    class MyDetail(BaseDetailPanel):
        @requires_company
        def load_item(self, item_id: int):
            ...

    # مثال مع رسالة مخصصة:
    @requires_company(message="اختر شركة لعرض الطلبات")
    def _load_orders(self):
        ...

السلوك:
    - لو الشركة جاهزة → ينفذ الـ method عادي.
    - لو لا → يعرض رسالة تحذير (لو self.show_warning موجود)
              ويرجع None بصمت.
    - لا يرمي exception — السلوك الصامت مناسب للـ UI.
"""

import logging
import functools

logger = logging.getLogger(__name__)

_DEFAULT_MSG = "اختر شركة نشطة أولاً"


def requires_company(method=None, *, message: str = _DEFAULT_MSG):
    """
    Decorator يتحقق من وجود شركة نشطة قبل تنفيذ الـ method.

    يقبل استخدامين:
        @requires_company
        def my_method(self): ...

        @requires_company(message="رسالة مخصصة")
        def my_method(self): ...
    """
    # لو استُدعي بدون أقواس: @requires_company
    if method is not None:
        return _wrap(method, message)

    # لو استُدعي بأقواس: @requires_company(message=...)
    def decorator(fn):
        return _wrap(fn, message)
    return decorator


def _wrap(fn, message: str):
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        if not _is_company_ready():
            logger.debug(
                "%s.%s: شركة غير نشطة — تخطي",
                type(self).__name__, fn.__name__
            )
            _show_warning(self, message)
            return None
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