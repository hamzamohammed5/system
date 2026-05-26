"""
ui/widgets/utils/scrollable_form.py
===============================================
wrap_in_scroll + ScrollableFormWidget.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QSizePolicy
from PyQt5.QtCore    import Qt

from ui.app_settings import _C


def scroll_style(width: int = 8) -> str:
    r   = width // 2
    bg  = _C.get('bg_surface_2', '#f5f5f5')
    bdr = _C.get('border_med',   '#bdbdbd')
    return f"""
        QScrollArea {{ border:none; background:transparent; }}
        QScrollBar:vertical {{
            background:{bg}; width:{width}px; border-radius:{r}px;
        }}
        QScrollBar::handle:vertical {{
            background:{bdr}; border-radius:{r}px; min-height:30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background:{_C.get('border','#e0e0e0')};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0px; }}
        QScrollBar:horizontal {{
            background:{bg}; height:{width}px; border-radius:{r}px;
        }}
        QScrollBar::handle:horizontal {{
            background:{bdr}; border-radius:{r}px; min-width:30px;
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width:0px; }}
    """


def wrap_in_scroll(widget: QWidget,
                   min_height: int = 0,
                   horizontal: bool = False) -> QScrollArea:
    """يلف أي widget في QScrollArea موحد."""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(widget)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll.setHorizontalScrollBarPolicy(
        Qt.ScrollBarAsNeeded if horizontal else Qt.ScrollBarAlwaysOff
    )
    scroll.setStyleSheet(scroll_style())
    if min_height:
        scroll.setMinimumHeight(min_height)
    return scroll


class ScrollableFormWidget(QWidget):
    """
    Base class لأي form panel يحتاج scroll.

    Override:
        _build_content(container) → أضف widgets على container
    """

    def __init__(self, min_width: int = 280, parent=None):
        super().__init__(parent)
        self._min_width = min_width
        self._setup()

    def _setup(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._content = QWidget()
        self._content.setMinimumWidth(self._min_width)
        self._content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        outer.addWidget(wrap_in_scroll(self._content))
        self._build_content(self._content)

    def _build_content(self, container: QWidget):
        raise NotImplementedError


def build_inner_scroll(parent_widget: QWidget,
                        min_width: int = 280) -> tuple:
    """
    يبني الهيكل الأساسي لأي form panel بـ scroll.
    يرجع (outer_layout, inner_widget, inner_layout)
    """
    outer = QVBoxLayout(parent_widget)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(0)

    inner = QWidget()
    inner.setMinimumWidth(min_width)
    inner.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

    scroll = wrap_in_scroll(inner)
    outer.addWidget(scroll)

    lay = QVBoxLayout(inner)
    lay.setSpacing(10)
    lay.setContentsMargins(12, 12, 12, 12)

    return outer, inner, lay