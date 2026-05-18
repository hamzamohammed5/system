"""
ui/tabs/orders/dashboard/_recent_table.py
==========================================
بناء جدول آخر الطلبات في لوحة المتابعة.

القاعدة:
  ✅ الجدول Fixed — لا يتمدد مع النافذة
  ✅ كل الأعمدة عرضها محدد ثابت
  ✅ الـ container يحتوي الجدول + stretch
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont, QColor

from ui.widgets.shared.table_utils import make_detail_table, insert_row, ROW_HEIGHT_NORMAL
from ._config import (
    TABLE_COLS, COL_WIDTHS, TABLE_TOTAL_W,
    STATUS_MAP, STATUS_COLOR, TYPE_MAP, PRIORITY_MAP,
)


def build_recent_table(dashboard) -> QWidget:
    """
    يبني جدول آخر الطلبات داخل container.
    يرجع QWidget (container) جاهز للإضافة.
    يحفظ reference في dashboard.recent_table.
    """
    # ── container ──
    container = QWidget()
    container.setStyleSheet("background:transparent;")
    lay = QHBoxLayout(container)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(0)

    # ── الجدول ──
    dashboard.recent_table = make_detail_table(
        columns=TABLE_COLS,
        stretch_col=-1,
        col_widths=COL_WIDTHS,
        min_height=60,
    )

    # ✅ الجدول Fixed — لا يتمدد
    dashboard.recent_table.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
    dashboard.recent_table.setFixedWidth(TABLE_TOTAL_W)

    lay.addWidget(dashboard.recent_table)
    lay.addStretch()  # ✅ الـ stretch هنا بس — الجدول ثابت

    return container


def fill_recent_table(dashboard, orders: list):
    """
    يملأ جدول آخر الطلبات بالبيانات.
    """
    dashboard.recent_table.setRowCount(0)

    for o in orders:
        r = insert_row(dashboard.recent_table, ROW_HEIGHT_NORMAL)

        num_item = QTableWidgetItem(o["order_number"])
        f = QFont()
        f.setWeight(QFont.Medium)
        num_item.setFont(f)
        dashboard.recent_table.setItem(r, 0, num_item)

        dashboard.recent_table.setItem(r, 1,
            QTableWidgetItem(o["customer_name"]))
        dashboard.recent_table.setItem(r, 2,
            QTableWidgetItem(TYPE_MAP.get(o["order_type"], o["order_type"])))

        status_item = QTableWidgetItem(STATUS_MAP.get(o["status"], o["status"]))
        status_item.setForeground(QColor(STATUS_COLOR.get(o["status"], "#555")))
        status_item.setTextAlignment(Qt.AlignCenter)
        dashboard.recent_table.setItem(r, 3, status_item)

        dashboard.recent_table.setItem(r, 4,
            QTableWidgetItem(PRIORITY_MAP.get(o["priority"], "")))
        dashboard.recent_table.setItem(r, 5,
            QTableWidgetItem(f"{(o['net_amount'] or 0):,.2f} ج"))
        dashboard.recent_table.setItem(r, 6,
            QTableWidgetItem(o["order_date"] or ""))