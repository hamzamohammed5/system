"""
ui/widgets/components/button.py
========================================
make_btn — المصنع الموحد لإنشاء أزرار التطبيق.

التغييرات:
  - [i18n/themes] make_btn يحفظ style على الزر كـ Qt property ("_btn_style").
    هذا يسمح لـ refresh_visible_buttons() بإعادة تطبيق الـ stylesheet
    على الأزرار الظاهرة بعد تغيير الثيم، بدون الحاجة لمعرفة الـ style
    الأصلي لكل زر.
  - [i18n/themes] إضافة refresh_visible_buttons(root_widget) لإعادة رسم
    كل الأزرار في الـ widget tree بعد تغيير الثيم.
  - [تحسين 37 محفوظ] _styles() dict ثابت بـ hardcoded hex أُزيل.
  - [تحسين 43 محفوظ] _stylesheet_cache يحفظ الـ stylesheet لكل (style, font_size).
  - [Refactor V3] إصلاح imports: ui.app_settings → ui.theme + ui.font
"""
from PyQt5.QtWidgets import QPushButton, QSizePolicy
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QFont, QFontMetrics

from ui.font  import fs, get_font_size
from ui.theme import _C
from ui.constants import BTN_HEIGHT_PAD, BTN_PAD_H, BTN_BORDER_RADIUS, BTN_TEXT_PAD

# cache: (style_name, font_size) → stylesheet string
_stylesheet_cache: dict[tuple[str, int], str] = {}


def _styles() -> dict[str, dict]:
    """
    يبني dict أنماط الأزرار من _C.
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
    all_styles = _styles()
    s    = all_styles.get(style, all_styles["normal"])
    h    = base * 2 + BTN_HEIGHT_PAD
    fsz  = fs(base, 0)
    bold = "font-weight:700;" if s["bold"] else ""

    return f"""
        QPushButton {{
            background:{s['bg']}; color:{s['fg']};
            border:1.5px solid {s['border']};
            font-size:{fsz}pt; border-radius:{BTN_BORDER_RADIUS}px;
            padding:0 {BTN_PAD_H}px; min-height:{h}px;
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
    key = (style, base)
    if key not in _stylesheet_cache:
        _stylesheet_cache[key] = _build_stylesheet(style, base)
    return _stylesheet_cache[key]


def invalidate_stylesheet_cache():
    """
    يمسح الـ cache عند تغيير حجم الخط أو الثيم.
    استدعه من apply_font() في ui/font.py.
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
    h    = base * 2 + BTN_HEIGHT_PAD
    fsz  = fs(base, 0)

    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet(_get_stylesheet(style, base))
    btn.setFixedHeight(h)

    btn.setProperty("_btn_style", style)

    f = QFont()
    f.setPointSize(fsz)
    w = QFontMetrics(f).horizontalAdvance(text) + BTN_TEXT_PAD
    if fixed_size:
        btn.setFixedWidth(w)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    else:
        btn.setMinimumWidth(w)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    return btn


def refresh_visible_buttons(root_widget) -> int:
    """
    يُعيد تطبيق stylesheet على كل QPushButton في الـ widget tree.
    يُستدعى بعد تغيير الثيم.
    """
    invalidate_stylesheet_cache()
    base = get_font_size()
    count = 0

    try:
        for btn in root_widget.findChildren(QPushButton):
            style = btn.property("_btn_style")
            if style:
                try:
                    btn.setStyleSheet(_get_stylesheet(style, base))
                    h = base * 2 + BTN_HEIGHT_PAD
                    if btn.minimumHeight() > 0:
                        btn.setFixedHeight(h)
                    count += 1
                except RuntimeError:
                    pass
    except RuntimeError:
        pass

    return count


def calc_btn_width(text: str, font_size: int, padding: int = BTN_TEXT_PAD) -> int:
    f = QFont()
    f.setPointSize(font_size)
    return QFontMetrics(f).horizontalAdvance(text) + padding