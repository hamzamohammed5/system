"""
ui/widgets/core/conn.py
================================
Mixins موحدة لإدارة اتصالات قاعدة البيانات.

[إصلاح 3] LiveConnMixin._conn_cache أصبح instance variable.
[إصلاح Phase 4] _live_conn() / _get_safe_conn() / _get_erp_conn()
  ترمي RuntimeError واضحة بدل إرجاع None صامت.
[إصلاح 13] __init_subclass__ تُصدر تحذيراً فعلياً.
[إصلاح private API] SafeConnMixin._get_safe_conn و DualConnMixin._get_erp_conn
  يستخدمان get_erp_conn() (public) بدل _get_conn() (private).
[إصلاح شرط مستحيل] _get_safe_conn كانت تحتوي على:
    if self.__safe_db_name == "erp": ...
    else:
        if get_fn and self.__safe_db_name == "erp":  ← مستحيل دائماً False هنا
  أُصلح إلى منطق مباشر بدون الشرط الداخلي الزائد.
[إصلاح _get_safe_conn else branch] القديم:
    else:
        get_fn = getattr(company_state, "get_erp_conn", None)
        if get_fn and self.__safe_db_name == "erp":  ← مستحيل
            new_conn = get_fn()
        else:
            _get = getattr(company_state, "_get_conn", None)
            new_conn = _get(self.__safe_db_name) if _get else None
  الجديد: إزالة الشرط المستحيل، إضافة warning لو لم يُجد public API.
"""
import logging
import warnings

logger = logging.getLogger(__name__)


def _test_conn(conn) -> bool:
    """يختبر الاتصال — يرجع True لو سليم، False لو فشل."""
    if conn is None:
        return False
    try:
        conn.execute("SELECT 1")
        return True
    except Exception:
        return False


def _conn_null_error(class_name: str, method: str, db: str = "erp") -> RuntimeError:
    """يبني RuntimeError موحدة لحالة فشل الاتصال."""
    return RuntimeError(
        f"{class_name}.{method}: تعذّر الحصول على اتصال بقاعدة بيانات «{db}».\n"
        "تأكد من اختيار شركة نشطة من القائمة."
    )


class LiveConnMixin:
    """Mixin يوفر _live_conn() لأي QWidget يحتفظ بـ DB connection."""

    _conn_attr: str = "conn"

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if "_conn_attr" in cls.__dict__:
            return
        suspicious_names = set()
        for name in cls.__dict__.get("__annotations__", {}):
            if name != "conn" and ("conn" in name.lower() or "connection" in name.lower()):
                suspicious_names.add(name)
        for name, val in cls.__dict__.items():
            if name.startswith("_"):
                continue
            if not callable(val) and name != "conn":
                if "conn" in name.lower() or "connection" in name.lower():
                    suspicious_names.add(name)
        if suspicious_names:
            warnings.warn(
                f"{cls.__qualname__} يرث من LiveConnMixin ويُعرِّف "
                f"{suspicious_names} لكن لم يُحدِّث _conn_attr. "
                f"لو كان يستخدم اسماً مختلفاً للـ connection، أضف: "
                f"_conn_attr = '{next(iter(suspicious_names))}'",
                UserWarning,
                stacklevel=2,
            )

    def _live_conn(self):
        """
        يرجع connection حي دائماً.
        1. الـ cache → 2. self.conn → 3. company_state → 4. RuntimeError
        """
        _cache = self.__dict__.get("_conn_cache")
        if _test_conn(_cache):
            return _cache

        stored = getattr(self, self._conn_attr, None)
        if _test_conn(stored):
            object.__setattr__(self, "_conn_cache", stored)
            return stored

        logger.debug("%s._live_conn: stored conn failed, trying fallback",
                     type(self).__name__)
        try:
            from db.companies.company_state import company_state
            new_conn = company_state.get_erp_conn()
            if _test_conn(new_conn):
                object.__setattr__(self, "_conn_cache", new_conn)
                setattr(self, self._conn_attr, new_conn)
                return new_conn
        except Exception as e:
            logger.warning("%s._live_conn: fallback failed: %s",
                           type(self).__name__, e)

        raise _conn_null_error(type(self).__name__, "_live_conn")

    def _invalidate_conn_cache(self):
        """يمسح الـ cached connection."""
        object.__setattr__(self, "_conn_cache", None)

    def _live_acc_conn(self):
        """يرجع accounting connection حي."""
        stored = getattr(self, "acc_conn", None)
        if _test_conn(stored):
            return stored

        logger.debug("%s._live_acc_conn: failed, trying fallback",
                     type(self).__name__)
        try:
            from db.shared.connection import get_accounting_connection
            new_conn = get_accounting_connection()
            if _test_conn(new_conn):
                return new_conn
        except Exception as e:
            logger.warning("%s._live_acc_conn: fallback failed: %s",
                           type(self).__name__, e)

        raise _conn_null_error(type(self).__name__, "_live_acc_conn", "accounting")


class SafeConnMixin:
    """
    Mixin متقدم يدعم إعادة الاتصال التلقائي.

    [إصلاح شرط مستحيل + إصلاح else branch]:
    القديم:
        if self.__safe_db_name == "erp":
            new_conn = company_state.get_erp_conn()
        else:
            get_fn = getattr(company_state, "get_erp_conn", None)
            if get_fn and self.__safe_db_name == "erp":  ← مستحيل! الـ else يعني != "erp"
                new_conn = get_fn()
            else:
                _get = getattr(company_state, "_get_conn", None)
                new_conn = _get(self.__safe_db_name) if _get else None

    الجديد: منطق مباشر — لو erp استخدم public API، وإلا استخدم _get_conn مع warning.
    """

    def _init_safe_conn(self, conn, db_name: str = "accounting"):
        self.__safe_conn    = conn
        self.__safe_db_name = db_name

    def _get_safe_conn(self):
        if _test_conn(self.__safe_conn):
            return self.__safe_conn

        logger.debug("%s._get_safe_conn: reconnecting to '%s'",
                     type(self).__name__, self.__safe_db_name)
        try:
            from db.companies.company_state import company_state

            if self.__safe_db_name == "erp":
                # public API مباشرة
                new_conn = company_state.get_erp_conn()
            else:
                # لأنواع DB الأخرى (accounting, etc.) — نحاول _get_conn كـ fallback
                # لأن public API غير متاح لكل أنواع DB
                _get = getattr(company_state, "_get_conn", None)
                if _get is not None:
                    new_conn = _get(self.__safe_db_name)
                else:
                    logger.warning(
                        "%s._get_safe_conn: no _get_conn on company_state for db '%s', "
                        "trying erp fallback",
                        type(self).__name__, self.__safe_db_name
                    )
                    new_conn = company_state.get_erp_conn()

                # لو _get_conn لم يُعطِ نتيجة، نحاول erp كـ last resort
                if not _test_conn(new_conn):
                    logger.warning(
                        "%s._get_safe_conn: no valid conn for db '%s', "
                        "falling back to erp",
                        type(self).__name__, self.__safe_db_name
                    )
                    new_conn = company_state.get_erp_conn()

            if _test_conn(new_conn):
                self.__safe_conn = new_conn
                return new_conn
        except Exception as e:
            logger.warning("%s._get_safe_conn: reconnect failed: %s",
                           type(self).__name__, e)

        raise _conn_null_error(
            type(self).__name__, "_get_safe_conn", self.__safe_db_name
        )

    @staticmethod
    def _get_company_id() -> "int | None":
        try:
            from db.companies.company_state import company_state
            return company_state.company_id if company_state.is_ready else None
        except Exception:
            return None

    def _should_respond_to_company(self, company_id: int,
                                    stored_attr: str = "_company_id") -> bool:
        stored = getattr(self, stored_attr, None)
        should = (stored is None) or (stored == company_id)
        if should:
            setattr(self, stored_attr, company_id)
        return should


class DualConnMixin(SafeConnMixin):
    """
    Mixin لأي widget يحتاج acc_conn + erp_conn معاً.
    [إصلاح private API] يستخدم get_erp_conn() (public).
    """

    def _init_dual_conn(self, acc_conn, erp_conn, acc_db: str = "accounting"):
        self._init_safe_conn(acc_conn, acc_db)
        self._erp_conn_ref = erp_conn
        self._company_id   = self._get_company_id()

    def _get_erp_conn(self):
        if _test_conn(self._erp_conn_ref):
            return self._erp_conn_ref

        logger.debug("%s._get_erp_conn: reconnecting", type(self).__name__)
        try:
            from db.companies.company_state import company_state
            # [إصلاح private API] get_erp_conn() (public) بدل _get_conn("erp")
            new = company_state.get_erp_conn()
            if _test_conn(new):
                self._erp_conn_ref = new
                return new
        except Exception as e:
            logger.warning("%s._get_erp_conn: failed: %s",
                           type(self).__name__, e)

        raise _conn_null_error(type(self).__name__, "_get_erp_conn", "erp")

    def _on_dual_company_event(self, company_id: int) -> bool:
        return self._should_respond_to_company(company_id)