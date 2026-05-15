"""
ui/tabs/accounting/investors/_link_to_entry_panel.py
=====================================================
_LinkToEntryPanel — لوحة ربط مستثمر بقيد محاسبي موجود.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton,
    QComboBox, QMessageBox,
)
from PyQt5.QtCore import Qt

from db.inventory.investors_repo import fetch_all_investors, link_investor_to_line
from ui.events import bus
from ._helpers import _spin


class _LinkToEntryPanel(QWidget):
    def __init__(self, acc_conn, erp_conn, parent=None):
        super().__init__(parent)
        self.acc_conn = acc_conn
        self.erp_conn = erp_conn
        self._build()
        bus.data_changed.connect(self._reload_investors)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(10)

        lbl_info = QLabel(
            "🔗  ربط قيد محاسبي موجود بمستثمر\n"
            "استخدم هذا لو أضفت القيد يدوياً في تبويب القيود وتريد نسبته لمستثمر."
        )
        lbl_info.setStyleSheet(
            "background:#fff3e0; border:1px solid #ffcc80; border-radius:6px;"
            "padding:10px; color:#e65100; font-size:11px;"
        )
        lbl_info.setWordWrap(True)
        root.addWidget(lbl_info)

        grp = QGroupBox("بيانات الربط")
        grp.setStyleSheet(
            "QGroupBox { border:1px solid #e0e0e0; border-radius:8px;"
            "margin-top:8px; padding-top:8px; font-weight:bold; }"
        )
        form = QFormLayout(grp)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.cmb_investor = QComboBox()
        self.cmb_investor.setMinimumHeight(30)
        self._reload_investors()
        form.addRow("المستثمر:", self.cmb_investor)

        self.cmb_move = QComboBox()
        self.cmb_move.addItem("💰  رأس مال (capital)", "capital")
        self.cmb_move.addItem("💸  مسحوبات (drawings)", "drawings")
        self.cmb_move.setMinimumHeight(30)
        form.addRow("نوع الحركة:", self.cmb_move)

        self.inp_entry_ref = QLineEdit()
        self.inp_entry_ref.setPlaceholderText("مثال: JE-00012")
        self.inp_entry_ref.setMinimumHeight(30)
        form.addRow("رقم القيد:", self.inp_entry_ref)

        self.sp_amount = _spin()
        form.addRow("المبلغ:", self.sp_amount)

        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("ملاحظات...")
        self.inp_notes.setMinimumHeight(28)
        form.addRow("ملاحظات:", self.inp_notes)

        root.addWidget(grp)

        btn_link = QPushButton("🔗  ربط")
        btn_link.setMinimumHeight(34)
        btn_link.setStyleSheet("""
            QPushButton {
                background: #e65100; color: white;
                font-weight: bold; border-radius: 6px; padding: 0 20px;
            }
            QPushButton:hover { background: #bf360c; }
        """)
        btn_link.clicked.connect(self._link)
        root.addWidget(btn_link)
        root.addStretch()

    def _reload_investors(self):
        prev = self.cmb_investor.currentData() if self.cmb_investor.count() else None
        self.cmb_investor.blockSignals(True)
        self.cmb_investor.clear()
        for inv in fetch_all_investors(self.erp_conn):
            self.cmb_investor.addItem(inv["name"], inv["id"])
        self.cmb_investor.blockSignals(False)
        if prev:
            for i in range(self.cmb_investor.count()):
                if self.cmb_investor.itemData(i) == prev:
                    self.cmb_investor.setCurrentIndex(i)
                    break

    def _link(self):
        inv_id    = self.cmb_investor.currentData()
        move_type = self.cmb_move.currentData()
        ref_no    = self.inp_entry_ref.text().strip()
        amount    = self.sp_amount.value()

        if not inv_id:
            QMessageBox.warning(self, "تنبيه", "اختر المستثمر")
            return
        if not ref_no:
            QMessageBox.warning(self, "تنبيه", "أدخل رقم القيد")
            return
        if amount <= 0:
            QMessageBox.warning(self, "تنبيه", "أدخل مبلغاً أكبر من صفر")
            return

        entry_row = self.acc_conn.execute(
            "SELECT id FROM journal_entries WHERE ref_no=?", (ref_no,)
        ).fetchone()
        if not entry_row:
            QMessageBox.warning(self, "تنبيه", f"لم يُعثر على قيد برقم «{ref_no}»")
            return

        entry_id = entry_row["id"]
        if move_type == "capital":
            line_row = self.acc_conn.execute(
                "SELECT id FROM journal_lines WHERE entry_id=? AND credit>0 LIMIT 1",
                (entry_id,)
            ).fetchone()
        else:
            line_row = self.acc_conn.execute(
                "SELECT id FROM journal_lines WHERE entry_id=? AND debit>0 LIMIT 1",
                (entry_id,)
            ).fetchone()
        line_id = line_row["id"] if line_row else 0
        notes   = self.inp_notes.text().strip() or None
        try:
            link_investor_to_line(
                self.erp_conn, inv_id, entry_id, line_id,
                move_type, amount, notes
            )
            self.inp_entry_ref.clear()
            self.sp_amount.setValue(0)
            self.inp_notes.clear()
            bus.data_changed.emit()
            QMessageBox.information(self, "تم", "✅ تم ربط القيد بالمستثمر بنجاح")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))