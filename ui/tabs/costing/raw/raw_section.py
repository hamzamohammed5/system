"""
ui/tabs/costing/raw/raw_section.py
====================================
RawSection — القسم الرئيسي للخامات.

يرث من BaseSection — لا QSplitter يدوي، لا style مكررة.
"""

from ui.widgets.base.section import BaseSection

from .raw_input_panel import RawInputPanel
from .raw_table_panel import RawTablePanel
from PyQt5.QtWidgets import QWidget
from ui.constants import RAW_SECTION_LIST_MIN_W

class RawSection(BaseSection):
    """
    قسم الخامات:
      - الفورم فوق  (FORM_POSITION = "top")
      - الجدول تحت

    BaseSection يبني الـ QSplitter تلقائياً بالـ style الموحد.
    """

    FORM_POSITION = "top"
    LIST_MIN_W    = RAW_SECTION_LIST_MIN_W
    CONNECT_BUS   = False    # كل panel بيتعامل مع bus بنفسه

    def _create_form(self):
        self._form_panel = RawInputPanel(conn=self.conn)
        return self._form_panel

    def _create_list(self):
        self._table_panel = RawTablePanel(
            conn=self.conn,
            input_panel=None,
        )
        return self._table_panel

    def _connect_signals(self):
        # بعد حفظ الفورم → نحدّث الجدول
        self._form_panel.saved.connect(self._table_panel.refresh)
        # double-click على صف → نفتحه في الفورم
        if hasattr(self._table_panel, "item_double_clicked"):
            self._table_panel.item_double_clicked.connect(
                self._form_panel.load_for_edit
            )
        # نربط input_panel بعد التأكد إن الاثنين اتبنوا
        if hasattr(self._table_panel, "input_panel"):
            self._table_panel.input_panel = self._form_panel
    def _create_detail(self) -> QWidget:
        w = QWidget()
        w.hide()
        w.setMaximumWidth(0)
        return w