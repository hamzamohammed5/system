"""
ui/widgets/utils/flow_layout.py
===========================================
FlowLayout — layout يرتب الـ widgets أفقياً وينزل لسطر تاني تلقائياً.
"""
from PyQt5.QtWidgets import QLayout, QSizePolicy, QWidget
from PyQt5.QtCore    import Qt, QRect, QSize, QPoint

from ui.constants import FLOW_LAYOUT_DEFAULT_H_SPACING, FLOW_LAYOUT_DEFAULT_V_SPACING


class FlowLayout(QLayout):
    """
    Layout يرتب الـ widgets أفقياً وينزل تلقائياً لسطر جديد.

    الاستخدام:
        layout = FlowLayout(widget, h_spacing=8, v_spacing=4)
        layout.addWidget(btn1)
        layout.addWidget(btn2)
    """

    def __init__(self, parent=None, h_spacing: int = FLOW_LAYOUT_DEFAULT_H_SPACING,
                 v_spacing: int = FLOW_LAYOUT_DEFAULT_V_SPACING):
        super().__init__(parent)
        self._h_space = h_spacing
        self._v_space = v_spacing
        self._items: list = []

    def addItem(self, item):
        self._items.append(item)

    def horizontalSpacing(self) -> int:
        return self._h_space

    def verticalSpacing(self) -> int:
        return self._v_space

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self) -> Qt.Orientations:
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect: QRect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(
            margins.left() + margins.right(),
            margins.top()  + margins.bottom(),
        )
        return size

    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        margins = self.contentsMargins()
        effective = rect.adjusted(
            margins.left(), margins.top(),
            -margins.right(), -margins.bottom()
        )

        x = effective.x()
        y = effective.y()
        line_height = 0

        for item in self._items:
            wid = item.widget()
            space_x = self._h_space
            space_y = self._v_space

            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > effective.right() and line_height > 0:
                x = effective.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(
                    QRect(QPoint(x, y), item.sizeHint())
                )

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y() + margins.bottom()