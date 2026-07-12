"""
ui/tabs/accounting/journal/lines/_smart_line.py
================================================
_SmartLine — صف قيد واحد ذكي (حساب + اتجاه + مبلغ + بيان + ربط مستثمر).

[إصلاح v6]:
  - DualConnMixin بدل _get_erp_conn() المكرر يدوياً.
  - get_active_company_id() من company_utils بدل الدالة المحلية.

[إصلاح v7]:
  - _cached_acc_type: يُخزَّن عند اختيار الحساب ويُستخدم في
    _get_acc_type() و _update_side_style() بدل استدعاء fetch_account() مرتين.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QLabel, QLineEdit, QPushButton,
    QDoubleSpinBox,
    QRadioButton, QButtonGroup,
)
from PyQt5.QtCore import Qt
from ui.widgets.panels.themed_inputs import ThemedComboBox

from services.accounting.accounts_service import AccountsService
from ui.widgets.core.events import bus, get_active_company_id
from ui.widgets.core.conn import DualConnMixin
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.font import FS_XS, FS_SM, FS_BASE
from ui.constants import (
    SMART_LINE_BORDER_RADIUS,
    SMART_LINE_BORDER_W,
    SMART_LINE_MARGIN_H,
    SMART_LINE_MARGIN_V,
    SMART_LINE_SPACING,
    SMART_LINE_MAIN_ROW_SPACING,
    SMART_LINE_MOVE_BTN_SIZE,
    SMART_LINE_DIR_FRAME_W,
    SMART_LINE_DIR_SPACING,
    SMART_LINE_AMOUNT_MIN_H,
    SMART_LINE_AMOUNT_W,
    SMART_LINE_AMOUNT_MAX,
    SMART_LINE_AMOUNT_DECIMALS,
    SMART_LINE_DESC_MIN_H,
    SMART_LINE_DEL_BTN_SIZE,
    SMART_LINE_INV_ROW_RADIUS,
    SMART_LINE_INV_ROW_BORDER_W,
    SMART_LINE_INV_MARGIN_H,
    SMART_LINE_INV_MARGIN_V,
    SMART_LINE_INV_SPACING,
    SMART_LINE_INV_LBL_W,
    SMART_LINE_INV_CMB_MIN_H,
    SMART_LINE_ACCENT_BORDER_W,
    SMART_LINE_INV_ROW_MARGIN_T,
)
from ..account_picker._account_picker_button import _AccountPickerButton

_INVESTOR_TYPES = {"capital", "drawings"}


def _resolve_side(acc_type: str, is_increase: bool) -> str:
    nb = AccountsService(None).get_normal_balance(acc_type)
    return nb if is_increase else ("cr" if nb == "dr" else "dr")


class _SmartLine(DualConnMixin, QFrame, WidgetMixin):
    """صف قيد واحد: حساب + زيادة/نقص + مبلغ + بيان + ربط مستثمر اختياري."""

    def __init__(self, conn, erp_conn, on_change, on_remove,
                 on_move_up, on_move_dn, parent=None):
        super().__init__(parent)
        self._init_dual_conn(conn, erp_conn)
        self._on_change       = on_change
        self._on_remove       = on_remove
        self._on_move_up      = on_move_up
        self._on_move_dn      = on_move_dn
        self._resolved_side   = "dr"
        self._cached_acc_type = None   # [إصلاح v7] cache بدل fetch مزدوج
        self._company_id      = get_active_company_id()

        self._build()
        self._init_widget_mixin(lang=False, data=False)
        bus.company_data_changed.connect(self._on_company_event)

    def _on_company_event(self, company_id: int):
        if self._on_company_event_safe(company_id):
            self._cached_acc_type = None  # [إصلاح v7] نُبطل الـ cache عند تغيير الشركة
            self._reload_investors()

    def _build(self):
        self.setStyleSheet(f"""
            QFrame {{
                background: {_C['journal_neutral_bg']};
                border: {SMART_LINE_BORDER_W}px solid {_C['journal_neutral_border']};
                border-radius: {SMART_LINE_BORDER_RADIUS}px;
            }}
            QFrame:hover {{ border-color: {_C['border_med']}; }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(SMART_LINE_MARGIN_H, SMART_LINE_MARGIN_V,
                               SMART_LINE_MARGIN_H, SMART_LINE_MARGIN_V)
        lay.setSpacing(SMART_LINE_SPACING)

        main_row = QHBoxLayout()
        main_row.setSpacing(SMART_LINE_MAIN_ROW_SPACING)

        self.btn_up = QPushButton("▲")
        self.btn_dn = QPushButton("▼")
        for b in (self.btn_up, self.btn_dn):
            b.setFixedSize(SMART_LINE_MOVE_BTN_SIZE, SMART_LINE_MOVE_BTN_SIZE)
            b.setStyleSheet(
                f"QPushButton {{ background:transparent; border:none; color:{_C['text_disabled']}; font-size:{FS_XS}px; }}"
                f"QPushButton:hover {{ color:{_C['accent']}; }}"
            )
        self.btn_up.clicked.connect(lambda: self._on_move_up(self))
        self.btn_dn.clicked.connect(lambda: self._on_move_dn(self))
        ord_col = QVBoxLayout()
        ord_col.setSpacing(0)
        ord_col.setContentsMargins(0, 0, 0, 0)
        ord_col.addWidget(self.btn_up)
        ord_col.addWidget(self.btn_dn)
        main_row.addLayout(ord_col)

        self._acc = _AccountPickerButton(self._get_safe_conn())
        self._acc.set_on_changed(self._on_acc_changed)
        main_row.addWidget(self._acc, stretch=4)

        dir_frame = QFrame()
        dir_frame.setStyleSheet("QFrame { background:transparent; border:none; }")
        dir_lay = QHBoxLayout(dir_frame)
        dir_lay.setContentsMargins(0, 0, 0, 0)
        dir_lay.setSpacing(SMART_LINE_DIR_SPACING)
        self.rdo_inc = QRadioButton(tr("journal_increase"))
        self.rdo_dec = QRadioButton(tr("journal_decrease"))
        self.rdo_inc.setChecked(True)
        self.rdo_inc.setStyleSheet(f"font-size:{FS_XS}px; color:{_C['investor_capital_text']}; font-weight:bold;")
        self.rdo_dec.setStyleSheet(f"font-size:{FS_XS}px; color:{_C['journal_cr_accent']}; font-weight:bold;")
        self._dir_group = QButtonGroup(self)
        self._dir_group.addButton(self.rdo_inc, 1)
        self._dir_group.addButton(self.rdo_dec, 0)
        self.rdo_inc.toggled.connect(self._on_dir_changed)
        dir_lay.addWidget(self.rdo_inc)
        dir_lay.addWidget(self.rdo_dec)
        dir_frame.setFixedWidth(SMART_LINE_DIR_FRAME_W)
        main_row.addWidget(dir_frame)

        self.sp_amount = QDoubleSpinBox()
        self.sp_amount.setRange(0, SMART_LINE_AMOUNT_MAX)
        self.sp_amount.setDecimals(SMART_LINE_AMOUNT_DECIMALS)
        self.sp_amount.setMinimumHeight(SMART_LINE_AMOUNT_MIN_H)
        self.sp_amount.setFixedWidth(SMART_LINE_AMOUNT_W)
        self.sp_amount.valueChanged.connect(self._on_change)
        main_row.addWidget(self.sp_amount)

        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText(tr("line_description_placeholder"))
        self.inp_desc.setMinimumHeight(SMART_LINE_DESC_MIN_H)
        main_row.addWidget(self.inp_desc, stretch=2)

        btn_del = QPushButton("✖")
        btn_del.setFixedSize(SMART_LINE_DEL_BTN_SIZE, SMART_LINE_DEL_BTN_SIZE)
        btn_del.setStyleSheet(
            f"QPushButton {{ background:transparent; border:none; color:{_C['text_disabled']}; font-size:{FS_SM}px; }}"
            f"QPushButton:hover {{ color:{_C['danger']}; }}"
        )
        btn_del.clicked.connect(lambda: self._on_remove(self))
        main_row.addWidget(btn_del)

        lay.addLayout(main_row)

        self._investor_row = QFrame()
        self._investor_row.setStyleSheet(
            f"QFrame {{ background:{_C['investor_link_bg']}; border:{SMART_LINE_INV_ROW_BORDER_W}px solid {_C['investor_link_border']};"
            f"border-radius:{SMART_LINE_INV_ROW_RADIUS}px; margin-top:{SMART_LINE_INV_ROW_MARGIN_T}px; }}"
        )
        inv_lay = QHBoxLayout(self._investor_row)
        inv_lay.setContentsMargins(SMART_LINE_INV_MARGIN_H, SMART_LINE_INV_MARGIN_V,
                                   SMART_LINE_INV_MARGIN_H, SMART_LINE_INV_MARGIN_V)
        inv_lay.setSpacing(SMART_LINE_INV_SPACING)

        lbl_inv = QLabel(tr("link_investor_to_entry"))
        lbl_inv.setStyleSheet(
            f"font-size:{FS_XS}px; font-weight:bold; color:{_C['investor_link_text']};"
            "background:transparent; border:none;"
        )
        lbl_inv.setFixedWidth(SMART_LINE_INV_LBL_W)
        inv_lay.addWidget(lbl_inv)

        self.cmb_investor = ThemedComboBox()
        self.cmb_investor.setMinimumHeight(SMART_LINE_INV_CMB_MIN_H)
        self.cmb_investor.setStyleSheet(f"font-size:{FS_SM}px;")
        self._reload_investors()
        inv_lay.addWidget(self.cmb_investor, stretch=1)

        lbl_hint = QLabel(tr("investor_link_optional"))
        lbl_hint.setStyleSheet(
            f"font-size:{FS_XS}px; color:{_C['text_disabled']}; background:transparent; border:none;"
        )
        inv_lay.addWidget(lbl_hint)

        lay.addWidget(self._investor_row)
        self._investor_row.setVisible(False)

        self._update_side_style()

    def _reload_investors(self):
        erp = self._get_erp_conn()
        if erp is None:
            return
        try:
            from services.accounting.investors_service import InvestorsService
            prev = self.cmb_investor.currentData()
            self.cmb_investor.blockSignals(True)
            self.cmb_investor.clear()
            self.cmb_investor.addItem(tr("filter_all"), None)
            for inv in InvestorsService(erp).list_investors():
                self.cmb_investor.addItem(f"{tr('investor_icon')} {inv['name']}", inv["id"])
            self.cmb_investor.blockSignals(False)
            if prev:
                for i in range(self.cmb_investor.count()):
                    if self.cmb_investor.itemData(i) == prev:
                        self.cmb_investor.setCurrentIndex(i)
                        break
        except Exception:
            pass

    def _get_acc_type(self) -> str | None:
        """
        [إصلاح v7] يرجع من الـ cache إن كان موجوداً.
        يُحدَّث الـ cache فقط في _on_acc_changed().
        """
        return self._cached_acc_type

    def _update_side_style(self):
        acc_type = self._cached_acc_type  # [إصلاح v7] من الـ cache مباشرة
        is_inc   = self.rdo_inc.isChecked()

        show_investor = acc_type in _INVESTOR_TYPES if acc_type else False
        self._investor_row.setVisible(show_investor)
        if show_investor:
            self._reload_investors()

        if acc_type:
            side = _resolve_side(acc_type, is_inc)
            self._resolved_side = side
            if side == "dr":
                self.setStyleSheet(f"""
                    QFrame {{
                        background: {_C['journal_dr_bg']};
                        border: {SMART_LINE_BORDER_W}px solid {_C['journal_dr_border']};
                        border-right: {SMART_LINE_ACCENT_BORDER_W}px solid {_C['journal_dr_accent']};
                        border-radius: {SMART_LINE_BORDER_RADIUS}px;
                    }}
                """)
            else:
                self.setStyleSheet(f"""
                    QFrame {{
                        background: {_C['journal_cr_bg']};
                        border: {SMART_LINE_BORDER_W}px solid {_C['journal_cr_border']};
                        border-right: {SMART_LINE_ACCENT_BORDER_W}px solid {_C['journal_cr_accent']};
                        border-radius: {SMART_LINE_BORDER_RADIUS}px;
                    }}
                """)
        else:
            self._resolved_side = "dr"
            self.setStyleSheet(f"""
                QFrame {{
                    background: {_C['journal_neutral_bg']};
                    border: {SMART_LINE_BORDER_W}px solid {_C['journal_neutral_border']};
                    border-radius: {SMART_LINE_BORDER_RADIUS}px;
                }}
            """)

    def _refresh_style(self, *_):
        self._update_side_style()

    def _on_acc_changed(self):
        """
        [إصلاح v7] نستدعي fetch_account() هنا مرة واحدة فقط
        ونخزن الـ type في _cached_acc_type.
        _update_side_style() و get_values() يقرآن من الـ cache.
        """
        acc_id = self._acc.current_account_id()
        if acc_id:
            acc = AccountsService(self._get_safe_conn()).get_account(acc_id)
            self._cached_acc_type = acc["type"] if acc else None
        else:
            self._cached_acc_type = None
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
        return {
            "investor_id": inv_id,
            "acc_type":    self._cached_acc_type,  # [إصلاح v7] من الـ cache
            "amount":      self.sp_amount.value(),
        }

    def get_amount(self) -> float:
        return self.sp_amount.value()

    def get_side(self) -> str:
        return self._resolved_side