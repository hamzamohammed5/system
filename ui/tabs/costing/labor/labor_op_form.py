"""
ui/tabs/costing/labor/labor_op_form.py
=======================================
_LaborOpForm — فورم إضافة / تعديل عملية عمالة.

التحسينات:
  - يرث من LiveConnMixin
  - يستخدم form_utils: FormGroup, labeled_widget, spin_field, ResultBadge
"""

from PyQt5.QtWidgets import (
    QWidget, QMessageBox, QPushButton, QLineEdit, QSizePolicy,
)

from db.costing.operations_repo import (
    fetch_labor_op, insert_labor_op, update_labor_op,
)
from ui.helpers import EditModeMixin, buttons_row
from ui.widgets.shared.category_manager import CategoryCombo
from ui.widgets.shared.connection_mixin import LiveConnMixin
from ui.widgets.shared.form_utils import (
    FormGroup, labeled_widget, spin_field, ResultBadge, build_inner_scroll,
)
from ui.events import bus


class _LaborOpForm(QWidget, EditModeMixin, LiveConnMixin):
    def __init__(self, conn, settings, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._settings = settings
        self._build()
        self.init_edit_mode(self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode)
        bus.data_changed.connect(self._update_preview)

    def _build(self):
        _outer, _inner, root = build_inner_scroll(self, min_width=260)

        grp = FormGroup("بيانات العملية")

        from PyQt5.QtWidgets import QLabel
        self.lbl_mode = QLabel("─── إضافة عملية عمالة جديدة ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0;")
        grp.add_label_row(self.lbl_mode)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("مثال: خياطة، تغليف...")
        self.inp_name.setMinimumHeight(30)

        self.sp_minutes = spin_field(max_=99999, dec=2)
        self.sp_minutes.valueChanged.connect(self._update_preview)

        self.cmb_category = CategoryCombo(self._live_conn(), scope="labor")
        self.lbl_cost = ResultBadge()

        grp.add_row("اسم العملية :", self.inp_name)
        grp.add_row("الوقت :",       labeled_widget(self.sp_minutes, "دقيقة"))
        grp.add_row("التصنيف :",     self.cmb_category)
        grp.add_row("التكلفة :",     self.lbl_cost)
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

    def _update_preview(self):
        rate = self._settings.get_hourly_rate()
        cost = (self.sp_minutes.value() / 60.0) * rate
        self.lbl_cost.set_value(
            f"{cost:.2f} جنيه / وحدة   ({self.sp_minutes.value():.2f} د ÷ 60 × {rate:.2f})"
        )

    def load_for_edit(self, op_id: int):
        try:
            op = fetch_labor_op(self._live_conn(), op_id)
        except Exception:
            return
        if not op:
            return
        self.inp_name.setText(op["name"])
        self.sp_minutes.setValue(op["minutes"])
        self.cmb_category.set_category(op["category_id"])
        self.enter_edit_mode(op_id, f"─── تعديل: {op['name']} ───")

    def _add(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم العملية")
            return
        try:
            insert_labor_op(self._live_conn(), name, self.sp_minutes.value(),
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
            update_labor_op(self._live_conn(), self._editing_id, name,
                            self.sp_minutes.value(),
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
        self.sp_minutes.setValue(0)
        self.lbl_cost.reset()
        self.cmb_category.setCurrentIndex(0)
        self.exit_edit_mode("─── إضافة عملية عمالة جديدة ───")