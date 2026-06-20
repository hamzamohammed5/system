"""
ui/tabs/orders/dashboard/_recent_table.py
"""
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QFont, QColor

from ui.widgets.tables.tables import (
    make_table, insert_row, ROW_HEIGHT_NORMAL,
    auto_fit_columns,
)
from ui.widgets.core.i18n import tr
from ._config import get_status_map, get_status_color, get_type_map, get_priority_map, get_table_cols, COL_WIDTHS


def build_recent_table(dashboard):
    table = make_table(get_table_cols(), stretch_col=-1, col_widths=COL_WIDTHS)
    dashboard.recent_table = table
    return table


def fill_recent_table(dashboard, orders: list):
    table = dashboard.recent_table
    table.setRowCount(0)

    status_map   = get_status_map()
    status_color = get_status_color()
    type_map     = get_type_map()
    priority_map = get_priority_map()

    for o in orders:
        r = insert_row(table, ROW_HEIGHT_NORMAL)

        num_item = QTableWidgetItem(o["order_number"])
        f = QFont()
        f.setWeight(QFont.Medium)
        num_item.setFont(f)
        table.setItem(r, 0, num_item)

        table.setItem(r, 1, QTableWidgetItem(o["customer_name"]))
        table.setItem(r, 2, QTableWidgetItem(type_map.get(o["order_type"], o["order_type"])))

        status_item = QTableWidgetItem(status_map.get(o["status"], o["status"]))
        status_item.setForeground(QColor(status_color.get(o["status"], "#555")))
        status_item.setTextAlignment(Qt.AlignCenter)
        table.setItem(r, 3, status_item)

        pri_item = QTableWidgetItem(priority_map.get(o["priority"], ""))
        pri_item.setTextAlignment(Qt.AlignCenter)
        table.setItem(r, 4, pri_item)

        amt_item = QTableWidgetItem(f"{(o['net_amount'] or 0):,.2f} {tr('currency_sym')}")
        amt_item.setTextAlignment(Qt.AlignCenter)
        table.setItem(r, 5, amt_item)

        date_item = QTableWidgetItem(o["order_date"] or "")
        date_item.setTextAlignment(Qt.AlignCenter)
        table.setItem(r, 6, date_item)

    auto_fit_columns(table, fixed_cols=list(COL_WIDTHS.keys()), stretch_col=-1)
