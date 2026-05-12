"""
ui/tabs/costing/machine/machine_op_form.py
==========================================
_MachineOpForm — فورم إضافة / تعديل عملية تشغيل.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QDoubleSpinBox, QLabel,
    QMessageBox, QGroupBox, QComboBox, QRadioButton,
)
from PyQt5.QtCore import Qt

from db.operations_repo import (
    fetch_machine, fetch_machine_op,
    fetch_all_machines,
    insert_machine_op, update_machine_op,
)
from ui.helpers import EditModeMixin, buttons_row
from ui.widgets.category_manager import CategoryCombo
from ui.events import bus


def _labeled(widget, unit: str) -> QWidget:
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(6)
    lay.addWidget(widget)
    lay.addWidget(QLabel(unit))
    lay.addStretch()
    return w


def _spin(max_=999999, dec=4):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(30)
    return s


class _MachineOpForm(QWidget, EditModeMixin):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self.init_edit_mode(self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode)
        bus.data_changed.connect(self._refresh_machines)
        bus.data_changed.connect(self._update_preview)

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(12, 12, 12, 12)

        grp  = QGroupBox("بيانات عملية التشغيل")
        form = QFormLayout(grp)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = QLabel("─── إضافة عملية تشغيل جديدة ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0;")
        form.addRow(self.lbl_mode)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("مثال: خياطة غرزة، كبس...")
        self.inp_name.setMinimumHeight(30)

        self.cmb_machine = QComboBox()
        self.cmb_machine.setMinimumHeight(30)
        self.cmb_machine.currentIndexChanged.connect(self._update_preview)

        mode_row = QHBoxLayout()
        self.rdo_time = QRadioButton("⏱ بالوقت (دقيقة)")
        self.rdo_unit = QRadioButton("📦 بالوحدة")
        self.rdo_time.setChecked(True)
        mode_row.addWidget(self.rdo_time)
        mode_row.addWidget(self.rdo_unit)
        mode_row.addStretch()
        self.rdo_time.toggled.connect(self._update_mode_label)
        self.rdo_time.toggled.connect(self._update_preview)

        self.sp_value = _spin(99999, 4)
        self.sp_value.valueChanged.connect(self._update_preview)

        self._lbl_value = QLabel("دقيقة")
        self._lbl_value.setFixedWidth(50)

        value_row = QHBoxLayout()
        value_row.addWidget(self.sp_value)
        value_row.addWidget(self._lbl_value)
        value_row.addStretch()

        self.cmb_category = CategoryCombo(self.conn, scope="machine")

        self.lbl_cost = QLabel("─")
        self.lbl_cost.setStyleSheet(
            "color:#1a6e1a; font-weight:bold;"
            "background:#f0faf0; border:1px solid #b2dfb2; border-radius:4px; padding:4px 8px;"
        )

        self._refresh_machines()

        form.addRow("اسم العملية :", self.inp_name)
        form.addRow("الماكينة :",    self.cmb_machine)
        form.addRow("وضع الحساب :", mode_row)
        form.addRow("القيمة :",      value_row)
        form.addRow("التصنيف :",     self.cmb_category)
        form.addRow("التكلفة :",     self.lbl_cost)
        root.addWidget(grp)

        self.btn_add    = QPushButton("➕  إضافة")
        self.btn_save   = QPushButton("💾  حفظ التعديل")
        self.btn_cancel = QPushButton("✖  إلغاء")
        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn.setMinimumHeight(30)
        self.btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save_edit)
        self.btn_cancel.clicked.connect(self._cancel)
        root.addLayout(buttons_row(self.btn_add, self.btn_save, self.btn_cancel))
        root.addStretch()

    def _refresh_machines(self):
        prev = self.cmb_machine.currentData()
        self.cmb_machine.blockSignals(True)
        self.cmb_machine.clear()
        for m in fetch_all_machines(self.conn):
            self.cmb_machine.addItem(f"{m['id']} — {m['name']}", m["id"])
        for i in range(self.cmb_machine.count()):
            if self.cmb_machine.itemData(i) == prev:
                self.cmb_machine.setCurrentIndex(i)
                break
        self.cmb_machine.blockSignals(False)
        self._update_preview()

    def _update_mode_label(self):
        self._lbl_value.setText("دقيقة" if self.rdo_time.isChecked() else "وحدة")

    def _update_preview(self):
        if not hasattr(self, 'lbl_cost'):
            return
        machine_id = self.cmb_machine.currentData()
        if machine_id is None:
            self.lbl_cost.setText("─")
            return
        m = fetch_machine(self.conn, machine_id)
        if not m:
            self.lbl_cost.setText("─")
            return
        val = self.sp_value.value()
        if self.rdo_time.isChecked():
            cost = (val / 60.0) * m["rate_per_hour"]
            desc = f"{val:.2f} د ÷ 60 × {m['rate_per_hour']:.2f}"
        else:
            cost = val * m["rate_per_unit"]
            desc = f"{val:.4f} × {m['rate_per_unit']:.2f}"
        self.lbl_cost.setText(f"{cost:.2f} جنيه / وحدة   ({desc})")

    def load_for_edit(self, op_id: int):
        op = fetch_machine_op(self.conn, op_id)
        if not op:
            return
        self.inp_name.setText(op["name"])
        for i in range(self.cmb_machine.count()):
            if self.cmb_machine.itemData(i) == op["machine_id"]:
                self.cmb_machine.setCurrentIndex(i)
                break
        if op["mode"] == "time":
            self.rdo_time.setChecked(True)
        else:
            self.rdo_unit.setChecked(True)
        self._update_mode_label()
        self.sp_value.setValue(op["value"])
        self.cmb_category.set_category(op["category_id"])
        self.enter_edit_mode(op_id, f"─── تعديل: {op['name']} ───")

    def _collect(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم العملية")
            return None
        machine_id = self.cmb_machine.currentData()
        if machine_id is None:
            QMessageBox.warning(self, "تنبيه", "اختر ماكينة أولاً")
            return None
        mode = "time" if self.rdo_time.isChecked() else "unit"
        return name, machine_id, mode, self.sp_value.value()

    def _add(self):
        result = self._collect()
        if result is None:
            return
        name, machine_id, mode, value = result
        insert_machine_op(self.conn, machine_id, name, mode, value,
                          category_id=self.cmb_category.get_category())
        self._reset()
        bus.data_changed.emit()

    def _save_edit(self):
        result = self._collect()
        if result is None:
            return
        name, machine_id, mode, value = result
        update_machine_op(self.conn, self._editing_id, machine_id, name, mode, value,
                          category_id=self.cmb_category.get_category())
        self._reset()
        bus.data_changed.emit()

    def _cancel(self):
        self._reset()

    def _reset(self):
        self.inp_name.clear()
        self.sp_value.setValue(0)
        self.rdo_time.setChecked(True)
        self._update_mode_label()
        self.cmb_category.setCurrentIndex(0)
        self.lbl_cost.setText("─")
        self.exit_edit_mode("─── إضافة عملية تشغيل جديدة ───")