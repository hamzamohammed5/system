"""
ui/widgets/components/headers_page.py
=======================================
SectionHeader + PageHeader + DetailHeader — هيدرات الصفحات والتفاصيل.

[إصلاح 2.5] from .stat_row import BadgeLabel
         → from .badge import BadgeLabel
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont

from ui.widgets.panels.themed_inputs import ThemedFrame

from ui.theme import _C
from ui.font  import fs, get_font_size
from ..theme.builders import h_divider, v_divider
from .button         import make_btn
from .badge          import BadgeLabel           # [إصلاح 2.5]
from .label          import InfoRow
from ..core.i18n import tr
from ..core.widget_mixin import WidgetMixin
from ui.constants import (
    SPACING_XS, SPACING_SM, SPACING_MD, SPACING_LG,
    SECTION_BAR_W, SECTION_BAR_H, SECTION_BAR_RADIUS,
    DETAIL_HEADER_MARGIN_H, DETAIL_HEADER_MARGIN_T, DETAIL_HEADER_BORDER_W,
    PAGE_HEADER_MARGIN_H, PAGE_HEADER_MARGIN_V,
    PAGE_HEADER_MARGIN_H_COMPACT, PAGE_HEADER_MARGIN_V_COMPACT, PAGE_HEADER_BORDER_W,
    DETAIL_HEADER_TOOLBAR_SPACING,
)


# ══════════════════════════════════════════════════════════
# SectionHeader
# ══════════════════════════════════════════════════════════

class SectionHeader(QWidget, WidgetMixin):
    """هيدر قسم داخلي: accent bar + عنوان + أزرار."""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self._title_text = title
        self._bar = None
        self._lbl = None
        self._build(title)
        self._init_widget_mixin(theme=True, font=True)
        self._refresh_style()

    def _build(self, title: str):
        self.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, SPACING_SM, 0, SPACING_SM)
        lay.setSpacing(SPACING_LG)

        self._bar = QLabel()
        self._bar.setFixedSize(SECTION_BAR_W, SECTION_BAR_H)
        lay.addWidget(self._bar)

        self._lbl = QLabel(title)
        lay.addWidget(self._lbl)
        lay.addStretch()
        self._btn_row = lay
        self._refresh_style()

    def _refresh_style(self, *_):
        self._bar.setStyleSheet(f"background:{_C['accent']}; border-radius:{SECTION_BAR_RADIUS}px; border:none;")
        base = get_font_size()
        self._lbl.setStyleSheet(
            f"font-weight:700; font-size:{fs(base,+1)}pt;"
            f"color:{_C['text_primary']}; background:transparent; border:none;"
        )

    def set_title(self, title: str):
        self._lbl.setText(title)

    def add_button(self, text: str, callback=None,
                   style: str = "normal") -> QPushButton:
        btn = make_btn(text, style)
        if callback:
            btn.clicked.connect(callback)
        self._btn_row.addWidget(btn)
        return btn


# ══════════════════════════════════════════════════════════
# PageHeader
# ══════════════════════════════════════════════════════════

class PageHeader(ThemedFrame, WidgetMixin):
    """هيدر صفحة رئيسية: أيقونة + عنوان + subtitle + أزرار."""

    def __init__(self, title: str = "", subtitle: str = "",
                 icon: str = "", accent: str = None,
                 compact: bool = False, parent=None):
        super().__init__(parent)
        self._accent  = accent or _C['accent']
        self._compact = compact
        self._icon    = icon
        self._lbl_icon = None
        self._lbl_title = None
        self._lbl_sub   = None
        self._build(title, subtitle, icon)
        self._init_widget_mixin(theme=True, font=True)
        self._refresh_style()

    def _build(self, title: str, subtitle: str, icon: str):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        h_pad = PAGE_HEADER_MARGIN_H_COMPACT if self._compact else PAGE_HEADER_MARGIN_H
        v_pad = PAGE_HEADER_MARGIN_V_COMPACT if self._compact else PAGE_HEADER_MARGIN_V

        lay = QHBoxLayout(self)
        lay.setContentsMargins(h_pad, v_pad, h_pad, v_pad)
        lay.setSpacing(SPACING_LG)

        if icon:
            self._lbl_icon = QLabel(icon)
            self._lbl_icon.setAlignment(Qt.AlignVCenter)
            lay.addWidget(self._lbl_icon)

        col = QVBoxLayout()
        col.setSpacing(SPACING_XS)
        col.setContentsMargins(0, 0, 0, 0)

        self._lbl_title = QLabel(title)
        col.addWidget(self._lbl_title)

        self._lbl_sub = None
        if subtitle:
            self._lbl_sub = QLabel(subtitle)
            col.addWidget(self._lbl_sub)

        lay.addLayout(col, stretch=1)

        self._btn_row = QHBoxLayout()
        self._btn_row.setSpacing(SPACING_MD)
        lay.addLayout(self._btn_row)

        self._refresh_style()

    def _refresh_style(self, *_):
        self.setStyleSheet(f"""
            QFrame {{
                background:{_C['bg_surface']};
                border-bottom:{PAGE_HEADER_BORDER_W}px solid {_C['border']};
            }}
        """)
        base = get_font_size()

        if self._lbl_icon:
            sz = fs(base, +1) if self._compact else fs(base, +2)
            self._lbl_icon.setStyleSheet(
                f"font-size:{sz}pt; background:transparent; border:none;"
            )

        f = QFont()
        f.setPointSize(fs(base, +1) if self._compact else fs(base, +2))
        f.setBold(True)
        self._lbl_title.setFont(f)
        self._lbl_title.setStyleSheet(
            f"color:{_C['text_primary']}; background:transparent; border:none;"
        )

        if self._lbl_sub:
            self._lbl_sub.setStyleSheet(
                f"color:{_C['text_muted']}; font-size:{fs(base,-1)}pt;"
                "background:transparent; border:none;"
            )

    def set_title(self, text: str):
        self._lbl_title.setText(text)

    def set_subtitle(self, text: str):
        if self._lbl_sub:
            self._lbl_sub.setText(text)

    def add_action(self, text: str, callback=None,
                   style: str = "primary") -> QPushButton:
        btn = make_btn(text, style)
        if callback:
            btn.clicked.connect(callback)
        self._btn_row.addWidget(btn)
        return btn


# ══════════════════════════════════════════════════════════
# DetailHeader
# ══════════════════════════════════════════════════════════

class DetailHeader(ThemedFrame, WidgetMixin):
    """
    هيدر صفحة تفاصيل: عنوان + شارات + بطاقات إحصائية + toolbar أزرار.
    """

    def __init__(self, bg: str = None, parent=None):
        super().__init__(parent)
        # [إصلاح ثيم — جذري] كان bg بيتحسب مرة واحدة في BaseDetailPanel._build()
        # عبر (self.HEADER_BG or _C['bg_surface']) وقت الثيم الحالي وقتها،
        # ثم يتبعت هنا كـ *قيمة نصية ثابتة* وتتخزن في self._custom_bg — فبتفضل
        # جامدة (مثلاً "#FAFAF8") للأبد، حتى لو _C['bg_surface'] اتغيّر بعد
        # كده. النتيجة: DetailHeader._refresh_style() كانت تُعاد استدعاؤها
        # صح عند كل theme_changed، لكنها كانت تُعيد رسم *نفس* اللون القديم
        # في كل مرة (تكتب فوق أي تصحيح خارجي كان BaseDetailPanel يحاول عمله).
        #
        # الحل الصحيح: DetailHeader نفسها تحتفظ فقط بلون *مخصص فعلي* (لو
        # الـ subclass حدد HEADER_BG صراحة). لو مفيش تخصيص، بنسيب self._custom_bg
        # = None وبنقرأ _C['bg_surface'] *وقت كل رسم* داخل _refresh_style —
        # مش نسخة محسوبة مسبقًا. BaseDetailPanel._build() اتعدلت بالتوازي
        # عشان تبعت bg=None (مش القيمة المحسوبة) لما HEADER_BG يكون None.
        self._custom_bg  = bg
        self._stat_cards = []
        self._toolbar    = None
        self._tb_section = None
        self._tb_lay     = None
        self._title_is_custom = False
        self._type_color = None
        self._priority_color = None
        self._build()
        self._init_widget_mixin(theme=True, font=True, lang=True)
        self._refresh_style()

    def _build(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        root = QVBoxLayout(self)
        root.setContentsMargins(DETAIL_HEADER_MARGIN_H, DETAIL_HEADER_MARGIN_T,
                                DETAIL_HEADER_MARGIN_H, 0)
        root.setSpacing(0)

        top = QWidget()
        top.setStyleSheet("background:transparent;")
        top_lay = QVBoxLayout(top)
        top_lay.setContentsMargins(0, 0, 0, SPACING_LG)
        top_lay.setSpacing(SPACING_XS)

        title_row = QHBoxLayout()
        title_row.setSpacing(SPACING_LG)
        title_row.setAlignment(Qt.AlignVCenter)

        self._lbl_title = QLabel()
        self._lbl_type = QLabel("")
        self._badge_status   = BadgeLabel()
        self._badge_priority = QLabel("")
        self._badge_priority.setStyleSheet("background:transparent; border:none;")

        title_row.addWidget(self._lbl_title)
        title_row.addWidget(self._lbl_type)
        title_row.addStretch()
        title_row.addWidget(self._badge_priority)
        title_row.addWidget(self._badge_status)
        top_lay.addLayout(title_row)

        self._lbl_customer = QLabel("")
        self._lbl_customer.setWordWrap(True)
        self._lbl_customer.setVisible(False)
        top_lay.addWidget(self._lbl_customer)

        self._info_row = InfoRow()
        top_lay.addWidget(self._info_row)

        root.addWidget(top)
        root.addWidget(h_divider())

        cards_section = QWidget()
        cards_section.setStyleSheet("background:transparent;")
        cards_lay = QVBoxLayout(cards_section)
        cards_lay.setContentsMargins(0, SPACING_LG, 0, SPACING_LG)
        self._cards_row = QHBoxLayout()
        self._cards_row.setSpacing(SPACING_LG)
        cards_lay.addLayout(self._cards_row)
        root.addWidget(cards_section)
        root.addWidget(h_divider())

        self._tb_section = QWidget()
        self._tb_section.setStyleSheet("background:transparent;")
        self._tb_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._tb_lay = QVBoxLayout(self._tb_section)
        self._tb_lay.setContentsMargins(0, SPACING_MD, 0, SPACING_LG)
        self._tb_section.setVisible(False)
        root.addWidget(self._tb_section)

        self._root_layout = root

    def _refresh_style(self, *_):
        bg = self._custom_bg or _C['bg_surface']
        self.setStyleSheet(f"""
            QFrame {{
                background:{bg};
                border:none;
                border-bottom:{DETAIL_HEADER_BORDER_W}px solid {_C['border']};
            }}
        """)

        base = get_font_size()

        if not self._title_is_custom:
            self._lbl_title.setText(tr('amount_dash_placeholder'))
        f = QFont()
        f.setPointSize(fs(base, +4))
        f.setBold(True)
        self._lbl_title.setFont(f)
        self._lbl_title.setStyleSheet(
            f"color:{_C['text_primary']}; background:transparent; border:none;"
        )

        type_color = self._type_color or _C['text_muted']
        self._lbl_type.setStyleSheet(
            f"color:{type_color}; font-size:{fs(base,0)}pt;"
            "background:transparent; border:none; font-weight:500;"
        )

        priority_color = self._priority_color or _C['text_neutral']
        self._badge_priority.setStyleSheet(
            f"color:{priority_color}; background:transparent; border:none;"
            f"font-size:{fs(base,+1)}pt;"
        )

        self._lbl_customer.setStyleSheet(
            f"color:{_C['text_sec']}; font-size:{fs(base,+1)}pt; font-weight:600;"
            "background:transparent; border:none;"
        )

    def _refresh_lang(self, *_):
        if not self._title_is_custom:
            self._lbl_title.setText(tr('amount_dash_placeholder'))

    def _ensure_toolbar(self) -> "ActionToolbar":
        if self._toolbar is None:
            from .action_toolbar import ActionToolbar
            self._toolbar = ActionToolbar(spacing=DETAIL_HEADER_TOOLBAR_SPACING)
            self._tb_lay.addWidget(self._toolbar)
            self._tb_section.setVisible(True)
        return self._toolbar

    def set_title(self, text: str):
        self._title_is_custom = True
        self._lbl_title.setText(text)

    def set_type_badge(self, text: str, color: str = None):
        self._lbl_type.setText(text)
        self._type_color = color
        base = get_font_size()
        self._lbl_type.setStyleSheet(
            f"color:{color or _C['text_muted']}; font-size:{fs(base,0)}pt;"
            "background:transparent; border:none; font-weight:500;"
        )

    def set_status_badge(self, text: str, text_color: str = None,
                         bg: str = None, border: str = None):
        self._badge_status.set_badge(
            text,
            text_color or _C['text_neutral'],
            bg         or _C['card_fallback_bg'],
            border     or _C['card_fallback_border'],
        )

    def set_priority_badge(self, text: str, color: str = None):
        self._priority_color = color
        _color = color or _C['text_neutral']
        self._badge_priority.setText(text)
        self._badge_priority.setStyleSheet(
            f"color:{_color}; background:transparent; border:none;"
            f"font-size:{fs(get_font_size(),+1)}pt;"
        )

    def set_customer_name(self, name: str):
        if name:
            self._lbl_customer.setText(name)
            self._lbl_customer.setVisible(True)
        else:
            self._lbl_customer.setVisible(False)

    def set_info(self, parts: list):
        self._info_row.set_parts(parts)

    def add_stat_card(self, icon: str, title: str, value: str = None,
                      color: str = None, compact: bool = True):
        from .stat_card import StatCard
        _value = value if value is not None else tr('amount_dash_placeholder')
        _color = color or _C['blue']
        card = StatCard(icon, title, _value, _color, compact=compact)
        self._cards_row.addWidget(card, stretch=1)
        self._stat_cards.append(card)
        return card

    def clear_stat_cards(self):
        for card in self._stat_cards:
            self._cards_row.removeWidget(card)
            card.deleteLater()
        self._stat_cards.clear()

    def add_action(self, text: str, callback=None,
                   style: str = "primary") -> QPushButton:
        return self._ensure_toolbar().add_action(text, style, callback)

    @property
    def toolbar(self) -> "ActionToolbar":
        return self._ensure_toolbar()