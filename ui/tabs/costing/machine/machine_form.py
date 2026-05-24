"""
ui/tabs/costing/machine/machine_form.py
=======================================
_MachineForm — فورم إضافة / تعديل الماكينة.

التحسينات:
  - يرث من LiveConnMixin بدل كتابة _live_conn يدوياً
  - يستخدم form_utils: FormGroup, labeled_widget, spin_field, build_inner_scroll
"""

from PyQt5.QtWidgets import (
    QWidget, QMessageBox, QPushButton, QSizePolicy,
)

from db.costing.operations_repo import fetch_machine, insert_machine, update_machine
from ui.helpers import EditModeMixin, buttons_row
from ui.widgets.shared.category_manager import CategoryCombo
from ui.widgets.shared.connection_mixin import LiveConnMixin
from ui.widgets.shared.form_utils import (
    FormGroup, labeled_widget, spin_field, build_inner_scroll,
)
from ui.events import bus


class _MachineForm(QWidget, EditModeMixin, LiveConnMixin):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self.init_edit_mode(self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode)

    def _build(self):
        _outer, _inner, root = build_inner_scroll(self, min_width=260)

        grp = FormGroup("بيانات الماكينة")

        from PyQt5.QtWidgets import QLabel
        self.lbl_mode = QLabel("─── إضافة ماكينة جديدة ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0;")
        grp.add_label_row(self.lbl_mode)

        from PyQt5.QtWidgets import QLineEdit
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("مثال: ماكينة خياطة، فرن، مكبس...")
        self.inp_name.setMinimumHeight(30)

        self.sp_rate_hour = spin_field(max_=999999, dec=2)
        self.sp_rate_unit = spin_field(max_=999999, dec=2)
        self.cmb_category = CategoryCombo(self._live_conn(), scope="machine")

        grp.add_row("اسم الماكينة :",       self.inp_name)
        grp.add_row("معدل التشغيل / ساعة :", labeled_widget(self.sp_rate_hour, "جنيه / ساعة"))
        grp.add_row("معدل التشغيل / وحدة :", labeled_widget(self.sp_rate_unit, "جنيه / وحدة"))
        grp.add_row("التصنيف :",             self.cmb_category)
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
        try:
            m = fetch_machine(self._live_conn(), machine_id)
        except Exception:
            return
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
        try:
            insert_machine(self._live_conn(), name,
                           self.sp_rate_hour.value(), self.sp_rate_unit.value(),
                           category_id=self.cmb_category.get_category())
        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))
            return
        self._reset()
        bus.data_changed.emit()

    def _save_edit(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل الاسم")
            return
        try:
            update_machine(self._live_conn(), self._editing_id, name,
                           self.sp_rate_hour.value(), self.sp_rate_unit.value(),
                           category_id=self.cmb_category.get_category())
        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))
            return
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