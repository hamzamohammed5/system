"""
ui/tabs/design/design_styles.py
================================
أنماط CSS ديناميكية لوحدة التصميمات — متناسقة مع app_settings.py
"""

from ui.font import get_font_size, fs
from ui.theme import _C as APP_COLORS


class _Styles:
    """
    كائن يحمل أحجام الخطوط الحالية ويولّد stylesheet strings.
    الألوان مأخوذة من app_settings._C للتناسق الكامل.
    """

    # ── Palette من app_settings ──────────────────────────
    BG          = APP_COLORS["bg_input"]
    BG_SURFACE  = APP_COLORS["bg_surface"]
    BG_HOVER    = APP_COLORS["bg_hover"]
    BORDER      = APP_COLORS["border"]
    BORDER_MED  = APP_COLORS["border_med"]
    TEXT_PRI    = APP_COLORS["text_primary"]
    TEXT_SEC    = APP_COLORS["text_sec"]
    TEXT_MUT    = APP_COLORS["text_muted"]
    ACCENT      = APP_COLORS["accent"]
    ACCENT_LT   = APP_COLORS["accent_light"]
    ACCENT_BDR  = APP_COLORS["accent_mid"]
    ACCENT_DARK = APP_COLORS["accent_hover"]
    ACCENT_TEXT = APP_COLORS["accent_text"]
    BTN_PRIMARY_TEXT = APP_COLORS["btn_primary_text"]
    SUCCESS     = APP_COLORS["success"]
    SUCCESS_LT  = APP_COLORS["success_bg"]
    SUCCESS_BDR = APP_COLORS["success_border"]
    SUCCESS_HOVER_BG = APP_COLORS["success_hover_bg"]
    DANGER      = APP_COLORS["danger"]
    DANGER_LT   = APP_COLORS["danger_bg"]
    DANGER_BDR  = APP_COLORS["danger_border"]
    DANGER_HOVER_BG = APP_COLORS["danger_hover_bg"]
    WARNING     = APP_COLORS["warning"]

    RADIUS    = "6px"
    RADIUS_SM = "4px"
    RADIUS_XS = "3px"

    def __init__(self, base: int):
        self.base   = base
        self.tiny   = fs(base, -2)
        self.small  = fs(base, -1)
        self.normal = fs(base,  0)
        self.large  = fs(base, +1)
        self.xlarge = fs(base, +2)

    def _h(self, override=None) -> int:
        """ارتفاع قياسي للعناصر."""
        return override or (self.normal * 2 + 8)

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
            "background:transparent; border:none; letter-spacing:0.2px;"
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
            f"border-radius:{self.RADIUS_SM}; padding:2px 8px;"
        )

    def badge_count(self) -> str:
        return (
            f"font-size:{self.small}px; font-weight:700; color:{self.ACCENT_TEXT};"
            f"background:{self.ACCENT_LT}; border:1px solid {self.ACCENT_BDR};"
            f"border-radius:10px; padding:1px 8px; min-width:20px;"
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
            f"  padding:0 14px; font-size:{self.normal}px; font-weight:500;"
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
            f"  padding:0 18px; font-size:{self.normal}px; font-weight:600;"
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
            f"  padding:0 14px; font-size:{self.normal}px; font-weight:500;"
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
            f"  padding:0 14px; font-size:{self.normal}px; font-weight:600;"
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
            f"  padding:0 14px; font-size:{self.normal}px;"
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
            f"  padding:0 10px; font-size:{self.normal}px;"
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
            f"  padding:0 10px; font-size:{self.normal}px;"
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
            f"  padding:0 8px; font-size:{self.normal}px;"
            f"  background:{self.BG}; color:{self.TEXT_PRI};"
            f"  min-height:{h}px;"
            f"}}"
            f"QComboBox:focus{{border:1.5px solid {self.ACCENT};}}"
            f"QComboBox::drop-down{{border:none; border-left:1px solid {self.BORDER}; width:22px;}}"
        )


def get_styles() -> _Styles:
    """يرجع كائن _Styles بأحجام الخط الحالية."""
    return _Styles(get_font_size())