"""
ui/widgets/shared/dialog_base.py
=================================
BaseDialog — قاعدة مشتركة لكل الـ dialogs في التطبيق.

توفر:
  - هيدر ملون جاهز
  - زر إغلاق موحد
  - layout جاهز للمحتوى
  - RTL تلقائي
  - style موحد

الاستخدام:
    from ui.widgets.shared.dialog_base import BaseDialog

    class MyDialog(BaseDialog):
        def __init__(self, parent=None):
            super().__init__(
                parent=parent,
                title="عنوان النافذة",
                icon="🔧",
                subtitle="نص توضيحي",
                min_size=(600, 500),
            )
            # أضف محتواك في self.body_layout

        def _on_accept(self):
            # منطق الحفظ
            ...
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QWidget,
)
from PyQt5.QtCore import Qt

from ui.app_settings import _C, fs
from ui.widgets.shared.panles_helper.colors_and_base import _base


class BaseDialog(QDialog):
    """
    قاعدة مشتركة للـ dialogs.

    المعاملات:
        title     : عنوان النافذة (يظهر في الهيدر)
        icon      : أيقونة emoji تظهر في الهيدر
        subtitle  : نص توضيحي أسفل العنوان (اختياري)
        min_size  : (width, height) الحد الأدنى
        accent    : لون الهيدر (hex)
        show_btns : هل يظهر شريط الأزرار الافتراضي (حفظ / إلغاء)
    """

    def __init__(self, parent=None,
                 title: str = "",
                 icon: str = "📋",
                 subtitle: str = "",
                 min_size: tuple = (500, 400),
                 accent: str = "#1565c0",
                 show_btns: bool = True):
        super().__init__(parent, Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(*min_size)
        self.setLayoutDirection(Qt.RightToLeft)
        self._accent = accent

        self._build_shell(title, icon, subtitle, show_btns)

    # ── بناء الهيكل ───────────────────────────────────────

    def _build_shell(self, title: str, icon: str,
                     subtitle: str, show_btns: bool):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # الهيدر
        root.addWidget(self._build_header(icon, title, subtitle))

        # المحتوى
        body = QWidget()
        body.setStyleSheet(f"background: {_C['bg_page']};")
        self._body_layout = QVBoxLayout(body)
        self._body_layout.setContentsMargins(16, 14, 16, 14)
        self._body_layout.setSpacing(12)
        self._build_content(self._body_layout)
        root.addWidget(body, stretch=1)

        # شريط الأزرار
        if show_btns:
            root.addWidget(self._build_btn_bar())

    def _build_header(self, icon: str, title: str, subtitle: str) -> QFrame:
        """يبني الهيدر الملون."""
        a = self._accent
        # تفتيح اللون قليلاً للـ gradient
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {a}, stop:1 {a}dd);
                border-bottom: 2px solid {a}99;
            }}
        """)
        header.setFixedHeight(64)

        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(20, 0, 20, 0)
        h_lay.setSpacing(12)

        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet(
            "font-size:26px; background:transparent; border:none;"
        )

        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        lbl_title = QLabel(title)
        base = _base()
        lbl_title.setStyleSheet(
            f"font-size:{fs(base,+2)}pt; font-weight:bold; color:white;"
            "background:transparent; border:none;"
        )

        text_col.addWidget(lbl_title)
        if subtitle:
            lbl_sub = QLabel(subtitle)
            lbl_sub.setStyleSheet(
                f"font-size:{fs(base,-1)}pt; color:rgba(255,255,255,0.8);"
                "background:transparent; border:none;"
            )
            text_col.addWidget(lbl_sub)

        h_lay.addWidget(lbl_icon)
        h_lay.addLayout(text_col)
        h_lay.addStretch()
        return header

    def _build_btn_bar(self) -> QFrame:
        """يبني شريط الأزرار السفلي."""
        bar = QFrame()
        bar.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_surface']};
                border-top: 1px solid {_C['border']};
            }}
        """)
        bar.setFixedHeight(56)

        lay = QHBoxLayout(bar)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.setSpacing(8)
        lay.addStretch()

        btn_cancel = QPushButton("✖  إلغاء")
        btn_cancel.setMinimumHeight(36)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: {_C['bg_surface_2']}; color: {_C['text_sec']};
                border: 1px solid {_C['border']}; border-radius: 6px;
                padding: 0 16px; font-size: {fs(_base(), 0)}pt;
            }}
            QPushButton:hover {{ background: {_C['bg_hover']}; }}
        """)
        btn_cancel.clicked.connect(self.reject)

        self._btn_ok = QPushButton("✅  حفظ")
        self._btn_ok.setMinimumHeight(36)
        self._btn_ok.setStyleSheet(f"""
            QPushButton {{
                background: {self._accent}; color: white;
                font-weight: bold; border-radius: 6px;
                padding: 0 20px; font-size: {fs(_base(), 0)}pt;
                border: none;
            }}
            QPushButton:hover {{ background: {self._accent}dd; }}
            QPushButton:disabled {{ background: {_C['text_disabled']}; }}
        """)
        self._btn_ok.clicked.connect(self._on_accept)

        lay.addWidget(btn_cancel)
        lay.addWidget(self._btn_ok)
        return bar

    # ── دوال للـ override ──────────────────────────────────

    def _build_content(self, lay: QVBoxLayout):
        """
        Override هنا لإضافة محتوى النافذة.
        lay هو الـ layout الداخلي.
        """
        pass

    def _on_accept(self):
        """
        Override هنا لمنطق الحفظ.
        افتراضياً يغلق النافذة بـ accept().
        """
        self.accept()

    # ── خصائص مساعدة ─────────────────────────────────────

    @property
    def body_layout(self) -> QVBoxLayout:
        """الـ layout الداخلي للمحتوى."""
        return self._body_layout

    def set_ok_enabled(self, enabled: bool):
        """يفعّل/يعطّل زر الحفظ."""
        if hasattr(self, "_btn_ok"):
            self._btn_ok.setEnabled(enabled)

    def set_ok_text(self, text: str):
        """يغير نص زر الحفظ."""
        if hasattr(self, "_btn_ok"):
            self._btn_ok.setText(text)