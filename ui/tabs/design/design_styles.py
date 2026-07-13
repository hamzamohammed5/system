"""
ui/tabs/design/design_styles.py
================================
أنماط CSS ديناميكية لوحدة التصميمات — متناسقة مع app_settings.py
"""

from ui.font import get_font_size, fs
from ui.theme import _C as APP_COLORS
from ui.constants import (
    STYLES_RADIUS_LG, STYLES_RADIUS_SM, STYLES_RADIUS_XS,
    STYLES_BTN_HEIGHT_PAD, STYLES_LABEL_FIELD_LETTER_SPACING,
    STYLES_BADGE_PAD_V, STYLES_BADGE_PAD_H,
    STYLES_BADGE_COUNT_RADIUS, STYLES_BADGE_COUNT_PAD_V, STYLES_BADGE_COUNT_MIN_W,
    STYLES_BTN_PAD_H, STYLES_BTN_PRIMARY_PAD_H,
    STYLES_INPUT_PAD_H, STYLES_COMBO_PAD_H,
    STYLES_COMBO_DROPDOWN_BORDER_W, STYLES_COMBO_DROPDOWN_W,
)


class _Styles:
    """
    كائن يحمل أحجام الخطوط الحالية ويولّد stylesheet strings.
    الألوان مأخوذة من app_settings._C للتناسق الكامل.

    [إصلاح dark-theme] كانت الألوان (BG, BORDER, ACCENT, ...) معرّفة
    كـ class attributes بتتقيم مرة واحدة بس وقت تعريف الكلاس (وقت أول
    import للملف) — يعني بتتجمد على قيمة الثيم اللي كان شغال وقتها
    للأبد. أي theme_manager.set_theme() لاحق في نفس الجلسة كان بيتجاهل
    الألوان دي تمامًا، لأنها مش property بتتقرأ من _C كل مرة. الحل:
    تحويلها لـ @property تقرأ من ui.theme._C الحية في كل استدعاء.
    """

    RADIUS    = f"{STYLES_RADIUS_LG}px"
    RADIUS_SM = f"{STYLES_RADIUS_SM}px"
    RADIUS_XS = f"{STYLES_RADIUS_XS}px"

    @property
    def BG(self):
        from ui.theme import _C
        return _C["bg_input"]

    @property
    def BG_SURFACE(self):
        from ui.theme import _C
        return _C["bg_surface"]

    @property
    def BG_HOVER(self):
        from ui.theme import _C
        return _C["bg_hover"]

    @property
    def BORDER(self):
        from ui.theme import _C
        return _C["border"]

    @property
    def BORDER_MED(self):
        from ui.theme import _C
        return _C["border_med"]

    @property
    def TEXT_PRI(self):
        from ui.theme import _C
        return _C["text_primary"]

    @property
    def TEXT_SEC(self):
        from ui.theme import _C
        return _C["text_sec"]

    @property
    def TEXT_MUT(self):
        from ui.theme import _C
        return _C["text_muted"]

    @property
    def ACCENT(self):
        from ui.theme import _C
        return _C["accent"]

    @property
    def ACCENT_LT(self):
        from ui.theme import _C
        return _C["accent_light"]

    @property
    def ACCENT_BDR(self):
        from ui.theme import _C
        return _C["accent_mid"]

    @property
    def ACCENT_DARK(self):
        from ui.theme import _C
        return _C["accent_hover"]

    @property
    def ACCENT_TEXT(self):
        from ui.theme import _C
        return _C["accent_text"]

    @property
    def BTN_PRIMARY_TEXT(self):
        from ui.theme import _C
        return _C["btn_primary_text"]

    @property
    def SUCCESS(self):
        from ui.theme import _C
        return _C["success"]

    @property
    def SUCCESS_LT(self):
        from ui.theme import _C
        return _C["success_bg"]

    @property
    def SUCCESS_BDR(self):
        from ui.theme import _C
        return _C["success_border"]

    @property
    def SUCCESS_HOVER_BG(self):
        from ui.theme import _C
        return _C["success_hover_bg"]

    @property
    def DANGER(self):
        from ui.theme import _C
        return _C["danger"]

    @property
    def DANGER_LT(self):
        from ui.theme import _C
        return _C["danger_bg"]

    @property
    def DANGER_BDR(self):
        from ui.theme import _C
        return _C["danger_border"]

    @property
    def DANGER_HOVER_BG(self):
        from ui.theme import _C
        return _C["danger_hover_bg"]

    @property
    def WARNING(self):
        from ui.theme import _C
        return _C["warning"]

    def __init__(self, base: int):
        self.base   = base
        self.tiny   = fs(base, -2)
        self.small  = fs(base, -1)
        self.normal = fs(base,  0)
        self.large  = fs(base, +1)
        self.xlarge = fs(base, +2)

    def _h(self, override=None) -> int:
        """ارتفاع قياسي للعناصر."""
        return override or (self.normal * 2 + STYLES_BTN_HEIGHT_PAD)

    # ══════════════════════════════════════════════════════
    # Labels
    # ══════════════════════════════════════════════════════

    def label_header(self) -> str:
        return (
            f"font-size:{self.xlarge}px; font-weight:700; color:{self.TEXT_PRI};"
            "background:transparent; border:none;"
        )

    def label_section(self) -> str:
        return (
            f"font-size:{self.large}px; font-weight:600; color:{self.TEXT_SEC};"
            "background:transparent; border:none;"
        )

    def label_field(self) -> str:
        return (
            f"font-size:{self.small}px; font-weight:600; color:{self.TEXT_MUT};"
            f"background:transparent; border:none; letter-spacing:{STYLES_LABEL_FIELD_LETTER_SPACING}px;"
        )

    def label_secondary(self) -> str:
        return (
            f"font-size:{self.normal}px; color:{self.TEXT_SEC};"
            "background:transparent; border:none;"
        )

    def label_muted(self) -> str:
        return (
            f"font-size:{self.small}px; color:{self.TEXT_MUT};"
            "background:transparent; border:none;"
        )

    # ══════════════════════════════════════════════════════
    # Badges
    # ══════════════════════════════════════════════════════

    def badge_accent(self) -> str:
        return (
            f"font-size:{self.small}px; font-weight:600; color:{self.ACCENT_TEXT};"
            f"background:{self.ACCENT_LT}; border:1px solid {self.ACCENT_BDR};"
            f"border-radius:{self.RADIUS_SM}; padding:{STYLES_BADGE_PAD_V}px {STYLES_BADGE_PAD_H}px;"
        )

    def badge_count(self) -> str:
        return (
            f"font-size:{self.small}px; font-weight:700; color:{self.ACCENT_TEXT};"
            f"background:{self.ACCENT_LT}; border:1px solid {self.ACCENT_BDR};"
            f"border-radius:{STYLES_BADGE_COUNT_RADIUS}px; padding:{STYLES_BADGE_COUNT_PAD_V}px {STYLES_BADGE_PAD_H}px; min-width:{STYLES_BADGE_COUNT_MIN_W}px;"
        )

    # ══════════════════════════════════════════════════════
    # Buttons
    # ══════════════════════════════════════════════════════

    def btn(self, bg, fg, bdr, hover_bg, height: int = None, radius: str = None) -> str:
        h = height or self._h()
        r = radius or self.RADIUS
        return (
            f"QPushButton{{"
            f"  background:{bg}; color:{fg};"
            f"  border:1px solid {bdr}; border-radius:{r};"
            f"  padding:0 {STYLES_BTN_PAD_H}px; font-size:{self.normal}px; font-weight:500;"
            f"  min-height:{h}px;"
            f"}}"
            f"QPushButton:hover{{background:{hover_bg}; border-color:{self.BORDER_MED};}}"
            f"QPushButton:pressed{{opacity:0.9;}}"
        )

    def btn_primary(self, height: int = None) -> str:
        h = height or self._h()
        return (
            f"QPushButton{{"
            f"  background:{self.ACCENT}; color:{self.BTN_PRIMARY_TEXT};"
            f"  border:none; border-radius:{self.RADIUS};"
            f"  padding:0 {STYLES_BTN_PRIMARY_PAD_H}px; font-size:{self.normal}px; font-weight:600;"
            f"  min-height:{h}px;"
            f"}}"
            f"QPushButton:hover{{background:{self.ACCENT_DARK};}}"
            f"QPushButton:pressed{{background:{self.ACCENT_DARK}; opacity:0.9;}}"
            f"QPushButton:disabled{{background:{self.BORDER_MED}; color:{self.BTN_PRIMARY_TEXT};}}"
        )

    def btn_ghost(self, height: int = None) -> str:
        h = height or self._h()
        return (
            f"QPushButton{{"
            f"  background:transparent; color:{self.ACCENT};"
            f"  border:1.5px solid {self.ACCENT_BDR}; border-radius:{self.RADIUS};"
            f"  padding:0 {STYLES_BTN_PAD_H}px; font-size:{self.normal}px; font-weight:500;"
            f"  min-height:{h}px;"
            f"}}"
            f"QPushButton:hover{{background:{self.ACCENT_LT}; border-color:{self.ACCENT};}}"
        )

    def btn_success(self, height: int = None) -> str:
        h = height or self._h()
        return (
            f"QPushButton{{"
            f"  background:{self.SUCCESS_LT}; color:{self.SUCCESS};"
            f"  border:1px solid {self.SUCCESS_BDR}; border-radius:{self.RADIUS};"
            f"  padding:0 {STYLES_BTN_PAD_H}px; font-size:{self.normal}px; font-weight:600;"
            f"  min-height:{h}px;"
            f"}}"
            f"QPushButton:hover{{background:{self.SUCCESS_HOVER_BG}; border-color:{self.SUCCESS};}}"
        )

    def btn_danger(self, height: int = None) -> str:
        h = height or self._h()
        return (
            f"QPushButton{{"
            f"  background:{self.DANGER_LT}; color:{self.DANGER};"
            f"  border:1px solid {self.DANGER_BDR}; border-radius:{self.RADIUS};"
            f"  padding:0 {STYLES_BTN_PAD_H}px; font-size:{self.normal}px;"
            f"  min-height:{h}px;"
            f"}}"
            f"QPushButton:hover{{background:{self.DANGER_HOVER_BG}; border-color:{self.DANGER};}}"
        )

    # ══════════════════════════════════════════════════════
    # Inputs
    # ══════════════════════════════════════════════════════

    def input_field(self, height: int = None) -> str:
        h = height or self._h()
        return (
            f"QLineEdit{{"
            f"  border:1px solid {self.BORDER_MED}; border-radius:{self.RADIUS};"
            f"  padding:0 {STYLES_INPUT_PAD_H}px; font-size:{self.normal}px;"
            f"  background:{self.BG}; color:{self.TEXT_PRI};"
            f"  min-height:{h}px;"
            f"}}"
            f"QLineEdit:hover{{border-color:{self.BORDER_MED};}}"
            f"QLineEdit:focus{{border:1.5px solid {self.ACCENT}; background:{self.BG};}}"
        )

    def input_search(self, height: int = None) -> str:
        h = height or self._h()
        return (
            f"QLineEdit{{"
            f"  border:1px solid {self.BORDER}; border-radius:{self.RADIUS};"
            f"  padding:0 {STYLES_INPUT_PAD_H}px; font-size:{self.normal}px;"
            f"  background:{self.BG_SURFACE}; color:{self.TEXT_PRI};"
            f"  min-height:{h}px;"
            f"}}"
            f"QLineEdit:focus{{border:1.5px solid {self.ACCENT}; background:{self.BG};}}"
        )

    def combo_field(self, height: int = None) -> str:
        h = height or self._h()
        return (
            f"QComboBox{{"
            f"  border:1px solid {self.BORDER_MED}; border-radius:{self.RADIUS};"
            f"  padding:0 {STYLES_COMBO_PAD_H}px; font-size:{self.normal}px;"
            f"  background:{self.BG}; color:{self.TEXT_PRI};"
            f"  min-height:{h}px;"
            f"}}"
            f"QComboBox:focus{{border:1.5px solid {self.ACCENT};}}"
            f"QComboBox::drop-down{{border:none; border-left:{STYLES_COMBO_DROPDOWN_BORDER_W}px solid {self.BORDER}; width:{STYLES_COMBO_DROPDOWN_W}px;}}"
        )


def get_styles() -> _Styles:
    """يرجع كائن _Styles بأحجام الخط الحالية."""
    return _Styles(get_font_size())