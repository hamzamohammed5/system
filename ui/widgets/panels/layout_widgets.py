"""
ui/widgets/panels/layout_widgets.py
=====================================
CardGrid + CollapsibleCard — Widgets تنظيم Layout.

التغييرات:
  - [إصلاح imports] استبدال ui.theme/ui.font بـ ui.app_settings
  - [إصلاح imports] استبدال ..styles بـ ..theme.styles
"""
from PyQt5.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QGridLayout,
    QPushButton, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal

from ...font import fs, get_font_size
from ...theme import _C
from ..theme.builders   import h_divider
from ..theme.card_styles import card_style

# ══════════════════════════════════════════════════════════
# CardGrid
# ══════════════════════════════════════════════════════════

class CardGrid(QWidget):
    """شبكة بطاقات بعدد أعمدة ثابت — تملأ الصفوف تلقائياً."""

    def __init__(self, cols: int = 4, spacing: int = 10, parent=None):
        super().__init__(parent)
        self._cols  = cols
        self._count = 0
        self.setStyleSheet("background:transparent;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._grid = QGridLayout(self)
        self._grid.setSpacing(spacing)
        self._grid.setContentsMargins(0, 0, 0, 0)

        for c in range(cols):
            self._grid.setColumnStretch(c, 1)

    def add_widget(self, widget: QWidget):
        row = self._count // self._cols
        col = self._count % self._cols
        self._grid.addWidget(widget, row, col)
        self._count += 1

    def clear(self):
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._count = 0

    @classmethod
    def from_widgets(cls, widgets: list, cols: int = 4,
                     spacing: int = 10) -> "CardGrid":
        grid = cls(cols=cols, spacing=spacing)
        for w in widgets:
            grid.add_widget(w)
        return grid


# ══════════════════════════════════════════════════════════
# CollapsibleCard
# ══════════════════════════════════════════════════════════

class CollapsibleCard(QFrame):
    """
    بطاقة قابلة للطي مع header زر ومحتوى قابل للإخفاء.

    Signals:
        toggled(bool) — يُطلق عند تغيير حالة التوسع
    """

    toggled = pyqtSignal(bool)

    def __init__(self, title: str = "", expanded: bool = True,
                 accent: str = None, parent=None):
        super().__init__(parent)
        self._expanded = expanded
        self._accent   = accent or _C['accent']
        self._title    = title
        self._build(title)

    def _build(self, title: str):
        self.setStyleSheet(card_style())

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._header_btn = QPushButton()
        self._header_btn.setCursor(Qt.PointingHandCursor)
        self._header_btn.clicked.connect(self._toggle)
        self._update_header_style()
        root.addWidget(self._header_btn)

        self._divider = h_divider()
        self._divider.setVisible(self._expanded)
        root.addWidget(self._divider)

        self._content_widget = QWidget()
        self._content_widget.setStyleSheet("background:transparent;")
        self.content_layout  = QVBoxLayout(self._content_widget)
        self.content_layout.setContentsMargins(12, 10, 12, 12)
        self.content_layout.setSpacing(8)
        self._content_widget.setVisible(self._expanded)
        root.addWidget(self._content_widget)

        self._update_header_text()

    def _update_header_style(self):
        base = get_font_size()
        self._header_btn.setStyleSheet(f"""
            QPushButton {{
                background:{_C['bg_surface_2']};
                border:none;
                border-radius:10px 10px 0 0;
                padding:10px 14px;
                text-align:right;
                font-weight:700;
                font-size:{fs(base, 0)}pt;
                color:{_C['text_sec']};
            }}
            QPushButton:hover {{
                background:{_C['bg_hover']};
                color:{_C['text_primary']};
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
        self.toggled.emit(self._expanded)

    def set_expanded(self, expanded: bool):
        if self._expanded != expanded:
            self._toggle()

    @property
    def is_expanded(self) -> bool:
        return self._expanded