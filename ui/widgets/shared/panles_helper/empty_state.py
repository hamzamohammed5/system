"""
ui/widgets/shared/panles_helper/empty_state.py
"""
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from ui.app_settings import _C, fs
from .make_btn import _make_btn
from .colors_and_base import _card_colors, _base


class EmptyState(QFrame):
    action_clicked = pyqtSignal()

    def __init__(self, icon: str = "📋",
                 title: str = "لا توجد بيانات",
                 subtitle: str = "",
                 action_text: str = "",
                 style: str = "dashed",
                 color: str = "#10b981",
                 min_height: int = 80,
                 parent=None):
        super().__init__(parent)
        self._build(icon, title, subtitle, action_text, style, color, min_height)

    def _build(self, icon, title, subtitle, action_text, style, color, min_h):
        _bg, _border = _card_colors(color)
        border_style = {"dashed": "dashed", "solid": "solid", "plain": "none"}.get(style, "dashed")

        self.setStyleSheet(f"""
            QFrame {{
                background: {_bg};
                border: 2px {border_style} {_border};
                border-radius: 10px;
            }}
        """)
        self.setMinimumHeight(min_h)

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(6)
        lay.setContentsMargins(20, 16, 20, 16)

        base = _base()

        if icon:
            lbl_icon = QLabel(icon)
            lbl_icon.setAlignment(Qt.AlignCenter)
            lbl_icon.setStyleSheet(
                f"background:transparent; border:none; font-size:{fs(base,+8)}pt;"
            )
            lay.addWidget(lbl_icon)

        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet(
            f"color:{color}; font-weight:700; font-size:{fs(base,+1)}pt;"
            "background:transparent; border:none;"
        )
        lay.addWidget(lbl_title)

        if subtitle:
            lbl_sub = QLabel(subtitle)
            lbl_sub.setAlignment(Qt.AlignCenter)
            lbl_sub.setStyleSheet(
                f"color:{_C['text_muted']}; font-size:{fs(base,-1)}pt;"
                "background:transparent; border:none;"
            )
            lay.addWidget(lbl_sub)

        if action_text:
            btn = _make_btn(action_text, "success")
            btn.setFixedWidth(140)
            btn.clicked.connect(self.action_clicked.emit)
            lay.addWidget(btn, alignment=Qt.AlignCenter)