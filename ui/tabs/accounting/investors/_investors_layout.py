"""
ui/tabs/accounting/investors/_investors_layout.py
=================================================
_build_investors_tabs() — دالة بناء QTabWidget للمستثمرين.

[تحديث v3]:
  - منطق بناء اللوحة الرئيسية انتقل لـ _investors_panel.py
  - هذا الملف يبقى نقطة الدخول الوحيدة لبناء الـ tabs
"""

from ui.widgets.shared.tab_builder import make_tabs

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

    tabs = make_tabs(
        ("👥  المستثمرون",       main_widget),
        ("🔗  ربط بقيد محاسبي", _LinkToEntryPanel(acc_conn, erp_conn)),
        style="minimal",
        accent="#1565c0",
    )

    return tabs, details