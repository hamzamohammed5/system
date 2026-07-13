"""
ui/tabs/design/dimension_sets/_values_panel.py
=====================================
لوحة إدخال قيم المقاسات — مع دعم تغيير حجم الخط ديناميكياً.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PyQt5.QtCore import Qt

from .values_panel._sets_list_panel  import _SetsListPanel
from .values_panel._instances_table import _InstancesTable
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.theme import _C
from ui.constants import (
    SMART_SPLITTER_HANDLE_W, LIST_PANEL_MIN_W,
    DIM_VALUES_LIST_MIN_W, DIM_VALUES_LIST_MAX_W, DIM_VALUES_SPLITTER_R,
    DIM_SETS_LIST_HAIRLINE_W, SPACING_ZERO, MARGIN_ZERO,
)


class _ValuesPanel(QWidget, WidgetMixin):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn    = conn
        self._set_id = None
        self._build()
        self._init_widget_mixin(lang=False, data=False)
        self._refresh_style()

    def showEvent(self, event):
        """[إصلاح dark-theme] راجع نفس التعليق في _InstancesTable.showEvent."""
        super().showEvent(event)
        self._refresh_style()

    def _refresh_style(self, *_):
        from ui.font import get_font_size
        size = get_font_size()
        self._sets_list._on_font_changed(size)
        self._table._on_font_changed(size)

        # [إصلاح dark-theme] الودجتس دي كانت بتاخد لون الخلفية وقت
        # البناء بس (setStyleSheet في _build) ومفيهاش تحديث هنا، فكانت
        # بتفضل بلون الثيم القديم بعد التحويل لـ dark.
        if hasattr(self, '_splitter'):
            self._splitter.setStyleSheet(f"""
                QSplitter::handle {{ background: {_C['border']}; }}
                QSplitter::handle:hover {{ background: {_C['accent_mid']}; }}
            """)
        if hasattr(self, '_sets_list'):
            self._sets_list.setStyleSheet(
                f"background: {_C['bg_surface']}; border-right: {DIM_SETS_LIST_HAIRLINE_W}px solid {_C['border']};"
            )
        # [إصلاح dark-theme] أُزيل override الخارجي على self._table هنا —
        # _InstancesTable تدير خلفيتها الداخلية بالكامل بنفسها.

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(*MARGIN_ZERO)
        root.setSpacing(SPACING_ZERO)

        splitter = QSplitter(Qt.Horizontal)
        self._splitter = splitter   # [إصلاح dark-theme]
        splitter.setHandleWidth(SMART_SPLITTER_HANDLE_W)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{ background: {_C['border']}; }}
            QSplitter::handle:hover {{ background: {_C['accent_mid']}; }}
        """)

        self._sets_list = _SetsListPanel(self.conn)
        self._sets_list.setMinimumWidth(DIM_VALUES_LIST_MIN_W)
        self._sets_list.setMaximumWidth(DIM_VALUES_LIST_MAX_W)
        self._sets_list.setStyleSheet(f"background: {_C['bg_surface']}; border-right: {DIM_SETS_LIST_HAIRLINE_W}px solid {_C['border']};")

        self._table = _InstancesTable(self.conn)
        # [إصلاح dark-theme] أُزيل setStyleSheet الخارجي هنا — كان بيحط
        # قاعدة background عامة على _InstancesTable من بره، وممكن يتعارض
        # (بترتيب الـ cascade في Qt) مع الستايلات الداخلية التفصيلية اللي
        # _InstancesTable بتدير نفسها بيها في _refresh_style/_build الخاصة
        # بيها (toolbar, table, status_bar, _empty_state). _InstancesTable
        # مسؤولة بالكامل عن مظهرها الداخلي.

        self._sets_list.set_selected.connect(self._on_set_selected)

        splitter.addWidget(self._sets_list)
        splitter.addWidget(self._table)
        splitter.setSizes([LIST_PANEL_MIN_W, DIM_VALUES_SPLITTER_R])
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