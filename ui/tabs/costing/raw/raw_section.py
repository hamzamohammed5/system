"""
ui/tabs/costing/raw/raw_section.py
====================================
_RawSection — القسم الرئيسي للخامات باستخدام BaseSection.

يستخدم النمط المشترك من BaseSection لعرض:
  - _InputPanel  (الجزء العلوي — فورم الإضافة/التعديل)
  - _TablePanel  (الجزء السفلي — جدول الخامات)

ملاحظة: لأن هذا القسم يختلف عن pattern الـ list+detail العادي
(هو input+table عمودي)، نستخدم QSplitter مباشرة مع تطبيق
نفس الأسلوب المتسق مع بقية التطبيق.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PyQt5.QtCore    import Qt

from ui.app_settings import _C

_SPLITTER_STYLE = f"""
    QSplitter::handle {{
        background: {_C['border']};
        border-top: 1px solid {_C['border_med']};
    }}
    QSplitter::handle:hover {{ background: {_C['accent_mid']}; }}
    QSplitter::handle:pressed {{ background: {_C['accent']}; }}
"""


class _RawSection(QWidget):
    """
    قسم الخامات — input panel فوق + table panel تحت.

    المعاملات:
        conn : اتصال قاعدة البيانات
    """

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self._conn = conn
        self._build()

    def _build(self):
        from .raw_input_panel import _InputPanel
        from .raw_table_panel import _TablePanel

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(_SPLITTER_STYLE)

        self._input = _InputPanel(self._conn)
        self._table = _TablePanel(self._conn, self._input)

        splitter.addWidget(self._input)
        splitter.addWidget(self._table)
        splitter.setSizes([300, 400])
        splitter.setCollapsible(0, True)
        splitter.setCollapsible(1, False)

        root.addWidget(splitter)