"""
widgets/panels/filter.py
=========================
FilterToolbar — شريط فلاتر موحد (بحث + تصنيف + تاريخ).

التغييرات عن النسخة القديمة (panles_helper/filter_toolbar.py):
  - SearchBar مستوردة من panels/header بدل إعادة تعريف
  - _style_combo / _make_sep مدمجتان مباشرة
  - reset_button style يستخدم _C مباشرة
  - لا يوجد تكرار لـ stylesheet الـ QLineEdit
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QComboBox,
)
from PyQt5.QtCore import QDate, pyqtSignal

from ui.app_settings import _C

_COMBO_STYLE = """
    QComboBox {
        background:white; border:1px solid #c5cae9;
        border-radius:4px; padding:2px 8px; font-size:12px;
    }
    QComboBox:focus { border-color:#1565c0; }
    QComboBox::drop-down { border:none; }
"""

_RESET_BTN_STYLE = f"""
    QPushButton {{
        background:{_C.get('bg_hover','#e8eaf6')};
        border:1px solid {_C.get('border_med','#c5cae9')};
        border-radius:4px; font-size:13px;
        color:{_C.get('accent','#3949ab')};
    }}
    QPushButton:hover {{ background:{_C.get('border_med','#c5cae9')}; }}
"""


class FilterToolbar(QWidget):
    """شريط فلاتر: [بحث] | [تصنيف] | [نطاق التاريخ] [↺]"""

    filter_changed = pyqtSignal()

    def __init__(self, conn=None, scope: str = "all",
                 show_category: bool = True,
                 show_date: bool = False,
                 placeholder: str = "بحث...",
                 show_presets: bool = False,
                 parent=None):
        super().__init__(parent)
        self._conn         = conn
        self._scope        = scope
        self._show_cat     = show_category
        self._show_date    = show_date
        self._show_presets = show_presets
        self._build(placeholder)

    # ── بناء ──────────────────────────────────────────────

    def _build(self, placeholder: str):
        self.setStyleSheet(f"""
            QWidget {{
                background:{_C.get('bg_surface_2','#f0f4ff')};
                border:1px solid {_C.get('border','#d0d9f0')};
                border-radius:6px;
            }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(8)

        # بحث — SearchBar من panels/header
        from ..panels.header import SearchBar
        self._search = SearchBar(placeholder=placeholder, delay_ms=250, height=28)
        self._search.search_changed.connect(lambda _: self.filter_changed.emit())
        self.inp_search = self._search.inp
        lay.addWidget(self._search, stretch=2)

        # تصنيف
        self.cmb_cat = None
        if self._show_cat:
            lay.addWidget(self._sep())
            lbl = QLabel("🏷")
            lbl.setStyleSheet("background:transparent; border:none; font-size:13px;")
            lbl.setFixedWidth(20)
            lay.addWidget(lbl)
            self.cmb_cat = QComboBox()
            self.cmb_cat.setMinimumHeight(28)
            self.cmb_cat.setMinimumWidth(160)
            self.cmb_cat.setStyleSheet(_COMBO_STYLE)
            self._reload_categories()
            self.cmb_cat.currentIndexChanged.connect(lambda _: self.filter_changed.emit())
            lay.addWidget(self.cmb_cat, stretch=1)

        # نطاق التاريخ
        self._date_filter = None
        self.dt_from = self.dt_to = None
        if self._show_date:
            lay.addWidget(self._sep())
            from ..utils.date_range import DateRangeFilter
            self._date_filter = DateRangeFilter(
                default_from=QDate(2000, 1, 1),
                default_to=QDate.currentDate(),
                show_presets=self._show_presets,
            )
            self._date_filter.range_changed.connect(self.filter_changed.emit)
            self.dt_from = self._date_filter.dt_from
            self.dt_to   = self._date_filter.dt_to
            lay.addWidget(self._date_filter)

        # زر مسح
        btn_reset = QPushButton("↺")
        btn_reset.setToolTip("مسح الكل")
        btn_reset.setMinimumHeight(28)
        btn_reset.setFixedWidth(32)
        btn_reset.setStyleSheet(_RESET_BTN_STYLE)
        btn_reset.clicked.connect(self.reset)
        lay.addWidget(btn_reset)

        # عداد
        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet(
            f"color:{_C.get('accent','#1565c0')}; font-size:10px; font-weight:bold;"
            "background:transparent; border:none; min-width:50px;"
        )
        lay.addWidget(self.lbl_count)

    @staticmethod
    def _sep() -> QLabel:
        sep = QLabel("│")
        sep.setStyleSheet("color:#c5cae9; background:transparent; border:none; font-size:16px;")
        return sep

    # ── تصنيفات ───────────────────────────────────────────

    def _reload_categories(self):
        if self.cmb_cat is None or self._conn is None:
            return
        prev = self.cmb_cat.currentData() if self.cmb_cat.count() else None
        self.cmb_cat.blockSignals(True)
        self.cmb_cat.clear()
        try:
            from ui.widgets.shared.category_combo import _populate_category_combo
            _populate_category_combo(self.cmb_cat, self._conn, self._scope,
                                     all_label="— كل التصنيفات —")
        except Exception:
            self.cmb_cat.addItem("— كل التصنيفات —", None)
        for i in range(self.cmb_cat.count()):
            if self.cmb_cat.itemData(i) == prev:
                self.cmb_cat.setCurrentIndex(i)
                break
        self.cmb_cat.blockSignals(False)

    def reload(self, conn=None):
        if conn:
            self._conn = conn
        self._reload_categories()

    # ── API ───────────────────────────────────────────────

    @property
    def name_query(self) -> str:
        return self._search.text()

    @property
    def category_id(self):
        return self.cmb_cat.currentData() if self.cmb_cat else None

    def match(self, name: str = "", cat_id=None, date_str: str = "") -> bool:
        q = self.name_query
        if q and q not in (name or "").lower():
            return False
        fcat = self.category_id
        if fcat is not None and cat_id != fcat:
            return False
        if self._date_filter and date_str and not self._date_filter.in_range(date_str):
            return False
        return True

    def in_date_range(self, date_str: str) -> bool:
        return self._date_filter.in_range(date_str) if self._date_filter else True

    def set_count(self, shown: int, total: int):
        self.lbl_count.setText(
            f"({total})" if shown == total else f"({shown}/{total})"
        )

    def reset(self):
        self._search.clear()
        if self.cmb_cat is not None:
            self.cmb_cat.blockSignals(True)
            self.cmb_cat.setCurrentIndex(0)
            self.cmb_cat.blockSignals(False)
        if self._date_filter is not None:
            self._date_filter.reset()
        else:
            self.filter_changed.emit()