"""
ui/widgets/panels/form_badges.py
==================================
Badge & Preview widgets للفورمات.

مستخرج من panels/form_parts.py:
  ResultBadge, ModeBadge, InlinePreview, make_preview_label
"""

from PyQt5.QtWidgets import QLabel, QWidget, QHBoxLayout
from PyQt5.QtCore    import Qt

from ui.theme import _C
from ui.font  import get_font_size, fs
from ui.widgets.core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import (
    BADGE_BORDER_RADIUS, BADGE_PAD_H, BADGE_PAD_V, MODE_BADGE_PAD_V,
    PREVIEW_LABEL_RADIUS, PREVIEW_LABEL_PAD_V, PREVIEW_LABEL_PAD_H,
    INLINE_PREVIEW_SPACING,
)
from ..core.colors import status_colors


def make_preview_label(text: str = None, status: str = "info") -> QLabel:
    s = status_colors(status)
    lbl = QLabel(text if text is not None else tr('amount_dash_placeholder'))
    base = get_font_size()
    lbl.setStyleSheet(
        f"background:{s['bg']}; border:1px solid {s['border']}; color:{s['fg']};"
        f"border-radius:{PREVIEW_LABEL_RADIUS}px;"
        f"padding:{PREVIEW_LABEL_PAD_V}px {PREVIEW_LABEL_PAD_H}px;"
        f"font-size:{fs(base,-1)}pt;"
    )
    lbl.setWordWrap(True)
    return lbl


class ResultBadge(QLabel, WidgetMixin):
    """Label لعرض نتيجة / تكلفة محسوبة."""

    def __init__(self, text: str = None, color: str = None,
                 status: str = "success", parent=None):
        super().__init__(text if text is not None else tr('amount_dash_placeholder'), parent)
        self._custom_color = color
        self._status       = status
        self._init_widget_mixin(theme=True, font=True, lang=False, data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        base = get_font_size()
        s = status_colors(self._status)
        if self._custom_color:
            self.setStyleSheet(
                f"color:{self._custom_color}; font-weight:bold; font-size:{fs(base,0)}pt;"
                f"background:{s['bg']}; border:1px solid {s['border']};"
                f"border-radius:{BADGE_BORDER_RADIUS}px;"
                f"padding:{BADGE_PAD_V}px {BADGE_PAD_H}px;"
            )
        else:
            self.setStyleSheet(
                f"color:{s['fg']}; font-weight:bold; font-size:{fs(base,0)}pt;"
                f"background:{s['bg']}; border:1px solid {s['border']};"
                f"border-radius:{BADGE_BORDER_RADIUS}px;"
                f"padding:{BADGE_PAD_V}px {BADGE_PAD_H}px;"
            )

    # رُبط _refresh_style بالـ bus — لا حاجة لـ _apply() منفصلة
    def set_value(self, text: str, color: str = None):
        self.setText(text)
        if color and color != self._custom_color:
            self._custom_color = color
            self._refresh_style()

    def set_status(self, status: str):
        if status != self._status:
            self._status = status
            self._refresh_style()

    def reset(self):
        self.setText(tr('amount_dash_placeholder'))


class ModeBadge(QLabel, WidgetMixin):
    """Label لعرض الوضع الحالي مع ستايل ملون."""

    def __init__(self, text: str = None, color: str = "blue", parent=None):
        super().__init__(text if text is not None else tr('amount_dash_placeholder'), parent)
        self._color_key = color
        self._init_widget_mixin(theme=True, font=True, lang=False, data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        _map = {
            "blue":   "primary",
            "orange": "warning",
            "green":  "success",
            "red":    "danger",
            "purple": "purple",
        }
        s = status_colors(_map.get(self._color_key, "info"))
        base = get_font_size()
        self.setStyleSheet(
            f"color:{s['fg']}; font-weight:bold; font-size:{fs(base,-1)}pt;"
            f"background:{s['bg']}; border:1px solid {s['border']};"
            f"border-radius:{BADGE_BORDER_RADIUS}px;"
            f"padding:{MODE_BADGE_PAD_V}px {BADGE_PAD_H}px;"
        )

    def set_mode(self, text: str, color: str = None):
        self.setText(text)
        if color and color != self._color_key:
            self._color_key = color
            self._refresh_style()

    def reset(self):
        self.setText(tr('amount_dash_placeholder'))


class InlinePreview(QWidget, WidgetMixin):
    """يعرض: [label] [القيمة المحسوبة]"""

    def __init__(self, label: str = None, color: str = None,
                 status: str = "success", parent=None):
        super().__init__(parent)
        self._label_text = label
        self.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(INLINE_PREVIEW_SPACING)

        self._lbl = QLabel()
        self._lbl_value = ResultBadge(color=color, status=status)
        lay.addWidget(self._lbl)
        lay.addWidget(self._lbl_value)
        lay.addStretch()

        self._init_widget_mixin(theme=True, font=True, lang=True, data=False)
        self._refresh_style()
        self._refresh_lang()

    def _refresh_style(self, *_):
        self._lbl.setStyleSheet(
            f"color:{_C['text_sec']}; font-weight:600;"
            f"font-size:{fs(get_font_size(),-1)}pt; background:transparent;"
        )

    def _refresh_lang(self, *_):
        text = self._label_text if self._label_text is not None else tr('inline_preview_label')
        self._lbl.setText(text)

    def set_value(self, text: str):
        self._lbl_value.set_value(text)

    def reset(self):
        self._lbl_value.reset()