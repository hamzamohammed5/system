"""
services/design/__init__.py
=============================
Factory مركزية لخدمات التصميم — نقطة الدخول الوحيدة من tabs/widgets.

بدل ما كل widget يعمل DesignService(conn) بنفسه، بيستخدم الـ factory
هنا عشان يضمن نفس الـ instance لنفس الـ connection، وميكسرش لو الشركة
النشطة اتغيرت (conn جديد).

الاستخدام:
    from services.design import get_design_service, get_design_size_service, get_dimension_set_service

    class MyWidget(QWidget):
        def __init__(self, conn):
            self._design_svc = get_design_service(conn)
            ...

قاعدة الـ Layering:
    tabs/widgets  →  services/design (عبر الـ factory هنا)  →  repos (db.*)  →  DB

    ✓ الـ widgets لازم تستدعي الـ factory دي بس — ما تعملش DesignService(conn) مباشرة
    ✓ لو الشركة اتغيرت (conn جديد)، الـ factory بتبني instance جديد تلقائياً
      ومبتفضلش ماسكة conn قديم ميت
"""

from .design_service import DesignService
from .design_size_service import DesignSizeService
from .dimension_set_service import DimensionSetService


# ══════════════════════════════════════════════════════════
# Cache داخلي — instance واحد نشط فقط لكل نوع service
# ══════════════════════════════════════════════════════════
# [ملاحظة] استخدمنا متغير مفرد بدل dict مفتوح بـ id(conn):
#   - في أي لحظة فيه شركة نشطة واحدة بس (company_state.company_id)
#   - dict بمفتاح id(conn) كان هيتراكم فيه مرجع دائم لكل conn قديم
#     (حتى بعد إغلاق الشركة) ← memory leak طول عمر التطبيق
#   - المتغير المفرد بيستبدل نفسه تلقائياً عند تغيّر الـ conn،
#     فمفيش أي مرجع قديم فاضل يمنع الـ garbage collector
_design_service_instance:       "DesignService | None" = None
_design_size_service_instance:  "DesignSizeService | None" = None
_dimension_set_service_instance: "DimensionSetService | None" = None


def get_design_service(conn) -> DesignService:
    """
    يرجع DesignService واحد للـ conn الحالي.
    نفس الـ conn → نفس الـ instance (بدون إعادة بناء).
    conn مختلف (شركة جديدة) → instance جديد يستبدل القديم تلقائياً.
    """
    global _design_service_instance
    if _design_service_instance is None or _design_service_instance.conn is not conn:
        _design_service_instance = DesignService(conn)
    return _design_service_instance


def get_design_size_service(conn) -> DesignSizeService:
    """يرجع DesignSizeService واحد للـ conn الحالي."""
    global _design_size_service_instance
    if _design_size_service_instance is None or _design_size_service_instance.conn is not conn:
        _design_size_service_instance = DesignSizeService(conn)
    return _design_size_service_instance


def get_dimension_set_service(conn) -> DimensionSetService:
    """يرجع DimensionSetService واحد للـ conn الحالي."""
    global _dimension_set_service_instance
    if _dimension_set_service_instance is None or _dimension_set_service_instance.conn is not conn:
        _dimension_set_service_instance = DimensionSetService(conn)
    return _dimension_set_service_instance
