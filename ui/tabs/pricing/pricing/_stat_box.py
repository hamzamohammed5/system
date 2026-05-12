"""
ui/tabs/pricing/pricing/_stat_box.py
=====================================
دالة مساعدة لإنشاء بطاقة إحصائية في تبويب التسعير.
"""

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt


def stat_box(label: str, color: str = "#1565c0") -> tuple:
    """يرجع (QFrame, QLabel_value) — بطاقة إحصائية."""
    frame = QFrame()
    frame.setStyleSheet("""
        QFrame {
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 4px;
        }
    """)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(10, 6, 10, 6)
    lay.setSpacing(2)
    lbl_title = QLabel(label)
    lbl_title.setStyleSheet(
        "font-size:10px; color:#888; background:transparent; border:none;"
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