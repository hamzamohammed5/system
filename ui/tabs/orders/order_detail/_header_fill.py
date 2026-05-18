"""
ui/tabs/orders/order_detail/_header_fill.py
============================================
ملء الـ header في _OrderDetail — منفصل للوضوح.
"""

from ._status_config import (
    STATUS_LABELS, STATUS_TRANSITIONS,
    PRIORITY_LABELS, TYPE_LABELS,
)

_GREEN = "#10b981"


def _fill_header(detail):
    """يملأ الـ header ببيانات الطلب."""
    d = detail._order_data

    detail._hdr.set_title(d["order_number"])
    detail._hdr.set_type_badge(TYPE_LABELS.get(d["order_type"], ""))

    status_info = STATUS_LABELS.get(
        d["status"], (d["status"], "#555", "#fff", "#eee"))
    detail._hdr.set_status_badge(
        status_info[0], status_info[1], status_info[2], status_info[3])

    pri_lbl, pri_color = PRIORITY_LABELS.get(d["priority"], ("", "#6b7280"))
    detail._hdr.set_priority_badge(pri_lbl, pri_color)

    customer_line = f"👤  {d['customer_name']}  ({d['customer_code']})"
    info_parts = []
    if d.get("customer_phone"):
        info_parts.append(f"📞 {d['customer_phone']}")
    if d.get("customer_city"):
        info_parts.append(f"📍 {d['customer_city']}")

    detail._hdr.set_customer_name(customer_line)
    detail._hdr.set_info(info_parts)

    net    = d.get("net_amount")  or 0
    paid   = d.get("paid_amount") or 0
    remain = net - paid

    detail._card_total.set_value(f"{net:,.2f} ج")
    detail._card_paid.set_value(f"{paid:,.2f} ج")
    detail._card_balance.set_value(f"{remain:,.2f} ج")
    detail._card_balance.set_color("#ef4444" if remain > 0 else _GREEN)
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