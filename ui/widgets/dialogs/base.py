"""
ui/widgets/dialogs/base.py
===========================
BaseDialog — قاعدة مشتركة لكل الـ dialogs.
"""
from PyQt5.QtWidgets import QPushButton, QVBoxLayout

from ui.app_settings import _C, fs
from ..core          import get_font_size
from ..components.button import make_btn
from .shell import DialogShell


class BaseDialog(DialogShell):
    """
    قاعدة مشتركة للـ dialogs.

    Override:
        _build_content(lay) → أضف المحتوى
        _on_accept()        → منطق الحفظ
    """

    def __init__(self, parent=None, title: str = "", icon: str = "📋",
                 subtitle: str = "", min_size: tuple = (500, 400),
                 accent: str = None, show_btns: bool = True):
        # accent=None → يستخدم _C['accent'] تلقائياً من DialogShell
        super().__init__(
            parent, title=title, icon=icon, subtitle=subtitle,
            accent=accent, min_width=min_size[0], min_height=min_size[1],
        )
        if show_btns:
            self._add_default_buttons()
        else:
            self._btn_ok = QPushButton()  # dummy

        self._build_content(self._body_layout)

    def _add_default_buttons(self):
        btn_cancel = make_btn("✖  إلغاء", "ghost")
        btn_cancel.setMinimumHeight(36)
        btn_cancel.clicked.connect(self.reject)

        self._btn_ok = make_btn("✅  حفظ", "primary")
        self._btn_ok.setMinimumHeight(36)

        # نقارن بـ _C['accent'] بدل hardcoded "#1565c0"
        if self._accent and self._accent != _C.get("accent"):
            base = get_font_size()
            self._btn_ok.setStyleSheet(f"""
                QPushButton {{
                    background:{self._accent}; color:white; font-weight:bold;
                    border-radius:6px; padding:0 20px;
                    font-size:{fs(base,0)}pt; border:none; min-height:36px;
                }}
                QPushButton:hover {{ background:{self._accent}dd; }}
                QPushButton:disabled {{ background:{_C['text_disabled']}; }}
            """)

        self._btn_ok.clicked.connect(self._on_accept)
        self.btn_layout.addWidget(btn_cancel)
        self.btn_layout.addWidget(self._btn_ok)

    def _build_content(self, lay: QVBoxLayout):
        pass

    def _on_accept(self):
        self.accept()

    def set_ok_enabled(self, enabled: bool):
        if hasattr(self, "_btn_ok"):
            self._btn_ok.setEnabled(enabled)

    def set_ok_text(self, text: str):
        if hasattr(self, "_btn_ok"):
            self._btn_ok.setText(text)