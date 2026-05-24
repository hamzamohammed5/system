"""
ui/tabs/costing/machine/machine_op_form.py
==========================================
_MachineOpForm — فورم إضافة / تعديل عملية تشغيل.

التحسينات:
  - يرث من LiveConnMixin
  - يستخدم form_utils: FormGroup, ModeBadge, ResultBadge, build_inner_scroll
"""

from PyQt5.QtWidgets import (
    QWidget, QMessageBox, QPushButton, QLineEdit,
    QComboBox, QSizePolicy,
)

from db.costing.operations_repo import (
    fetch_machine, fetch_machine_op,
    fetch_all_machines,
    insert_machine_op, update_machine_op,
)
from db.costing.machine_op_rows_repo import calc_op_total_cost
from ui.helpers import EditModeMixin, buttons_row
from ui.widgets.shared.category_manager import CategoryCombo
from ui.widgets.shared.connection_mixin import LiveConnMixin
from ui.widgets.shared.form_utils import (
    FormGroup, ModeBadge, ResultBadge, build_inner_scroll,
)
from ui.tabs.costing.shared.machine_op_rows_editor import _OpRowsEditor
from ui.events import bus


class _MachineOpForm(QWidget, EditModeMixin, LiveConnMixin):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._rows_editor = None
        self._build()
        self.init_edit_mode(self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode)
        bus.data_changed.connect(self._refresh_machines)

    def _build(self):
        _outer, _inner, root = build_inner_scroll(self, min_width=280)

        grp = FormGroup("بيانات عملية التشغيل")

        from PyQt5.QtWidgets import QLabel
        self.lbl_mode = QLabel("─── إضافة عملية تشغيل جديدة ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0;")
        grp.add_label_row(self.lbl_mode)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("مثال: خياطة غرزة، كبس...")
        self.inp_name.setMinimumHeight(30)

        self.cmb_machine = QComboBox()
        self.cmb_machine.setMinimumHeight(30)

        # ModeBadge بدل QLabel عادي
        self.lbl_machine_mode = ModeBadge(color="orange")
        self.lbl_machine_mode.setToolTip(
            "وضع الحساب يُحدد تلقائياً من الماكينة المختارة\n"
            "لتغييره، عدّل إعداد الماكينة في تبويب الماكينات"
        )

        self.cmb_category = CategoryCombo(self._live_conn(), scope="machine")

        # ResultBadge بدل QLabel عادي
        self.lbl_cost = ResultBadge()

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
            conn = self._live_conn()
            machines = fetch_all_machines(conn)
        except Exception:
            return
        prev = self.cmb_machine.currentData()
        self.cmb_machine.blockSignals(True)
        self.cmb_machine.clear()
        for m in machines:
            self.cmb_machine.addItem(f"{m['id']} — {m['name']}", m["id"])
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
            m = fetch_machine(self._live_conn(), machine_id)
        except Exception:
            return
        if not m:
            return

        if float(m["rate_per_hour"]) > 0:
            mode = "time"
            self.lbl_machine_mode.set_mode(
                f"⏱ بالوقت  │  {m['rate_per_hour']:.2f} جنيه/ساعة",
                color="orange"
            )
        else:
            mode = "unit"
            self.lbl_machine_mode.set_mode(
                f"📦 بالوحدة  │  {m['rate_per_unit']:.2f} جنيه/وحدة",
                color="blue"
            )

        if self._rows_editor is not None and self._rows_editor.isEnabled():
            self._rows_editor.update_rates(
                mode, float(m["rate_per_hour"]), float(m["rate_per_unit"])
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
            op = fetch_machine_op(self._live_conn(), op_id)
        except Exception:
            return
        if not op:
            return
        self.inp_name.setText(op["name"])
        for i in range(self.cmb_machine.count()):
            if self.cmb_machine.itemData(i) == op["machine_id"]:
                self.cmb_machine.setCurrentIndex(i)
                break
        self.cmb_category.set_category(op["category_id"])
        self.enter_edit_mode(op_id, f"─── تعديل: {op['name']} ───")

        try:
            m = fetch_machine(self._live_conn(), op["machine_id"])
        except Exception:
            m = None
        if m:
            mode = "time" if float(m["rate_per_hour"]) > 0 else "unit"
            self._rows_editor.load_op(
                op_id, mode,
                float(m["rate_per_hour"]),
                float(m["rate_per_unit"])
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
            m = fetch_machine(self._live_conn(), machine_id)
        except Exception:
            return None
        if not m:
            return None
        mode = "time" if float(m["rate_per_hour"]) > 0 else "unit"
        return name, machine_id, mode, 0.0

    def _add(self):
        result = self._collect()
        if result is None:
            return
        name, machine_id, mode, value = result
        try:
            conn  = self._live_conn()
            op_id = insert_machine_op(
                conn, machine_id, name, mode, value,
                category_id=self.cmb_category.get_category()
            )
        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))
            return
        bus.data_changed.emit()

        try:
            m = fetch_machine(self._live_conn(), machine_id)
            rate_h = float(m["rate_per_hour"]) if m else 0.0
            rate_u = float(m["rate_per_unit"]) if m else 0.0
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
            conn = self._live_conn()
            update_machine_op(
                conn, self._editing_id, machine_id, name, mode, value,
                category_id=self.cmb_category.get_category()
            )
            m = fetch_machine(conn, machine_id)
            if m:
                self._rows_editor.update_rates(
                    mode, float(m["rate_per_hour"]), float(m["rate_per_unit"])
                )
        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))
            return
        self._reset()
        bus.data_changed.emit()

    def _cancel(self):
        self._reset()

    def _reset(self):
        self.inp_name.clear()
        self.cmb_category.setCurrentIndex(0)
        self.lbl_cost.reset()
        self._rows_editor.clear()
        self.exit_edit_mode("─── إضافة عملية تشغيل جديدة ───")
        self.btn_add.setVisible(True)