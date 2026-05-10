"""
ui/tabs/accounting/journal_tab.py
===================================
قيود اليومية — تصميم بعمودين منفصلين DR | CR:

  - عمود DR على اليمين  وعمود CR على اليسار
  - إضافة صفوف غير محدودة في كل جانب بشكل مستقل
  - ترتيب الصفوف داخل كل جانب بأزرار ↑ ↓
  - لا يوجد auto-fill — المستخدم يدخل الأرقام بنفسه
  - شريط التوازن في الأسفل: إجمالي DR | إجمالي CR | الفرق | الحالة
  - زر الحفظ معطَّل حتى يتحقق التوازن (DR == CR)
  - كل الصفوف تُحفظ في Entry واحد
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QSplitter, QPushButton,
    QTableWidgetItem, QMessageBox,
    QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox,
    QScrollArea,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui  import QColor

from db.accounting_repo import (
    fetch_all_entries, insert_entry, add_entry_lines,
    delete_entry, validate_entry_balance,
)
from ui.helpers import (
    make_table, setup_table_columns, buttons_row,
    section_label, danger_button, confirm_delete,
)
from ui.events import bus
from .account_combo import _AccountCombo


# ══════════════════════════════════════════════════════════
# صف إدخال واحد — يُستخدم في كلا العمودين
# ══════════════════════════════════════════════════════════

class _SideLine(QFrame):
    """
    صف واحد داخل عمود DR أو CR:
      [▲][▼]  [حساب combo]  [مبلغ]  [بيان]  [✖]
    """
    def __init__(self, conn, side: str, on_change, on_remove, on_move_up, on_move_down,
                 parent=None):
        super().__init__(parent)
        self.conn         = conn
        self._side        = side
        self._on_change   = on_change
        self._on_remove   = on_remove
        self._on_move_up  = on_move_up
        self._on_move_dn  = on_move_down
        self._build()

    def _build(self):
        self._apply_style()
        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(4)

        # ── أزرار الترتيب ──
        self.btn_up = QPushButton("▲")
        self.btn_dn = QPushButton("▼")
        for b in (self.btn_up, self.btn_dn):
            b.setFixedSize(22, 22)
            b.setStyleSheet(
                "QPushButton { background:transparent; border:none; color:#aaa; font-size:9px; }"
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
        self._acc.cmb_account.currentIndexChanged.connect(self._changed)
        lay.addWidget(self._acc, stretch=3)

        # ── المبلغ ──
        self.sp_amount = QDoubleSpinBox()
        self.sp_amount.setRange(0, 999_999_999)
        self.sp_amount.setDecimals(2)
        self.sp_amount.setMinimumHeight(26)
        self.sp_amount.setFixedWidth(110)
        self.sp_amount.valueChanged.connect(self._changed)
        lay.addWidget(self.sp_amount)

        # ── البيان ──
        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("بيان...")
        self.inp_desc.setMinimumHeight(26)
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

    def _apply_style(self):
        if self._side == "dr":
            self.setStyleSheet("""
                QFrame {
                    background: #f4f8ff;
                    border: 1px solid #c5d8f7;
                    border-right: 3px solid #1565c0;
                    border-radius: 5px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background: #fff4f4;
                    border: 1px solid #f7c5c5;
                    border-right: 3px solid #c62828;
                    border-radius: 5px;
                }
            """)

    def _changed(self):
        self._on_change()

    # ── API ──────────────────────────────────────────────
    def get_values(self) -> dict | None:
        acc_id = self._acc.current_account_id()
        amount = self.sp_amount.value()
        if not acc_id or amount == 0:
            return None
        return {
            "account_id":  acc_id,
            "debit":       amount if self._side == "dr" else 0.0,
            "credit":      amount if self._side == "cr" else 0.0,
            "description": self.inp_desc.text().strip(),
        }

    def get_amount(self) -> float:
        return self.sp_amount.value()


# ══════════════════════════════════════════════════════════
# لوحة عمود واحد (DR أو CR) مع scroll وأزرار
# ══════════════════════════════════════════════════════════

class _SidePanel(QFrame):
    """
    لوحة عمود واحد: عنوان + scroll بالصفوف + زر إضافة + إجمالي
    """
    def __init__(self, conn, side: str, on_balance_changed, parent=None):
        super().__init__(parent)
        self.conn                = conn
        self._side               = side
        self._on_balance_changed = on_balance_changed
        self._lines: list[_SideLine] = []
        self._build()

    def _build(self):
        color     = "#1565c0" if self._side == "dr" else "#c62828"
        bg_header = "#e3f2fd" if self._side == "dr" else "#fdecea"
        title_txt = "📥  مدين  (DR)" if self._side == "dr" else "📤  دائن  (CR)"

        self.setObjectName(f"side_{self._side}")
        self.setStyleSheet(f"""
            QFrame#side_{self._side} {{
                border: 2px solid {color};
                border-radius: 8px;
                background: white;
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── رأس ──
        hdr = QFrame()
        hdr.setStyleSheet(f"background:{bg_header}; border-radius:6px 6px 0 0;")
        hdr.setFixedHeight(36)
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(10, 4, 10, 4)

        lbl_title = QLabel(title_txt)
        lbl_title.setStyleSheet(
            f"font-weight:bold; color:{color}; font-size:12px;"
            "background:transparent; border:none;"
        )
        lbl_tot_label = QLabel("الإجمالي:")
        lbl_tot_label.setStyleSheet("background:transparent; border:none; color:#555;")
        self.lbl_total = QLabel("0.00")
        self.lbl_total.setStyleSheet(
            f"font-weight:bold; color:{color}; font-size:13px;"
            "background:transparent; border:none;"
        )

        hdr_lay.addWidget(lbl_title)
        hdr_lay.addStretch()
        hdr_lay.addWidget(lbl_tot_label)
        hdr_lay.addWidget(self.lbl_total)
        root.addWidget(hdr)

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
        scroll.setMinimumHeight(120)
        scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")
        root.addWidget(scroll, stretch=1)

        # ── زر إضافة ──
        btn_add = QPushButton(
            f"➕  إضافة صف {'مدين' if self._side == 'dr' else 'دائن'}"
        )
        btn_add.setMinimumHeight(28)
        btn_add.setStyleSheet(f"""
            QPushButton {{
                background:{bg_header}; color:{color};
                border:1px solid {color}; border-radius:4px;
                font-weight:bold; padding:2px 10px; margin:4px 6px;
            }}
            QPushButton:hover {{ background:{color}; color:white; }}
        """)
        btn_add.clicked.connect(self.add_line)
        root.addWidget(btn_add)

    # ─────────────────────────────────────────────────────
    def add_line(self) -> "_SideLine":
        line = _SideLine(
            conn         = self.conn,
            side         = self._side,
            on_change    = self._on_line_changed,
            on_remove    = self._remove_line,
            on_move_up   = self._move_up,
            on_move_down = self._move_down,
        )
        self._lines.append(line)
        self._rows_lay.insertWidget(self._rows_lay.count() - 1, line)
        self._refresh_total()
        return line

    def _remove_line(self, line: "_SideLine"):
        if len(self._lines) <= 1:
            QMessageBox.information(None, "تنبيه", "لازم يكون في صف واحد على الأقل")
            return
        self._lines.remove(line)
        self._rows_lay.removeWidget(line)
        line.deleteLater()
        self._on_line_changed()

    def _move_up(self, line: "_SideLine"):
        idx = self._lines.index(line)
        if idx == 0:
            return
        self._lines[idx], self._lines[idx - 1] = self._lines[idx - 1], self._lines[idx]
        self._rebuild_rows()

    def _move_down(self, line: "_SideLine"):
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
        self._refresh_total()
        self._on_balance_changed()

    def _refresh_total(self):
        total = sum(ln.get_amount() for ln in self._lines)
        self.lbl_total.setText(f"{total:,.2f}")

    # ── API ──────────────────────────────────────────────
    def get_total(self) -> float:
        return sum(ln.get_amount() for ln in self._lines)

    def get_all_values(self) -> list:
        return [v for ln in self._lines if (v := ln.get_values()) is not None]

    def clear_lines(self):
        for ln in list(self._lines):
            self._rows_lay.removeWidget(ln)
            ln.deleteLater()
        self._lines.clear()
        self._refresh_total()


# ══════════════════════════════════════════════════════════
# فورم القيد الكامل
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

        # ── رأس ──
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

        # ── العمودان DR | CR ──
        cols = QHBoxLayout()
        cols.setSpacing(10)
        self._dr_panel = _SidePanel(self.conn, "dr", self._on_balance_changed)
        self._cr_panel = _SidePanel(self.conn, "cr", self._on_balance_changed)
        cols.addWidget(self._dr_panel, stretch=1)
        cols.addWidget(self._cr_panel, stretch=1)
        root.addLayout(cols, stretch=1)

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

        def _bal_lbl(text, style=""):
            l = QLabel(text)
            if style:
                l.setStyleSheet(style)
            return l

        def _sep():
            s = QLabel("│")
            s.setStyleSheet("color:#c5cae9; font-size:18px; margin:0 10px;")
            return s

        lbl_dr_t = _bal_lbl("إجمالي DR:", "font-weight:bold; color:#1565c0;")
        self.lbl_sum_dr = _bal_lbl("0.00",
            "font-size:14px; font-weight:bold; color:#1565c0;"
            "background:#e3f2fd; border-radius:4px; padding:3px 10px; margin-left:4px;")

        lbl_cr_t = _bal_lbl("إجمالي CR:", "font-weight:bold; color:#c62828;")
        self.lbl_sum_cr = _bal_lbl("0.00",
            "font-size:14px; font-weight:bold; color:#c62828;"
            "background:#fdecea; border-radius:4px; padding:3px 10px; margin-left:4px;")

        lbl_diff_t = _bal_lbl("الفرق:", "font-weight:bold; color:#555;")
        self.lbl_diff = _bal_lbl("0.00",
            "font-size:14px; font-weight:bold; color:#888;"
            "background:#f5f5f5; border-radius:4px; padding:3px 10px; margin-left:4px;")

        self.lbl_status = _bal_lbl("○ أضف صفوف",
            "font-size:12px; font-weight:bold; color:#888;")

        for w in (lbl_dr_t, self.lbl_sum_dr, _sep(),
                  lbl_cr_t, self.lbl_sum_cr, _sep(),
                  lbl_diff_t, self.lbl_diff, _sep(),
                  self.lbl_status):
            bal_lay.addWidget(w)
        bal_lay.addStretch()

        root.addWidget(bal_frame)

        # ── أزرار الحفظ ──
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

        # ابدأ بصف واحد في كل جانب
        self._dr_panel.add_line()
        self._cr_panel.add_line()

    # ══════════════════════════════════════════════════════
    # التوازن — يُحسب ويُعرض فقط ولا يعدّل أي مدخل
    # ══════════════════════════════════════════════════════

    def _on_balance_changed(self):
        total_dr = self._dr_panel.get_total()
        total_cr = self._cr_panel.get_total()
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
            # ✅ متوازن
            self.lbl_status.setText("✅  متوازن — يمكن الحفظ")
            self.lbl_status.setStyleSheet("font-size:12px; font-weight:bold; color:#2e7d32;")
            self.lbl_diff.setStyleSheet(
                "font-size:14px; font-weight:bold; color:#2e7d32;"
                "background:#f1f8e9; border-radius:4px; padding:3px 10px; margin-left:4px;"
            )
            self.btn_save.setEnabled(True)

        else:
            # ⚠️ غير متوازن
            side_ar = "DR أكبر" if diff > 0 else "CR أكبر"
            self.lbl_status.setText(
                f"⚠️  غير متوازن ({side_ar} بـ {abs(diff):,.2f}) — لا يمكن الحفظ"
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

        dr_lines  = self._dr_panel.get_all_values()
        cr_lines  = self._cr_panel.get_all_values()
        all_lines = dr_lines + cr_lines

        if not dr_lines:
            QMessageBox.warning(self, "تنبيه", "أضف صفًا مدينًا (DR) واحدًا على الأقل")
            return
        if not cr_lines:
            QMessageBox.warning(self, "تنبيه", "أضف صفًا دائنًا (CR) واحدًا على الأقل")
            return

        # guard نهائي
        if not validate_entry_balance(all_lines):
            td = sum(l["debit"]  for l in all_lines)
            tc = sum(l["credit"] for l in all_lines)
            QMessageBox.warning(
                self, "خطأ في التوازن",
                f"مجموع DR ({td:,.2f}) ≠ مجموع CR ({tc:,.2f})\n"
                "تأكد من التوازن قبل الحفظ."
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
        self._dr_panel.clear_lines()
        self._cr_panel.clear_lines()
        self.inp_desc.clear()
        self.dt_date.setDate(QDate.currentDate())
        self.cmb_type.setCurrentIndex(0)
        self.lbl_mode.setText("── قيد يومية جديد ──")
        self.btn_save.setEnabled(False)
        # أعد صفًا واحدًا في كل جانب
        self._dr_panel.add_line()
        self._cr_panel.add_line()
        self._on_balance_changed()


# ══════════════════════════════════════════════════════════
# تبويب القيود الكامل
# ══════════════════════════════════════════════════════════

class JournalTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        bus.data_changed.connect(self._load_table)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet("""
            QSplitter::handle { background:#e0e0e0; }
            QSplitter::handle:hover { background:#bbdefb; }
        """)

        self._form = _JournalForm(self.conn)
        splitter.addWidget(self._form)

        # ── جدول القيود المحفوظة ──
        table_w = QWidget()
        tl = QVBoxLayout(table_w)
        tl.setContentsMargins(12, 8, 12, 12)
        tl.setSpacing(6)
        tl.addWidget(section_label("── القيود المحاسبية المحفوظة ──"))

        self.table = make_table(
            ["#", "رقم القيد", "التاريخ", "النوع", "البيان", "مجموع DR", "مجموع CR"],
            stretch_col=4
        )
        setup_table_columns(self.table,
            widths={0: 40, 1: 90, 2: 90, 3: 80, 5: 100, 6: 100},
            stretch_col=4
        )
        self.table.setAlternatingRowColors(True)
        tl.addWidget(self.table, stretch=1)

        btn_del = danger_button("🗑️  حذف القيد المحدد")
        btn_del.setMinimumHeight(30)
        btn_del.clicked.connect(self._delete_entry)
        tl.addLayout(buttons_row(btn_del))

        splitter.addWidget(table_w)
        splitter.setSizes([480, 280])
        root.addWidget(splitter)
        self._load_table()

    def _load_table(self):
        entries = fetch_all_entries(self.conn)
        self.table.setRowCount(0)
        type_ar = {
            "manual":     "يدوي",
            "purchase":   "شراء",
            "sale":       "بيع",
            "payment":    "دفع",
            "receipt":    "تحصيل",
            "adjustment": "تسوية",
        }
        for e in entries:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(e["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(e["ref_no"]))
            self.table.setItem(r, 2, QTableWidgetItem(e["date"]))
            self.table.setItem(r, 3, QTableWidgetItem(type_ar.get(e["type"], e["type"])))
            di = QTableWidgetItem(e["description"])
            di.setToolTip(e["description"])
            self.table.setItem(r, 4, di)
            dr_item = QTableWidgetItem(f"{e['total_debit']:,.2f}")
            dr_item.setForeground(QColor("#1565c0"))
            self.table.setItem(r, 5, dr_item)
            cr_item = QTableWidgetItem(f"{e['total_credit']:,.2f}")
            cr_item.setForeground(QColor("#c62828"))
            self.table.setItem(r, 6, cr_item)

    def _delete_entry(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر قيدًا أولًا")
            return
        eid  = int(self.table.item(row, 0).text())
        desc = self.table.item(row, 4).text()
        if confirm_delete(self, desc):
            delete_entry(self.conn, eid)
            bus.data_changed.emit()