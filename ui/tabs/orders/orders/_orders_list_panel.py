"""
ui/tabs/orders/orders/_orders_list_panel.py
"""
from PyQt5.QtWidgets import QSizePolicy, QVBoxLayout
from PyQt5.QtCore    import Qt, pyqtSignal

from services.orders.order_service import OrderService
from ui.widgets.base.list_panel import BaseListPanel
from ui.widgets.tables.tables import (
    make_item, colored_item, bold_item, muted_item, auto_fit_columns,
)
from ui.widgets.core.i18n import tr
from ui.theme import _C
from ui.constants import (
    ORDERS_LIST_COL_WIDTHS, ORDERS_LIST_MIN_W, ORDERS_LIST_MAX_W,
    ORDERS_LIST_AUTOFIT_MIN_W, ORDERS_LIST_AUTOFIT_MAX_W,
)

from ._filter_toolbar  import _FilterToolbar
from ._status_delegate import _StatusDelegate
from ..order_detail._status_config import get_status_labels, get_priority_labels


class _OrdersListPanel(BaseListPanel):
    order_selected = pyqtSignal(int)
    new_order      = pyqtSignal()

    COLUMNS     = []   # تُبنى ديناميكياً في __init__
    STRETCH_COL = -1
    COL_WIDTHS  = ORDERS_LIST_COL_WIDTHS
    MIN_W       = ORDERS_LIST_MIN_W
    MAX_W       = ORDERS_LIST_MAX_W
    EMPTY_TITLE = "no_orders"   # مفتاح tr

    @property
    def EMPTY_ICON(self) -> str:
        """
        [تعديل هيكلي] كانت class attribute ثابتة (\"📋\") تُقرأ وقت
        الـ import. أصبحت الآن property تستدعي tr() في كل مرة تُقرأ
        فيها — اتساقاً مع بقية الملف رغم أن قيمة الأيقونة نفسها
        متطابقة حالياً في ar.py وen.py (empty_icon_table).
        """
        return tr("empty_icon_table")

    def __init__(self, conn, parent=None):
        self.COLUMNS = [
            tr("order_col_number"), tr("order_col_customer"),
            tr("order_col_status"), tr("order_col_priority"), tr("order_col_date"),
        ]
        self._filter_bar = _FilterToolbar()
        super().__init__(conn=conn, parent=parent)
        self.item_selected.connect(self.order_selected.emit)
        self._status_delegate = _StatusDelegate(self.table)
        self.table.setItemDelegateForColumn(2, self._status_delegate)

    def _build_toolbar(self, lay: QVBoxLayout):
        self._filter_bar.btn_new.clicked.connect(self.new_order.emit)
        self._filter_bar.changed.connect(self._apply_filter)
        lay.addWidget(self._filter_bar)

    def _load_rows(self) -> list:
        return OrderService(self.conn).list_orders()

    def _match_filter(self, row, q: str) -> bool:
        if not hasattr(self, '_filter_bar'):
            return True
        status   = self._filter_bar.status_filter
        priority = self._filter_bar.priority_filter
        if status   and row["status"]   != status:   return False
        if priority and row["priority"] != priority: return False
        if q and q not in row["order_number"].lower() \
            and q not in row["customer_name"].lower():
            return False
        return True

    def _fill_row(self, table, r, row):
        STATUS_LABELS   = get_status_labels()
        PRIORITY_LABELS = get_priority_labels()

        num_item = make_item(row["order_number"], user_data=row["id"])
        bold_item(num_item)
        colored_item(num_item, _C['accent'])
        table.setItem(r, 0, num_item)

        table.setItem(r, 1, make_item(row["customer_name"], tooltip=row["customer_name"]))

        status_text = STATUS_LABELS.get(row["status"], (row["status"],))[0]
        s_item = make_item(status_text, align=Qt.AlignCenter)
        s_item.setData(Qt.UserRole + 1, row["status"])
        table.setItem(r, 2, s_item)

        pri_lbl, pri_color = PRIORITY_LABELS.get(row["priority"], ("", _C['text_muted']))
        pri_text = pri_lbl.split()[0] if pri_lbl else ""
        pri_item = make_item(pri_text, align=Qt.AlignCenter)
        from PyQt5.QtGui import QColor
        pri_item.setForeground(QColor(pri_color))
        if row["priority"] in ("high", "urgent"):
            bold_item(pri_item)
        table.setItem(r, 3, pri_item)

        table.setItem(r, 4, muted_item(make_item((row["order_date"] or "")[:10])))

    def _auto_resize(self):
        auto_fit_columns(
            self.table,
            fixed_cols=list(self.COL_WIDTHS.keys()),
            stretch_col=self.STRETCH_COL,
            min_width=ORDERS_LIST_AUTOFIT_MIN_W,
            max_width=ORDERS_LIST_AUTOFIT_MAX_W,
        )

    def select_order(self, order_id: int):
        self.select_item(order_id)
