"""
ui/tabs/orders/customers_tab.py
================================
تبويب إدارة العملاء:
  يسار : قائمة العملاء مع بحث وفلتر
  يمين : تفاصيل العميل + إحصائياته + طلباته
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QFrame, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QAbstractItemView, QMessageBox,
    QDialog, QScrollArea,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui  import QColor, QFont

from db.orders.customers_repo import (
    fetch_all_customers, fetch_customer,
    delete_customer, toggle_customer_active,
    fetch_customer_stats, fetch_contacts,
)
from db.orders.orders_repo import fetch_customer_orders
from ui.tabs.orders._customer_form import _CustomerForm


# ══════════════════════════════════════════════════════════
# لوحة قائمة العملاء (يسار)
# ══════════════════════════════════════════════════════════

class _CustomersListPanel(QWidget):
    customer_selected = pyqtSignal(int)
    new_customer      = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._all_rows = []
        self._timer    = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._apply_filter)
        self._build()
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        toolbar = QFrame()
        toolbar.setStyleSheet("""
            QFrame { background: #ffffff; border-bottom: 1px solid #e5e9f0; }
        """)
        tb = QVBoxLayout(toolbar)
        tb.setContentsMargins(12, 10, 12, 10)
        tb.setSpacing(8)

        # صف البحث + زر جديد
        row1 = QHBoxLayout()
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("بحث بالاسم أو الهاتف أو الكود...")
        self.inp_search.setMinimumHeight(34)
        self.inp_search.setStyleSheet("""
            QLineEdit {
                background: #f8f9fb; border: 1px solid #cdd3e0;
                border-radius: 6px; padding: 0 10px; font-size: 12px;
            }
            QLineEdit:focus { border-color: #1565c0; background: white; }
        """)
        self.inp_search.textChanged.connect(lambda: self._timer.start())

        btn_new = QPushButton("  + عميل جديد")
        btn_new.setMinimumHeight(34)
        btn_new.setStyleSheet("""
            QPushButton {
                background: #1565c0; color: white;
                border: none; border-radius: 6px;
                padding: 0 14px; font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background: #0d47a1; }
        """)
        btn_new.clicked.connect(self.new_customer.emit)
        row1.addWidget(self.inp_search, stretch=1)
        row1.addWidget(btn_new)
        tb.addLayout(row1)

        # فلتر النوع + الحالة
        row2 = QHBoxLayout()
        self.cmb_type = QComboBox()
        self.cmb_type.setMinimumHeight(28)
        self.cmb_type.addItem("كل الأنواع", None)
        self.cmb_type.addItem("أفراد", "individual")
        self.cmb_type.addItem("شركات", "company")
        self.cmb_type.currentIndexChanged.connect(self._apply_filter)

        self.cmb_active = QComboBox()
        self.cmb_active.setMinimumHeight(28)
        self.cmb_active.addItem("الكل", None)
        self.cmb_active.addItem("نشط", 1)
        self.cmb_active.addItem("غير نشط", 0)
        self.cmb_active.currentIndexChanged.connect(self._apply_filter)

        for cmb in (self.cmb_type, self.cmb_active):
            cmb.setStyleSheet("""
                QComboBox {
                    background: #f8f9fb; border: 1px solid #cdd3e0;
                    border-radius: 5px; padding: 0 8px; font-size: 11px;
                }
                QComboBox:focus { border-color: #1565c0; }
                QComboBox::drop-down { border: none; }
            """)

        row2.addWidget(self.cmb_type, stretch=1)
        row2.addWidget(self.cmb_active, stretch=1)
        tb.addLayout(row2)

        root.addWidget(toolbar)

        # الجدول
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["الكود", "الاسم", "الهاتف", "المدينة", "الطلبات"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget {
                border: none; background: white;
                alternate-background-color: #fafbff;
                font-size: 12px; outline: none;
            }
            QTableWidget::item { padding: 6px 10px; }
            QTableWidget::item:selected { background: #dbeafe; color: #1e40af; }
            QHeaderView::section {
                background: #f8f9fb; color: #6b7280;
                font-size: 11px; font-weight: bold;
                padding: 6px 10px; border: none;
                border-bottom: 2px solid #e5e9f0;
                border-right: 1px solid #e5e9f0;
            }
        """)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.itemSelectionChanged.connect(self._on_select)
        self.table.doubleClicked.connect(self._on_select)
        root.addWidget(self.table, stretch=1)

        # شريط الحالة
        self._status_bar = QLabel("")
        self._status_bar.setAlignment(Qt.AlignCenter)
        self._status_bar.setStyleSheet("""
            background: #f8f9fb; color: #6b7280;
            font-size: 10px; padding: 5px;
            border-top: 1px solid #e5e9f0;
        """)
        root.addWidget(self._status_bar)

    def _load(self):
        self._all_rows = fetch_all_customers(self.conn)
        self._apply_filter()

    def _apply_filter(self):
        q      = self.inp_search.text().strip().lower()
        typ    = self.cmb_type.currentData()
        active = self.cmb_active.currentData()

        filtered = []
        for r in self._all_rows:
            if typ is not None and r["customer_type"] != typ:
                continue
            if active is not None and r["is_active"] != active:
                continue
            if q:
                name  = (r["name"] or "").lower()
                phone = (r["phone"] or "").lower()
                code  = (r["code"] or "").lower()
                if q not in name and q not in phone and q not in code:
                    continue
            filtered.append(r)

        self.table.setRowCount(0)
        for row in filtered:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, 40)

            code_item = QTableWidgetItem(row["code"] or "")
            code_item.setData(Qt.UserRole, row["id"])
            self.table.setItem(r, 0, code_item)

            name_item = QTableWidgetItem(row["name"])
            if not row["is_active"]:
                name_item.setForeground(QColor("#9ca3af"))
            f = QFont()
            f.setWeight(QFont.Medium)
            name_item.setFont(f)
            self.table.setItem(r, 1, name_item)

            self.table.setItem(r, 2, QTableWidgetItem(row["phone"] or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(row["city"] or "—"))
            self.table.setItem(r, 4, QTableWidgetItem(str(row["orders_count"] or 0)))

        cnt = len(filtered)
        total = len(self._all_rows)
        self._status_bar.setText(
            f"{cnt} عميل" if cnt == total else f"{cnt} من {total} عميل"
        )

    def _on_select(self):
        row = self.table.currentRow()
        if row < 0:
            return
        item = self.table.item(row, 0)
        if item:
            self.customer_selected.emit(item.data(Qt.UserRole))

    def select_customer(self, cid: int):
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item and item.data(Qt.UserRole) == cid:
                self.table.selectRow(r)
                break

    def refresh(self):
        self._load()


# ══════════════════════════════════════════════════════════
# لوحة تفاصيل العميل (يمين)
# ══════════════════════════════════════════════════════════

def _stat_card(title, value="─", color="#1565c0"):
    frame = QFrame()
    frame.setStyleSheet("""
        QFrame {
            background: white;
            border: 1px solid #e5e9f0;
            border-radius: 8px;
        }
    """)
    from PyQt5.QtWidgets import QVBoxLayout
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(12, 8, 12, 8)
    lay.setSpacing(2)
    lt = QLabel(title)
    lt.setStyleSheet("font-size:10px; color:#9ba5be; background:transparent; border:none;")
    lv = QLabel(value)
    lv.setStyleSheet(
        f"font-size:14px; font-weight:bold; color:{color};"
        "background:transparent; border:none;"
    )
    lv.setAlignment(Qt.AlignCenter)
    lay.addWidget(lt)
    lay.addWidget(lv)
    return frame, lv


class _CustomerDetailPanel(QWidget):
    edited  = pyqtSignal(int)
    deleted = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._customer_id = None
        self._build()
        self._show_empty()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ──────────────────────────────────────────
        self._hdr = QFrame()
        self._hdr.setStyleSheet("""
            QFrame { background: white; border-bottom: 1px solid #e5e9f0; }
        """)
        hdr_lay = QVBoxLayout(self._hdr)
        hdr_lay.setContentsMargins(18, 14, 18, 14)
        hdr_lay.setSpacing(10)

        title_row = QHBoxLayout()
        self._lbl_name = QLabel("")
        f = QFont()
        f.setPointSize(13)
        f.setBold(True)
        self._lbl_name.setFont(f)
        self._lbl_name.setStyleSheet("color:#1a2035; background:transparent;")

        self._lbl_type = QLabel("")
        self._lbl_type.setStyleSheet("""
            font-size:11px; font-weight:bold; padding:3px 10px;
            border-radius:10px; background:#e8f0fe; color:#1565c0;
        """)

        self._lbl_code = QLabel("")
        self._lbl_code.setStyleSheet(
            "color:#9ba5be; font-size:11px; background:transparent;"
        )

        title_row.addWidget(self._lbl_name)
        title_row.addWidget(self._lbl_type)
        title_row.addStretch()
        title_row.addWidget(self._lbl_code)
        hdr_lay.addLayout(title_row)

        # معلومات الاتصال
        self._lbl_contact = QLabel("")
        self._lbl_contact.setStyleSheet(
            "color:#5a6680; font-size:12px; background:transparent;"
        )
        hdr_lay.addWidget(self._lbl_contact)

        # بطاقات الإحصائيات
        stats_row = QHBoxLayout()
        stats_row.setSpacing(8)
        f1, self._lbl_total_orders  = _stat_card("إجمالي الطلبات",    color="#1565c0")
        f2, self._lbl_active_orders = _stat_card("طلبات جارية",       color="#8b5cf6")
        f3, self._lbl_total_value   = _stat_card("إجمالي القيمة",     color="#10b981")
        f4, self._lbl_balance       = _stat_card("المتبقي",           color="#ef4444")
        for ff in (f1, f2, f3, f4):
            stats_row.addWidget(ff, stretch=1)
        hdr_lay.addLayout(stats_row)

        # أزرار الإجراءات
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        self.btn_edit = QPushButton("✏️  تعديل")
        self.btn_del  = QPushButton("🗑️  حذف")
        self.btn_toggle = QPushButton("⏸  تعطيل")

        for btn in (self.btn_edit, self.btn_del, self.btn_toggle):
            btn.setMinimumHeight(32)
            btn.setStyleSheet("""
                QPushButton {
                    background: #f8f9fb; color: #374151;
                    border: 1px solid #cdd3e0; border-radius: 6px;
                    padding: 0 12px; font-size: 12px;
                }
                QPushButton:hover { background: #dbeafe; color: #1565c0; }
            """)

        self.btn_del.setStyleSheet("""
            QPushButton {
                background: #fef2f2; color: #dc2626;
                border: 1px solid #fecaca; border-radius: 6px;
                padding: 0 12px; font-size: 12px;
            }
            QPushButton:hover { background: #fee2e2; }
        """)

        self.btn_edit.clicked.connect(self._edit)
        self.btn_del.clicked.connect(self._delete)
        self.btn_toggle.clicked.connect(self._toggle_active)

        btn_row.addWidget(self.btn_edit)
        btn_row.addWidget(self.btn_toggle)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_del)
        hdr_lay.addLayout(btn_row)

        root.addWidget(self._hdr)

        # ── محتوى قابل للتمرير ─────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: #f8f9fb; }
            QScrollBar:vertical {
                background: #f0f0f0; width: 5px; border-radius: 2px;
            }
            QScrollBar::handle:vertical {
                background: #cdd3e0; border-radius: 2px; min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
        """)

        content = QWidget()
        content.setStyleSheet("background:#f8f9fb;")
        self._content_lay = QVBoxLayout(content)
        self._content_lay.setContentsMargins(18, 14, 18, 14)
        self._content_lay.setSpacing(14)

        # جهات الاتصال
        self._lbl_contacts_hdr = QLabel("📞  جهات الاتصال")
        self._lbl_contacts_hdr.setStyleSheet(
            "font-size:12px; font-weight:bold; color:#374151; background:transparent;"
        )
        self._content_lay.addWidget(self._lbl_contacts_hdr)

        self.contacts_table = QTableWidget()
        self.contacts_table.setColumnCount(4)
        self.contacts_table.setHorizontalHeaderLabels(
            ["الاسم", "الصفة", "الهاتف", "الإيميل"]
        )
        self.contacts_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.contacts_table.verticalHeader().setVisible(False)
        self.contacts_table.setMaximumHeight(140)
        self.contacts_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e5e9f0; border-radius: 8px;
                background: white; font-size: 11px; outline: none;
            }
            QTableWidget::item { padding: 5px 8px; }
            QHeaderView::section {
                background: #f8f9fb; color: #6b7280;
                font-size: 10px; font-weight: bold;
                padding: 5px 8px; border: none;
                border-bottom: 1px solid #e5e9f0;
            }
        """)
        hh = self.contacts_table.horizontalHeader()
        for i in range(4):
            hh.setSectionResizeMode(i, QHeaderView.Stretch)
        hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._content_lay.addWidget(self.contacts_table)

        # آخر الطلبات
        self._lbl_orders_hdr = QLabel("📋  آخر الطلبات")
        self._lbl_orders_hdr.setStyleSheet(
            "font-size:12px; font-weight:bold; color:#374151; background:transparent;"
        )
        self._content_lay.addWidget(self._lbl_orders_hdr)

        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(5)
        self.orders_table.setHorizontalHeaderLabels(
            ["رقم الطلب", "الحالة", "الأولوية", "الإجمالي", "التاريخ"]
        )
        self.orders_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.orders_table.verticalHeader().setVisible(False)
        self.orders_table.setMaximumHeight(200)
        self.orders_table.setStyleSheet(self.contacts_table.styleSheet())
        hh2 = self.orders_table.horizontalHeader()
        hh2.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh2.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh2.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh2.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh2.setSectionResizeMode(4, QHeaderView.Stretch)
        hh2.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._content_lay.addWidget(self.orders_table)

        self._content_lay.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, stretch=1)

        # حالة فارغة
        self._empty = QFrame()
        self._empty.setStyleSheet("background:#f8f9fb; border:none;")
        e_lay = QVBoxLayout(self._empty)
        e_lay.setAlignment(Qt.AlignCenter)
        for text, style in [
            ("👤", "font-size:48px; background:transparent;"),
            ("اختر عميلاً من القائمة أو أضف عميلاً جديداً",
             "font-size:13px; color:#6b7280; background:transparent;"),
        ]:
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(style)
            e_lay.addWidget(lbl)
        root.addWidget(self._empty)

    # ── API ────────────────────────────────────────────────

    def load_customer(self, cid: int):
        self._customer_id = cid
        c = fetch_customer(self.conn, cid)
        if not c:
            return
        self._show_detail()

        type_map = {"individual": "فرد", "company": "شركة"}
        self._lbl_name.setText(c["name"])
        self._lbl_code.setText(c["code"] or "")
        self._lbl_type.setText(type_map.get(c["customer_type"], ""))

        parts = []
        if c["phone"]:  parts.append(f"📞 {c['phone']}")
        if c["city"]:   parts.append(f"📍 {c['city']}")
        if c["email"]:  parts.append(f"✉️ {c['email']}")
        self._lbl_contact.setText("   |   ".join(parts) if parts else "")

        # إحصائيات
        stats = fetch_customer_stats(self.conn, cid)
        self._lbl_total_orders.setText(str(stats.get("total_orders") or 0))
        self._lbl_active_orders.setText(str(stats.get("active") or 0))
        self._lbl_total_value.setText(f"{(stats.get('total_value') or 0):,.0f} ج")
        balance = (stats.get("total_value") or 0) - (stats.get("total_paid") or 0)
        self._lbl_balance.setText(f"{balance:,.0f} ج")

        # حالة التفعيل
        self.btn_toggle.setText("✅  تفعيل" if not c["is_active"] else "⏸  تعطيل")

        # جهات الاتصال
        contacts = fetch_contacts(self.conn, cid)
        self.contacts_table.setRowCount(0)
        for ct in contacts:
            r = self.contacts_table.rowCount()
            self.contacts_table.insertRow(r)
            self.contacts_table.setRowHeight(r, 36)
            self.contacts_table.setItem(r, 0, QTableWidgetItem(ct["name"]))
            self.contacts_table.setItem(r, 1, QTableWidgetItem(ct["role"] or ""))
            self.contacts_table.setItem(r, 2, QTableWidgetItem(ct["phone"] or ""))
            self.contacts_table.setItem(r, 3, QTableWidgetItem(ct["email"] or ""))

        if not contacts:
            self._lbl_contacts_hdr.setVisible(False)
            self.contacts_table.setVisible(False)
        else:
            self._lbl_contacts_hdr.setVisible(True)
            self.contacts_table.setVisible(True)

        # آخر الطلبات
        STATUS_MAP = {
            "pending": "⏳ انتظار", "confirmed": "✅ مؤكد",
            "in_progress": "🔧 تنفيذ", "ready": "📦 جاهز",
            "delivered": "🚚 مُسلَّم", "cancelled": "❌ ملغي",
            "on_hold": "⏸ معلق",
        }
        PRIORITY_MAP = {
            "low": "⬇ منخفض", "normal": "➡ عادي",
            "high": "⬆ عالي", "urgent": "🔴 عاجل",
        }
        orders = fetch_customer_orders(self.conn, cid)
        self.orders_table.setRowCount(0)
        for o in orders[:20]:
            r = self.orders_table.rowCount()
            self.orders_table.insertRow(r)
            self.orders_table.setRowHeight(r, 36)
            self.orders_table.setItem(r, 0, QTableWidgetItem(o["order_number"]))
            self.orders_table.setItem(r, 1, QTableWidgetItem(
                STATUS_MAP.get(o["status"], o["status"])
            ))
            self.orders_table.setItem(r, 2, QTableWidgetItem(
                PRIORITY_MAP.get(o["priority"], "")
            ))
            self.orders_table.setItem(r, 3, QTableWidgetItem(
                f"{(o['net_amount'] or 0):,.2f} ج"
            ))
            self.orders_table.setItem(r, 4, QTableWidgetItem(o["order_date"] or ""))

    def _show_empty(self):
        self._empty.setVisible(True)
        self._hdr.setVisible(False)

    def _show_detail(self):
        self._empty.setVisible(False)
        self._hdr.setVisible(True)

    def _edit(self):
        if not self._customer_id:
            return
        dlg = _CustomerForm(self.conn, customer_id=self._customer_id, parent=self)
        dlg.saved.connect(lambda cid: (self.load_customer(cid), self.edited.emit(cid)))
        dlg.exec_()

    def _delete(self):
        if not self._customer_id:
            return
        c = fetch_customer(self.conn, self._customer_id)
        if not c:
            return
        if QMessageBox.question(
            self, "تأكيد الحذف",
            f"حذف العميل «{c['name']}» نهائياً؟\n"
            "لا يمكن حذف عميل له طلبات مسجلة.",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            if delete_customer(self.conn, self._customer_id):
                self._customer_id = None
                self._show_empty()
                self.deleted.emit()
            else:
                QMessageBox.warning(
                    self, "تعذر الحذف",
                    "لا يمكن حذف هذا العميل لوجود طلبات مرتبطة به.\n"
                    "يمكنك تعطيله بدلاً من الحذف."
                )

    def _toggle_active(self):
        if not self._customer_id:
            return
        toggle_customer_active(self.conn, self._customer_id)
        self.load_customer(self._customer_id)
        self.edited.emit(self._customer_id)


# ══════════════════════════════════════════════════════════
# تبويب العملاء الرئيسي
# ══════════════════════════════════════════════════════════

class CustomersTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(4)
        splitter.setStyleSheet("""
            QSplitter::handle { background: #e5e9f0; }
            QSplitter::handle:hover { background: #bfdbfe; }
        """)

        self._list   = _CustomersListPanel(self.conn)
        self._detail = _CustomerDetailPanel(self.conn)

        splitter.addWidget(self._list)
        splitter.addWidget(self._detail)
        splitter.setSizes([380, 680])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        root.addWidget(splitter)

        self._list.customer_selected.connect(self._detail.load_customer)
        self._list.new_customer.connect(self._new_customer)
        self._detail.edited.connect(lambda _: self._list.refresh())
        self._detail.deleted.connect(self._list.refresh)

    def _new_customer(self):
        dlg = _CustomerForm(self.conn, parent=self)
        dlg.saved.connect(self._on_saved)
        dlg.exec_()

    def _on_saved(self, cid: int):
        self._list.refresh()
        self._list.select_customer(cid)
        self._detail.load_customer(cid)

    def refresh(self):
        self._list.refresh()