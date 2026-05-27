"""
ui/widgets/components/button.py
========================================
make_btn — المصنع الموحد لإنشاء أزرار التطبيق.

التغييرات:
  - _STYLES dict ثابت بـ hardcoded hex أُزيل.
  - _styles() دالة جديدة تبني الأنماط من _C مباشرة.
  - _stylesheet_cache يحفظ الـ stylesheet لكل (style, font_size)
    بدل إعادة بنائها في كل استدعاء.
  - _r() أُزيلت — لم تعد ضرورية بعد ما _styles() ترجع قيم مباشرة.
"""
from PyQt5.QtWidgets import QPushButton, QSizePolicy
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QFont, QFontMetrics

from ui.app_settings import _C, fs
from ui.app_settings import get_font_size

# cache: (style_name, font_size) → stylesheet string
_stylesheet_cache: dict[tuple[str, int], str] = {}


def _styles() -> dict[str, dict]:
    """
    يبني dict أنماط الأزرار من _C.

    التغيير: بدل _STYLES = { "success": dict(bg="#ecfdf5", ...) }
    اللي كان hardcoded، الدالة دي بتقرأ من _C مباشرة.
    يُستدعى في كل make_btn — الـ cache يمنع أي overhead.
    """
    return {
        "primary": dict(
            bg=_C["accent_light"],  fg=_C["accent_text"],  border=_C["accent_mid"],
            h_bg=_C["accent_mid"],  h_fg=_C["accent_text"], h_bdr=_C["accent"],
            bold=True,
        ),
        "success": dict(
            bg=_C["success_bg"],    fg=_C["success"],        border=_C["success_border"],
            h_bg=_C["success_bg"],  h_fg=_C["success"],      h_bdr=_C["success"],
            bold=True,
        ),
        "danger": dict(
            bg=_C["danger_bg"],     fg=_C["danger"],         border=_C["danger_border"],
            h_bg=_C["danger_bg"],   h_fg=_C["danger"],       h_bdr=_C["danger"],
            bold=False,
        ),
        "ghost": dict(
            bg="transparent",        fg=_C["text_sec"],      border=_C["border_med"],
            h_bg=_C["accent_light"], h_fg=_C["accent_text"], h_bdr=_C["accent_mid"],
            bold=False,
        ),
        "normal": dict(
            bg=_C["bg_surface_2"],  fg=_C["text_sec"],       border=_C["border"],
            h_bg=_C["bg_hover"],    h_fg=_C["text_primary"], h_bdr=_C["border_med"],
            bold=False,
        ),
    }


def _build_stylesheet(style: str, base: int) -> str:
    """
    يبني الـ stylesheet لنمط وحجم خط معين.
    النتيجة تُحفظ في _stylesheet_cache.
    """
    all_styles = _styles()
    s    = all_styles.get(style, all_styles["normal"])
    h    = base * 2 + 8
    fsz  = fs(base, 0)
    bold = "font-weight:700;" if s["bold"] else ""

    return f"""
        QPushButton {{
            background:{s['bg']}; color:{s['fg']};
            border:1.5px solid {s['border']};
            font-size:{fsz}pt; border-radius:6px;
            padding:0 14px; min-height:{h}px;
            {bold}
        }}
        QPushButton:hover {{
            background:{s['h_bg']}; color:{s['h_fg'] or s['fg']};
            border-color:{s['h_bdr']};
        }}
        QPushButton:disabled {{
            background:{_C['bg_surface_2']};
            color:{_C['text_disabled']};
            border-color:{_C['border']};
        }}
    """


def _get_stylesheet(style: str, base: int) -> str:
    """يرجع الـ stylesheet من الـ cache أو يبنيها إذا لم تكن موجودة."""
    key = (style, base)
    if key not in _stylesheet_cache:
        _stylesheet_cache[key] = _build_stylesheet(style, base)
    return _stylesheet_cache[key]


def invalidate_stylesheet_cache():
    """
    يمسح الـ cache عند تغيير حجم الخط أو الثيم.
    استدعه من apply_font() في app_settings.
    """
    _stylesheet_cache.clear()


def make_btn(text: str, style: str = "normal",
             fixed_size: bool = True) -> QPushButton:
    """
    ينشئ QPushButton بالنمط المحدد.
    style: "primary" | "success" | "danger" | "ghost" | "normal"
    fixed_size: True = عرض ثابت، False = عرض أدنى قابل للتمدد
    """
    base = get_font_size()
    h    = base * 2 + 8
    fsz  = fs(base, 0)

    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet(_get_stylesheet(style, base))
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