"""
ui/tabs/orders/order_detail/_log_section.py
============================================
قسم سجل تغييرات الحالة — دوال مستقلة تُستدعى من _OrderDetail.
"""

from PyQt5.QtCore import Qt

from db.orders.orders_repo import fetch_status_log

from ui.widgets.shared.panels import CollapsibleCard
from ui.widgets.shared.table_utils import (
    make_compact_table,
    make_table_item, color_item, bold_item, muted_item,
    insert_row, auto_fit_columns, ROW_HEIGHT_COMPACT,
)
from ._status_config import STATUS_LABELS


def _build_log_section(detail):
    """يبني قسم سجل الحالة."""
    detail._log_card = CollapsibleCard(
        "سجل تغييرات الحالة", expanded=False
    )
    detail.log_table = make_compact_table(
        columns=["من", "إلى", "الملاحظات", "الوقت"],
        stretch_col=2,
        col_widths={0: 100, 1: 100, 3: 140},
        max_height=160,
    )
    detail._log_card.content_layout.addWidget(detail.log_table)
    detail._content_lay.addWidget(detail._log_card)


def _fill_log(detail):
    """يملأ جدول سجل الحالة."""
    logs = [dict(r) for r in fetch_status_log(detail.conn, detail._order_id)]
    detail.log_table.setRowCount(0)

    for log in logs:
        r = insert_row(detail.log_table, ROW_HEIGHT_COMPACT)

        old_lbl  = STATUS_LABELS.get(
            log.get("old_status") or "", ("—",))[0]
        new_info = STATUS_LABELS.get(
            log.get("new_status", ""),
            (log.get("new_status", ""), "#555"))
        new_lbl, new_color = new_info[0], new_info[1]

        detail.log_table.setItem(r, 0, muted_item(make_table_item(old_lbl)))

        new_item = make_table_item(new_lbl)
        color_item(new_item, new_color)
        bold_item(new_item)
        detail.log_table.setItem(r, 1, new_item)

        detail.log_table.setItem(r, 2,
            make_table_item(log.get("notes") or ""))
        detail.log_table.setItem(r, 3, muted_item(
            make_table_item(
                (log.get("changed_at") or "")[:16], align=Qt.AlignCenter
            )
        ))

    # ضبط عرض الأعمدة على قد المحتوى بعد الملء
    if logs:
        auto_fit_columns(
            detail.log_table,
            fixed_cols=[0, 1, 3],
            stretch_col=2,
            min_width=60,
            max_width=200,
        )