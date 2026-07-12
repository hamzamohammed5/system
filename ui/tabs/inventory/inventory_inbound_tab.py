"""
ui/tabs/inventory/inventory_inbound_tab.py
================================
تبويب حركة الوارد (شراء / استلام مخزن) مع قيد محاسبي تلقائي.

يحتوي على:
  _safe_subtype   — دالة مساعدة لقراءة subtype بأمان
  _InboundTab     — فورم الاستلام + جدول آخر الحركات
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox,
    QLabel, QPushButton, QDoubleSpinBox,
    QDateEdit, QTableWidgetItem, QMessageBox,
)
from ui.widgets.panels.themed_inputs import ThemedLineEdit, ThemedComboBox

from PyQt5.QtCore import Qt, QDate

from services.accounting.inventory_posting_service import InventoryPostingService
from services.inventory.inventory_service import InventoryService

from ui.widgets.tables.tables import auto_fit_columns
from ui.widgets.panels.form_labels   import section_title
from ui.widgets.tables.tables       import make_table

from ui.widgets.core.widget_mixin import WidgetMixin
from ui.widgets.core.events import emit_company_data_changed
from ui.widgets.core.i18n import tr
from ui.font import FS_LG
from ui.constants import (
    INVENTORY_SPIN_MAX, INVENTORY_SPIN_DEC,
    INVENTORY_INPUT_MIN_H, INVENTORY_CMB_MIN_H,
    INVENTORY_DATE_W, INVENTORY_SAVE_BTN_H, INVENTORY_ITEM_MIN_W,
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

class _InboundTab(QWidget, WidgetMixin):
    def __init__(self, inv_conn, acc_conn, parent=None):
        super().__init__(parent)
        self.inv_conn = inv_conn
        self.acc_conn = acc_conn
        self._svc = InventoryService(inv_conn, acc_conn=acc_conn)
        self._posting_svc = InventoryPostingService(inv_conn, acc_conn)
        self._init_widget_mixin(data=True)
        self._build()
        self._refresh_style()

    def _refresh_data(self, company_id=None):
        self._reload_items()
        self._load_moves()

    def _refresh_style(self, *_):
        from ui.theme import _C
        self.grp.setStyleSheet(f"""
            QGroupBox {{ font-weight:bold; color:{_C['success']}; border:1px solid {_C['success_border']};
                        border-radius:{INVENTORY_GRP_BORDER_RADIUS}px; margin-top:{INVENTORY_GRP_MARGIN_TOP}px; padding-top:{INVENTORY_GRP_PAD_TOP}px; }}
            QGroupBox::title {{ subcontrol-origin:margin; padding:0 {INVENTORY_GRP_TITLE_PAD_H}px; }}
        """)
        self.lbl_total.setStyleSheet(
            f"font-weight:bold; color:{_C['success']}; font-size:{FS_LG}px;"
        )
        self.btn_save.setStyleSheet(f"""
            QPushButton {{ background:{_C['success']}; color:{_C['bg_input']}; font-weight:bold;
                border-radius:{INVENTORY_SAVE_BTN_RADIUS}px; padding:0 {INVENTORY_SAVE_BTN_PAD_H}px; }}
            QPushButton:hover {{ background:{_C['success_hover']}; }}
        """)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(*FORM_LAYOUT_MARGIN)
        root.setSpacing(SPACING_MD_LG)

        self.grp = QGroupBox(tr("inventory_inbound_title"))
        form = QFormLayout(self.grp)
        form.setSpacing(SPACING_MD_LG)
        form.setLabelAlignment(Qt.AlignRight)

        self.cmb_item = ThemedComboBox()
        self.cmb_item.setMinimumHeight(INVENTORY_INPUT_MIN_H)
        self.cmb_item.setMinimumWidth(INVENTORY_ITEM_MIN_W)
        self._reload_items()
        self.cmb_item.currentIndexChanged.connect(self._on_item_changed)

        self.sp_qty       = _spin(dec=4)
        self.sp_qty.setValue(1)
        self.sp_unit_cost = _spin(dec=4)

        self.lbl_total = QLabel(f"0.00  {tr('currency_abbr')}")
        self.sp_qty.valueChanged.connect(self._update_total)
        self.sp_unit_cost.valueChanged.connect(self._update_total)

        self.dt_date = QDateEdit(QDate.currentDate())
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDisplayFormat("yyyy-MM-dd")
        self.dt_date.setFixedWidth(INVENTORY_DATE_W)

        # حساب الدفع — الخصوم + الأصول النقدية/البنكية
        self.cmb_payment = ThemedComboBox()
        self.cmb_payment.setMinimumHeight(INVENTORY_CMB_MIN_H)

        for acc in self._svc.list_payment_accounts("liability"):
            self.cmb_payment.addItem(f"{acc['code']}{tr('account_code_name_sep')}{acc['name']}", acc["id"])

        for acc in self._svc.list_payment_accounts("asset"):
            subtype = _safe_subtype(acc)
            if subtype in ("cash", "bank"):
                self.cmb_payment.addItem(f"{acc['code']}{tr('account_code_name_sep')}{acc['name']}", acc["id"])

        # اختيار الموردين افتراضياً
        supplier_kw = tr("inventory_supplier_keyword").lower()
        for i in range(self.cmb_payment.count()):
            text = self.cmb_payment.itemText(i) or ""
            if "211" in text or supplier_kw in text.lower():
                self.cmb_payment.setCurrentIndex(i)
                break

        self.inp_notes = ThemedLineEdit()
        self.inp_notes.setPlaceholderText(tr("notes_placeholder"))
        self.inp_notes.setMinimumHeight(INVENTORY_CMB_MIN_H)

        form.addRow(f"{tr('item')}:", self.cmb_item)
        form.addRow(f"{tr('quantity')}:", self.sp_qty)
        form.addRow(f"{tr('unit_price')}:", self.sp_unit_cost)
        form.addRow(f"{tr('total')}:", self.lbl_total)
        form.addRow(f"{tr('date')}:", self.dt_date)
        form.addRow(f"{tr('inventory_payment_account')}:", self.cmb_payment)
        form.addRow(f"{tr('notes')}:", self.inp_notes)

        self.btn_save = QPushButton(tr("inventory_inbound_save"))
        self.btn_save.setMinimumHeight(INVENTORY_SAVE_BTN_H)
        self.btn_save.clicked.connect(self._save)
        form.addRow(self.btn_save)

        root.addWidget(self.grp)

        root.addWidget(section_title(tr("inventory_recent_inbound")))
        self.table = make_table(
            [tr("date"), tr("item"), tr("quantity"), tr("unit_price"), tr("total"), tr("entry_no_col")],
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
            if inv and inv["avg_cost"] > 0:
                self.sp_unit_cost.setValue(inv["avg_cost"])
        self._update_total()

    def _update_total(self):
        total = self.sp_qty.value() * self.sp_unit_cost.value()
        self.lbl_total.setText(f"{total:,.2f}  {tr('currency_abbr')}")

    def _save(self):
        inv_id  = self.cmb_item.currentData()
        pay_acc = self.cmb_payment.currentData()
        if not inv_id:
            QMessageBox.warning(self, tr("warning"), tr("inventory_select_item"))
            return
        if not pay_acc:
            QMessageBox.warning(self, tr("warning"), tr("inventory_select_payment"))
            return
        qty       = self.sp_qty.value()
        unit_cost = self.sp_unit_cost.value()
        if qty <= 0 or unit_cost < 0:
            QMessageBox.warning(self, tr("warning"), tr("inventory_valid_qty_cost"))
            return
        date  = self.dt_date.date().toString("yyyy-MM-dd")
        notes = self.inp_notes.text().strip() or None
        try:
            self._posting_svc.purchase(
                inv_id, qty, unit_cost, date, pay_acc, notes
            )
            self.inp_notes.clear()
            emit_company_data_changed()
            QMessageBox.information(
                self, tr("done"), tr("inventory_purchase_success")
            )
        except Exception as e:
            QMessageBox.critical(self, tr("error"), str(e))

    def _load_moves(self):
        rows = self._svc.list_recent_moves_with_names("in", limit=100)
        
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
            ref = r["ref_entry_no"] if "ref_entry_no" in r.keys() else tr("dash")
            self.table.setItem(row, 5, QTableWidgetItem(ref or tr("dash")))
            
        auto_fit_columns(
            self.table,
            fixed_cols=[0, 2, 3, 4, 5],
            stretch_col=1,
            min_width=COL_MIN_WIDTH,
            max_width=INVENTORY_COL_MAX_W,
        )
