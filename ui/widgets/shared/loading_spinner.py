"""
ui/widgets/shared/loading_spinner.py
=====================================
LoadingSpinner — مؤشر تحميل موحد للتطبيق.
LoadingOverlay  — طبقة تحميل فوق widget موجود.

الاستخدام:
    # مؤشر بسيط:
    spinner = LoadingSpinner("جارٍ التحميل...")
    layout.addWidget(spinner)
    spinner.start()
    spinner.stop()

    # طبقة فوق widget:
    overlay = LoadingOverlay(parent_widget)
    overlay.show_loading("جارٍ الحفظ...")
    overlay.hide_loading()
"""

from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QSizePolicy,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui  import QFont

from ui.app_settings import _C, fs
from ui.widgets.shared.panles_helper.colors_and_base import _base


# ══════════════════════════════════════════════════════════
# LoadingSpinner — مؤشر تحميل نصي متحرك
# ══════════════════════════════════════════════════════════

class LoadingSpinner(QWidget):
    """
    مؤشر تحميل بسيط مع أيقونة دوّارة ونص.

    الاستخدام:
        spinner = LoadingSpinner("جارٍ التحميل...")
        layout.addWidget(spinner)
        spinner.start()
        # عند الانتهاء:
        spinner.stop()
        spinner.setVisible(False)
    """

    _FRAMES = ["⠋", "⠙", "⠸", "⠴", "⠦", "⠇"]

    def __init__(self, text: str = "جارٍ التحميل...",
                 color: str = None,
                 compact: bool = False,
                 parent=None):
        super().__init__(parent)
        self._text    = text
        self._color   = color or _C.get("accent", "#1565c0")
        self._compact = compact
        self._frame   = 0
        self._timer   = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._tick)
        self._build()

    def _build(self):
        self.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        lay.setAlignment(Qt.AlignCenter)

        base = _base()
        sz   = fs(base, +2) if not self._compact else fs(base, 0)

        self._lbl_icon = QLabel(self._FRAMES[0])
        self._lbl_icon.setStyleSheet(
            f"font-size: {sz}pt; color: {self._color}; background: transparent; border: none;"
        )
        lay.addWidget(self._lbl_icon)

        if self._text:
            self._lbl_text = QLabel(self._text)
            self._lbl_text.setStyleSheet(
                f"font-size: {fs(base, 0)}pt; color: {self._color};"
                "background: transparent; border: none;"
            )
            lay.addWidget(self._lbl_text)

    def _tick(self):
        self._frame = (self._frame + 1) % len(self._FRAMES)
        self._lbl_icon.setText(self._FRAMES[self._frame])

    def start(self):
        """يبدأ الدوران ويظهر الـ spinner."""
        self.setVisible(True)
        self._timer.start()

    def stop(self):
        """يوقف الدوران."""
        self._timer.stop()
        self._lbl_icon.setText("✓")

    def set_text(self, text: str):
        if hasattr(self, "_lbl_text"):
            self._lbl_text.setText(text)

    def is_running(self) -> bool:
        return self._timer.isActive()


# ══════════════════════════════════════════════════════════
# LoadingOverlay — طبقة تحميل فوق widget
# ══════════════════════════════════════════════════════════

class LoadingOverlay(QFrame):
    """
    طبقة شفافة فوق أي widget تعرض رسالة تحميل.

    الاستخدام:
        overlay = LoadingOverlay(my_table)
        overlay.show_loading("جارٍ تحميل البيانات...")
        # عند الانتهاء:
        overlay.hide_loading()
    """

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._build()
        self.hide()

    def _build(self):
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 180);
                border-radius: 8px;
            }
        """)

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setContentsMargins(20, 20, 20, 20)

        self._spinner = LoadingSpinner(compact=False)
        lay.addWidget(self._spinner, alignment=Qt.AlignCenter)

    def show_loading(self, text: str = "جارٍ التحميل..."):
        """يظهر الطبقة ويبدأ التحميل."""
        self._spinner.set_text(text)
        if self.parent():
            self.resize(self.parent().size())
        self.show()
        self.raise_()
        self._spinner.start()

    def hide_loading(self):
        """يخفي الطبقة."""
        self._spinner.stop()
        self.hide()

    def resizeEvent(self, event):
        """يتكيف مع حجم الـ parent."""
        if self.parent():
            self.resize(self.parent().size())
        super().resizeEvent(event)


# ══════════════════════════════════════════════════════════
# LoadingButton — زر يتحول لـ spinner عند الضغط
# ══════════════════════════════════════════════════════════

from PyQt5.QtWidgets import QPushButton


class LoadingButton(QPushButton):
    """
    زر يعرض spinner بدل النص عند تفعيل التحميل.

    الاستخدام:
        btn = LoadingButton("💾 حفظ")
        btn.clicked.connect(self._on_save)
        layout.addWidget(btn)

        def _on_save(self):
            btn.set_loading(True)
            # ... عمل غير متزامن ...
            btn.set_loading(False)
    """

    _FRAMES = ["⠋", "⠙", "⠸", "⠴", "⠦", "⠇"]

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._original_text = text
        self._frame  = 0
        self._timer  = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._tick)

    def _tick(self):
        self._frame = (self._frame + 1) % len(self._FRAMES)
        self.setText(f"{self._FRAMES[self._frame]}  جارٍ الحفظ...")

    def set_loading(self, loading: bool, text: str = None):
        """يفعّل/يعطّل وضع التحميل."""
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