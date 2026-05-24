"""
ui/widgets/shared/date_range_filter.py
========================================
DateRangeFilter — فلتر نطاق التاريخ الموحد.

يحل محل الكود المكرر في:
  - _JournalFilterBar
  - _LedgerFilterBar
  - أي شريط فلاتر يحتوي على من/إلى

الاستخدام:
    from ui.widgets.shared.date_range_filter import DateRangeFilter

    date_filter = DateRangeFilter()
    layout.addLayout(date_filter.layout())

    # فلترة:
    if date_filter.in_range(date_str):
        ...

    # ربط signal:
    date_filter.range_changed.connect(self._apply_filter)
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QDateEdit,
)
from PyQt5.QtCore import QDate, pyqtSignal

from ui.app_settings import _C, fs
from ui.widgets.shared.panles_helper.colors_and_base import _base

_DATE_STYLE = f"""
    QDateEdit {{
        background: white;
        border: 1px solid {_C.get('border_med', '#c5cae9')};
        border-radius: 5px;
        padding: 2px 6px;
        font-size: 11px;
    }}
    QDateEdit:focus {{ border-color: {_C.get('accent', '#1565c0')}; }}
    QDateEdit::drop-down {{ border: none; width: 20px; }}
"""

_LBL_STYLE = (
    "background: transparent; border: none; font-weight: bold;"
    "font-size: 11px; color: #555;"
)


class DateRangeFilter(QWidget):
    """
    فلتر نطاق التاريخ: [من: ___] [إلى: ___]

    Signals:
        range_changed — يُطلق عند تغيير أي تاريخ

    الاستخدام:
        f = DateRangeFilter()
        layout.addWidget(f)
        f.range_changed.connect(self._filter)

        # في الفلترة:
        if f.in_range("2024-03-15"):
            ...

        # إعادة تعيين:
        f.reset()
    """

    range_changed = pyqtSignal()

    def __init__(self,
                 default_from: QDate = None,
                 default_to: QDate = None,
                 width: int = 115,
                 height: int = 30,
                 parent=None):
        super().__init__(parent)
        self._width   = width
        self._height  = height
        self._default_from = default_from or QDate(2000, 1, 1)
        self._default_to   = default_to or QDate.currentDate()
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        lbl_from = QLabel("من:")
        lbl_from.setStyleSheet(_LBL_STYLE)

        self.dt_from = QDateEdit()
        self.dt_from.setCalendarPopup(True)
        self.dt_from.setDisplayFormat("yyyy-MM-dd")
        self.dt_from.setDate(self._default_from)
        self.dt_from.setFixedWidth(self._width)
        self.dt_from.setMinimumHeight(self._height)
        self.dt_from.setStyleSheet(_DATE_STYLE)
        self.dt_from.dateChanged.connect(self.range_changed.emit)

        lbl_to = QLabel("إلى:")
        lbl_to.setStyleSheet(_LBL_STYLE)

        self.dt_to = QDateEdit()
        self.dt_to.setCalendarPopup(True)
        self.dt_to.setDisplayFormat("yyyy-MM-dd")
        self.dt_to.setDate(self._default_to)
        self.dt_to.setFixedWidth(self._width)
        self.dt_to.setMinimumHeight(self._height)
        self.dt_to.setStyleSheet(_DATE_STYLE)
        self.dt_to.dateChanged.connect(self.range_changed.emit)

        lay.addWidget(lbl_from)
        lay.addWidget(self.dt_from)
        lay.addWidget(lbl_to)
        lay.addWidget(self.dt_to)

    def in_range(self, date_str: str) -> bool:
        """
        يتحقق لو التاريخ المحدد في النطاق.

        date_str: تاريخ بصيغة "yyyy-MM-dd"
        """
        if not date_str:
            return True
        try:
            d = QDate.fromString(date_str, "yyyy-MM-dd")
            return self.dt_from.date() <= d <= self.dt_to.date()
        except Exception:
            return True

    def reset(self):
        """يعيد التواريخ للقيم الافتراضية."""
        self.dt_from.blockSignals(True)
        self.dt_to.blockSignals(True)
        self.dt_from.setDate(self._default_from)
        self.dt_to.setDate(self._default_to)
        self.dt_from.blockSignals(False)
        self.dt_to.blockSignals(False)
        self.range_changed.emit()

    @property
    def from_date(self) -> QDate:
        return self.dt_from.date()

    @property
    def to_date(self) -> QDate:
        return self.dt_to.date()

    def set_from(self, date: QDate):
        self.dt_from.setDate(date)

    def set_to(self, date: QDate):
        self.dt_to.setDate(date)