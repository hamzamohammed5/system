"""
ui/main_window.py
=================
النافذة الرئيسية — Sidebar Navigation + Content Area.

التحديثات:
  - أيقونة ونص الـ Sidebar أكبر
  - الـ Sidebar قابل للطي والفرد بزر Toggle (◀ / ▶)
  - في وضع الطي تظهر الأيقونة فقط، في وضع الفرد تظهر الأيقونة + النص

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
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve

from ui.tabs.costing_section  import CostingSection
from ui.tabs.pricing_section  import PricingSection
from ui.tabs.accounting_section   import AccountingTab
from ui.tabs.inventory_section    import InventoryTab
from ui.settings_dialog       import SettingsDialog


# ══════════════════════════════════════════════════════════
# الأبعاد
# ══════════════════════════════════════════════════════════

SIDEBAR_EXPANDED_WIDTH  = 150   # عرض الـ sidebar مفرود
SIDEBAR_COLLAPSED_WIDTH = 58    # عرض الـ sidebar مطوي (أيقونة فقط)
BTN_HEIGHT              = 72    # ارتفاع كل زر تنقل
ICON_FONT_SIZE          = 26    # حجم الأيقونة (pt)
LABEL_FONT_SIZE         = 12    # حجم النص (pt)


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
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)

        self._ico_lbl = QLabel(self._icon)
        self._ico_lbl.setAlignment(Qt.AlignCenter)
        self._ico_lbl.setStyleSheet(
            f"font-size:{ICON_FONT_SIZE}px; background:transparent; border:none;"
        )

        self._txt_lbl = QLabel(self._label)
        self._txt_lbl.setAlignment(Qt.AlignCenter)
        self._txt_lbl.setStyleSheet(
            f"font-size:{LABEL_FONT_SIZE}px; background:transparent; border:none;"
        )
        self._txt_lbl.setWordWrap(True)

        layout.addWidget(self._ico_lbl)
        layout.addWidget(self._txt_lbl)

    # ── إظهار/إخفاء النص حسب وضع الـ sidebar ──────────

    def set_collapsed(self, collapsed: bool):
        """إخفاء النص في وضع الطي وإظهاره في وضع الفرد."""
        self._txt_lbl.setVisible(not collapsed)
        new_width = SIDEBAR_COLLAPSED_WIDTH if collapsed else SIDEBAR_EXPANDED_WIDTH
        self.setFixedWidth(new_width)

    # ── الستايل ──────────────────────────────────────────

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
    """زر صغير في أسفل الـ sidebar لطيه وفرده."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._collapsed = False
        self.setFixedHeight(36)
        self.setCursor(Qt.PointingHandCursor)
        self._refresh()
        self.setStyleSheet("""
            QPushButton {
                background: #e8eaf6;
                border: none;
                border-top: 1px solid #e0e0e0;
                color: #3949ab;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background: #c5cae9; }
        """)

    def _refresh(self):
        self.setText("◀" if not self._collapsed else "▶")
        self.setToolTip("طي الشريط الجانبي" if not self._collapsed else "فرد الشريط الجانبي")

    def toggle_state(self) -> bool:
        """يبدّل الحالة ويعيد True لو أصبح مطوياً."""
        self._collapsed = not self._collapsed
        self._refresh()
        return self._collapsed

    @property
    def is_collapsed(self) -> bool:
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

        # ── رأس الـ sidebar ──
        self._header = QLabel("ERP\nالتكاليف")
        self._header.setAlignment(Qt.AlignCenter)
        self._header.setFixedHeight(70)
        self._header.setStyleSheet("""
            QLabel {
                background: #1565c0;
                color: white;
                font-size: 15px;
                font-weight: bold;
                border: none;
                padding: 8px;
            }
        """)
        layout.addWidget(self._header)
        layout.addSpacing(8)

        # ── أزرار التنقل ──
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

        # ── زر الإعدادات ──
        btn_settings = _NavButton("⚙️", "الإعدادات")
        btn_settings.setProperty("nav_key", "settings")
        self._buttons.append(btn_settings)
        layout.addWidget(btn_settings)

        # ── زر الطي ──
        self._toggle_btn = _ToggleButton()
        self._toggle_btn.clicked.connect(self._on_toggle)
        layout.addWidget(self._toggle_btn)

    # ── الطي / الفرد ──────────────────────────────────────

    def _on_toggle(self):
        self._collapsed = self._toggle_btn.toggle_state()

        # انيميشن على عرض الـ sidebar
        target_width = SIDEBAR_COLLAPSED_WIDTH if self._collapsed else SIDEBAR_EXPANDED_WIDTH

        self._anim = QPropertyAnimation(self, b"minimumWidth")
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.InOutQuad)
        self._anim.setStartValue(self.width())
        self._anim.setEndValue(target_width)

        self._anim2 = QPropertyAnimation(self, b"maximumWidth")
        self._anim2.setDuration(180)
        self._anim2.setEasingCurve(QEasingCurve.InOutQuad)
        self._anim2.setStartValue(self.width())
        self._anim2.setEndValue(target_width)

        self._anim.start()
        self._anim2.start()

        # إخفاء/إظهار النصوص في الأزرار
        for btn in self._buttons:
            btn.set_collapsed(self._collapsed)

        # إخفاء/إظهار نص الرأس
        if self._collapsed:
            self._header.setText("ERP")
            self._header.setStyleSheet("""
                QLabel {
                    background: #1565c0;
                    color: white;
                    font-size: 13px;
                    font-weight: bold;
                    border: none;
                    padding: 4px;
                }
            """)
        else:
            self._header.setText("ERP\nالتكاليف")
            self._header.setStyleSheet("""
                QLabel {
                    background: #1565c0;
                    color: white;
                    font-size: 15px;
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

        # index 0 → حساب التكلفة
        self._costing = CostingSection()
        self._stack.addWidget(self._costing)

        # index 1 → التسعير
        self._pricing = PricingSection()
        self._stack.addWidget(self._pricing)

        # index 2 → الحسابات
        self._accounting = AccountingTab()
        self._stack.addWidget(self._accounting)

        # index 3 → المخزن
        self._inventory = InventoryTab()
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