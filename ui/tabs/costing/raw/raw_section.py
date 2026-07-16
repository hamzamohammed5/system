"""
ui/tabs/costing/raw/raw_section.py
====================================
RawSection — القسم الرئيسي للخامات.

يرث من BaseSection — splitter أفقي بين الفورم (شمال) والجدول (يمين)،
بنفس آلية OrdersTab/CustomersTab (list + detail)، بدل FORM_POSITION
العمودي القديم. قابل للإخفاء بالسحب (COLLAPSIBLE من BaseSection).
"""

from PyQt5.QtWidgets import QWidget

from ui.widgets.base.section import BaseSection

from .raw_input_panel import RawInputPanel
from .raw_table_panel import RawTablePanel
from ui.constants import RAW_SECTION_LIST_MIN_W


class RawSection(BaseSection):
    """
    قسم الخامات:
      - list (يمين/يسار حسب LAYOUT_REVERSED)  = فورم إدخال/تعديل الخامة
      - detail                                = جدول الخامات

    BaseSection يبني الـ QSplitter الأفقي تلقائياً بالـ style الموحد،
    وبيسمح بإخفاء أي من الجانبين بالكامل بالسحب (COLLAPSIBLE = True).
    """

    LIST_MIN_W  = RAW_SECTION_LIST_MIN_W
    CONNECT_BUS = False    # كل panel بيتعامل مع bus بنفسه

    def _create_list(self):
        """الفورم — بيبقى في الجانب اللي BaseSection بيحطه أولاً بالـ splitter."""
        self._form_panel = RawInputPanel(conn=self.conn)
        return self._form_panel

    def _create_detail(self) -> QWidget:
        """الجدول."""
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
        # [Fix] كان بيكتب على self._table_panel.input_panel (من غير underscore)
        # بينما RawTablePanel.__init__ بيخزن القيمة في self._input_panel
        # (بـ underscore) — يعني كانت بتضبط attribute مختلف تمامًا وتفضل
        # self._input_panel = None طول الوقت، فزرار التعديل مكنش بيعمل حاجة.
        self._table_panel._input_panel = self._form_panel
