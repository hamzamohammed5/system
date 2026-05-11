"""
ui/tabs/accounting/journal_filter.py
======================================
_JournalFilterBar — شريط فلاتر القيود المحاسبية.

يوفر:
  - بحث نصي في الوصف ورقم القيد
  - فلتر تصنيف الحسابات (شجرة هرمية عبر _TreeGroupCombo)
  - فلتر التوازن (متوازن / غير متوازن)
  - نطاق التاريخ من/إلى
  - زر مسح الفلاتر
"""

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QDateEdit, QPushButton,
)
from PyQt5.QtCore import Qt, QDate, QTimer

from .journal_group_combo import _TreeGroupCombo


class _JournalFilterBar(QFrame):
    """شريط فلاتر متكامل لجدول القيود — بفلتر تصنيفات شجري."""

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.setStyleSheet("""
            QFrame {
                background: #f0f4ff;
                border: 1px solid #c5cae9;
                border-radius: 8px;
            }
        """)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(6)

        # ══ الصف الأول: بحث + تصنيف + التوازن ══
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        lbl_s = QLabel("🔍")
        lbl_s.setStyleSheet("background:transparent; border:none; font-size:13px;")
        lbl_s.setFixedWidth(20)

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("بحث في الوصف أو رقم القيد...")
        self.inp_search.setMinimumHeight(30)
        self.inp_search.setStyleSheet("""
            QLineEdit {
                background: white; border: 1px solid #c5cae9;
                border-radius: 5px; padding: 2px 8px; font-size: 12px;
            }
            QLineEdit:focus { border-color: #1565c0; }
        """)

        lbl_grp = QLabel("🏷 التصنيف:")
        lbl_grp.setStyleSheet(
            "background:transparent; border:none; font-weight:bold;"
            "font-size:11px; color:#555;"
        )

        self.cmb_group = _TreeGroupCombo(self.conn)
        self.cmb_group.setMinimumHeight(30)
        self.cmb_group.setMinimumWidth(200)
        self.cmb_group.setMaximumWidth(280)
        self.cmb_group.setStyleSheet("""
            QComboBox {
                background: white; border: 1px solid #c5cae9;
                border-radius: 5px; padding: 2px 8px; font-size: 11px;
            }
            QComboBox::drop-down { border: none; width: 20px; }
        """)

        lbl_bal = QLabel("الحالة:")
        lbl_bal.setStyleSheet(lbl_grp.styleSheet())

        self.cmb_balance = QComboBox()
        self.cmb_balance.setMinimumHeight(30)
        self.cmb_balance.setFixedWidth(120)
        self.cmb_balance.addItem("الكل",          None)
        self.cmb_balance.addItem("✅ متوازن",      "balanced")
        self.cmb_balance.addItem("⚠️ غير متوازن", "unbalanced")
        self.cmb_balance.setStyleSheet("""
            QComboBox {
                background: white; border: 1px solid #c5cae9;
                border-radius: 5px; padding: 2px 8px; font-size: 11px;
            }
            QComboBox::drop-down { border: none; }
        """)

        row1.addWidget(lbl_s)
        row1.addWidget(self.inp_search, stretch=2)
        row1.addWidget(lbl_grp)
        row1.addWidget(self.cmb_group, stretch=1)
        row1.addWidget(lbl_bal)
        row1.addWidget(self.cmb_balance)
        root.addLayout(row1)

        # ══ الصف الثاني: نطاق التاريخ + مسح ══
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        lbl_date = QLabel("📅")
        lbl_date.setStyleSheet("background:transparent; border:none; font-size:13px;")
        lbl_date.setFixedWidth(20)

        lbl_from = QLabel("من:")
        lbl_from.setStyleSheet(lbl_grp.styleSheet())

        date_style = """
            QDateEdit {
                background: white; border: 1px solid #c5cae9;
                border-radius: 5px; padding: 2px 6px; font-size: 11px;
            }
            QDateEdit::drop-down { border: none; }
        """

        self.dt_from = QDateEdit()
        self.dt_from.setCalendarPopup(True)
        self.dt_from.setDisplayFormat("yyyy-MM-dd")
        self.dt_from.setDate(QDate(2000, 1, 1))
        self.dt_from.setFixedWidth(115)
        self.dt_from.setMinimumHeight(28)
        self.dt_from.setStyleSheet(date_style)

        lbl_to = QLabel("إلى:")
        lbl_to.setStyleSheet(lbl_grp.styleSheet())

        self.dt_to = QDateEdit()
        self.dt_to.setCalendarPopup(True)
        self.dt_to.setDisplayFormat("yyyy-MM-dd")
        self.dt_to.setDate(QDate.currentDate())
        self.dt_to.setFixedWidth(115)
        self.dt_to.setMinimumHeight(28)
        self.dt_to.setStyleSheet(date_style)

        sep = QLabel("│")
        sep.setStyleSheet("color:#c5cae9; background:transparent; border:none; font-size:16px;")

        btn_reset = QPushButton("↺ مسح الفلاتر")
        btn_reset.setMinimumHeight(28)
        btn_reset.setFixedWidth(95)
        btn_reset.setStyleSheet("""
            QPushButton {
                background: #e8eaf6; border: 1px solid #c5cae9;
                border-radius: 5px; color: #3949ab;
                font-size: 11px; padding: 2px 8px;
            }
            QPushButton:hover { background: #c5cae9; }
        """)
        btn_reset.clicked.connect(self.reset)

        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet(
            "color:#1565c0; font-size:10px; font-weight:bold;"
            "background:transparent; border:none; min-width:70px;"
        )
        self.lbl_count.setAlignment(Qt.AlignCenter)

        row2.addWidget(lbl_date)
        row2.addWidget(lbl_from)
        row2.addWidget(self.dt_from)
        row2.addWidget(lbl_to)
        row2.addWidget(self.dt_to)
        row2.addWidget(sep)
        row2.addWidget(btn_reset)
        row2.addStretch()
        row2.addWidget(self.lbl_count)
        root.addLayout(row2)

    # ── API الفلترة ──────────────────────────────────────

    def reset(self):
        self.inp_search.clear()
        self.cmb_group.reset()
        self.cmb_balance.setCurrentIndex(0)
        self.dt_from.setDate(QDate(2000, 1, 1))
        self.dt_to.setDate(QDate.currentDate())

    def matches(self, entry: dict) -> bool:
        """يتحقق إذا كان القيد يطابق الفلاتر الحالية."""
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

        date_str = entry.get("date", "")
        if date_str:
            try:
                d = QDate.fromString(date_str, "yyyy-MM-dd")
                if d < self.dt_from.date() or d > self.dt_to.date():
                    return False
            except Exception:
                pass

        return True

    def set_count(self, shown: int, total: int):
        if shown == total:
            self.lbl_count.setText(f"({total} قيد)")
        else:
            self.lbl_count.setText(f"({shown} / {total})")