"""
ui/tabs/costing/labor/labor_settings.py
========================================
_LaborSettingsPanel — لوحة إعدادات معايير حساب تكلفة العمالة.

[Refactor] استخدام المسارات الموثقة في files_reference:
  - FormGroup, labeled_widget, spin_field, ResultBadge → ui.widgets.panels.form_parts
  - wrap_in_scroll → ui.widgets.theme.styles
[Refactor] كل النصوص عبر tr() + _C للألوان.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QMessageBox,
)

from db.shared.settings_repo import get_setting, set_setting
from ui.widgets.panels.form_fields import (labeled_widget, spin_field)
from ui.widgets.panels.form_badges import ResultBadge

from ui.widgets.panels.form_group import FormGroup


from ui.widgets.theme.builders import wrap_in_scroll
from ui.widgets.core.i18n import tr
from ui.widgets.core.events import bus, emit_company_data_changed


class _LaborSettingsPanel(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self._load()

    def _build(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        inner = QWidget()
        inner.setMinimumWidth(260)
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        scroll = wrap_in_scroll(inner)
        outer_layout.addWidget(scroll)

        grp = FormGroup(tr("labor_cost_settings"))

        self.sp_salary   = spin_field(max_=999999, dec=2)
        self.sp_days     = spin_field(max_=31,     dec=0)
        self.sp_holidays = spin_field(max_=31,     dec=0)
        self.sp_hours    = spin_field(max_=24,     dec=1)
        self.sp_overhead = spin_field(max_=10,     dec=2)

        grp.add_row(
            f"{tr('base_salary')} :",
            labeled_widget(self.sp_salary,   f"{tr('currency')} / {tr('month')}")
        )
        grp.add_row(
            f"{tr('working_days')} :",
            labeled_widget(self.sp_days,     f"{tr('day')} / {tr('month')}")
        )
        grp.add_row(
            f"{tr('holiday_days')} :",
            labeled_widget(self.sp_holidays, f"{tr('day')} / {tr('month')}")
        )
        grp.add_row(
            f"{tr('working_hours_per_day')} :",
            labeled_widget(self.sp_hours,    f"{tr('hour')} / {tr('day')}")
        )
        grp.add_row(
            f"{tr('overhead_factor')} :",
            labeled_widget(self.sp_overhead, "×")
        )

        self.lbl_rate = ResultBadge()
        grp.add_row(f"➡  {tr('hourly_rate')} :", self.lbl_rate)
        layout.addWidget(grp)

        for sp in (self.sp_salary, self.sp_days, self.sp_holidays,
                   self.sp_hours, self.sp_overhead):
            sp.valueChanged.connect(self._update_preview)

        btn = QPushButton(f"💾  {tr('save_labor_settings')}")
        btn.setMinimumHeight(32)
        btn.clicked.connect(self._save)
        layout.addWidget(btn)
        layout.addStretch()

    def _calc_rate(self):
        net_days  = max(self.sp_days.value() - self.sp_holidays.value(), 1)
        net_hours = net_days * max(self.sp_hours.value(), 1)
        return (self.sp_salary.value() / net_hours) * self.sp_overhead.value() \
               if net_hours else 0.0

    def _update_preview(self):
        self.lbl_rate.set_value(f"{self._calc_rate():.2f}  {tr('currency_per_hour')}")

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
        QMessageBox.information(
            self, tr("done"),
            f"✅  {tr('labor_settings_saved')}"
        )
        emit_company_data_changed()

    def get_hourly_rate(self):
        return self._calc_rate()