"""
ui/tabs/orders/order_detail/_log_section.py
"""
from PyQt5.QtCore import Qt

from ui.widgets.panels.layout_widgets import CollapsibleCard
from ui.widgets.tables.tables import (
    make_table, insert_row, auto_fit_columns,
    make_item, colored_item, bold_item, muted_item,
    ROW_HEIGHT_COMPACT,
)
from ui.widgets.core.i18n import tr
from ui.theme import _C
from ui.constants import ORDER_LOG_TABLE_COL_WIDTHS, ORDER_LOG_TABLE_MAX_H
from ._status_config import get_status_labels


def _build_log_section(detail):
    detail._log_card = CollapsibleCard(tr("log_section_title"), expanded=False)

    detail.log_table = make_table(
        columns=[
            tr("log_col_from"), tr("log_col_to"),
            tr("log_col_notes"), tr("log_col_time"),
        ],
        stretch_col=2,
        col_widths=ORDER_LOG_TABLE_COL_WIDTHS,
    )
    detail.log_table.setMaximumHeight(ORDER_LOG_TABLE_MAX_H)
    detail._log_card.content_layout.addWidget(detail.log_table)
    detail._content_lay.addWidget(detail._log_card)


def _fill_log(detail):
    logs   = [dict(r) for r in detail._svc.get_status_log(detail._order_id)]
    table  = detail.log_table
    STATUS_LABELS = get_status_labels()
    table.setRowCount(0)

    for log in logs:
        r = insert_row(table, ROW_HEIGHT_COMPACT)

        old_lbl  = STATUS_LABELS.get(log.get("old_status") or "", (tr("dash"),))[0]
        new_info = STATUS_LABELS.get(log.get("new_status", ""),
                                     (log.get("new_status", ""), _C['text_neutral'], _C['card_fallback_bg'], _C['card_fallback_border']))
        new_lbl, new_color = new_info[0], new_info[1]

        # [إصلاح] muted_item()/bold_item()/colored_item() بتاخد *نص* (str)
        # وبترجع QTableWidgetItem جاهز — مش بتاخد item جاهز كمدخل. الكود
        # القديم كان بيعمل muted_item(make_item(old_lbl)): بيبني item فارغ
        # الأول، ثم يبعته كـ "text" لـ muted_item، فـ QTableWidgetItem(str(item))
        # كانت بتطبع repr الكائن نفسه ("<PyQt5.QtWidgets.QTableWidgetItem...>")
        # بدل النص الفعلي. الحل: نبعت old_lbl (النص) مباشرة.
        table.setItem(r, 0, muted_item(old_lbl))

        # [إصلاح] نفس الغلط هنا بشكل مختلف: bold_item(new_item) و
        # colored_item(new_lbl, new_color) كل واحدة فيهم كانت بترجع
        # QTableWidgetItem *جديد* منفصل ومحدش بياخده — القيمتين كانوا
        # بيترموا فورًا، وكان بيتحط في الجدول فعليًا new_item الأصلي
        # (plain، من غير bold ومن غير new_color خالص). الحل: نبني item
        # واحد بالخط العريض واللون الصح مباشرة عبر bold_item(text, color).
        new_item = bold_item(new_lbl, color=new_color)
        table.setItem(r, 1, new_item)

        table.setItem(r, 2, make_item(log.get("notes") or ""))
        table.setItem(r, 3, muted_item((log.get("changed_at") or "")[:16]))

    if logs:
        auto_fit_columns(table, fixed_cols=[0, 1, 3], stretch_col=2)
