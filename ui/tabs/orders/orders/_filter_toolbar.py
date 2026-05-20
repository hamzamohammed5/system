"""
ui/tabs/orders/orders/_filter_toolbar.py
=========================================
شريط فلتر قائمة الطلبات.

✅ كل الأزرار حجمها Fixed — مش بتكبر مع النافذة أو الـ splitter
✅ الـ toolbar نفسه عرضه Expanding بس ارتفاعه Fixed
"""

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout,
    QFrame, QLineEdit, QPushButton, QComboBox, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui  import QFontMetrics, QFont

from ui.app_settings import _C
from ui.widgets.shared.panels import _make_btn

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

_BTN_NEW_SS = f"""
    QPushButton {{
        background: {_C['accent']}; color: white;
        border: none; border-radius: 8px;
        padding: 0 16px; font-weight: 700; font-size: 12px;
    }}
    QPushButton:hover {{ background: {_C['accent_hover']}; }}
"""

_COMBO_SS = f"""
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


def _fixed_btn(text: str, stylesheet: str, h: int = 36) -> QPushButton:
    """
    ✅ زر بحجم ثابت مبني على النص — مش بيكبر مع النافذة أبداً.
    """
    btn = QPushButton(text)
    btn.setStyleSheet(stylesheet)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFixedHeight(h)
    # حساب العرض بناءً على النص فقط
    fm = QFontMetrics(QFont("", 12))
    w  = fm.horizontalAdvance(text) + 40
    btn.setFixedWidth(max(w, 100))
    btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    return btn


class _FilterToolbar(QFrame):
    changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self.changed.emit)
        # ✅ الـ toolbar ارتفاعه Fixed
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
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

        # ── صف 1: زر جديد (Fixed) ──
        row0 = QHBoxLayout()
        row0.setContentsMargins(0, 0, 0, 0)
        row0.setSpacing(0)

        # ✅ Fixed size — مش بيكبر مطلقاً
        self.btn_new = _fixed_btn("＋  طلب جديد", _BTN_NEW_SS, h=36)
        row0.addWidget(self.btn_new)
        row0.addStretch(1)   # المساحة الفاضية على اليسار
        root.addLayout(row0)

        # ── صف 2: البحث (Expanding داخل الـ toolbar بس) ──
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍  بحث برقم الطلب أو اسم العميل...")
        self.inp_search.setFixedHeight(34)
        self.inp_search.setClearButtonEnabled(True)
        self.inp_search.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
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

        # ── صف 3: فلاتر (Expanding داخل الـ toolbar) ──
        row2 = QHBoxLayout()
        row2.setSpacing(6)

        self.cmb_status = QComboBox()
        self.cmb_status.setFixedHeight(28)
        self.cmb_status.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cmb_status.setStyleSheet(_COMBO_SS)
        self.cmb_status.addItem("كل الحالات", None)
        for k, (lbl, *_) in STATUS_LABELS.items():
            self.cmb_status.addItem(lbl, k)
        self.cmb_status.currentIndexChanged.connect(self.changed.emit)

        self.cmb_priority = QComboBox()
        self.cmb_priority.setFixedHeight(28)
        self.cmb_priority.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cmb_priority.setStyleSheet(_COMBO_SS)
        self.cmb_priority.addItem("كل الأولويات", None)
        for k, (icon, _) in PRIORITY_LABELS.items():
            self.cmb_priority.addItem(icon, k)
        self.cmb_priority.currentIndexChanged.connect(self.changed.emit)

        # ✅ زر مسح Fixed
        btn_reset = _make_btn("↺  مسح", "ghost")
        btn_reset.setToolTip("مسح كل الفلاتر")
        btn_reset.clicked.connect(self.reset)

        row2.addWidget(self.cmb_status,   stretch=3)
        row2.addWidget(self.cmb_priority, stretch=2)
        row2.addWidget(btn_reset)
        root.addLayout(row2)

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