"""
ui/tabs/orders/customers_tab.py  — نسخة محسّنة v2
================================
تبويب إدارة العملاء باستخدام المكونات المشتركة:
  - DetailHeader  من panels.py
  - EmptyState    من panels.py
  - make_compact_table من table_utils.py
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

# مكونات مشتركة
from ui.widgets.shared.panels import (
    DetailHeader, EmptyState, StatCard,
)
from ui.widgets.shared.table_utils import (
    make_compact_table, make_table_item,
    color_item, bold_item, muted_item,
    insert_row, ROW_HEIGHT_COMPACT, ROW_HEIGHT_NORMAL, ROW_HEIGHT_LARGE,
)
from ui.app_settings import _C

# ── ثوابت ──
_BG     = "#f8f9fb"
_WHITE  = "#ffffff"
_BLUE   = "#1565c0"
_BORDER = "#e5e9f0"

_COMBO_SS = f"""
    QComboBox {{
        background: {_BG}; border: 1px solid #cdd3e0;
        border-radius: 5px; padding: 0 8px; min-height: 28px;
    }}
    QComboBox:focus {{ border-color: {_BLUE}; }}
    QComboBox::drop-down {{ border: none; }}
"""

STATUS_MAP = {
    "pending":     "⏳ انتظار",  "confirmed":   "✅ مؤكد",
    "in_progress": "🔧 تنفيذ",  "ready":       "📦 جاهز",
    "delivered":   "🚚 مُسلَّم", "cancelled":   "❌ ملغي",
    "on_hold":     "⏸ معلق",
}
PRIORITY_MAP = {
    "low":    "⬇ منخفض", "normal": "➡ عادي",
    "high":   "⬆ عالي",  "urgent": "🔴 عاجل",
}


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

        # ── شريط الأدوات ──
        toolbar = QFrame()
        toolbar.setStyleSheet(f"""
            QFrame {{ background: {_WHITE}; border-bottom: 1px solid {_BORDER}; }}
        """)
        tb = QVBoxLayout(toolbar)
        tb.setContentsMargins(10, 10, 10, 10)
        tb.setSpacing(6)

        # صف البحث + زر جديد
        row1 = QHBoxLayout()
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("بحث بالاسم أو الهاتف أو الكود...")
        self.inp_search.setMinimumHeight(34)
        self.inp_search.setStyleSheet(f"""
            QLineEdit {{
                background: {_BG}; border: 1px solid #cdd3e0;
                border-radius: 6px; padding: 0 10px; font-size: 12px;
            }}
            QLineEdit:focus {{ border-color: {_BLUE}; background: {_WHITE}; }}
        """)
        self.inp_search.textChanged.connect(lambda: self._timer.start())

        btn_new = QPushButton("＋  عميل جديد")
        btn_new.setMinimumHeight(34)
        btn_new.setStyleSheet(f"""
            QPushButton {{
                background: {_BLUE}; color: white;
                border: none; border-radius: 6px;
                padding: 0 14px; font-weight: bold; font-size: 12px;
            }}
            QPushButton:hover {{ background: #0d47a1; }}
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
        self.cmb_type.setStyleSheet(_COMBO_SS)
        self.cmb_type.currentIndexChanged.connect(self._apply_filter)

        self.cmb_active = QComboBox()
        self.cmb_active.setMinimumHeight(28)
        self.cmb_active.addItem("الكل", None)
        self.cmb_active.addItem("نشط", 1)
        self.cmb_active.addItem("غير نشط", 0)
        self.cmb_active.setStyleSheet(_COMBO_SS)
        self.cmb_active.currentIndexChanged.connect(self._apply_filter)

        row2.addWidget(self.cmb_type, stretch=1)
        row2.addWidget(self.cmb_active, stretch=1)
        tb.addLayout(row2)
        root.addWidget(toolbar)

        # ── الجدول ──
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["الكود", "الاسم", "الهاتف", "المدينة", "الطلبات"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: none; background: {_WHITE};
                alternate-background-color: #fafbff; outline: none;
            }}
            QTableWidget::item {{ padding: 6px 10px; border-bottom: 1px solid {_BORDER}; }}
            QTableWidget::item:selected {{ background: #dbeafe; color: #1e40af; }}
            QHeaderView::section {{
                background: {_BG}; color: {_BLUE}; font-weight: bold; font-size:11px;
                padding: 6px 10px; border: none; border-bottom: 2px solid {_BORDER};
            }}
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
        self._status_bar.setStyleSheet(f"""
            background: {_BG}; color: #6b7280;
            padding: 5px; font-size: 11px;
            border-top: 1px solid {_BORDER};
        """)
        root.addWidget(self._status_bar)

    def _load(self):
        self._all_rows = fetch_all_customers(self.conn)
        self._apply_filter()

    def _apply_filter(self):
        q      = self.inp_search.text().strip().lower()
        typ    = self.cmb_type.currentData()
        active = self.cmb_active.currentData()

        filtered = [
            r for r in self._all_rows
            if (typ is None or r["customer_type"] == typ)
            and (active is None or r["is_active"] == active)
            and (not q or q in (r["name"] or "").lower()
                      or q in (r["phone"] or "").lower()
                      or q in (r["code"] or "").lower())
        ]

        self.table.setRowCount(0)
        for row in filtered:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, ROW_HEIGHT_LARGE)

            code_item = make_table_item(row["code"] or "", user_data=row["id"])
            muted_item(code_item)
            self.table.setItem(r, 0, code_item)

            name_item = make_table_item(row["name"])
            if not row["is_active"]:
                color_item(name_item, "#9ca3af")
            else:
                bold_item(name_item, also_medium=True)
            self.table.setItem(r, 1, name_item)

            self.table.setItem(r, 2, muted_item(make_table_item(row["phone"] or "—")))
            self.table.setItem(r, 3, muted_item(make_table_item(row["city"] or "—")))
            cnt_item = make_table_item(str(row["orders_count"] or 0), align=Qt.AlignCenter)
            color_item(cnt_item, _BLUE)
            self.table.setItem(r, 4, cnt_item)

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

class _CustomerDetailPanel(QWidget):
    edited  = pyqtSignal(int)
    deleted = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn         = conn
        self._customer_id = None
        self._build()
        self._show_empty()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header موحد ──
        self._hdr = DetailHeader()

        # بطاقات إحصائيات العميل
        self._card_total_orders  = self._hdr.add_stat_card("📋", "إجمالي الطلبات", color=_BLUE)
        self._card_active_orders = self._hdr.add_stat_card("🔧", "طلبات جارية",    color="#8b5cf6")
        self._card_total_value   = self._hdr.add_stat_card("💰", "إجمالي القيمة",  color="#10b981")
        self._card_balance       = self._hdr.add_stat_card("⚖️", "المتبقي",         color="#ef4444")

        # أزرار
        self.btn_edit   = self._hdr.toolbar.add_action("✏️  تعديل",  "primary", self._edit)
        self.btn_toggle = self._hdr.toolbar.add_action("⏸  تعطيل",  "ghost",   self._toggle_active)
        self.btn_del    = self._hdr.toolbar.add_danger("🗑️  حذف",               self._delete)

        root.addWidget(self._hdr)

        # ── محتوى قابل للتمرير ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: {_BG}; }}
            QScrollBar:vertical {{
                background: #f0f0f0; width: 5px; border-radius: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: #cdd3e0; border-radius: 2px; min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
        """)

        content = QWidget()
        content.setStyleSheet(f"background:{_BG};")
        self._content_lay = QVBoxLayout(content)
        self._content_lay.setContentsMargins(16, 12, 16, 12)
        self._content_lay.setSpacing(10)

        # جهات الاتصال
        self._lbl_contacts_hdr = QLabel("📞  جهات الاتصال")
        self._lbl_contacts_hdr.setStyleSheet(
            f"font-weight:bold; color:{_C['text_sec']}; background:transparent;"
        )
        self._content_lay.addWidget(self._lbl_contacts_hdr)

        self.contacts_table = make_compact_table(
            columns=["الاسم", "الصفة", "الهاتف", "الإيميل"],
            stretch_col=0,
            col_widths={1: 80, 2: 100, 3: 120},
            max_height=140,
        )
        self._content_lay.addWidget(self.contacts_table)

        # آخر الطلبات
        self._lbl_orders_hdr = QLabel("📋  آخر الطلبات")
        self._lbl_orders_hdr.setStyleSheet(
            f"font-weight:bold; color:{_C['text_sec']}; background:transparent;"
        )
        self._content_lay.addWidget(self._lbl_orders_hdr)

        self.orders_table = make_compact_table(
            columns=["رقم الطلب", "الحالة", "الأولوية", "الإجمالي", "التاريخ"],
            stretch_col=0,
            col_widths={1: 90, 2: 70, 3: 80, 4: 90},
            max_height=220,
        )
        self._content_lay.addWidget(self.orders_table)
        self._content_lay.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll, stretch=1)

        # حالة فارغة
        self._empty = EmptyState(
            icon="👤",
            title="اختر عميلاً من القائمة",
            subtitle="أو أضف عميلاً جديداً بالضغط على ＋",
            style="plain",
            color="#6b7280",
            min_height=200,
        )
        root.addWidget(self._empty)

    # ── API ──

    def load_customer(self, cid: int):
        self._customer_id = cid
        c = fetch_customer(self.conn, cid)
        if not c:
            return
        c = dict(c)
        self._show_detail()

        type_map = {"individual": "فرد", "company": "🏢 شركة"}
        self._hdr.set_title(c["name"])
        self._hdr.set_type_badge(type_map.get(c["customer_type"], ""))
        self._hdr.set_status_badge(
            c["code"] or "",
            text_color="#6b7280", bg="transparent", border="transparent"
        )

        parts = []
        if c.get("phone"):   parts.append(f"📞 {c['phone']}")
        if c.get("city"):    parts.append(f"📍 {c['city']}")
        if c.get("email"):   parts.append(f"✉️ {c['email']}")
        self._hdr.set_info(parts)

        # إحصائيات
        stats = fetch_customer_stats(self.conn, cid)
        self._card_total_orders.set_value(str(stats.get("total_orders") or 0))
        self._card_active_orders.set_value(str(stats.get("active") or 0))
        self._card_total_value.set_value(f"{(stats.get('total_value') or 0):,.0f} ج")
        balance = (stats.get("total_value") or 0) - (stats.get("total_paid") or 0)
        self._card_balance.set_value(f"{balance:,.0f} ج")
        self._card_balance.set_color("#ef4444" if balance > 0 else "#10b981")

        self.btn_toggle.setText("✅  تفعيل" if not c["is_active"] else "⏸  تعطيل")

        # جهات الاتصال
        contacts = [dict(ct) for ct in fetch_contacts(self.conn, cid)]

        self.contacts_table.setRowCount(0)
        for ct in contacts:
            r = insert_row(self.contacts_table, ROW_HEIGHT_COMPACT)
            bold_item(make_table_item(ct["name"]))
            self.contacts_table.setItem(r, 0, bold_item(make_table_item(ct["name"])))
            self.contacts_table.setItem(r, 1, muted_item(make_table_item(ct.get("role") or "")))
            self.contacts_table.setItem(r, 2, make_table_item(ct.get("phone") or ""))
            self.contacts_table.setItem(r, 3, muted_item(make_table_item(ct.get("email") or "")))

        self._lbl_contacts_hdr.setVisible(bool(contacts))
        self.contacts_table.setVisible(bool(contacts))

        # آخر الطلبات
        orders = fetch_customer_orders(self.conn, cid)
        self.orders_table.setRowCount(0)
        for o in orders[:20]:
            r = insert_row(self.orders_table, ROW_HEIGHT_COMPACT)
            num_item = make_table_item(o["order_number"])
            bold_item(num_item, also_medium=True)
            color_item(num_item, _BLUE)
            self.orders_table.setItem(r, 0, num_item)

            status_item = make_table_item(STATUS_MAP.get(o["status"], o["status"]))
            self.orders_table.setItem(r, 1, status_item)

            self.orders_table.setItem(r, 2, muted_item(
                make_table_item(PRIORITY_MAP.get(o["priority"], ""))
            ))

            val_item = make_table_item(f"{(o['net_amount'] or 0):,.2f} ج", align=Qt.AlignCenter)
            color_item(val_item, _BLUE)
            self.orders_table.setItem(r, 3, val_item)

            self.orders_table.setItem(r, 4, muted_item(
                make_table_item(o["order_date"] or "")
            ))

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
        splitter.setHandleWidth(3)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{ background: {_BORDER}; }}
            QSplitter::handle:hover {{ background: #bfdbfe; }}
        """)

        self._list   = _CustomersListPanel(self.conn)
        self._detail = _CustomerDetailPanel(self.conn)

        splitter.addWidget(self._list)
        splitter.addWidget(self._detail)
        splitter.setSizes([340, 760])
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