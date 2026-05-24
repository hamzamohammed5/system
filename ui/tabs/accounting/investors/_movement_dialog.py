"""
ui/tabs/accounting/investors/_movement_dialog.py
=================================================
_MovementDialog — نافذة إضافة حركة (capital / drawings) لمستثمر.

[إصلاح v4 — DualConnMixin]:
  - DualConnMixin بدل _get_erp_conn() المكرر يدوياً.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QGroupBox, QPushButton,
    QLineEdit, QComboBox, QDateEdit, QMessageBox,
)
from PyQt5.QtCore import Qt, QDate

from ui.events import bus
from ui.widgets.shared.safe_conn_mixin import DualConnMixin
from ._helpers import (
    _spin, _fill_capital_combo, _fill_drawings_combo, _fill_asset_combo,
    _post_capital_entry, _post_drawings_entry,
)


class _MovementDialog(DualConnMixin, QDialog):
    def __init__(self, acc_conn, erp_conn,
                 investor_id, investor_name,
                 move_type="capital", parent=None):
        super().__init__(parent)
        self._init_dual_conn(acc_conn, erp_conn)
        self.investor_id   = investor_id
        self.investor_name = investor_name
        self.move_type     = move_type

        is_cap = move_type == "capital"
        title  = "💰  إضافة رأس مال" if is_cap else "💸  تسجيل مسحوبات"
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        self.setModal(True)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build()

    def _build(self):
        root   = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(20, 16, 20, 16)
        acc    = self._get_safe_conn()
        is_cap = self.move_type == "capital"
        color  = "#2e7d32" if is_cap else "#c62828"
        bg     = "#f1f8e9" if is_cap else "#fdecea"
        icon   = "💰" if is_cap else "💸"
        op_ar  = "إضافة رأس مال" if is_cap else "مسحوبات"

        lbl_title = QLabel(f"{icon}  {self.investor_name}  —  {op_ar}")
        lbl_title.setStyleSheet(
            f"font-size:13px; font-weight:bold; color:{color};"
            f"background:{bg}; border-radius:6px; padding:8px 14px;"
        )
        root.addWidget(lbl_title)

        grp  = QGroupBox()
        grp.setStyleSheet(
            "QGroupBox { border:1px solid #e0e0e0; border-radius:8px; padding-top:10px; }"
        )
        form = QFormLayout(grp)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        self.sp_amount = _spin()
        form.addRow("المبلغ (جنيه):", self.sp_amount)

        self.dt_date = QDateEdit(QDate.currentDate())
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDisplayFormat("yyyy-MM-dd")
        self.dt_date.setFixedWidth(140)
        self.dt_date.setMinimumHeight(30)
        form.addRow("التاريخ:", self.dt_date)

        self.cmb_equity_acc = QComboBox()
        self.cmb_equity_acc.setMinimumHeight(30)
        if is_cap:
            _fill_capital_combo(self.cmb_equity_acc, acc)
            form.addRow("حساب رأس المال:", self.cmb_equity_acc)
        else:
            _fill_drawings_combo(self.cmb_equity_acc, acc)
            form.addRow("حساب المسحوبات:", self.cmb_equity_acc)

        self.cmb_asset_acc = QComboBox()
        self.cmb_asset_acc.setMinimumHeight(30)
        _fill_asset_combo(self.cmb_asset_acc, acc)
        asset_lbl = "حساب الإيداع (أصل):" if is_cap else "حساب الصرف (أصل):"
        form.addRow(asset_lbl, self.cmb_asset_acc)

        self.lbl_preview = QLabel()
        self.lbl_preview.setStyleSheet(
            "background:#f8f9ff; border:1px solid #c5cae9; border-radius:6px;"
            "padding:8px 12px; font-size:11px; color:#333;"
        )
        self.lbl_preview.setWordWrap(True)
        self.sp_amount.valueChanged.connect(self._update_preview)
        self.cmb_equity_acc.currentIndexChanged.connect(self._update_preview)
        self.cmb_asset_acc.currentIndexChanged.connect(self._update_preview)
        form.addRow("القيد المتوقع:", self.lbl_preview)
        self._update_preview()

        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("ملاحظات اختيارية...")
        self.inp_notes.setMinimumHeight(28)
        form.addRow("ملاحظات:", self.inp_notes)

        root.addWidget(grp)

        btn_ok     = QPushButton("✅  تسجيل")
        btn_cancel = QPushButton("✖  إلغاء")
        btn_ok.setMinimumHeight(34)
        btn_cancel.setMinimumHeight(34)
        btn_ok.setStyleSheet(f"""
            QPushButton {{
                background: {color}; color: white;
                font-weight: bold; border-radius: 6px; padding: 0 20px;
            }}
            QPushButton:hover {{ background: {'#1b5e20' if is_cap else '#b71c1c'}; }}
        """)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: #f5f5f5; color: #555;
                border: 1px solid #ddd; border-radius: 6px; padding: 0 14px;
            }
        """)
        btn_ok.clicked.connect(self._accept)
        btn_cancel.clicked.connect(self.reject)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        root.addLayout(btn_row)

    def _update_preview(self):
        is_cap   = self.move_type == "capital"
        amount   = self.sp_amount.value()
        eq_text  = self.cmb_equity_acc.currentText() or "—"
        ast_text = self.cmb_asset_acc.currentText() or "—"
        dr_acc   = ast_text if is_cap else eq_text
        cr_acc   = eq_text  if is_cap else ast_text
        self.lbl_preview.setText(
            f"<b>مدين (DR):</b>  {dr_acc}  ←  {amount:,.2f} ج<br>"
            f"<b>دائن (CR):</b>  {cr_acc}  ←  {amount:,.2f} ج"
        )

    def _accept(self):
        amount = self.sp_amount.value()
        if amount <= 0:
            QMessageBox.warning(self, "تنبيه", "أدخل مبلغاً أكبر من صفر")
            return
        equity_acc = self.cmb_equity_acc.currentData()
        asset_acc  = self.cmb_asset_acc.currentData()
        if not equity_acc or not asset_acc:
            QMessageBox.warning(self, "تنبيه", "اختر الحسابات المطلوبة")
            return
        date  = self.dt_date.date().toString("yyyy-MM-dd")
        notes = self.inp_notes.text().strip() or None
        acc = self._get_safe_conn()
        erp = self._get_erp_conn()
        try:
            if self.move_type == "capital":
                _post_capital_entry(
                    acc, erp,
                    self.investor_id, self.investor_name,
                    equity_acc, asset_acc, amount, date, notes
                )
            else:
                _post_drawings_entry(
                    acc, erp,
                    self.investor_id, self.investor_name,
                    equity_acc, asset_acc, amount, date, notes
                )
            if self._company_id is not None:
                bus.company_data_changed.emit(self._company_id)
            else:
                bus.data_changed.emit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))
