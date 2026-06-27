"""
ui/tabs/accounting/journal/form/_entry_meta.py
===============================================
_EntryTypeBadge — badge موحد لنوع القيد المحاسبي.
_EntryRefLabel  — label موحد لرقم مرجعي للقيد.

مُستخرج لتجنب التكرار في أي مكان يعرض نوع القيد.

الاستخدام:
    badge = _EntryTypeBadge("manual")
    layout.addWidget(badge)

    ref = _EntryRefLabel("QD-2025-001")
    layout.addWidget(ref)
"""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
from ui.widgets.core.i18n import tr
from ui.font import FS_XS, FS_SM
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import (
    ENTRY_BADGE_BORDER_W, ENTRY_BADGE_BORDER_RADIUS, ENTRY_BADGE_PAD_V, ENTRY_BADGE_PAD_H,
    ENTRY_REF_BORDER_W, ENTRY_REF_BORDER_RADIUS, ENTRY_REF_PAD_V, ENTRY_REF_PAD_H,
)

def _get_type_colors(entry_type: str) -> tuple:
    """يرجع (fg, bg, border) من _C حسب نوع القيد."""
    from ui.theme import _C
    mapping = {
        "manual":   (_C["accent"],      _C["accent_light"],    _C["accent_mid"]),
        "opening":  (_C["success"],     _C["success_bg"],      _C["success_border"]),
        "closing":  (_C["purple"],      _C["purple_bg"],       _C["purple_border"]),
        "transfer": (_C["orange"],      _C["orange_bg"],       _C["orange_border"]),
        "auto":     (_C["teal"],        _C["teal_bg"],         _C["teal_border"]),
    }
    return mapping.get(entry_type, (_C["text_sec"], _C["bg_surface_2"], _C["border"]))

def _get_type_label(entry_type: str) -> str:
    mapping = {
        "manual":   tr("entry_type_manual_short"),
        "opening":  tr("entry_type_opening_short"),
        "closing":  tr("entry_type_closing_short"),
        "transfer": tr("entry_type_transfer_short"),
        "auto":     tr("entry_type_auto_short"),
    }
    return mapping.get(entry_type, entry_type)


class _EntryTypeBadge(QLabel, WidgetMixin):
    """
    Badge لعرض نوع القيد بألوان موحدة.

    الاستخدام:
        badge = _EntryTypeBadge("manual")
        badge.set_type("opening")
    """

    def __init__(self, entry_type: str = "manual", parent=None):
        super().__init__(parent)
        self._entry_type = entry_type
        self.setAlignment(Qt.AlignCenter)
        self._init_widget_mixin(data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        self.set_type(self._entry_type)

    def set_type(self, entry_type: str):
        self._entry_type = entry_type
        fg, bg, border = _get_type_colors(entry_type)
        label = _get_type_label(entry_type)
        self.setText(label)
        self.setStyleSheet(
            f"QLabel {{"
            f"    color: {fg};"
            f"    background: {bg};"
            f"    border: {ENTRY_BADGE_BORDER_W}px solid {border};"
            f"    border-radius: {ENTRY_BADGE_BORDER_RADIUS}px;"
            f"    padding: {ENTRY_BADGE_PAD_V}px {ENTRY_BADGE_PAD_H}px;"
            f"    font-size: {FS_XS}px;"
            f"    font-weight: bold;"
            f"}}"
        )


class _EntryRefLabel(QLabel, WidgetMixin):
    """
    Label لعرض رقم مرجعي للقيد.

    الاستخدام:
        ref = _EntryRefLabel("QD-2025-001")
    """

    def __init__(self, ref_no: str = None, parent=None):
        super().__init__(ref_no or tr("amount_dash_placeholder"), parent)
        self.setAlignment(Qt.AlignCenter)
        self._init_widget_mixin(lang=False, data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        from ui.theme import _C
        self.setStyleSheet(
            f"QLabel {{"
            f"    color: {_C['badge_dr_text']};"
            f"    background: {_C['accent_light']};"
            f"    border: {ENTRY_REF_BORDER_W}px solid {_C['accent_mid']};"
            f"    border-radius: {ENTRY_REF_BORDER_RADIUS}px;"
            f"    padding: {ENTRY_REF_PAD_V}px {ENTRY_REF_PAD_H}px;"
            f"    font-size: {FS_SM}px;"
            f"    font-weight: bold;"
            f"    font-family: monospace;"
            f"}}"
        )

    def set_ref(self, ref_no: str):
        self.setText(ref_no or tr("amount_dash_placeholder"))
