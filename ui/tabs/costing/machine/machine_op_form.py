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
from ui.widgets.combo.category          import CategoryCombo
from ui.widgets.panels.form_group import FormGroup
from ui.widgets.panels.form_badges import ResultBadge
from ui.widgets.panels.form_badges       import ModeBadge

from ui.widgets.theme.builders          import wrap_in_scroll
from ui.tabs.costing.shared.machine_op_rows_editor import _OpRowsEditor
from ui.widgets.core.events             import emit_company_data_changed, bus


def _buttons_row(*buttons) -> QHBoxLayout:
    """صف أزرار أفقي."""
    row = QHBoxLayout()
    row.setSpacing(6)
    for btn in buttons:
        row.addWidget(btn)
    row.addStretch()
    return row


class _MachineOpForm(QWidget, EditModeMixin, LiveConnMixin):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._rows_editor = None
        self._build()
        self.init_edit_mode(self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode)
        # [Fix D2] استخدام named slot بدل lambda لتجنب memory leaks
        bus.company_data_changed.connect(self._on_company_data_changed)

    def _on_company_data_changed(self, _company_id: int = None):
        """يُستدعى عند تغيير بيانات الشركة — يحدّث قائمة الماكينات."""
        self._refresh_machines()

    def _build(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        inner = QWidget()
        inner.setMinimumWidth(280)
        root = QVBoxLayout(inner)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        scroll = wrap_in_scroll(inner)
        outer_layout.addWidget(scroll)

        grp = FormGroup("بيانات عملية التشغيل")

        self.lbl_mode = QLabel("─── إضافة عملية تشغيل جديدة ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0;")
        grp.add_label_row(self.lbl_mode)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("مثال: خياطة غرزة، كبس...")
        self.inp_name.setMinimumHeight(30)

        self.cmb_machine = QComboBox()
        self.cmb_machine.setMinimumHeight(30)

        self.lbl_machine_mode = ModeBadge(color="orange")
        self.lbl_machine_mode.setToolTip(
            "وضع الحساب يُحدد تلقائياً من الماكينة المختارة\n"
            "لتغييره، عدّل إعداد الماكينة في تبويب الماكينات"
        )

        self.cmb_category = CategoryCombo(self._live_conn(), scope="machine")
        self.lbl_cost     = ResultBadge()

        grp.add_row("اسم العملية :",     self.inp_name)
        grp.add_row("الماكينة :",        self.cmb_machine)
        grp.add_row("وضع الحساب :",      self.lbl_machine_mode)
        grp.add_row("التصنيف :",         self.cmb_category)
        grp.add_row("إجمالي التكلفة :", self.lbl_cost)
        root.addWidget(grp)

        self.btn_add    = QPushButton("➕  إضافة العملية")
        self.btn_save   = QPushButton("💾  حفظ التعديل")
        self.btn_cancel = QPushButton("✖  إلغاء")
        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn.setMinimumHeight(30)
        self.btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save_edit)
        self.btn_cancel.clicked.connect(self._cancel)
        root.addLayout(_buttons_row(self.btn_add, self.btn_save, self.btn_cancel))

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
                f"⏱ بالوقت  │  {m.rate_per_hour:.2f} جنيه/ساعة",
                color="orange"
            )
        else:
            mode = "unit"
            self.lbl_machine_mode.set_mode(
                f"📦 بالوحدة  │  {m.rate_per_unit:.2f} جنيه/وحدة",
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
                self.lbl_cost.set_value(f"{total:.4f} جنيه / قطعة")
            except Exception:
                self.lbl_cost.reset()
        else:
            self.lbl_cost.set_value("─ (أضف العملية أولاً لتظهر الصفوف)")

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
        self.enter_edit_mode(op_id, f"─── تعديل: {op.name} ───")

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
            QMessageBox.warning(self, "تنبيه", "أدخل اسم العملية")
            return None
        machine_id = self.cmb_machine.currentData()
        if machine_id is None:
            QMessageBox.warning(self, "تنبيه", "اختر ماكينة أولاً")
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
            QMessageBox.warning(self, "خطأ", str(e))
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
        self.enter_edit_mode(op_id, f"─── تعديل صفوف: {name} ───")
        self.btn_add.setVisible(False)
        self._update_cost_label()

        QMessageBox.information(
            self, "تم",
            f"✅ تمت إضافة العملية «{name}»\nأضف الصفوف الآن ثم اضغط «حفظ التعديل»"
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
            QMessageBox.warning(self, "خطأ", str(e))
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
        self.exit_edit_mode("─── إضافة عملية تشغيل جديدة ───")
        self.btn_add.setVisible(True)