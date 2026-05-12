"""
ui/tabs/accounting/journal/lines/_lines_panel.py
================================================
_LinesPanel — لوحة صفوف القيد كاملة مع scroll وإضافة/حذف/ترتيب.
"""

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea,
    QMessageBox,
)

from ._smart_line import _SmartLine


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
        col_hdr = QFrame()
        col_hdr.setStyleSheet("background:#fafbff;")
        ch_lay = QHBoxLayout(col_hdr)
        ch_lay.setContentsMargins(28, 2, 8, 2)
        ch_lay.setSpacing(6)

        def _ch(text, w=None, stretch=0):
            lbl2 = QLabel(text)
            lbl2.setStyleSheet(
                "font-size:9px; color:#888; font-weight:bold;"
                "background:transparent; border:none;"
            )
            if w:
                lbl2.setFixedWidth(w)
            ch_lay.addWidget(lbl2, stretch=stretch)

        _ch("الحساب",  stretch=4)
        _ch("الاتجاه", w=130)
        _ch("المبلغ",  w=110)
        _ch("البيان",  stretch=2)
        _ch("",        w=22)
        root.addWidget(col_hdr)

        # منطقة الصفوف
        self._rows_w   = QFrame()
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