"""
ui/widgets/utils/date_range.py
================================
DateRangeFilter — فلتر نطاق التاريخ الموحد.
"""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QDateEdit, QPushButton
from PyQt5.QtCore    import QDate, pyqtSignal

from ui.app_settings     import _C, fs, get_font_size
from ..utils.signals     import blocked_signals
from ..components.button import make_btn


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
            # ← استخدام _C بدل raw CSS strings hardcoded
            base = get_font_size()
            d.setStyleSheet(f"""
                QDateEdit {{
                    background:{_C['bg_input']};
                    border:1px solid {_C['border_med']};
                    border-radius:5px; padding:2px 6px;
                    font-size:{fs(base, -1)}pt;
                    color:{_C['text_primary']};
                }}
                QDateEdit:focus {{ border-color:{_C['accent']}; }}
                QDateEdit::drop-down {{ border:none; width:20px; }}
            """)
            return d

        base     = get_font_size()
        lbl_style = (
            f"background:transparent; border:none; font-weight:bold;"
            f"font-size:{fs(base, -1)}pt; color:{_C['text_sec']};"
        )

        lbl_from = QLabel("من:")
        lbl_from.setStyleSheet(lbl_style)
        self.dt_from = _date_edit(self._default_from)
        self.dt_from.dateChanged.connect(self.range_changed.emit)

        lbl_to = QLabel("إلى:")
        lbl_to.setStyleSheet(lbl_style)
        self.dt_to = _date_edit(self._default_to)
        self.dt_to.dateChanged.connect(self.range_changed.emit)

        for w in (lbl_from, self.dt_from, lbl_to, self.dt_to):
            lay.addWidget(w)

        if show_presets:
            for label, slot in [("اليوم", self._preset_today),
                                 ("الشهر", self._preset_month),
                                 ("العام",  self._preset_year)]:
                # ← استخدام make_btn بدل raw QPushButton + stylesheet hardcoded
                btn = make_btn(label, "normal")
                btn.setMinimumHeight(height)
                btn.clicked.connect(slot)
                lay.addWidget(btn)

    def _set_range(self, from_date: QDate, to_date: QDate):
        # ← استخدام blocked_signals بدل blockSignals يدوي
        with blocked_signals(self.dt_from, self.dt_to):
            self.dt_from.setDate(from_date)
            self.dt_to.setDate(to_date)
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