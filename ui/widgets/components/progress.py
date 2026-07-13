"""
ui/widgets/components/progress.py
====================================
ProgressBar + MultiProgressBar.

مستخرج من components/label.py.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont

from ui.widgets.panels.themed_inputs import ThemedFrame

from ui.theme import _C
from ui.font  import fs, get_font_size
from ..core.colors import status_colors
from ..core.i18n import tr
from ..core.widget_mixin import WidgetMixin
from ui.constants import (
    SPACING_MD, PROGRESS_BAR_H, PROGRESS_TOP_SPACING,
)


class ProgressBar(QWidget, WidgetMixin):
    """شريط تقدم: [label] [████░░░] [75%]"""

    def __init__(self, label: str = "", color: str = None,
                 height: int = PROGRESS_BAR_H, show_pct: bool = True,
                 compact: bool = False, parent=None):
        super().__init__(parent)
        self._custom_color = color
        self._color    = color or _C.get("accent")
        self._height   = height
        self._show_pct = show_pct
        self._value    = 0.0
        self._label    = label
        self._build(label)
        self._init_widget_mixin(theme=True, font=True, lang=True)
        self._refresh_style()

    def _build(self, label: str):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(PROGRESS_TOP_SPACING)

        top_row = QHBoxLayout()
        top_row.setSpacing(SPACING_MD)

        self._lbl_title = None
        if label:
            self._lbl_title = QLabel(label)
            top_row.addWidget(self._lbl_title)

        top_row.addStretch()

        self._lbl_pct = None
        if self._show_pct:
            self._lbl_pct = QLabel(tr('progress_zero_pct'))
            self._lbl_pct.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            top_row.addWidget(self._lbl_pct)

        root.addLayout(top_row)

        track = ThemedFrame()
        track.setFixedHeight(self._height)

        track_lay = QHBoxLayout(track)
        track_lay.setContentsMargins(0, 0, 0, 0)
        track_lay.setSpacing(0)

        self._fill = ThemedFrame()
        self._fill.setFixedHeight(self._height)
        self._fill.setFixedWidth(0)
        track_lay.addWidget(self._fill)
        track_lay.addStretch()

        self._track = track
        root.addWidget(track)

    def _refresh_style(self, *_):
        if self._custom_color is None:
            self._color = _C.get("accent")

        self.setStyleSheet("background:transparent;")
        base = get_font_size()

        if self._lbl_title:
            self._lbl_title.setStyleSheet(
                f"color:{_C['text_sec']}; font-size:{fs(base, -1)}pt;"
                "background:transparent; border:none;"
            )

        if self._lbl_pct:
            f = QFont()
            f.setPointSize(fs(base, -1))
            f.setBold(True)
            self._lbl_pct.setFont(f)

        self._track.setStyleSheet(f"""
            QFrame {{
                background:{_C['border']}; border-radius:{self._height // 2}px; border:none;
            }}
        """)

        self._update_color()

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
        self._custom_color = color
        self._color = color
        self._update_color()

    def _refresh_lang(self, *_):
        if self._lbl_pct and self._value == 0:
            self._lbl_pct.setText(tr('progress_zero_pct'))

    def value(self) -> float:
        return self._value

    def reset(self):
        self.set_value(0, tr('amount_dash_placeholder'))

    def resizeEvent(self, event):
        """
        يُعيد حساب عرض الـ fill عند تغيير حجم الـ widget.
        التحقق من total_w > 0 مقصود — guard للحالة الأولى.
        """
        super().resizeEvent(event)
        total_w = self._track.width()
        if total_w > 0:
            self._fill.setFixedWidth(int(total_w * self._value / 100))


class MultiProgressBar(QWidget, WidgetMixin):
    """أشرطة تقدم متعددة في عمود."""

    def __init__(self, spacing: int = SPACING_MD, parent=None):
        super().__init__(parent)
        self._bars: list[ProgressBar] = []
        self.setStyleSheet("background:transparent;")
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(spacing)
        self._init_widget_mixin(theme=True, font=False, lang=False, data=False)

    def _refresh_style(self, *_):
        self.setStyleSheet("background:transparent;")

    def add_bar(self, label: str, value: float = 0,
                color: str = None) -> ProgressBar:
        from ui.theme import _C
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