"""
ui/widgets/dialogs/message.py
==============================
نوافذ الرسائل الموحدة (info / warning / critical / question).

التحسينات:
  - [i18n] نصوص الأزرار ("حسناً"، "نعم"، "لا") تستخدم مفاتيح الترجمة
    بدل النصوص العربية المباشرة.
  - [إصلاح ثيم] _ICONS كان dict على مستوى الـ module بيقرأ _C وقت الـ
    import فقط، فالألوان كانت تتجمد على الثيم الأول. اتحول لدالة
    _icon_for(kind) بتُستدعى من جوه _refresh_style عشان تفضل محدّثة.
    باقي الستايلات (label, أزرار) بقت تتبني عبر WidgetMixin.
"""
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore    import Qt

from ui.font  import get_font_size, fs
from ui.theme import _C
from ..components.button import make_btn
from ..core.i18n         import tr
from .dialogs_base import DialogShell
from ui.constants import DIALOG_MIN_WIDTH, MSG_BTN_MIN_H


def _icon_for(kind: str) -> tuple:
    icons = {
        "question": ("❓", _C["accent"]),
        "info":     ("ℹ️",  _C["accent"]),
        "warning":  ("⚠️",  _C["warning"]),
        "critical": ("❌",  _C["danger"]),
    }
    return icons.get(kind, ("ℹ️", _C["accent"]))


class MessageDialog(DialogShell):
    """نافذة رسالة موحدة."""

    def __init__(self, parent, title: str, text: str,
                 kind: str = "info", yes_no: bool = False):
        icon, accent = _icon_for(kind)
        super().__init__(parent, title=title, icon=icon,
                         accent=accent, min_width=DIALOG_MIN_WIDTH)
        self._result = False
        self._text    = text
        self._yes_no  = yes_no
        self._build_body(text, yes_no)
        self._init_widget_mixin(theme=True, font=True, lang=True)
        self._refresh_style()
        self._refresh_lang()

    def _build_body(self, text: str, yes_no: bool):
        self._lbl = QLabel(text)
        self._lbl.setWordWrap(True)
        self._lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.body_layout.addWidget(self._lbl)

        if yes_no:
            self._btn_yes = make_btn(tr("yes"), "primary")
            self._btn_no  = make_btn(tr("no"),  "ghost")
            self._btn_yes.setMinimumHeight(MSG_BTN_MIN_H)
            self._btn_no.setMinimumHeight(MSG_BTN_MIN_H)
            self._btn_yes.clicked.connect(self._on_yes)
            self._btn_no.clicked.connect(self.reject)
            self.btn_layout.addWidget(self._btn_yes)
            self.btn_layout.addWidget(self._btn_no)
        else:
            self._result = True
            self._btn_ok = make_btn(tr("ok"), "primary")
            self._btn_ok.setMinimumHeight(MSG_BTN_MIN_H)
            self._btn_ok.clicked.connect(self.accept)
            self.btn_layout.addWidget(self._btn_ok)

    def _refresh_style(self, *_):
        super()._refresh_style()
        base = get_font_size()
        self._lbl.setStyleSheet(
            f"font-size:{fs(base,0)}pt; color:{_C.get('text_primary')};"
            "background:transparent; border:none;"
        )

    def _refresh_lang(self, *_):
        if self._yes_no:
            self._btn_yes.setText(tr("yes"))
            self._btn_no.setText(tr("no"))
        else:
            self._btn_ok.setText(tr("ok"))

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