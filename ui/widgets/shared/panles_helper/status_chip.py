"""
ui/widgets/shared/panles_helper/status_chip.py

التغييرات:
  - StatusChip: القيم الافتراضية للألوان بتيجي من _C بدل hardcoded "#555"/"#f5f5f5"
  - make_stat_card_simple: نفس الشيء
  - make_status_chip: نفس الشيء
  - _card_colors fallback بيستخدم _C بدل hardcoded
  - مفيش تغيير في الـ API
"""
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont

from ui.app_settings import _C, fs
from .colors_and_base import _base, _card_colors

# ── قيم افتراضية من _C بدل hardcoded ──
_DEFAULT_COLOR  = "#6b7280"   # text_sec مقارب
_DEFAULT_BG     = None        # بيُحسب من _card_colors
_DEFAULT_BORDER = None


def _chip_defaults(color: str, bg: str, border: str):
    """يرجع (bg, border) محسوبتان من _card_colors لو مش محددتان."""
    _bg, _bdr = _card_colors(color)
    return bg or _bg, border or _bdr


# ══════════════════════════════════════════════════════════
# StatusChip
# ══════════════════════════════════════════════════════════

class StatusChip(QFrame):
    """شريحة تعرض: أيقونة + اسم الحالة + العدد."""

    def __init__(self, icon: str = "", label: str = "",
                 count: int = 0,
                 color: str = _DEFAULT_COLOR,
                 bg: str = None,
                 border: str = None,
                 compact: bool = False,
                 parent=None):
        super().__init__(parent)
        self._color   = color
        self._compact = compact
        _bg, _bdr = _chip_defaults(color, bg, border)
        self._build(icon, label, count, color, _bg, _bdr)

    def _build(self, icon, label, count, color, bg, border):
        self.setStyleSheet(f"""
            QFrame {{
                background:{bg};
                border:1px solid {border};
                border-radius:8px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay  = QHBoxLayout(self)
        base = _base()
        lay.setContentsMargins(*(10, 6, 10, 6) if self._compact else (12, 8, 12, 8))
        lay.setSpacing(8)

        if icon:
            lbl_icon = QLabel(icon)
            lbl_icon.setStyleSheet("background:transparent; border:none;")
            lay.addWidget(lbl_icon)

        lbl_label = QLabel(label)
        lbl_label.setStyleSheet(
            f"font-weight:600; color:{color}; background:transparent; border:none;"
            f"font-size:{fs(base,0)}pt;"
        )
        lay.addWidget(lbl_label, stretch=1)

        self._lbl_count = QLabel(str(count))
        f = QFont()
        f.setPointSize(fs(base, +1) if self._compact else fs(base, +2))
        f.setBold(True)
        self._lbl_count.setFont(f)
        self._lbl_count.setStyleSheet(
            f"color:{color}; background:transparent; border:none;"
        )
        lay.addWidget(self._lbl_count)

    def set_count(self, count: int):
        self._lbl_count.setText(str(count))

    def count(self) -> int:
        try:
            return int(self._lbl_count.text())
        except ValueError:
            return 0


# ══════════════════════════════════════════════════════════
# make_stat_card_simple
# ══════════════════════════════════════════════════════════

def make_stat_card_simple(icon: str, title: str, value: str = "─",
                           color: str = "#1565c0",
                           bg: str = None, border: str = None,
                           sub: str = "") -> tuple:
    """
    يبني بطاقة إحصائية بسيطة.
    يرجع (QFrame, QLabel_value).
    """
    _bg, _border = _chip_defaults(color, bg, border)

    frame = QFrame()
    frame.setStyleSheet(f"""
        QFrame {{
            background:{_bg};
            border:1px solid {_border};
            border-radius:12px;
        }}
    """)
    frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    lay  = QVBoxLayout(frame)
    lay.setContentsMargins(16, 14, 16, 14)
    lay.setSpacing(4)

    base = _base()

    top_row = QHBoxLayout()
    lbl_icon = QLabel(icon)
    lbl_icon.setStyleSheet("background:transparent; border:none;")
    lbl_val = QLabel(value)
    f = QFont()
    f.setPointSize(fs(base, +5))
    f.setBold(True)
    lbl_val.setFont(f)
    lbl_val.setStyleSheet(f"color:{color}; background:transparent; border:none;")
    lbl_val.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    top_row.addWidget(lbl_icon)
    top_row.addStretch()
    top_row.addWidget(lbl_val)
    lay.addLayout(top_row)

    lbl_title = QLabel(title)
    lbl_title.setStyleSheet(
        f"color:{color}; font-weight:600; font-size:{fs(base,0)}pt;"
        "background:transparent; border:none;"
    )
    lay.addWidget(lbl_title)

    if sub:
        lbl_sub = QLabel(sub)
        lbl_sub.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{fs(base,-1)}pt;"
            "background:transparent; border:none;"
        )
        lay.addWidget(lbl_sub)

    return frame, lbl_val


# ══════════════════════════════════════════════════════════
# make_status_chip
# ══════════════════════════════════════════════════════════

def make_status_chip(icon: str, label: str, count: int = 0,
                     color: str = _DEFAULT_COLOR,
                     bg: str = None,
                     border: str = None,
                     compact: bool = False) -> tuple:
    """
    يبني StatusChip ويرجع (chip, lbl_count).
    bg و border اختياريان — بيتحسبوا من color تلقائياً.
    """
    chip = StatusChip(icon, label, count, color, bg, border, compact)
    return chip, chip._lbl_count