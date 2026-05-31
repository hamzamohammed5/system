"""
ui/widgets/components/progress.py
====================================
ProgressBar + MultiProgressBar.

مستخرج من components/label.py.
"""

from PyQt5.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont

from ui.theme import _C
from ui.font  import fs, get_font_size
from ..core.colors import status_colors


class ProgressBar(QWidget):
    """شريط تقدم: [label] [████░░░] [75%]"""

    def __init__(self, label: str = "", color: str = None,
                 height: int = 8, show_pct: bool = True,
                 compact: bool = False, parent=None):
        super().__init__(parent)
        self._color    = color or _C.get("accent")
        self._height   = height
        self._show_pct = show_pct
        self._value    = 0.0
        self._build(label)

    def _build(self, label: str):
        self.setStyleSheet("background:transparent;")
        base = get_font_size()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(3)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        if label:
            self._lbl_title = QLabel(label)
            self._lbl_title.setStyleSheet(
                f"color:{_C['text_sec']}; font-size:{fs(base, -1)}pt;"
                "background:transparent; border:none;"
            )
            top_row.addWidget(self._lbl_title)

        top_row.addStretch()

        if self._show_pct:
            self._lbl_pct = QLabel("0%")
            f = QFont()
            f.setPointSize(fs(base, -1))
            f.setBold(True)
            self._lbl_pct.setFont(f)
            self._lbl_pct.setStyleSheet(
                f"color:{self._color}; background:transparent; border:none;"
            )
            self._lbl_pct.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            top_row.addWidget(self._lbl_pct)

        root.addLayout(top_row)

        track = QFrame()
        track.setFixedHeight(self._height)
        track.setStyleSheet(f"""
            QFrame {{
                background:{_C['border']}; border-radius:{self._height // 2}px; border:none;
            }}
        """)

        track_lay = QHBoxLayout(track)
        track_lay.setContentsMargins(0, 0, 0, 0)
        track_lay.setSpacing(0)

        self._fill = QFrame()
        self._fill.setFixedHeight(self._height)
        self._fill.setStyleSheet(f"""
            QFrame {{
                background:{self._color}; border-radius:{self._height // 2}px; border:none;
            }}
        """)
        self._fill.setFixedWidth(0)
        track_lay.addWidget(self._fill)
        track_lay.addStretch()

        self._track = track
        root.addWidget(track)

    def set_value(self, value: float, label: str = None):
        self._value = max(0.0, min(100.0, value))
        total_w = self._track.width()
        fill_w  = int(total_w * self._value / 100) if total_w > 0 else 0
        self._fill.setFixedWidth(fill_w)

        if self._show_pct:
            self._lbl_pct.setText(label if label is not None else f"{self._value:.0f}%")

        self._update_color()

    def _update_color(self):
        s_success = status_colors("success")
        s_warning = status_colors("warning")
        s_danger  = status_colors("danger")

        if self._value >= 90:
            color = s_success["fg"]
        elif self._value >= 60:
            color = self._color
        elif self._value >= 30:
            color = s_warning["fg"]
        else:
            color = s_danger["fg"]

        self._fill.setStyleSheet(f"""
            QFrame {{
                background:{color}; border-radius:{self._height // 2}px; border:none;
            }}
        """)
        if self._show_pct:
            self._lbl_pct.setStyleSheet(
                f"color:{color}; background:transparent; border:none;"
            )

    def set_color(self, color: str):
        self._color = color
        self._update_color()

    def value(self) -> float:
        return self._value

    def reset(self):
        self.set_value(0, "─")

    def resizeEvent(self, event):
        """
        يُعيد حساب عرض الـ fill عند تغيير حجم الـ widget.
        التحقق من total_w > 0 مقصود — guard للحالة الأولى.
        """
        super().resizeEvent(event)
        total_w = self._track.width()
        if total_w > 0:
            self._fill.setFixedWidth(int(total_w * self._value / 100))


class MultiProgressBar(QWidget):
    """أشرطة تقدم متعددة في عمود."""

    def __init__(self, spacing: int = 8, parent=None):
        super().__init__(parent)
        self._bars: list[ProgressBar] = []
        self.setStyleSheet("background:transparent;")
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(spacing)

    def add_bar(self, label: str, value: float = 0,
                color: str = None) -> ProgressBar:
        bar = ProgressBar(label=label, color=color or _C.get("accent"))
        bar.set_value(value)
        self._lay.addWidget(bar)
        self._bars.append(bar)
        return bar

    def clear_bars(self):
        for bar in self._bars:
            self._lay.removeWidget(bar)
            bar.deleteLater()
        self._bars.clear()

    def update_bar(self, index: int, value: float):
        if 0 <= index < len(self._bars):
            self._bars[index].set_value(value)