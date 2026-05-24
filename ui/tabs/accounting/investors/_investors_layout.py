"""
ui/tabs/accounting/investors/_investors_layout.py
=================================================
_build_investors_tabs() — دالة بناء QTabWidget للمستثمرين.

[تحديث v2]: يستخدم make_tabs من tab_builder بشكل صحيح.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PyQt5.QtCore import Qt

from ui.widgets.shared.tab_builder import make_tabs

from ._investor_form       import _InvestorForm
from ._investors_table     import _InvestorsTable
from ._investor_details    import _InvestorDetails
from ._link_to_entry_panel import _LinkToEntryPanel


def _build_main_tab(acc_conn, erp_conn, on_investor_selected) -> tuple:
    """
    يبني الـ tab الرئيسي للمستثمرين (جدول + فورم + تفاصيل).
    يرجع (main_widget, details)
    """
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

    form    = _InvestorForm(acc_conn, erp_conn)
    details = _InvestorDetails(acc_conn, erp_conn)
    table   = _InvestorsTable(
        acc_conn, erp_conn, form,
        on_select=on_investor_selected
    )

    splitter_h.addWidget(form)
    splitter_h.addWidget(table)
    splitter_h.setSizes([310, 600])

    top_lay.addWidget(splitter_h)
    splitter_v.addWidget(top_widget)
    splitter_v.addWidget(details)
    splitter_v.setSizes([320, 320])

    main_lay.addWidget(splitter_v)
    return main_widget, details


def build_investors_tabs(acc_conn, erp_conn, on_investor_selected) -> tuple:
    """
    يبني QTabWidget كامل لقسم المستثمرين.

    يرجع: (QTabWidget, _InvestorDetails)
    """
    main_widget, details = _build_main_tab(acc_conn, erp_conn, on_investor_selected)

    tabs = make_tabs(
        ("👥  المستثمرون",       main_widget),
        ("🔗  ربط بقيد محاسبي", _LinkToEntryPanel(acc_conn, erp_conn)),
        style="minimal",
        accent="#1565c0",
    )

    return tabs, details