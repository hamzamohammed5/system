"""
ui/tabs/accounting/journal/journal_filter.py
======================================
_JournalFilterBar — شريط فلاتر القيود المحاسبية.

[v5]:
  - DateRangeFilter الموحد بدل بناء حقول التاريخ يدوياً.
  - SafeConnMixin + get_active_company_id() من company_utils.
  - group_reloaded signal بعد استبدال الـ widget.
"""

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton,
)
from PyQt5.QtCore import Qt, QDate, QTimer, pyqtSignal
from ui.widgets.panels.themed_inputs import ThemedLineEdit, ThemedComboBox

from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.utils.date_range import DateRangeFilter
from ui.widgets.core.events import bus, get_active_company_id
from ui.widgets.core.i18n import tr
from ui.font import FS_XS, FS_SM, FS_BASE, FS_XL
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import (
    FILTER_BAR_BORDER_RADIUS,
    JOURNAL_FILTER_BORDER_W,
    JOURNAL_FILTER_MARGIN_H,
    JOURNAL_FILTER_MARGIN_V,
    JOURNAL_FILTER_SPACING,
    JOURNAL_FILTER_ROW_SPACING,
    JOURNAL_FILTER_INPUT_MIN_H,
    JOURNAL_FILTER_ICON_W,
    JOURNAL_FILTER_INPUT_RADIUS,
    JOURNAL_FILTER_INPUT_PAD_V,
    JOURNAL_FILTER_INPUT_PAD_H,
    JOURNAL_FILTER_DROP_W,
    JOURNAL_FILTER_GROUP_CMB_MIN_W,
    JOURNAL_FILTER_GROUP_CMB_MAX_W,
    JOURNAL_FILTER_BAL_CMB_W,
    JOURNAL_FILTER_BTN_RESET_MIN_H,
    JOURNAL_FILTER_BTN_RESET_W,
    JOURNAL_FILTER_COUNT_MIN_W,
    JOURNAL_BALANCE_EPSILON,
    JOURNAL_FILTER_DEFAULT_FROM_YEAR,
    JOURNAL_FILTER_DEFAULT_FROM_MONTH,
    JOURNAL_FILTER_DEFAULT_FROM_DAY,
)
from .group_combo._tree_group_combo import _TreeGroupCombo


class _JournalFilterBar(SafeConnMixin, QFrame, WidgetMixin):
    """شريط فلاتر متكامل لجدول القيود — بفلتر تصنيفات شجري."""

    # signal يُطلق بعد إعادة بناء _TreeGroupCombo عند تغيير الشركة
    group_reloaded = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self._init_safe_conn(conn, "accounting")
        self._company_id = get_active_company_id()
        self._build()
        self._init_widget_mixin(lang=True, data=False)
        self._refresh_style()
        bus.company_data_changed.connect(self._on_company_event)

    def _refresh_lang(self, *_):
        self.inp_search.setPlaceholderText(tr("journal_search_placeholder"))
        self.lbl_grp.setText(tr("group_filter"))
        self.lbl_bal.setText(tr("balance_status_filter"))
        self.sep.setText(tr("vertical_separator"))
        self.btn_reset.setText(tr("clear_filters"))
        # إعادة بناء items الـ combo مع حفظ الاختيار الحالي
        prev = self.cmb_balance.currentData()
        self.cmb_balance.clear()
        self.cmb_balance.addItem(tr("all"),              None)
        self.cmb_balance.addItem(tr("balanced_filter"),   "balanced")
        self.cmb_balance.addItem(tr("unbalanced_filter"), "unbalanced")
        for i in range(self.cmb_balance.count()):
            if self.cmb_balance.itemData(i) == prev:
                self.cmb_balance.setCurrentIndex(i)
                break

    def _refresh_style(self, *_):
        from ui.theme import _C
        self.setStyleSheet(f"""
            QFrame {{
                background: {_C['journal_header_bg']};
                border: {JOURNAL_FILTER_BORDER_W}px solid {_C['journal_header_border']};
                border-radius: {FILTER_BAR_BORDER_RADIUS}px;
            }}
        """)
        self.inp_search.setStyleSheet(f"""
            QLineEdit {{
                background: {_C['bg_input']}; border: {JOURNAL_FILTER_BORDER_W}px solid {_C['border_med']};
                border-radius: {JOURNAL_FILTER_INPUT_RADIUS}px; padding: {JOURNAL_FILTER_INPUT_PAD_V}px {JOURNAL_FILTER_INPUT_PAD_H}px; font-size: {FS_BASE}px;
            }}
            QLineEdit:focus {{ border-color: {_C['accent']}; }}
        """)
        _lbl_secondary = (
            f"background:transparent; border:none; font-weight:bold;"
            f"font-size:{FS_SM}px; color:{_C['text_sec']};"
        )
        self.lbl_grp.setStyleSheet(_lbl_secondary)
        self.lbl_bal.setStyleSheet(_lbl_secondary)
        self.cmb_group.setStyleSheet(f"""
            QComboBox {{
                background: {_C['bg_input']}; border: {JOURNAL_FILTER_BORDER_W}px solid {_C['border_med']};
                border-radius: {JOURNAL_FILTER_INPUT_RADIUS}px; padding: {JOURNAL_FILTER_INPUT_PAD_V}px {JOURNAL_FILTER_INPUT_PAD_H}px; font-size: {FS_SM}px;
            }}
            QComboBox::drop-down {{ border: none; width: {JOURNAL_FILTER_DROP_W}px; }}
        """)
        self.cmb_balance.setStyleSheet(f"""
            QComboBox {{
                background: {_C['bg_input']}; border: {JOURNAL_FILTER_BORDER_W}px solid {_C['border_med']};
                border-radius: {JOURNAL_FILTER_INPUT_RADIUS}px; padding: {JOURNAL_FILTER_INPUT_PAD_V}px {JOURNAL_FILTER_INPUT_PAD_H}px; font-size: {FS_SM}px;
            }}
            QComboBox::drop-down {{ border: none; }}
        """)
        self.sep.setStyleSheet(
            f"color:{_C['input_accent_border']}; background:transparent; border:none; font-size:{FS_XL}px;"
        )
        self.btn_reset.setStyleSheet(f"""
            QPushButton {{
                background: {_C['accent_light']}; border: {JOURNAL_FILTER_BORDER_W}px solid {_C['border_med']};
                border-radius: {JOURNAL_FILTER_INPUT_RADIUS}px; color: {_C['accent']};
                font-size: {FS_SM}px; padding: {JOURNAL_FILTER_INPUT_PAD_V}px {JOURNAL_FILTER_INPUT_PAD_H}px;
            }}
            QPushButton:hover {{ background: {_C['border_med']}; }}
        """)
        self.lbl_count.setStyleSheet(
            f"color:{_C['accent']}; font-size:{FS_XS}px; font-weight:bold;"
            f"background:transparent; border:none; min-width:{JOURNAL_FILTER_COUNT_MIN_W}px;"
        )

    def _on_company_event(self, company_id: int):
        if self._on_company_event_safe(company_id):
            QTimer.singleShot(0, self._reload_group_combo)

    def _reload_group_combo(self):
        """
        يُعيد إنشاء _TreeGroupCombo بـ conn حي.
        بعد الاستبدال يُطلق group_reloaded حتى يتمكن
        _JournalTreeTable من إعادة ربط signal الـ click.
        """
        conn = self._get_safe_conn()
        old_combo = self.cmb_group

        new_combo = _TreeGroupCombo(conn)
        new_combo.setMinimumHeight(JOURNAL_FILTER_INPUT_MIN_H)
        new_combo.setMinimumWidth(JOURNAL_FILTER_GROUP_CMB_MIN_W)
        new_combo.setMaximumWidth(JOURNAL_FILTER_GROUP_CMB_MAX_W)
        new_combo.setStyleSheet(old_combo.styleSheet())

        layout = old_combo.parent().layout() if old_combo.parent() else None
        if layout:
            idx = layout.indexOf(old_combo)
            if idx >= 0:
                layout.removeWidget(old_combo)
                old_combo.deleteLater()
                layout.insertWidget(idx, new_combo)

        self.cmb_group = new_combo
        self.group_reloaded.emit()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(JOURNAL_FILTER_MARGIN_H, JOURNAL_FILTER_MARGIN_V,
                                JOURNAL_FILTER_MARGIN_H, JOURNAL_FILTER_MARGIN_V)
        root.setSpacing(JOURNAL_FILTER_SPACING)

        # ══ الصف الأول: بحث + تصنيف + التوازن ══
        row1 = QHBoxLayout()
        row1.setSpacing(JOURNAL_FILTER_ROW_SPACING)

        lbl_s = QLabel(tr("empty_icon_search"))
        lbl_s.setFixedWidth(JOURNAL_FILTER_ICON_W)

        self.inp_search = ThemedLineEdit()
        self.inp_search.setPlaceholderText(tr("journal_search_placeholder"))
        self.inp_search.setMinimumHeight(JOURNAL_FILTER_INPUT_MIN_H)

        self.lbl_grp = QLabel(tr("group_filter"))

        self.cmb_group = _TreeGroupCombo(self._get_safe_conn())
        self.cmb_group.setMinimumHeight(JOURNAL_FILTER_INPUT_MIN_H)
        self.cmb_group.setMinimumWidth(JOURNAL_FILTER_GROUP_CMB_MIN_W)
        self.cmb_group.setMaximumWidth(JOURNAL_FILTER_GROUP_CMB_MAX_W)

        self.lbl_bal = QLabel(tr("balance_status_filter"))

        self.cmb_balance = ThemedComboBox()
        self.cmb_balance.setMinimumHeight(JOURNAL_FILTER_INPUT_MIN_H)
        self.cmb_balance.setFixedWidth(JOURNAL_FILTER_BAL_CMB_W)
        self.cmb_balance.addItem(tr("all"),            None)
        self.cmb_balance.addItem(tr("balanced_filter"),   "balanced")
        self.cmb_balance.addItem(tr("unbalanced_filter"), "unbalanced")

        row1.addWidget(lbl_s)
        row1.addWidget(self.inp_search, stretch=2)
        row1.addWidget(self.lbl_grp)
        row1.addWidget(self.cmb_group, stretch=1)
        row1.addWidget(self.lbl_bal)
        row1.addWidget(self.cmb_balance)
        root.addLayout(row1)

        # ══ الصف الثاني: DateRangeFilter الموحد + مسح ══
        row2 = QHBoxLayout()
        row2.setSpacing(JOURNAL_FILTER_ROW_SPACING)

        lbl_date = QLabel(tr("filter_date_icon"))
        lbl_date.setFixedWidth(JOURNAL_FILTER_ICON_W)
        row2.addWidget(lbl_date)

        self._date_filter = DateRangeFilter(
            default_from=QDate(JOURNAL_FILTER_DEFAULT_FROM_YEAR,
                               JOURNAL_FILTER_DEFAULT_FROM_MONTH,
                               JOURNAL_FILTER_DEFAULT_FROM_DAY),
            default_to=QDate.currentDate(),
        )
        # كشف dt_from و dt_to للتوافق مع الكود الخارجي
        self.dt_from = self._date_filter.dt_from
        self.dt_to   = self._date_filter.dt_to
        row2.addWidget(self._date_filter)

        self.sep = QLabel(tr("vertical_separator"))
        row2.addWidget(self.sep)

        self.btn_reset = QPushButton(tr("clear_filters"))
        self.btn_reset.setMinimumHeight(JOURNAL_FILTER_BTN_RESET_MIN_H)
        self.btn_reset.setFixedWidth(JOURNAL_FILTER_BTN_RESET_W)
        self.btn_reset.clicked.connect(self.reset)
        row2.addWidget(self.btn_reset)
        row2.addStretch()

        self.lbl_count = QLabel("")
        self.lbl_count.setAlignment(Qt.AlignCenter)
        row2.addWidget(self.lbl_count)
        root.addLayout(row2)

    # ── API الفلترة ──────────────────────────────────────

    def reset(self):
        self.inp_search.clear()
        self.cmb_group.reset()
        self.cmb_balance.setCurrentIndex(0)
        self._date_filter.reset()

    def matches(self, entry: dict) -> bool:
        q = self.inp_search.text().strip().lower()
        if q:
            desc   = (entry.get("description") or "").lower()
            ref_no = (entry.get("ref_no") or "").lower()
            if q not in desc and q not in ref_no:
                return False

        group_entry_ids = self.cmb_group.get_group_entry_ids()
        if group_entry_ids is not None:
            if entry.get("id") not in group_entry_ids:
                return False

        bal_filt = self.cmb_balance.currentData()
        if bal_filt:
            diff = abs(
                (entry.get("total_debit") or 0) -
                (entry.get("total_credit") or 0)
            )
            is_balanced = diff < JOURNAL_BALANCE_EPSILON
            if bal_filt == "balanced" and not is_balanced:
                return False
            if bal_filt == "unbalanced" and is_balanced:
                return False

        if not self._date_filter.in_range(entry.get("date", "")):
            return False

        return True

    def set_count(self, shown: int, total: int):
        if shown == total:
            self.lbl_count.setText(tr("journal_count_label", count=total))
        else:
            self.lbl_count.setText(tr("journal_count_filtered", shown=shown, total=total))
