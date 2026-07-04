"""
ui/tabs/inventory/items/_item_form.py
======================================
_ItemForm — فورم إضافة / تعديل صنف مخزن.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QPushButton, QDoubleSpinBox, QComboBox, QMessageBox,
    QLabel,
)
from PyQt5.QtCore import Qt

from db.inventory.inventory_repo import (
    fetch_inventory_item, insert_inventory_item, update_inventory_item,
)
from db.accounting.accounting_accounts_repo import fetch_leaf_accounts
from db.shared.items_repo import fetch_items_by_type
from db.companies.company_state import company_state
from ui.widgets.mixins.form_mixins import EditModeMixin
from ui.widgets.core.events import emit_company_data_changed
from ui.widgets.core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import (
    INVENTORY_SPIN_MAX, INVENTORY_SPIN_DEC,
    INVENTORY_INPUT_MIN_H, INVENTORY_CMB_MIN_H, INVENTORY_UNIT_W,
    INVENTORY_GRP_BORDER_RADIUS, INVENTORY_GRP_MARGIN_TOP,
    INVENTORY_GRP_PAD_TOP, INVENTORY_GRP_TITLE_PAD_H,
    FORM_LAYOUT_SPACING,
)


def _spin(max_=INVENTORY_SPIN_MAX, dec=INVENTORY_SPIN_DEC):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(INVENTORY_INPUT_MIN_H)
    return s


class _ItemForm(QWidget, EditModeMixin, WidgetMixin):
    def __init__(self, inv_conn, acc_conn, parent=None):
        super().__init__(parent)
        self.inv_conn = inv_conn
        self.acc_conn = acc_conn
        self._init_widget_mixin(data=False)
        self._build()
        self._refresh_style()
        self.init_edit_mode(self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode)

    def _refresh_style(self, *_):
        from ui.theme import _C
        self.grp.setStyleSheet(f"""
            QGroupBox {{ font-weight:bold; color:{_C['accent']}; border:1px solid {_C['border']};
                        border-radius:{INVENTORY_GRP_BORDER_RADIUS}px; margin-top:{INVENTORY_GRP_MARGIN_TOP}px; padding-top:{INVENTORY_GRP_PAD_TOP}px; }}
            QGroupBox::title {{ subcontrol-origin:margin; padding:0 {INVENTORY_GRP_TITLE_PAD_H}px; }}
        """)
        self.lbl_mode.setStyleSheet(f"font-weight:bold; color:{_C['accent']};")

    def _refresh_lang(self, *_):
        self.grp.setTitle(tr("inventory_item_data_group"))
        self.lbl_mode.setText(tr("inventory_item_new_mode"))
        self.inp_name.setPlaceholderText(tr("inventory_item_name_placeholder"))
        self.inp_unit.setPlaceholderText(tr("inventory_unit_placeholder"))
        self.sp_qty_min.setToolTip(tr("inventory_qty_min_tooltip"))
        self.inp_notes.setPlaceholderText(tr("notes_placeholder"))
        self.btn_add.setText(tr("inventory_add_item"))
        self.btn_save.setText(tr("save_edit"))
        self.btn_cancel.setText(tr("cancel"))

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        self.grp = QGroupBox(tr("inventory_item_data_group"))
        form = QFormLayout(self.grp)
        form.setSpacing(FORM_LAYOUT_SPACING)
        form.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = QLabel(tr("inventory_item_new_mode"))
        form.addRow(self.lbl_mode)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText(tr("inventory_item_name_placeholder"))
        self.inp_name.setMinimumHeight(INVENTORY_INPUT_MIN_H)

        self.inp_unit = QLineEdit()
        self.inp_unit.setPlaceholderText(tr("inventory_unit_placeholder"))
        self.inp_unit.setMinimumHeight(INVENTORY_INPUT_MIN_H)
        self.inp_unit.setText(tr("piece"))
        self.inp_unit.setFixedWidth(INVENTORY_UNIT_W)

        self.sp_qty_min = _spin(dec=2)
        self.sp_qty_min.setFixedWidth(INVENTORY_UNIT_W)
        self.sp_qty_min.setToolTip(tr("inventory_qty_min_tooltip"))

        # ربط بصنف من items (اختياري)
        self.cmb_item = QComboBox()
        self.cmb_item.setMinimumHeight(INVENTORY_CMB_MIN_H)
        self.cmb_item.addItem(tr("investor_no_link"), None)
        for item in fetch_items_by_type(company_state.get_erp_conn(), "raw"):
            self.cmb_item.addItem(tr("inventory_raw_item_fmt").format(name=item["name"]), item["id"])

        # ربط بحساب محاسبي
        self.cmb_account = QComboBox()
        self.cmb_account.setMinimumHeight(INVENTORY_CMB_MIN_H)
        self.cmb_account.addItem(tr("inventory_default_account_placeholder"), None)
        for acc in fetch_leaf_accounts(self.acc_conn, "asset"):
            self.cmb_account.addItem(f"{acc['code']} — {acc['name']}", acc["id"])

        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText(tr("notes_placeholder"))
        self.inp_notes.setMinimumHeight(INVENTORY_CMB_MIN_H)

        form.addRow(f"{tr('inventory_item_name')}:", self.inp_name)
        form.addRow(f"{tr('unit')}:", self.inp_unit)
        form.addRow(f"{tr('inventory_min_qty_label')}:", self.sp_qty_min)
        form.addRow(f"{tr('inventory_link_raw')}:", self.cmb_item)
        form.addRow(f"{tr('inventory_acc_account')}:", self.cmb_account)
        form.addRow(f"{tr('notes')}:", self.inp_notes)

        self.btn_add    = QPushButton(tr("inventory_add_item"))
        self.btn_save   = QPushButton(tr("save_edit"))
        self.btn_cancel = QPushButton(tr("cancel"))
        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn.setMinimumHeight(INVENTORY_INPUT_MIN_H)
        self.btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save_edit)
        self.btn_cancel.clicked.connect(self._cancel)
        form.addRow(self._make_btn_widget())

        root.addWidget(self.grp)
        root.addStretch()

    def _make_btn_widget(self):
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.btn_add)
        lay.addWidget(self.btn_save)
        lay.addWidget(self.btn_cancel)
        lay.addStretch()
        return w

    def _collect(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, tr("warning"), tr("enter_field").format(label=tr("inventory_item_name")))
            return None
        return {
            "name":       name,
            "unit":       self.inp_unit.text().strip() or tr("piece"),
            "qty_min":    self.sp_qty_min.value(),
            "account_id": self.cmb_account.currentData(),
            "item_id":    self.cmb_item.currentData(),
            "notes":      self.inp_notes.text().strip() or None,
        }

    def _add(self):
        data = self._collect()
        if not data:
            return
        insert_inventory_item(self.inv_conn, **data)
        self._reset()
        emit_company_data_changed()

    def _save_edit(self):
        data = self._collect()
        if not data:
            return
        update_inventory_item(self.inv_conn, self._editing_id,
                              data["name"], data["unit"],
                              data["qty_min"], data["account_id"],
                              data["notes"])
        self._reset()
        emit_company_data_changed()

    def _cancel(self):
        self._reset()

    def load_for_edit(self, inv_id: int):
        inv = fetch_inventory_item(self.inv_conn, inv_id)
        if not inv:
            return
        self.inp_name.setText(inv["name"])
        self.inp_unit.setText(inv["unit"])
        self.sp_qty_min.setValue(inv["qty_min"])
        for i in range(self.cmb_account.count()):
            if self.cmb_account.itemData(i) == inv["account_id"]:
                self.cmb_account.setCurrentIndex(i)
                break
        self.inp_notes.setText(inv["notes"] or "")
        self.enter_edit_mode(inv_id, tr("edit_mode_fmt").format(name=inv["name"]))

    def _reset(self):
        self.inp_name.clear()
        self.inp_unit.setText(tr("piece"))
        self.sp_qty_min.setValue(0)
        self.cmb_account.setCurrentIndex(0)
        self.cmb_item.setCurrentIndex(0)
        self.inp_notes.clear()
        self.exit_edit_mode(tr("inventory_item_new_mode"))
