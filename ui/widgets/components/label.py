"""
ui/widgets/components/label.py
================================
InfoRow + ModeLabel — الـ widgets الأصلية لهذا الملف.

باقي الـ classes أصبح لها ملفات مصدر مستقلة:
  - ProgressBar, MultiProgressBar  → progress.py
  - AmountLabel, DebitCreditDisplay, BalanceDisplay,
    format_amount, amount_color, dr_cr_color         → amount_label.py

للاستيراد الصحيح:
    from ui.widgets.components.progress     import ProgressBar, MultiProgressBar
    from ui.widgets.components.amount_label import AmountLabel, format_amount, ...
"""
from __future__ import annotations

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore    import Qt

from ui.theme import _C
from ui.font  import fs, get_font_size
from ..core.i18n import tr
from ..core.widget_mixin import WidgetMixin


# ══════════════════════════════════════════════════════════
# InfoRow
# ══════════════════════════════════════════════════════════

class InfoRow(QWidget, WidgetMixin):
    """صف معلومات ثانوية مفصولة بـ separator."""

    def __init__(self, separator: str = None, parent=None):
        super().__init__(parent)
        self._custom_separator = separator
        self._lbl = QLabel()
        self._lbl.setWordWrap(True)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._lbl)
        self._parts = []
        self._init_widget_mixin(theme=True, font=True, lang=True)
        self._refresh_style()

    @property
    def _separator(self) -> str:
        return self._custom_separator if self._custom_separator is not None else tr('info_row_separator')

    def _refresh_style(self, *_):
        self._lbl.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{fs(get_font_size(), -1)}pt;"
            "background:transparent; border:none;"
        )

    def _refresh_lang(self, *_):
        if self._parts:
            self._lbl.setText(self._separator.join(self._parts))

    def set_parts(self, parts: list):
        self._parts = [str(p) for p in parts if p]
        self._lbl.setText(self._separator.join(self._parts) if self._parts else "")

    def set_text(self, text: str):
        self._parts = []
        self._lbl.setText(text)

    def label(self) -> QLabel:
        return self._lbl


# ══════════════════════════════════════════════════════════
# ModeLabel
# ══════════════════════════════════════════════════════════

class ModeLabel(QLabel, WidgetMixin):
    """
    Label يُظهر وضع الفورم الحالي.
    أزرق = إضافة، برتقالي = تعديل.
    """

    def __init__(self, add_text: str = None,
                 icon: str = "", parent=None):
        super().__init__(parent)
        self._custom_add_text = add_text
        self._icon       = icon
        self._is_edit     = False
        self._edit_name   = ""
        self._custom_text  = None
        self._custom_color = None
        self._add_mode_text = None
        self._init_widget_mixin(theme=True, font=True, lang=True)
        self.set_add_mode()

    @property
    def _add_text(self) -> str:
        return self._custom_add_text if self._custom_add_text is not None else tr('new')

    def set_add_mode(self, text: str = None):
        self._is_edit = False
        self._custom_text = None
        self._add_mode_text = text
        self._render_add_mode()

    def _render_add_mode(self):
        prefix  = f"{self._icon}  " if self._icon else ""
        display = self._add_mode_text or self._add_text
        self.setText(tr('mode_label_wrap').format(content=f"{prefix}{display}"))
        base = get_font_size()
        self.setStyleSheet(
            f"font-weight:bold; font-size:{fs(base, 0)}pt;"
            f"color:{_C['accent']}; background:transparent; border:none;"
        )

    def set_edit_mode(self, name: str = ""):
        self._is_edit = True
        self._custom_text = None
        self._edit_name = name
        self._render_edit_mode()

    def _render_edit_mode(self):
        prefix = f"{self._icon}  " if self._icon else ""
        suffix = f": {self._edit_name}" if self._edit_name else ""
        self.setText(tr('mode_label_wrap').format(content=f"{prefix}{tr('edit')}{suffix}"))
        base = get_font_size()
        self.setStyleSheet(
            f"font-weight:bold; font-size:{fs(base, 0)}pt;"
            f"color:{_C['warning']}; background:transparent; border:none;"
        )

    def set_custom(self, text: str, color: str = None):
        self._custom_text  = text
        self._custom_color = color
        self._render_custom()

    def _render_custom(self):
        base = get_font_size()
        self.setText(self._custom_text)
        self.setStyleSheet(
            f"font-weight:bold; font-size:{fs(base, 0)}pt;"
            f"color:{self._custom_color or _C['text_sec']}; background:transparent; border:none;"
        )

    def _refresh_style(self, *_):
        if self._custom_text is not None:
            self._render_custom()
        elif self._is_edit:
            self._render_edit_mode()
        else:
            self._render_add_mode()

    def _refresh_lang(self, *_):
        # النص المخصص (set_custom) خارج إدارة الترجمة — لا نلمسه
        if self._custom_text is not None:
            return
        if self._is_edit:
            self._render_edit_mode()
        else:
            self._render_add_mode()

    @property
    def is_edit_mode(self) -> bool:
        return self._is_edit