"""
ui/widgets/dialogs/confirm.py
==============================
نوافذ التأكيد الموحدة.

التحسينات:
  - [i18n] نصوص الأزرار والرسائل الافتراضية تستخدم مفاتيح الترجمة
    من i18n.py بدل النصوص العربية المباشرة.
  - confirm_delete, confirm_action, confirm_save تستخدم tr() بمفاتيح.
"""
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore    import Qt

from ui.theme import _C
from ui.font  import get_font_size, fs

from ..components.button import make_btn
from ..core.i18n         import tr
from .dialogs_base import DialogShell


def _confirm_btn(text: str, accent: str, ghost: bool = False) -> 'QPushButton':
    from PyQt5.QtWidgets import QPushButton
    btn = make_btn(text, "ghost" if ghost else "primary")
    btn.setMinimumHeight(34)
    btn.setMinimumWidth(80)
    if not ghost and accent and accent != _C.get("accent"):
        base = get_font_size()
        btn.setStyleSheet(f"""
            QPushButton {{
                background:{accent}; color:white; font-weight:bold;
                border:none; border-radius:6px; padding:0 20px;
                font-size:{fs(base, 0)}pt; min-height:34px; min-width:80px;
            }}
            QPushButton:hover {{ background:{accent}dd; }}
        """)
    return btn


class ConfirmDialog(DialogShell):
    """نافذة تأكيد قابلة لإعادة الاستخدام."""

    def __init__(self, parent=None, title: str = "",
                 message: str = "", icon: str = "❓",
                 confirm_text: str = "", cancel_text: str = "",
                 danger: bool = False, accent: str = None):
        _accent = accent or (_C["danger"] if danger else _C.get("accent"))
        _title = title or tr("confirm_action")
        super().__init__(parent, title=_title, icon=icon,
                         accent=_accent, min_width=380)
        self.setMaximumWidth(520)
        self._result = False
        _confirm = confirm_text or tr("confirm")
        _cancel  = cancel_text  or tr("cancel")
        self._build_body(message, _confirm, _cancel, _accent)

    def _build_body(self, message, confirm_text, cancel_text, accent):
        base = get_font_size()
        lbl = QLabel(message)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignTop)
        lbl.setStyleSheet(
            f"font-size:{fs(base, 0)}pt; color:{_C['text_primary']};"
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
    msg = tr("delete_confirm_msg", name=item_name)
    if extra_msg:
        msg += f"\n\n{extra_msg}"
    dlg = ConfirmDialog(
        parent,
        title=tr("confirm_delete"),
        message=msg,
        icon="🗑️",
        confirm_text=tr("delete"),
        cancel_text=tr("cancel"),
        danger=True,
    )
    dlg.exec_()
    return dlg.result_confirmed()


def confirm_action(parent, title: str, message: str, icon: str = "❓",
                   confirm_text: str = "", cancel_text: str = "",
                   danger: bool = False, accent: str = None) -> bool:
    dlg = ConfirmDialog(
        parent,
        title=title,
        message=message,
        icon=icon,
        confirm_text=confirm_text or tr("confirm"),
        cancel_text=cancel_text  or tr("cancel"),
        danger=danger,
        accent=accent,
    )
    dlg.exec_()
    return dlg.result_confirmed()


def confirm_save(parent, item_name: str = "", extra_msg: str = "") -> bool:
    if item_name:
        msg = tr("save_confirm_msg", name=item_name)
    else:
        msg = tr("confirm_save") + "؟"
    if extra_msg:
        msg += f"\n\n{extra_msg}"
    return confirm_action(
        parent,
        title=tr("confirm_save"),
        message=msg,
        icon="💾",
        confirm_text=tr("save"),
        accent=_C.get("success"),
    )