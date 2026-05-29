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
"""

import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QTextEdit, QHeaderView, QAbstractItemView,
    QSizePolicy, QFrame,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui  import QColor, QFont

from ui.app_settings  import _C, fs, get_font_size
from ui.widgets.theme.styles  import (
    table_style, scroll_style, splitter_style,
    ROW_HEIGHT_NORMAL,
)
from ui.widgets.components.headers  import ListHeader, StatusBar
from ui.widgets.components.button   import make_btn
from ui.widgets.panels.state        import EmptyState
from ui.widgets.core.conn           import LiveConnMixin


# ── ألوان الـ actions ─────────────────────────────────────
_ACTION_COLORS = {
    "delete": ("#C0392B", "#FDF0EF"),   # أحمر
    "update": ("#7A5C00", "#FDF8E7"),   # برتقالي
    "create": ("#2E7D52", "#EDF7F2"),   # أخضر
}

_ACTION_ICONS = {
    "delete": "🗑️",
    "update": "✏️",
    "create": "➕",
}

_TABLE_LABELS = {
    "journal_entries":  "قيود محاسبية",
    "journal_lines":    "سطور قيود",
    "accounts":         "حسابات",
    "inventory_moves":  "حركات مخزون",
    "investor_entries": "ربط مستثمرين",
}

_PAGE_SIZE = 200


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
        self.setWindowTitle("تفاصيل العملية")
        self.setModal(True)
        self.setMinimumSize(560, 420)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build(record)

    def _build(self, r: dict):
        self.setStyleSheet(f"QDialog {{ background:{_C['bg_page']}; }}")
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        base = get_font_size()

        # ── Header ───────────────────────────────────────
        action = r.get("action", "")
        fg, bg = _ACTION_COLORS.get(action, (_C["text_primary"], _C["bg_surface_2"]))
        icon   = _ACTION_ICONS.get(action, "📋")

        hdr = QFrame()
        hdr.setStyleSheet(f"""
            QFrame {{
                background:{bg}; border:1px solid {fg}44;
                border-radius:8px; padding:4px;
            }}
        """)
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(12, 8, 12, 8)

        lbl_action = QLabel(f"{icon}  {action.upper()}")
        lbl_action.setStyleSheet(
            f"font-weight:bold; font-size:{fs(base,+1)}pt;"
            f"color:{fg}; background:transparent; border:none;"
        )
        hdr_lay.addWidget(lbl_action)
        hdr_lay.addStretch()

        lbl_time = QLabel(r.get("created_at", ""))
        lbl_time.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{fs(base,-1)}pt;"
            "background:transparent; border:none;"
        )
        hdr_lay.addWidget(lbl_time)
        root.addWidget(hdr)

        # ── Meta ──────────────────────────────────────────
        table_label = _TABLE_LABELS.get(r.get("table_name", ""),
                                        r.get("table_name", "─"))
        meta_text = (
            f"الجدول: {table_label}  │  "
            f"ID السجل: {r.get('record_id', '─')}  │  "
            f"بواسطة: {r.get('changed_by', 'system')}"
        )
        lbl_meta = QLabel(meta_text)
        lbl_meta.setStyleSheet(
            f"color:{_C['text_sec']}; font-size:{fs(base,0)}pt;"
            "background:transparent; border:none;"
        )
        root.addWidget(lbl_meta)

        # ── Old Data ──────────────────────────────────────
        lbl_data = QLabel("البيانات القديمة:")
        lbl_data.setStyleSheet(
            f"font-weight:bold; color:{_C['text_primary']};"
            f"font-size:{fs(base,0)}pt; background:transparent; border:none;"
        )
        root.addWidget(lbl_data)

        txt = QTextEdit()
        txt.setReadOnly(True)
        txt.setStyleSheet(f"""
            QTextEdit {{
                background:{_C['bg_surface_2']}; border:1px solid {_C['border_med']};
                border-radius:6px; padding:8px;
                font-family:monospace; font-size:{fs(base,-1)}pt;
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
            display = "─ لا توجد بيانات محفوظة ─"

        txt.setPlainText(display)
        root.addWidget(txt, stretch=1)

        # ── Close ─────────────────────────────────────────
        btn_close = make_btn("إغلاق", "ghost")
        btn_close.clicked.connect(self.accept)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        root.addLayout(btn_row)


# ══════════════════════════════════════════════════════════
# AuditLogTab
# ══════════════════════════════════════════════════════════

class AuditLogTab(QWidget, LiveConnMixin):
    """
    [E-04] Tab لعرض سجل العمليات الحساسة.

    الاستخدام:
        tab = AuditLogTab(acc_conn)
        tabs.addTab(tab, "🔍 سجل العمليات")
    """

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._all_records : list = []
        self._offset      : int  = 0
        self._total_count : int  = 0
        self._build()
        # تأجيل التحميل لبعد ظهور الـ widget
        QTimer.singleShot(100, self._load)

    # ── بناء الواجهة ──────────────────────────────────────

    def _build(self):
        self.setStyleSheet(f"background:{_C['bg_page']};")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())
        root.addWidget(self._build_filter_bar())
        root.addWidget(self._build_table(), stretch=1)
        root.addWidget(self._build_pagination())
        root.addWidget(self._status_bar)

    def _build_header(self) -> QWidget:
        base = get_font_size()
        hdr = QFrame()
        hdr.setStyleSheet(f"""
            QFrame {{
                background:{_C['bg_surface']};
                border-bottom:1px solid {_C['border']};
            }}
        """)
        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(16, 12, 16, 12)

        lbl = QLabel("🔍  سجل العمليات الحساسة")
        lbl.setStyleSheet(
            f"font-weight:bold; font-size:{fs(base,+2)}pt;"
            f"color:{_C['text_primary']}; background:transparent; border:none;"
        )
        lay.addWidget(lbl)
        lay.addStretch()

        self._btn_refresh = make_btn("🔄 تحديث", "normal")
        self._btn_refresh.clicked.connect(self._load)
        lay.addWidget(self._btn_refresh)

        return hdr

    def _build_filter_bar(self) -> QWidget:
        base = get_font_size()
        bar = QFrame()
        bar.setStyleSheet(f"""
            QFrame {{
                background:{_C['bg_surface_2']};
                border-bottom:1px solid {_C['border']};
            }}
        """)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(12)

        combo_style = f"""
            QComboBox {{
                background:{_C['bg_input']}; border:1px solid {_C['border_med']};
                border-radius:5px; padding:3px 10px;
                font-size:{fs(base,-1)}pt; color:{_C['text_primary']};
                min-height:28px;
            }}
            QComboBox:focus {{ border-color:{_C['accent']}; }}
            QComboBox::drop-down {{ border:none; width:20px; }}
        """

        # فلتر الجدول
        lbl_table = QLabel("الجدول:")
        lbl_table.setStyleSheet(
            f"color:{_C['text_sec']}; font-size:{fs(base,-1)}pt;"
            "background:transparent; border:none; font-weight:bold;"
        )
        self._cmb_table = QComboBox()
        self._cmb_table.setMinimumWidth(180)
        self._cmb_table.setStyleSheet(combo_style)
        self._cmb_table.addItem("— كل الجداول —", None)
        for key, label in _TABLE_LABELS.items():
            self._cmb_table.addItem(f"{label}  ({key})", key)
        self._cmb_table.currentIndexChanged.connect(self._on_filter_changed)

        # فلتر النوع
        lbl_action = QLabel("النوع:")
        lbl_action.setStyleSheet(
            f"color:{_C['text_sec']}; font-size:{fs(base,-1)}pt;"
            "background:transparent; border:none; font-weight:bold;"
        )
        self._cmb_action = QComboBox()
        self._cmb_action.setMinimumWidth(130)
        self._cmb_action.setStyleSheet(combo_style)
        self._cmb_action.addItem("— كل الأنواع —", None)
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
        cols = ["#", "النوع", "الجدول", "ID السجل", "بواسطة", "التاريخ"]
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
        hh.setSectionResizeMode(0, QHeaderView.Fixed);  self.table.setColumnWidth(0, 55)
        hh.setSectionResizeMode(1, QHeaderView.Fixed);  self.table.setColumnWidth(1, 90)
        hh.setSectionResizeMode(2, QHeaderView.Fixed);  self.table.setColumnWidth(2, 140)
        hh.setSectionResizeMode(3, QHeaderView.Fixed);  self.table.setColumnWidth(3, 80)
        hh.setSectionResizeMode(4, QHeaderView.Fixed);  self.table.setColumnWidth(4, 100)
        hh.setSectionResizeMode(5, QHeaderView.Stretch)

        vh = self.table.verticalHeader()
        vh.setDefaultSectionSize(ROW_HEIGHT_NORMAL)
        vh.setSectionResizeMode(QHeaderView.Fixed)

        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.itemDoubleClicked.connect(self._on_row_double_clicked)

        # Empty state
        self._empty = EmptyState(
            icon="🔍",
            title="لا توجد سجلات",
            subtitle="لم يُسجَّل أي عملية حتى الآن",
            style="plain",
            color=_C['text_muted'],
            min_height=120,
        )
        self._empty.setVisible(False)

        # Status bar
        self._status_bar = StatusBar()

        container = QWidget()
        container.setStyleSheet(f"background:{_C['bg_input']};")
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self.table, stretch=1)
        lay.addWidget(self._empty)

        return container

    def _build_pagination(self) -> QWidget:
        base = get_font_size()
        bar = QFrame()
        bar.setStyleSheet(f"""
            QFrame {{
                background:{_C['bg_surface_2']};
                border-top:1px solid {_C['border']};
            }}
        """)
        bar.setFixedHeight(44)

        lay = QHBoxLayout(bar)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(10)

        self._lbl_page = QLabel("")
        self._lbl_page.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{fs(base,-1)}pt;"
            "background:transparent; border:none;"
        )
        lay.addWidget(self._lbl_page, stretch=1)

        self._btn_load_more = make_btn(f"تحميل {_PAGE_SIZE} إضافي  ▼", "normal")
        self._btn_load_more.clicked.connect(self._load_more)
        self._btn_load_more.setVisible(False)
        lay.addWidget(self._btn_load_more)

        self._pagination_bar = bar
        return bar

    # ── تحميل البيانات ────────────────────────────────────

    def _load(self):
        """يُعيد تحميل من البداية."""
        self._offset = 0
        self._all_records = []
        self.table.setRowCount(0)
        self._fetch_and_fill()

    def _load_more(self):
        """يُحمِّل الصفحة التالية."""
        self._fetch_and_fill()

    def _on_filter_changed(self):
        self._load()

    def _fetch_and_fill(self):
        try:
            conn = self._live_conn()
        except Exception:
            return

        table_filter  = self._cmb_table.currentData()
        action_filter = self._cmb_action.currentData()

        # جلب الإجمالي عند أول تحميل
        if self._offset == 0:
            try:
                from db.accounting.accounting_audit_repo import fetch_audit_log_count
                self._total_count = fetch_audit_log_count(
                    conn,
                    table_name = table_filter,
                    action     = action_filter,
                )
            except Exception:
                self._total_count = 0

        # جلب البيانات
        try:
            from db.accounting.accounting_audit_repo import fetch_audit_log
            rows = fetch_audit_log(
                conn,
                table_name = table_filter,
                action     = action_filter,
                limit      = _PAGE_SIZE,
                offset     = self._offset,
            )
        except Exception:
            rows = []

        self._all_records.extend(rows)
        self._offset += len(rows)

        self._fill_table(rows)
        self._update_pagination()

    def _fill_table(self, rows: list):
        base = get_font_size()

        for r in rows:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            self.table.setRowHeight(row_idx, ROW_HEIGHT_NORMAL)

            # [0] ID
            item_id = QTableWidgetItem(str(r.get("id", "")))
            item_id.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            item_id.setData(Qt.UserRole, r)   # حفظ الـ record كاملاً
            self.table.setItem(row_idx, 0, item_id)

            # [1] النوع مع لون
            action = r.get("action", "")
            icon   = _ACTION_ICONS.get(action, "")
            fg, _  = _ACTION_COLORS.get(action, (_C["text_primary"], ""))
            item_action = QTableWidgetItem(f"{icon} {action}")
            item_action.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            item_action.setForeground(QColor(fg))
            f = QFont()
            f.setBold(True)
            item_action.setFont(f)
            self.table.setItem(row_idx, 1, item_action)

            # [2] الجدول
            table_name  = r.get("table_name", "")
            table_label = _TABLE_LABELS.get(table_name, table_name)
            item_table  = QTableWidgetItem(table_label)
            item_table.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_idx, 2, item_table)

            # [3] ID السجل
            item_rec = QTableWidgetItem(str(r.get("record_id") or "─"))
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
            self._lbl_page.setText(f"يعرض {shown:,} من {total:,}")
            self._btn_load_more.setText(
                f"تحميل {min(remaining, _PAGE_SIZE):,} إضافي  ▼"
            )
            self._btn_load_more.setVisible(True)
        else:
            self._lbl_page.setText(f"يعرض كل {shown:,} سجل")
            self._btn_load_more.setVisible(False)

    # ── Double click → Detail dialog ──────────────────────

    def _on_row_double_clicked(self, item):
        # نجلب الـ record من العمود الأول
        row = item.row()
        id_item = self.table.item(row, 0)
        if not id_item:
            return
        record = id_item.data(Qt.UserRole)
        if record:
            dlg = _AuditDetailDialog(record, parent=self)
            dlg.exec_()