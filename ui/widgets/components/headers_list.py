"""
ui/widgets/components/headers_list.py
=======================================
SearchBar + StatusBar + ListHeader — هيدرات لوحات القوائم.

مستخرج من components/headers.py.
"""

from PyQt5.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QLineEdit, QSizePolicy,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

from ui.theme import _C
from ui.font  import fs, get_font_size
from .button  import make_btn
from ..core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin


# ══════════════════════════════════════════════════════════
# SearchBar
# ══════════════════════════════════════════════════════════

class SearchBar(QWidget, WidgetMixin):
    """حقل بحث موحد مع debounce delay."""

    search_changed = pyqtSignal(str)

    def __init__(self, placeholder: str = "",
                 delay_ms: int = 250,
                 height: int = 34,
                 parent=None):
        super().__init__(parent)
        self._placeholder = placeholder or tr("list_search_placeholder")
        self._height = height
        self._delay = delay_ms
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(delay_ms)
        self._timer.timeout.connect(self._emit)
        self._build(self._placeholder, height)
        self._init_widget_mixin(theme=True, font=True, lang=True)

    def _build(self, placeholder: str, height: int):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)

        self.inp = QLineEdit()
        self.inp.setPlaceholderText(placeholder)
        self.inp.setFixedHeight(height)
        self.inp.setClearButtonEnabled(True)
        self.inp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.inp.textChanged.connect(self._on_change)
        lay.addWidget(self.inp)
        self._refresh_style()

    def _refresh_style(self, *_):
        base = get_font_size()
        self.inp.setStyleSheet(f"""
            QLineEdit {{
                background:{_C['bg_input']};
                border:1.5px solid {_C['border_med']};
                border-radius:6px; padding:0 10px;
                font-size:{fs(base,0)}pt; color:{_C['text_primary']};
            }}
            QLineEdit:focus {{ border-color:{_C['accent']}; background:{_C['bg_input_focus']}; }}
        """)

    def _refresh_lang(self, *_):
        if not self.inp.text():
            self.inp.setPlaceholderText(tr("list_search_placeholder"))

    def _on_change(self):
        if self._delay > 0:
            self._timer.start()
        else:
            self._emit()

    def _emit(self):
        self.search_changed.emit(self.inp.text().strip().lower())

    def text(self) -> str:
        return self.inp.text().strip().lower()

    def clear(self):
        self.inp.clear()

    def set_placeholder(self, text: str):
        self.inp.setPlaceholderText(text)


# ══════════════════════════════════════════════════════════
# StatusBar
# ══════════════════════════════════════════════════════════

class StatusBar(QLabel, WidgetMixin):
    """شريط حالة بسيط يعرض عدد العناصر."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(24)
        self._shown = 0
        self._total = 0
        self._has_count = False
        self._custom_text = None
        self._init_widget_mixin(theme=True, font=True, lang=True)
        self._refresh_style()

    def _refresh_style(self, *_):
        base = get_font_size()
        self.setStyleSheet(f"""
            background:{_C['bg_surface_2']};
            color:{_C['text_muted']};
            padding:0 10px;
            font-size:{fs(base,-1)}pt;
            font-weight:600;
            border-top:1px solid {_C['border']};
        """)

    def _refresh_lang(self, *_):
        if self._custom_text is not None:
            return
        if self._has_count:
            self.set_count(self._shown, self._total)

    def set_count(self, shown: int, total: int):
        self._shown = shown
        self._total = total
        self._has_count = True
        self._custom_text = None
        if shown == total:
            self.setText(tr("showing_all", total=total))
        else:
            self.setText(tr("showing_of", shown=shown, total=total))

    def set_text(self, text: str):
        self._custom_text = text
        self._has_count = False
        self.setText(text)

    def clear_count(self):
        self.setText("")
        self._shown = 0
        self._total = 0
        self._has_count = False
        self._custom_text = None


# ══════════════════════════════════════════════════════════
# ListHeader
# ══════════════════════════════════════════════════════════

class ListHeader(QFrame, WidgetMixin):
    """هيدر لوحة قائمة: عنوان + بحث + زر إضافة + أزرار إضافية."""

    search_changed = pyqtSignal(str)
    add_clicked    = pyqtSignal()

    def __init__(self, title: str = "", add_text: str = "",
                 show_search: bool = True,
                 search_placeholder: str = "",
                 search_delay: int = 250, parent=None):
        super().__init__(parent)
        self._title       = title
        self._add_text    = add_text
        self._show_search = show_search
        self._btn_add     = None
        self._search_bar  = None
        self._btn_row     = None
        self._lbl_title   = None
        _placeholder = search_placeholder or tr("list_search_placeholder")
        self._build(_placeholder, search_delay)
        self._init_widget_mixin(theme=True, font=True, lang=True)

    def _build(self, placeholder: str, delay: int):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 8)
        root.setSpacing(6)

        if self._title or self._add_text:
            self._btn_row = QHBoxLayout()
            self._btn_row.setSpacing(8)

            if self._title:
                self._lbl_title = QLabel(self._title)
                self._btn_row.addWidget(self._lbl_title)

            self._btn_row.addStretch()

            if self._add_text:
                self._btn_add = make_btn(self._add_text, "primary")
                self._btn_add.clicked.connect(self.add_clicked.emit)
                self._btn_row.addWidget(self._btn_add)

            root.addLayout(self._btn_row)

        if self._show_search:
            self._search_bar = SearchBar(placeholder=placeholder, delay_ms=delay)
            self._search_bar.search_changed.connect(self.search_changed.emit)
            root.addWidget(self._search_bar)

        self._refresh_style()

    def _refresh_style(self, *_):
        self.setStyleSheet(f"""
            QFrame {{
                background:{_C['bg_input']};
                border-bottom:1px solid {_C['border']};
            }}
        """)
        if self._lbl_title:
            base = get_font_size()
            self._lbl_title.setStyleSheet(
                f"font-weight:700; font-size:{fs(base,0)}pt;"
                f"color:{_C['text_primary']}; background:transparent; border:none;"
            )

    def _refresh_lang(self, *_):
        if self._search_bar:
            self._search_bar.set_placeholder(tr("list_search_placeholder"))

    def add_action(self, text: str, callback=None,
                   style: str = "normal") -> QPushButton:
        btn = make_btn(text, style)
        if callback:
            btn.clicked.connect(callback)
        if self._btn_row:
            if self._btn_add:
                idx = self._btn_row.indexOf(self._btn_add)
                self._btn_row.insertWidget(idx, btn)
            else:
                self._btn_row.addWidget(btn)
        return btn

    def search_text(self) -> str:
        return self._search_bar.text() if self._search_bar else ""

    def clear_search(self):
        if self._search_bar:
            self._search_bar.clear()

    def set_add_enabled(self, enabled: bool):
        if self._btn_add:
            self._btn_add.setEnabled(enabled)

    @property
    def search_bar(self) -> "SearchBar | None":
        return self._search_bar

    @property
    def btn_add(self) -> "QPushButton | None":
        return self._btn_add


def make_list_header(title: str = "", add_text: str = "",
                     show_search: bool = True,
                     placeholder: str = "") -> ListHeader:
    return ListHeader(title=title, add_text=add_text,
                      show_search=show_search,
                      search_placeholder=placeholder or tr("list_search_placeholder"))