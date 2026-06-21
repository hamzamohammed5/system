"""
ui/tabs/inventory/inventory_report_tab.py
================================
تقرير المخزن وعرض حركات صنف محدد.

يحتوي على:
  _ReportTab   — تقرير تفصيلي مع بطاقات إحصائيات
  _MovesPanel  — جدول حركات صنف مخزن محدد
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QTableWidgetItem,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.inventory.inventory_repo import (
    fetch_all_inventory, fetch_inventory_item,
    fetch_inventory_moves,
)
from ui.widgets.panels.form_labels   import section_title
from ui.widgets.tables.tables       import make_table, auto_fit_columns
from ui.widgets.mixins.bus import BusConnectedMixin
from ui.widgets.core.events import emit_company_data_changed
from ui.widgets.core.i18n import tr
from ui.theme import _C
from ui.font import FS_XS, FS_XL, FS_MD


# ══════════════════════════════════════════════════════════
# تقرير المخزن
# ══════════════════════════════════════════════════════════

class _ReportTab(QWidget, BusConnectedMixin):
    def __init__(self, inv_conn, parent=None):
        super().__init__(parent)
        self.inv_conn = inv_conn
        self._build()
        self._load()
        self._connect_bus(data=True)

    def _on_data_changed(self):
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(10)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)

        def _card(label, color):
            f = QFrame()
            f.setStyleSheet(f"""
                QFrame {{
                    background: {_C['bg_surface']};
                    border-left: 4px solid {color};
                    border-radius: 6px;
                    padding: 4px;
                }}
            """)
            lay = QVBoxLayout(f)
            lay.setContentsMargins(12, 8, 12, 8)
            lbl_t = QLabel(label)
            lbl_t.setStyleSheet(
                f"font-size:{FS_XS}px; color:{_C['text_muted']};"
                "background:transparent; border:none;"
            )
            lbl_v = QLabel(tr("dash"))
            lbl_v.setStyleSheet(
                f"font-size:{FS_XL}px; font-weight:bold; color:{color};"
                "background:transparent; border:none;"
            )
            lay.addWidget(lbl_t)
            lay.addWidget(lbl_v)
            cards_row.addWidget(f, stretch=1)
            return lbl_v

        self.lbl_total_items = _card(tr("inventory_total_items_card"), _C["info"])
        self.lbl_total_value = _card(tr("inventory_total_value_card"), _C["success"])
        self.lbl_low_stock   = _card(tr("inventory_low_stock_card"),   _C["stock_critical_fg"])
        self.lbl_zero_stock  = _card(tr("inventory_zero_stock_card"),  _C["stock_low_fg"])

        root.addLayout(cards_row)

        root.addWidget(section_title(tr("inventory_detailed_report_header")))
        self.table = make_table(
            [tr("item"), tr("unit"), tr("balance"), tr("inventory_min_qty_label"),
             tr("avg_cost"), tr("total_value"), tr("status")],
            stretch_col=0
        )
        
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, stretch=1)

    def _load(self):
        rows = fetch_all_inventory(self.inv_conn)
        self.table.setRowCount(0)
        total_val = 0.0
        low_count = zero_count = 0

        for inv in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)

            name_item = QTableWidgetItem(inv["name"])
            name_item.setToolTip(inv["name"])
            self.table.setItem(r, 0, name_item)
            self.table.setItem(r, 1, QTableWidgetItem(inv["unit"]))
            self.table.setItem(r, 2, QTableWidgetItem(f"{inv['qty_on_hand']:,.4g}"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{inv['qty_min']:,.4g}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"{inv['avg_cost']:,.4f}"))
            self.table.setItem(r, 5, QTableWidgetItem(f"{inv['total_value']:,.2f}"))

            if inv["qty_on_hand"] == 0:
                status = tr("inventory_status_out")
                color  = QColor(_C["stock_critical_fg"])
                zero_count += 1
            elif inv["qty_on_hand"] <= inv["qty_min"]:
                status = tr("inventory_status_low")
                color  = QColor(_C["stock_low_fg"])
                low_count += 1
            else:
                status = tr("inventory_status_ok")
                color  = QColor(_C["stock_ok_fg"])

            status_item = QTableWidgetItem(status)
            status_item.setForeground(color)
            self.table.setItem(r, 6, status_item)
            total_val += inv["total_value"]

        self.lbl_total_items.setText(str(len(rows)))
        self.lbl_total_value.setText(f"{total_val:,.2f}  {tr('currency_abbr')}")
        self.lbl_low_stock.setText(str(low_count))
        self.lbl_zero_stock.setText(str(zero_count))
        auto_fit_columns(self.table, fixed_cols=[1, 2, 3, 4, 5, 6], stretch_col=0, min_width=40, max_width=150)



# ══════════════════════════════════════════════════════════
# لوحة حركات صنف محدد
# ══════════════════════════════════════════════════════════

class _MovesPanel(QWidget):
    def __init__(self, inv_conn, parent=None):
        super().__init__(parent)
        self.inv_conn = inv_conn
        self._inv_id  = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(6)

        self.lbl_title = QLabel(tr("inventory_select_item_for_moves"))
        self.lbl_title.setStyleSheet(
            f"font-weight:bold; color:{_C['accent']}; font-size:{FS_MD}px;"
        )
        root.addWidget(self.lbl_title)

        self.table = make_table(
            [tr("date"), tr("type_col"), tr("quantity"), tr("unit_price"),
             tr("total"), tr("entry_no_col"), tr("notes")],
            stretch_col=6
        )
        
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, stretch=1)

    def load(self, inv_id: int):
        self._inv_id = inv_id
        inv = fetch_inventory_item(self.inv_conn, inv_id)
        if not inv:
            return
        self.lbl_title.setText(
            tr("inventory_item_moves_title_fmt").format(
                name=inv["name"], qty=f"{inv['qty_on_hand']:,.4g}", unit=inv["unit"]
            )
        )
        moves = fetch_inventory_moves(self.inv_conn, inv_id)
        self.table.setRowCount(0)

        type_ar    = {
            "in":     tr("move_type_in"),
            "out":    tr("move_type_out"),
            "adjust": tr("move_type_adjust"),
        }
        type_color = {
            "in":     _C["stock_ok_fg"],
            "out":    _C["stock_critical_fg"],
            "adjust": _C["journal_dr_accent"],
        }

        for m in moves:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(m["date"]))
            type_item = QTableWidgetItem(
                type_ar.get(m["move_type"], m["move_type"])
            )
            type_item.setForeground(
                QColor(type_color.get(m["move_type"], _C["text_primary"]))
            )
            self.table.setItem(r, 1, type_item)
            self.table.setItem(r, 2, QTableWidgetItem(f"{m['qty']:,.4g}"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{m['unit_cost']:,.4f}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"{m['total_cost']:,.2f}"))
            ref = m["ref_entry_no"] if "ref_entry_no" in m.keys() else tr("dash")
            self.table.setItem(r, 5, QTableWidgetItem(ref or tr("dash")))
            notes_item = QTableWidgetItem(m["notes"] or tr("dash"))
            notes_item.setToolTip(m["notes"] or "")
            self.table.setItem(r, 6, notes_item)
        auto_fit_columns(self.table, fixed_cols=[0, 1, 2, 3, 4, 5], stretch_col=6, min_width=40, max_width=150)

    def clear(self):
        self.table.setRowCount(0)
        self.lbl_title.setText(tr("inventory_select_item_for_moves"))
