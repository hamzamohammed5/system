"""
ui/tabs/design/design_styles.py
================================
أنماط CSS ديناميكية لوحدة التصميمات — تعتمد على حجم الخط الحالي.

الاستخدام:
    from ui.tabs.design.design_styles import get_styles

    s = get_styles()
    widget.setStyleSheet(s.label_header())
    btn.setStyleSheet(s.btn_primary())
"""

from ui.app_settings import get_font_size, fs


class _Styles:
    """
    كائن يحمل أحجام الخطوط الحالية ويولّد stylesheet strings.
    يُنشأ عبر get_styles() في كل مرة تحتاج فيها للأنماط الحالية.
    """

    # ── Palette ──────────────────────────────────────────
    BG          = "#FFFFFF"
    BG_SURFACE  = "#F8F9FB"
    BG_HOVER    = "#F1F4F9"
    BORDER      = "#E5E9F0"
    BORDER_MED  = "#CDD3E0"
    TEXT_PRI    = "#1A2035"
    TEXT_SEC    = "#5A6680"
    TEXT_MUT    = "#9BA5BE"
    ACCENT      = "#4F6EF7"
    ACCENT_LT   = "#EEF2FF"
    ACCENT_BDR  = "#C7D2FE"
    ACCENT_DARK = "#3D5BEF"
    SUCCESS     = "#16A34A"
    SUCCESS_LT  = "#F0FDF4"
    SUCCESS_BDR = "#BBF7D0"
    DANGER      = "#DC2626"
    DANGER_LT   = "#FEF2F2"
    DANGER_BDR  = "#FECACA"
    WARNING     = "#D97706"

    RADIUS    = "10px"
    RADIUS_SM = "6px"
    RADIUS_XS = "4px"

    def __init__(self, base: int):
        self.base   = base
        self.tiny   = fs(base, -2)
        self.small  = fs(base, -1)
        self.normal = fs(base,  0)
        self.large  = fs(base, +1)
        self.xlarge = fs(base, +2)

    # ══════════════════════════════════════════════════════
    # Labels
    # ══════════════════════════════════════════════════════

    def label_header(self) -> str:
        return (
            f"font-size:{self.xlarge}pt; font-weight:700; color:{self.TEXT_PRI};"
            "background:transparent; border:none;"
        )

    def label_section(self) -> str:
        return (
            f"font-size:{self.large}pt; font-weight:600; color:{self.TEXT_PRI};"
            "background:transparent; border:none;"
        )

    def label_field(self) -> str:
        return (
            f"font-size:{self.small}pt; font-weight:600; color:{self.TEXT_SEC};"
            "background:transparent; border:none;"
        )

    def label_secondary(self) -> str:
        return (
            f"font-size:{self.normal}pt; color:{self.TEXT_SEC};"
            "background:transparent; border:none;"
        )

    def label_muted(self) -> str:
        return (
            f"font-size:{self.small}pt; color:{self.TEXT_MUT};"
            "background:transparent; border:none;"
        )

    # ══════════════════════════════════════════════════════
    # Badges
    # ══════════════════════════════════════════════════════

    def badge_accent(self) -> str:
        return (
            f"font-size:{self.small}pt; font-weight:600; color:{self.ACCENT};"
            f"background:{self.ACCENT_LT}; border:1px solid {self.ACCENT_BDR};"
            f"border-radius:{self.RADIUS_XS}; padding:2px 8px;"
        )

    def badge_count(self) -> str:
        return (
            f"font-size:{self.small}pt; font-weight:700; color:{self.ACCENT};"
            f"background:{self.ACCENT_LT}; border:1px solid {self.ACCENT_BDR};"
            f"border-radius:10px; padding:1px 8px; min-width:20px;"
        )

    # ══════════════════════════════════════════════════════
    # Buttons
    # ══════════════════════════════════════════════════════

    def btn(self, bg, fg, bdr, hover_bg, height: int = None, radius: str = None) -> str:
        h  = height  or (self.normal * 2 + 6)
        r  = radius  or self.RADIUS_SM
        return (
            f"QPushButton{{"
            f"  background:{bg}; color:{fg};"
            f"  border:1px solid {bdr}; border-radius:{r};"
            f"  padding:0 12px; font-size:{self.normal}pt; min-height:{h}px;"
            f"}}"
            f"QPushButton:hover{{background:{hover_bg};}}"
            f"QPushButton:pressed{{opacity:0.85;}}"
        )

    def btn_primary(self, height: int = None) -> str:
        h = height or (self.normal * 2 + 6)
        return (
            f"QPushButton{{"
            f"  background:{self.ACCENT}; color:#fff;"
            f"  border:none; border-radius:{self.RADIUS_SM};"
            f"  padding:0 16px; font-size:{self.normal}pt; font-weight:600;"
            f"  min-height:{h}px;"
            f"}}"
            f"QPushButton:hover{{background:{self.ACCENT_DARK};}}"
            f"QPushButton:disabled{{background:#b0bec5; color:#fff;}}"
        )

    def btn_ghost(self, height: int = None) -> str:
        h = height or (self.normal * 2 + 6)
        return (
            f"QPushButton{{"
            f"  background:{self.BG}; color:{self.ACCENT};"
            f"  border:1.5px solid {self.ACCENT_BDR}; border-radius:{self.RADIUS_SM};"
            f"  padding:0 14px; font-size:{self.normal}pt;"
            f"  min-height:{h}px;"
            f"}}"
            f"QPushButton:hover{{background:{self.ACCENT_LT};}}"
        )

    def btn_success(self, height: int = None) -> str:
        h = height or (self.normal * 2 + 6)
        return (
            f"QPushButton{{"
            f"  background:{self.SUCCESS_LT}; color:{self.SUCCESS};"
            f"  border:1px solid {self.SUCCESS_BDR}; border-radius:{self.RADIUS_SM};"
            f"  padding:0 14px; font-size:{self.normal}pt; font-weight:600;"
            f"  min-height:{h}px;"
            f"}}"
            f"QPushButton:hover{{background:#DCFCE7;}}"
        )

    def btn_danger(self, height: int = None) -> str:
        h = height or (self.normal * 2 + 6)
        return (
            f"QPushButton{{"
            f"  background:{self.DANGER_LT}; color:{self.DANGER};"
            f"  border:1px solid {self.DANGER_BDR}; border-radius:{self.RADIUS_SM};"
            f"  padding:0 14px; font-size:{self.normal}pt;"
            f"  min-height:{h}px;"
            f"}}"
            f"QPushButton:hover{{background:#FEE2E2;}}"
        )

    # ══════════════════════════════════════════════════════
    # Inputs
    # ══════════════════════════════════════════════════════

    def input_field(self, height: int = None) -> str:
        h = height or (self.normal * 2 + 8)
        return (
            f"QLineEdit{{"
            f"  border:1px solid {self.BORDER_MED}; border-radius:{self.RADIUS_SM};"
            f"  padding:0 10px; font-size:{self.normal}pt;"
            f"  background:{self.BG}; color:{self.TEXT_PRI};"
            f"  min-height:{h}px;"
            f"}}"
            f"QLineEdit:focus{{border-color:{self.ACCENT}; background:{self.BG};}}"
        )

    def input_search(self, height: int = None) -> str:
        h = height or (self.normal * 2 + 6)
        return (
            f"QLineEdit{{"
            f"  border:1px solid {self.BORDER}; border-radius:{self.RADIUS_SM};"
            f"  padding:0 10px; font-size:{self.normal}pt;"
            f"  background:{self.BG_SURFACE}; color:{self.TEXT_PRI};"
            f"  min-height:{h}px;"
            f"}}"
            f"QLineEdit:focus{{border-color:{self.ACCENT}; background:{self.BG};}}"
        )

    def combo_field(self, height: int = None) -> str:
        h = height or (self.normal * 2 + 8)
        return (
            f"QComboBox{{"
            f"  border:1px solid {self.BORDER_MED}; border-radius:{self.RADIUS_SM};"
            f"  padding:0 8px; font-size:{self.normal}pt;"
            f"  background:{self.BG}; color:{self.TEXT_PRI};"
            f"  min-height:{h}px;"
            f"}}"
            f"QComboBox:focus{{border-color:{self.ACCENT};}}"
            f"QComboBox::drop-down{{border:none; width:18px;}}"
        )


def get_styles() -> _Styles:
    """
    يرجع كائن _Styles بأحجام الخط الحالية.
    استدعها في كل مرة تحتاج stylesheet ديناميكي.
    """
    return _Styles(get_font_size())