"""
ui/widgets/shared/base_detail_panel.py
========================================
BaseDetailPanel — قاعدة مشتركة لكل لوحات التفاصيل.

توفر:
  - DetailHeader مع stat cards وأزرار
  - scroll area للمحتوى
  - EmptyState لما ما في اختيار
  - signals: saved(int), deleted()

الاستخدام:
    class MyDetailPanel(BaseDetailPanel):
        def _build_content(self, lay):
            # أضف widgets على lay
            ...

        def _fill_data(self, data: dict):
            # ملء البيانات في الـ widgets
            ...

        def _load_data(self, item_id: int) -> dict:
            return fetch_item(self.conn, item_id)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea,
)
from PyQt5.QtCore import Qt, pyqtSignal

from ui.widgets.shared.panels import DetailHeader, EmptyState
from ui.helpers import SCROLL_SS
from ui.app_settings import _C

_BG = "#f8f9fb"


class BaseDetailPanel(QWidget):
    """
    قاعدة مشتركة للوحات التفاصيل.

    Override:
      EMPTY_ICON, EMPTY_TITLE, EMPTY_SUBTITLE
      _build_content(lay), _fill_data(data), _load_data(item_id)
      _build_header_cards(), _build_header_buttons()
    """

    saved   = pyqtSignal(int)
    deleted = pyqtSignal()

    # ── قابل للـ override ──
    EMPTY_ICON     : str = "📋"
    EMPTY_TITLE    : str = "اختر عنصراً من القائمة"
    EMPTY_SUBTITLE : str = ""
    HEADER_BG      : str = "#ffffff"

    def __init__(self, conn=None, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._item_id   = None
        self._item_data = None
        self._build_base()
        self._show_empty()

    # ══════════════════════════════════════════════════════
    # override في الـ subclass
    # ══════════════════════════════════════════════════════

    def _build_header_cards(self):
        """أضف stat cards على الـ header."""
        pass

    def _build_header_buttons(self):
        """أضف أزرار على الـ header toolbar."""
        pass

    def _build_content(self, lay: QVBoxLayout):
        """ابن المحتوى الداخلي على الـ layout."""
        pass

    def _load_data(self, item_id: int):
        """يجلب بيانات العنصر من DB."""
        return None

    def _fill_data(self, data):
        """يملأ الـ widgets بالبيانات."""
        pass

    # ══════════════════════════════════════════════════════
    # بناء الواجهة الأساسية
    # ══════════════════════════════════════════════════════

    def _build_base(self):
        self.setStyleSheet(f"background:{_BG};")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ──
        self._hdr = DetailHeader(bg=self.HEADER_BG)
        self._build_header_cards()
        self._build_header_buttons()
        root.addWidget(self._hdr)

        # ── Scroll + Content ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(SCROLL_SS)

        content = QWidget()
        content.setStyleSheet(f"background:{_BG};")
        self._content_lay = QVBoxLayout(content)
        self._content_lay.setContentsMargins(16, 14, 16, 16)
        self._content_lay.setSpacing(12)

        self._build_content(self._content_lay)
        self._content_lay.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll, stretch=1)

        # ── Empty State ──
        self._empty = EmptyState(
            icon=self.EMPTY_ICON,
            title=self.EMPTY_TITLE,
            subtitle=self.EMPTY_SUBTITLE,
            style="plain", color="#6b7280", min_height=200,
        )
        root.addWidget(self._empty)

    # ══════════════════════════════════════════════════════
    # API خارجي
    # ══════════════════════════════════════════════════════

    def load_item(self, item_id: int):
        self._item_id   = item_id
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

    # ══════════════════════════════════════════════════════
    # helpers
    # ══════════════════════════════════════════════════════

    def _show_empty(self):
        self._empty.setVisible(True)
        self._hdr.setVisible(False)

    def _show_detail(self):
        self._empty.setVisible(False)
        self._hdr.setVisible(True)