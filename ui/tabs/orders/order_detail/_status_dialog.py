"""
ui/tabs/orders/order_detail/_status_dialog.py
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QLineEdit,
)
from PyQt5.QtCore import Qt

from ui.theme import _C
from ui.font import FS_MD, FS_BASE
from ui.widgets.components.button import make_btn
from ui.widgets.theme.input_styles import input_style
from ui.widgets.core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import (
    STATUS_DLG_MIN_W, STATUS_DLG_MARGIN, STATUS_DLG_SPACING,
    STATUS_DLG_HDR_RADIUS, STATUS_DLG_HDR_PAD_V, STATUS_DLG_HDR_PAD_H,
    STATUS_DLG_CUR_RADIUS, STATUS_DLG_CUR_BORDER_W, STATUS_DLG_CUR_PAD_V, STATUS_DLG_CUR_PAD_H,
    STATUS_DLG_CMB_MIN_H, STATUS_DLG_BTN_OK_MIN_H,
)
from ._status_config import get_status_labels, get_status_labels_short, get_status_colors


class _StatusDialog(QDialog, WidgetMixin):
    def __init__(self, current_status: str, next_statuses: list, parent=None):
        super().__init__(parent)
        self._current_status = current_status
        self._next_statuses  = next_statuses
        self.setMinimumWidth(STATUS_DLG_MIN_W)
        self.setModal(True)
        self._result = (next_statuses[0] if next_statuses else current_status, "")
        self._init_widget_mixin(data=False)
        self._build(current_status, next_statuses)
        self._refresh_style()
        self._refresh_lang()

    def _build(self, current, nexts):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(*STATUS_DLG_MARGIN)
        lay.setSpacing(STATUS_DLG_SPACING)

        self._lbl_hdr = QLabel()
        lay.addWidget(self._lbl_hdr)

        self._lbl_cur = QLabel()
        lay.addWidget(self._lbl_cur)

        self._lbl_new_hint = QLabel()
        lay.addWidget(self._lbl_new_hint)

        self._cmb = QComboBox()
        self._cmb.setMinimumHeight(STATUS_DLG_CMB_MIN_H)
        for s in nexts:
            self._cmb.addItem(s, s)
        lay.addWidget(self._cmb)

        self._lbl_note_hint = QLabel()
        lay.addWidget(self._lbl_note_hint)

        self._note = QLineEdit()
        lay.addWidget(self._note)

        btns = QHBoxLayout()
        self._btn_cancel = make_btn("", "ghost")
        self._btn_cancel.clicked.connect(self.reject)

        self._btn_ok = make_btn("", "primary")
        self._btn_ok.setMinimumHeight(STATUS_DLG_BTN_OK_MIN_H)
        self._btn_ok.clicked.connect(self._save)

        btns.addWidget(self._btn_cancel)
        btns.addWidget(self._btn_ok, stretch=1)
        lay.addLayout(btns)

    def _refresh_style(self, *_):
        self.setStyleSheet(input_style())

        STATUS_COLORS = get_status_colors()
        cur_info = STATUS_COLORS.get(
            self._current_status, (_C['text_sec'], _C['bg_surface_2'], _C['border'])
        )

        self._lbl_hdr.setStyleSheet(f"""
            font-size: {FS_MD}px; font-weight: bold; color: {_C['accent_text']};
            background: {_C['accent_light']};
            border-radius: {STATUS_DLG_HDR_RADIUS}px; padding: {STATUS_DLG_HDR_PAD_V}px {STATUS_DLG_HDR_PAD_H}px; border: none;
        """)

        self._lbl_cur.setStyleSheet(
            f"color:{cur_info[0]}; font-weight:600; font-size:{FS_BASE}px;"
            f"background:{cur_info[1]}; border:{STATUS_DLG_CUR_BORDER_W}px solid {cur_info[2]};"
            f"border-radius:{STATUS_DLG_CUR_RADIUS}px; padding:{STATUS_DLG_CUR_PAD_V}px {STATUS_DLG_CUR_PAD_H}px;"
        )

    def _refresh_lang(self, *_):
        self.setWindowTitle(tr("status_change_title"))

        STATUS_LABELS_SHORT = get_status_labels_short()

        self._lbl_hdr.setText(tr("status_change_title"))
        self._lbl_cur.setText(
            f"{tr('status_current_lbl')}  {STATUS_LABELS_SHORT.get(self._current_status, self._current_status)}"
        )
        self._lbl_new_hint.setText(tr("status_new_lbl"))

        prev = self._cmb.currentData()
        self._cmb.clear()
        for s in self._next_statuses:
            self._cmb.addItem(STATUS_LABELS_SHORT.get(s, s), s)
        for i in range(self._cmb.count()):
            if self._cmb.itemData(i) == prev:
                self._cmb.setCurrentIndex(i)
                break

        self._lbl_note_hint.setText(tr("status_note_lbl"))
        self._note.setPlaceholderText(tr("status_note_placeholder"))

        self._btn_cancel.setText(tr("cancel"))
        self._btn_ok.setText(tr("status_change_btn"))

    def _save(self):
        self._result = (self._cmb.currentData(), self._note.text().strip())
        self.accept()

    def get_result(self):
        return self._result
