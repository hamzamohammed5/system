"""
ui/tabs/machine_tab.py
======================
تبويب التشغيل — تبويبات متداخلة:
  ① الماكينات
  ② عمليات التشغيل
  ③ تصنيفات التشغيل
"""

from PyQt5.QtCore    import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget,
    QLineEdit, QPushButton, QTableWidgetItem, QSplitter,
    QDoubleSpinBox, QLabel, QMessageBox, QGroupBox,
    QComboBox, QStackedWidget, QHeaderView,
)

from db.connection      import get_connection
from db.operations_repo import (
    fetch_all_machines, fetch_machine,
    insert_machine, update_machine, delete_machine,
    fetch_all_machine_ops, fetch_machine_op,
    insert_machine_op, update_machine_op, delete_machine_op,
)
from ui.helpers import (
    EditModeMixin, make_table, buttons_row,
    section_label, confirm_delete, danger_button,
)
from ui.widgets.category_manager import CategoryCombo, CategoryManager
from ui.events import bus

_SPLITTER_STYLE = """
    QSplitter::handle { background: #e0e0e0; border-top: 1px solid #ccc; }
    QSplitter::handle:hover { background: #bbdefb; }
"""


def _labeled(widget, unit):
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
# فورم الماكينات
# ══════════════════════════════════════════════════════════

class _MachineForm(QWidget, EditModeMixin):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self.init_edit_mode(self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        grp  = QGroupBox("بيانات الماكينة")
        form = QFormLayout(grp)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = QLabel("─── إضافة ماكينة جديدة ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0;")
        form.addRow(self.lbl_mode)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("أدخل اسم الماكينة...")
        self.inp_name.setMinimumHeight(30)
        self.sp_hour = _spin()
        self.sp_unit = _spin()

        # ── التصنيف ──
        self.cmb_category = CategoryCombo(self.conn, scope="machine")

        form.addRow("الاسم :",                  self.inp_name)
        form.addRow("تكلفة التشغيل / ساعة :",   _labeled(self.sp_hour, "جنيه / ساعة"))
        form.addRow("تكلفة الاستهلاك / وحدة :", _labeled(self.sp_unit, "جنيه / وحدة"))
        form.addRow("التصنيف :",                self.cmb_category)
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

    def load_for_edit(self, m_id):
        m = fetch_machine(self.conn, m_id)
        if not m:
            return
        self.inp_name.setText(m["name"])
        self.sp_hour.setValue(m["rate_per_hour"])
        self.sp_unit.setValue(m["rate_per_unit"])
        self.cmb_category.set_category(m["category_id"])
        self.enter_edit_mode(m_id, f"─── تعديل: {m['name']} ───")

    def _add(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم الماكينة")
            return
        insert_machine(self.conn, name, self.sp_hour.value(), self.sp_unit.value(),
                       category_id=self.cmb_category.get_category())
        self._reset()
        bus.data_changed.emit()

    def _save_edit(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل الاسم")
            return
        update_machine(self.conn, self._editing_id, name,
                       self.sp_hour.value(), self.sp_unit.value(),
                       category_id=self.cmb_category.get_category())
        self._reset()
        bus.data_changed.emit()

    def _cancel(self):
        self._reset()

    def _reset(self):
        self.inp_name.clear()
        self.sp_hour.setValue(0)
        self.sp_unit.setValue(0)
        self.cmb_category.setCurrentIndex(0)
        self.exit_edit_mode("─── إضافة ماكينة جديدة ───")


# ══════════════════════════════════════════════════════════
# جدول الماكينات
# ══════════════════════════════════════════════════════════

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
            ["ID", "الاسم", "التصنيف", "ج / ساعة تشغيل", "ج / وحدة"],
            stretch_col=1
        )
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Fixed)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 160)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 100)
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
        m_id   = int(self.table.item(row, 0).text())
        m_name = self.table.item(row, 1).text()
        if self._form.is_editing and self._form._editing_id == m_id:
            self._form._reset()
        if confirm_delete(self, m_name):
            delete_machine(self.conn, m_id)
            bus.data_changed.emit()

    def _load(self):
        self.table.setRowCount(0)
        for r, m in enumerate(fetch_all_machines(self.conn)):
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(m["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(m["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(m["category_name"] if m["category_name"] else "—"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{m['rate_per_hour']:.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"{m['rate_per_unit']:.2f}"))


# ══════════════════════════════════════════════════════════
# فورم عمليات التشغيل
# ══════════════════════════════════════════════════════════

class _MachineOpForm(QWidget, EditModeMixin):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self.init_edit_mode(self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode)
        bus.data_changed.connect(self._refresh_machines)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        grp  = QGroupBox("بيانات العملية")
        form = QFormLayout(grp)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = QLabel("─── إضافة عملية تشغيل جديدة ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0;")
        form.addRow(self.lbl_mode)

        self.inp_name    = QLineEdit()
        self.inp_name.setPlaceholderText("مثال: قطع، لحام...")
        self.inp_name.setMinimumHeight(30)

        self.cmb_machine = QComboBox()
        self.cmb_machine.setMinimumHeight(30)
        self.cmb_machine.currentIndexChanged.connect(self._update_preview)

        self.cmb_mode = QComboBox()
        self.cmb_mode.setMinimumHeight(30)
        self.cmb_mode.addItem("🕐  وقت تشغيل",     "time")
        self.cmb_mode.addItem("📦  وحدات استهلاك", "unit")
        self.cmb_mode.currentIndexChanged.connect(self._on_mode_changed)

        self.sp_minutes = _spin(999999, 2)
        self.sp_minutes.valueChanged.connect(self._update_preview)
        self.sp_units   = _spin(999999, 4)
        self.sp_units.valueChanged.connect(self._update_preview)

        self.stack = QStackedWidget()
        self.stack.addWidget(_labeled(self.sp_minutes, "دقيقة"))
        self.stack.addWidget(_labeled(self.sp_units,   "وحدة"))

        # ── التصنيف ──
        self.cmb_category = CategoryCombo(self.conn, scope="machine")

        self.lbl_cost = QLabel("─")
        self.lbl_cost.setStyleSheet(
            "color:#1a6e1a; font-weight:bold;"
            "background:#f0faf0; border:1px solid #b2dfb2; border-radius:4px; padding:4px 8px;"
        )

        form.addRow("اسم العملية :", self.inp_name)
        form.addRow("الماكينة :",    self.cmb_machine)
        form.addRow("وضع الحساب :", self.cmb_mode)
        form.addRow("القيمة :",      self.stack)
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

        self._refresh_machines()

    def _refresh_machines(self):
        prev = self.cmb_machine.currentData()
        self.cmb_machine.blockSignals(True)
        self.cmb_machine.clear()
        for m in fetch_all_machines(self.conn):
            self.cmb_machine.addItem(m["name"], (m["id"], m["rate_per_hour"], m["rate_per_unit"]))
        if prev:
            for i in range(self.cmb_machine.count()):
                if self.cmb_machine.itemData(i)[0] == prev[0]:
                    self.cmb_machine.setCurrentIndex(i)
                    break
        self.cmb_machine.blockSignals(False)
        self._update_preview()

    def _on_mode_changed(self, _):
        self.stack.setCurrentIndex(0 if self.cmb_mode.currentData() == "time" else 1)
        self._update_preview()

    def _update_preview(self):
        data = self.cmb_machine.currentData()
        if not data:
            self.lbl_cost.setText("─")
            return
        _, rph, rpu = data
        if self.cmb_mode.currentData() == "time":
            val  = self.sp_minutes.value()
            cost = (val / 60.0) * rph
            self.lbl_cost.setText(f"{cost:.2f} جنيه / وحدة   ({val:.2f} د ÷ 60 × {rph:.2f})")
        else:
            val  = self.sp_units.value()
            cost = val * rpu
            self.lbl_cost.setText(f"{cost:.2f} جنيه / وحدة   ({val:.4f} × {rpu:.2f})")

    def load_for_edit(self, op_id):
        op = fetch_machine_op(self.conn, op_id)
        if not op:
            return
        self.inp_name.setText(op["name"])
        self._refresh_machines()
        for i in range(self.cmb_machine.count()):
            if self.cmb_machine.itemData(i)[0] == op["machine_id"]:
                self.cmb_machine.setCurrentIndex(i)
                break
        self.cmb_mode.setCurrentIndex(0 if op["mode"] == "time" else 1)
        self._on_mode_changed(None)
        if op["mode"] == "time":
            self.sp_minutes.setValue(op["value"])
        else:
            self.sp_units.setValue(op["value"])
        self.cmb_category.set_category(op["category_id"])
        self.enter_edit_mode(op_id, f"─── تعديل: {op['name']} ───")

    def _add(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم العملية")
            return
        data = self.cmb_machine.currentData()
        if data is None:
            QMessageBox.warning(self, "تنبيه", "أضف ماكينة أولاً")
            return
        val = self.sp_minutes.value() if self.cmb_mode.currentData() == "time" else self.sp_units.value()
        insert_machine_op(self.conn, data[0], name, self.cmb_mode.currentData(), val,
                          category_id=self.cmb_category.get_category())
        self._reset()
        bus.data_changed.emit()

    def _save_edit(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل الاسم")
            return
        data = self.cmb_machine.currentData()
        val  = self.sp_minutes.value() if self.cmb_mode.currentData() == "time" else self.sp_units.value()
        update_machine_op(self.conn, self._editing_id, data[0], name,
                          self.cmb_mode.currentData(), val,
                          category_id=self.cmb_category.get_category())
        self._reset()
        bus.data_changed.emit()

    def _cancel(self):
        self._reset()

    def _reset(self):
        self.inp_name.clear()
        self.sp_minutes.setValue(0)
        self.sp_units.setValue(0)
        self.lbl_cost.setText("─")
        self.cmb_mode.setCurrentIndex(0)
        self.stack.setCurrentIndex(0)
        self.cmb_category.setCurrentIndex(0)
        self.exit_edit_mode("─── إضافة عملية تشغيل جديدة ───")


# ══════════════════════════════════════════════════════════
# جدول عمليات التشغيل
# ══════════════════════════════════════════════════════════

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
            ["ID", "اسم العملية", "الماكينة", "التصنيف", "الوضع", "القيمة", "التكلفة"],
            stretch_col=1
        )
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Fixed)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 130)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 70)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 110)
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

    def _load(self):
        self.table.setRowCount(0)
        for r, op in enumerate(fetch_all_machine_ops(self.conn)):
            cost = (op["value"] / 60.0) * op["rate_per_hour"] \
                   if op["mode"] == "time" else op["value"] * op["rate_per_unit"]
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(op["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(op["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(op["machine_name"]))
            self.table.setItem(r, 3, QTableWidgetItem(op["category_name"] if op["category_name"] else "—"))
            self.table.setItem(r, 4, QTableWidgetItem("دقائق" if op["mode"] == "time" else "وحدات"))
            self.table.setItem(r, 5, QTableWidgetItem(f"{op['value']:.4f}"))
            self.table.setItem(r, 6, QTableWidgetItem(f"{cost:.2f} جنيه"))


# ══════════════════════════════════════════════════════════
# تبويب الماكينات
# ══════════════════════════════════════════════════════════

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
        splitter.setSizes([260, 400])
        splitter.setCollapsible(0, True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(splitter)


# ══════════════════════════════════════════════════════════
# تبويب عمليات التشغيل
# ══════════════════════════════════════════════════════════

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
        splitter.setSizes([320, 380])
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

        tabs = QTabWidget()
        tabs.addTab(_MachinesTab(self.conn),                       "🏭  الماكينات")
        tabs.addTab(_MachineOpsTab(self.conn),                     "📋  عمليات التشغيل")
        tabs.addTab(CategoryManager(self.conn, scope="machine"),   "🏷️  التصنيفات")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(tabs)

    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)
