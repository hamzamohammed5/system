"""
ui/widgets/panels/filter.py
=========================
FilterToolbar — شريط فلاتر موحد (بحث + تصنيف + تاريخ).

التغييرات:
  - [إصلاح imports] استبدال ui.theme/ui.font بـ ui.app_settings
  - [إصلاح imports] استبدال ..utils.ui_utils بـ ..utils.signals (الصح)
  - [إصلاح imports] استبدال ..styles بـ ..theme.styles
  - [إصلاح 14] FilterToolbar تستمع لـ bus.company_data_changed.
  - [تحسين 16] reload() تُحدّث conn ثم تُعيد تحميل التصنيفات.

  [FIX] استبدال from ...font و from ...theme (ثلاث نقاط خاطئة تُسبب ImportError)
        بـ absolute imports مباشرة.
"""
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QComboBox,
)
from PyQt5.QtCore import QDate, pyqtSignal

# [FIX] absolute imports — ثلاث نقاط كانت خاطئة تُسبب ImportError
from ui.font  import fs, get_font_size
from ui.theme import _C

from ..utils.signals          import blocked_signals
from ui.widgets.core.widget_mixin import WidgetMixin


def _combo_style() -> str:
    base = get_font_size()
    return f"""
        QComboBox {{
            background:{_C['bg_input']}; border:1px solid {_C['border_med']};
            border-radius:4px; padding:2px 8px; font-size:{fs(base,-1)}pt;
            color:{_C['text_primary']};
        }}
        QComboBox:focus {{ border-color:{_C['accent']}; }}
        QComboBox::drop-down {{ border:none; }}
    """


def _reset_btn_style() -> str:
    return f"""
        QPushButton {{
            background:{_C['bg_hover']}; border:1px solid {_C['border_med']};
            border-radius:4px; font-size:13px; color:{_C['accent']};
        }}
        QPushButton:hover {{ background:{_C['border_med']}; }}
    """


class FilterToolbar(QWidget, WidgetMixin):
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
        self._init_widget_mixin(theme=False, font=False, data=True)

    # ── بناء ──────────────────────────────────────────────

    def _build(self, placeholder: str):
        self.setStyleSheet(f"""
            QWidget {{
                background:{_C['bg_surface_2']};
                border:1px solid {_C['border']};
                border-radius:6px;
            }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(8)

        from ..components.headers_list import SearchBar
        self._search = SearchBar(placeholder=placeholder, delay_ms=250, height=28)
        self._search.search_changed.connect(lambda _: self.filter_changed.emit())
        self.inp_search = self._search.inp
        lay.addWidget(self._search, stretch=2)

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
            self.cmb_cat.setStyleSheet(_combo_style())
            self._reload_categories()
            self.cmb_cat.currentIndexChanged.connect(lambda _: self.filter_changed.emit())
            lay.addWidget(self.cmb_cat, stretch=1)

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

        btn_reset = QPushButton("↺")
        btn_reset.setToolTip("مسح الكل")
        btn_reset.setMinimumHeight(28)
        btn_reset.setFixedWidth(32)
        btn_reset.setStyleSheet(_reset_btn_style())
        btn_reset.clicked.connect(self.reset)
        lay.addWidget(btn_reset)

        base = get_font_size()
        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet(
            f"color:{_C['accent']}; font-size:{fs(base,-2)}pt; font-weight:bold;"
            "background:transparent; border:none; min-width:50px;"
        )
        lay.addWidget(self.lbl_count)

    def _sep(self) -> QLabel:
        sep = QLabel("│")
        sep.setStyleSheet(
            f"color:{_C['border_med']}; background:transparent;"
            "border:none; font-size:16px;"
        )
        return sep

    def _refresh_data(self, company_id=None):
        if self.cmb_cat is None:
            return
        try:
            from db.companies.company_state import company_state
            if company_state.is_ready:
                new_conn = company_state.get_erp_conn()
                if new_conn is not None:
                    self._conn = new_conn
        except Exception:
            pass
        self._reload_categories()

    # ── تصنيفات ───────────────────────────────────────────

    def _reload_categories(self):
        if self.cmb_cat is None or self._conn is None:
            return
        prev = self.cmb_cat.currentData() if self.cmb_cat.count() else None

        with blocked_signals(self.cmb_cat):
            self.cmb_cat.clear()
            try:
                from ..combo.category import populate_category_combo
                populate_category_combo(self.cmb_cat, self._conn, self._scope,
                                        all_label="— كل التصنيفات —")
            except Exception:
                self.cmb_cat.addItem("— كل التصنيفات —", None)

            for i in range(self.cmb_cat.count()):
                if self.cmb_cat.itemData(i) == prev:
                    self.cmb_cat.setCurrentIndex(i)
                    break

    def reload(self, conn=None):
        """[تحسين 16] يُحدّث conn ثم يُعيد تحميل التصنيفات."""
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
            with blocked_signals(self.cmb_cat):
                self.cmb_cat.setCurrentIndex(0)
        if self._date_filter is not None:
            self._date_filter.reset()
        else:
            self.filter_changed.emit()