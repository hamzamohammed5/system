"""
ui/widgets/panels/crud_section.py
=============================================
CrudSection — قاعدة موحدة لأقسام CRUD الكاملة.

[List Panel] | [Detail/Form Panel]
"""
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QSizePolicy,
)
from PyQt5.QtCore import Qt, QTimer

from ..styles        import splitter_style


class CrudSection(QWidget):
    """
    قاعدة موحدة لأقسام CRUD.

    Override:
        _create_list()     → لوحة القائمة
        _create_detail()   → لوحة التفاصيل
        _create_form()     → فورم الإضافة/التعديل (None = مدمج في detail)
        _connect_signals() → ربط الـ signals
    """

    LIST_MIN_W    : int   = 280
    LIST_MAX_W    : int   = 580
    DETAIL_MIN_W  : int   = 380
    SPLITTER_RATIO: tuple = (1, 2)
    FORM_POSITION : str   = "left"   # "left" | "bottom" | "none"

    def __init__(self, conn=None, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self._connect_signals()
        QTimer.singleShot(60, self._apply_sizes)

    # ── override ──────────────────────────────────────────

    def _create_list(self) -> QWidget:
        raise NotImplementedError

    def _create_detail(self) -> QWidget:
        raise NotImplementedError

    def _create_form(self) -> "QWidget | None":
        return None

    def _connect_signals(self):
        pass

    def _on_item_selected(self, item_id: int):
        if hasattr(self._detail, 'load_item'):
            self._detail.load_item(item_id)

    # ── بناء الواجهة ──────────────────────────────────────

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.setHandleWidth(5)
        self._splitter.setStyleSheet(splitter_style())
        self._splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        left          = self._build_left()
        self._detail  = self._create_detail()

        left.setMinimumWidth(self.LIST_MIN_W)
        left.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self._detail.setMinimumWidth(self.DETAIL_MIN_W)
        self._detail.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._splitter.addWidget(left)
        self._splitter.addWidget(self._detail)
        self._splitter.setCollapsible(0, False)
        self._splitter.setCollapsible(1, False)
        self._splitter.setStretchFactor(0, self.SPLITTER_RATIO[0])
        self._splitter.setStretchFactor(1, self.SPLITTER_RATIO[1])

        root.addWidget(self._splitter)

    def _build_left(self) -> QWidget:
        self._list = self._create_list()
        form       = self._create_form()

        if form is None or self.FORM_POSITION == "none":
            self._form = None
            return self._list

        if self.FORM_POSITION == "bottom":
            container = QWidget()
            container.setStyleSheet("background:transparent;")
            lay = QVBoxLayout(container)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(0)
            lay.addWidget(self._list, stretch=1)
            lay.addWidget(form)
            self._form = form
            return container

        self._form = form
        return self._list

    def _apply_sizes(self):
        total = self._splitter.width()
        if total <= 0:
            QTimer.singleShot(100, self._apply_sizes)
            return
        list_w   = max(self.LIST_MIN_W,
                       min(self.LIST_MIN_W + 60, self.LIST_MAX_W))
        detail_w = max(self.DETAIL_MIN_W,
                       total - list_w - self._splitter.handleWidth())
        self._splitter.blockSignals(True)
        self._splitter.setSizes([list_w, detail_w])
        self._splitter.blockSignals(False)

    # ── API ───────────────────────────────────────────────

    def refresh(self):
        if hasattr(self._list, 'refresh'):
            self._list.refresh()

    def select_item(self, item_id: int):
        if hasattr(self._list, 'select_item'):
            self._list.select_item(item_id)
        self._on_item_selected(item_id)

    @property
    def list_panel(self) -> QWidget:
        return self._list

    @property
    def detail_panel(self) -> QWidget:
        return self._detail

    @property
    def form_panel(self) -> "QWidget | None":
        return self._form