"""
ui/tabs/accounting/ledger/ledger_t_account.py
==============================================
_TAccountPanel — لوحة حساب T في دفتر الأستاذ.

[إصلاح v4 — توحيد الـ UI]:
  - PageHeader بدل lbl_title اليدوي.
  - BalanceDisplay بدل lbl_balance اليدوي.
  - الباقي كما هو (conn isolation من v3).
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor, QFont

from services.accounting.journal_service import JournalService
from services.accounting.accounts_service import AccountsService
from ui.tabs.accounting.helpers import TYPE_COLORS
from ui.widgets.components.headers_page import PageHeader
from ui.widgets.components.amount_label  import BalanceDisplay
from ui.widgets.core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.font import FS_BASE, FS_SM
from ui.constants import (
    T_ACCOUNT_COL_DATE_W, T_ACCOUNT_COL_REF_W, T_ACCOUNT_COL_AMT_W,
    T_ACCOUNT_FRAME_RADIUS, T_ACCOUNT_FRAME_BORDER_W,
    T_ACCOUNT_HDR_RADIUS, T_ACCOUNT_HDR_PAD, T_ACCOUNT_HDR_BORDER_W,
    T_ACCOUNT_TOT_RADIUS, T_ACCOUNT_TOT_PAD_V, T_ACCOUNT_TOT_PAD_H,
    T_ACCOUNT_DR_MARGIN, T_ACCOUNT_CR_MARGIN, T_ACCOUNT_SIDE_SPACING,
    T_ACCOUNT_ROOT_SPACING, T_ACCOUNT_SEP_W, T_ACCOUNT_HDR_CELL_PAD,
    MARGIN_ZERO, SPACING_ZERO,
)
from .ledger_filter_bar import _LedgerFilterBar
from .ledger_stat_cards import _StatCards


class _TAccountPanel(QWidget, WidgetMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_data = None
        self._init_widget_mixin(lang=False, data=False)
        self._build()

    def _refresh_style(self, *_):
        from ui.theme import _C
        if not hasattr(self, '_t_frame'):
            return
        self._t_frame.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_surface']};
                border: {T_ACCOUNT_FRAME_BORDER_W}px solid {_C['t_account_frame']};
                border-radius: {T_ACCOUNT_FRAME_RADIUS}px;
            }}
        """)
        self._dr_hdr.setStyleSheet(f"""
            font-weight: bold; color: {_C['acc_type_asset']}; font-size: {FS_BASE}px;
            background: {_C['t_account_dr_bg']}; border-radius: {T_ACCOUNT_HDR_RADIUS}px; padding: {T_ACCOUNT_HDR_PAD}px;
        """)
        self._cr_hdr.setStyleSheet(f"""
            font-weight: bold; color: {_C['acc_type_liability']}; font-size: {FS_BASE}px;
            background: {_C['t_account_cr_bg']}; border-radius: {T_ACCOUNT_HDR_RADIUS}px; padding: {T_ACCOUNT_HDR_PAD}px;
        """)
        self.lbl_dr_total.setStyleSheet(f"""
            font-weight: bold; color: {_C['acc_type_asset']}; font-size: {FS_SM}px;
            background: {_C['t_account_dr_bg']}; border-radius: {T_ACCOUNT_TOT_RADIUS}px; padding: {T_ACCOUNT_TOT_PAD_V}px {T_ACCOUNT_TOT_PAD_H}px;
        """)
        self.lbl_cr_total.setStyleSheet(f"""
            font-weight: bold; color: {_C['acc_type_liability']}; font-size: {FS_SM}px;
            background: {_C['t_account_cr_bg']}; border-radius: {T_ACCOUNT_TOT_RADIUS}px; padding: {T_ACCOUNT_TOT_PAD_V}px {T_ACCOUNT_TOT_PAD_H}px;
        """)
        self._sep.setStyleSheet(f"color: {_C['acc_type_asset']}; background: {_C['t_account_frame']};")
        self.t_dr_table.setStyleSheet(f"""
            QTableWidget {{ border: none; background: transparent; gridline-color: {_C['table_gridline']}; }}
            QHeaderView::section {{
                background: {_C['row_alt_bg']}; border: none;
                border-bottom: {T_ACCOUNT_HDR_BORDER_W}px solid {_C['border_subtle']};
                padding: {T_ACCOUNT_HDR_CELL_PAD}px; font-weight: bold; font-size: {FS_SM}px; color: {_C['text_neutral']};
            }}
        """)
        self.t_cr_table.setStyleSheet(self.t_dr_table.styleSheet())

    def _build(self):
        from ui.theme import _C
        root = QVBoxLayout(self)
        root.setContentsMargins(*MARGIN_ZERO)
        root.setSpacing(T_ACCOUNT_ROOT_SPACING)

        # ── هيدر الحساب (بدل lbl_title اليدوي) ──
        self._page_hdr = PageHeader(
            title=tr("ledger_select_account_prompt"),
            icon="📒",
            accent=_C["acc_type_asset"],
            compact=True,
        )
        root.addWidget(self._page_hdr)

        self._stats = _StatCards()
        root.addWidget(self._stats)

        self._filter = _LedgerFilterBar()
        self._filter.inp_search.textChanged.connect(self._apply_filter)
        self._filter.cmb_move_type.currentIndexChanged.connect(self._apply_filter)
        self._filter.dt_from.dateChanged.connect(self._apply_filter)
        self._filter.dt_to.dateChanged.connect(self._apply_filter)
        orig_reset = self._filter.reset

        def _reset_and_apply():
            orig_reset()
            self._apply_filter()

        self._filter.reset = _reset_and_apply
        root.addWidget(self._filter)

        self._t_frame = QFrame()
        self._t_frame.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_surface']};
                border: {T_ACCOUNT_FRAME_BORDER_W}px solid {_C['t_account_frame']};
                border-radius: {T_ACCOUNT_FRAME_RADIUS}px;
            }}
        """)
        t_lay = QHBoxLayout(self._t_frame)
        t_lay.setContentsMargins(*MARGIN_ZERO)
        t_lay.setSpacing(SPACING_ZERO)

        # جانب المدين
        dr_widget = QWidget()
        dr_widget.setStyleSheet("background: transparent;")
        dr_lay = QVBoxLayout(dr_widget)
        dr_lay.setContentsMargins(*T_ACCOUNT_DR_MARGIN)
        dr_lay.setSpacing(T_ACCOUNT_SIDE_SPACING)

        self._dr_hdr = QLabel(tr("t_account_dr_header"))
        self._dr_hdr.setAlignment(Qt.AlignCenter)
        self._dr_hdr.setStyleSheet(f"""
            font-weight: bold; color: {_C['acc_type_asset']}; font-size: {FS_BASE}px;
            background: {_C['t_account_dr_bg']}; border-radius: {T_ACCOUNT_HDR_RADIUS}px; padding: {T_ACCOUNT_HDR_PAD}px;
        """)
        dr_lay.addWidget(self._dr_hdr)
        self.t_dr_table = self._make_t_table()
        dr_lay.addWidget(self.t_dr_table, stretch=1)

        self.lbl_dr_total = QLabel(tr("t_account_total", label=tr("total"), amount="0.00"))
        self.lbl_dr_total.setAlignment(Qt.AlignCenter)
        self.lbl_dr_total.setStyleSheet(f"""
            font-weight: bold; color: {_C['acc_type_asset']}; font-size: {FS_SM}px;
            background: {_C['t_account_dr_bg']}; border-radius: {T_ACCOUNT_TOT_RADIUS}px; padding: {T_ACCOUNT_TOT_PAD_V}px {T_ACCOUNT_TOT_PAD_H}px;
        """)
        dr_lay.addWidget(self.lbl_dr_total)

        self._sep = QFrame()
        self._sep.setFrameShape(QFrame.VLine)
        self._sep.setStyleSheet(f"color: {_C['acc_type_asset']}; background: {_C['t_account_frame']};")
        self._sep.setFixedWidth(T_ACCOUNT_SEP_W)

        # جانب الدائن
        cr_widget = QWidget()
        cr_widget.setStyleSheet("background: transparent;")
        cr_lay = QVBoxLayout(cr_widget)
        cr_lay.setContentsMargins(*T_ACCOUNT_CR_MARGIN)
        cr_lay.setSpacing(T_ACCOUNT_SIDE_SPACING)

        self._cr_hdr = QLabel(tr("t_account_cr_header"))
        self._cr_hdr.setAlignment(Qt.AlignCenter)
        self._cr_hdr.setStyleSheet(f"""
            font-weight: bold; color: {_C['acc_type_liability']}; font-size: {FS_BASE}px;
            background: {_C['t_account_cr_bg']}; border-radius: {T_ACCOUNT_HDR_RADIUS}px; padding: {T_ACCOUNT_HDR_PAD}px;
        """)
        cr_lay.addWidget(self._cr_hdr)
        self.t_cr_table = self._make_t_table()
        cr_lay.addWidget(self.t_cr_table, stretch=1)

        self.lbl_cr_total = QLabel(tr("t_account_total", label=tr("total"), amount="0.00"))
        self.lbl_cr_total.setAlignment(Qt.AlignCenter)
        self.lbl_cr_total.setStyleSheet(f"""
            font-weight: bold; color: {_C['acc_type_liability']}; font-size: {FS_SM}px;
            background: {_C['t_account_cr_bg']}; border-radius: {T_ACCOUNT_TOT_RADIUS}px; padding: {T_ACCOUNT_TOT_PAD_V}px {T_ACCOUNT_TOT_PAD_H}px;
        """)
        cr_lay.addWidget(self.lbl_cr_total)

        t_lay.addWidget(dr_widget, stretch=1)
        t_lay.addWidget(self._sep)
        t_lay.addWidget(cr_widget, stretch=1)
        root.addWidget(self._t_frame, stretch=1)

        # ── رصيد الحساب (بدل lbl_balance اليدوي) ──
        self._balance_disp = BalanceDisplay()
        root.addWidget(self._balance_disp)

    def _make_t_table(self) -> QTableWidget:
        from ui.theme import _C
        tbl = QTableWidget()
        tbl.setColumnCount(4)
        tbl.setHorizontalHeaderLabels([tr("date"), tr("entry_no_col"), tr("lines_col_desc"), tr("amount")])
        tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tbl.setAlternatingRowColors(True)

        hh = tbl.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Interactive)
        hh.setSectionResizeMode(1, QHeaderView.Interactive)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.Interactive)
        tbl.setColumnWidth(0, T_ACCOUNT_COL_DATE_W)
        tbl.setColumnWidth(1, T_ACCOUNT_COL_REF_W)
        tbl.setColumnWidth(3, T_ACCOUNT_COL_AMT_W)

        tbl.setStyleSheet(f"""
            QTableWidget {{ border: none; background: transparent; gridline-color: {_C['table_gridline']}; }}
            QHeaderView::section {{
                background: {_C['row_alt_bg']}; border: none;
                border-bottom: {T_ACCOUNT_HDR_BORDER_W}px solid {_C['border_subtle']};
                padding: {T_ACCOUNT_HDR_CELL_PAD}px; font-weight: bold; font-size: {FS_SM}px; color: {_C['text_neutral']};
            }}
        """)
        tbl.verticalHeader().setVisible(False)
        tbl.setShowGrid(True)
        return tbl

    def load(self, conn, account_id: int):
        from ui.theme import _C
        self._conn = conn
        data = JournalService(conn).get_t_account(account_id)
        if not data:
            return
        self._all_data = data

        acc = data["account"]
        nb  = data["normal_balance"]

        type_ar  = AccountsService(conn).get_type_labels_map().get(acc["type"], "")
        color    = TYPE_COLORS.get(acc["type"], _C["acc_type_asset"])
        nb_ar    = tr("ledger_nb_short_dr") if nb == "dr" else tr("ledger_nb_short_cr")

        # تحديث PageHeader بدل lbl_title
        self._page_hdr.set_title(
            tr("t_account_summary", code=acc["code"], name=acc["name"], type=type_ar, nb=nb_ar)
        )
        self._apply_filter()

    def _apply_filter(self):
        if not self._all_data:
            return

        from ui.theme import _C
        data    = self._all_data
        lines   = data["lines"]
        acc     = data["account"]
        nb      = data["normal_balance"]

        filtered = [ln for ln in lines if self._filter.matches(ln)]

        self.t_dr_table.setRowCount(0)
        self.t_cr_table.setRowCount(0)

        filt_dr = filt_cr = 0.0

        for line in filtered:
            if line["debit"] > 0:
                r = self.t_dr_table.rowCount()
                self.t_dr_table.insertRow(r)
                self._fill_t_row(self.t_dr_table, r, line, line["debit"], _C["acc_type_asset"])
                filt_dr += line["debit"]

            if line["credit"] > 0:
                r = self.t_cr_table.rowCount()
                self.t_cr_table.insertRow(r)
                self._fill_t_row(self.t_cr_table, r, line, line["credit"], _C["acc_type_liability"])
                filt_cr += line["credit"]

        self.lbl_dr_total.setText(tr("t_account_total", label=tr("total"), amount=f"{filt_dr:,.2f}"))
        self.lbl_cr_total.setText(tr("t_account_total", label=tr("total"), amount=f"{filt_cr:,.2f}"))

        # BalanceDisplay بدل lbl_balance اليدوي
        self._balance_disp.set_debit_credit_balance(filt_dr, filt_cr)

        total_count = len(lines)
        filt_count  = len(filtered)
        filt_bal    = filt_dr - filt_cr
        self._stats.update(
            self._conn, filt_dr, filt_cr, filt_bal,
            filt_count, nb, acc["type"]
        )
        self._filter.set_count(filt_count, total_count)

    def _fill_t_row(self, tbl: QTableWidget, r: int, line: dict,
                    amount: float, color: str):
        from ui.theme import _C
        date_item = QTableWidgetItem(line.get("date", "—"))
        date_item.setTextAlignment(Qt.AlignCenter)
        date_item.setForeground(QColor(_C["text_neutral"]))
        tbl.setItem(r, 0, date_item)

        ref_item = QTableWidgetItem(line.get("ref_no", "—"))
        ref_item.setTextAlignment(Qt.AlignCenter)
        ref_item.setForeground(QColor(_C["acc_type_asset"]))
        tbl.setItem(r, 1, ref_item)

        desc = line.get("description") or line.get("entry_desc") or "—"
        desc_item = QTableWidgetItem(desc)
        desc_item.setToolTip(f"{line.get('date','—')}  {desc}")
        tbl.setItem(r, 2, desc_item)

        amt_item = QTableWidgetItem(f"{amount:,.2f}")
        amt_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        amt_item.setForeground(QColor(color))
        f = QFont()
        f.setBold(True)
        amt_item.setFont(f)
        tbl.setItem(r, 3, amt_item)

    def clear(self):
        self._all_data = None
        self.t_dr_table.setRowCount(0)
        self.t_cr_table.setRowCount(0)
        self.lbl_dr_total.setText(tr("t_account_total", label=tr("total"), amount="0.00"))
        self.lbl_cr_total.setText(tr("t_account_total", label=tr("total"), amount="0.00"))
        self._balance_disp.reset()
        self._stats.clear()
        self._page_hdr.set_title(tr("ledger_select_account_prompt"))