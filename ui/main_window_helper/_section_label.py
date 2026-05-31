"""
ui/main_window_helper/_section_label.py
===================================================
[Refactor V3] إصلاح imports: ui.app_settings → ui.theme + ui.font
"""

from PyQt5.QtWidgets import QLabel
from ui.theme import _C
from ui.font  import fs, get_font_size


# ══════════════════════════════════════════════════════════
# _SectionLabel
# ══════════════════════════════════════════════════════════

class _SectionLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text.upper(), parent)
        self._apply_style()

    def _apply_style(self):
        """
        يُطبّق الـ stylesheet الحالي على الـ label.
        تُستدعى من _sidebar.refresh_all_buttons() عند تغيير حجم الخط.
        """
        base = get_font_size()
        self.setStyleSheet(f"""
            QLabel {{
                color: {_C['sidebar_muted']}; font-size: {fs(base, -2)}pt;
                font-weight: 700; letter-spacing: 1.5px;
                padding: 12px 16px 4px 16px;
                background: transparent; border: none;
            }}
        """)

    def set_collapsed(self, collapsed):
        self.setVisible(not collapsed)