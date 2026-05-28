"""
ui/tabs/accounting/investors/_investor_form.py
==============================================
_InvestorForm — فورم إضافة / تعديل مستثمر مع رأس المال الأولي.

[إصلاح v5 — توحيد الـ UI]:
  - FormGroup بدل QGroupBox اليدوي.
  - ModeLabel بدل lbl_mode اليدوي.
  - DateField بدل QDateEdit اليدوي.
  - _make_btn بدل QPushButton اليدوي.
  - DualConnMixin كما هو.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QLabel, QComboBox, QLineEdit, QMessageBox,
)
from PyQt5.QtCore import Qt, QDate

from db.accounting.investors_repo import (
    fetch_investor, insert_investor, update_investor,
)
from ui.helpers import EditModeMixin
from ui.events  import bus
from ui.widgets.shared.safe_conn_mixin import DualConnMixin
from ui.widgets.shared.panels import (
    FormGroup,
    ModeLabel,
    _make_btn,
    NotesLineEdit,
)
from ui.widgets.shared.input_widgets import DateField, AmountSpinBox
from ._helpers import (
    _fill_capital_combo, _fill_asset_combo,
    _post_capital_entry,
)


class _InvestorForm(DualConnMixin, QWidget, EditModeMixin):
    def __init__(self, acc_conn, erp_conn, parent=None):
        super().__init__(parent)
        self._init_dual_conn(acc_conn, erp_conn)

        self._build()
        self.init_edit_mode(self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode)
        bus.company_data_changed.connect(self._on_company_event)

    def _on_company_event(self, company_id: int):
        if self._on_dual_company_event(company_id):
            self._refresh_account_combos()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        # ── فورم بيانات المستثمر (FormGroup بدل QGroupBox) ──
        grp = FormGroup("بيانات المستثمر")

        self.lbl_mode = ModeLabel(add_text="مستثمر جديد", icon="👤")
        grp.add_label_row(self.lbl_mode)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم المستثمر...")
        self.inp_name.setMinimumHeight(30)
        grp.add_row("الاسم:", self.inp_name)

        self.dt_joined = DateField(height=30)
        grp.add_row("تاريخ الانضمام:", self.dt_joined)

        self.inp_notes = NotesLineEdit()
        grp.add_row("ملاحظات:", self.inp_notes)

        root.addWidget(grp)

        # ── رأس المال الأولي ──
        self._initial_grp = FormGroup("💰  رأس المال الأولي (اختياري)", accent="#2e7d32")

        self.sp_initial = AmountSpinBox(max_=999_999_999, dec=2, height=30)
        self._initial_grp.add_row("المبلغ:", self.sp_initial)

        self.cmb_capital_acc = QComboBox()
        self.cmb_capital_acc.setMinimumHeight(28)
        _fill_capital_combo(self.cmb_capital_acc, self._get_safe_conn())
        self._initial_grp.add_row("حساب رأس المال:", self.cmb_capital_acc)

        self.cmb_asset_acc = QComboBox()
        self.cmb_asset_acc.setMinimumHeight(28)
        _fill_asset_combo(self.cmb_asset_acc, self._get_safe_conn())
        self._initial_grp.add_row("حساب الإيداع:", self.cmb_asset_acc)

        self.lbl_init_preview = QLabel("─")
        self.lbl_init_preview.setStyleSheet(
            "color:#2e7d32; font-size:10px; background:transparent; border:none;"
        )
        self.lbl_init_preview.setWordWrap(True)
        self.sp_initial.valueChanged.connect(self._update_init_preview)
        self.cmb_capital_acc.currentIndexChanged.connect(self._update_init_preview)
        self.cmb_asset_acc.currentIndexChanged.connect(self._update_init_preview)
        self._initial_grp.add_row("القيد:", self.lbl_init_preview)

        root.addWidget(self._initial_grp)

        # ── أزرار (بدل QPushButton اليدوي) ──
        self.btn_add    = _make_btn("➕  إضافة مستثمر", "primary")
        self.btn_save   = _make_btn("💾  حفظ التعديل",  "success")
        self.btn_cancel = _make_btn("✖  إلغاء",         "ghost")
        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn.setMinimumHeight(30)
        self.btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save_edit)
        self.btn_cancel.clicked.connect(self._cancel)

        btn_w = QWidget()
        bl    = QHBoxLayout(btn_w)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.addWidget(self.btn_add)
        bl.addWidget(self.btn_save)
        bl.addWidget(self.btn_cancel)
        bl.addStretch()
        root.addWidget(btn_w)
        root.addStretch()

    def _refresh_account_combos(self):
        conn       = self._get_safe_conn()
        prev_cap   = self.cmb_capital_acc.currentData()
        prev_asset = self.cmb_asset_acc.currentData()
        _fill_capital_combo(self.cmb_capital_acc, conn, prev_cap)
        _fill_asset_combo(self.cmb_asset_acc, conn, prev_asset)
        self._update_init_preview()

    def _update_init_preview(self):
        amount   = self.sp_initial.value()
        ast_text = self.cmb_asset_acc.currentText() or "الأصل"
        cap_text = self.cmb_capital_acc.currentText() or "رأس المال"
        if amount > 0:
            self.lbl_init_preview.setText(
                f"DR {ast_text[:30]} ← {amount:,.2f} ج\n"
                f"CR {cap_text[:30]} ← {amount:,.2f} ج"
            )
        else:
            self.lbl_init_preview.setText("─ أدخل مبلغاً لعرض القيد")

    def _collect(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم المستثمر")
            return None
        return {
            "name":      name,
            "joined_at": self.dt_joined.date_str(),
            "notes":     self.inp_notes.text().strip() or None,
        }

    def _add(self):
        data = self._collect()
        if not data:
            return
        erp    = self._get_erp_conn()
        acc    = self._get_safe_conn()
        inv_id = insert_investor(erp, **data)
        amount = self.sp_initial.value()
        if amount > 0:
            cap_acc   = self.cmb_capital_acc.currentData()
            asset_acc = self.cmb_asset_acc.currentData()
            if cap_acc and asset_acc:
                try:
                    _post_capital_entry(
                        acc, erp,
                        inv_id, data["name"],
                        cap_acc, asset_acc, amount,
                        data["joined_at"],
                        notes=f"رأس المال الأولي — {data['name']}"
                    )
                except Exception as e:
                    QMessageBox.warning(self, "تنبيه",
                                        f"تم إضافة المستثمر لكن فشل القيد:\n{e}")
        self._reset()
        bus.company_data_changed.emit(self._company_id or 0)

    def _save_edit(self):
        data = self._collect()
        if not data:
            return
        update_investor(self._get_erp_conn(), self._editing_id,
                        data["name"], data["notes"], data["joined_at"])
        self._reset()
        bus.company_data_changed.emit(self._company_id or 0)

    def _cancel(self):
        self._reset()

    def load_for_edit(self, inv_id: int):
        inv = fetch_investor(self._get_erp_conn(), inv_id)
        if not inv:
            return
        self.inp_name.setText(inv["name"])
        self.inp_notes.setText(inv["notes"] or "")
        if inv["joined_at"]:
            self.dt_joined.set_date_str(inv["joined_at"])
        self._initial_grp.setVisible(False)
        self.enter_edit_mode(inv_id, f"─── تعديل: {inv['name']} ───")

    def _reset(self):
        self.inp_name.clear()
        self.inp_notes.clear()
        self.dt_joined.setDate(QDate.currentDate())
        self.sp_initial.setValue(0)
        self._initial_grp.setVisible(True)
        self.lbl_init_preview.setText("─")
        self.exit_edit_mode("─── مستثمر جديد ───")