"""
ui/tabs/accounting/journal_tab.py  — نسخة محدَّثة
===================================================
التغييرات:
  1. Smart routing  — بناءً على نوع الحساب والاتجاه (زيادة/نقص):
       asset / expense / drawings  → زيادة = DR  |  نقص = CR
       liability / capital / revenue → زيادة = CR  |  نقص = DR
     المستخدم يختار "زيادة ✚" أو "نقص ✖" والنظام يوجّه تلقائياً.

  2. جدول شجري — صف رئيسي (مجمل) + صفوف فرعية قابلة للطي.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QSplitter, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QAbstractItemView,
    QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox,
    QScrollArea, QRadioButton, QButtonGroup,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui  import QColor, QFont, QBrush

from db.accounting_repo import (
    fetch_all_entries, fetch_entry_lines,
    insert_entry, add_entry_lines,
    delete_entry, validate_entry_balance,
    fetch_account,
)
from db.accounting_schema import NORMAL_BALANCE
from ui.helpers import (
    make_table, setup_table_columns, buttons_row,
    section_label, danger_button, confirm_delete,
)
from ui.events import bus
from .account_combo import _AccountCombo


# ══════════════════════════════════════════════════════════
# منطق التوجيه التلقائي
# ══════════════════════════════════════════════════════════

def _resolve_side(acc_type: str, is_increase: bool) -> str:
    """
    يحدد الجانب الصحيح (dr أو cr) بناءً على نوع الحساب والاتجاه.

    الرصيد الطبيعي:
      DR: asset, expense, drawings
      CR: liability, capital, revenue

    زيادة الرصيد الطبيعي → نفس الجانب
    نقص  الرصيد الطبيعي → الجانب الآخر
    """
    nb = NORMAL_BALANCE.get(acc_type, "dr")   # dr أو cr
    if is_increase:
        return nb
    else:
        return "cr" if nb == "dr" else "dr"


# ══════════════════════════════════════════════════════════
# صف إدخال واحد — Smart
# ══════════════════════════════════════════════════════════

class _SmartLine(QFrame):
    """
    صف ذكي: المستخدم يختار الحساب والمبلغ واتجاه (زيادة/نقص)
    والنظام يحدد DR أو CR تلقائياً.
    """
    def __init__(self, conn, on_change, on_remove, on_move_up, on_move_dn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._on_change  = on_change
        self._on_remove  = on_remove
        self._on_move_up = on_move_up
        self._on_move_dn = on_move_dn
        self._resolved_side = "dr"   # القيمة المحسوبة الأخيرة
        self._build()

    def _build(self):
        self.setStyleSheet("""
            QFrame {
                background: #fafbff;
                border: 1px solid #dde3f0;
                border-radius: 6px;
            }
            QFrame:hover { border-color: #90aad4; }
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 5, 6, 5)
        lay.setSpacing(6)

        # ── أزرار الترتيب ──
        self.btn_up = QPushButton("▲")
        self.btn_dn = QPushButton("▼")
        for b in (self.btn_up, self.btn_dn):
            b.setFixedSize(20, 20)
            b.setStyleSheet(
                "QPushButton { background:transparent; border:none; color:#bbb; font-size:8px; }"
                "QPushButton:hover { color:#1565c0; }"
            )
        self.btn_up.clicked.connect(lambda: self._on_move_up(self))
        self.btn_dn.clicked.connect(lambda: self._on_move_dn(self))
        ord_col = QVBoxLayout()
        ord_col.setSpacing(0)
        ord_col.setContentsMargins(0, 0, 0, 0)
        ord_col.addWidget(self.btn_up)
        ord_col.addWidget(self.btn_dn)
        lay.addLayout(ord_col)

        # ── اختيار الحساب ──
        self._acc = _AccountCombo(self.conn)
        self._acc.cmb_account.currentIndexChanged.connect(self._on_acc_changed)
        lay.addWidget(self._acc, stretch=4)

        # ── اتجاه العملية ──
        dir_frame = QFrame()
        dir_frame.setStyleSheet("QFrame { background:transparent; border:none; }")
        dir_lay = QHBoxLayout(dir_frame)
        dir_lay.setContentsMargins(0, 0, 0, 0)
        dir_lay.setSpacing(4)

        self.rdo_inc = QRadioButton("زيادة ✚")
        self.rdo_dec = QRadioButton("نقص  ✖")
        self.rdo_inc.setChecked(True)
        self.rdo_inc.setStyleSheet("font-size:10px; color:#2e7d32; font-weight:bold;")
        self.rdo_dec.setStyleSheet("font-size:10px; color:#c62828; font-weight:bold;")
        self._dir_group = QButtonGroup(self)
        self._dir_group.addButton(self.rdo_inc, 1)
        self._dir_group.addButton(self.rdo_dec, 0)
        self.rdo_inc.toggled.connect(self._on_dir_changed)

        dir_lay.addWidget(self.rdo_inc)
        dir_lay.addWidget(self.rdo_dec)
        lay.addWidget(dir_frame)

        # ── مؤشر الجانب (DR/CR) ──
        self.lbl_side = QLabel("DR")
        self.lbl_side.setFixedWidth(34)
        self.lbl_side.setAlignment(Qt.AlignCenter)
        self.lbl_side.setStyleSheet(
            "font-weight:bold; font-size:11px; border-radius:4px; padding:2px 4px;"
            "background:#e3f2fd; color:#1565c0; border:1px solid #90caf9;"
        )
        lay.addWidget(self.lbl_side)

        # ── المبلغ ──
        self.sp_amount = QDoubleSpinBox()
        self.sp_amount.setRange(0, 999_999_999)
        self.sp_amount.setDecimals(2)
        self.sp_amount.setMinimumHeight(28)
        self.sp_amount.setFixedWidth(120)
        self.sp_amount.valueChanged.connect(self._on_change)
        lay.addWidget(self.sp_amount)

        # ── البيان ──
        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("بيان...")
        self.inp_desc.setMinimumHeight(28)
        lay.addWidget(self.inp_desc, stretch=2)

        # ── حذف ──
        btn_del = QPushButton("✖")
        btn_del.setFixedSize(24, 24)
        btn_del.setStyleSheet(
            "QPushButton { background:transparent; border:none; color:#bbb; font-size:11px; }"
            "QPushButton:hover { color:#e53935; }"
        )
        btn_del.clicked.connect(lambda: self._on_remove(self))
        lay.addWidget(btn_del)

        # حدّث المؤشر مبدئياً
        self._update_side_indicator()

    # ── منطق التوجيه ─────────────────────────────────────

    def _get_acc_type(self) -> str | None:
        acc_id = self._acc.current_account_id()
        if not acc_id:
            return None
        acc = fetch_account(self.conn, acc_id)
        return acc["type"] if acc else None

    def _update_side_indicator(self):
        acc_type = self._get_acc_type()
        is_inc   = self.rdo_inc.isChecked()

        if acc_type:
            side = _resolve_side(acc_type, is_inc)
            self._resolved_side = side
            if side == "dr":
                self.lbl_side.setText("DR")
                self.lbl_side.setStyleSheet(
                    "font-weight:bold; font-size:11px; border-radius:4px; padding:2px 4px;"
                    "background:#e3f2fd; color:#1565c0; border:1px solid #90caf9;"
                )
                self.setStyleSheet("""
                    QFrame {
                        background: #f4f8ff;
                        border: 1px solid #c5d8f7;
                        border-right: 3px solid #1565c0;
                        border-radius: 6px;
                    }
                """)
            else:
                self.lbl_side.setText("CR")
                self.lbl_side.setStyleSheet(
                    "font-weight:bold; font-size:11px; border-radius:4px; padding:2px 4px;"
                    "background:#fdecea; color:#c62828; border:1px solid #f7c5c5;"
                )
                self.setStyleSheet("""
                    QFrame {
                        background: #fff4f4;
                        border: 1px solid #f7c5c5;
                        border-right: 3px solid #c62828;
                        border-radius: 6px;
                    }
                """)
        else:
            self._resolved_side = "dr"
            self.lbl_side.setText("─")
            self.lbl_side.setStyleSheet(
                "font-weight:bold; font-size:11px; border-radius:4px; padding:2px 4px;"
                "background:#f5f5f5; color:#999; border:1px solid #ddd;"
            )
            self.setStyleSheet("""
                QFrame {
                    background: #fafbff;
                    border: 1px solid #dde3f0;
                    border-radius: 6px;
                }
            """)

    def _on_acc_changed(self):
        self._update_side_indicator()
        self._on_change()

    def _on_dir_changed(self):
        self._update_side_indicator()
        self._on_change()

    # ── API ──────────────────────────────────────────────

    def get_values(self) -> dict | None:
        acc_id = self._acc.current_account_id()
        amount = self.sp_amount.value()
        if not acc_id or amount == 0:
            return None
        side = self._resolved_side
        return {
            "account_id":  acc_id,
            "debit":       amount if side == "dr" else 0.0,
            "credit":      amount if side == "cr" else 0.0,
            "description": self.inp_desc.text().strip(),
        }

    def get_amount(self) -> float:
        return self.sp_amount.value()

    def get_side(self) -> str:
        return self._resolved_side


# ══════════════════════════════════════════════════════════
# لوحة الصفوف الذكية
# ══════════════════════════════════════════════════════════

class _LinesPanel(QFrame):
    def __init__(self, conn, on_balance_changed, parent=None):
        super().__init__(parent)
        self.conn                = conn
        self._on_balance_changed = on_balance_changed
        self._lines: list[_SmartLine] = []
        self._build()

    def _build(self):
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── رأس ──
        hdr = QFrame()
        hdr.setStyleSheet("background:#f0f4ff; border-radius:7px 7px 0 0;")
        hdr.setFixedHeight(38)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(12, 4, 12, 4)

        lbl = QLabel("📋  صفوف القيد")
        lbl.setStyleSheet("font-weight:bold; font-size:12px; color:#1565c0; background:transparent; border:none;")

        self.lbl_dr = QLabel("DR: 0.00")
        self.lbl_dr.setStyleSheet(
            "font-weight:bold; color:#1565c0; background:#e3f2fd; border-radius:4px;"
            "padding:2px 8px; font-size:11px; border:none;"
        )
        self.lbl_cr = QLabel("CR: 0.00")
        self.lbl_cr.setStyleSheet(
            "font-weight:bold; color:#c62828; background:#fdecea; border-radius:4px;"
            "padding:2px 8px; font-size:11px; border:none;"
        )

        hl.addWidget(lbl)
        hl.addStretch()
        hl.addWidget(self.lbl_dr)
        hl.addSpacing(8)
        hl.addWidget(self.lbl_cr)
        root.addWidget(hdr)

        # ── ترويسة الأعمدة ──
        col_hdr = QWidget()
        col_hdr.setStyleSheet("background:#fafbff;")
        ch_lay = QHBoxLayout(col_hdr)
        ch_lay.setContentsMargins(36, 2, 8, 2)
        ch_lay.setSpacing(6)

        def _ch(text, w=None, stretch=0):
            l = QLabel(text)
            l.setStyleSheet("font-size:9px; color:#888; font-weight:bold; background:transparent;")
            if w:
                l.setFixedWidth(w)
            ch_lay.addWidget(l, stretch=stretch)

        _ch("الحساب", stretch=4)
        _ch("الاتجاه", 95)
        _ch("DR/CR", 34)
        _ch("المبلغ", 120)
        _ch("البيان", stretch=2)
        _ch("", 24)
        root.addWidget(col_hdr)

        # ── منطقة الصفوف ──
        self._rows_w   = QWidget()
        self._rows_w.setStyleSheet("background:transparent;")
        self._rows_lay = QVBoxLayout(self._rows_w)
        self._rows_lay.setSpacing(3)
        self._rows_lay.setContentsMargins(6, 6, 6, 6)
        self._rows_lay.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._rows_w)
        scroll.setMinimumHeight(130)
        scroll.setMaximumHeight(320)
        scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")
        root.addWidget(scroll)

        # ── زر إضافة ──
        btn_add = QPushButton("➕  إضافة صف")
        btn_add.setMinimumHeight(28)
        btn_add.setStyleSheet("""
            QPushButton {
                background: #f0f4ff; color: #1565c0;
                border: 1px solid #c5cae9; border-radius: 4px;
                font-weight: bold; padding: 2px 12px; margin: 4px 8px;
            }
            QPushButton:hover { background: #1565c0; color: white; }
        """)
        btn_add.clicked.connect(self.add_line)
        root.addWidget(btn_add)

    # ── إدارة الصفوف ─────────────────────────────────────

    def add_line(self) -> _SmartLine:
        line = _SmartLine(
            conn        = self.conn,
            on_change   = self._on_line_changed,
            on_remove   = self._remove_line,
            on_move_up  = self._move_up,
            on_move_dn  = self._move_dn,
        )
        self._lines.append(line)
        self._rows_lay.insertWidget(self._rows_lay.count() - 1, line)
        self._refresh_totals()
        return line

    def _remove_line(self, line: _SmartLine):
        if len(self._lines) <= 1:
            QMessageBox.information(None, "تنبيه", "لازم يكون في صف واحد على الأقل")
            return
        self._lines.remove(line)
        self._rows_lay.removeWidget(line)
        line.deleteLater()
        self._on_line_changed()

    def _move_up(self, line: _SmartLine):
        idx = self._lines.index(line)
        if idx == 0:
            return
        self._lines[idx], self._lines[idx - 1] = self._lines[idx - 1], self._lines[idx]
        self._rebuild_rows()

    def _move_dn(self, line: _SmartLine):
        idx = self._lines.index(line)
        if idx >= len(self._lines) - 1:
            return
        self._lines[idx], self._lines[idx + 1] = self._lines[idx + 1], self._lines[idx]
        self._rebuild_rows()

    def _rebuild_rows(self):
        while self._rows_lay.count() > 1:
            item = self._rows_lay.takeAt(0)
            if item and item.widget():
                item.widget().setParent(None)
        for line in self._lines:
            self._rows_lay.insertWidget(self._rows_lay.count() - 1, line)

    def _on_line_changed(self):
        self._refresh_totals()
        self._on_balance_changed()

    def _refresh_totals(self):
        total_dr = sum(ln.get_amount() for ln in self._lines if ln.get_side() == "dr")
        total_cr = sum(ln.get_amount() for ln in self._lines if ln.get_side() == "cr")
        self.lbl_dr.setText(f"DR: {total_dr:,.2f}")
        self.lbl_cr.setText(f"CR: {total_cr:,.2f}")

    # ── API ──────────────────────────────────────────────

    def get_total_dr(self) -> float:
        return sum(ln.get_amount() for ln in self._lines if ln.get_side() == "dr")

    def get_total_cr(self) -> float:
        return sum(ln.get_amount() for ln in self._lines if ln.get_side() == "cr")

    def get_all_values(self) -> list:
        return [v for ln in self._lines if (v := ln.get_values()) is not None]

    def clear_lines(self):
        for ln in list(self._lines):
            self._rows_lay.removeWidget(ln)
            ln.deleteLater()
        self._lines.clear()
        self._refresh_totals()


# ══════════════════════════════════════════════════════════
# فورم القيد
# ══════════════════════════════════════════════════════════

class _JournalForm(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        # ── رأس القيد ──
        self.lbl_mode = QLabel("── قيد يومية جديد ──")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0; font-size:12px;")
        root.addWidget(self.lbl_mode)

        info_row = QHBoxLayout()
        info_row.setSpacing(8)

        self.dt_date = QDateEdit(QDate.currentDate())
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDisplayFormat("yyyy-MM-dd")
        self.dt_date.setFixedWidth(130)
        self.dt_date.setMinimumHeight(30)

        self.cmb_type = QComboBox()
        self.cmb_type.setMinimumHeight(30)
        self.cmb_type.setFixedWidth(120)
        for key, label in [
            ("manual",     "يدوي"),
            ("purchase",   "شراء"),
            ("sale",       "بيع"),
            ("payment",    "دفع"),
            ("receipt",    "تحصيل"),
            ("adjustment", "تسوية"),
        ]:
            self.cmb_type.addItem(label, key)

        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("وصف القيد الإجمالي...")
        self.inp_desc.setMinimumHeight(30)

        info_row.addWidget(QLabel("التاريخ:"))
        info_row.addWidget(self.dt_date)
        info_row.addWidget(QLabel("النوع:"))
        info_row.addWidget(self.cmb_type)
        info_row.addWidget(self.inp_desc, stretch=1)
        root.addLayout(info_row)

        # ── لوحة الصفوف الذكية ──
        self._lines_panel = _LinesPanel(self.conn, self._on_balance_changed)
        root.addWidget(self._lines_panel)

        # ── شريط التوازن ──
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

        # ── أزرار ──
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

        # ابدأ بصف واحد
        self._lines_panel.add_line()

    # ══════════════════════════════════════════════════════
    # التوازن
    # ══════════════════════════════════════════════════════

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

    # ══════════════════════════════════════════════════════
    # حفظ / مسح
    # ══════════════════════════════════════════════════════

    def _save(self):
        desc = self.inp_desc.text().strip()
        if not desc:
            QMessageBox.warning(self, "تنبيه", "أدخل وصف القيد")
            return

        all_lines = self._lines_panel.get_all_values()
        if not all_lines:
            QMessageBox.warning(self, "تنبيه", "أضف صفاً واحداً على الأقل")
            return

        dr_lines = [l for l in all_lines if l["debit"] > 0]
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

        entry_id = insert_entry(
            self.conn,
            self.dt_date.date().toString("yyyy-MM-dd"),
            desc,
            self.cmb_type.currentData()
        )
        add_entry_lines(self.conn, entry_id, all_lines)

        self._clear()
        bus.data_changed.emit()
        QMessageBox.information(self, "تم", "✅ تم حفظ القيد بنجاح")

    def _clear(self):
        self._lines_panel.clear_lines()
        self.inp_desc.clear()
        self.dt_date.setDate(QDate.currentDate())
        self.cmb_type.setCurrentIndex(0)
        self.lbl_mode.setText("── قيد يومية جديد ──")
        self.btn_save.setEnabled(False)
        self._lines_panel.add_line()
        self._on_balance_changed()


# ══════════════════════════════════════════════════════════
# جدول القيود — شجري (صف رئيسي + صفوف فرعية)
# ══════════════════════════════════════════════════════════

class _JournalTreeTable(QWidget):
    """
    جدول يعرض القيود بشكل شجري:
      ▶  JE-00001 | 2025-01-10 | شراء مواد | DR: 1000 | CR: 1000
         ├─ بنك          | CR | 1000
         └─ مخزون        | DR | 1000
    """

    # أعمدة الجدول
    COLS = ["#", "رقم القيد", "التاريخ", "النوع", "البيان / الحساب", "DR", "CR", "الرصيد"]

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._expanded: set[int] = set()   # IDs المفتوحة
        self._entries_data = []            # cache
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        # ── شريط أدوات ──
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(12, 6, 12, 0)

        root.addWidget(section_label("── القيود المحاسبية المحفوظة ──"))

        btn_expand_all   = QPushButton("⊞ توسيع الكل")
        btn_collapse_all = QPushButton("⊟ طي الكل")
        btn_del          = danger_button("🗑️  حذف القيد المحدد")

        for btn in (btn_expand_all, btn_collapse_all, btn_del):
            btn.setMinimumHeight(26)

        btn_expand_all.setStyleSheet(
            "QPushButton { background:#e8f4fd; color:#1565c0; border:1px solid #90caf9;"
            "border-radius:4px; padding:2px 10px; font-size:11px; }"
            "QPushButton:hover { background:#1565c0; color:white; }"
        )
        btn_collapse_all.setStyleSheet(btn_expand_all.styleSheet())

        btn_expand_all.clicked.connect(self._expand_all)
        btn_collapse_all.clicked.connect(self._collapse_all)
        btn_del.clicked.connect(self._delete_selected)

        root.addLayout(buttons_row(btn_expand_all, btn_collapse_all, btn_del))

        # ── الجدول ──
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(4, QHeaderView.Stretch)
        for col, w in {0:30, 1:85, 2:90, 3:70, 5:90, 6:90, 7:90}.items():
            hh.setSectionResizeMode(col, QHeaderView.Fixed)
            self.table.setColumnWidth(col, w)

        hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setWordWrap(False)
        self.table.cellClicked.connect(self._on_cell_clicked)

        root.addWidget(self.table, stretch=1)

    # ── تحميل البيانات ────────────────────────────────────

    def _load(self):
        from db.accounting_schema import TYPE_AR as _TYPE_AR
        self._type_ar = _TYPE_AR

        entries = fetch_all_entries(self.conn)
        self._entries_data = []

        for e in entries:
            lines = fetch_entry_lines(self.conn, e["id"])
            self._entries_data.append({
                "id":          e["id"],
                "ref_no":      e["ref_no"],
                "date":        e["date"],
                "type":        e["type"],
                "description": e["description"],
                "total_debit": e["total_debit"],
                "total_credit":e["total_credit"],
                "lines":       [dict(l) for l in lines],
            })

        self._render()

    def _render(self):
        self.table.setRowCount(0)
        self._row_meta = {}   # row_index → {"entry_id": ..., "is_parent": ..., "is_child": ...}

        type_ar = {
            "manual":     "يدوي",
            "purchase":   "شراء",
            "sale":       "بيع",
            "payment":    "دفع",
            "receipt":    "تحصيل",
            "adjustment": "تسوية",
        }

        for entry in self._entries_data:
            eid       = entry["id"]
            expanded  = eid in self._expanded
            total_dr  = entry["total_debit"]
            total_cr  = entry["total_credit"]

            # ── الصف الرئيسي ──
            r = self.table.rowCount()
            self.table.insertRow(r)
            self._row_meta[r] = {"entry_id": eid, "is_parent": True, "is_child": False}

            # خلية الـ toggle
            toggle_text = "▼" if expanded else "▶"
            toggle_item = QTableWidgetItem(toggle_text)
            toggle_item.setTextAlignment(Qt.AlignCenter)
            toggle_item.setForeground(QBrush(QColor("#1565c0")))
            f = QFont()
            f.setBold(True)
            toggle_item.setFont(f)
            self.table.setItem(r, 0, toggle_item)

            self.table.setItem(r, 1, self._bold_item(entry["ref_no"], "#1565c0"))
            self.table.setItem(r, 2, self._bold_item(entry["date"]))
            self.table.setItem(r, 3, QTableWidgetItem(type_ar.get(entry["type"], entry["type"])))
            self.table.setItem(r, 4, self._bold_item(entry["description"]))

            dr_item = self._bold_item(f"{total_dr:,.2f}", "#1565c0")
            cr_item = self._bold_item(f"{total_cr:,.2f}", "#c62828")
            self.table.setItem(r, 5, dr_item)
            self.table.setItem(r, 6, cr_item)

            diff = total_dr - total_cr
            bal_color = "#2e7d32" if abs(diff) < 0.01 else "#c62828"
            bal_text  = "✅ متوازن" if abs(diff) < 0.01 else f"⚠️ {abs(diff):,.2f}"
            self.table.setItem(r, 7, self._bold_item(bal_text, bal_color))

            # لون خلفية الصف الرئيسي
            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                if item:
                    item.setBackground(QBrush(QColor("#eef3fb")))

            # ── الصفوف الفرعية (تظهر فقط لو مفتوح) ──
            if expanded:
                for line in entry["lines"]:
                    rc = self.table.rowCount()
                    self.table.insertRow(rc)
                    self._row_meta[rc] = {"entry_id": eid, "is_parent": False, "is_child": True}

                    # مسافة بادئة في عمود البيان/الحساب
                    prefix = "    └─ "
                    acc_name = line.get("account_name", "")
                    acc_code = line.get("account_code", "")
                    acc_type = line.get("account_type", "")

                    desc_text = f"{prefix}{acc_code} — {acc_name}"
                    if line.get("description"):
                        desc_text += f"  │  {line['description']}"

                    side = "DR" if line["debit"] > 0 else "CR"
                    side_color = "#1565c0" if side == "DR" else "#c62828"

                    self.table.setItem(rc, 0, QTableWidgetItem(""))   # لا toggle
                    self.table.setItem(rc, 1, QTableWidgetItem(""))
                    self.table.setItem(rc, 2, QTableWidgetItem(""))
                    self.table.setItem(rc, 3, QTableWidgetItem(side))
                    self.table.item(rc, 3).setForeground(QBrush(QColor(side_color)))

                    desc_item = QTableWidgetItem(desc_text)
                    desc_item.setToolTip(f"{acc_code} — {acc_name}")
                    self.table.setItem(rc, 4, desc_item)

                    if line["debit"] > 0:
                        self.table.setItem(rc, 5, self._colored_item(f"{line['debit']:,.2f}", "#1565c0"))
                        self.table.setItem(rc, 6, QTableWidgetItem(""))
                    else:
                        self.table.setItem(rc, 5, QTableWidgetItem(""))
                        self.table.setItem(rc, 6, self._colored_item(f"{line['credit']:,.2f}", "#c62828"))

                    self.table.setItem(rc, 7, QTableWidgetItem(""))

                    # لون خلفية الصف الفرعي
                    bg = QColor("#f4f8ff") if side == "DR" else QColor("#fff4f4")
                    for c in range(self.table.columnCount()):
                        item = self.table.item(rc, c)
                        if item:
                            item.setBackground(QBrush(bg))

        self.table.setRowCount(self.table.rowCount())

    # ── مساعدات ──────────────────────────────────────────

    def _bold_item(self, text: str, color: str = None) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        f = QFont()
        f.setBold(True)
        item.setFont(f)
        if color:
            item.setForeground(QBrush(QColor(color)))
        return item

    def _colored_item(self, text: str, color: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setForeground(QBrush(QColor(color)))
        return item

    # ── التفاعل ──────────────────────────────────────────

    def _on_cell_clicked(self, row: int, col: int):
        meta = self._row_meta.get(row)
        if not meta or not meta["is_parent"]:
            return
        # فقط كليك على عمود الـ toggle أو الـ ref_no يفتح/يغلق
        if col not in (0, 1):
            return
        eid = meta["entry_id"]
        if eid in self._expanded:
            self._expanded.discard(eid)
        else:
            self._expanded.add(eid)
        self._render()

    def _expand_all(self):
        self._expanded = {e["id"] for e in self._entries_data}
        self._render()

    def _collapse_all(self):
        self._expanded.clear()
        self._render()

    def _selected_entry_id(self) -> int | None:
        row = self.table.currentRow()
        meta = self._row_meta.get(row)
        if not meta:
            return None
        return meta["entry_id"]

    def _delete_selected(self):
        eid = self._selected_entry_id()
        if eid is None:
            QMessageBox.information(self, "تنبيه", "اختر قيداً أولاً")
            return
        # ابحث عن الوصف
        entry_data = next((e for e in self._entries_data if e["id"] == eid), None)
        desc = entry_data["description"] if entry_data else f"ID:{eid}"

        if confirm_delete(self, desc):
            delete_entry(self.conn, eid)
            self._expanded.discard(eid)
            bus.data_changed.emit()


# ══════════════════════════════════════════════════════════
# تبويب القيود الكامل
# ══════════════════════════════════════════════════════════

class JournalTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet("""
            QSplitter::handle { background:#e0e0e0; }
            QSplitter::handle:hover { background:#bbdefb; }
        """)

        self._form        = _JournalForm(self.conn)
        self._tree_table  = _JournalTreeTable(self.conn)

        splitter.addWidget(self._form)
        splitter.addWidget(self._tree_table)
        splitter.setSizes([420, 380])
        splitter.setCollapsible(0, True)

        root.addWidget(splitter)