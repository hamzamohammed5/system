"""
ui/main_window.py
=================
النافذة الرئيسية — Sidebar + Content.

القاعدة:
  - عرض النافذة أقصى ما يكون = عرض الـ sidebar + عرض الـ content
  - الـ content عرضه يكفي بالضبط إن الـ horizontal scroll يختفي
  - الجداول والأزرار حجمهم ثابت ومش بيتمدد
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame,
    QScrollArea, QSizePolicy,
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve

from ui.tabs.costing_section      import CostingSection
from ui.tabs.pricing_section      import PricingSection
from ui.tabs.accounting_section   import AccountingTab
from ui.tabs.inventory_section    import InventoryTab
from ui.tabs.design_section       import DesignSection
from ui.tabs.orders_section       import OrdersSection
from ui.settings_dialog           import SettingsDialog
from ui.app_settings              import get_font_size, _C

SIDEBAR_EXPANDED_WIDTH  = 224
SIDEBAR_COLLAPSED_WIDTH = 56


# ══════════════════════════════════════════════════════════
# Scroll wrapper — فقط للمحتوى العمودي
# ══════════════════════════════════════════════════════════

_SCROLL_SS = f"""
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical {{
        background: {_C['border_med']};
        border-radius: 3px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {_C['border_strong']};
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 6px;
        border-radius: 3px;
    }}
    QScrollBar::handle:horizontal {{
        background: {_C['border_med']};
        border-radius: 3px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {_C['border_strong']};
    }}
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
"""


def _wrap_scroll(widget) -> QScrollArea:
    """
    يلف الـ widget في scroll area.
    الـ horizontal scroll يظهر فقط لو الـ widget أكبر من المساحة.
    """
    scroll = QScrollArea()
    scroll.setWidget(widget)
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll.setStyleSheet(_SCROLL_SS)
    return scroll


# ══════════════════════════════════════════════════════════
# _SectionLabel
# ══════════════════════════════════════════════════════════

class _SectionLabel(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text.upper(), parent)
        self._collapsed = False
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QLabel {{
                color: {_C['sidebar_muted']};
                font-size: 8pt;
                font-weight: 700;
                letter-spacing: 1.5px;
                padding: 12px 16px 4px 16px;
                background: transparent;
                border: none;
            }}
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
        self._icon      = icon
        self._label     = label
        self._badge     = badge
        self._collapsed = False
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        # حجم ثابت — مش بيتمدد
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
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
        self._ico_lbl.setStyleSheet(
            f"background:transparent; border:none; font-size:15pt; color:{_C['sidebar_text']};"
        )

        self._txt_lbl = QLabel(self._label)
        self._txt_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._txt_lbl.setWordWrap(False)
        self._txt_lbl.setStyleSheet(
            f"background:transparent; border:none; color:{_C['sidebar_text']};"
        )

        self._badge_lbl = QLabel(self._badge)
        self._badge_lbl.setVisible(bool(self._badge))
        self._badge_lbl.setAlignment(Qt.AlignCenter)
        self._badge_lbl.setStyleSheet("""
            QLabel {
                background: #C0392B; color: #FFFFFF;
                font-size: 8pt; font-weight: 700;
                padding: 1px 6px; border-radius: 8px; border: none;
            }
        """)

        # RTL
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
            self.setFixedWidth(SIDEBAR_EXPANDED_WIDTH - 16)
            self.layout().setContentsMargins(10, 0, 10, 0)
            self.layout().setAlignment(Qt.AlignVCenter)

    def _update_style(self):
        if self.isChecked():
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {_C['sidebar_active']};
                    border: none;
                    border-right: 2px solid {_C['accent']};
                    border-radius: 6px;
                    color: {_C['sidebar_text']};
                    font-weight: 600;
                    text-align: right;
                    padding: 0px;
                    min-height: 38px;
                }}
            """)
            self._ico_lbl.setStyleSheet(
                f"background:transparent; border:none; font-size:15pt; color:{_C['accent_mid']};"
            )
            self._txt_lbl.setStyleSheet(
                f"background:transparent; border:none; color:{_C['sidebar_text']}; font-weight:600;"
            )
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    border-radius: 6px;
                    color: {_C['sidebar_text']};
                    text-align: right;
                    padding: 0px;
                    min-height: 38px;
                }}
                QPushButton:hover {{
                    background: {_C['sidebar_hover']};
                }}
            """)
            self._ico_lbl.setStyleSheet(
                f"background:transparent; border:none; font-size:15pt; color:{_C['sidebar_muted']};"
            )
            self._txt_lbl.setStyleSheet(
                f"background:transparent; border:none; color:{_C['sidebar_text']}; font-weight:400;"
            )

    def setChecked(self, checked):
        super().setChecked(checked)
        self._update_style()

    def refresh_sizes(self):
        base = get_font_size()
        self._ico_lbl.setStyleSheet(
            f"background:transparent; border:none; font-size:{base + 4}pt;"
        )
        self._txt_lbl.setStyleSheet(
            f"background:transparent; border:none; font-size:{base}pt;"
        )
        h = base * 2 + 14
        self.setFixedHeight(max(38, h))
        if not self._collapsed:
            self.setFixedWidth(SIDEBAR_EXPANDED_WIDTH - 16)


# ══════════════════════════════════════════════════════════
# _ToggleButton
# ══════════════════════════════════════════════════════════

class _ToggleButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._collapsed = False
        self.setFixedHeight(36)
        self.setCursor(Qt.PointingHandCursor)
        self._refresh()
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-top: 1px solid {_C['sidebar_border']};
                color: {_C['sidebar_muted']};
                font-size: 11pt;
            }}
            QPushButton:hover {{
                background: {_C['sidebar_hover']};
                color: {_C['sidebar_text']};
            }}
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
        # الـ sidebar عرضه ثابت
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setStyleSheet(f"""
            QFrame {{
                background: {_C['sidebar_bg']};
                border-left: 1px solid {_C['sidebar_border']};
            }}
        """)
        self._buttons: list[_NavButton]           = []
        self._section_labels: list[_SectionLabel] = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ──
        header = QWidget()
        header.setFixedHeight(64)
        header.setStyleSheet(f"""
            QWidget {{
                background: {_C['sidebar_bg']};
                border-bottom: 1px solid {_C['sidebar_border']};
            }}
        """)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(14, 0, 14, 0)
        h_lay.setSpacing(10)

        self._brand_icon = QLabel("🏭")
        self._brand_icon.setFixedWidth(30)
        self._brand_icon.setAlignment(Qt.AlignCenter)
        self._brand_icon.setStyleSheet(
            "font-size: 18pt; background: transparent; border: none;"
        )

        self._brand_text_widget = QWidget()
        self._brand_text_widget.setStyleSheet("background:transparent;")
        bt_lay = QVBoxLayout(self._brand_text_widget)
        bt_lay.setContentsMargins(0, 0, 0, 0)
        bt_lay.setSpacing(1)

        self._brand_title = QLabel("ERP")
        self._brand_title.setStyleSheet(f"""
            color: {_C['sidebar_text']}; font-size: 14pt; font-weight: 700;
            background: transparent; border: none; letter-spacing: 1px;
        """)

        self._brand_sub = QLabel("إدارة التكاليف")
        self._brand_sub.setStyleSheet(f"""
            color: {_C['sidebar_muted']}; font-size: 8pt;
            background: transparent; border: none; letter-spacing: 0.3px;
        """)

        bt_lay.addWidget(self._brand_title)
        bt_lay.addWidget(self._brand_sub)

        h_lay.addWidget(self._brand_text_widget, stretch=1)
        h_lay.addWidget(self._brand_icon)
        layout.addWidget(header)

        # ── Nav Scroll ──
        nav_scroll = QScrollArea()
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        nav_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        nav_scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: transparent; width: 3px; border-radius: 1px;
            }}
            QScrollBar::handle:vertical {{
                background: {_C['sidebar_border']}; border-radius: 1px; min-height: 20px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

        nav_widget = QWidget()
        nav_widget.setStyleSheet("background: transparent;")
        nav_lay = QVBoxLayout(nav_widget)
        nav_lay.setContentsMargins(8, 8, 8, 8)
        nav_lay.setSpacing(1)

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
                btn.setFixedHeight(38)
                self._buttons.append(btn)
                nav_lay.addWidget(btn)

            nav_lay.addSpacing(4)

        nav_lay.addStretch()
        nav_scroll.setWidget(nav_widget)
        layout.addWidget(nav_scroll, stretch=1)

        # ── Footer ──
        footer = QWidget()
        footer.setStyleSheet("QWidget { background: transparent; }")
        f_lay = QVBoxLayout(footer)
        f_lay.setContentsMargins(8, 4, 8, 4)
        f_lay.setSpacing(1)

        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setFixedHeight(1)
        div.setStyleSheet(f"background: {_C['sidebar_border']}; border: none; margin: 2px 4px;")
        f_lay.addWidget(div)

        btn_settings = _NavButton("⚙️", "الإعدادات")
        btn_settings.setProperty("nav_key", "settings")
        btn_settings.setFixedWidth(SIDEBAR_EXPANDED_WIDTH - 16)
        btn_settings.setFixedHeight(38)
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
        self._anim_min.setDuration(200)
        self._anim_min.setEasingCurve(QEasingCurve.InOutCubic)
        self._anim_min.setStartValue(self.width())
        self._anim_min.setEndValue(target)

        self._anim_max = QPropertyAnimation(self, b"maximumWidth")
        self._anim_max.setDuration(200)
        self._anim_max.setEasingCurve(QEasingCurve.InOutCubic)
        self._anim_max.setStartValue(self.width())
        self._anim_max.setEndValue(target)

        self._anim_min.start()
        self._anim_max.start()

        for btn in self._buttons:
            btn.set_collapsed(self._collapsed)

        for lbl in self._section_labels:
            lbl.set_collapsed(self._collapsed)

        self._brand_text_widget.setVisible(not self._collapsed)
        self._toggle_btn.setFixedWidth(target)

    def refresh_all_buttons(self):
        for btn in self._buttons:
            btn.refresh_sizes()
            if self._collapsed:
                btn.set_collapsed(True)

    def get_buttons(self) -> list:
        return self._buttons


# ══════════════════════════════════════════════════════════
# MainWindow
# ══════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self._app = app

        self.setWindowTitle("ERP — نظام إدارة التكاليف")
        self.resize(1300, 820)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumSize(800, 500)

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

        # فاصل
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"background: {_C['border']}; border: none;")
        main_layout.addWidget(sep)

        # ── الـ stack: يأخذ كل المساحة المتبقية ──
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background: {_C['bg_page']};")
        # Expanding: يكبر مع النافذة
        self._stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._costing    = CostingSection()
        self._pricing    = PricingSection()
        self._accounting = AccountingTab()
        self._inventory  = InventoryTab()
        self._design     = DesignSection()
        self._orders     = OrdersSection()

        # الأقسام اللي فيها list+detail: مش محتاجة wrap في scroll
        # لأن الـ list panel بيضبط عرضه بنفسه
        self._stack.addWidget(self._costing)        # 0
        self._stack.addWidget(self._pricing)        # 1
        self._stack.addWidget(self._accounting)     # 2
        self._stack.addWidget(self._inventory)      # 3
        self._stack.addWidget(self._design)         # 4
        self._stack.addWidget(self._orders)         # 5

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