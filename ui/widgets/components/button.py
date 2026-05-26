"""
ui/widgets/components/button.py
========================================
make_btn — المصنع الموحد لإنشاء أزرار التطبيق.

دمج: panels/_btn.py + components/button.py
"""
from PyQt5.QtWidgets import QPushButton, QSizePolicy
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QFont, QFontMetrics

from ui.app_settings import _C, fs
from ..core.settings import get_base

_STYLES = {
    "primary": dict(
        bg="_C['accent_light']", fg="_C['accent_text']", border="_C['accent_mid']",
        h_bg="_C['accent_mid']", h_fg=None, h_bdr="_C['accent']", bold=True,
    ),
    "success": dict(
        bg="#ecfdf5", fg="#065f46", border="#6ee7b7",
        h_bg="#d1fae5", h_fg=None, h_bdr="#34d399", bold=True,
    ),
    "danger": dict(
        bg="#fef2f2", fg="#dc2626", border="#fca5a5",
        h_bg="#fee2e2", h_fg=None, h_bdr="#f87171", bold=False,
    ),
    "ghost": dict(
        bg="transparent", fg="_C['text_sec']", border="_C['border_med']",
        h_bg="_C['accent_light']", h_fg="_C['accent_text']", h_bdr="_C['accent_mid']", bold=False,
    ),
    "normal": dict(
        bg="_C['bg_surface_2']", fg="_C['text_sec']", border="_C['border']",
        h_bg="_C['bg_hover']", h_fg=None, h_bdr="_C['border_med']", bold=False,
    ),
}


def _r(val: str | None) -> str:
    if not val:
        return "transparent"
    if val.startswith("_C["):
        return _C.get(val[4:-2], val)
    return val


def make_btn(text: str, style: str = "normal",
             fixed_size: bool = True) -> QPushButton:
    """
    ينشئ QPushButton بالنمط المحدد.
    style: "primary" | "success" | "danger" | "ghost" | "normal"
    fixed_size: True = عرض ثابت، False = عرض أدنى قابل للتمدد
    """
    s    = _STYLES.get(style, _STYLES["normal"])
    base = get_base()
    h    = base * 2 + 8
    fsz  = fs(base, 0)

    bg  = _r(s["bg"]);  fg  = _r(s["fg"]);  bdr = _r(s["border"])
    hbg = _r(s["h_bg"]); hfg = _r(s["h_fg"]) or fg; hbdr = _r(s["h_bdr"])
    bold = "font-weight:700;" if s["bold"] else ""

    stylesheet = f"""
        QPushButton {{
            background:{bg}; color:{fg};
            border:1.5px solid {bdr};
            font-size:{fsz}pt; border-radius:6px;
            padding:0 14px; min-height:{h}px;
            {bold}
        }}
        QPushButton:hover {{
            background:{hbg}; color:{hfg}; border-color:{hbdr};
        }}
        QPushButton:disabled {{
            background:{_C.get('bg_surface_2','#f5f5f5')};
            color:{_C.get('text_disabled','#bdbdbd')};
            border-color:{_C.get('border','#e0e0e0')};
        }}
    """
    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet(stylesheet)
    btn.setFixedHeight(h)

    f = QFont()
    f.setPointSize(fsz)
    w = QFontMetrics(f).horizontalAdvance(text) + 32
    if fixed_size:
        btn.setFixedWidth(w)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    else:
        btn.setMinimumWidth(w)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    return btn


def calc_btn_width(text: str, font_size: int, padding: int = 32) -> int:
    f = QFont()
    f.setPointSize(font_size)
    return QFontMetrics(f).horizontalAdvance(text) + padding


# aliases للتوافق مع الكود القديم
_make_btn       = make_btn
_calc_btn_width = calc_btn_width