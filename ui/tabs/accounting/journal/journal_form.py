"""
ui/tabs/accounting/journal/journal_form.py
====================================
_JournalForm — فورم إدخال القيد اليومي الكامل.

[إصلاح v6]:
  - DualConnMixin بدل _get_erp_conn() المكرر يدوياً.
  - emit_company_data_changed() من company_utils بدل الدالة المحلية.

[إصلاح v7]:
  - _post_investor_links() دالة مستقلة بدل 30 سطراً داخل _save().
  - fetch_capital/drawings_line_for_entry() من repo_ui_helpers بدل SQL مباشر.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
)

from services.accounting.journal_service import JournalService, JournalLine
from ui.widgets.core.conn import DualConnMixin
from ui.widgets.core.events import emit_company_data_changed
from ui.widgets.core.i18n import tr
from ui.font import FS_BASE
from ui.widgets.dialogs.message import msg_warning, msg_info
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import (
    JOURNAL_FORM_MARGIN_H,
    JOURNAL_FORM_MARGIN_V,
    JOURNAL_FORM_SPACING,
    JOURNAL_FORM_BTN_MIN_H,
    JOURNAL_FORM_BTN_RADIUS,
    JOURNAL_FORM_BTN_SAVE_PAD_H,
    JOURNAL_FORM_BTN_CANCEL_PAD_H,
    JOURNAL_FORM_BORDER_W,
)
from .lines._lines_panel import _LinesPanel
from .form._balance_bar    import _BalanceBar
from .form._journal_header import _JournalHeader


class _JournalForm(DualConnMixin, QWidget, WidgetMixin):
    """فورم كامل لإدخال قيد يومية جديد مع صفوف ذكية وشريط توازن."""

    def __init__(self, conn, erp_conn=None, parent=None):
        super().__init__(parent)
        self._init_dual_conn(conn, erp_conn)
        self._build()
        self._init_widget_mixin(lang=True, data=False)
        self._refresh_style()

    def _refresh_lang(self, *_):
        self.lbl_mode.setText(tr("new_journal_entry"))
        self.btn_save.setText(tr("entry_save_btn"))
        self.btn_cancel.setText(tr("entry_clear_btn"))

    def _refresh_style(self, *_):
        from ui.theme import _C
        self.lbl_mode.setStyleSheet(
            f"font-weight:bold; color:{_C['accent']}; font-size:{FS_BASE}px;"
        )
        self.btn_save.setStyleSheet(
            f"QPushButton {{ background:{_C['accent']}; color:{_C['accent_text']};"
            f"font-weight:bold; border-radius:{JOURNAL_FORM_BTN_RADIUS}px; padding:0 {JOURNAL_FORM_BTN_SAVE_PAD_H}px; }}"
            f"QPushButton:hover {{ background:{_C['accent_hover']}; }}"
            f"QPushButton:disabled {{ background:{_C['text_disabled']}; color:{_C['bg_surface_2']}; }}"
        )
        self.btn_cancel.setStyleSheet(
            f"QPushButton {{ background:{_C['bg_surface_2']}; color:{_C['text_sec']};"
            f"border:{JOURNAL_FORM_BORDER_W}px solid {_C['border']}; border-radius:{JOURNAL_FORM_BTN_RADIUS}px; padding:0 {JOURNAL_FORM_BTN_CANCEL_PAD_H}px; }}"
            f"QPushButton:hover {{ background:{_C['bg_hover']}; }}"
        )

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(JOURNAL_FORM_MARGIN_H, JOURNAL_FORM_MARGIN_V,
                                JOURNAL_FORM_MARGIN_H, JOURNAL_FORM_MARGIN_V)
        root.setSpacing(JOURNAL_FORM_SPACING)

        self.lbl_mode = QLabel(tr("new_journal_entry"))
        root.addWidget(self.lbl_mode)

        self._hdr = _JournalHeader()
        root.addWidget(self._hdr)

        self._lines_panel = _LinesPanel(
            self._get_safe_conn(), self._get_erp_conn(), self._on_balance_changed
        )
        root.addWidget(self._lines_panel)

        self._balance_bar = _BalanceBar()
        root.addWidget(self._balance_bar)

        self.btn_save   = QPushButton(tr("entry_save_btn"))
        self.btn_cancel = QPushButton(tr("entry_clear_btn"))
        self.btn_save.setMinimumHeight(JOURNAL_FORM_BTN_MIN_H)
        self.btn_cancel.setMinimumHeight(JOURNAL_FORM_BTN_MIN_H)
        self.btn_save.setEnabled(False)

        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self._clear)
        _btn_row = QHBoxLayout()
        _btn_row.setSpacing(JOURNAL_FORM_SPACING)
        _btn_row.addWidget(self.btn_save)
        _btn_row.addWidget(self.btn_cancel)
        _btn_row.addStretch()
        root.addLayout(_btn_row)

        self._lines_panel.add_line()
        self._lines_panel.add_line()

    def _on_balance_changed(self):
        total_dr = self._lines_panel.get_total_dr()
        total_cr = self._lines_panel.get_total_cr()
        balanced = self._balance_bar.update(total_dr, total_cr)
        self.btn_save.setEnabled(balanced and (total_dr > 0 or total_cr > 0))

    def _save(self):
        conn = self._get_safe_conn()
        erp  = self._get_erp_conn()

        desc = self._hdr.description()
        if not desc:
            msg_warning(self, tr("warning"), tr("enter_field", label=tr("description")))
            return

        all_lines = self._lines_panel.get_all_values()
        if not all_lines:
            msg_warning(self, tr("warning"), tr("add_at_least_one_line"))
            return

        dr_lines = [l for l in all_lines if l["debit"]  > 0]
        cr_lines = [l for l in all_lines if l["credit"] > 0]
        if not dr_lines:
            msg_warning(self, tr("warning"), tr("no_dr_line"))
            return
        if not cr_lines:
            msg_warning(self, tr("warning"), tr("no_cr_line"))
            return

        svc_journal = JournalService(conn)
        journal_lines = [
            JournalLine(account_id=l["account_id"], dr=l["debit"], cr=l["credit"],
                       note=l.get("description", ""))
            for l in all_lines
        ]

        if not svc_journal.check_balance(journal_lines).is_balanced:
            td = sum(l["debit"]  for l in all_lines)
            tc = sum(l["credit"] for l in all_lines)
            msg_warning(self, tr("balance_error_title"), tr("balance_error_msg", dr=f"{td:,.2f}", cr=f"{tc:,.2f}"))
            return

        date   = self._hdr.date_str()
        result = svc_journal.post_entry(
            entry_data={"date": date, "description": desc, "entry_type": "manual"},
            lines=journal_lines,
        )
        entry_id = result.entry_id

        # [إصلاح v7] منطق ربط المستثمر في دالة منفصلة
        investor_links = self._lines_panel.get_all_investor_links()
        if investor_links and erp is not None:
            self._post_investor_links(conn, erp, entry_id, investor_links, desc)

        self._clear()
        emit_company_data_changed()
        msg_info(self, tr("done"), tr("journal_saved_success"))

    def _post_investor_links(self, conn, erp, entry_id: int,
                              investor_links: list, desc: str):
        """
        [إصلاح v7] يربط كل مستثمر بالقيد المناسب.
        مستخرج من _save() لتقليل حجمه وتسهيل الاختبار.
        يستخدم repo helpers بدل SQL مباشر.
        """
        from services.accounting.investors_service import InvestorsService
        svc_journal   = JournalService(conn)
        svc_investors = InvestorsService(erp, acc_conn=conn)

        for link in investor_links:
            inv_id    = link["investor_id"]
            acc_type  = link["acc_type"]
            amount    = link["amount"]
            move_type = "capital" if acc_type == "capital" else "drawings"

            side    = "credit" if move_type == "capital" else "debit"
            line_id = svc_journal.get_line_id(entry_id, side)

            try:
                svc_investors.link_to_line(
                    inv_id, entry_id, line_id,
                    move_type, amount, desc
                )
            except Exception as e:
                print(f"[JournalForm] investor link error: {e}")

    def _clear(self):
        self._lines_panel.clear_lines()
        self._hdr.reset()
        self.lbl_mode.setText(tr("new_journal_entry"))
        self.btn_save.setEnabled(False)
        self._lines_panel.add_line()
        self._lines_panel.add_line()
        self._on_balance_changed()
