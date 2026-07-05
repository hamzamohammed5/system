"""
ui/tabs/pricing/pricing/_stat_box.py
=====================================
دالة مساعدة لإنشاء بطاقة إحصائية في تبويب التسعير.
"""

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

from ui.theme import _C
from ui.font import FS_XS, FS_LG
from ui.constants import STAT_BOX_BORDER_RADIUS, STAT_BOX_PADDING, STAT_INNER_MARGIN_COMPACT, STAT_CARD_SPACING_COMPACT
from ui.widgets.core.i18n import tr


def stat_box(label: str, color_key: str = "accent") -> tuple:
    """يرجع (QFrame, QLabel_value) — بطاقة إحصائية.

    Args:
        label:     النص المعروض كعنوان البطاقة (يأتي من tr() خارجياً).
        color_key: مفتاح اللون في _C (افتراضي: "accent").
    """
    color = _C[color_key]
    frame = QFrame()
    frame.setStyleSheet(f"""
        QFrame {{
            background: {_C['bg_surface']};
            border: 1px solid {_C['border']};
            border-radius: {STAT_BOX_BORDER_RADIUS}px;
            padding: {STAT_BOX_PADDING}px;
        }}
    """)
    lay = QVBoxLayout(frame)
    m = STAT_INNER_MARGIN_COMPACT
    lay.setContentsMargins(m[0], m[1], m[2], m[3])
    lay.setSpacing(STAT_CARD_SPACING_COMPACT)
    lbl_title = QLabel(label)
    lbl_title.setStyleSheet(
        f"font-size:{FS_XS}px; color:{_C['text_muted']}; background:transparent; border:none;"
    )
    lbl_title.setAlignment(Qt.AlignCenter)
    lbl_val = QLabel(tr("empty_placeholder"))
    lbl_val.setStyleSheet(
        f"font-size:{FS_LG}px; font-weight:bold; color:{color};"
        "background:transparent; border:none;"
    )
    lbl_val.setAlignment(Qt.AlignCenter)
    lay.addWidget(lbl_title)
    lay.addWidget(lbl_val)
    return frame, lbl_val
