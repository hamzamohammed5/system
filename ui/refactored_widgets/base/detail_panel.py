"""
widgets/base/detail_panel.py
=============================
BaseDetailPanel — قاعدة مشتركة لكل لوحات التفاصيل.

التغييرات عن النسخة القديمة:
  - _DetailNotifMixin و _DetailStateMixin مدمجتان هنا مباشرة
  - _set_mode موحدة بدون aliases قديمة
  - _fill_header hook افتراضي يضبط العنوان من data['name']
  - BusConnectedMixin بدل boilerplate يدوي
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QSizePolicy
from PyQt5.QtCore    import Qt, pyqtSignal

from ui.app_settings import _C
from ..panels.header  import DetailHeader
from ..panels.state   import EmptyState
from ..panels.notify  import NotificationBar
from ..mixins.bus     import BusConnectedMixin

_BG = "#f8f9fb"


class BaseDetailPanel(QWidget, BusConnectedMixin):
    """
    قاعدة مشتركة لكل لوحات التفاصيل.

    Override المطلوب:
        _load_data(item_id)  → dict | None
        _fill_data(data)
        _build_content(layout)

    Override الاختياري:
        _build_header_cards()
        _build_header_buttons()
        _fill_header(data)
        _on_data_changed()
        EMPTY_ICON, EMPTY_TITLE, EMPTY_SUBTITLE, HEADER_BG
        MIN_CONTENT_W, CONNECT_BUS
    """

    saved   = pyqtSignal(int)
    deleted = pyqtSignal()

    EMPTY_ICON     : str  = "📋"
    EMPTY_TITLE    : str  = "اختر عنصراً من القائمة"
    EMPTY_SUBTITLE : str  = ""
    HEADER_BG      : str  = "#ffffff"
    MIN_CONTENT_W  : int  = 500
    CONNECT_BUS    : bool = False

    def __init__(self, conn=None, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._item_id   = None
        self._item_data = None
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumWidth(300)
        self._build()
        self._set_mode(has_data=False)

        if self.CONNECT_BUS:
            self._connect_bus(data=True)

    # ── override hooks ────────────────────────────────────

    def _build_header_cards(self):
        pass

    def _build_header_buttons(self):
        pass

    def _build_content(self, layout: QVBoxLayout):
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

    def _build(self):
        self.setStyleSheet(f"background:{_BG};")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # notification bar
        self._notif = NotificationBar(show_dismiss=True)
        root.addWidget(self._notif)

        # scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet(self._scroll_style())
        self._scroll = scroll

        inner = QWidget()
        inner.setMinimumWidth(self.MIN_CONTENT_W)
        inner.setStyleSheet(f"background:{_BG};")
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(0, 0, 0, 0)
        inner_lay.setSpacing(0)

        # detail header
        self._hdr = DetailHeader(bg=self.HEADER_BG)
        self._build_header_cards()
        self._build_header_buttons()
        inner_lay.addWidget(self._hdr)

        # content
        content = QWidget()
        content.setStyleSheet(f"background:{_BG};")
        self._content_lay = QVBoxLayout(content)
        self._content_lay.setContentsMargins(16, 14, 16, 16)
        self._content_lay.setSpacing(12)
        self._build_content(self._content_lay)
        self._content_lay.addStretch()
        inner_lay.addWidget(content, stretch=1)

        scroll.setWidget(inner)
        root.addWidget(scroll, stretch=1)

        # empty state
        self._empty = EmptyState(
            icon=self.EMPTY_ICON, title=self.EMPTY_TITLE,
            subtitle=self.EMPTY_SUBTITLE,
            style="plain", color="#6b7280", min_height=200,
        )
        root.addWidget(self._empty)

    # ── public API ────────────────────────────────────────

    def load_item(self, item_id: int):
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
        self._item_id   = None
        self._item_data = None
        self._notif.hide_bar()
        self._set_mode(has_data=False)

    # ── إشعارات ───────────────────────────────────────────

    def show_success(self, msg: str, auto_hide: int = 3000):
        self._notif.show(msg, "success", auto_hide)

    def show_error(self, msg: str):
        self._notif.show(msg, "danger")

    def show_warning(self, msg: str, auto_hide: int = 0):
        self._notif.show(msg, "warning", auto_hide)

    def show_info(self, msg: str, auto_hide: int = 0):
        self._notif.show(msg, "info", auto_hide)

    # ── state ─────────────────────────────────────────────

    def _set_mode(self, has_data: bool):
        self._scroll.setVisible(has_data)
        self._hdr.setVisible(has_data)
        self._empty.setVisible(not has_data)

    # ── خصائص ────────────────────────────────────────────

    @property
    def item_id(self) -> "int | None":
        return self._item_id

    @property
    def item_data(self) -> "dict | None":
        return self._item_data

    @property
    def header(self) -> DetailHeader:
        return self._hdr

    @property
    def content_layout(self) -> QVBoxLayout:
        return self._content_lay

    @staticmethod
    def _scroll_style(width: int = 6) -> str:
        r = width // 2
        return f"""
            QScrollArea {{ border:none; background:transparent; }}
            QScrollBar:vertical {{
                background:transparent; width:{width}px; border-radius:{r}px;
            }}
            QScrollBar::handle:vertical {{
                background:{_C['border_med']}; border-radius:{r}px; min-height:30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0px; }}
        """