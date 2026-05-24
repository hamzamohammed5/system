"""
ui/widgets/shared/confirm_dialog.py
=====================================
دوال تأكيد موحدة تستخدم BaseDialog بدل QMessageBox المتناثر.

تحل محل:
  - QMessageBox.question(...) في كل ملفات الحذف
  - confirm_delete() في ui/helpers.py
  - msg_question() في message_box.py (تكامل لا استبدال)

الاستخدام:
    from ui.widgets.shared.confirm_dialog import confirm_delete, confirm_action

    if confirm_delete(self, "اسم العنصر"):
        do_delete()

    if confirm_action(self, "تأكيد الإرسال", "هل تريد إرسال الطلب؟", icon="📤"):
        do_send()
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.app_settings import _C, fs
from ui.widgets.shared.panles_helper.colors_and_base import _base


# ══════════════════════════════════════════════════════════
# _ConfirmDialog — نافذة تأكيد موحدة
# ══════════════════════════════════════════════════════════

class _ConfirmDialog(QDialog):
    """
    نافذة تأكيد بتصميم موحد.

    المعاملات:
        title       : عنوان النافذة
        message     : نص الرسالة
        icon        : emoji الأيقونة
        confirm_text: نص زر التأكيد
        cancel_text : نص زر الإلغاء
        danger      : هل زر التأكيد بلون خطر (أحمر)
        accent      : لون مخصص لزر التأكيد
    """

    def __init__(self, parent=None,
                 title: str = "تأكيد",
                 message: str = "",
                 icon: str = "❓",
                 confirm_text: str = "تأكيد",
                 cancel_text: str = "إلغاء",
                 danger: bool = False,
                 accent: str = None):
        super().__init__(parent, Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(380)
        self.setMaximumWidth(520)
        self.setLayoutDirection(Qt.RightToLeft)
        self._result = False
        self._danger = danger
        self._accent = accent or ("#c62828" if danger else _C.get("accent", "#1565c0"))
        self._build(icon, title, message, confirm_text, cancel_text)

    def _build(self, icon, title, message, confirm_text, cancel_text):
        self.setStyleSheet(f"""
            QDialog {{
                background: {_C.get('bg_page', '#f9f9f9')};
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── هيدر ──
        hdr = QFrame()
        accent = self._accent
        hdr.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {accent}, stop:1 {accent}cc);
                border-bottom: 2px solid {accent}99;
            }}
        """)
        hdr.setFixedHeight(56)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(16, 0, 16, 0)

        lbl_ico = QLabel(icon)
        lbl_ico.setStyleSheet("font-size:22px; background:transparent; border:none;")
        lbl_title = QLabel(title)
        base = _base()
        lbl_title.setStyleSheet(
            f"font-size:{fs(base,+1)}pt; font-weight:bold; color:white;"
            "background:transparent; border:none;"
        )
        hl.addWidget(lbl_ico)
        hl.addWidget(lbl_title)
        hl.addStretch()
        root.addWidget(hdr)

        # ── الرسالة ──
        body = QFrame()
        body.setStyleSheet(f"background:{_C.get('bg_page','#f9f9f9')};")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(20, 18, 20, 16)
        bl.setSpacing(0)

        lbl_msg = QLabel(message)
        lbl_msg.setWordWrap(True)
        lbl_msg.setAlignment(Qt.AlignRight | Qt.AlignTop)
        lbl_msg.setStyleSheet(
            f"font-size:{fs(base,0)}pt; color:{_C.get('text_primary','#1c1b18')};"
            "background:transparent; border:none; line-height:1.6;"
        )
        bl.addWidget(lbl_msg)
        root.addWidget(body, stretch=1)

        # ── الفاصل ──
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{_C.get('border','#e0e0e0')}; border:none;")
        root.addWidget(sep)

        # ── أزرار ──
        btn_bar = QFrame()
        btn_bar.setStyleSheet(f"""
            QFrame {{
                background: {_C.get('bg_surface', 'white')};
            }}
        """)
        btn_bar.setFixedHeight(54)
        bl2 = QHBoxLayout(btn_bar)
        bl2.setContentsMargins(16, 0, 16, 0)
        bl2.setSpacing(8)
        bl2.addStretch()

        # زر الإلغاء
        btn_cancel = QPushButton(cancel_text)
        btn_cancel.setMinimumHeight(34)
        btn_cancel.setMinimumWidth(80)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: {_C.get('bg_surface_2','#f5f5f5')};
                color: {_C.get('text_sec','#555')};
                border: 1px solid {_C.get('border','#e0e0e0')};
                border-radius: 6px;
                padding: 0 16px;
                font-size: {fs(base,0)}pt;
            }}
            QPushButton:hover {{
                background: {_C.get('bg_hover','#eeeeee')};
            }}
        """)
        btn_cancel.clicked.connect(self.reject)

        # زر التأكيد
        btn_ok = QPushButton(confirm_text)
        btn_ok.setMinimumHeight(34)
        btn_ok.setMinimumWidth(80)
        btn_ok.setStyleSheet(f"""
            QPushButton {{
                background: {self._accent};
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
                font-size: {fs(base,0)}pt;
            }}
            QPushButton:hover {{
                background: {self._accent}dd;
            }}
        """)
        btn_ok.clicked.connect(self._on_confirm)

        bl2.addWidget(btn_cancel)
        bl2.addWidget(btn_ok)
        root.addWidget(btn_bar)

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
    نافذة تأكيد الحذف بتصميم موحد.

    item_name : اسم العنصر المراد حذفه
    extra_msg : رسالة إضافية (مثل تحذير الصفوف التابعة)

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