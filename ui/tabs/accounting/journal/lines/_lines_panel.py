"""
ui/tabs/accounting/journal/lines/_lines_panel.py
================================================
_LinesPanel — لوحة صفوف القيد كاملة مع scroll وإضافة/حذف/ترتيب.

[إصلاح v4 — DualConnMixin]:
  - DualConnMixin بدل _get_erp_conn() المكرر يدوياً.
  - add_line() تمرر _get_erp_conn() حي لكل _SmartLine جديدة.
"""

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea,
    QMessageBox,
)

from ui.widgets.core.conn import DualConnMixin
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.font import FS_XS, FS_SM, FS_BASE
from ui.constants import (
    LINES_PANEL_BORDER_W,
    LINES_PANEL_BORDER_RADIUS,
    LINES_PANEL_HDR_H,
    LINES_PANEL_HDR_BORDER_RADIUS,
    LINES_PANEL_HDR_MARGIN_H,
    LINES_PANEL_HDR_MARGIN_V,
    LINES_PANEL_BADGE_RADIUS,
    LINES_PANEL_BADGE_PAD_V,
    LINES_PANEL_BADGE_PAD_H,
    LINES_PANEL_HDR_SPACING,
    LINES_PANEL_COL_HDR_MARGIN_L,
    LINES_PANEL_COL_HDR_MARGIN_R,
    LINES_PANEL_COL_HDR_MARGIN_V,
    LINES_PANEL_COL_HDR_SPACING,
    LINES_PANEL_ROWS_SPACING,
    LINES_PANEL_ROWS_MARGIN,
    LINES_PANEL_SCROLL_MIN_H,
    LINES_PANEL_SCROLL_MAX_H,
    LINES_PANEL_BTN_ADD_MIN_H,
    LINES_PANEL_BTN_ADD_RADIUS,
    LINES_PANEL_BTN_ADD_BORDER_W,
    LINES_PANEL_BTN_ADD_PAD_V,
    LINES_PANEL_BTN_ADD_PAD_H,
    LINES_PANEL_BTN_ADD_MARGIN_V,
    LINES_PANEL_BTN_ADD_MARGIN_H,
)
from ._smart_line import _SmartLine


class _LinesPanel(DualConnMixin, QFrame, WidgetMixin):
    """لوحة صفوف القيد: رأس DR/CR + scroll + زر إضافة."""

    def __init__(self, conn, erp_conn, on_balance_changed, parent=None):
        super().__init__(parent)
        self._init_dual_conn(conn, erp_conn)
        self._on_balance_changed = on_balance_changed
        self._lines: list[_SmartLine] = []
        self._build()
        self._init_widget_mixin(lang=False, data=False)

    def _build(self):
        self.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_surface']};
                border: {LINES_PANEL_BORDER_W}px solid {_C['border']};
                border-radius: {LINES_PANEL_BORDER_RADIUS}px;
            }}
        """)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # رأس
        hdr = QFrame()
        hdr.setStyleSheet(f"background:{_C['journal_header_bg']}; border-radius:{LINES_PANEL_HDR_BORDER_RADIUS};")
        hdr.setFixedHeight(LINES_PANEL_HDR_H)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(LINES_PANEL_HDR_MARGIN_H, LINES_PANEL_HDR_MARGIN_V,
                              LINES_PANEL_HDR_MARGIN_H, LINES_PANEL_HDR_MARGIN_V)

        lbl = QLabel(tr("journal_lines_title"))
        lbl.setStyleSheet(
            f"font-weight:bold; font-size:{FS_BASE}px; color:{_C['accent']};"
            "background:transparent; border:none;"
        )
        self.lbl_dr = QLabel(tr("journal_dr_total", amount="0.00"))
        self.lbl_dr.setStyleSheet(
            f"font-weight:bold; color:{_C['journal_dr_accent']}; background:{_C['badge_dr_bg']};"
            f"border-radius:{LINES_PANEL_BADGE_RADIUS}px; padding:{LINES_PANEL_BADGE_PAD_V}px {LINES_PANEL_BADGE_PAD_H}px; font-size:{FS_SM}px; border:none;"
        )
        self.lbl_cr = QLabel(tr("journal_cr_total", amount="0.00"))
        self.lbl_cr.setStyleSheet(
            f"font-weight:bold; color:{_C['journal_cr_accent']}; background:{_C['badge_cr_bg']};"
            f"border-radius:{LINES_PANEL_BADGE_RADIUS}px; padding:{LINES_PANEL_BADGE_PAD_V}px {LINES_PANEL_BADGE_PAD_H}px; font-size:{FS_SM}px; border:none;"
        )
        hl.addWidget(lbl)
        hl.addStretch()
        hl.addWidget(self.lbl_dr)
        hl.addSpacing(LINES_PANEL_HDR_SPACING)
        hl.addWidget(self.lbl_cr)
        root.addWidget(hdr)

        # رؤوس الأعمدة
        col_hdr = QFrame()
        col_hdr.setStyleSheet(f"background:{_C['bg_surface_2']};")
        ch_lay = QHBoxLayout(col_hdr)
        ch_lay.setContentsMargins(LINES_PANEL_COL_HDR_MARGIN_L, LINES_PANEL_COL_HDR_MARGIN_V,
                                  LINES_PANEL_COL_HDR_MARGIN_R, LINES_PANEL_COL_HDR_MARGIN_V)
        ch_lay.setSpacing(LINES_PANEL_COL_HDR_SPACING)

        def _ch(text, w=None, stretch=0):
            lbl2 = QLabel(text)
            lbl2.setStyleSheet(
                f"font-size:{FS_XS}px; color:{_C['text_sec']}; font-weight:bold;"
                "background:transparent; border:none;"
            )
            if w:
                lbl2.setFixedWidth(w)
            ch_lay.addWidget(lbl2, stretch=stretch)

        _ch(tr("lines_col_account"),  stretch=4)
        _ch(tr("lines_col_direction"), w=130)
        _ch(tr("lines_col_amount"),   w=110)
        _ch(tr("lines_col_desc"),     stretch=2)
        _ch("",        w=22)
        root.addWidget(col_hdr)

        # منطقة الصفوف
        self._rows_w   = QFrame()
        self._rows_w.setStyleSheet("background:transparent;")
        self._rows_lay = QVBoxLayout(self._rows_w)
        self._rows_lay.setSpacing(LINES_PANEL_ROWS_SPACING)
        self._rows_lay.setContentsMargins(LINES_PANEL_ROWS_MARGIN, LINES_PANEL_ROWS_MARGIN,
                                          LINES_PANEL_ROWS_MARGIN, LINES_PANEL_ROWS_MARGIN)
        self._rows_lay.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._rows_w)
        scroll.setMinimumHeight(LINES_PANEL_SCROLL_MIN_H)
        scroll.setMaximumHeight(LINES_PANEL_SCROLL_MAX_H)
        scroll.setStyleSheet(f"QScrollArea {{ border:none; background:{_C['bg_surface']}; }}")
        root.addWidget(scroll)

        btn_add = QPushButton(tr("add_journal_line"))
        btn_add.setMinimumHeight(LINES_PANEL_BTN_ADD_MIN_H)
        btn_add.setStyleSheet(f"""
            QPushButton {{
                background: {_C['journal_header_bg']}; color: {_C['accent']};
                border: {LINES_PANEL_BTN_ADD_BORDER_W}px solid {_C['journal_header_border']}; border-radius: {LINES_PANEL_BTN_ADD_RADIUS}px;
                font-weight: bold; padding: {LINES_PANEL_BTN_ADD_PAD_V}px {LINES_PANEL_BTN_ADD_PAD_H}px; margin: {LINES_PANEL_BTN_ADD_MARGIN_V}px {LINES_PANEL_BTN_ADD_MARGIN_H}px;
            }}
            QPushButton:hover {{ background: {_C['accent']}; color: {_C['accent_text']}; }}
        """)
        btn_add.clicked.connect(self.add_line)
        root.addWidget(btn_add)

    def _refresh_style(self, *_):
        from ui.theme import _C
        self.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_surface']};
                border: {LINES_PANEL_BORDER_W}px solid {_C['border']};
                border-radius: {LINES_PANEL_BORDER_RADIUS}px;
            }}
        """)

    def add_line(self) -> _SmartLine:
        line = _SmartLine(
            conn        = self._get_safe_conn(),
            erp_conn    = self._get_erp_conn(),
            on_change   = self._on_line_changed,
            on_remove   = self._remove_line,
            on_move_up  = self._move_up,
            on_move_dn  = self._move_dn,
        )
        self._lines.append(line)
        self._rows_lay.insertWidget(self._rows_lay.count() - 1, line)
        self._refresh_totals()
        return line

    def _remove_line(self, line):
        if len(self._lines) <= 1:
            from ui.widgets.dialogs.message import msg_info
            msg_info(None, tr("warning"), tr("min_one_row_required"))
            return
        self._lines.remove(line)
        self._rows_lay.removeWidget(line)
        line.deleteLater()
        self._on_line_changed()

    def _move_up(self, line):
        idx = self._lines.index(line)
        if idx == 0:
            return
        self._lines[idx], self._lines[idx - 1] = self._lines[idx - 1], self._lines[idx]
        self._rebuild_rows()

    def _move_dn(self, line):
        idx = self._lines.index(line)
        if idx >= len(self._lines) - 1:
            return
        self._lines[idx], self._lines[idx + 1] = self._lines[idx + 1], self._lines[idx]
        self._rebuild_rows()

    def _rebuild_rows(self):
        while self._rows_lay.count() > 1:
            item = self._rows_lay.takeAt(0)
            if item and item.widget():
                item.widget().setParent(None)
        for line in self._lines:
            self._rows_lay.insertWidget(self._rows_lay.count() - 1, line)

    def _on_line_changed(self):
        self._refresh_totals()
        self._on_balance_changed()

    def _refresh_totals(self):
        total_dr = sum(ln.get_amount() for ln in self._lines if ln.get_side() == "dr")
        total_cr = sum(ln.get_amount() for ln in self._lines if ln.get_side() == "cr")
        self.lbl_dr.setText(tr("journal_dr_total", amount=f"{total_dr:,.2f}"))
        self.lbl_cr.setText(tr("journal_cr_total", amount=f"{total_cr:,.2f}"))

    def get_total_dr(self) -> float:
        return sum(ln.get_amount() for ln in self._lines if ln.get_side() == "dr")

    def get_total_cr(self) -> float:
        return sum(ln.get_amount() for ln in self._lines if ln.get_side() == "cr")

    def get_all_values(self) -> list:
        return [v for ln in self._lines if (v := ln.get_values()) is not None]

    def get_all_investor_links(self) -> list:
        return [lk for ln in self._lines if (lk := ln.get_investor_link()) is not None]

    def clear_lines(self):
        for ln in list(self._lines):
            self._rows_lay.removeWidget(ln)
            ln.deleteLater()
        self._lines.clear()
        self._refresh_totals()
