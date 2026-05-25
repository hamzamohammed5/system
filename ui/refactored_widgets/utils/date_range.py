"""
ui/widgets/utils/date_range.py
================================
DateRangeFilter — فلتر نطاق التاريخ الموحد.
"""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QDateEdit, QPushButton
from PyQt5.QtCore    import QDate, pyqtSignal

from ui.app_settings import _C

_DATE_STYLE = f"""
    QDateEdit {{
        background:white; border:1px solid {_C.get('border_med','#c5cae9')};
        border-radius:5px; padding:2px 6px; font-size:11px;
    }}
    QDateEdit:focus {{ border-color:{_C.get('accent','#1565c0')}; }}
    QDateEdit::drop-down {{ border:none; width:20px; }}
"""
_LBL  = "background:transparent; border:none; font-weight:bold; font-size:11px; color:#555;"
_BTN  = """
    QPushButton {
        background:#e8eaf6; border:1px solid #c5cae9; border-radius:4px;
        color:#3949ab; font-size:10px; padding:2px 6px; min-height:22px;
    }
    QPushButton:hover { background:#c5cae9; }
"""


class DateRangeFilter(QWidget):
    """فلتر [من: ___] [إلى: ___] مع اختصارات سريعة اختيارية."""

    range_changed = pyqtSignal()

    def __init__(self, default_from: QDate = None, default_to: QDate = None,
                 width: int = 115, height: int = 30,
                 show_presets: bool = False, parent=None):
        super().__init__(parent)
        self._default_from = default_from or QDate(2000, 1, 1)
        self._default_to   = default_to   or QDate.currentDate()
        self._build(width, height, show_presets)

    def _build(self, width, height, show_presets):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        def _date_edit(default):
            d = QDateEdit()
            d.setCalendarPopup(True)
            d.setDisplayFormat("yyyy-MM-dd")
            d.setDate(default)
            d.setFixedWidth(width)
            d.setMinimumHeight(height)
            d.setStyleSheet(_DATE_STYLE)
            return d

        lbl_from = QLabel("من:")
        lbl_from.setStyleSheet(_LBL)
        self.dt_from = _date_edit(self._default_from)
        self.dt_from.dateChanged.connect(self.range_changed.emit)

        lbl_to = QLabel("إلى:")
        lbl_to.setStyleSheet(_LBL)
        self.dt_to = _date_edit(self._default_to)
        self.dt_to.dateChanged.connect(self.range_changed.emit)

        for w in (lbl_from, self.dt_from, lbl_to, self.dt_to):
            lay.addWidget(w)

        if show_presets:
            for label, slot in [("اليوم", self._preset_today),
                                 ("الشهر", self._preset_month),
                                 ("العام",  self._preset_year)]:
                btn = QPushButton(label)
                btn.setStyleSheet(_BTN)
                btn.clicked.connect(slot)
                lay.addWidget(btn)

    def _set_range(self, from_date: QDate, to_date: QDate):
        for d in (self.dt_from, self.dt_to):
            d.blockSignals(True)
        self.dt_from.setDate(from_date)
        self.dt_to.setDate(to_date)
        for d in (self.dt_from, self.dt_to):
            d.blockSignals(False)
        self.range_changed.emit()

    def _preset_today(self):
        t = QDate.currentDate()
        self._set_range(t, t)

    def _preset_month(self):
        t = QDate.currentDate()
        self._set_range(QDate(t.year(), t.month(), 1), t)

    def _preset_year(self):
        t = QDate.currentDate()
        self._set_range(QDate(t.year(), 1, 1), t)

    def in_range(self, date_str: str) -> bool:
        if not date_str:
            return True
        try:
            d = QDate.fromString(date_str, "yyyy-MM-dd")
            return self.dt_from.date() <= d <= self.dt_to.date()
        except Exception:
            return True

    def reset(self):
        self._set_range(self._default_from, self._default_to)

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