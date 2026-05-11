"""
ui/tabs/inventory_items_tab.py
==============================
فورم وجدول أصناف المخزن.

يحتوي على:
  _ItemForm   — فورم إضافة / تعديل صنف مخزن
  _ItemsTable — جدول الأصناف مع تحديد وتعديل وحذف
  _ItemsTab   — تبويب يجمع الفورم والجدول في Splitter
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QGroupBox, QFormLayout,
    QLineEdit, QPushButton, QDoubleSpinBox, QComboBox,
    QTableWidgetItem, QMessageBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.connection      import get_connection
from db.inventory_repo  import (
    fetch_all_inventory, fetch_inventory_item,
    insert_inventory_item, update_inventory_item, delete_inventory_item,
)
from db.accounting_repo import fetch_leaf_accounts
from db.items_repo      import fetch_items_by_type
from ui.helpers import (
    make_table, setup_table_columns, buttons_row,
    section_label, danger_button, confirm_delete,
    EditModeMixin,
)
from ui.events import bus


def _spin(max_=999999999, dec=4):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(30)
    return s


def _safe_subtype(acc_row) -> str:
    try:
        val = acc_row["subtype"]
        return val if val else ""
    except (IndexError, KeyError):
        return ""


# ══════════════════════════════════════════════════════════
# فورم إضافة / تعديل صنف مخزن
# ══════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════
# جدول الأصناف
# ══════════════════════════════════════════════════════════

class _ItemsTable(QWidget):
    def __init__(self, inv_conn, form: _ItemForm, on_select, parent=None):
        super().__init__(parent)
        self.inv_conn   = inv_conn
        self._form      = form
        self._on_select = on_select
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(6)
        root.addWidget(section_label("─── أصناف المخزن ───"))

        self.table = make_table(
            ["ID", "الصنف", "الوحدة", "الرصيد", "الحد الأدنى",
             "متوسط التكلفة", "إجمالي القيمة"],
            stretch_col=1
        )
        setup_table_columns(self.table,
            widths={0: 40, 2: 70, 3: 80, 4: 80, 5: 110, 6: 110},
            stretch_col=1
        )
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(
            lambda: self._on_select(self._selected_id())
        )
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

    def _load(self):
        rows = fetch_all_inventory(self.inv_conn)
        self.table.setRowCount(0)
        for inv in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(inv["id"])))
            name_item = QTableWidgetItem(inv["name"])
            name_item.setToolTip(inv["name"])
            self.table.setItem(r, 1, name_item)
            self.table.setItem(r, 2, QTableWidgetItem(inv["unit"]))

            qty_item = QTableWidgetItem(f"{inv['qty_on_hand']:,.4g}")
            if inv["qty_on_hand"] <= inv["qty_min"]:
                qty_item.setForeground(QColor("#c62828"))
                qty_item.setToolTip(f"⚠️ تحت الحد الأدنى ({inv['qty_min']:,.4g})")
            self.table.setItem(r, 3, qty_item)

            self.table.setItem(r, 4, QTableWidgetItem(f"{inv['qty_min']:,.4g}"))
            self.table.setItem(r, 5, QTableWidgetItem(f"{inv['avg_cost']:,.4f}"))
            self.table.setItem(r, 6, QTableWidgetItem(f"{inv['total_value']:,.2f}"))

    def _edit(self):
        inv_id = self._selected_id()
        if not inv_id:
            QMessageBox.information(self, "تنبيه", "اختر صنفاً أولاً")
            return
        self._form.load_for_edit(inv_id)

    def _delete(self):
        inv_id = self._selected_id()
        if not inv_id:
            QMessageBox.information(self, "تنبيه", "اختر صنفاً أولاً")
            return
        inv = fetch_inventory_item(self.inv_conn, inv_id)
        if confirm_delete(self, inv["name"]):
            delete_inventory_item(self.inv_conn, inv_id)
            bus.data_changed.emit()


# ══════════════════════════════════════════════════════════
# تبويب الأصناف
# ══════════════════════════════════════════════════════════

class _ItemsTab(QWidget):
    def __init__(self, inv_conn, acc_conn, on_select, parent=None):
        super().__init__(parent)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)

        form  = _ItemForm(inv_conn, acc_conn)
        table = _ItemsTable(inv_conn, form, on_select)

        splitter.addWidget(form)
        splitter.addWidget(table)
        splitter.setSizes([320, 580])
        splitter.setCollapsible(0, True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(splitter)
