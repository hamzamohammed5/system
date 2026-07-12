"""
ui/tabs/orders/orders/_filter_toolbar.py
"""
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFrame,
    QPushButton, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui  import QFontMetrics, QFont
from ui.widgets.panels.themed_inputs import ThemedLineEdit, ThemedComboBox

from ui.theme import _C
from ui.widgets.components.button import make_btn
from ui.widgets.core.i18n import tr
from ui.font import FS_BASE
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import (
    FILTER_DEBOUNCE_MS,
    FILTER_TB_COMBO_RADIUS, FILTER_TB_COMBO_PAD_H, FILTER_TB_COMBO_MIN_H,
    FILTER_TB_COMBO_DROPDOWN_W, FILTER_TB_NEW_BTN_RADIUS, FILTER_TB_NEW_BTN_H,
    FILTER_TB_NEW_BTN_MIN_W, FILTER_TB_NEW_BTN_TEXT_PAD,
    FILTER_TB_ROOT_MARGIN_H, FILTER_TB_ROOT_MARGIN_T, FILTER_TB_ROOT_MARGIN_B,
    FILTER_TB_ROOT_SPACING, FILTER_TB_ROW2_SPACING,
    FILTER_TB_SEARCH_H, FILTER_TB_SEARCH_RADIUS, FILTER_TB_SEARCH_PAD_H,
    FILTER_TB_SEARCH_BORDER_W,
    SPACING_XL,
)
from ..order_detail._status_config import get_status_labels, get_priority_labels


def _combo_ss() -> str:
    return f"""
        QComboBox {{
            background: {_C['bg_surface_2']};
            border: 1px solid {_C['border']};
            border-radius: {FILTER_TB_COMBO_RADIUS}px;
            padding: 0 {FILTER_TB_COMBO_PAD_H}px;
            min-height: {FILTER_TB_COMBO_MIN_H}px;
            font-size: {FS_BASE - 1}px;
            color: {_C['text_primary']};
        }}
        QComboBox:focus {{ border-color: {_C['accent']}; }}
        QComboBox::drop-down {{ border: none; width: {FILTER_TB_COMBO_DROPDOWN_W}px; }}
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
            border: none; border-radius: {FILTER_TB_NEW_BTN_RADIUS}px;
            padding: 0 {SPACING_XL}px; font-weight: 700; font-size: {FS_BASE}px;
        }}
        QPushButton:hover {{ background: {_C['accent_hover']}; }}
    """


def _fixed_btn(text: str, h: int = FILTER_TB_NEW_BTN_H) -> QPushButton:
    btn = QPushButton(text)
    btn.setStyleSheet(_new_btn_ss())
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFixedHeight(h)
    fm = QFontMetrics(QFont("", FS_BASE))
    w  = fm.horizontalAdvance(text) + FILTER_TB_NEW_BTN_TEXT_PAD
    btn.setFixedWidth(max(w, FILTER_TB_NEW_BTN_MIN_W))
    btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    return btn


class _FilterToolbar(QFrame, WidgetMixin):
    changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(FILTER_DEBOUNCE_MS)
        self._timer.timeout.connect(self.changed.emit)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._init_widget_mixin(data=False)
        self._build()
        self._refresh_style()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(
            FILTER_TB_ROOT_MARGIN_H, FILTER_TB_ROOT_MARGIN_T,
            FILTER_TB_ROOT_MARGIN_H, FILTER_TB_ROOT_MARGIN_B,
        )
        root.setSpacing(FILTER_TB_ROOT_SPACING)

        row0 = QHBoxLayout()
        row0.setContentsMargins(0, 0, 0, 0)
        row0.setSpacing(0)

        self.btn_new = _fixed_btn(tr("order_new_btn"), h=FILTER_TB_NEW_BTN_H)
        row0.addWidget(self.btn_new)
        row0.addStretch(1)
        root.addLayout(row0)

        self.inp_search = ThemedLineEdit()
        self.inp_search.setPlaceholderText(tr("order_search_placeholder"))
        self.inp_search.setFixedHeight(FILTER_TB_SEARCH_H)
        self.inp_search.setClearButtonEnabled(True)
        self.inp_search.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.inp_search.textChanged.connect(lambda: self._timer.start())
        root.addWidget(self.inp_search)

        row2 = QHBoxLayout()
        row2.setSpacing(FILTER_TB_ROW2_SPACING)

        STATUS_LABELS   = get_status_labels()
        PRIORITY_LABELS = get_priority_labels()

        self.cmb_status = ThemedComboBox()
        self.cmb_status.setFixedHeight(FILTER_TB_COMBO_MIN_H)
        self.cmb_status.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cmb_status.setStyleSheet(_combo_ss())
        self.cmb_status.addItem(tr("order_all_statuses"), None)
        for k, (lbl, *_) in STATUS_LABELS.items():
            self.cmb_status.addItem(lbl, k)
        self.cmb_status.currentIndexChanged.connect(self.changed.emit)

        self.cmb_priority = ThemedComboBox()
        self.cmb_priority.setFixedHeight(FILTER_TB_COMBO_MIN_H)
        self.cmb_priority.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cmb_priority.setStyleSheet(_combo_ss())
        self.cmb_priority.addItem(tr("order_all_priorities"), None)
        for k, (lbl, _) in PRIORITY_LABELS.items():
            icon = lbl.split()[0] if lbl else ""
            self.cmb_priority.addItem(icon, k)
        self.cmb_priority.currentIndexChanged.connect(self.changed.emit)

        self.btn_reset = make_btn(tr("order_reset_filter"), "ghost")
        self.btn_reset.setToolTip(tr("order_reset_filter"))
        self.btn_reset.clicked.connect(self.reset)

        row2.addWidget(self.cmb_status,   stretch=3)
        row2.addWidget(self.cmb_priority, stretch=2)
        row2.addWidget(self.btn_reset)
        root.addLayout(row2)

    def _refresh_style(self, *_):
        self.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_input']};
                border: none;
                border-bottom: 1px solid {_C['border']};
            }}
        """)

        self.inp_search.setStyleSheet(f"""
            QLineEdit {{
                background: {_C['bg_input']};
                border: {FILTER_TB_SEARCH_BORDER_W}px solid {_C['border_med']};
                border-radius: {FILTER_TB_SEARCH_RADIUS}px;
                padding: 0 {FILTER_TB_SEARCH_PAD_H}px;
                font-size: {FS_BASE}px;
                color: {_C['text_primary']};
            }}
            QLineEdit:focus {{ border-color: {_C['accent']}; background: {_C['bg_surface']}; }}
        """)

        self.cmb_status.setStyleSheet(_combo_ss())
        self.cmb_priority.setStyleSheet(_combo_ss())

    def _refresh_lang(self, *_):
        self.btn_new.setText(tr("order_new_btn"))
        self.inp_search.setPlaceholderText(tr("order_search_placeholder"))

        prev_status = self.cmb_status.currentData()
        self.cmb_status.blockSignals(True)
        self.cmb_status.clear()
        self.cmb_status.addItem(tr("order_all_statuses"), None)
        for k, (lbl, *_) in get_status_labels().items():
            self.cmb_status.addItem(lbl, k)
        for i in range(self.cmb_status.count()):
            if self.cmb_status.itemData(i) == prev_status:
                self.cmb_status.setCurrentIndex(i)
                break
        self.cmb_status.blockSignals(False)

        prev_priority = self.cmb_priority.currentData()
        self.cmb_priority.blockSignals(True)
        self.cmb_priority.clear()
        self.cmb_priority.addItem(tr("order_all_priorities"), None)
        for k, (lbl, _) in get_priority_labels().items():
            icon = lbl.split()[0] if lbl else ""
            self.cmb_priority.addItem(icon, k)
        for i in range(self.cmb_priority.count()):
            if self.cmb_priority.itemData(i) == prev_priority:
                self.cmb_priority.setCurrentIndex(i)
                break
        self.cmb_priority.blockSignals(False)

        self.btn_reset.setText(tr("order_reset_filter"))
        self.btn_reset.setToolTip(tr("order_reset_filter"))

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
