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
from PyQt5.QtCore    import Qt, QSize, QByteArray
from PyQt5.QtGui     import QFont, QFontMetrics, QIcon
from PyQt5.QtSvg     import QSvgRenderer
from PyQt5.QtGui     import QPixmap, QPainter

from ui.font  import fs, get_font_size
from ui.theme import _C
from ui.constants import BTN_HEIGHT_PAD, BTN_PAD_H, BTN_BORDER_RADIUS, BTN_TEXT_PAD, BTN_BORDER_W

# cache: (style_name, font_size) → stylesheet string
_stylesheet_cache: dict[tuple[str, int], str] = {}

# cache: (svg_source, size, color) → QIcon
_icon_cache: dict[tuple[str, int, str], QIcon] = {}


# [أيقونات SVG] رموز مرسومة بالكود بدل الاعتماد على دعم الفونت لرموز
# يونيكود زي ↺ (اللي بتظهر متكسرة في بعض الفونتات/الأنظمة).
# كل قيمة عبارة عن SVG path بسيط بمقاس viewBox="0 0 24 24"، واللون
# بيتحقن وقت التوليد عشان يتماشى مع الثيم الحالي.
ICON_PATHS: dict[str, str] = {
    "reset": (
        "M17.65 6.35A7.95 7.95 0 0 0 12 4a8 8 0 1 0 7.75 10h-2.08"
        "A6 6 0 1 1 12 6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35Z"
    ),
}


def _make_svg_icon(icon_key: str, color: str, size: int = 18) -> QIcon:
    """
    يبني QIcon من path مرسوم بالكود (ICON_PATHS)، بلون ثابت
    مش معتمد على الفونت — بيحل مشكلة الرموز اليونيكودية المتقطعة.
    """
    cache_key = (icon_key, size, color)
    if cache_key in _icon_cache:
        return _icon_cache[cache_key]

    path_d = ICON_PATHS.get(icon_key)
    if not path_d:
        return QIcon()

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
        <path fill="{color}" d="{path_d}"/>
    </svg>'''

    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    icon = QIcon(pixmap)
    _icon_cache[cache_key] = icon
    return icon


def invalidate_icon_cache():
    """يمسح الـ icon cache عند تغيير الثيم (الألوان بتتغير)."""
    _icon_cache.clear()


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
            border:{BTN_BORDER_W}px solid {s['border']};
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


def make_btn(text: str = "", style: str = "normal",
             fixed_size: bool = True, icon: str = None) -> QPushButton:
    """
    ينشئ QPushButton بالنمط المحدد.
    style: "primary" | "success" | "danger" | "ghost" | "normal"
    fixed_size: True = عرض ثابت، False = عرض أدنى قابل للتمدد
    icon: مفتاح من ICON_PATHS (زي "reset") — لو موجود وتم بدون text،
          الزرار بيتحول لأيقونة فقط بشكل مربع (عرض = ارتفاع)، مرسومة
          بالكود بدل الاعتماد على رمز يونيكود من الفونت (مش دايمًا
          مدعوم بشكل كامل في كل الفونتات/الأنظمة).
    """
    base = get_font_size()
    h    = base * 2 + BTN_HEIGHT_PAD
    fsz  = fs(base, 0)

    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet(_get_stylesheet(style, base))
    btn.setFixedHeight(h)

    btn.setProperty("_btn_style", style)

    if icon and not text:
        # [أيقونة فقط] زرار مربع — العرض = الارتفاع، والأيقونة بلون
        # النص المحدد في نفس الـ style عشان تتماشى مع الثيم/الـ hover.
        btn.setProperty("_btn_icon", icon)
        all_styles = _styles()
        s = all_styles.get(style, all_styles["normal"])
        icon_size = max(14, h - BTN_PAD_H)
        btn.setIcon(_make_svg_icon(icon, s["fg"], size=icon_size))
        btn.setIconSize(QSize(icon_size, icon_size))
        btn.setFixedWidth(h)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        return btn

    # [FIX] استخدام فونت الزرار الفعلي (اللي اتطبق من الـ stylesheet)
    # بدل QFont() افتراضي — عشان أي نص عادي بيتقاس صح.
    f = btn.font()
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
    invalidate_icon_cache()  # الألوان بتتغير مع الثيم، لازم نعيد رسم الأيقونات
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

                    icon_key = btn.property("_btn_icon")
                    if icon_key:
                        all_styles = _styles()
                        s = all_styles.get(style, all_styles["normal"])
                        icon_size = max(14, h - BTN_PAD_H)
                        btn.setIcon(_make_svg_icon(icon_key, s["fg"], size=icon_size))
                        btn.setIconSize(QSize(icon_size, icon_size))
                        btn.setFixedWidth(h)

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