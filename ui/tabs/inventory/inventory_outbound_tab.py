"""
ui/tabs/inventory/inventory_outbound_tab.py
=================================
تبويب حركة الصادر (صرف / استهلاك مخزن).

يحتوي على:
  _OutboundTab — فورم الصرف + جدول آخر حركات الصادر
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox,
    QLabel, QPushButton, QDoubleSpinBox,
    QTableWidgetItem, QMessageBox,
)
from PyQt5.QtCore import Qt, QDate
from ui.widgets.panels.themed_inputs import ThemedLineEdit, ThemedComboBox, ThemedDateEdit

from services.inventory.inventory_service import InventoryService

from ui.widgets.tables.tables import auto_fit_columns
from ui.widgets.panels.form_labels   import section_title
from ui.widgets.tables.tables       import make_table

from ui.widgets.core.widget_mixin import WidgetMixin
from ui.widgets.core.events import emit_company_data_changed
from ui.widgets.core.i18n import tr
from ui.constants import (
    INVENTORY_SPIN_MAX, INVENTORY_SPIN_DEC,
    INVENTORY_INPUT_MIN_H, INVENTORY_CMB_MIN_H,
    INVENTORY_DATE_W, INVENTORY_SAVE_BTN_H,
    INVENTORY_GRP_BORDER_RADIUS, INVENTORY_GRP_MARGIN_TOP,
    INVENTORY_GRP_PAD_TOP, INVENTORY_GRP_TITLE_PAD_H,
    INVENTORY_SAVE_BTN_RADIUS, INVENTORY_SAVE_BTN_PAD_H,
    COL_MIN_WIDTH, INVENTORY_COL_MAX_W,
    FORM_LAYOUT_MARGIN, SPACING_MD_LG,
)


def _spin(max_=INVENTORY_SPIN_MAX, dec=INVENTORY_SPIN_DEC):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(INVENTORY_INPUT_MIN_H)
    return s


# ══════════════════════════════════════════════════════════
# تبويب الصادر (صرف)
# ══════════════════════════════════════════════════════════

class _OutboundTab(QWidget, WidgetMixin):
    def __init__(self, inv_conn, parent=None):
        super().__init__(parent)
        self.inv_conn = inv_conn
        self._svc = InventoryService(inv_conn)
        self._init_widget_mixin(data=True)
        self._build()
        self._refresh_style()

    def _refresh_data(self, company_id=None):
        self._reload_items()
        self._load_moves()

    def _refresh_style(self, *_):
        from ui.theme import _C
        self.grp.setStyleSheet(f"""
            QGroupBox {{ font-weight:bold; color:{_C['orange']}; border:1px solid {_C['orange_border']};
                        border-radius:{INVENTORY_GRP_BORDER_RADIUS}px; margin-top:{INVENTORY_GRP_MARGIN_TOP}px; padding-top:{INVENTORY_GRP_PAD_TOP}px; }}
            QGroupBox::title {{ subcontrol-origin:margin; padding:0 {INVENTORY_GRP_TITLE_PAD_H}px; }}
        """)
        self.lbl_available.setStyleSheet(
            f"color:{_C['accent']}; font-weight:bold;"
        )
        self.btn_save.setStyleSheet(f"""
            QPushButton {{ background:{_C['orange']}; color:{_C['bg_input']}; font-weight:bold;
                border-radius:{INVENTORY_SAVE_BTN_RADIUS}px; padding:0 {INVENTORY_SAVE_BTN_PAD_H}px; }}
            QPushButton:hover {{ background:{_C['orange_hover']}; }}
        """)
        # [إصلاح dark-mode] نفس مشكلة self.table في _InboundTab/_ReportTab.
        from ui.widgets.tables.tables import refresh_table_styles
        if hasattr(self, "table"):
            refresh_table_styles(self)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(*FORM_LAYOUT_MARGIN)
        root.setSpacing(SPACING_MD_LG)

        self.grp = QGroupBox(tr("inventory_outbound_title"))
        form = QFormLayout(self.grp)
        form.setSpacing(SPACING_MD_LG)
        form.setLabelAlignment(Qt.AlignRight)

        self.cmb_item = ThemedComboBox()
        self.cmb_item.setMinimumHeight(INVENTORY_INPUT_MIN_H)
        self._reload_items()
        self.cmb_item.currentIndexChanged.connect(self._on_item_changed)

        self.sp_qty = _spin(dec=4)
        self.sp_qty.setValue(1)

        self.lbl_available = QLabel(tr("inventory_available_none"))

        self.dt_date = ThemedDateEdit(QDate.currentDate())
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDisplayFormat("yyyy-MM-dd")
        self.dt_date.setFixedWidth(INVENTORY_DATE_W)

        self.inp_notes = ThemedLineEdit()
        self.inp_notes.setPlaceholderText(tr("inventory_purpose"))
        self.inp_notes.setMinimumHeight(INVENTORY_CMB_MIN_H)

        form.addRow(f"{tr('item')}:", self.cmb_item)
        form.addRow(f"{tr('quantity')}:", self.sp_qty)
        form.addRow(f"{tr('current_balance')}:", self.lbl_available)
        form.addRow(f"{tr('date')}:", self.dt_date)
        form.addRow(f"{tr('statement_col')}:", self.inp_notes)

        self.btn_save = QPushButton(tr("inventory_outbound_save"))
        self.btn_save.setMinimumHeight(INVENTORY_SAVE_BTN_H)
        self.btn_save.clicked.connect(self._save)
        form.addRow(self.btn_save)

        root.addWidget(self.grp)

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
        for inv in self._svc.list_items():
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
            inv = self._svc.get_item(inv_id)
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
            self._svc.record_outbound(inv_id, qty, date, notes)
            self.inp_notes.clear()
            emit_company_data_changed()
        except ValueError as e:
            QMessageBox.critical(self, tr("error"), str(e))

    def _load_moves(self):
        rows = self._svc.list_recent_moves_with_names("out", limit=100)

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
            min_width=COL_MIN_WIDTH,
            max_width=INVENTORY_COL_MAX_W,
        )
