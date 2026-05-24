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

# ألوان أنواع القيود — متوافقة مع TYPE_COLORS في helpers.py
_TYPE_COLORS = {
    "manual":   ("#1565c0", "#e8f0fe", "#90caf9"),
    "opening":  ("#2e7d32", "#e8f5e9", "#a5d6a7"),
    "closing":  ("#6a1b9a", "#f3e5f5", "#ce93d8"),
    "transfer": ("#e65100", "#fff3e0", "#ffcc80"),
    "auto":     ("#0891b2", "#e0f7fa", "#80deea"),
}

_TYPE_LABELS = {
    "manual":   "يدوي",
    "opening":  "افتتاحي",
    "closing":  "ختامي",
    "transfer": "ترحيل",
    "auto":     "تلقائي",
}


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
        fg, bg, border = _TYPE_COLORS.get(entry_type, ("#555", "#f5f5f5", "#e0e0e0"))
        label = _TYPE_LABELS.get(entry_type, entry_type)
        self.setText(label)
        self.setStyleSheet(f"""
            QLabel {{
                color: {fg};
                background: {bg};
                border: 1px solid {border};
                border-radius: 4px;
                padding: 2px 10px;
                font-size: 10px;
                font-weight: bold;
            }}
        """)


class _EntryRefLabel(QLabel):
    """
    Label لعرض رقم مرجعي للقيد.

    الاستخدام:
        ref = _EntryRefLabel("QD-2025-001")
    """

    def __init__(self, ref_no: str = "─", parent=None):
        super().__init__(ref_no, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                color: #1565c0;
                background: #e8f0fe;
                border: 1px solid #90caf9;
                border-radius: 4px;
                padding: 2px 10px;
                font-size: 11px;
                font-weight: bold;
                font-family: monospace;
            }
        """)

    def set_ref(self, ref_no: str):
        self.setText(ref_no or "─")