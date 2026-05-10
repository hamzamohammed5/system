"""
ui/tabs/accounting/investors_tab.py
=====================================
تبويب المستثمرين — إدارة شاملة:

① إضافة مستثمر جديد + تسجيل مبلغ رأس المال الأولي → قيد محاسبي تلقائي
② إضافة استثمار إضافي (capital) → قيد محاسبي
③ تسجيل مسحوبات (drawings) → قيد محاسبي
④ عرض ملخص كل مستثمر (رأس المال / المسحوبات / الصافي)
⑤ في تبويب القيود: ربط capital/drawings بمستثمر معين

كل عملية تسجل:
  - قيد محاسبي في accounting.db
  - سجل في investor_entries في erp.db
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QFrame, QSplitter, QPushButton,
    QTableWidgetItem, QHeaderView, QMessageBox,
    QLineEdit, QDoubleSpinBox, QComboBox,
    QGroupBox, QTabWidget, QDateEdit,
    QDialog, QDialogButtonBox, QAbstractItemView,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui  import QColor

from db.investors_repo import (
    fetch_all_investors, fetch_investor,
    insert_investor, update_investor, delete_investor,
    link_investor_to_line, fetch_investor_entries,
    calc_investor_summary, calc_all_investors_summary,
    create_investors_tables, _migrate_investors,
)
from db.accounting_repo import (
    fetch_leaf_accounts, insert_entry, add_entry_lines,
    fetch_all_accounts,
)
from ui.helpers import (
    make_table, setup_table_columns, buttons_row,
    section_label, danger_button, confirm_delete,
    EditModeMixin,
)
from ui.events import bus


# ══════════════════════════════════════════════════════════
# مساعدات
# ══════════════════════════════════════════════════════════

def _spin(max_=999_999_999, dec=2):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(30)
    return s


def _stat_card(label: str, color: str = "#1565c0"):
    f = QFrame()
    f.setStyleSheet(f"""
        QFrame {{
            background: white;
            border-left: 4px solid {color};
            border-radius: 6px;
        }}
    """)
    lay = QVBoxLayout(f)
    lay.setContentsMargins(12, 8, 12, 8)
    lt = QLabel(label)
    lt.setStyleSheet("font-size:10px; color:#888; background:transparent; border:none;")
    lv = QLabel("0.00  ج")
    lv.setStyleSheet(
        f"font-size:15px; font-weight:bold; color:{color};"
        " background:transparent; border:none;"
    )
    lay.addWidget(lt)
    lay.addWidget(lv)
    return f, lv


def _fetch_capital_accounts(acc_conn):
    """حسابات رأس المال (capital)."""
    try:
        return acc_conn.execute("""
            SELECT id, code, name FROM accounts
            WHERE type='capital' AND is_leaf=1
            ORDER BY code
        """).fetchall()
    except Exception:
        return []


def _fetch_drawings_accounts(acc_conn):
    """حسابات المسحوبات (drawings)."""
    try:
        return acc_conn.execute("""
            SELECT id, code, name FROM accounts
            WHERE type='drawings' AND is_leaf=1
            ORDER BY code
        """).fetchall()
    except Exception:
        return []


def _fetch_asset_accounts(acc_conn):
    """حسابات الأصول النقدية/البنكية للخصم/الإيداع."""
    try:
        return acc_conn.execute("""
            SELECT id, code, name, subtype FROM accounts
            WHERE type='asset' AND is_leaf=1
            ORDER BY code
        """).fetchall()
    except Exception:
        return []


def _post_capital_entry(acc_conn, erp_conn, investor_id: int, investor_name: str,
                         capital_acc_id: int, asset_acc_id: int,
                         amount: float, date: str, notes: str = None) -> int:
    """
    يسجل قيد رأس مال:
      DR  الأصل (نقدية/بنك)
      CR  رأس المال
    ويربطه بالمستثمر.
    يرجع entry_id.
    """
    desc = f"رأس مال — {investor_name}  {amount:,.2f} ج"
    entry_id = insert_entry(acc_conn, date, desc, entry_type="manual", notes=notes)
    lines = [
        {"account_id": asset_acc_id,   "debit": amount, "credit": 0,      "description": desc},
        {"account_id": capital_acc_id, "debit": 0,      "credit": amount,  "description": desc},
    ]
    add_entry_lines(acc_conn, entry_id, lines)

    # اجيب line_id للـ CR (رأس المال)
    line_row = acc_conn.execute(
        "SELECT id FROM journal_lines WHERE entry_id=? AND credit>0", (entry_id,)
    ).fetchone()
    line_id = line_row["id"] if line_row else 0

    link_investor_to_line(
        erp_conn, investor_id, entry_id, line_id,
        move_type="capital", amount=amount, notes=notes
    )
    return entry_id


def _post_drawings_entry(acc_conn, erp_conn, investor_id: int, investor_name: str,
                          drawings_acc_id: int, asset_acc_id: int,
                          amount: float, date: str, notes: str = None) -> int:
    """
    يسجل قيد مسحوبات:
      DR  المسحوبات
      CR  الأصل (نقدية/بنك)
    يرجع entry_id.
    """
    desc = f"مسحوبات — {investor_name}  {amount:,.2f} ج"
    entry_id = insert_entry(acc_conn, date, desc, entry_type="manual", notes=notes)
    lines = [
        {"account_id": drawings_acc_id, "debit": amount, "credit": 0,     "description": desc},
        {"account_id": asset_acc_id,    "debit": 0,      "credit": amount, "description": desc},
    ]
    add_entry_lines(acc_conn, entry_id, lines)

    line_row = acc_conn.execute(
        "SELECT id FROM journal_lines WHERE entry_id=? AND debit>0", (entry_id,)
    ).fetchone()
    line_id = line_row["id"] if line_row else 0

    link_investor_to_line(
        erp_conn, investor_id, entry_id, line_id,
        move_type="drawings", amount=amount, notes=notes
    )
    return entry_id


# ══════════════════════════════════════════════════════════
# نافذة إضافة حركة (capital / drawings)
# ══════════════════════════════════════════════════════════

class _MovementDialog(QDialog):
    """
    نافذة popup لتسجيل حركة مالية لمستثمر:
      - capital   : إضافة استثمار
      - drawings  : مسحوبات
    """
    def __init__(self, acc_conn, erp_conn,
                 investor_id: int, investor_name: str,
                 move_type: str = "capital",
                 parent=None):
        super().__init__(parent)
        self.acc_conn      = acc_conn
        self.erp_conn      = erp_conn
        self.investor_id   = investor_id
        self.investor_name = investor_name
        self.move_type     = move_type  # "capital" | "drawings"

        title = "💰  إضافة رأس مال" if move_type == "capital" else "💸  تسجيل مسحوبات"
        self.setWindowTitle(title)
        self.setMinimumWidth(480)
        self.setModal(True)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(20, 16, 20, 16)

        # ── عنوان ──
        color = "#2e7d32" if self.move_type == "capital" else "#c62828"
        icon  = "💰" if self.move_type == "capital" else "💸"
        lbl_title = QLabel(
            f"{icon}  {self.investor_name}  —  "
            f"{'إضافة رأس مال' if self.move_type == 'capital' else 'مسحوبات'}"
        )
        lbl_title.setStyleSheet(
            f"font-size:13px; font-weight:bold; color:{color};"
            f"background:#{'f1f8e9' if self.move_type=='capital' else 'fdecea'};"
            "border-radius:6px; padding:8px 14px;"
        )
        root.addWidget(lbl_title)

        grp = QGroupBox()
        grp.setStyleSheet("""
            QGroupBox { border:1px solid #e0e0e0; border-radius:8px; padding-top:10px; }
        """)
        form = QFormLayout(grp)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        # المبلغ
        self.sp_amount = _spin()
        self.sp_amount.setValue(0)
        form.addRow("المبلغ (جنيه):", self.sp_amount)

        # التاريخ
        self.dt_date = QDateEdit(QDate.currentDate())
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDisplayFormat("yyyy-MM-dd")
        self.dt_date.setFixedWidth(140)
        self.dt_date.setMinimumHeight(30)
        form.addRow("التاريخ:", self.dt_date)

        # حساب رأس المال / المسحوبات
        self.cmb_equity_acc = QComboBox()
        self.cmb_equity_acc.setMinimumHeight(30)
        if self.move_type == "capital":
            for acc in _fetch_capital_accounts(self.acc_conn):
                self.cmb_equity_acc.addItem(f"{acc['code']} — {acc['name']}", acc["id"])
            form.addRow("حساب رأس المال:", self.cmb_equity_acc)
        else:
            for acc in _fetch_drawings_accounts(self.acc_conn):
                self.cmb_equity_acc.addItem(f"{acc['code']} — {acc['name']}", acc["id"])
            form.addRow("حساب المسحوبات:", self.cmb_equity_acc)

        # حساب الأصل (نقدية/بنك)
        self.cmb_asset_acc = QComboBox()
        self.cmb_asset_acc.setMinimumHeight(30)
        for acc in _fetch_asset_accounts(self.acc_conn):
            self.cmb_asset_acc.addItem(f"{acc['code']} — {acc['name']}", acc["id"])
        asset_label = "حساب الإيداع (أصل):" if self.move_type == "capital" else "حساب الصرف (أصل):"
        form.addRow(asset_label, self.cmb_asset_acc)

        # ملاحظات
        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("ملاحظات اختيارية...")
        self.inp_notes.setMinimumHeight(28)
        form.addRow("ملاحظات:", self.inp_notes)

        root.addWidget(grp)

        # أزرار
        btn_ok     = QPushButton("✅  تسجيل")
        btn_cancel = QPushButton("✖  إلغاء")
        btn_ok.setMinimumHeight(34)
        btn_cancel.setMinimumHeight(34)
        btn_ok.setStyleSheet(f"""
            QPushButton {{
                background: {color}; color: white;
                font-weight: bold; border-radius: 6px; padding: 0 20px;
            }}
            QPushButton:hover {{ opacity: 0.85; }}
        """)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: #f5f5f5; color: #555;
                border: 1px solid #ddd; border-radius: 6px; padding: 0 14px;
            }
        """)
        btn_ok.clicked.connect(self._accept)
        btn_cancel.clicked.connect(self.reject)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        root.addLayout(btn_row)

    def _accept(self):
        amount = self.sp_amount.value()
        if amount <= 0:
            QMessageBox.warning(self, "تنبيه", "أدخل مبلغاً أكبر من صفر")
            return
        equity_acc = self.cmb_equity_acc.currentData()
        asset_acc  = self.cmb_asset_acc.currentData()
        if not equity_acc or not asset_acc:
            QMessageBox.warning(self, "تنبيه", "اختر الحسابات المطلوبة")
            return

        date  = self.dt_date.date().toString("yyyy-MM-dd")
        notes = self.inp_notes.text().strip() or None

        try:
            if self.move_type == "capital":
                _post_capital_entry(
                    self.acc_conn, self.erp_conn,
                    self.investor_id, self.investor_name,
                    equity_acc, asset_acc, amount, date, notes
                )
            else:
                _post_drawings_entry(
                    self.acc_conn, self.erp_conn,
                    self.investor_id, self.investor_name,
                    equity_acc, asset_acc, amount, date, notes
                )
            bus.data_changed.emit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))


# ══════════════════════════════════════════════════════════
# فورم إضافة / تعديل مستثمر
# ══════════════════════════════════════════════════════════

class _InvestorForm(QWidget, EditModeMixin):
    def __init__(self, acc_conn, erp_conn, parent=None):
        super().__init__(parent)
        self.acc_conn = acc_conn
        self.erp_conn = erp_conn
        self._build()
        self.init_edit_mode(self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        grp = QGroupBox("بيانات المستثمر")
        grp.setStyleSheet("""
            QGroupBox { font-weight:bold; color:#1565c0; border:1px solid #e0e0e0;
                        border-radius:8px; margin-top:8px; padding-top:8px; }
            QGroupBox::title { subcontrol-origin:margin; padding:0 6px; }
        """)
        form = QFormLayout(grp)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = QLabel("─── مستثمر جديد ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0;")
        form.addRow(self.lbl_mode)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم المستثمر...")
        self.inp_name.setMinimumHeight(30)

        self.dt_joined = QDateEdit(QDate.currentDate())
        self.dt_joined.setCalendarPopup(True)
        self.dt_joined.setDisplayFormat("yyyy-MM-dd")
        self.dt_joined.setFixedWidth(140)
        self.dt_joined.setMinimumHeight(30)

        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("ملاحظات...")
        self.inp_notes.setMinimumHeight(28)

        form.addRow("الاسم:", self.inp_name)
        form.addRow("تاريخ الانضمام:", self.dt_joined)
        form.addRow("ملاحظات:", self.inp_notes)

        # ── رأس المال الأولي (عند الإضافة فقط) ──
        self._initial_frame = QFrame()
        self._initial_frame.setStyleSheet(
            "QFrame { background:#f1f8e9; border:1px solid #c8e6c9;"
            "border-radius:6px; padding:4px; }"
        )
        init_lay = QFormLayout(self._initial_frame)
        init_lay.setSpacing(8)
        init_lay.setLabelAlignment(Qt.AlignRight)

        lbl_init = QLabel("💰  رأس المال الأولي (اختياري)")
        lbl_init.setStyleSheet("font-weight:bold; color:#2e7d32; background:transparent; border:none;")
        init_lay.addRow(lbl_init)

        self.sp_initial = _spin()
        self.sp_initial.setValue(0)
        init_lay.addRow("المبلغ:", self.sp_initial)

        self.cmb_capital_acc = QComboBox()
        self.cmb_capital_acc.setMinimumHeight(28)
        for acc in _fetch_capital_accounts(self.acc_conn):
            self.cmb_capital_acc.addItem(f"{acc['code']} — {acc['name']}", acc["id"])
        init_lay.addRow("حساب رأس المال:", self.cmb_capital_acc)

        self.cmb_asset_acc = QComboBox()
        self.cmb_asset_acc.setMinimumHeight(28)
        for acc in _fetch_asset_accounts(self.acc_conn):
            self.cmb_asset_acc.addItem(f"{acc['code']} — {acc['name']}", acc["id"])
        init_lay.addRow("حساب الإيداع:", self.cmb_asset_acc)

        form.addRow(self._initial_frame)
        root.addWidget(grp)

        self.btn_add    = QPushButton("➕  إضافة مستثمر")
        self.btn_save   = QPushButton("💾  حفظ التعديل")
        self.btn_cancel = QPushButton("✖  إلغاء")
        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn.setMinimumHeight(30)
        self.btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save_edit)
        self.btn_cancel.clicked.connect(self._cancel)

        btn_w = QWidget()
        bl = QHBoxLayout(btn_w)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.addWidget(self.btn_add)
        bl.addWidget(self.btn_save)
        bl.addWidget(self.btn_cancel)
        bl.addStretch()
        root.addWidget(btn_w)
        root.addStretch()

    def _collect(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم المستثمر")
            return None
        return {
            "name":      name,
            "joined_at": self.dt_joined.date().toString("yyyy-MM-dd"),
            "notes":     self.inp_notes.text().strip() or None,
        }

    def _add(self):
        data = self._collect()
        if not data:
            return
        inv_id = insert_investor(self.erp_conn, **data)

        # رأس المال الأولي
        amount = self.sp_initial.value()
        if amount > 0:
            cap_acc   = self.cmb_capital_acc.currentData()
            asset_acc = self.cmb_asset_acc.currentData()
            if cap_acc and asset_acc:
                try:
                    _post_capital_entry(
                        self.acc_conn, self.erp_conn,
                        inv_id, data["name"],
                        cap_acc, asset_acc, amount,
                        data["joined_at"],
                        notes=f"رأس المال الأولي — {data['name']}"
                    )
                except Exception as e:
                    QMessageBox.warning(self, "تنبيه", f"تم إضافة المستثمر لكن فشل القيد:\n{e}")

        self._reset()
        bus.data_changed.emit()

    def _save_edit(self):
        data = self._collect()
        if not data:
            return
        update_investor(self.erp_conn, self._editing_id,
                        data["name"], data["notes"], data["joined_at"])
        self._reset()
        bus.data_changed.emit()

    def _cancel(self):
        self._reset()

    def load_for_edit(self, inv_id: int):
        inv = fetch_investor(self.erp_conn, inv_id)
        if not inv:
            return
        self.inp_name.setText(inv["name"])
        self.inp_notes.setText(inv["notes"] or "")
        if inv["joined_at"]:
            self.dt_joined.setDate(QDate.fromString(inv["joined_at"], "yyyy-MM-dd"))
        self._initial_frame.setVisible(False)
        self.enter_edit_mode(inv_id, f"─── تعديل: {inv['name']} ───")

    def _reset(self):
        self.inp_name.clear()
        self.inp_notes.clear()
        self.dt_joined.setDate(QDate.currentDate())
        self.sp_initial.setValue(0)
        self._initial_frame.setVisible(True)
        self.exit_edit_mode("─── مستثمر جديد ───")


# ══════════════════════════════════════════════════════════
# جدول المستثمرين
# ══════════════════════════════════════════════════════════

class _InvestorsTable(QWidget):
    def __init__(self, acc_conn, erp_conn, form: _InvestorForm,
                 on_select, parent=None):
        super().__init__(parent)
        self.acc_conn   = acc_conn
        self.erp_conn   = erp_conn
        self._form      = form
        self._on_select = on_select
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(6)
        root.addWidget(section_label("─── المستثمرون ───"))

        self.table = make_table(
            ["ID", "الاسم", "تاريخ الانضمام",
             "رأس المال", "المسحوبات", "صافي الاستثمار"],
            stretch_col=1
        )
        setup_table_columns(self.table,
            widths={0: 40, 2: 100, 3: 110, 4: 100, 5: 120},
            stretch_col=1
        )
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(
            lambda: self._on_select(self._selected_id())
        )
        root.addWidget(self.table, stretch=1)

        btn_edit    = QPushButton("✏️  تعديل")
        btn_del     = danger_button("🗑️  حذف")
        btn_capital = QPushButton("💰  إضافة استثمار")
        btn_draw    = QPushButton("💸  مسحوبات")

        btn_capital.setStyleSheet(
            "QPushButton { background:#2e7d32; color:white; border-radius:4px;"
            "padding:4px 10px; font-weight:bold; }"
            "QPushButton:hover { background:#1b5e20; }"
        )
        btn_draw.setStyleSheet(
            "QPushButton { background:#c62828; color:white; border-radius:4px;"
            "padding:4px 10px; font-weight:bold; }"
            "QPushButton:hover { background:#b71c1c; }"
        )
        for btn in (btn_edit, btn_del, btn_capital, btn_draw):
            btn.setMinimumHeight(30)

        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        btn_capital.clicked.connect(lambda: self._open_movement("capital"))
        btn_draw.clicked.connect(lambda: self._open_movement("drawings"))

        root.addLayout(buttons_row(btn_edit, btn_del, btn_capital, btn_draw))

    def _selected_id(self):
        row = self.table.currentRow()
        if row == -1:
            return None
        return int(self.table.item(row, 0).text())

    def _load(self):
        summaries = calc_all_investors_summary(self.erp_conn)
        self.table.setRowCount(0)
        for s in summaries:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(s["investor_id"])))
            self.table.setItem(r, 1, QTableWidgetItem(s["investor_name"]))
            self.table.setItem(r, 2, QTableWidgetItem(s.get("joined_at", "—")))
            self.table.setItem(r, 3, QTableWidgetItem(f"{s['total_capital']:,.2f}"))

            draw_item = QTableWidgetItem(f"{s['total_drawings']:,.2f}")
            draw_item.setForeground(QColor("#c62828"))
            self.table.setItem(r, 4, draw_item)

            net = s["net_investment"]
            net_item = QTableWidgetItem(f"{net:,.2f}")
            net_item.setForeground(
                QColor("#2e7d32") if net >= 0 else QColor("#c62828")
            )
            net_item.setFont(self.table.font())
            self.table.setItem(r, 5, net_item)

    def _edit(self):
        inv_id = self._selected_id()
        if not inv_id:
            QMessageBox.information(self, "تنبيه", "اختر مستثمراً أولاً")
            return
        self._form.load_for_edit(inv_id)

    def _delete(self):
        inv_id = self._selected_id()
        if not inv_id:
            QMessageBox.information(self, "تنبيه", "اختر مستثمراً أولاً")
            return
        inv = fetch_investor(self.erp_conn, inv_id)
        if confirm_delete(self, inv["name"]):
            delete_investor(self.erp_conn, inv_id)
            bus.data_changed.emit()

    def _open_movement(self, move_type: str):
        inv_id = self._selected_id()
        if not inv_id:
            QMessageBox.information(self, "تنبيه", "اختر مستثمراً أولاً")
            return
        inv = fetch_investor(self.erp_conn, inv_id)
        dlg = _MovementDialog(
            self.acc_conn, self.erp_conn,
            inv_id, inv["name"], move_type, parent=self
        )
        dlg.exec_()


# ══════════════════════════════════════════════════════════
# لوحة تفاصيل مستثمر واحد
# ══════════════════════════════════════════════════════════

class _InvestorDetails(QWidget):
    def __init__(self, erp_conn, parent=None):
        super().__init__(parent)
        self.erp_conn = erp_conn
        self._inv_id  = None
        self._build()
        bus.data_changed.connect(self._refresh)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(8)

        self.lbl_title = QLabel("اختر مستثمراً لعرض تفاصيله")
        self.lbl_title.setStyleSheet(
            "font-weight:bold; font-size:13px; color:#1565c0;"
            "background:#e8f4fd; border:1px solid #90caf9;"
            "border-radius:6px; padding:8px 14px;"
        )
        self.lbl_title.setAlignment(Qt.AlignCenter)
        root.addWidget(self.lbl_title)

        # ── بطاقات الملخص ──
        cards = QHBoxLayout()
        cards.setSpacing(8)
        f1, self.lbl_cap   = _stat_card("إجمالي رأس المال",     "#2e7d32")
        f2, self.lbl_draw  = _stat_card("إجمالي المسحوبات",     "#c62828")
        f3, self.lbl_net   = _stat_card("صافي الاستثمار",       "#1565c0")
        for f in (f1, f2, f3):
            cards.addWidget(f, stretch=1)
        root.addLayout(cards)

        # ── جدول الحركات ──
        root.addWidget(section_label("─── الحركات المالية ───"))
        self.table = make_table(
            ["التاريخ", "النوع", "المبلغ", "رقم القيد", "البيان"],
            stretch_col=4
        )
        setup_table_columns(self.table,
            widths={0: 90, 1: 90, 2: 110, 3: 90},
            stretch_col=4
        )
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, stretch=1)

    def load(self, inv_id: int):
        self._inv_id = inv_id
        self._refresh()

    def _refresh(self):
        if self._inv_id is None:
            return
        s = calc_investor_summary(self.erp_conn, self._inv_id)
        if not s:
            return

        self.lbl_title.setText(
            f"👤  {s['investor_name']}  │  انضم: {s.get('joined_at','—')}"
        )
        self.lbl_cap.setText(f"{s['total_capital']:,.2f}  ج")
        self.lbl_draw.setText(f"{s['total_drawings']:,.2f}  ج")

        net = s["net_investment"]
        color = "#2e7d32" if net >= 0 else "#c62828"
        self.lbl_net.setText(f"{net:,.2f}  ج")
        self.lbl_net.setStyleSheet(
            f"font-size:15px; font-weight:bold; color:{color};"
            " background:transparent; border:none;"
        )

        self.table.setRowCount(0)
        type_ar    = {"capital": "💰 رأس مال", "drawings": "💸 مسحوبات"}
        type_color = {"capital": "#2e7d32",    "drawings": "#c62828"}

        for e in s["entries"]:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(e.get("date", "—")))

            mt  = e["move_type"]
            ti  = QTableWidgetItem(type_ar.get(mt, mt))
            ti.setForeground(QColor(type_color.get(mt, "#333")))
            self.table.setItem(r, 1, ti)

            self.table.setItem(r, 2, QTableWidgetItem(f"{e['amount']:,.2f}"))
            self.table.setItem(r, 3, QTableWidgetItem(e.get("ref_no") or "—"))
            self.table.setItem(r, 4, QTableWidgetItem(
                e.get("entry_desc") or e.get("notes") or "—"
            ))

    def clear(self):
        self._inv_id = None
        self.lbl_title.setText("اختر مستثمراً لعرض تفاصيله")
        self.table.setRowCount(0)
        for lbl in (self.lbl_cap, self.lbl_draw, self.lbl_net):
            lbl.setText("─")


# ══════════════════════════════════════════════════════════
# لوحة ربط المستثمر بقيد موجود
# ══════════════════════════════════════════════════════════

class _LinkToEntryPanel(QWidget):
    """
    تتيح ربط مستثمر بقيد محاسبي موجود في accounting.db.
    يُستخدم لو القيد اتضاف يدوياً ومحتاج ينسب لمستثمر.
    """
    def __init__(self, acc_conn, erp_conn, parent=None):
        super().__init__(parent)
        self.acc_conn = acc_conn
        self.erp_conn = erp_conn
        self._build()
        bus.data_changed.connect(self._reload_investors)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(10)

        lbl_info = QLabel(
            "🔗  ربط قيد محاسبي موجود بمستثمر\n"
            "استخدم هذا لو أضفت القيد يدوياً في تبويب القيود وتريد نسبته لمستثمر."
        )
        lbl_info.setStyleSheet(
            "background:#fff3e0; border:1px solid #ffcc80; border-radius:6px;"
            "padding:10px; color:#e65100; font-size:11px;"
        )
        lbl_info.setWordWrap(True)
        root.addWidget(lbl_info)

        grp = QGroupBox("بيانات الربط")
        grp.setStyleSheet("""
            QGroupBox { border:1px solid #e0e0e0; border-radius:8px;
                        margin-top:8px; padding-top:8px; font-weight:bold; }
        """)
        form = QFormLayout(grp)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        # المستثمر
        self.cmb_investor = QComboBox()
        self.cmb_investor.setMinimumHeight(30)
        self._reload_investors()
        form.addRow("المستثمر:", self.cmb_investor)

        # نوع الحركة
        self.cmb_move = QComboBox()
        self.cmb_move.addItem("💰  رأس مال (capital)", "capital")
        self.cmb_move.addItem("💸  مسحوبات (drawings)", "drawings")
        self.cmb_move.setMinimumHeight(30)
        form.addRow("نوع الحركة:", self.cmb_move)

        # رقم القيد
        self.inp_entry_ref = QLineEdit()
        self.inp_entry_ref.setPlaceholderText("مثال: JE-00012")
        self.inp_entry_ref.setMinimumHeight(30)
        form.addRow("رقم القيد:", self.inp_entry_ref)

        # المبلغ
        self.sp_amount = _spin()
        form.addRow("المبلغ:", self.sp_amount)

        # ملاحظات
        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("ملاحظات...")
        self.inp_notes.setMinimumHeight(28)
        form.addRow("ملاحظات:", self.inp_notes)

        root.addWidget(grp)

        btn_link = QPushButton("🔗  ربط")
        btn_link.setMinimumHeight(34)
        btn_link.setStyleSheet("""
            QPushButton {
                background: #e65100; color: white;
                font-weight: bold; border-radius: 6px; padding: 0 20px;
            }
            QPushButton:hover { background: #bf360c; }
        """)
        btn_link.clicked.connect(self._link)
        root.addWidget(btn_link)
        root.addStretch()

    def _reload_investors(self):
        prev = self.cmb_investor.currentData() if self.cmb_investor.count() else None
        self.cmb_investor.blockSignals(True)
        self.cmb_investor.clear()
        for inv in fetch_all_investors(self.erp_conn):
            self.cmb_investor.addItem(inv["name"], inv["id"])
        self.cmb_investor.blockSignals(False)
        if prev:
            for i in range(self.cmb_investor.count()):
                if self.cmb_investor.itemData(i) == prev:
                    self.cmb_investor.setCurrentIndex(i)
                    break

    def _link(self):
        inv_id    = self.cmb_investor.currentData()
        move_type = self.cmb_move.currentData()
        ref_no    = self.inp_entry_ref.text().strip()
        amount    = self.sp_amount.value()

        if not inv_id:
            QMessageBox.warning(self, "تنبيه", "اختر المستثمر")
            return
        if not ref_no:
            QMessageBox.warning(self, "تنبيه", "أدخل رقم القيد")
            return
        if amount <= 0:
            QMessageBox.warning(self, "تنبيه", "أدخل مبلغاً أكبر من صفر")
            return

        # ابحث عن القيد في accounting.db
        entry_row = self.acc_conn.execute(
            "SELECT id FROM journal_entries WHERE ref_no=?", (ref_no,)
        ).fetchone()
        if not entry_row:
            QMessageBox.warning(self, "تنبيه", f"لم يُعثر على قيد برقم «{ref_no}»")
            return

        entry_id = entry_row["id"]
        # اجيب أول سطر مناسب
        if move_type == "capital":
            line_row = self.acc_conn.execute(
                "SELECT id FROM journal_lines WHERE entry_id=? AND credit>0 LIMIT 1",
                (entry_id,)
            ).fetchone()
        else:
            line_row = self.acc_conn.execute(
                "SELECT id FROM journal_lines WHERE entry_id=? AND debit>0 LIMIT 1",
                (entry_id,)
            ).fetchone()

        line_id = line_row["id"] if line_row else 0

        notes = self.inp_notes.text().strip() or None
        try:
            link_investor_to_line(
                self.erp_conn, inv_id, entry_id, line_id,
                move_type, amount, notes
            )
            self.inp_entry_ref.clear()
            self.sp_amount.setValue(0)
            self.inp_notes.clear()
            bus.data_changed.emit()
            QMessageBox.information(self, "تم", "✅ تم ربط القيد بالمستثمر بنجاح")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))


# ══════════════════════════════════════════════════════════
# التبويب الرئيسي للمستثمرين
# ══════════════════════════════════════════════════════════

class InvestorsTab(QWidget):
    def __init__(self, erp_conn, acc_conn, parent=None):
        super().__init__(parent)
        self.erp_conn = erp_conn
        self.acc_conn = acc_conn

        # تأكد من وجود الجداول
        _migrate_investors(erp_conn)

        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabBar::tab:selected { color:#1565c0; border-top:2px solid #1565c0; }
        """)

        # ── تبويب 1: إدارة المستثمرين + التفاصيل ──
        main_widget = QWidget()
        main_lay    = QVBoxLayout(main_widget)
        main_lay.setContentsMargins(0, 0, 0, 0)

        splitter_v = QSplitter(Qt.Vertical)
        splitter_v.setHandleWidth(6)

        # الجزء العلوي: فورم + جدول
        top_widget  = QWidget()
        top_lay     = QVBoxLayout(top_widget)
        top_lay.setContentsMargins(0, 0, 0, 0)

        splitter_h = QSplitter(Qt.Horizontal)
        splitter_h.setHandleWidth(6)

        self._form = _InvestorForm(self.acc_conn, self.erp_conn)
        splitter_h.addWidget(self._form)

        self._details = _InvestorDetails(self.erp_conn)
        self._table   = _InvestorsTable(
            self.acc_conn, self.erp_conn,
            self._form,
            on_select=self._on_investor_selected
        )
        splitter_h.addWidget(self._table)
        splitter_h.setSizes([300, 600])

        top_lay.addWidget(splitter_h)
        splitter_v.addWidget(top_widget)
        splitter_v.addWidget(self._details)
        splitter_v.setSizes([320, 300])

        main_lay.addWidget(splitter_v)
        tabs.addTab(main_widget, "👥  المستثمرون")

        # ── تبويب 2: ربط بقيد موجود ──
        tabs.addTab(
            _LinkToEntryPanel(self.acc_conn, self.erp_conn),
            "🔗  ربط بقيد"
        )

        root.addWidget(tabs)

    def _on_investor_selected(self, inv_id):
        if inv_id:
            self._details.load(inv_id)
        else:
            self._details.clear()