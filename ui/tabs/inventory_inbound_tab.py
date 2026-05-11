"""
ui/tabs/inventory_inbound_tab.py
================================
تبويب حركة الوارد (شراء / استلام مخزن) مع قيد محاسبي تلقائي.

يحتوي على:
  _safe_subtype   — دالة مساعدة لقراءة subtype بأمان
  _InboundTab     — فورم الاستلام + جدول آخر الحركات
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QDoubleSpinBox,
    QComboBox, QDateEdit, QTableWidgetItem, QMessageBox,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui  import QColor

from db.inventory_repo  import (
    fetch_all_inventory, fetch_inventory_item,
    record_inventory_move,
)
from db.accounting_repo import fetch_leaf_accounts, purchase_inventory
from ui.helpers import (
    make_table, setup_table_columns, section_label,
)
from ui.events import bus


def _spin(max_=999999999, dec=4):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(30)
    return s


def _safe_subtype(acc_row) -> str:
    """يرجع subtype بأمان من sqlite3.Row أو dict."""
    try:
        val = acc_row["subtype"]
        return val if val else ""
    except (IndexError, KeyError):
        return ""


# ══════════════════════════════════════════════════════════
# تبويب الوارد (شراء)
# ══════════════════════════════════════════════════════════

class _InboundTab(QWidget):
    def __init__(self, inv_conn, acc_conn, parent=None):
        super().__init__(parent)
        self.inv_conn = inv_conn
        self.acc_conn = acc_conn
        self._build()
        bus.data_changed.connect(self._reload_items)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(10)

        grp = QGroupBox("📥  استلام / شراء مخزن")
        grp.setStyleSheet("""
            QGroupBox { font-weight:bold; color:#2e7d32; border:1px solid #c8e6c9;
                        border-radius:8px; margin-top:8px; padding-top:8px; }
            QGroupBox::title { subcontrol-origin:margin; padding:0 6px; }
        """)
        form = QFormLayout(grp)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.cmb_item = QComboBox()
        self.cmb_item.setMinimumHeight(30)
        self.cmb_item.setMinimumWidth(220)
        self._reload_items()
        self.cmb_item.currentIndexChanged.connect(self._on_item_changed)

        self.sp_qty       = _spin(dec=4)
        self.sp_qty.setValue(1)
        self.sp_unit_cost = _spin(dec=4)

        self.lbl_total = QLabel("0.00  ج")
        self.lbl_total.setStyleSheet(
            "font-weight:bold; color:#2e7d32; font-size:14px;"
        )
        self.sp_qty.valueChanged.connect(self._update_total)
        self.sp_unit_cost.valueChanged.connect(self._update_total)

        self.dt_date = QDateEdit(QDate.currentDate())
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDisplayFormat("yyyy-MM-dd")
        self.dt_date.setFixedWidth(130)

        # حساب الدفع — الخصوم + الأصول النقدية/البنكية
        self.cmb_payment = QComboBox()
        self.cmb_payment.setMinimumHeight(28)

        for acc in fetch_leaf_accounts(self.acc_conn, "liability"):
            self.cmb_payment.addItem(f"{acc['code']} — {acc['name']}", acc["id"])

        for acc in fetch_leaf_accounts(self.acc_conn, "asset"):
            subtype = _safe_subtype(acc)
            if subtype in ("cash", "bank"):
                self.cmb_payment.addItem(f"{acc['code']} — {acc['name']}", acc["id"])

        # اختيار الموردين افتراضياً
        for i in range(self.cmb_payment.count()):
            text = self.cmb_payment.itemText(i) or ""
            if "211" in text or "مورد" in text.lower():
                self.cmb_payment.setCurrentIndex(i)
                break

        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("ملاحظات...")
        self.inp_notes.setMinimumHeight(28)

        form.addRow("الصنف:", self.cmb_item)
        form.addRow("الكمية:", self.sp_qty)
        form.addRow("سعر الوحدة:", self.sp_unit_cost)
        form.addRow("الإجمالي:", self.lbl_total)
        form.addRow("التاريخ:", self.dt_date)
        form.addRow("حساب الدفع:", self.cmb_payment)
        form.addRow("ملاحظات:", self.inp_notes)

        btn_save = QPushButton("📥  تسجيل الاستلام + قيد محاسبي")
        btn_save.setMinimumHeight(36)
        btn_save.setStyleSheet("""
            QPushButton { background:#2e7d32; color:white; font-weight:bold;
                border-radius:6px; padding:0 18px; }
            QPushButton:hover { background:#1b5e20; }
        """)
        btn_save.clicked.connect(self._save)
        form.addRow(btn_save)

        root.addWidget(grp)

        root.addWidget(section_label("─── آخر حركات الوارد ───"))
        self.table = make_table(
            ["التاريخ", "الصنف", "الكمية", "سعر الوحدة", "الإجمالي", "رقم القيد"],
            stretch_col=1
        )
        setup_table_columns(self.table,
            widths={0: 90, 2: 80, 3: 100, 4: 100, 5: 100},
            stretch_col=1
        )
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, stretch=1)

        self._load_moves()
        bus.data_changed.connect(self._load_moves)

    def _reload_items(self):
        prev = self.cmb_item.currentData() if self.cmb_item.count() else None
        self.cmb_item.blockSignals(True)
        self.cmb_item.clear()
        self.cmb_item.addItem("— اختر الصنف —", None)
        for inv in fetch_all_inventory(self.inv_conn):
            self.cmb_item.addItem(
                f"{inv['name']}  ({inv['qty_on_hand']:,.4g} {inv['unit']})",
                inv["id"]
            )
        self.cmb_item.blockSignals(False)
        if prev:
            for i in range(self.cmb_item.count()):
                if self.cmb_item.itemData(i) == prev:
                    self.cmb_item.setCurrentIndex(i)
                    break

    def _on_item_changed(self):
        inv_id = self.cmb_item.currentData()
        if inv_id:
            inv = fetch_inventory_item(self.inv_conn, inv_id)
            if inv and inv["avg_cost"] > 0:
                self.sp_unit_cost.setValue(inv["avg_cost"])
        self._update_total()

    def _update_total(self):
        total = self.sp_qty.value() * self.sp_unit_cost.value()
        self.lbl_total.setText(f"{total:,.2f}  ج")

    def _save(self):
        inv_id  = self.cmb_item.currentData()
        pay_acc = self.cmb_payment.currentData()
        if not inv_id:
            QMessageBox.warning(self, "تنبيه", "اختر الصنف أولاً")
            return
        if not pay_acc:
            QMessageBox.warning(self, "تنبيه", "اختر حساب الدفع")
            return
        qty       = self.sp_qty.value()
        unit_cost = self.sp_unit_cost.value()
        if qty <= 0 or unit_cost < 0:
            QMessageBox.warning(self, "تنبيه", "أدخل كمية وسعر صحيحين")
            return
        date  = self.dt_date.date().toString("yyyy-MM-dd")
        notes = self.inp_notes.text().strip() or None
        try:
            purchase_inventory(
                self.inv_conn, self.acc_conn,
                inv_id, qty, unit_cost, date, pay_acc, notes
            )
            self.inp_notes.clear()
            bus.data_changed.emit()
            QMessageBox.information(
                self, "تم", "✅ تم تسجيل الاستلام وإنشاء قيد محاسبي"
            )
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _load_moves(self):
        try:
            rows = self.inv_conn.execute("""
                SELECT im.date, inv.name, im.qty, im.unit_cost, im.total_cost,
                       im.ref_entry_no
                FROM inventory_moves im
                JOIN inventory_items inv ON inv.id = im.inventory_id
                WHERE im.move_type = 'in'
                ORDER BY im.date DESC, im.id DESC
                LIMIT 100
            """).fetchall()
        except Exception:
            rows = []

        self.table.setRowCount(0)
        for r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(r["date"]))
            name_item = QTableWidgetItem(r["name"])
            name_item.setToolTip(r["name"])
            self.table.setItem(row, 1, name_item)
            self.table.setItem(row, 2, QTableWidgetItem(f"{r['qty']:,.4g}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{r['unit_cost']:,.4f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{r['total_cost']:,.2f}"))
            ref = r["ref_entry_no"] if "ref_entry_no" in r.keys() else "—"
            self.table.setItem(row, 5, QTableWidgetItem(ref or "—"))
