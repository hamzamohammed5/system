"""
ui/tabs/accounting/ledger/ledger_filter_bar.py
===============================================
_LedgerFilterBar — شريط فلاتر دفتر الأستاذ.
"""

from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QDateEdit, QPushButton,
)
from PyQt5.QtCore import Qt, QDate


class _LedgerFilterBar(QFrame):
    """شريط فلاتر متكامل لدفتر الأستاذ."""

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

        lbl_from = QLabel("من:")
        lbl_from.setStyleSheet(
            "background:transparent; border:none; font-weight:bold; font-size:11px; color:#555;"
        )

        self.dt_from = QDateEdit()
        self.dt_from.setCalendarPopup(True)
        self.dt_from.setDisplayFormat("yyyy-MM-dd")
        self.dt_from.setDate(QDate(2000, 1, 1))
        self.dt_from.setFixedWidth(115)
        self.dt_from.setMinimumHeight(30)
        self.dt_from.setStyleSheet("""
            QDateEdit {
                background: white; border: 1px solid #c5cae9;
                border-radius: 5px; padding: 2px 6px; font-size: 11px;
            }
            QDateEdit:focus { border-color: #1565c0; }
            QDateEdit::drop-down { border: none; }
        """)

        lbl_to = QLabel("إلى:")
        lbl_to.setStyleSheet(lbl_from.styleSheet())

        self.dt_to = QDateEdit()
        self.dt_to.setCalendarPopup(True)
        self.dt_to.setDisplayFormat("yyyy-MM-dd")
        self.dt_to.setDate(QDate.currentDate())
        self.dt_to.setFixedWidth(115)
        self.dt_to.setMinimumHeight(30)
        self.dt_to.setStyleSheet(self.dt_from.styleSheet())

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
        lay.addWidget(lbl_from)
        lay.addWidget(self.dt_from)
        lay.addWidget(lbl_to)
        lay.addWidget(self.dt_to)
        lay.addWidget(sep2)
        lay.addWidget(btn_reset)
        lay.addWidget(self.lbl_count)

    def reset(self):
        self.inp_search.clear()
        self.cmb_move_type.setCurrentIndex(0)
        self.dt_from.setDate(QDate(2000, 1, 1))
        self.dt_to.setDate(QDate.currentDate())

    def matches(self, line: dict) -> bool:
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

        date_str = line.get("date", "")
        if date_str:
            try:
                from PyQt5.QtCore import QDate
                line_date = QDate.fromString(date_str, "yyyy-MM-dd")
                if line_date < self.dt_from.date() or line_date > self.dt_to.date():
                    return False
            except Exception:
                pass

        return True

    def set_count(self, shown: int, total: int):
        if shown == total:
            self.lbl_count.setText(f"({total})")
        else:
            self.lbl_count.setText(f"({shown}/{total})")