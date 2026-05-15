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
from ui.helpers import (
    make_table, setup_table_columns, section_label,
)
from ui.events import bus


# ══════════════════════════════════════════════════════════
# تقرير المخزن
# ══════════════════════════════════════════════════════════

class _ReportTab(QWidget):
    def __init__(self, inv_conn, parent=None):
        super().__init__(parent)
        self.inv_conn = inv_conn
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

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
                    background: white;
                    border-left: 4px solid {color};
                    border-radius: 6px;
                    padding: 4px;
                }}
            """)
            lay = QVBoxLayout(f)
            lay.setContentsMargins(12, 8, 12, 8)
            lbl_t = QLabel(label)
            lbl_t.setStyleSheet(
                "font-size:10px; color:#888;"
                "background:transparent; border:none;"
            )
            lbl_v = QLabel("─")
            lbl_v.setStyleSheet(
                f"font-size:16px; font-weight:bold; color:{color};"
                "background:transparent; border:none;"
            )
            lay.addWidget(lbl_t)
            lay.addWidget(lbl_v)
            cards_row.addWidget(f, stretch=1)
            return lbl_v

        self.lbl_total_items = _card("عدد الأصناف",           "#1565c0")
        self.lbl_total_value = _card("إجمالي قيمة المخزن",    "#2e7d32")
        self.lbl_low_stock   = _card("أصناف تحت الحد الأدنى", "#c62828")
        self.lbl_zero_stock  = _card("أصناف نفدت",            "#e65100")

        root.addLayout(cards_row)

        root.addWidget(section_label("─── تقرير مخزن تفصيلي ───"))
        self.table = make_table(
            ["الصنف", "الوحدة", "الرصيد", "الحد الأدنى",
             "متوسط التكلفة", "القيمة الإجمالية", "الحالة"],
            stretch_col=0
        )
        setup_table_columns(self.table,
            widths={1: 70, 2: 80, 3: 80, 4: 110, 5: 120, 6: 90},
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
                status = "❌ نفد"
                color  = QColor("#c62828")
                zero_count += 1
            elif inv["qty_on_hand"] <= inv["qty_min"]:
                status = "⚠️ منخفض"
                color  = QColor("#e65100")
                low_count += 1
            else:
                status = "✅ متوفر"
                color  = QColor("#2e7d32")

            status_item = QTableWidgetItem(status)
            status_item.setForeground(color)
            self.table.setItem(r, 6, status_item)
            total_val += inv["total_value"]

        self.lbl_total_items.setText(str(len(rows)))
        self.lbl_total_value.setText(f"{total_val:,.2f}  ج")
        self.lbl_low_stock.setText(str(low_count))
        self.lbl_zero_stock.setText(str(zero_count))


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

        self.lbl_title = QLabel("اختر صنفاً لعرض حركاته")
        self.lbl_title.setStyleSheet(
            "font-weight:bold; color:#1565c0; font-size:13px;"
        )
        root.addWidget(self.lbl_title)

        self.table = make_table(
            ["التاريخ", "النوع", "الكمية", "سعر الوحدة",
             "الإجمالي", "رقم القيد", "ملاحظات"],
            stretch_col=6
        )
        setup_table_columns(self.table,
            widths={0: 90, 1: 70, 2: 80, 3: 100, 4: 100, 5: 100},
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
            f"📦  حركات: {inv['name']}"
            f"  (رصيد: {inv['qty_on_hand']:,.4g} {inv['unit']})"
        )
        moves = fetch_inventory_moves(self.inv_conn, inv_id)
        self.table.setRowCount(0)

        type_ar    = {"in": "📥 وارد", "out": "📤 صادر", "adjust": "⚖️ تسوية"}
        type_color = {"in": "#2e7d32", "out": "#c62828",  "adjust": "#1565c0"}

        for m in moves:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(m["date"]))
            type_item = QTableWidgetItem(
                type_ar.get(m["move_type"], m["move_type"])
            )
            type_item.setForeground(
                QColor(type_color.get(m["move_type"], "#333"))
            )
            self.table.setItem(r, 1, type_item)
            self.table.setItem(r, 2, QTableWidgetItem(f"{m['qty']:,.4g}"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{m['unit_cost']:,.4f}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"{m['total_cost']:,.2f}"))
            ref = m["ref_entry_no"] if "ref_entry_no" in m.keys() else "—"
            self.table.setItem(r, 5, QTableWidgetItem(ref or "—"))
            notes_item = QTableWidgetItem(m["notes"] or "—")
            notes_item.setToolTip(m["notes"] or "")
            self.table.setItem(r, 6, notes_item)

    def clear(self):
        self.table.setRowCount(0)
        self.lbl_title.setText("اختر صنفاً لعرض حركاته")
