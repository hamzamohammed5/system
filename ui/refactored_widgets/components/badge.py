"""
ui/widgets/shared/components/badge.py
========================================
BadgeLabel — شارة نصية ملونة.
StatusChip — شريحة حالة مع أيقونة وعدد.
"""
from PyQt5.QtWidgets import QLabel, QFrame, QHBoxLayout, QSizePolicy
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QFont

from ui.app_settings import _C, fs
from ui.widgets.shared.core.settings import get_base
from ui.widgets.shared.core.colors   import card_colors


class BadgeLabel(QLabel):
    """شارة نصية ملونة — تُستخدم في هيدر التفاصيل."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self._apply_style()

    def _apply_style(self, text_color: str = "#555",
                     bg: str = "#f5f5f5", border: str = "#e0e0e0"):
        base = get_base()
        self.setStyleSheet(
            f"font-weight:700; font-size:{fs(base,-1)}pt;"
            f"padding:3px 12px; border-radius:20px;"
            f"color:{text_color}; background:{bg}; border:1.5px solid {border};"
        )

    def set_badge(self, text: str, text_color: str = "#555",
                  bg: str = "#f5f5f5", border: str = "#e0e0e0"):
        self.setText(text)
        self._apply_style(text_color, bg, border)

    def clear_badge(self):
        self.setText("")
        self._apply_style()


class StatusChip(QFrame):
    """شريحة تعرض: أيقونة + اسم الحالة + العدد."""

    def __init__(self, icon: str = "", label: str = "",
                 count: int = 0, color: str = "#6b7280",
                 bg: str = None, border: str = None,
                 compact: bool = False, parent=None):
        super().__init__(parent)
        _bg, _bdr = card_colors(color)
        self._build(icon, label, count, color,
                    bg or _bg, border or _bdr, compact)

    def _build(self, icon, label, count, color, bg, border, compact):
        self.setStyleSheet(f"""
            QFrame {{
                background:{bg}; border:1px solid {border};
                border-radius:8px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay  = QHBoxLayout(self)
        base = get_base()
        m    = (10, 6, 10, 6) if compact else (12, 8, 12, 8)
        lay.setContentsMargins(*m)
        lay.setSpacing(8)

        if icon:
            lbl_icon = QLabel(icon)
            lbl_icon.setStyleSheet("background:transparent; border:none;")
            lay.addWidget(lbl_icon)

        lbl_label = QLabel(label)
        lbl_label.setStyleSheet(
            f"font-weight:600; color:{color}; background:transparent;"
            f"border:none; font-size:{fs(base,0)}pt;"
        )
        lay.addWidget(lbl_label, stretch=1)

        self._lbl_count = QLabel(str(count))
        f = QFont()
        f.setPointSize(fs(base, +1 if compact else +2))
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