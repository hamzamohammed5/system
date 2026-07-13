"""
ui/tabs/orders/customers/customers_list_panel.py
=================================================
لوحة قائمة العملاء — ترث من BaseListPanel.

✅ الـ panel عرضه محدود بـ MIN_W → MAX_W
✅ الـ handle في الـ splitter مش بيتحرك أكتر من MAX_W
"""

from PyQt5.QtWidgets import (
    QHBoxLayout, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget,
)
from PyQt5.QtCore import Qt, pyqtSignal
from ui.widgets.panels.themed_inputs import ThemedComboBox

from services.orders.customer_service import CustomerService

from ui.widgets.base.list_panel import BaseListPanel
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.widgets.tables.tables import make_item, muted_item
from ui.widgets.core.i18n import tr
from ui.constants import (
    LIST_PANEL_MIN_W, LIST_PANEL_MAX_W,
    FILTER_SEARCH_H,
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
        # [إصلاح] لازم نملأ COLUMNS قبل استدعاء super().__init__()،
        # لأن BaseListPanel.__init__ بينادي self._build() فوراً، وهي
        # بتبني الجدول باستخدام self.COLUMNS في نفس اللحظة. لو استنينا
        # نملأها في _refresh_lang() (اللي بتتنفذ بعد ما super().__init__()
        # ترجع)، هيبقى الجدول اتبنى بالفعل بصفر أعمدة، فمفيش صفوف تظهر
        # حتى لو الداتا اترجعت صح من refresh().
        self.COLUMNS = [
            tr("customer_col_code"), tr("customer_col_name"),
            tr("customer_col_phone"), tr("customer_col_city"),
            tr("customer_col_orders"),
        ]
        super().__init__(conn=conn, parent=parent)
        self._init_widget_mixin(data=False)
        self._insert_toolbar()
        self._refresh_lang()
        self._refresh_style()
        self.item_selected.connect(self.customer_selected.emit)

    def _insert_toolbar(self):
        """
        [إصلاح] _build_toolbar() كانت معرّفة بس محدش كان بينادِيها —
        BaseListPanel._build() لا تستدعي أي method بهذا الاسم (فقط
        _build_header/_build_filter/_build_extra_header_actions). النتيجة:
        self.inp_search و self._btn_new و self.cmb_type/cmb_active كانوا
        يُبنون في الذاكرة كـ attributes لكن بلا أي مكان في الواجهة —
        الكومبوهات (النوع/الحالة) ماكانتش بتظهر للمستخدم إطلاقاً.

        الحل: نبني QWidget منفصل بلايوت خاص بيه، ننده _build_toolbar()
        عليه، ونضيفه لـ layout الأساسي بتاع BaseListPanel (self.layout())
        فوق الـ splitter مباشرة (بعد الـ header).
        """
        toolbar_widget = QWidget()
        toolbar_lay = QVBoxLayout(toolbar_widget)
        toolbar_lay.setContentsMargins(0, 0, 0, 0)
        self._build_toolbar(toolbar_lay)
        self.layout().insertWidget(1, toolbar_widget)

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
        _btn_ss = f"""
            QPushButton {{
                background: {_C['accent']}; color: {_C['btn_primary_text']};
                border: none; border-radius: 6px;
                padding: 0 14px; font-weight: bold; font-size: {FS_BASE}px;
            }}
            QPushButton:hover {{ background: {_C['accent_hover']}; }}
        """
        if hasattr(self, '_btn_new'):
            self._btn_new.setStyleSheet(_btn_ss)
        if hasattr(self, 'cmb_type'):
            self.cmb_type.setStyleSheet(_combo_ss)
        if hasattr(self, 'cmb_active'):
            self.cmb_active.setStyleSheet(_combo_ss)

    def _refresh_lang(self, *_):
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
        from ui.font import FS_SM

        # [إصلاح] صف البحث + زر "جديد" اتشال من هنا لأنه كان مكرر:
        # ListHeader (المبني في BaseListPanel._build_header عبر ADD_TEXT
        # و show_search) بيوفر بالفعل بحث وزر إضافة. كان فيه صف تاني هنا
        # بيعمل نفس الحاجة بالظبط لكن من غير أي ربط فعلي بـ _get_search_query()
        # (اللي بتقرا من self._header.search_bar بس)، فكان شكل بصري لبحث
        # تاني بيعمل حاجة، بينما فعليًا مش متصل بمنطق الفلترة خالص.

        # ── صف الفلاتر (النوع / الحالة) ──
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

        self.cmb_type = ThemedComboBox()
        self.cmb_type.setFixedHeight(FILTER_SEARCH_H)
        self.cmb_type.addItem(tr("filter_all"), None)
        self.cmb_type.addItem(tr("customer_type_individual"), "individual")
        self.cmb_type.addItem(tr("customer_type_company"), "company")
        self.cmb_type.setStyleSheet(_combo_ss)
        self.cmb_type.currentIndexChanged.connect(self._on_combo_changed)

        self.cmb_active = ThemedComboBox()
        self.cmb_active.setFixedHeight(FILTER_SEARCH_H)
        self.cmb_active.addItem(tr("all"), None)
        self.cmb_active.addItem(tr("customer_toggle_active"), 1)
        self.cmb_active.addItem(tr("customer_toggle_inactive"), 0)
        self.cmb_active.setStyleSheet(_combo_ss)
        self.cmb_active.currentIndexChanged.connect(self._on_combo_changed)

        self._btn_new = QPushButton(tr("customer_new_btn"))
        self._btn_new.setFixedHeight(FILTER_SEARCH_H)
        self._btn_new.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._btn_new.setStyleSheet(f"""
            QPushButton {{
                background: {_C['accent']}; color: {_C['btn_primary_text']};
                border: none; border-radius: 6px;
                padding: 0 14px; font-weight: bold; font-size: {FS_SM}px;
            }}
            QPushButton:hover {{ background: {_C['accent_hover']}; }}
        """)
        self._btn_new.clicked.connect(self.new_customer.emit)

        row2.addWidget(self.cmb_type, stretch=1)
        row2.addWidget(self.cmb_active, stretch=1)
        row2.addWidget(self._btn_new)
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
        code_item = muted_item(row["code"] or "")
        code_item.setData(Qt.UserRole, row["id"])
        code_item.setToolTip(row["code"] or "")
        table.setItem(r, 0, code_item)

        name_item = make_item(row["name"], tooltip=row["name"])
        # [إصلاح ثيم] نخزن is_active في الـ item نفسه عشان _refresh_style
        # تقدر تعيد حساب اللون الصحيح بعد تغيير الثيم من غير إعادة استعلام DB
        name_item.setData(Qt.UserRole + 1, bool(row["is_active"]))
        if not row["is_active"]:
            name_item.setForeground(QColor(_C['text_disabled']))
        else:
            f = name_item.font()
            f.setBold(True)
            name_item.setFont(f)
        table.setItem(r, 1, name_item)

        table.setItem(r, 2, muted_item(
            row["phone"] or tr("dash")))
        table.item(r, 2).setToolTip(row["phone"] or "")
        table.setItem(r, 3, muted_item(
            row["city"] or tr("dash")))
        table.item(r, 3).setToolTip(row["city"] or "")

        cnt_item = make_item(str(row["orders_count"] or 0),
                             align=Qt.AlignCenter)
        cnt_item.setForeground(QColor(_C['accent']))
        table.setItem(r, 4, cnt_item)

    def _refresh_style(self, *_):
        """
        [إصلاح ثيم] setForeground اللي بيتحط في _fill_row (اسم العميل
        غير النشط، لون عمود عدد الطلبات) بتتحدد وقت التعبئة بس ومش
        بتتحدث تلقائياً مع الثيم. هنا بنعيد رسم الصفوف الموجودة فعلياً.
        """
        super()._refresh_style(*_)
        from PyQt5.QtGui import QColor
        from ui.theme import _C
        for r in range(self.table.rowCount()):
            name_item = self.table.item(r, 1)
            if name_item is not None:
                is_active = name_item.data(Qt.UserRole + 1)
                if is_active is False:
                    name_item.setForeground(QColor(_C['text_disabled']))
                else:
                    name_item.setForeground(QColor(_C['text_primary']))

            cnt_item = self.table.item(r, 4)
            if cnt_item is not None:
                cnt_item.setForeground(QColor(_C['accent']))

    # ══════════════════════════════════════════════════════
    # API
    # ══════════════════════════════════════════════════════

    def select_customer(self, cid: int):
        self.select_item(cid)