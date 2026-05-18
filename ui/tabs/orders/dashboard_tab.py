"""
ui/tabs/orders/dashboard_tab.py
================================
لوحة متابعة الطلبات — إحصائيات وملخص سريع.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFrame, QLabel, QPushButton, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont, QColor

from db.orders.orders_repo import fetch_orders_summary, fetch_all_orders

from ui.widgets.shared.panels import StatCard
from ui.widgets.shared.table_utils import (
    make_table_item, color_item, bold_item, muted_item,
    ROW_HEIGHT_LARGE,
)
from ui.helpers import SCROLL_SS

# ── ثوابت الحالة ──────────────────────────────────────────
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
    "urgent": ("🔴", "عاجل", "#ef4444"),
    "high":   ("⬆",  "عالي", "#f59e0b"),
    "normal": ("➡",  "عادي", "#6b7280"),
    "low":    ("⬇",  "منخفض","#9ca3af"),
}

STATUS_MAP = {k: f"{v[0]} {v[1]}" for k, v in STATUS_CONFIG.items()}
TYPE_MAP   = {"new": "جديد", "reorder": "إعادة طلب", "custom": "مخصص"}
PRIORITY_MAP = {
    "low": "⬇ منخفض", "normal": "➡ عادي",
    "high": "⬆ عالي", "urgent": "🔴 عاجل",
}
STATUS_COLOR = {k: v[2] for k, v in STATUS_CONFIG.items()}


def _status_chip(icon, label, count, color, bg, border):
    """بطاقة حالة صغيرة تعرض العدد."""
    frame = QFrame()
    frame.setStyleSheet(f"""
        QFrame {{
            background: {bg};
            border: 1px solid {border};
            border-radius: 8px;
        }}
    """)
    lay = QHBoxLayout(frame)
    lay.setContentsMargins(12, 8, 12, 8)
    lay.setSpacing(8)

    lbl_icon = QLabel(icon)
    lbl_icon.setStyleSheet("background:transparent; border:none;")

    lbl_lbl = QLabel(label)
    lbl_lbl.setStyleSheet(
        f"font-weight:600; color:{color}; background:transparent; border:none;"
    )

    lbl_cnt = QLabel(str(count))
    f = QFont()
    f.setPointSize(14)
    f.setBold(True)
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

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(SCROLL_SS + "QScrollArea { background: #f8f9fb; }")

        content = QWidget()
        content.setStyleSheet("background: #f8f9fb;")
        lay = QVBoxLayout(content)
        lay.setContentsMargins(20, 16, 20, 20)
        lay.setSpacing(16)

        # ── بطاقات الإجمالي — StatCard من panels.py ──────────
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

        # ── شبكة الحالات ──────────────────────────────────────
        lbl_status = QLabel("توزيع الطلبات حسب الحالة")
        lbl_status.setStyleSheet(
            "font-weight:bold; color:#374151; background:transparent;"
        )
        lay.addWidget(lbl_status)

        grid = QGridLayout()
        grid.setSpacing(10)

        self._status_chips = {}
        statuses = list(STATUS_CONFIG.keys())
        for idx, status in enumerate(statuses):
            icon, label, color, bg, border = STATUS_CONFIG[status]
            frame, cnt_lbl = _status_chip(icon, label, 0, color, bg, border)
            grid.addWidget(frame, idx // 4, idx % 4)
            self._status_chips[status] = cnt_lbl

        lay.addLayout(grid)

        # ── آخر الطلبات ───────────────────────────────────────
        recent_hdr = QHBoxLayout()
        lbl_recent = QLabel("آخر الطلبات")
        lbl_recent.setStyleSheet(
            "font-weight:bold; color:#374151; background:transparent;"
        )

        btn_refresh = QPushButton("↺  تحديث")
        btn_refresh.setMinimumHeight(30)
        btn_refresh.setStyleSheet("""
            QPushButton {
                background: #e8eaf6; color: #3949ab;
                border: 1px solid #c5cae9; border-radius: 5px;
                padding: 0 12px;
            }
            QPushButton:hover { background: #c5cae9; }
        """)
        btn_refresh.clicked.connect(self.refresh)

        recent_hdr.addWidget(lbl_recent)
        recent_hdr.addStretch()
        recent_hdr.addWidget(btn_refresh)
        lay.addLayout(recent_hdr)

        self.recent_table = QTableWidget()
        self.recent_table.setColumnCount(7)
        self.recent_table.setHorizontalHeaderLabels([
            "رقم الطلب", "العميل", "النوع", "الحالة",
            "الأولوية", "الإجمالي", "التاريخ"
        ])
        self.recent_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.recent_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.recent_table.setAlternatingRowColors(True)
        self.recent_table.verticalHeader().setVisible(False)
        self.recent_table.setMaximumHeight(320)
        self.recent_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e5e9f0; border-radius: 8px;
                background: white; outline: none;
                alternate-background-color: #fafbff;
            }
            QTableWidget::item { padding: 6px 10px; }
            QTableWidget::item:selected { background: #dbeafe; color: #1e40af; }
            QHeaderView::section {
                background: #f8f9fb; color: #6b7280;
                font-weight: bold;
                padding: 6px 10px; border: none;
                border-bottom: 2px solid #e5e9f0;
                border-right: 1px solid #e5e9f0;
            }
        """)
        hh = self.recent_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lay.addWidget(self.recent_table)

        lay.addStretch()
        scroll.setWidget(content)
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
            r = self.recent_table.rowCount()
            self.recent_table.insertRow(r)
            self.recent_table.setRowHeight(r, ROW_HEIGHT_LARGE)

            num_item = make_table_item(o["order_number"])
            bold_item(num_item)
            self.recent_table.setItem(r, 0, num_item)
            self.recent_table.setItem(r, 1, make_table_item(o["customer_name"]))
            self.recent_table.setItem(r, 2, make_table_item(
                TYPE_MAP.get(o["order_type"], o["order_type"])
            ))

            status_item = make_table_item(STATUS_MAP.get(o["status"], o["status"]))
            color_item(status_item, STATUS_COLOR.get(o["status"], "#555"))
            status_item.setTextAlignment(Qt.AlignCenter)
            self.recent_table.setItem(r, 3, status_item)

            self.recent_table.setItem(r, 4, make_table_item(
                PRIORITY_MAP.get(o["priority"], "")
            ))
            self.recent_table.setItem(r, 5, make_table_item(
                f"{(o['net_amount'] or 0):,.2f} ج"
            ))
            self.recent_table.setItem(r, 6, muted_item(
                make_table_item(o["order_date"] or "")
            ))