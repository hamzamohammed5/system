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
    QLabel, QComboBox, QLineEdit,
)
from PyQt5.QtCore import Qt, QDate

from services.accounting.investors_service import InvestorsService
from ui.widgets.mixins.form_mixins import EditModeMixin
from ui.widgets.core.events import bus
from ui.widgets.core.conn import DualConnMixin
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.widgets.panels.form_group import FormGroup
from ui.widgets.components.label import ModeLabel
from ui.widgets.components.button import make_btn as _make_btn
from ui.widgets.forms.inputs import NotesLineEdit, DateField, AmountSpinBox
from ui.widgets.core.i18n import tr
from ui.constants import (
    BTN_MIN_HEIGHT, FILTER_COMBO_MIN_H,
    SPACING_LG, SPACING_MD, FORM_GROUP_MARGIN_TOP,
)
from ._helpers import (
    _fill_capital_combo, _fill_asset_combo,
    _post_capital_entry,
)


class _InvestorForm(DualConnMixin, QWidget, WidgetMixin, EditModeMixin):
    def __init__(self, acc_conn, erp_conn, parent=None):
        super().__init__(parent)
        self._init_dual_conn(acc_conn, erp_conn)
        self._init_widget_mixin(lang=False, data=False)

        self._build()
        self._refresh_style()
        self.init_edit_mode(self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode)
        bus.company_data_changed.connect(self._on_company_event)

    def _on_company_event(self, company_id: int):
        if self._on_dual_company_event(company_id):
            self._refresh_account_combos()

    def _refresh_style(self, *_):
        from ui.theme import _C
        from ui.font import FS_XS
        self.lbl_init_preview.setStyleSheet(
            f"color:{_C['investor_capital_text']}; font-size:{FS_XS}px;"
            "background:transparent; border:none;"
        )

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(SPACING_LG, FORM_GROUP_MARGIN_TOP, SPACING_LG, FORM_GROUP_MARGIN_TOP)
        root.setSpacing(SPACING_MD)

        grp = FormGroup(tr("investor_data_header"))

        self.lbl_mode = ModeLabel(add_text=tr("investor_new"), icon="👤")
        grp.add_label_row(self.lbl_mode)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText(tr("investor_name_placeholder"))
        self.inp_name.setMinimumHeight(BTN_MIN_HEIGHT)
        grp.add_row(tr("name") + ":", self.inp_name)

        self.dt_joined = DateField(height=BTN_MIN_HEIGHT)
        grp.add_row(tr("investor_join_date") + ":", self.dt_joined)

        self.inp_notes = NotesLineEdit()
        grp.add_row(tr("notes") + ":", self.inp_notes)

        root.addWidget(grp)

        from ui.theme import _C
        self._initial_grp = FormGroup(tr("initial_capital_header"), accent=_C["investor_capital_text"])

        self.sp_initial = AmountSpinBox(max_=999_999_999, dec=2, height=BTN_MIN_HEIGHT)
        self._initial_grp.add_row(tr("amount_label"), self.sp_initial)

        self.cmb_capital_acc = QComboBox()
        self.cmb_capital_acc.setMinimumHeight(FILTER_COMBO_MIN_H)
        _fill_capital_combo(self.cmb_capital_acc, self._get_safe_conn())
        self._initial_grp.add_row(tr("capital_account_label"), self.cmb_capital_acc)

        self.cmb_asset_acc = QComboBox()
        self.cmb_asset_acc.setMinimumHeight(FILTER_COMBO_MIN_H)
        _fill_asset_combo(self.cmb_asset_acc, self._get_safe_conn())
        self._initial_grp.add_row(tr("deposit_account_label"), self.cmb_asset_acc)

        self.lbl_init_preview = QLabel("─")
        self.lbl_init_preview.setWordWrap(True)
        self.sp_initial.valueChanged.connect(self._update_init_preview)
        self.cmb_capital_acc.currentIndexChanged.connect(self._update_init_preview)
        self.cmb_asset_acc.currentIndexChanged.connect(self._update_init_preview)
        self._initial_grp.add_row(tr("expected_entry_label"), self.lbl_init_preview)

        root.addWidget(self._initial_grp)

        self.btn_add    = _make_btn(tr("add_investor_btn"),  "primary")
        self.btn_save   = _make_btn(tr("btn_save"),          "success")
        self.btn_cancel = _make_btn(tr("btn_cancel"),        "ghost")
        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn.setMinimumHeight(BTN_MIN_HEIGHT)
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
        ast_text = self.cmb_asset_acc.currentText() or tr("assets")
        cap_text = self.cmb_capital_acc.currentText() or tr("capital_account")
        if amount > 0:
            self.lbl_init_preview.setText(
                f"DR {ast_text[:30]} ← {amount:,.2f} {tr('currency_abbr')}\n"
                f"CR {cap_text[:30]} ← {amount:,.2f} {tr('currency_abbr')}"
            )
        else:
            self.lbl_init_preview.setText(tr("enter_amount_preview"))

    def _collect(self):
        name = self.inp_name.text().strip()
        if not name:
            from ui.widgets.dialogs.message import msg_warning
            msg_warning(self, tr("warning"), tr("enter_investor_name"))
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
        svc    = InvestorsService(erp, acc_conn=acc)
        inv_id = svc.add_investor(**data).investor_id
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
                        notes=f"{tr('initial_capital')} — {data['name']}"
                    )
                except Exception as e:
                    from ui.widgets.dialogs.message import msg_warning
                    msg_warning(self, tr("warning"),
                                tr("investor_added_failed_entry").format(error=e))
        self._reset()
        bus.company_data_changed.emit(self._company_id or 0)

    def _save_edit(self):
        data = self._collect()
        if not data:
            return
        InvestorsService(self._get_erp_conn()).update_investor(
            self._editing_id, data["name"],
            notes=data["notes"], joined_at=data["joined_at"])
        self._reset()
        bus.company_data_changed.emit(self._company_id or 0)

    def _cancel(self):
        self._reset()

    def load_for_edit(self, inv_id: int):
        inv = InvestorsService(self._get_erp_conn()).get_investor(inv_id)
        if not inv:
            return
        self.inp_name.setText(inv["name"])
        self.inp_notes.setText(inv["notes"] or "")
        if inv["joined_at"]:
            self.dt_joined.set_date_str(inv["joined_at"])
        self._initial_grp.setVisible(False)
        self.enter_edit_mode(inv_id, f"─── {tr('edit')} {inv['name']} ───")

    def _reset(self):
        self.inp_name.clear()
        self.inp_notes.clear()
        self.dt_joined.setDate(QDate.currentDate())
        self.sp_initial.setValue(0)
        self._initial_grp.setVisible(True)
        self.lbl_init_preview.setText("─")
        self.exit_edit_mode(f"─── {tr('investor_new')} ───")