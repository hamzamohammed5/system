"""
ui/tabs/design/dimension_sets/_values_panel.py
=====================================
لوحة إدخال قيم المقاسات — تصميم جديد:

  يسار : قايمة مجموعات المقاسات (بطاقات واضحة)
  يمين : جدول instances + قيمها لما تختار مجموعة
  Popup: نافذة تعديل/إضافة instance
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter,
)
from PyQt5.QtCore import Qt


from .values_panel._setsList_panel  import _SetsListPanel
from .values_panel._instances_table import  _InstancesTable

# ──────────────────────────────────────────────────────────
# ثوابت الستايل
# ──────────────────────────────────────────────────────────


_BLUE_MID   = "#bbdefb"
_GREEN      = "#2e7d32"
_GRAY_BG    = "#f8f9fc"
_BORDER     = "#e0e7f3"


# ══════════════════════════════════════════════════════════
# اللوحة الرئيسية
# ══════════════════════════════════════════════════════════

class _ValuesPanel(QWidget):
    """
    اللوحة الرئيسية — Splitter:
      يسار: قايمة بطاقات المجموعات
      يمين: جدول instances + toolbar
    """

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn    = conn
        self._set_id = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(4)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {_BORDER};
            }}
            QSplitter::handle:hover {{
                background: {_BLUE_MID};
            }}
        """)

        self._sets_list = _SetsListPanel(self.conn)
        self._sets_list.setMinimumWidth(240)
        self._sets_list.setMaximumWidth(360)
        self._sets_list.setStyleSheet(f"""
            background: {_GRAY_BG};
            border-right: 1px solid {_BORDER};
        """)

        self._table = _InstancesTable(self.conn)
        self._table.setStyleSheet("background: white;")

        self._sets_list.set_selected.connect(self._on_set_selected)

        splitter.addWidget(self._sets_list)
        splitter.addWidget(self._table)
        splitter.setSizes([280, 720])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        root.addWidget(splitter)

    def load_set(self, set_id: int):
        self._set_id = set_id
        self._sets_list._on_card_click(set_id)

    def _on_set_selected(self, set_id: int):
        self._set_id = set_id
        self._table.load_set(set_id)

    def clear(self):
        self._set_id = None
        self._table.clear()