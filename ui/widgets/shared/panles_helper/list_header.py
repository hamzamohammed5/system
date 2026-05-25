"""
ui/widgets/shared/panles_helper/list_header.py

التغييرات:
  - SearchBar.inp stylesheet يستخدم _input_style() من input_widgets
    بدل تعريف نفس الـ QLineEdit style من جديد
  - StatusBar stylesheet يستخدم _C بشكل مباشر (كان صح، مُنظَّف فقط)
  - مفيش تغيير في الـ API
"""
from PyQt5.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

from ui.app_settings import _C, fs
from .colors_and_base import _base
from .make_btn import _make_btn

# stylesheet مشترك مع SearchLineEdit في input_widgets
def _search_input_style(height: int) -> str:
    base = _base()
    return f"""
        QLineEdit {{
            background:{_C['bg_input']};
            border:1.5px solid {_C['border_med']};
            border-radius:6px; padding:0 10px;
            font-size:{fs(base,0)}pt; color:{_C['text_primary']};
        }}
        QLineEdit:focus {{
            border-color:{_C['accent']}; background:white;
        }}
    """


# ══════════════════════════════════════════════════════════
# SearchBar
# ══════════════════════════════════════════════════════════

class SearchBar(QWidget):
    """شريط بحث مع delay موحد."""

    search_changed = pyqtSignal(str)

    def __init__(self, placeholder: str = "🔍  بحث...",
                 delay_ms: int = 250,
                 height: int = 34,
                 parent=None):
        super().__init__(parent)
        self._delay_ms = delay_ms
        self._timer    = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(delay_ms)
        self._timer.timeout.connect(self._emit_change)
        self._build(placeholder, height)

    def _build(self, placeholder: str, height: int):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.inp = QLineEdit()
        self.inp.setPlaceholderText(placeholder)
        self.inp.setFixedHeight(height)
        self.inp.setClearButtonEnabled(True)
        self.inp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.inp.setStyleSheet(_search_input_style(height))
        self.inp.textChanged.connect(self._on_text_changed)
        lay.addWidget(self.inp)

    def _on_text_changed(self):
        if self._delay_ms > 0:
            self._timer.start()
        else:
            self._emit_change()

    def _emit_change(self):
        self.search_changed.emit(self.inp.text().strip().lower())

    def text(self) -> str:
        return self.inp.text().strip().lower()

    def clear(self):
        self.inp.clear()

    def set_placeholder(self, text: str):
        self.inp.setPlaceholderText(text)


# ══════════════════════════════════════════════════════════
# ListHeader
# ══════════════════════════════════════════════════════════

class ListHeader(QFrame):
    """هيدر موحد للوحات القوائم."""

    search_changed = pyqtSignal(str)
    add_clicked    = pyqtSignal()

    def __init__(self,
                 title: str = "",
                 add_text: str = "",
                 show_search: bool = True,
                 search_placeholder: str = "🔍  بحث...",
                 search_delay: int = 250,
                 parent=None):
        super().__init__(parent)
        self._title       = title
        self._add_text    = add_text
        self._show_search = show_search
        self._action_btns: list[QPushButton] = []
        self._build(search_placeholder, search_delay)

    def _build(self, placeholder: str, delay: int):
        self.setStyleSheet(f"""
            QFrame {{
                background:{_C['bg_input']};
                border-bottom:1px solid {_C['border']};
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 8)
        root.setSpacing(6)

        if self._title or self._add_text:
            title_row = QHBoxLayout()
            title_row.setSpacing(8)

            if self._title:
                lbl = QLabel(self._title)
                base = _base()
                lbl.setStyleSheet(
                    f"font-weight:700; font-size:{fs(base,0)}pt;"
                    f"color:{_C['text_primary']}; background:transparent; border:none;"
                )
                title_row.addWidget(lbl)

            title_row.addStretch()

            if self._add_text:
                self._btn_add = _make_btn(self._add_text, "primary")
                self._btn_add.clicked.connect(self.add_clicked.emit)
                title_row.addWidget(self._btn_add)
            else:
                self._btn_add = None

            self._btn_row = title_row
            root.addLayout(title_row)

        if self._show_search:
            self._search_bar = SearchBar(
                placeholder=placeholder, delay_ms=delay
            )
            self._search_bar.search_changed.connect(self.search_changed.emit)
            root.addWidget(self._search_bar)
        else:
            self._search_bar = None

    def add_action(self, text: str, callback=None,
                   style: str = "normal") -> QPushButton:
        btn = _make_btn(text, style)
        if callback:
            btn.clicked.connect(callback)
        if hasattr(self, "_btn_row"):
            if self._btn_add:
                idx = self._btn_row.indexOf(self._btn_add)
                self._btn_row.insertWidget(idx, btn)
            else:
                self._btn_row.addWidget(btn)
        self._action_btns.append(btn)
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
    def search_bar(self) -> SearchBar | None:
        return self._search_bar

    @property
    def btn_add(self) -> QPushButton | None:
        return self._btn_add


# ══════════════════════════════════════════════════════════
# StatusBar
# ══════════════════════════════════════════════════════════

class StatusBar(QLabel):
    """شريط حالة بسيط يعرض عدد العناصر."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(24)
        self.setStyleSheet(f"""
            background:{_C['bg_surface_2']};
            color:{_C['text_muted']};
            padding:0 10px;
            font-size:{fs(_base(),-1)}pt;
            font-weight:600;
            border-top:1px solid {_C['border']};
        """)

    def set_count(self, shown: int, total: int):
        self.setText(str(total) if shown == total else f"{shown} / {total}")

    def set_text(self, text: str):
        self.setText(text)

    def clear_count(self):
        self.setText("")


# ══════════════════════════════════════════════════════════
# دالة سريعة
# ══════════════════════════════════════════════════════════

def make_list_header(title: str = "",
                     add_text: str = "",
                     show_search: bool = True,
                     placeholder: str = "🔍  بحث...") -> ListHeader:
    return ListHeader(
        title=title,
        add_text=add_text,
        show_search=show_search,
        search_placeholder=placeholder,
    )