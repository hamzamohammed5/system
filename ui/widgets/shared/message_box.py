"""
ui/widgets/shared/message_box.py
=================================
دوال بديلة لـ QMessageBox بخلفية بيضاء مضمونة.

استخدمها بدل QMessageBox مباشرة في كل مكان:

    from ui.widgets.shared.message_box import msg_question, msg_info, msg_warning, msg_critical

    if msg_question(self, "تأكيد", "هل تريد الحذف؟"):
        ...

    msg_info(self, "تم", "تم الحفظ بنجاح")
    msg_warning(self, "تنبيه", "هذا الحقل مطلوب")
    msg_critical(self, "خطأ", "حدث خطأ غير متوقع")
"""

from PyQt5.QtWidgets import QLabel, QPushButton
from PyQt5.QtCore    import Qt

from ui.app_settings import _C, fs
from ui.widgets.shared.panles_helper.dialog_shell import _DialogShell
from ui.widgets.shared.panles_helper.colors_and_base import _base


_ICONS = {
    "question": ("❓", "#1565c0"),
    "info":     ("ℹ️",  "#1565c0"),
    "warning":  ("⚠️",  "#e65100"),
    "critical": ("❌",  "#c62828"),
}

_BTN_STYLE = """
    QPushButton {{
        background: {bg};
        color: {fg};
        border: 1px solid {border};
        border-radius: 6px;
        padding: 5px 20px;
        min-width: 72px;
        min-height: 30px;
        font-size: {fs}pt;
    }}
    QPushButton:hover {{
        background: {hover};
        border-color: {border_h};
    }}
    QPushButton:pressed {{ background: {pressed}; }}
"""


def _make_ok_btn(text: str = "حسناً", accent: str = "#1565c0") -> QPushButton:
    btn = QPushButton(text)
    base = _base()
    btn.setStyleSheet(_BTN_STYLE.format(
        bg=accent, fg="white",
        border=accent, hover=f"{accent}dd", border_h=accent,
        pressed=f"{accent}bb", fs=fs(base, 0),
    ))
    btn.setMinimumHeight(32)
    btn.setMinimumWidth(80)
    return btn


def _make_ghost_btn(text: str) -> QPushButton:
    btn = QPushButton(text)
    base = _base()
    btn.setStyleSheet(_BTN_STYLE.format(
        bg=_C.get('bg_surface_2', '#f5f5f5'),
        fg=_C.get('text_sec', '#555'),
        border=_C.get('border', '#e0e0e0'),
        hover=_C.get('bg_hover', '#eeeeee'),
        border_h=_C.get('border_med', '#bdbdbd'),
        pressed=_C.get('border', '#e0e0e0'),
        fs=fs(_base(), 0),
    ))
    btn.setMinimumHeight(32)
    btn.setMinimumWidth(80)
    return btn


class _MsgDialog(_DialogShell):
    """
    نافذة رسالة مخصصة — تستخدم _DialogShell للهيكل.
    """

    def __init__(self, parent, title: str, text: str,
                 kind: str = "info", yes_no: bool = False):
        icon, accent = _ICONS.get(kind, ("ℹ️", "#1565c0"))
        super().__init__(
            parent,
            title=title,
            icon=icon,
            accent=accent,
            min_width=380,
        )
        self._result = False
        self._build_body(text, kind, yes_no, accent)

    def _build_body(self, text: str, kind: str, yes_no: bool, accent: str):
        # النص
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        base = _base()
        lbl.setStyleSheet(
            f"font-size: {fs(base, 0)}pt;"
            f"color: {_C.get('text_primary', '#1c1b18')};"
            "background: transparent; border: none;"
        )
        self.body_layout.addWidget(lbl)

        # الأزرار
        if yes_no:
            btn_yes = _make_ok_btn("نعم", accent)
            btn_no  = _make_ghost_btn("لا")
            btn_yes.clicked.connect(self._on_yes)
            btn_no.clicked.connect(self.reject)
            self.btn_layout.addWidget(btn_yes)
            self.btn_layout.addWidget(btn_no)
        else:
            self._result = True
            btn_ok = _make_ok_btn("حسناً", accent)
            btn_ok.clicked.connect(self.accept)
            self.btn_layout.addWidget(btn_ok)

    def _on_yes(self):
        self._result = True
        self.accept()

    def result_yes(self) -> bool:
        return self._result


# ══════════════════════════════════════════════════════════
# API عام
# ══════════════════════════════════════════════════════════

def msg_question(parent, title: str, text: str) -> bool:
    """يرجع True لو اختار المستخدم 'نعم'."""
    dlg = _MsgDialog(parent, title, text, kind="question", yes_no=True)
    dlg.exec_()
    return dlg.result_yes()


def msg_info(parent, title: str, text: str):
    """رسالة معلومات."""
    _MsgDialog(parent, title, text, kind="info").exec_()


def msg_warning(parent, title: str, text: str):
    """رسالة تحذير."""
    _MsgDialog(parent, title, text, kind="warning").exec_()


def msg_critical(parent, title: str, text: str):
    """رسالة خطأ."""
    _MsgDialog(parent, title, text, kind="critical").exec_()