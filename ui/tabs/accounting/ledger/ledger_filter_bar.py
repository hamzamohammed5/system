"""
ui/tabs/accounting/ledger/ledger_filter_bar.py
===============================================
_LedgerFilterBar — شريط فلاتر دفتر الأستاذ.

[إصلاح v3]:
  - يستخدم DateRangeFilter الموحد بدل بناء حقول التاريخ يدوياً.
  - لا يحفظ conn داخلياً — الـ LedgerTab هي المسؤولة عن تمرير conn حي.
  - الـ matches() و set_count() تعمل بدون أي DB access — فلترة محلية فقط.
"""

from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPushButton,
)
from PyQt5.QtCore import Qt, QDate

from ui.widgets.shared.date_range_filter import DateRangeFilter


class _LedgerFilterBar(QFrame):
    """شريط فلاتر متكامل لدفتر الأستاذ — لا يحتاج DB access."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: #f0f4ff;
                border: 1px solid #c5cae9;
                border-radius: 8px;
            }
        """)
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(8)

        lbl_search = QLabel("🔍")
        lbl_search.setStyleSheet("background:transparent; border:none; font-size:13px;")
        lbl_search.setFixedWidth(20)

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("بحث في البيان أو رقم القيد...")
        self.inp_search.setMinimumHeight(30)
        self.inp_search.setStyleSheet("""
            QLineEdit {
                background: white; border: 1px solid #c5cae9;
                border-radius: 5px; padding: 2px 8px; font-size: 12px;
            }
            QLineEdit:focus { border-color: #1565c0; }
        """)

        self.cmb_move_type = QComboBox()
        self.cmb_move_type.setMinimumHeight(30)
        self.cmb_move_type.setFixedWidth(120)
        self.cmb_move_type.addItem("كل الحركات", None)
        self.cmb_move_type.addItem("مدين فقط", "dr")
        self.cmb_move_type.addItem("دائن فقط", "cr")
        self.cmb_move_type.setStyleSheet("""
            QComboBox {
                background: white; border: 1px solid #c5cae9;
                border-radius: 5px; padding: 2px 8px; font-size: 12px;
            }
            QComboBox:focus { border-color: #1565c0; }
            QComboBox::drop-down { border: none; }
        """)

        sep1 = QLabel("│")
        sep1.setStyleSheet("color:#c5cae9; background:transparent; border:none; font-size:16px;")

        # ← DateRangeFilter الموحد بدل بناء حقول يدوياً
        self._date_filter = DateRangeFilter(
            default_from=QDate(2000, 1, 1),
            default_to=QDate.currentDate(),
        )
        # كشف dt_from و dt_to للتوافق مع الكود الخارجي
        self.dt_from = self._date_filter.dt_from
        self.dt_to   = self._date_filter.dt_to

        sep2 = QLabel("│")
        sep2.setStyleSheet(sep1.styleSheet())

        btn_reset = QPushButton("↺ مسح")
        btn_reset.setMinimumHeight(30)
        btn_reset.setFixedWidth(70)
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
            "background:transparent; border:none; min-width:60px;"
        )
        self.lbl_count.setAlignment(Qt.AlignCenter)

        lay.addWidget(lbl_search)
        lay.addWidget(self.inp_search, stretch=2)
        lay.addWidget(self.cmb_move_type)
        lay.addWidget(sep1)
        lay.addWidget(self._date_filter)
        lay.addWidget(sep2)
        lay.addWidget(btn_reset)
        lay.addWidget(self.lbl_count)

    def reset(self):
        self.inp_search.clear()
        self.cmb_move_type.setCurrentIndex(0)
        self._date_filter.reset()

    def matches(self, line: dict) -> bool:
        """فلترة محلية بالكامل — لا تحتاج DB access."""
        q = self.inp_search.text().strip().lower()
        if q:
            desc  = (line.get("description") or "").lower()
            ref   = (line.get("ref_no") or "").lower()
            entry = (line.get("entry_desc") or "").lower()
            if q not in desc and q not in ref and q not in entry:
                return False

        move_type = self.cmb_move_type.currentData()
        if move_type == "dr" and not (line.get("debit", 0) > 0):
            return False
        if move_type == "cr" and not (line.get("credit", 0) > 0):
            return False

        # استخدام DateRangeFilter.in_range() الموحدة
        if not self._date_filter.in_range(line.get("date", "")):
            return False

        return True

    def set_count(self, shown: int, total: int):
        if shown == total:
            self.lbl_count.setText(f"({total})")
        else:
            self.lbl_count.setText(f"({shown}/{total})")