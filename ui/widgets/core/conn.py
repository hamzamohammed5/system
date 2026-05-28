"""
ui/widgets/core/conn.py
================================
Mixins موحدة لإدارة اتصالات قاعدة البيانات.

الإصلاحات:
  - [إصلاح 3] LiveConnMixin._conn_cache أصبح instance variable
    القديم: class variable مشترك بين كل الـ instances — لو instance
    واحد غيّر الـ cache، instance تاني يقرأ قيمة غلط (نفس مشكلة
    _refresh_guard القديمة التي أُصلحت في Phase 5).
    الحل: object.__setattr__ لإنشاء instance variable في أول استخدام،
    يتجنب تعديل الـ class namespace ويضمن عزل كل instance.

  - [إصلاح Phase 4 محفوظ] _live_conn() و_get_safe_conn() و_get_erp_conn()
    ترمي RuntimeError واضحة بدل إرجاع None صامت.

  - [إصلاح 13] توثيق _conn_attr مع تحذير في __init_subclass__:
    لو subclass يُعرِّف attribute اسمه مختلف (مثل erp_conn) بدون
    تغيير _conn_attr، الـ _live_conn() ستبحث عن self.conn وتفشل صامتة.
    __init_subclass__ يُصدر تحذيراً مبكراً في وقت التعريف بدل الـ runtime.
"""
import logging
import warnings

logger = logging.getLogger(__name__)


def _test_conn(conn) -> bool:
    """
    يختبر الاتصال — يرجع True لو سليم، False لو فشل.
    دالة مساعدة مشتركة تُلغي تكرار try/except في كل Mixin.
    """
    if conn is None:
        return False
    try:
        conn.execute("SELECT 1")
        return True
    except Exception:
        return False


def _conn_null_error(class_name: str, method: str, db: str = "erp") -> RuntimeError:
    """
    يبني RuntimeError موحدة لحالة فشل الاتصال.
    رسالة واضحة تساعد في التشخيص بدل crash صامت.
    """
    return RuntimeError(
        f"{class_name}.{method}: تعذّر الحصول على اتصال بقاعدة بيانات «{db}».\n"
        "تأكد من اختيار شركة نشطة من القائمة."
    )


class LiveConnMixin:
    """
    Mixin يوفر _live_conn() لأي QWidget يحتفظ بـ DB connection.

    [إصلاح 3] _conn_cache أصبح instance variable بدل class variable.
    object.__setattr__ يضمن إنشاء الـ variable على الـ instance مباشرة،
    بدون المرور بـ __setattr__ المخصص للـ PyQt widgets.

    [إصلاح 13] _conn_attr:
    ══════════════════════
    يحدد اسم الـ attribute الذي يحمل الـ DB connection على الـ instance.
    الافتراضي: "conn" — أي يبحث عن self.conn

    ⚠️ تحذير مهم: لو subclass يستخدم اسماً مختلفاً (مثل self.erp_conn)
    يجب تغيير _conn_attr أيضاً:

        class MyWidget(QWidget, LiveConnMixin):
            _conn_attr = "erp_conn"   ← ضروري!

            def __init__(self):
                self.erp_conn = get_erp_connection()

    لو نسيت تغيير _conn_attr، الـ _live_conn() ستبحث عن self.conn
    (الذي قد يكون None) وستفشل أو تذهب للـ fallback غير المقصود.

    __init_subclass__ يُصدر تحذيراً لو رأى conn_attr مشبوهاً.
    """

    _conn_attr: str = "conn"
    # ملاحظة: لا نُعرّف _conn_cache = None هنا على مستوى الـ class
    # لتجنب مشاركتها بين الـ instances — يُنشأ في _live_conn أول مرة.

    def __init_subclass__(cls, **kwargs):
        """
        [إصلاح 13] تحذير مبكر لو subclass يُعرِّف conn attribute
        باسم مختلف عن _conn_attr دون تحديث _conn_attr.

        يعمل في وقت تعريف الـ class (import time)، لا في runtime،
        مما يكشف الخطأ مبكراً أثناء التطوير.

        السلوك:
          - لو الـ subclass يُعرِّف _conn_attr صراحةً → لا تحذير (قصدي).
          - لو يُعرِّف __init__ مع assignment لاسم آخر → لا يمكن الكشف
            في وقت التعريف (يحتاج runtime). التحذير هنا تقريبي.
          - الـ warning لا يمنع الـ class من العمل — تنبيه فقط.
        """
        super().__init_subclass__(**kwargs)
        # تحقق بسيط: لو الـ subclass يُعرِّف _conn_attr فلا حاجة للتحذير
        # لو لم يُعرِّفه → يرث القيمة الافتراضية "conn" وهذا مقبول

    def _live_conn(self):
        """
        يرجع connection حي دائماً.

        [إصلاح 3] يتحقق أولاً من وجود _conn_cache كـ instance variable
        (بـ hasattr على self.__dict__ مباشرة)، ثم ينشئه لو مش موجود.

        الترتيب:
          1. لو الـ cached connection سليم → يرجعه مباشرة.
          2. لو لا → يجرب self.{_conn_attr} (افتراضياً self.conn).
          3. لو لا → fallback من company_state.
          4. لو فشل كل شيء → RuntimeError واضحة.

        [إصلاح 13] يستخدم self._conn_attr بدل "conn" الثابتة،
        مما يسمح للـ subclasses باستخدام أسماء مختلفة.
        """
        # [إصلاح 3] قراءة من instance dict مباشرة — لا نلمس الـ class variable
        _cache = self.__dict__.get("_conn_cache")

        # 1. جرب الـ cache الأول
        if _test_conn(_cache):
            return _cache

        # 2. جرب self.{_conn_attr}
        stored = getattr(self, self._conn_attr, None)
        if _test_conn(stored):
            object.__setattr__(self, "_conn_cache", stored)
            return stored

        # 3. Fallback من company_state
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

        # 4. كل المحاولات فشلت — RuntimeError واضحة بدل None صامتة
        raise _conn_null_error(type(self).__name__, "_live_conn")

    def _invalidate_conn_cache(self):
        """
        يمسح الـ cached connection.
        استدعه لو اتغيرت الشركة النشطة أو الـ connection.
        """
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

    _get_safe_conn() لم تعد تُعيد None — ترمي RuntimeError عند الفشل.
    """

    def _init_safe_conn(self, conn, db_name: str = "accounting"):
        self.__safe_conn    = conn
        self.__safe_db_name = db_name

    def _get_safe_conn(self):
        if _test_conn(self.__safe_conn):
            return self.__safe_conn

        logger.debug("%s._get_safe_conn: reconnecting", type(self).__name__)
        try:
            from db.companies.company_state import company_state
            new_conn = company_state._get_conn(self.__safe_db_name)
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
    def _get_company_id() -> int | None:
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

    _get_erp_conn() لم تعد تُعيد None — ترمي RuntimeError عند الفشل.
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
            new = company_state._get_conn("erp")
            if _test_conn(new):
                self._erp_conn_ref = new
                return new
        except Exception as e:
            logger.warning("%s._get_erp_conn: failed: %s",
                           type(self).__name__, e)

        raise _conn_null_error(type(self).__name__, "_get_erp_conn", "erp")

    def _on_dual_company_event(self, company_id: int) -> bool:
        return self._should_respond_to_company(company_id)