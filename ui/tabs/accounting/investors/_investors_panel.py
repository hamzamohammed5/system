"""
ui/tabs/accounting/investors/_investors_panel.py
================================================
_InvestorsPanel — لوحة موحدة تجمع الجدول + الفورم في splitter أفقي.

[إصلاح v2]:
  - get_splitter_style من panels بدل ستايل inline يدوي
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PyQt5.QtCore import Qt

from ui.widgets.theme.table_styles import splitter_style as get_splitter_style

from ._investor_form   import _InvestorForm
from ._investors_table import _InvestorsTable


def build_main_panel(acc_conn, erp_conn,
                     on_investor_selected) -> tuple:
    """
    يبني اللوحة الرئيسية (فورم + جدول + تفاصيل).
    يرجع (main_widget, details_widget).
    """
    from ._investor_details import _InvestorDetails

    main_widget = QWidget()
    main_lay    = QVBoxLayout(main_widget)
    main_lay.setContentsMargins(0, 0, 0, 0)

    splitter_v = QSplitter(Qt.Vertical)
    splitter_v.setHandleWidth(6)
    splitter_v.setStyleSheet(get_splitter_style())

    top_widget = QWidget()
    top_lay    = QVBoxLayout(top_widget)
    top_lay.setContentsMargins(0, 0, 0, 0)

    splitter_h = QSplitter(Qt.Horizontal)
    splitter_h.setHandleWidth(6)
    splitter_h.setStyleSheet(get_splitter_style())

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