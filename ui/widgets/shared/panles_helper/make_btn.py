"""
ui/widgets/shared/panles_helper/make_btn.py
"""
from PyQt5.QtWidgets import QPushButton, QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontMetrics

from ui.app_settings import _C, fs
from .colors_and_base import _base


def _make_btn(text: str, style: str = "normal",
              fixed_size: bool = True) -> QPushButton:
    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    base  = _base()
    btn_h = base * 2 + 8
    font_size = fs(base, 0)

    styles = {
        "primary": f"""
            QPushButton {{
                background: {_C['accent_light']}; color: {_C['accent_text']};
                border: 1.5px solid {_C['accent_mid']};
                font-size: {font_size}pt;
                border-radius: 6px;
                padding: 0 14px;
                min-height: {btn_h}px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {_C['accent_mid']}; color: {_C['accent_text']};
                border-color: {_C['accent']};
            }}
            QPushButton:disabled {{
                background: {_C['bg_surface_2']}; color: {_C['text_disabled']};
                border-color: {_C['border']};
            }}
        """,
        "success": f"""
            QPushButton {{
                background: #ecfdf5; color: #065f46;
                border: 1.5px solid #6ee7b7;
                font-size: {font_size}pt;
                border-radius: 6px;
                padding: 0 14px;
                min-height: {btn_h}px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background: #d1fae5; border-color: #34d399; }}
            QPushButton:disabled {{
                background: {_C['bg_surface_2']}; color: {_C['text_disabled']};
                border-color: {_C['border']};
            }}
        """,
        "danger": f"""
            QPushButton {{
                background: #fef2f2; color: #dc2626;
                border: 1.5px solid #fca5a5;
                font-size: {font_size}pt;
                border-radius: 6px;
                padding: 0 14px;
                min-height: {btn_h}px;
            }}
            QPushButton:hover {{ background: #fee2e2; border-color: #f87171; }}
            QPushButton:disabled {{
                background: {_C['bg_surface_2']}; color: {_C['text_disabled']};
                border-color: {_C['border']};
            }}
        """,
        "ghost": f"""
            QPushButton {{
                background: transparent; color: {_C['text_sec']};
                border: 1.5px solid {_C['border_med']};
                font-size: {font_size}pt;
                border-radius: 6px;
                padding: 0 14px;
                min-height: {btn_h}px;
            }}
            QPushButton:hover {{
                background: {_C['accent_light']}; color: {_C['accent_text']};
                border-color: {_C['accent_mid']};
            }}
            QPushButton:disabled {{
                background: {_C['bg_surface_2']}; color: {_C['text_disabled']};
                border-color: {_C['border']};
            }}
        """,
        "normal": f"""
            QPushButton {{
                background: {_C['bg_surface_2']}; color: {_C['text_sec']};
                border: 1px solid {_C['border']};
                font-size: {font_size}pt;
                border-radius: 6px;
                padding: 0 14px;
                min-height: {btn_h}px;
            }}
            QPushButton:hover {{
                background: {_C['bg_hover']}; border-color: {_C['border_med']};
            }}
            QPushButton:disabled {{
                background: {_C['bg_surface_2']}; color: {_C['text_disabled']};
            }}
        """,
    }
    btn.setStyleSheet(styles.get(style, styles["normal"]))

    # ── حجم ثابت ──
    f = QFont()
    f.setPointSize(font_size)
    fm    = QFontMetrics(f)
    txt_w = fm.horizontalAdvance(text)
    w     = txt_w + 32   # padding يمين + شمال

    btn.setFixedHeight(btn_h)
    btn.setFixedWidth(w)
    btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    if not fixed_size:
        btn.setMinimumWidth(w)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    return btn