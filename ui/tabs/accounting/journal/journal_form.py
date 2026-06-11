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
from PyQt5.QtCore import Qt

from db.accounting.accounting_repo import (
    insert_entry, add_entry_lines, validate_entry_balance,
)
from db.accounting.accounting_repo_ui_helpers import (
    fetch_capital_line_for_entry,
    fetch_drawings_line_for_entry,
)
from ui.widgets.core.conn import DualConnMixin
from ui.widgets.core.events import emit_company_data_changed
from ui.widgets.core.i18n import tr
from ui.theme import _C
from ui.widgets.dialogs.message import msg_warning, msg_info
from .journal_lines import _LinesPanel
from .form._balance_bar    import _BalanceBar
from .form._journal_header import _JournalHeader


class _JournalForm(DualConnMixin, QWidget):
    """فورم كامل لإدخال قيد يومية جديد مع صفوف ذكية وشريط توازن."""

    def __init__(self, conn, erp_conn=None, parent=None):
        super().__init__(parent)
        self._init_dual_conn(conn, erp_conn)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        self.lbl_mode = QLabel(tr("new_journal_entry"))
        self.lbl_mode.setStyleSheet(
            f"font-weight:bold; color:{_C['accent']}; font-size:12px;"
        )
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
        self.btn_save.setMinimumHeight(34)
        self.btn_cancel.setMinimumHeight(34)
        self.btn_save.setEnabled(False)
        self.btn_save.setStyleSheet(
            f"QPushButton {{ background:{_C['accent']}; color:{_C['accent_text']};"            "font-weight:bold; border-radius:6px; padding:0 20px; }"            f"QPushButton:hover {{ background:{_C['accent_hover']}; }}"            f"QPushButton:disabled {{ background:{_C['text_disabled']}; color:{_C['bg_surface_2']}; }}"
        )
        self.btn_cancel.setStyleSheet(
            f"QPushButton {{ background:{_C['bg_surface_2']}; color:{_C['text_sec']};"            f"border:1px solid {_C['border']}; border-radius:6px; padding:0 14px; }}"            f"QPushButton:hover {{ background:{_C['bg_hover']}; }}"
        )
        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self._clear)
        _btn_row = QHBoxLayout()
        _btn_row.setSpacing(8)
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

        if not validate_entry_balance(all_lines):
            td = sum(l["debit"]  for l in all_lines)
            tc = sum(l["credit"] for l in all_lines)
            msg_warning(self, tr("balance_error_title"), tr("balance_error_msg", dr=f"{td:,.2f}", cr=f"{tc:,.2f}"))
            return

        date     = self._hdr.date_str()
        entry_id = insert_entry(conn, date, desc, "manual")
        add_entry_lines(conn, entry_id, all_lines)

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
        from db.accounting.investors_repo import link_investor_to_line

        for link in investor_links:
            inv_id    = link["investor_id"]
            acc_type  = link["acc_type"]
            amount    = link["amount"]
            move_type = "capital" if acc_type == "capital" else "drawings"

            # [إصلاح v7] repo helpers بدل conn.execute() مباشر
            if move_type == "capital":
                line_id = fetch_capital_line_for_entry(conn, entry_id)
            else:
                line_id = fetch_drawings_line_for_entry(conn, entry_id)

            try:
                link_investor_to_line(
                    erp, inv_id, entry_id, line_id,
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