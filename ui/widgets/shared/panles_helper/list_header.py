"""
ui/widgets/shared/panles_helper/list_header.py
===============================================
ListHeader — هيدر موحد للوحات القوائم (List Panels).

يحل محل الـ toolbar المكررة في كل لوحة قائمة.

المتوفر:
  ListHeader       — هيدر كامل مع بحث وعنوان وأزرار
  SearchBar        — شريط بحث بسيط
  make_list_header — دالة سريعة لبناء هيدر جاهز
"""

from PyQt5.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

from ui.app_settings import _C, fs
from .colors_and_base import _base
from .make_btn import _make_btn


# ══════════════════════════════════════════════════════════
# SearchBar — شريط بحث مستقل
# ══════════════════════════════════════════════════════════

class SearchBar(QWidget):
    """
    شريط بحث مع delay موحد.

    Signals:
        search_changed(str) — يُطلق بعد توقف الكتابة بـ delay_ms
    """

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
        base = _base()
        lay  = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.inp = QLineEdit()
        self.inp.setPlaceholderText(placeholder)
        self.inp.setFixedHeight(height)
        self.inp.setClearButtonEnabled(True)
        self.inp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.inp.setStyleSheet(f"""
            QLineEdit {{
                background: {_C['bg_input']};
                border: 1.5px solid {_C['border_med']};
                border-radius: 6px;
                padding: 0 10px;
                font-size: {fs(base, 0)}pt;
                color: {_C['text_primary']};
            }}
            QLineEdit:focus {{
                border-color: {_C['accent']};
                background: white;
            }}
        """)
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
# ListHeader — هيدر كامل للوحة القائمة
# ══════════════════════════════════════════════════════════

class ListHeader(QFrame):
    """
    هيدر موحد للوحات القوائم.

    يشمل:
      - عنوان القسم
      - شريط بحث
      - أزرار إضافة/إجراءات

    Signals:
        search_changed(str)  — تغير نص البحث
        add_clicked          — ضغط زر الإضافة

    الاستخدام:
        hdr = ListHeader(title="المنتجات", add_text="➕ إضافة")
        hdr.search_changed.connect(self._filter)
        hdr.add_clicked.connect(self._open_add_form)
        layout.addWidget(hdr)

        # إضافة زر مخصص:
        btn = hdr.add_action("📤 تصدير", callback=self._export)
    """

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
        self._title      = title
        self._add_text   = add_text
        self._show_search = show_search
        self._action_btns: list[QPushButton] = []
        self._build(search_placeholder, search_delay)

    def _build(self, placeholder: str, delay: int):
        self.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_input']};
                border-bottom: 1px solid {_C['border']};
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 8)
        root.setSpacing(6)

        # ── صف العنوان والأزرار ──
        if self._title or self._add_text:
            title_row = QHBoxLayout()
            title_row.setSpacing(8)

            if self._title:
                lbl = QLabel(self._title)
                base = _base()
                lbl.setStyleSheet(
                    f"font-weight: 700; font-size: {fs(base, 0)}pt;"
                    f"color: {_C['text_primary']}; background: transparent; border: none;"
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

        # ── شريط البحث ──
        if self._show_search:
            self._search_bar = SearchBar(
                placeholder=placeholder, delay_ms=delay
            )
            self._search_bar.search_changed.connect(self.search_changed.emit)
            root.addWidget(self._search_bar)
        else:
            self._search_bar = None

    # ── API خارجي ──────────────────────────────────────

    def add_action(self, text: str, callback=None,
                   style: str = "normal") -> QPushButton:
        """يضيف زر إجراء في صف العنوان."""
        btn = _make_btn(text, style)
        if callback:
            btn.clicked.connect(callback)
        if hasattr(self, '_btn_row'):
            # أضف قبل زر الإضافة لو موجود
            if self._btn_add:
                idx = self._btn_row.indexOf(self._btn_add)
                self._btn_row.insertWidget(idx, btn)
            else:
                self._btn_row.addWidget(btn)
        self._action_btns.append(btn)
        return btn

    def search_text(self) -> str:
        if self._search_bar:
            return self._search_bar.text()
        return ""

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
# StatusBar — شريط الحالة السفلي
# ══════════════════════════════════════════════════════════

class StatusBar(QLabel):
    """
    شريط حالة بسيط يعرض عدد العناصر.

    الاستخدام:
        bar = StatusBar()
        bar.set_count(shown=15, total=50)  # → "15 / 50"
        bar.set_count(shown=50, total=50)  # → "50"
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(24)
        self.setStyleSheet(f"""
            background: {_C['bg_surface_2']};
            color: {_C['text_muted']};
            padding: 0 10px;
            font-size: {fs(_base(), -1)}pt;
            font-weight: 600;
            border-top: 1px solid {_C['border']};
        """)

    def set_count(self, shown: int, total: int):
        """يحدّث العداد."""
        if shown == total:
            self.setText(str(total))
        else:
            self.setText(f"{shown} / {total}")

    def set_text(self, text: str):
        self.setText(text)

    def clear_count(self):
        self.setText("")


# ══════════════════════════════════════════════════════════
# دوال مساعدة
# ══════════════════════════════════════════════════════════

def make_list_header(title: str = "",
                     add_text: str = "",
                     show_search: bool = True,
                     placeholder: str = "🔍  بحث...") -> ListHeader:
    """
    دالة سريعة لبناء ListHeader جاهز.

    الاستخدام:
        hdr = make_list_header("المنتجات", "➕ إضافة")
        layout.addWidget(hdr)
    """
    return ListHeader(
        title=title,
        add_text=add_text,
        show_search=show_search,
        search_placeholder=placeholder,
    )