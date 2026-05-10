"""
ui/tabs/accounting/journal_tab.py
===================================
_SmartEntryLine — صف إدخال ذكي (حساب + عملية + مبلغ).
JournalTab      — تبويب قيود اليومية.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QSplitter, QPushButton,
    QTableWidgetItem, QMessageBox,
    QLineEdit, QComboBox, QDateEdit, QRadioButton, QButtonGroup,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui  import QColor

from db.accounting_repo import (
    fetch_account, calc_signed_amount,
    fetch_all_entries, insert_entry, add_entry_lines,
    delete_entry, validate_entry_balance,
)
from ui.helpers import (
    make_table, setup_table_columns, buttons_row,
    section_label, danger_button, confirm_delete,
)
from ui.events import bus
from .helpers      import _spin
from .account_combo import _AccountCombo


class _SmartEntryLine(QFrame):
    def __init__(self, conn, on_change=None, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._on_change = on_change
        self._build()

    def _build(self):
        self.setStyleSheet("""
            QFrame {
                background: #fafafa;
                border: 1px solid #e8e8e8;
                border-radius: 6px;
            }
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(6)

        row1 = QHBoxLayout()
        self._acc_combo = _AccountCombo(self.conn)
        self._acc_combo.cmb_account.currentIndexChanged.connect(self._on_acc_changed)
        row1.addWidget(self._acc_combo, stretch=1)
        lay.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(8)

        lbl_op = QLabel("العملية:")
        lbl_op.setStyleSheet("font-weight:bold; font-size:11px;")

        self.rdo_inc = QRadioButton("➕ زيادة")
        self.rdo_dec = QRadioButton("➖ نقص")
        self.rdo_inc.setChecked(True)
        self._rdo_grp = QButtonGroup(self)
        self._rdo_grp.addButton(self.rdo_inc)
        self._rdo_grp.addButton(self.rdo_dec)
        self._rdo_grp.buttonClicked.connect(self._on_change_trigger)

        row2.addWidget(lbl_op)
        row2.addWidget(self.rdo_inc)
        row2.addWidget(self.rdo_dec)
        row2.addSpacing(16)

        lbl_amt = QLabel("المبلغ:")
        lbl_amt.setStyleSheet("font-weight:bold; font-size:11px;")
        self.sp_amount = _spin()
        self.sp_amount.setFixedWidth(130)
        self.sp_amount.valueChanged.connect(self._on_change_trigger)
        row2.addWidget(lbl_amt)
        row2.addWidget(self.sp_amount)
        row2.addSpacing(12)

        self.lbl_dr_cr = QLabel("—")
        self.lbl_dr_cr.setFixedWidth(120)
        self.lbl_dr_cr.setAlignment(Qt.AlignCenter)
        self.lbl_dr_cr.setStyleSheet(
            "font-size:12px; font-weight:bold; border-radius:4px;"
            "padding:4px 8px; background:#f5f5f5;"
        )
        row2.addWidget(self.lbl_dr_cr)
        row2.addStretch()

        self.btn_manual = QPushButton("⚙️ يدوي")
        self.btn_manual.setCheckable(True)
        self.btn_manual.setMinimumHeight(26)
        self.btn_manual.setStyleSheet(
            "QPushButton { background:#f5f5f5; border:1px solid #ccc;"
            "border-radius:4px; font-size:10px; padding:2px 6px; }"
            "QPushButton:checked { background:#fff3e0; border-color:#e65100;"
            "color:#e65100; }"
        )
        self.btn_manual.toggled.connect(self._toggle_manual)
        row2.addWidget(self.btn_manual)
        lay.addLayout(row2)

        self._manual_frame = QFrame()
        self._manual_frame.setStyleSheet(
            "QFrame { background:#fff8e1; border:1px solid #ffe082;"
            "border-radius:4px; }"
        )
        ml = QHBoxLayout(self._manual_frame)
        ml.setContentsMargins(8, 4, 8, 4)

        lbl_m = QLabel("⚙️ تحديد يدوي:")
        lbl_m.setStyleSheet("font-size:10px; color:#e65100; font-weight:bold;")
        self.rdo_dr = QRadioButton("مدين (DR)")
        self.rdo_cr = QRadioButton("دائن (CR)")
        self.rdo_dr.setChecked(True)
        grp2 = QButtonGroup(self)
        grp2.addButton(self.rdo_dr)
        grp2.addButton(self.rdo_cr)
        grp2.buttonClicked.connect(self._on_change_trigger)

        ml.addWidget(lbl_m)
        ml.addWidget(self.rdo_dr)
        ml.addWidget(self.rdo_cr)
        ml.addStretch()
        self._manual_frame.setVisible(False)
        lay.addWidget(self._manual_frame)

        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("بيان (اختياري)...")
        self.inp_desc.setMinimumHeight(26)
        lay.addWidget(self.inp_desc)

    def _on_acc_changed(self):
        self._update_dr_cr_label()
        if self._on_change:
            self._on_change()

    def _on_change_trigger(self):
        self._update_dr_cr_label()
        if self._on_change:
            self._on_change()

    def _toggle_manual(self, checked):
        self._manual_frame.setVisible(checked)
        self._update_dr_cr_label()

    def _update_dr_cr_label(self):
        acc_id = self._acc_combo.current_account_id()
        if not acc_id:
            self.lbl_dr_cr.setText("—")
            self.lbl_dr_cr.setStyleSheet(
                "font-size:12px; font-weight:bold; border-radius:4px;"
                "padding:4px 8px; background:#f5f5f5;"
            )
            return

        dr, cr = self.get_debit_credit()
        if dr > 0:
            self.lbl_dr_cr.setText(f"DR  {dr:,.2f}")
            self.lbl_dr_cr.setStyleSheet(
                "font-size:11px; font-weight:bold; color:#1565c0;"
                "background:#e3f2fd; border-radius:4px; padding:4px 8px;"
            )
        elif cr > 0:
            self.lbl_dr_cr.setText(f"CR  {cr:,.2f}")
            self.lbl_dr_cr.setStyleSheet(
                "font-size:11px; font-weight:bold; color:#c62828;"
                "background:#fdecea; border-radius:4px; padding:4px 8px;"
            )
        else:
            self.lbl_dr_cr.setText("0.00")
            self.lbl_dr_cr.setStyleSheet(
                "font-size:12px; font-weight:bold; border-radius:4px;"
                "padding:4px 8px; background:#f5f5f5;"
            )

    def get_debit_credit(self) -> tuple:
        acc_id = self._acc_combo.current_account_id()
        amount = self.sp_amount.value()
        if not acc_id or amount == 0:
            return 0.0, 0.0

        if self.btn_manual.isChecked():
            return (amount, 0.0) if self.rdo_dr.isChecked() else (0.0, amount)

        acc = fetch_account(self.conn, acc_id)
        if not acc:
            return 0.0, 0.0
        return calc_signed_amount(acc["type"], self.rdo_inc.isChecked(), amount)

    def get_values(self) -> dict | None:
        acc_id = self._acc_combo.current_account_id()
        if not acc_id:
            return None
        dr, cr = self.get_debit_credit()
        return {
            "account_id":  acc_id,
            "debit":       dr,
            "credit":      cr,
            "description": self.inp_desc.text().strip(),
        }

    def clear(self):
        self._acc_combo.cmb_account.setCurrentIndex(0)
        self.rdo_inc.setChecked(True)
        self.sp_amount.setValue(0)
        self.inp_desc.clear()
        self.btn_manual.setChecked(False)
        self.lbl_dr_cr.setText("—")


class JournalTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        bus.data_changed.connect(self._load_table)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)

        # ── فورم القيد ──
        form_w = QWidget()
        fl     = QVBoxLayout(form_w)
        fl.setContentsMargins(12, 10, 12, 10)
        fl.setSpacing(8)

        self.lbl_mode = QLabel("── قيد يومية جديد ──")
        self.lbl_mode.setStyleSheet(
            "font-weight:bold; color:#1565c0; font-size:12px;"
        )
        fl.addWidget(self.lbl_mode)

        info_row = QHBoxLayout()
        self.dt_date = QDateEdit(QDate.currentDate())
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDisplayFormat("yyyy-MM-dd")
        self.dt_date.setFixedWidth(130)

        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("وصف القيد...")
        self.inp_desc.setMinimumHeight(30)

        self.cmb_type = QComboBox()
        self.cmb_type.setMinimumHeight(30)
        self.cmb_type.setFixedWidth(120)
        for key, label in [
            ("manual","يدوي"), ("purchase","شراء"), ("sale","بيع"),
            ("payment","دفع"), ("receipt","تحصيل"), ("adjustment","تسوية"),
        ]:
            self.cmb_type.addItem(label, key)

        info_row.addWidget(QLabel("التاريخ:"))
        info_row.addWidget(self.dt_date)
        info_row.addWidget(QLabel("النوع:"))
        info_row.addWidget(self.cmb_type)
        info_row.addWidget(self.inp_desc, stretch=1)
        fl.addLayout(info_row)

        self.line1 = _SmartEntryLine(self.conn, on_change=self._update_balance)
        self.line2 = _SmartEntryLine(self.conn, on_change=self._update_balance)

        for lbl_text, line in [
            ("العملية الأولى:", self.line1),
            ("العملية الثانية (المقابلة):", self.line2),
        ]:
            lbl = QLabel(lbl_text)
            lbl.setStyleSheet("font-weight:bold; font-size:11px; color:#555;")
            fl.addWidget(lbl)
            fl.addWidget(line)

        bal_row = QHBoxLayout()
        self.lbl_sum_d  = QLabel("مدين: 0.00")
        self.lbl_sum_c  = QLabel("دائن: 0.00")
        self.lbl_bal_st = QLabel("—")
        for l in (self.lbl_sum_d, self.lbl_sum_c, self.lbl_bal_st):
            l.setStyleSheet("font-weight:bold; font-size:11px;")
        bal_row.addWidget(self.lbl_sum_d)
        bal_row.addSpacing(16)
        bal_row.addWidget(self.lbl_sum_c)
        bal_row.addSpacing(16)
        bal_row.addWidget(self.lbl_bal_st)
        bal_row.addStretch()
        fl.addLayout(bal_row)

        btn_save = QPushButton("💾 حفظ القيد")
        btn_save.setMinimumHeight(32)
        btn_save.setStyleSheet("""
            QPushButton { background:#1565c0; color:white;
                font-weight:bold; border-radius:6px; padding:0 18px; }
            QPushButton:hover { background:#0d47a1; }
        """)
        btn_save.clicked.connect(self._save)

        btn_clear = QPushButton("✖ مسح")
        btn_clear.setMinimumHeight(32)
        btn_clear.clicked.connect(self._clear_form)
        fl.addLayout(buttons_row(btn_save, btn_clear))
        splitter.addWidget(form_w)

        # ── جدول القيود ──
        table_w = QWidget()
        tl = QVBoxLayout(table_w)
        tl.setContentsMargins(12, 8, 12, 12)
        tl.setSpacing(6)
        tl.addWidget(section_label("── القيود المحاسبية ──"))

        self.table = make_table(
            ["#","رقم القيد","التاريخ","النوع","البيان","مدين","دائن"],
            stretch_col=4
        )
        setup_table_columns(self.table,
            widths={0:40,1:90,2:90,3:80,5:90,6:90}, stretch_col=4)
        self.table.setAlternatingRowColors(True)
        tl.addWidget(self.table, stretch=1)

        btn_del = danger_button("🗑️ حذف القيد")
        btn_del.setMinimumHeight(30)
        btn_del.clicked.connect(self._delete_entry)
        tl.addLayout(buttons_row(btn_del))
        splitter.addWidget(table_w)

        splitter.setSizes([400, 350])
        root.addWidget(splitter)
        self._load_table()

    def _update_balance(self):
        v1 = self.line1.get_values()
        v2 = self.line2.get_values()
        td = (v1["debit"]  if v1 else 0) + (v2["debit"]  if v2 else 0)
        tc = (v1["credit"] if v1 else 0) + (v2["credit"] if v2 else 0)
        self.lbl_sum_d.setText(f"مدين: {td:,.2f}")
        self.lbl_sum_c.setText(f"دائن: {tc:,.2f}")
        diff = abs(td - tc)
        if diff < 0.001 and td > 0:
            self.lbl_bal_st.setText("✅ متوازن")
            self.lbl_bal_st.setStyleSheet("font-weight:bold; color:#2e7d32;")
        else:
            self.lbl_bal_st.setText(f"⚠️ فرق: {diff:,.2f}" if td > 0 else "—")
            self.lbl_bal_st.setStyleSheet("font-weight:bold; color:#c62828;")

    def _save(self):
        v1 = self.line1.get_values()
        v2 = self.line2.get_values()
        if not v1 or not v2:
            QMessageBox.warning(self, "تنبيه", "اختر الحسابين أولًا")
            return
        if v1["account_id"] == v2["account_id"]:
            QMessageBox.warning(self, "تنبيه", "لا يمكن استخدام نفس الحساب في العمليتين")
            return
        lines = [v1, v2]
        if not validate_entry_balance(lines):
            QMessageBox.warning(self, "خطأ", "مجموع المدين ≠ مجموع الدائن")
            return
        desc = self.inp_desc.text().strip()
        if not desc:
            QMessageBox.warning(self, "تنبيه", "أدخل وصف القيد")
            return
        entry_id = insert_entry(
            self.conn,
            self.dt_date.date().toString("yyyy-MM-dd"),
            desc,
            self.cmb_type.currentData()
        )
        add_entry_lines(self.conn, entry_id, lines)
        self._clear_form()
        bus.data_changed.emit()
        QMessageBox.information(self, "تم", "✅ تم حفظ القيد")

    def _clear_form(self):
        self.line1.clear()
        self.line2.clear()
        self.inp_desc.clear()
        self.dt_date.setDate(QDate.currentDate())
        self._update_balance()

    def _load_table(self):
        entries = fetch_all_entries(self.conn)
        self.table.setRowCount(0)
        type_ar = {
            "manual":"يدوي","purchase":"شراء","sale":"بيع",
            "payment":"دفع","receipt":"تحصيل","adjustment":"تسوية",
        }
        for e in entries:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(e["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(e["ref_no"]))
            self.table.setItem(r, 2, QTableWidgetItem(e["date"]))
            self.table.setItem(r, 3, QTableWidgetItem(type_ar.get(e["type"], e["type"])))
            di = QTableWidgetItem(e["description"])
            di.setToolTip(e["description"])
            self.table.setItem(r, 4, di)
            self.table.setItem(r, 5, QTableWidgetItem(f"{e['total_debit']:,.2f}"))
            self.table.setItem(r, 6, QTableWidgetItem(f"{e['total_credit']:,.2f}"))

    def _delete_entry(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر قيدًا أولًا")
            return
        eid  = int(self.table.item(row, 0).text())
        desc = self.table.item(row, 4).text()
        if confirm_delete(self, desc):
            delete_entry(self.conn, eid)
            bus.data_changed.emit()