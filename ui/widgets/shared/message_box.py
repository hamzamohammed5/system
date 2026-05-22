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

from PyQt5.QtWidgets import QMessageBox, QDialog, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QFrame
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QColor


# ── الألوان الثابتة (مستقلة عن _C عشان تشتغل في أي وقت) ──
_BG       = "#FAFAF8"
_TEXT     = "#1C1B18"
_BTN_BG   = "#F0EEE9"
_BTN_HV   = "#ECEAE4"
_BTN_PR   = "#E4E2DA"
_BORDER   = "#C8C4B8"
_BORDER_S = "#6B6760"


_STYLE = f"""
QDialog {{
    background: {_BG};
}}
QDialog QWidget {{
    background: {_BG};
    color: {_TEXT};
}}
QLabel {{
    background: transparent;
    color: {_TEXT};
    font-size: 11pt;
}}
QPushButton {{
    background: {_BTN_BG};
    color: {_TEXT};
    border: 1px solid {_BORDER};
    border-radius: 6px;
    padding: 5px 20px;
    min-width: 72px;
    min-height: 30px;
    font-size: 11pt;
}}
QPushButton:hover {{
    background: {_BTN_HV};
    border-color: {_BORDER_S};
}}
QPushButton:pressed {{
    background: {_BTN_PR};
}}
QFrame#sep {{
    background: {_BORDER};
    border: none;
}}
"""


# ══════════════════════════════════════════════════════════
# _MsgDialog — نافذة رسالة مخصصة بالكامل
# ══════════════════════════════════════════════════════════

_ICONS = {
    "question": "❓",
    "info":     "ℹ️",
    "warning":  "⚠️",
    "critical": "❌",
}


class _MsgDialog(QDialog):
    """
    QDialog بسيط بخلفية بيضاء مضمونة 100%.
    بديل كامل لـ QMessageBox.
    """

    def __init__(self, parent, title: str, text: str,
                 kind: str = "info", yes_no: bool = False):
        super().__init__(parent, Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(360)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(14)

        # ── صف الأيقونة + النص ──
        msg_row = QHBoxLayout()
        msg_row.setSpacing(14)

        ico = QLabel(_ICONS.get(kind, "ℹ️"))
        ico.setStyleSheet("font-size: 22pt; background: transparent;")
        ico.setAlignment(Qt.AlignTop)
        ico.setFixedWidth(36)

        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl.setStyleSheet(f"font-size: 11pt; color: {_TEXT}; background: transparent;")

        msg_row.addWidget(lbl, stretch=1)
        msg_row.addWidget(ico)
        root.addLayout(msg_row)

        # ── فاصل ──
        sep = QFrame()
        sep.setObjectName("sep")
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        root.addWidget(sep)

        # ── أزرار ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()

        if yes_no:
            self._result = False
            btn_yes = QPushButton("نعم")
            btn_no  = QPushButton("لا")
            btn_yes.clicked.connect(self._on_yes)
            btn_no.clicked.connect(self.reject)
            btn_row.addWidget(btn_yes)
            btn_row.addWidget(btn_no)
        else:
            self._result = True
            btn_ok = QPushButton("حسناً")
            btn_ok.clicked.connect(self.accept)
            btn_row.addWidget(btn_ok)

        root.addLayout(btn_row)

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
