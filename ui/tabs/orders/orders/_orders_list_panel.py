"""
ui/tabs/orders/orders/_orders_list_panel.py
"""
from PyQt5.QtWidgets import QSizePolicy, QVBoxLayout
from PyQt5.QtCore    import Qt, pyqtSignal

from services.orders.order_service import OrderService
from ui.widgets.base.list_panel import BaseListPanel
from ui.widgets.tables.tables import (
    make_item, muted_item, auto_fit_columns,
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
        # [إصلاح] _build_toolbar() كانت معرّفة بس محدش كان بينادِيها —
        # نفس الباج بالظبط اللي كان في CustomersListPanel: BaseListPanel._build()
        # بتنادي _build_header()/_build_filter() بس، مفيش أي استدعاء لـ
        # _build_toolbar() في أي مكان. النتيجة: self._filter_bar (وفيها
        # btn_new — زرار "طلب جديد") كانت بتتبني في الذاكرة فعلاً وتتربط
        # إشاراتها، لكن مفيش حد بيضيفها لأي layout ظاهر — فكانت غير مرئية
        # تمامًا للمستخدم رغم إنها موجودة وشغالة برمجيًا.
        #
        # الحل: نفس نمط _insert_toolbar() في CustomersListPanel — نبني
        # QWidget منفصل، ننده _build_toolbar() عليه، ونضيفه لـ layout
        # الأساسي فوق الـ splitter مباشرة (بعد الـ header).
        self._insert_toolbar()
        self.item_selected.connect(self.order_selected.emit)
        self._status_delegate = _StatusDelegate(self.table)
        self.table.setItemDelegateForColumn(2, self._status_delegate)

    def _insert_toolbar(self):
        from PyQt5.QtWidgets import QWidget
        toolbar_widget = QWidget()
        toolbar_lay = QVBoxLayout(toolbar_widget)
        toolbar_lay.setContentsMargins(0, 0, 0, 0)
        self._build_toolbar(toolbar_lay)
        self.layout().insertWidget(1, toolbar_widget)

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
        f = num_item.font()
        f.setBold(True)
        num_item.setFont(f)
        from PyQt5.QtGui import QColor
        num_item.setForeground(QColor(_C['accent']))
        table.setItem(r, 0, num_item)

        table.setItem(r, 1, make_item(row["customer_name"], tooltip=row["customer_name"]))

        status_text = STATUS_LABELS.get(row["status"], (row["status"],))[0]
        s_item = make_item(status_text, align=Qt.AlignCenter)
        s_item.setData(Qt.UserRole + 1, row["status"])
        table.setItem(r, 2, s_item)

        pri_lbl, pri_color = PRIORITY_LABELS.get(row["priority"], ("", _C['text_muted']))
        pri_text = pri_lbl.split()[0] if pri_lbl else ""
        pri_item = make_item(pri_text, align=Qt.AlignCenter)
        # [إصلاح ثيم] بنخزن مفتاح الـ priority نفسه (مش اللون) في UserRole+1
        # عشان _refresh_style تقدر تعيد حساب اللون الصحيح من get_priority_labels()
        # الحالية (بعد تغيير الثيم) بدل ما يفضل حافظ لون الثيم القديم.
        pri_item.setData(Qt.UserRole + 1, row["priority"])
        pri_item.setForeground(QColor(pri_color))
        if row["priority"] in ("high", "urgent"):
            f = pri_item.font()
            f.setBold(True)
            pri_item.setFont(f)
        table.setItem(r, 3, pri_item)

        table.setItem(r, 4, muted_item((row["order_date"] or "")[:10]))

    def _refresh_style(self, *_):
        """
        [إصلاح ثيم] الألوان اللي بتتحط جوه الخلايا عن طريق setForeground
        وقت _fill_row بتتحدد مرة واحدة بس (وقت التعبئة)، ومش جزء من الـ
        stylesheet العام، فلما الثيم يتغير مفيش حد بيعيد رسمها ⇒ بتفضل
        بلون الثيم القديم (المشكلة اللي شايفينها في السكرين شوت).

        الحل هنا: نعيد تلوين الصفوف الموجودة فعلياً في الجدول من غير
        إعادة تحميل الداتا من DB (أرخص وأسرع من refresh() كاملة).
        """
        super()._refresh_style(*_)
        from PyQt5.QtGui import QColor
        PRIORITY_LABELS = get_priority_labels()
        for r in range(self.table.rowCount()):
            num_item = self.table.item(r, 0)
            if num_item is not None:
                num_item.setForeground(QColor(_C['accent']))

            pri_item = self.table.item(r, 3)
            if pri_item is not None:
                pri_key = pri_item.data(Qt.UserRole + 1)
                _, pri_color = PRIORITY_LABELS.get(pri_key, ("", _C['text_muted']))
                pri_item.setForeground(QColor(pri_color))

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
