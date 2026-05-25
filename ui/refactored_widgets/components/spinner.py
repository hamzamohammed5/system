"""
ui/widgets/components/spinner.py
=========================================
LoadingSpinner / LoadingOverlay / LoadingButton — مؤشرات تحميل موحدة.
"""
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QSizePolicy, QPushButton,
)
from PyQt5.QtCore import Qt, QTimer

from ui.app_settings import _C, fs
from ..core.settings import get_base


_FRAMES = ["⠋", "⠙", "⠸", "⠴", "⠦", "⠇"]


class LoadingSpinner(QWidget):
    """مؤشر تحميل نصي متحرك."""

    def __init__(self, text: str = "جارٍ التحميل...",
                 color: str = None, compact: bool = False, parent=None):
        super().__init__(parent)
        self._text    = text
        self._color   = color or _C.get("accent", "#1565c0")
        self._frame   = 0
        self._timer   = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._tick)
        self._build(compact)

    def _build(self, compact: bool):
        self.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        lay.setAlignment(Qt.AlignCenter)

        base = get_base()
        sz   = fs(base, 0 if compact else +2)

        self._lbl_icon = QLabel(_FRAMES[0])
        self._lbl_icon.setStyleSheet(
            f"font-size:{sz}pt; color:{self._color}; background:transparent; border:none;"
        )
        lay.addWidget(self._lbl_icon)

        if self._text:
            self._lbl_text = QLabel(self._text)
            self._lbl_text.setStyleSheet(
                f"font-size:{fs(base,0)}pt; color:{self._color};"
                "background:transparent; border:none;"
            )
            lay.addWidget(self._lbl_text)

    def _tick(self):
        self._frame = (self._frame + 1) % len(_FRAMES)
        self._lbl_icon.setText(_FRAMES[self._frame])

    def start(self):
        self.setVisible(True)
        self._timer.start()

    def stop(self):
        self._timer.stop()
        self._lbl_icon.setText("✓")

    def set_text(self, text: str):
        if hasattr(self, "_lbl_text"):
            self._lbl_text.setText(text)

    def is_running(self) -> bool:
        return self._timer.isActive()


class LoadingOverlay(QFrame):
    """طبقة شفافة فوق أي widget تعرض رسالة تحميل."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setStyleSheet("QFrame { background:rgba(255,255,255,180); border-radius:8px; }")
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setContentsMargins(20, 20, 20, 20)
        self._spinner = LoadingSpinner(compact=False)
        lay.addWidget(self._spinner, alignment=Qt.AlignCenter)
        self.hide()

    def show_loading(self, text: str = "جارٍ التحميل..."):
        self._spinner.set_text(text)
        if self.parent():
            self.resize(self.parent().size())
        self.show()
        self.raise_()
        self._spinner.start()

    def hide_loading(self):
        self._spinner.stop()
        self.hide()

    def resizeEvent(self, event):
        if self.parent():
            self.resize(self.parent().size())
        super().resizeEvent(event)


class LoadingButton(QPushButton):
    """زر يعرض spinner عند تفعيل التحميل."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._original_text = text
        self._frame  = 0
        self._timer  = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._tick)

    def _tick(self):
        self._frame = (self._frame + 1) % len(_FRAMES)
        self.setText(f"{_FRAMES[self._frame]}  جارٍ الحفظ...")

    def set_loading(self, loading: bool, text: str = None):
        self.setEnabled(not loading)
        if loading:
            self._timer.start()
        else:
            self._timer.stop()
            self.setText(text or self._original_text)

    def set_original_text(self, text: str):
        self._original_text = text
        if not self._timer.isActive():
            self.setText(text)