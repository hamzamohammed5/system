"""
ui/widgets/shared/panles_helper/status_chip.py
================================================
StatusChip — شريحة حالة ملونة للـ dashboards والقوائم.
make_stat_card_simple — بطاقة إحصائية بسيطة بدون كلاس.
make_status_chip — دالة سريعة لبناء StatusChip.

الاستخدام:
    chip = StatusChip("⏳", "انتظار", 5, "#f59e0b", "#fffbeb", "#fde68a")
    layout.addWidget(chip)
    chip.set_count(7)          # تحديث العدد

    frame, lbl_val = make_stat_card_simple("📋", "إجمالي", "─",
                                            color="#1565c0", bg="#e8f0fe", border="#90caf9")
"""

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont

from ui.app_settings import fs
from .colors_and_base import _base, _card_colors


# ══════════════════════════════════════════════════════════
# StatusChip
# ══════════════════════════════════════════════════════════

class StatusChip(QFrame):
    """
    شريحة تعرض: أيقونة + اسم الحالة + العدد.
    مثال:  ⏳  انتظار  |  5

    المعاملات:
        icon, label : أيقونة ونص الحالة
        count       : العدد (ممكن يتحدث بـ set_count)
        color, bg, border : ألوان التصميم
        compact     : حجم أصغر
    """

    def __init__(self, icon: str = "", label: str = "",
                 count: int = 0,
                 color: str = "#555", bg: str = "#f5f5f5",
                 border: str = "#e0e0e0",
                 compact: bool = False,
                 parent=None):
        super().__init__(parent)
        self._color   = color
        self._compact = compact
        self._build(icon, label, count, color, bg, border)

    def _build(self, icon, label, count, color, bg, border):
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 8px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay = QHBoxLayout(self)
        base = _base()

        if self._compact:
            lay.setContentsMargins(10, 6, 10, 6)
        else:
            lay.setContentsMargins(12, 8, 12, 8)
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
        f.setPointSize(fs(base, +2) if not self._compact else fs(base, +1))
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
# make_stat_card_simple — بطاقة إحصائية بسيطة (tuple)
# ══════════════════════════════════════════════════════════

def make_stat_card_simple(icon: str, title: str, value: str = "─",
                           color: str = "#1565c0",
                           bg: str = None, border: str = None,
                           sub: str = "") -> tuple:
    """
    يبني بطاقة إحصائية بسيطة.
    يرجع (QFrame, QLabel_value) عشان تقدر تحدّث القيمة بعدين.

    الاستخدام:
        frame, lbl = make_stat_card_simple("📋", "الطلبات", color="#1565c0")
        layout.addWidget(frame)
        lbl.setText("15")
    """
    _bg, _border = _card_colors(color)
    if bg:     _bg = bg
    if border: _border = border

    frame = QFrame()
    frame.setStyleSheet(f"""
        QFrame {{
            background: {_bg};
            border: 1px solid {_border};
            border-radius: 12px;
        }}
    """)
    frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    lay = QVBoxLayout(frame)
    lay.setContentsMargins(16, 14, 16, 14)
    lay.setSpacing(4)

    base = _base()

    # صف العنوان + الأيقونة
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

    # العنوان
    lbl_title = QLabel(title)
    lbl_title.setStyleSheet(
        f"color:{color}; font-weight:600; font-size:{fs(base,0)}pt;"
        "background:transparent; border:none;"
    )
    lay.addWidget(lbl_title)

    # النص الفرعي
    if sub:
        lbl_sub = QLabel(sub)
        lbl_sub.setStyleSheet(
            f"color:#6b7280; font-size:{fs(base,-1)}pt;"
            "background:transparent; border:none;"
        )
        lay.addWidget(lbl_sub)

    return frame, lbl_val


# ══════════════════════════════════════════════════════════
# make_status_chip — دالة سريعة
# ══════════════════════════════════════════════════════════

def make_status_chip(icon: str, label: str, count: int = 0,
                     color: str = "#555", bg: str = "#f5f5f5",
                     border: str = "#e0e0e0",
                     compact: bool = False) -> tuple:
    """
    يبني StatusChip ويرجع (QFrame, lbl_count).

    الاستخدام:
        chip, cnt_lbl = make_status_chip("⏳", "انتظار", 0,
                                          "#f59e0b", "#fffbeb", "#fde68a")
        layout.addWidget(chip)
        cnt_lbl.setText("7")
    """
    chip = StatusChip(icon, label, count, color, bg, border, compact)
    # نرجع الـ chip نفسه + label العدد للتحديث السهل
    cnt_lbl = chip._lbl_count
    return chip, cnt_lbl