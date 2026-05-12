"""
ui/tabs/pricing/offers/offer_details.py
================================
_OfferDetails — لوحة عرض تفاصيل العرض المختار.

تعرض:
  - عنوان العرض مع الخصم والتاريخ والتصنيف
  - صناديق إحصائيات (إجمالي، خصم، بيع، تكلفة، ربح)
  - جدول تفصيلي بسطور المنتجات
  - ملاحظات العرض
"""

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.offers_repo import calc_offer_summary


def _stat_box(title: str, color: str = "#1565c0"):
    """يرجع (QFrame, QLabel_value) — بطاقة إحصائية."""
    frame = QFrame()
    frame.setStyleSheet("""
        QFrame {
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 4px;
        }
    """)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(10, 6, 10, 6)
    lay.setSpacing(2)
    lbl_t = QLabel(title)
    lbl_t.setStyleSheet("font-size:10px; color:#888; background:transparent; border:none;")
    lbl_t.setAlignment(Qt.AlignCenter)
    lbl_v = QLabel("─")
    lbl_v.setStyleSheet(
        f"font-size:14px; font-weight:bold; color:{color};"
        "background:transparent; border:none;"
    )
    lbl_v.setAlignment(Qt.AlignCenter)
    lay.addWidget(lbl_t)
    lay.addWidget(lbl_v)
    return frame, lbl_v


class _OfferDetails(QFrame):
    """لوحة تفاصيل العرض المختار من الجدول."""

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #ffe0b2;
                border-radius: 8px;
            }
        """)
        self._build()

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        # ── العنوان ──
        self.lbl_title = QLabel("اختر عرضاً لعرض تفاصيله")
        self.lbl_title.setStyleSheet(
            "font-weight:bold; color:#e65100; font-size:13px;"
            "background:transparent; border:none;"
        )
        self.lbl_title.setAlignment(Qt.AlignCenter)
        root.addWidget(self.lbl_title)

        # ── صناديق الإحصائيات ──
        stats_row = QHBoxLayout()
        stats_row.setSpacing(6)
        f1, self.sl_listed = _stat_box("إجمالي السعر قبل الخصم", "#1565c0")
        f2, self.sl_disc   = _stat_box("قيمة الخصم",             "#e53935")
        f3, self.sl_sell   = _stat_box("سعر البيع النهائي",      "#2e7d32")
        f4, self.sl_cost   = _stat_box("إجمالي التكلفة",         "#555555")
        f5, self.sl_profit = _stat_box("الربح",                   "#1b5e20")
        for f in (f1, f2, f3, f4, f5):
            stats_row.addWidget(f, stretch=1)
        root.addLayout(stats_row)

        # ── جدول تفاصيل السطور ──
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "المنتج", "التصنيف", "الكمية",
            "تكلفة/وحدة", "سعر/وحدة", "إجمالي السطر", "الربح/سطر"
        ])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        col_widths = {1: 90, 2: 55, 3: 80, 4: 75, 5: 90, 6: 80}
        for col, w in col_widths.items():
            hh.setSectionResizeMode(col, QHeaderView.Interactive)
            self.table.setColumnWidth(col, w)
        self.table.setMinimumHeight(120)
        root.addWidget(self.table, stretch=1)

        # ── ملاحظات ──
        self.lbl_notes = QLabel("")
        self.lbl_notes.setStyleSheet(
            "font-size:10px; color:#999; background:transparent; border:none;"
        )
        self.lbl_notes.setWordWrap(True)
        root.addWidget(self.lbl_notes)

    # ══════════════════════════════════════════════════════
    # تحميل بيانات عرض
    # ══════════════════════════════════════════════════════

    def load(self, offer_id: int):
        s = calc_offer_summary(self.conn, offer_id)
        if not s:
            return

        # ── العنوان ──
        cat_part = f"  │  🏷 {s['category_name']}" if s.get("category_name") else ""
        self.lbl_title.setText(
            f"📋  {s['offer_name']}  —  خصم {s['discount']:.1f}%"
            f"  │  {s['created_at']}{cat_part}"
        )

        # ── جدول السطور ──
        self.table.setRowCount(0)
        for line in s["lines"]:
            r = self.table.rowCount()
            self.table.insertRow(r)

            icon = "🏭" if line["item_type"] == "final" else "🔧"
            self.table.setItem(r, 0, QTableWidgetItem(f"{icon} {line['item_name']}"))
            self.table.setItem(r, 1, QTableWidgetItem(line["category_name"] or "—"))
            self.table.setItem(r, 2, QTableWidgetItem(f"{line['qty']:.4g}"))

            cost_item = QTableWidgetItem(f"{line['unit_cost']:.2f}")
            cost_item.setForeground(QColor("#1565c0"))
            self.table.setItem(r, 3, cost_item)

            if line["has_pricing"]:
                price_item = QTableWidgetItem(f"{line['unit_price']:.2f}")
                price_item.setForeground(QColor("#2e7d32"))
            else:
                price_item = QTableWidgetItem("─ ⚠️")
                price_item.setForeground(QColor("#e65100"))
            self.table.setItem(r, 4, price_item)

            if line["has_pricing"]:
                line_item = QTableWidgetItem(f"{line['line_listed']:.2f}")
                line_item.setForeground(QColor("#e65100"))
            else:
                line_item = QTableWidgetItem("─")
            self.table.setItem(r, 5, line_item)

            if line["has_pricing"]:
                line_profit = (line["unit_price"] - line["unit_cost"]) * line["qty"]
                lp_item = QTableWidgetItem(f"{line_profit:.2f}")
                lp_item.setForeground(
                    QColor("#1b5e20") if line_profit >= 0 else QColor("#b71c1c")
                )
                self.table.setItem(r, 6, lp_item)
            else:
                self.table.setItem(r, 6, QTableWidgetItem("─"))

        # ── الإحصائيات ──
        disc_pct = s["discount"]
        disc_amt = s["total_listed"] - s["sell_price"]

        self.sl_listed.setText(f"{s['total_listed']:.2f}  ج")
        self.sl_disc.setText(f"{disc_amt:.2f}  ج  ({disc_pct:.1f}%)")
        self.sl_sell.setText(f"{s['sell_price']:.2f}  ج")
        self.sl_cost.setText(f"{s['total_cost']:.2f}  ج")

        profit = s["profit"]
        color  = "#1b5e20" if profit >= 0 else "#b71c1c"
        self.sl_profit.setText(f"{profit:.2f}  ج")
        self.sl_profit.setStyleSheet(
            f"font-size:14px; font-weight:bold; color:{color};"
            "background:transparent; border:none;"
        )

        self.lbl_notes.setText(f"📝 {s['notes']}" if s.get("notes") else "")

    def clear(self):
        self.lbl_title.setText("اختر عرضاً لعرض تفاصيله")
        self.table.setRowCount(0)
        for lbl in (self.sl_listed, self.sl_disc, self.sl_sell,
                    self.sl_cost, self.sl_profit):
            lbl.setText("─")
        self.lbl_notes.setText("")
