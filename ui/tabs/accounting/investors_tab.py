"""
ui/tabs/accounting/investors_tab.py
====================================
InvestorsTab — تبويب المستثمرين.

إصلاح (v5):
  - يستمع لـ bus.company_data_changed ويعيد بناء كل الـ children
    بـ connections حية للشركة الجديدة.
  - _rebuild() يحذف الـ QTabWidget القديم وينشئ جديد.
  - هذا يضمن إن كل child يبدأ بـ conn للشركة الصح من أول لحظة.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter, QTabWidget,
)
from PyQt5.QtCore import Qt, QTimer

from db.inventory.investors_repo import _migrate_investors
from db.companies.company_state import company_state

from .investors._investor_form       import _InvestorForm
from .investors._investors_table     import _InvestorsTable
from .investors._investor_details    import _InvestorDetails
from .investors._link_to_entry_panel import _LinkToEntryPanel
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
from ui.events import bus


class InvestorsTab(SafeConnMixin, QWidget):
    def __init__(self, erp_conn, acc_conn, parent=None):
        super().__init__(parent)
        self._init_safe_conn(acc_conn, "accounting")
        self._erp_conn_ref = erp_conn
        self._company_id   = self._get_company_id()

        # مراجع للـ children الحية — نحتاجها لـ _on_investor_selected
        self._details: _InvestorDetails | None = None
        self._tabs_widget: QTabWidget | None = None

        self._migrate()
        self._build()
        bus.company_data_changed.connect(self._on_company_event)

    def _migrate(self):
        try:
            _migrate_investors(self._get_erp_conn())
        except Exception as e:
            print(f"[InvestorsTab] migrate error: {e}")

    def _get_erp_conn(self):
        try:
            self._erp_conn_ref.execute("SELECT 1")
            return self._erp_conn_ref
        except Exception:
            pass
        try:
            new = company_state._get_conn("erp")
            self._erp_conn_ref = new
            return new
        except Exception:
            return self._erp_conn_ref

    def _on_company_event(self, company_id: int):
        if self._on_company_event_safe(company_id):
            # [إصلاح] نعيد بناء كل الـ children بـ connections حية
            QTimer.singleShot(0, self._rebuild)

    def _build(self):
        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._tabs_widget = self._make_tabs()
        self._root_layout.addWidget(self._tabs_widget)

    def _rebuild(self):
        """يحذف الـ tabs القديمة وينشئ جديدة بـ connections للشركة النشطة."""
        if self._tabs_widget:
            self._root_layout.removeWidget(self._tabs_widget)
            self._tabs_widget.hide()
            self._tabs_widget.deleteLater()
            self._tabs_widget = None
            self._details = None

        self._migrate()
        self._tabs_widget = self._make_tabs()
        self._root_layout.addWidget(self._tabs_widget)

    def _make_tabs(self) -> QTabWidget:
        """ينشئ QTabWidget كامل بـ connections حية."""
        acc = self._get_safe_conn()
        erp = self._get_erp_conn()

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabBar::tab:selected { color:#1565c0; border-top:2px solid #1565c0; }
        """)

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

        form = _InvestorForm(acc, erp)
        splitter_h.addWidget(form)

        # نحتاج مرجع للـ details لـ _on_investor_selected
        self._details = _InvestorDetails(acc, erp)

        table = _InvestorsTable(
            acc, erp, form,
            on_select=self._on_investor_selected
        )
        splitter_h.addWidget(table)
        splitter_h.setSizes([310, 600])

        top_lay.addWidget(splitter_h)
        splitter_v.addWidget(top_widget)
        splitter_v.addWidget(self._details)
        splitter_v.setSizes([320, 320])

        main_lay.addWidget(splitter_v)
        tabs.addTab(main_widget, "👥  المستثمرون")
        tabs.addTab(
            _LinkToEntryPanel(acc, erp),
            "🔗  ربط بقيد محاسبي"
        )

        return tabs

    def _on_investor_selected(self, inv_id):
        if self._details is None:
            return
        if inv_id:
            self._details.load(inv_id)
        else:
            self._details.clear()