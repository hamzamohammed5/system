"""
ui/widgets/dialogs/confirm.py
==============================
نوافذ التأكيد الموحدة.

التحسينات:
  - [i18n] نصوص الأزرار والرسائل الافتراضية تستخدم مفاتيح الترجمة
    من i18n.py بدل النصوص العربية المباشرة.
  - confirm_delete, confirm_action, confirm_save تستخدم tr() بمفاتيح.
  - [إصلاح ثيم] ConfirmDialog كان بيبني الـ stylesheet بتاع label
    والأزرار مرة واحدة بس في _build_body بقيم _C/get_font_size وقت
    الإنشاء. اتحول لـ WidgetMixin (theme+font) عشان يتحدث تلقائياً،
    وبناء الأزرار اتفصل عن تطبيق الستايل عليها.
"""
from PyQt5.QtWidgets import QLabel, QPushButton
from PyQt5.QtCore    import Qt

from ui.theme import _C
from ui.font  import get_font_size, fs

from ..components.button import make_btn
from ..core.i18n         import tr
from .dialogs_base import DialogShell


def _confirm_btn(text: str, ghost: bool = False) -> QPushButton:
    btn = make_btn(text, "ghost" if ghost else "primary")
    btn.setMinimumHeight(34)
    btn.setMinimumWidth(80)
    return btn


def _style_confirm_btn(btn: QPushButton, accent: str) -> None:
    base = get_font_size()
    btn.setStyleSheet(f"""
        QPushButton {{
            background:{accent}; color:white; font-weight:bold;
            border:none; border-radius:6px; padding:0 20px;
            font-size:{fs(base, 0)}pt; min-height:34px; min-width:80px;
        }}
        QPushButton:hover {{ background:{accent}dd; }}
    """)


class ConfirmDialog(DialogShell):
    """نافذة تأكيد قابلة لإعادة الاستخدام."""

    def __init__(self, parent=None, title: str = "",
                 message: str = "", icon: str = "❓",
                 confirm_text: str = "", cancel_text: str = "",
                 danger: bool = False, accent: str = None):
        self._danger      = danger
        self._explicit_accent = accent
        _accent = self._resolve_accent()
        _title = title or tr("confirm_action")
        super().__init__(parent, title=_title, icon=icon,
                         accent=_accent, min_width=380)
        self.setMaximumWidth(520)
        self._result = False
        self._message      = message
        self._confirm_text = confirm_text
        self._cancel_text  = cancel_text
        self._build_body(message)
        self._init_widget_mixin(theme=True, font=True, lang=True)
        self._refresh_style()
        self._refresh_lang()

    def _resolve_accent(self) -> str:
        return self._explicit_accent or (
            _C["danger"] if self._danger else _C.get("accent")
        )

    def _build_body(self, message: str):
        self._lbl = QLabel(message)
        self._lbl.setWordWrap(True)
        self._lbl.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.body_layout.addWidget(self._lbl)

        self._btn_cancel = _confirm_btn(self._cancel_text or tr("cancel"), ghost=True)
        self._btn_ok     = _confirm_btn(self._confirm_text or tr("confirm"))
        self._btn_cancel.clicked.connect(self.reject)
        self._btn_ok.clicked.connect(self._on_confirm)
        self.btn_layout.addWidget(self._btn_cancel)
        self.btn_layout.addWidget(self._btn_ok)

    def _refresh_style(self, *_):
        super()._refresh_style()
        base = get_font_size()
        self._lbl.setStyleSheet(
            f"font-size:{fs(base, 0)}pt; color:{_C['text_primary']};"
            "background:transparent; border:none; line-height:1.6;"
        )
        accent = self._resolve_accent()
        if accent and accent != _C.get("accent"):
            _style_confirm_btn(self._btn_ok, accent)

    def _refresh_lang(self, *_):
        self._btn_cancel.setText(self._cancel_text or tr("cancel"))
        self._btn_ok.setText(self._confirm_text or tr("confirm"))

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