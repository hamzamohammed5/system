"""
ui/widgets/dialogs/message.py
==============================
نوافذ الرسائل الموحدة (info / warning / critical / question).
"""
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore    import Qt

from ui.app_settings import _C, fs
from ..core          import get_font_size
from ..components.button import make_btn
from .shell import DialogShell

_ICONS = {
    "question": ("❓", _C["accent"]),
    "info":     ("ℹ️",  _C["accent"]),
    "warning":  ("⚠️",  _C["warning"]),
    "critical": ("❌",  _C["danger"]),
}


class MessageDialog(DialogShell):
    """نافذة رسالة موحدة."""

    def __init__(self, parent, title: str, text: str,
                 kind: str = "info", yes_no: bool = False):
        icon, accent = _ICONS.get(kind, ("ℹ️", _C["accent"]))
        super().__init__(parent, title=title, icon=icon,
                         accent=accent, min_width=380)
        self._result = False
        self._build_body(text, yes_no, accent)

    def _build_body(self, text: str, yes_no: bool, accent: str):
        base = get_font_size()
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl.setStyleSheet(
            f"font-size:{fs(base,0)}pt; color:{_C.get('text_primary')};"
            "background:transparent; border:none;"
        )
        self.body_layout.addWidget(lbl)

        if yes_no:
            btn_yes = make_btn("نعم", "primary")
            btn_no  = make_btn("لا",  "ghost")
            btn_yes.setMinimumHeight(32)
            btn_no.setMinimumHeight(32)
            btn_yes.clicked.connect(self._on_yes)
            btn_no.clicked.connect(self.reject)
            self.btn_layout.addWidget(btn_yes)
            self.btn_layout.addWidget(btn_no)
        else:
            self._result = True
            btn_ok = make_btn("حسناً", "primary")
            btn_ok.setMinimumHeight(32)
            btn_ok.clicked.connect(self.accept)
            self.btn_layout.addWidget(btn_ok)

    def _on_yes(self):
        self._result = True
        self.accept()

    def result_yes(self) -> bool:
        return self._result


# ── API سريع ──────────────────────────────────────────────

def msg_question(parent, title: str, text: str) -> bool:
    dlg = MessageDialog(parent, title, text, kind="question", yes_no=True)
    dlg.exec_()
    return dlg.result_yes()


def msg_info(parent, title: str, text: str):
    MessageDialog(parent, title, text, kind="info").exec_()


def msg_warning(parent, title: str, text: str):
    MessageDialog(parent, title, text, kind="warning").exec_()


def msg_critical(parent, title: str, text: str):
    MessageDialog(parent, title, text, kind="critical").exec_()