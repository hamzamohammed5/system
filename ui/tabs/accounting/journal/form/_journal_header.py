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
from ui.widgets.core.i18n import tr
from ui.theme import _C
from ui.font import FS_SM


def _get_entry_types():
    return [
        ("manual",   tr("entry_type_manual")),
        ("opening",  tr("entry_type_opening")),
        ("closing",  tr("entry_type_closing")),
        ("transfer", tr("entry_type_transfer")),
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
        for key, label in _get_entry_types():
            self.cmb_type.addItem(label, key)
        self.cmb_type.setStyleSheet(
            f"QComboBox {{"
            f"    background: {_C['bg_input']};"
            f"    border: 1px solid {_C['border_med']};"
            f"    border-radius: 4px;"
            f"    padding: 2px 6px;"
            f"    font-size: {FS_SM}px;"
            f"}}"
            f"QComboBox:focus {{ border-color: {_C['accent']}; }}"
            f"QComboBox::drop-down {{ border: none; }}"
        )

        # ── الوصف ──
        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText(tr("entry_description_placeholder"))
        self.inp_desc.setMinimumHeight(30)

        lay.addWidget(QLabel(tr("entry_date_label")))
        lay.addWidget(self.dt_date)
        lay.addSpacing(6)
        lay.addWidget(QLabel(tr("entry_type_label")))
        lay.addWidget(self.cmb_type)
        lay.addSpacing(6)
        lay.addWidget(QLabel(tr("entry_desc_label")))
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