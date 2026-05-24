"""
ui/tabs/accounting/journal/form/_journal_header.py
==================================================
_JournalHeader — صف التاريخ والوصف في فورم القيد اليومي.

مُستخرج من journal_form.py لتقليل الحجم.
يُستخدم فقط من _JournalForm.
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QLineEdit, QDateEdit,
)
from PyQt5.QtCore import QDate


class _JournalHeader(QWidget):
    """
    صف التاريخ والوصف في فورم القيد:
      [التاريخ: ___] [الوصف: ___________________________]

    الاستخدام:
        hdr = _JournalHeader()
        date_str = hdr.date_str()    # "2025-01-15"
        desc     = hdr.description() # "قيد شراء..."
        hdr.reset()                  # يعيد التاريخ لليوم ويمسح الوصف
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self.dt_date = QDateEdit(QDate.currentDate())
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDisplayFormat("yyyy-MM-dd")
        self.dt_date.setFixedWidth(130)
        self.dt_date.setMinimumHeight(30)

        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("وصف القيد الإجمالي...")
        self.inp_desc.setMinimumHeight(30)

        lay.addWidget(QLabel("التاريخ:"))
        lay.addWidget(self.dt_date)
        lay.addSpacing(12)
        lay.addWidget(QLabel("الوصف:"))
        lay.addWidget(self.inp_desc, stretch=1)

    # ── API خارجي ──────────────────────────────────────

    def date_str(self) -> str:
        """يرجع التاريخ بصيغة 'yyyy-MM-dd'."""
        return self.dt_date.date().toString("yyyy-MM-dd")

    def description(self) -> str:
        """يرجع نص الوصف مجتزأ الفراغات."""
        return self.inp_desc.text().strip()

    def reset(self):
        """يعيد التاريخ لليوم ويمسح الوصف."""
        self.dt_date.setDate(QDate.currentDate())
        self.inp_desc.clear()