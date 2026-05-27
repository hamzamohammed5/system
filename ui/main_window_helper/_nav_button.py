"""
ui/main_window_helper/_nav_button.py
===================================================

التغيير: الثوابت (SIDEBAR_EXPANDED_WIDTH، إلخ) نُقلت لـ app_settings.py
وأصبحت مستوردة من هناك — لا تعريف مكرر.
"""

from PyQt5.QtWidgets import (
    QHBoxLayout,
    QPushButton, QLabel, QSizePolicy,
)
from PyQt5.QtCore import Qt

from ui.app_settings import (
    get_font_size, _C,
    SIDEBAR_EXPANDED_WIDTH,   # noqa: F401 — مُعاد تصديرها للـ imports القديمة
    SIDEBAR_COLLAPSED_WIDTH,  # noqa: F401
    CONTENT_MIN_WIDTH,        # noqa: F401
    WINDOW_DEFAULT_W,         # noqa: F401
)


# ══════════════════════════════════════════════════════════
# _NavButton
# ══════════════════════════════════════════════════════════

class _NavButton(QPushButton):
    def __init__(self, icon, label, badge="", parent=None):
        super().__init__(parent)
        self._icon = icon; self._label = label
        self._badge = badge; self._collapsed = False
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._build_content(); self._update_style()

    def _build_content(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 0, 10, 0)
        lay.setSpacing(10)
        lay.setAlignment(Qt.AlignVCenter)
        self._ico_lbl = QLabel(self._icon)
        self._ico_lbl.setFixedWidth(22)
        self._ico_lbl.setAlignment(Qt.AlignCenter)
        self._ico_lbl.setStyleSheet(
            f"background:transparent;border:none;font-size:15pt;color:{_C['sidebar_text']};"
        )
        self._txt_lbl = QLabel(self._label)
        self._txt_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._txt_lbl.setWordWrap(False)
        self._txt_lbl.setStyleSheet(
            f"background:transparent;border:none;color:{_C['sidebar_text']};"
        )
        self._badge_lbl = QLabel(self._badge)
        self._badge_lbl.setVisible(bool(self._badge))
        self._badge_lbl.setAlignment(Qt.AlignCenter)
        self._badge_lbl.setStyleSheet(
            "QLabel{background:#C0392B;color:#FFF;font-size:8pt;font-weight:700;"
            "padding:1px 6px;border-radius:8px;border:none;}"
        )
        lay.addWidget(self._txt_lbl, stretch=1)
        lay.addWidget(self._badge_lbl)
        lay.addWidget(self._ico_lbl)

    def set_badge(self, text):
        self._badge = text
        self._badge_lbl.setText(text)
        self._badge_lbl.setVisible(bool(text) and not self._collapsed)

    def set_collapsed(self, collapsed):
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
                    background:{_C['sidebar_active']};border:none;
                    border-right:2px solid {_C['accent']};
                    border-radius:6px;color:{_C['sidebar_text']};
                    font-weight:600;text-align:right;padding:0px;min-height:38px;
                }}
            """)
            self._ico_lbl.setStyleSheet(
                f"background:transparent;border:none;font-size:15pt;color:{_C['accent_mid']};"
            )
            self._txt_lbl.setStyleSheet(
                f"background:transparent;border:none;color:{_C['sidebar_text']};font-weight:600;"
            )
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background:transparent;border:none;border-radius:6px;
                    color:{_C['sidebar_text']};text-align:right;
                    padding:0px;min-height:38px;
                }}
                QPushButton:hover {{ background:{_C['sidebar_hover']}; }}
            """)
            self._ico_lbl.setStyleSheet(
                f"background:transparent;border:none;font-size:15pt;color:{_C['sidebar_muted']};"
            )
            self._txt_lbl.setStyleSheet(
                f"background:transparent;border:none;color:{_C['sidebar_text']};font-weight:400;"
            )

    def setChecked(self, v):
        super().setChecked(v); self._update_style()

    def refresh_sizes(self):
        base = get_font_size()
        self._ico_lbl.setStyleSheet(
            f"background:transparent;border:none;font-size:{base+4}pt;"
        )
        self._txt_lbl.setStyleSheet(
            f"background:transparent;border:none;font-size:{base}pt;"
        )
        h = base * 2 + 14
        self.setFixedHeight(max(38, h))
        if not self._collapsed:
            self.setFixedWidth(SIDEBAR_EXPANDED_WIDTH - 16)