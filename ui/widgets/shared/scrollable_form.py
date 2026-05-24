"""
ui/widgets/shared/scrollable_form.py
==============================
ScrollableForm — wrapper يلف أي QWidget جوه QScrollArea عمودي.

[تحديث]: توحيد الستايل مع _C من app_settings.

الاستخدام:
    from ui.widgets.shared.scrollable_form import wrap_in_scroll

    scroll = wrap_in_scroll(your_widget)
    layout.addWidget(scroll)

أو ترث منه مباشرة:
    class MyForm(ScrollableFormWidget):
        def _build_content(self, container):
            # أضف widgets على container
            ...
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QSizePolicy,
)
from PyQt5.QtCore import Qt

from ui.app_settings import _C


def wrap_in_scroll(widget: QWidget,
                   min_height: int = 0,
                   horizontal: bool = False) -> QScrollArea:
    """
    يلف أي widget جوه QScrollArea.

    widget       : الـ widget المطلوب لفه
    min_height   : ارتفاع أدنى للـ scroll area (0 = بدون حد)
    horizontal   : هل يسمح بالتمرير الأفقي (False = عمودي فقط)
    """
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(widget)

    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    if horizontal:
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    else:
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    # ستايل موحد مع theme التطبيق
    border_med = _C.get('border_med', '#bdbdbd')
    border     = _C.get('border', '#e0e0e0')
    bg_surface = _C.get('bg_surface_2', '#f5f5f5')

    scroll.setStyleSheet(f"""
        QScrollArea {{
            border: none;
            background: transparent;
        }}
        QScrollArea > QWidget > QWidget {{
            background: transparent;
        }}
        QScrollBar:vertical {{
            background: {bg_surface};
            width: 8px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: {border_med};
            border-radius: 4px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {border};
        }}
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
    """)

    if min_height:
        scroll.setMinimumHeight(min_height)

    return scroll


class ScrollableFormWidget(QWidget):
    """
    Base class لأي form panel يحتاج scroll عند التصغير.

    الاستخدام:
        class MyPanel(ScrollableFormWidget):
            def _build_content(self, container: QWidget):
                lay = QVBoxLayout(container)
                # أضف widgets هنا ...

    يمكن تمرير min_width عشان يكون فيه حد أدنى للعرض قبل ظهور الـ scrollbar.
    """

    def __init__(self, min_width: int = 280, parent=None):
        super().__init__(parent)
        self._min_width = min_width
        self._setup_scroll()

    def _setup_scroll(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._content = QWidget()
        self._content.setMinimumWidth(self._min_width)
        self._content.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Minimum
        )

        scroll = wrap_in_scroll(self._content)
        outer.addWidget(scroll)

        self._build_content(self._content)

    def _build_content(self, container: QWidget):
        """
        Override هنا لبناء المحتوى.
        container هو الـ QWidget الداخلي — أضف layout وwidgets عليه.
        """
        raise NotImplementedError