"""
ui/helpers.py
=============
أدوات UI مشتركة — لا منطق عمل هنا، فقط مساعدات واجهة.
"""

from PyQt5.QtWidgets import (
    QPushButton, QLabel, QHBoxLayout, QWidget,
    QTableWidget, QHeaderView, QMessageBox,
    QAbstractItemView, QSizePolicy,
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt


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


# ══════════════════════════════════════════════════════════
# الجداول — مع tooltip تلقائي وعرض مرن
# ══════════════════════════════════════════════════════════

def _install_tooltip_delegate(table: QTableWidget):
    """
    يضيف tooltip تلقائي لأي خلية نصها أطول من عرضها.
    يشتغل عن طريق override لـ itemChanged + كل مرة بيتحدث الجدول.
    """
    # نربط الـ signal مرة واحدة فقط
    def _update_tooltips():
        for r in range(table.rowCount()):
            for c in range(table.columnCount()):
                item = table.item(r, c)
                if item:
                    # دايمًا نضيف tooltip بالنص الكامل
                    item.setToolTip(item.text())

    # نربطه بأي تغيير في الجدول
    table.model().dataChanged.connect(lambda *_: _update_tooltips())
    table.model().rowsInserted.connect(lambda *_: _update_tooltips())


def make_table(columns: list[str], stretch_col: int = -1) -> QTableWidget:
    """
    إنشاء جدول جاهز بإعدادات موحدة:
    - الأعمدة قابلة للسحب والتغيير
    - النص في الخلايا يظهر كـ tooltip كامل
    - الجدول نفسه scrollable أفقياً وعمودياً
    """
    table = QTableWidget()
    table.setColumnCount(len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)

    hh = table.horizontalHeader()

    if stretch_col >= 0:
        # العمود المحدد يتمدد — الباقي Interactive (قابل للسحب)
        for i in range(len(columns)):
            if i == stretch_col:
                hh.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                hh.setSectionResizeMode(i, QHeaderView.Interactive)
    else:
        # الأعمدة كلها Interactive والأخير يتمدد
        for i in range(len(columns)):
            hh.setSectionResizeMode(i, QHeaderView.Interactive)
        hh.setStretchLastSection(True)

    # الـ header نفسه قابل للسحب
    hh.setMinimumSectionSize(40)
    hh.setDefaultSectionSize(100)

    # scroll أفقي لما الأعمدة تفضل ضيقة
    table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
    table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

    # word wrap في الـ header
    hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)

    # tooltip تلقائي
    _install_tooltip_delegate(table)

    return table


def setup_table_columns(table: QTableWidget,
                        widths: dict[int, int] | None = None,
                        stretch_col: int = -1,
                        min_width: int = 50):
    """
    إعداد عرض الأعمدة بشكل مرن:
    - widths: dict من {col_index: width} للأعمدة ذات العرض المبدئي المحدد
    - stretch_col: العمود اللي يتمدد مع الشاشة (الاسم عادةً)
    - min_width: أقل عرض للأعمدة Interactive
    """
    hh = table.horizontalHeader()
    n  = table.columnCount()

    for i in range(n):
        if i == stretch_col:
            hh.setSectionResizeMode(i, QHeaderView.Stretch)
        else:
            hh.setSectionResizeMode(i, QHeaderView.Interactive)
            if widths and i in widths:
                table.setColumnWidth(i, widths[i])

    hh.setMinimumSectionSize(min_width)


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