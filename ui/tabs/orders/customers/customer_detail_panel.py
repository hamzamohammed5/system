"""
ui/tabs/orders/customers/customer_detail_panel.py
==================================================
لوحة تفاصيل العميل — ترث من BaseDetailPanel.
"""

from PyQt5.QtWidgets import QMessageBox, QVBoxLayout
from PyQt5.QtCore    import Qt, pyqtSignal

from ui.constants import (
    CUSTOMER_CONTACTS_MAX_H,
    CUSTOMER_ORDERS_MAX_H,
    CUSTOMER_CONTACT_COL_ROLE_W,
    CUSTOMER_CONTACT_COL_PHONE_W,
    CUSTOMER_CONTACT_COL_EMAIL_W,
    CUSTOMER_ORDERS_COL_STATUS_W,
    CUSTOMER_ORDERS_COL_PRI_W,
    CUSTOMER_ORDERS_COL_TOTAL_W,
    CUSTOMER_ORDERS_COL_DATE_W,
)

from services.orders.customer_service import CustomerService

from ui.tabs.orders._customer_form import _CustomerForm
from ui.widgets.base.detail_panel import BaseDetailPanel
from ui.widgets.tables.tables import (
    make_table, make_compact_table, insert_row, auto_fit_columns,
    make_item, bold_item, colored_item, muted_item,
    ROW_HEIGHT_COMPACT,
)
from ui.widgets.components.headers_page import SectionHeader
from ui.widgets.components.button import make_btn
from ui.widgets.core.i18n import tr
from ui.theme import _C

from ..order_detail._status_config import get_status_labels, get_priority_labels


class CustomerDetailPanel(BaseDetailPanel):
    edited  = pyqtSignal(int)
    deleted = pyqtSignal()

    EMPTY_ICON     = "👤"
    EMPTY_TITLE    = "customer_select_first"
    EMPTY_SUBTITLE = "customer_select_subtitle"

    def __init__(self, conn, parent=None):
        super().__init__(conn=conn, parent=parent)
        self._svc = CustomerService(conn)

    def _build_header_cards(self):
        self._card_total_orders  = self._hdr.add_stat_card("📋", tr("customer_total_orders"),  color=_C['accent'])
        self._card_active_orders = self._hdr.add_stat_card("🔧", tr("customer_active_orders"), color=_C['purple'])
        self._card_total_value   = self._hdr.add_stat_card("💰", tr("customer_total_value"),   color=_C['success'])
        self._card_balance       = self._hdr.add_stat_card("⚖️", tr("customer_balance"),        color=_C['danger'])

    def _build_header_buttons(self):
        self.btn_edit   = self._hdr.toolbar.add_action(tr("order_edit_btn"),           "primary")
        self.btn_toggle = self._hdr.toolbar.add_action(tr("customer_toggle_inactive"),  "ghost")
        self.btn_del    = self._hdr.toolbar.add_danger(tr("order_delete_btn"))

        self.btn_edit.clicked.connect(self._edit)
        self.btn_toggle.clicked.connect(self._toggle_active)
        self.btn_del.clicked.connect(self._delete)

    def _build_content(self, lay: QVBoxLayout):
        # ── جهات الاتصال ──
        self._contacts_hdr = SectionHeader(tr("customer_contacts_title"))
        lay.addWidget(self._contacts_hdr)

        self.contacts_table = make_compact_table(
            columns=[
                tr("contact_name_lbl"), tr("contact_role_lbl"),
                tr("contact_phone_lbl"), tr("contact_email_lbl"),
            ],
            stretch_col=0,
            col_widths={1: CUSTOMER_CONTACT_COL_ROLE_W, 2: CUSTOMER_CONTACT_COL_PHONE_W, 3: CUSTOMER_CONTACT_COL_EMAIL_W},
            max_height=CUSTOMER_CONTACTS_MAX_H,
        )
        lay.addWidget(self.contacts_table)

        # ── آخر الطلبات ──
        self._orders_hdr = SectionHeader(tr("customer_orders_title"))
        lay.addWidget(self._orders_hdr)

        self.orders_table = make_table(
            columns=[
                tr("order_col_number"), tr("order_col_status"),
                tr("order_col_priority"), tr("order_header_total"), tr("order_date"),
            ],
            stretch_col=0,
            col_widths={1: CUSTOMER_ORDERS_COL_STATUS_W, 2: CUSTOMER_ORDERS_COL_PRI_W, 3: CUSTOMER_ORDERS_COL_TOTAL_W, 4: CUSTOMER_ORDERS_COL_DATE_W},
        )
        self.orders_table.setMaximumHeight(CUSTOMER_ORDERS_MAX_H)
        lay.addWidget(self.orders_table)

    def _load_data(self, item_id: int):
        return self._svc.get_customer(item_id)

    def _fill_data(self, data: dict):
        c = data
        type_map = {
            "individual": tr("customer_type_individual"),
            "company":    f"🏢 {tr('customer_type_company')}",
        }
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

        stats = self._svc.get_stats(self._item_id)
        self._card_total_orders.set_value(str(stats.get("total_orders") or 0))
        self._card_active_orders.set_value(str(stats.get("active") or 0))
        self._card_total_value.set_value(f"{(stats.get('total_value') or 0):,.0f} {tr('currency_sym')}")
        balance = (stats.get("total_value") or 0) - (stats.get("total_paid") or 0)
        self._card_balance.set_value(f"{balance:,.0f} {tr('currency_sym')}")
        self._card_balance.set_color(_C['danger'] if balance > 0 else _C['success'])

        self.btn_toggle.setText(
            tr("customer_toggle_active") if not c["is_active"] else tr("customer_toggle_inactive")
        )

        # ── جهات الاتصال ──
        contacts = [dict(ct) for ct in self._svc.list_contacts(self._item_id)]
        self.contacts_table.setRowCount(0)
        for ct in contacts:
            r = insert_row(self.contacts_table, ROW_HEIGHT_COMPACT)
            self.contacts_table.setItem(r, 0, bold_item(ct["name"]))
            self.contacts_table.setItem(r, 1, muted_item(ct.get("role") or ""))
            self.contacts_table.setItem(r, 2, make_item(ct.get("phone") or ""))
            self.contacts_table.setItem(r, 3, muted_item(ct.get("email") or ""))

        self._contacts_hdr.setVisible(bool(contacts))
        self.contacts_table.setVisible(bool(contacts))

        # ── آخر الطلبات ──
        STATUS_LABELS   = get_status_labels()
        PRIORITY_LABELS = get_priority_labels()
        orders = self._svc.list_orders(self._item_id)
        table  = self.orders_table
        table.setRowCount(0)

        for o in orders[:20]:
            r = insert_row(table, ROW_HEIGHT_COMPACT)
            num_item = bold_item(o["order_number"])
            from PyQt5.QtGui import QColor
            num_item.setForeground(QColor(_C['accent']))
            table.setItem(r, 0, num_item)

            status_lbl = STATUS_LABELS.get(o["status"], (o["status"],))[0]
            table.setItem(r, 1, make_item(status_lbl))

            pri_lbl, _ = PRIORITY_LABELS.get(o["priority"], ("", ""))
            table.setItem(r, 2, muted_item(pri_lbl))

            val_item = make_item(f"{(o['net_amount'] or 0):,.2f} {tr('currency_sym')}",
                                 align=Qt.AlignCenter)
            val_item.setForeground(QColor(_C['accent']))
            table.setItem(r, 3, val_item)
            table.setItem(r, 4, muted_item(o["order_date"] or ""))

        if orders:
            auto_fit_columns(table, fixed_cols=[1, 2, 3, 4], stretch_col=0)

    def _refresh_style(self, *_):
        """
        [إصلاح ثيم] الألوان اللي بتتحط بـ setForeground(QColor(_C[...]))
        وقت _fill_data (رقم الطلب، قيمة الطلب) بتتحدد مرة واحدة وقت
        التعبئة، مش جزء من الـ stylesheet، فبتفضل بلون الثيم القديم بعد
        تبديل الثيم. هنا بنعيد رسم الصفوف الموجودة فعلياً في جدول الطلبات.
        """
        super()._refresh_style(*_)
        from PyQt5.QtGui import QColor
        table = getattr(self, "orders_table", None)
        if table is None:
            return
        for r in range(table.rowCount()):
            num_item = table.item(r, 0)
            if num_item is not None:
                num_item.setForeground(QColor(_C['accent']))
            val_item = table.item(r, 3)
            if val_item is not None:
                val_item.setForeground(QColor(_C['accent']))

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
            self, tr("confirm_delete"),
            tr("customer_delete_confirm").format(name=c['name']),
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            if self._svc.delete(self._item_id):
                self._item_id = None
                self._show_empty()
                self.deleted.emit()
            else:
                QMessageBox.warning(self, tr("warning"), tr("customer_delete_failed"))

    def _toggle_active(self):
        if not self._item_id:
            return
        self._svc.toggle_active(self._item_id)
        self.load_customer(self._item_id)
        self.edited.emit(self._item_id)