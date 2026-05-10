"""
ui/tabs/accounting/journal_tab.py
===================================
قيود اليومية — تصميم جديد:
  - صفوف غير محدودة (DR و CR)
  - إجمالي مدين / دائن في الأسفل مع indicator التوازن
  - auto-fill: لو DR=1000 والصف التالي CR يقترح 1000 تلقائياً
  - تقسيم: ممكن توزع المبلغ على أكتر من صف
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QSplitter, QPushButton,
    QTableWidgetItem, QMessageBox,
    QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox,
    QScrollArea, QSizePolicy,
)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui  import QColor

from db.accounting_repo import (
    fetch_account,
    fetch_all_entries, insert_entry, add_entry_lines,
    delete_entry, validate_entry_balance,
    fetch_leaf_accounts,
)
from ui.helpers import (
    make_table, setup_table_columns, buttons_row,
    section_label, danger_button, confirm_delete,
)
from ui.events import bus
from .helpers      import _spin
from .account_combo import _AccountCombo


# ══════════════════════════════════════════════════════════
# صف إدخال واحد (حساب + مبلغ + DR/CR)
# ══════════════════════════════════════════════════════════

class _EntryLine(QFrame):
    """
    صف واحد في القيد:
      [حساب combo] [مبلغ] [DR / CR] [بيان] [حذف]
    """
    def __init__(self, conn, side: str, on_change=None, on_remove=None, parent=None):
        """
        side: 'dr' أو 'cr' — يحدد الجانب الافتراضي
        """
        super().__init__(parent)
        self.conn       = conn
        self._side      = side          # 'dr' أو 'cr'
        self._on_change = on_change
        self._on_remove = on_remove
        self._build()

    def _build(self):
        self.setStyleSheet("""
            QFrame {
                background: #fafafa;
                border: 1px solid #e8e8e8;
                border-radius: 6px;
            }
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(6)

        # ── حساب ──
        self._acc_combo = _AccountCombo(self.conn)
        self._acc_combo.cmb_account.currentIndexChanged.connect(self._changed)
        lay.addWidget(self._acc_combo, stretch=3)

        # ── المبلغ ──
        self.sp_amount = QDoubleSpinBox()
        self.sp_amount.setRange(0, 999_999_999)
        self.sp_amount.setDecimals(2)
        self.sp_amount.setMinimumHeight(28)
        self.sp_amount.setFixedWidth(120)
        self.sp_amount.valueChanged.connect(self._changed)
        lay.addWidget(self.sp_amount)

        # ── DR / CR toggle ──
        self.btn_side = QPushButton("DR" if self._side == "dr" else "CR")
        self.btn_side.setCheckable(True)
        self.btn_side.setChecked(self._side == "dr")
        self.btn_side.setFixedWidth(50)
        self.btn_side.setMinimumHeight(28)
        self._update_side_style()
        self.btn_side.toggled.connect(self._on_side_toggled)
        lay.addWidget(self.btn_side)

        # ── بيان ──
        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("بيان...")
        self.inp_desc.setMinimumHeight(28)
        self.inp_desc.setMinimumWidth(100)
        lay.addWidget(self.inp_desc, stretch=2)

        # ── حذف ──
        btn_del = QPushButton("✖")
        btn_del.setFixedSize(28, 28)
        btn_del.setStyleSheet(
            "QPushButton { background:transparent; border:none; color:#aaa; font-size:13px; }"
            "QPushButton:hover { color:#e53935; }"
        )
        btn_del.clicked.connect(lambda: self._on_remove(self) if self._on_remove else None)
        lay.addWidget(btn_del)

    def _on_side_toggled(self, checked):
        self._side = "dr" if checked else "cr"
        self.btn_side.setText("DR" if checked else "CR")
        self._update_side_style()
        self._changed()

    def _update_side_style(self):
        if self._side == "dr":
            self.btn_side.setStyleSheet("""
                QPushButton {
                    background: #e3f2fd; color: #1565c0;
                    font-weight: bold; border: 1px solid #90caf9;
                    border-radius: 4px;
                }
                QPushButton:hover { background: #bbdefb; }
            """)
        else:
            self.btn_side.setStyleSheet("""
                QPushButton {
                    background: #fdecea; color: #c62828;
                    font-weight: bold; border: 1px solid #ef9a9a;
                    border-radius: 4px;
                }
                QPushButton:hover { background: #ffcdd2; }
            """)

    def _changed(self):
        if self._on_change:
            self._on_change()

    # ── API ──
    def get_values(self) -> dict | None:
        acc_id = self._acc_combo.current_account_id()
        amount = self.sp_amount.value()
        if not acc_id or amount == 0:
            return None
        dr = amount if self._side == "dr" else 0.0
        cr = amount if self._side == "cr" else 0.0
        return {
            "account_id":  acc_id,
            "debit":       dr,
            "credit":      cr,
            "description": self.inp_desc.text().strip(),
        }

    def set_amount(self, amount: float):
        self.sp_amount.setValue(amount)

    def set_side(self, side: str):
        self._side = side
        self.btn_side.setChecked(side == "dr")
        self.btn_side.setText("DR" if side == "dr" else "CR")
        self._update_side_style()

    def get_amount(self) -> float:
        return self.sp_amount.value()

    def get_side(self) -> str:
        return self._side

    def clear(self):
        self._acc_combo.cmb_account.setCurrentIndex(0)
        self.sp_amount.setValue(0)
        self.inp_desc.clear()


# ══════════════════════════════════════════════════════════
# فورم القيد الكامل
# ══════════════════════════════════════════════════════════

class _JournalForm(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._lines: list[_EntryLine] = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        # ── رأس: تاريخ + نوع + وصف ──
        self.lbl_mode = QLabel("── قيد يومية جديد ──")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0; font-size:12px;")
        root.addWidget(self.lbl_mode)

        info_row = QHBoxLayout()
        info_row.setSpacing(8)

        self.dt_date = QDateEdit(QDate.currentDate())
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDisplayFormat("yyyy-MM-dd")
        self.dt_date.setFixedWidth(130)
        self.dt_date.setMinimumHeight(30)

        self.cmb_type = QComboBox()
        self.cmb_type.setMinimumHeight(30)
        self.cmb_type.setFixedWidth(120)
        for key, label in [
            ("manual",     "يدوي"),
            ("purchase",   "شراء"),
            ("sale",       "بيع"),
            ("payment",    "دفع"),
            ("receipt",    "تحصيل"),
            ("adjustment", "تسوية"),
        ]:
            self.cmb_type.addItem(label, key)

        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("وصف القيد...")
        self.inp_desc.setMinimumHeight(30)

        info_row.addWidget(QLabel("التاريخ:"))
        info_row.addWidget(self.dt_date)
        info_row.addWidget(QLabel("النوع:"))
        info_row.addWidget(self.cmb_type)
        info_row.addWidget(self.inp_desc, stretch=1)
        root.addLayout(info_row)

        # ── رؤوس الأعمدة ──
        hdr = QWidget()
        hdr.setStyleSheet("background:transparent;")
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(8, 0, 8, 0)
        hdr_lay.setSpacing(6)

        def _h(text, stretch=0, w=None):
            lbl = QLabel(text)
            lbl.setStyleSheet(
                "font-size:10px; font-weight:bold; color:#666;"
                "border-bottom:1px solid #ddd; background:transparent;"
            )
            if w:
                lbl.setFixedWidth(w)
            hdr_lay.addWidget(lbl, stretch=stretch)

        _h("الحساب",  stretch=3)
        _h("المبلغ",  w=120)
        _h("الجانب",  w=50)
        _h("البيان",  stretch=2)
        _h("",        w=28)
        root.addWidget(hdr)

        # ── منطقة الصفوف ──
        self._rows_container = QWidget()
        self._rows_container.setStyleSheet("background:transparent;")
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setSpacing(4)
        self._rows_layout.setContentsMargins(0, 0, 4, 0)
        self._rows_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._rows_container)
        scroll.setMinimumHeight(140)
        scroll.setMaximumHeight(320)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background: #f9f9f9;
            }
        """)
        root.addWidget(scroll, stretch=1)

        # ── أزرار الإضافة ──
        add_row = QHBoxLayout()
        add_row.setSpacing(8)

        btn_add_dr = QPushButton("➕ إضافة صف مدين (DR)")
        btn_add_dr.setMinimumHeight(28)
        btn_add_dr.setStyleSheet("""
            QPushButton {
                background:#e3f2fd; color:#1565c0;
                border:1px solid #90caf9; border-radius:4px;
                font-weight:bold; padding:2px 10px;
            }
            QPushButton:hover { background:#bbdefb; }
        """)
        btn_add_dr.clicked.connect(lambda: self._add_line("dr"))

        btn_add_cr = QPushButton("➕ إضافة صف دائن (CR)")
        btn_add_cr.setMinimumHeight(28)
        btn_add_cr.setStyleSheet("""
            QPushButton {
                background:#fdecea; color:#c62828;
                border:1px solid #ef9a9a; border-radius:4px;
                font-weight:bold; padding:2px 10px;
            }
            QPushButton:hover { background:#ffcdd2; }
        """)
        btn_add_cr.clicked.connect(lambda: self._add_line("cr"))

        add_row.addWidget(btn_add_dr)
        add_row.addWidget(btn_add_cr)
        add_row.addStretch()
        root.addLayout(add_row)

        # ── شريط التوازن ──
        balance_frame = QFrame()
        balance_frame.setStyleSheet("""
            QFrame {
                background: #f0f4ff;
                border: 1px solid #c5cae9;
                border-radius: 6px;
            }
        """)
        bal_lay = QHBoxLayout(balance_frame)
        bal_lay.setContentsMargins(12, 8, 12, 8)
        bal_lay.setSpacing(20)

        lbl_dr_title = QLabel("إجمالي مدين (DR):")
        lbl_dr_title.setStyleSheet("font-weight:bold; color:#1565c0;")
        self.lbl_total_dr = QLabel("0.00")
        self.lbl_total_dr.setStyleSheet(
            "font-size:14px; font-weight:bold; color:#1565c0;"
            "background:#e3f2fd; border-radius:4px; padding:4px 10px;"
        )

        lbl_cr_title = QLabel("إجمالي دائن (CR):")
        lbl_cr_title.setStyleSheet("font-weight:bold; color:#c62828;")
        self.lbl_total_cr = QLabel("0.00")
        self.lbl_total_cr.setStyleSheet(
            "font-size:14px; font-weight:bold; color:#c62828;"
            "background:#fdecea; border-radius:4px; padding:4px 10px;"
        )

        self.lbl_diff = QLabel("الفرق: 0.00")
        self.lbl_diff.setStyleSheet(
            "font-size:13px; font-weight:bold; color:#2e7d32;"
            "background:#f1f8e9; border-radius:4px; padding:4px 10px;"
        )

        self.lbl_status = QLabel("○ أضف صفوف")
        self.lbl_status.setStyleSheet("font-size:12px; color:#888; font-weight:bold;")

        bal_lay.addWidget(lbl_dr_title)
        bal_lay.addWidget(self.lbl_total_dr)
        bal_lay.addSpacing(8)
        bal_lay.addWidget(lbl_cr_title)
        bal_lay.addWidget(self.lbl_total_cr)
        bal_lay.addSpacing(8)
        bal_lay.addWidget(self.lbl_diff)
        bal_lay.addWidget(self.lbl_status)
        bal_lay.addStretch()
        root.addWidget(balance_frame)

        # ── أزرار الحفظ ──
        self.btn_save   = QPushButton("💾 حفظ القيد")
        self.btn_cancel = QPushButton("✖ إلغاء")
        self.btn_save.setMinimumHeight(32)
        self.btn_cancel.setMinimumHeight(32)
        self.btn_save.setStyleSheet("""
            QPushButton { background:#1565c0; color:white;
                font-weight:bold; border-radius:6px; padding:0 18px; }
            QPushButton:hover { background:#0d47a1; }
        """)
        self.btn_cancel.setVisible(False)
        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self._clear)
        root.addLayout(buttons_row(self.btn_save, self.btn_cancel))

        # ── ابدأ بصفين افتراضيين ──
        self._add_line("dr")
        self._add_line("cr")

    # ══════════════════════════════════════════════════════
    # إدارة الصفوف
    # ══════════════════════════════════════════════════════

    def _add_line(self, side: str, amount: float = 0.0) -> _EntryLine:
        line = _EntryLine(
            self.conn,
            side=side,
            on_change=self._update_balance,
            on_remove=self._remove_line,
        )
        if amount:
            line.set_amount(amount)
        self._lines.append(line)
        self._rows_layout.insertWidget(self._rows_layout.count() - 1, line)
        self._update_balance()
        return line

    def _remove_line(self, line: _EntryLine):
        if len(self._lines) <= 2:
            QMessageBox.information(self, "تنبيه", "القيد يحتاج صفين على الأقل")
            return
        self._lines.remove(line)
        self._rows_layout.removeWidget(line)
        line.deleteLater()
        self._update_balance()

    def _clear_lines(self):
        for line in list(self._lines):
            self._rows_layout.removeWidget(line)
            line.deleteLater()
        self._lines.clear()

    # ══════════════════════════════════════════════════════
    # حساب التوازن
    # ══════════════════════════════════════════════════════

    def _update_balance(self):
        total_dr = sum(
            ln.get_amount() for ln in self._lines if ln.get_side() == "dr"
        )
        total_cr = sum(
            ln.get_amount() for ln in self._lines if ln.get_side() == "cr"
        )
        diff = total_dr - total_cr

        self.lbl_total_dr.setText(f"{total_dr:,.2f}")
        self.lbl_total_cr.setText(f"{total_cr:,.2f}")
        self.lbl_diff.setText(f"الفرق: {abs(diff):,.2f}")

        if total_dr == 0 and total_cr == 0:
            self.lbl_status.setText("○ أضف صفوف")
            self.lbl_status.setStyleSheet("font-size:12px; color:#888; font-weight:bold;")
            self.lbl_diff.setStyleSheet(
                "font-size:13px; font-weight:bold; color:#888;"
                "background:#f5f5f5; border-radius:4px; padding:4px 10px;"
            )
        elif abs(diff) < 0.001:
            self.lbl_status.setText("✅ متوازن")
            self.lbl_status.setStyleSheet("font-size:12px; color:#2e7d32; font-weight:bold;")
            self.lbl_diff.setStyleSheet(
                "font-size:13px; font-weight:bold; color:#2e7d32;"
                "background:#f1f8e9; border-radius:4px; padding:4px 10px;"
            )
        else:
            self.lbl_status.setText("⚠️ غير متوازن")
            self.lbl_status.setStyleSheet("font-size:12px; color:#c62828; font-weight:bold;")
            self.lbl_diff.setStyleSheet(
                "font-size:13px; font-weight:bold; color:#c62828;"
                "background:#fdecea; border-radius:4px; padding:4px 10px;"
            )

        # ── auto-fill: لو عندنا DR بس → اقترح مبلغ CR المتبقي ──
        self._auto_suggest_remaining()

    def _auto_suggest_remaining(self):
        """
        لو في صف CR مبلغه صفر وإجمالي DR > 0،
        ضع المبلغ المتبقي تلقائياً في أول صف CR فارغ.
        """
        total_dr = sum(
            ln.get_amount() for ln in self._lines if ln.get_side() == "dr"
        )
        total_cr = sum(
            ln.get_amount() for ln in self._lines if ln.get_side() == "cr"
        )
        remaining = total_dr - total_cr

        if remaining <= 0:
            return

        # أول صف CR فارغ
        for ln in self._lines:
            if ln.get_side() == "cr" and ln.get_amount() == 0:
                ln.sp_amount.blockSignals(True)
                ln.set_amount(remaining)
                ln.sp_amount.blockSignals(False)
                break

    # ══════════════════════════════════════════════════════
    # حفظ / مسح
    # ══════════════════════════════════════════════════════

    def _save(self):
        desc = self.inp_desc.text().strip()
        if not desc:
            QMessageBox.warning(self, "تنبيه", "أدخل وصف القيد")
            return

        lines = [ln.get_values() for ln in self._lines]
        lines = [l for l in lines if l]   # ازل الفارغة

        if len(lines) < 2:
            QMessageBox.warning(self, "تنبيه", "أضف صفين على الأقل بحسابات ومبالغ")
            return

        if not validate_entry_balance(lines):
            QMessageBox.warning(
                self, "خطأ في التوازن",
                "مجموع المدين ≠ مجموع الدائن\n"
                "تأكد من أن إجمالي DR = إجمالي CR"
            )
            return

        # تحقق من عدم تكرار نفس الحساب في نفس الجانب
        dr_accounts = [l["account_id"] for l in lines if l["debit"] > 0]
        cr_accounts = [l["account_id"] for l in lines if l["credit"] > 0]
        if len(dr_accounts) != len(set(dr_accounts)):
            QMessageBox.warning(self, "تنبيه", "يوجد حساب مكرر في جانب المدين")
            return
        if len(cr_accounts) != len(set(cr_accounts)):
            QMessageBox.warning(self, "تنبيه", "يوجد حساب مكرر في جانب الدائن")
            return

        entry_id = insert_entry(
            self.conn,
            self.dt_date.date().toString("yyyy-MM-dd"),
            desc,
            self.cmb_type.currentData()
        )
        add_entry_lines(self.conn, entry_id, lines)
        self._clear()
        bus.data_changed.emit()
        QMessageBox.information(self, "تم", "✅ تم حفظ القيد")

    def _clear(self):
        self._clear_lines()
        self.inp_desc.clear()
        self.dt_date.setDate(QDate.currentDate())
        self.cmb_type.setCurrentIndex(0)
        self.lbl_mode.setText("── قيد يومية جديد ──")
        self.btn_cancel.setVisible(False)
        # أعد الصفين الافتراضيين
        self._add_line("dr")
        self._add_line("cr")
        self._update_balance()


# ══════════════════════════════════════════════════════════
# تبويب القيود الكامل
# ══════════════════════════════════════════════════════════

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
        splitter.setStyleSheet("""
            QSplitter::handle { background:#e0e0e0; }
            QSplitter::handle:hover { background:#bbdefb; }
        """)

        # ── فورم القيد ──
        self._form = _JournalForm(self.conn)
        splitter.addWidget(self._form)

        # ── جدول القيود المحفوظة ──
        table_w = QWidget()
        tl = QVBoxLayout(table_w)
        tl.setContentsMargins(12, 8, 12, 12)
        tl.setSpacing(6)
        tl.addWidget(section_label("── القيود المحاسبية المحفوظة ──"))

        self.table = make_table(
            ["#", "رقم القيد", "التاريخ", "النوع", "البيان", "مدين", "دائن"],
            stretch_col=4
        )
        setup_table_columns(self.table,
            widths={0: 40, 1: 90, 2: 90, 3: 80, 5: 90, 6: 90},
            stretch_col=4
        )
        self.table.setAlternatingRowColors(True)
        tl.addWidget(self.table, stretch=1)

        btn_del = danger_button("🗑️ حذف القيد المحدد")
        btn_del.setMinimumHeight(30)
        btn_del.clicked.connect(self._delete_entry)
        tl.addLayout(buttons_row(btn_del))

        splitter.addWidget(table_w)
        splitter.setSizes([420, 300])

        root.addWidget(splitter)
        self._load_table()

    def _load_table(self):
        entries = fetch_all_entries(self.conn)
        self.table.setRowCount(0)
        type_ar = {
            "manual":     "يدوي",
            "purchase":   "شراء",
            "sale":       "بيع",
            "payment":    "دفع",
            "receipt":    "تحصيل",
            "adjustment": "تسوية",
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
            dr_item = QTableWidgetItem(f"{e['total_debit']:,.2f}")
            dr_item.setForeground(QColor("#1565c0"))
            self.table.setItem(r, 5, dr_item)
            cr_item = QTableWidgetItem(f"{e['total_credit']:,.2f}")
            cr_item.setForeground(QColor("#c62828"))
            self.table.setItem(r, 6, cr_item)

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