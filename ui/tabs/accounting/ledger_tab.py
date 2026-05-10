"""
ui/tabs/accounting/ledger_tab.py
==================================
LedgerTab — دفتر الأستاذ (حسابات T).

التحديثات:
  - التاريخ في عمود مستقل
  - فلاتر متكاملة: بحث + نوع الحساب + تصنيف + نطاق التاريخ
  - واجهة محسّنة مع إحصائيات سريعة
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem,
    QFrame, QLabel, QLineEdit, QHeaderView, QComboBox,
    QPushButton, QDateEdit, QGroupBox, QAbstractItemView,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui  import QColor, QFont

from db.accounting_repo import (
    fetch_all_accounts, fetch_t_account, get_normal_balance,
)
from db.accounting_schema import TYPE_AR
from ui.helpers import make_table, section_label
from ui.events  import bus
from .helpers   import TYPE_COLORS


# ══════════════════════════════════════════════════════════
# شريط الفلاتر
# ══════════════════════════════════════════════════════════

class _LedgerFilterBar(QFrame):
    """شريط فلاتر متكامل لدفتر الأستاذ."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: #f0f4ff;
                border: 1px solid #c5cae9;
                border-radius: 8px;
            }
        """)
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(8)

        # ── بحث بالبيان ──
        lbl_search = QLabel("🔍")
        lbl_search.setStyleSheet("background:transparent; border:none; font-size:13px;")
        lbl_search.setFixedWidth(20)

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("بحث في البيان أو رقم القيد...")
        self.inp_search.setMinimumHeight(30)
        self.inp_search.setStyleSheet("""
            QLineEdit {
                background: white; border: 1px solid #c5cae9;
                border-radius: 5px; padding: 2px 8px; font-size: 12px;
            }
            QLineEdit:focus { border-color: #1565c0; }
        """)

        # ── فلتر نوع الحركة ──
        self.cmb_move_type = QComboBox()
        self.cmb_move_type.setMinimumHeight(30)
        self.cmb_move_type.setFixedWidth(120)
        self.cmb_move_type.addItem("كل الحركات", None)
        self.cmb_move_type.addItem("مدين فقط", "dr")
        self.cmb_move_type.addItem("دائن فقط", "cr")
        self.cmb_move_type.setStyleSheet("""
            QComboBox {
                background: white; border: 1px solid #c5cae9;
                border-radius: 5px; padding: 2px 8px; font-size: 12px;
            }
            QComboBox:focus { border-color: #1565c0; }
            QComboBox::drop-down { border: none; }
        """)

        # ── فلتر التاريخ من ──
        sep1 = QLabel("│")
        sep1.setStyleSheet("color:#c5cae9; background:transparent; border:none; font-size:16px;")

        lbl_from = QLabel("من:")
        lbl_from.setStyleSheet("background:transparent; border:none; font-weight:bold; font-size:11px; color:#555;")

        self.dt_from = QDateEdit()
        self.dt_from.setCalendarPopup(True)
        self.dt_from.setDisplayFormat("yyyy-MM-dd")
        self.dt_from.setDate(QDate(2000, 1, 1))
        self.dt_from.setFixedWidth(115)
        self.dt_from.setMinimumHeight(30)
        self.dt_from.setStyleSheet("""
            QDateEdit {
                background: white; border: 1px solid #c5cae9;
                border-radius: 5px; padding: 2px 6px; font-size: 11px;
            }
            QDateEdit:focus { border-color: #1565c0; }
            QDateEdit::drop-down { border: none; }
        """)

        lbl_to = QLabel("إلى:")
        lbl_to.setStyleSheet("background:transparent; border:none; font-weight:bold; font-size:11px; color:#555;")

        self.dt_to = QDateEdit()
        self.dt_to.setCalendarPopup(True)
        self.dt_to.setDisplayFormat("yyyy-MM-dd")
        self.dt_to.setDate(QDate.currentDate())
        self.dt_to.setFixedWidth(115)
        self.dt_to.setMinimumHeight(30)
        self.dt_to.setStyleSheet(self.dt_from.styleSheet())

        # ── زر إعادة تعيين ──
        sep2 = QLabel("│")
        sep2.setStyleSheet(sep1.styleSheet())

        btn_reset = QPushButton("↺ مسح")
        btn_reset.setMinimumHeight(30)
        btn_reset.setFixedWidth(70)
        btn_reset.setStyleSheet("""
            QPushButton {
                background: #e8eaf6; border: 1px solid #c5cae9;
                border-radius: 5px; color: #3949ab;
                font-size: 11px; padding: 2px 8px;
            }
            QPushButton:hover { background: #c5cae9; }
        """)
        btn_reset.clicked.connect(self.reset)

        # ── عداد النتائج ──
        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet(
            "color:#1565c0; font-size:10px; font-weight:bold;"
            "background:transparent; border:none; min-width:60px;"
        )
        self.lbl_count.setAlignment(Qt.AlignCenter)

        lay.addWidget(lbl_search)
        lay.addWidget(self.inp_search, stretch=2)
        lay.addWidget(self.cmb_move_type)
        lay.addWidget(sep1)
        lay.addWidget(lbl_from)
        lay.addWidget(self.dt_from)
        lay.addWidget(lbl_to)
        lay.addWidget(self.dt_to)
        lay.addWidget(sep2)
        lay.addWidget(btn_reset)
        lay.addWidget(self.lbl_count)

    def reset(self):
        self.inp_search.clear()
        self.cmb_move_type.setCurrentIndex(0)
        self.dt_from.setDate(QDate(2000, 1, 1))
        self.dt_to.setDate(QDate.currentDate())

    def matches(self, line: dict) -> bool:
        """يتحقق إذا كانت الحركة تطابق الفلاتر."""
        q = self.inp_search.text().strip().lower()
        if q:
            desc  = (line.get("description") or "").lower()
            ref   = (line.get("ref_no") or "").lower()
            entry = (line.get("entry_desc") or "").lower()
            if q not in desc and q not in ref and q not in entry:
                return False

        move_type = self.cmb_move_type.currentData()
        if move_type == "dr" and not (line.get("debit", 0) > 0):
            return False
        if move_type == "cr" and not (line.get("credit", 0) > 0):
            return False

        date_str = line.get("date", "")
        if date_str:
            try:
                line_date = QDate.fromString(date_str, "yyyy-MM-dd")
                if line_date < self.dt_from.date() or line_date > self.dt_to.date():
                    return False
            except Exception:
                pass

        return True

    def set_count(self, shown: int, total: int):
        if shown == total:
            self.lbl_count.setText(f"({total})")
        else:
            self.lbl_count.setText(f"({shown}/{total})")


# ══════════════════════════════════════════════════════════
# بطاقات الإحصائيات
# ══════════════════════════════════════════════════════════

class _StatCards(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(0)

        def _card(icon, label, color):
            w = QWidget()
            w.setStyleSheet("background:transparent;")
            wl = QVBoxLayout(w)
            wl.setContentsMargins(12, 4, 12, 4)
            wl.setSpacing(2)
            lbl_t = QLabel(f"{icon}  {label}")
            lbl_t.setStyleSheet(
                f"font-size:10px; color:#888; background:transparent; border:none;"
            )
            lbl_v = QLabel("─")
            lbl_v.setStyleSheet(
                f"font-size:14px; font-weight:bold; color:{color};"
                "background:transparent; border:none;"
            )
            wl.addWidget(lbl_t)
            wl.addWidget(lbl_v)
            return w, lbl_v

        def _sep():
            s = QFrame()
            s.setFrameShape(QFrame.VLine)
            s.setStyleSheet("color:#e0e0e0; background:#e0e0e0;")
            s.setFixedWidth(1)
            return s

        w1, self.lbl_dr   = _card("📥", "إجمالي المدين",   "#1565c0")
        w2, self.lbl_cr   = _card("📤", "إجمالي الدائن",   "#c62828")
        w3, self.lbl_bal  = _card("⚖️", "الرصيد",           "#2e7d32")
        w4, self.lbl_cnt  = _card("🔢", "عدد الحركات",      "#6a1b9a")
        w5, self.lbl_nb   = _card("📌", "الرصيد الطبيعي",   "#e65100")

        for i, w in enumerate([w1, _sep(), w2, _sep(), w3, _sep(), w4, _sep(), w5]):
            if isinstance(w, QFrame):
                lay.addWidget(w)
            else:
                lay.addWidget(w, stretch=1)

    def update(self, total_dr: float, total_cr: float,
               balance: float, count: int, normal_balance: str, acc_type: str):
        self.lbl_dr.setText(f"{total_dr:,.2f}  ج")
        self.lbl_cr.setText(f"{total_cr:,.2f}  ج")

        bal_color = "#2e7d32" if balance >= 0 else "#c62828"
        self.lbl_bal.setText(f"{abs(balance):,.2f}  ج")
        self.lbl_bal.setStyleSheet(
            f"font-size:14px; font-weight:bold; color:{bal_color};"
            "background:transparent; border:none;"
        )

        self.lbl_cnt.setText(str(count))

        nb_ar    = "مدين (DR↑)" if normal_balance == "dr" else "دائن (CR↑)"
        type_ar  = TYPE_AR.get(acc_type, "")
        nb_color = "#1565c0" if normal_balance == "dr" else "#c62828"
        self.lbl_nb.setText(f"{nb_ar} — {type_ar}")
        self.lbl_nb.setStyleSheet(
            f"font-size:13px; font-weight:bold; color:{nb_color};"
            "background:transparent; border:none;"
        )

    def clear(self):
        for lbl in (self.lbl_dr, self.lbl_cr, self.lbl_bal, self.lbl_cnt, self.lbl_nb):
            lbl.setText("─")


# ══════════════════════════════════════════════════════════
# الجانب الأيسر: قائمة الحسابات مع بحث وفلاتر
# ══════════════════════════════════════════════════════════

class _AccountsPanel(QWidget):
    def __init__(self, conn, on_select, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._on_select = on_select
        self._all       = []
        self._build()
        self._refresh_accounts()
        bus.data_changed.connect(self._refresh_accounts)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        # ── عنوان ──
        hdr = QLabel("📚  الحسابات")
        hdr.setStyleSheet("""
            font-weight: bold;
            font-size: 13px;
            color: #1565c0;
            background: #e8f4fd;
            border: 1px solid #90caf9;
            border-radius: 6px;
            padding: 6px 12px;
        """)
        hdr.setAlignment(Qt.AlignCenter)
        root.addWidget(hdr)

        # ── فلتر النوع ──
        self.cmb_type = QComboBox()
        self.cmb_type.setMinimumHeight(28)
        self.cmb_type.addItem("── كل الأنواع ──", None)
        for key, label in TYPE_AR.items():
            self.cmb_type.addItem(label, key)
        self.cmb_type.setStyleSheet("""
            QComboBox {
                background: white; border: 1px solid #c5cae9;
                border-radius: 5px; padding: 2px 8px; font-size: 11px;
            }
            QComboBox::drop-down { border: none; }
        """)
        self.cmb_type.currentIndexChanged.connect(self._filter_accounts)
        root.addWidget(self.cmb_type)

        # ── بحث ──
        search_row = QHBoxLayout()
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍  بحث بالاسم أو الكود...")
        self.inp_search.setMinimumHeight(28)
        self.inp_search.setStyleSheet("""
            QLineEdit {
                background: white; border: 1px solid #c5cae9;
                border-radius: 5px; padding: 2px 8px; font-size: 11px;
            }
            QLineEdit:focus { border-color: #1565c0; }
        """)
        self.inp_search.textChanged.connect(self._filter_accounts)
        search_row.addWidget(self.inp_search)
        root.addLayout(search_row)

        # ── قائمة الحسابات ──
        self.lst = QTreeWidget()
        self.lst.setHeaderLabels(["الكود", "الاسم", "الرصيد"])
        hh = self.lst.header()
        hh.setSectionResizeMode(0, QHeaderView.Interactive)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Interactive)
        self.lst.setColumnWidth(0, 65)
        self.lst.setColumnWidth(2, 90)
        self.lst.setAlternatingRowColors(True)
        self.lst.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background: white;
            }
            QTreeWidget::item { padding: 3px 2px; }
            QTreeWidget::item:selected {
                background: #e3f2fd;
                color: #1565c0;
            }
            QTreeWidget::item:hover:!selected { background: #f5f5f5; }
        """)
        self.lst.itemSelectionChanged.connect(self._on_selected)
        root.addWidget(self.lst, stretch=1)

        # ── عداد ──
        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet(
            "color:#888; font-size:10px; background:transparent;"
            "border:none; padding:2px;"
        )
        self.lbl_count.setAlignment(Qt.AlignCenter)
        root.addWidget(self.lbl_count)

    def _refresh_accounts(self):
        self._all = fetch_all_accounts(self.conn)
        self._filter_accounts()

    def _filter_accounts(self):
        q         = self.inp_search.text().strip().lower()
        type_filt = self.cmb_type.currentData()

        self.lst.clear()
        count = 0

        for acc in self._all:
            if not acc["is_leaf"]:
                continue
            if type_filt and acc["type"] != type_filt:
                continue
            if q and q not in acc["name"].lower() and q not in acc["code"].lower():
                continue

            # حساب الرصيد
            try:
                bal_row = self.conn.execute("""
                    SELECT COALESCE(SUM(debit)-SUM(credit), 0) AS bal
                    FROM journal_lines WHERE account_id=?
                """, (acc["id"],)).fetchone()
                bal = bal_row["bal"] if bal_row else 0.0
            except Exception:
                bal = 0.0

            item = QTreeWidgetItem()
            item.setText(0, acc["code"])
            item.setText(1, acc["name"])
            item.setText(2, f"{bal:,.2f}")
            item.setData(0, Qt.UserRole, acc["id"])

            color = TYPE_COLORS.get(acc["type"], "#333")
            item.setForeground(0, QColor(color))
            item.setToolTip(1, f"{acc['code']} — {acc['name']}")

            if bal < 0:
                item.setForeground(2, QColor("#c62828"))
            elif bal > 0:
                item.setForeground(2, QColor("#2e7d32"))

            self.lst.addTopLevelItem(item)
            count += 1

        total = sum(1 for a in self._all if a["is_leaf"])
        if count == total:
            self.lbl_count.setText(f"({count} حساب)")
        else:
            self.lbl_count.setText(f"({count} / {total})")

    def _on_selected(self):
        items = self.lst.selectedItems()
        if not items:
            return
        acc_id = items[0].data(0, Qt.UserRole)
        if acc_id:
            self._on_select(acc_id)


# ══════════════════════════════════════════════════════════
# جدول حساب T — مع تاريخ مستقل وفلاتر
# ══════════════════════════════════════════════════════════

class _TAccountPanel(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._all_data = None   # كل بيانات الحساب المحمّل
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        # ── عنوان الحساب ──
        self.lbl_title = QLabel("اختر حسابًا من القائمة لعرض حركاته")
        self.lbl_title.setStyleSheet("""
            font-size: 13px;
            font-weight: bold;
            color: #1565c0;
            background: #e8f4fd;
            border: 1px solid #90caf9;
            border-radius: 8px;
            padding: 8px 16px;
        """)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setWordWrap(True)
        root.addWidget(self.lbl_title)

        # ── بطاقات الإحصائيات ──
        self._stats = _StatCards()
        root.addWidget(self._stats)

        # ── شريط الفلاتر ──
        self._filter = _LedgerFilterBar()
        self._filter.inp_search.textChanged.connect(self._apply_filter)
        self._filter.cmb_move_type.currentIndexChanged.connect(self._apply_filter)
        self._filter.dt_from.dateChanged.connect(self._apply_filter)
        self._filter.dt_to.dateChanged.connect(self._apply_filter)
        # زر مسح الفلاتر يستدعي reset ثم apply
        orig_reset = self._filter.reset
        def _reset_and_apply():
            orig_reset()
            self._apply_filter()
        self._filter.reset = _reset_and_apply
        root.addWidget(self._filter)

        # ── جدول حساب T ──
        t_frame = QFrame()
        t_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px solid #c5cae9;
                border-radius: 8px;
            }
        """)
        t_lay = QHBoxLayout(t_frame)
        t_lay.setContentsMargins(0, 0, 0, 0)
        t_lay.setSpacing(0)

        # جانب المدين
        dr_widget = QWidget()
        dr_widget.setStyleSheet("background: transparent;")
        dr_lay = QVBoxLayout(dr_widget)
        dr_lay.setContentsMargins(8, 8, 4, 8)
        dr_lay.setSpacing(4)

        dr_hdr = QLabel("📥  مدين  (DR)")
        dr_hdr.setAlignment(Qt.AlignCenter)
        dr_hdr.setStyleSheet("""
            font-weight: bold;
            color: #1565c0;
            font-size: 12px;
            background: #e3f2fd;
            border-radius: 5px;
            padding: 5px;
        """)
        dr_lay.addWidget(dr_hdr)

        self.t_dr_table = self._make_t_table()
        dr_lay.addWidget(self.t_dr_table, stretch=1)

        self.lbl_dr_total = QLabel("الإجمالي: 0.00")
        self.lbl_dr_total.setAlignment(Qt.AlignCenter)
        self.lbl_dr_total.setStyleSheet("""
            font-weight: bold; color: #1565c0; font-size: 11px;
            background: #e3f2fd; border-radius: 4px; padding: 4px 8px;
        """)
        dr_lay.addWidget(self.lbl_dr_total)

        # فاصل
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color: #1565c0; background: #c5cae9;")
        sep.setFixedWidth(2)

        # جانب الدائن
        cr_widget = QWidget()
        cr_widget.setStyleSheet("background: transparent;")
        cr_lay = QVBoxLayout(cr_widget)
        cr_lay.setContentsMargins(4, 8, 8, 8)
        cr_lay.setSpacing(4)

        cr_hdr = QLabel("📤  دائن  (CR)")
        cr_hdr.setAlignment(Qt.AlignCenter)
        cr_hdr.setStyleSheet("""
            font-weight: bold;
            color: #c62828;
            font-size: 12px;
            background: #fdecea;
            border-radius: 5px;
            padding: 5px;
        """)
        cr_lay.addWidget(cr_hdr)

        self.t_cr_table = self._make_t_table()
        cr_lay.addWidget(self.t_cr_table, stretch=1)

        self.lbl_cr_total = QLabel("الإجمالي: 0.00")
        self.lbl_cr_total.setAlignment(Qt.AlignCenter)
        self.lbl_cr_total.setStyleSheet("""
            font-weight: bold; color: #c62828; font-size: 11px;
            background: #fdecea; border-radius: 4px; padding: 4px 8px;
        """)
        cr_lay.addWidget(self.lbl_cr_total)

        t_lay.addWidget(dr_widget, stretch=1)
        t_lay.addWidget(sep)
        t_lay.addWidget(cr_widget, stretch=1)
        root.addWidget(t_frame, stretch=1)

        # ── شريط الرصيد ──
        self.lbl_balance = QLabel("الرصيد: —")
        self.lbl_balance.setAlignment(Qt.AlignCenter)
        self.lbl_balance.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #2e7d32;
            background: #f0faf0;
            border: 1px solid #a5d6a7;
            border-radius: 6px;
            padding: 6px 16px;
        """)
        root.addWidget(self.lbl_balance)

    def _make_t_table(self) -> QTableWidget:
        """ينشئ جدول حساب T مع عمود التاريخ المستقل."""
        tbl = QTableWidget()
        tbl.setColumnCount(4)
        tbl.setHorizontalHeaderLabels(["التاريخ", "رقم القيد", "البيان", "المبلغ"])
        tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tbl.setAlternatingRowColors(True)

        hh = tbl.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Fixed)
        hh.setSectionResizeMode(1, QHeaderView.Fixed)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.Fixed)
        tbl.setColumnWidth(0, 90)   # التاريخ
        tbl.setColumnWidth(1, 80)   # رقم القيد
        tbl.setColumnWidth(3, 90)   # المبلغ

        tbl.setStyleSheet("""
            QTableWidget {
                border: none;
                background: transparent;
                gridline-color: #f0f0f0;
            }
            QHeaderView::section {
                background: #fafafa;
                border: none;
                border-bottom: 1px solid #e0e0e0;
                padding: 4px;
                font-weight: bold;
                font-size: 11px;
                color: #555;
            }
        """)
        tbl.verticalHeader().setVisible(False)
        tbl.setShowGrid(True)
        return tbl

    def load(self, conn, account_id: int):
        data = fetch_t_account(conn, account_id)
        if not data:
            return

        self._all_data = data
        acc = data["account"]
        nb  = data["normal_balance"]

        # عنوان
        type_ar   = TYPE_AR.get(acc["type"], "")
        color     = TYPE_COLORS.get(acc["type"], "#1565c0")
        nb_ar     = "DR↑" if nb == "dr" else "CR↑"
        self.lbl_title.setText(
            f"📒  {acc['code']} — {acc['name']}  │  {type_ar}  │  رصيد طبيعي: {nb_ar}"
        )
        self.lbl_title.setStyleSheet(f"""
            font-size: 13px; font-weight: bold;
            color: {color};
            background: #f8f9ff;
            border: 1px solid {color}44;
            border-right: 4px solid {color};
            border-radius: 6px;
            padding: 8px 14px;
        """)

        self._apply_filter()

    def _apply_filter(self):
        if not self._all_data:
            return

        data    = self._all_data
        lines   = data["lines"]
        acc     = data["account"]
        nb      = data["normal_balance"]

        # تطبيق الفلاتر
        filtered = [ln for ln in lines if self._filter.matches(ln)]

        # ملء الجداول
        self.t_dr_table.setRowCount(0)
        self.t_cr_table.setRowCount(0)

        filt_dr = filt_cr = 0.0

        for line in filtered:
            if line["debit"] > 0:
                r = self.t_dr_table.rowCount()
                self.t_dr_table.insertRow(r)
                self._fill_t_row(self.t_dr_table, r, line, line["debit"], "#1565c0")
                filt_dr += line["debit"]

            if line["credit"] > 0:
                r = self.t_cr_table.rowCount()
                self.t_cr_table.insertRow(r)
                self._fill_t_row(self.t_cr_table, r, line, line["credit"], "#c62828")
                filt_cr += line["credit"]

        self.lbl_dr_total.setText(f"الإجمالي: {filt_dr:,.2f}")
        self.lbl_cr_total.setText(f"الإجمالي: {filt_cr:,.2f}")

        # رصيد المجموعة المفلترة
        filt_bal = filt_dr - filt_cr
        b_side   = "مدين" if filt_bal >= 0 else "دائن"
        b_color  = "#1565c0" if filt_bal >= 0 else "#c62828"
        self.lbl_balance.setText(f"الرصيد ({b_side}): {abs(filt_bal):,.2f}  ج")
        self.lbl_balance.setStyleSheet(f"""
            font-size:14px; font-weight:bold; color:{b_color};
            background:#f0f8ff; border:1px solid #90caf9;
            border-radius:6px; padding:6px 16px;
        """)

        # تحديث الإحصائيات
        total_count = len(lines)
        filt_count  = len(filtered)
        self._stats.update(
            filt_dr, filt_cr, filt_bal,
            filt_count, nb, acc["type"]
        )
        self._filter.set_count(filt_count, total_count)

    def _fill_t_row(self, tbl: QTableWidget, r: int, line: dict,
                    amount: float, color: str):
        """يملأ صف في جدول حساب T مع تاريخ مستقل."""
        # التاريخ
        date_item = QTableWidgetItem(line.get("date", "—"))
        date_item.setTextAlignment(Qt.AlignCenter)
        date_item.setForeground(QColor("#555"))
        tbl.setItem(r, 0, date_item)

        # رقم القيد
        ref_item = QTableWidgetItem(line.get("ref_no", "—"))
        ref_item.setTextAlignment(Qt.AlignCenter)
        ref_item.setForeground(QColor("#1565c0"))
        tbl.setItem(r, 1, ref_item)

        # البيان
        desc = line.get("description") or line.get("entry_desc") or "—"
        desc_item = QTableWidgetItem(desc)
        desc_item.setToolTip(f"{line.get('date','—')}  {desc}")
        tbl.setItem(r, 2, desc_item)

        # المبلغ
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
        self.lbl_dr_total.setText("الإجمالي: 0.00")
        self.lbl_cr_total.setText("الإجمالي: 0.00")
        self.lbl_balance.setText("الرصيد: —")
        self._stats.clear()
        self.lbl_title.setText("اختر حسابًا من القائمة لعرض حركاته")
        self.lbl_title.setStyleSheet("""
            font-size: 13px; font-weight: bold; color: #1565c0;
            background: #e8f4fd; border: 1px solid #90caf9;
            border-radius: 8px; padding: 8px 16px;
        """)


# ══════════════════════════════════════════════════════════
# التبويب الرئيسي
# ══════════════════════════════════════════════════════════

class LedgerTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background: #e0e0e0;
            }
            QSplitter::handle:hover { background: #bbdefb; }
        """)

        # ── يسار: قائمة الحسابات ──
        left = QWidget()
        ll   = QVBoxLayout(left)
        ll.setContentsMargins(10, 10, 6, 10)
        ll.setSpacing(0)

        self._accounts_panel = _AccountsPanel(
            self.conn,
            on_select=self._on_account_selected
        )
        ll.addWidget(self._accounts_panel)
        splitter.addWidget(left)

        # ── يمين: تفاصيل الحساب ──
        right = QWidget()
        rl    = QVBoxLayout(right)
        rl.setContentsMargins(6, 10, 10, 10)
        rl.setSpacing(0)

        self._t_panel = _TAccountPanel(self.conn)
        rl.addWidget(self._t_panel)
        splitter.addWidget(right)

        splitter.setSizes([240, 760])
        root.addWidget(splitter)

    def _on_account_selected(self, acc_id: int):
        self._t_panel.load(self.conn, acc_id)