"""
ui/tabs/accounting/journal_lines.py
=====================================
_SmartLine  — صف قيد ذكي واحد (حساب + اتجاه + مبلغ + بيان + ربط مستثمر)
_LinesPanel — لوحة صفوف القيد كاملة مع scroll وإضافة/حذف/ترتيب
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QLabel, QLineEdit, QPushButton,
    QDoubleSpinBox, QComboBox, QScrollArea,
    QMessageBox, QRadioButton, QButtonGroup,
)
from PyQt5.QtCore import Qt

from db.accounting_repo import fetch_account, get_normal_balance
from db.accounting_schema import NORMAL_BALANCE
from ui.events import bus
from .journal_account_picker import _AccountPickerButton

_INVESTOR_TYPES = {"capital", "drawings"}


def _resolve_side(acc_type: str, is_increase: bool) -> str:
    nb = NORMAL_BALANCE.get(acc_type, "dr")
    return nb if is_increase else ("cr" if nb == "dr" else "dr")


class _SmartLine(QFrame):
    """صف قيد واحد: حساب + زيادة/نقص + مبلغ + بيان + ربط مستثمر اختياري."""

    def __init__(self, conn, erp_conn, on_change, on_remove,
                 on_move_up, on_move_dn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self.erp_conn    = erp_conn
        self._on_change  = on_change
        self._on_remove  = on_remove
        self._on_move_up = on_move_up
        self._on_move_dn = on_move_dn
        self._resolved_side = "dr"
        self._build()
        bus.data_changed.connect(self._reload_investors)

    def _build(self):
        self.setStyleSheet("""
            QFrame {
                background: #fafbff;
                border: 1px solid #dde3f0;
                border-radius: 6px;
            }
            QFrame:hover { border-color: #90aad4; }
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(4)

        main_row = QHBoxLayout()
        main_row.setSpacing(6)

        # أزرار الترتيب
        self.btn_up = QPushButton("▲")
        self.btn_dn = QPushButton("▼")
        for b in (self.btn_up, self.btn_dn):
            b.setFixedSize(18, 18)
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
        main_row.addLayout(ord_col)

        # اختيار الحساب
        self._acc = _AccountPickerButton(self.conn)
        self._acc.set_on_changed(self._on_acc_changed)
        main_row.addWidget(self._acc, stretch=4)

        # اتجاه الحركة
        dir_frame = QFrame()
        dir_frame.setStyleSheet("QFrame { background:transparent; border:none; }")
        dir_lay = QHBoxLayout(dir_frame)
        dir_lay.setContentsMargins(0, 0, 0, 0)
        dir_lay.setSpacing(3)
        self.rdo_inc = QRadioButton("زيادة ✚")
        self.rdo_dec = QRadioButton("نقص ✖")
        self.rdo_inc.setChecked(True)
        self.rdo_inc.setStyleSheet("font-size:10px; color:#2e7d32; font-weight:bold;")
        self.rdo_dec.setStyleSheet("font-size:10px; color:#c62828; font-weight:bold;")
        self._dir_group = QButtonGroup(self)
        self._dir_group.addButton(self.rdo_inc, 1)
        self._dir_group.addButton(self.rdo_dec, 0)
        self.rdo_inc.toggled.connect(self._on_dir_changed)
        dir_lay.addWidget(self.rdo_inc)
        dir_lay.addWidget(self.rdo_dec)
        dir_frame.setFixedWidth(130)
        main_row.addWidget(dir_frame)

        # المبلغ
        self.sp_amount = QDoubleSpinBox()
        self.sp_amount.setRange(0, 999_999_999)
        self.sp_amount.setDecimals(2)
        self.sp_amount.setMinimumHeight(28)
        self.sp_amount.setFixedWidth(110)
        self.sp_amount.valueChanged.connect(self._on_change)
        main_row.addWidget(self.sp_amount)

        # البيان
        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("بيان...")
        self.inp_desc.setMinimumHeight(28)
        main_row.addWidget(self.inp_desc, stretch=2)

        # زر الحذف
        btn_del = QPushButton("✖")
        btn_del.setFixedSize(22, 22)
        btn_del.setStyleSheet(
            "QPushButton { background:transparent; border:none; color:#bbb; font-size:11px; }"
            "QPushButton:hover { color:#e53935; }"
        )
        btn_del.clicked.connect(lambda: self._on_remove(self))
        main_row.addWidget(btn_del)

        lay.addLayout(main_row)

        # صف ربط المستثمر (يظهر فقط لحسابات capital/drawings)
        self._investor_row = QFrame()
        self._investor_row.setStyleSheet(
            "QFrame { background:#fff8e1; border:1px solid #ffe082;"
            "border-radius:4px; margin-top:2px; }"
        )
        inv_lay = QHBoxLayout(self._investor_row)
        inv_lay.setContentsMargins(8, 4, 8, 4)
        inv_lay.setSpacing(8)

        lbl_inv = QLabel("👤  ربط بمستثمر:")
        lbl_inv.setStyleSheet(
            "font-size:10px; font-weight:bold; color:#f57f17;"
            "background:transparent; border:none;"
        )
        lbl_inv.setFixedWidth(95)
        inv_lay.addWidget(lbl_inv)

        self.cmb_investor = QComboBox()
        self.cmb_investor.setMinimumHeight(24)
        self.cmb_investor.setStyleSheet("font-size:11px;")
        self._reload_investors()
        inv_lay.addWidget(self.cmb_investor, stretch=1)

        lbl_hint = QLabel("(اختياري)")
        lbl_hint.setStyleSheet(
            "font-size:9px; color:#aaa; background:transparent; border:none;"
        )
        inv_lay.addWidget(lbl_hint)

        lay.addWidget(self._investor_row)
        self._investor_row.setVisible(False)

        self._update_side_style()

    def _reload_investors(self):
        if self.erp_conn is None:
            return
        try:
            from db.investors_repo import fetch_all_investors
            prev = self.cmb_investor.currentData()
            self.cmb_investor.blockSignals(True)
            self.cmb_investor.clear()
            self.cmb_investor.addItem("— لا يوجد ربط —", None)
            for inv in fetch_all_investors(self.erp_conn):
                self.cmb_investor.addItem(f"👤 {inv['name']}", inv["id"])
            self.cmb_investor.blockSignals(False)
            if prev:
                for i in range(self.cmb_investor.count()):
                    if self.cmb_investor.itemData(i) == prev:
                        self.cmb_investor.setCurrentIndex(i)
                        break
        except Exception:
            pass

    def _get_acc_type(self) -> str | None:
        acc_id = self._acc.current_account_id()
        if not acc_id:
            return None
        acc = fetch_account(self.conn, acc_id)
        return acc["type"] if acc else None

    def _update_side_style(self):
        acc_type = self._get_acc_type()
        is_inc   = self.rdo_inc.isChecked()

        show_investor = acc_type in _INVESTOR_TYPES if acc_type else False
        self._investor_row.setVisible(show_investor)
        if show_investor:
            self._reload_investors()

        if acc_type:
            side = _resolve_side(acc_type, is_inc)
            self._resolved_side = side
            if side == "dr":
                self.setStyleSheet("""
                    QFrame {
                        background: #f4f8ff;
                        border: 1px solid #c5d8f7;
                        border-right: 3px solid #1565c0;
                        border-radius: 6px;
                    }
                """)
            else:
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
            self.setStyleSheet("""
                QFrame {
                    background: #fafbff;
                    border: 1px solid #dde3f0;
                    border-radius: 6px;
                }
            """)

    def _on_acc_changed(self):
        self._update_side_style()
        self._on_change()

    def _on_dir_changed(self):
        self._update_side_style()
        self._on_change()

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

    def get_investor_link(self) -> dict | None:
        if not self._investor_row.isVisible():
            return None
        inv_id = self.cmb_investor.currentData()
        if not inv_id:
            return None
        acc_type = self._get_acc_type()
        return {
            "investor_id": inv_id,
            "acc_type":    acc_type,
            "amount":      self.sp_amount.value(),
        }

    def get_amount(self) -> float:
        return self.sp_amount.value()

    def get_side(self) -> str:
        return self._resolved_side


class _LinesPanel(QFrame):
    """لوحة صفوف القيد: رأس DR/CR + scroll + زر إضافة."""

    def __init__(self, conn, erp_conn, on_balance_changed, parent=None):
        super().__init__(parent)
        self.conn                = conn
        self.erp_conn            = erp_conn
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

        # رأس
        hdr = QFrame()
        hdr.setStyleSheet("background:#f0f4ff; border-radius:7px 7px 0 0;")
        hdr.setFixedHeight(38)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(12, 4, 12, 4)

        lbl = QLabel("📋  صفوف القيد")
        lbl.setStyleSheet(
            "font-weight:bold; font-size:12px; color:#1565c0;"
            "background:transparent; border:none;"
        )
        self.lbl_dr = QLabel("DR: 0.00")
        self.lbl_dr.setStyleSheet(
            "font-weight:bold; color:#1565c0; background:#e3f2fd;"
            "border-radius:4px; padding:2px 8px; font-size:11px; border:none;"
        )
        self.lbl_cr = QLabel("CR: 0.00")
        self.lbl_cr.setStyleSheet(
            "font-weight:bold; color:#c62828; background:#fdecea;"
            "border-radius:4px; padding:2px 8px; font-size:11px; border:none;"
        )
        hl.addWidget(lbl)
        hl.addStretch()
        hl.addWidget(self.lbl_dr)
        hl.addSpacing(8)
        hl.addWidget(self.lbl_cr)
        root.addWidget(hdr)

        # رؤوس الأعمدة
        col_hdr = QWidget()
        col_hdr.setStyleSheet("background:#fafbff;")
        ch_lay = QHBoxLayout(col_hdr)
        ch_lay.setContentsMargins(28, 2, 8, 2)
        ch_lay.setSpacing(6)

        def _ch(text, w=None, stretch=0):
            l = QLabel(text)
            l.setStyleSheet(
                "font-size:9px; color:#888; font-weight:bold;"
                "background:transparent; border:none;"
            )
            if w:
                l.setFixedWidth(w)
            ch_lay.addWidget(l, stretch=stretch)

        _ch("الحساب",  stretch=4)
        _ch("الاتجاه", w=130)
        _ch("المبلغ",  w=110)
        _ch("البيان",  stretch=2)
        _ch("",        w=22)
        root.addWidget(col_hdr)

        # منطقة الصفوف
        self._rows_w   = QWidget()
        self._rows_w.setStyleSheet("background:transparent;")
        self._rows_lay = QVBoxLayout(self._rows_w)
        self._rows_lay.setSpacing(3)
        self._rows_lay.setContentsMargins(6, 6, 6, 6)
        self._rows_lay.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._rows_w)
        scroll.setMinimumHeight(150)
        scroll.setMaximumHeight(380)
        scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")
        root.addWidget(scroll)

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

    def add_line(self) -> _SmartLine:
        line = _SmartLine(
            conn        = self.conn,
            erp_conn    = self.erp_conn,
            on_change   = self._on_line_changed,
            on_remove   = self._remove_line,
            on_move_up  = self._move_up,
            on_move_dn  = self._move_dn,
        )
        self._lines.append(line)
        self._rows_lay.insertWidget(self._rows_lay.count() - 1, line)
        self._refresh_totals()
        return line

    def _remove_line(self, line):
        if len(self._lines) <= 1:
            QMessageBox.information(None, "تنبيه", "لازم يكون في صف واحد على الأقل")
            return
        self._lines.remove(line)
        self._rows_lay.removeWidget(line)
        line.deleteLater()
        self._on_line_changed()

    def _move_up(self, line):
        idx = self._lines.index(line)
        if idx == 0:
            return
        self._lines[idx], self._lines[idx - 1] = self._lines[idx - 1], self._lines[idx]
        self._rebuild_rows()

    def _move_dn(self, line):
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

    def get_total_dr(self) -> float:
        return sum(ln.get_amount() for ln in self._lines if ln.get_side() == "dr")

    def get_total_cr(self) -> float:
        return sum(ln.get_amount() for ln in self._lines if ln.get_side() == "cr")

    def get_all_values(self) -> list:
        return [v for ln in self._lines if (v := ln.get_values()) is not None]

    def get_all_investor_links(self) -> list:
        return [lk for ln in self._lines if (lk := ln.get_investor_link()) is not None]

    def clear_lines(self):
        for ln in list(self._lines):
            self._rows_lay.removeWidget(ln)
            ln.deleteLater()
        self._lines.clear()
        self._refresh_totals()