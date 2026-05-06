"""
ui/helpers.py
=============
أدوات UI مشتركة — لا منطق عمل هنا، فقط مساعدات واجهة.
"""

from PyQt5.QtWidgets import (
    QPushButton, QLabel, QHBoxLayout, QWidget,
    QTableWidget, QHeaderView, QMessageBox
)
from PyQt5.QtGui import QFont


# ══════════════════════════════════════════════════════════
# مساعدات إنشاء عناصر UI
# ══════════════════════════════════════════════════════════

def bold_label(text: str) -> QLabel:
    lbl = QLabel(text)
    f = QFont()
    f.setBold(True)
    lbl.setFont(f)
    return lbl


def section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet("font-weight:bold; font-size:13px; color:#333;")
    return lbl


def danger_button(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setStyleSheet("color:#c0392b;")
    return btn


def success_button(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setStyleSheet("background:#27ae60; color:white; font-weight:bold; padding:4px 14px;")
    return btn


def make_table(columns: list[str], stretch_col: int = -1) -> QTableWidget:
    """إنشاء جدول جاهز بإعدادات موحدة."""
    from PyQt5.QtWidgets import QAbstractItemView
    table = QTableWidget()
    table.setColumnCount(len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    if stretch_col >= 0:
        table.horizontalHeader().setSectionResizeMode(stretch_col, QHeaderView.Stretch)
    else:
        table.horizontalHeader().setStretchLastSection(True)
    return table


def buttons_row(*buttons) -> QHBoxLayout:
    """صف أفقي من الأزرار مع stretch في النهاية."""
    row = QHBoxLayout()
    for btn in buttons:
        row.addWidget(btn)
    row.addStretch()
    return row


# ══════════════════════════════════════════════════════════
# EditModeMixin — يُضاف لأي تبويب يحتاج وضع إضافة/تعديل
# ══════════════════════════════════════════════════════════

class EditModeMixin:
    """
    Mixin يوفر تبديل وضع الإضافة ↔ التعديل.

    الاستخدام:
        class MyTab(QWidget, EditModeMixin):
            def __init__(self):
                ...
                self.init_edit_mode(
                    add_btn    = self.btn_add,
                    save_btn   = self.btn_save,
                    cancel_btn = self.btn_cancel,
                    mode_label = self.lbl_mode,   # اختياري
                )
    """

    def init_edit_mode(self, add_btn, save_btn, cancel_btn, mode_label=None):
        self._em_add_btn    = add_btn
        self._em_save_btn   = save_btn
        self._em_cancel_btn = cancel_btn
        self._em_mode_label = mode_label
        self._editing_id    = None
        save_btn.setVisible(False)
        cancel_btn.setVisible(False)

    def enter_edit_mode(self, record_id: int, label_text: str = ""):
        self._editing_id = record_id
        self._em_add_btn.setVisible(False)
        self._em_save_btn.setVisible(True)
        self._em_cancel_btn.setVisible(True)
        if self._em_mode_label and label_text:
            self._em_mode_label.setText(label_text)

    def exit_edit_mode(self, default_label: str = ""):
        self._editing_id = None
        self._em_add_btn.setVisible(True)
        self._em_save_btn.setVisible(False)
        self._em_cancel_btn.setVisible(False)
        if self._em_mode_label and default_label:
            self._em_mode_label.setText(default_label)

    @property
    def is_editing(self) -> bool:
        return self._editing_id is not None


# ══════════════════════════════════════════════════════════
# تأكيد الحذف
# ══════════════════════════════════════════════════════════

def confirm_delete(parent, name: str) -> bool:
    return QMessageBox.question(
        parent, "تأكيد الحذف", f"هل تريد حذف «{name}»؟",
        QMessageBox.Yes | QMessageBox.No
    ) == QMessageBox.Yes
