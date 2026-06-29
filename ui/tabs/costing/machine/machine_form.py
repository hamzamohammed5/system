"""
ui/tabs/costing/machine/machine_form.py
=======================================
_MachineForm — فورم إضافة / تعديل الماكينة.

[Fix A2] from ui.widgets.mixins.form_mixins import EditModeMixin
[Fix A3] from ui.widgets.theme.builders import wrap_in_scroll
[Fix A4] from ui.widgets.panels.form_group import FormGroup
         from ui.widgets.panels.form_fields import spin_field, labeled_widget
[Refactor] استخدام emit_company_data_changed بدل bus.data_changed.emit()
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QMessageBox,
)

from services.costing.machine_service   import MachineService
from ui.widgets.mixins.form_mixins      import EditModeMixin
from ui.widgets.core.conn               import LiveConnMixin
from ui.widgets.core.widget_mixin       import WidgetMixin
from ui.widgets.combo.category          import CategoryCombo
from ui.widgets.panels.form_group       import FormGroup
from ui.widgets.panels.form_fields      import spin_field, labeled_widget
from ui.widgets.theme.builders          import wrap_in_scroll
from ui.widgets.core.events             import emit_company_data_changed
from ui.widgets.core.i18n               import tr
from ui.font                            import FS_MD
from ui.constants import (
    MARGIN_ZERO, SPACING_ZERO, SPACING_SM,
    MARGIN_FORM, SPACING_MD, FORM_MIN_W, BTN_MIN_HEIGHT,
    MACHINE_FORM_SPIN_MAX_RATE, MACHINE_FORM_SPIN_DEC_RATE,
    MACHINE_FORM_INP_MIN_H,
)


def buttons_row(*buttons) -> QHBoxLayout:
    """صف أزرار أفقي."""
    row = QHBoxLayout()
    row.setSpacing(SPACING_SM)
    for btn in buttons:
        row.addWidget(btn)
    row.addStretch()
    return row


class _MachineForm(QWidget, EditModeMixin, LiveConnMixin, WidgetMixin):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._init_widget_mixin(lang=False, data=False)
        self._build()
        self.init_edit_mode(self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode)
        self._refresh_style()

    def _refresh_style(self, *_):
        from ui.theme import _C
        self.lbl_mode.setStyleSheet(
            f"font-weight:bold; font-size:{FS_MD}px; color:{_C['accent']};"
        )

    def _build(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(*MARGIN_ZERO)
        outer_layout.setSpacing(SPACING_ZERO)

        inner = QWidget()
        inner.setMinimumWidth(FORM_MIN_W)
        root = QVBoxLayout(inner)
        root.setContentsMargins(*MARGIN_FORM)
        root.setSpacing(SPACING_MD)

        scroll = wrap_in_scroll(inner)
        outer_layout.addWidget(scroll)

        grp = FormGroup(tr("machine_form_title"))

        self.lbl_mode = QLabel(tr("mode_label_wrap").format(content=tr("add_machine_new")))
        grp.add_label_row(self.lbl_mode)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText(tr("machine_name_placeholder"))
        self.inp_name.setMinimumHeight(MACHINE_FORM_INP_MIN_H)

        self.sp_rate_hour = spin_field(max_=MACHINE_FORM_SPIN_MAX_RATE, dec=MACHINE_FORM_SPIN_DEC_RATE)
        self.sp_rate_unit = spin_field(max_=MACHINE_FORM_SPIN_MAX_RATE, dec=MACHINE_FORM_SPIN_DEC_RATE)
        self.cmb_category = CategoryCombo(self._live_conn(), scope="machine")

        grp.add_row(f"{tr('machine_name')} :",   self.inp_name)
        grp.add_row(f"{tr('rate_per_hour')} :", labeled_widget(self.sp_rate_hour, tr('currency_per_hour')))
        grp.add_row(f"{tr('rate_per_unit')} :", labeled_widget(self.sp_rate_unit, tr('currency_per_unit')))
        grp.add_row(f"{tr('category')} :",      self.cmb_category)
        root.addWidget(grp)

        self.btn_add    = QPushButton(tr("btn_add"))
        self.btn_save   = QPushButton(tr("btn_save"))
        self.btn_cancel = QPushButton(tr("btn_cancel"))
        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn.setMinimumHeight(BTN_MIN_HEIGHT)
        self.btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save_edit)
        self.btn_cancel.clicked.connect(self._cancel)
        root.addLayout(buttons_row(self.btn_add, self.btn_save, self.btn_cancel))
        root.addStretch()

    def load_for_edit(self, machine_id: int):
        try:
            svc = MachineService(self._live_conn())
            m   = svc.get(machine_id)
        except Exception:
            return
        if not m:
            return
        self.inp_name.setText(m.name)
        self.sp_rate_hour.setValue(m.rate_per_hour)
        self.sp_rate_unit.setValue(m.rate_per_unit)
        self.cmb_category.set_category(m.category_id)
        self.enter_edit_mode(machine_id, tr("mode_label_wrap").format(content=f"{tr('editing_prefix')}: {m.name}"))

    def _add(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, tr("warning"), tr("machine_name_required"))
            return
        try:
            svc = MachineService(self._live_conn())
            svc.add(
                name,
                self.sp_rate_hour.value(),
                self.sp_rate_unit.value(),
                category_id=self.cmb_category.get_category(),
            )
        except Exception as e:
            QMessageBox.warning(self, tr("error"), str(e))
            return
        self._reset()
        emit_company_data_changed()

    def _save_edit(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, tr("warning"), tr("enter_name"))
            return
        try:
            svc = MachineService(self._live_conn())
            svc.update(
                self._editing_id,
                name,
                self.sp_rate_hour.value(),
                self.sp_rate_unit.value(),
                category_id=self.cmb_category.get_category(),
            )
        except Exception as e:
            QMessageBox.warning(self, tr("error"), str(e))
            return
        self._reset()
        emit_company_data_changed()

    def _cancel(self):
        self._reset()

    def _reset(self):
        self.inp_name.clear()
        self.sp_rate_hour.setValue(0)
        self.sp_rate_unit.setValue(0)
        self.cmb_category.setCurrentIndex(0)
        self.exit_edit_mode(tr("mode_label_wrap").format(content=tr("add_machine_new")))