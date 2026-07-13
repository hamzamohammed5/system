"""
ui/widgets/utils/date_range.py
================================
DateRangeFilter — فلتر نطاق التاريخ الموحد.
"""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore    import QDate, pyqtSignal

from ui.widgets.panels.themed_inputs import ThemedDateEdit

from ui.constants import (
    DATE_RANGE_EDIT_W, DATE_RANGE_EDIT_H,
    DATE_RANGE_EDIT_RADIUS, DATE_RANGE_EDIT_PAD_H, DATE_RANGE_EDIT_PAD_V,
    DATE_RANGE_DROPDOWN_W, DATE_RANGE_LAYOUT_SPACING,
    FILTER_DATE_DEFAULT_FROM,
)
from ..utils.signals     import blocked_signals
from ..components.button import make_btn
from ui.widgets.core.widget_mixin import WidgetMixin


class DateRangeFilter(QWidget, WidgetMixin):
    """فلتر [من: ___] [إلى: ___] مع اختصارات سريعة اختيارية."""

    range_changed = pyqtSignal()

    def __init__(self, default_from: QDate = None, default_to: QDate = None,
                 width: int = DATE_RANGE_EDIT_W, height: int = DATE_RANGE_EDIT_H,
                 show_presets: bool = False, parent=None):
        super().__init__(parent)
        self._default_from = default_from or QDate(*FILTER_DATE_DEFAULT_FROM)
        self._default_to   = default_to   or QDate.currentDate()
        self._edit_width   = width
        self._edit_height  = height
        self._show_presets = show_presets
        self._build(width, height, show_presets)
        self._init_widget_mixin(lang=True, data=False)
        self._refresh_style()
        self._refresh_lang()

    def _build(self, width, height, show_presets):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(DATE_RANGE_LAYOUT_SPACING)

        self.dt_from = self._make_date_edit(self._default_from, width, height)
        self.dt_from.dateChanged.connect(self.range_changed.emit)

        self.dt_to = self._make_date_edit(self._default_to, width, height)
        self.dt_to.dateChanged.connect(self.range_changed.emit)

        self.lbl_from = QLabel()
        self.lbl_to   = QLabel()

        for w in (self.lbl_from, self.dt_from, self.lbl_to, self.dt_to):
            lay.addWidget(w)

        self._preset_btns = []
        if show_presets:
            for slot in (self._preset_today, self._preset_month, self._preset_year):
                btn = make_btn("", "normal")
                btn.setMinimumHeight(height)
                btn.clicked.connect(slot)
                lay.addWidget(btn)
                self._preset_btns.append(btn)

    def _make_date_edit(self, default: QDate, width: int, height: int) -> ThemedDateEdit:
        d = ThemedDateEdit()
        d.setCalendarPopup(True)
        d.setDisplayFormat("yyyy-MM-dd")
        d.setDate(default)
        d.setFixedWidth(width)
        d.setMinimumHeight(height)
        return d

    def _refresh_style(self, *_):
        from ui.theme import _C
        from ui.font import fs, get_font_size
        base = get_font_size()
        date_ss = f"""
            QDateEdit {{
                background:{_C['bg_input']};
                border:1px solid {_C['border_med']};
                border-radius:{DATE_RANGE_EDIT_RADIUS}px;
                padding:{DATE_RANGE_EDIT_PAD_V}px {DATE_RANGE_EDIT_PAD_H}px;
                font-size:{fs(base, -1)}pt;
                color:{_C['text_primary']};
            }}
            QDateEdit:focus {{ border-color:{_C['accent']}; }}
            QDateEdit::drop-down {{ border:none; width:{DATE_RANGE_DROPDOWN_W}px; }}
        """
        lbl_ss = (
            f"background:transparent; border:none; font-weight:bold;"
            f"font-size:{fs(base, -1)}pt; color:{_C['text_sec']};"
        )
        self.dt_from.setStyleSheet(date_ss)
        self.dt_to.setStyleSheet(date_ss)
        self.lbl_from.setStyleSheet(lbl_ss)
        self.lbl_to.setStyleSheet(lbl_ss)

    def _refresh_lang(self, *_):
        from ui.widgets.core.i18n import tr
        self.lbl_from.setText(tr('date_from'))
        self.lbl_to.setText(tr('date_to'))
        preset_keys = ('today', 'this_month', 'this_year')
        for btn, key in zip(self._preset_btns, preset_keys):
            btn.setText(tr(key))

    def _set_range(self, from_date: QDate, to_date: QDate):
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
