"""
ui/tabs/orders/dashboard/_recent_table.py
==========================================
جدول آخر الطلبات في لوحة المتابعة.

✅ الجدول بعرض محتواه الطبيعي
✅ جوا QSplitter — تقدر توسعه أو تضيقه بالـ handle
✅ الجانب الثاني فاضي يأخذ المساحة الزيادة
"""

from PyQt5.QtWidgets import (
    QTableWidgetItem, QSplitter, QWidget, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont, QColor

from ui.widgets.shared.table_utils import (
    make_detail_table, insert_row, ROW_HEIGHT_NORMAL,
    calc_table_width,
)
from ui.app_settings import _C
from ._config import STATUS_MAP, STATUS_COLOR, TYPE_MAP, PRIORITY_MAP

TABLE_COLS  = ["رقم الطلب", "العميل", "النوع", "الحالة", "الأولوية", "الإجمالي", "التاريخ"]
COL_WIDTHS  = {0: 130, 1: 150, 2: 70, 3: 95, 4: 65, 5: 95, 6: 85}
STRETCH_COL = -1   # بلا stretch — كل الأعمدة Interactive


def build_recent_table(dashboard) -> QSplitter:
    """
    يبني الجدول جوا QSplitter أفقي.
    - يسار: الجدول بعرض محتواه
    - يمين: widget فاضي يأخذ الباقي
    يرجع QSplitter جاهز للإضافة في الـ layout.
    """
    splitter = QSplitter(Qt.Horizontal)
    splitter.setHandleWidth(6)
    splitter.setStyleSheet(f"""
        QSplitter::handle {{
            background: {_C['border_med']};
            border-radius: 3px;
        }}
        QSplitter::handle:hover {{
            background: {_C['accent_mid']};
        }}
        QSplitter::handle:pressed {{
            background: {_C['accent']};
        }}
    """)

    # ── الجدول ──
    dashboard.recent_table = make_detail_table(
        columns=TABLE_COLS,
        stretch_col=STRETCH_COL,
        col_widths=COL_WIDTHS,
        min_height=60,
    )
    dashboard.recent_table.setSizePolicy(
        QSizePolicy.Preferred, QSizePolicy.Expanding
    )

    # ── widget فاضي يأخذ الباقي ──
    spacer = QWidget()
    spacer.setStyleSheet("background: transparent;")
    spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    splitter.addWidget(dashboard.recent_table)
    splitter.addWidget(spacer)

    # حجم ابتدائي: الجدول بعرض محتواه، الباقي للـ spacer
    table_w = calc_table_width(dashboard.recent_table, extra_pad=20)
    splitter.setSizes([table_w, 9999])
    splitter.setCollapsible(0, False)
    splitter.setCollapsible(1, True)

    dashboard._recent_splitter = splitter
    return splitter


def fill_recent_table(dashboard, orders: list):
    """يملأ جدول آخر الطلبات بالبيانات ويعيد ضبط العرض."""
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

        pri_item = QTableWidgetItem(PRIORITY_MAP.get(o["priority"], ""))
        pri_item.setTextAlignment(Qt.AlignCenter)
        dashboard.recent_table.setItem(r, 4, pri_item)

        amt_item = QTableWidgetItem(f"{(o['net_amount'] or 0):,.2f} ج")
        amt_item.setTextAlignment(Qt.AlignCenter)
        dashboard.recent_table.setItem(r, 5, amt_item)

        date_item = QTableWidgetItem(o["order_date"] or "")
        date_item.setTextAlignment(Qt.AlignCenter)
        dashboard.recent_table.setItem(r, 6, date_item)

    # ── إعادة ضبط عرض الجدول بعد الملء ──
    if hasattr(dashboard, '_recent_splitter'):
        table_w = calc_table_width(dashboard.recent_table, extra_pad=20)
        total   = dashboard._recent_splitter.width()
        remaining = max(0, total - table_w)
        dashboard._recent_splitter.setSizes([table_w, remaining])