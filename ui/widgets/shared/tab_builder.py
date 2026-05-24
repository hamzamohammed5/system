"""
ui/widgets/shared/tab_builder.py
=================================
TabBuilder — أداة بناء QTabWidget موحدة.

تحل التكرار في:
  - accounting_tabs_builder.py    (_make_inner_tabs محلية)
  - financial_statements.py       (tabs setup مكرر)
  - investors_tab.py              (tabs styling مكرر)
  - journal_tab_widget.py         (splitter + tabs pattern)

الاستخدام:
    from ui.widgets.shared.tab_builder import make_tabs, make_inner_tabs

    # Tabs رئيسية (style كبير):
    tabs = make_tabs(
        ("🏦  الحسابات", accounts_widget),
        ("📒  القيود",    journal_widget),
    )

    # Tabs داخلية (style صغير):
    tabs = make_inner_tabs(
        ("📊 الحسابات",   tree_panel),
        ("🏷️ التصنيفات", group_manager),
    )

    # مع style مخصص:
    tabs = make_tabs(
        ("📊 قائمة الدخل", income_tab),
        accent="#6a1b9a",
    )
"""

from PyQt5.QtWidgets import QTabWidget, QWidget


# ══════════════════════════════════════════════════════════
# Styles جاهزة
# ══════════════════════════════════════════════════════════

def _main_tab_style(accent: str = "#1565c0") -> str:
    return f"""
        QTabWidget::pane {{
            border: none;
            background: #f9f9f9;
        }}
        QTabBar::tab {{
            background: #f0f0f0;
            border: 1px solid #ddd;
            border-bottom: none;
            padding: 8px 16px;
            margin-left: 2px;
            font-size: 11px;
            color: #555;
        }}
        QTabBar::tab:selected {{
            background: #ffffff;
            color: {accent};
            font-weight: bold;
            border-top: 2px solid {accent};
        }}
        QTabBar::tab:hover:!selected {{
            background: #e8f0fe;
            color: {accent};
        }}
    """


def _inner_tab_style(accent: str = "#1565c0") -> str:
    return f"""
        QTabWidget::pane {{ border: none; background: #fafafa; }}
        QTabBar::tab {{
            background: #f5f5f5;
            border: 1px solid #e0e0e0;
            border-bottom: none;
            padding: 6px 12px;
            font-size: 10px;
            color: #666;
        }}
        QTabBar::tab:selected {{
            background: white;
            color: {accent};
            font-weight: bold;
            border-top: 2px solid {accent};
        }}
        QTabBar::tab:hover:!selected {{ background: #eeeeee; }}
    """


def _financial_tab_style() -> str:
    return """
        QTabBar::tab:selected { color:#1565c0; border-top:2px solid #1565c0; }
    """


# ══════════════════════════════════════════════════════════
# الدوال العامة
# ══════════════════════════════════════════════════════════

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
        tabs.setStyleSheet(_inner_tab_style(accent))
    elif style == "financial":
        tabs.setStyleSheet(_financial_tab_style())
    elif style == "minimal":
        tabs.setStyleSheet(
            f"QTabBar::tab:selected {{ color:{accent}; border-top:2px solid {accent}; }}"
        )
    else:
        tabs.setStyleSheet(_main_tab_style(accent))

    for label, widget in tab_defs:
        tabs.addTab(widget, label)

    return tabs


def make_inner_tabs(*tab_defs, accent: str = "#1565c0") -> QTabWidget:
    """
    يبني QTabWidget داخلي بـ style صغير.

    بديل مباشر لـ _make_inner_tabs() في accounting_tabs_builder.py

    الاستخدام:
        tabs = make_inner_tabs(
            ("📊 الحسابات",   AccountsTreePanel(acc, ["asset"], "الأصول")),
            ("🏷️ التصنيفات", _GroupManagerPanel(acc, "asset")),
        )
    """
    return make_tabs(*tab_defs, accent=accent, style="inner")


def make_financial_tabs(*tab_defs) -> QTabWidget:
    """
    يبني QTabWidget بـ style القوائم المالية.

    الاستخدام:
        tabs = make_financial_tabs(
            ("📊 قائمة الدخل", IncomeStatementTab(conn)),
            ("👑 حقوق الملكية", OwnersEquityTab(conn)),
        )
    """
    return make_tabs(*tab_defs, style="financial")