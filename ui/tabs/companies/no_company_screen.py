"""
ui/widgets/shared/no_company_screen.py
=======================================
شاشة تظهر لما ما فيش شركة محددة بعد.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore    import Qt, pyqtSignal
from ui.app_settings import _C


class NoCompanyScreen(QWidget):
    """شاشة الترحيب — تظهر قبل اختيار شركة."""

    open_manager = pyqtSignal()  # لفتح نافذة إدارة الشركات

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(16)

        ico = QLabel("🏢")
        ico.setAlignment(Qt.AlignCenter)
        ico.setStyleSheet("font-size: 48pt; background: transparent;")
        lay.addWidget(ico)

        title = QLabel("مرحباً بك في نظام ERP")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"font-size: 18pt; font-weight: bold; color: {_C['text_primary']};"
        )
        lay.addWidget(title)

        sub = QLabel("اختر شركة من القائمة أعلاه للبدء\nأو أنشئ شركة جديدة")
        sub.setAlignment(Qt.AlignCenter)
        sub.setWordWrap(True)
        sub.setStyleSheet(f"font-size: 12pt; color: {_C['text_muted']};")
        lay.addWidget(sub)

        btn = QPushButton("➕  إنشاء شركة جديدة")
        btn.setFixedHeight(42)
        btn.setFixedWidth(220)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {_C['accent']}; color: white;
                font-weight: 600; font-size: 11pt;
                border: none; border-radius: 8px;
            }}
            QPushButton:hover {{ background: {_C['accent_hover']}; }}
        """)
        btn.clicked.connect(self.open_manager)
        lay.addWidget(btn, alignment=Qt.AlignCenter)