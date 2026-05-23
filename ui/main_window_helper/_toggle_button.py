"""
ui/main_window_helper/_toggle_button.py
===================================================
"""

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt

from ui.app_settings  import _C

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
                background:transparent;border:none;
                border-top:1px solid {_C['sidebar_border']};
                color:{_C['sidebar_muted']};font-size:11pt;
            }}
            QPushButton:hover {{
                background:{_C['sidebar_hover']};color:{_C['sidebar_text']};
            }}
        """)

    def _refresh(self):
        self.setText("◀" if not self._collapsed else "▶")
        self.setToolTip("طي الشريط الجانبي" if not self._collapsed else "فرد الشريط الجانبي")

    def toggle_state(self):
        self._collapsed = not self._collapsed
        self._refresh()
        return self._collapsed


