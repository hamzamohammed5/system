"""
ui/tabs/accounting/investors/_details_table.py
----------------------------------------------
_DetailsTable — جدول الحركات المالية للمستثمر.

مُستخرج من _investor_details.py لفصل منطق بناء الجدول.
يُستخدم فقط من _investor_details.py.
"""

from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtGui import QColor

from ui.widgets.tables.tables import make_table, auto_fit_columns
from ui.widgets.core.i18n import tr
from ui.theme import _C


def build_movements_table():
    """
    يبني جدول الحركات المالية.
    يرجع QTableWidget جاهز.
    """
    cols = [
        tr("link_no_col"),
        tr("date"),
        tr("movement_type_col"),
        tr("movement_amount"),
        tr("ref_no"),
        tr("movement_desc"),
    ]
    table = make_table(cols, stretch_col=5)
    table.setColumnHidden(0, True)
    table.setColumnWidth(1, 90)
    table.setColumnWidth(2, 90)
    table.setColumnWidth(3, 110)
    table.setColumnWidth(4, 95)
    table.setAlternatingRowColors(True)
    return table


def _type_ar(move_type: str) -> str:
    return tr("capital_movement") if move_type == "capital" else tr("drawings_movement")


def _type_color(move_type: str) -> str:
    return _C["investor_capital_text"] if move_type == "capital" else _C["investor_drawings_text"]


def fill_movement_row(table, r: int, entry: dict):
    """
    يملأ صف واحد في جدول الحركات.
    """
    table.setItem(r, 0, QTableWidgetItem(str(entry.get("id", ""))))
    table.setItem(r, 1, QTableWidgetItem(entry.get("date", "—")))

    mt = entry["move_type"]
    ti = QTableWidgetItem(_type_ar(mt))
    ti.setForeground(QColor(_type_color(mt)))
    table.setItem(r, 2, ti)

    amt_item = QTableWidgetItem(f"{entry['amount']:,.2f}")
    amt_item.setForeground(QColor(_type_color(mt)))
    table.setItem(r, 3, amt_item)

    table.setItem(r, 4, QTableWidgetItem(entry.get("ref_no") or "—"))
    table.setItem(r, 5, QTableWidgetItem(
        entry.get("entry_desc") or entry.get("notes") or "—"
    ))