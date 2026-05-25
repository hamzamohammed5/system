"""
ui/tabs/accounting/investors/_link_to_entry_panel.py
=====================================================
_LinkToEntryPanel — لوحة ربط مستثمر بقيد محاسبي موجود.

[إصلاح v5]:
  - FormGroup من panels بدل QGroupBox اليدوي
  - _make_btn من panels بدل QPushButton اليدوي
  - spin_field من panels بدل _spin المحلي
  - NotificationBar من panels بدل QMessageBox للنجاح

[إصلاح v6]:
  - fetch_entry_by_ref() و fetch_capital/drawings_line_for_entry()
    من repo_ui_helpers بدل SQL مباشر.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit,
    QComboBox, QMessageBox,
)
from PyQt5.QtCore import Qt

from db.inventory.investors_repo import fetch_all_investors, link_investor_to_line
from db.accounting.accounting_repo_ui_helpers import (
    fetch_entry_by_ref,
    fetch_capital_line_for_entry,
    fetch_drawings_line_for_entry,
)
from ui.events import bus
from ui.widgets.shared.safe_conn_mixin import DualConnMixin
from ui.widgets.shared.panels import (
    FormGroup,
    spin_field,
    _make_btn,
    NotificationBar,
    make_form_layout,
    required_label,
    form_label,
    NotesLineEdit,
)


class _LinkToEntryPanel(DualConnMixin, QWidget):
    def __init__(self, acc_conn, erp_conn, parent=None):
        super().__init__(parent)
        self._init_dual_conn(acc_conn, erp_conn)
        self._build()
        bus.company_data_changed.connect(self._on_company_event)

    def _on_company_event(self, company_id: int):
        if self._on_dual_company_event(company_id):
            self._reload_investors()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(10)

        self._notif = NotificationBar(show_dismiss=True)
        root.addWidget(self._notif)

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

        grp  = FormGroup("بيانات الربط")
        form = grp.form

        self.cmb_investor = QComboBox()
        self.cmb_investor.setMinimumHeight(30)
        self._reload_investors()
        form.addRow(required_label("المستثمر:"), self.cmb_investor)

        self.cmb_move = QComboBox()
        self.cmb_move.addItem("💰  رأس مال (capital)", "capital")
        self.cmb_move.addItem("💸  مسحوبات (drawings)", "drawings")
        self.cmb_move.setMinimumHeight(30)
        form.addRow(form_label("نوع الحركة:"), self.cmb_move)

        self.inp_entry_ref = QLineEdit()
        self.inp_entry_ref.setPlaceholderText("مثال: JE-00012")
        self.inp_entry_ref.setMinimumHeight(30)
        form.addRow(required_label("رقم القيد:"), self.inp_entry_ref)

        self.sp_amount = spin_field(max_=999_999_999, dec=2)
        form.addRow(required_label("المبلغ:"), self.sp_amount)

        self.inp_notes = NotesLineEdit()
        form.addRow(form_label("ملاحظات:"), self.inp_notes)

        root.addWidget(grp)

        btn_link = _make_btn("🔗  ربط", "danger")
        btn_link.clicked.connect(self._link)
        root.addWidget(btn_link)
        root.addStretch()

    def _reload_investors(self):
        prev = self.cmb_investor.currentData() if self.cmb_investor.count() else None
        self.cmb_investor.blockSignals(True)
        self.cmb_investor.clear()
        try:
            for inv in fetch_all_investors(self._get_erp_conn()):
                self.cmb_investor.addItem(inv["name"], inv["id"])
        except Exception:
            pass
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

        acc = self._get_safe_conn()
        erp = self._get_erp_conn()

        # [إصلاح v6] fetch_entry_by_ref بدل SQL مباشر
        entry_row = fetch_entry_by_ref(acc, ref_no)
        if not entry_row:
            QMessageBox.warning(self, "تنبيه", f"لم يُعثر على قيد برقم «{ref_no}»")
            return

        entry_id = entry_row["id"]
        # [إصلاح v6] دوال repo بدل SQL مباشر
        if move_type == "capital":
            line_id = fetch_capital_line_for_entry(acc, entry_id)
        else:
            line_id = fetch_drawings_line_for_entry(acc, entry_id)

        notes = self.inp_notes.text().strip() or None
        try:
            link_investor_to_line(erp, inv_id, entry_id, line_id,
                                  move_type, amount, notes)
            self.inp_entry_ref.clear()
            self.sp_amount.setValue(0)
            self.inp_notes.clear()
            bus.company_data_changed.emit(self._company_id or 0)
            self._notif.show("✅ تم ربط القيد بالمستثمر بنجاح", "success", auto_hide=3000)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))