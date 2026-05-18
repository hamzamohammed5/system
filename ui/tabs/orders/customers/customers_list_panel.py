"""
ui/tabs/orders/customers/customers_list_panel.py
=================================================
لوحة قائمة العملاء — ترث من BaseListPanel.
عرض ثابت على المحتوى، لا يتمدد مع النافذة، بدون horizontal scroll.
"""

from PyQt5.QtWidgets import (
    QHBoxLayout, QComboBox, QPushButton, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal

from db.orders.customers_repo import fetch_all_customers

from ui.widgets.shared.base_list_panel import BaseListPanel
from ui.widgets.shared.table_utils import (
    make_table_item, color_item, bold_item, muted_item,
)
from ui.app_settings import _C

_BLUE   = _C['accent']

_COMBO_SS = f"""
    QComboBox {{
        background: {_C['bg_surface_2']}; border: 1px solid {_C['border_med']};
        border-radius: 5px; padding: 0 8px; min-height: 28px;
        font-size: 11px; color: {_C['text_primary']};
    }}
    QComboBox:focus {{ border-color: {_BLUE}; }}
    QComboBox::drop-down {{ border: none; width: 16px; }}
"""


class CustomersListPanel(BaseListPanel):
    customer_selected = pyqtSignal(int)   # alias لـ item_selected
    new_customer      = pyqtSignal()

    COLUMNS     = ["الكود", "الاسم", "الهاتف", "المدينة", "الطلبات"]
    STRETCH_COL = 1
    COL_WIDTHS  = {0: 80, 2: 110, 3: 80, 4: 55}
    MIN_W       = 280
    MAX_W       = 560
    EMPTY_ICON  = "👥"
    EMPTY_TITLE = "لا يوجد عملاء"

    def __init__(self, conn, parent=None):
        self._type_filter   = None
        self._active_filter = None
        super().__init__(conn=conn, parent=parent)
        # ربط item_selected بـ customer_selected
        self.item_selected.connect(self.customer_selected.emit)

    # ══════════════════════════════════════════════════════
    # toolbar إضافي — زر جديد + فلاتر
    # ══════════════════════════════════════════════════════

    def _build_toolbar(self, lay):
        from PyQt5.QtWidgets import QVBoxLayout as QVL, QHBoxLayout as QHL, QLineEdit

        # صف 1: بحث + زر جديد
        row1 = QHL()
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("بحث بالاسم أو الهاتف أو الكود...")
        self.inp_search.setMinimumHeight(34)
        self.inp_search.setClearButtonEnabled(True)
        self.inp_search.setStyleSheet(f"""
            QLineEdit {{
                background: {_C['bg_input']}; border: 1px solid {_C['border_med']};
                border-radius: 6px; padding: 0 10px; font-size: 12px;
            }}
            QLineEdit:focus {{ border-color: {_BLUE}; background: white; }}
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
        lay.addLayout(row1)

        # صف 2: فلاتر النوع والنشاط
        row2 = QHL()
        self.cmb_type = QComboBox()
        self.cmb_type.setMinimumHeight(28)
        self.cmb_type.addItem("كل الأنواع", None)
        self.cmb_type.addItem("أفراد", "individual")
        self.cmb_type.addItem("شركات", "company")
        self.cmb_type.setStyleSheet(_COMBO_SS)
        self.cmb_type.currentIndexChanged.connect(self._on_combo_changed)

        self.cmb_active = QComboBox()
        self.cmb_active.setMinimumHeight(28)
        self.cmb_active.addItem("الكل", None)
        self.cmb_active.addItem("نشط", 1)
        self.cmb_active.addItem("غير نشط", 0)
        self.cmb_active.setStyleSheet(_COMBO_SS)
        self.cmb_active.currentIndexChanged.connect(self._on_combo_changed)

        row2.addWidget(self.cmb_type, stretch=1)
        row2.addWidget(self.cmb_active, stretch=1)
        lay.addLayout(row2)

    def _on_combo_changed(self):
        self._type_filter   = self.cmb_type.currentData()
        self._active_filter = self.cmb_active.currentData()
        self._apply_filter()

    # ══════════════════════════════════════════════════════
    # data
    # ══════════════════════════════════════════════════════

    def _load_rows(self) -> list:
        return fetch_all_customers(self.conn)

    def _match_filter(self, row, q: str) -> bool:
        typ    = getattr(self, '_type_filter',   None)
        active = getattr(self, '_active_filter', None)
        if typ    is not None and row["customer_type"] != typ:    return False
        if active is not None and row["is_active"]     != active: return False
        if q and q not in (row["name"]  or "").lower() \
              and q not in (row["phone"] or "").lower() \
              and q not in (row["code"]  or "").lower():
            return False
        return True

    def _fill_row(self, table, r, row):
        code_item = make_table_item(row["code"] or "", user_data=row["id"],
                                    tooltip=row["code"] or "")
        muted_item(code_item)
        table.setItem(r, 0, code_item)

        name_item = make_table_item(row["name"], tooltip=row["name"])
        if not row["is_active"]:
            color_item(name_item, "#9ca3af")
        else:
            bold_item(name_item, also_medium=True)
        table.setItem(r, 1, name_item)

        table.setItem(r, 2, muted_item(make_table_item(
            row["phone"] or "—", tooltip=row["phone"] or "")))
        table.setItem(r, 3, muted_item(make_table_item(
            row["city"] or "—", tooltip=row["city"] or "")))

        from ui.widgets.shared.table_utils import color_item as ci
        cnt_item = make_table_item(str(row["orders_count"] or 0),
                                   align=Qt.AlignCenter)
        ci(cnt_item, _BLUE)
        table.setItem(r, 4, cnt_item)

    # ══════════════════════════════════════════════════════
    # API
    # ══════════════════════════════════════════════════════

    def select_customer(self, cid: int):
        self.select_item(cid)