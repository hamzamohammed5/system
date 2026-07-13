"""
ui/widgets/panels/themed_inputs.py
=====================================
Themed input widgets — الحل الجذري لمشكلة "خلفيات فاتحة باقية بعد التحويل لـ dark".

المشكلة:
--------
كتير من الأماكن في المشروع كانت بتستخدم QLineEdit() / QComboBox() مباشرة
بدون setStyleSheet() خالص. الـ widget ده كان بياخد الـ default Qt style
(أبيض دايمًا) لأنه:
  1. مفيش ستايل بيتحط عليه وقت الإنشاء.
  2. مفيش استماع لـ theme_changed عشان يعيد رسم نفسه.

الحل:
-----
نفس نمط _ThemedDoubleSpinBox الموجود في form_fields.py:
  - الـ widget بيرث WidgetMixin.
  - بيسجل نفسه في theme_changed عبر _init_widget_mixin(theme=True,...).
  - عنده _refresh_style() بيتنادى تلقائيًا كل مرة الثيم يتغير، وكمان أول
    مرة وقت الإنشاء.

الاستخدام:
----------
    from ui.widgets.panels.themed_inputs import ThemedLineEdit, ThemedComboBox

    # بدل:
    self.inp_code = QLineEdit()

    # اكتب:
    self.inp_code = ThemedLineEdit()

كل باقي الـ API (setPlaceholderText, setMinimumHeight, text(), setText()...)
شغالة بنفس الشكل بالظبط لأنها QLineEdit/QComboBox عادي، بس بقى عنده ستايل
ذاتي يتابع الثيم.
"""
from PyQt5.QtWidgets import QLineEdit, QComboBox, QDateEdit, QTextEdit, QPlainTextEdit, QFrame
from PyQt5.QtCore import Qt

from ui.widgets.core.widget_mixin import WidgetMixin
from ..theme.input_styles import input_style
from ui.constants import INPUT_HEIGHT


class ThemedLineEdit(QLineEdit, WidgetMixin):
    """
    QLineEdit بيتابع الثيم تلقائيًا — بديل مباشر لـ QLineEdit().

    [ملاحظة تصميم مهمة] لا يُستدعى self._refresh_style() تلقائيًا هنا في
    نهاية __init__. السبب: كلاسات وارثة (زي _TreeGroupCombo) ممكن تكون
    عايزة تبني أجزاء إضافية (self._tree_view مثلاً) بعد استدعاء super().__init__()
    وقبل أول استدعاء لـ _refresh_style الخاصة بيها (اللي هي override).
    لو استدعيناها هنا تلقائيًا، هتتنفذ نسخة الكلاس الوارث قبل ما يبني
    أجزاءه فتطلع AttributeError.

    لذلك: كل كلاس Themed* بيستدعي self._refresh_style() بنفسه، صراحةً،
    في آخر سطر من __init__ بتاعه — بعد ما يخلص بناء كل الأجزاء.
    الكلاسات البسيطة (زي الاستخدام العادي لـ ThemedLineEdit وحدها) لازم
    تتذكر برضه تعمل نفس الحاجة، وهي بتعملها فعلاً هنا في __init__ الأساسي.
    """

    def __init__(self, parent=None, min_height: int = INPUT_HEIGHT, error: bool = False):
        super().__init__(parent)
        self._h = min_height
        self._error = error
        self._init_widget_mixin(font=False, lang=False, data=False)
        if type(self) is ThemedLineEdit:
            self._refresh_style()

    def _refresh_style(self, *_):
        self.setStyleSheet(input_style(self._h, error=self._error))

    def set_error(self, error: bool):
        """يبدّل حالة الخطأ (حدود حمراء) ويعيد الرسم فورًا."""
        self._error = error
        self._refresh_style()


class ThemedComboBox(QComboBox, WidgetMixin):
    """
    QComboBox بيتابع الثيم تلقائيًا — بديل مباشر لـ QComboBox().

    [مهم لو بترث من الكلاس ده] لو عندك كلاس وارث بيضيف أجزاء إضافية
    (زي self._tree_view)، استخدم النمط ده بالظبط:

        class MyCombo(ThemedComboBox):
            def __init__(self, parent=None):
                super().__init__(parent, auto_style=False)   # لا تبني الستايل لسه
                self._tree_view = QTreeView(self)             # ابني أجزاءك أولاً
                ...
                self._refresh_style()                          # ثم استدعِ الستايل يدويًا
                self._init_widget_mixin(...)                   # سجّل الاستماع لتغيير الثيم
    """

    def __init__(self, parent=None, min_height: int = INPUT_HEIGHT, auto_style: bool = True):
        super().__init__(parent)
        self._h = min_height
        if auto_style:
            self._init_widget_mixin(font=False, lang=False, data=False)
            self._refresh_style()

    def _refresh_style(self, *_):
        self.setStyleSheet(input_style(self._h))


class ThemedDateEdit(QDateEdit, WidgetMixin):
    """QDateEdit بيتابع الثيم تلقائيًا — بديل مباشر لـ QDateEdit()."""

    def __init__(self, parent=None, min_height: int = INPUT_HEIGHT):
        super().__init__(parent)
        self._h = min_height
        self._init_widget_mixin(font=False, lang=False, data=False)
        if type(self) is ThemedDateEdit:
            self._refresh_style()

    def _refresh_style(self, *_):
        self.setStyleSheet(input_style(self._h))


class ThemedTextEdit(QTextEdit, WidgetMixin):
    """QTextEdit (متعدد الأسطر) بيتابع الثيم تلقائيًا."""

    def __init__(self, parent=None, min_height: int = INPUT_HEIGHT):
        super().__init__(parent)
        self._h = min_height
        self._init_widget_mixin(font=False, lang=False, data=False)
        if type(self) is ThemedTextEdit:
            self._refresh_style()

    def _refresh_style(self, *_):
        self.setStyleSheet(input_style(self._h))


class ThemedPlainTextEdit(QPlainTextEdit, WidgetMixin):
    """QPlainTextEdit بيتابع الثيم تلقائيًا."""

    def __init__(self, parent=None, min_height: int = INPUT_HEIGHT):
        super().__init__(parent)
        self._h = min_height
        self._init_widget_mixin(font=False, lang=False, data=False)
        if type(self) is ThemedPlainTextEdit:
            self._refresh_style()


class ThemedFrame(QFrame, WidgetMixin):
    """
    QFrame بيتابع الثيم تلقائيًا — بديل مباشر لـ QFrame() لأي frame
    محتاج خلفية/حدود بتتغيّر مع الثيم (زي شاشات "لا يوجد بيانات" الفارغة).

    [السبب في الحاجة للكلاس ده تحديدًا، مش نفس نمط ThemedLineEdit]
    QFrame من غير QSS بيتصرف بشكل مختلف عن QLineEdit/QComboBox: خاصية
    "background" في الـ stylesheet مش بتتطبّق فعليًا وقت الرسم إلا لو
    WA_StyledBackground مفعّلة صراحةً (QLineEdit/QComboBox عندهم السلوك
    ده افتراضيًا، QFrame لأ).

    كمان اكتشفنا مشكلة تانية مرتبطة: لو الثيم اتغيّر والـ frame كانت
    مخفية (widget في تاب مش نشط مثلاً)، الـ stylesheet بيتحدّث في الذاكرة
    صح، لكن Qt مبيعيدش رسمها فعليًا إلا لما تظهر تاني — وأحيانًا بيرسمها
    بحالة قديمة (cached) لحد أول إعادة رسم كاملة. الحل: showEvent بيجبر
    _refresh_style() تاني في اللحظة اللي الـ frame بتظهر فيها فعليًا.

    الاستخدام:
        from ui.widgets.panels.themed_inputs import ThemedFrame

        # بدل:
        self._empty_state = QFrame()
        self._empty_state.setStyleSheet(f"background: {_C['bg_input']}; border: none;")

        # اكتب:
        self._empty_state = ThemedFrame(bg_key="bg_input")
        # لو محتاج حدود أو راديوس، مرّرهم كمان:
        self._empty_state = ThemedFrame(bg_key="bg_input", border="none")
    """

    def __init__(self, parent=None, bg_key: str = "bg_surface",
                 border: str = "none", border_radius: int = 0):
        super().__init__(parent)
        self._bg_key        = bg_key
        self._border        = border
        self._border_radius = border_radius
        # [أساسي] من غيرها خاصية background في الـ stylesheet هتتخزن
        # بس مش هتتطبّق فعليًا وقت الرسم — QFrame محتاجها صراحةً.
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._init_widget_mixin(font=False, lang=False, data=False)
        # [إصلاح جذري] لا تنادِ self._refresh_style() هنا إلا لو الكلاس
        # الفعلي هو ThemedFrame نفسها (استخدام مباشر بدون وراثة).
        #
        # السبب: self._refresh_style() نداء polymorphic — لو فيه كلاس
        # وارث (زي ListHeader, EmptyState, NotificationBar, StatCard,
        # _OfferItemRow ...) عامل override لـ _refresh_style()، فالنداء
        # هنا هيوجّه فورًا لنسخة الكلاس الوارث، رغم إن __init__ بتاعه
        # لسه ما وصلش لسطر super().__init__() في الأغلب (لسه في نص
        # تنفيذ super().__init__() نفسها دلوقتي!) — يعني _build() بتاعته
        # لسه ما اتنفذتش، والـ attributes/widgets اللي _refresh_style
        # الوارثة محتاجاها لسه مش موجودة → AttributeError متكرر.
        #
        # كل الكلاسات الوارثة من ThemedFrame في المشروع بتنادي بالفعل
        # self._refresh_style() صراحةً في آخر سطر من __init__ بتاعها
        # (بعد ما تخلص _build())، فمفيش داعي إن ThemedFrame تتحمل
        # مسؤولية النداء الأول نيابة عنها — العكس هو اللي بيسبب الأعطال.
        if type(self) is ThemedFrame:
            self._refresh_style()

    def showEvent(self, event):
        """[إصلاح dark-theme] يجبر إعادة تطبيق الستايل وقت ظهور الـ frame
        فعليًا — يغطي حالة إن الثيم اتغيّر وهي كانت مخفية."""
        super().showEvent(event)
        self._refresh_style()

    def _refresh_style(self, *_):
        from ui.theme import _C
        radius = f"border-radius:{self._border_radius}px; " if self._border_radius else ""
        self.setStyleSheet(
            f"background: {_C[self._bg_key]}; border: {self._border}; {radius}"
        )

    def set_bg_key(self, bg_key: str):
        """يغيّر مفتاح لون الخلفية المستخدم من _C ويعيد الرسم فورًا."""
        self._bg_key = bg_key
        self._refresh_style()
