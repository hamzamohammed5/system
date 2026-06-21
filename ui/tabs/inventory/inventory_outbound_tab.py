"""
ui/tabs/inventory/inventory_outbound_tab.py
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

from db.inventory.inventory_repo import (
    fetch_all_inventory, fetch_inventory_item,
    record_inventory_move,
)

from ui.widgets.tables.tables import auto_fit_columns
from ui.widgets.panels.form_labels   import section_title
from ui.widgets.tables.tables       import make_table

from ui.widgets.mixins.bus import BusConnectedMixin
from ui.widgets.core.events import emit_company_data_changed
from ui.widgets.core.i18n import tr
from ui.theme import _C


def _spin(max_=999999999, dec=4):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(30)
    return s


# ══════════════════════════════════════════════════════════
# تبويب الصادر (صرف)
# ══════════════════════════════════════════════════════════

class _OutboundTab(QWidget, BusConnectedMixin):
    def __init__(self, inv_conn, parent=None):
        super().__init__(parent)
        self.inv_conn = inv_conn
        self._build()
        self._connect_bus(data=True)

    def _on_data_changed(self):
        self._reload_items()
        self._load_moves()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(10)

        grp = QGroupBox(tr("inventory_outbound_title"))
        grp.setStyleSheet(f"""
            QGroupBox {{ font-weight:bold; color:{_C['orange']}; border:1px solid {_C['orange_border']};
                        border-radius:8px; margin-top:8px; padding-top:8px; }}
            QGroupBox::title {{ subcontrol-origin:margin; padding:0 6px; }}
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

        self.lbl_available = QLabel(tr("inventory_available_none"))
        self.lbl_available.setStyleSheet(
            f"color:{_C['accent']}; font-weight:bold;"
        )

        self.dt_date = QDateEdit(QDate.currentDate())
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDisplayFormat("yyyy-MM-dd")
        self.dt_date.setFixedWidth(130)

        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText(tr("inventory_purpose"))
        self.inp_notes.setMinimumHeight(28)

        form.addRow(f"{tr('item')}:", self.cmb_item)
        form.addRow(f"{tr('quantity')}:", self.sp_qty)
        form.addRow(f"{tr('current_balance')}:", self.lbl_available)
        form.addRow(f"{tr('date')}:", self.dt_date)
        form.addRow(f"{tr('statement_col')}:", self.inp_notes)

        btn_save = QPushButton(f"📤  {tr('inventory_outbound_save')}")
        btn_save.setMinimumHeight(36)
        btn_save.setStyleSheet(f"""
            QPushButton {{ background:{_C['orange']}; color:{_C['bg_input']}; font-weight:bold;
                border-radius:6px; padding:0 18px; }}
            QPushButton:hover {{ background:{_C['orange_hover']}; }}
        """)
        btn_save.clicked.connect(self._save)
        form.addRow(btn_save)

        root.addWidget(grp)

        root.addWidget(section_title(tr("inventory_recent_outbound")))
        self.table = make_table(
            [tr("date"), tr("item"), tr("quantity"), tr("avg_cost"),
             tr("total_value"), tr("statement_col")],
            stretch_col=1
        )
        
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, stretch=1)

        self._load_moves()

    def _reload_items(self):
        prev = self.cmb_item.currentData() if self.cmb_item.count() else None
        self.cmb_item.blockSignals(True)
        self.cmb_item.clear()
        self.cmb_item.addItem(tr("inventory_select_item_placeholder"), None)
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
                    tr("inventory_available_qty").format(qty=f"{inv['qty_on_hand']:,.4g}", unit=inv["unit"])
                )
        else:
            self.lbl_available.setText(tr("inventory_available_none"))

    def _save(self):
        inv_id = self.cmb_item.currentData()
        if not inv_id:
            QMessageBox.warning(self, tr("warning"), tr("inventory_select_item"))
            return
        qty   = self.sp_qty.value()
        date  = self.dt_date.date().toString("yyyy-MM-dd")
        notes = self.inp_notes.text().strip() or None
        try:
            record_inventory_move(
                self.inv_conn, inv_id, "out", qty, 0, date, notes
            )
            self.inp_notes.clear()
            emit_company_data_changed()
        except ValueError as e:
            QMessageBox.critical(self, tr("error"), str(e))

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
            notes_item = QTableWidgetItem(r["notes"] or tr("dash"))
            notes_item.setToolTip(r["notes"] or "")
            self.table.setItem(row, 5, notes_item)
        auto_fit_columns(
            self.table,
            fixed_cols=[0, 2, 3, 4],
            stretch_col=1,
            min_width=40,
            max_width=150,
        )
        
    def closeEvent(self, event):
        self._disconnect_bus()
        super().closeEvent(event)
