"""
ui/widgets/panels/form_buttons.py
===================================
CrudButtonsBar — شريط أزرار CRUD موحد.

مستخرج من panels/form_parts.py.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore    import Qt, pyqtSignal

from ui.theme import _C
from ui.font  import get_font_size, fs
from ..components.button      import make_btn
from ..core.i18n              import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import SPACING_XS, SPACING_SM, SPACING_MD


class CrudButtonsBar(QWidget, WidgetMixin):
    """
    شريط أزرار موحد: إضافة / حفظ / إلغاء + label الوضع.

    يشترك في bus.language_changed لتحديث النصوص تلقائياً.
    """

    add_clicked    = pyqtSignal()
    save_clicked   = pyqtSignal()
    cancel_clicked = pyqtSignal()

    def __init__(self, add_text: str = "",
                 save_text: str = "",
                 cancel_text: str = "",
                 show_mode: bool = True, parent=None):
        super().__init__(parent)
        self._add_text    = add_text    or tr("btn_add")
        self._save_text   = save_text   or tr("btn_save")
        self._cancel_text = cancel_text or tr("btn_cancel")
        self._show_mode   = show_mode
        self._build(show_mode)
        self._init_widget_mixin(theme=False, font=False, lang=True, data=False)

    def _build(self, show_mode):
        self.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, SPACING_XS, 0, SPACING_XS)
        lay.setSpacing(SPACING_SM)

        if show_mode:
            self.lbl_mode = QLabel(tr('mode_label_wrap').format(content=tr('add')))
            base = get_font_size()
            self.lbl_mode.setStyleSheet(
                f"font-weight:bold; font-size:{fs(base,0)}pt;"
                f"color:{_C['accent']}; background:transparent;"
            )
            lay.addWidget(self.lbl_mode)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(SPACING_MD)

        self.btn_add    = make_btn(self._add_text,    "primary")
        self.btn_save   = make_btn(self._save_text,   "success")
        self.btn_cancel = make_btn(self._cancel_text, "ghost")

        self.btn_add.clicked.connect(self.add_clicked.emit)
        self.btn_save.clicked.connect(self.save_clicked.emit)
        self.btn_cancel.clicked.connect(self.cancel_clicked.emit)

        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn_row.addWidget(btn)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        if not show_mode:
            self.lbl_mode = QLabel()

    def _refresh_lang(self, *_):
        self.btn_add.setText(tr("btn_add"))
        self.btn_save.setText(tr("btn_save"))
        self.btn_cancel.setText(tr("btn_cancel"))

    def set_mode_text(self, text: str):
        self.lbl_mode.setText(text)