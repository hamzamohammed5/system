"""
ui/tabs/accounting/journal/form/_journal_header.py
==================================================
_JournalHeader — صف التاريخ والوصف ونوع القيد في فورم القيد اليومي.

[v2]: إضافة اختيار نوع القيد (يدوي / افتتاحي / ختامي).
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QLineEdit,
    QDateEdit, QComboBox,
)
from PyQt5.QtCore import QDate


_ENTRY_TYPES = [
    ("manual",   "📝 يدوي"),
    ("opening",  "🟢 افتتاحي"),
    ("closing",  "🔴 ختامي"),
    ("transfer", "🔄 ترحيل"),
]


class _JournalHeader(QWidget):
    """
    صف بيانات القيد:
      [التاريخ: ___] [النوع: ▼] [الوصف: ___________________________]

    الاستخدام:
        hdr = _JournalHeader()
        date_str    = hdr.date_str()       # "2025-01-15"
        desc        = hdr.description()    # "قيد شراء..."
        entry_type  = hdr.entry_type()     # "manual"
        hdr.reset()
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        # ── التاريخ ──
        self.dt_date = QDateEdit(QDate.currentDate())
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDisplayFormat("yyyy-MM-dd")
        self.dt_date.setFixedWidth(130)
        self.dt_date.setMinimumHeight(30)

        # ── نوع القيد ──
        self.cmb_type = QComboBox()
        self.cmb_type.setMinimumHeight(30)
        self.cmb_type.setFixedWidth(110)
        for key, label in _ENTRY_TYPES:
            self.cmb_type.addItem(label, key)
        self.cmb_type.setStyleSheet("""
            QComboBox {
                background: white;
                border: 1px solid #c5cae9;
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 11px;
            }
            QComboBox:focus { border-color: #1565c0; }
            QComboBox::drop-down { border: none; }
        """)

        # ── الوصف ──
        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("وصف القيد الإجمالي...")
        self.inp_desc.setMinimumHeight(30)

        lay.addWidget(QLabel("التاريخ:"))
        lay.addWidget(self.dt_date)
        lay.addSpacing(6)
        lay.addWidget(QLabel("النوع:"))
        lay.addWidget(self.cmb_type)
        lay.addSpacing(6)
        lay.addWidget(QLabel("الوصف:"))
        lay.addWidget(self.inp_desc, stretch=1)

    # ── API خارجي ──────────────────────────────────────

    def date_str(self) -> str:
        """يرجع التاريخ بصيغة 'yyyy-MM-dd'."""
        return self.dt_date.date().toString("yyyy-MM-dd")

    def description(self) -> str:
        """يرجع نص الوصف مجتزأ الفراغات."""
        return self.inp_desc.text().strip()

    def entry_type(self) -> str:
        """يرجع نوع القيد ('manual', 'opening', ...)."""
        return self.cmb_type.currentData() or "manual"

    def reset(self):
        """يعيد التاريخ لليوم ويمسح الوصف ويعيد النوع لـ manual."""
        self.dt_date.setDate(QDate.currentDate())
        self.inp_desc.clear()
        self.cmb_type.setCurrentIndex(0)