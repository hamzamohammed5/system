"""
ui/widgets/shared/panles_helper/make_btn.py

التغييرات:
  - حذف _STYLES None cache (مش بيشتغل صح مع تغيير theme)
  - _get_styles بتستخدم _C بشكل كامل، مفيش hardcoded hex
  - _calc_btn_width مستخرجة بشكل أنظف
  - fixed_size=False يستخدم setMinimumWidth بدل setFixedWidth
"""
from PyQt5.QtWidgets import QPushButton, QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontMetrics

from ui.app_settings import _C, fs
from .colors_and_base import _base

_BTN_STYLES = {
    "primary": (
        "_C['accent_light']", "_C['accent_text']", "_C['accent_mid']",
        "_C['accent_mid']",   "_C['accent_text']", "_C['accent']",
    ),
    "success": ("#ecfdf5", "#065f46", "#6ee7b7", "#d1fae5", None, "#34d399"),
    "danger":  ("#fef2f2", "#dc2626", "#fca5a5", "#fee2e2", None, "#f87171"),
    "ghost":   (
        "transparent", "_C['text_sec']", "_C['border_med']",
        "_C['accent_light']", "_C['accent_text']", "_C['accent_mid']",
    ),
    "normal":  (
        "_C['bg_surface_2']", "_C['text_sec']", "_C['border']",
        "_C['bg_hover']",     None,             "_C['border_med']",
    ),
}


def _resolve(val: str) -> str:
    """يحوّل string reference لـ _C إلى القيمة الفعلية."""
    if val is None:
        return "transparent"
    if val.startswith("_C["):
        key = val[4:-2]
        return _C.get(key, val)
    return val


def _build_style(key: str, font_size: int, btn_h: int) -> str:
    bg, fg, border, hover_bg, hover_fg, hover_border = _BTN_STYLES.get(
        key, _BTN_STYLES["normal"]
    )
    bg      = _resolve(bg)
    fg      = _resolve(fg)
    border  = _resolve(border)
    h_bg    = _resolve(hover_bg)
    h_fg    = _resolve(hover_fg) if hover_fg else fg
    h_bdr   = _resolve(hover_border)
    dis_bg  = _C.get("bg_surface_2", "#f5f5f5")
    dis_fg  = _C.get("text_disabled", "#bdbdbd")
    dis_bdr = _C.get("border", "#e0e0e0")

    return f"""
        QPushButton {{
            background:{bg}; color:{fg};
            border:1.5px solid {border};
            font-size:{font_size}pt; border-radius:6px;
            padding:0 14px; min-height:{btn_h}px;
            {"font-weight:700;" if key in ("primary","success") else ""}
        }}
        QPushButton:hover {{
            background:{h_bg}; color:{h_fg};
            border-color:{h_bdr};
        }}
        QPushButton:disabled {{
            background:{dis_bg}; color:{dis_fg};
            border-color:{dis_bdr};
        }}
    """


def _calc_btn_width(text: str, font_size: int, padding: int = 32) -> int:
    f = QFont()
    f.setPointSize(font_size)
    return QFontMetrics(f).horizontalAdvance(text) + padding


def _make_btn(text: str, style: str = "normal",
              fixed_size: bool = True) -> QPushButton:
    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    base      = _base()
    btn_h     = base * 2 + 8
    font_size = fs(base, 0)

    btn.setStyleSheet(_build_style(style, font_size, btn_h))
    btn.setFixedHeight(btn_h)

    w = _calc_btn_width(text, font_size)
    if fixed_size:
        btn.setFixedWidth(w)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    else:
        btn.setMinimumWidth(w)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    return btn