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

[مقترح 2] return_value مدعوم بشكل كامل لكل الأنواع:
    - return_value=[]    للـ methods التي ترجع list
    - return_value={}    للـ methods التي ترجع dict
    - return_value=False للـ methods التي ترجع bool
    - return_value=0     للـ methods التي ترجع int/float
    - الافتراضي None     للـ methods التي لا ترجع شيئاً

الاستخدام:

    from ui.widgets.core.guard import requires_company

    class MyPanel(BaseListPanel):
        @requires_company
        def _load_rows(self):
            return ItemService(self.conn).list_by_type("raw")

        @requires_company
        def _on_add_clicked(self):
            ...

    # [مقترح 2] مع return_value للـ methods التي تُعيد قيمة:
    class MyPanel(BaseListPanel):
        @requires_company(return_value=[])
        def _load_rows(self) -> list:
            return ItemService(self.conn).list_by_type("raw")

        @requires_company(return_value={})
        def _load_data(self) -> dict:
            ...

        @requires_company(return_value=False)
        def _can_save(self) -> bool:
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

    تحذير: return_value=[] يُنشئ list مشتركة لجميع الاستدعاءات.
    للـ methods التي تُعدّل القيمة المُعادة مباشرة، استخدم
    return_value_factory بدلاً منه:

    @requires_company(return_value_factory=list)
    def _load_rows(self) -> list:
        ...
    هذا يُنشئ [] جديدة في كل استدعاء بدل إعادة نفس الـ instance.
"""

import logging
import functools

logger = logging.getLogger(__name__)

_DEFAULT_MSG = "اختر شركة نشطة أولاً"
_SENTINEL    = object()  # للتمييز بين None المقصود وغياب القيمة


def requires_company(method=None, *,
                     message: str        = _DEFAULT_MSG,
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

        @requires_company(message="اختر شركة", return_value={})
        def _load_data(self) -> dict: ...

    4. [مقترح 2] مع factory لتجنب mutable default sharing:
        @requires_company(return_value_factory=list)
        def _load_rows(self) -> list: ...
        # يُنشئ [] جديدة في كل استدعاء

    Parameters
    ----------
    message : str
        الرسالة التي تُعرض للمستخدم إذا لم تكن الشركة جاهزة.
    return_value : Any
        القيمة التي يرجعها الـ decorator عند غياب الشركة.
        افتراضياً None — غيّرها لـ [] أو {} أو False حسب نوع الـ method.
        ملاحظة: لو return_value_factory محدد، يُتجاهل return_value.
    return_value_factory : type | callable | None
        دالة تُستدعى بدون arguments لإنتاج القيمة الافتراضية.
        مفيد مع الأنواع المتغيرة (list, dict) لتجنب shared state.
        مثال: return_value_factory=list  أو  return_value_factory=dict
    """
    # لو استُدعي بدون أقواس: @requires_company
    if method is not None:
        return _wrap(method, message, return_value, return_value_factory)

    # لو استُدعي بأقواس: @requires_company(...) أو @requires_company(message=...)
    def decorator(fn):
        return _wrap(fn, message, return_value, return_value_factory)
    return decorator


def _wrap(fn, message: str, return_value, return_value_factory):
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        if not _is_company_ready():
            logger.debug(
                "%s.%s: شركة غير نشطة — تخطي (return_value=%r, factory=%r)",
                type(self).__name__, fn.__name__,
                return_value, return_value_factory,
            )
            _show_warning(self, message)
            # [مقترح 2] الـ factory لها أولوية على return_value
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