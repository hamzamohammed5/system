"""
ui/tabs/costing/machine/machine_form.py
=======================================
_MachineForm — فورم إضافة / تعديل الماكينة.
مع scroll عمودي لما المساحة تكون ضيقة.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QDoubleSpinBox, QLabel,
    QMessageBox, QGroupBox, QSizePolicy,
)
from PyQt5.QtCore import Qt

from db.costing.operations_repo import fetch_machine, insert_machine, update_machine
from ui.helpers import EditModeMixin, buttons_row
from ui.widgets.shared.category_manager import CategoryCombo
from ui.widgets.shared.scrollable_form import wrap_in_scroll
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


def _spin(max_=999999, dec=2):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(30)
    return s


class _MachineForm(QWidget, EditModeMixin):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self.init_edit_mode(self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode)

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._inner = QWidget()
        self._inner.setMinimumWidth(260)
        self._inner.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        scroll = wrap_in_scroll(self._inner)
        outer.addWidget(scroll)

        root = QVBoxLayout(self._inner)
        root.setSpacing(10)
        root.setContentsMargins(12, 12, 12, 12)

        grp  = QGroupBox("بيانات الماكينة")
        form = QFormLayout(grp)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = QLabel("─── إضافة ماكينة جديدة ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0;")
        form.addRow(self.lbl_mode)

        self.inp_name      = QLineEdit()
        self.inp_name.setPlaceholderText("مثال: ماكينة خياطة، فرن، مكبس...")
        self.inp_name.setMinimumHeight(30)
        self.sp_rate_hour  = _spin()
        self.sp_rate_unit  = _spin()
        self.cmb_category  = CategoryCombo(self.conn, scope="machine")

        form.addRow("اسم الماكينة :",       self.inp_name)
        form.addRow("معدل التشغيل / ساعة :", _labeled(self.sp_rate_hour, "جنيه / ساعة"))
        form.addRow("معدل التشغيل / وحدة :", _labeled(self.sp_rate_unit, "جنيه / وحدة"))
        form.addRow("التصنيف :",             self.cmb_category)
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

    def load_for_edit(self, machine_id: int):
        m = fetch_machine(self.conn, machine_id)
        if not m:
            return
        self.inp_name.setText(m["name"])
        self.sp_rate_hour.setValue(m["rate_per_hour"])
        self.sp_rate_unit.setValue(m["rate_per_unit"])
        self.cmb_category.set_category(m["category_id"])
        self.enter_edit_mode(machine_id, f"─── تعديل: {m['name']} ───")

    def _add(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم الماكينة")
            return
        insert_machine(self.conn, name,
                       self.sp_rate_hour.value(), self.sp_rate_unit.value(),
                       category_id=self.cmb_category.get_category())
        self._reset()
        bus.data_changed.emit()

    def _save_edit(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل الاسم")
            return
        update_machine(self.conn, self._editing_id, name,
                       self.sp_rate_hour.value(), self.sp_rate_unit.value(),
                       category_id=self.cmb_category.get_category())
        self._reset()
        bus.data_changed.emit()

    def _cancel(self):
        self._reset()

    def _reset(self):
        self.inp_name.clear()
        self.sp_rate_hour.setValue(0)
        self.sp_rate_unit.setValue(0)
        self.cmb_category.setCurrentIndex(0)
        self.exit_edit_mode("─── إضافة ماكينة جديدة ───")