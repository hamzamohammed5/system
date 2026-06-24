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
from ui.font  import fs, get_font_size, FS_SM
from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.constants import (
    FILTER_TOOLBAR_MARGIN_H, FILTER_TOOLBAR_MARGIN_V, FILTER_TOOLBAR_SPACING,
    FILTER_COMBO_MIN_H, FILTER_COMBO_MIN_W, FILTER_RESET_BTN_W, FILTER_SEARCH_H,
    SPACING_SM, FILTER_COUNT_LABEL_MIN_W, FILTER_DEBOUNCE_MS,
)

from ..utils.signals          import blocked_signals
from ui.widgets.core.widget_mixin import WidgetMixin


def _combo_style() -> str:
    from ui.constants import FILTER_COMBO_BORDER_RADIUS, FILTER_COMBO_PAD_H
    base = get_font_size()
    return f"""
        QComboBox {{
            background:{_C['bg_input']}; border:1px solid {_C['border_med']};
            border-radius:{FILTER_COMBO_BORDER_RADIUS}px; padding:2px {FILTER_COMBO_PAD_H}px; font-size:{fs(base,-1)}pt;
            color:{_C['text_primary']};
        }}
        QComboBox:focus {{ border-color:{_C['accent']}; }}
        QComboBox::drop-down {{ border:none; }}
    """


def _reset_btn_style() -> str:
    from ui.font import FS_MD
    from ui.constants import FILTER_COMBO_BORDER_RADIUS
    return f"""
        QPushButton {{
            background:{_C['bg_hover']}; border:1px solid {_C['border_med']};
            border-radius:{FILTER_COMBO_BORDER_RADIUS}px; font-size:{FS_MD}pt; color:{_C['accent']};
        }}
        QPushButton:hover {{ background:{_C['border_med']}; }}
    """


class FilterToolbar(QWidget, WidgetMixin):
    """شريط فلاتر: [بحث] | [تصنيف] | [نطاق التاريخ] [↺]"""

    filter_changed = pyqtSignal()

    def __init__(self, conn=None, scope: str = "all",
                 show_category: bool = True,
                 show_date: bool = False,
                 placeholder: str = None,
                 show_presets: bool = False,
                 parent=None):
        super().__init__(parent)
        self._conn         = conn
        self._scope        = scope
        self._show_cat     = show_category
        self._show_date    = show_date
        self._show_presets = show_presets
        self._build(placeholder or tr('search'))
        self._init_widget_mixin(theme=True, font=False, data=True)
        self._refresh_style()

    # ── بناء ──────────────────────────────────────────────

    def _build(self, placeholder: str):
        from ui.constants import FILTER_TOOLBAR_BORDER_RADIUS
        self.setStyleSheet(f"""
            QWidget {{
                background:{_C['bg_surface_2']};
                border:1px solid {_C['border']};
                border-radius:{FILTER_TOOLBAR_BORDER_RADIUS}px;
            }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(FILTER_TOOLBAR_MARGIN_H, FILTER_TOOLBAR_MARGIN_V,
                               FILTER_TOOLBAR_MARGIN_H, FILTER_TOOLBAR_MARGIN_V)
        lay.setSpacing(FILTER_TOOLBAR_SPACING)

        from ..components.headers_list import SearchBar
        self._search = SearchBar(placeholder=placeholder, delay_ms=FILTER_DEBOUNCE_MS, height=FILTER_SEARCH_H)
        self._search.search_changed.connect(lambda _: self.filter_changed.emit())
        self.inp_search = self._search.inp
        lay.addWidget(self._search, stretch=2)

        self.cmb_cat = None
        if self._show_cat:
            lay.addWidget(self._sep())
            lbl = QLabel(tr('filter_cat_icon'))
            lbl.setStyleSheet(f"background:transparent; border:none; font-size:{FS_SM}pt;")
            from ui.constants import FILTER_CAT_ICON_W
            lbl.setFixedWidth(FILTER_CAT_ICON_W)
            lay.addWidget(lbl)
            self.cmb_cat = QComboBox()
            self.cmb_cat.setMinimumHeight(FILTER_COMBO_MIN_H)
            self.cmb_cat.setMinimumWidth(FILTER_COMBO_MIN_W)
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

        btn_reset = QPushButton(tr('filter_reset_btn'))
        btn_reset.setToolTip(tr('filter_reset_tooltip'))
        btn_reset.setMinimumHeight(FILTER_COMBO_MIN_H)
        btn_reset.setFixedWidth(FILTER_RESET_BTN_W)
        btn_reset.setStyleSheet(_reset_btn_style())
        btn_reset.clicked.connect(self.reset)
        lay.addWidget(btn_reset)

        self.lbl_count = QLabel("")
        lay.addWidget(self.lbl_count)

    def _sep(self) -> QLabel:
        sep = QLabel(tr('vertical_separator'))
        sep.setStyleSheet(
            f"color:{_C['border_med']}; background:transparent;"
            f"border:none; font-size:{FS_SM}pt;"
        )
        return sep

    def _refresh_style(self, *_):
        base = get_font_size()
        self.lbl_count.setStyleSheet(
            f"color:{_C['accent']}; font-size:{fs(base,-2)}pt; font-weight:bold;"
            f"background:transparent; border:none; min-width:{FILTER_COUNT_LABEL_MIN_W}px;"
        )
        if self.cmb_cat is not None:
            self.cmb_cat.setStyleSheet(_combo_style())

    def _refresh_data(self, company_id=None):
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
                                        all_label=tr('filter_all_categories'))
            except Exception:
                self.cmb_cat.addItem(tr('filter_all_categories'), None)

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