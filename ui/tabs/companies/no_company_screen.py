"""
ui/widgets/shared/no_company_screen.py
=======================================
شاشة تظهر لما ما فيش شركة محددة بعد.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore    import Qt, pyqtSignal
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.font import FS_BASE, FS_XL, fs
from ui.widgets.core.i18n import tr
from ui.constants import (
    NO_COMPANY_BTN_H, NO_COMPANY_BTN_W,
    NO_COMPANY_BTN_RADIUS, NO_COMPANY_SPACING,
)


class NoCompanyScreen(QWidget, WidgetMixin):
    """شاشة الترحيب — تظهر قبل اختيار شركة."""

    open_manager = pyqtSignal()  # لفتح نافذة إدارة الشركات

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_widget_mixin(data=False)
        self._build()
        self._refresh_style()
        self._refresh_lang()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(NO_COMPANY_SPACING)

        self._ico = QLabel()
        self._ico.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._ico)

        self._title = QLabel()
        self._title.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._title)

        self._sub = QLabel()
        self._sub.setAlignment(Qt.AlignCenter)
        self._sub.setWordWrap(True)
        lay.addWidget(self._sub)

        self._btn = QPushButton()
        self._btn.setFixedHeight(NO_COMPANY_BTN_H)
        self._btn.setFixedWidth(NO_COMPANY_BTN_W)
        self._btn.clicked.connect(self.open_manager)
        lay.addWidget(self._btn, alignment=Qt.AlignCenter)

    def _refresh_style(self, *_):
        from ui.theme import _C
        self._ico.setStyleSheet(
            f"font-size: {fs(FS_XL, 16)}px; background: transparent;"
        )
        self._title.setStyleSheet(
            f"font-size: {fs(FS_XL, 2)}px; font-weight: bold; color: {_C['text_primary']};"
        )
        self._sub.setStyleSheet(
            f"font-size: {FS_BASE}px; color: {_C['text_muted']};"
        )
        self._btn.setStyleSheet(f"""
            QPushButton {{
                background: {_C['accent']}; color: {_C['bg_input']};
                font-weight: 600; font-size: {FS_BASE}px;
                border: none; border-radius: {NO_COMPANY_BTN_RADIUS}px;
            }}
            QPushButton:hover {{ background: {_C['accent_hover']}; }}
        """)

    def _refresh_lang(self, *_):
        self._ico.setText(tr("company_selector_icon"))
        self._title.setText(tr("no_company_welcome"))
        self._sub.setText(tr("no_company_subtitle"))
        self._btn.setText(tr("no_company_add_btn"))