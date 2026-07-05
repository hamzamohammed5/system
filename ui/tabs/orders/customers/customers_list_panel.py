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

from services.orders.customer_service import CustomerService

from ui.widgets.base.list_panel import BaseListPanel
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.widgets.tables.tables import make_item, colored_item, bold_item, muted_item
from ui.widgets.core.i18n import tr
from ui.constants import (
    LIST_PANEL_MIN_W, LIST_PANEL_MAX_W,
    SEARCH_BAR_H, FILTER_SEARCH_H,
    CUSTOMERS_LIST_COL_CODE_W, CUSTOMERS_LIST_COL_NAME_W,
    CUSTOMERS_LIST_COL_PHONE_W, CUSTOMERS_LIST_COL_CITY_W,
    CUSTOMERS_LIST_COL_ORDERS_W,
)


class CustomersListPanel(BaseListPanel, WidgetMixin):
    customer_selected = pyqtSignal(int)
    new_customer      = pyqtSignal()

    COLUMNS     = []
    STRETCH_COL = -1
    COL_WIDTHS  = {
        0: CUSTOMERS_LIST_COL_CODE_W,
        1: CUSTOMERS_LIST_COL_NAME_W,
        2: CUSTOMERS_LIST_COL_PHONE_W,
        3: CUSTOMERS_LIST_COL_CITY_W,
        4: CUSTOMERS_LIST_COL_ORDERS_W,
    }
    MIN_W       = LIST_PANEL_MIN_W
    MAX_W       = LIST_PANEL_MAX_W
    EMPTY_ICON  = "👥"
    EMPTY_TITLE = "no_customers"

    def __init__(self, conn, parent=None):
        self._svc = CustomerService(conn)
        self._type_filter   = None
        self._active_filter = None
        super().__init__(conn=conn, parent=parent)
        self._init_widget_mixin(data=False)
        self._refresh_lang()
        self._refresh_style()
        self.item_selected.connect(self.customer_selected.emit)

    def _refresh_style(self, *_):
        from ui.theme import _C
        from ui.font import FS_SM, FS_BASE
        _combo_ss = f"""
            QComboBox {{
                background: {_C['bg_surface_2']}; border: 1px solid {_C['border_med']};
                border-radius: 5px; padding: 0 8px; min-height: {FILTER_SEARCH_H}px;
                font-size: {FS_SM}px; color: {_C['text_primary']};
            }}
            QComboBox:focus {{ border-color: {_C['accent']}; }}
            QComboBox::drop-down {{ border: none; width: 16px; }}
        """
        _search_ss = f"""
            QLineEdit {{
                background: {_C['bg_input']}; border: 1px solid {_C['border_med']};
                border-radius: 6px; padding: 0 10px; font-size: {FS_BASE}px;
            }}
            QLineEdit:focus {{ border-color: {_C['accent']}; background: {_C['bg_surface']}; }}
        """
        _btn_ss = f"""
            QPushButton {{
                background: {_C['accent']}; color: {_C['btn_primary_text']};
                border: none; border-radius: 6px;
                padding: 0 14px; font-weight: bold; font-size: {FS_BASE}px;
            }}
            QPushButton:hover {{ background: {_C['accent_hover']}; }}
        """
        if hasattr(self, 'inp_search'):
            self.inp_search.setStyleSheet(_search_ss)
        if hasattr(self, '_btn_new'):
            self._btn_new.setStyleSheet(_btn_ss)
        if hasattr(self, 'cmb_type'):
            self.cmb_type.setStyleSheet(_combo_ss)
        if hasattr(self, 'cmb_active'):
            self.cmb_active.setStyleSheet(_combo_ss)

    def _refresh_lang(self, *_):
        if hasattr(self, 'inp_search'):
            self.inp_search.setPlaceholderText(tr("order_customer_search"))
        if hasattr(self, '_btn_new'):
            self._btn_new.setText(tr("customer_new_btn"))
        if hasattr(self, 'cmb_type') and self.cmb_type.count() == 0:
            self.cmb_type.addItem(tr("filter_all"), None)
            self.cmb_type.addItem(tr("customer_type_individual"), "individual")
            self.cmb_type.addItem(tr("customer_type_company"), "company")
        if hasattr(self, 'cmb_active') and self.cmb_active.count() == 0:
            self.cmb_active.addItem(tr("all"), None)
            self.cmb_active.addItem(tr("customer_toggle_active"), 1)
            self.cmb_active.addItem(tr("customer_toggle_inactive"), 0)
        self.COLUMNS = [
            tr("customer_col_code"), tr("customer_col_name"),
            tr("customer_col_phone"), tr("customer_col_city"),
            tr("customer_col_orders"),
        ]

    # ══════════════════════════════════════════════════════
    # toolbar إضافي
    # ══════════════════════════════════════════════════════

    def _build_toolbar(self, lay: QVBoxLayout):
        from ui.theme import _C
        from ui.font import FS_BASE, FS_SM
        # ── صف 1: بحث + زر جديد ──
        row1 = QHBoxLayout()

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText(tr("order_customer_search"))
        self.inp_search.setFixedHeight(SEARCH_BAR_H)
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

        self._btn_new = QPushButton(tr("customer_new_btn"))
        self._btn_new.setFixedHeight(SEARCH_BAR_H)
        self._btn_new.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._btn_new.setStyleSheet(f"""
            QPushButton {{
                background: {_C['accent']}; color: {_C['btn_primary_text']};
                border: none; border-radius: 6px;
                padding: 0 14px; font-weight: bold; font-size: {FS_BASE}px;
            }}
            QPushButton:hover {{ background: {_C['accent_hover']}; }}
        """)
        self._btn_new.clicked.connect(self.new_customer.emit)

        row1.addWidget(self.inp_search, stretch=1)
        row1.addWidget(self._btn_new)
        lay.addLayout(row1)

        # ── صف 2: فلاتر ──
        row2 = QHBoxLayout()

        _combo_ss = f"""
            QComboBox {{
                background: {_C['bg_surface_2']}; border: 1px solid {_C['border_med']};
                border-radius: 5px; padding: 0 8px; min-height: {FILTER_SEARCH_H}px;
                font-size: {FS_SM}px; color: {_C['text_primary']};
            }}
            QComboBox:focus {{ border-color: {_C['accent']}; }}
            QComboBox::drop-down {{ border: none; width: 16px; }}
        """

        self.cmb_type = QComboBox()
        self.cmb_type.setFixedHeight(FILTER_SEARCH_H)
        self.cmb_type.addItem(tr("filter_all"), None)
        self.cmb_type.addItem(tr("customer_type_individual"), "individual")
        self.cmb_type.addItem(tr("customer_type_company"), "company")
        self.cmb_type.setStyleSheet(_combo_ss)
        self.cmb_type.currentIndexChanged.connect(self._on_combo_changed)

        self.cmb_active = QComboBox()
        self.cmb_active.setFixedHeight(FILTER_SEARCH_H)
        self.cmb_active.addItem(tr("all"), None)
        self.cmb_active.addItem(tr("customer_toggle_active"), 1)
        self.cmb_active.addItem(tr("customer_toggle_inactive"), 0)
        self.cmb_active.setStyleSheet(_combo_ss)
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
        return self._svc.list_customers()

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
        from PyQt5.QtGui import QColor
        from ui.theme import _C
        code_item = make_item(row["code"] or "", user_data=row["id"],
                              tooltip=row["code"] or "")
        muted_item(code_item)
        table.setItem(r, 0, code_item)

        name_item = make_item(row["name"], tooltip=row["name"])
        if not row["is_active"]:
            name_item.setForeground(QColor(_C['text_disabled']))
        else:
            bold_item(name_item)
        table.setItem(r, 1, name_item)

        table.setItem(r, 2, muted_item(make_item(
            row["phone"] or tr("dash"), tooltip=row["phone"] or "")))
        table.setItem(r, 3, muted_item(make_item(
            row["city"] or tr("dash"), tooltip=row["city"] or "")))

        cnt_item = make_item(str(row["orders_count"] or 0),
                             align=Qt.AlignCenter)
        cnt_item.setForeground(QColor(_C['accent']))
        table.setItem(r, 4, cnt_item)

    # ══════════════════════════════════════════════════════
    # API
    # ══════════════════════════════════════════════════════

    def select_customer(self, cid: int):
        self.select_item(cid)