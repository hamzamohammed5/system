"""
ui/main_window.py  (محدَّث — مع قسم الطلبات + scroll لكل الـ sections)
=================
النافذة الرئيسية — Sidebar Navigation + Content Area.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame,
    QScrollArea,
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve

from ui.tabs.costing_section      import CostingSection
from ui.tabs.pricing_section      import PricingSection
from ui.tabs.accounting_section   import AccountingTab
from ui.tabs.inventory_section    import InventoryTab
from ui.tabs.design_section       import DesignSection
from ui.tabs.orders_section       import OrdersSection
from ui.settings_dialog           import SettingsDialog
from ui.app_settings              import get_font_size


SIDEBAR_EXPANDED_WIDTH  = 200
SIDEBAR_COLLAPSED_WIDTH = 64


# ══════════════════════════════════════════════════════════
# Scroll wrapper — الحل المركزي
# ══════════════════════════════════════════════════════════

_SCROLL_SS = """
    QScrollArea {
        border: none;
        background: transparent;
    }
    QScrollBar:vertical {
        background: #f5f5f5;
        width: 8px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical {
        background: #bdbdbd;
        border-radius: 4px;
        min-height: 30px;
    }
    QScrollBar::handle:vertical:hover {
        background: #9e9e9e;
    }
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar:horizontal {
        background: #f5f5f5;
        height: 8px;
        border-radius: 4px;
    }
    QScrollBar::handle:horizontal {
        background: #bdbdbd;
        border-radius: 4px;
        min-width: 30px;
    }
    QScrollBar::handle:horizontal:hover {
        background: #9e9e9e;
    }
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {
        width: 0px;
    }
"""


def _wrap_scroll(widget) -> QScrollArea:
    """
    يغلف أي section widget بـ QScrollArea أفقي + عمودي.
    لما النافذة تصغر عن حجم المحتوى → يظهر scroll بدل ما يتضغط.
    """
    scroll = QScrollArea()
    scroll.setWidget(widget)
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll.setStyleSheet(_SCROLL_SS)
    return scroll


# ══════════════════════════════════════════════════════════
# _NavButton
# ══════════════════════════════════════════════════════════

class _NavButton(QPushButton):
    def __init__(self, icon: str, label: str, parent=None):
        super().__init__(parent)
        self._icon  = icon
        self._label = label
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self._build_content()
        self._update_style()
        self.refresh_sizes()

    def _build_content(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(10)
        lay.setAlignment(Qt.AlignVCenter)

        self._ico_lbl = QLabel(self._icon)
        self._ico_lbl.setObjectName("nav_icon")
        self._ico_lbl.setAlignment(Qt.AlignCenter)
        self._ico_lbl.setFixedWidth(32)

        self._txt_lbl = QLabel(self._label.replace("\n", " "))
        self._txt_lbl.setObjectName("nav_label")
        self._txt_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._txt_lbl.setWordWrap(False)

        lay.addWidget(self._txt_lbl, stretch=1)
        lay.addWidget(self._ico_lbl)

    def refresh_sizes(self):
        base     = get_font_size()
        icon_pt  = base + 6
        label_pt = base
        height   = icon_pt * 2 + 20

        self._ico_lbl.setStyleSheet(
            f"font-size: {icon_pt}pt;"
            " background: transparent; border: none;"
        )
        self._txt_lbl.setStyleSheet(
            f"font-size: {label_pt}pt; font-weight: bold;"
            " background: transparent; border: none;"
        )
        self.setFixedHeight(height)
        self.setFixedWidth(SIDEBAR_EXPANDED_WIDTH)

    def set_collapsed(self, collapsed: bool):
        self._txt_lbl.setVisible(not collapsed)
        if collapsed:
            self.setFixedWidth(SIDEBAR_COLLAPSED_WIDTH)
            lay = self.layout()
            if lay:
                lay.setAlignment(Qt.AlignCenter)
        else:
            self.setFixedWidth(SIDEBAR_EXPANDED_WIDTH)
            lay = self.layout()
            if lay:
                lay.setAlignment(Qt.AlignVCenter)

    def _update_style(self):
        if self.isChecked():
            self.setStyleSheet("""
                QPushButton {
                    background: #e8f4fd;
                    border: none;
                    border-right: 4px solid #1565c0;
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
                    border-right: 4px solid transparent;
                    border-radius: 0px;
                    color: #555;
                }
                QPushButton:hover { background: #f5f5f5; color: #1565c0; }
            """)

    def setChecked(self, checked):
        super().setChecked(checked)
        self._update_style()


# ══════════════════════════════════════════════════════════
# _ToggleButton
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
        self.setText("▶" if not self._collapsed else "◀")
        self.setToolTip(
            "طي الشريط الجانبي" if not self._collapsed
            else "فرد الشريط الجانبي"
        )

    def toggle_state(self) -> bool:
        self._collapsed = not self._collapsed
        self._refresh()
        return self._collapsed


# ══════════════════════════════════════════════════════════
# _Sidebar
# ══════════════════════════════════════════════════════════

class _Sidebar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._collapsed = False
        self.setFixedWidth(SIDEBAR_EXPANDED_WIDTH)
        self.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border-left: 1px solid #e0e0e0;
            }
        """)
        self._buttons: list[_NavButton] = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

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
        layout.addSpacing(4)

        nav_items = [
            ("📊", "حساب التكلفة",  "costing"),
            ("💰", "التسعير",        "pricing"),
            ("🏦", "الحسابات",       "accounting"),
            ("📦", "المخزن",         "inventory"),
            ("🎨", "التصميمات",      "design"),
            ("📋", "الطلبات",        "orders"),
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

    def refresh_all_buttons(self):
        for btn in self._buttons:
            btn.refresh_sizes()
            if self._collapsed:
                btn.set_collapsed(True)

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
                    background: #1565c0; color: white;
                    font-size: 11pt; font-weight: bold;
                    border: none; padding: 4px;
                }
            """)
        else:
            self._header.setText("ERP\nالتكاليف")
            self._header.setStyleSheet("""
                QLabel#sidebar_header {
                    background: #1565c0; color: white;
                    font-size: 15pt; font-weight: bold;
                    border: none; padding: 8px;
                }
            """)

    def get_buttons(self) -> list[_NavButton]:
        return self._buttons


# ══════════════════════════════════════════════════════════
# MainWindow
# ══════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self._app = app

        self.setWindowTitle("ERP — نظام إدارة التكاليف")
        self.resize(1280, 800)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumSize(600, 400)   # ← حد أدنى أصغر، الـ scroll يتولى الباقي

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

        # ── إنشاء الـ sections ──────────────────────────────
        self._costing    = CostingSection()
        self._pricing    = PricingSection()
        self._accounting = AccountingTab()
        self._inventory  = InventoryTab()
        self._design     = DesignSection()
        self._orders     = OrdersSection()

        # ── إضافتها للـ stack مع wrap_scroll ─────────────────
        # كل section مغلوف بـ QScrollArea → scroll أفقي + عمودي
        # لما النافذة تصغر عن المحتوى يظهر scroll بدل ما يتضغط
        self._stack.addWidget(_wrap_scroll(self._costing))       # index 0
        self._stack.addWidget(_wrap_scroll(self._pricing))       # index 1
        self._stack.addWidget(_wrap_scroll(self._accounting))    # index 2
        self._stack.addWidget(_wrap_scroll(self._inventory))     # index 3
        self._stack.addWidget(_wrap_scroll(self._design))        # index 4
        self._stack.addWidget(_wrap_scroll(self._orders))        # index 5

        main_layout.addWidget(self._stack, stretch=1)

        for btn in self._sidebar.get_buttons():
            btn.clicked.connect(lambda checked, b=btn: self._on_nav(b))

    def _on_nav(self, clicked_btn):
        for btn in self._sidebar.get_buttons():
            if btn is not clicked_btn:
                btn.setChecked(False)
        clicked_btn.setChecked(True)

        key = clicked_btn.property("nav_key")
        index_map = {
            "costing":    0,
            "pricing":    1,
            "accounting": 2,
            "inventory":  3,
            "design":     4,
            "orders":     5,
        }
        if key in index_map:
            self._stack.setCurrentIndex(index_map[key])
        elif key == "settings":
            clicked_btn.setChecked(False)
            dlg = SettingsDialog(self._app, parent=self)
            dlg.exec_()
            self._sidebar.refresh_all_buttons()