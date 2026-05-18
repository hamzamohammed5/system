"""
ui/tabs/orders/customers/customer_detail_panel.py
==================================================
لوحة تفاصيل العميل — منقولة من customers_tab.py
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal

from db.orders.customers_repo import (
    fetch_customer, delete_customer, toggle_customer_active,
    fetch_customer_stats, fetch_contacts,
)
from db.orders.orders_repo import fetch_customer_orders

from ui.tabs.orders._customer_form import _CustomerForm

from ui.widgets.shared.panels import DetailHeader, EmptyState
from ui.widgets.shared.table_utils import (
    make_compact_table, make_table_item,
    color_item, bold_item, muted_item,
    insert_row, auto_fit_columns,
    ROW_HEIGHT_COMPACT,
)
from ui.helpers import SCROLL_SS
from ui.app_settings import _C

_BG    = "#f8f9fb"
_WHITE = "#ffffff"
_BLUE  = "#1565c0"

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


class CustomerDetailPanel(QWidget):
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

        # ── Header ──
        self._hdr = DetailHeader()
        self._card_total_orders  = self._hdr.add_stat_card("📋", "إجمالي الطلبات", color=_BLUE)
        self._card_active_orders = self._hdr.add_stat_card("🔧", "طلبات جارية",    color="#8b5cf6")
        self._card_total_value   = self._hdr.add_stat_card("💰", "إجمالي القيمة",  color="#10b981")
        self._card_balance       = self._hdr.add_stat_card("⚖️", "المتبقي",         color="#ef4444")

        self.btn_edit   = self._hdr.toolbar.add_action("✏️  تعديل",  "primary", self._edit)
        self.btn_toggle = self._hdr.toolbar.add_action("⏸  تعطيل",  "ghost",   self._toggle_active)
        self.btn_del    = self._hdr.toolbar.add_danger("🗑️  حذف",               self._delete)
        root.addWidget(self._hdr)

        # ── المحتوى ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(SCROLL_SS)

        content = QWidget()
        content.setStyleSheet(f"background:{_BG};")
        self._content_lay = QVBoxLayout(content)
        self._content_lay.setContentsMargins(16, 12, 16, 12)
        self._content_lay.setSpacing(10)

        self._lbl_contacts_hdr = self._make_section_label("📞  جهات الاتصال")
        self._content_lay.addWidget(self._lbl_contacts_hdr)

        self.contacts_table = make_compact_table(
            columns=["الاسم", "الصفة", "الهاتف", "الإيميل"],
            stretch_col=0, col_widths={1: 80, 2: 100, 3: 120}, max_height=140)
        self._content_lay.addWidget(self.contacts_table)

        self._lbl_orders_hdr = self._make_section_label("📋  آخر الطلبات")
        self._content_lay.addWidget(self._lbl_orders_hdr)

        self.orders_table = make_compact_table(
            columns=["رقم الطلب", "الحالة", "الأولوية", "الإجمالي", "التاريخ"],
            stretch_col=0, col_widths={1: 90, 2: 70, 3: 80, 4: 90}, max_height=220)
        self._content_lay.addWidget(self.orders_table)
        self._content_lay.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll, stretch=1)

        # ── حالة فارغة ──
        self._empty = EmptyState(
            icon="👤", title="اختر عميلاً من القائمة",
            subtitle="أو أضف عميلاً جديداً بالضغط على ＋",
            style="plain", color="#6b7280", min_height=200)
        root.addWidget(self._empty)

    def _make_section_label(self, text: str):
        from PyQt5.QtWidgets import QLabel
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"font-weight:bold; color:{_C['text_sec']}; background:transparent;")
        return lbl

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
            c["code"] or "", text_color="#6b7280",
            bg="transparent", border="transparent")

        parts = []
        if c.get("phone"):  parts.append(f"📞 {c['phone']}")
        if c.get("city"):   parts.append(f"📍 {c['city']}")
        if c.get("email"):  parts.append(f"✉️ {c['email']}")
        self._hdr.set_info(parts)

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
            self.orders_table.setItem(r, 1,
                make_table_item(STATUS_MAP.get(o["status"], o["status"])))
            self.orders_table.setItem(r, 2, muted_item(
                make_table_item(PRIORITY_MAP.get(o["priority"], ""))))
            val_item = make_table_item(f"{(o['net_amount'] or 0):,.2f} ج",
                                       align=Qt.AlignCenter)
            color_item(val_item, _BLUE)
            self.orders_table.setItem(r, 3, val_item)
            self.orders_table.setItem(r, 4, muted_item(
                make_table_item(o["order_date"] or "")))

        if orders:
            auto_fit_columns(self.orders_table, fixed_cols=[1, 2, 3, 4],
                             stretch_col=0, min_width=55, max_width=160)

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
                QMessageBox.warning(self, "تعذر الحذف",
                    "لا يمكن حذف هذا العميل لوجود طلبات مرتبطة به.\n"
                    "يمكنك تعطيله بدلاً من الحذف.")

    def _toggle_active(self):
        if not self._customer_id:
            return
        toggle_customer_active(self.conn, self._customer_id)
        self.load_customer(self._customer_id)
        self.edited.emit(self._customer_id)