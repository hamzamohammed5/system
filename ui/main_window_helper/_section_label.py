"""
ui/main_window_helper/_section_label.py
===================================================

"""

from PyQt5.QtWidgets import QLabel
from ui.app_settings  import _C

# ══════════════════════════════════════════════════════════
# _SectionLabel
# ══════════════════════════════════════════════════════════



class _SectionLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text.upper(), parent)
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QLabel {{
                color: {_C['sidebar_muted']}; font-size: 8pt;
                font-weight: 700; letter-spacing: 1.5px;
                padding: 12px 16px 4px 16px;
                background: transparent; border: none;
            }}
        """)

    def set_collapsed(self, collapsed):
        self.setVisible(not collapsed)

