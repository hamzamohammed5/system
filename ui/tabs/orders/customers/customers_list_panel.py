"""
ui/tabs/orders/customers/customers_list_panel.py
=================================================
لوحة قائمة العملاء — منقولة من customers_tab.py
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QLabel, QLineEdit, QPushButton,
    QTableWidget, QHeaderView, QComboBox,
    QAbstractItemView,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

from db.orders.customers_repo import fetch_all_customers

from ui.widgets.shared.table_utils import (
    make_table_item, color_item, bold_item, muted_item,
    auto_fit_columns, ROW_HEIGHT_LARGE,
)
from ui.app_settings import _C

_BG     = "#f8f9fb"
_WHITE  = "#ffffff"
_BLUE   = "#1565c0"
_BORDER = "#e5e9f0"

_COMBO_SS = f"""
    QComboBox {{
        background: {_BG}; border: 1px solid #cdd3e0;
        border-radius: 5px; padding: 0 8px; min-height: 28px;
    }}
    QComboBox:focus {{ border-color: {_BLUE}; }}
    QComboBox::drop-down {{ border: none; }}
"""


class CustomersListPanel(QWidget):
    customer_selected = pyqtSignal(int)
    new_customer      = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._all_rows = []
        self._timer    = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._apply_filter)
        self._build()
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── شريط الأدوات ──
        toolbar = QFrame()
        toolbar.setStyleSheet(f"""
            QFrame {{ background: {_WHITE}; border-bottom: 1px solid {_BORDER}; }}
        """)
        tb = QVBoxLayout(toolbar)
        tb.setContentsMargins(10, 10, 10, 10)
        tb.setSpacing(6)

        row1 = QHBoxLayout()
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("بحث بالاسم أو الهاتف أو الكود...")
        self.inp_search.setMinimumHeight(34)
        self.inp_search.setClearButtonEnabled(True)
        self.inp_search.setStyleSheet(f"""
            QLineEdit {{
                background: {_BG}; border: 1px solid #cdd3e0;
                border-radius: 6px; padding: 0 10px; font-size: 12px;
            }}
            QLineEdit:focus {{ border-color: {_BLUE}; background: {_WHITE}; }}
        """)
        self.inp_search.textChanged.connect(lambda: self._timer.start())

        btn_new = QPushButton("＋  عميل جديد")
        btn_new.setMinimumHeight(34)
        btn_new.setStyleSheet(f"""
            QPushButton {{
                background: {_BLUE}; color: white;
                border: none; border-radius: 6px;
                padding: 0 14px; font-weight: bold; font-size: 12px;
            }}
            QPushButton:hover {{ background: #0d47a1; }}
        """)
        btn_new.clicked.connect(self.new_customer.emit)
        row1.addWidget(self.inp_search, stretch=1)
        row1.addWidget(btn_new)
        tb.addLayout(row1)

        row2 = QHBoxLayout()
        self.cmb_type = QComboBox()
        self.cmb_type.setMinimumHeight(28)
        self.cmb_type.addItem("كل الأنواع", None)
        self.cmb_type.addItem("أفراد", "individual")
        self.cmb_type.addItem("شركات", "company")
        self.cmb_type.setStyleSheet(_COMBO_SS)
        self.cmb_type.currentIndexChanged.connect(self._apply_filter)

        self.cmb_active = QComboBox()
        self.cmb_active.setMinimumHeight(28)
        self.cmb_active.addItem("الكل", None)
        self.cmb_active.addItem("نشط", 1)
        self.cmb_active.addItem("غير نشط", 0)
        self.cmb_active.setStyleSheet(_COMBO_SS)
        self.cmb_active.currentIndexChanged.connect(self._apply_filter)

        row2.addWidget(self.cmb_type, stretch=1)
        row2.addWidget(self.cmb_active, stretch=1)
        tb.addLayout(row2)
        root.addWidget(toolbar)

        # ── الجدول ──
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["الكود", "الاسم", "الهاتف", "المدينة", "الطلبات"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: none; background: {_WHITE};
                alternate-background-color: #fafbff; outline: none;
            }}
            QTableWidget::item {{ padding: 6px 10px; border-bottom: 1px solid {_BORDER}; }}
            QTableWidget::item:selected {{ background: #dbeafe; color: #1e40af; }}
            QTableWidget::item:hover {{ background: {_C['bg_hover']}; }}
            QHeaderView::section {{
                background: {_BG}; color: {_BLUE}; font-weight: bold; font-size:11px;
                padding: 6px 10px; border: none; border-bottom: 2px solid {_BORDER};
                border-right: 1px solid {_BORDER};
            }}
            QHeaderView::section:hover {{
                background: {_C['bg_hover']}; color: {_C['text_primary']};
            }}
        """)

        hh = self.table.horizontalHeader()
        hh.setSectionsMovable(False)
        hh.setSectionResizeMode(0, QHeaderView.Interactive)
        self.table.setColumnWidth(0, 80)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Interactive)
        self.table.setColumnWidth(2, 110)
        hh.setSectionResizeMode(3, QHeaderView.Interactive)
        self.table.setColumnWidth(3, 80)
        hh.setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(4, 55)
        hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hh.setMinimumSectionSize(40)

        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.itemSelectionChanged.connect(self._on_select)
        self.table.doubleClicked.connect(self._on_select)
        root.addWidget(self.table, stretch=1)

        # ── شريط الحالة ──
        self._status_bar = QLabel("")
        self._status_bar.setAlignment(Qt.AlignCenter)
        self._status_bar.setStyleSheet(f"""
            background: {_BG}; color: #6b7280;
            padding: 5px; font-size: 11px;
            border-top: 1px solid {_BORDER};
        """)
        root.addWidget(self._status_bar)

    def _load(self):
        self._all_rows = fetch_all_customers(self.conn)
        self._apply_filter()

    def _apply_filter(self):
        q      = self.inp_search.text().strip().lower()
        typ    = self.cmb_type.currentData()
        active = self.cmb_active.currentData()

        filtered = [
            r for r in self._all_rows
            if (typ is None or r["customer_type"] == typ)
            and (active is None or r["is_active"] == active)
            and (not q or q in (r["name"] or "").lower()
                      or q in (r["phone"] or "").lower()
                      or q in (r["code"] or "").lower())
        ]

        self.table.setRowCount(0)
        for row in filtered:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, ROW_HEIGHT_LARGE)

            code_item = make_table_item(row["code"] or "", user_data=row["id"],
                                        tooltip=row["code"] or "")
            muted_item(code_item)
            self.table.setItem(r, 0, code_item)

            name_item = make_table_item(row["name"], tooltip=row["name"])
            if not row["is_active"]:
                color_item(name_item, "#9ca3af")
            else:
                bold_item(name_item, also_medium=True)
            self.table.setItem(r, 1, name_item)

            self.table.setItem(r, 2, muted_item(make_table_item(
                row["phone"] or "—", tooltip=row["phone"] or "")))
            self.table.setItem(r, 3, muted_item(make_table_item(
                row["city"] or "—", tooltip=row["city"] or "")))

            cnt_item = make_table_item(str(row["orders_count"] or 0),
                                       align=Qt.AlignCenter)
            color_item(cnt_item, _BLUE)
            self.table.setItem(r, 4, cnt_item)

        cnt   = len(filtered)
        total = len(self._all_rows)
        self._status_bar.setText(
            f"{cnt} عميل" if cnt == total else f"{cnt} من {total} عميل"
        )

        if filtered:
            auto_fit_columns(self.table, fixed_cols=[0, 2, 3],
                             stretch_col=1, min_width=55, max_width=180)

    def _on_select(self):
        row = self.table.currentRow()
        if row < 0:
            return
        item = self.table.item(row, 0)
        if item:
            self.customer_selected.emit(item.data(Qt.UserRole))

    def select_customer(self, cid: int):
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item and item.data(Qt.UserRole) == cid:
                self.table.selectRow(r)
                break

    def refresh(self):
        self._load()