"""
ui/tabs/pricing/pricing/_stat_box.py
=====================================
دالة مساعدة لإنشاء بطاقة إحصائية في تبويب التسعير.
"""

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

from ui.theme import _C


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
            border-radius: 6px;
            padding: 4px;
        }}
    """)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(10, 6, 10, 6)
    lay.setSpacing(2)
    lbl_title = QLabel(label)
    lbl_title.setStyleSheet(
        f"font-size:10px; color:{_C['text_muted']}; background:transparent; border:none;"
    )
    lbl_title.setAlignment(Qt.AlignCenter)
    lbl_val = QLabel("─")
    lbl_val.setStyleSheet(
        f"font-size:14px; font-weight:bold; color:{color};"
        "background:transparent; border:none;"
    )
    lbl_val.setAlignment(Qt.AlignCenter)
    lay.addWidget(lbl_title)
    lay.addWidget(lbl_val)
    return frame, lbl_val
