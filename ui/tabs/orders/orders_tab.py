"""
ui/tabs/orders/orders_tab.py  — نسخة UX v3 محسّنة
=============================
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QSplitter,
)
from PyQt5.QtCore import Qt

from ui.tabs.orders._order_detail import _OrderDetail



from ui.app_settings import _C

from .orders._orders_list_panel import _OrdersListPanel
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

_BG     = "#f8f9fb"
_WHITE  = "#ffffff"
_BLUE   = _C['accent']
_BORDER = _C['border']






# ══════════════════════════════════════════════════════════
# تبويب الطلبات الرئيسي
# ══════════════════════════════════════════════════════════

class OrdersTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(4)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {_C['border']};
            }}
            QSplitter::handle:hover {{
                background: {_C['accent_mid']};
            }}
            QSplitter::handle:pressed {{
                background: {_C['accent']};
            }}
        """)

        self._list   = _OrdersListPanel(self.conn)
        self._detail = _OrderDetail(self.conn)

        splitter.addWidget(self._list)
        splitter.addWidget(self._detail)

        splitter.setSizes([480, 640])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        root.addWidget(splitter)

        self._list.order_selected.connect(self._on_order_selected)
        self._list.new_order.connect(self._on_new_order)
        self._detail.saved.connect(self._on_saved)
        self._detail.deleted.connect(self._on_deleted)
        self._detail.status_changed.connect(self._on_status_changed)

    def _on_order_selected(self, order_id: int):
        self._detail.load_order(order_id)

    def _on_new_order(self):
        self._detail.new_order()

    def _on_saved(self, order_id: int):
        self._list.refresh()
        self._list.select_order(order_id)

    def _on_deleted(self):
        self._list.refresh()
        self._detail.clear()

    def _on_status_changed(self, order_id: int):
        self._list.refresh()
        self._list.select_order(order_id)
        self._detail.load_order(order_id)

    def refresh(self):
        self._list.refresh()