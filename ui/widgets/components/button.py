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
    # [إضافة] سهم expand/collapse — نفس سبب "reset": الرموز اليونيكودية
    # ▶/▼ (U+25B6 / U+25BC) مش مضمونة الدعم في كل الفونتات، وبتظهر
    # كمربع/حرف غريب (زي "I") في فونتات معينة بدل السهم الفعلي.
    # مثلث بسيط للسهم المتجه ناحية اليمين (الحالة المقفولة).
    "chevron_right": "M9 5.5 15.5 12 9 18.5V5.5Z",
    # نفس المثلث لكن متجه لتحت (الحالة المفتوحة) — دوران 90 درجة.
    "chevron_down": "M5.5 9 12 15.5 18.5 9H5.5Z",
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


def _build_square_stylesheet(style: str) -> str:
    """
    [Fix] نسخة مخصصة لزرارات الأيقونة/compact المربعة (icon-only أو
    compact=True). المشكلة الأصلية: _build_stylesheet العادية بتحقن
    `min-height:{h}px` جوه QSS، وقواعد QSS بتتطبّق بعد setFixedSize()
    البرمجي — يعني حتى لو الكود عمل setFixedSize(side, side) بحجم
    صغير مضبوط، الـ min-height الكبيرة (مبنية على ارتفاع زرار نص
    عادي base*2+BTN_HEIGHT_PAD) كانت بتفوز وتفرض ارتفاع أكبر، فالزرار
    كان بيبان مستطيل طويل بدل مربع صغير حوالين الأيقونة. نفس الشيء
    بالنسبة لـ padding الأفقي الكبير (BTN_PAD_H) اللي مصمم لمسافة
    حوالين نص، مش حوالين أيقونة وحيدة صغيرة.
    الحل: stylesheet بدون min-height وبدون padding خالص — الحجم
    بيتحدد بالكامل من setFixedSize() في الكود، وQSS بس بيدي اللون/
    الحدود/الراديوس.
    """
    all_styles = _styles()
    s    = all_styles.get(style, all_styles["normal"])

    return f"""
        QPushButton {{
            background:{s['bg']}; color:{s['fg']};
            border:{BTN_BORDER_W}px solid {s['border']};
            border-radius:{BTN_BORDER_RADIUS}px;
            padding:0;
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


def _get_square_stylesheet(style: str) -> str:
    key = ("__square__", style)
    if key not in _stylesheet_cache:
        _stylesheet_cache[key] = _build_square_stylesheet(style)
    return _stylesheet_cache[key]


def invalidate_stylesheet_cache():
    """
    يمسح الـ cache عند تغيير حجم الخط أو الثيم.
    استدعه من apply_font() في ui/font.py.
    """
    _stylesheet_cache.clear()


# [FIX عام] الحساب القديم w = horizontalAdvance(text) + BTN_TEXT_PAD كان
# بيتجاهل حدود الزرار (border) اللي متعرفة في الـ stylesheet نفسه
# (`border:{BTN_BORDER_W}px solid ...` على كل الجهات، يعني 2×BTN_BORDER_W
# إجمالي) — فكان ممكن النص يتقص فعليًا في نصوص عربية طويلة أو نصوص
# فيها حروف بمسافة فعلية أكبر شوية من horizontalAdvance (كباس/تشكيل).
# الحل: نحسب من نفس القيم اللي الـ stylesheet شايفها فعلاً
# (BTN_PAD_H من كل جهة + BTN_BORDER_W من كل جهة)، ونضيف هامش أمان بسيط
# (safety_pad) بدل الاعتماد على BTN_TEXT_PAD وحده كرقم تقريبي منفصل.
# دالة واحدة مركزية هنا يعني أي تعديل مستقبلي (خط أعرض، حدود أتخن)
# بينعكس تلقائيًا على كل زرار في المشروع من غير ما حد يلمس نداءات make_btn.
def _calc_btn_width_for_text(text: str, font: QFont, extra_pad: int = 0) -> int:
    """
    يحسب العرض الأدنى اللازم لزرار نصه `text` بالفونت `font`، بحيث
    النص يبان كامل من غير قص — بياخد في الاعتبار padding الزرار
    الأفقي (من الجهتين) وحدود الزرار (من الجهتين) زي ما هي متعرّفة
    فعليًا في الـ stylesheet المُولّد من _build_stylesheet، بدل رقم
    تقريبي منفصل.
    """
    text_w = QFontMetrics(font).horizontalAdvance(text)
    chrome = 2 * BTN_PAD_H + 2 * BTN_BORDER_W
    # هامش أمان صغير إضافي (extra_pad) — بيغطي فروق قياس دقيقة بين
    # منصات/فونتات مختلفة (النصوص العربية أحيانًا بتاخد مسافة فعلية
    # أكبر شوية من القيمة اللي horizontalAdvance بترجعها).
    # [Fix] int() صريح — لو أي ثابت من دول (BTN_PAD_H/BTN_BORDER_W/
    # extra_pad) متعرّف كـ float في constants.py، الجمع كله بيتحول
    # float ضمنيًا، وQPushButton.setFixedWidth() بترفضه (بتاخد int بس).
    return int(text_w + chrome + extra_pad)


def make_btn(text: str = "", style: str = "normal",
             fixed_size: bool = True, icon: str = None,
             compact: bool = False) -> QPushButton:
    """
    ينشئ QPushButton بالنمط المحدد.
    style: "primary" | "success" | "danger" | "ghost" | "normal"
    fixed_size: True = عرض ثابت، False = عرض أدنى قابل للتمدد
    icon: مفتاح من ICON_PATHS (زي "reset") — لو موجود وتم بدون text،
          الزرار بيتحول لأيقونة فقط بشكل مربع (عرض = ارتفاع)، مرسومة
          بالكود بدل الاعتماد على رمز يونيكود من الفونت (مش دايمًا
          مدعوم بشكل كامل في كل الفونتات/الأنظمة).
    compact: [إضافة] True = زرار مربع يتحسب حجمه (عرض وارتفاع مع بعض)
          تلقائيًا بالكامل من القياس الفعلي للرمز نفسه (عبر
          QFontMetrics.boundingRect، أدق من horizontalAdvance للرموز
          اللي مش نص عادي زي ▼/▶) + هامش صغير ثابت — بدل ما يرث ارتفاع
          زرار النص العادي (base*2 + BTN_HEIGHT_PAD) اللي مصمم لصف نص
          كامل مش لرمز واحد. مفيد لأي زرار expand/collapse/toggle في
          أي جدول بالمشروع، مش بس جدول الخامات.
          لو عايز رمز بلون مخصص عن طريق SVG (زي icon=) استخدم icon
          بدل compact؛ compact هنا للنص القصير المباشر (يونيكود).
    """
    base = get_font_size()
    # [Fix] int() صريح — لو BTN_HEIGHT_PAD متعرّفة كـ float في
    # constants.py، h كانت بتتحول float ضمنيًا، وأي setFixedHeight(h)/
    # setFixedSize(h, h) بعدها كانت بترمي TypeError (setFixedSize
    # بتاخد int بس مش float). حماية واحدة هنا كفاية لكل استخدام تابع.
    h    = int(base * 2 + BTN_HEIGHT_PAD)
    fsz  = fs(base, 0)

    if compact and text and not icon:
        # [compact] حجم الزرار بالكامل (عرض + ارتفاع) من قياس الرمز
        # الفعلي، مش من ثوابت زرار النص العادي. boundingRect بيدّي
        # صندوق الرمز الحقيقي (بما فيه أي زيادة فوق/تحت خط الأساس
        # لرموز زي الأسهم اليونيكودية) بعكس horizontalAdvance اللي
        # بيدّي بس "المسافة اللي الكيرسور هيتحرك بيها" وممكن تكون
        # أضيق من الشكل الفعلي المرسوم.
        f = QFont()
        f.setPointSize(fsz)
        rect = QFontMetrics(f).boundingRect(text)
        # هامش صغير متساوي حوالين الرمز (مش padding زرار النص الكامل)
        margin = max(BTN_BORDER_W * 2, 6)
        side = int(max(rect.width(), rect.height()) + margin * 2)
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        # [Fix] stylesheet مربع مخصص (بدون min-height) بدل _get_stylesheet
        # العادية — min-height:{h}px كانت بتفرض ارتفاع زرار نص عادي
        # حتى بعد setFixedSize(side, side)، فالزرار كان يبان مستطيل
        # طويل بدل مربع صغير حوالين الرمز.
        btn.setStyleSheet(_get_square_stylesheet(style))
        btn.setProperty("_btn_style", style)
        btn.setProperty("_btn_square", True)
        btn.setFixedSize(side, side)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        return btn

    if icon and not text:
        # [أيقونة فقط] زرار مربع.
        # [Fix] بُني من الصفر بـ stylesheet مربع مخصص (بدون min-height)
        # بدل ما ياخد _get_stylesheet العادية (فيها min-height:{h}px
        # مصمم لزرار نص كامل) ثم نحاول "نصلّحها" بـ setFixedSize بعد
        # كده — القاعدة دي (min-height في QSS) كانت بتفوز دايمًا على
        # setFixedWidth/setFixedHeight البرمجي، فالزرار كان يبان
        # مستطيل طويل بدل مربع صغير حوالين السهم، بغض النظر عن
        # compact=True/False.
        btn = QPushButton()
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(_get_square_stylesheet(style))
        btn.setProperty("_btn_style", style)
        btn.setProperty("_btn_square", True)
        btn.setProperty("_btn_icon", icon)
        all_styles = _styles()
        s = all_styles.get(style, all_styles["normal"])
        if compact:
            # [Fix] margin كانت max(BTN_BORDER_W, 4) — بتفرض حد أدنى
            # 4px هامش من كل جهة حتى لو BTN_BORDER_W أصغر، يعني الزرار
            # كان دايمًا أكبر من الأيقونة بمقدار ثابت زيادة عن اللازم.
            # المطلوب: الزرار يبقى بالظبط بحجم الأيقونة + سمك حدود
            # الزرار نفسها بس (من غير أي padding إضافي)، عشان الارتفاع
            # يكون بالظبط "كافي لعرض الأيقونة كاملة" مش أكبر من كده.
            margin = BTN_BORDER_W
            icon_size = max(12, int(fsz * 1.4))
            side = int(icon_size + margin * 2)
            btn.setIcon(_make_svg_icon(icon, s["fg"], size=icon_size))
            btn.setIconSize(QSize(icon_size, icon_size))
            btn.setFixedSize(side, side)
        else:
            icon_size = max(14, h - BTN_PAD_H)
            btn.setIcon(_make_svg_icon(icon, s["fg"], size=icon_size))
            btn.setIconSize(QSize(icon_size, icon_size))
            btn.setFixedSize(h, h)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        return btn

    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet(_get_stylesheet(style, base))
    btn.setFixedHeight(h)

    btn.setProperty("_btn_style", style)

    # [FIX] استخدام فونت الزرار الفعلي (اللي اتطبق من الـ stylesheet)
    # بدل QFont() افتراضي — عشان أي نص عادي بيتقاس صح.
    f = btn.font()
    f.setPointSize(fsz)
    w = _calc_btn_width_for_text(text, f, extra_pad=BTN_TEXT_PAD)
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
                    is_square = bool(btn.property("_btn_square"))
                    icon_key  = btn.property("_btn_icon")

                    if is_square:
                        # [Fix] الأزرار المربعة (compact أو icon-only)
                        # لازم تاخد stylesheet بدون min-height. وبدل ما
                        # نحافظ على حجمها الحالي (btn.width()) — اللي
                        # ممكن يكون لسه متضخّم من نسخة قديمة للحساب —
                        # بنعيد حساب الحجم من الصفر بنفس منطق make_btn
                        # الجديد: icon_size أولًا، وside = icon_size +
                        # BTN_BORDER_W*2 (بدون أي padding إضافي)، عشان
                        # الزرار يفضل بالظبط بحجم الأيقونة + سمك الحدود
                        # بس، حتى بعد أي تغيير ثيم.
                        icon_size = max(12, int(fs(base, 0) * 1.4))
                        side = int(icon_size + BTN_BORDER_W * 2)
                        btn.setStyleSheet(_get_square_stylesheet(style))
                        if icon_key:
                            all_styles = _styles()
                            s = all_styles.get(style, all_styles["normal"])
                            btn.setIcon(_make_svg_icon(icon_key, s["fg"], size=icon_size))
                            btn.setIconSize(QSize(icon_size, icon_size))
                        btn.setFixedSize(side, side)
                    else:
                        btn.setStyleSheet(_get_stylesheet(style, base))
                        h = int(base * 2 + BTN_HEIGHT_PAD)
                        if btn.minimumHeight() > 0:
                            btn.setFixedHeight(h)

                        if icon_key:
                            all_styles = _styles()
                            s = all_styles.get(style, all_styles["normal"])
                            icon_size = max(14, h - BTN_PAD_H)
                            btn.setIcon(_make_svg_icon(icon_key, s["fg"], size=icon_size))
                            btn.setIconSize(QSize(icon_size, icon_size))
                            btn.setFixedSize(h, h)

                    count += 1
                except RuntimeError:
                    pass
    except RuntimeError:
        pass

    return count


def calc_btn_width(text: str, font_size: int, padding: int = BTN_TEXT_PAD) -> int:
    """
    [FIX] بتستخدم دلوقتي _calc_btn_width_for_text نفسها اللي بيستخدمها
    make_btn داخليًا — عشان أي كود بره button.py بيحسب عرض زرار يدويًا
    (زي علشان يحجز مساحة قبل ما الزرار يتبني) ياخد نفس الرقم بالظبط
    اللي make_btn هيطلعه فعليًا، بدل رقمين مختلفين لنفس النص.
    """
    f = QFont()
    f.setPointSize(font_size)
    return _calc_btn_width_for_text(text, f, extra_pad=padding)