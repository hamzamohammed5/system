"""
ui/tabs/inventory_outbound_tab.py
=================================
تبويب حركة الصادر (صرف / استهلاك مخزن).

يحتوي على:
  _OutboundTab — فورم الصرف + جدول آخر حركات الصادر
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QDoubleSpinBox,
    QComboBox, QDateEdit, QTableWidgetItem, QMessageBox,
)
from PyQt5.QtCore import Qt, QDate

from db.inventory_repo import (
    fetch_all_inventory, fetch_inventory_item,
    record_inventory_move,
)
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


# ══════════════════════════════════════════════════════════
# تبويب الصادر (صرف)
# ══════════════════════════════════════════════════════════

class _OutboundTab(QWidget):
    def __init__(self, inv_conn, parent=None):
        super().__init__(parent)
        self.inv_conn = inv_conn
        self._build()
        bus.data_changed.connect(self._reload_items)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(10)

        grp = QGroupBox("📤  صرف / استهلاك مخزن")
        grp.setStyleSheet("""
            QGroupBox { font-weight:bold; color:#e65100; border:1px solid #ffe0b2;
                        border-radius:8px; margin-top:8px; padding-top:8px; }
            QGroupBox::title { subcontrol-origin:margin; padding:0 6px; }
        """)
        form = QFormLayout(grp)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.cmb_item = QComboBox()
        self.cmb_item.setMinimumHeight(30)
        self._reload_items()
        self.cmb_item.currentIndexChanged.connect(self._on_item_changed)

        self.sp_qty = _spin(dec=4)
        self.sp_qty.setValue(1)

        self.lbl_available = QLabel("الرصيد: —")
        self.lbl_available.setStyleSheet(
            "color:#1565c0; font-weight:bold;"
        )

        self.dt_date = QDateEdit(QDate.currentDate())
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDisplayFormat("yyyy-MM-dd")
        self.dt_date.setFixedWidth(130)

        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("الغرض من الصرف...")
        self.inp_notes.setMinimumHeight(28)

        form.addRow("الصنف:", self.cmb_item)
        form.addRow("الكمية:", self.sp_qty)
        form.addRow("الرصيد الحالي:", self.lbl_available)
        form.addRow("التاريخ:", self.dt_date)
        form.addRow("البيان:", self.inp_notes)

        btn_save = QPushButton("📤  تسجيل الصرف")
        btn_save.setMinimumHeight(36)
        btn_save.setStyleSheet("""
            QPushButton { background:#e65100; color:white; font-weight:bold;
                border-radius:6px; padding:0 18px; }
            QPushButton:hover { background:#bf360c; }
        """)
        btn_save.clicked.connect(self._save)
        form.addRow(btn_save)

        root.addWidget(grp)

        root.addWidget(section_label("─── آخر حركات الصادر ───"))
        self.table = make_table(
            ["التاريخ", "الصنف", "الكمية", "متوسط التكلفة",
             "إجمالي القيمة", "البيان"],
            stretch_col=1
        )
        setup_table_columns(self.table,
            widths={0: 90, 2: 80, 3: 110, 4: 110, 5: 150},
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
            if inv:
                self.lbl_available.setText(
                    f"الرصيد: {inv['qty_on_hand']:,.4g} {inv['unit']}"
                )
        else:
            self.lbl_available.setText("الرصيد: —")

    def _save(self):
        inv_id = self.cmb_item.currentData()
        if not inv_id:
            QMessageBox.warning(self, "تنبيه", "اختر الصنف أولاً")
            return
        qty   = self.sp_qty.value()
        date  = self.dt_date.date().toString("yyyy-MM-dd")
        notes = self.inp_notes.text().strip() or None
        try:
            record_inventory_move(
                self.inv_conn, inv_id, "out", qty, 0, date, notes
            )
            self.inp_notes.clear()
            bus.data_changed.emit()
        except ValueError as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _load_moves(self):
        try:
            rows = self.inv_conn.execute("""
                SELECT im.date, inv.name, im.qty, im.unit_cost,
                       im.total_cost, im.notes
                FROM inventory_moves im
                JOIN inventory_items inv ON inv.id = im.inventory_id
                WHERE im.move_type = 'out'
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
            notes_item = QTableWidgetItem(r["notes"] or "—")
            notes_item.setToolTip(r["notes"] or "")
            self.table.setItem(row, 5, notes_item)
