"""
ui/widgets/components/spinner.py
=========================================
LoadingSpinner / LoadingOverlay / LoadingButton — مؤشرات تحميل موحدة.

[Refactor V3] إصلاح imports: ui.app_settings → ui.theme + ui.font
"""
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QSizePolicy, QPushButton,
)
from PyQt5.QtCore import Qt, QTimer

from ui.theme import _C
from ui.font  import fs, get_font_size
from ..core.i18n import tr
from ..core.widget_mixin import WidgetMixin
from ui.constants import (
    MARGIN_ZERO, SPACING_MD,
    OVERLAY_MARGIN, OVERLAY_BORDER_RADIUS, SPINNER_FRAME_INTERVAL_MS,
)


_FRAMES = ["⠋", "⠙", "⠸", "⠴", "⠦", "⠇"]


class LoadingSpinner(QWidget, WidgetMixin):
    """مؤشر تحميل نصي متحرك."""

    def __init__(self, text: str = None,
                 color: str = None, compact: bool = False, parent=None):
        super().__init__(parent)
        self._custom_text = text
        self._text    = text if text is not None else tr('spinner_loading_text')
        self._custom_color = color
        self._color   = color or _C["accent"]
        self._compact = compact
        self._frame   = 0
        self._timer   = QTimer(self)
        self._timer.setInterval(SPINNER_FRAME_INTERVAL_MS)
        self._timer.timeout.connect(self._tick)
        self._build(self._text)
        self._init_widget_mixin(theme=True, font=True, lang=True)
        self._refresh_style()

    def _build(self, text: str):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(*MARGIN_ZERO)
        lay.setSpacing(SPACING_MD)
        lay.setAlignment(Qt.AlignCenter)

        self._lbl_icon = QLabel(_FRAMES[0])
        lay.addWidget(self._lbl_icon)

        self._lbl_text = None
        if text:
            self._lbl_text = QLabel(text)
            lay.addWidget(self._lbl_text)

    def _refresh_style(self, *_):
        if self._custom_color is None:
            self._color = _C["accent"]

        self.setStyleSheet("background:transparent;")
        base = get_font_size()
        sz   = fs(base, 0 if self._compact else +2)

        self._lbl_icon.setStyleSheet(
            f"font-size:{sz}pt; color:{self._color}; background:transparent; border:none;"
        )
        if self._lbl_text:
            self._lbl_text.setStyleSheet(
                f"font-size:{fs(base,0)}pt; color:{self._color};"
                "background:transparent; border:none;"
            )

    def _refresh_lang(self, *_):
        if self._custom_text is None and self._lbl_text and not self._timer.isActive():
            self._text = tr('spinner_loading_text')
            self._lbl_text.setText(self._text)

    def _tick(self):
        self._frame = (self._frame + 1) % len(_FRAMES)
        self._lbl_icon.setText(_FRAMES[self._frame])

    def start(self):
        self.setVisible(True)
        self._timer.start()

    def stop(self):
        self._timer.stop()
        self._lbl_icon.setText(tr('spinner_done_check'))

    def set_text(self, text: str):
        self._custom_text = text
        self._text = text
        if self._lbl_text:
            self._lbl_text.setText(text)

    def is_running(self) -> bool:
        return self._timer.isActive()


class LoadingOverlay(QFrame, WidgetMixin):
    """طبقة شفافة فوق أي widget تعرض رسالة تحميل."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setContentsMargins(OVERLAY_MARGIN, OVERLAY_MARGIN, OVERLAY_MARGIN, OVERLAY_MARGIN)
        self._spinner = LoadingSpinner(compact=False)
        lay.addWidget(self._spinner, alignment=Qt.AlignCenter)
        self._init_widget_mixin(theme=True, font=False, lang=False, data=False)
        self._refresh_style()
        self.hide()

    def _refresh_style(self, *_):
        self.setStyleSheet(
            f"QFrame {{ background:{_C['overlay_bg']}; border-radius:{OVERLAY_BORDER_RADIUS}px; }}"
        )

    def show_loading(self, text: str = None):
        self._spinner.set_text(text if text is not None else tr('spinner_loading_text'))
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


class LoadingButton(QPushButton, WidgetMixin):
    """زر يعرض spinner عند تفعيل التحميل."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._original_text = text
        self._frame  = 0
        self._timer  = QTimer(self)
        self._timer.setInterval(SPINNER_FRAME_INTERVAL_MS)
        self._timer.timeout.connect(self._tick)
        self._init_widget_mixin(theme=False, font=False, lang=True)

    def _tick(self):
        self._frame = (self._frame + 1) % len(_FRAMES)
        self.setText(f"{_FRAMES[self._frame]}  {tr('loading_button_saving_text')}")

    def _refresh_lang(self, *_):
        if not self._timer.isActive():
            self.setText(self._original_text)

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