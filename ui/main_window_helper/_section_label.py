"""
ui/main_window_helper/_section_label.py
===================================================
[Refactor V3] إصلاح imports: ui.app_settings → ui.theme + ui.font
[Refactor V4] تحويل _SectionLabel إلى WidgetMixin لتحديث تلقائي عند تغيير الثيم/الخط.
"""

from PyQt5.QtWidgets import QLabel
from ui.font  import fs, get_font_size
from ui.constants import (
    SECTION_LABEL_PAD_TOP,
    SECTION_LABEL_PAD_H,
    SECTION_LABEL_PAD_BOT,
    SECTION_LABEL_LTR_SPACING,
)
from ui.widgets.core.widget_mixin import WidgetMixin


# ══════════════════════════════════════════════════════════
# _SectionLabel
# ══════════════════════════════════════════════════════════

class _SectionLabel(QLabel, WidgetMixin):
    def __init__(self, text, parent=None):
        super().__init__(text.upper(), parent)
        self._init_widget_mixin(lang=False, data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        """
        يُطبّق الـ stylesheet الحالي على الـ label.
        تُستدعى تلقائياً عند تغيير الثيم أو حجم الخط.
        تُستدعى أيضاً من _sidebar.refresh_all_buttons() للتوافق مع الكود القائم.
        """
        from ui.theme import _C
        base = get_font_size()
        self.setStyleSheet(f"""
            QLabel {{
                color: {_C['sidebar_muted']}; font-size: {fs(base, -2)}pt;
                font-weight: 700; letter-spacing: {SECTION_LABEL_LTR_SPACING};
                padding: {SECTION_LABEL_PAD_TOP}px {SECTION_LABEL_PAD_H}px {SECTION_LABEL_PAD_BOT}px {SECTION_LABEL_PAD_H}px;
                background: transparent; border: none;
            }}
        """)

    # للتوافق مع الاستدعاء القديم من _sidebar.refresh_all_buttons()
    _apply_style = _refresh_style

    def set_collapsed(self, collapsed):
        self.setVisible(not collapsed)
