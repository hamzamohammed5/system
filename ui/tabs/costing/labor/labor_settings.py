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

from services.shared.settings_service import SettingsService
from ui.widgets.panels.form_fields import (labeled_widget, spin_field)
from ui.widgets.panels.form_badges import ResultBadge

from ui.widgets.panels.form_group import FormGroup


from ui.widgets.theme.builders import wrap_in_scroll
from ui.widgets.core.i18n import tr
from ui.widgets.core.events import emit_company_data_changed
from ui.constants import (
    MARGIN_ZERO, SPACING_ZERO,
    LABOR_SETTINGS_MIN_W, LABOR_SETTINGS_INNER_MARGIN, LABOR_SETTINGS_INNER_SPACING,
    LABOR_SETTINGS_BTN_MIN_H,
    LABOR_SETTINGS_SPIN_MAX_SALARY, LABOR_SETTINGS_SPIN_MAX_DAYS,
    LABOR_SETTINGS_SPIN_MAX_HOURS, LABOR_SETTINGS_SPIN_MAX_OVHD,
    LABOR_SETTINGS_SPIN_DEC_SALARY, LABOR_SETTINGS_SPIN_DEC_DAYS,
    LABOR_SETTINGS_SPIN_DEC_HOURS, LABOR_SETTINGS_SPIN_DEC_OVHD,
)


class _LaborSettingsPanel(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self._load()

    def _build(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(*MARGIN_ZERO)
        outer_layout.setSpacing(SPACING_ZERO)

        inner = QWidget()
        inner.setMinimumWidth(LABOR_SETTINGS_MIN_W)
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(*LABOR_SETTINGS_INNER_MARGIN)
        layout.setSpacing(LABOR_SETTINGS_INNER_SPACING)

        scroll = wrap_in_scroll(inner)
        outer_layout.addWidget(scroll)

        grp = FormGroup(tr("labor_cost_settings"))

        self.sp_salary   = spin_field(max_=LABOR_SETTINGS_SPIN_MAX_SALARY, dec=LABOR_SETTINGS_SPIN_DEC_SALARY)
        self.sp_days     = spin_field(max_=LABOR_SETTINGS_SPIN_MAX_DAYS,   dec=LABOR_SETTINGS_SPIN_DEC_DAYS)
        self.sp_holidays = spin_field(max_=LABOR_SETTINGS_SPIN_MAX_DAYS,   dec=LABOR_SETTINGS_SPIN_DEC_DAYS)
        self.sp_hours    = spin_field(max_=LABOR_SETTINGS_SPIN_MAX_HOURS,  dec=LABOR_SETTINGS_SPIN_DEC_HOURS)
        self.sp_overhead = spin_field(max_=LABOR_SETTINGS_SPIN_MAX_OVHD,   dec=LABOR_SETTINGS_SPIN_DEC_OVHD)

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
        btn.setMinimumHeight(LABOR_SETTINGS_BTN_MIN_H)
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
        self.sp_salary.setValue(  SettingsService.get("monthly_salary",    3000))
        self.sp_days.setValue(    SettingsService.get("working_days",         25))
        self.sp_holidays.setValue(SettingsService.get("holiday_days",          4))
        self.sp_hours.setValue(   SettingsService.get("working_hours_day",     8))
        self.sp_overhead.setValue(SettingsService.get("overhead_factor",    1.10))
        self._update_preview()

    def _save(self):
        SettingsService.set("monthly_salary",    self.sp_salary.value())
        SettingsService.set("working_days",      self.sp_days.value())
        SettingsService.set("holiday_days",      self.sp_holidays.value())
        SettingsService.set("working_hours_day", self.sp_hours.value())
        SettingsService.set("overhead_factor",   self.sp_overhead.value())
        QMessageBox.information(
            self, tr("done"),
            f"✅  {tr('labor_settings_saved')}"
        )
        emit_company_data_changed()

    def get_hourly_rate(self):
        return self._calc_rate()