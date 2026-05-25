"""
ui/widgets/shared/message_box.py
=================================
دوال بديلة لـ QMessageBox بخلفية بيضاء مضمونة.

[إصلاح v2]:
  - _make_ok_btn و _make_ghost_btn تستخدمان _make_btn من make_btn.py
    بدل تعريف ستايلات مستقلة.

استخدمها بدل QMessageBox مباشرة في كل مكان:

    from ui.widgets.shared.message_box import msg_question, msg_info, msg_warning, msg_critical

    if msg_question(self, "تأكيد", "هل تريد الحذف؟"):
        ...

    msg_info(self, "تم", "تم الحفظ بنجاح")
    msg_warning(self, "تنبيه", "هذا الحقل مطلوب")
    msg_critical(self, "خطأ", "حدث خطأ غير متوقع")
"""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore    import Qt

from ui.app_settings import _C, fs
from ui.widgets.shared.panles_helper.dialog_shell    import _DialogShell
from ui.widgets.shared.panles_helper.make_btn        import _make_btn
from ui.widgets.shared.panles_helper.colors_and_base import _base


_ICONS = {
    "question": ("❓", "#1565c0"),
    "info":     ("ℹ️",  "#1565c0"),
    "warning":  ("⚠️",  "#e65100"),
    "critical": ("❌",  "#c62828"),
}


def _make_ok_btn(text: str = "حسناً", accent: str = "#1565c0"):
    """زر OK — يستخدم _make_btn الموحدة مع override اللون لو مختلف."""
    btn = _make_btn(text, "primary")
    btn.setMinimumHeight(32)
    btn.setMinimumWidth(80)
    if accent and accent != _C.get("accent", "#1565c0"):
        base = _base()
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {accent}; color: white;
                border: 1px solid {accent}; border-radius: 6px;
                padding: 5px 20px; min-width: 72px; min-height: 30px;
                font-size: {fs(base, 0)}pt;
            }}
            QPushButton:hover {{ background: {accent}dd; border-color: {accent}; }}
            QPushButton:pressed {{ background: {accent}bb; }}
        """)
    return btn


def _make_ghost_btn(text: str):
    """زر إلغاء — يستخدم _make_btn الموحدة بستايل ghost."""
    btn = _make_btn(text, "ghost")
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