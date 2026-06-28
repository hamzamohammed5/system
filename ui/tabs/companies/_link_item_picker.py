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
from ui.widgets.core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import (
    LINK_PICKER_MIN_W, LINK_PICKER_MIN_H,
    LINK_PICKER_SPACING, LINK_PICKER_MARGIN,
    LINK_PICKER_LIST_RADIUS,
    LINK_PICKER_LIST_ITEM_PAD_V, LINK_PICKER_LIST_ITEM_PAD_H,
    LINK_PICKER_OK_BTN_H, LINK_PICKER_OK_BTN_RADIUS, LINK_PICKER_OK_BTN_PAD_H,
    LINK_PICKER_BTN_PAD_V,
    LINK_PICKER_CANCEL_BTN_H, LINK_PICKER_CANCEL_BTN_RADIUS, LINK_PICKER_CANCEL_BTN_PAD_H,
)

_TYPE_AR = {
    "raw":        tr("shared_type_raw"),
    "machine":    tr("shared_type_machine"),
    "labor_op":   tr("shared_type_labor_op"),
    "machine_op": tr("shared_type_machine_op"),
}


class LinkItemPicker(QDialog, WidgetMixin):
    def __init__(self, items: list, parent=None):
        super().__init__(parent)
        self.selected_id = None
        self._items      = items

        self.setWindowTitle(tr("link_item_title"))
        self.setMinimumSize(LINK_PICKER_MIN_W, LINK_PICKER_MIN_H)
        self.setModal(True)
        self._init_widget_mixin(data=False)
        self._build()
        self._refresh_style()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(LINK_PICKER_SPACING)
        lay.setContentsMargins(*LINK_PICKER_MARGIN)

        lay.addWidget(QLabel(tr("link_item_prompt")))

        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self._accept)

        for item in self._items:
            type_ar = _TYPE_AR.get(item["shared_type"], item["shared_type"])
            source  = item["source_company_name"] or tr("dash")
            text    = f"{item['name']}  [{type_ar}]  {tr('link_item_from').format(company=source)}"
            wi = QListWidgetItem(text)
            wi.setData(Qt.UserRole, item["id"])
            self._list.addItem(wi)

        lay.addWidget(self._list)

        btn_row = QHBoxLayout()
        self._ok_btn = QPushButton(tr("link_item_btn"))
        self._ok_btn.setFixedHeight(LINK_PICKER_OK_BTN_H)
        self._ok_btn.clicked.connect(self._accept)

        self._cancel_btn = QPushButton(tr("btn_cancel"))
        self._cancel_btn.setFixedHeight(LINK_PICKER_CANCEL_BTN_H)
        self._cancel_btn.clicked.connect(self.reject)

        btn_row.addStretch()
        btn_row.addWidget(self._ok_btn)
        btn_row.addWidget(self._cancel_btn)
        lay.addLayout(btn_row)

    def _refresh_style(self, *_):
        from ui.theme import _C
        self._list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {_C['border']};
                border-radius: {LINK_PICKER_LIST_RADIUS}px;
            }}
            QListWidget::item {{ padding: {LINK_PICKER_LIST_ITEM_PAD_V}px {LINK_PICKER_LIST_ITEM_PAD_H}px; }}
            QListWidget::item:selected {{
                background: {_C['accent_light']};
                color: {_C['accent_text']};
            }}
            QListWidget::item:hover {{ background: {_C['bg_hover']}; }}
        """)
        self._ok_btn.setStyleSheet(f"""
            QPushButton {{
                background: {_C['accent']}; color: {_C['bg_input']}; font-weight: 600;
                border: none; border-radius: {LINK_PICKER_OK_BTN_RADIUS}px;
                padding: {LINK_PICKER_BTN_PAD_V}px {LINK_PICKER_OK_BTN_PAD_H}px;
            }}
            QPushButton:hover {{ background: {_C['accent_hover']}; }}
        """)
        self._cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {_C['bg_surface_2']};
                border: 1px solid {_C['border_med']};
                border-radius: {LINK_PICKER_CANCEL_BTN_RADIUS}px;
                padding: {LINK_PICKER_BTN_PAD_V}px {LINK_PICKER_CANCEL_BTN_PAD_H}px;
            }}
            QPushButton:hover {{ background: {_C['bg_hover']}; }}
        """)

    def _accept(self):
        item = self._list.currentItem()
        if item:
            self.selected_id = item.data(Qt.UserRole)
            self.accept()