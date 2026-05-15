"""
ui/tabs/accounting/investors_tab.py
=====================================
InvestorsTab — التبويب الرئيسي للمستثمرين.

التقسيم الداخلي:
  investors/_helpers.py             → _spin, _stat_card, دوال جلب/ملء/تسجيل
  investors/_movement_dialog.py     → _MovementDialog
  investors/_investor_form.py       → _InvestorForm
  investors/_investors_table.py     → _InvestorsTable
  investors/_investor_details.py    → _InvestorDetails
  investors/_link_to_entry_panel.py → _LinkToEntryPanel
  investors_tab.py                  → InvestorsTab  (هذا الملف)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter, QTabWidget,
)
from PyQt5.QtCore import Qt

from db.inventory.investors_repo import _migrate_investors

from .investors._investor_form       import _InvestorForm
from .investors._investors_table     import _InvestorsTable
from .investors._investor_details    import _InvestorDetails
from .investors._link_to_entry_panel import _LinkToEntryPanel


class InvestorsTab(QWidget):
    def __init__(self, erp_conn, acc_conn, parent=None):
        super().__init__(parent)
        self.erp_conn = erp_conn
        self.acc_conn = acc_conn
        _migrate_investors(erp_conn)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabBar::tab:selected { color:#1565c0; border-top:2px solid #1565c0; }
        """)

        # ── تبويب 1: إدارة المستثمرين ──
        main_widget = QWidget()
        main_lay    = QVBoxLayout(main_widget)
        main_lay.setContentsMargins(0, 0, 0, 0)

        splitter_v = QSplitter(Qt.Vertical)
        splitter_v.setHandleWidth(6)
        splitter_v.setStyleSheet("""
            QSplitter::handle { background:#e0e0e0; }
            QSplitter::handle:hover { background:#bbdefb; }
        """)

        top_widget = QWidget()
        top_lay    = QVBoxLayout(top_widget)
        top_lay.setContentsMargins(0, 0, 0, 0)

        splitter_h = QSplitter(Qt.Horizontal)
        splitter_h.setHandleWidth(6)

        self._form = _InvestorForm(self.acc_conn, self.erp_conn)
        splitter_h.addWidget(self._form)

        self._table = _InvestorsTable(
            self.acc_conn, self.erp_conn,
            self._form,
            on_select=self._on_investor_selected
        )
        splitter_h.addWidget(self._table)
        splitter_h.setSizes([310, 600])

        top_lay.addWidget(splitter_h)
        splitter_v.addWidget(top_widget)

        self._details = _InvestorDetails(self.acc_conn, self.erp_conn)
        splitter_v.addWidget(self._details)
        splitter_v.setSizes([320, 320])

        main_lay.addWidget(splitter_v)
        tabs.addTab(main_widget, "👥  المستثمرون")

        # ── تبويب 2: ربط بقيد موجود ──
        tabs.addTab(
            _LinkToEntryPanel(self.acc_conn, self.erp_conn),
            "🔗  ربط بقيد محاسبي"
        )

        root.addWidget(tabs)

    def _on_investor_selected(self, inv_id):
        if inv_id:
            self._details.load(inv_id)
        else:
            self._details.clear()