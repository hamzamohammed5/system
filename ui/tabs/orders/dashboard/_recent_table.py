"""
ui/tabs/orders/dashboard/_recent_table.py
==========================================
جدول آخر الطلبات في لوحة المتابعة.
"""

from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QFont, QColor

from ui.widgets.shared.table_utils import (
    make_splitter_table, fit_splitter_table,
    insert_row, ROW_HEIGHT_NORMAL,
)
from ._config import STATUS_MAP, STATUS_COLOR, TYPE_MAP, PRIORITY_MAP

TABLE_COLS = ["رقم الطلب", "العميل", "النوع", "الحالة", "الأولوية", "الإجمالي", "التاريخ"]
COL_WIDTHS = {0: 130, 1: 150, 2: 70, 3: 95, 4: 65, 5: 95, 6: 85}


def build_recent_table(dashboard):
    """
    يبني جدول آخر الطلبات جوا QSplitter.
    يرجع QSplitter جاهز للإضافة في الـ layout.
    """
    splitter, table = make_splitter_table(
        columns=TABLE_COLS,
        col_widths=COL_WIDTHS,
        min_height=60,
    )
    dashboard.recent_table        = table
    dashboard._recent_splitter    = splitter
    return splitter


def fill_recent_table(dashboard, orders: list):
    """يملأ جدول آخر الطلبات بالبيانات ويعيد ضبط العرض."""
    table = dashboard.recent_table
    table.setRowCount(0)

    for o in orders:
        r = insert_row(table, ROW_HEIGHT_NORMAL)

        num_item = QTableWidgetItem(o["order_number"])
        f = QFont()
        f.setWeight(QFont.Medium)
        num_item.setFont(f)
        table.setItem(r, 0, num_item)

        table.setItem(r, 1, QTableWidgetItem(o["customer_name"]))
        table.setItem(r, 2, QTableWidgetItem(TYPE_MAP.get(o["order_type"], o["order_type"])))

        status_item = QTableWidgetItem(STATUS_MAP.get(o["status"], o["status"]))
        status_item.setForeground(QColor(STATUS_COLOR.get(o["status"], "#555")))
        status_item.setTextAlignment(Qt.AlignCenter)
        table.setItem(r, 3, status_item)

        pri_item = QTableWidgetItem(PRIORITY_MAP.get(o["priority"], ""))
        pri_item.setTextAlignment(Qt.AlignCenter)
        table.setItem(r, 4, pri_item)

        amt_item = QTableWidgetItem(f"{(o['net_amount'] or 0):,.2f} ج")
        amt_item.setTextAlignment(Qt.AlignCenter)
        table.setItem(r, 5, amt_item)

        date_item = QTableWidgetItem(o["order_date"] or "")
        date_item.setTextAlignment(Qt.AlignCenter)
        table.setItem(r, 6, date_item)

    fit_splitter_table(dashboard._recent_splitter, table)
