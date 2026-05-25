"""
ui/widgets/shared/tab_builder.py
=================================
TabBuilder — أداة بناء QTabWidget موحدة.

[تحديث v4]:
  - make_tabs يقبل accent من theme تلقائياً لو لم يُمرر.
  - إضافة make_scrollable_tabs لـ tabs كثيرة.
  - الـ styles كلها من theme.py بدل تعريف محلي.
"""

from PyQt5.QtWidgets import QTabWidget, QWidget
from ui.widgets.shared.panles_helper.theme import get_tab_style


def make_tabs(*tab_defs,
              accent: str = "#1565c0",
              style: str = "main") -> QTabWidget:
    """
    يبني QTabWidget رئيسي.

    tab_defs : tuples من (label, widget)
    accent   : لون التبويب المحدد
    style    : "main" | "inner" | "financial" | "minimal"

    الاستخدام:
        tabs = make_tabs(
            ("🏦  الحسابات", accounts_widget),
            ("📒  القيود",    journal_widget),
            accent="#1565c0",
        )
    """
    tabs = QTabWidget()

    if style == "inner":
        tabs.setStyleSheet(get_tab_style(accent=accent, size="small"))
    elif style in ("financial", "minimal"):
        tabs.setStyleSheet(
            f"QTabBar::tab:selected {{ color:{accent}; border-top:2px solid {accent}; }}"
        )
    else:
        tabs.setStyleSheet(get_tab_style(accent=accent, size="normal"))

    for label, widget in tab_defs:
        tabs.addTab(widget, label)

    return tabs


def make_inner_tabs(*tab_defs, accent: str = "#1565c0") -> QTabWidget:
    """
    يبني QTabWidget داخلي بـ style صغير.

    الاستخدام:
        tabs = make_inner_tabs(
            ("📊 الحسابات",   AccountsTreePanel(acc, ["asset"], "الأصول")),
            ("🏷️ التصنيفات", _GroupManagerPanel(acc, "asset")),
        )
    """
    return make_tabs(*tab_defs, accent=accent, style="inner")


def make_financial_tabs(*tab_defs, accent: str = "#1565c0") -> QTabWidget:
    """
    يبني QTabWidget بـ style القوائم المالية.

    الاستخدام:
        tabs = make_financial_tabs(
            ("📊 قائمة الدخل", IncomeStatementTab(conn)),
            ("👑 حقوق الملكية", OwnersEquityTab(conn)),
        )
    """
    return make_tabs(*tab_defs, accent=accent, style="financial")


def make_scrollable_tabs(*tab_defs,
                          accent: str = "#1565c0",
                          style: str = "main") -> QTabWidget:
    """
    يبني QTabWidget مع دعم التمرير الأفقي للتبويبات الكثيرة.
    """
    tabs = make_tabs(*tab_defs, accent=accent, style=style)
    tabs.setUsesScrollButtons(True)
    tabs.setElideMode(0)  # Qt.ElideNone
    return tabs