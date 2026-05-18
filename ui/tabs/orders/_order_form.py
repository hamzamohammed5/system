"""
ui/tabs/orders/_order_form.py
==============================
Dialog لإنشاء طلب جديد أو تعديل طلب موجود.
يدعم:
  - اختيار عميل موجود أو إنشاء عميل جديد
  - تحديد نوع الطلب / الأولوية / تاريخ التسليم
  - إضافة وتعديل وحذف بنود الطلب مباشرة من الفورم
  - اختيار المنتج من قائمة المنتجات المسعّرة (مجمّعة بالتصنيف)
  - اختيار عروض جاهزة وإضافة بنودها دفعة واحدة
"""


from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton,
    QComboBox, QTextEdit, QDateEdit,
    QMessageBox, QGroupBox,
    QDoubleSpinBox, QScrollArea,
    QWidget, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui  import QFont

from db.orders.customers_repo import fetch_all_customers, search_customers
from db.orders.orders_repo import (
    fetch_order, insert_order, update_order,
    fetch_order_items, insert_order_item,
    update_order_item, delete_order_item,
)
from .order_form._item_row_widget   import _ItemRowWidget
from .order_form._products_fetcher  import fetch_offers, fetch_offer_lines

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

_BLUE   = "#1565c0"
_ORANGE = "#e65100"
_GREEN  = "#2e7d32"
_GRAY   = "#6b7280"
_BG     = "#f8f9fb"
_BORDER = "#cdd3e0"
_WHITE  = "#ffffff"


def _input_ss():
    return f"""
        QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox, QDateEdit {{
            background: {_BG}; border: 1px solid {_BORDER};
            border-radius: 6px; padding: 4px 10px;
            font-size: 12px; color: #1a2035; min-height: 32px;
        }}
        QLineEdit:focus, QTextEdit:focus,
        QComboBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {{
            border-color: {_BLUE}; background: {_WHITE};
        }}
        QComboBox::drop-down {{ border: none; width: 20px; }}
    """


def _group_ss(accent=_BLUE):
    return f"""
        QGroupBox {{
            font-weight: bold; color: #374151;
            border: 1px solid #e5e9f0; border-radius: 8px;
            margin-top: 10px; padding-top: 10px; background: {_WHITE};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin; right: 12px; padding: 0 6px;
            font-size: 11px; color: {accent};
        }}
    """


def _btn_ss(bg=_BLUE, color=_WHITE, border=None):
    b = border or bg
    return f"""
        QPushButton {{
            background: {bg}; color: {color};
            border: 1px solid {b}; border-radius: 6px;
            padding: 0 14px; font-size: 12px; min-height: 32px;
        }}
        QPushButton:hover {{ opacity: 0.85; }}
    """


class _OrderForm(QDialog):
    saved = pyqtSignal(int)

    def __init__(self, conn, order_id: int = None, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self.order_id   = order_id
        self._customer_id = None
        self._item_rows: list[_ItemRowWidget] = []

        _ItemRowWidget.invalidate_cache()

        title = "تعديل الطلب" if order_id else "طلب جديد"
        self.setWindowTitle(title)
        self.setMinimumWidth(880)
        self.setMinimumHeight(760)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background: {_BG}; }}")

        self._build()
        if order_id:
            self._load()

    # ══ بناء الواجهة ══════════════════════════════════════

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background: #f0f0f0; width: 6px; border-radius: 3px; }
            QScrollBar::handle:vertical { background: #cdd3e0; border-radius: 3px; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        content = QWidget()
        content.setStyleSheet(f"background: {_BG};")
        root = QVBoxLayout(content)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(14)
        scroll.setWidget(content)
        outer.addWidget(scroll)
        self.setStyleSheet(self.styleSheet() + _input_ss())

        # رأس
        hdr = QLabel("✏️  تعديل الطلب" if self.order_id else "📋  طلب جديد")
        hdr.setStyleSheet(f"""
            font-size: 15px; font-weight: bold; color: {_BLUE};
            background: #e8f0fe; border-radius: 8px; padding: 10px 16px;
        """)
        root.addWidget(hdr)

        # ── قسم 1: العميل ──
        self._build_customer_section(root)

        # ── قسم 2: تفاصيل الطلب ──
        self._build_order_details(root)

        # ── قسم 3: بنود الطلب ──
        self._build_items_section(root)

        # ── قسم 4: الملاحظات ──
        self._build_notes_section(root)

        # ── أزرار الحفظ ──
        self._build_save_buttons(root)

        self._add_item_row()

    def _build_customer_section(self, root):
        cust_grp = QGroupBox("👤  بيانات العميل")
        cust_grp.setStyleSheet(_group_ss(_BLUE))
        c_lay = QVBoxLayout(cust_grp)
        c_lay.setSpacing(8)

        search_row = QHBoxLayout()
        self.inp_cust_search = QLineEdit()
        self.inp_cust_search.setPlaceholderText("ابحث عن عميل بالاسم أو الهاتف أو الكود...")
        self.inp_cust_search.textChanged.connect(self._search_customers)

        btn_new_cust = QPushButton("+ عميل جديد")
        btn_new_cust.setMinimumHeight(34)
        btn_new_cust.setStyleSheet(_btn_ss("#ecfdf5", "#065f46", "#a7f3d0"))
        btn_new_cust.clicked.connect(self._new_customer)
        search_row.addWidget(self.inp_cust_search, stretch=1)
        search_row.addWidget(btn_new_cust)
        c_lay.addLayout(search_row)

        self.cmb_customer = QComboBox()
        self.cmb_customer.setPlaceholderText("─ اختر عميل ─")
        self._all_customers = fetch_all_customers(self.conn, active_only=True)
        for c in self._all_customers:
            label = f"{c['code']}  —  {c['name']}  ({c['phone'] or 'بدون هاتف'})"
            self.cmb_customer.addItem(label, c["id"])
        self.cmb_customer.currentIndexChanged.connect(self._on_customer_changed)
        c_lay.addWidget(self.cmb_customer)

        self._lbl_cust_info = QLabel("")
        self._lbl_cust_info.setStyleSheet(
            f"font-size:11px; color:#6b7280; background:{_BG};"
            "border:1px solid #e5e9f0; border-radius:6px; padding:6px 10px;"
        )
        self._lbl_cust_info.setVisible(False)
        c_lay.addWidget(self._lbl_cust_info)
        root.addWidget(cust_grp)

    def _build_order_details(self, root):
        order_grp = QGroupBox("📋  تفاصيل الطلب")
        order_grp.setStyleSheet(_group_ss(_BLUE))
        form = QFormLayout(order_grp)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.cmb_type = QComboBox()
        for k, v in TYPE_OPTIONS:
            self.cmb_type.addItem(v, k)
        form.addRow("نوع الطلب :", self.cmb_type)

        self.cmb_status = QComboBox()
        for k, v in STATUS_OPTIONS:
            self.cmb_status.addItem(v, k)
        if not self.order_id:
            self.cmb_status.setVisible(False)
        form.addRow("الحالة :", self.cmb_status)

        self.cmb_priority = QComboBox()
        for k, v in PRIORITY_OPTIONS:
            self.cmb_priority.addItem(v, k)
        self.cmb_priority.setCurrentIndex(1)
        form.addRow("الأولوية :", self.cmb_priority)

        self.inp_due_date = QDateEdit()
        self.inp_due_date.setCalendarPopup(True)
        self.inp_due_date.setDate(QDate.currentDate().addDays(7))
        self.inp_due_date.setDisplayFormat("yyyy-MM-dd")
        form.addRow("تاريخ التسليم :", self.inp_due_date)

        self.sp_discount = QDoubleSpinBox()
        self.sp_discount.setRange(0, 99_999)
        self.sp_discount.setDecimals(2)
        self.sp_discount.setSuffix(" ج")
        form.addRow("الخصم الكلي :", self.sp_discount)

        self.sp_paid = QDoubleSpinBox()
        self.sp_paid.setRange(0, 9_999_999)
        self.sp_paid.setDecimals(2)
        self.sp_paid.setSuffix(" ج")
        form.addRow("المدفوع :", self.sp_paid)
        root.addWidget(order_grp)

    def _build_items_section(self, root):
        items_grp = QGroupBox("📦  بنود الطلب")
        items_grp.setStyleSheet(_group_ss(_ORANGE))
        items_lay = QVBoxLayout(items_grp)
        items_lay.setSpacing(8)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        btn_add_item = QPushButton("➕  إضافة بند")
        btn_add_item.setMinimumHeight(34)
        btn_add_item.setStyleSheet(_btn_ss("#ecfdf5", "#065f46", "#a7f3d0"))
        btn_add_item.clicked.connect(self._add_item_row)

        lbl_offer = QLabel("أو استورد عرضاً:")
        lbl_offer.setStyleSheet(f"color:{_GRAY}; font-size:11px;")

        self.cmb_offers = QComboBox()
        self.cmb_offers.setMinimumHeight(34)
        self.cmb_offers.setMinimumWidth(200)
        self._load_offers_combo()

        btn_import_offer = QPushButton("📥  استيراد")
        btn_import_offer.setMinimumHeight(34)
        btn_import_offer.setStyleSheet(_btn_ss("#e8f0fe", _BLUE, "#90caf9"))
        btn_import_offer.clicked.connect(self._import_offer)

        toolbar.addWidget(btn_add_item)
        toolbar.addStretch()
        toolbar.addWidget(lbl_offer)
        toolbar.addWidget(self.cmb_offers, stretch=1)
        toolbar.addWidget(btn_import_offer)
        items_lay.addLayout(toolbar)

        self._rows_container = QWidget()
        self._rows_container.setStyleSheet("background: transparent;")
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setSpacing(6)
        self._rows_layout.setContentsMargins(0, 0, 4, 0)
        items_lay.addWidget(self._rows_container)

        from PyQt5.QtWidgets import QFrame
        total_bar = QFrame()
        total_bar.setStyleSheet("""
            QFrame { background: #e8f0fe; border: 1px solid #90caf9; border-radius: 6px; }
        """)
        total_row = QHBoxLayout(total_bar)
        total_row.setContentsMargins(14, 8, 14, 8)

        lbl_items_count = QLabel("البنود:")
        lbl_items_count.setStyleSheet(f"color:{_GRAY}; font-size:11px; background:transparent;")
        self.lbl_items_count = QLabel("0")
        self.lbl_items_count.setStyleSheet(f"font-weight:bold; color:{_BLUE}; background:transparent;")
        lbl_subtotal_txt = QLabel("الإجمالي قبل الخصم:")
        lbl_subtotal_txt.setStyleSheet(f"color:{_GRAY}; font-size:11px; background:transparent;")
        self.lbl_subtotal = QLabel("0.00 ج")
        self.lbl_subtotal.setStyleSheet(f"font-weight:bold; color:{_BLUE}; font-size:13px; background:transparent;")

        total_row.addWidget(lbl_items_count)
        total_row.addWidget(self.lbl_items_count)
        total_row.addStretch()
        total_row.addWidget(lbl_subtotal_txt)
        total_row.addWidget(self.lbl_subtotal)
        items_lay.addWidget(total_bar)
        root.addWidget(items_grp)

    def _build_notes_section(self, root):
        notes_grp = QGroupBox("📝  الملاحظات")
        notes_grp.setStyleSheet(_group_ss(_GRAY))
        n_lay = QVBoxLayout(notes_grp)
        n_lay.setSpacing(8)

        self.inp_notes = QTextEdit()
        self.inp_notes.setPlaceholderText("ملاحظات للعميل...")
        self.inp_notes.setMaximumHeight(65)
        n_lay.addWidget(QLabel("ملاحظات للعميل:"))
        n_lay.addWidget(self.inp_notes)

        self.inp_internal = QTextEdit()
        self.inp_internal.setPlaceholderText("ملاحظات داخلية (لا تظهر للعميل)...")
        self.inp_internal.setMaximumHeight(65)
        n_lay.addWidget(QLabel("ملاحظات داخلية:"))
        n_lay.addWidget(self.inp_internal)
        root.addWidget(notes_grp)

    def _build_save_buttons(self, root):
        btns = QHBoxLayout()

        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setMinimumHeight(40)
        btn_cancel.setStyleSheet(_btn_ss(_WHITE, "#374151", _BORDER))
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("💾  حفظ الطلب")
        btn_save.setMinimumHeight(40)
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background: {_BLUE}; color: {_WHITE};
                border: none; border-radius: 8px;
                padding: 0 24px; font-weight: bold; font-size: 13px;
            }}
            QPushButton:hover {{ background: #0d47a1; }}
        """)
        btn_save.clicked.connect(self._save)

        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save, stretch=1)
        root.addLayout(btns)

    # ══ عمليات البنود ════════════════════════════════════

    def _add_item_row(self, prefill: dict = None) -> _ItemRowWidget:
        row = _ItemRowWidget()
        row.changed.connect(self._update_totals)
        row.removed.connect(self._remove_item_row)
        self._item_rows.append(row)
        self._rows_layout.addWidget(row)
        if prefill:
            row.load_from_order_item(prefill)
        self._update_totals()
        return row

    def _remove_item_row(self, row_widget: _ItemRowWidget):
        if row_widget in self._item_rows:
            self._item_rows.remove(row_widget)
        self._rows_layout.removeWidget(row_widget)
        row_widget.deleteLater()
        self._update_totals()

    def _update_totals(self):
        total = sum(r.get_total() for r in self._item_rows)
        valid = sum(1 for r in self._item_rows if r.get_product_name())
        self.lbl_items_count.setText(str(valid))
        self.lbl_subtotal.setText(f"{total:,.2f} ج")

    # ══ العروض ════════════════════════════════════════════

    def _load_offers_combo(self):
        self.cmb_offers.clear()
        self.cmb_offers.addItem("— اختر عرضاً —", None)
        for o in fetch_offers():
            cat = f" [{o['category_name']}]" if o.get("category_name") else ""
            label = f"🎁 {o['name']}  —  خصم {o['discount']:.0f}%{cat}"
            self.cmb_offers.addItem(label, o["id"])

    def _import_offer(self):
        oid = self.cmb_offers.currentData()
        if not oid:
            return
        offer_discount = 0.0
        try:
            from db.shared.connection import get_costing_connection
            conn_erp = get_costing_connection()
            o = conn_erp.execute("SELECT discount FROM offers WHERE id=?", (oid,)).fetchone()
            if o:
                offer_discount = float(o["discount"])
            conn_erp.close()
        except Exception:
            pass

        lines = fetch_offer_lines(oid)
        if not lines:
            QMessageBox.information(self, "تنبيه", "هذا العرض لا يحتوي على بنود.")
            return

        for r in list(self._item_rows):
            if not r.get_product_name():
                self._remove_item_row(r)

        for line in lines:
            row = self._add_item_row()
            pid = line.get("item_id")
            if pid:
                cmb = row.cmb_product
                for i in range(cmb.count()):
                    if cmb.itemData(i) == pid:
                        cmb.blockSignals(True)
                        cmb.setCurrentIndex(i)
                        cmb.blockSignals(False)
                        for p in _ItemRowWidget._get_products():
                            if p["id"] == pid:
                                row._unit_price = p.get("price") or 0.0
                                row.lbl_price.setText(f"{row._unit_price:.2f} ج")
                                break
                        break
            row.sp_qty.setValue(line["qty"])
            row.set_offer_discount(offer_discount)

        self.cmb_offers.setCurrentIndex(0)

    # ══ العميل ════════════════════════════════════════════

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
                parts = []
                if c["phone"]:  parts.append(f"📞 {c['phone']}")
                if c["city"]:   parts.append(f"📍 {c['city']}")
                if c["email"]:  parts.append(f"✉️ {c['email']}")
                self._lbl_cust_info.setText("  |  ".join(parts) if parts else "")
                self._lbl_cust_info.setVisible(bool(parts))
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

    # ══ تحميل ══════════════════════════════════════════════

    def _load(self):
        d = fetch_order(self.conn, self.order_id)
        if not d:
            return

        for i in range(self.cmb_customer.count()):
            if self.cmb_customer.itemData(i) == d["customer_id"]:
                self.cmb_customer.setCurrentIndex(i)
                break

        for cmb, key in [(self.cmb_type, "order_type"),
                         (self.cmb_priority, "priority"),
                         (self.cmb_status, "status")]:
            for i in range(cmb.count()):
                if cmb.itemData(i) == d[key]:
                    cmb.setCurrentIndex(i)
                    break

        if d["due_date"]:
            self.inp_due_date.setDate(QDate.fromString(d["due_date"], "yyyy-MM-dd"))
        self.sp_discount.setValue(d["discount"] or 0)
        self.sp_paid.setValue(d["paid_amount"] or 0)
        self.inp_notes.setPlainText(d["notes"] or "")
        self.inp_internal.setPlainText(d["internal_notes"] or "")

        for r in list(self._item_rows):
            self._remove_item_row(r)

        items = fetch_order_items(self.conn, self.order_id)
        for item in items:
            self._add_item_row(prefill=dict(item))

    # ══ حفظ ════════════════════════════════════════════════

    def _save(self):
        if not self._customer_id:
            QMessageBox.warning(self, "تنبيه", "اختر عميلاً أولاً")
            return

        valid_rows = [r for r in self._item_rows if r.get_product_name()]
        if not valid_rows:
            QMessageBox.warning(self, "تنبيه", "أضف بنداً واحداً على الأقل")
            return

        priority   = self.cmb_priority.currentData()
        order_type = self.cmb_type.currentData()
        due_date   = self.inp_due_date.date().toString("yyyy-MM-dd")
        discount   = self.sp_discount.value()
        paid       = self.sp_paid.value()
        notes      = self.inp_notes.toPlainText().strip()
        internal   = self.inp_internal.toPlainText().strip()

        if self.order_id:
            update_order(self.conn, self.order_id, priority=priority,
                         due_date=due_date, discount=discount,
                         paid_amount=paid, notes=notes, internal_notes=internal)
            existing = fetch_order_items(self.conn, self.order_id)
            for eid in {i["id"] for i in existing}:
                delete_order_item(self.conn, eid)
            for idx, row in enumerate(valid_rows):
                d = row.get_data()
                insert_order_item(self.conn, self.order_id,
                                  item_name=d["item_name"], description=d["description"],
                                  quantity=d["quantity"], unit=d["unit"],
                                  unit_price=d["unit_price"], discount_pct=d["discount_pct"],
                                  design_ref=d["design_ref"], notes=d["notes"], sort_order=idx)
            self.saved.emit(self.order_id)
        else:
            oid = insert_order(self.conn, customer_id=self._customer_id,
                               order_type=order_type, priority=priority,
                               due_date=due_date, discount=discount,
                               paid_amount=paid, notes=notes, internal_notes=internal)
            for idx, row in enumerate(valid_rows):
                d = row.get_data()
                insert_order_item(self.conn, oid,
                                  item_name=d["item_name"], description=d["description"],
                                  quantity=d["quantity"], unit=d["unit"],
                                  unit_price=d["unit_price"], discount_pct=d["discount_pct"],
                                  design_ref=d["design_ref"], notes=d["notes"], sort_order=idx)
            self.saved.emit(oid)

        self.accept()