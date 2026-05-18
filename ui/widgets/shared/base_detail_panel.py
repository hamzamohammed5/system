"""
ui/widgets/shared/base_detail_panel.py
========================================
BaseDetailPanel — قاعدة مشتركة لكل لوحات التفاصيل.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal

from ui.widgets.shared.panels import DetailHeader, EmptyState
from ui.helpers import make_detail_scroll, set_detail_content
from ui.app_settings import _C

_BG = "#f8f9fb"

# الحد الأدنى لعرض الـ detail panel قبل ظهور الـ horizontal scroll
DETAIL_MIN_WIDTH = 500


class BaseDetailPanel(QWidget):
    saved   = pyqtSignal(int)
    deleted = pyqtSignal()

    EMPTY_ICON     : str = "📋"
    EMPTY_TITLE    : str = "اختر عنصراً من القائمة"
    EMPTY_SUBTITLE : str = ""
    HEADER_BG      : str = "#ffffff"
    # اضبط هذا في الـ subclass لو المحتوى أعرض من 500px
    MIN_CONTENT_W  : int = DETAIL_MIN_WIDTH

    def __init__(self, conn=None, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._item_id   = None
        self._item_data = None

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # حد أدنى للعرض — لما الـ splitter يضغط أقل منه يظهر الـ horizontal scroll
        self.setMinimumWidth(DETAIL_MIN_WIDTH)
        self._build_base()
        self._show_empty()

    def _build_header_cards(self):
        pass

    def _build_header_buttons(self):
        pass

    def _build_content(self, lay: QVBoxLayout):
        pass

    def _load_data(self, item_id: int):
        return None

    def _fill_data(self, data):
        pass

    def _build_base(self):
        self.setStyleSheet(f"background:{_BG};")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header (خارج الـ scroll — ثابت في الأعلى) ──
        self._hdr = DetailHeader(bg=self.HEADER_BG)
        self._build_header_cards()
        self._build_header_buttons()
        root.addWidget(self._hdr)

        # ── Scroll + Content ──
        scroll = make_detail_scroll(min_content_width=self.MIN_CONTENT_W)

        content = QWidget()
        self._content_lay = QVBoxLayout(content)
        self._content_lay.setContentsMargins(16, 14, 16, 16)
        self._content_lay.setSpacing(12)

        self._build_content(self._content_lay)
        self._content_lay.addStretch()

        set_detail_content(scroll, content, bg=_BG)
        root.addWidget(scroll, stretch=1)

        # ── Empty State ──
        self._empty = EmptyState(
            icon=self.EMPTY_ICON,
            title=self.EMPTY_TITLE,
            subtitle=self.EMPTY_SUBTITLE,
            style="plain", color="#6b7280", min_height=200,
        )
        root.addWidget(self._empty)

    def load_item(self, item_id: int):
        self._item_id = item_id
        data = self._load_data(item_id)
        self._item_data = dict(data) if data else None
        if not self._item_data:
            return
        self._show_detail()
        self._fill_data(self._item_data)

    def clear(self):
        self._item_id   = None
        self._item_data = None
        self._show_empty()

    def _show_empty(self):
        self._empty.setVisible(True)
        self._hdr.setVisible(False)

    def _show_detail(self):
        self._empty.setVisible(False)
        self._hdr.setVisible(True)