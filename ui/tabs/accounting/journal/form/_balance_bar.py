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
from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.font import FS_BASE, FS_LG, FS_XL


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
        self.setStyleSheet(f"""
            QFrame {{
                background: {_C['journal_header_bg']};
                border: 1px solid {_C['journal_header_border']};
                border-radius: 6px;
            }}
        """)
        bal_lay = QHBoxLayout(self)
        bal_lay.setContentsMargins(14, 8, 14, 8)
        bal_lay.setSpacing(4)

        def _sep():
            s = QLabel("│")
            s.setStyleSheet(f"color:{_C['border_med']}; font-size:{FS_XL}px; margin:0 8px;")
            return s

        lbl_dr_t = QLabel(tr("total_debit") + ":")
        lbl_dr_t.setStyleSheet(f"font-weight:bold; color:{_C['journal_dr_accent']};")
        self.lbl_sum_dr = QLabel("0.00")
        self.lbl_sum_dr.setStyleSheet(
            f"font-size:{FS_LG}px; font-weight:bold; color:{_C['journal_dr_accent']};"
            f"background:{_C['badge_dr_bg']}; border-radius:4px; padding:3px 10px; margin-left:4px;"
        )

        lbl_cr_t = QLabel(tr("total_credit") + ":")
        lbl_cr_t.setStyleSheet(f"font-weight:bold; color:{_C['journal_cr_accent']};")
        self.lbl_sum_cr = QLabel("0.00")
        self.lbl_sum_cr.setStyleSheet(
            f"font-size:{FS_LG}px; font-weight:bold; color:{_C['journal_cr_accent']};"
            f"background:{_C['badge_cr_bg']}; border-radius:4px; padding:3px 10px; margin-left:4px;"
        )

        lbl_diff_t = QLabel(tr("balance_bar_diff"))
        lbl_diff_t.setStyleSheet(f"font-weight:bold; color:{_C['text_sec']};")
        self.lbl_diff = QLabel("0.00")
        self.lbl_diff.setStyleSheet(
            f"font-size:{FS_LG}px; font-weight:bold; color:{_C['text_hint']};"
            f"background:{_C['bg_surface_2']}; border-radius:4px; padding:3px 10px; margin-left:4px;"
        )

        self.lbl_status = QLabel(tr("balance_bar_add_rows"))
        self.lbl_status.setStyleSheet(
            f"font-size:{FS_BASE}px; font-weight:bold; color:{_C['text_hint']};"
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
        self.lbl_status.setText(tr("balance_bar_add_rows"))
        self.lbl_status.setStyleSheet(
            f"font-size:{FS_BASE}px; font-weight:bold; color:{_C['text_hint']};"
        )
        self.lbl_diff.setStyleSheet(
            f"font-size:{FS_LG}px; font-weight:bold; color:{_C['text_hint']};"
            f"background:{_C['bg_surface_2']}; border-radius:4px; padding:3px 10px; margin-left:4px;"
        )

    def _set_balanced(self):
        self.lbl_status.setText(tr("journal_balanced"))
        self.lbl_status.setStyleSheet(
            f"font-size:{FS_BASE}px; font-weight:bold; color:{_C['investor_capital_text']};"
        )
        self.lbl_diff.setStyleSheet(
            f"font-size:{FS_LG}px; font-weight:bold; color:{_C['investor_capital_text']};"
            f"background:{_C['investor_capital_bg']}; border-radius:4px; padding:3px 10px; margin-left:4px;"
        )

    def _set_unbalanced(self, diff: float):
        side = tr("dr_bigger") if diff > 0 else tr("cr_bigger")
        self.lbl_status.setText(
            tr("journal_unbalanced_detail", side=side, diff=f"{abs(diff):,.2f}")
        )
        self.lbl_status.setStyleSheet(
            f"font-size:{FS_BASE}px; font-weight:bold; color:{_C['journal_cr_accent']};"
        )
        self.lbl_diff.setStyleSheet(
            f"font-size:{FS_LG}px; font-weight:bold; color:{_C['journal_cr_accent']};"
            f"background:{_C['badge_cr_bg']}; border-radius:4px; padding:3px 10px; margin-left:4px;"
        )