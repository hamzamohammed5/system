"""
ui/tabs/machine_tab.py
======================
تبويب التشغيل — تبويبات متداخلة:
  ① الماكينات
  ② عمليات التشغيل  (مع زر "استبدال شامل")
  ③ تصنيفات التشغيل
"""

from PyQt5.QtCore    import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget,
    QLineEdit, QPushButton, QTableWidgetItem, QSplitter,
    QDoubleSpinBox, QLabel, QMessageBox, QGroupBox,
    QComboBox, QHeaderView, QRadioButton, QButtonGroup,
)

from db.connection      import get_connection
from db.operations_repo import (
    fetch_all_machines, fetch_machine,
    insert_machine, update_machine, delete_machine,
    fetch_all_machine_ops, fetch_machine_op,
    insert_machine_op, update_machine_op, delete_machine_op,
)
from models.costing import calc_machine_op_cost
from ui.helpers import (
    EditModeMixin, make_table, buttons_row,
    section_label, confirm_delete, danger_button,
)
from ui.widgets.category_manager import CategoryCombo, CategoryManager
from ui.widgets.bulk_replace_dialog import BulkReplaceDialog
from ui.events import bus

_SPLITTER_STYLE = """
    QSplitter::handle { background: #e0e0e0; border-top: 1px solid #ccc; }
    QSplitter::handle:hover { background: #bbdefb; }
"""


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


# ══════════════════════════════════════════════════════════
# تبويب الماكينات
# ══════════════════════════════════════════════════════════

class _MachineForm(QWidget, EditModeMixin):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self.init_edit_mode(self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode)

    def _build(self):
        root = QVBoxLayout(self)
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


class _MachineTable(QWidget):
    def __init__(self, conn, form: _MachineForm, parent=None):
        super().__init__(parent)
        self.conn  = conn
        self._form = form
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(6)
        root.addWidget(section_label("─── الماكينات المحفوظة ───"))

        self.table = make_table(
            ["ID", "الاسم", "التصنيف", "جنيه/ساعة", "جنيه/وحدة"],
            stretch_col=1
        )
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Fixed)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 160)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 90)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table)

        btn_edit = QPushButton("✏️  تعديل")
        btn_del  = danger_button("🗑️  حذف")
        for btn in (btn_edit, btn_del):
            btn.setMinimumHeight(30)
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        root.addLayout(buttons_row(btn_edit, btn_del))

    def _edit(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر ماكينة أولاً")
            return
        self._form.load_for_edit(int(self.table.item(row, 0).text()))

    def _delete(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر ماكينة أولاً")
            return
        mid  = int(self.table.item(row, 0).text())
        name = self.table.item(row, 1).text()
        if self._form.is_editing and self._form._editing_id == mid:
            self._form._reset()
        if confirm_delete(self, name):
            delete_machine(self.conn, mid)
            bus.data_changed.emit()

    def _load(self):
        self.table.setRowCount(0)
        for r, m in enumerate(fetch_all_machines(self.conn)):
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(m["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(m["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(m["category_name"] or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{m['rate_per_hour']:.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"{m['rate_per_unit']:.2f}"))


class _MachinesTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(_SPLITTER_STYLE)

        form  = _MachineForm(conn)
        table = _MachineTable(conn, form)

        splitter.addWidget(form)
        splitter.addWidget(table)
        splitter.setSizes([260, 380])
        splitter.setCollapsible(0, True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(splitter)


# ══════════════════════════════════════════════════════════
# تبويب عمليات التشغيل
# ══════════════════════════════════════════════════════════

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

        # ── اختيار الماكينة ──
        self.cmb_machine = QComboBox()
        self.cmb_machine.setMinimumHeight(30)
        self._refresh_machines()
        self.cmb_machine.currentIndexChanged.connect(self._update_preview)

        # ── وضع الحساب ──
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
        # استعادة الاختيار السابق
        for i in range(self.cmb_machine.count()):
            if self.cmb_machine.itemData(i) == prev:
                self.cmb_machine.setCurrentIndex(i)
                break
        self.cmb_machine.blockSignals(False)
        self._update_preview()

    def _update_mode_label(self):
        self._lbl_value.setText("دقيقة" if self.rdo_time.isChecked() else "وحدة")

    def _update_preview(self):
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
        # اختار الماكينة
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


class _MachineOpTable(QWidget):
    def __init__(self, conn, form: _MachineOpForm, parent=None):
        super().__init__(parent)
        self.conn  = conn
        self._form = form
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(6)
        root.addWidget(section_label("─── عمليات التشغيل المحفوظة ───"))

        self.table = make_table(
            ["ID", "اسم العملية", "التصنيف", "الماكينة", "الوضع", "القيمة", "التكلفة"],
            stretch_col=1
        )
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Fixed)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 140)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 70)
        self.table.setColumnWidth(5, 70)
        self.table.setColumnWidth(6, 110)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table)

        btn_edit    = QPushButton("✏️  تعديل")
        btn_del     = danger_button("🗑️  حذف")
        btn_replace = QPushButton("🔄  استبدال شامل")
        btn_replace.setStyleSheet(
            "QPushButton { background:#e65100; color:white; border-radius:4px;"
            "padding:4px 10px; font-weight:bold; }"
            "QPushButton:hover { background:#bf360c; }"
        )

        for btn in (btn_edit, btn_del, btn_replace):
            btn.setMinimumHeight(30)

        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        btn_replace.clicked.connect(self._bulk_replace)
        root.addLayout(buttons_row(btn_edit, btn_del, btn_replace))

    def _edit(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر عملية أولاً")
            return
        self._form.load_for_edit(int(self.table.item(row, 0).text()))

    def _delete(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر عملية أولاً")
            return
        op_id   = int(self.table.item(row, 0).text())
        op_name = self.table.item(row, 1).text()
        if self._form.is_editing and self._form._editing_id == op_id:
            self._form._reset()
        if confirm_delete(self, op_name):
            delete_machine_op(self.conn, op_id)
            bus.data_changed.emit()

    def _bulk_replace(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر عملية أولاً")
            return
        op_id   = int(self.table.item(row, 0).text())
        op_name = self.table.item(row, 1).text()
        dlg = BulkReplaceDialog(
            conn       = self.conn,
            child_type = "machine_op",
            child_id   = op_id,
            child_name = op_name,
            parent     = self,
        )
        dlg.exec_()

    def _load(self):
        self.table.setRowCount(0)
        for r, op in enumerate(fetch_all_machine_ops(self.conn)):
            cost = calc_machine_op_cost(self.conn, op["id"])
            mode_ar = "وقت" if op["mode"] == "time" else "وحدة"
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(op["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(op["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(op["category_name"] or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(op["machine_name"]))
            self.table.setItem(r, 4, QTableWidgetItem(mode_ar))
            self.table.setItem(r, 5, QTableWidgetItem(f"{op['value']:.4f}"))
            self.table.setItem(r, 6, QTableWidgetItem(f"{cost:.2f} جنيه"))


class _MachineOpsTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(_SPLITTER_STYLE)

        form  = _MachineOpForm(conn)
        table = _MachineOpTable(conn, form)

        splitter.addWidget(form)
        splitter.addWidget(table)
        splitter.setSizes([300, 400])
        splitter.setCollapsible(0, True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(splitter)


# ══════════════════════════════════════════════════════════
# التبويب الرئيسي
# ══════════════════════════════════════════════════════════

class MachineTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn = get_connection()
        self._build()

    def _build(self):
        tabs = QTabWidget()
        tabs.addTab(_MachinesTab(self.conn),                       "🖥️  الماكينات")
        tabs.addTab(_MachineOpsTab(self.conn),                     "⚙️  عمليات التشغيل")
        tabs.addTab(CategoryManager(self.conn, scope="machine"),   "🏷️  التصنيفات")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(tabs)

    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)