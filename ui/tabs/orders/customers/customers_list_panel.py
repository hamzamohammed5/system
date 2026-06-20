"""
ui/tabs/orders/customers/customers_list_panel.py
=================================================
لوحة قائمة العملاء — ترث من BaseListPanel.

✅ الـ panel عرضه محدود بـ MIN_W → MAX_W
✅ الـ handle في الـ splitter مش بيتحرك أكتر من MAX_W
"""

from PyQt5.QtWidgets import (
    QHBoxLayout, QComboBox, QPushButton, QSizePolicy, QLineEdit,
    QVBoxLayout,
)
from PyQt5.QtCore import Qt, pyqtSignal

from db.orders.customers_repo import fetch_all_customers

from ui.widgets.base.list_panel import BaseListPanel
from ui.widgets.tables.tables import make_item, colored_item, bold_item, muted_item
from ui.widgets.core.i18n import tr
from ui.theme import _C
from ui.font import FS_BASE, FS_SM


def _combo_ss() -> str:
    return f"""
        QComboBox {{
            background: {_C['bg_surface_2']}; border: 1px solid {_C['border_med']};
            border-radius: 5px; padding: 0 8px; min-height: 28px;
            font-size: {FS_SM}px; color: {_C['text_primary']};
        }}
        QComboBox:focus {{ border-color: {_C['accent']}; }}
        QComboBox::drop-down {{ border: none; width: 16px; }}
    """


class CustomersListPanel(BaseListPanel):
    customer_selected = pyqtSignal(int)
    new_customer      = pyqtSignal()

    COLUMNS     = []
    STRETCH_COL = -1
    COL_WIDTHS  = {0: 80, 1: 160, 2: 110, 3: 80, 4: 55}
    MIN_W       = 280
    MAX_W       = 560
    EMPTY_ICON  = "👥"
    EMPTY_TITLE = "no_customers"

    def __init__(self, conn, parent=None):
        self.COLUMNS = [
            tr("customer_col_code"), tr("customer_col_name"),
            tr("customer_col_phone"), tr("customer_col_city"),
            tr("customer_col_orders"),
        ]
        self._type_filter   = None
        self._active_filter = None
        super().__init__(conn=conn, parent=parent)
        self.item_selected.connect(self.customer_selected.emit)

    # ══════════════════════════════════════════════════════
    # toolbar إضافي
    # ══════════════════════════════════════════════════════

    def _build_toolbar(self, lay: QVBoxLayout):
        # ── صف 1: بحث + زر جديد ──
        row1 = QHBoxLayout()

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText(tr("order_customer_search"))
        self.inp_search.setFixedHeight(34)
        self.inp_search.setClearButtonEnabled(True)
        self.inp_search.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.inp_search.setStyleSheet(f"""
            QLineEdit {{
                background: {_C['bg_input']}; border: 1px solid {_C['border_med']};
                border-radius: 6px; padding: 0 10px; font-size: {FS_BASE}px;
            }}
            QLineEdit:focus {{ border-color: {_C['accent']}; background: {_C['bg_surface']}; }}
        """)
        self.inp_search.textChanged.connect(lambda: self._timer.start())

        btn_new = QPushButton(tr("customer_new_btn"))
        btn_new.setFixedHeight(34)
        btn_new.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn_new.setStyleSheet(f"""
            QPushButton {{
                background: {_C['accent']}; color: white;
                border: none; border-radius: 6px;
                padding: 0 14px; font-weight: bold; font-size: {FS_BASE}px;
            }}
            QPushButton:hover {{ background: {_C['accent_hover']}; }}
        """)
        btn_new.clicked.connect(self.new_customer.emit)

        row1.addWidget(self.inp_search, stretch=1)
        row1.addWidget(btn_new)
        lay.addLayout(row1)

        # ── صف 2: فلاتر ──
        row2 = QHBoxLayout()

        self.cmb_type = QComboBox()
        self.cmb_type.setFixedHeight(28)
        self.cmb_type.addItem(tr("filter_all"), None)
        self.cmb_type.addItem(tr("customer_type_individual"), "individual")
        self.cmb_type.addItem(tr("customer_type_company"), "company")
        self.cmb_type.setStyleSheet(_combo_ss())
        self.cmb_type.currentIndexChanged.connect(self._on_combo_changed)

        self.cmb_active = QComboBox()
        self.cmb_active.setFixedHeight(28)
        self.cmb_active.addItem(tr("all"), None)
        self.cmb_active.addItem(tr("customer_toggle_active"), 1)
        self.cmb_active.addItem(tr("customer_toggle_inactive"), 0)
        self.cmb_active.setStyleSheet(_combo_ss())
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
        code_item = make_item(row["code"] or "", user_data=row["id"],
                              tooltip=row["code"] or "")
        muted_item(code_item)
        table.setItem(r, 0, code_item)

        name_item = make_item(row["name"], tooltip=row["name"])
        if not row["is_active"]:
            from PyQt5.QtGui import QColor
            name_item.setForeground(QColor(_C['text_disabled']))
        else:
            bold_item(name_item)
        table.setItem(r, 1, name_item)

        table.setItem(r, 2, muted_item(make_item(
            row["phone"] or "—", tooltip=row["phone"] or "")))
        table.setItem(r, 3, muted_item(make_item(
            row["city"] or "—", tooltip=row["city"] or "")))

        cnt_item = make_item(str(row["orders_count"] or 0),
                             align=Qt.AlignCenter)
        from PyQt5.QtGui import QColor
        cnt_item.setForeground(QColor(_C['accent']))
        table.setItem(r, 4, cnt_item)

    # ══════════════════════════════════════════════════════
    # API
    # ══════════════════════════════════════════════════════

    def select_customer(self, cid: int):
        self.select_item(cid)