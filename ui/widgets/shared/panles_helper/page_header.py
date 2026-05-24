"""
ui/widgets/shared/panles_helper/page_header.py
===============================================
PageHeader — هيدر موحد لصفحات الأقسام الرئيسية.

يكمل:
  - DetailHeader  : هيدر صفحة التفاصيل
  - ListHeader    : هيدر لوحة القائمة
  - SectionHeader : هيدر قسم داخل صفحة

PageHeader هو هيدر الصفحة الكاملة (أعلى tab أو section).

الاستخدام:
    hdr = PageHeader(
        title="إدارة المخزون",
        subtitle="إضافة وتعديل وتتبع المنتجات",
        icon="📦",
    )
    layout.addWidget(hdr)
    hdr.add_action("📤 تصدير", callback=self._export)
    hdr.add_action("⚙️ إعدادات", callback=self._settings, style="ghost")
"""

from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.app_settings import _C, fs
from .colors_and_base import _base
from .make_btn import _make_btn


class PageHeader(QFrame):
    """
    هيدر موحد لصفحات الأقسام الرئيسية.

    المعاملات:
        title    : عنوان الصفحة
        subtitle : نص توضيحي (اختياري)
        icon     : emoji الأيقونة
        accent   : لون التأكيد (hex)
        compact  : نسخة مضغوطة
    """

    def __init__(self, title: str = "",
                 subtitle: str = "",
                 icon: str = "",
                 accent: str = None,
                 compact: bool = False,
                 parent=None):
        super().__init__(parent)
        self._accent  = accent or _C.get('accent', '#1565c0')
        self._compact = compact
        self._build(title, subtitle, icon)

    def _build(self, title, subtitle, icon):
        self.setStyleSheet(f"""
            QFrame {{
                background: {_C.get('bg_surface', 'white')};
                border-bottom: 1px solid {_C.get('border', '#e0e0e0')};
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        h_pad = 12 if self._compact else 20
        v_pad = 8  if self._compact else 14

        lay = QHBoxLayout(self)
        lay.setContentsMargins(h_pad, v_pad, h_pad, v_pad)
        lay.setSpacing(12)

        # أيقونة
        if icon:
            base = _base()
            size = fs(base, +2) if not self._compact else fs(base, +1)
            lbl_icon = QLabel(icon)
            lbl_icon.setStyleSheet(
                f"font-size:{size}pt; background:transparent; border:none;"
            )
            lbl_icon.setAlignment(Qt.AlignVCenter)
            lay.addWidget(lbl_icon)

        # عمود العنوان
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.setContentsMargins(0, 0, 0, 0)

        base = _base()
        self._lbl_title = QLabel(title)
        f = QFont()
        f.setPointSize(fs(base, +2) if not self._compact else fs(base, +1))
        f.setBold(True)
        self._lbl_title.setFont(f)
        self._lbl_title.setStyleSheet(
            f"color:{_C.get('text_primary','#1c1b18')};"
            "background:transparent; border:none;"
        )
        text_col.addWidget(self._lbl_title)

        if subtitle:
            self._lbl_sub = QLabel(subtitle)
            self._lbl_sub.setStyleSheet(
                f"color:{_C.get('text_muted','#9ca3af')}; font-size:{fs(base,-1)}pt;"
                "background:transparent; border:none;"
            )
            text_col.addWidget(self._lbl_sub)
        else:
            self._lbl_sub = None

        lay.addLayout(text_col, stretch=1)

        # حاوية الأزرار
        self._btn_row = QHBoxLayout()
        self._btn_row.setSpacing(8)
        lay.addLayout(self._btn_row)

    # ── API ──────────────────────────────────────────────

    def set_title(self, text: str):
        self._lbl_title.setText(text)

    def set_subtitle(self, text: str):
        if self._lbl_sub:
            self._lbl_sub.setText(text)

    def add_action(self, text: str, callback=None,
                   style: str = "primary"):
        """يضيف زر في يسار الهيدر."""
        btn = _make_btn(text, style)
        if callback:
            btn.clicked.connect(callback)
        self._btn_row.addWidget(btn)
        return btn