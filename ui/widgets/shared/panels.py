"""
ui/widgets/shared/panels.py
============================
مكونات UI مشتركة قابلة لإعادة الاستخدام في كل الأقسام.
"""

from PyQt5.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui  import QFont, QColor

from ui.app_settings import _C, get_font_size, fs


def _base() -> int:
    return get_font_size()


_CARD_PALETTE = {
    "#1565c0": ("#e8f0fe", "#90caf9"),
    "#0d47a1": ("#e3f2fd", "#64b5f6"),
    "#1d4ed8": ("#eff6ff", "#93c5fd"),
    "#10b981": ("#ecfdf5", "#6ee7b7"),
    "#2e7d32": ("#e8f5e9", "#a5d6a7"),
    "#065f46": ("#ecfdf5", "#a7f3d0"),
    "#ef4444": ("#fef2f2", "#fca5a5"),
    "#dc2626": ("#fef2f2", "#fca5a5"),
    "#c62828": ("#ffebee", "#ef9a9a"),
    "#991b1b": ("#fef2f2", "#fecaca"),
    "#f59e0b": ("#fffbeb", "#fcd34d"),
    "#e65100": ("#fff3e0", "#ffcc80"),
    "#b45309": ("#fffbeb", "#fde68a"),
    "#6b7280": ("#f9fafb", "#d1d5db"),
    "#374151": ("#f9fafb", "#e5e7eb"),
    "#8b5cf6": ("#f5f3ff", "#c4b5fd"),
    "#6d28d9": ("#f5f3ff", "#ddd6fe"),
    "#6a1b9a": ("#f3e5f5", "#ce93d8"),
}


def _card_colors(color: str) -> tuple:
    return _CARD_PALETTE.get(color, ("#f5f5f5", "#e0e0e0"))


# ══════════════════════════════════════════════════════════
# StatCard
# ══════════════════════════════════════════════════════════

class StatCard(QFrame):
    def __init__(self, icon: str = "", title: str = "",
                 value: str = "─", color: str = "#1565c0",
                 bg: str = None, border: str = None,
                 compact: bool = False, parent=None):
        super().__init__(parent)
        self._color   = color
        self._compact = compact
        self._icon    = icon
        self._title   = title
        self._build(icon, title, value, color, bg, border)

    def _build(self, icon, title, value, color, bg, border):
        _bg, _border = _card_colors(color)
        if bg:     _bg = bg
        if border: _border = border

        self.setStyleSheet(f"""
            QFrame {{
                background: {_bg};
                border: 1px solid {_border};
                border-radius: 10px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay = QVBoxLayout(self)
        base = _base()

        if self._compact:
            lay.setContentsMargins(10, 8, 10, 8)
            lay.setSpacing(2)
        else:
            lay.setContentsMargins(14, 12, 14, 12)
            lay.setSpacing(3)

        top_row = QHBoxLayout()
        top_row.setSpacing(0)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(
            f"color:{color}; font-size:{fs(base,-1)}pt; font-weight:600;"
            "background:transparent; border:none; letter-spacing:0.2px;"
        )
        top_row.addWidget(lbl_title)
        top_row.addStretch()

        if icon:
            lbl_icon = QLabel(icon)
            lbl_icon.setStyleSheet(
                f"font-size:{fs(base,+1) if self._compact else fs(base,+2)}pt;"
                "background:transparent; border:none; opacity:0.8;"
            )
            top_row.addWidget(lbl_icon)

        lay.addLayout(top_row)

        self._lbl_value = QLabel(value)
        f = QFont()
        val_size = fs(base, +1) if self._compact else fs(base, +3)
        f.setPointSize(val_size)
        f.setBold(True)
        self._lbl_value.setFont(f)
        self._lbl_value.setStyleSheet(
            f"color:{color}; background:transparent; border:none;"
        )
        self._lbl_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lay.addWidget(self._lbl_value)

        self._lbl_title = lbl_title

    def set_value(self, text: str):
        self._lbl_value.setText(text)

    def set_color(self, color: str):
        self._color = color
        self._lbl_value.setStyleSheet(
            f"color:{color}; background:transparent; border:none;"
        )
        self._lbl_title.setStyleSheet(
            f"color:{color}; font-size:{fs(_base(),-1)}pt; font-weight:600;"
            "background:transparent; border:none;"
        )

    def value_label(self) -> QLabel:
        return self._lbl_value


# ══════════════════════════════════════════════════════════
# SectionHeader
# ══════════════════════════════════════════════════════════

class SectionHeader(QWidget):
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self._build(title)

    def _build(self, title):
        self.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 6, 0, 6)
        lay.setSpacing(10)

        accent = QFrame()
        accent.setFixedSize(3, 18)
        accent.setStyleSheet(
            f"background:{_C['accent']}; border-radius:2px; border:none;"
        )
        lay.addWidget(accent)

        self._lbl = QLabel(title)
        base = _base()
        self._lbl.setStyleSheet(
            f"font-weight:700; font-size:{fs(base,+1)}pt;"
            f"color:{_C['text_primary']}; background:transparent; border:none;"
        )
        lay.addWidget(self._lbl)
        lay.addStretch()

        self._btn_container = lay

    def set_title(self, title: str):
        self._lbl.setText(title)

    def add_button(self, text: str, callback=None,
                   style: str = "normal") -> QPushButton:
        btn = _make_btn(text, style)
        if callback:
            btn.clicked.connect(callback)
        self._btn_container.addWidget(btn)
        return btn


# ══════════════════════════════════════════════════════════
# EmptyState
# ══════════════════════════════════════════════════════════

class EmptyState(QFrame):
    action_clicked = pyqtSignal()

    def __init__(self, icon: str = "📋",
                 title: str = "لا توجد بيانات",
                 subtitle: str = "",
                 action_text: str = "",
                 style: str = "dashed",
                 color: str = "#10b981",
                 min_height: int = 80,
                 parent=None):
        super().__init__(parent)
        self._build(icon, title, subtitle, action_text, style, color, min_height)

    def _build(self, icon, title, subtitle, action_text, style, color, min_h):
        _bg, _border = _card_colors(color)

        border_style = {
            "dashed": "dashed", "solid": "solid", "plain": "none"
        }.get(style, "dashed")

        self.setStyleSheet(f"""
            QFrame {{
                background: {_bg};
                border: 2px {border_style} {_border};
                border-radius: 10px;
            }}
        """)
        self.setMinimumHeight(min_h)

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(6)
        lay.setContentsMargins(20, 16, 20, 16)

        base = _base()

        if icon:
            lbl_icon = QLabel(icon)
            lbl_icon.setAlignment(Qt.AlignCenter)
            lbl_icon.setStyleSheet(
                f"background:transparent; border:none; font-size:{fs(base,+8)}pt;"
            )
            lay.addWidget(lbl_icon)

        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet(
            f"color:{color}; font-weight:700; font-size:{fs(base,+1)}pt;"
            "background:transparent; border:none;"
        )
        lay.addWidget(lbl_title)

        if subtitle:
            lbl_sub = QLabel(subtitle)
            lbl_sub.setAlignment(Qt.AlignCenter)
            lbl_sub.setStyleSheet(
                f"color:{_C['text_muted']}; font-size:{fs(base,-1)}pt;"
                "background:transparent; border:none;"
            )
            lay.addWidget(lbl_sub)

        if action_text:
            btn = _make_btn(action_text, "success")
            btn.setFixedWidth(140)
            btn.clicked.connect(self.action_clicked.emit)
            lay.addWidget(btn, alignment=Qt.AlignCenter)


# ══════════════════════════════════════════════════════════
# BadgeLabel
# ══════════════════════════════════════════════════════════

class BadgeLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self._apply_base_style()

    def _apply_base_style(self, text_color="#555", bg="#f5f5f5", border="#e0e0e0"):
        base = _base()
        self.setStyleSheet(
            f"font-weight:700; font-size:{fs(base,-1)}pt;"
            f"padding:3px 12px; border-radius:20px;"
            f"color:{text_color}; background:{bg}; border:1.5px solid {border};"
        )

    def set_badge(self, text: str, text_color: str = "#555",
                  bg: str = "#f5f5f5", border: str = "#e0e0e0"):
        self.setText(text)
        self._apply_base_style(text_color, bg, border)

    def clear_badge(self):
        self.setText("")
        self._apply_base_style()


# ══════════════════════════════════════════════════════════
# InfoRow
# ══════════════════════════════════════════════════════════

class InfoRow(QWidget):
    def __init__(self, separator: str = "  ·  ", parent=None):
        super().__init__(parent)
        self._separator = separator
        self._lbl = QLabel()
        base = _base()
        self._lbl.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{fs(base,-1)}pt;"
            "background:transparent; border:none;"
        )
        self._lbl.setWordWrap(True)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._lbl)

    def set_parts(self, parts: list):
        filtered = [str(p) for p in parts if p]
        self._lbl.setText(self._separator.join(filtered) if filtered else "")

    def set_text(self, text: str):
        self._lbl.setText(text)

    def label(self) -> QLabel:
        return self._lbl


# ══════════════════════════════════════════════════════════
# ActionToolbar
# ══════════════════════════════════════════════════════════

class ActionToolbar(QWidget):
    def __init__(self, spacing: int = 6, parent=None):
        super().__init__(parent)
        self._spacing = spacing
        self._has_danger = False
        self._build()

    def _build(self):
        self.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(self._spacing)

        self._left_lay = QHBoxLayout()
        self._left_lay.setSpacing(self._spacing)

        self._right_lay = QHBoxLayout()
        self._right_lay.setSpacing(self._spacing)

        lay.addLayout(self._left_lay)
        lay.addStretch()

        self._sep = QFrame()
        self._sep.setFrameShape(QFrame.VLine)
        self._sep.setFixedWidth(1)
        self._sep.setStyleSheet(
            f"background:{_C['border_med']}; border:none; margin:4px 0;"
        )
        self._sep.setVisible(False)
        lay.addWidget(self._sep)

        lay.addLayout(self._right_lay)

    def add_action(self, text: str, style: str = "normal",
                   callback=None, enabled: bool = True) -> QPushButton:
        btn = _make_btn(text, style)
        btn.setEnabled(enabled)
        if callback:
            btn.clicked.connect(callback)
        self._left_lay.addWidget(btn)
        return btn

    def add_danger(self, text: str, callback=None,
                   enabled: bool = True) -> QPushButton:
        btn = _make_btn(text, "danger")
        btn.setEnabled(enabled)
        if callback:
            btn.clicked.connect(callback)
        self._right_lay.addWidget(btn)
        self._sep.setVisible(True)
        self._has_danger = True
        return btn

    def add_separator(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"background:{_C['border']}; border:none; margin:4px 0;")
        self._left_lay.addWidget(sep)


# ══════════════════════════════════════════════════════════
# CollapsibleCard
# ══════════════════════════════════════════════════════════

class CollapsibleCard(QFrame):
    toggled = pyqtSignal(bool)

    def __init__(self, title: str = "", expanded: bool = True,
                 accent: str = None, parent=None):
        super().__init__(parent)
        self._expanded = expanded
        self._accent   = accent or _C['accent']
        self._title    = title
        self._build(title)

    def _build(self, title):
        self.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_surface']};
                border: 1px solid {_C['border']};
                border-radius: 10px;
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._header_btn = QPushButton()
        self._header_btn.setCursor(Qt.PointingHandCursor)
        self._header_btn.clicked.connect(self._toggle)
        self._update_header_style()
        root.addWidget(self._header_btn)

        self._divider = QFrame()
        self._divider.setFrameShape(QFrame.HLine)
        self._divider.setFixedHeight(1)
        self._divider.setStyleSheet(
            f"background:{_C['border']}; border:none; margin:0;"
        )
        self._divider.setVisible(self._expanded)
        root.addWidget(self._divider)

        self._content_widget = QWidget()
        self._content_widget.setStyleSheet("background:transparent;")
        self.content_layout = QVBoxLayout(self._content_widget)
        self.content_layout.setContentsMargins(12, 10, 12, 12)
        self.content_layout.setSpacing(8)
        self._content_widget.setVisible(self._expanded)
        root.addWidget(self._content_widget)

        self._update_header_text()

    def _update_header_style(self):
        base = _base()
        self._header_btn.setStyleSheet(f"""
            QPushButton {{
                background: {_C['bg_surface_2']};
                border: none;
                border-radius: 10px 10px 0 0;
                padding: 10px 14px;
                text-align: right;
                font-weight: 700;
                font-size: {fs(base, 0)}pt;
                color: {_C['text_sec']};
            }}
            QPushButton:hover {{
                background: {_C['bg_hover']};
                color: {_C['text_primary']};
            }}
        """)

    def _update_header_text(self):
        arrow = "▼" if self._expanded else "▶"
        self._header_btn.setText(f"{arrow}   {self._title}")

    def _toggle(self):
        self._expanded = not self._expanded
        self._content_widget.setVisible(self._expanded)
        self._divider.setVisible(self._expanded)
        self._update_header_text()
        if self._expanded:
            self._header_btn.setStyleSheet(
                self._header_btn.styleSheet().replace(
                    "border-radius: 10px;", "border-radius: 10px 10px 0 0;"
                )
            )
        else:
            self._header_btn.setStyleSheet(
                self._header_btn.styleSheet().replace(
                    "border-radius: 10px 10px 0 0;", "border-radius: 10px;"
                )
            )
        self.toggled.emit(self._expanded)

    def set_expanded(self, expanded: bool):
        if self._expanded != expanded:
            self._toggle()


# ══════════════════════════════════════════════════════════
# دالة مساعدة لبناء الأزرار
# ══════════════════════════════════════════════════════════

def _make_btn(text: str, style: str = "normal") -> QPushButton:
    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    base = _base()
    btn_h = base * 2 + 8

    _common = f"""
        font-size: {fs(base, 0)}pt;
        border-radius: 6px;
        padding: 0 14px;
        min-height: {btn_h}px;
    """

    styles = {
        "primary": f"""
            QPushButton {{
                background: {_C['accent_light']}; color: {_C['accent_text']};
                border: 1.5px solid {_C['accent_mid']}; {_common}
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {_C['accent_mid']}; color: {_C['accent_text']};
                border-color: {_C['accent']};
            }}
            QPushButton:disabled {{
                background: {_C['bg_surface_2']}; color: {_C['text_disabled']};
                border-color: {_C['border']};
            }}
        """,
        "success": f"""
            QPushButton {{
                background: #ecfdf5; color: #065f46;
                border: 1.5px solid #6ee7b7; {_common}
                font-weight: 700;
            }}
            QPushButton:hover {{ background: #d1fae5; border-color: #34d399; }}
            QPushButton:disabled {{
                background: {_C['bg_surface_2']}; color: {_C['text_disabled']};
                border-color: {_C['border']};
            }}
        """,
        "danger": f"""
            QPushButton {{
                background: #fef2f2; color: #dc2626;
                border: 1.5px solid #fca5a5; {_common}
            }}
            QPushButton:hover {{ background: #fee2e2; border-color: #f87171; }}
            QPushButton:disabled {{
                background: {_C['bg_surface_2']}; color: {_C['text_disabled']};
                border-color: {_C['border']};
            }}
        """,
        "ghost": f"""
            QPushButton {{
                background: transparent; color: {_C['text_sec']};
                border: 1.5px solid {_C['border_med']}; {_common}
            }}
            QPushButton:hover {{
                background: {_C['accent_light']}; color: {_C['accent_text']};
                border-color: {_C['accent_mid']};
            }}
            QPushButton:disabled {{
                background: {_C['bg_surface_2']}; color: {_C['text_disabled']};
                border-color: {_C['border']};
            }}
        """,
        "normal": f"""
            QPushButton {{
                background: {_C['bg_surface_2']}; color: {_C['text_sec']};
                border: 1px solid {_C['border']}; {_common}
            }}
            QPushButton:hover {{ background: {_C['bg_hover']}; border-color: {_C['border_med']}; }}
            QPushButton:disabled {{
                background: {_C['bg_surface_2']}; color: {_C['text_disabled']};
            }}
        """,
    }
    btn.setStyleSheet(styles.get(style, styles["normal"]))
    return btn


# ══════════════════════════════════════════════════════════
# DetailHeader — محسّن مع set_customer_name
# ══════════════════════════════════════════════════════════

class DetailHeader(QFrame):
    """
    هيدر موحد لصفحات التفاصيل.

    الجديد: set_customer_name() — يعرض اسم العميل في سطر مخصص
    تحت العنوان الرئيسي، بخط واضح ومع word-wrap.
    """

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

        # ── صف 2: اسم العميل — سطر مخصص، واسع ومقروء ──
        self._lbl_customer = QLabel("")
        self._lbl_customer.setWordWrap(True)
        self._lbl_customer.setStyleSheet(
            f"color:{_C['text_sec']}; font-size:{fs(base, +1)}pt; font-weight:600;"
            "background:transparent; border:none;"
        )
        self._lbl_customer.setVisible(False)
        top_lay.addWidget(self._lbl_customer)

        # ── صف 3: التفاصيل الثانوية (هاتف · مدينة) ──
        self._info_row = InfoRow(separator="  ·  ")
        top_lay.addWidget(self._info_row)

        root.addWidget(top_section)

        # ── فاصل ──
        div1 = self._make_divider()
        root.addWidget(div1)

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
        div2 = self._make_divider()
        root.addWidget(div2)

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
        """
        يعرض اسم العميل في سطر مخصص تحت العنوان الرئيسي.
        الاسم بيظهر كامل مع word-wrap — مش بيتقطع بنقط.
        """
        if name:
            self._lbl_customer.setText(name)
            self._lbl_customer.setVisible(True)
        else:
            self._lbl_customer.setVisible(False)

    def set_info(self, parts: list):
        """التفاصيل الثانوية: هاتف، مدينة، إلخ."""
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