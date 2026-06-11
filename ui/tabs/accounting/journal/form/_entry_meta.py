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
from ui.theme import _C
from ui.widgets.core.i18n import tr

def _get_type_colors(entry_type: str) -> tuple:
    """يرجع (fg, bg, border) من _C حسب نوع القيد."""
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
        "manual":   tr("entry_type_manual").replace("📝 ", ""),
        "opening":  tr("entry_type_opening").replace("🟢 ", ""),
        "closing":  tr("entry_type_closing").replace("🔴 ", ""),
        "transfer": tr("entry_type_transfer").replace("🔄 ", ""),
        "auto":     tr("entry_type_auto").replace("🤖 ", ""),
    }
    return mapping.get(entry_type, entry_type)


class _EntryTypeBadge(QLabel):
    """
    Badge لعرض نوع القيد بألوان موحدة.

    الاستخدام:
        badge = _EntryTypeBadge("manual")
        badge.set_type("opening")
    """

    def __init__(self, entry_type: str = "manual", parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.set_type(entry_type)

    def set_type(self, entry_type: str):
        fg, bg, border = _get_type_colors(entry_type)
        label = _get_type_label(entry_type)
        self.setText(label)
        self.setStyleSheet(
            f"QLabel {{ color: {fg}; background: {bg}; border: 1px solid {border};"            "border-radius: 4px; padding: 2px 10px; font-size: 10px; font-weight: bold; }}"
        )


class _EntryRefLabel(QLabel):
    """
    Label لعرض رقم مرجعي للقيد.

    الاستخدام:
        ref = _EntryRefLabel("QD-2025-001")
    """

    def __init__(self, ref_no: str = "─", parent=None):
        super().__init__(ref_no, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            f"QLabel {{ color: {_C['badge_dr_text']}; background: {_C['accent_light']};"            f"border: 1px solid {_C['accent_mid']};"            "border-radius: 4px; padding: 2px 10px; font-size: 11px; font-weight: bold; font-family: monospace; }}"
        )

    def set_ref(self, ref_no: str):
        self.setText(ref_no or "─")