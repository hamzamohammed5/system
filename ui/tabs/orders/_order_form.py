"""
ui/tabs/orders/_order_form.py
==============================
Dialog لإنشاء طلب جديد أو تعديل طلب موجود.
يدعم:
  - اختيار عميل موجود أو إنشاء عميل جديد
  - تحديد نوع الطلب (جديد / إعادة طلب / مخصص)
  - تحديد الأولوية وتاريخ التسليم
  - الملاحظات العامة والداخلية
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton,
    QComboBox, QTextEdit, QDateEdit,
    QDialogButtonBox, QMessageBox, QGroupBox,
    QDoubleSpinBox,
)
from PyQt5.QtCore import Qt, pyqtSignal, QDate

from db.orders.customers_repo import fetch_all_customers, search_customers
from db.orders.orders_repo import (
    fetch_order, insert_order, update_order,
)

STATUS_OPTIONS = [
    ("pending",     "⏳ انتظار"),
    ("confirmed",   "✅ مؤكد"),
    ("in_progress", "🔧 تنفيذ"),
    ("ready",       "📦 جاهز"),
]

PRIORITY_OPTIONS = [
    ("low",    "⬇ منخفض"),
    ("normal", "➡ عادي"),
    ("high",   "⬆ عالي"),
    ("urgent", "🔴 عاجل"),
]

TYPE_OPTIONS = [
    ("new",     "🆕 جديد"),
    ("reorder", "🔄 إعادة طلب"),
    ("custom",  "⚙️ مخصص"),
]


def _input_ss():
    return """
        QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox, QDateEdit {
            background: #f8f9fb;
            border: 1px solid #cdd3e0;
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 12px;
            color: #1a2035;
            min-height: 34px;
        }
        QLineEdit:focus, QTextEdit:focus,
        QComboBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
            border-color: #1565c0;
            background: white;
        }
        QComboBox::drop-down { border: none; width: 20px; }
    """


class _OrderForm(QDialog):
    saved = pyqtSignal(int)  # order_id

    def __init__(self, conn, order_id: int = None, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self.order_id   = order_id
        self._customer_id = None

        title = "تعديل الطلب" if order_id else "طلب جديد"
        self.setWindowTitle(title)
        self.setMinimumWidth(560)
        self.setMinimumHeight(620)
        self.setModal(True)
        self.setStyleSheet("QDialog { background: #f8f9fb; }")

        self._build()
        if order_id:
            self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(14)

        # ── رأس ──
        hdr = QLabel(
            "✏️  تعديل الطلب" if self.order_id else "📋  طلب جديد"
        )
        hdr.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #1565c0;
            background: #e8f0fe;
            border-radius: 8px;
            padding: 8px 14px;
        """)
        root.addWidget(hdr)

        self.setStyleSheet(self.styleSheet() + _input_ss())

        # ══ قسم العميل ════════════════════════════════════
        cust_group = QGroupBox("بيانات العميل")
        cust_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #374151;
                border: 1px solid #e5e9f0;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                right: 12px; padding: 0 4px;
                font-size: 11px;
            }
        """)
        cust_lay = QVBoxLayout(cust_group)
        cust_lay.setSpacing(8)

        # بحث العميل
        search_row = QHBoxLayout()
        self.inp_cust_search = QLineEdit()
        self.inp_cust_search.setPlaceholderText("ابحث عن عميل بالاسم أو الهاتف أو الكود...")
        self.inp_cust_search.textChanged.connect(self._search_customers)

        btn_new_cust = QPushButton("+ عميل جديد")
        btn_new_cust.setMinimumHeight(34)
        btn_new_cust.setStyleSheet("""
            QPushButton {
                background: #ecfdf5; color: #065f46;
                border: 1px solid #a7f3d0; border-radius: 6px;
                padding: 0 12px; font-size: 11px;
            }
            QPushButton:hover { background: #d1fae5; }
        """)
        btn_new_cust.clicked.connect(self._new_customer)

        search_row.addWidget(self.inp_cust_search, stretch=1)
        search_row.addWidget(btn_new_cust)
        cust_lay.addLayout(search_row)

        # قائمة نتائج البحث
        self.cmb_customer = QComboBox()
        self.cmb_customer.setPlaceholderText("─ اختر عميل ─")
        self._all_customers = fetch_all_customers(self.conn, active_only=True)
        for c in self._all_customers:
            label = f"{c['code']}  —  {c['name']}  ({c['phone'] or 'بدون هاتف'})"
            self.cmb_customer.addItem(label, c["id"])
        self.cmb_customer.currentIndexChanged.connect(self._on_customer_changed)
        cust_lay.addWidget(self.cmb_customer)

        # معلومات العميل المختار
        self._lbl_cust_info = QLabel("")
        self._lbl_cust_info.setStyleSheet(
            "font-size:11px; color:#6b7280; background:#f8f9fb;"
            "border:1px solid #e5e9f0; border-radius:6px; padding:6px 10px;"
        )
        self._lbl_cust_info.setVisible(False)
        cust_lay.addWidget(self._lbl_cust_info)

        root.addWidget(cust_group)

        # ══ قسم الطلب ══════════════════════════════════════
        order_group = QGroupBox("تفاصيل الطلب")
        order_group.setStyleSheet(cust_group.styleSheet())
        form = QFormLayout(order_group)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        # النوع
        self.cmb_type = QComboBox()
        for k, v in TYPE_OPTIONS:
            self.cmb_type.addItem(v, k)
        form.addRow("نوع الطلب :", self.cmb_type)

        # الحالة (للتعديل فقط)
        self.cmb_status = QComboBox()
        for k, v in STATUS_OPTIONS:
            self.cmb_status.addItem(v, k)
        if not self.order_id:
            self.cmb_status.setVisible(False)
            form.addRow("الحالة :", self.cmb_status)
        else:
            form.addRow("الحالة :", self.cmb_status)

        # الأولوية
        self.cmb_priority = QComboBox()
        for k, v in PRIORITY_OPTIONS:
            self.cmb_priority.addItem(v, k)
        self.cmb_priority.setCurrentIndex(1)  # normal
        form.addRow("الأولوية :", self.cmb_priority)

        # تاريخ التسليم
        self.inp_due_date = QDateEdit()
        self.inp_due_date.setCalendarPopup(True)
        self.inp_due_date.setDate(QDate.currentDate().addDays(7))
        self.inp_due_date.setDisplayFormat("yyyy-MM-dd")
        form.addRow("تاريخ التسليم :", self.inp_due_date)

        # الخصم
        self.sp_discount = QDoubleSpinBox()
        self.sp_discount.setRange(0, 99999)
        self.sp_discount.setDecimals(2)
        self.sp_discount.setSuffix(" ج")
        form.addRow("الخصم الكلي :", self.sp_discount)

        # المدفوع
        self.sp_paid = QDoubleSpinBox()
        self.sp_paid.setRange(0, 9999999)
        self.sp_paid.setDecimals(2)
        self.sp_paid.setSuffix(" ج")
        form.addRow("المدفوع :", self.sp_paid)

        root.addWidget(order_group)

        # ══ الملاحظات ══════════════════════════════════════
        notes_group = QGroupBox("الملاحظات")
        notes_group.setStyleSheet(cust_group.styleSheet())
        n_lay = QVBoxLayout(notes_group)
        n_lay.setSpacing(8)

        self.inp_notes = QTextEdit()
        self.inp_notes.setPlaceholderText("ملاحظات للعميل...")
        self.inp_notes.setMaximumHeight(70)
        n_lay.addWidget(QLabel("ملاحظات للعميل:"))
        n_lay.addWidget(self.inp_notes)

        self.inp_internal = QTextEdit()
        self.inp_internal.setPlaceholderText("ملاحظات داخلية (لا تظهر للعميل)...")
        self.inp_internal.setMaximumHeight(70)
        n_lay.addWidget(QLabel("ملاحظات داخلية:"))
        n_lay.addWidget(self.inp_internal)

        root.addWidget(notes_group)

        # ══ أزرار ══════════════════════════════════════════
        btns = QHBoxLayout()
        btn_save = QPushButton("💾  حفظ الطلب")
        btn_save.setMinimumHeight(38)
        btn_save.setStyleSheet("""
            QPushButton {
                background: #1565c0; color: white;
                border: none; border-radius: 7px;
                padding: 0 22px; font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background: #0d47a1; }
        """)
        btn_save.clicked.connect(self._save)

        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setMinimumHeight(38)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: white; color: #374151;
                border: 1px solid #cdd3e0; border-radius: 7px;
                padding: 0 16px; font-size: 12px;
            }
            QPushButton:hover { background: #f8f9fb; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save, stretch=1)
        root.addLayout(btns)

    def _search_customers(self, text: str):
        if len(text) < 2:
            return
        results = search_customers(self.conn, text)
        self.cmb_customer.blockSignals(True)
        self.cmb_customer.clear()
        for c in results:
            label = f"{c['code']}  —  {c['name']}  ({c['phone'] or 'بدون هاتف'})"
            self.cmb_customer.addItem(label, c["id"])
        self.cmb_customer.blockSignals(False)
        if results:
            self.cmb_customer.setCurrentIndex(0)
            self._on_customer_changed(0)

    def _on_customer_changed(self, idx: int):
        cid = self.cmb_customer.currentData()
        self._customer_id = cid
        if cid:
            from db.orders.customers_repo import fetch_customer
            c = fetch_customer(self.conn, cid)
            if c:
                info_parts = []
                if c["phone"]:  info_parts.append(f"📞 {c['phone']}")
                if c["city"]:   info_parts.append(f"📍 {c['city']}")
                if c["email"]:  info_parts.append(f"✉️ {c['email']}")
                self._lbl_cust_info.setText("  |  ".join(info_parts) if info_parts else "")
                self._lbl_cust_info.setVisible(bool(info_parts))
        else:
            self._lbl_cust_info.setVisible(False)

    def _new_customer(self):
        from ui.tabs.orders._customer_form import _CustomerForm
        dlg = _CustomerForm(self.conn, parent=self)
        dlg.saved.connect(self._on_customer_created)
        dlg.exec_()

    def _on_customer_created(self, customer_id: int):
        from db.orders.customers_repo import fetch_customer
        c = fetch_customer(self.conn, customer_id)
        if c:
            label = f"{c['code']}  —  {c['name']}  ({c['phone'] or 'بدون هاتف'})"
            self.cmb_customer.insertItem(0, label, customer_id)
            self.cmb_customer.setCurrentIndex(0)
            self._customer_id = customer_id

    def _load(self):
        d = fetch_order(self.conn, self.order_id)
        if not d:
            return

        # اختيار العميل
        for i in range(self.cmb_customer.count()):
            if self.cmb_customer.itemData(i) == d["customer_id"]:
                self.cmb_customer.setCurrentIndex(i)
                break

        # النوع
        for i in range(self.cmb_type.count()):
            if self.cmb_type.itemData(i) == d["order_type"]:
                self.cmb_type.setCurrentIndex(i)
                break

        # الأولوية
        for i in range(self.cmb_priority.count()):
            if self.cmb_priority.itemData(i) == d["priority"]:
                self.cmb_priority.setCurrentIndex(i)
                break

        # تاريخ التسليم
        if d["due_date"]:
            self.inp_due_date.setDate(QDate.fromString(d["due_date"], "yyyy-MM-dd"))

        self.sp_discount.setValue(d["discount"] or 0)
        self.sp_paid.setValue(d["paid_amount"] or 0)
        self.inp_notes.setPlainText(d["notes"] or "")
        self.inp_internal.setPlainText(d["internal_notes"] or "")

    def _save(self):
        if not self._customer_id:
            QMessageBox.warning(self, "تنبيه", "اختر عميلاً أولاً")
            return

        priority  = self.cmb_priority.currentData()
        order_type = self.cmb_type.currentData()
        due_date  = self.inp_due_date.date().toString("yyyy-MM-dd")
        discount  = self.sp_discount.value()
        paid      = self.sp_paid.value()
        notes     = self.inp_notes.toPlainText().strip()
        internal  = self.inp_internal.toPlainText().strip()

        if self.order_id:
            update_order(
                self.conn, self.order_id,
                priority=priority,
                due_date=due_date,
                discount=discount,
                paid_amount=paid,
                notes=notes,
                internal_notes=internal,
            )
            self.saved.emit(self.order_id)
        else:
            oid = insert_order(
                self.conn,
                customer_id=self._customer_id,
                order_type=order_type,
                priority=priority,
                due_date=due_date,
                discount=discount,
                paid_amount=paid,
                notes=notes,
                internal_notes=internal,
            )
            self.saved.emit(oid)

        self.accept()