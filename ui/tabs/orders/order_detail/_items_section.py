"""
ui/tabs/orders/order_detail/_items_section.py
"""
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtCore    import Qt

from ui.widgets.panels.themed_inputs import ThemedFrame

from ui.widgets.components.headers_page import SectionHeader
from ui.widgets.panels.state import EmptyState
from ui.widgets.components.button import make_btn
from ui.widgets.tables.tables import (
    make_table, insert_row, auto_fit_columns,
    make_item, bold_item, colored_item, muted_item,
    ROW_HEIGHT_NORMAL,
)
from ui.widgets.core.i18n import tr
from ui.theme import _C
from ui.constants import (
    ORDER_ITEMS_TABLE_COL_WIDTHS, ORDER_ITEMS_TABLE_MAX_H, ORDER_ITEMS_TABLE_MIN_H,
    ORDER_ITEMS_EMPTY_MIN_H, ORDER_ITEMS_TOOLBAR_SPACING, ORDER_ITEMS_BTN_MIN_H,
)


def _build_items_section(detail):
    items_hdr = SectionHeader(tr("order_items_section"))
    detail.btn_add_item = items_hdr.add_button(tr("order_add_item_btn"), detail._add_item, "success")
    detail._content_lay.addWidget(items_hdr)

    detail.items_table = make_table(
        columns=[
            tr("items_col_name"), tr("items_col_desc"), tr("items_col_qty"),
            tr("items_col_unit"), tr("items_col_price"),
            tr("items_col_discount"), tr("items_col_total"),
        ],
        stretch_col=0,
        col_widths=ORDER_ITEMS_TABLE_COL_WIDTHS,
    )
    detail.items_table.setMaximumHeight(ORDER_ITEMS_TABLE_MAX_H)
    detail.items_table.setMinimumHeight(ORDER_ITEMS_TABLE_MIN_H)
    detail._content_lay.addWidget(detail.items_table)

    detail._empty_items = EmptyState(
        icon=tr("order_no_items_icon"),
        title=tr("order_no_items_title"),
        subtitle=tr("order_no_items_hint"),
        style="dashed",
        color=_C['success'],
        min_height=ORDER_ITEMS_EMPTY_MIN_H,
    )
    detail._empty_items.action_clicked.connect(detail._add_item)
    detail._content_lay.addWidget(detail._empty_items)

    item_toolbar = ThemedFrame()
    item_toolbar.setStyleSheet("background:transparent;")
    itb_lay = QHBoxLayout(item_toolbar)
    itb_lay.setContentsMargins(0, 0, 0, 0)
    itb_lay.setSpacing(ORDER_ITEMS_TOOLBAR_SPACING)

    detail.btn_edit_item = make_btn(tr("order_edit_item_btn"), "ghost")
    detail.btn_edit_item.setMinimumHeight(ORDER_ITEMS_BTN_MIN_H)
    detail.btn_edit_item.clicked.connect(detail._edit_item)

    detail.btn_del_item = make_btn(tr("order_del_item_btn"), "danger")
    detail.btn_del_item.setMinimumHeight(ORDER_ITEMS_BTN_MIN_H)
    detail.btn_del_item.clicked.connect(detail._del_item)

    itb_lay.addWidget(detail.btn_edit_item)
    itb_lay.addWidget(detail.btn_del_item)
    itb_lay.addStretch()

    detail._item_toolbar = item_toolbar
    detail._content_lay.addWidget(item_toolbar)


def _fill_items(detail):
    items = detail._svc.get_order_items(detail._order_id)
    table = detail.items_table
    table.setRowCount(0)

    has_items = bool(items)
    table.setVisible(has_items)
    detail._empty_items.setVisible(not has_items)
    detail.btn_edit_item.setVisible(has_items)
    detail.btn_del_item.setVisible(has_items)
    detail._item_toolbar.setVisible(has_items)

    for item in items:
        r = insert_row(table, ROW_HEIGHT_NORMAL)

        name_item = make_item(item["item_name"], user_data=item["id"])
        f0 = name_item.font()
        f0.setBold(True)
        name_item.setFont(f0)
        table.setItem(r, 0, name_item)
        table.setItem(r, 1, make_item(item["description"] or ""))
        table.setItem(r, 2, make_item(f"{item['quantity']:g}", align=Qt.AlignCenter))

        unit_item = muted_item(item["unit"], align=Qt.AlignCenter)
        table.setItem(r, 3, unit_item)
        table.setItem(r, 4, make_item(f"{item['unit_price']:,.2f}", align=Qt.AlignCenter))

        disc_item = muted_item(f"{item['discount_pct']:g}%", align=Qt.AlignCenter)
        table.setItem(r, 5, disc_item)

        total_val  = item["quantity"] * item["unit_price"] * (1 - item["discount_pct"] / 100)
        total_item = colored_item(
            f"{total_val:,.2f}", _C['accent'], align=Qt.AlignCenter
        )
        f = total_item.font()
        f.setBold(True)
        total_item.setFont(f)
        table.setItem(r, 6, total_item)

    if has_items:
        auto_fit_columns(table, fixed_cols=[2, 3, 4, 5, 6], stretch_col=0)
