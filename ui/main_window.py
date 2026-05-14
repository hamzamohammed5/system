"""
ui/main_window.py
=================
النافذة الرئيسية — Sidebar Navigation + Content Area.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont

from ui.tabs.costing_section  import CostingSection
from ui.tabs.pricing_section  import PricingSection
from ui.tabs.accounting_section   import AccountingTab
from ui.tabs.inventory_section    import InventoryTab
from ui.settings_dialog       import SettingsDialog
from ui.app_settings import get_font_size


# ── ثوابت الـ Sidebar ──
_SIDEBAR_WIDTH   = 148   # عرض ثابت مناسب
_BTN_HEIGHT      = 72    # ارتفاع كل زر
_ICON_SIZE_PT    = 22    # حجم الأيقونة بـ pt (لا يتأثر بالخط)
_LABEL_SIZE_DELTA = 0    # حجم النص = base + هذا الرقم


class _NavButton(QPushButton):
    def __init__(self, icon: str, label: str, parent=None):
        super().__init__(parent)
        self._icon  = icon
        self._label = label
        self.setCheckable(True)
        self.setMinimumHeight(_BTN_HEIGHT)
        self.setFixedWidth(_SIDEBAR_WIDTH)
        self.setCursor(Qt.PointingHandCursor)
        self._build_content()
        self._update_style()

    def _build_content(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)

        ico = QLabel(self._icon)
        ico.setAlignment(Qt.AlignCenter)
        # الأيقونة بحجم ثابت كبير — لا تتأثر بإعداد الخط
        ico.setStyleSheet(
            f"font-size: {_ICON_SIZE_PT}pt;"
            " background: transparent;"
            " border: none;"
        )

        lbl = QLabel(self._label)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)
        # النص يأخذ حجم الخط الأساسي من الـ stylesheet العام
        lbl.setStyleSheet("background: transparent; border: none;")

        layout.addWidget(ico)
        layout.addWidget(lbl)

    def _update_style(self):
        if self.isChecked():
            self.setStyleSheet(f"""
                QPushButton {{
                    background: #e8f4fd;
                    border: none;
                    border-left: 4px solid #1565c0;
                    border-radius: 0px;
                    color: #1565c0;
                    font-weight: bold;
                    min-width: {_SIDEBAR_WIDTH}px;
                }}
                QPushButton:hover {{ background: #d6ebfb; }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    border-left: 4px solid transparent;
                    border-radius: 0px;
                    color: #555;
                    min-width: {_SIDEBAR_WIDTH}px;
                }}
                QPushButton:hover {{ background: #f5f5f5; color: #1565c0; }}
            """)

    def setChecked(self, checked):
        super().setChecked(checked)
        self._update_style()


class _Sidebar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(_SIDEBAR_WIDTH)
        self.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border-right: 1px solid #e0e0e0;
            }
        """)
        self._buttons = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── هيدر ──
        header = QLabel("ERP\nالتكاليف")
        header.setAlignment(Qt.AlignCenter)
        header.setFixedHeight(74)
        header.setStyleSheet("""
            QLabel {
                background: #1565c0;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                border: none;
                padding: 8px;
            }
        """)
        layout.addWidget(header)
        layout.addSpacing(6)

        nav_items = [
            ("📊", "حساب\nالتكلفة", "costing"),
            ("💰", "التسعير",        "pricing"),
            ("🏦", "الحسابات",       "accounting"),
            ("📦", "المخزن",         "inventory"),
        ]
        for icon, label, key in nav_items:
            btn = _NavButton(icon, label)
            btn.setProperty("nav_key", key)
            self._buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(sep)

        btn_settings = _NavButton("⚙️", "الإعدادات")
        btn_settings.setProperty("nav_key", "settings")
        self._buttons.append(btn_settings)
        layout.addWidget(btn_settings)

    def get_buttons(self):
        return self._buttons


class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self._app = app

        self.setWindowTitle("ERP — نظام إدارة التكاليف")
        self.resize(1200, 800)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumSize(900, 600)

        self._build()
        self._sidebar.get_buttons()[0].setChecked(True)
        self._stack.setCurrentIndex(0)

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._sidebar = _Sidebar()
        main_layout.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: #f9f9f9;")

        self._costing    = CostingSection()
        self._pricing    = PricingSection()
        self._accounting = AccountingTab()
        self._inventory  = InventoryTab()

        self._stack.addWidget(self._costing)
        self._stack.addWidget(self._pricing)
        self._stack.addWidget(self._accounting)
        self._stack.addWidget(self._inventory)

        main_layout.addWidget(self._stack, stretch=1)

        for btn in self._sidebar.get_buttons():
            btn.clicked.connect(lambda checked, b=btn: self._on_nav(b))

    def _on_nav(self, clicked_btn):
        for btn in self._sidebar.get_buttons():
            if btn is not clicked_btn:
                btn.setChecked(False)
        clicked_btn.setChecked(True)

        key = clicked_btn.property("nav_key")
        if key == "costing":
            self._stack.setCurrentIndex(0)
        elif key == "pricing":
            self._stack.setCurrentIndex(1)
        elif key == "accounting":
            self._stack.setCurrentIndex(2)
        elif key == "inventory":
            self._stack.setCurrentIndex(3)
        elif key == "settings":
            clicked_btn.setChecked(False)
            SettingsDialog(self._app, parent=self).exec_()