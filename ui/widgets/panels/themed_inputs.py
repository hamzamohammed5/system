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
from PyQt5.QtWidgets import QLineEdit, QComboBox, QDateEdit, QTextEdit, QPlainTextEdit

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
        self._refresh_style()

    def _refresh_style(self, *_):
        self.setStyleSheet(input_style(self._h))


class ThemedTextEdit(QTextEdit, WidgetMixin):
    """QTextEdit (متعدد الأسطر) بيتابع الثيم تلقائيًا."""

    def __init__(self, parent=None, min_height: int = INPUT_HEIGHT):
        super().__init__(parent)
        self._h = min_height
        self._init_widget_mixin(font=False, lang=False, data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        self.setStyleSheet(input_style(self._h))


class ThemedPlainTextEdit(QPlainTextEdit, WidgetMixin):
    """QPlainTextEdit بيتابع الثيم تلقائيًا."""

    def __init__(self, parent=None, min_height: int = INPUT_HEIGHT):
        super().__init__(parent)
        self._h = min_height
        self._init_widget_mixin(font=False, lang=False, data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        self.setStyleSheet(input_style(self._h))
