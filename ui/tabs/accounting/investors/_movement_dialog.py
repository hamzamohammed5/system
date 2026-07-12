"""
ui/tabs/accounting/investors/_movement_dialog.py
=================================================
_MovementDialog — نافذة إضافة حركة (capital / drawings) لمستثمر.

[إصلاح v5 — توحيد الـ UI]:
  - FormGroup بدل QGroupBox اليدوي.
  - _make_btn بدل QPushButton بستايل inline.
  - DateField بدل QDateEdit اليدوي.
  - AmountSpinBox بدل _spin المحلي.
  - DualConnMixin كما هو.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel,
)
from PyQt5.QtCore import Qt
from ui.widgets.panels.themed_inputs import ThemedComboBox

from ui.widgets.core.events import bus, emit_company_data_changed
from ui.widgets.core.conn import DualConnMixin
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.widgets.panels.form_group import FormGroup
from ui.widgets.components.button import make_btn as _make_btn
from ui.widgets.forms.inputs import NotesLineEdit, DateField, AmountSpinBox
from ui.widgets.core.i18n import tr
from ui.font import FS_MD, FS_SM
from ui.constants import (
    BTN_MIN_HEIGHT, CONFIRM_BTN_MIN_H,
    MOVEMENT_DIALOG_MIN_W, MOVEMENT_DIALOG_SPACING,
    MOVEMENT_DIALOG_MARGINS, MOVEMENT_DIALOG_BTN_H,
    MOVEMENT_DIALOG_TITLE_RADIUS, MOVEMENT_DIALOG_TITLE_PAD_V,
    MOVEMENT_DIALOG_TITLE_PAD_H, MOVEMENT_DIALOG_PREVIEW_RADIUS,
    MOVEMENT_DIALOG_PREVIEW_PAD_V, MOVEMENT_DIALOG_PREVIEW_PAD_H,
)
from ._helpers import (
    _fill_capital_combo, _fill_drawings_combo, _fill_asset_combo,
    _post_capital_entry, _post_drawings_entry,
)


class _MovementDialog(DualConnMixin, WidgetMixin, QDialog):
    def __init__(self, acc_conn, erp_conn,
                 investor_id, investor_name,
                 move_type="capital", parent=None):
        super().__init__(parent)
        self._init_dual_conn(acc_conn, erp_conn)
        self._init_widget_mixin(lang=False, data=False)
        self.investor_id   = investor_id
        self.investor_name = investor_name
        self.move_type     = move_type

        is_cap = move_type == "capital"
        title  = tr("add_capital_title") if is_cap else tr("add_drawings_title")
        self.setWindowTitle(title)
        self._is_cap = is_cap
        self.setMinimumWidth(MOVEMENT_DIALOG_MIN_W)
        self.setModal(True)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build()

    def _refresh_style(self, *_):
        from ui.theme import _C
        if hasattr(self, 'lbl_title'):
            is_cap = self.move_type == "capital"
            color  = _C["investor_capital_text"] if is_cap else _C["investor_drawings_text"]
            bg     = _C["investor_capital_bg"] if is_cap else _C["investor_drawings_bg"]
            self.lbl_title.setStyleSheet(
                f"font-size:{FS_MD}px; font-weight:bold; color:{color};"
                f"background:{bg};"
                f"border-radius:{MOVEMENT_DIALOG_TITLE_RADIUS}px;"
                f"padding:{MOVEMENT_DIALOG_TITLE_PAD_V}px {MOVEMENT_DIALOG_TITLE_PAD_H}px;"
            )
        if hasattr(self, 'lbl_preview'):
            self.lbl_preview.setStyleSheet(
                f"background:{_C['bg_surface_2']};"
                f"border:1px solid {_C['journal_header_border']};"
                f"border-radius:{MOVEMENT_DIALOG_PREVIEW_RADIUS}px;"
                f"padding:{MOVEMENT_DIALOG_PREVIEW_PAD_V}px {MOVEMENT_DIALOG_PREVIEW_PAD_H}px;"
                f"font-size:{FS_SM}px;"
            )
        # [إصلاح dark-mode] btn_ok/btn_cancel و combos مبنية بستايل ثابت
        # وقت الإنشاء. نفس نمط الإصلاح في باقي ملفات investors/.
        from ui.widgets.components.button import refresh_visible_buttons
        refresh_visible_buttons(self)

    def _build(self):
        from ui.theme import _C
        root   = QVBoxLayout(self)
        root.setSpacing(MOVEMENT_DIALOG_SPACING)
        root.setContentsMargins(*MOVEMENT_DIALOG_MARGINS)
        acc    = self._get_safe_conn()
        is_cap = self.move_type == "capital"
        color  = _C["investor_capital_text"] if is_cap else _C["investor_drawings_text"]
        icon   = tr("movement_icon_capital") if is_cap else tr("movement_icon_drawings")
        op_ar  = tr("add_capital_title") if is_cap else tr("add_drawings_title")

        self.lbl_title = QLabel(f"{icon}  {self.investor_name}  —  {op_ar}")
        self._refresh_style()
        root.addWidget(self.lbl_title)

        grp = FormGroup(accent=color)

        self.sp_amount = AmountSpinBox(max_=999_999_999, dec=2, height=30)
        grp.add_row(tr("amount") + f" ({tr('currency')}):", self.sp_amount)

        self.dt_date = DateField(height=30, width=140)
        grp.add_row(tr("date") + ":", self.dt_date)

        self.cmb_equity_acc = ThemedComboBox()
        self.cmb_equity_acc.setMinimumHeight(BTN_MIN_HEIGHT)
        if is_cap:
            _fill_capital_combo(self.cmb_equity_acc, acc)
            grp.add_row(tr("capital_account_row"), self.cmb_equity_acc)
        else:
            _fill_drawings_combo(self.cmb_equity_acc, acc)
            grp.add_row(tr("drawings_account_row"), self.cmb_equity_acc)

        self.cmb_asset_acc = ThemedComboBox()
        self.cmb_asset_acc.setMinimumHeight(BTN_MIN_HEIGHT)
        _fill_asset_combo(self.cmb_asset_acc, acc)
        asset_lbl = tr("deposit_account_row") if is_cap else tr("payment_account_label")
        grp.add_row(asset_lbl, self.cmb_asset_acc)

        self.lbl_preview = QLabel()
        self.lbl_preview.setWordWrap(True)
        self.sp_amount.valueChanged.connect(self._update_preview)
        self.cmb_equity_acc.currentIndexChanged.connect(self._update_preview)
        self.cmb_asset_acc.currentIndexChanged.connect(self._update_preview)
        grp.add_row(tr("expected_entry"), self.lbl_preview)
        self._refresh_style()
        self._update_preview()

        self.inp_notes = NotesLineEdit()
        grp.add_row(tr("notes") + ":", self.inp_notes)

        root.addWidget(grp)

        btn_ok     = _make_btn(tr("record_btn"),  "success" if is_cap else "danger")
        btn_cancel = _make_btn(tr("btn_cancel"),  "ghost")
        btn_ok.setMinimumHeight(MOVEMENT_DIALOG_BTN_H)
        btn_cancel.setMinimumHeight(MOVEMENT_DIALOG_BTN_H)
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
            f"<b>{tr('debit')} (DR):</b>  {dr_acc}  ←  {amount:,.2f} {tr('currency_abbr')}<br>"
            f"<b>{tr('credit')} (CR):</b>  {cr_acc}  ←  {amount:,.2f} {tr('currency_abbr')}"
        )

    def _accept(self):
        amount = self.sp_amount.value()
        if amount <= 0:
            from ui.widgets.dialogs.message import msg_warning
            msg_warning(self, tr("warning"), tr("enter_amount_warning"))
            return
        equity_acc = self.cmb_equity_acc.currentData()
        asset_acc  = self.cmb_asset_acc.currentData()
        if not equity_acc or not asset_acc:
            from ui.widgets.dialogs.message import msg_warning
            msg_warning(self, tr("warning"), tr("select_accounts_warning"))
            return
        date  = self.dt_date.date_str()
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
            emit_company_data_changed()
            self.accept()
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, tr("error"), str(e))