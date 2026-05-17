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


def _stat_card(icon, title, value="─", sub="",
               color="#1565c0", bg="#e8f0fe", border="#90caf9"):
    frame = QFrame()
    frame.setStyleSheet(f"""
        QFrame {{
            background: {bg};
            border: 1px solid {border};
            border-radius: 12px;
        }}
    """)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(16, 14, 16, 14)
    lay.setSpacing(4)

    row = QHBoxLayout()
    lbl_icon = QLabel(icon)
    lbl_icon.setStyleSheet("background:transparent; border:none;")
    lbl_val = QLabel(value)
    f = QFont()
    f.setPointSize(18)
    f.setBold(True)
    lbl_val.setFont(f)
    lbl_val.setStyleSheet(f"color:{color}; background:transparent; border:none;")
    lbl_val.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    row.addWidget(lbl_icon)
    row.addStretch()
    row.addWidget(lbl_val)
    lay.addLayout(row)

    lbl_t = QLabel(title)
    lbl_t.setStyleSheet(
        f"color:{color}; font-weight:600;"
        "background:transparent; border:none;"
    )
    lay.addWidget(lbl_t)

    if sub:
        lbl_s = QLabel(sub)
        lbl_s.setStyleSheet("color:#6b7280; background:transparent; border:none;")
        lay.addWidget(lbl_s)

    return frame, lbl_val


def _status_chip(icon, label, count, color, bg, border):
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
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: #f8f9fb; }
            QScrollBar:vertical {
                background: #f0f0f0; width: 6px; border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #cdd3e0; border-radius: 3px; min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        content = QWidget()
        content.setStyleSheet("background: #f8f9fb;")
        lay = QVBoxLayout(content)
        lay.setContentsMargins(20, 16, 20, 20)
        lay.setSpacing(16)

        # ── بطاقات الإجمالي ──────────────────────────────────
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        f1, self._lbl_total        = _stat_card("📋", "إجمالي الطلبات",
                                                 color="#1565c0", bg="#e8f0fe", border="#90caf9")
        f2, self._lbl_urgent       = _stat_card("🔴", "عاجل",
                                                 color="#ef4444", bg="#fef2f2", border="#fecaca")
        f3, self._lbl_total_value  = _stat_card("💰", "إجمالي القيمة",
                                                 color="#10b981", bg="#ecfdf5", border="#a7f3d0")
        f4, self._lbl_total_paid   = _stat_card("✅", "إجمالي المدفوع",
                                                 color="#1565c0", bg="#eff6ff", border="#bfdbfe")

        for ff in (f1, f2, f3, f4):
            top_row.addWidget(ff, stretch=1)
        lay.addLayout(top_row)

        # ── شبكة الحالات ─────────────────────────────────────
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
            row_i = idx // 4
            col_i = idx % 4
            grid.addWidget(frame, row_i, col_i)
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

        self._lbl_total.setText(str(summary.get("total") or 0))
        self._lbl_urgent.setText(str(summary.get("urgent") or 0))
        tv = summary.get("total_value") or 0
        tp = summary.get("total_paid") or 0
        self._lbl_total_value.setText(f"{tv:,.0f} ج")
        self._lbl_total_paid.setText(f"{tp:,.0f} ج")

        for status, lbl in self._status_chips.items():
            lbl.setText(str(summary.get(status) or 0))

        # آخر 20 طلب
        orders = fetch_all_orders(self.conn)[:20]
        STATUS_MAP = {
            "pending": "⏳ انتظار", "confirmed": "✅ مؤكد",
            "in_progress": "🔧 تنفيذ", "ready": "📦 جاهز",
            "delivered": "🚚 مُسلَّم", "cancelled": "❌ ملغي",
            "on_hold": "⏸ معلق",
        }
        TYPE_MAP = {"new": "جديد", "reorder": "إعادة طلب", "custom": "مخصص"}
        PRIORITY_MAP = {
            "low": "⬇ منخفض", "normal": "➡ عادي",
            "high": "⬆ عالي", "urgent": "🔴 عاجل",
        }
        STATUS_COLOR = {
            "pending": "#f59e0b", "confirmed": "#3b82f6",
            "in_progress": "#8b5cf6", "ready": "#10b981",
            "delivered": "#6b7280", "cancelled": "#ef4444",
            "on_hold": "#f97316",
        }

        self.recent_table.setRowCount(0)
        for o in orders:
            r = self.recent_table.rowCount()
            self.recent_table.insertRow(r)
            self.recent_table.setRowHeight(r, 40)

            num_item = QTableWidgetItem(o["order_number"])
            f = QFont()
            f.setWeight(QFont.Medium)
            num_item.setFont(f)
            self.recent_table.setItem(r, 0, num_item)
            self.recent_table.setItem(r, 1, QTableWidgetItem(o["customer_name"]))
            self.recent_table.setItem(r, 2, QTableWidgetItem(
                TYPE_MAP.get(o["order_type"], o["order_type"])
            ))

            status_item = QTableWidgetItem(STATUS_MAP.get(o["status"], o["status"]))
            status_item.setForeground(QColor(STATUS_COLOR.get(o["status"], "#555")))
            status_item.setTextAlignment(Qt.AlignCenter)
            self.recent_table.setItem(r, 3, status_item)

            self.recent_table.setItem(r, 4, QTableWidgetItem(
                PRIORITY_MAP.get(o["priority"], "")
            ))
            self.recent_table.setItem(r, 5, QTableWidgetItem(
                f"{(o['net_amount'] or 0):,.2f} ج"
            ))
            self.recent_table.setItem(r, 6, QTableWidgetItem(o["order_date"] or ""))