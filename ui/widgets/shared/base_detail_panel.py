"""
ui/widgets/shared/base_detail_panel.py
========================================
BaseDetailPanel — قاعدة مشتركة لكل لوحات التفاصيل.

[تحديث v2]:
  - يستخدم get_scroll_style() من theme بدل ستايل inline مكرر
  - يستخدم EmptyState من panels مباشرة
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal

from ui.widgets.shared.panels import DetailHeader, EmptyState, get_scroll_style
from ui.app_settings import _C

_BG              = "#f8f9fb"
DETAIL_MIN_WIDTH = 500


class BaseDetailPanel(QWidget):
    saved   = pyqtSignal(int)
    deleted = pyqtSignal()

    EMPTY_ICON     : str = "📋"
    EMPTY_TITLE    : str = "اختر عنصراً من القائمة"
    EMPTY_SUBTITLE : str = ""
    HEADER_BG      : str = "#ffffff"
    MIN_CONTENT_W  : int = DETAIL_MIN_WIDTH

    def __init__(self, conn=None, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._item_id   = None
        self._item_data = None
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumWidth(300)
        self._build_base()
        self._show_empty()

    # ── override في الـ subclass ──────────────────────────

    def _build_header_cards(self):   pass
    def _build_header_buttons(self): pass
    def _build_content(self, lay: QVBoxLayout): pass
    def _load_data(self, item_id: int): return None
    def _fill_data(self, data): pass

    # ── بناء الواجهة ──────────────────────────────────────

    def _build_base(self):
        self.setStyleSheet(f"background:{_BG};")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Scroll يلف كل حاجة — يستخدم get_scroll_style() الموحد
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll.setStyleSheet(get_scroll_style(width=6))

        self._inner = QWidget()
        self._inner.setMinimumWidth(self.MIN_CONTENT_W)
        self._inner.setStyleSheet(f"background:{_BG};")

        inner_lay = QVBoxLayout(self._inner)
        inner_lay.setContentsMargins(0, 0, 0, 0)
        inner_lay.setSpacing(0)

        # Header
        self._hdr = DetailHeader(bg=self.HEADER_BG)
        self._build_header_cards()
        self._build_header_buttons()
        inner_lay.addWidget(self._hdr)

        # Content
        content = QWidget()
        content.setStyleSheet(f"background:{_BG};")
        self._content_lay = QVBoxLayout(content)
        self._content_lay.setContentsMargins(16, 14, 16, 16)
        self._content_lay.setSpacing(12)
        self._build_content(self._content_lay)
        self._content_lay.addStretch()

        inner_lay.addWidget(content, stretch=1)
        self._scroll.setWidget(self._inner)
        root.addWidget(self._scroll, stretch=1)

        # Empty state
        self._empty = EmptyState(
            icon=self.EMPTY_ICON,
            title=self.EMPTY_TITLE,
            subtitle=self.EMPTY_SUBTITLE,
            style="plain", color="#6b7280", min_height=200,
        )
        root.addWidget(self._empty)

    # ── public API ────────────────────────────────────────

    def load_item(self, item_id: int):
        self._item_id   = item_id
        data            = self._load_data(item_id)
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
        self._scroll.setVisible(False)
        self._empty.setVisible(True)

    def _show_detail(self):
        self._empty.setVisible(False)
        self._scroll.setVisible(True)
        self._hdr.setVisible(True)