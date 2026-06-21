"""
ui/tabs/accounting/ledger/ledger_filter_bar.py
===============================================
_LedgerFilterBar — شريط فلاتر دفتر الأستاذ.

[إصلاح v4]:
  - يرث من FilterToolbar الموحد بدل بناء يدوي كامل.
  - DateRangeFilter مدمج تلقائياً عبر show_date=True.
  - matches() و set_count() محتفظ بهم للتوافق مع _TAccountPanel.
  - لا يحتاج conn — فلترة محلية بالكامل.
"""

from PyQt5.QtWidgets import QComboBox, QLabel
from PyQt5.QtCore import QDate

from ui.widgets.panels.filter       import FilterToolbar
from ui.widgets.theme.builders import v_divider
from ui.widgets.theme.input_styles import input_style
from ui.widgets.core.i18n import tr

class _LedgerFilterBar(FilterToolbar):
    """
    شريط فلاتر دفتر الأستاذ — يرث من FilterToolbar.

    يضيف:
      - فلتر نوع الحركة (مدين/دائن)
      - matches() للتوافق مع _TAccountPanel
    """

    def __init__(self, parent=None):
        super().__init__(
            conn=None,
            scope="all",
            show_category=False,
            show_date=True,
            show_presets=False,
            placeholder=tr("ledger_search_placeholder"),
            parent=parent,
        )
        self._add_move_type_filter()

    def _add_move_type_filter(self):
        """يضيف فلتر نوع الحركة بعد شريط البحث."""
        # separator
        sep = v_divider()
        # نضيف قبل زر المسح — نجد موقعه في الـ layout
        lay = self.layout()
        # نعثر على زر المسح (آخر widget قبل lbl_count)
        count = lay.count()
        # أضف separator + combo قبل زر المسح (index -2)
        insert_pos = max(1, count - 2)

        self.cmb_move_type = QComboBox()
        self.cmb_move_type.setMinimumHeight(28)
        self.cmb_move_type.setFixedWidth(120)
        self.cmb_move_type.addItem(tr("move_type_all"), None)
        self.cmb_move_type.addItem(tr("move_type_dr"),   "dr")
        self.cmb_move_type.addItem(tr("move_type_cr"),   "cr")
        self.cmb_move_type.setStyleSheet(input_style(height=28))
        self.cmb_move_type.currentIndexChanged.connect(
            lambda _: self.filter_changed.emit()
        )

        lay.insertWidget(insert_pos,     sep)
        lay.insertWidget(insert_pos + 1, self.cmb_move_type)

        # كشف dt_from / dt_to للتوافق مع _TAccountPanel
        if self._date_filter:
            self.dt_from = self._date_filter.dt_from
            self.dt_to   = self._date_filter.dt_to

    # ── API للتوافق مع _TAccountPanel ──────────────────────

    def matches(self, line: dict) -> bool:
        """فلترة محلية كاملة — لا تحتاج DB."""
        # بحث نصي
        q = self.name_query
        if q:
            desc  = (line.get("description") or "").lower()
            ref   = (line.get("ref_no")      or "").lower()
            entry = (line.get("entry_desc")  or "").lower()
            if q not in desc and q not in ref and q not in entry:
                return False

        # نوع الحركة
        move_type = self.cmb_move_type.currentData()
        if move_type == "dr" and not (line.get("debit",  0) > 0):
            return False
        if move_type == "cr" and not (line.get("credit", 0) > 0):
            return False

        # نطاق التاريخ
        if not self.in_date_range(line.get("date", "")):
            return False

        return True

    def reset(self):
        """يمسح كل الفلاتر بما فيها نوع الحركة."""
        super().reset()
        self.cmb_move_type.blockSignals(True)
        self.cmb_move_type.setCurrentIndex(0)
        self.cmb_move_type.blockSignals(False)
        self.filter_changed.emit()