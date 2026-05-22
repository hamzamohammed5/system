"""
ui/tabs/companies/_link_item_picker.py
=======================================
Dialog بسيط لاختيار عنصر مشترك للربط.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem,
)
from PyQt5.QtCore import Qt
from ui.app_settings import _C

_TYPE_AR = {
    "raw":        "خامة",
    "machine":    "ماكينة",
    "labor_op":   "عملية عمالة",
    "machine_op": "عملية تشغيل",
}


class LinkItemPicker(QDialog):
    def __init__(self, items: list, parent=None):
        super().__init__(parent)
        self.selected_id = None
        self._items      = items

        self.setWindowTitle("🔗  اختر عنصراً للربط")
        self.setMinimumSize(460, 380)
        self.setModal(True)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(10)
        lay.setContentsMargins(16, 16, 16, 16)

        lay.addWidget(QLabel("اختر العنصر المشترك الذي تريد ربطه بشركتك:"))

        self._list = QListWidget()
        self._list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {_C['border']};
                border-radius: 6px;
            }}
            QListWidget::item {{ padding: 8px 12px; }}
            QListWidget::item:selected {{
                background: {_C['accent_light']};
                color: {_C['accent_text']};
            }}
            QListWidget::item:hover {{ background: {_C['bg_hover']}; }}
        """)
        self._list.itemDoubleClicked.connect(self._accept)

        for item in self._items:
            type_ar = _TYPE_AR.get(item["shared_type"], item["shared_type"])
            text    = f"{item['name']}  [{type_ar}]  — من: {item['source_company_name'] or '?'}"
            wi = QListWidgetItem(text)
            wi.setData(Qt.UserRole, item["id"])
            self._list.addItem(wi)

        lay.addWidget(self._list)

        btn_row = QHBoxLayout()
        ok_btn = QPushButton("✅  ربط")
        ok_btn.setFixedHeight(34)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background: {_C['accent']}; color: white; font-weight: 600;
                border: none; border-radius: 5px; padding: 4px 18px;
            }}
            QPushButton:hover {{ background: {_C['accent_hover']}; }}
        """)
        ok_btn.clicked.connect(self._accept)

        cancel_btn = QPushButton("✖  إلغاء")
        cancel_btn.setFixedHeight(34)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {_C['bg_surface_2']};
                border: 1px solid {_C['border_med']};
                border-radius: 5px; padding: 4px 14px;
            }}
            QPushButton:hover {{ background: {_C['bg_hover']}; }}
        """)
        cancel_btn.clicked.connect(self.reject)

        btn_row.addStretch()
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        lay.addLayout(btn_row)

    def _accept(self):
        item = self._list.currentItem()
        if item:
            self.selected_id = item.data(Qt.UserRole)
            self.accept()