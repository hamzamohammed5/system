"""
ui/widgets/shared/panles_helper/detail_header.py
============================
"""

from PyQt5.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont

from ui.app_settings import _C, fs
from .stat_card import StatCard
from .badge_label import BadgeLabel
from .info_row import InfoRow
from .action_toolbar import ActionToolbar
from .colors_and_base import _base


class DetailHeader(QFrame):
    """
    هيدر موحد لصفحات التفاصيل.
    minimum width = 0 عشان الـ _inner في BaseDetailPanel هو اللي يتحكم في الـ scroll.
    """

    # ✅ صفر — مش إحنا اللي نحدد الـ minimum، الـ _inner في BaseDetailPanel هو اللي يحددها
    HEADER_MIN_WIDTH = 0

    def __init__(self, bg: str = None, parent=None):
        super().__init__(parent)
        self._stat_cards: list[StatCard] = []
        self._build(bg or _C['bg_surface'])

    def _build(self, bg):
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: none;
                border-bottom: 1px solid {_C['border']};
            }}
        """)
        # ✅ بدون minimum width — الـ BaseDetailPanel._inner هو اللي يتحكم
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 14, 20, 0)
        root.setSpacing(0)

        # ══ القسم العلوي ══
        top_section = QWidget()
        top_section.setStyleSheet("background:transparent;")
        top_lay = QVBoxLayout(top_section)
        top_lay.setContentsMargins(0, 0, 0, 12)
        top_lay.setSpacing(4)

        # ── صف 1: العنوان + الشارات ──
        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        title_row.setAlignment(Qt.AlignVCenter)

        self._lbl_title = QLabel("─")
        base = _base()
        f = QFont()
        f.setPointSize(fs(base, +4))
        f.setBold(True)
        self._lbl_title.setFont(f)
        self._lbl_title.setStyleSheet(
            f"color:{_C['text_primary']}; background:transparent; border:none;"
            "letter-spacing:-0.3px;"
        )

        self._lbl_type = QLabel("")
        self._lbl_type.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{fs(base,0)}pt;"
            "background:transparent; border:none; font-weight:500;"
        )

        title_row.addWidget(self._lbl_title)
        title_row.addWidget(self._lbl_type)
        title_row.addStretch()

        self._badge_priority = QLabel("")
        self._badge_priority.setStyleSheet(
            f"background:transparent; border:none; font-size:{fs(base,0)}pt;"
        )

        self._badge_status = BadgeLabel()

        title_row.addWidget(self._badge_priority)
        title_row.addWidget(self._badge_status)
        top_lay.addLayout(title_row)

        # ── صف 2: اسم العميل ──
        self._lbl_customer = QLabel("")
        self._lbl_customer.setWordWrap(True)
        self._lbl_customer.setStyleSheet(
            f"color:{_C['text_sec']}; font-size:{fs(base, +1)}pt; font-weight:600;"
            "background:transparent; border:none;"
        )
        self._lbl_customer.setVisible(False)
        top_lay.addWidget(self._lbl_customer)

        # ── صف 3: التفاصيل الثانوية ──
        self._info_row = InfoRow(separator="  ·  ")
        top_lay.addWidget(self._info_row)

        root.addWidget(top_section)

        # ── فاصل ──
        root.addWidget(self._make_divider())

        # ══ البطاقات الإحصائية ══
        cards_section = QWidget()
        cards_section.setStyleSheet("background:transparent;")
        cards_lay = QVBoxLayout(cards_section)
        cards_lay.setContentsMargins(0, 12, 0, 12)
        cards_lay.setSpacing(0)

        self._cards_row = QHBoxLayout()
        self._cards_row.setSpacing(10)
        cards_lay.addLayout(self._cards_row)

        root.addWidget(cards_section)

        # ── فاصل ──
        root.addWidget(self._make_divider())

        # ══ شريط الأزرار ══
        toolbar_section = QWidget()
        toolbar_section.setStyleSheet("background:transparent;")
        tb_lay = QVBoxLayout(toolbar_section)
        tb_lay.setContentsMargins(0, 8, 0, 10)
        tb_lay.setSpacing(0)

        self.toolbar = ActionToolbar(spacing=8)
        tb_lay.addWidget(self.toolbar)

        root.addWidget(toolbar_section)

    @staticmethod
    def _make_divider() -> QFrame:
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setFixedHeight(1)
        div.setStyleSheet(f"background:{_C['border']}; border:none;")
        return div

    # ── API ──────────────────────────────────────────────

    def set_title(self, text: str):
        self._lbl_title.setText(text)

    def set_type_badge(self, text: str, color: str = None):
        self._lbl_type.setText(text)
        if color:
            self._lbl_type.setStyleSheet(
                f"color:{color}; font-size:{fs(_base(),0)}pt;"
                "background:transparent; border:none; font-weight:500;"
            )

    def set_status_badge(self, text: str, text_color: str = "#555",
                         bg: str = "#f5f5f5", border: str = "#e0e0e0"):
        self._badge_status.set_badge(text, text_color, bg, border)

    def set_priority_badge(self, text: str, color: str = "#6b7280"):
        self._badge_priority.setText(text)
        self._badge_priority.setStyleSheet(
            f"color:{color}; background:transparent; border:none;"
            f"font-size:{fs(_base(),+1)}pt;"
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
                      color: str = "#1565c0", compact: bool = True) -> StatCard:
        card = StatCard(icon, title, value, color, compact=compact)
        self._cards_row.addWidget(card, stretch=1)
        self._stat_cards.append(card)
        return card

    def clear_stat_cards(self):
        for card in self._stat_cards:
            self._cards_row.removeWidget(card)
            card.deleteLater()
        self._stat_cards.clear()