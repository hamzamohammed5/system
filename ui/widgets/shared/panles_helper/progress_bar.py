"""
ui/widgets/shared/panles_helper/progress_bar.py
================================================
ProgressBar — شريط تقدم موحد مع تسمية ونسبة مئوية.

يُستخدم في:
  - تقارير الإنتاج
  - لوحات الإحصاء
  - أي مكان يحتاج عرض نسبة مئوية بصرياً

الاستخدام:
    bar = ProgressBar(label="الإنجاز", color="#1565c0")
    layout.addWidget(bar)
    bar.set_value(75)       # → 75%
    bar.set_value(0, "─")   # reset
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.app_settings import _C, fs
from .colors_and_base import _base


class ProgressBar(QWidget):
    """
    شريط تقدم موحد: [label]  [████░░░]  [75%]

    المعاملات:
        label     : نص التسمية
        color     : لون الشريط الممتلئ
        height    : ارتفاع الشريط (px)
        show_pct  : هل تظهر النسبة المئوية
        compact   : نسخة مضغوطة
    """

    def __init__(self, label: str = "",
                 color: str = "#1565c0",
                 height: int = 8,
                 show_pct: bool = True,
                 compact: bool = False,
                 parent=None):
        super().__init__(parent)
        self._color    = color
        self._height   = height
        self._show_pct = show_pct
        self._compact  = compact
        self._value    = 0
        self._build(label)

    def _build(self, label: str):
        self.setStyleSheet("background: transparent;")
        base = _base()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(3)

        # صف العنوان + النسبة
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        if label:
            self._lbl_title = QLabel(label)
            self._lbl_title.setStyleSheet(
                f"color: {_C['text_sec']}; font-size: {fs(base, -1)}pt;"
                "background: transparent; border: none;"
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
                f"color: {self._color}; background: transparent; border: none;"
            )
            self._lbl_pct.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            top_row.addWidget(self._lbl_pct)

        root.addLayout(top_row)

        # الشريط
        track = QFrame()
        track.setFixedHeight(self._height)
        track.setStyleSheet(f"""
            QFrame {{
                background: {_C['border']};
                border-radius: {self._height // 2}px;
                border: none;
            }}
        """)

        track_lay = QHBoxLayout(track)
        track_lay.setContentsMargins(0, 0, 0, 0)
        track_lay.setSpacing(0)

        self._fill = QFrame()
        self._fill.setFixedHeight(self._height)
        self._fill.setStyleSheet(f"""
            QFrame {{
                background: {self._color};
                border-radius: {self._height // 2}px;
                border: none;
            }}
        """)
        self._fill.setFixedWidth(0)
        track_lay.addWidget(self._fill)
        track_lay.addStretch()

        self._track = track
        root.addWidget(track)

    def set_value(self, value: float, label: str = None):
        """
        يحدّث قيمة الشريط.

        value : قيمة من 0 إلى 100
        label : نص مخصص بدل النسبة (مثل "─" أو "N/A")
        """
        self._value = max(0.0, min(100.0, value))

        # عرض الشريط
        total_w = self._track.width()
        fill_w  = int(total_w * self._value / 100) if total_w > 0 else 0
        self._fill.setFixedWidth(fill_w)

        # النص
        if self._show_pct:
            if label is not None:
                self._lbl_pct.setText(label)
            else:
                self._lbl_pct.setText(f"{self._value:.0f}%")

        # لون ديناميكي حسب النسبة
        self._update_color()

    def _update_color(self):
        if self._value >= 90:
            color = "#2e7d32"  # أخضر
        elif self._value >= 60:
            color = self._color
        elif self._value >= 30:
            color = "#f59e0b"  # برتقالي
        else:
            color = "#ef4444"  # أحمر

        self._fill.setStyleSheet(f"""
            QFrame {{
                background: {color};
                border-radius: {self._height // 2}px;
                border: none;
            }}
        """)
        if self._show_pct:
            self._lbl_pct.setStyleSheet(
                f"color: {color}; background: transparent; border: none;"
            )

    def set_color(self, color: str):
        """يغير لون الشريط."""
        self._color = color
        self._update_color()

    def value(self) -> float:
        return self._value

    def reset(self):
        self.set_value(0, "─")

    def resizeEvent(self, event):
        """يعيد حساب عرض الشريط عند تغيير الحجم."""
        super().resizeEvent(event)
        total_w = self._track.width()
        if total_w > 0:
            fill_w = int(total_w * self._value / 100)
            self._fill.setFixedWidth(fill_w)


class MultiProgressBar(QWidget):
    """
    أشرطة تقدم متعددة في عمود.

    الاستخدام:
        bars = MultiProgressBar()
        bars.add_bar("الإنتاج",  75, "#1565c0")
        bars.add_bar("المبيعات", 60, "#2e7d32")
        bars.add_bar("الإرجاع",  10, "#ef4444")
        layout.addWidget(bars)
    """

    def __init__(self, spacing: int = 8, parent=None):
        super().__init__(parent)
        self._bars: list[ProgressBar] = []
        self.setStyleSheet("background: transparent;")
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(spacing)

    def add_bar(self, label: str, value: float = 0,
                color: str = "#1565c0") -> ProgressBar:
        bar = ProgressBar(label=label, color=color)
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