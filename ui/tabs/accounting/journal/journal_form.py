"""
ui/tabs/accounting/journal/journal_form.py
====================================
_JournalForm — فورم إدخال القيد اليومي الكامل.

التقسيم الداخلي:
  form/_balance_bar.py   → _BalanceBar   (شريط DR/CR/الفرق/الحالة)
  form/_journal_header.py → _JournalHeader (صف التاريخ والوصف)

[إصلاح v4 — erp_conn reconnect]:
  - استبدال self.erp_conn الثابت بـ _get_erp_conn() helper.
  - _get_erp_conn() تتحقق من الـ conn وتعمل reconnect تلقائي لو احتاج.
  - _save() تجيب erp conn حي وقت الحفظ — مش وقت الإنشاء.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox,
)
from PyQt5.QtCore import Qt

from db.accounting.accounting_repo import (
    insert_entry, add_entry_lines, validate_entry_balance,
)
from ui.helpers import buttons_row
from ui.events  import bus
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
from .journal_lines import _LinesPanel
from .form._balance_bar    import _BalanceBar
from .form._journal_header import _JournalHeader


def _get_current_company_id() -> int | None:
    try:
        from db.companies.company_state import company_state
        return company_state.company_id if company_state.is_ready else None
    except Exception:
        return None


def _emit_data_changed():
    cid = _get_current_company_id()
    if cid is not None:
        bus.company_data_changed.emit(cid)
    else:
        bus.data_changed.emit()


class _JournalForm(SafeConnMixin, QWidget):
    """فورم كامل لإدخال قيد يومية جديد مع صفوف ذكية وشريط توازن."""

    def __init__(self, conn, erp_conn=None, parent=None):
        super().__init__(parent)
        self._init_safe_conn(conn, "accounting")
        self._erp_conn_ref = erp_conn
        self._build()

    def _get_erp_conn(self):
        """
        يرجع erp conn صالح دايماً.
        لو الـ connection مات أو لشركة مختلفة → يعمل reconnect تلقائي.
        """
        try:
            if self._erp_conn_ref is not None:
                self._erp_conn_ref.execute("SELECT 1")
                return self._erp_conn_ref
        except Exception:
            pass
        try:
            from db.companies.company_state import company_state
            new = company_state._get_conn("erp")
            self._erp_conn_ref = new
            return new
        except Exception:
            return self._erp_conn_ref

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        self.lbl_mode = QLabel("── قيد يومية جديد ──")
        self.lbl_mode.setStyleSheet(
            "font-weight:bold; color:#1565c0; font-size:12px;"
        )
        root.addWidget(self.lbl_mode)

        # ── رأس الفورم (التاريخ + الوصف) ──
        self._hdr = _JournalHeader()
        root.addWidget(self._hdr)

        # ── صفوف القيد ──
        self._lines_panel = _LinesPanel(
            self._get_safe_conn(), self._get_erp_conn(), self._on_balance_changed
        )
        root.addWidget(self._lines_panel)

        # ── شريط التوازن ──
        self._balance_bar = _BalanceBar()
        root.addWidget(self._balance_bar)

        # ── أزرار الحفظ والمسح ──
        self.btn_save   = QPushButton("💾  حفظ القيد")
        self.btn_cancel = QPushButton("✖  مسح")
        self.btn_save.setMinimumHeight(34)
        self.btn_cancel.setMinimumHeight(34)
        self.btn_save.setEnabled(False)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background:#1565c0; color:white;
                font-weight:bold; border-radius:6px; padding:0 20px;
            }
            QPushButton:hover  { background:#0d47a1; }
            QPushButton:disabled { background:#b0bec5; color:#eceff1; }
        """)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background:#f5f5f5; color:#555;
                border:1px solid #ddd; border-radius:6px; padding:0 14px;
            }
            QPushButton:hover { background:#eeeeee; }
        """)
        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self._clear)
        root.addLayout(buttons_row(self.btn_save, self.btn_cancel))

        self._lines_panel.add_line()
        self._lines_panel.add_line()

    def _on_balance_changed(self):
        total_dr  = self._lines_panel.get_total_dr()
        total_cr  = self._lines_panel.get_total_cr()
        balanced  = self._balance_bar.update(total_dr, total_cr)
        self.btn_save.setEnabled(balanced and (total_dr > 0 or total_cr > 0))

    def _save(self):
        conn = self._get_safe_conn()
        erp  = self._get_erp_conn()

        desc = self._hdr.description()
        if not desc:
            QMessageBox.warning(self, "تنبيه", "أدخل وصف القيد")
            return

        all_lines = self._lines_panel.get_all_values()
        if not all_lines:
            QMessageBox.warning(self, "تنبيه", "أضف صفاً واحداً على الأقل")
            return

        dr_lines = [l for l in all_lines if l["debit"]  > 0]
        cr_lines = [l for l in all_lines if l["credit"] > 0]
        if not dr_lines:
            QMessageBox.warning(self, "تنبيه", "لا يوجد أي صف مدين (DR)")
            return
        if not cr_lines:
            QMessageBox.warning(self, "تنبيه", "لا يوجد أي صف دائن (CR)")
            return

        if not validate_entry_balance(all_lines):
            td = sum(l["debit"]  for l in all_lines)
            tc = sum(l["credit"] for l in all_lines)
            QMessageBox.warning(
                self, "خطأ في التوازن",
                f"مجموع DR ({td:,.2f}) ≠ مجموع CR ({tc:,.2f})"
            )
            return

        date     = self._hdr.date_str()
        entry_id = insert_entry(conn, date, desc, "manual")
        add_entry_lines(conn, entry_id, all_lines)

        investor_links = self._lines_panel.get_all_investor_links()
        if investor_links and erp is not None:
            from db.inventory.investors_repo import link_investor_to_line
            for link in investor_links:
                inv_id    = link["investor_id"]
                acc_type  = link["acc_type"]
                amount    = link["amount"]
                move_type = "capital" if acc_type == "capital" else "drawings"
                if move_type == "capital":
                    line_row = conn.execute(
                        "SELECT id FROM journal_lines WHERE entry_id=? AND credit>0 LIMIT 1",
                        (entry_id,)
                    ).fetchone()
                else:
                    line_row = conn.execute(
                        "SELECT id FROM journal_lines WHERE entry_id=? AND debit>0 LIMIT 1",
                        (entry_id,)
                    ).fetchone()
                line_id = line_row["id"] if line_row else 0
                try:
                    link_investor_to_line(
                        erp, inv_id, entry_id, line_id,
                        move_type, amount, desc
                    )
                except Exception as e:
                    print(f"[JournalForm] investor link error: {e}")

        self._clear()
        _emit_data_changed()
        QMessageBox.information(self, "تم", "✅ تم حفظ القيد بنجاح")

    def _clear(self):
        self._lines_panel.clear_lines()
        self._hdr.reset()
        self.lbl_mode.setText("── قيد يومية جديد ──")
        self.btn_save.setEnabled(False)
        self._lines_panel.add_line()
        self._lines_panel.add_line()
        self._on_balance_changed()