"""
ui/tabs/accounting/investors/_link_to_entry_panel.py
=====================================================
_LinkToEntryPanel — لوحة ربط مستثمر بقيد محاسبي موجود.

[إصلاح v5]:
  - FormGroup من panels بدل QGroupBox اليدوي
  - _make_btn من panels بدل QPushButton اليدوي
  - spin_field من panels بدل _spin المحلي
  - NotificationBar من panels بدل QMessageBox للنجاح
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit,
    QComboBox,
)
from PyQt5.QtCore import Qt

from services.accounting.investors_service import InvestorsService
from services.accounting.journal_service import JournalService
from ui.widgets.core.events import bus
from ui.widgets.core.conn import DualConnMixin
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.widgets.panels.form_group import FormGroup
from ui.widgets.panels.form_fields import spin_field
from ui.widgets.panels.form_labels import required_label, form_label
from ui.widgets.components.button import make_btn as _make_btn
from ui.widgets.components.notification import NotificationBar
from ui.widgets.forms.inputs import NotesLineEdit
from ui.widgets.dialogs.message import msg_warning
from ui.widgets.core.i18n import tr
from ui.constants import BTN_MIN_HEIGHT, LINK_PANEL_MARGINS, LINK_PANEL_SPACING, LINK_PANEL_INFO_RADIUS, LINK_PANEL_INFO_PAD


class _LinkToEntryPanel(DualConnMixin, WidgetMixin, QWidget):
    def __init__(self, acc_conn, erp_conn, parent=None):
        super().__init__(parent)
        self._init_dual_conn(acc_conn, erp_conn)
        self._init_widget_mixin(lang=False, data=False)
        self._build()
        self._refresh_style()
        bus.company_data_changed.connect(self._on_company_event)

    def _refresh_style(self, *_):
        from ui.theme import _C
        from ui.font import FS_SM
        if hasattr(self, 'lbl_info'):
            self.lbl_info.setStyleSheet(
                f"background:{_C['orange_bg']}; border:1px solid {_C['orange_border']};"
                f"border-radius:{LINK_PANEL_INFO_RADIUS}px; padding:{LINK_PANEL_INFO_PAD}px;"
                f"color:{_C['orange']}; font-size:{FS_SM}px;"
            )

    def _on_company_event(self, company_id: int):
        if self._on_dual_company_event(company_id):
            self._reload_investors()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(*LINK_PANEL_MARGINS)
        root.setSpacing(LINK_PANEL_SPACING)

        self._notif = NotificationBar(show_dismiss=True)
        root.addWidget(self._notif)

        self.lbl_info = QLabel(tr("link_entry_info"))
        self.lbl_info.setWordWrap(True)
        root.addWidget(self.lbl_info)

        grp = FormGroup(tr("link_data_header"))
        form = grp.form

        self.cmb_investor = QComboBox()
        self.cmb_investor.setMinimumHeight(BTN_MIN_HEIGHT)
        self._reload_investors()
        form.addRow(required_label(tr("investors") + ":"), self.cmb_investor)

        self.cmb_move = QComboBox()
        self.cmb_move.addItem(tr("investor_capital_badge") + " (capital)",   "capital")
        self.cmb_move.addItem(tr("investor_drawings_badge") + " (drawings)", "drawings")
        self.cmb_move.setMinimumHeight(BTN_MIN_HEIGHT)
        form.addRow(form_label(tr("move_type_label")), self.cmb_move)

        self.inp_entry_ref = QLineEdit()
        self.inp_entry_ref.setPlaceholderText(tr("entry_ref_placeholder"))
        self.inp_entry_ref.setMinimumHeight(BTN_MIN_HEIGHT)
        form.addRow(required_label(tr("ref_no_label")), self.inp_entry_ref)

        self.sp_amount = spin_field(max_=999_999_999, dec=2)
        form.addRow(required_label(tr("amount") + ":"), self.sp_amount)

        self.inp_notes = NotesLineEdit()
        form.addRow(form_label(tr("notes") + ":"), self.inp_notes)

        root.addWidget(grp)

        btn_link = _make_btn(tr("link_entry_btn"), "danger")
        btn_link.clicked.connect(self._link)
        root.addWidget(btn_link)
        root.addStretch()

    def _reload_investors(self):
        prev = self.cmb_investor.currentData() if self.cmb_investor.count() else None
        self.cmb_investor.blockSignals(True)
        self.cmb_investor.clear()
        try:
            svc = InvestorsService(self._get_erp_conn())
            for inv in svc.list_investors():
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
            msg_warning(self, tr("warning"), tr("investor_not_found"))
            return
        if not ref_no:
            msg_warning(self, tr("warning"), tr("enter_ref_no"))
            return
        if amount <= 0:
            msg_warning(self, tr("warning"), tr("enter_positive_amount"))
            return

        acc = self._get_safe_conn()
        erp = self._get_erp_conn()
        svc_journal = JournalService(acc)

        entry_row = svc_journal.get_entry_by_ref(ref_no)
        if not entry_row:
            msg_warning(self, tr("warning"), tr("entry_not_found").format(ref=ref_no))
            return

        entry_id = entry_row["id"]
        side     = "credit" if move_type == "capital" else "debit"
        line_id  = svc_journal.get_line_id(entry_id, side)

        notes   = self.inp_notes.text().strip() or None
        try:
            svc = InvestorsService(erp, acc_conn=acc)
            svc.link_to_line(inv_id, entry_id, line_id,
                             move_type, amount, notes)
            self.inp_entry_ref.clear()
            self.sp_amount.setValue(0)
            self.inp_notes.clear()
            bus.company_data_changed.emit(self._company_id or 0)
            self._notif.show(tr("link_success"), "success", auto_hide=3000)
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, tr("error"), str(e))