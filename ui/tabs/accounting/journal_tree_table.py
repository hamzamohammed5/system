"""
ui/tabs/accounting/journal_tree_table.py
=========================================
_JournalTreeTable — جدول القيود المحاسبية مع expand/collapse وفلاتر متكاملة.
JournalTab        — التبويب الرئيسي يجمع الفورم والجدول.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QMessageBox, QAbstractItemView,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui  import QColor, QFont, QBrush

from db.accounting_repo import (
    fetch_all_entries, fetch_entry_lines,
    delete_entry,
)
from ui.helpers import (
    section_label, buttons_row,
    danger_button, confirm_delete,
)
from ui.events import bus
from .helpers  import TYPE_COLORS
from .journal_filter  import _JournalFilterBar
from .journal_form    import _JournalForm


class _JournalTreeTable(QWidget):
    """
    جدول القيود المحاسبية:
    - كل قيد يُعرض كصف رئيسي قابل للتوسيع/الطي
    - عند التوسيع تظهر صفوف الحسابات (DR/CR) تحته
    - فلاتر: بحث + تصنيف شجري + توازن + نطاق تاريخ
    """

    COLS = ["#", "التاريخ", "رقم القيد", "البيان / الحساب", "DR", "CR", "الحالة"]

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn          = conn
        self._expanded: set[int] = set()
        self._entries_data = []
        self._row_meta     = {}
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        root.addWidget(section_label("── القيود المحاسبية المحفوظة ──"))

        # ── شريط الفلاتر ──
        self._filter = _JournalFilterBar(self.conn)
        self._filter.inp_search.textChanged.connect(self._apply_filter)
        self._filter.cmb_group._tree_view.clicked.connect(
            lambda _: QTimer.singleShot(50, self._apply_filter)
        )
        self._filter.cmb_balance.currentIndexChanged.connect(self._apply_filter)
        self._filter.dt_from.dateChanged.connect(self._apply_filter)
        self._filter.dt_to.dateChanged.connect(self._apply_filter)

        # ربط زر المسح
        orig_reset = self._filter.reset
        def _reset_and_apply():
            orig_reset()
            self._apply_filter()
        self._filter.reset = _reset_and_apply
        root.addWidget(self._filter)

        # ── أزرار التحكم ──
        btn_expand_all   = QPushButton("⊞ توسيع الكل")
        btn_collapse_all = QPushButton("⊟ طي الكل")
        btn_del          = danger_button("🗑️  حذف القيد المحدد")
        for btn in (btn_expand_all, btn_collapse_all, btn_del):
            btn.setMinimumHeight(26)

        _btn_style = (
            "QPushButton { background:#e8f4fd; color:#1565c0; border:1px solid #90caf9;"
            "border-radius:4px; padding:2px 10px; font-size:11px; }"
            "QPushButton:hover { background:#1565c0; color:white; }"
        )
        btn_expand_all.setStyleSheet(_btn_style)
        btn_collapse_all.setStyleSheet(_btn_style)
        btn_expand_all.clicked.connect(self._expand_all)
        btn_collapse_all.clicked.connect(self._collapse_all)
        btn_del.clicked.connect(self._delete_selected)
        root.addLayout(buttons_row(btn_expand_all, btn_collapse_all, btn_del))

        # ── الجدول ──
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Interactive)
        hh.setSectionResizeMode(1, QHeaderView.Interactive)
        hh.setSectionResizeMode(2, QHeaderView.Interactive)
        hh.setSectionResizeMode(3, QHeaderView.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.Interactive)
        hh.setSectionResizeMode(5, QHeaderView.Interactive)
        hh.setSectionResizeMode(6, QHeaderView.Interactive)

        self.table.setColumnWidth(0, 28)
        self.table.setColumnWidth(1, 92)
        self.table.setColumnWidth(2, 85)
        self.table.setColumnWidth(4, 95)
        self.table.setColumnWidth(5, 95)
        self.table.setColumnWidth(6, 85)
        hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setWordWrap(False)
        self.table.cellClicked.connect(self._on_cell_clicked)
        root.addWidget(self.table, stretch=1)

    # ══════════════════════════════════════════════════════
    # تحميل البيانات
    # ══════════════════════════════════════════════════════

    def _load(self):
        entries = fetch_all_entries(self.conn)
        self._entries_data = []
        for e in entries:
            lines = fetch_entry_lines(self.conn, e["id"])
            self._entries_data.append({
                "id":           e["id"],
                "ref_no":       e["ref_no"],
                "date":         e["date"],
                "type":         e["type"],
                "description":  e["description"],
                "total_debit":  e["total_debit"],
                "total_credit": e["total_credit"],
                "lines":        [dict(l) for l in lines],
            })
        self._apply_filter()

    # ══════════════════════════════════════════════════════
    # الفلترة والعرض
    # ══════════════════════════════════════════════════════

    def _apply_filter(self):
        filtered = [e for e in self._entries_data if self._filter.matches(e)]
        self._filter.set_count(len(filtered), len(self._entries_data))
        self._render(filtered)

    def _render(self, entries=None):
        if entries is None:
            entries = self._entries_data

        self.table.setRowCount(0)
        self._row_meta = {}

        for entry in entries:
            eid      = entry["id"]
            expanded = eid in self._expanded
            total_dr = entry["total_debit"]
            total_cr = entry["total_credit"]

            # ── الصف الرئيسي ──
            r = self.table.rowCount()
            self.table.insertRow(r)
            self._row_meta[r] = {"entry_id": eid, "is_parent": True, "is_child": False}

            toggle_item = QTableWidgetItem("▼" if expanded else "▶")
            toggle_item.setTextAlignment(Qt.AlignCenter)
            toggle_item.setForeground(QBrush(QColor("#1565c0")))
            f = QFont(); f.setBold(True)
            toggle_item.setFont(f)
            self.table.setItem(r, 0, toggle_item)

            date_item = QTableWidgetItem(entry["date"])
            date_item.setTextAlignment(Qt.AlignCenter)
            df = QFont(); df.setBold(True)
            date_item.setFont(df)
            date_item.setForeground(QBrush(QColor("#2e7d32")))
            self.table.setItem(r, 1, date_item)

            self.table.setItem(r, 2, self._bold_item(entry["ref_no"], "#1565c0"))
            self.table.setItem(r, 3, self._bold_item(entry["description"]))
            self.table.setItem(r, 4, self._bold_item(f"{total_dr:,.2f}", "#1565c0"))
            self.table.setItem(r, 5, self._bold_item(f"{total_cr:,.2f}", "#c62828"))

            diff      = total_dr - total_cr
            bal_color = "#2e7d32" if abs(diff) < 0.01 else "#c62828"
            bal_text  = "✅ متوازن" if abs(diff) < 0.01 else f"⚠️ {abs(diff):,.2f}"
            self.table.setItem(r, 6, self._bold_item(bal_text, bal_color))

            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                if item:
                    item.setBackground(QBrush(QColor("#eef3fb")))

            # ── صفوف الأبناء (لو موسع) ──
            if expanded:
                for line in entry["lines"]:
                    rc = self.table.rowCount()
                    self.table.insertRow(rc)
                    self._row_meta[rc] = {
                        "entry_id": eid, "is_parent": False, "is_child": True
                    }

                    acc_name = line.get("account_name", "")
                    acc_code = line.get("account_code", "")
                    acc_type = line.get("account_type", "")
                    acc_color = TYPE_COLORS.get(acc_type, "#333")

                    prefix    = "    └─ "
                    desc_text = f"{prefix}{acc_code} — {acc_name}"
                    if line.get("description"):
                        desc_text += f"  │  {line['description']}"

                    is_dr  = line["debit"] > 0
                    row_bg = QColor("#f4f8ff") if is_dr else QColor("#fff4f4")

                    for c in range(4):
                        self.table.setItem(rc, c, QTableWidgetItem(""))

                    desc_item = QTableWidgetItem(desc_text)
                    desc_item.setToolTip(f"{acc_code} — {acc_name}")
                    desc_item.setForeground(QBrush(QColor(acc_color)))
                    self.table.setItem(rc, 3, desc_item)

                    if is_dr:
                        self.table.setItem(rc, 4,
                            self._colored_item(f"{line['debit']:,.2f}", "#1565c0"))
                        self.table.setItem(rc, 5, QTableWidgetItem(""))
                    else:
                        self.table.setItem(rc, 4, QTableWidgetItem(""))
                        self.table.setItem(rc, 5,
                            self._colored_item(f"{line['credit']:,.2f}", "#c62828"))

                    self.table.setItem(rc, 6, QTableWidgetItem(""))

                    for c in range(self.table.columnCount()):
                        item = self.table.item(rc, c)
                        if item:
                            item.setBackground(QBrush(row_bg))

    # ══════════════════════════════════════════════════════
    # مساعدات العرض
    # ══════════════════════════════════════════════════════

    def _bold_item(self, text, color=None):
        item = QTableWidgetItem(text)
        f = QFont(); f.setBold(True)
        item.setFont(f)
        if color:
            item.setForeground(QBrush(QColor(color)))
        return item

    def _colored_item(self, text, color):
        item = QTableWidgetItem(text)
        item.setForeground(QBrush(QColor(color)))
        return item

    # ══════════════════════════════════════════════════════
    # تفاعل المستخدم
    # ══════════════════════════════════════════════════════

    def _on_cell_clicked(self, row, col):
        meta = self._row_meta.get(row)
        if not meta or not meta["is_parent"]:
            return
        # الضغط على الأعمدة الأولى يفتح/يغلق
        if col not in (0, 1, 2):
            return
        eid = meta["entry_id"]
        if eid in self._expanded:
            self._expanded.discard(eid)
        else:
            self._expanded.add(eid)
        self._apply_filter()

    def _expand_all(self):
        self._expanded = {e["id"] for e in self._entries_data}
        self._apply_filter()

    def _collapse_all(self):
        self._expanded.clear()
        self._apply_filter()

    def _selected_entry_id(self):
        row  = self.table.currentRow()
        meta = self._row_meta.get(row)
        if not meta:
            return None
        return meta["entry_id"]

    def _delete_selected(self):
        eid = self._selected_entry_id()
        if eid is None:
            QMessageBox.information(self, "تنبيه", "اختر قيداً أولاً")
            return
        entry_data = next(
            (e for e in self._entries_data if e["id"] == eid), None
        )
        desc = entry_data["description"] if entry_data else f"ID:{eid}"
        if confirm_delete(self, desc):
            delete_entry(self.conn, eid)
            self._expanded.discard(eid)
            bus.data_changed.emit()


# ══════════════════════════════════════════════════════════
# التبويب الرئيسي
# ══════════════════════════════════════════════════════════

class JournalTab(QWidget):
    """
    تبويب القيود المحاسبية الكامل:
    - فورم إدخال القيد (أعلى)
    - جدول القيود المحفوظة مع فلاتر (أسفل)
    """

    def __init__(self, conn, erp_conn=None, parent=None):
        super().__init__(parent)
        self.conn     = conn
        self.erp_conn = erp_conn
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet("""
            QSplitter::handle { background:#e0e0e0; }
            QSplitter::handle:hover { background:#bbdefb; }
        """)

        self._form       = _JournalForm(self.conn, self.erp_conn)
        self._tree_table = _JournalTreeTable(self.conn)

        splitter.addWidget(self._form)
        splitter.addWidget(self._tree_table)
        splitter.setSizes([440, 360])
        splitter.setCollapsible(0, True)

        root.addWidget(splitter)