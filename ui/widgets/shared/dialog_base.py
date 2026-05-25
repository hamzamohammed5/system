"""
ui/widgets/shared/dialog_base.py
=================================
BaseDialog — قاعدة مشتركة لكل الـ dialogs في التطبيق.

[إصلاح v2]:
  - _add_default_buttons تستخدم _make_btn بدل inline QPushButton styles
"""

from PyQt5.QtWidgets import QPushButton, QVBoxLayout
from PyQt5.QtCore    import Qt

from ui.app_settings import _C, fs
from ui.widgets.shared.panles_helper.dialog_shell    import _DialogShell
from ui.widgets.shared.panles_helper.make_btn        import _make_btn
from ui.widgets.shared.panles_helper.colors_and_base import _base


class BaseDialog(_DialogShell):
    """
    قاعدة مشتركة للـ dialogs — يرث من _DialogShell.

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
        super().__init__(
            parent,
            title=title,
            icon=icon,
            subtitle=subtitle,
            accent=accent,
            min_width=min_size[0],
            min_height=min_size[1],
        )
        if show_btns:
            self._add_default_buttons()
        else:
            self._btn_ok = QPushButton()   # dummy للتوافق

        self._build_content(self._body_layout)

    # ── أزرار افتراضية ────────────────────────────────────

    def _add_default_buttons(self):
        btn_cancel = _make_btn("✖  إلغاء", "ghost")
        btn_cancel.setMinimumHeight(36)
        btn_cancel.clicked.connect(self.reject)

        self._btn_ok = _make_btn("✅  حفظ", "primary")
        self._btn_ok.setMinimumHeight(36)

        # override لون الـ accent لو مختلف
        if self._accent and self._accent != _C.get("accent", "#1565c0"):
            base = _base()
            self._btn_ok.setStyleSheet(f"""
                QPushButton {{
                    background: {self._accent}; color: white;
                    font-weight: bold; border-radius: 6px;
                    padding: 0 20px; font-size: {fs(base, 0)}pt;
                    border: none; min-height: 36px;
                }}
                QPushButton:hover {{ background: {self._accent}dd; }}
                QPushButton:disabled {{ background: {_C['text_disabled']}; }}
            """)

        self._btn_ok.clicked.connect(self._on_accept)

        self.btn_layout.addWidget(btn_cancel)
        self.btn_layout.addWidget(self._btn_ok)

    # ── دوال للـ override ──────────────────────────────────

    def _build_content(self, lay: QVBoxLayout):
        """Override هنا لإضافة محتوى النافذة."""
        pass

    def _on_accept(self):
        """Override هنا لمنطق الحفظ."""
        self.accept()

    # ── خصائص مساعدة ─────────────────────────────────────

    def set_ok_enabled(self, enabled: bool):
        if hasattr(self, "_btn_ok"):
            self._btn_ok.setEnabled(enabled)

    def set_ok_text(self, text: str):
        if hasattr(self, "_btn_ok"):
            self._btn_ok.setText(text)