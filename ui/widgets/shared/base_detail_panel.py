"""
ui/widgets/shared/base_detail_panel.py
========================================
BaseDetailPanel — قاعدة مشتركة لكل لوحات التفاصيل.

[تحديث v5]:
  - _DetailNotifMixin و _DetailStateMixin مستخرجتان لـ detail_panel_mixins.py
  - BusConnectedMixin للربط التلقائي
  - error handling واضح في load_item
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal

from ui.widgets.shared.panels import (
    DetailHeader,
    EmptyState,
    NotificationBar,
    get_scroll_style,
)
from ui.widgets.shared.shared_ui_mixins import BusConnectedMixin
from ui.widgets.shared.detail_panel_mixins import _DetailNotifMixin, _DetailStateMixin
from ui.app_settings import _C

_BG              = "#f8f9fb"
DETAIL_MIN_WIDTH = 500


class BaseDetailPanel(QWidget, BusConnectedMixin, _DetailNotifMixin, _DetailStateMixin):
    """
    قاعدة موحدة لكل لوحات التفاصيل.

    Override المطلوب:
        _load_data(item_id)  → يجلب بيانات العنصر
        _fill_data(data)     → يملأ الـ widgets بالبيانات

    Override الاختياري:
        _build_header_cards()   → stat cards في الهيدر
        _build_header_buttons() → أزرار في الهيدر
        _build_content(lay)     → محتوى صفحة التفاصيل
        _fill_header(data)      → يملأ الهيدر (افتراضياً data['name'])
        _on_data_changed()      → استجابة لـ bus
    """

    saved   = pyqtSignal(int)
    deleted = pyqtSignal()

    EMPTY_ICON     : str  = "📋"
    EMPTY_TITLE    : str  = "اختر عنصراً من القائمة"
    EMPTY_SUBTITLE : str  = ""
    HEADER_BG      : str  = "#ffffff"
    MIN_CONTENT_W  : int  = DETAIL_MIN_WIDTH
    CONNECT_BUS    : bool = False

    def __init__(self, conn=None, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._item_id   = None
        self._item_data = None
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumWidth(300)
        self._build_base()
        self._set_mode(has_data=False)

        if self.CONNECT_BUS:
            self._connect_bus(data=True)

    # ── override في الـ subclass ──────────────────────────

    def _build_header_cards(self):
        pass

    def _build_header_buttons(self):
        pass

    def _build_content(self, lay: QVBoxLayout):
        pass

    def _load_data(self, item_id: int):
        return None

    def _fill_data(self, data: dict):
        pass

    def _fill_header(self, data: dict):
        self._hdr.set_title(data.get("name", "─"))

    def _on_data_changed(self):
        if self._item_id is not None:
            self.load_item(self._item_id)

    # ── بناء الواجهة ──────────────────────────────────────

    def _build_base(self):
        self.setStyleSheet(f"background:{_BG};")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Notification Bar ──
        self._notif = NotificationBar(show_dismiss=True)
        root.addWidget(self._notif)

        # ── Scroll Area ──
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

        # ── Detail Header ──
        self._hdr = DetailHeader(bg=self.HEADER_BG)
        self._build_header_cards()
        self._build_header_buttons()
        inner_lay.addWidget(self._hdr)

        # ── Content ──
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

        # ── Empty State ──
        self._empty = EmptyState(
            icon=self.EMPTY_ICON,
            title=self.EMPTY_TITLE,
            subtitle=self.EMPTY_SUBTITLE,
            style="plain", color="#6b7280", min_height=200,
        )
        root.addWidget(self._empty)

    # ── public API ────────────────────────────────────────

    def load_item(self, item_id: int):
        """يحمّل بيانات عنصر ويعرضها."""
        self._item_id = item_id
        try:
            data = self._load_data(item_id)
        except Exception as e:
            self.show_error(f"خطأ في تحميل البيانات: {e}")
            return

        self._item_data = dict(data) if data else None
        if not self._item_data:
            self._set_mode(has_data=False)
            return

        self._set_mode(has_data=True)
        self._fill_header(self._item_data)
        self._fill_data(self._item_data)

    def clear(self):
        """يمسح التفاصيل ويعرض الـ empty state."""
        self._item_id   = None
        self._item_data = None
        self._notif.hide_bar()
        self._set_mode(has_data=False)

    # ── خصائص ────────────────────────────────────────────

    @property
    def item_id(self) -> int | None:
        return self._item_id

    @property
    def item_data(self) -> dict | None:
        return self._item_data

    @property
    def header(self) -> DetailHeader:
        return self._hdr

    @property
    def content_layout(self) -> QVBoxLayout:
        return self._content_lay