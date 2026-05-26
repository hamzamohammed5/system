"""
ui/helpers.py
=============
مساعدات UI مشتركة — بعد الـ refactoring.

يحتوي فقط على ما لا يوجد له مكان في ui/widgets/:
  - SCROLL_SS / _SCROLL_SS
  - _spin / _stat_card
  - live_conn
  - make_detail_scroll / set_detail_content
  - EditModeMixin           ← من ui.widgets.mixins.edit
  - buttons_row
  - bold_label / section_label
  - danger_button / success_button
  - setup_table_columns / confirm_delete
"""

from PyQt5.QtWidgets import (
    QLabel, QHBoxLayout,
    QWidget, QTableWidget, QScrollArea, QPushButton,
)
from PyQt5.QtGui  import QFont
from PyQt5.QtCore import Qt

from ui.widgets.mixins.edit       import EditModeMixin         # noqa: F401
from ui.widgets.dialogs.confirm   import confirm_delete        # noqa: F401
from ui.widgets.components.button import make_btn
from ui.widgets.theme.styles      import scroll_style

SCROLL_SS  = scroll_style()
_SCROLL_SS = SCROLL_SS


# ── _spin ────────────────────────────────────────────────────────────────

def _spin(max_=999_999_999, dec=2):
    """
    QDoubleSpinBox بسيط.
    في الكود الجديد استخدم AmountSpinBox من ui.widgets.forms.inputs.
    """
    from ui.widgets.forms.inputs import AmountSpinBox
    return AmountSpinBox(max_=max_, dec=dec, height=30)


# ── _stat_card ───────────────────────────────────────────────────────────

def _stat_card(label: str, color: str = "#1565c0"):
    """
    يرجع (QFrame, QLabel_value).
    في الكود الجديد استخدم StatCard من ui.widgets.components.stat_row.
    """
    from ui.widgets.components.stat_row import StatCard
    card = StatCard(title=label, color=color, compact=True)
    return card, card.value_label()


# ── buttons_row ──────────────────────────────────────────────────────────

def buttons_row(*buttons) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(6)
    for btn in buttons:
        row.addWidget(btn)
    row.addStretch()
    return row


# ── live_conn ────────────────────────────────────────────────────────────

def live_conn(stored_conn=None, db: str = "erp"):
    """
    يرجع connection صالح دايماً.
    في الكود الجديد استخدم LiveConnMixin من ui.widgets.core.conn.
    """
    if stored_conn is not None:
        try:
            stored_conn.execute("SELECT 1")
            return stored_conn
        except Exception:
            pass
    from db.companies.company_state import company_state
    return company_state._get_conn(db)


# ── make_detail_scroll / set_detail_content ──────────────────────────────

def make_detail_scroll(min_content_width: int = 520) -> QScrollArea:
    """
    QScrollArea للـ detail panels.
    في الكود الجديد استخدم wrap_in_scroll() من ui.widgets.theme.styles.
    """
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll.setStyleSheet(SCROLL_SS)
    scroll._min_content_width = min_content_width
    return scroll


def set_detail_content(scroll: QScrollArea, content: QWidget,
                       bg: str = "#f8f9fb"):
    min_w = getattr(scroll, '_min_content_width', 520)
    content.setStyleSheet(f"background:{bg};")
    content.setMinimumWidth(min_w)
    scroll.setWidget(content)


# ── label helpers ────────────────────────────────────────────────────────

def bold_label(text: str) -> QLabel:
    lbl = QLabel(text)
    f = QFont()
    f.setBold(True)
    lbl.setFont(f)
    return lbl


def section_label(text: str) -> QLabel:
    """في الكود الجديد استخدم section_title() من ui.widgets.panels.form_parts."""
    from ui.widgets.panels.form_parts import section_title
    return section_title(text)


# ── button helpers ───────────────────────────────────────────────────────

def danger_button(text: str) -> QPushButton:
    return make_btn(text, "danger")


def success_button(text: str) -> QPushButton:
    return make_btn(text, "success")


# ── setup_table_columns ──────────────────────────────────────────────────

def setup_table_columns(
    table: QTableWidget,
    widths: dict = None,
    stretch_col: int = -1,
    min_width: int = 50,
):
    """في الكود الجديد استخدم auto_fit_columns() من ui.widgets.tables.items."""
    from PyQt5.QtWidgets import QHeaderView
    hh = table.horizontalHeader()
    n  = table.columnCount()
    for i in range(n):
        if i == stretch_col:
            hh.setSectionResizeMode(i, QHeaderView.Stretch)
        else:
            hh.setSectionResizeMode(i, QHeaderView.Interactive)
            if widths and i in widths:
                table.setColumnWidth(i, widths[i])
    hh.setMinimumSectionSize(min_width)
