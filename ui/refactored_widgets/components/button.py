"""
ui/widgets/shared/components/button.py
========================================
make_btn — المصنع الموحد لإنشاء أزرار التطبيق.
"""
from PyQt5.QtWidgets import QPushButton, QSizePolicy
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QFont, QFontMetrics

from ui.app_settings import _C, fs
from ui.widgets.shared.core.settings import get_base


# ── تعريف الأنماط ────────────────────────────────────────────────────────
# كل نمط: (bg, fg, border, hover_bg, hover_fg_or_None, hover_border)
_STYLE_MAP = {
    "primary": (
        "_C['accent_light']", "_C['accent_text']", "_C['accent_mid']",
        "_C['accent_mid']",   "_C['accent_text']", "_C['accent']",
    ),
    "success": ("#ecfdf5", "#065f46", "#6ee7b7", "#d1fae5", None, "#34d399"),
    "danger":  ("#fef2f2", "#dc2626", "#fca5a5", "#fee2e2", None, "#f87171"),
    "ghost":   (
        "transparent",       "_C['text_sec']",  "_C['border_med']",
        "_C['accent_light']","_C['accent_text']","_C['accent_mid']",
    ),
    "normal":  (
        "_C['bg_surface_2']","_C['text_sec']",  "_C['border']",
        "_C['bg_hover']",    None,              "_C['border_med']",
    ),
}


def _resolve(val: str) -> str:
    if val is None:
        return "transparent"
    if val.startswith("_C["):
        key = val[4:-2]
        return _C.get(key, val)
    return val


def _build_style(key: str, font_size: int, btn_h: int) -> str:
    bg, fg, border, h_bg, h_fg_raw, h_bdr = _STYLE_MAP.get(key, _STYLE_MAP["normal"])
    bg     = _resolve(bg)
    fg     = _resolve(fg)
    border = _resolve(border)
    h_bg   = _resolve(h_bg)
    h_fg   = _resolve(h_fg_raw) if h_fg_raw else fg
    h_bdr  = _resolve(h_bdr)

    bold = "font-weight:700;" if key in ("primary", "success") else ""

    return f"""
        QPushButton {{
            background:{bg}; color:{fg};
            border:1.5px solid {border};
            font-size:{font_size}pt; border-radius:6px;
            padding:0 14px; min-height:{btn_h}px;
            {bold}
        }}
        QPushButton:hover {{
            background:{h_bg}; color:{h_fg}; border-color:{h_bdr};
        }}
        QPushButton:disabled {{
            background:{_C.get('bg_surface_2','#f5f5f5')};
            color:{_C.get('text_disabled','#bdbdbd')};
            border-color:{_C.get('border','#e0e0e0')};
        }}
    """


def calc_btn_width(text: str, font_size: int, padding: int = 32) -> int:
    f = QFont()
    f.setPointSize(font_size)
    return QFontMetrics(f).horizontalAdvance(text) + padding


def make_btn(text: str, style: str = "normal",
             fixed_size: bool = True) -> QPushButton:
    """
    ينشئ QPushButton بالنمط المحدد.

    style: "primary" | "success" | "danger" | "ghost" | "normal"
    fixed_size: True = عرض ثابت، False = عرض أدنى قابل للتمدد
    """
    btn       = QPushButton(text)
    base      = get_base()
    btn_h     = base * 2 + 8
    font_size = fs(base, 0)

    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet(_build_style(style, font_size, btn_h))
    btn.setFixedHeight(btn_h)

    w = calc_btn_width(text, font_size)
    if fixed_size:
        btn.setFixedWidth(w)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    else:
        btn.setMinimumWidth(w)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    return btn


# Alias للتوافق مع الكود القديم
_make_btn = make_btn
_calc_btn_width = calc_btn_width