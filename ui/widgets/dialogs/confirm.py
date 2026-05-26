"""
ui/widgets/dialogs/confirm.py
==============================
نوافذ التأكيد الموحدة.
"""
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore    import Qt

from ui.app_settings import _C, fs
from ..core          import get_font_size
from ..components.button import make_btn
from .shell import DialogShell


def _confirm_btn(text: str, accent: str, ghost: bool = False) -> 'QPushButton':
    from PyQt5.QtWidgets import QPushButton
    btn = make_btn(text, "ghost" if ghost else "primary")
    btn.setMinimumHeight(34)
    btn.setMinimumWidth(80)
    if not ghost and accent and accent != _C.get("accent", "#1565c0"):
        btn.setStyleSheet(f"""
            QPushButton {{
                background:{accent}; color:white; font-weight:bold;
                border:none; border-radius:6px; padding:0 20px;
                font-size:{fs(get_font_size(),0)}pt; min-height:34px; min-width:80px;
            }}
            QPushButton:hover {{ background:{accent}dd; }}
        """)
    return btn


class ConfirmDialog(DialogShell):
    """نافذة تأكيد قابلة لإعادة الاستخدام."""

    def __init__(self, parent=None, title: str = "تأكيد",
                 message: str = "", icon: str = "❓",
                 confirm_text: str = "تأكيد", cancel_text: str = "إلغاء",
                 danger: bool = False, accent: str = None):
        _accent = accent or ("#c62828" if danger else _C.get("accent", "#1565c0"))
        super().__init__(parent, title=title, icon=icon,
                         accent=_accent, min_width=380)
        self.setMaximumWidth(520)
        self._result = False
        self._build_body(message, confirm_text, cancel_text, _accent)

    def _build_body(self, message, confirm_text, cancel_text, accent):
        base = get_font_size()
        lbl = QLabel(message)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignTop)
        lbl.setStyleSheet(
            f"font-size:{fs(base,0)}pt; color:{_C.get('text_primary','#1c1b18')};"
            "background:transparent; border:none; line-height:1.6;"
        )
        self.body_layout.addWidget(lbl)

        btn_cancel = _confirm_btn(cancel_text, accent, ghost=True)
        btn_ok     = _confirm_btn(confirm_text, accent)
        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self._on_confirm)
        self.btn_layout.addWidget(btn_cancel)
        self.btn_layout.addWidget(btn_ok)

    def _on_confirm(self):
        self._result = True
        self.accept()

    def result_confirmed(self) -> bool:
        return self._result


# ── API سريع ──────────────────────────────────────────────

def confirm_delete(parent, item_name: str, extra_msg: str = "") -> bool:
    msg = f"هل تريد حذف «{item_name}»؟"
    if extra_msg:
        msg += f"\n\n{extra_msg}"
    dlg = ConfirmDialog(parent, title="تأكيد الحذف", message=msg,
                        icon="🗑️", confirm_text="حذف", danger=True)
    dlg.exec_()
    return dlg.result_confirmed()


def confirm_action(parent, title: str, message: str, icon: str = "❓",
                   confirm_text: str = "تأكيد", cancel_text: str = "إلغاء",
                   danger: bool = False, accent: str = None) -> bool:
    dlg = ConfirmDialog(parent, title=title, message=message, icon=icon,
                        confirm_text=confirm_text, cancel_text=cancel_text,
                        danger=danger, accent=accent)
    dlg.exec_()
    return dlg.result_confirmed()


def confirm_save(parent, item_name: str = "", extra_msg: str = "") -> bool:
    msg = f"تأكيد حفظ «{item_name}»؟" if item_name else "تأكيد الحفظ؟"
    if extra_msg:
        msg += f"\n\n{extra_msg}"
    return confirm_action(parent, "تأكيد الحفظ", msg,
                          icon="💾", confirm_text="حفظ", accent="#2e7d32")