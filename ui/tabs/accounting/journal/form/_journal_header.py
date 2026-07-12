"""
ui/tabs/accounting/journal/form/_journal_header.py
==================================================
_JournalHeader — صف التاريخ والوصف ونوع القيد في فورم القيد اليومي.

[v2]: إضافة اختيار نوع القيد (يدوي / افتتاحي / ختامي).
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel,
    QDateEdit
)
from ui.widgets.panels.themed_inputs import ThemedLineEdit, ThemedComboBox

from PyQt5.QtCore import QDate
from ui.widgets.core.i18n import tr
from ui.font import FS_SM
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import (
    MARGIN_ZERO, BTN_MIN_HEIGHT,
    JOURNAL_HEADER_DATE_W, JOURNAL_HEADER_CMB_W, JOURNAL_HEADER_SPACING,
    JOURNAL_HEADER_CMB_RADIUS, JOURNAL_HEADER_CMB_BORDER_W,
    JOURNAL_HEADER_CMB_PAD_V, JOURNAL_HEADER_CMB_PAD_H,
    JOURNAL_HEADER_GROUP_SPACING,
)


def _get_entry_types():
    return [
        ("manual",   tr("entry_type_manual")),
        ("opening",  tr("entry_type_opening")),
        ("closing",  tr("entry_type_closing")),
        ("transfer", tr("entry_type_transfer")),
    ]


class _JournalHeader(QWidget, WidgetMixin):
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
        self._init_widget_mixin(data=False)
        self._build()
        self._refresh_style()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(*MARGIN_ZERO)
        lay.setSpacing(JOURNAL_HEADER_SPACING)

        # ── التاريخ ──
        self.dt_date = QDateEdit(QDate.currentDate())
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDisplayFormat("yyyy-MM-dd")
        self.dt_date.setFixedWidth(JOURNAL_HEADER_DATE_W)
        self.dt_date.setMinimumHeight(BTN_MIN_HEIGHT)

        # ── نوع القيد ──
        self.cmb_type = ThemedComboBox()
        self.cmb_type.setMinimumHeight(BTN_MIN_HEIGHT)
        self.cmb_type.setFixedWidth(JOURNAL_HEADER_CMB_W)
        for key, label in _get_entry_types():
            self.cmb_type.addItem(label, key)

        # ── الوصف ──
        self.inp_desc = ThemedLineEdit()
        self.inp_desc.setPlaceholderText(tr("entry_description_placeholder"))
        self.inp_desc.setMinimumHeight(BTN_MIN_HEIGHT)

        self.lbl_date = QLabel()
        self.lbl_type = QLabel()
        self.lbl_desc = QLabel()

        lay.addWidget(self.lbl_date)
        lay.addWidget(self.dt_date)
        lay.addSpacing(JOURNAL_HEADER_GROUP_SPACING)
        lay.addWidget(self.lbl_type)
        lay.addWidget(self.cmb_type)
        lay.addSpacing(JOURNAL_HEADER_GROUP_SPACING)
        lay.addWidget(self.lbl_desc)
        lay.addWidget(self.inp_desc, stretch=1)

    def _refresh_style(self, *_):
        from ui.theme import _C
        self.lbl_date.setText(tr("entry_date_label"))
        self.lbl_type.setText(tr("entry_type_label"))
        self.lbl_desc.setText(tr("entry_desc_label"))
        self.cmb_type.setStyleSheet(
            f"QComboBox {{"
            f"    background: {_C['bg_input']};"
            f"    border: {JOURNAL_HEADER_CMB_BORDER_W}px solid {_C['border_med']};"
            f"    border-radius: {JOURNAL_HEADER_CMB_RADIUS}px;"
            f"    padding: {JOURNAL_HEADER_CMB_PAD_V}px {JOURNAL_HEADER_CMB_PAD_H}px;"
            f"    font-size: {FS_SM}px;"
            f"}}"
            f"QComboBox:focus {{ border-color: {_C['accent']}; }}"
            f"QComboBox::drop-down {{ border: none; }}"
        )

    def _refresh_lang(self, *_):
        self.lbl_date.setText(tr("entry_date_label"))
        self.lbl_type.setText(tr("entry_type_label"))
        self.lbl_desc.setText(tr("entry_desc_label"))
        self.inp_desc.setPlaceholderText(tr("entry_description_placeholder"))
        current_data = self.cmb_type.currentData()
        self.cmb_type.blockSignals(True)
        self.cmb_type.clear()
        for key, label in _get_entry_types():
            self.cmb_type.addItem(label, key)
        for i in range(self.cmb_type.count()):
            if self.cmb_type.itemData(i) == current_data:
                self.cmb_type.setCurrentIndex(i)
                break
        self.cmb_type.blockSignals(False)

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
