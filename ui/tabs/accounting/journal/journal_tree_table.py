"""
ui/tabs/accounting/journal/journal_tree_table.py
================================================
_JournalTreeTable — جدول القيود المحاسبية.

[v9]:
  - استخدام emit_company_data_changed() من company_utils.
  - جميع imports من panels (نقطة واحدة).
  - كود أنظف وأقل تكراراً.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui  import QColor

from db.accounting.accounting_repo import (
    fetch_all_entries, fetch_entry_lines,
    delete_entry,
)
from ui.widgets.core.events import bus, get_active_company_id, emit_company_data_changed
from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.components.headers_list import ListHeader, StatusBar as ListStatusBar
from ui.widgets.dialogs.confirm import confirm_delete
from ui.widgets.components.button import make_btn as _make_btn
from ui.widgets.tables.tables import (
    bold_item as bold_table_item,
    colored_item as colored_table_item,
    center_item as center_table_item,
    set_row_bg as set_row_background,
)
from ui.theme import _C
from ui.widgets.core.i18n import tr
from ..helpers  import TYPE_COLORS
from .journal_filter  import _JournalFilterBar
from .journal_form    import _JournalForm


class _JournalTreeTable(SafeConnMixin, QWidget):
    """جدول القيود المحاسبية — SafeConnMixin يضمن conn الشركة الصح."""

    @staticmethod
    def _cols():
        return ["#", tr("date"), tr("ref_no"), tr("journal_description"), tr("journal_dr_col"), tr("journal_cr_col"), tr("status")]

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self._init_safe_conn(conn, "accounting")
        self._expanded: set[int] = set()
        self._entries_data = []
        self._row_meta     = {}
        self._company_id   = get_active_company_id()

        self._build()
        self._load()
        bus.company_data_changed.connect(self._on_company_data_changed)

    def _on_company_data_changed(self, company_id: int):
        if self._on_company_event_safe(company_id):
            self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── هيدر موحد ──
        self._header = ListHeader(
            title=tr("journal_table_title"),
            show_search=False,
        )
        self._header.add_action(tr("journal_expand_all"),   self._expand_all,   "normal")
        self._header.add_action(tr("journal_collapse_all"), self._collapse_all, "normal")
        self._header.add_action(tr("journal_delete_selected"), self._delete_selected, "danger")
        root.addWidget(self._header)

        # ── شريط الفلاتر ──
        self._filter = _JournalFilterBar(self._get_safe_conn())
        self._connect_filter_signals()

        orig_reset = self._filter.reset
        def _reset_and_apply():
            orig_reset()
            self._apply_filter()
        self._filter.reset = _reset_and_apply

        self._filter.group_reloaded.connect(self._reconnect_group_signal)
        root.addWidget(self._filter)

        # ── الجدول ──
        self.table = QTableWidget()
        _cols = self._cols()
        self.table.setColumnCount(len(_cols))
        self.table.setHorizontalHeaderLabels(_cols)
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
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setWordWrap(False)
        self.table.cellClicked.connect(self._on_cell_clicked)
        root.addWidget(self.table, stretch=1)

        # ── شريط الحالة ──
        self._status = ListStatusBar()
        root.addWidget(self._status)

    def _connect_filter_signals(self):
        self._filter.inp_search.textChanged.connect(self._apply_filter)
        self._filter.cmb_group._tree_view.clicked.connect(
            lambda _: QTimer.singleShot(50, self._apply_filter)
        )
        self._filter.cmb_balance.currentIndexChanged.connect(self._apply_filter)
        self._filter.dt_from.dateChanged.connect(self._apply_filter)
        self._filter.dt_to.dateChanged.connect(self._apply_filter)

    def _reconnect_group_signal(self):
        try:
            self._filter.cmb_group._tree_view.clicked.connect(
                lambda _: QTimer.singleShot(50, self._apply_filter)
            )
        except Exception as e:
            print(f"[_JournalTreeTable] _reconnect_group_signal error: {e}")

    def _load(self):
        conn    = self._get_safe_conn()
        entries = fetch_all_entries(conn)
        self._entries_data = []
        for e in entries:
            lines = fetch_entry_lines(conn, e["id"])
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

    def _apply_filter(self):
        filtered = [e for e in self._entries_data if self._filter.matches(e)]
        self._filter.set_count(len(filtered), len(self._entries_data))
        self._status.set_count(len(filtered), len(self._entries_data))
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

            r = self.table.rowCount()
            self.table.insertRow(r)
            self._row_meta[r] = {"entry_id": eid, "is_parent": True, "is_child": False}

            self.table.setItem(r, 0, center_table_item(
                "▼" if expanded else "▶", color=_C["accent"], bold=True,
            ))
            self.table.setItem(r, 1, center_table_item(entry["date"], color=_C["success"], bold=True))
            self.table.setItem(r, 2, bold_table_item(entry["ref_no"],      _C["accent"]))
            self.table.setItem(r, 3, bold_table_item(entry["description"]))
            self.table.setItem(r, 4, bold_table_item(f"{total_dr:,.2f}",   _C["acc_type_asset"]))
            self.table.setItem(r, 5, bold_table_item(f"{total_cr:,.2f}",   _C["acc_type_liability"]))

            diff      = total_dr - total_cr
            bal_color = _C["success"] if abs(diff) < 0.01 else _C["danger"]
            bal_text  = tr("journal_status_balanced") if abs(diff) < 0.01 else tr("journal_status_unbalanced", diff=f"{abs(diff):,.2f}")
            self.table.setItem(r, 6, bold_table_item(bal_text, bal_color))

            set_row_background(self.table, r, _C["accent_light"])

            if expanded:
                for line in entry["lines"]:
                    rc = self.table.rowCount()
                    self.table.insertRow(rc)
                    self._row_meta[rc] = {
                        "entry_id": eid, "is_parent": False, "is_child": True
                    }

                    acc_name  = line.get("account_name", "")
                    acc_code  = line.get("account_code", "")
                    acc_type  = line.get("account_type", "")
                    acc_color = TYPE_COLORS.get(acc_type, _C["text_primary"])

                    prefix    = "    └─ "
                    desc_text = f"{prefix}{acc_code} — {acc_name}"
                    if line.get("description"):
                        desc_text += f"  │  {line['description']}"

                    is_dr  = line["debit"] > 0
                    row_bg = _C["journal_dr_bg"] if is_dr else _C["journal_cr_bg"]

                    for c in range(3):
                        self.table.setItem(rc, c, QTableWidgetItem(""))

                    self.table.setItem(rc, 3, colored_table_item(
                        desc_text, acc_color,
                        tooltip=f"{acc_code} — {acc_name}",
                    ))

                    if is_dr:
                        self.table.setItem(rc, 4, colored_table_item(f"{line['debit']:,.2f}",  _C["acc_type_asset"]))
                        self.table.setItem(rc, 5, QTableWidgetItem(""))
                    else:
                        self.table.setItem(rc, 4, QTableWidgetItem(""))
                        self.table.setItem(rc, 5, colored_table_item(f"{line['credit']:,.2f}", _C["acc_type_liability"]))

                    self.table.setItem(rc, 6, QTableWidgetItem(""))
                    set_row_background(self.table, rc, row_bg)

    def _on_cell_clicked(self, row, col):
        meta = self._row_meta.get(row)
        if not meta or not meta["is_parent"]:
            return
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
        from ui.widgets.dialogs.message import msg_info
        eid = self._selected_entry_id()
        if eid is None:
            msg_info(self, tr("warning"), tr("select_entry_first"))
            return
        entry_data = next(
            (e for e in self._entries_data if e["id"] == eid), None
        )
        desc = entry_data["description"] if entry_data else f"ID:{eid}"
        if confirm_delete(self, desc):
            delete_entry(self._get_safe_conn(), eid)
            self._expanded.discard(eid)
            emit_company_data_changed()