"""
ui/tabs/orders/order_detail/_status_dialog.py
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QLineEdit,
)
from PyQt5.QtCore import Qt

from ui.theme import _C
from ui.widgets.components.button import make_btn
from ui.widgets.theme.input_styles import input_style
from ui.widgets.core.i18n import tr
from ._status_config import get_status_labels, get_status_labels_short, get_status_colors


class _StatusDialog(QDialog):
    def __init__(self, current_status: str, next_statuses: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("status_change_title"))
        self.setMinimumWidth(400)
        self.setModal(True)
        self._result = (next_statuses[0] if next_statuses else current_status, "")
        self._build(current_status, next_statuses)

    def _build(self, current, nexts):
        self.setStyleSheet(input_style())

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(12)

        STATUS_LABELS_SHORT = get_status_labels_short()
        STATUS_COLORS       = get_status_colors()

        lbl_hdr = QLabel(tr("status_change_title"))
        lbl_hdr.setStyleSheet(f"""
            font-size: 14px; font-weight: bold; color: {_C['accent_text']};
            background: {_C['accent_light']};
            border-radius: 8px; padding: 8px 14px; border: none;
        """)
        lay.addWidget(lbl_hdr)

        cur_info = STATUS_COLORS.get(current, (_C['text_sec'], _C['bg_surface_2'], _C['border']))
        lbl_cur  = QLabel(f"{tr('status_current_lbl')}  {STATUS_LABELS_SHORT.get(current, current)}")
        lbl_cur.setStyleSheet(
            f"color:{cur_info[0]}; font-weight:600; font-size:12px;"
            f"background:{cur_info[1]}; border:1px solid {cur_info[2]};"
            "border-radius:6px; padding:6px 10px;"
        )
        lay.addWidget(lbl_cur)

        lay.addWidget(QLabel(tr("status_new_lbl")))
        self._cmb = QComboBox()
        self._cmb.setMinimumHeight(36)
        for s in nexts:
            self._cmb.addItem(STATUS_LABELS_SHORT.get(s, s), s)
        lay.addWidget(self._cmb)

        lay.addWidget(QLabel(tr("status_note_lbl")))
        self._note = QLineEdit()
        self._note.setPlaceholderText(tr("status_note_placeholder"))
        lay.addWidget(self._note)

        btns = QHBoxLayout()
        btn_cancel = make_btn(tr("cancel"), "ghost")
        btn_cancel.clicked.connect(self.reject)

        btn_ok = make_btn(tr("status_change_btn"), "primary")
        btn_ok.setMinimumHeight(38)
        btn_ok.clicked.connect(self._save)

        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok, stretch=1)
        lay.addLayout(btns)

    def _save(self):
        self._result = (self._cmb.currentData(), self._note.text().strip())
        self.accept()

    def get_result(self):
        return self._result
