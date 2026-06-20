"""
ui/tabs/orders/order_detail/_header_fill.py
"""
from ui.widgets.core.i18n import tr
from ._status_config import (
    get_status_labels, get_priority_labels, get_type_labels, get_status_transitions
)
from ui.theme import _C


def _fill_header(detail):
    d = detail._order_data
    STATUS_LABELS      = get_status_labels()
    PRIORITY_LABELS     = get_priority_labels()
    TYPE_LABELS          = get_type_labels()
    STATUS_TRANSITIONS  = get_status_transitions()

    detail._hdr.set_title(d["order_number"])
    detail._hdr.set_type_badge(TYPE_LABELS.get(d["order_type"], ""))

    si = STATUS_LABELS.get(d["status"], (d["status"], _C['text_sec'], _C['bg_surface_2'], _C['border']))
    detail._hdr.set_status_badge(si[0], si[1], si[2], si[3])

    pri_lbl, pri_color = PRIORITY_LABELS.get(d["priority"], ("", _C['text_muted']))
    detail._hdr.set_priority_badge(pri_lbl, pri_color)

    customer_line = f"👤  {d['customer_name']}  ({d['customer_code']})"
    info_parts = []
    if d.get("customer_phone"): info_parts.append(f"📞 {d['customer_phone']}")
    if d.get("customer_city"):  info_parts.append(f"📍 {d['customer_city']}")

    detail._hdr.set_customer_name(customer_line)
    detail._hdr.set_info(info_parts)

    net    = d.get("net_amount")  or 0
    paid   = d.get("paid_amount") or 0
    remain = net - paid

    detail._card_total.set_value(f"{net:,.2f} {tr('currency_sym')}")
    detail._card_paid.set_value(f"{paid:,.2f} {tr('currency_sym')}")
    detail._card_balance.set_value(f"{remain:,.2f} {tr('currency_sym')}")
    detail._card_balance.set_color(_C['danger'] if remain > 0 else _C['success'])
    detail._card_due.set_value(d.get("due_date") or "─")

    status     = d["status"]
    can_edit   = status not in ("delivered", "cancelled")
    can_cancel = status not in ("delivered", "cancelled")
    can_delete = status in ("pending", "cancelled")
    can_change = bool(STATUS_TRANSITIONS.get(status))

    detail.btn_edit.setEnabled(can_edit)
    detail.btn_cancel.setEnabled(can_cancel)
    detail.btn_delete.setEnabled(can_delete)
    detail.btn_status.setEnabled(can_change)
    detail.btn_add_item.setEnabled(can_edit)
