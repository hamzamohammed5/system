"""
ui/main_window.py  (محدَّث — sidebar محسّن + navigation منظم)
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


SIDEBAR_EXPANDED_WIDTH  = 220
SIDEBAR_COLLAPSED_WIDTH = 56


# ══════════════════════════════════════════════════════════
# Scroll wrapper
# ══════════════════════════════════════════════════════════

_SCROLL_SS = """
    QScrollArea {
        border: none;
        background: transparent;
    }
    QScrollBar:vertical {
        background: transparent;
        width: 6px;
        border-radius: 3px;
    }
    QScrollBar::handle:vertical {
        background: #D3D1C7;
        border-radius: 3px;
        min-height: 30px;
    }
    QScrollBar::handle:vertical:hover {
        background: #B4B2A9;
    }
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar:horizontal {
        background: transparent;
        height: 6px;
        border-radius: 3px;
    }
    QScrollBar::handle:horizontal {
        background: #D3D1C7;
        border-radius: 3px;
        min-width: 30px;
    }
    QScrollBar::handle:horizontal:hover {
        background: #B4B2A9;
    }
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {
        width: 0px;
    }
"""


def _wrap_scroll(widget) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setWidget(widget)
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll.setStyleSheet(_SCROLL_SS)
    return scroll


# ══════════════════════════════════════════════════════════
# _SectionLabel — عنوان القسم في الـ sidebar
# ══════════════════════════════════════════════════════════

class _SectionLabel(QLabel):
    """عنوان فئة صغير داخل الـ sidebar (الإنتاج / المالية / العمل)."""

    def __init__(self, text: str, parent=None):
        super().__init__(text.upper(), parent)
        self._collapsed = False
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet("""
            QLabel {
                color: #888780;
                font-size: 9pt;
                font-weight: bold;
                letter-spacing: 1px;
                padding: 10px 14px 4px 14px;
                background: transparent;
                border: none;
            }
        """)

    def set_collapsed(self, collapsed: bool):
        self._collapsed = collapsed
        self.setVisible(not collapsed)


# ══════════════════════════════════════════════════════════
# _NavButton
# ══════════════════════════════════════════════════════════

class _NavButton(QPushButton):
    def __init__(self, icon: str, label: str, badge: str = "", parent=None):
        super().__init__(parent)
        self._icon    = icon
        self._label   = label
        self._badge   = badge
        self._collapsed = False
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self._build_content()
        self._update_style()

    def _build_content(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 0, 10, 0)
        lay.setSpacing(10)
        lay.setAlignment(Qt.AlignVCenter)

        self._ico_lbl = QLabel(self._icon)
        self._ico_lbl.setFixedWidth(22)
        self._ico_lbl.setAlignment(Qt.AlignCenter)
        self._ico_lbl.setStyleSheet("background:transparent; border:none; font-size:16pt;")

        self._txt_lbl = QLabel(self._label)
        self._txt_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._txt_lbl.setWordWrap(False)
        self._txt_lbl.setStyleSheet("background:transparent; border:none;")

        # badge (عدد الطلبات العاجلة مثلاً)
        self._badge_lbl = QLabel(self._badge)
        self._badge_lbl.setVisible(bool(self._badge))
        self._badge_lbl.setAlignment(Qt.AlignCenter)
        self._badge_lbl.setStyleSheet("""
            QLabel {
                background: #F5C4B3;
                color: #993C1D;
                font-size: 9pt;
                font-weight: bold;
                padding: 0px 5px;
                border-radius: 8px;
                border: none;
            }
        """)

        # RTL: النص أولاً ثم الأيقونة
        lay.addWidget(self._txt_lbl, stretch=1)
        lay.addWidget(self._badge_lbl)
        lay.addWidget(self._ico_lbl)

    def set_badge(self, text: str):
        self._badge = text
        self._badge_lbl.setText(text)
        self._badge_lbl.setVisible(bool(text) and not self._collapsed)

    def set_collapsed(self, collapsed: bool):
        self._collapsed = collapsed
        self._txt_lbl.setVisible(not collapsed)
        self._badge_lbl.setVisible(bool(self._badge) and not collapsed)
        if collapsed:
            self.setFixedWidth(SIDEBAR_COLLAPSED_WIDTH)
            self.layout().setContentsMargins(0, 0, 0, 0)
            self.layout().setAlignment(Qt.AlignCenter)
        else:
            self.setFixedWidth(SIDEBAR_EXPANDED_WIDTH)
            self.layout().setContentsMargins(10, 0, 10, 0)
            self.layout().setAlignment(Qt.AlignVCenter)

    def _update_style(self):
        if self.isChecked():
            self.setStyleSheet("""
                QPushButton {
                    background: #F1EFE8;
                    border: none;
                    border-radius: 6px;
                    color: #2C2C2A;
                    font-weight: bold;
                    text-align: right;
                    padding: 0px;
                    min-height: 36px;
                }
                QPushButton:hover { background: #D3D1C7; }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    border-radius: 6px;
                    color: #5F5E5A;
                    text-align: right;
                    padding: 0px;
                    min-height: 36px;
                }
                QPushButton:hover {
                    background: #F1EFE8;
                    color: #2C2C2A;
                }
            """)

    def setChecked(self, checked):
        super().setChecked(checked)
        self._update_style()

    def refresh_sizes(self):
        """تحديث الأحجام عند تغيير حجم الخط."""
        base = get_font_size()
        self._ico_lbl.setStyleSheet(
            f"background:transparent; border:none; font-size:{base + 4}pt;"
        )
        self._txt_lbl.setStyleSheet(
            f"background:transparent; border:none; font-size:{base}pt;"
        )
        h = base * 2 + 10
        self.setFixedHeight(max(36, h))
        if not self._collapsed:
            self.setFixedWidth(SIDEBAR_EXPANDED_WIDTH)


# ══════════════════════════════════════════════════════════
# _Divider — فاصل خفيف
# ══════════════════════════════════════════════════════════

class _Divider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setFixedHeight(1)
        self.setStyleSheet("background: #E8E6DF; border: none; margin: 4px 0;")


# ══════════════════════════════════════════════════════════
# _ToggleButton
# ══════════════════════════════════════════════════════════

class _ToggleButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._collapsed = False
        self.setFixedHeight(32)
        self.setCursor(Qt.PointingHandCursor)
        self._refresh()
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-top: 1px solid #E8E6DF;
                color: #888780;
                font-size: 12pt;
            }
            QPushButton:hover {
                background: #F1EFE8;
                color: #444441;
            }
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
# _Sidebar
# ══════════════════════════════════════════════════════════

class _Sidebar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._collapsed = False
        self.setFixedWidth(SIDEBAR_EXPANDED_WIDTH)
        self.setStyleSheet("""
            QFrame {
                background: #FAFAF8;
                border-left: 1px solid #E8E6DF;
            }
        """)
        self._buttons: list[_NavButton]       = []
        self._section_labels: list[_SectionLabel] = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header / Brand ─────────────────────────────────
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QWidget {
                background: #2C2C2A;
                border: none;
            }
        """)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(14, 0, 14, 0)
        h_lay.setSpacing(10)

        self._brand_icon = QLabel("🏭")
        self._brand_icon.setFixedWidth(28)
        self._brand_icon.setAlignment(Qt.AlignCenter)
        self._brand_icon.setStyleSheet(
            "font-size: 16pt; background: transparent; border: none;"
        )

        self._brand_text_widget = QWidget()
        bt_lay = QVBoxLayout(self._brand_text_widget)
        bt_lay.setContentsMargins(0, 0, 0, 0)
        bt_lay.setSpacing(0)

        self._brand_title = QLabel("ERP")
        self._brand_title.setStyleSheet(
            "color: #F1EFE8; font-size: 13pt; font-weight: bold;"
            "background: transparent; border: none;"
        )
        self._brand_sub = QLabel("إدارة التكاليف")
        self._brand_sub.setStyleSheet(
            "color: #888780; font-size: 9pt;"
            "background: transparent; border: none;"
        )
        bt_lay.addWidget(self._brand_title)
        bt_lay.addWidget(self._brand_sub)

        # RTL: نص أولاً ثم أيقونة
        h_lay.addWidget(self._brand_text_widget, stretch=1)
        h_lay.addWidget(self._brand_icon)
        layout.addWidget(header)

        # ── Nav scroll area ────────────────────────────────
        nav_scroll = QScrollArea()
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        nav_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        nav_scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                background: transparent; width: 4px; border-radius: 2px;
            }
            QScrollBar::handle:vertical {
                background: #D3D1C7; border-radius: 2px; min-height: 20px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height: 0px; }
        """)

        nav_widget = QWidget()
        nav_widget.setStyleSheet("background: transparent;")
        nav_lay = QVBoxLayout(nav_widget)
        nav_lay.setContentsMargins(8, 8, 8, 8)
        nav_lay.setSpacing(2)

        # ── تعريف المجموعات والأزرار ────────────────────────
        nav_sections = [
            ("الإنتاج", [
                ("📊", "حساب التكلفة", "costing",    ""),
                ("💰", "التسعير",       "pricing",    ""),
            ]),
            ("المالية", [
                ("🏦", "الحسابات",     "accounting", ""),
                ("📦", "المخزن",        "inventory",  ""),
            ]),
            ("العمل", [
                ("🎨", "التصميمات",    "design",     ""),
                ("📋", "الطلبات",       "orders",     ""),
            ]),
        ]

        for section_name, items in nav_sections:
            lbl = _SectionLabel(section_name)
            self._section_labels.append(lbl)
            nav_lay.addWidget(lbl)

            for icon, label, key, badge in items:
                btn = _NavButton(icon, label, badge)
                btn.setProperty("nav_key", key)
                btn.setFixedWidth(SIDEBAR_EXPANDED_WIDTH - 16)
                self._buttons.append(btn)
                nav_lay.addWidget(btn)

            nav_lay.addSpacing(4)

        nav_lay.addStretch()
        nav_scroll.setWidget(nav_widget)
        layout.addWidget(nav_scroll, stretch=1)

        # ── Footer ─────────────────────────────────────────
        footer = QWidget()
        footer.setStyleSheet("""
            QWidget {
                background: transparent;
                border-top: 1px solid #E8E6DF;
            }
        """)
        f_lay = QVBoxLayout(footer)
        f_lay.setContentsMargins(8, 6, 8, 4)
        f_lay.setSpacing(2)

        btn_settings = _NavButton("⚙️", "الإعدادات")
        btn_settings.setProperty("nav_key", "settings")
        btn_settings.setFixedWidth(SIDEBAR_EXPANDED_WIDTH - 16)
        self._buttons.append(btn_settings)
        f_lay.addWidget(btn_settings)

        self._toggle_btn = _ToggleButton()
        self._toggle_btn.setFixedWidth(SIDEBAR_EXPANDED_WIDTH)
        self._toggle_btn.clicked.connect(self._on_toggle)
        f_lay.addWidget(self._toggle_btn)

        layout.addWidget(footer)

    def _on_toggle(self):
        self._collapsed = self._toggle_btn.toggle_state()
        target = (
            SIDEBAR_COLLAPSED_WIDTH if self._collapsed
            else SIDEBAR_EXPANDED_WIDTH
        )

        self._anim_min = QPropertyAnimation(self, b"minimumWidth")
        self._anim_min.setDuration(180)
        self._anim_min.setEasingCurve(QEasingCurve.InOutQuad)
        self._anim_min.setStartValue(self.width())
        self._anim_min.setEndValue(target)

        self._anim_max = QPropertyAnimation(self, b"maximumWidth")
        self._anim_max.setDuration(180)
        self._anim_max.setEasingCurve(QEasingCurve.InOutQuad)
        self._anim_max.setStartValue(self.width())
        self._anim_max.setEndValue(target)

        self._anim_min.start()
        self._anim_max.start()

        for btn in self._buttons:
            btn.set_collapsed(self._collapsed)

        for lbl in self._section_labels:
            lbl.set_collapsed(self._collapsed)

        # تغيير الـ brand
        self._brand_text_widget.setVisible(not self._collapsed)
        self._toggle_btn.setFixedWidth(target)

    def refresh_all_buttons(self):
        for btn in self._buttons:
            btn.refresh_sizes()
            if self._collapsed:
                btn.set_collapsed(True)

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
        self.setMinimumSize(600, 400)

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
        self._stack.setStyleSheet("background: #F7F6F3;")

        self._costing    = CostingSection()
        self._pricing    = PricingSection()
        self._accounting = AccountingTab()
        self._inventory  = InventoryTab()
        self._design     = DesignSection()
        self._orders     = OrdersSection()

        self._stack.addWidget(_wrap_scroll(self._costing))       # 0
        self._stack.addWidget(_wrap_scroll(self._pricing))       # 1
        self._stack.addWidget(_wrap_scroll(self._accounting))    # 2
        self._stack.addWidget(_wrap_scroll(self._inventory))     # 3
        self._stack.addWidget(_wrap_scroll(self._design))        # 4
        self._stack.addWidget(_wrap_scroll(self._orders))        # 5

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