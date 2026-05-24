"""
ui/widgets/shared/flow_layout.py
=================================
FlowLayout — layout بيلف الـ widgets لسطر تاني تلقائياً لو مفيش مساحة.
"""

from PyQt5.QtWidgets import QLayout, QWidgetItem
from PyQt5.QtCore import Qt, QRect, QSize, QPoint


class FlowLayout(QLayout):
    def __init__(self, parent=None, h_spacing: int = 6, v_spacing: int = 4):
        super().__init__(parent)
        self._items     = []
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing

    def addItem(self, item):
        self._items.append(item)

    def addWidget(self, widget):
        # FIX 4: كان بيضيف QWidgetItem للـ list مباشرة متجاوزاً addItem
        # ده بيخلي Qt internal state inconsistent
        # الصح: تمرير الـ item عبر addItem() عشان Qt يتتبعه صح
        self.addItem(QWidgetItem(widget))

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int):
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index: int):
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def expandingDirections(self):
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
        m = self.contentsMargins()
        return size + QSize(m.left() + m.right(), m.top() + m.bottom())

    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        m   = self.contentsMargins()
        eff = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        x, y, lh = eff.x(), eff.y(), 0

        for item in self._items:
            w = item.widget()
            if w and not w.isVisible():
                continue
            sz = item.sizeHint()
            nx = x + sz.width() + self._h_spacing
            if nx - self._h_spacing > eff.right() and lh > 0:
                x, y, lh = eff.x(), y + lh + self._v_spacing, 0
                nx = x + sz.width() + self._h_spacing
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), sz))
            x, lh = nx, max(lh, sz.height())

        return y + lh - rect.y() + m.bottom()