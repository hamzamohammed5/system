"""
ui/tabs/orders/customers/customer_detail_panel.py
==================================================
لوحة تفاصيل العميل — ترث من BaseDetailPanel.
"""

from PyQt5.QtWidgets import QMessageBox, QVBoxLayout
from PyQt5.QtCore    import Qt, pyqtSignal

from db.orders.customers_repo import (
    fetch_customer, delete_customer, toggle_customer_active,
    fetch_customer_stats, fetch_contacts,
)
from db.orders.orders_repo import fetch_customer_orders

from ui.tabs.orders._customer_form import _CustomerForm
from ui.widgets.shared.base_detail_panel import BaseDetailPanel
from ui.widgets.shared.table_utils import (
    make_splitter_table_guarded, fit_splitter_table,
    make_compact_table,
    make_table_item, color_item, bold_item, muted_item,
    insert_row, auto_fit_columns,
    ROW_HEIGHT_COMPACT,
)
from ui.widgets.shared.panels import SectionHeader, _make_btn
from ui.app_settings import _C

_BLUE = _C['accent']

STATUS_MAP = {
    "pending":     "⏳ انتظار",
    "confirmed":   "✅ مؤكد",
    "in_progress": "🔧 تنفيذ",
    "ready":       "📦 جاهز",
    "delivered":   "🚚 مُسلَّم",
    "cancelled":   "❌ ملغي",
    "on_hold":     "⏸ معلق",
}
PRIORITY_MAP = {
    "low":    "⬇ منخفض",
    "normal": "➡ عادي",
    "high":   "⬆ عالي",
    "urgent": "🔴 عاجل",
}


class CustomerDetailPanel(BaseDetailPanel):
    edited  = pyqtSignal(int)
    deleted = pyqtSignal()

    EMPTY_ICON     = "👤"
    EMPTY_TITLE    = "اختر عميلاً من القائمة"
    EMPTY_SUBTITLE = "أو أضف عميلاً جديداً بالضغط على ＋"

    def __init__(self, conn, parent=None):
        super().__init__(conn=conn, parent=parent)

    def _build_header_cards(self):
        self._card_total_orders  = self._hdr.add_stat_card("📋", "إجمالي الطلبات", color=_BLUE)
        self._card_active_orders = self._hdr.add_stat_card("🔧", "طلبات جارية",    color="#8b5cf6")
        self._card_total_value   = self._hdr.add_stat_card("💰", "إجمالي القيمة",  color="#10b981")
        self._card_balance       = self._hdr.add_stat_card("⚖️", "المتبقي",         color="#ef4444")

    def _build_header_buttons(self):
        self.btn_edit   = self._hdr.toolbar.add_action("✏️  تعديل",  "primary")
        self.btn_toggle = self._hdr.toolbar.add_action("⏸  تعطيل",  "ghost")
        self.btn_del    = self._hdr.toolbar.add_danger("🗑️  حذف")

        self.btn_edit.clicked.connect(self._edit)
        self.btn_toggle.clicked.connect(self._toggle_active)
        self.btn_del.clicked.connect(self._delete)

    def _build_content(self, lay: QVBoxLayout):
        # ── جهات الاتصال ──
        self._contacts_hdr = SectionHeader("📞  جهات الاتصال")
        lay.addWidget(self._contacts_hdr)

        self.contacts_table = make_compact_table(
            columns=["الاسم", "الصفة", "الهاتف", "الإيميل"],
            stretch_col=0,
            col_widths={1: 80, 2: 100, 3: 120},
            max_height=140,
        )
        lay.addWidget(self.contacts_table)

        # ── آخر الطلبات (splitter + guard) ──
        self._orders_hdr = SectionHeader("📋  آخر الطلبات")
        lay.addWidget(self._orders_hdr)

        splitter, table, guard = make_splitter_table_guarded(
            columns=["رقم الطلب", "الحالة", "الأولوية", "الإجمالي", "التاريخ"],
            stretch_col=0,
            col_widths={1: 90, 2: 70, 3: 80, 4: 90},
            max_height=220,
            variant="compact",
            row_height=ROW_HEIGHT_COMPACT,
        )
        self.orders_table     = table
        self._orders_splitter = splitter
        self._orders_guard    = guard          # ← احتفظ بيه
        lay.addWidget(splitter)

    def _load_data(self, item_id: int):
        return fetch_customer(self.conn, item_id)

    def _fill_data(self, data: dict):
        c = data
        type_map = {"individual": "فرد", "company": "🏢 شركة"}
        self._hdr.set_title(c["name"])
        self._hdr.set_type_badge(type_map.get(c["customer_type"], ""))
        self._hdr.set_status_badge(
            c["code"] or "", text_color=_C['text_muted'],
            bg="transparent", border="transparent")

        parts = []
        if c.get("phone"):  parts.append(f"📞 {c['phone']}")
        if c.get("city"):   parts.append(f"📍 {c['city']}")
        if c.get("email"):  parts.append(f"✉️ {c['email']}")
        self._hdr.set_info(parts)

        stats = fetch_customer_stats(self.conn, self._item_id)
        self._card_total_orders.set_value(str(stats.get("total_orders") or 0))
        self._card_active_orders.set_value(str(stats.get("active") or 0))
        self._card_total_value.set_value(f"{(stats.get('total_value') or 0):,.0f} ج")
        balance = (stats.get("total_value") or 0) - (stats.get("total_paid") or 0)
        self._card_balance.set_value(f"{balance:,.0f} ج")
        self._card_balance.set_color("#ef4444" if balance > 0 else "#10b981")

        self.btn_toggle.setText("✅  تفعيل" if not c["is_active"] else "⏸  تعطيل")

        # ── جهات الاتصال ──
        contacts = [dict(ct) for ct in fetch_contacts(self.conn, self._item_id)]
        self.contacts_table.setRowCount(0)
        for ct in contacts:
            r = insert_row(self.contacts_table, ROW_HEIGHT_COMPACT)
            self.contacts_table.setItem(r, 0, bold_item(make_table_item(ct["name"])))
            self.contacts_table.setItem(r, 1, muted_item(make_table_item(ct.get("role") or "")))
            self.contacts_table.setItem(r, 2, make_table_item(ct.get("phone") or ""))
            self.contacts_table.setItem(r, 3, muted_item(make_table_item(ct.get("email") or "")))

        self._contacts_hdr.setVisible(bool(contacts))
        self.contacts_table.setVisible(bool(contacts))

        # ── آخر الطلبات ──
        orders = fetch_customer_orders(self.conn, self._item_id)
        table  = self.orders_table
        table.setRowCount(0)

        for o in orders[:20]:
            r = insert_row(table, ROW_HEIGHT_COMPACT)
            num_item = make_table_item(o["order_number"])
            bold_item(num_item, also_medium=True)
            color_item(num_item, _BLUE)
            table.setItem(r, 0, num_item)
            table.setItem(r, 1,
                make_table_item(STATUS_MAP.get(o["status"], o["status"])))
            table.setItem(r, 2, muted_item(
                make_table_item(PRIORITY_MAP.get(o["priority"], ""))))
            val_item = make_table_item(f"{(o['net_amount'] or 0):,.2f} ج",
                                       align=Qt.AlignCenter)
            color_item(val_item, _BLUE)
            table.setItem(r, 3, val_item)
            table.setItem(r, 4, muted_item(
                make_table_item(o["order_date"] or "")))

        if orders:
            auto_fit_columns(table, fixed_cols=[1, 2, 3, 4],
                             stretch_col=0, min_width=55, max_width=160)
            fit_splitter_table(self._orders_splitter, table)
            self._orders_guard.refresh()       # ← تحديث الـ guard

    def load_customer(self, cid: int):
        self.load_item(cid)

    def _edit(self):
        if not self._item_id:
            return
        dlg = _CustomerForm(self.conn, customer_id=self._item_id, parent=self)
        dlg.saved.connect(lambda cid: (self.load_customer(cid), self.edited.emit(cid)))
        dlg.exec_()

    def _delete(self):
        if not self._item_id:
            return
        c = self._item_data
        if not c:
            return
        if QMessageBox.question(
            self, "تأكيد الحذف",
            f"حذف العميل «{c['name']}» نهائياً؟\n"
            "لا يمكن حذف عميل له طلبات مسجلة.",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            if delete_customer(self.conn, self._item_id):
                self._item_id = None
                self._show_empty()
                self.deleted.emit()
            else:
                QMessageBox.warning(self, "تعذر الحذف",
                    "لا يمكن حذف هذا العميل لوجود طلبات مرتبطة به.\n"
                    "يمكنك تعطيله بدلاً من الحذف.")

    def _toggle_active(self):
        if not self._item_id:
            return
        toggle_customer_active(self.conn, self._item_id)
        self.load_customer(self._item_id)
        self.edited.emit(self._item_id)