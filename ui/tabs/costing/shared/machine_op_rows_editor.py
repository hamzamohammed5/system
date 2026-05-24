"""
ui/widgets/costing/machine_op_rows_editor.py
=====================================
_OpRowsEditor — محرر صفوف عملية التشغيل.

يُستخدم داخل فورم عملية التشغيل (_MachineOpForm).
يعرض جدولاً بسيطاً لإضافة/تعديل/حذف صفوف (label + value + count).

التكلفة المحسوبة للصف = (value × rate) ÷ count
حيث rate يُحدد من الماكينة + mode.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QGroupBox, QMessageBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor, QFont

from db.costing.machine_op_rows_repo import (
    fetch_op_rows, insert_op_row, update_op_row,
    delete_op_row, calc_op_row_cost, calc_op_total_cost,
)
from ui.events import bus


class _OpRowsEditor(QGroupBox):
    """
    محرر صفوف عملية التشغيل.

    الاستخدام:
        self._rows_editor = _OpRowsEditor(conn)
        self._rows_editor.load_op(op_id, machine_mode, rate_per_hour, rate_per_unit)
    """

    def __init__(self, conn, parent=None):
        super().__init__("📋  صفوف العملية", parent)
        self.conn         = conn
        self._op_id       = None
        self._mode        = "time"   # "time" | "unit"
        self._rate_hour   = 0.0
        self._rate_unit   = 0.0
        self._editing_row_id = None
        self._build()
        self.setEnabled(False)

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold; color: #e65100;
                border: 1px solid #ffcc80;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
                background: #fffde7;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                padding: 0 6px;
            }
        """)

        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(10, 12, 10, 10)

        # ── شرح الوضع الحالي ──
        self.lbl_mode_info = QLabel("⏱ وضع الحساب: بالوقت (من الماكينة)")
        self.lbl_mode_info.setStyleSheet(
            "font-size:10px; color:#555; font-weight:normal;"
            "background:#e3f2fd; border-radius:4px; padding:4px 8px;"
            "border:1px solid #90caf9;"
        )
        root.addWidget(self.lbl_mode_info)

        # ── فورم إضافة/تعديل صف ──
        form_row = QHBoxLayout()
        form_row.setSpacing(8)

        lbl_label = QLabel("الوصف:")
        lbl_label.setStyleSheet("font-weight:bold; font-size:11px;")
        self.inp_label = QLineEdit()
        self.inp_label.setPlaceholderText("وصف اختياري للصف...")
        self.inp_label.setMinimumHeight(28)

        self.lbl_value = QLabel("القيمة (د):")  # تتغير حسب mode
        self.lbl_value.setStyleSheet("font-weight:bold; font-size:11px;")
        self.sp_value = QDoubleSpinBox()
        self.sp_value.setRange(0, 999999)
        self.sp_value.setDecimals(4)
        self.sp_value.setMinimumHeight(28)
        self.sp_value.setFixedWidth(100)
        self.sp_value.valueChanged.connect(self._update_preview)

        lbl_count = QLabel("العدد:")
        lbl_count.setStyleSheet("font-weight:bold; font-size:11px;")
        self.sp_count = QDoubleSpinBox()
        self.sp_count.setRange(0.0001, 999999)
        self.sp_count.setDecimals(4)
        self.sp_count.setValue(1.0)
        self.sp_count.setMinimumHeight(28)
        self.sp_count.setFixedWidth(90)
        self.sp_count.valueChanged.connect(self._update_preview)

        # معاينة التكلفة
        self.lbl_preview = QLabel("= ─")
        self.lbl_preview.setStyleSheet(
            "color:#e65100; font-weight:bold; font-size:11px; min-width:130px;"
        )

        self.btn_add    = QPushButton("➕ إضافة صف")
        self.btn_save   = QPushButton("💾 حفظ")
        self.btn_cancel = QPushButton("✖")
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        self.btn_cancel.setFixedWidth(28)
        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn.setMinimumHeight(28)

        self.btn_add.clicked.connect(self._add_row)
        self.btn_save.clicked.connect(self._save_edit)
        self.btn_cancel.clicked.connect(self._reset_form)

        form_row.addWidget(lbl_label)
        form_row.addWidget(self.inp_label, stretch=2)
        form_row.addWidget(self.lbl_value)
        form_row.addWidget(self.sp_value)
        form_row.addWidget(lbl_count)
        form_row.addWidget(self.sp_count)
        form_row.addWidget(self.lbl_preview)
        form_row.addWidget(self.btn_add)
        form_row.addWidget(self.btn_save)
        form_row.addWidget(self.btn_cancel)
        root.addLayout(form_row)

        # ── جدول الصفوف ──
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "الوصف", "القيمة", "العدد", "تكلفة/قطعة"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setMaximumHeight(180)
        self.table.setMinimumHeight(80)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Fixed)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Interactive)
        hh.setSectionResizeMode(3, QHeaderView.Interactive)
        hh.setSectionResizeMode(4, QHeaderView.Interactive)
        self.table.setColumnHidden(0, True)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 110)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignRight)

        root.addWidget(self.table)

        # ── مجموع التكلفة ──
        total_row = QHBoxLayout()
        total_row.addStretch()
        lbl_total_lbl = QLabel("إجمالي تكلفة العملية:")
        lbl_total_lbl.setStyleSheet("font-size:11px; font-weight:bold; color:#333;")
        self.lbl_total = QLabel("─")
        self.lbl_total.setStyleSheet(
            "color:#1a6e1a; font-weight:bold; font-size:12px; min-width:140px;"
            "background:#f0faf0; border:1px solid #b2dfb2; border-radius:4px; padding:3px 8px;"
        )
        total_row.addWidget(lbl_total_lbl)
        total_row.addWidget(self.lbl_total)
        root.addLayout(total_row)

        # ── أزرار تعديل/حذف ──
        btn_row = QHBoxLayout()
        btn_edit = QPushButton("✏️ تعديل الصف")
        btn_del  = QPushButton("🗑️ حذف الصف")
        btn_del.setStyleSheet("color:#c0392b;")
        for btn in (btn_edit, btn_del):
            btn.setMinimumHeight(26)
        btn_edit.clicked.connect(self._edit_row)
        btn_del.clicked.connect(self._delete_row)
        btn_row.addWidget(btn_edit)
        btn_row.addWidget(btn_del)
        btn_row.addStretch()
        root.addLayout(btn_row)

    # ══════════════════════════════════════════════════════
    # API خارجي
    # ══════════════════════════════════════════════════════

    def load_op(self, op_id: int, mode: str,
                rate_per_hour: float, rate_per_unit: float):
        """تحميل صفوف عملية تشغيل."""
        self._op_id     = op_id
        self._mode      = mode
        self._rate_hour = rate_per_hour
        self._rate_unit = rate_per_unit
        self.setEnabled(True)
        self._update_mode_ui()
        self._reset_form()
        self._load_table()

    def update_rates(self, mode: str, rate_per_hour: float, rate_per_unit: float):
        """تحديث المعدلات لو تغيرت الماكينة أو الوضع."""
        self._mode      = mode
        self._rate_hour = rate_per_hour
        self._rate_unit = rate_per_unit
        self._update_mode_ui()
        self._update_preview()
        if self._op_id:
            self._load_table()

    def clear(self):
        self._op_id = None
        self.table.setRowCount(0)
        self.lbl_total.setText("─")
        self._reset_form()
        self.setEnabled(False)

    # ══════════════════════════════════════════════════════
    # منطق الـ UI
    # ══════════════════════════════════════════════════════

    def _update_mode_ui(self):
        if self._mode == "time":
            self.lbl_mode_info.setText(
                f"⏱ وضع الحساب: بالوقت  │  معدل: {self._rate_hour:.2f} جنيه/ساعة"
            )
            self.lbl_value.setText("الوقت (د):")
        else:
            self.lbl_mode_info.setText(
                f"📦 وضع الحساب: بالوحدة  │  معدل: {self._rate_unit:.2f} جنيه/وحدة"
            )
            self.lbl_value.setText("الوحدات:")

    def _update_preview(self):
        value = self.sp_value.value()
        count = max(self.sp_count.value(), 0.0001)
        if self._mode == "time":
            raw = (value / 60.0) * self._rate_hour
        else:
            raw = value * self._rate_unit
        unit_cost = raw / count
        self.lbl_preview.setText(f"= {unit_cost:.4f} ج/قطعة")

    def _load_table(self):
        if self._op_id is None:
            return
        self.table.setRowCount(0)
        rows = fetch_op_rows(self.conn, self._op_id)
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(row["label"] or "—"))

            # القيمة مع وحدة
            val_txt = (
                f"{row['value']:.4g} د"
                if self._mode == "time"
                else f"{row['value']:.4g} وحدة"
            )
            val_item = QTableWidgetItem(val_txt)
            val_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 2, val_item)

            cnt_item = QTableWidgetItem(f"{row['count']:.4g}")
            cnt_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 3, cnt_item)

            # تكلفة الصف
            row_cost = calc_op_row_cost(self.conn, row["id"])
            cost_item = QTableWidgetItem(f"{row_cost:.4f} ج")
            cost_item.setForeground(QColor("#1565c0"))
            cost_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 4, cost_item)

        # تحديث الإجمالي
        total = calc_op_total_cost(self.conn, self._op_id)
        self.lbl_total.setText(f"{total:.4f} جنيه / قطعة")

    # ══════════════════════════════════════════════════════
    # CRUD
    # ══════════════════════════════════════════════════════

    def _add_row(self):
        if self._op_id is None:
            return
        value = self.sp_value.value()
        count = self.sp_count.value()
        label = self.inp_label.text().strip()
        insert_op_row(
            self.conn, self._op_id, label, value, count,
            sort_order=self.table.rowCount()
        )
        self._reset_form()
        self._load_table()
        bus.data_changed.emit()

    def _edit_row(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر صفاً أولاً")
            return
        from db.costing.machine_op_rows_repo import fetch_op_row
        rid = int(self.table.item(row, 0).text())
        r   = fetch_op_row(self.conn, rid)
        if not r:
            return
        self._editing_row_id = rid
        self.inp_label.setText(r["label"] or "")
        self.sp_value.setValue(float(r["value"]))
        self.sp_count.setValue(float(r["count"]))
        self._update_preview()
        self.btn_add.setVisible(False)
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)

    def _save_edit(self):
        if self._editing_row_id is None:
            return
        update_op_row(
            self.conn, self._editing_row_id,
            self.inp_label.text().strip(),
            self.sp_value.value(),
            self.sp_count.value(),
        )
        self._reset_form()
        self._load_table()
        bus.data_changed.emit()

    def _delete_row(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر صفاً أولاً")
            return
        # لا يجوز حذف آخر صف
        if self.table.rowCount() <= 1:
            QMessageBox.warning(
                self, "تنبيه",
                "يجب أن تحتوي العملية على صف واحد على الأقل."
            )
            return
        rid = int(self.table.item(row, 0).text())
        delete_op_row(self.conn, rid)
        self._load_table()
        bus.data_changed.emit()

    def _reset_form(self):
        self._editing_row_id = None
        self.inp_label.clear()
        self.sp_value.setValue(0.0)
        self.sp_count.setValue(1.0)
        self._update_preview()
        self.btn_add.setVisible(True)
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)