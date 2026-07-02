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
# Cache داخلي — key بـ id(conn) عشان نربط كل service بالـ connection بتاعه
# ══════════════════════════════════════════════════════════
_design_services: dict = {}
_design_size_services: dict = {}
_dimension_set_services: dict = {}


def get_design_service(conn) -> DesignService:
    """
    يرجع DesignService واحد لكل conn.
    نفس الـ conn → نفس الـ instance (بدون إعادة بناء).
    conn مختلف (شركة جديدة) → instance جديد تلقائياً.
    """
    key = id(conn)
    svc = _design_services.get(key)
    if svc is None or svc.conn is not conn:
        svc = DesignService(conn)
        _design_services[key] = svc
    return svc


def get_design_size_service(conn) -> DesignSizeService:
    """يرجع DesignSizeService واحد لكل conn."""
    key = id(conn)
    svc = _design_size_services.get(key)
    if svc is None or svc.conn is not conn:
        svc = DesignSizeService(conn)
        _design_size_services[key] = svc
    return svc


def get_dimension_set_service(conn) -> DimensionSetService:
    """يرجع DimensionSetService واحد لكل conn."""
    key = id(conn)
    svc = _dimension_set_services.get(key)
    if svc is None or svc.conn is not conn:
        svc = DimensionSetService(conn)
        _dimension_set_services[key] = svc
    return svc
