"""
ui/tabs/inventory_tab.py
========================
تبويب المخزن — إدارة الأصناف والحركات مع ربط محاسبي تلقائي.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QFrame, QSplitter, QPushButton,
    QTableWidgetItem, QHeaderView, QMessageBox,
    QLineEdit, QDoubleSpinBox, QComboBox,
    QFormLayout, QGroupBox, QDateEdit,
    QAbstractItemView,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui  import QColor

from db.connection      import get_connection, get_accounting_connection, get_inventory_connection
from db.inventory_repo  import (
    fetch_all_inventory, fetch_inventory_item,
    insert_inventory_item, update_inventory_item, delete_inventory_item,
    fetch_inventory_moves, record_inventory_move,
)
from db.accounting_repo import (
    fetch_leaf_accounts, purchase_inventory,
)
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
    """يرجع subtype بأمان من sqlite3.Row أو dict."""
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
            ["ID", "الصنف", "الوحدة", "الرصيد", "الحد الأدنى", "متوسط التكلفة", "إجمالي القيمة"],
            stretch_col=1
        )
        setup_table_columns(self.table,
            widths={0:40, 2:70, 3:80, 4:80, 5:110, 6:110},
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


# ══════════════════════════════════════════════════════════
# تبويب حركة الوارد (شراء)
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
        self.lbl_total.setStyleSheet("font-weight:bold; color:#2e7d32; font-size:14px;")
        self.sp_qty.valueChanged.connect(self._update_total)
        self.sp_unit_cost.valueChanged.connect(self._update_total)

        self.dt_date = QDateEdit(QDate.currentDate())
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDisplayFormat("yyyy-MM-dd")
        self.dt_date.setFixedWidth(130)

        # حساب الدفع — نجيب الخصوم + الأصول النقدية/البنكية بأمان
        self.cmb_payment = QComboBox()
        self.cmb_payment.setMinimumHeight(28)

        # الخصوم (موردون/دائنون)
        for acc in fetch_leaf_accounts(self.acc_conn, "liability"):
            self.cmb_payment.addItem(f"{acc['code']} — {acc['name']}", acc["id"])

        # الأصول النقدية والبنكية
        for acc in fetch_leaf_accounts(self.acc_conn, "asset"):
            subtype = _safe_subtype(acc)
            if subtype in ("cash", "bank"):
                self.cmb_payment.addItem(f"{acc['code']} — {acc['name']}", acc["id"])

        # اختار الموردين افتراضياً (كود 211)
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
            widths={0:90, 2:80, 3:100, 4:100, 5:100},
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
            QMessageBox.information(self, "تم", "✅ تم تسجيل الاستلام وإنشاء قيد محاسبي")
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


# ══════════════════════════════════════════════════════════
# تبويب حركة الصادر (صرف)
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
        self.lbl_available.setStyleSheet("color:#1565c0; font-weight:bold;")

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
            ["التاريخ", "الصنف", "الكمية", "متوسط التكلفة", "إجمالي القيمة", "البيان"],
            stretch_col=1
        )
        setup_table_columns(self.table,
            widths={0:90, 2:80, 3:110, 4:110, 5:150},
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
            record_inventory_move(self.inv_conn, inv_id, "out", qty, 0, date, notes)
            self.inp_notes.clear()
            bus.data_changed.emit()
        except ValueError as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _load_moves(self):
        try:
            rows = self.inv_conn.execute("""
                SELECT im.date, inv.name, im.qty, im.unit_cost, im.total_cost, im.notes
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


# ══════════════════════════════════════════════════════════
# تقرير المخزن
# ══════════════════════════════════════════════════════════

class _ReportTab(QWidget):
    def __init__(self, inv_conn, parent=None):
        super().__init__(parent)
        self.inv_conn = inv_conn
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(10)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)

        def _card(label, color):
            f = QFrame()
            f.setStyleSheet(f"""
                QFrame {{
                    background: white;
                    border-left: 4px solid {color};
                    border-radius: 6px;
                    padding: 4px;
                }}
            """)
            lay = QVBoxLayout(f)
            lay.setContentsMargins(12, 8, 12, 8)
            lbl_t = QLabel(label)
            lbl_t.setStyleSheet("font-size:10px; color:#888; background:transparent; border:none;")
            lbl_v = QLabel("─")
            lbl_v.setStyleSheet(f"font-size:16px; font-weight:bold; color:{color}; background:transparent; border:none;")
            lay.addWidget(lbl_t)
            lay.addWidget(lbl_v)
            cards_row.addWidget(f, stretch=1)
            return lbl_v

        self.lbl_total_items = _card("عدد الأصناف",              "#1565c0")
        self.lbl_total_value = _card("إجمالي قيمة المخزن",       "#2e7d32")
        self.lbl_low_stock   = _card("أصناف تحت الحد الأدنى",    "#c62828")
        self.lbl_zero_stock  = _card("أصناف نفدت",               "#e65100")

        root.addLayout(cards_row)

        root.addWidget(section_label("─── تقرير مخزن تفصيلي ───"))
        self.table = make_table(
            ["الصنف", "الوحدة", "الرصيد", "الحد الأدنى", "متوسط التكلفة", "القيمة الإجمالية", "الحالة"],
            stretch_col=0
        )
        setup_table_columns(self.table,
            widths={1:70, 2:80, 3:80, 4:110, 5:120, 6:90},
            stretch_col=0
        )
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, stretch=1)

    def _load(self):
        rows = fetch_all_inventory(self.inv_conn)
        self.table.setRowCount(0)
        total_val = 0.0
        low_count = zero_count = 0

        for inv in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)

            name_item = QTableWidgetItem(inv["name"])
            name_item.setToolTip(inv["name"])
            self.table.setItem(r, 0, name_item)
            self.table.setItem(r, 1, QTableWidgetItem(inv["unit"]))
            self.table.setItem(r, 2, QTableWidgetItem(f"{inv['qty_on_hand']:,.4g}"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{inv['qty_min']:,.4g}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"{inv['avg_cost']:,.4f}"))
            self.table.setItem(r, 5, QTableWidgetItem(f"{inv['total_value']:,.2f}"))

            if inv["qty_on_hand"] == 0:
                status = "❌ نفد"
                color  = QColor("#c62828")
                zero_count += 1
            elif inv["qty_on_hand"] <= inv["qty_min"]:
                status = "⚠️ منخفض"
                color  = QColor("#e65100")
                low_count += 1
            else:
                status = "✅ متوفر"
                color  = QColor("#2e7d32")

            status_item = QTableWidgetItem(status)
            status_item.setForeground(color)
            self.table.setItem(r, 6, status_item)
            total_val += inv["total_value"]

        self.lbl_total_items.setText(str(len(rows)))
        self.lbl_total_value.setText(f"{total_val:,.2f}  ج")
        self.lbl_low_stock.setText(str(low_count))
        self.lbl_zero_stock.setText(str(zero_count))


# ══════════════════════════════════════════════════════════
# تبويب حركات صنف محدد
# ══════════════════════════════════════════════════════════

class _MovesPanel(QWidget):
    def __init__(self, inv_conn, parent=None):
        super().__init__(parent)
        self.inv_conn = inv_conn
        self._inv_id  = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(6)

        self.lbl_title = QLabel("اختر صنفاً لعرض حركاته")
        self.lbl_title.setStyleSheet("font-weight:bold; color:#1565c0; font-size:13px;")
        root.addWidget(self.lbl_title)

        self.table = make_table(
            ["التاريخ", "النوع", "الكمية", "سعر الوحدة", "الإجمالي", "رقم القيد", "ملاحظات"],
            stretch_col=6
        )
        setup_table_columns(self.table,
            widths={0:90, 1:70, 2:80, 3:100, 4:100, 5:100},
            stretch_col=6
        )
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, stretch=1)

    def load(self, inv_id: int):
        self._inv_id = inv_id
        inv = fetch_inventory_item(self.inv_conn, inv_id)
        if not inv:
            return
        self.lbl_title.setText(
            f"📦  حركات: {inv['name']}  (رصيد: {inv['qty_on_hand']:,.4g} {inv['unit']})"
        )
        moves = fetch_inventory_moves(self.inv_conn, inv_id)
        self.table.setRowCount(0)
        type_ar    = {"in": "📥 وارد", "out": "📤 صادر", "adjust": "⚖️ تسوية"}
        type_color = {"in": "#2e7d32",  "out": "#c62828",  "adjust": "#1565c0"}
        for m in moves:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(m["date"]))
            type_item = QTableWidgetItem(type_ar.get(m["move_type"], m["move_type"]))
            type_item.setForeground(QColor(type_color.get(m["move_type"], "#333")))
            self.table.setItem(r, 1, type_item)
            self.table.setItem(r, 2, QTableWidgetItem(f"{m['qty']:,.4g}"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{m['unit_cost']:,.4f}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"{m['total_cost']:,.2f}"))
            ref = m["ref_entry_no"] if "ref_entry_no" in m.keys() else "—"
            self.table.setItem(r, 5, QTableWidgetItem(ref or "—"))
            notes_item = QTableWidgetItem(m["notes"] or "—")
            notes_item.setToolTip(m["notes"] or "")
            self.table.setItem(r, 6, notes_item)

    def clear(self):
        self.table.setRowCount(0)
        self.lbl_title.setText("اختر صنفاً لعرض حركاته")


# ══════════════════════════════════════════════════════════
# التبويب الرئيسي للمخزن
# ══════════════════════════════════════════════════════════

class InventoryTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.inv_conn     = get_inventory_connection()
        self.acc_conn     = get_accounting_connection()
        self._moves_panel = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self._moves_panel = _MovesPanel(self.inv_conn)

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabBar::tab:selected { color:#2e7d32; border-top:2px solid #2e7d32; }
        """)

        tabs.addTab(
            _ItemsTab(self.inv_conn, self.acc_conn, self._on_item_selected),
            "📦  الأصناف"
        )
        tabs.addTab(_InboundTab(self.inv_conn, self.acc_conn), "📥  وارد / شراء")
        tabs.addTab(_OutboundTab(self.inv_conn),               "📤  صادر / صرف")
        tabs.addTab(_ReportTab(self.inv_conn),                 "📊  تقرير المخزن")
        tabs.addTab(self._moves_panel,                         "🔄  حركات الصنف")

        root.addWidget(tabs)

    def _on_item_selected(self, inv_id):
        if inv_id and self._moves_panel:
            self._moves_panel.load(inv_id)

    def closeEvent(self, event):
        self.inv_conn.close()
        self.acc_conn.close()
        super().closeEvent(event)