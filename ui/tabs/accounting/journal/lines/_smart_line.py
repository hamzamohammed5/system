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
    QDoubleSpinBox, QComboBox,
    QRadioButton, QButtonGroup,
)
from PyQt5.QtCore import Qt

from db.accounting.accounting_repo import fetch_account, get_normal_balance
from db.accounting.accounting_schema import NORMAL_BALANCE
from ui.events import bus
from ui.widgets.shared.safe_conn_mixin import DualConnMixin
from ui.widgets.shared.company_utils import get_active_company_id
from ..journal_account_picker import _AccountPickerButton

_INVESTOR_TYPES = {"capital", "drawings"}


def _resolve_side(acc_type: str, is_increase: bool) -> str:
    nb = NORMAL_BALANCE.get(acc_type, "dr")
    return nb if is_increase else ("cr" if nb == "dr" else "dr")


class _SmartLine(DualConnMixin, QFrame):
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
        bus.company_data_changed.connect(self._on_company_event)

    def _on_company_event(self, company_id: int):
        if self._on_company_event_safe(company_id):
            self._cached_acc_type = None  # [إصلاح v7] نُبطل الـ cache عند تغيير الشركة
            self._reload_investors()

    def _build(self):
        self.setStyleSheet("""
            QFrame {
                background: #fafbff;
                border: 1px solid #dde3f0;
                border-radius: 6px;
            }
            QFrame:hover { border-color: #90aad4; }
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(4)

        main_row = QHBoxLayout()
        main_row.setSpacing(6)

        self.btn_up = QPushButton("▲")
        self.btn_dn = QPushButton("▼")
        for b in (self.btn_up, self.btn_dn):
            b.setFixedSize(18, 18)
            b.setStyleSheet(
                "QPushButton { background:transparent; border:none; color:#bbb; font-size:8px; }"
                "QPushButton:hover { color:#1565c0; }"
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
        dir_lay.setSpacing(3)
        self.rdo_inc = QRadioButton("زيادة ✚")
        self.rdo_dec = QRadioButton("نقص ✖")
        self.rdo_inc.setChecked(True)
        self.rdo_inc.setStyleSheet("font-size:10px; color:#2e7d32; font-weight:bold;")
        self.rdo_dec.setStyleSheet("font-size:10px; color:#c62828; font-weight:bold;")
        self._dir_group = QButtonGroup(self)
        self._dir_group.addButton(self.rdo_inc, 1)
        self._dir_group.addButton(self.rdo_dec, 0)
        self.rdo_inc.toggled.connect(self._on_dir_changed)
        dir_lay.addWidget(self.rdo_inc)
        dir_lay.addWidget(self.rdo_dec)
        dir_frame.setFixedWidth(130)
        main_row.addWidget(dir_frame)

        self.sp_amount = QDoubleSpinBox()
        self.sp_amount.setRange(0, 999_999_999)
        self.sp_amount.setDecimals(2)
        self.sp_amount.setMinimumHeight(28)
        self.sp_amount.setFixedWidth(110)
        self.sp_amount.valueChanged.connect(self._on_change)
        main_row.addWidget(self.sp_amount)

        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("بيان...")
        self.inp_desc.setMinimumHeight(28)
        main_row.addWidget(self.inp_desc, stretch=2)

        btn_del = QPushButton("✖")
        btn_del.setFixedSize(22, 22)
        btn_del.setStyleSheet(
            "QPushButton { background:transparent; border:none; color:#bbb; font-size:11px; }"
            "QPushButton:hover { color:#e53935; }"
        )
        btn_del.clicked.connect(lambda: self._on_remove(self))
        main_row.addWidget(btn_del)

        lay.addLayout(main_row)

        self._investor_row = QFrame()
        self._investor_row.setStyleSheet(
            "QFrame { background:#fff8e1; border:1px solid #ffe082;"
            "border-radius:4px; margin-top:2px; }"
        )
        inv_lay = QHBoxLayout(self._investor_row)
        inv_lay.setContentsMargins(8, 4, 8, 4)
        inv_lay.setSpacing(8)

        lbl_inv = QLabel("👤  ربط بمستثمر:")
        lbl_inv.setStyleSheet(
            "font-size:10px; font-weight:bold; color:#f57f17;"
            "background:transparent; border:none;"
        )
        lbl_inv.setFixedWidth(95)
        inv_lay.addWidget(lbl_inv)

        self.cmb_investor = QComboBox()
        self.cmb_investor.setMinimumHeight(24)
        self.cmb_investor.setStyleSheet("font-size:11px;")
        self._reload_investors()
        inv_lay.addWidget(self.cmb_investor, stretch=1)

        lbl_hint = QLabel("(اختياري)")
        lbl_hint.setStyleSheet(
            "font-size:9px; color:#aaa; background:transparent; border:none;"
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
            from db.inventory.investors_repo import fetch_all_investors
            prev = self.cmb_investor.currentData()
            self.cmb_investor.blockSignals(True)
            self.cmb_investor.clear()
            self.cmb_investor.addItem("— لا يوجد ربط —", None)
            for inv in fetch_all_investors(erp):
                self.cmb_investor.addItem(f"👤 {inv['name']}", inv["id"])
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
                self.setStyleSheet("""
                    QFrame {
                        background: #f4f8ff;
                        border: 1px solid #c5d8f7;
                        border-right: 3px solid #1565c0;
                        border-radius: 6px;
                    }
                """)
            else:
                self.setStyleSheet("""
                    QFrame {
                        background: #fff4f4;
                        border: 1px solid #f7c5c5;
                        border-right: 3px solid #c62828;
                        border-radius: 6px;
                    }
                """)
        else:
            self._resolved_side = "dr"
            self.setStyleSheet("""
                QFrame {
                    background: #fafbff;
                    border: 1px solid #dde3f0;
                    border-radius: 6px;
                }
            """)

    def _on_acc_changed(self):
        """
        [إصلاح v7] نستدعي fetch_account() هنا مرة واحدة فقط
        ونخزن الـ type في _cached_acc_type.
        _update_side_style() و get_values() يقرآن من الـ cache.
        """
        acc_id = self._acc.current_account_id()
        if acc_id:
            acc = fetch_account(self._get_safe_conn(), acc_id)
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