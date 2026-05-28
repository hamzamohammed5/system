"""
ui/main_window_helper/_section_label.py
===================================================
[تحسين 20] _apply_style أصبحت public (قابلة للاستدعاء من _sidebar.refresh_all_buttons)
لتحديث حجم الخط عند تغييره من الإعدادات.
"""

from PyQt5.QtWidgets import QLabel
from ui.app_settings  import _C, fs, get_font_size


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

        [تحسين 20] تُستدعى من _sidebar.refresh_all_buttons() عند تغيير حجم الخط،
        بالإضافة لاستدعائها في __init__ عند الإنشاء الأول.

        تقرأ get_font_size() في كل استدعاء لضمان استخدام الحجم الحالي.
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