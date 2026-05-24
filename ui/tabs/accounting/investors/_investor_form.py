"""
ui/tabs/accounting/investors/_investor_form.py
==============================================
_InvestorForm — فورم إضافة / تعديل مستثمر مع رأس المال الأولي.

تغييرات (v3 — SafeConnMixin):
  - SafeConnMixin على acc_conn.
  - _get_erp_conn() بدل self.erp_conn الثابت.
  - يستمع لـ bus.company_data_changed مع فلترة company_id.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QFrame, QGroupBox, QPushButton,
    QLineEdit, QComboBox, QDateEdit, QMessageBox,
)
from PyQt5.QtCore import Qt, QDate

from db.inventory.investors_repo import (
    fetch_investor, insert_investor, update_investor,
)
from ui.helpers import EditModeMixin
from ui.events  import bus
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
from ._helpers  import (
    _spin, _fill_capital_combo, _fill_asset_combo,
    _post_capital_entry,
)


class _InvestorForm(SafeConnMixin, QWidget, EditModeMixin):
    def __init__(self, acc_conn, erp_conn, parent=None):
        super().__init__(parent)
        self._init_safe_conn(acc_conn, "accounting")
        self._erp_conn_ref = erp_conn
        self._company_id   = self._get_company_id()

        self._build()
        self.init_edit_mode(self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode)
        bus.company_data_changed.connect(self._on_company_event)

    def _on_company_event(self, company_id: int):
        if self._on_company_event_safe(company_id):
            self._refresh_account_combos()

    def _get_erp_conn(self):
        try:
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

        grp = QGroupBox("بيانات المستثمر")
        grp.setStyleSheet("""
            QGroupBox { font-weight:bold; color:#1565c0; border:1px solid #e0e0e0;
                        border-radius:8px; margin-top:8px; padding-top:8px; }
            QGroupBox::title { subcontrol-origin:margin; padding:0 6px; }
        """)
        form = QFormLayout(grp)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = QLabel("─── مستثمر جديد ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0;")
        form.addRow(self.lbl_mode)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم المستثمر...")
        self.inp_name.setMinimumHeight(30)

        self.dt_joined = QDateEdit(QDate.currentDate())
        self.dt_joined.setCalendarPopup(True)
        self.dt_joined.setDisplayFormat("yyyy-MM-dd")
        self.dt_joined.setFixedWidth(140)
        self.dt_joined.setMinimumHeight(30)

        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("ملاحظات...")
        self.inp_notes.setMinimumHeight(28)

        form.addRow("الاسم:", self.inp_name)
        form.addRow("تاريخ الانضمام:", self.dt_joined)
        form.addRow("ملاحظات:", self.inp_notes)

        # ── رأس المال الأولي ──
        self._initial_frame = QFrame()
        self._initial_frame.setStyleSheet(
            "QFrame { background:#f1f8e9; border:1px solid #c8e6c9;"
            "border-radius:6px; padding:4px; }"
        )
        init_lay = QFormLayout(self._initial_frame)
        init_lay.setSpacing(8)
        init_lay.setLabelAlignment(Qt.AlignRight)

        lbl_init = QLabel("💰  رأس المال الأولي (اختياري)")
        lbl_init.setStyleSheet(
            "font-weight:bold; color:#2e7d32; background:transparent; border:none;"
        )
        init_lay.addRow(lbl_init)

        self.sp_initial = _spin()
        self.sp_initial.setValue(0)
        init_lay.addRow("المبلغ:", self.sp_initial)

        self.cmb_capital_acc = QComboBox()
        self.cmb_capital_acc.setMinimumHeight(28)
        _fill_capital_combo(self.cmb_capital_acc, self._get_safe_conn())
        init_lay.addRow("حساب رأس المال:", self.cmb_capital_acc)

        self.cmb_asset_acc = QComboBox()
        self.cmb_asset_acc.setMinimumHeight(28)
        _fill_asset_combo(self.cmb_asset_acc, self._get_safe_conn())
        init_lay.addRow("حساب الإيداع:", self.cmb_asset_acc)

        self.lbl_init_preview = QLabel("─")
        self.lbl_init_preview.setStyleSheet(
            "color:#2e7d32; font-size:10px; background:transparent; border:none;"
        )
        self.lbl_init_preview.setWordWrap(True)
        self.sp_initial.valueChanged.connect(self._update_init_preview)
        self.cmb_capital_acc.currentIndexChanged.connect(self._update_init_preview)
        self.cmb_asset_acc.currentIndexChanged.connect(self._update_init_preview)
        init_lay.addRow("القيد:", self.lbl_init_preview)

        form.addRow(self._initial_frame)
        root.addWidget(grp)

        self.btn_add    = QPushButton("➕  إضافة مستثمر")
        self.btn_save   = QPushButton("💾  حفظ التعديل")
        self.btn_cancel = QPushButton("✖  إلغاء")
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
            "joined_at": self.dt_joined.date().toString("yyyy-MM-dd"),
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
            self.dt_joined.setDate(QDate.fromString(inv["joined_at"], "yyyy-MM-dd"))
        self._initial_frame.setVisible(False)
        self.enter_edit_mode(inv_id, f"─── تعديل: {inv['name']} ───")

    def _reset(self):
        self.inp_name.clear()
        self.inp_notes.clear()
        self.dt_joined.setDate(QDate.currentDate())
        self.sp_initial.setValue(0)
        self._initial_frame.setVisible(True)
        self.lbl_init_preview.setText("─")
        self.exit_edit_mode("─── مستثمر جديد ───")