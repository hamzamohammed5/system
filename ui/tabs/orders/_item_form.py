"""
ui/tabs/orders/_item_form.py
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QDoubleSpinBox, QMessageBox,
)
from PyQt5.QtCore import Qt

from db.orders.orders_repo import fetch_order_items, insert_order_item, update_order_item
from ui.widgets.components.button import make_btn
from ui.widgets.theme.input_styles import input_style
from ui.widgets.core.i18n import tr
from ui.theme import _C
from ui.font import FS_BASE


def _spin(min_=0, max_=9999999, dec=2, suffix=""):
    s = QDoubleSpinBox()
    s.setRange(min_, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(34)
    if suffix:
        s.setSuffix(f" {suffix}")
    return s


class _ItemForm(QDialog):
    def __init__(self, conn, order_id: int, item_id: int = None, parent=None):
        super().__init__(parent)
        self.conn     = conn
        self.order_id = order_id
        self.item_id  = item_id

        self.setWindowTitle(tr("item_edit_title") if item_id else tr("item_add_title"))
        self.setMinimumWidth(480)
        self.setModal(True)
        self.setStyleSheet(input_style())
        self._build()
        if item_id:
            self._load()

        self.sp_qty.valueChanged.connect(self._update_total)
        self.sp_price.valueChanged.connect(self._update_total)
        self.sp_discount.valueChanged.connect(self._update_total)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        hdr = QLabel(tr("item_add_title") if not self.item_id else tr("item_edit_title"))
        hdr.setStyleSheet(f"""
            font-size: {FS_BASE + 1}px; font-weight: bold; color: {_C['accent_text']};
            background: {_C['accent_light']};
            border-radius: 8px; padding: 8px 14px;
        """)
        root.addWidget(hdr)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText(tr("product_name_placeholder"))
        form.addRow(tr("item_name_lbl"), self.inp_name)

        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText(tr("description"))
        form.addRow(tr("item_desc_lbl"), self.inp_desc)

        self.sp_qty = _spin(min_=0.001, max_=99999, dec=3)
        self.sp_qty.setValue(1)
        form.addRow(tr("item_qty_lbl"), self.sp_qty)

        self.inp_unit = QLineEdit()
        self.inp_unit.setText(tr("order_unit_default"))
        self.inp_unit.setPlaceholderText(tr("order_unit_default"))
        form.addRow(tr("order_unit_label"), self.inp_unit)

        self.sp_price = _spin(max_=9999999, dec=2, suffix=tr("currency_sym"))
        form.addRow(tr("item_unit_price"), self.sp_price)

        self.sp_discount = _spin(max_=100, dec=2, suffix="%")
        form.addRow(tr("item_discount_lbl"), self.sp_discount)

        self.lbl_total = QLabel(f"0.00 {tr('currency_sym')}")
        self.lbl_total.setStyleSheet(f"""
            font-size: {FS_BASE + 2}px; font-weight: bold; color: {_C['accent_text']};
            background: {_C['accent_light']};
            border: 1px solid {_C['accent_mid']};
            border-radius: 6px; padding: 6px 12px;
        """)
        form.addRow(tr("item_total_lbl"), self.lbl_total)

        self.inp_design_ref = QLineEdit()
        self.inp_design_ref.setPlaceholderText(tr("item_design_ref_lbl"))
        form.addRow(tr("item_design_ref_lbl"), self.inp_design_ref)

        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText(tr("notes"))
        form.addRow(tr("item_notes_lbl"), self.inp_notes)

        root.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = make_btn(tr("cancel"), "ghost")
        btn_cancel.clicked.connect(self.reject)
        btn_save = make_btn(tr("item_save_btn"), "primary")
        btn_save.setMinimumHeight(36)
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save, stretch=1)
        root.addLayout(btn_row)

    def _update_total(self):
        qty      = self.sp_qty.value()
        price    = self.sp_price.value()
        discount = self.sp_discount.value()
        total    = qty * price * (1 - discount / 100)
        self.lbl_total.setText(f"{total:,.2f} {tr('currency_sym')}")

    def _load(self):
        items = fetch_order_items(self.conn, self.order_id)
        item  = next((i for i in items if i["id"] == self.item_id), None)
        if not item:
            return
        self.inp_name.setText(item["item_name"])
        self.inp_desc.setText(item["description"] or "")
        self.sp_qty.setValue(item["quantity"])
        self.inp_unit.setText(item["unit"])
        self.sp_price.setValue(item["unit_price"])
        self.sp_discount.setValue(item["discount_pct"])
        self.inp_design_ref.setText(item["design_ref"] or "")
        self.inp_notes.setText(item["notes"] or "")
        self._update_total()

    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, tr("warning"), tr("item_name_warn"))
            self.inp_name.setFocus()
            return

        qty      = self.sp_qty.value()
        unit     = self.inp_unit.text().strip() or tr("order_unit_default")
        price    = self.sp_price.value()
        discount = self.sp_discount.value()
        desc     = self.inp_desc.text().strip()
        ref      = self.inp_design_ref.text().strip()
        notes    = self.inp_notes.text().strip()

        if self.item_id:
            update_order_item(
                self.conn, self.item_id,
                item_name=name, description=desc,
                quantity=qty, unit=unit,
                unit_price=price, discount_pct=discount,
                design_ref=ref, notes=notes,
            )
        else:
            insert_order_item(
                self.conn, self.order_id,
                item_name=name, description=desc,
                quantity=qty, unit=unit,
                unit_price=price, discount_pct=discount,
                design_ref=ref, notes=notes,
            )
        self.accept()
