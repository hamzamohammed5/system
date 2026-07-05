"""
ui/tabs/orders/orders/_status_delegate.py
"""
from PyQt5.QtWidgets import QStyledItemDelegate, QStyle, QApplication
from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtGui  import QColor, QPainter, QBrush, QPen

from ui.widgets.tables.tables import ROW_HEIGHT_LARGE
from ui.font import get_font_size, fs
from ui.theme import _C
from ui.constants import (
    STATUS_DELEGATE_PAD_V, STATUS_DELEGATE_PAD_H,
    STATUS_DELEGATE_BADGE_MAX_W, STATUS_DELEGATE_BADGE_MIN_H,
    STATUS_DELEGATE_BADGE_MAX_H, STATUS_DELEGATE_BADGE_RADIUS,
    STATUS_DELEGATE_BORDER_W, STATUS_DELEGATE_FONT_MIN_PT,
    STATUS_DELEGATE_SIZE_HINT_W,
)
from ..order_detail._status_config import get_status_labels


class _StatusDelegate(QStyledItemDelegate):
    """يرسم badge ملون وواضح لخلية الحالة."""

    def paint(self, painter: QPainter, option, index):
        painter.save()
        self.initStyleOption(option, index)
        style = option.widget.style() if option.widget else QApplication.style()
        style.drawPrimitive(QStyle.PE_PanelItemViewItem, option, painter, option.widget)

        STATUS_LABELS = get_status_labels()
        status_key = index.data(Qt.UserRole + 1)
        text = index.data(Qt.DisplayRole) or ""

        info = STATUS_LABELS.get(status_key)
        if info:
            _, fg, bg, bd = info
        else:
            fg, bg, bd = _C['text_sec'], _C['bg_surface_2'], _C['border']

        rect   = option.rect
        pad_v  = STATUS_DELEGATE_PAD_V
        pad_h  = STATUS_DELEGATE_PAD_H
        badge_w = min(rect.width() - pad_h * 2, STATUS_DELEGATE_BADGE_MAX_W)
        badge_h = rect.height() - pad_v * 2
        badge_h = max(badge_h, STATUS_DELEGATE_BADGE_MIN_H)
        badge_h = min(badge_h, STATUS_DELEGATE_BADGE_MAX_H)
        badge_x = rect.x() + (rect.width() - badge_w) // 2
        badge_y = rect.y() + (rect.height() - badge_h) // 2
        badge_rect = QRect(badge_x, badge_y, badge_w, badge_h)

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(bg)))
        painter.setPen(QPen(QColor(bd), STATUS_DELEGATE_BORDER_W))
        painter.drawRoundedRect(badge_rect, STATUS_DELEGATE_BADGE_RADIUS, STATUS_DELEGATE_BADGE_RADIUS)

        painter.setPen(QPen(QColor(fg)))
        f = painter.font()
        f.setBold(True)
        base = get_font_size()
        f.setPointSize(max(STATUS_DELEGATE_FONT_MIN_PT, fs(base, -1)))
        painter.setFont(f)
        painter.drawText(badge_rect, Qt.AlignCenter, text)
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(STATUS_DELEGATE_SIZE_HINT_W, ROW_HEIGHT_LARGE)
