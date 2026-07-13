"""
ui/tabs/accounting/journal/form/_balance_bar.py
================================================
_BalanceBar — شريط عرض توازن القيد (DR / CR / الفرق / الحالة).

مُستخرج من journal_form.py لتقليل الحجم وتسهيل إعادة الاستخدام.
يُستخدم فقط من _JournalForm.
"""

from PyQt5.QtWidgets import (
    QHBoxLayout, QLabel,
)
from PyQt5.QtCore import pyqtSignal
from ui.widgets.panels.themed_inputs import ThemedFrame

from ui.widgets.core.i18n import tr
from ui.font import FS_BASE, FS_LG, FS_XL
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import (
    BALANCE_BAR_MARGIN_H, BALANCE_BAR_MARGIN_V, BALANCE_BAR_SPACING,
    BALANCE_BAR_BORDER_RADIUS, BALANCE_BAR_BORDER_W,
    BALANCE_BAR_BADGE_RADIUS, BALANCE_BAR_BADGE_PAD_V, BALANCE_BAR_BADGE_PAD_H,
    BALANCE_BAR_BADGE_MARGIN_L,
)


class _BalanceBar(ThemedFrame, WidgetMixin):
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
        self._init_widget_mixin(data=False)
        self._build()
        self._refresh_style()

    def _build(self):
        bal_lay = QHBoxLayout(self)
        bal_lay.setContentsMargins(BALANCE_BAR_MARGIN_H, BALANCE_BAR_MARGIN_V,
                                   BALANCE_BAR_MARGIN_H, BALANCE_BAR_MARGIN_V)
        bal_lay.setSpacing(BALANCE_BAR_SPACING)

        def _sep():
            s = QLabel(tr("vertical_separator"))
            return s

        self.lbl_dr_t   = QLabel()
        self.lbl_sum_dr = QLabel(tr("amount_zero_placeholder"))

        self.lbl_cr_t   = QLabel()
        self.lbl_sum_cr = QLabel(tr("amount_zero_placeholder"))

        self.lbl_diff_t = QLabel()
        self.lbl_diff   = QLabel(tr("amount_zero_placeholder"))

        self.lbl_status = QLabel()

        self._sep1 = _sep()
        self._sep2 = _sep()
        self._sep3 = _sep()

        for w in (self.lbl_dr_t, self.lbl_sum_dr, self._sep1,
                  self.lbl_cr_t, self.lbl_sum_cr, self._sep2,
                  self.lbl_diff_t, self.lbl_diff, self._sep3,
                  self.lbl_status):
            bal_lay.addWidget(w)
        bal_lay.addStretch()

    @property
    def _badge_style(self) -> str:
        return (
            f"border-radius:{BALANCE_BAR_BADGE_RADIUS}px;"
            f"padding:{BALANCE_BAR_BADGE_PAD_V}px {BALANCE_BAR_BADGE_PAD_H}px;"
            f"margin-left:{BALANCE_BAR_BADGE_MARGIN_L}px;"
        )

    def _refresh_style(self, *_):
        from ui.theme import _C
        self.setStyleSheet(
            f"QFrame {{"
            f" background: {_C['journal_header_bg']};"
            f" border: {BALANCE_BAR_BORDER_W}px solid {_C['journal_header_border']};"
            f" border-radius: {BALANCE_BAR_BORDER_RADIUS}px;"
            f"}}"
        )
        _b = self._badge_style
        self.lbl_dr_t.setStyleSheet(f"font-weight:bold; color:{_C['journal_dr_accent']};")
        self.lbl_sum_dr.setStyleSheet(
            f"font-size:{FS_LG}px; font-weight:bold; color:{_C['journal_dr_accent']};"
            f"background:{_C['badge_dr_bg']}; {_b}"
        )
        self.lbl_cr_t.setStyleSheet(f"font-weight:bold; color:{_C['journal_cr_accent']};")
        self.lbl_sum_cr.setStyleSheet(
            f"font-size:{FS_LG}px; font-weight:bold; color:{_C['journal_cr_accent']};"
            f"background:{_C['badge_cr_bg']}; {_b}"
        )
        self.lbl_diff_t.setStyleSheet(f"font-weight:bold; color:{_C['text_sec']};")
        self.lbl_diff.setStyleSheet(
            f"font-size:{FS_LG}px; font-weight:bold; color:{_C['text_hint']};"
            f"background:{_C['bg_surface_2']}; {_b}"
        )
        self.lbl_status.setStyleSheet(
            f"font-size:{FS_BASE}px; font-weight:bold; color:{_C['text_hint']};"
        )
        self._sep1.setStyleSheet(
            f"color:{_C['border_med']}; font-size:{FS_XL}px; margin:0 {BALANCE_BAR_SPACING}px;"
        )
        self._sep2.setStyleSheet(self._sep1.styleSheet())
        self._sep3.setStyleSheet(self._sep1.styleSheet())

    def _refresh_lang(self, *_):
        self.lbl_dr_t.setText(tr("total_debit") + ":")
        self.lbl_cr_t.setText(tr("total_credit") + ":")
        self.lbl_diff_t.setText(tr("balance_bar_diff"))
        self.lbl_status.setText(tr("balance_bar_add_rows"))

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
        from ui.theme import _C
        _b = self._badge_style
        self.lbl_status.setText(tr("balance_bar_add_rows"))
        self.lbl_status.setStyleSheet(
            f"font-size:{FS_BASE}px; font-weight:bold; color:{_C['text_hint']};"
        )
        self.lbl_diff.setStyleSheet(
            f"font-size:{FS_LG}px; font-weight:bold; color:{_C['text_hint']};"
            f"background:{_C['bg_surface_2']}; {_b}"
        )

    def _set_balanced(self):
        from ui.theme import _C
        _b = self._badge_style
        self.lbl_status.setText(tr("journal_balanced"))
        self.lbl_status.setStyleSheet(
            f"font-size:{FS_BASE}px; font-weight:bold; color:{_C['investor_capital_text']};"
        )
        self.lbl_diff.setStyleSheet(
            f"font-size:{FS_LG}px; font-weight:bold; color:{_C['investor_capital_text']};"
            f"background:{_C['investor_capital_bg']}; {_b}"
        )

    def _set_unbalanced(self, diff: float):
        from ui.theme import _C
        _b = self._badge_style
        side = tr("dr_bigger") if diff > 0 else tr("cr_bigger")
        self.lbl_status.setText(
            tr("journal_unbalanced_detail", side=side, diff=f"{abs(diff):,.2f}")
        )
        self.lbl_status.setStyleSheet(
            f"font-size:{FS_BASE}px; font-weight:bold; color:{_C['journal_cr_accent']};"
        )
        self.lbl_diff.setStyleSheet(
            f"font-size:{FS_LG}px; font-weight:bold; color:{_C['journal_cr_accent']};"
            f"background:{_C['badge_cr_bg']}; {_b}"
        )
