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

    # مع return_value للـ methods التي تُعيد قيمة (مقترح 2):
    class MyPanel(BaseListPanel):
        @requires_company(return_value=[])
        def _load_rows(self) -> list:
            return ItemService(self.conn).list_by_type("raw")

    # لو الـ widget يورث من BaseDetailPanel (فيها show_warning):
    class MyDetail(BaseDetailPanel):
        @requires_company
        def load_item(self, item_id: int):
            ...

    # مثال مع رسالة مخصصة:
    @requires_company(message="اختر شركة لعرض الطلبات")
    def _load_orders(self):
        ...

    # مثال مع رسالة مخصصة وقيمة افتراضية:
    @requires_company(message="اختر شركة لعرض الطلبات", return_value=[])
    def _load_orders(self) -> list:
        ...

السلوك:
    - لو الشركة جاهزة → ينفذ الـ method عادي.
    - لو لا → يعرض رسالة تحذير (لو self.show_warning موجود)
              ويرجع return_value (افتراضياً None) بصمت.
    - لا يرمي exception — السلوك الصامت مناسب للـ UI.

ملاحظة مهمة (مقترح 2):
    لو الـ method ترجع list استخدم return_value=[] لتجنب:
        for row in None:  # → TypeError
    لو ترجع dict استخدم return_value={}
    لو ترجع int/bool استخدم return_value=0 أو False
"""

import logging
import functools

logger = logging.getLogger(__name__)

_DEFAULT_MSG = "اختر شركة نشطة أولاً"
_SENTINEL    = object()  # للتمييز بين None المقصود وغياب القيمة


def requires_company(method=None, *,
                     message: str  = _DEFAULT_MSG,
                     return_value          = None):
    """
    Decorator يتحقق من وجود شركة نشطة قبل تنفيذ الـ method.

    يقبل ثلاثة أنماط:

    1. بدون أقواس:
        @requires_company
        def my_method(self): ...

    2. بأقواس مع رسالة مخصصة:
        @requires_company(message="رسالة مخصصة")
        def my_method(self): ...

    3. بأقواس مع رسالة وقيمة افتراضية عند الغياب (مقترح 2):
        @requires_company(return_value=[])
        def _load_rows(self) -> list: ...

        @requires_company(message="اختر شركة", return_value={})
        def _load_data(self) -> dict: ...

    Parameters
    ----------
    message : str
        الرسالة التي تُعرض للمستخدم إذا لم تكن الشركة جاهزة.
    return_value : Any
        القيمة التي يرجعها الـ decorator عند غياب الشركة.
        افتراضياً None — غيّرها لـ [] أو {} أو False حسب نوع الـ method.
    """
    # لو استُدعي بدون أقواس: @requires_company
    if method is not None:
        return _wrap(method, message, return_value)

    # لو استُدعي بأقواس: @requires_company(...) أو @requires_company(message=...)
    def decorator(fn):
        return _wrap(fn, message, return_value)
    return decorator


def _wrap(fn, message: str, return_value):
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        if not _is_company_ready():
            logger.debug(
                "%s.%s: شركة غير نشطة — تخطي (return_value=%r)",
                type(self).__name__, fn.__name__, return_value,
            )
            _show_warning(self, message)
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