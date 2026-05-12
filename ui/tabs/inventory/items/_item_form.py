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

from db.connection      import get_connection
from db.inventory_repo  import fetch_inventory_item, insert_inventory_item, update_inventory_item
from db.accounting_repo import fetch_leaf_accounts
from db.items_repo      import fetch_items_by_type
from ui.helpers import EditModeMixin
from ui.events  import bus


def _spin(max_=999999999, dec=4):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(30)
    return s


class _ItemForm(QWidget, EditModeMixin):
    def __init__(self, inv_conn, acc_conn, parent=None):
        super().__init__(parent)
        self.inv_conn = inv_conn
        self.acc_conn = acc_conn
        self._build()
        self.init_edit_mode(self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        grp = QGroupBox("بيانات الصنف")
        grp.setStyleSheet("""
            QGroupBox { font-weight:bold; color:#1565c0; border:1px solid #e0e0e0;
                        border-radius:8px; margin-top:8px; padding-top:8px; }
            QGroupBox::title { subcontrol-origin:margin; padding:0 6px; }
        """)
        form = QFormLayout(grp)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = QLabel("─── صنف جديد ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0;")
        form.addRow(self.lbl_mode)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم الصنف...")
        self.inp_name.setMinimumHeight(30)

        self.inp_unit = QLineEdit()
        self.inp_unit.setPlaceholderText("قطعة / متر / كيلو...")
        self.inp_unit.setMinimumHeight(30)
        self.inp_unit.setText("قطعة")
        self.inp_unit.setFixedWidth(120)

        self.sp_qty_min = _spin(dec=2)
        self.sp_qty_min.setFixedWidth(120)
        self.sp_qty_min.setToolTip("الكمية الدنيا للتنبيه بالطلب")

        # ربط بصنف من items (اختياري)
        self.cmb_item = QComboBox()
        self.cmb_item.setMinimumHeight(28)
        self.cmb_item.addItem("— لا يوجد ربط —", None)
        for item in fetch_items_by_type(get_connection(), "raw"):
            self.cmb_item.addItem(f"🧱 {item['name']}", item["id"])

        # ربط بحساب محاسبي
        self.cmb_account = QComboBox()
        self.cmb_account.setMinimumHeight(28)
        self.cmb_account.addItem("— حساب المخزون الافتراضي —", None)
        for acc in fetch_leaf_accounts(self.acc_conn, "asset"):
            self.cmb_account.addItem(f"{acc['code']} — {acc['name']}", acc["id"])

        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("ملاحظات...")
        self.inp_notes.setMinimumHeight(28)

        form.addRow("اسم الصنف:", self.inp_name)
        form.addRow("وحدة القياس:", self.inp_unit)
        form.addRow("الحد الأدنى:", self.sp_qty_min)
        form.addRow("ربط بخامة:", self.cmb_item)
        form.addRow("حساب المخزون:", self.cmb_account)
        form.addRow("ملاحظات:", self.inp_notes)

        self.btn_add    = QPushButton("➕  إضافة صنف")
        self.btn_save   = QPushButton("💾  حفظ التعديل")
        self.btn_cancel = QPushButton("✖  إلغاء")
        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn.setMinimumHeight(30)
        self.btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save_edit)
        self.btn_cancel.clicked.connect(self._cancel)
        form.addRow(self._make_btn_widget())

        root.addWidget(grp)
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
            QMessageBox.warning(self, "تنبيه", "أدخل اسم الصنف")
            return None
        return {
            "name":       name,
            "unit":       self.inp_unit.text().strip() or "قطعة",
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
        bus.data_changed.emit()

    def _save_edit(self):
        data = self._collect()
        if not data:
            return
        update_inventory_item(self.inv_conn, self._editing_id,
                              data["name"], data["unit"],
                              data["qty_min"], data["account_id"],
                              data["notes"])
        self._reset()
        bus.data_changed.emit()

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
        self.enter_edit_mode(inv_id, f"─── تعديل: {inv['name']} ───")

    def _reset(self):
        self.inp_name.clear()
        self.inp_unit.setText("قطعة")
        self.sp_qty_min.setValue(0)
        self.cmb_account.setCurrentIndex(0)
        self.cmb_item.setCurrentIndex(0)
        self.inp_notes.clear()
        self.exit_edit_mode("─── صنف جديد ───")