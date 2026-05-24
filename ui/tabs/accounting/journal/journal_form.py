"""
ui/tabs/accounting/journal/journal_form.py
====================================
_JournalForm — فورم إدخال القيد اليومي الكامل.

[إصلاح v4 — erp_conn reconnect]:
  - استبدال self.erp_conn الثابت بـ _get_erp_conn() helper.
  - _get_erp_conn() تتحقق من الـ conn وتعمل reconnect تلقائي لو احتاج.
  - _save() تجيب erp conn حي وقت الحفظ — مش وقت الإنشاء.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QLabel, QLineEdit, QPushButton, QDateEdit,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QDate

from db.accounting.accounting_repo import (
    insert_entry, add_entry_lines, validate_entry_balance,
)
from ui.helpers import buttons_row
from ui.events  import bus
from ui.tabs.accounting.safe_conn_mixin import SafeConnMixin
from .journal_lines import _LinesPanel


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
        # [إصلاح] نحفظ erp_conn كـ ref ونستخدم _get_erp_conn() دايماً
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

        # التاريخ والوصف
        info_row = QHBoxLayout()
        info_row.setSpacing(8)

        self.dt_date = QDateEdit(QDate.currentDate())
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDisplayFormat("yyyy-MM-dd")
        self.dt_date.setFixedWidth(130)
        self.dt_date.setMinimumHeight(30)

        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("وصف القيد الإجمالي...")
        self.inp_desc.setMinimumHeight(30)

        info_row.addWidget(QLabel("التاريخ:"))
        info_row.addWidget(self.dt_date)
        info_row.addSpacing(12)
        info_row.addWidget(QLabel("الوصف:"))
        info_row.addWidget(self.inp_desc, stretch=1)
        root.addLayout(info_row)

        # [إصلاح] _LinesPanel تستقبل _get_erp_conn() — conn حي وقت البناء
        # و_LinesPanel نفسها بتستخدم SafeConnMixin + _get_safe_conn() في add_line()
        self._lines_panel = _LinesPanel(
            self._get_safe_conn(), self._get_erp_conn(), self._on_balance_changed
        )
        root.addWidget(self._lines_panel)

        # شريط التوازن
        bal_frame = QFrame()
        bal_frame.setStyleSheet("""
            QFrame {
                background: #f0f4ff;
                border: 1px solid #c5cae9;
                border-radius: 6px;
            }
        """)
        bal_lay = QHBoxLayout(bal_frame)
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
        self.lbl_status.setStyleSheet("font-size:12px; font-weight:bold; color:#888;")

        for w in (lbl_dr_t, self.lbl_sum_dr, _sep(),
                  lbl_cr_t, self.lbl_sum_cr, _sep(),
                  lbl_diff_t, self.lbl_diff, _sep(),
                  self.lbl_status):
            bal_lay.addWidget(w)
        bal_lay.addStretch()
        root.addWidget(bal_frame)

        # أزرار
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
        total_dr = self._lines_panel.get_total_dr()
        total_cr = self._lines_panel.get_total_cr()
        diff     = total_dr - total_cr

        self.lbl_sum_dr.setText(f"{total_dr:,.2f}")
        self.lbl_sum_cr.setText(f"{total_cr:,.2f}")
        self.lbl_diff.setText(f"{abs(diff):,.2f}")

        if total_dr == 0 and total_cr == 0:
            self.lbl_status.setText("○ أضف صفوف")
            self.lbl_status.setStyleSheet("font-size:12px; font-weight:bold; color:#888;")
            self.lbl_diff.setStyleSheet(
                "font-size:14px; font-weight:bold; color:#888;"
                "background:#f5f5f5; border-radius:4px; padding:3px 10px; margin-left:4px;"
            )
            self.btn_save.setEnabled(False)
        elif abs(diff) < 0.001:
            self.lbl_status.setText("✅  متوازن — يمكن الحفظ")
            self.lbl_status.setStyleSheet("font-size:12px; font-weight:bold; color:#2e7d32;")
            self.lbl_diff.setStyleSheet(
                "font-size:14px; font-weight:bold; color:#2e7d32;"
                "background:#f1f8e9; border-radius:4px; padding:3px 10px; margin-left:4px;"
            )
            self.btn_save.setEnabled(True)
        else:
            side_ar = "DR أكبر" if diff > 0 else "CR أكبر"
            self.lbl_status.setText(
                f"⚠️  غير متوازن ({side_ar} بـ {abs(diff):,.2f})"
            )
            self.lbl_status.setStyleSheet("font-size:12px; font-weight:bold; color:#c62828;")
            self.lbl_diff.setStyleSheet(
                "font-size:14px; font-weight:bold; color:#c62828;"
                "background:#fdecea; border-radius:4px; padding:3px 10px; margin-left:4px;"
            )
            self.btn_save.setEnabled(False)

    def _save(self):
        # [إصلاح] كلا الـ connections حية وقت الحفظ
        conn = self._get_safe_conn()
        erp  = self._get_erp_conn()

        desc = self.inp_desc.text().strip()
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

        date     = self.dt_date.date().toString("yyyy-MM-dd")
        entry_id = insert_entry(conn, date, desc, "manual")
        add_entry_lines(conn, entry_id, all_lines)

        # [إصلاح] ربط المستثمرين يستخدم erp حي من _get_erp_conn()
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
        self.inp_desc.clear()
        self.dt_date.setDate(QDate.currentDate())
        self.lbl_mode.setText("── قيد يومية جديد ──")
        self.btn_save.setEnabled(False)
        self._lines_panel.add_line()
        self._lines_panel.add_line()
        self._on_balance_changed()
