"""
ui/main_window.py
=================
النافذة الرئيسية — Sidebar Navigation + Content Area.

التحديثات:
  - أيقونة ونص الـ Sidebar أكبر — عبر setObjectName + stylesheet في app_settings
  - الـ Sidebar قابل للطي والفرد بزر Toggle (◀ / ▶)

الأقسام:
  📊 حساب التكلفة  →  CostingSection
  💰 التسعير       →  PricingSection
  🏦 الحسابات     →  AccountingTab
  📦 المخزن        →  InventoryTab
  ⚙️ الإعدادات    →  SettingsDialog
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame,
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve

from ui.tabs.costing_section      import CostingSection
from ui.tabs.pricing_section      import PricingSection
from ui.tabs.accounting_section   import AccountingTab
from ui.tabs.inventory_section    import InventoryTab
from ui.settings_dialog           import SettingsDialog


SIDEBAR_EXPANDED_WIDTH  = 155
SIDEBAR_COLLAPSED_WIDTH = 60
BTN_HEIGHT              = 76


# ══════════════════════════════════════════════════════════
# زر الـ Sidebar
# ══════════════════════════════════════════════════════════

class _NavButton(QPushButton):
    def __init__(self, icon: str, label: str, parent=None):
        super().__init__(parent)
        self._icon  = icon
        self._label = label
        self.setCheckable(True)
        self.setMinimumHeight(BTN_HEIGHT)
        self.setFixedWidth(SIDEBAR_EXPANDED_WIDTH)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()
        self._build_content()

    def _build_content(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignCenter)

        # objectName يسمح للـ stylesheet في app_settings يستهدفهم بدقة
        self._ico_lbl = QLabel(self._icon)
        self._ico_lbl.setObjectName("nav_icon")
        self._ico_lbl.setAlignment(Qt.AlignCenter)

        self._txt_lbl = QLabel(self._label)
        self._txt_lbl.setObjectName("nav_label")
        self._txt_lbl.setAlignment(Qt.AlignCenter)
        self._txt_lbl.setWordWrap(True)

        layout.addWidget(self._ico_lbl)
        layout.addWidget(self._txt_lbl)

    def set_collapsed(self, collapsed: bool):
        self._txt_lbl.setVisible(not collapsed)
        self.setFixedWidth(
            SIDEBAR_COLLAPSED_WIDTH if collapsed else SIDEBAR_EXPANDED_WIDTH
        )

    def _update_style(self):
        if self.isChecked():
            self.setStyleSheet("""
                QPushButton {
                    background: #e8f4fd;
                    border: none;
                    border-left: 4px solid #1565c0;
                    border-radius: 0px;
                    color: #1565c0;
                    font-weight: bold;
                }
                QPushButton:hover { background: #d6ebfb; }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    border-left: 4px solid transparent;
                    border-radius: 0px;
                    color: #555;
                }
                QPushButton:hover { background: #f5f5f5; color: #1565c0; }
            """)

    def setChecked(self, checked):
        super().setChecked(checked)
        self._update_style()


# ══════════════════════════════════════════════════════════
# زر الطي / الفرد
# ══════════════════════════════════════════════════════════

class _ToggleButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._collapsed = False
        self.setFixedHeight(34)
        self.setCursor(Qt.PointingHandCursor)
        self._refresh()
        self.setStyleSheet("""
            QPushButton {
                background: #e8eaf6;
                border: none;
                border-top: 1px solid #e0e0e0;
                color: #3949ab;
                font-size: 14pt;
                font-weight: bold;
            }
            QPushButton:hover { background: #c5cae9; }
        """)

    def _refresh(self):
        self.setText("◀" if not self._collapsed else "▶")
        self.setToolTip(
            "طي الشريط الجانبي" if not self._collapsed
            else "فرد الشريط الجانبي"
        )

    def toggle_state(self) -> bool:
        self._collapsed = not self._collapsed
        self._refresh()
        return self._collapsed


# ══════════════════════════════════════════════════════════
# Sidebar
# ══════════════════════════════════════════════════════════

class _Sidebar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._collapsed = False
        self.setFixedWidth(SIDEBAR_EXPANDED_WIDTH)
        self.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border-right: 1px solid #e0e0e0;
            }
        """)
        self._buttons: list[_NavButton] = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._header = QLabel("ERP\nالتكاليف")
        self._header.setObjectName("sidebar_header")
        self._header.setAlignment(Qt.AlignCenter)
        self._header.setFixedHeight(72)
        self._header.setStyleSheet("""
            QLabel#sidebar_header {
                background: #1565c0;
                color: white;
                font-size: 15pt;
                font-weight: bold;
                border: none;
                padding: 8px;
            }
        """)
        layout.addWidget(self._header)
        layout.addSpacing(8)

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

        self._toggle_btn = _ToggleButton()
        self._toggle_btn.clicked.connect(self._on_toggle)
        layout.addWidget(self._toggle_btn)

    def _on_toggle(self):
        self._collapsed = self._toggle_btn.toggle_state()
        target = (
            SIDEBAR_COLLAPSED_WIDTH if self._collapsed
            else SIDEBAR_EXPANDED_WIDTH
        )

        self._anim_min = QPropertyAnimation(self, b"minimumWidth")
        self._anim_min.setDuration(200)
        self._anim_min.setEasingCurve(QEasingCurve.InOutQuad)
        self._anim_min.setStartValue(self.width())
        self._anim_min.setEndValue(target)

        self._anim_max = QPropertyAnimation(self, b"maximumWidth")
        self._anim_max.setDuration(200)
        self._anim_max.setEasingCurve(QEasingCurve.InOutQuad)
        self._anim_max.setStartValue(self.width())
        self._anim_max.setEndValue(target)

        self._anim_min.start()
        self._anim_max.start()

        for btn in self._buttons:
            btn.set_collapsed(self._collapsed)

        if self._collapsed:
            self._header.setText("ERP")
            self._header.setStyleSheet("""
                QLabel#sidebar_header {
                    background: #1565c0;
                    color: white;
                    font-size: 11pt;
                    font-weight: bold;
                    border: none;
                    padding: 4px;
                }
            """)
        else:
            self._header.setText("ERP\nالتكاليف")
            self._header.setStyleSheet("""
                QLabel#sidebar_header {
                    background: #1565c0;
                    color: white;
                    font-size: 15pt;
                    font-weight: bold;
                    border: none;
                    padding: 8px;
                }
            """)

    def get_buttons(self) -> list[_NavButton]:
        return self._buttons


# ══════════════════════════════════════════════════════════
# النافذة الرئيسية
# ══════════════════════════════════════════════════════════

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