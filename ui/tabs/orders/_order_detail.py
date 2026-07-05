"""
ui/tabs/orders/_order_detail.py
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QDialog
from PyQt5.QtCore import pyqtSignal

from db.orders.orders_repo import (
    fetch_order, fetch_order_items,
    change_order_status, cancel_order, delete_order,
    reorder as do_reorder, delete_order_item,
)
from ui.tabs.orders._order_form import _OrderForm
from ui.tabs.orders._item_form  import _ItemForm
from ui.widgets.base.detail_panel import BaseDetailPanel
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.widgets.core.i18n import tr
from ui.theme import _C

from ui.tabs.orders.order_detail._items_section import _build_items_section, _fill_items
from ui.tabs.orders.order_detail._log_section   import _build_log_section, _fill_log
from ui.tabs.orders.order_detail._header_fill   import _fill_header
from ui.tabs.orders.order_detail._status_config import STATUS_TRANSITIONS
from ui.tabs.orders.order_detail._status_dialog import _StatusDialog


class _OrderDetail(BaseDetailPanel, WidgetMixin):
    saved          = pyqtSignal(int)
    deleted        = pyqtSignal()
    status_changed = pyqtSignal(int)

    EMPTY_TITLE    = "order_select_first"      # مفتاح tr
    EMPTY_SUBTITLE = "order_select_subtitle"   # مفتاح tr

    @property
    def EMPTY_ICON(self) -> str:
        return tr("empty_icon_table")

    def __init__(self, conn, parent=None):
        self._order_id   = None
        self._order_data = None
        super().__init__(conn=conn, parent=parent)
        self._init_widget_mixin(font=False, lang=False, data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        from ui.theme import _C as C
        if self._order_data:
            remain = (self._order_data.get("net_amount") or 0) - (self._order_data.get("paid_amount") or 0)
            if hasattr(self, "_card_balance"):
                self._card_balance.set_color(C['danger'] if remain > 0 else C['success'])

    def _build_header_cards(self):
        self._card_total   = self._hdr.add_stat_card(tr("order_icon_total"),   tr("order_header_total"),   color=_C['accent'])
        self._card_paid    = self._hdr.add_stat_card(tr("order_icon_paid"),    tr("order_header_paid"),    color=_C['success'])
        self._card_balance = self._hdr.add_stat_card(tr("order_icon_balance"), tr("order_header_balance"), color=_C['danger'])
        self._card_due     = self._hdr.add_stat_card(tr("order_icon_due"),     tr("order_header_due"),     color=_C['warning'])

    def _build_header_buttons(self):
        self.btn_edit    = self._hdr.toolbar.add_action(tr("order_edit_btn"),          "primary")
        self.btn_status  = self._hdr.toolbar.add_action(tr("order_change_status_btn"), "ghost")
        self.btn_reorder = self._hdr.toolbar.add_action(tr("order_reorder_btn"),       "ghost")
        self.btn_cancel  = self._hdr.toolbar.add_danger(tr("order_cancel_btn_action"))
        self.btn_delete  = self._hdr.toolbar.add_danger(tr("order_delete_btn"))

        self.btn_edit.clicked.connect(self._edit_order)
        self.btn_status.clicked.connect(self._change_status_dialog)
        self.btn_reorder.clicked.connect(self._do_reorder)
        self.btn_cancel.clicked.connect(self._cancel_order)
        self.btn_delete.clicked.connect(self._delete_order)

    def _build_content(self, lay: QVBoxLayout):
        _build_items_section(self)
        _build_log_section(self)

    def _load_data(self, item_id: int):
        return fetch_order(self.conn, item_id)

    def _fill_data(self, data: dict):
        self._order_id   = self._item_id
        self._order_data = data
        _fill_header(self)
        _fill_items(self)
        _fill_log(self)

    def load_order(self, order_id: int):
        self.load_item(order_id)

    def clear(self):
        self._order_id   = None
        self._order_data = None
        self._item_id    = None
        self._item_data  = None
        self._show_empty()

    def new_order(self):
        dlg = _OrderForm(self.conn, parent=self)
        dlg.saved.connect(self._on_form_saved)
        dlg.exec_()

    def _edit_order(self):
        if not self._order_id:
            return
        dlg = _OrderForm(self.conn, order_id=self._order_id, parent=self)
        dlg.saved.connect(self._on_form_saved)
        dlg.exec_()

    def _on_form_saved(self, order_id: int):
        self.load_order(order_id)
        self.saved.emit(order_id)

    def _change_status_dialog(self):
        if not self._order_id or not self._order_data:
            return
        current       = self._order_data["status"]
        next_statuses = STATUS_TRANSITIONS.get(current, [])
        if not next_statuses:
            return
        dlg = _StatusDialog(current, next_statuses, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            new_status, note = dlg.get_result()
            change_order_status(self.conn, self._order_id, new_status, note)
            self.status_changed.emit(self._order_id)

    def _cancel_order(self):
        if not self._order_id:
            return
        d = self._order_data
        if d["status"] in ("delivered", "cancelled"):
            return
        reason, ok = _get_text_input(
            self,
            tr("order_cancel_title"),
            tr("order_cancel_reason").format(number=d['order_number'])
        )
        if ok:
            cancel_order(self.conn, self._order_id, reason)
            self.status_changed.emit(self._order_id)

    def _delete_order(self):
        if not self._order_id:
            return
        d = self._order_data
        if QMessageBox.question(
            self, tr("confirm_delete"),
            tr("order_delete_confirm").format(number=d['order_number']),
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            if delete_order(self.conn, self._order_id):
                self.deleted.emit()
            else:
                QMessageBox.warning(self, tr("warning"), tr("order_delete_failed"))

    def _do_reorder(self):
        if not self._order_id:
            return
        d = self._order_data
        if QMessageBox.question(
            self, tr("order_reorder_btn"),
            tr("order_reorder_confirm").format(number=d['order_number']),
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            new_id = do_reorder(self.conn, self._order_id)
            if new_id:
                self.load_order(new_id)
                self.saved.emit(new_id)

    def _add_item(self):
        if not self._order_id:
            return
        if self._order_data and self._order_data["status"] in ("delivered", "cancelled"):
            QMessageBox.information(self, tr("info"), tr("order_no_items_warn"))
            return
        dlg = _ItemForm(self.conn, self._order_id, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            _fill_items(self)
            self._fill_header_amounts()

    def _edit_item(self):
        from PyQt5.QtCore import Qt
        row = self.items_table.currentRow()
        if row < 0:
            QMessageBox.information(self, tr("info"), tr("select_item_first"))
            return
        item_id = self.items_table.item(row, 0).data(Qt.UserRole)
        dlg = _ItemForm(self.conn, self._order_id, item_id=item_id, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            _fill_items(self)
            self._fill_header_amounts()

    def _del_item(self):
        from PyQt5.QtCore import Qt
        row = self.items_table.currentRow()
        if row < 0:
            QMessageBox.information(self, tr("info"), tr("select_item_first"))
            return
        item_id = self.items_table.item(row, 0).data(Qt.UserRole)
        name    = self.items_table.item(row, 0).text()
        if QMessageBox.question(
            self, tr("confirm_delete"),
            tr("delete_confirm_msg").format(name=name),
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            delete_order_item(self.conn, item_id)
            _fill_items(self)
            self._fill_header_amounts()

    def _fill_header_amounts(self):
        if not self._order_id:
            return
        row = fetch_order(self.conn, self._order_id)
        self._order_data = dict(row) if row else None
        if self._order_data:
            from ui.theme import _C as C
            net    = self._order_data.get("net_amount")  or 0
            paid   = self._order_data.get("paid_amount") or 0
            remain = net - paid
            self._card_total.set_value(f"{net:,.2f} {tr('currency_sym')}")
            self._card_paid.set_value(f"{paid:,.2f} {tr('currency_sym')}")
            self._card_balance.set_value(f"{remain:,.2f} {tr('currency_sym')}")
            self._card_balance.set_color(C['danger'] if remain > 0 else C['success'])


def _get_text_input(parent, title, prompt):
    from PyQt5.QtWidgets import QInputDialog
    return QInputDialog.getText(parent, title, prompt)
