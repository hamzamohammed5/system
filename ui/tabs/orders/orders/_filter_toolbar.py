"""
ui/tabs/orders/orders/_filter_toolbar.py
"""
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFrame,
    QLineEdit, QPushButton, QComboBox, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui  import QFontMetrics, QFont

from ui.theme import _C
from ui.widgets.components.button import make_btn
from ui.widgets.core.i18n import tr
from ui.font import FS_BASE
from ..order_detail._status_config import get_status_labels, get_priority_labels


def _combo_ss() -> str:
    return f"""
        QComboBox {{
            background: {_C['bg_surface_2']};
            border: 1px solid {_C['border']};
            border-radius: 5px;
            padding: 0 8px;
            min-height: 28px;
            font-size: {FS_BASE - 1}px;
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


def _new_btn_ss() -> str:
    return f"""
        QPushButton {{
            background: {_C['accent']}; color: {_C['btn_primary_text']};
            border: none; border-radius: 8px;
            padding: 0 16px; font-weight: 700; font-size: {FS_BASE}px;
        }}
        QPushButton:hover {{ background: {_C['accent_hover']}; }}
    """


def _fixed_btn(text: str, h: int = 36) -> QPushButton:
    btn = QPushButton(text)
    btn.setStyleSheet(_new_btn_ss())
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFixedHeight(h)
    fm = QFontMetrics(QFont("", FS_BASE))
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

        row0 = QHBoxLayout()
        row0.setContentsMargins(0, 0, 0, 0)
        row0.setSpacing(0)

        self.btn_new = _fixed_btn(tr("order_new_btn"), h=36)
        row0.addWidget(self.btn_new)
        row0.addStretch(1)
        root.addLayout(row0)

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText(tr("order_search_placeholder"))
        self.inp_search.setFixedHeight(34)
        self.inp_search.setClearButtonEnabled(True)
        self.inp_search.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.inp_search.setStyleSheet(f"""
            QLineEdit {{
                background: {_C['bg_input']};
                border: 1.5px solid {_C['border_med']};
                border-radius: 6px;
                padding: 0 10px;
                font-size: {FS_BASE}px;
                color: {_C['text_primary']};
            }}
            QLineEdit:focus {{ border-color: {_C['accent']}; background: {_C['bg_surface']}; }}
        """)
        self.inp_search.textChanged.connect(lambda: self._timer.start())
        root.addWidget(self.inp_search)

        row2 = QHBoxLayout()
        row2.setSpacing(6)

        STATUS_LABELS   = get_status_labels()
        PRIORITY_LABELS = get_priority_labels()

        self.cmb_status = QComboBox()
        self.cmb_status.setFixedHeight(28)
        self.cmb_status.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cmb_status.setStyleSheet(_combo_ss())
        self.cmb_status.addItem(tr("order_all_statuses"), None)
        for k, (lbl, *_) in STATUS_LABELS.items():
            self.cmb_status.addItem(lbl, k)
        self.cmb_status.currentIndexChanged.connect(self.changed.emit)

        self.cmb_priority = QComboBox()
        self.cmb_priority.setFixedHeight(28)
        self.cmb_priority.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cmb_priority.setStyleSheet(_combo_ss())
        self.cmb_priority.addItem(tr("order_all_priorities"), None)
        for k, (lbl, _) in PRIORITY_LABELS.items():
            icon = lbl.split()[0] if lbl else ""
            self.cmb_priority.addItem(icon, k)
        self.cmb_priority.currentIndexChanged.connect(self.changed.emit)

        btn_reset = make_btn(tr("order_reset_filter"), "ghost")
        btn_reset.setToolTip(tr("order_reset_filter"))
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
