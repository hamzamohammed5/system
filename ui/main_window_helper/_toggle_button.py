"""
ui/main_window_helper/_toggle_button.py
===================================================
[Refactor V3] إصلاح imports: ui.app_settings → ui.theme
"""

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt

from ui.theme import _C
from ui.constants import SIDEBAR_TOGGLE_H
from ui.font import FS_SM

# ══════════════════════════════════════════════════════════
# _ToggleButton
# ══════════════════════════════════════════════════════════

class _ToggleButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._collapsed = False
        self.setFixedHeight(SIDEBAR_TOGGLE_H)
        self.setCursor(Qt.PointingHandCursor)
        self._refresh()
        self.setStyleSheet(f"""
            QPushButton {{
                background:transparent;border:none;
                border-top:1px solid {_C['sidebar_border']};
                color:{_C['sidebar_muted']};font-size:{FS_SM}pt;
            }}
            QPushButton:hover {{
                background:{_C['sidebar_hover']};color:{_C['sidebar_text']};
            }}
        """)

    def _refresh(self):
        from ui.widgets.core.i18n import tr
        self.setText(tr('sidebar_collapse_icon') if not self._collapsed else tr('sidebar_expand_icon'))
        self.setToolTip(tr('sidebar_collapse_tip') if not self._collapsed else tr('sidebar_expand_tip'))

    def toggle_state(self):
        self._collapsed = not self._collapsed
        self._refresh()
        return self._collapsed