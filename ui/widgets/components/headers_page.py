"""
ui/widgets/components/headers_page.py
=======================================
SectionHeader + PageHeader + DetailHeader — هيدرات الصفحات والتفاصيل.

[إصلاح 2.5] from .stat_row import BadgeLabel
         → from .badge import BadgeLabel
"""

from PyQt5.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont

from ui.theme import _C
from ui.font  import fs, get_font_size
from ..theme.builders import h_divider, v_divider
from .button         import make_btn
from .badge          import BadgeLabel           # [إصلاح 2.5]
from .label          import InfoRow


# ══════════════════════════════════════════════════════════
# SectionHeader
# ══════════════════════════════════════════════════════════

class SectionHeader(QWidget):
    """هيدر قسم داخلي: accent bar + عنوان + أزرار."""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self._build(title)

    def _build(self, title: str):
        self.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 6, 0, 6)
        lay.setSpacing(10)

        bar = QLabel()
        bar.setFixedSize(3, 18)
        bar.setStyleSheet(f"background:{_C['accent']}; border-radius:2px; border:none;")
        lay.addWidget(bar)

        base = get_font_size()
        self._lbl = QLabel(title)
        self._lbl.setStyleSheet(
            f"font-weight:700; font-size:{fs(base,+1)}pt;"
            f"color:{_C['text_primary']}; background:transparent; border:none;"
        )
        lay.addWidget(self._lbl)
        lay.addStretch()
        self._btn_row = lay

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

class PageHeader(QFrame):
    """هيدر صفحة رئيسية: أيقونة + عنوان + subtitle + أزرار."""

    def __init__(self, title: str = "", subtitle: str = "",
                 icon: str = "", accent: str = None,
                 compact: bool = False, parent=None):
        super().__init__(parent)
        self._accent  = accent or _C.get('accent', '#1565c0')
        self._compact = compact
        self._build(title, subtitle, icon)

    def _build(self, title: str, subtitle: str, icon: str):
        self.setStyleSheet(f"""
            QFrame {{
                background:{_C.get('bg_surface','white')};
                border-bottom:1px solid {_C.get('border','#e0e0e0')};
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        h_pad = 12 if self._compact else 20
        v_pad = 8  if self._compact else 14

        lay = QHBoxLayout(self)
        lay.setContentsMargins(h_pad, v_pad, h_pad, v_pad)
        lay.setSpacing(12)

        base = get_font_size()

        if icon:
            sz = fs(base, +1) if self._compact else fs(base, +2)
            lbl_icon = QLabel(icon)
            lbl_icon.setStyleSheet(
                f"font-size:{sz}pt; background:transparent; border:none;"
            )
            lbl_icon.setAlignment(Qt.AlignVCenter)
            lay.addWidget(lbl_icon)

        col = QVBoxLayout()
        col.setSpacing(2)
        col.setContentsMargins(0, 0, 0, 0)

        self._lbl_title = QLabel(title)
        f = QFont()
        f.setPointSize(fs(base, +1) if self._compact else fs(base, +2))
        f.setBold(True)
        self._lbl_title.setFont(f)
        self._lbl_title.setStyleSheet(
            f"color:{_C.get('text_primary','#1c1b18')}; background:transparent; border:none;"
        )
        col.addWidget(self._lbl_title)

        self._lbl_sub = None
        if subtitle:
            self._lbl_sub = QLabel(subtitle)
            self._lbl_sub.setStyleSheet(
                f"color:{_C.get('text_muted','#9ca3af')}; font-size:{fs(base,-1)}pt;"
                "background:transparent; border:none;"
            )
            col.addWidget(self._lbl_sub)

        lay.addLayout(col, stretch=1)

        self._btn_row = QHBoxLayout()
        self._btn_row.setSpacing(8)
        lay.addLayout(self._btn_row)

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

class DetailHeader(QFrame):
    """
    هيدر صفحة تفاصيل: عنوان + شارات + بطاقات إحصائية + toolbar أزرار.
    """

    def __init__(self, bg: str = None, parent=None):
        super().__init__(parent)
        self._stat_cards = []
        self._toolbar    = None
        self._tb_section = None
        self._tb_lay     = None
        self._build(bg or _C['bg_surface'])

    def _build(self, bg: str):
        self.setStyleSheet(f"""
            QFrame {{
                background:{bg};
                border:none;
                border-bottom:1px solid {_C['border']};
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 14, 20, 0)
        root.setSpacing(0)

        top = QWidget()
        top.setStyleSheet("background:transparent;")
        top_lay = QVBoxLayout(top)
        top_lay.setContentsMargins(0, 0, 0, 12)
        top_lay.setSpacing(4)

        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        title_row.setAlignment(Qt.AlignVCenter)

        base = get_font_size()
        self._lbl_title = QLabel("─")
        f = QFont()
        f.setPointSize(fs(base, +4))
        f.setBold(True)
        self._lbl_title.setFont(f)
        self._lbl_title.setStyleSheet(
            f"color:{_C['text_primary']}; background:transparent; border:none;"
        )

        self._lbl_type = QLabel("")
        self._lbl_type.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{fs(base,0)}pt;"
            "background:transparent; border:none; font-weight:500;"
        )

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
        self._lbl_customer.setStyleSheet(
            f"color:{_C['text_sec']}; font-size:{fs(base,+1)}pt; font-weight:600;"
            "background:transparent; border:none;"
        )
        self._lbl_customer.setVisible(False)
        top_lay.addWidget(self._lbl_customer)

        self._info_row = InfoRow(separator="  ·  ")
        top_lay.addWidget(self._info_row)

        root.addWidget(top)
        root.addWidget(h_divider())

        cards_section = QWidget()
        cards_section.setStyleSheet("background:transparent;")
        cards_lay = QVBoxLayout(cards_section)
        cards_lay.setContentsMargins(0, 12, 0, 12)
        self._cards_row = QHBoxLayout()
        self._cards_row.setSpacing(10)
        cards_lay.addLayout(self._cards_row)
        root.addWidget(cards_section)
        root.addWidget(h_divider())

        self._tb_section = QWidget()
        self._tb_section.setStyleSheet("background:transparent;")
        self._tb_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._tb_lay = QVBoxLayout(self._tb_section)
        self._tb_lay.setContentsMargins(0, 8, 0, 10)
        self._tb_section.setVisible(False)
        root.addWidget(self._tb_section)

        self._root_layout = root

    def _ensure_toolbar(self) -> "ActionToolbar":
        if self._toolbar is None:
            from .action_toolbar import ActionToolbar
            self._toolbar = ActionToolbar(spacing=8)
            self._tb_lay.addWidget(self._toolbar)
            self._tb_section.setVisible(True)
        return self._toolbar

    def set_title(self, text: str):
        self._lbl_title.setText(text)

    def set_type_badge(self, text: str, color: str = None):
        self._lbl_type.setText(text)
        if color:
            base = get_font_size()
            self._lbl_type.setStyleSheet(
                f"color:{color}; font-size:{fs(base,0)}pt;"
                "background:transparent; border:none; font-weight:500;"
            )

    def set_status_badge(self, text: str, text_color: str = "#555",
                         bg: str = "#f5f5f5", border: str = "#e0e0e0"):
        self._badge_status.set_badge(text, text_color, bg, border)

    def set_priority_badge(self, text: str, color: str = "#6b7280"):
        self._badge_priority.setText(text)
        self._badge_priority.setStyleSheet(
            f"color:{color}; background:transparent; border:none;"
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

    def add_stat_card(self, icon: str, title: str, value: str = "─",
                      color: str = "#1565c0", compact: bool = True):
        from .stat_card import StatCard
        card = StatCard(icon, title, value, color, compact=compact)
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