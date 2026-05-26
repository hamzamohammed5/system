"""
ui/widgets/panels/card_grid.py
==========================================
CardGrid — شبكة بطاقات متجاوبة بعدد أعمدة ثابت.

الاستخدام:
    grid = CardGrid(cols=4, spacing=12)
    grid.add_widget(frame1)
    grid.add_widget(frame2)
    layout.addWidget(grid)

    # أو مباشرة من list:
    grid = CardGrid.from_widgets([f1, f2, f3], cols=3)
"""
from PyQt5.QtWidgets import QWidget, QGridLayout, QSizePolicy


class CardGrid(QWidget):
    """شبكة بطاقات بعدد أعمدة ثابت — تملأ الصفوف تلقائياً."""

    def __init__(self, cols: int = 4, spacing: int = 10, parent=None):
        super().__init__(parent)
        self._cols  = cols
        self._count = 0
        self.setStyleSheet("background:transparent;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._grid = QGridLayout(self)
        self._grid.setSpacing(spacing)
        self._grid.setContentsMargins(0, 0, 0, 0)

        for c in range(cols):
            self._grid.setColumnStretch(c, 1)

    def add_widget(self, widget: QWidget):
        row = self._count // self._cols
        col = self._count % self._cols
        self._grid.addWidget(widget, row, col)
        self._count += 1

    def clear(self):
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._count = 0

    @classmethod
    def from_widgets(cls, widgets: list, cols: int = 4,
                     spacing: int = 10) -> "CardGrid":
        grid = cls(cols=cols, spacing=spacing)
        for w in widgets:
            grid.add_widget(w)
        return grid