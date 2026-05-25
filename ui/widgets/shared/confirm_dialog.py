"""
ui/widgets/shared/confirm_dialog.py
=====================================
دوال تأكيد موحدة تستخدم _DialogShell للهيكل.

[إصلاح v2]:
  - _make_btn المحلية حُذفت — تُستخدم _make_btn من make_btn.py مباشرة
    لتجنب تكرار تعريف ستايل الأزرار.

الاستخدام:
    from ui.widgets.shared.confirm_dialog import confirm_delete, confirm_action

    if confirm_delete(self, "اسم العنصر"):
        do_delete()

    if confirm_action(self, "تأكيد الإرسال", "هل تريد إرسال الطلب؟", icon="📤"):
        do_send()
"""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore    import Qt

from ui.app_settings import _C, fs
from ui.widgets.shared.panles_helper.dialog_shell    import _DialogShell
from ui.widgets.shared.panles_helper.make_btn        import _make_btn
from ui.widgets.shared.panles_helper.colors_and_base import _base


def _make_confirm_btn(text: str, accent: str, ghost: bool = False):
    """يبني زر تأكيد بستايل مخصص فوق _make_btn الموحدة."""
    btn = _make_btn(text, "ghost" if ghost else "primary")
    btn.setMinimumHeight(34)
    btn.setMinimumWidth(80)
    # override اللون لو مش accent افتراضي
    if not ghost and accent and accent != _C.get("accent", "#1565c0"):
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {accent};
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
                font-size: {fs(_base(), 0)}pt;
                min-height: 34px;
                min-width: 80px;
            }}
            QPushButton:hover {{ background: {accent}dd; }}
        """)
    return btn


class _ConfirmDialog(_DialogShell):
    """
    نافذة تأكيد — تستخدم _DialogShell للهيكل.

    المعاملات:
        title        : عنوان النافذة
        message      : نص الرسالة
        icon         : emoji الأيقونة
        confirm_text : نص زر التأكيد
        cancel_text  : نص زر الإلغاء
        danger       : هل زر التأكيد بلون خطر (أحمر)
        accent       : لون مخصص لزر التأكيد
    """

    def __init__(self, parent=None,
                 title: str = "تأكيد",
                 message: str = "",
                 icon: str = "❓",
                 confirm_text: str = "تأكيد",
                 cancel_text: str = "إلغاء",
                 danger: bool = False,
                 accent: str = None):
        _accent = accent or ("#c62828" if danger else _C.get("accent", "#1565c0"))
        super().__init__(
            parent,
            title=title,
            icon=icon,
            accent=_accent,
            min_width=380,
        )
        self.setMaximumWidth(520)
        self._result = False
        self._build_body(message, confirm_text, cancel_text, _accent)

    def _build_body(self, message: str, confirm_text: str,
                    cancel_text: str, accent: str):
        base = _base()
        lbl = QLabel(message)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignTop)
        lbl.setStyleSheet(
            f"font-size: {fs(base, 0)}pt;"
            f"color: {_C.get('text_primary', '#1c1b18')};"
            "background: transparent; border: none; line-height: 1.6;"
        )
        self.body_layout.addWidget(lbl)

        btn_cancel = _make_confirm_btn(cancel_text, accent, ghost=True)
        btn_ok     = _make_confirm_btn(confirm_text, accent, ghost=False)

        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self._on_confirm)

        self.btn_layout.addWidget(btn_cancel)
        self.btn_layout.addWidget(btn_ok)

    def _on_confirm(self):
        self._result = True
        self.accept()

    def result_confirmed(self) -> bool:
        return self._result


# ══════════════════════════════════════════════════════════
# API عام — دوال سريعة
# ══════════════════════════════════════════════════════════

def confirm_delete(parent, item_name: str,
                   extra_msg: str = "") -> bool:
    """
    نافذة تأكيد الحذف.
    يرجع True لو وافق المستخدم.
    """
    msg = f"هل تريد حذف «{item_name}»؟"
    if extra_msg:
        msg += f"\n\n{extra_msg}"

    dlg = _ConfirmDialog(
        parent=parent,
        title="تأكيد الحذف",
        message=msg,
        icon="🗑️",
        confirm_text="حذف",
        cancel_text="إلغاء",
        danger=True,
    )
    dlg.exec_()
    return dlg.result_confirmed()


def confirm_action(parent,
                   title: str,
                   message: str,
                   icon: str = "❓",
                   confirm_text: str = "تأكيد",
                   cancel_text: str = "إلغاء",
                   danger: bool = False,
                   accent: str = None) -> bool:
    """
    نافذة تأكيد عامة.
    يرجع True لو وافق المستخدم.
    """
    dlg = _ConfirmDialog(
        parent=parent,
        title=title,
        message=message,
        icon=icon,
        confirm_text=confirm_text,
        cancel_text=cancel_text,
        danger=danger,
        accent=accent,
    )
    dlg.exec_()
    return dlg.result_confirmed()


def confirm_save(parent,
                 item_name: str = "",
                 extra_msg: str = "") -> bool:
    """نافذة تأكيد الحفظ."""
    msg = f"تأكيد حفظ «{item_name}»؟" if item_name else "تأكيد الحفظ؟"
    if extra_msg:
        msg += f"\n\n{extra_msg}"
    return confirm_action(
        parent, "تأكيد الحفظ", msg,
        icon="💾", confirm_text="حفظ",
        accent="#2e7d32",
    )