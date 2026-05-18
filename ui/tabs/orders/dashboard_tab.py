"""
ui/tabs/orders/dashboard_tab.py
================================
لوحة متابعة الطلبات — إحصائيات وملخص سريع.

✅ يستخدم shared panels بالكامل (make_stat_card_simple, make_status_chip, CardGrid)
✅ الجدول Fixed — لا يتمدد مع النافذة
✅ مقسّم على ملفات منفصلة في مجلد dashboard/
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea,
    QSizePolicy,
)
from PyQt5.QtCore import Qt

from db.orders.orders_repo import fetch_orders_summary, fetch_all_orders

from .dashboard._top_cards    import build_top_cards
from .dashboard._status_grid  import build_status_grid
from .dashboard._recent_table import build_recent_table, fill_recent_table


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

        # ── بطاقات الإحصائيات العلوية ──
        lay.addLayout(build_top_cards(self))

        # ── عنوان شبكة الحالات ──
        lbl_status = QLabel("توزيع الطلبات حسب الحالة")
        lbl_status.setStyleSheet(
            "font-weight:bold; color:#374151; background:transparent;"
        )
        lay.addWidget(lbl_status)

        # ── شبكة شرائح الحالات ──
        lay.addWidget(build_status_grid(self))

        # ── رأس جدول آخر الطلبات ──
        recent_hdr = QHBoxLayout()
        lbl_recent = QLabel("آخر الطلبات")
        lbl_recent.setStyleSheet(
            "font-weight:bold; color:#374151; background:transparent;"
        )
        btn_refresh = QPushButton("↺  تحديث")
        btn_refresh.setMinimumHeight(30)
        btn_refresh.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
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

        # ── جدول آخر الطلبات (Fixed) ──
        lay.addWidget(build_recent_table(self))
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

        orders = fetch_all_orders(self.conn)[:20]
        fill_recent_table(self, orders)