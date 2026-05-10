"""
ui/tabs/accounting/investors_tab.py
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QSplitter, QLabel, QLineEdit, QPushButton,
    QTableWidgetItem, QMessageBox, QDateEdit,
    QDoubleSpinBox, QComboBox, QGroupBox, QFrame,
    QHeaderView,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui  import QColor

from db.investors_repo import (
    fetch_all_investors, fetch_investor,
    insert_investor, update_investor, delete_investor,
    calc_investor_summary, calc_all_investors_summary,
    link_investor_to_line,
)
from db.accounting_repo import fetch_all_entries, fetch_entry_lines
from ui.helpers import (
    make_table, setup_table_columns, buttons_row,
    section_label, danger_button, confirm_delete,
    EditModeMixin,
)
from ui.events import bus


def _spin(max_=999_999_999, dec=2):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(30)
    return s


class _InvestorForm(QWidget, EditModeMixin):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self.init_edit_mode(self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        grp = QGroupBox("بيانات المستثمر")
        grp.setStyleSheet("""
            QGroupBox { font-weight:bold; color:#2e7d32;
                border:1px solid #c8e6c9; border-radius:8px;
                margin-top:8px; padding-top:8px; }
            QGroupBox::title { subcontrol-origin:margin; padding:0 6px; }
        """)
        form = QFormLayout(grp)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = QLabel("─── مستثمر جديد ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#2e7d32;")
        form.addRow(self.lbl_mode)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم المستثمر...")
        self.inp_name.setMinimumHeight(30)

        self.dt_joined = QDateEdit(QDate.currentDate())
        self.dt_joined.setCalendarPopup(True)
        self.dt_joined.setDisplayFormat("yyyy-MM-dd")
        self.dt_joined.setFixedWidth(130)

        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("ملاحظات...")
        self.inp_notes.setMinimumHeight(28)

        form.addRow("الاسم:", self.inp_name)
        form.addRow("تاريخ الانضمام:", self.dt_joined)
        form.addRow("ملاحظات:", self.inp_notes)

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
        form.addRow(btn_w)

        root.addWidget(grp)
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
        insert_investor(self.conn, **data)
        self._reset()
        bus.data_changed.emit()

    def _save_edit(self):
        data = self._collect()
        if not data:
            return
        update_investor(self.conn, self._editing_id, **data)
        self._reset()
        bus.data_changed.emit()

    def _cancel(self):
        self._reset()

    def load_for_edit(self, investor_id: int):
        inv = fetch_investor(self.conn, investor_id)
        if not inv:
            return
        self.inp_name.setText(inv["name"])
        self.dt_joined.setDate(QDate.fromString(inv["joined_at"], "yyyy-MM-dd"))
        self.inp_notes.setText(inv["notes"] or "")
        self.enter_edit_mode(investor_id, f"─── تعديل: {inv['name']} ───")

    def _reset(self):
        self.inp_name.clear()
        self.dt_joined.setDate(QDate.currentDate())
        self.inp_notes.clear()
        self.exit_edit_mode("─── مستثمر جديد ───")


class _InvestorsTable(QWidget):
    def __init__(self, conn, form, on_select, parent=None):
        super().__init__(parent)
        self.conn       = conn
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
            ["ID", "الاسم", "تاريخ الانضمام", "رأس المال", "المسحوبات", "صافي الاستثمار"],
            stretch_col=1
        )
        setup_table_columns(self.table,
            widths={0: 40, 2: 110, 3: 100, 4: 100, 5: 120},
            stretch_col=1
        )
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self._on_selection)
        root.addWidget(self.table, stretch=1)

        btn_edit = QPushButton("✏️  تعديل")
        btn_del  = danger_button("🗑️  حذف")
        for btn in (btn_edit, btn_del):
            btn.setMinimumHeight(30)
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        root.addLayout(buttons_row(btn_edit, btn_del))

    def _selected_id(self):
        row = self.table.currentRow()
        if row == -1:
            return None
        return int(self.table.item(row, 0).text())

    def _on_selection(self):
        inv_id = self._selected_id()
        if inv_id is not None:
            self._on_select(inv_id)

    def _load(self):
        summaries = calc_all_investors_summary(self.conn, acc_conn=None)
        self.table.setRowCount(0)
        for s in summaries:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(s["investor_id"])))
            self.table.setItem(r, 1, QTableWidgetItem(s["investor_name"]))
            self.table.setItem(r, 2, QTableWidgetItem(s.get("joined_at", "—")))
            self.table.setItem(r, 3, QTableWidgetItem(f"{s['total_capital']:,.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"{s['total_drawings']:,.2f}"))
            net = s["net_investment"]
            ni = QTableWidgetItem(f"{net:,.2f}")
            ni.setForeground(QColor("#2e7d32") if net >= 0 else QColor("#c62828"))
            self.table.setItem(r, 5, ni)

    def _edit(self):
        inv_id = self._selected_id()
        if inv_id is None:
            QMessageBox.information(self, "تنبيه", "اختر مستثمراً أولاً")
            return
        self._form.load_for_edit(inv_id)

    def _delete(self):
        inv_id = self._selected_id()
        if inv_id is None:
            QMessageBox.information(self, "تنبيه", "اختر مستثمراً أولاً")
            return
        inv = fetch_investor(self.conn, inv_id)
        if inv and confirm_delete(self, inv["name"]):
            delete_investor(self.conn, inv_id)
            bus.data_changed.emit()


class _InvestorDetails(QFrame):
    def __init__(self, conn, acc_conn, parent=None):
        super().__init__(parent)
        self.conn     = conn
        self.acc_conn = acc_conn
        self._current_investor_id = None
        self.setStyleSheet("""
            QFrame { background:white; border:1px solid #c8e6c9; border-radius:8px; }
        """)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(10)

        self.lbl_title = QLabel("اختر مستثمراً لعرض تفاصيله")
        self.lbl_title.setStyleSheet(
            "font-weight:bold; color:#2e7d32; font-size:13px;"
            "background:transparent; border:none;"
        )
        self.lbl_title.setAlignment(Qt.AlignCenter)
        root.addWidget(self.lbl_title)

        cards = QHBoxLayout()

        def _card(label, color):
            f = QFrame()
            f.setStyleSheet(f"""
                QFrame {{ background:white; border-left:4px solid {color};
                         border-radius:6px; padding:4px; }}
            """)
            lay = QVBoxLayout(f)
            lay.setContentsMargins(10, 6, 10, 6)
            lt = QLabel(label)
            lt.setStyleSheet("font-size:10px; color:#888; background:transparent; border:none;")
            lv = QLabel("─")
            lv.setStyleSheet(
                f"font-size:14px; font-weight:bold; color:{color};"
                "background:transparent; border:none;"
            )
            lay.addWidget(lt)
            lay.addWidget(lv)
            cards.addWidget(f, stretch=1)
            return lv

        self.lbl_capital  = _card("رأس المال",       "#2e7d32")
        self.lbl_drawings = _card("المسحوبات",       "#c62828")
        self.lbl_net      = _card("صافي الاستثمار",  "#1565c0")
        root.addLayout(cards)

        root.addWidget(section_label("─── الحركات ───"))
        self.table = make_table(
            ["التاريخ", "رقم القيد", "البيان", "النوع", "المبلغ", "الحساب"],
            stretch_col=2
        )
        setup_table_columns(self.table,
            widths={0: 90, 1: 85, 3: 70, 4: 90, 5: 130},
            stretch_col=2
        )
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, stretch=1)

        # ربط قيد
        root.addWidget(section_label("─── ربط قيد محاسبي ───"))
        lf = QFrame()
        lf.setStyleSheet("QFrame { background:#f8fbff; border:1px solid #bbdefb; border-radius:6px; }")
        fl = QFormLayout(lf)
        fl.setSpacing(8)
        fl.setLabelAlignment(Qt.AlignRight)

        self.cmb_entry = QComboBox()
        self.cmb_entry.setMinimumHeight(28)
        self.cmb_entry.currentIndexChanged.connect(self._on_entry_changed)

        self.cmb_line = QComboBox()
        self.cmb_line.setMinimumHeight(28)

        self.cmb_move_type = QComboBox()
        self.cmb_move_type.addItem("💰 رأس مال", "capital")
        self.cmb_move_type.addItem("💸 مسحوبات", "drawings")
        self.cmb_move_type.setMinimumHeight(28)

        self.sp_amount = _spin()
        self.sp_amount.setFixedWidth(120)

        btn_link = QPushButton("🔗  ربط")
        btn_link.setMinimumHeight(30)
        btn_link.setStyleSheet(
            "QPushButton { background:#1565c0; color:white; font-weight:bold;"
            "border-radius:4px; padding:0 14px; }"
            "QPushButton:hover { background:#0d47a1; }"
        )
        btn_link.clicked.connect(self._link_entry)

        fl.addRow("القيد:", self.cmb_entry)
        fl.addRow("الصف:", self.cmb_line)
        fl.addRow("النوع:", self.cmb_move_type)
        fl.addRow("المبلغ:", self.sp_amount)
        fl.addRow(btn_link)
        root.addWidget(lf)

        self._load_entries()

    def _load_entries(self):
        self.cmb_entry.blockSignals(True)
        self.cmb_entry.clear()
        self.cmb_entry.addItem("— اختر قيداً —", None)
        try:
            for e in fetch_all_entries(self.acc_conn):
                self.cmb_entry.addItem(
                    f"{e['ref_no']}  —  {e['date']}  —  {e['description']}", e["id"]
                )
        except Exception:
            pass
        self.cmb_entry.blockSignals(False)

    def _on_entry_changed(self):
        entry_id = self.cmb_entry.currentData()
        self.cmb_line.clear()
        if not entry_id:
            return
        try:
            for line in fetch_entry_lines(self.acc_conn, entry_id):
                side = "DR" if line["debit"] > 0 else "CR"
                amt  = line["debit"] if line["debit"] > 0 else line["credit"]
                self.cmb_line.addItem(
                    f"{line['account_code']} — {line['account_name']}  [{side}: {amt:,.2f}]",
                    line["id"]
                )
                if self.cmb_line.count() == 1:
                    self.sp_amount.setValue(amt)
        except Exception:
            pass

    def _link_entry(self):
        if not self._current_investor_id:
            QMessageBox.warning(self, "تنبيه", "اختر مستثمراً أولاً")
            return
        entry_id = self.cmb_entry.currentData()
        line_id  = self.cmb_line.currentData()
        if not entry_id or not line_id:
            QMessageBox.warning(self, "تنبيه", "اختر قيداً وصفاً")
            return
        amount = self.sp_amount.value()
        if amount <= 0:
            QMessageBox.warning(self, "تنبيه", "أدخل مبلغاً صحيحاً")
            return
        try:
            link_investor_to_line(
                self.conn, self._current_investor_id,
                entry_id, line_id, self.cmb_move_type.currentData(), amount
            )
            bus.data_changed.emit()
            QMessageBox.information(self, "تم", "✅ تم ربط القيد")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def load(self, investor_id: int):
        self._current_investor_id = investor_id
        s = calc_investor_summary(self.conn, investor_id, acc_conn=self.acc_conn)
        if not s:
            return
        self.lbl_title.setText(f"👤  {s['investor_name']}  │  انضم: {s['joined_at']}")
        self.lbl_capital.setText(f"{s['total_capital']:,.2f}  ج")
        self.lbl_drawings.setText(f"{s['total_drawings']:,.2f}  ج")
        net = s["net_investment"]
        self.lbl_net.setText(f"{net:,.2f}  ج")
        color = "#2e7d32" if net >= 0 else "#c62828"
        self.lbl_net.setStyleSheet(
            f"font-size:14px; font-weight:bold; color:{color};"
            "background:transparent; border:none;"
        )
        self.table.setRowCount(0)
        type_ar    = {"capital": "💰 رأس مال", "drawings": "💸 مسحوبات"}
        type_color = {"capital": "#2e7d32",    "drawings": "#c62828"}
        for e in s.get("entries", []):
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(e.get("date", "—")))
            self.table.setItem(r, 1, QTableWidgetItem(e.get("ref_no", "—")))
            di = QTableWidgetItem(e.get("entry_desc", "—"))
            di.setToolTip(e.get("entry_desc", ""))
            self.table.setItem(r, 2, di)
            mt = e.get("move_type", "")
            mi = QTableWidgetItem(type_ar.get(mt, mt))
            mi.setForeground(QColor(type_color.get(mt, "#333")))
            self.table.setItem(r, 3, mi)
            self.table.setItem(r, 4, QTableWidgetItem(f"{e.get('amount', 0):,.2f}"))
            self.table.setItem(r, 5, QTableWidgetItem(
                f"{e.get('account_code', '')} — {e.get('account_name', '')}"
            ))
        self._load_entries()

    def clear(self):
        self._current_investor_id = None
        self.lbl_title.setText("اختر مستثمراً لعرض تفاصيله")
        self.table.setRowCount(0)
        for lbl in (self.lbl_capital, self.lbl_drawings, self.lbl_net):
            lbl.setText("─")


class InvestorsTab(QWidget):
    def __init__(self, conn, acc_conn, parent=None):
        super().__init__(parent)
        self.conn     = conn
        self.acc_conn = acc_conn
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)

        top = QSplitter(Qt.Horizontal)
        top.setHandleWidth(5)
        self._form  = _InvestorForm(self.conn)
        self._table = _InvestorsTable(self.conn, self._form, self._on_select)
        top.addWidget(self._form)
        top.addWidget(self._table)
        top.setSizes([300, 500])

        self._details = _InvestorDetails(self.conn, self.acc_conn)

        splitter.addWidget(top)
        splitter.addWidget(self._details)
        splitter.setSizes([250, 450])

        root.addWidget(splitter)

    def _on_select(self, investor_id: int):
        self._details.load(investor_id)