"""
ui/main_window_helper/_nav_button.py
===================================================
[Refactor V3] إصلاح imports: ui.app_settings → ui.theme + ui.font + ui.constants

[إصلاح ألوان] badge stylesheet يستخدم _C['danger'] و _C['bg_input']
  بدل "#C0392B" و "#FFF" الـ hardcoded.
  يُضاف _update_badge_style() لإعادة التطبيق عند تغيير الثيم.
"""

from PyQt5.QtWidgets import (
    QHBoxLayout,
    QPushButton, QLabel, QSizePolicy,
)
from PyQt5.QtCore import Qt

from ui.theme     import _C
from ui.font      import get_font_size
from ui.constants import (
    SIDEBAR_EXPANDED_WIDTH,
    SIDEBAR_COLLAPSED_WIDTH,
    CONTENT_MIN_WIDTH,
    WINDOW_DEFAULT_W,
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
        # [إصلاح] _C['danger'] و _C['bg_input'] بدل "#C0392B" و "#FFF" hardcoded
        self._apply_badge_style()
        lay.addWidget(self._txt_lbl, stretch=1)
        lay.addWidget(self._badge_lbl)
        lay.addWidget(self._ico_lbl)

    def _apply_badge_style(self):
        """
        [إصلاح] يطبق badge stylesheet من _C الحالي.
        يُستدعى من _build_content() وعند تغيير الثيم.
        """
        self._badge_lbl.setStyleSheet(
            f"QLabel{{background:{_C['danger']};color:{_C['bg_input']};"
            "font-size:8pt;font-weight:700;"
            "padding:1px 6px;border-radius:8px;border:none;}"
        )

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
        # [إصلاح] إعادة تطبيق badge style عند تغيير حجم الخط (قد يتغير الثيم أيضاً)
        self._apply_badge_style()