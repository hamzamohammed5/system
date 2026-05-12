"""
ui/tabs/costing/labor/labor_settings.py
========================================
_LaborSettingsPanel — لوحة إعدادات معايير حساب تكلفة العمالة.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QDoubleSpinBox, QLabel, QGroupBox, QPushButton, QMessageBox,
)
from PyQt5.QtCore import Qt

from db.settings_repo import get_setting, set_setting
from ui.events import bus


def _spin(max_=999999, dec=2):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(30)
    return s


def _labeled(widget, unit):
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(6)
    lay.addWidget(widget)
    lay.addWidget(QLabel(unit))
    lay.addStretch()
    return w


class _LaborSettingsPanel(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self._load()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        grp  = QGroupBox("معايير حساب تكلفة العمالة")
        form = QFormLayout(grp)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.sp_salary   = _spin()
        self.sp_days     = _spin(31, 0)
        self.sp_holidays = _spin(31, 0)
        self.sp_hours    = _spin(24, 1)
        self.sp_overhead = _spin(10, 2)

        form.addRow("الراتب الأساسي :",         _labeled(self.sp_salary,   "جنيه / شهر"))
        form.addRow("أيام العمل :",             _labeled(self.sp_days,     "يوم / شهر"))
        form.addRow("أيام الإجازات :",          _labeled(self.sp_holidays, "يوم / شهر"))
        form.addRow("ساعات العمل / يوم :",      _labeled(self.sp_hours,    "ساعة / يوم"))
        form.addRow("معامل الأعباء الإدارية :", _labeled(self.sp_overhead, "×"))

        self.lbl_rate = QLabel("─")
        self.lbl_rate.setStyleSheet(
            "font-weight:bold; color:#1a6e1a; font-size:13px;"
            "background:#f0faf0; border:1px solid #b2dfb2;"
            "border-radius:4px; padding:4px 8px;"
        )
        form.addRow("➡  معدل الأجر / ساعة :", self.lbl_rate)
        layout.addWidget(grp)

        for sp in (self.sp_salary, self.sp_days, self.sp_holidays,
                   self.sp_hours, self.sp_overhead):
            sp.valueChanged.connect(self._update_preview)

        btn = QPushButton("💾  حفظ إعدادات العمالة")
        btn.setMinimumHeight(32)
        btn.clicked.connect(self._save)
        layout.addWidget(btn)
        layout.addStretch()

    def _calc_rate(self):
        net_days  = max(self.sp_days.value() - self.sp_holidays.value(), 1)
        net_hours = net_days * max(self.sp_hours.value(), 1)
        return (self.sp_salary.value() / net_hours) * self.sp_overhead.value() if net_hours else 0.0

    def _update_preview(self):
        self.lbl_rate.setText(f"{self._calc_rate():.2f}  جنيه / ساعة")

    def _load(self):
        self.sp_salary.setValue(  get_setting(self.conn, "monthly_salary",    3000))
        self.sp_days.setValue(    get_setting(self.conn, "working_days",         25))
        self.sp_holidays.setValue(get_setting(self.conn, "holiday_days",          4))
        self.sp_hours.setValue(   get_setting(self.conn, "working_hours_day",     8))
        self.sp_overhead.setValue(get_setting(self.conn, "overhead_factor",    1.10))
        self._update_preview()

    def _save(self):
        set_setting(self.conn, "monthly_salary",    self.sp_salary.value())
        set_setting(self.conn, "working_days",      self.sp_days.value())
        set_setting(self.conn, "holiday_days",      self.sp_holidays.value())
        set_setting(self.conn, "working_hours_day", self.sp_hours.value())
        set_setting(self.conn, "overhead_factor",   self.sp_overhead.value())
        QMessageBox.information(self, "تم", "✅  تم حفظ إعدادات العمالة")
        bus.data_changed.emit()

    def get_hourly_rate(self):
        return self._calc_rate()