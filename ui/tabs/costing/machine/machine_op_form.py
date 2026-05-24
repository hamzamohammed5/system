"""
ui/tabs/costing/machine/machine_op_form.py
==========================================
_MachineOpForm — فورم إضافة / تعديل عملية تشغيل.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel,
    QMessageBox, QGroupBox, QComboBox,
    QSizePolicy,
)
from PyQt5.QtCore import Qt

from db.costing.operations_repo import (
    fetch_machine, fetch_machine_op,
    fetch_all_machines,
    insert_machine_op, update_machine_op,
)
from db.costing.machine_op_rows_repo import calc_op_total_cost
from ui.helpers import EditModeMixin, buttons_row
from ui.widgets.shared.category_manager import CategoryCombo
from ui.widgets.shared.scrollable_form import wrap_in_scroll
from ui.tabs.costing.shared.machine_op_rows_editor import _OpRowsEditor
from ui.events import bus


class _MachineOpForm(QWidget, EditModeMixin):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._rows_editor = None
        self._build()
        self.init_edit_mode(self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode)
        bus.data_changed.connect(self._refresh_machines)

    # ── connection صالح دايماً ────────────────────────────

    def _live_conn(self):
        if self.conn is not None:
            try:
                self.conn.execute("SELECT 1")
                return self.conn
            except Exception:
                pass
        from db.companies.company_state import company_state
        return company_state.get_erp_conn()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._inner = QWidget()
        self._inner.setMinimumWidth(280)
        self._inner.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        scroll = wrap_in_scroll(self._inner)
        outer.addWidget(scroll)

        root = QVBoxLayout(self._inner)
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

        self.lbl_machine_mode = QLabel("─")
        self.lbl_machine_mode.setStyleSheet(
            "color:#e65100; font-weight:bold; font-size:11px;"
            "background:#fff3e0; border:1px solid #ffcc80;"
            "border-radius:4px; padding:3px 8px;"
        )
        self.lbl_machine_mode.setToolTip(
            "وضع الحساب يُحدد تلقائياً من الماكينة المختارة\n"
            "لتغييره، عدّل إعداد الماكينة في تبويب الماكينات"
        )

        self.cmb_category = CategoryCombo(self._live_conn(), scope="machine")

        self.lbl_cost = QLabel("─")
        self.lbl_cost.setStyleSheet(
            "color:#1a6e1a; font-weight:bold;"
            "background:#f0faf0; border:1px solid #b2dfb2; border-radius:4px; padding:4px 8px;"
        )

        form.addRow("اسم العملية :",     self.inp_name)
        form.addRow("الماكينة :",        self.cmb_machine)
        form.addRow("وضع الحساب :",      self.lbl_machine_mode)
        form.addRow("التصنيف :",         self.cmb_category)
        form.addRow("إجمالي التكلفة :", self.lbl_cost)
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
    # تحديث الماكينات والوضع
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
            self.lbl_machine_mode.setText("─")
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
            self.lbl_machine_mode.setText(
                f"⏱ بالوقت  │  {m['rate_per_hour']:.2f} جنيه/ساعة"
            )
        else:
            mode = "unit"
            self.lbl_machine_mode.setText(
                f"📦 بالوحدة  │  {m['rate_per_unit']:.2f} جنيه/وحدة"
            )

        if self._rows_editor is not None and self._rows_editor.isEnabled():
            self._rows_editor.update_rates(
                mode,
                float(m["rate_per_hour"]),
                float(m["rate_per_unit"])
            )

        self._update_cost_label()

    def _update_cost_label(self):
        editing_id = getattr(self, '_editing_id', None)
        if editing_id is not None and editing_id > 0:
            try:
                total = calc_op_total_cost(self._live_conn(), editing_id)
                self.lbl_cost.setText(f"{total:.4f} جنيه / قطعة")
            except Exception:
                self.lbl_cost.setText("─")
        else:
            self.lbl_cost.setText("─ (أضف العملية أولاً لتظهر الصفوف)")

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
        self.lbl_cost.setText("─")
        self._rows_editor.clear()
        self.exit_edit_mode("─── إضافة عملية تشغيل جديدة ───")
        self.btn_add.setVisible(True)