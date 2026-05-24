"""
ui/widgets/shared/panles_helper/notification_bar.py
====================================================
NotificationBar — شريط إشعارات موحد بمستويات مختلفة.

يكمل BaseWarningBar (للأخطاء والتحذيرات الهيكلية) بدعم
مستويات الإشعارات العامة: success, info, warning, danger.

الاستخدام:
    bar = NotificationBar()
    layout.addWidget(bar)

    bar.show("تم الحفظ بنجاح", "success", auto_hide=2000)
    bar.show("تحقق من البيانات", "warning")
    bar.hide_bar()
"""

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import QTimer, pyqtSignal

from ui.app_settings import fs
from .colors_and_base import _base

_LEVELS = {
    "success": {
        "bg": "#ecfdf5", "border": "#6ee7b7",
        "text": "#065f46", "icon": "✅",
    },
    "info": {
        "bg": "#eff6ff", "border": "#93c5fd",
        "text": "#1e40af", "icon": "ℹ️",
    },
    "warning": {
        "bg": "#fffbeb", "border": "#fcd34d",
        "text": "#92400e", "icon": "⚠️",
    },
    "danger": {
        "bg": "#fef2f2", "border": "#fca5a5",
        "text": "#991b1b", "icon": "❌",
    },
}


class NotificationBar(QFrame):
    """
    شريط إشعارات موحد.

    Signals:
        dismissed — المستخدم أغلق الشريط
    """

    dismissed = pyqtSignal()

    def __init__(self, show_dismiss: bool = True, parent=None):
        super().__init__(parent)
        self._show_dismiss = show_dismiss
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide_bar)
        self._build()
        self.setVisible(False)

    def _build(self):
        self.setObjectName("notifBar")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(8)

        self._lbl_icon = QLabel()
        self._lbl_icon.setStyleSheet(
            "background:transparent; border:none; font-size:14px;"
        )
        lay.addWidget(self._lbl_icon)

        self._lbl_msg = QLabel()
        self._lbl_msg.setWordWrap(True)
        self._lbl_msg.setStyleSheet("background:transparent; border:none;")
        lay.addWidget(self._lbl_msg, stretch=1)

        if self._show_dismiss:
            btn = QPushButton("✖")
            btn.setFixedSize(22, 22)
            btn.setStyleSheet(
                "QPushButton { background:transparent; border:none; color:#aaa; }"
                "QPushButton:hover { color:#666; }"
            )
            btn.clicked.connect(self._on_dismiss)
            lay.addWidget(btn)

    def show(self, message: str, level: str = "info",
             auto_hide: int = 0):
        """
        يعرض الإشعار.

        message  : نص الرسالة
        level    : "success" | "info" | "warning" | "danger"
        auto_hide: إخفاء تلقائي بعد N ms (0 = لا إخفاء تلقائي)
        """
        cfg  = _LEVELS.get(level, _LEVELS["info"])
        base = _base()

        self.setStyleSheet(f"""
            #notifBar {{
                background: {cfg['bg']};
                border: 1px solid {cfg['border']};
                border-radius: 6px;
            }}
        """)
        self._lbl_icon.setText(cfg["icon"])
        self._lbl_msg.setText(message)
        self._lbl_msg.setStyleSheet(
            f"font-size:{fs(base,0)}pt; font-weight:600;"
            f"color:{cfg['text']}; background:transparent; border:none;"
        )
        self.setVisible(True)

        if auto_hide > 0:
            self._timer.start(auto_hide)

    def hide_bar(self):
        self._timer.stop()
        self.setVisible(False)

    def _on_dismiss(self):
        self.hide_bar()
        self.dismissed.emit()