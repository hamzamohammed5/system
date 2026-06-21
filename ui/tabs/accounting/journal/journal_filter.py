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
    QLabel, QLineEdit, QComboBox, QPushButton,
)
from PyQt5.QtCore import Qt, QDate, QTimer, pyqtSignal

from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.utils.date_range import DateRangeFilter
from ui.widgets.core.events import bus, get_active_company_id
from ui.widgets.core.i18n import tr
from ui.theme import _C
from ui.font import FS_XS, FS_SM, FS_BASE, FS_MD, FS_XL
from .journal_group_combo import _TreeGroupCombo


class _JournalFilterBar(SafeConnMixin, QFrame):
    """شريط فلاتر متكامل لجدول القيود — بفلتر تصنيفات شجري."""

    # signal يُطلق بعد إعادة بناء _TreeGroupCombo عند تغيير الشركة
    group_reloaded = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self._init_safe_conn(conn, "accounting")
        self._company_id = get_active_company_id()
        self.setStyleSheet(f"""
            QFrame {{
                background: {_C['journal_header_bg']};
                border: 1px solid {_C['journal_header_border']};
                border-radius: 8px;
            }}
        """)
        self._build()
        bus.company_data_changed.connect(self._on_company_event)

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
        new_combo.setMinimumHeight(30)
        new_combo.setMinimumWidth(200)
        new_combo.setMaximumWidth(280)
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
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(6)

        # ══ الصف الأول: بحث + تصنيف + التوازن ══
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        lbl_s = QLabel("🔍")
        lbl_s.setStyleSheet(f"background:transparent; border:none; font-size:{FS_MD}px;")
        lbl_s.setFixedWidth(20)

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText(tr("journal_search_placeholder"))
        self.inp_search.setMinimumHeight(30)
        self.inp_search.setStyleSheet(f"""
            QLineEdit {{
                background: {_C['bg_input']}; border: 1px solid {_C['border_med']};
                border-radius: 5px; padding: 2px 8px; font-size: {FS_BASE}px;
            }}
            QLineEdit:focus {{ border-color: {_C['accent']}; }}
        """)

        lbl_grp = QLabel(tr("group_filter"))
        lbl_grp.setStyleSheet(
            f"background:transparent; border:none; font-weight:bold;"
            f"font-size:{FS_SM}px; color:{_C['text_sec']};"
        )

        self.cmb_group = _TreeGroupCombo(self._get_safe_conn())
        self.cmb_group.setMinimumHeight(30)
        self.cmb_group.setMinimumWidth(200)
        self.cmb_group.setMaximumWidth(280)
        self.cmb_group.setStyleSheet(f"""
            QComboBox {{
                background: {_C['bg_input']}; border: 1px solid {_C['border_med']};
                border-radius: 5px; padding: 2px 8px; font-size: {FS_SM}px;
            }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
        """)

        lbl_bal = QLabel(tr("balance_status_filter"))
        lbl_bal.setStyleSheet(lbl_grp.styleSheet())

        self.cmb_balance = QComboBox()
        self.cmb_balance.setMinimumHeight(30)
        self.cmb_balance.setFixedWidth(120)
        self.cmb_balance.addItem(tr("all"),            None)
        self.cmb_balance.addItem(tr("balanced_filter"),   "balanced")
        self.cmb_balance.addItem(tr("unbalanced_filter"), "unbalanced")
        self.cmb_balance.setStyleSheet(f"""
            QComboBox {{
                background: {_C['bg_input']}; border: 1px solid {_C['border_med']};
                border-radius: 5px; padding: 2px 8px; font-size: {FS_SM}px;
            }}
            QComboBox::drop-down {{ border: none; }}
        """)

        row1.addWidget(lbl_s)
        row1.addWidget(self.inp_search, stretch=2)
        row1.addWidget(lbl_grp)
        row1.addWidget(self.cmb_group, stretch=1)
        row1.addWidget(lbl_bal)
        row1.addWidget(self.cmb_balance)
        root.addLayout(row1)

        # ══ الصف الثاني: DateRangeFilter الموحد + مسح ══
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        lbl_date = QLabel("📅")
        lbl_date.setStyleSheet(f"background:transparent; border:none; font-size:{FS_MD}px;")
        lbl_date.setFixedWidth(20)
        row2.addWidget(lbl_date)

        self._date_filter = DateRangeFilter(
            default_from=QDate(2000, 1, 1),
            default_to=QDate.currentDate(),
        )
        # كشف dt_from و dt_to للتوافق مع الكود الخارجي
        self.dt_from = self._date_filter.dt_from
        self.dt_to   = self._date_filter.dt_to
        row2.addWidget(self._date_filter)

        sep = QLabel("│")
        sep.setStyleSheet(
            f"color:{_C['input_accent_border']}; background:transparent; border:none; font-size:{FS_XL}px;"
        )
        row2.addWidget(sep)

        btn_reset = QPushButton(tr("clear_filters"))
        btn_reset.setMinimumHeight(28)
        btn_reset.setFixedWidth(95)
        btn_reset.setStyleSheet(f"""
            QPushButton {{
                background: {_C['accent_light']}; border: 1px solid {_C['border_med']};
                border-radius: 5px; color: {_C['accent']};
                font-size: {FS_SM}px; padding: 2px 8px;
            }}
            QPushButton:hover {{ background: {_C['border_med']}; }}
        """)
        btn_reset.clicked.connect(self.reset)
        row2.addWidget(btn_reset)
        row2.addStretch()

        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet(
            f"color:{_C['accent']}; font-size:{FS_XS}px; font-weight:bold;"
            "background:transparent; border:none; min-width:70px;"
        )
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
            is_balanced = diff < 0.01
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