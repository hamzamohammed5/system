"""
ui/tabs/accounting/audit_log_tab.py
=====================================
[E-04] Audit Log UI — tab لعرض سجل العمليات الحساسة.

يعرض سجلات audit_log مع:
  - فلترة حسب الجدول والنوع
  - pagination (200 سجل في كل مرة)
  - تفاصيل السجل في dialog منفصل عند الضغط
  - عرض old_data كـ JSON مُنسَّق

الاستخدام:
    # في accounting_tabs_builder.py أو accounting_section.py:
    from ui.tabs.accounting.audit_log_tab import AuditLogTab
    tabs.addTab(AuditLogTab(acc_conn), "🔍 سجل العمليات")

[إصلاح v2]:
  - كل النصوص تُقرأ من tr() — لا نص مكتوب مباشرة.
  - كل الألوان تُقرأ من _C — لا قيمة لون مكتوبة مباشرة.
  - الخطوط تُقرأ من font.py (get_font_size, fs, FS_SM, FS_BASE, FS_MD).
  - _ACTION_COLORS → يعكس _C['audit_*'] مباشرة.
  - _TABLE_LABELS  → يُبنى من tr() عند الحاجة.
"""

import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QTextEdit, QHeaderView, QAbstractItemView,
    QSizePolicy, QFrame,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui  import QColor, QFont
from ui.widgets.panels.themed_inputs import ThemedComboBox

from services.accounting.audit_service import AuditService
from ui.font               import get_font_size, fs, FS_SM, FS_BASE, FS_MD
from ui.widgets.theme.table_styles  import table_style, splitter_style
from ui.widgets.components.headers_list import StatusBar
from ui.widgets.components.button       import make_btn
from ui.widgets.panels.state            import EmptyState
from ui.widgets.core.conn               import SafeConnMixin
from ui.widgets.core.i18n              import tr
from ui.widgets.core.widget_mixin       import WidgetMixin
from ui.constants import (
    AUDIT_DETAIL_MIN_W, AUDIT_DETAIL_MIN_H,
    AUDIT_DETAIL_BODY_MARGIN_H, AUDIT_DETAIL_BODY_MARGIN_V, AUDIT_DETAIL_BODY_SPACING,
    AUDIT_DETAIL_HDR_RADIUS, AUDIT_DETAIL_HDR_MARGIN_H, AUDIT_DETAIL_HDR_MARGIN_V,
    AUDIT_DETAIL_TXT_RADIUS, AUDIT_DETAIL_TXT_PAD,
    AUDIT_HDR_MARGIN_H, AUDIT_HDR_MARGIN_V,
    AUDIT_FILTER_MARGIN_H, AUDIT_FILTER_MARGIN_V, AUDIT_FILTER_SPACING,
    AUDIT_FILTER_CMB_TABLE_W, AUDIT_FILTER_CMB_ACTION_W,
    AUDIT_COL_INDEX_W, AUDIT_COL_TYPE_W, AUDIT_COL_TABLE_W,
    AUDIT_COL_RECORD_W, AUDIT_COL_BY_W, AUDIT_ROW_H,
    AUDIT_PAGIN_BAR_H, AUDIT_PAGIN_MARGIN_H, AUDIT_PAGIN_MARGIN_V, AUDIT_PAGIN_SPACING,
    AUDIT_FILTER_CMB_RADIUS, AUDIT_FILTER_CMB_PAD_V, AUDIT_FILTER_CMB_PAD_H,
    AUDIT_FILTER_DROP_W, FILTER_COMBO_MIN_H,
    AUDIT_PAGE_SIZE, AUDIT_LOAD_DELAY,
)


# ══════════════════════════════════════════════════════════
# ثوابت مساعدة — كل ألوان _ACTION_COLORS تأتي من _C
# ══════════════════════════════════════════════════════════

def _action_colors() -> dict:
    """
    ألوان أنواع العمليات — تُقرأ من _C دائماً لدعم الثيمات.
    يرجع dict: action → (fg, bg)
    """
    from ui.theme import _C
    return {
        "delete": (_C["audit_delete_fg"], _C["audit_delete_bg"]),
        "update": (_C["audit_update_fg"], _C["audit_update_bg"]),
        "create": (_C["audit_create_fg"], _C["audit_create_bg"]),
    }


def _table_labels() -> dict:
    """
    تسميات الجداول — تُقرأ من tr() دائماً.
    يرجع dict: table_key → label
    """
    return {
        "journal_entries":  tr("audit_table_journal_entries"),
        "journal_lines":    tr("audit_table_journal_lines"),
        "accounts":         tr("audit_table_accounts"),
        "inventory_moves":  tr("audit_table_inventory_moves"),
        "investor_entries": tr("audit_table_investor_entries"),
    }


_ACTION_ICONS = {
    "delete": tr("audit_log_delete"),
    "update": tr("audit_log_update"),
    "create": tr("audit_log_create"),
}

_PAGE_SIZE = AUDIT_PAGE_SIZE


# ══════════════════════════════════════════════════════════
# Detail Dialog
# ══════════════════════════════════════════════════════════

class _AuditDetailDialog(QDialog):
    """Dialog يعرض تفاصيل سجل Audit واحد."""

    def __init__(self, record: dict, parent=None):
        super().__init__(
            parent,
            Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint,
        )
        self.setWindowTitle(tr("audit_detail_title"))
        self.setModal(True)
        self.setMinimumSize(AUDIT_DETAIL_MIN_W, AUDIT_DETAIL_MIN_H)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build(record)

    def _build(self, r: dict):
        from ui.theme import _C
        self.setStyleSheet(f"QDialog {{ background:{_C['bg_page']}; }}")
        root = QVBoxLayout(self)
        root.setContentsMargins(AUDIT_DETAIL_BODY_MARGIN_H, AUDIT_DETAIL_BODY_MARGIN_V,
                                AUDIT_DETAIL_BODY_MARGIN_H, AUDIT_DETAIL_BODY_MARGIN_V)
        root.setSpacing(AUDIT_DETAIL_BODY_SPACING)

        base = get_font_size()

        # ── Header ───────────────────────────────────────
        action       = r.get("action", "")
        colors       = _action_colors()
        fg, bg       = colors.get(action, (_C["text_primary"], _C["bg_surface_2"]))
        icon         = _ACTION_ICONS.get(action, "📋")

        hdr = QFrame()
        hdr.setStyleSheet(f"""
            QFrame {{
                background:{bg}; border:1px solid {fg}44;
                border-radius:{AUDIT_DETAIL_HDR_RADIUS}px; padding:4px;
            }}
        """)
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(AUDIT_DETAIL_HDR_MARGIN_H, AUDIT_DETAIL_HDR_MARGIN_V,
                                   AUDIT_DETAIL_HDR_MARGIN_H, AUDIT_DETAIL_HDR_MARGIN_V)

        lbl_action = QLabel(f"{icon}  {action.upper()}")
        lbl_action.setStyleSheet(
            f"font-weight:bold; font-size:{fs(base, +1)}pt;"
            f"color:{fg}; background:transparent; border:none;"
        )
        hdr_lay.addWidget(lbl_action)
        hdr_lay.addStretch()

        lbl_time = QLabel(r.get("created_at", ""))
        lbl_time.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{fs(base, -1)}pt;"
            "background:transparent; border:none;"
        )
        hdr_lay.addWidget(lbl_time)
        root.addWidget(hdr)

        # ── Meta ──────────────────────────────────────────
        labels      = _table_labels()
        table_label = labels.get(r.get("table_name", ""), r.get("table_name", "─"))
        meta_text   = tr(
            "audit_meta_line",
            table      = table_label,
            record_id  = r.get("record_id", "─"),
            changed_by = r.get("changed_by", "system"),
        )
        lbl_meta = QLabel(meta_text)
        lbl_meta.setStyleSheet(
            f"color:{_C['text_sec']}; font-size:{fs(base, 0)}pt;"
            "background:transparent; border:none;"
        )
        root.addWidget(lbl_meta)

        # ── Old Data ──────────────────────────────────────
        lbl_data = QLabel(tr("old_data") + ":")
        lbl_data.setStyleSheet(
            f"font-weight:bold; color:{_C['text_primary']};"
            f"font-size:{fs(base, 0)}pt; background:transparent; border:none;"
        )
        root.addWidget(lbl_data)

        txt = QTextEdit()
        txt.setReadOnly(True)
        txt.setStyleSheet(f"""
            QTextEdit {{
                background:{_C['bg_surface_2']}; border:1px solid {_C['border_med']};
                border-radius:{AUDIT_DETAIL_TXT_RADIUS}px; padding:{AUDIT_DETAIL_TXT_PAD}px;
                font-family:monospace; font-size:{fs(base, -1)}pt;
                color:{_C['text_primary']};
            }}
        """)

        old_data = r.get("old_data", "")
        if old_data:
            try:
                parsed  = json.loads(old_data)
                display = json.dumps(parsed, ensure_ascii=False, indent=2)
            except Exception:
                display = old_data
        else:
            display = tr("audit_no_old_data")

        txt.setPlainText(display)
        root.addWidget(txt, stretch=1)

        # ── Close ─────────────────────────────────────────
        btn_close = make_btn(tr("close"), "ghost")
        btn_close.clicked.connect(self.accept)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        root.addLayout(btn_row)


# ══════════════════════════════════════════════════════════
# AuditLogTab
# ══════════════════════════════════════════════════════════

class AuditLogTab(SafeConnMixin, QWidget, WidgetMixin):
    """
    [E-04] Tab لعرض سجل العمليات الحساسة.

    الاستخدام:
        tab = AuditLogTab(acc_conn)
        tabs.addTab(tab, "🔍 سجل العمليات")
    """

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self._init_safe_conn(conn, "accounting")
        self._all_records : list = []
        self._offset      : int  = 0
        self._total_count : int  = 0
        self._build()
        self._init_widget_mixin(theme=True, font=True, lang=False, data=False)
        self._refresh_style()
        # تأجيل التحميل لبعد ظهور الـ widget
        QTimer.singleShot(AUDIT_LOAD_DELAY, self._load)

    # ── بناء الواجهة ──────────────────────────────────────

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())
        root.addWidget(self._build_filter_bar())
        root.addWidget(self._build_table(), stretch=1)
        root.addWidget(self._build_pagination())
        root.addWidget(self._status_bar)

    def _refresh_style(self, *_):
        from ui.theme import _C
        base = get_font_size()

        self.setStyleSheet(f"background:{_C['bg_page']};")

        self._hdr_frame.setStyleSheet(f"""
            QFrame {{
                background:{_C['bg_surface']};
                border-bottom:1px solid {_C['border']};
            }}
        """)
        self._lbl_header.setStyleSheet(
            f"font-weight:bold; font-size:{fs(base, +2)}pt;"
            f"color:{_C['text_primary']}; background:transparent; border:none;"
        )

        self._filter_bar_frame.setStyleSheet(f"""
            QFrame {{
                background:{_C['bg_surface_2']};
                border-bottom:1px solid {_C['border']};
            }}
        """)
        combo_style = f"""
            QComboBox {{
                background:{_C['bg_input']}; border:1px solid {_C['border_med']};
                border-radius:{AUDIT_FILTER_CMB_RADIUS}px; padding:{AUDIT_FILTER_CMB_PAD_V}px {AUDIT_FILTER_CMB_PAD_H}px;
                font-size:{fs(base, -1)}pt; color:{_C['text_primary']};
                min-height:{FILTER_COMBO_MIN_H}px;
            }}
            QComboBox:focus {{ border-color:{_C['accent']}; }}
            QComboBox::drop-down {{ border:none; width:{AUDIT_FILTER_DROP_W}px; }}
        """
        lbl_style = (
            f"color:{_C['text_sec']}; font-size:{fs(base, -1)}pt;"
            "background:transparent; border:none; font-weight:bold;"
        )
        self._cmb_table.setStyleSheet(combo_style)
        self._cmb_action.setStyleSheet(combo_style)
        self._lbl_table.setStyleSheet(lbl_style)
        self._lbl_action.setStyleSheet(lbl_style)

        self._table_container.setStyleSheet(f"background:{_C['bg_input']};")

        self._pagination_bar.setStyleSheet(f"""
            QFrame {{
                background:{_C['bg_surface_2']};
                border-top:1px solid {_C['border']};
            }}
        """)
        self._lbl_page.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{fs(base, -1)}pt;"
            "background:transparent; border:none;"
        )

    def _build_header(self) -> QWidget:
        base = get_font_size()
        hdr  = QFrame()
        self._hdr_frame = hdr
        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(AUDIT_HDR_MARGIN_H, AUDIT_HDR_MARGIN_V,
                               AUDIT_HDR_MARGIN_H, AUDIT_HDR_MARGIN_V)

        lbl = QLabel(tr("audit_log_header_title"))
        self._lbl_header = lbl
        lay.addWidget(lbl)
        lay.addStretch()

        self._btn_refresh = make_btn(tr("btn_refresh"), "normal")
        self._btn_refresh.clicked.connect(self._load)
        lay.addWidget(self._btn_refresh)

        return hdr

    def _build_filter_bar(self) -> QWidget:
        base = get_font_size()
        bar  = QFrame()
        self._filter_bar_frame = bar
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(AUDIT_FILTER_MARGIN_H, AUDIT_FILTER_MARGIN_V,
                               AUDIT_FILTER_MARGIN_H, AUDIT_FILTER_MARGIN_V)
        lay.setSpacing(AUDIT_FILTER_SPACING)

        # فلتر الجدول
        lbl_table = QLabel(tr("audit_table_filter_label"))
        self._lbl_table = lbl_table

        self._cmb_table = ThemedComboBox()
        self._cmb_table.setMinimumWidth(AUDIT_FILTER_CMB_TABLE_W)
        self._cmb_table.addItem(tr("audit_all_tables"), None)
        for key, label in _table_labels().items():
            self._cmb_table.addItem(f"{label}  ({key})", key)
        self._cmb_table.currentIndexChanged.connect(self._on_filter_changed)

        # فلتر النوع
        lbl_action = QLabel(tr("audit_col_type") + ":")
        self._lbl_action = lbl_action

        self._cmb_action = ThemedComboBox()
        self._cmb_action.setMinimumWidth(AUDIT_FILTER_CMB_ACTION_W)
        self._cmb_action.addItem(tr("audit_all_types"), None)
        for action, icon in _ACTION_ICONS.items():
            self._cmb_action.addItem(f"{icon}  {action}", action)
        self._cmb_action.currentIndexChanged.connect(self._on_filter_changed)

        lay.addWidget(lbl_table)
        lay.addWidget(self._cmb_table)
        lay.addWidget(lbl_action)
        lay.addWidget(self._cmb_action)
        lay.addStretch()

        return bar

    def _build_table(self) -> QWidget:
        cols = [
            tr("audit_col_index"),
            tr("audit_col_type"),
            tr("audit_col_table"),
            tr("audit_col_record_id"),
            tr("changed_by"),
            tr("audit_col_date"),
        ]
        self.table = QTableWidget()
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setStyleSheet(table_style())

        hh = self.table.horizontalHeader()
        hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hh.setSectionsClickable(False)
        hh.setSectionResizeMode(0, QHeaderView.Fixed);  self.table.setColumnWidth(0, AUDIT_COL_INDEX_W)
        hh.setSectionResizeMode(1, QHeaderView.Fixed);  self.table.setColumnWidth(1, AUDIT_COL_TYPE_W)
        hh.setSectionResizeMode(2, QHeaderView.Fixed);  self.table.setColumnWidth(2, AUDIT_COL_TABLE_W)
        hh.setSectionResizeMode(3, QHeaderView.Fixed);  self.table.setColumnWidth(3, AUDIT_COL_RECORD_W)
        hh.setSectionResizeMode(4, QHeaderView.Fixed);  self.table.setColumnWidth(4, AUDIT_COL_BY_W)
        hh.setSectionResizeMode(5, QHeaderView.Stretch)

        vh = self.table.verticalHeader()
        vh.setDefaultSectionSize(AUDIT_ROW_H)
        vh.setSectionResizeMode(QHeaderView.Fixed)

        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.itemDoubleClicked.connect(self._on_row_double_clicked)

        # Empty state
        self._empty = EmptyState(
            icon     = "🔍",
            title    = tr("no_audit_records"),
            subtitle = tr("no_audit_yet"),
            expandable = True,
        )
        self._empty.setVisible(False)

        # Status bar
        self._status_bar = StatusBar()

        container = QWidget()
        self._table_container = container
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self.table, stretch=1)
        lay.addWidget(self._empty)

        return container

    def _build_pagination(self) -> QWidget:
        base = get_font_size()
        bar  = QFrame()
        bar.setFixedHeight(AUDIT_PAGIN_BAR_H)
        self._pagination_bar = bar

        lay = QHBoxLayout(bar)
        lay.setContentsMargins(AUDIT_PAGIN_MARGIN_H, AUDIT_PAGIN_MARGIN_V,
                               AUDIT_PAGIN_MARGIN_H, AUDIT_PAGIN_MARGIN_V)
        lay.setSpacing(AUDIT_PAGIN_SPACING)

        self._lbl_page = QLabel("")
        lay.addWidget(self._lbl_page, stretch=1)

        self._btn_load_more = make_btn(
            tr("load_more", count=_PAGE_SIZE), "normal"
        )
        self._btn_load_more.clicked.connect(self._load_more)
        self._btn_load_more.setVisible(False)
        lay.addWidget(self._btn_load_more)

        return bar

    # ── تحميل البيانات ────────────────────────────────────

    def _load(self):
        """يُعيد تحميل من البداية."""
        self._offset      = 0
        self._all_records = []
        self.table.setRowCount(0)
        self._fetch_and_fill()

    def _load_more(self):
        """يُحمِّل الصفحة التالية."""
        self._fetch_and_fill()

    def _on_filter_changed(self):
        self._load()

    def _fetch_and_fill(self):
        conn = self._get_safe_conn()
        if conn is None:
            return

        table_filter  = self._cmb_table.currentData()
        action_filter = self._cmb_action.currentData()

        try:
            page = AuditService(conn).get_page(
                table_name = table_filter,
                action     = action_filter,
                limit      = _PAGE_SIZE,
                offset     = self._offset,
            )
            rows = page.rows
            if self._offset == 0:
                self._total_count = page.total_count if page.total_count != -1 else 0
        except Exception:
            rows = []
            if self._offset == 0:
                self._total_count = 0
        self._all_records.extend(rows)
        self._offset += len(rows)

        self._fill_table(rows)
        self._update_pagination()

    def _fill_table(self, rows: list):
        from ui.theme import _C
        base   = get_font_size()
        colors = _action_colors()
        labels = _table_labels()

        for r in rows:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            self.table.setRowHeight(row_idx, AUDIT_ROW_H)

            # [0] ID
            item_id = QTableWidgetItem(str(r.get("id", "")))
            item_id.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            item_id.setData(Qt.UserRole, r)   # حفظ الـ record كاملاً
            self.table.setItem(row_idx, 0, item_id)

            # [1] النوع مع لون
            action = r.get("action", "")
            icon   = _ACTION_ICONS.get(action, "")
            fg, _  = colors.get(action, (_C["text_primary"], ""))
            item_action = QTableWidgetItem(f"{icon} {action}")
            item_action.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            item_action.setForeground(QColor(fg))
            f = QFont()
            f.setBold(True)
            item_action.setFont(f)
            self.table.setItem(row_idx, 1, item_action)

            # [2] الجدول
            table_name  = r.get("table_name", "")
            table_label = labels.get(table_name, table_name)
            item_table  = QTableWidgetItem(table_label)
            item_table.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_idx, 2, item_table)

            # [3] ID السجل
            item_rec = QTableWidgetItem(str(r.get("record_id") or tr("dash")))
            item_rec.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            self.table.setItem(row_idx, 3, item_rec)

            # [4] بواسطة
            item_by = QTableWidgetItem(r.get("changed_by", "system"))
            item_by.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            item_by.setForeground(QColor(_C["text_muted"]))
            self.table.setItem(row_idx, 4, item_by)

            # [5] التاريخ
            item_date = QTableWidgetItem(r.get("created_at", ""))
            item_date.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_idx, 5, item_date)

        has_data = self.table.rowCount() > 0
        self.table.setVisible(has_data)
        self._empty.setVisible(not has_data)

    def _update_pagination(self):
        shown = self.table.rowCount()
        total = self._total_count
        self._status_bar.set_count(shown, total)

        remaining = total - shown
        if remaining > 0:
            self._lbl_page.setText(tr("showing_records", shown=shown, total=total))
            self._btn_load_more.setText(
                tr("load_more", count=min(remaining, _PAGE_SIZE))
            )
            self._btn_load_more.setVisible(True)
        else:
            self._lbl_page.setText(tr("showing_all_records", shown=shown))
            self._btn_load_more.setVisible(False)

    # ── Double click → Detail dialog ──────────────────────

    def _on_row_double_clicked(self, item):
        row     = item.row()
        id_item = self.table.item(row, 0)
        if not id_item:
            return
        record = id_item.data(Qt.UserRole)
        if record:
            dlg = _AuditDetailDialog(record, parent=self)
            dlg.exec_()
