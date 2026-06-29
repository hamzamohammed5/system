"""
ui/tabs/costing/machine/machine_op_form.py
==========================================
_MachineOpForm — فورم إضافة / تعديل عملية تشغيل.

[Refactor] استخدام MachineService + MachineOpService بدل operations_repo مباشرة.
[Refactor] imports من المسارات الموثقة في files_reference:
  - EditModeMixin   → ui.widgets.mixins.form_mixins
  - LiveConnMixin   → ui.widgets.core.conn
  - CategoryCombo   → ui.widgets.combo.category
  - FormGroup, ModeBadge, ResultBadge → ui.widgets.panels.form_parts
  - wrap_in_scroll  → ui.widgets.theme.builders
[Fix A2] EditModeMixin → ui.widgets.mixins.form_mixins
[Fix A3] wrap_in_scroll → ui.widgets.theme.builders
[Fix A6] from ui.widgets.core.events import bus (بدل ui.events)
[Fix D2] bus.data_changed → bus.company_data_changed مع named slot
[Fix] استخدام emit_company_data_changed بدل bus.data_changed.emit()
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QComboBox, QMessageBox,
)

from services.costing.machine_service   import MachineService, MachineOpService
from db.costing.machine_op_rows_repo    import calc_op_total_cost
from ui.widgets.mixins.form_mixins      import EditModeMixin
from ui.widgets.core.conn               import LiveConnMixin
from ui.widgets.core.widget_mixin       import WidgetMixin
from ui.widgets.combo.category          import CategoryCombo
from ui.widgets.panels.form_group import FormGroup
from ui.widgets.panels.form_badges import ResultBadge
from ui.widgets.panels.form_badges       import ModeBadge

from ui.widgets.theme.builders          import wrap_in_scroll
from ui.tabs.costing.shared.machine_op_rows_editor import _OpRowsEditor
from ui.widgets.core.events             import emit_company_data_changed, bus
from ui.widgets.core.i18n               import tr
from ui.font                            import FS_MD
from ui.constants import (
    MARGIN_ZERO, SPACING_ZERO, SPACING_SM,
    MARGIN_FORM, SPACING_MD, BTN_MIN_HEIGHT,
    MACHINE_FORM_INP_MIN_H,
    MACHINE_OP_FORM_MIN_W,
)


def buttons_row(*buttons) -> QHBoxLayout:
    """صف أزرار أفقي."""
    row = QHBoxLayout()
    row.setSpacing(SPACING_SM)
    for btn in buttons:
        row.addWidget(btn)
    row.addStretch()
    return row


class _MachineOpForm(QWidget, EditModeMixin, LiveConnMixin, WidgetMixin):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._rows_editor = None
        self._init_widget_mixin(lang=False, data=False)
        self._build()
        self.init_edit_mode(self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode)
        self._refresh_style()
        # [Fix D2] استخدام named slot بدل lambda لتجنب memory leaks
        bus.company_data_changed.connect(self._on_company_data_changed)

    def _refresh_style(self, *_):
        from ui.theme import _C
        self.lbl_mode.setStyleSheet(
            f"font-weight:bold; font-size:{FS_MD}px; color:{_C['accent']};"
        )

    def _on_company_data_changed(self, _company_id: int = None):
        """يُستدعى عند تغيير بيانات الشركة — يحدّث قائمة الماكينات."""
        self._refresh_machines()

    def _build(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(*MARGIN_ZERO)
        outer_layout.setSpacing(SPACING_ZERO)

        inner = QWidget()
        inner.setMinimumWidth(MACHINE_OP_FORM_MIN_W)
        root = QVBoxLayout(inner)
        root.setContentsMargins(*MARGIN_FORM)
        root.setSpacing(SPACING_MD)

        scroll = wrap_in_scroll(inner)
        outer_layout.addWidget(scroll)

        grp = FormGroup(tr("machine_op_form_title"))

        self.lbl_mode = QLabel(tr("mode_label_wrap").format(content=tr("add_machine_op_new")))
        grp.add_label_row(self.lbl_mode)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText(tr("machine_op_name_placeholder"))
        self.inp_name.setMinimumHeight(MACHINE_FORM_INP_MIN_H)

        self.cmb_machine = QComboBox()
        self.cmb_machine.setMinimumHeight(MACHINE_FORM_INP_MIN_H)

        self.lbl_machine_mode = ModeBadge(color="orange")
        self.lbl_machine_mode.setToolTip(tr("machine_mode_tooltip"))

        self.cmb_category = CategoryCombo(self._live_conn(), scope="machine")
        self.lbl_cost     = ResultBadge()

        grp.add_row(f"{tr('op_name')} :",        self.inp_name)
        grp.add_row(f"{tr('machine_label')} :",  self.cmb_machine)
        grp.add_row(f"{tr('calc_mode_label')} :", self.lbl_machine_mode)
        grp.add_row(f"{tr('category')} :",       self.cmb_category)
        grp.add_row(f"{tr('total_cost_label')} :", self.lbl_cost)
        root.addWidget(grp)

        self.btn_add    = QPushButton(tr("btn_add_op"))
        self.btn_save   = QPushButton(tr("btn_save"))
        self.btn_cancel = QPushButton(tr("btn_cancel"))
        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn.setMinimumHeight(BTN_MIN_HEIGHT)
        self.btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save_edit)
        self.btn_cancel.clicked.connect(self._cancel)
        root.addLayout(buttons_row(self.btn_add, self.btn_save, self.btn_cancel))

        self._rows_editor = _OpRowsEditor(self._live_conn())
        root.addWidget(self._rows_editor)
        root.addStretch()

        self.cmb_machine.currentIndexChanged.connect(self._on_machine_changed)
        self._refresh_machines()

    # ══════════════════════════════════════════════════════
    # تحديث الماكينات
    # ══════════════════════════════════════════════════════

    def _refresh_machines(self):
        try:
            svc      = MachineService(self._live_conn())
            machines = svc.list()
        except Exception:
            return
        prev = self.cmb_machine.currentData()
        self.cmb_machine.blockSignals(True)
        self.cmb_machine.clear()
        for m in machines:
            self.cmb_machine.addItem(f"{m.id} — {m.name}", m.id)
        for i in range(self.cmb_machine.count()):
            if self.cmb_machine.itemData(i) == prev:
                self.cmb_machine.setCurrentIndex(i)
                break
        self.cmb_machine.blockSignals(False)
        self._on_machine_changed()

    def _on_machine_changed(self):
        machine_id = self.cmb_machine.currentData()
        if machine_id is None:
            self.lbl_machine_mode.reset()
            if self._rows_editor is not None:
                self._rows_editor.update_rates("time", 0.0, 0.0)
            return
        try:
            svc = MachineService(self._live_conn())
            m   = svc.get(machine_id)
        except Exception:
            return
        if not m:
            return

        if float(m.rate_per_hour) > 0:
            mode = "time"
            self.lbl_machine_mode.set_mode(
                f"{tr('mode_time_label')}  {tr('vertical_separator')}  {m.rate_per_hour:.2f} {tr('currency_per_hour')}",
                color="orange"
            )
        else:
            mode = "unit"
            self.lbl_machine_mode.set_mode(
                f"{tr('mode_unit_label')}  {tr('vertical_separator')}  {m.rate_per_unit:.2f} {tr('currency_per_unit')}",
                color="blue"
            )

        if self._rows_editor is not None and self._rows_editor.isEnabled():
            self._rows_editor.update_rates(
                mode, float(m.rate_per_hour), float(m.rate_per_unit)
            )

        self._update_cost_label()

    def _update_cost_label(self):
        editing_id = getattr(self, '_editing_id', None)
        if editing_id is not None and editing_id > 0:
            try:
                total = calc_op_total_cost(self._live_conn(), editing_id)
                self.lbl_cost.set_value(f"{total:.4f} {tr('currency_per_piece')}")
            except Exception:
                self.lbl_cost.reset()
        else:
            self.lbl_cost.set_value(f"{tr('amount_dash_placeholder')} ({tr('add_op_first_hint')})")

    # ══════════════════════════════════════════════════════
    # تحميل للتعديل
    # ══════════════════════════════════════════════════════

    def load_for_edit(self, op_id: int):
        try:
            op_svc = MachineOpService(self._live_conn())
            op     = op_svc.get(op_id)
        except Exception:
            return
        if not op:
            return
        self.inp_name.setText(op.name)
        for i in range(self.cmb_machine.count()):
            if self.cmb_machine.itemData(i) == op.machine_id:
                self.cmb_machine.setCurrentIndex(i)
                break
        self.cmb_category.set_category(op.category_id)
        self.enter_edit_mode(op_id, tr("mode_label_wrap").format(content=f"{tr('editing_prefix')}: {op.name}"))

        try:
            m_svc = MachineService(self._live_conn())
            m     = m_svc.get(op.machine_id)
        except Exception:
            m = None
        if m:
            mode = "time" if float(m.rate_per_hour) > 0 else "unit"
            self._rows_editor.load_op(
                op_id, mode,
                float(m.rate_per_hour),
                float(m.rate_per_unit)
            )
        self._update_cost_label()

    # ══════════════════════════════════════════════════════
    # منطق الحفظ
    # ══════════════════════════════════════════════════════

    def _collect(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, tr("warning"), tr("enter_op_name"))
            return None
        machine_id = self.cmb_machine.currentData()
        if machine_id is None:
            QMessageBox.warning(self, tr("warning"), tr("select_machine_first"))
            return None
        try:
            svc = MachineService(self._live_conn())
            m   = svc.get(machine_id)
        except Exception:
            return None
        if not m:
            return None
        mode = "time" if float(m.rate_per_hour) > 0 else "unit"
        return name, machine_id, mode, 0.0

    def _add(self):
        result = self._collect()
        if result is None:
            return
        name, machine_id, mode, value = result
        try:
            op_svc = MachineOpService(self._live_conn())
            op_id  = op_svc.add(
                machine_id, name, mode, value,
                category_id=self.cmb_category.get_category(),
            )
        except Exception as e:
            QMessageBox.warning(self, tr("error"), str(e))
            return

        emit_company_data_changed()

        try:
            m_svc  = MachineService(self._live_conn())
            m      = m_svc.get(machine_id)
            rate_h = float(m.rate_per_hour) if m else 0.0
            rate_u = float(m.rate_per_unit) if m else 0.0
        except Exception:
            rate_h = rate_u = 0.0

        self._rows_editor.load_op(op_id, mode, rate_h, rate_u)
        self.enter_edit_mode(op_id, tr("mode_label_wrap").format(content=f"{tr('editing_rows_prefix')}: {name}"))
        self.btn_add.setVisible(False)
        self._update_cost_label()

        QMessageBox.information(
            self, tr("done"),
            f"✅ {tr('op_added_success').format(name=name)}"
        )

    def _save_edit(self):
        result = self._collect()
        if result is None:
            return
        name, machine_id, mode, value = result
        try:
            op_svc = MachineOpService(self._live_conn())
            op_svc.update(
                self._editing_id, machine_id, name, mode, value,
                category_id=self.cmb_category.get_category(),
            )
            m_svc = MachineService(self._live_conn())
            m     = m_svc.get(machine_id)
            if m and self._rows_editor:
                self._rows_editor.update_rates(
                    mode, float(m.rate_per_hour), float(m.rate_per_unit)
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
        self.cmb_category.setCurrentIndex(0)
        self.lbl_cost.reset()
        self._rows_editor.clear()
        self.exit_edit_mode(tr("mode_label_wrap").format(content=tr("add_machine_op_new")))
        self.btn_add.setVisible(True)