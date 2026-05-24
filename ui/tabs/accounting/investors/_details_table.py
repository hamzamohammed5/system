"""
ui/tabs/accounting/investors/_details_table.py
----------------------------------------------
_DetailsTable — جدول الحركات المالية للمستثمر.

مُستخرج من _investor_details.py لفصل منطق بناء الجدول.
يُستخدم فقط من _investor_details.py.
"""

from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtGui import QColor

from ui.helpers import make_table, setup_table_columns


def build_movements_table():
    """
    يبني جدول الحركات المالية.
    يرجع QTableWidget جاهز.
    """
    table = make_table(
        ["LinkID", "التاريخ", "النوع", "المبلغ", "رقم القيد", "البيان"],
        stretch_col=5
    )
    table.setColumnHidden(0, True)
    setup_table_columns(
        table,
        widths={1: 90, 2: 90, 3: 110, 4: 95},
        stretch_col=5
    )
    table.setAlternatingRowColors(True)
    return table


_TYPE_AR    = {"capital": "💰 رأس مال", "drawings": "💸 مسحوبات"}
_TYPE_COLOR = {"capital": "#2e7d32",    "drawings": "#c62828"}


def fill_movement_row(table, r: int, entry: dict):
    """
    يملأ صف واحد في جدول الحركات.

    table  : QTableWidget
    r      : رقم الصف
    entry  : dict من investor entries
    """
    table.setItem(r, 0, QTableWidgetItem(str(entry.get("id", ""))))
    table.setItem(r, 1, QTableWidgetItem(entry.get("date", "—")))

    mt = entry["move_type"]
    ti = QTableWidgetItem(_TYPE_AR.get(mt, mt))
    ti.setForeground(QColor(_TYPE_COLOR.get(mt, "#333")))
    table.setItem(r, 2, ti)

    amt_item = QTableWidgetItem(f"{entry['amount']:,.2f}")
    amt_item.setForeground(QColor(_TYPE_COLOR.get(mt, "#333")))
    table.setItem(r, 3, amt_item)

    table.setItem(r, 4, QTableWidgetItem(entry.get("ref_no") or "—"))
    table.setItem(r, 5, QTableWidgetItem(
        entry.get("entry_desc") or entry.get("notes") or "—"
    ))