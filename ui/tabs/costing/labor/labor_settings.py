"""
ui/tabs/costing/labor/labor_settings.py
========================================
_LaborSettingsPanel — لوحة إعدادات معايير حساب تكلفة العمالة.

التحسينات:
  - يستخدم form_utils: FormGroup, labeled_widget, spin_field, ResultBadge
  - يستخدم build_inner_scroll بدل بناء الـ scroll يدوياً
"""

from PyQt5.QtWidgets import (
    QWidget, QPushButton, QMessageBox, QSizePolicy,
)

from db.shared.settings_repo import get_setting, set_setting
from ui.widgets.shared.form_utils import (
    FormGroup, labeled_widget, spin_field, ResultBadge, build_inner_scroll,
)
from ui.events import bus


class _LaborSettingsPanel(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self._load()

    def _build(self):
        _outer, _inner, layout = build_inner_scroll(self, min_width=260)

        grp = FormGroup("معايير حساب تكلفة العمالة")

        self.sp_salary   = spin_field(max_=999999, dec=2)
        self.sp_days     = spin_field(max_=31,     dec=0)
        self.sp_holidays = spin_field(max_=31,     dec=0)
        self.sp_hours    = spin_field(max_=24,     dec=1)
        self.sp_overhead = spin_field(max_=10,     dec=2)

        grp.add_row("الراتب الأساسي :",         labeled_widget(self.sp_salary,   "جنيه / شهر"))
        grp.add_row("أيام العمل :",             labeled_widget(self.sp_days,     "يوم / شهر"))
        grp.add_row("أيام الإجازات :",          labeled_widget(self.sp_holidays, "يوم / شهر"))
        grp.add_row("ساعات العمل / يوم :",      labeled_widget(self.sp_hours,    "ساعة / يوم"))
        grp.add_row("معامل الأعباء الإدارية :", labeled_widget(self.sp_overhead, "×"))

        self.lbl_rate = ResultBadge()
        grp.add_row("➡  معدل الأجر / ساعة :", self.lbl_rate)
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
        self.lbl_rate.set_value(f"{self._calc_rate():.2f}  جنيه / ساعة")

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