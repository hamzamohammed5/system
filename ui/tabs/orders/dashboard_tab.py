"""
ui/tabs/orders/dashboard_tab.py
================================
لوحة متابعة الطلبات — إحصائيات وملخص سريع.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFrame, QLabel, QPushButton,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont

from db.orders.orders_repo import fetch_orders_summary, fetch_all_orders

from ui.widgets.shared.panels      import StatCard, SectionHeader, _make_btn
from ui.widgets.shared.table_utils import (
    make_detail_table,
    make_table_item, color_item, bold_item, muted_item,
    insert_row, ROW_HEIGHT_NORMAL,
)
from ui.helpers import make_detail_scroll, set_detail_content
from ui.app_settings import _C

STATUS_CONFIG = {
    "pending":     ("⏳", "انتظار",   "#f59e0b", "#fffbeb", "#fde68a"),
    "confirmed":   ("✅", "مؤكد",     "#3b82f6", "#eff6ff", "#bfdbfe"),
    "in_progress": ("🔧", "تنفيذ",   "#8b5cf6", "#f5f3ff", "#ddd6fe"),
    "ready":       ("📦", "جاهز",    "#10b981", "#ecfdf5", "#a7f3d0"),
    "delivered":   ("🚚", "مُسلَّم",  "#6b7280", "#f9fafb", "#e5e7eb"),
    "cancelled":   ("❌", "ملغي",    "#ef4444", "#fef2f2", "#fecaca"),
    "on_hold":     ("⏸", "معلق",    "#f97316", "#fff7ed", "#fed7aa"),
}
PRIORITY_CONFIG = {
    "urgent": ("🔴", "عاجل",  "#ef4444"),
    "high":   ("⬆",  "عالي",  "#f59e0b"),
    "normal": ("➡",  "عادي",  "#6b7280"),
    "low":    ("⬇",  "منخفض", "#9ca3af"),
}
STATUS_MAP   = {k: f"{v[0]} {v[1]}" for k, v in STATUS_CONFIG.items()}
STATUS_COLOR = {k: v[2]             for k, v in STATUS_CONFIG.items()}
TYPE_MAP     = {"new": "جديد", "reorder": "إعادة طلب", "custom": "مخصص"}
PRIORITY_MAP = {k: f"{v[0]} {v[1]}" for k, v in PRIORITY_CONFIG.items()}

_MIN_CONTENT_W = 500


def _status_chip(icon, label, count, color, bg, border):
    frame = QFrame()
    frame.setStyleSheet(f"QFrame {{ background:{bg}; border:1px solid {border}; border-radius:8px; }}")
    lay = QHBoxLayout(frame)
    lay.setContentsMargins(12, 8, 12, 8)
    lay.setSpacing(8)
    lbl_icon = QLabel(icon)
    lbl_icon.setStyleSheet("background:transparent; border:none;")
    lbl_lbl = QLabel(label)
    lbl_lbl.setStyleSheet(f"font-weight:600; color:{color}; background:transparent; border:none;")
    lbl_cnt = QLabel(str(count))
    f = QFont(); f.setPointSize(14); f.setBold(True)
    lbl_cnt.setFont(f)
    lbl_cnt.setStyleSheet(f"color:{color}; background:transparent; border:none;")
    lay.addWidget(lbl_icon)
    lay.addWidget(lbl_lbl, stretch=1)
    lay.addWidget(lbl_cnt)
    return frame, lbl_cnt


class OrdersDashboardTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = make_detail_scroll(min_content_width=_MIN_CONTENT_W)
        scroll.setStyleSheet(
            scroll.styleSheet() + f"\nQScrollArea {{ background: {_C['bg_page']}; }}"
        )

        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setContentsMargins(20, 16, 20, 20)
        lay.setSpacing(16)

        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        self._card_total       = StatCard("📋", "إجمالي الطلبات", color="#1565c0")
        self._card_urgent      = StatCard("🔴", "عاجل",           color="#ef4444")
        self._card_total_value = StatCard("💰", "إجمالي القيمة",  color="#10b981")
        self._card_total_paid  = StatCard("✅", "إجمالي المدفوع", color="#1565c0")
        for card in (self._card_total, self._card_urgent,
                     self._card_total_value, self._card_total_paid):
            top_row.addWidget(card, stretch=1)
        lay.addLayout(top_row)

        status_hdr = SectionHeader("توزيع الطلبات حسب الحالة")
        lay.addWidget(status_hdr)

        grid = QGridLayout()
        grid.setSpacing(10)
        self._status_chips = {}
        for idx, (status, cfg) in enumerate(STATUS_CONFIG.items()):
            icon, label, color, bg, border = cfg
            frame, cnt_lbl = _status_chip(icon, label, 0, color, bg, border)
            grid.addWidget(frame, idx // 4, idx % 4)
            self._status_chips[status] = cnt_lbl
        lay.addLayout(grid)

        recent_hdr = SectionHeader("آخر الطلبات")
        recent_hdr.add_button("↺  تحديث", self.refresh, "ghost")
        lay.addWidget(recent_hdr)

        self.recent_table = make_detail_table(
            columns=["رقم الطلب", "العميل", "النوع", "الحالة",
                     "الأولوية", "الإجمالي", "التاريخ"],
            stretch_col=1,
            col_widths={0: 120, 2: 70, 3: 95, 4: 75, 5: 90, 6: 90},
            max_height=320, min_height=60,
            row_height=ROW_HEIGHT_NORMAL,
        )
        lay.addWidget(self.recent_table)
        lay.addStretch()

        set_detail_content(scroll, content, bg=_C['bg_page'])
        root.addWidget(scroll)

    def refresh(self):
        summary = fetch_orders_summary(self.conn)
        self._card_total.set_value(str(summary.get("total") or 0))
        self._card_urgent.set_value(str(summary.get("urgent") or 0))
        self._card_total_value.set_value(f"{summary.get('total_value') or 0:,.0f} ج")
        self._card_total_paid.set_value(f"{summary.get('total_paid') or 0:,.0f} ج")

        for status, lbl in self._status_chips.items():
            lbl.setText(str(summary.get(status) or 0))

        orders = fetch_all_orders(self.conn)[:20]
        self.recent_table.setRowCount(0)
        for o in orders:
            r = insert_row(self.recent_table, ROW_HEIGHT_NORMAL)
            num_item = make_table_item(o["order_number"])
            bold_item(num_item); color_item(num_item, _C['accent'])
            self.recent_table.setItem(r, 0, num_item)
            self.recent_table.setItem(r, 1, make_table_item(o["customer_name"], tooltip=o["customer_name"]))
            self.recent_table.setItem(r, 2, muted_item(make_table_item(TYPE_MAP.get(o["order_type"], o["order_type"]))))
            s_item = make_table_item(STATUS_MAP.get(o["status"], o["status"]), align=Qt.AlignCenter)
            color_item(s_item, STATUS_COLOR.get(o["status"], "#555"))
            self.recent_table.setItem(r, 3, s_item)
            self.recent_table.setItem(r, 4, make_table_item(PRIORITY_MAP.get(o["priority"], ""), align=Qt.AlignCenter))
            v_item = make_table_item(f"{(o['net_amount'] or 0):,.2f} ج", align=Qt.AlignCenter)
            color_item(v_item, _C['accent'])
            self.recent_table.setItem(r, 5, v_item)
            self.recent_table.setItem(r, 6, muted_item(make_table_item(o["order_date"] or "")))