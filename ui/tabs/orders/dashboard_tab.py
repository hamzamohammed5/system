"""
ui/tabs/orders/dashboard_tab.py
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QSizePolicy,
)
from PyQt5.QtCore import Qt

from db.orders.orders_repo import fetch_orders_summary, fetch_all_orders
from ui.widgets.core.i18n import tr

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
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        scroll.setMaximumHeight(340)

        top_content = QWidget()
        top_lay = QVBoxLayout(top_content)
        top_lay.setContentsMargins(20, 16, 20, 12)
        top_lay.setSpacing(16)

        top_lay.addLayout(build_top_cards(self))

        lbl_status = QLabel(tr("dashboard_status_dist"))
        lbl_status.setStyleSheet("font-weight:bold;")
        top_lay.addWidget(lbl_status)
        top_lay.addWidget(build_status_grid(self))

        scroll.setWidget(top_content)
        root.addWidget(scroll)

        hdr_widget = QWidget()
        recent_hdr = QHBoxLayout(hdr_widget)
        recent_hdr.setContentsMargins(20, 8, 20, 4)

        lbl_recent = QLabel(tr("dashboard_recent_orders"))
        lbl_recent.setStyleSheet("font-weight:bold;")

        btn_refresh = QPushButton(tr("order_refresh_btn"))
        btn_refresh.setMinimumHeight(30)
        btn_refresh.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn_refresh.clicked.connect(self.refresh)

        recent_hdr.addWidget(lbl_recent)
        recent_hdr.addStretch()
        recent_hdr.addWidget(btn_refresh)
        root.addWidget(hdr_widget)

        table_container = QWidget()
        tc_lay = QVBoxLayout(table_container)
        tc_lay.setContentsMargins(20, 0, 20, 16)
        tc_lay.setSpacing(0)
        tc_lay.addWidget(build_recent_table(self))
        root.addWidget(table_container, stretch=1)

    def refresh(self):
        summary = fetch_orders_summary(self.conn)

        self._lbl_total.setText(str(summary.get("total") or 0))
        self._lbl_urgent.setText(str(summary.get("urgent") or 0))
        self._lbl_total_value.setText(f"{(summary.get('total_value') or 0):,.0f} {tr('currency_sym')}")
        self._lbl_total_paid.setText(f"{(summary.get('total_paid') or 0):,.0f} {tr('currency_sym')}")

        for status, lbl in self._status_chips.items():
            lbl.setText(str(summary.get(status) or 0))

        fill_recent_table(self, fetch_all_orders(self.conn)[:20])