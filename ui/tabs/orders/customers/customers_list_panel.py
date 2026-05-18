"""
ui/tabs/orders/customers/customers_list_panel.py
=================================================
لوحة قائمة العملاء — جدول بعرض ثابت على المحتوى.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QLabel, QLineEdit, QPushButton,
    QTableWidget, QHeaderView, QComboBox,
    QAbstractItemView, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

from db.orders.customers_repo import fetch_all_customers

from ui.widgets.shared.table_utils import (
    make_table_item, color_item, bold_item, muted_item,
    auto_fit_columns, fit_table_to_content, ROW_HEIGHT_LARGE,
    make_list_table,
)
from ui.app_settings import _C

_BG    = _C['bg_input']
_WHITE = "#ffffff"
_BLUE  = _C['accent']
_BORDER = _C['border']

_COMBO_SS = f"""
    QComboBox {{
        background: {_C['bg_surface_2']}; border: 1px solid {_C['border_med']};
        border-radius: 5px; padding: 0 8px; min-height: 28px;
        font-size: 11px; color: {_C['text_primary']};
    }}
    QComboBox:focus {{ border-color: {_BLUE}; }}
    QComboBox::drop-down {{ border: none; width: 16px; }}
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
        # الـ list panel عرضه ثابت
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self._build()
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── toolbar ──
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
                background: {_BG}; border: 1px solid {_C['border_med']};
                border-radius: 6px; padding: 0 10px; font-size: 12px;
            }}
            QLineEdit:focus {{ border-color: {_BLUE}; background: {_WHITE}; }}
        """)
        self.inp_search.textChanged.connect(lambda: self._timer.start())

        btn_new = QPushButton("＋  عميل جديد")
        btn_new.setMinimumHeight(34)
        btn_new.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn_new.setStyleSheet(f"""
            QPushButton {{
                background: {_BLUE}; color: white;
                border: none; border-radius: 6px;
                padding: 0 14px; font-weight: bold; font-size: 12px;
            }}
            QPushButton:hover {{ background: {_C['accent_hover']}; }}
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

        # ── الجدول — عرض ثابت ──
        self.table = make_list_table(
            columns=["الكود", "الاسم", "الهاتف", "المدينة", "الطلبات"],
            stretch_col=1,
            col_widths={0: 80, 2: 110, 3: 80, 4: 55},
        )
        # لا نسمح بـ horizontal scroll — العرض مضبوط
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.itemSelectionChanged.connect(self._on_select)
        root.addWidget(self.table, stretch=1)

        # ── status bar ──
        self._status_bar = QLabel("")
        self._status_bar.setAlignment(Qt.AlignCenter)
        self._status_bar.setStyleSheet(f"""
            background: {_C['bg_surface_2']}; color: {_C['text_muted']};
            padding: 5px; font-size: 10px; font-weight: 600;
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
            # اضبط عرض الأعمدة على المحتوى
            auto_fit_columns(self.table, fixed_cols=[0, 2, 3, 4],
                             stretch_col=1, min_width=40, max_width=180)
            # اضبط عرض الـ widget على قد الجدول
            from ui.widgets.shared.table_utils import calc_table_width
            w = calc_table_width(self.table, padding=12)
            self.setFixedWidth(max(280, min(w, 560)))

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