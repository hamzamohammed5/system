"""
ui/tabs/labor_tab.py
"""

from PyQt5.QtCore    import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget,
    QLineEdit, QPushButton, QTableWidgetItem, QSplitter,
    QDoubleSpinBox, QLabel, QMessageBox, QGroupBox, QHeaderView,
)

from db.connection      import get_connection
from db.settings_repo   import get_setting, set_setting
from db.operations_repo import (
    fetch_all_labor_ops, fetch_labor_op,
    insert_labor_op, update_labor_op, delete_labor_op,
)
from ui.helpers import (
    EditModeMixin, make_table, buttons_row,
    section_label, confirm_delete, danger_button,
)
from ui.widgets.category_manager import CategoryCombo, CategoryManager
from ui.widgets.bulk_replace_dialog import BulkReplaceDialog
from ui.widgets.filter_bar import FilterBar
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
# لوحة الإعدادات
# ══════════════════════════════════════════════════════════

class _LaborSettingsPanel(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self._load()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        grp  = QGroupBox("معايير حساب تكلفة العمالة")
        form = QFormLayout(grp)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.sp_salary   = _spin()
        self.sp_days     = _spin(31, 0)
        self.sp_holidays = _spin(31, 0)
        self.sp_hours    = _spin(24, 1)
        self.sp_overhead = _spin(10, 2)

        form.addRow("الراتب الأساسي :",         _labeled(self.sp_salary,   "جنيه / شهر"))
        form.addRow("أيام العمل :",             _labeled(self.sp_days,     "يوم / شهر"))
        form.addRow("أيام الإجازات :",          _labeled(self.sp_holidays, "يوم / شهر"))
        form.addRow("ساعات العمل / يوم :",      _labeled(self.sp_hours,    "ساعة / يوم"))
        form.addRow("معامل الأعباء الإدارية :", _labeled(self.sp_overhead, "×"))

        self.lbl_rate = QLabel("─")
        self.lbl_rate.setStyleSheet(
            "font-weight:bold; color:#1a6e1a; font-size:13px;"
            "background:#f0faf0; border:1px solid #b2dfb2;"
            "border-radius:4px; padding:4px 8px;"
        )
        form.addRow("➡  معدل الأجر / ساعة :", self.lbl_rate)
        layout.addWidget(grp)

        for sp in (self.sp_salary, self.sp_days, self.sp_holidays,
                   self.sp_hours, self.sp_overhead):
            sp.valueChanged.connect(self._update_preview)

        btn = QPushButton("💾  حفظ إعدادات العمالة")
        btn.setMinimumHeight(32)
        btn.clicked.connect(self._save)
        layout.addWidget(btn)
        layout.addStretch()

    def _calc_rate(self):
        net_days  = max(self.sp_days.value() - self.sp_holidays.value(), 1)
        net_hours = net_days * max(self.sp_hours.value(), 1)
        return (self.sp_salary.value() / net_hours) * self.sp_overhead.value() if net_hours else 0.0

    def _update_preview(self):
        self.lbl_rate.setText(f"{self._calc_rate():.2f}  جنيه / ساعة")

    def _load(self):
        self.sp_salary.setValue(  get_setting(self.conn, "monthly_salary",    3000))
        self.sp_days.setValue(    get_setting(self.conn, "working_days",         25))
        self.sp_holidays.setValue(get_setting(self.conn, "holiday_days",          4))
        self.sp_hours.setValue(   get_setting(self.conn, "working_hours_day",     8))
        self.sp_overhead.setValue(get_setting(self.conn, "overhead_factor",    1.10))
        self._update_preview()

    def _save(self):
        set_setting(self.conn, "monthly_salary",    self.sp_salary.value())
        set_setting(self.conn, "working_days",      self.sp_days.value())
        set_setting(self.conn, "holiday_days",      self.sp_holidays.value())
        set_setting(self.conn, "working_hours_day", self.sp_hours.value())
        set_setting(self.conn, "overhead_factor",   self.sp_overhead.value())
        QMessageBox.information(self, "تم", "✅  تم حفظ إعدادات العمالة")
        bus.data_changed.emit()

    def get_hourly_rate(self):
        return self._calc_rate()


# ══════════════════════════════════════════════════════════
# فورم + جدول العمليات
# ══════════════════════════════════════════════════════════

class _LaborOpForm(QWidget, EditModeMixin):
    def __init__(self, conn, settings: _LaborSettingsPanel, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._settings = settings
        self._build()
        self.init_edit_mode(self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode)
        bus.data_changed.connect(self._update_preview)

    def _build(self):
        layout = QVBoxLayout(self)
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


class _LaborOpTable(QWidget):
    def __init__(self, conn, settings: _LaborSettingsPanel, form: _LaborOpForm, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._settings = settings
        self._form     = form
        self._all_rows = []
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(6)
        root.addWidget(section_label("─── عمليات العمالة المحفوظة ───"))

        self._filter = FilterBar(self.conn, scope="labor")
        self._filter.filter_changed.connect(self._apply_filter)
        root.addWidget(self._filter)

        self.table = make_table(
            ["ID", "اسم العملية", "التصنيف", "الوقت (دقيقة)", "التكلفة / وحدة"],
            stretch_col=1
        )
        hh = self.table.horizontalHeader()
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 160)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 110)
        self.table.setColumnWidth(4, 130)
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

    def _selected_row(self):
        return self.table.currentRow()

    def _edit(self):
        row = self._selected_row()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر عملية أولاً")
            return
        self._form.load_for_edit(int(self.table.item(row, 0).text()))

    def _delete(self):
        row = self._selected_row()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر عملية أولاً")
            return
        op_id   = int(self.table.item(row, 0).text())
        op_name = self.table.item(row, 1).text()
        if self._form.is_editing and self._form._editing_id == op_id:
            self._form._reset()
        if confirm_delete(self, op_name):
            delete_labor_op(self.conn, op_id)
            bus.data_changed.emit()

    def _bulk_replace(self):
        row = self._selected_row()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر عملية أولاً")
            return
        op_id   = int(self.table.item(row, 0).text())
        op_name = self.table.item(row, 1).text()
        dlg = BulkReplaceDialog(
            conn=self.conn, child_type="labor_op",
            child_id=op_id, child_name=op_name, parent=self,
        )
        dlg.exec_()

    def _load(self):
        self._all_rows = list(fetch_all_labor_ops(self.conn))
        self._apply_filter()

    def _apply_filter(self):
        rate = self._settings.get_hourly_rate()
        self.table.setRowCount(0)
        shown = 0
        for op in self._all_rows:
            if not self._filter.match(op["name"], op["category_id"]):
                continue
            cost = (op["minutes"] / 60.0) * rate
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(op["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(op["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(op["category_name"] or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{op['minutes']:.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"{cost:.2f} جنيه"))
            shown += 1
        self._filter.set_count(shown, len(self._all_rows))


class _LaborOpsTab(QWidget):
    def __init__(self, conn, settings, parent=None):
        super().__init__(parent)
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(_SPLITTER_STYLE)

        self._form  = _LaborOpForm(conn, settings)
        self._table = _LaborOpTable(conn, settings, self._form)

        splitter.addWidget(self._form)
        splitter.addWidget(self._table)
        splitter.setSizes([280, 400])
        splitter.setCollapsible(0, True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(splitter)


class LaborTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn = get_connection()
        self._settings = _LaborSettingsPanel(self.conn)

        tabs = QTabWidget()
        tabs.addTab(self._settings,                                "⚙️  إعدادات العمالة")
        tabs.addTab(_LaborOpsTab(self.conn, self._settings),       "📋  عمليات العمالة")
        tabs.addTab(CategoryManager(self.conn, scope="labor"),     "🏷️  التصنيفات")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(tabs)

    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)
