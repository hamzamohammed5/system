"""
ui/tabs/orders/order_detail/_items_section.py
=============================================
قسم بنود الطلب — دوال مستقلة تُستدعى من _OrderDetail.
"""

from PyQt5.QtWidgets import QFrame, QHBoxLayout
from PyQt5.QtCore    import Qt

from db.orders.orders_repo import fetch_order_items

from ui.widgets.shared.panels import SectionHeader, EmptyState, _make_btn
from ui.widgets.shared.table_utils import (
    make_detail_table,
    make_table_item, color_item, bold_item, muted_item,
    insert_row, ROW_HEIGHT_NORMAL,
)

_BLUE  = "#1565c0"
_GREEN = "#10b981"


def _build_items_section(detail):
    """يبني قسم البنود في الـ detail panel."""
    items_hdr = SectionHeader("بنود الطلب")
    detail.btn_add_item = items_hdr.add_button(
        "＋  إضافة بند", detail._add_item, "success"
    )
    detail._content_lay.addWidget(items_hdr)

    detail.items_table = make_detail_table(
        columns=["البند", "الوصف", "الكمية", "الوحدة", "السعر", "الخصم%", "الإجمالي"],
        stretch_col=0,
        col_widths={2: 65, 3: 65, 4: 90, 5: 60, 6: 95},
        max_height=280, min_height=60,
        row_height=ROW_HEIGHT_NORMAL,
    )
    detail._content_lay.addWidget(detail.items_table)

    detail._empty_items = EmptyState(
        icon="📦", title="لا توجد بنود في هذا الطلب",
        subtitle="اضغط «＋ إضافة بند» لإضافة منتج",
        style="dashed", color=_GREEN, min_height=90,
    )
    detail._empty_items.action_clicked.connect(detail._add_item)
    detail._content_lay.addWidget(detail._empty_items)

    # أزرار البنود — حجمها ثابت
    item_toolbar = QFrame()
    item_toolbar.setStyleSheet("background:transparent;")
    itb_lay = QHBoxLayout(item_toolbar)
    itb_lay.setContentsMargins(0, 0, 0, 0)
    itb_lay.setSpacing(6)

    detail.btn_edit_item = _make_btn("✏️  تعديل البند", "ghost")
    detail.btn_edit_item.setMinimumHeight(28)
    detail.btn_edit_item.clicked.connect(detail._edit_item)

    detail.btn_del_item = _make_btn("🗑️  حذف البند", "danger")
    detail.btn_del_item.setMinimumHeight(28)
    detail.btn_del_item.clicked.connect(detail._del_item)

    itb_lay.addWidget(detail.btn_edit_item)
    itb_lay.addWidget(detail.btn_del_item)
    itb_lay.addStretch()
    detail._content_lay.addWidget(item_toolbar)


def _fill_items(detail):
    """يملأ جدول البنود بالبيانات."""
    items = fetch_order_items(detail.conn, detail._order_id)
    detail.items_table.setRowCount(0)

    has_items = bool(items)
    detail.items_table.setVisible(has_items)
    detail._empty_items.setVisible(not has_items)
    detail.btn_edit_item.setVisible(has_items)
    detail.btn_del_item.setVisible(has_items)

    for item in items:
        r = insert_row(detail.items_table, ROW_HEIGHT_NORMAL)

        name_item = make_table_item(item["item_name"], user_data=item["id"])
        bold_item(name_item)
        detail.items_table.setItem(r, 0, name_item)
        detail.items_table.setItem(r, 1,
            make_table_item(item.get("description") or ""))
        detail.items_table.setItem(r, 2,
            make_table_item(f"{item['quantity']:g}", align=Qt.AlignCenter))

        unit_item = make_table_item(item["unit"], align=Qt.AlignCenter)
        muted_item(unit_item)
        detail.items_table.setItem(r, 3, unit_item)
        detail.items_table.setItem(r, 4,
            make_table_item(f"{item['unit_price']:,.2f}", align=Qt.AlignCenter))

        disc_item = make_table_item(
            f"{item['discount_pct']:g}%", align=Qt.AlignCenter)
        muted_item(disc_item)
        detail.items_table.setItem(r, 5, disc_item)

        total_val  = (item["quantity"] * item["unit_price"]
                      * (1 - item["discount_pct"] / 100))
        total_item = make_table_item(f"{total_val:,.2f}", align=Qt.AlignCenter)
        bold_item(total_item)
        color_item(total_item, _BLUE)
        detail.items_table.setItem(r, 6, total_item)