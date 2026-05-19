"""
ui/tabs/orders/order_detail/_status_dialog.py
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QLineEdit,
)
from PyQt5.QtCore import Qt
from ui.app_settings import _C
from ._status_config import STATUS_LABELS_SHORT, STATUS_COLORS


class _StatusDialog(QDialog):
    def __init__(self, current_status: str, next_statuses: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تغيير حالة الطلب")
        self.setMinimumWidth(400)
        self.setModal(True)
        self._result = (next_statuses[0] if next_statuses else current_status, "")
        self._build(current_status, next_statuses)

    def _build(self, current, nexts):
        self.setStyleSheet(f"""
            QDialog {{ background: {_C['bg_surface']}; }}
            QLineEdit {{
                background: {_C['bg_input']}; border: 1.5px solid {_C['border_med']};
                border-radius: 6px; padding: 6px 10px;
                font-size: 12px; min-height: 34px;
            }}
            QLineEdit:focus {{ border-color: {_C['accent']}; }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(12)

        lbl_hdr = QLabel("تغيير حالة الطلب")
        lbl_hdr.setStyleSheet(f"""
            font-size: 14px; font-weight: bold; color: {_C['accent_text']};
            background: {_C['accent_light']}; border-radius: 8px;
            padding: 8px 14px; border: none;
        """)
        lay.addWidget(lbl_hdr)

        cur_info = STATUS_COLORS.get(current, ("#555", "#f5f5f5", "#e0e0e0"))
        lbl_cur  = QLabel(f"الحالة الحالية:  {STATUS_LABELS_SHORT.get(current, current)}")
        lbl_cur.setStyleSheet(
            f"color:{cur_info[0]}; font-weight:600; font-size:12px;"
            f"background:{cur_info[1]}; border:1px solid {cur_info[2]};"
            "border-radius:6px; padding:6px 10px;"
        )
        lay.addWidget(lbl_cur)

        lay.addWidget(QLabel("الحالة الجديدة:"))
        self._cmb = QComboBox()
        self._cmb.setMinimumHeight(36)
        self._cmb.setStyleSheet(f"""
            QComboBox {{
                background: {_C['bg_input']}; color: {_C['text_primary']};
                border: 1.5px solid {_C['border_med']}; border-radius: 6px;
                padding: 4px 10px; font-size: 12px;
            }}
            QComboBox:focus {{ border-color: {_C['accent']}; }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
        """)
        for s in nexts:
            self._cmb.addItem(STATUS_LABELS_SHORT.get(s, s), s)
        lay.addWidget(self._cmb)

        lay.addWidget(QLabel("ملاحظات (اختياري):"))
        self._note = QLineEdit()
        self._note.setPlaceholderText("سبب التغيير...")
        lay.addWidget(self._note)

        btns     = QHBoxLayout()
        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setMinimumHeight(38)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: {_C['bg_surface_2']}; color: {_C['text_sec']};
                border: 1px solid {_C['border_med']}; border-radius: 6px;
                padding: 0 16px;
            }}
            QPushButton:hover {{ background: {_C['bg_hover']}; }}
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("✅  تغيير الحالة")
        btn_ok.setMinimumHeight(38)
        btn_ok.setStyleSheet(f"""
            QPushButton {{
                background: {_C['accent_light']}; color: {_C['accent_text']};
                border: 1.5px solid {_C['accent_mid']}; border-radius: 6px;
                padding: 0 20px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {_C['accent_mid']}; }}
        """)
        btn_ok.clicked.connect(self._save)

        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok, stretch=1)
        lay.addLayout(btns)

    def _save(self):
        self._result = (self._cmb.currentData(), self._note.text().strip())
        self.accept()

    def get_result(self):
        return self._result