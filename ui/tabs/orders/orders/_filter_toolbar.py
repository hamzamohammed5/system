"""
ui/tabs/orders/orders/_filter_toolbar.py
=========================================
شريط فلتر قائمة الطلبات — يستخدم _C palette بالكامل.
"""

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout,
    QFrame, QLineEdit, QPushButton, QComboBox,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

from ui.app_settings import _C
from ui.widgets.shared.panels import _make_btn

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
    "low":    ("⬇", "#9ca3af"),
    "normal": ("➡", "#6b7280"),
    "high":   ("⬆", "#f59e0b"),
    "urgent": ("🔴", "#ef4444"),
}


class _FilterToolbar(QFrame):
    """شريط البحث والفلاتر لقائمة الطلبات."""

    changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self.changed.emit)
        self._build()

    def _build(self):
        self.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_input']};
                border: none;
                border-bottom: 1px solid {_C['border']};
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 10)
        root.setSpacing(8)

        # ── صف 1: زر جديد ──
        row0 = QHBoxLayout()
        self.btn_new = QPushButton("＋  طلب جديد")
        self.btn_new.setMinimumHeight(36)
        self.btn_new.setMinimumWidth(130)
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.setStyleSheet(f"""
            QPushButton {{
                background: {_C['accent']}; color: white;
                border: none; border-radius: 8px;
                padding: 0 16px; font-weight: 700; font-size: 12px;
            }}
            QPushButton:hover {{ background: {_C['accent_hover']}; }}
        """)
        row0.addWidget(self.btn_new)
        row0.addStretch()
        root.addLayout(row0)

        # ── صف 2: البحث ──
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍  بحث برقم الطلب أو اسم العميل...")
        self.inp_search.setMinimumHeight(34)
        self.inp_search.setClearButtonEnabled(True)
        self.inp_search.setStyleSheet(f"""
            QLineEdit {{
                background: {_C['bg_input']};
                border: 1.5px solid {_C['border_med']};
                border-radius: 6px;
                padding: 0 10px;
                font-size: 12px;
                color: {_C['text_primary']};
            }}
            QLineEdit:focus {{ border-color: {_C['accent']}; background: white; }}
        """)
        self.inp_search.textChanged.connect(lambda: self._timer.start())
        root.addWidget(self.inp_search)

        # ── صف 3: فلاتر + زر مسح ──
        row2 = QHBoxLayout()
        row2.setSpacing(6)

        _combo_ss = f"""
            QComboBox {{
                background: {_C['bg_surface_2']};
                border: 1px solid {_C['border']};
                border-radius: 5px;
                padding: 0 8px;
                min-height: 28px;
                font-size: 11px;
                color: {_C['text_primary']};
            }}
            QComboBox:focus {{ border-color: {_C['accent']}; }}
            QComboBox::drop-down {{ border: none; width: 16px; }}
            QComboBox QAbstractItemView {{
                background: {_C['bg_input']};
                border: 1px solid {_C['border_med']};
                selection-background-color: {_C['accent_light']};
                selection-color: {_C['accent_text']};
                outline: none;
            }}
        """

        self.cmb_status = QComboBox()
        self.cmb_status.setMinimumHeight(28)
        self.cmb_status.setStyleSheet(_combo_ss)
        self.cmb_status.addItem("كل الحالات", None)
        for k, (lbl, *_) in STATUS_LABELS.items():
            self.cmb_status.addItem(lbl, k)
        self.cmb_status.currentIndexChanged.connect(self.changed.emit)

        self.cmb_priority = QComboBox()
        self.cmb_priority.setMinimumHeight(28)
        self.cmb_priority.setStyleSheet(_combo_ss)
        self.cmb_priority.addItem("كل الأولويات", None)
        for k, (icon, _) in PRIORITY_LABELS.items():
            self.cmb_priority.addItem(icon, k)
        self.cmb_priority.currentIndexChanged.connect(self.changed.emit)

        btn_reset = _make_btn("↺  مسح", "ghost")
        btn_reset.setToolTip("مسح كل الفلاتر")
        btn_reset.clicked.connect(self.reset)

        row2.addWidget(self.cmb_status, stretch=3)
        row2.addWidget(self.cmb_priority, stretch=2)
        row2.addWidget(btn_reset, stretch=1)
        root.addLayout(row2)

    # ── properties ──────────────────────────────────────

    @property
    def search_text(self) -> str:
        return self.inp_search.text().strip().lower()

    @property
    def status_filter(self):
        return self.cmb_status.currentData()

    @property
    def priority_filter(self):
        return self.cmb_priority.currentData()

    def reset(self):
        self.cmb_status.setCurrentIndex(0)
        self.cmb_priority.setCurrentIndex(0)
        self.inp_search.clear()