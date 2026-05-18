"""
ui/tabs/orders/orders/_status_delegate.py 
=============================
"""

from PyQt5.QtWidgets import (
    QStyledItemDelegate, QStyle, QApplication,
)
from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtGui  import QColor, QPainter, QBrush, QPen




from ui.widgets.shared.table_utils import (
    ROW_HEIGHT_LARGE,
)
from ui.app_settings import _C, get_font_size, fs

# ── ثوابت الحالة ──
STATUS_LABELS = {
    "pending":     ("⏳ انتظار",   "#b45309", "#fffbeb", "#fde68a"),
    "confirmed":   ("✅ مؤكد",     "#1d4ed8", "#eff6ff", "#bfdbfe"),
    "in_progress": ("🔧 تنفيذ",   "#6d28d9", "#f5f3ff", "#ddd6fe"),
    "ready":       ("📦 جاهز",    "#065f46", "#ecfdf5", "#a7f3d0"),
    "delivered":   ("🚚 مُسلَّم",  "#374151", "#f9fafb", "#e5e7eb"),
    "cancelled":   ("❌ ملغي",    "#991b1b", "#fef2f2", "#fecaca"),
    "on_hold":     ("⏸ معلق",    "#9a3412", "#fff7ed", "#fed7aa"),
}

PRIORITY_LABELS = {
    "low":    ("⬇",  "#9ca3af"),
    "normal": ("➡",  "#6b7280"),
    "high":   ("⬆",  "#f59e0b"),
    "urgent": ("🔴", "#ef4444"),
}

TYPE_LABELS = {
    "new":     "جديد",
    "reorder": "إعادة",
    "custom":  "مخصص",
}

# ══════════════════════════════════════════════════════════
# Delegate لعرض badge الحالة — محسّن
# ══════════════════════════════════════════════════════════

class _StatusDelegate(QStyledItemDelegate):
    """يرسم badge ملون وواضح لخلية الحالة."""

    def paint(self, painter: QPainter, option, index):
        painter.save()
        self.initStyleOption(option, index)
        style = option.widget.style() if option.widget else QApplication.style()
        style.drawPrimitive(QStyle.PE_PanelItemViewItem, option, painter, option.widget)

        status_key = index.data(Qt.UserRole + 1)
        text = index.data(Qt.DisplayRole) or ""
        info = STATUS_LABELS.get(status_key, (text, "#555", "#f5f5f5", "#e0e0e0"))
        _, fg, bg, bd = info

        rect   = option.rect
        pad_v  = 7
        pad_h  = 6
        badge_w = min(rect.width() - pad_h * 2, 90)
        badge_h = rect.height() - pad_v * 2
        badge_h = max(badge_h, 22)
        badge_h = min(badge_h, 28)
        badge_x = rect.x() + (rect.width() - badge_w) // 2
        badge_y = rect.y() + (rect.height() - badge_h) // 2
        badge_rect = QRect(badge_x, badge_y, badge_w, badge_h)

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(bg)))
        painter.setPen(QPen(QColor(bd), 1.2))
        painter.drawRoundedRect(badge_rect, 10, 10)

        painter.setPen(QPen(QColor(fg)))
        f = painter.font()
        f.setBold(True)
        base = get_font_size()
        f.setPointSize(max(8, fs(base, -1)))
        painter.setFont(f)
        painter.drawText(badge_rect, Qt.AlignCenter, text)
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(100, ROW_HEIGHT_LARGE)

