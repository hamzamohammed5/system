"""
ui/tabs/accounting/investors/_investors_layout.py
=================================================
build_investors_tabs() — دالة بناء QTabWidget للمستثمرين.
"""

from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtCore import Qt

from ui.widgets.theme.layout_styles import tab_style
from ui.widgets.core.i18n import tr

from ._investors_panel     import build_main_panel
from ._link_to_entry_panel import _LinkToEntryPanel


def build_investors_tabs(acc_conn, erp_conn, on_investor_selected) -> tuple:
    """
    يبني QTabWidget كامل لقسم المستثمرين.
    يرجع: (QTabWidget, _InvestorDetails)
    """
    main_widget, details = build_main_panel(
        acc_conn, erp_conn, on_investor_selected
    )

    tabs = QTabWidget()
    tabs.setLayoutDirection(Qt.RightToLeft)
    tabs.setStyleSheet(tab_style())
    tabs.addTab(main_widget,                             tr("investors_tab_title"))
    tabs.addTab(_LinkToEntryPanel(acc_conn, erp_conn),   tr("link_to_entry_tab_title"))

    return tabs, details