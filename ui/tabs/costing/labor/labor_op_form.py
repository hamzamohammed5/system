"""
ui/tabs/costing/labor/labor_op_form.py
=======================================
_LaborOpForm — فورم إضافة / تعديل عملية عمالة.
مع scroll عمودي لما المساحة تكون ضيقة.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QDoubleSpinBox, QLabel, QGroupBox, QMessageBox,
    QSizePolicy,
)
from PyQt5.QtCore import Qt

from db.costing.operations_repo import (
    fetch_labor_op, insert_labor_op, update_labor_op,
)
from ui.helpers import EditModeMixin, buttons_row
from ui.widgets.shared.category_manager import CategoryCombo
from ui.widgets.shared.scrollable_form import wrap_in_scroll
from ui.events import bus


def _spin(max_=999999, dec=2):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(30)
    return s


def _labeled(widget, unit):
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(6)
    lay.addWidget(widget)
    lay.addWidget(QLabel(unit))
    lay.addStretch()
    return w


class _LaborOpForm(QWidget, EditModeMixin):
    def __init__(self, conn, settings, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._settings = settings
        self._build()
        self.init_edit_mode(self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode)
        bus.data_changed.connect(self._update_preview)

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._inner = QWidget()
        self._inner.setMinimumWidth(260)
        self._inner.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        scroll = wrap_in_scroll(self._inner)
        outer.addWidget(scroll)

        layout = QVBoxLayout(self._inner)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        grp  = QGroupBox("بيانات العملية")
        form = QFormLayout(grp)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = QLabel("─── إضافة عملية عمالة جديدة ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0;")
        form.addRow(self.lbl_mode)

        self.inp_name   = QLineEdit()
        self.inp_name.setPlaceholderText("مثال: خياطة، تغليف...")
        self.inp_name.setMinimumHeight(30)
        self.sp_minutes = _spin(99999, 2)
        self.sp_minutes.valueChanged.connect(self._update_preview)
        self.cmb_category = CategoryCombo(self.conn, scope="labor")

        self.lbl_cost = QLabel("─")
        self.lbl_cost.setStyleSheet(
            "color:#1a6e1a; font-weight:bold;"
            "background:#f0faf0; border:1px solid #b2dfb2; border-radius:4px; padding:4px 8px;"
        )

        form.addRow("اسم العملية :", self.inp_name)
        form.addRow("الوقت :",       _labeled(self.sp_minutes, "دقيقة"))
        form.addRow("التصنيف :",     self.cmb_category)
        form.addRow("التكلفة :",     self.lbl_cost)
        layout.addWidget(grp)

        self.btn_add    = QPushButton("➕  إضافة")
        self.btn_save   = QPushButton("💾  حفظ التعديل")
        self.btn_cancel = QPushButton("✖  إلغاء")
        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn.setMinimumHeight(30)
        self.btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save_edit)
        self.btn_cancel.clicked.connect(self._cancel)
        layout.addLayout(buttons_row(self.btn_add, self.btn_save, self.btn_cancel))
        layout.addStretch()

    def _update_preview(self):
        rate = self._settings.get_hourly_rate()
        cost = (self.sp_minutes.value() / 60.0) * rate
        self.lbl_cost.setText(
            f"{cost:.2f} جنيه / وحدة   ({self.sp_minutes.value():.2f} د ÷ 60 × {rate:.2f})"
        )

    def load_for_edit(self, op_id: int):
        op = fetch_labor_op(self.conn, op_id)
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
        insert_labor_op(self.conn, name, self.sp_minutes.value(),
                        category_id=self.cmb_category.get_category())
        self._reset()
        bus.data_changed.emit()

    def _save_edit(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل الاسم")
            return
        update_labor_op(self.conn, self._editing_id, name, self.sp_minutes.value(),
                        category_id=self.cmb_category.get_category())
        self._reset()
        bus.data_changed.emit()

    def _cancel(self):
        self._reset()

    def _reset(self):
        self.inp_name.clear()
        self.sp_minutes.setValue(0)
        self.lbl_cost.setText("─")
        self.cmb_category.setCurrentIndex(0)
        self.exit_edit_mode("─── إضافة عملية عمالة جديدة ───")