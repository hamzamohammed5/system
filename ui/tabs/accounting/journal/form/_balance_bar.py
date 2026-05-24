"""
ui/tabs/accounting/journal/form/_balance_bar.py
================================================
_BalanceBar — شريط عرض توازن القيد (DR / CR / الفرق / الحالة).

مُستخرج من journal_form.py لتقليل الحجم وتسهيل إعادة الاستخدام.
يُستخدم فقط من _JournalForm.
"""

from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton,
)
from PyQt5.QtCore import pyqtSignal


class _BalanceBar(QFrame):
    """
    شريط يعرض:
      إجمالي DR | إجمالي CR | الفرق | حالة التوازن

    Signal:
      save_clicked  → يُطلق عند الضغط على زر الحفظ
      clear_clicked → يُطلق عند الضغط على زر المسح

    الاستخدام:
        bar = _BalanceBar()
        bar.update(total_dr=1000, total_cr=1000)
        bar.save_clicked.connect(self._save)
        bar.clear_clicked.connect(self._clear)
    """

    save_clicked  = pyqtSignal()
    clear_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        self.setStyleSheet("""
            QFrame {
                background: #f0f4ff;
                border: 1px solid #c5cae9;
                border-radius: 6px;
            }
        """)
        bal_lay = QHBoxLayout(self)
        bal_lay.setContentsMargins(14, 8, 14, 8)
        bal_lay.setSpacing(4)

        def _sep():
            s = QLabel("│")
            s.setStyleSheet("color:#c5cae9; font-size:18px; margin:0 8px;")
            return s

        lbl_dr_t = QLabel("إجمالي DR:")
        lbl_dr_t.setStyleSheet("font-weight:bold; color:#1565c0;")
        self.lbl_sum_dr = QLabel("0.00")
        self.lbl_sum_dr.setStyleSheet(
            "font-size:14px; font-weight:bold; color:#1565c0;"
            "background:#e3f2fd; border-radius:4px; padding:3px 10px; margin-left:4px;"
        )

        lbl_cr_t = QLabel("إجمالي CR:")
        lbl_cr_t.setStyleSheet("font-weight:bold; color:#c62828;")
        self.lbl_sum_cr = QLabel("0.00")
        self.lbl_sum_cr.setStyleSheet(
            "font-size:14px; font-weight:bold; color:#c62828;"
            "background:#fdecea; border-radius:4px; padding:3px 10px; margin-left:4px;"
        )

        lbl_diff_t = QLabel("الفرق:")
        lbl_diff_t.setStyleSheet("font-weight:bold; color:#555;")
        self.lbl_diff = QLabel("0.00")
        self.lbl_diff.setStyleSheet(
            "font-size:14px; font-weight:bold; color:#888;"
            "background:#f5f5f5; border-radius:4px; padding:3px 10px; margin-left:4px;"
        )

        self.lbl_status = QLabel("○ أضف صفوف")
        self.lbl_status.setStyleSheet(
            "font-size:12px; font-weight:bold; color:#888;"
        )

        for w in (lbl_dr_t, self.lbl_sum_dr, _sep(),
                  lbl_cr_t, self.lbl_sum_cr, _sep(),
                  lbl_diff_t, self.lbl_diff, _sep(),
                  self.lbl_status):
            bal_lay.addWidget(w)
        bal_lay.addStretch()

    # ── API خارجي ──────────────────────────────────────

    def update(self, total_dr: float, total_cr: float):
        """
        يحدّث القيم ويغيّر الألوان حسب حالة التوازن.
        يرجع True لو القيد متوازن.
        """
        diff = total_dr - total_cr

        self.lbl_sum_dr.setText(f"{total_dr:,.2f}")
        self.lbl_sum_cr.setText(f"{total_cr:,.2f}")
        self.lbl_diff.setText(f"{abs(diff):,.2f}")

        if total_dr == 0 and total_cr == 0:
            self._set_neutral()
            return False

        if abs(diff) < 0.001:
            self._set_balanced()
            return True

        self._set_unbalanced(diff)
        return False

    def _set_neutral(self):
        self.lbl_status.setText("○ أضف صفوف")
        self.lbl_status.setStyleSheet(
            "font-size:12px; font-weight:bold; color:#888;"
        )
        self.lbl_diff.setStyleSheet(
            "font-size:14px; font-weight:bold; color:#888;"
            "background:#f5f5f5; border-radius:4px; padding:3px 10px; margin-left:4px;"
        )

    def _set_balanced(self):
        self.lbl_status.setText("✅  متوازن — يمكن الحفظ")
        self.lbl_status.setStyleSheet(
            "font-size:12px; font-weight:bold; color:#2e7d32;"
        )
        self.lbl_diff.setStyleSheet(
            "font-size:14px; font-weight:bold; color:#2e7d32;"
            "background:#f1f8e9; border-radius:4px; padding:3px 10px; margin-left:4px;"
        )

    def _set_unbalanced(self, diff: float):
        side_ar = "DR أكبر" if diff > 0 else "CR أكبر"
        self.lbl_status.setText(
            f"⚠️  غير متوازن ({side_ar} بـ {abs(diff):,.2f})"
        )
        self.lbl_status.setStyleSheet(
            "font-size:12px; font-weight:bold; color:#c62828;"
        )
        self.lbl_diff.setStyleSheet(
            "font-size:14px; font-weight:bold; color:#c62828;"
            "background:#fdecea; border-radius:4px; padding:3px 10px; margin-left:4px;"
        )