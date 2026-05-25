"""
ui/widgets/shared/empty_state_helpers.py
==========================================
أدوات مساعدة موحدة لحالات الـ Empty State في الجداول والـ panels.

[إصلاح v2]:
  - _make_btn مستوردة في أعلى الملف بدل lazy import داخل _build

المتوفر:
  set_table_empty_state  — يضيف صف رسالة في الجدول الفارغ
  clear_table_empty_state — يمسح صف الحالة الفارغة
  EmptyPanelState        — widget حالة فارغة للـ panels
"""

from PyQt5.QtWidgets import (
    QWidget, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QLabel, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui  import QColor, QFont

from ui.app_settings import _C, fs
from ui.widgets.shared.panles_helper.colors_and_base import _base
from ui.widgets.shared.panles_helper.make_btn import _make_btn


# ══════════════════════════════════════════════════════════
# set_table_empty_state — صف رسالة في الجدول الفارغ
# ══════════════════════════════════════════════════════════

def set_table_empty_state(table: QTableWidget,
                           message: str = "لا توجد بيانات",
                           icon: str = "📋",
                           color: str = "#9ca3af"):
    """
    يضيف صفاً واحداً في الجدول يعرض رسالة "لا توجد بيانات".
    يُستدعى بعد table.setRowCount(0) مباشرةً.

    الاستخدام:
        self.table.setRowCount(0)
        if not rows:
            set_table_empty_state(self.table, "لا توجد قيود")
            return
    """
    table.setRowCount(1)
    table.setRowHeight(0, 60)

    col_count = table.columnCount()
    msg_text  = f"{icon}  {message}" if icon else message

    item = QTableWidgetItem(msg_text)
    item.setTextAlignment(Qt.AlignCenter)
    item.setForeground(QColor(color))
    f = QFont()
    f.setItalic(True)
    item.setFont(f)
    item.setFlags(Qt.ItemIsEnabled)

    table.setItem(0, 0, item)

    if col_count > 1:
        table.setSpan(0, 0, 1, col_count)


def clear_table_empty_state(table: QTableWidget):
    """يمسح صف الحالة الفارغة لو كان موجوداً."""
    if table.rowCount() == 1:
        item = table.item(0, 0)
        if item and not (item.flags() & Qt.ItemIsSelectable):
            table.setRowCount(0)
            if table.columnCount() > 1:
                table.setSpan(0, 0, 1, 1)


# ══════════════════════════════════════════════════════════
# EmptyPanelState — widget حالة فارغة للـ panels
# ══════════════════════════════════════════════════════════

class EmptyPanelState(QWidget):
    """
    Widget يعرض حالة فارغة مع أيقونة ونص وزر إجراء اختياري.

    الاستخدام:
        empty = EmptyPanelState(
            icon="📋",
            title="لا توجد قيود",
            subtitle="اضغط ➕ لإضافة قيد جديد",
            action_text="➕ إضافة",
        )
        empty.action_clicked.connect(self._add_new)
        layout.addWidget(empty)
    """

    action_clicked = pyqtSignal()

    def __init__(self, icon: str = "📋",
                 title: str = "لا توجد بيانات",
                 subtitle: str = "",
                 action_text: str = "",
                 color: str = "#9ca3af",
                 parent=None):
        super().__init__(parent)
        self._build(icon, title, subtitle, action_text, color)

    def _build(self, icon, title, subtitle, action_text, color):
        self.setStyleSheet("background: transparent;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(8)
        lay.setContentsMargins(20, 30, 20, 30)

        base = _base()

        if icon:
            lbl_icon = QLabel(icon)
            lbl_icon.setAlignment(Qt.AlignCenter)
            lbl_icon.setStyleSheet(
                f"font-size: {fs(base, +8)}pt; background: transparent; border: none;"
            )
            lay.addWidget(lbl_icon)

        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet(
            f"color: {color}; font-weight: 700; font-size: {fs(base, +1)}pt;"
            "background: transparent; border: none;"
        )
        lay.addWidget(lbl_title)

        if subtitle:
            lbl_sub = QLabel(subtitle)
            lbl_sub.setAlignment(Qt.AlignCenter)
            lbl_sub.setStyleSheet(
                f"color: {_C.get('text_muted', '#9ca3af')}; font-size: {fs(base, -1)}pt;"
                "background: transparent; border: none;"
            )
            lbl_sub.setWordWrap(True)
            lay.addWidget(lbl_sub)

        if action_text:
            btn = _make_btn(action_text, "primary")   # ← لا lazy import
            btn.clicked.connect(self.action_clicked.emit)
            lay.addWidget(btn, alignment=Qt.AlignCenter)

    def update_content(self, title: str = None, subtitle: str = None):
        """تحديث النص بدون إعادة بناء كاملة."""
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item and item.widget():
                w = item.widget()
                if isinstance(w, QLabel) and not w.text().startswith(("📋", "📦", "🔍")):
                    if title and i == 1:
                        w.setText(title)
                    elif subtitle and i == 2:
                        w.setText(subtitle)