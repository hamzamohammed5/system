"""
ui/tabs/pricing/pricing/_stat_box.py
=====================================
دالة مساعدة لإنشاء بطاقة إحصائية في تبويب التسعير.

[إصلاح ثيم] stat_box() كانت بترجع QFrame عادي بستايل ثابت (hardcoded)
  اتحط مرة واحدة وقت الاستدعاء بس. النتيجة: أي كرت اتعمل بيها (كروت
  التسعير "التكلفة/الربح/سعر البيع المقترح..."، كروت العروض "الربح/
  إجمالي التكلفة/سعر البيع النهائي...") كان يفضل بالستايل القديم لما
  الثيم يتغير — خلفية بيضاء واضحة فوق باقي الواجهة الداكنة، مهما كان
  الكلاس المستخدم (_PricingPanel أو _OfferForm أو _OfferDetails) عنده
  _refresh_style() شغالة، لأن محدش فيهم كان بيلمس الـ frame ده تحديدًا.

  الحل: StatBoxFrame — كلاس صغير وارث WidgetMixin، بيسجل نفسه في
  theme_changed ويعيد رسم نفسه (frame + العنوان + القيمة) تلقائيًا.
  stat_box() بقت wrapper بسيط بترجع (frame, lbl_val) بنفس الـ API
  القديم بالظبط، فكل الأماكن المستخدمة لها حاليًا (_pricing_panel.py,
  offer_form.py, offer_details.py) شغالة من غير أي تعديل مطلوب فيها.
"""

from PyQt5.QtWidgets import QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

from ui.widgets.panels.themed_inputs import ThemedFrame

from ui.constants import STAT_BOX_BORDER_RADIUS, STAT_BOX_BORDER_W, STAT_BOX_PADDING, STAT_INNER_MARGIN_COMPACT, STAT_CARD_SPACING_COMPACT
from ui.widgets.core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin


class StatBoxFrame(ThemedFrame, WidgetMixin):
    """
    بطاقة إحصائية بتتابع الثيم تلقائيًا.

    عناصرها:
      - lbl_title: العنوان الثابت (زي "التكلفة")
      - lbl_val:   القيمة المتغيرة (زي "120.00") — دي اللي بتتحدث بعد كده
        من الكود المستخدم (عن طريق setText مباشرة على lbl_val نفسها).
    """

    def __init__(self, label: str, color_key: str = "accent", parent=None):
        super().__init__(parent)
        self._color_key    = color_key
        self._value_color  = None  # لون مخصص للقيمة (زي أحمر/أخضر حسب الربح) — يتخطى color_key لو موجود

        lay = QVBoxLayout(self)
        m = STAT_INNER_MARGIN_COMPACT
        lay.setContentsMargins(m[0], m[1], m[2], m[3])
        lay.setSpacing(STAT_CARD_SPACING_COMPACT)

        self.lbl_title = QLabel(label)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.lbl_title)

        self.lbl_val = QLabel(tr("empty_placeholder"))
        self.lbl_val.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.lbl_val)

        self._init_widget_mixin(font=False, lang=False, data=False)
        self._refresh_style()

    def set_value_color(self, color_key: str = None):
        """
        يحدد لون القيمة يدويًا (مثلاً 'success' أو 'danger' حسب الربح)،
        بيتحفظ ويتطبق تلقائيًا عند كل _refresh_style (تغيير ثيم) كمان —
        فمفيش فقدان للون عند تبديل الثيم.
        استدعِ set_value_color(None) للرجوع للون الافتراضي (color_key
        الأصلي المُمرر وقت الإنشاء).
        """
        self._value_color = color_key
        self._refresh_style()

    def _refresh_style(self, *_):
        from ui.theme import _C
        from ui.font import FS_XS, FS_LG
        color = _C[self._value_color or self._color_key]
        self.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_surface']};
                border: {STAT_BOX_BORDER_W}px solid {_C['border']};
                border-radius: {STAT_BOX_BORDER_RADIUS}px;
                padding: {STAT_BOX_PADDING}px;
            }}
        """)
        self.lbl_title.setStyleSheet(
            f"font-size:{FS_XS}px; color:{_C['text_muted']}; background:transparent; border:none;"
        )
        self.lbl_val.setStyleSheet(
            f"font-size:{FS_LG}px; font-weight:bold; color:{color};"
            "background:transparent; border:none;"
        )


def stat_box(label: str, color_key: str = "accent") -> tuple:
    """يرجع (QFrame, QLabel_value) — بطاقة إحصائية تتابع الثيم تلقائيًا.

    Args:
        label:     النص المعروض كعنوان البطاقة (يأتي من tr() خارجياً).
        color_key: مفتاح اللون في _C (افتراضي: "accent").
    """
    frame = StatBoxFrame(label, color_key)
    return frame, frame.lbl_val
