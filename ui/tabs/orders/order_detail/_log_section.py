"""
ui/tabs/orders/order_detail/_log_section.py
"""
from PyQt5.QtCore import Qt

from db.orders.orders_repo import fetch_status_log
from ui.widgets.panels.layout_widgets import CollapsibleCard
from ui.widgets.tables.tables import (
    make_table, insert_row, auto_fit_columns,
    make_item, colored_item, bold_item, muted_item,
    ROW_HEIGHT_COMPACT,
)
from ui.widgets.core.i18n import tr
from ._status_config import get_status_labels


def _build_log_section(detail):
    detail._log_card = CollapsibleCard(tr("log_section_title"), expanded=False)

    detail.log_table = make_table(
        columns=[
            tr("log_col_from"), tr("log_col_to"),
            tr("log_col_notes"), tr("log_col_time"),
        ],
        stretch_col=2,
        col_widths={0: 100, 1: 100, 3: 120},
    )
    detail.log_table.setMaximumHeight(160)
    detail._log_card.content_layout.addWidget(detail.log_table)
    detail._content_lay.addWidget(detail._log_card)


def _fill_log(detail):
    logs   = [dict(r) for r in fetch_status_log(detail.conn, detail._order_id)]
    table  = detail.log_table
    STATUS_LABELS = get_status_labels()
    table.setRowCount(0)

    for log in logs:
        r = insert_row(table, ROW_HEIGHT_COMPACT)

        old_lbl  = STATUS_LABELS.get(log.get("old_status") or "", ("—",))[0]
        new_info = STATUS_LABELS.get(log.get("new_status", ""),
                                     (log.get("new_status", ""), "#555", "#f5f5f5", "#e0e0e0"))
        new_lbl, new_color = new_info[0], new_info[1]

        table.setItem(r, 0, muted_item(make_item(old_lbl)))

        new_item = make_item(new_lbl)
        bold_item(new_item)
        colored_item(new_lbl, new_color)
        table.setItem(r, 1, new_item)

        table.setItem(r, 2, make_item(log.get("notes") or ""))
        table.setItem(r, 3, muted_item(
            make_item((log.get("changed_at") or "")[:16], align=Qt.AlignCenter)
        ))

    if logs:
        auto_fit_columns(table, fixed_cols=[0, 1, 3], stretch_col=2)
