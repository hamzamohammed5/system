"""
ui/widgets/panels/collapsible_card.py
=================================================
CollapsibleCard — بطاقة قابلة للطي/التوسع.
"""
from PyQt5.QtWidgets import QWidget, QFrame, QVBoxLayout, QPushButton
from PyQt5.QtCore    import Qt, pyqtSignal

from ui.app_settings import _C, fs
from ui.app_settings import get_font_size
from ..theme.styles import h_divider
from ..theme.styles   import card_style


class CollapsibleCard(QFrame):
    """
    بطاقة قابلة للطي مع header زر وmحتوى قابل للإخفاء.

    الاستخدام:
        card = CollapsibleCard("تفاصيل إضافية", expanded=False)
        card.content_layout.addWidget(my_widget)
        layout.addWidget(card)

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