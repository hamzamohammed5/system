"""
ui/widgets/components/status_chip.py
======================================
StatusChip + StatusCard.

مستخرج من components/stat_row.py.
"""

from PyQt5.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont

from ui.widgets.panels.themed_inputs import ThemedFrame

from ui.theme import _C
from ui.font  import fs, get_font_size
from ..core.colors import card_colors
from ..core.i18n import tr
from ..core.widget_mixin import WidgetMixin
from ui.constants import (
    SPACING_MD, SPACING_XS,
    STATUS_CHIP_MARGIN_COMPACT, STATUS_CHIP_MARGIN_NORMAL, STATUS_CHIP_BORDER_RADIUS, STATUS_CHIP_BORDER_W,
    STATUS_CARD_MARGIN, STATUS_CARD_SPACING, STATUS_CARD_BORDER_RADIUS, STATUS_CARD_BORDER_W,
)


class StatusChip(ThemedFrame, WidgetMixin):
    """شريحة حالة: أيقونة + اسم + عدد."""

    def __init__(self, icon: str = "", label: str = "", count: int = 0,
                 color: str = None, bg: str = None, border: str = None,
                 compact: bool = False, parent=None):
        super().__init__(parent)
        self._custom_color = color
        self._color  = color or _C["text_neutral"]
        self._custom_bg     = bg
        self._custom_border = border
        self._compact = compact
        self._build(icon, label, count, compact)
        self._init_widget_mixin(theme=True, font=True)
        self._refresh_style()

    def _build(self, icon, label, count, compact):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        m = STATUS_CHIP_MARGIN_COMPACT if compact else STATUS_CHIP_MARGIN_NORMAL
        lay = QHBoxLayout(self)
        lay.setContentsMargins(*m)
        lay.setSpacing(SPACING_MD)

        self._lbl_icon = None
        if icon:
            self._lbl_icon = QLabel(icon)
            self._lbl_icon.setStyleSheet("background:transparent; border:none;")
            lay.addWidget(self._lbl_icon)

        self._lbl_label = QLabel(label)
        lay.addWidget(self._lbl_label, stretch=1)

        self._lbl_count = QLabel(str(count))
        lay.addWidget(self._lbl_count)

    def _refresh_style(self, *_):
        if self._custom_color is None:
            self._color = _C["text_neutral"]
        _bg, _bdr = card_colors(self._color)
        if self._custom_bg:     _bg  = self._custom_bg
        if self._custom_border: _bdr = self._custom_border

        self.setStyleSheet(f"""
            QFrame {{
                background:{_bg}; border:{STATUS_CHIP_BORDER_W}px solid {_bdr};
                border-radius:{STATUS_CHIP_BORDER_RADIUS}px;
            }}
        """)

        base = get_font_size()

        self._lbl_label.setStyleSheet(
            f"font-weight:600; color:{self._color}; background:transparent;"
            f"border:none; font-size:{fs(base,0)}pt;"
        )

        f = QFont()
        f.setPointSize(fs(base, +1 if self._compact else +2))
        f.setBold(True)
        self._lbl_count.setFont(f)
        self._lbl_count.setStyleSheet(
            f"color:{self._color}; background:transparent; border:none;"
        )

    def set_count(self, count: int):
        self._lbl_count.setText(str(count))

    def count(self) -> int:
        try:
            return int(self._lbl_count.text())
        except ValueError:
            return 0


class StatusCard(ThemedFrame, WidgetMixin):
    """بطاقة حالة بسيطة — أيقونة + label + عدد كبير."""

    def __init__(self, icon: str = "", label: str = "",
                 value: str = None, color: str = None,
                 sub: str = "", parent=None):
        super().__init__(parent)
        self._custom_color = color
        self._color = color or _C["blue"]
        self._sub   = sub
        self._custom_value = value
        self._build(icon, label, value if value is not None else tr('dash'), sub)
        self._init_widget_mixin(theme=True, font=True, lang=True)
        self._refresh_style()

    def _build(self, icon, label, value, sub):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(*STATUS_CARD_MARGIN)
        lay.setSpacing(STATUS_CARD_SPACING)

        top = QHBoxLayout()

        self._lbl_icon = QLabel(icon)
        self._lbl_icon.setStyleSheet("background:transparent; border:none;")
        top.addWidget(self._lbl_icon)
        top.addStretch()

        self._lbl_value = QLabel(value)
        self._lbl_value.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        top.addWidget(self._lbl_value)
        lay.addLayout(top)

        self._lbl_title = QLabel(label)
        lay.addWidget(self._lbl_title)

        self._lbl_sub = None
        if sub:
            self._lbl_sub = QLabel(sub)
            lay.addWidget(self._lbl_sub)

    def _refresh_style(self, *_):
        if self._custom_color is None:
            self._color = _C["blue"]
        _bg, _bdr = card_colors(self._color)
        self.setStyleSheet(f"""
            QFrame {{
                background:{_bg}; border:{STATUS_CARD_BORDER_W}px solid {_bdr};
                border-radius:{STATUS_CARD_BORDER_RADIUS}px;
            }}
        """)

        base = get_font_size()

        f = QFont()
        f.setPointSize(fs(base, +5))
        f.setBold(True)
        self._lbl_value.setFont(f)
        self._lbl_value.setStyleSheet(
            f"color:{self._color}; background:transparent; border:none;"
        )

        self._lbl_title.setStyleSheet(
            f"color:{self._color}; font-weight:600; font-size:{fs(base,0)}pt;"
            "background:transparent; border:none;"
        )

        if self._lbl_sub:
            self._lbl_sub.setStyleSheet(
                f"color:{_C['text_muted']}; font-size:{fs(base,-1)}pt;"
                "background:transparent; border:none;"
            )

    def set_value(self, text: str):
        self._custom_value = text
        self._lbl_value.setText(text)

    def value_label(self) -> QLabel:
        return self._lbl_value

    def _refresh_lang(self, *_):
        if self._custom_value is None:
            self._lbl_value.setText(tr('dash'))


def make_status_chip(icon: str, label: str, count: int = 0,
                     color: str = None) -> StatusChip:
    return StatusChip(icon=icon, label=label, count=count, color=color or _C["text_neutral"])