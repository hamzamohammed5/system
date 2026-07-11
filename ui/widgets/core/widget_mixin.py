"""
ui/widgets/core/widget_mixin.py
=================================
WidgetMixin — mixin عام يربط أي widget بالـ bus events تلقائياً.

الوظيفة:
    بدل ما كل widget يكتب كود weakref وربط bus من الصفر،
    يرث من WidgetMixin ويستدعي _init_widget_mixin() في __init__،
    وبعدين يعرّف الدوال اللي محتاجها بس.

الاستخدام الأساسي:
    class MyWidget(QLabel, WidgetMixin):
        def __init__(self):
            super().__init__()
            self._init_widget_mixin()   # ← سطر واحد يربط كل الـ events
            self._refresh_style()       # ← أول رسم للـ stylesheet

        def _refresh_style(self, *_):
            self.setStyleSheet(f"color:{_C['text_primary']};")

الـ parameters:
    theme: bool = True  → يربط bus.theme_changed     → يستدعي _refresh_style
    font : bool = True  → يربط bus.font_changed      → يستدعي _refresh_style
    lang : bool = False → يربط bus.language_changed  → يستدعي _refresh_lang
    data : bool = False → يربط bus.company_data_changed → يستدعي _refresh_data
                          مع تحقق من company_id

الدوال اللي ممكن تعرّفها في الـ subclass:
    _refresh_style(self, *_)          → stylesheet — اتنادى عند theme أو font
    _refresh_lang(self, *_)           → نصوص     — اتنادى عند language
    _refresh_data(self, company_id)   → بيانات DB — اتنادى عند company_data

ملاحظات:
    - كل الربط بـ weakref — الـ widget مش هيمنع الـ GC
    - Qt.UniqueConnection — بيمنع الربط المضاعف لو _init_widget_mixin اتنادى أكتر من مرة
    - _cached_company_id — بيحفظ الـ company_id الحالي ويتحدث تلقائياً لما الشركة تتغير
    - _widget_mixin_init — flag يمنع double init (instance-level مش class-level)
    - _widget_mixin_slots — list على الـ instance يمنع الـ GC يحذف الـ slots
    - [إصلاح stylesheet] كل الـ slots بتتحقق من sip.isdeleted قبل استدعاء _refresh_style
      عشان تمنع خطأ "Could not parse stylesheet of object QPushButton(0x...)"
      اللي بييجي لما Qt بتحاول تطبق stylesheet على widget اتحذف من C++
"""

import weakref
import logging

from PyQt5.QtCore import Qt

try:
    import sip as _sip
    def _is_deleted(obj) -> bool:
        """يتحقق إن الـ Qt C++ object لسه موجود."""
        try:
            return _sip.isdeleted(obj)
        except Exception:
            return True
except ImportError:
    # fallback لو sip مش متاح
    def _is_deleted(obj) -> bool:
        return False

logger = logging.getLogger(__name__)


class WidgetMixin:

    # ── لا class-level mutable attributes ──────────────────────────────────
    # [إصلاح] القيم دي كانت على مستوى الـ class وده كان بيسبب مشاركتها
    # بين كل الـ instances. دلوقتي بيتحطوا على الـ instance في _init_widget_mixin.
    # بس محتاجين نعرّف الـ type hints بس عشان الـ static analyzers:
    _cached_company_id: "int | None"
    _widget_mixin_init: bool
    _widget_mixin_slots: "list | None"

    def _init_widget_mixin(self,
                            theme: bool = True,
                            font: bool = True,
                            lang: bool = True,
                            data: bool = True) -> None:
        """
        يربط الـ widget بالـ bus events المطلوبة.
        استدعيه في __init__ بعد super().__init__() مباشرة.

        آمن للاستدعاء أكتر من مرة — في حالة Base class تستدعيه بـ defaults
        والـ subclass يستدعيه بـ params مختلفة، الاستدعاء التاني بيربط
        الـ events الجديدة فقط (اللي مش اترتبطت قبل كده).

        مثال:
            self._init_widget_mixin()                      # كل حاجة theme + font + lang + data
            self._init_widget_mixin(lang=False)             # theme + font + data
            self._init_widget_mixin(theme=False)           # font + lang + data
            self._init_widget_mixin(font=False)            # theme + lang + data
        """
        # ── أول استدعاء: نحضّر الـ state ─────────────────────────────────
        first_call = not getattr(self, '_widget_mixin_init', False)
        if first_call:
            self._widget_mixin_init = True
            # نحفظ كل الـ slots في list على الـ instance
            # عشان نضمن إن الـ GC مش هيحذفهم طول عمر الـ widget
            self._widget_mixin_slots = []
            # نتتبع الـ events اللي اترتبطت عشان نتجنب ربط مضاعف
            self._widget_mixin_bound: "set[str]" = set()

        # ── تصفية: بس الـ events الجديدة اللي ملتش اترتبطت ─────────────
        _bound = self._widget_mixin_bound  # type: ignore[attr-defined]
        _register_theme = theme and "theme" not in _bound
        _register_font  = font  and "font"  not in _bound
        _register_lang  = lang  and "lang"  not in _bound
        _register_data  = data  and "data"  not in _bound

        if not any([_register_theme, _register_font, _register_lang, _register_data]):
            # مفيش events جديدة — مفيش حاجة نعملها
            return

        # lazy import عشان نتجنب circular imports عند load الـ module
        try:
            from ui.widgets.core.events import bus
        except Exception as e:
            logger.warning(f"WidgetMixin: فشل import bus — {e}")
            return

        # weakref عشان الـ widget يقدر يتحذف من الـ memory بشكل طبيعي
        # لو استخدمنا self مباشرة في الـ closure هيحصل memory leak
        _weak = weakref.ref(self)

        # ── helper: تحقق آمن من الـ widget قبل أي عملية ──────────────────
        # [إصلاح stylesheet] بيمنع خطأ:
        #   "Could not parse stylesheet of object QPushButton(0x...)"
        # السبب: بتييجي لما Qt بتطبق stylesheet على widget اتحذف من C++
        # الحل: sip.isdeleted() بتتحقق إن الـ C++ object لسه موجود
        def _safe_obj():
            """يرجع الـ widget لو لسه حي وإلا None."""
            obj = _weak()
            if obj is None:
                return None
            if _is_deleted(obj):
                return None
            return obj

        # ── theme ─────────────────────────────────────────────────────────
        if _register_theme:
            def _on_theme_change(_=None):
                obj = _safe_obj()
                if obj is None:
                    return
                try:
                    obj._refresh_style()
                except RuntimeError:
                    # الـ widget اتحذف من C++ بعد تحقق sip — race condition نادر
                    pass

            self._widget_mixin_slots.append(_on_theme_change)
            bus.theme_changed.connect(_on_theme_change, Qt.UniqueConnection)
            _bound.add("theme")

        # ── font ──────────────────────────────────────────────────────────
        # slot منفصل عن theme عشان لو الـ subclass عاوز يفرق بينهم مستقبلاً
        if _register_font:
            def _on_font_change(_=None):
                obj = _safe_obj()
                if obj is None:
                    return
                try:
                    obj._refresh_style()
                except RuntimeError:
                    pass

            self._widget_mixin_slots.append(_on_font_change)
            bus.font_changed.connect(_on_font_change, Qt.UniqueConnection)
            _bound.add("font")

        # ── language ──────────────────────────────────────────────────────
        if _register_lang:
            def _on_lang_change(_=None):
                obj = _safe_obj()
                if obj is None:
                    return
                try:
                    obj._refresh_lang()
                except RuntimeError:
                    pass

            self._widget_mixin_slots.append(_on_lang_change)
            bus.language_changed.connect(_on_lang_change, Qt.UniqueConnection)
            _bound.add("lang")

        # ── company data ──────────────────────────────────────────────────
        if _register_data:
            # نحاول نجيب الـ company_id الحالي
            # لو فشل (مفيش شركة نشطة) نحطه None ونعمل lazy init في أول إشعار
            try:
                from services.companies.company_service import CompanyService
                self._cached_company_id = CompanyService.get_current_company_id()
            except Exception:
                self._cached_company_id = None

            def _on_data_change(company_id: "int | None"):
                obj = _safe_obj()
                if obj is None:
                    return

                # تجاهل لو company_id جه None (حالة edge — مفيش شركة نشطة)
                if company_id is None:
                    return

                try:
                    # حدّث الـ cache دايماً (lazy init + شركة جديدة + نفس الشركة)
                    # ثم استدعي _refresh_data في كل الحالات
                    obj._cached_company_id = company_id
                    obj._refresh_data(company_id)

                except RuntimeError:
                    # الـ widget اتحذف من C++
                    pass
                except Exception as e:
                    # بنلوج الـ error بس مش بنوقف الـ UI
                    logger.error(
                        f"{obj.__class__.__name__}._refresh_data: {e}",
                        exc_info=True   # بيضيف الـ traceback كامل في الـ log
                    )

            self._widget_mixin_slots.append(_on_data_change)
            bus.company_data_changed.connect(_on_data_change, Qt.UniqueConnection)
            _bound.add("data")

    # ── default implementations ───────────────────────────────────────────
    # موجودة عشان الـ subclass ميضطرش يعرّف كل الدوال —
    # يعرّف بس اللي محتاجها

    def _refresh_style(self, *_):
        """
        Override لإعادة بناء الـ stylesheet.
        بتتنادى تلقائياً عند تغيير الثيم أو حجم الخط.

        مثال:
            def _refresh_style(self, *_):
                self.setStyleSheet(f"color:{_C['text_primary']};")
        """
        pass

    def _refresh_lang(self, *_):
        """
        Override لتحديث النصوص عند تغيير اللغة.
        بتتنادى تلقائياً عند bus.language_changed.

        مثال:
            def _refresh_lang(self, *_):
                self.setText(tr('save'))
        """
        pass

    def _refresh_data(self, company_id: "int | None" = None):
        """
        Override لإعادة تحميل البيانات من DB.
        بتتنادى تلقائياً عند bus.company_data_changed.
        بتتنادى برضو لما الشركة نفسها تتغير.

        مثال:
            def _refresh_data(self, company_id=None):
                rows = fetch_items(self._conn)
                prev = self.currentData()   # احفظ الاختيار الحالي

                self.clear()                # QComboBox.clear() — بتمسح كل الـ items
                self.addItem(tr('all'), None)

                for row in rows:
                    # addItem(النص_اللي_يتعرض, البيانات_المخفية)
                    # البيانات المخفية (ID) بتتجاب بـ currentData()
                    self.addItem(row['name'], row['id'])

                # أعد الاختيار السابق لو لسه موجود
                for i in range(self.count()):
                    if self.itemData(i) == prev:
                        self.setCurrentIndex(i)
                        break
        """
        pass