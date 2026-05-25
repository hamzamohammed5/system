"""
ui/tabs/accounting/journal/journal_tab_widget.py
=================================================
JournalTab — التبويب الرئيسي لليومية.

مُستخرج من journal_tree_table.py لتقليل حجمه.
يستورد _JournalTreeTable و _JournalForm ويجمعهم في splitter.

[إصلاح v2]:
  - DualConnMixin بدل _get_erp_conn() المعرَّفة يدوياً مع fallback يدوي.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PyQt5.QtCore import Qt, QTimer

from ui.widgets.shared.safe_conn_mixin import DualConnMixin
from ui.events import bus

from .journal_tree_table import _JournalTreeTable
from .journal_form       import _JournalForm


class JournalTab(DualConnMixin, QWidget):
    """
    التبويب الرئيسي لليومية — splitter رأسي بين الفورم والجدول.

    يستمع لـ bus.company_data_changed ويعيد بناء الـ children
    بـ connections حية للشركة الجديدة.
    """

    def __init__(self, conn, erp_conn=None, parent=None):
        super().__init__(parent)
        self._init_dual_conn(conn, erp_conn)
        self._splitter   = None
        self._form       = None
        self._tree_table = None
        self._build()
        bus.company_data_changed.connect(self._on_company_event)

    def _on_company_event(self, company_id: int):
        if self._on_dual_company_event(company_id):
            QTimer.singleShot(0, self._rebuild_children)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self._splitter = QSplitter(Qt.Vertical)
        self._splitter.setHandleWidth(6)
        self._splitter.setStyleSheet("""
            QSplitter::handle { background:#e0e0e0; }
            QSplitter::handle:hover { background:#bbdefb; }
        """)

        self._form       = _JournalForm(self._get_safe_conn(), self._get_erp_conn())
        self._tree_table = _JournalTreeTable(self._get_safe_conn())

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

        self._form       = _JournalForm(self._get_safe_conn(), self._get_erp_conn())
        self._tree_table = _JournalTreeTable(self._get_safe_conn())

        self._splitter.addWidget(self._form)
        self._splitter.addWidget(self._tree_table)

        if sizes and len(sizes) >= 2:
            self._splitter.setSizes(sizes)
        else:
            self._splitter.setSizes([440, 360])