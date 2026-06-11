"""
ui/tabs/accounting/journal/journal_tab_widget.py
=================================================
JournalTab — التبويب الرئيسي لليومية.

مُستخرج من journal_tree_table.py لتقليل حجمه.
يستورد _JournalTreeTable و _JournalForm ويجمعهم في splitter.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PyQt5.QtCore import Qt, QTimer

from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.core.events import bus
from ui.theme import _C

from .journal_tree_table import _JournalTreeTable
from .journal_form       import _JournalForm


class JournalTab(SafeConnMixin, QWidget):
    """
    التبويب الرئيسي لليومية — splitter رأسي بين الفورم والجدول.

    يستمع لـ bus.company_data_changed ويعيد بناء الـ children
    بـ connections حية للشركة الجديدة.
    """

    def __init__(self, conn, erp_conn=None, parent=None):
        super().__init__(parent)
        self._init_safe_conn(conn, "accounting")
        self._erp_conn   = erp_conn
        self._company_id = self._get_company_id()
        self._splitter   = None
        self._form       = None
        self._tree_table = None
        self._build()
        bus.company_data_changed.connect(self._on_company_event)

    def _on_company_event(self, company_id: int):
        if self._on_company_event_safe(company_id):
            QTimer.singleShot(0, self._rebuild_children)

    def _get_erp_conn(self):
        try:
            if self._erp_conn is not None:
                self._erp_conn.execute("SELECT 1")
                return self._erp_conn
        except Exception:
            pass
        try:
            from db.companies.company_state import company_state
            new = company_state.get_erp_conn()
            self._erp_conn = new
            return new
        except Exception:
            return self._erp_conn

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self._splitter = QSplitter(Qt.Vertical)
        self._splitter.setHandleWidth(6)
        self._splitter.setStyleSheet(
            f"QSplitter::handle {{ background:{_C['border']}; }}"            f"QSplitter::handle:hover {{ background:{_C['badge_dr_bg']}; }}"
        )

        conn = self._get_safe_conn()
        erp  = self._get_erp_conn()

        self._form       = _JournalForm(conn, erp)
        self._tree_table = _JournalTreeTable(conn)

        self._splitter.addWidget(self._form)
        self._splitter.addWidget(self._tree_table)
        self._splitter.setSizes([440, 360])
        self._splitter.setCollapsible(0, True)

        root.addWidget(self._splitter)

    def _rebuild_children(self):
        if self._splitter is None:
            return

        sizes = self._splitter.sizes()

        if self._form:
            self._splitter.widget(0).hide()
            old_form = self._form
            self._form = None
            old_form.deleteLater()

        if self._tree_table:
            if self._splitter.count() > 1:
                self._splitter.widget(1).hide()
            old_table = self._tree_table
            self._tree_table = None
            old_table.deleteLater()

        conn = self._get_safe_conn()
        erp  = self._get_erp_conn()

        self._form       = _JournalForm(conn, erp)
        self._tree_table = _JournalTreeTable(conn)

        self._splitter.addWidget(self._form)
        self._splitter.addWidget(self._tree_table)

        if sizes and len(sizes) >= 2:
            self._splitter.setSizes(sizes)
        else:
            self._splitter.setSizes([440, 360])