"""
ui/tabs/orders/order_form/_item_row_widget.py

[تعديل هيكلي]: أُزيل الاستيراد المباشر من ._products_fetcher
(fetch_priced_products) — كان هذا الملف يفتح اتصال DB وينفذ SQL
خام بنفسه من داخل ui/tabs، وهذا يخالف مبدأ الطبقات:
    widgets -> tabs/UI -> services -> repos (db) -> schema
المنطق بالكامل (SQL + caching) نُقل إلى:
    db.costing.catalog_repo      (SQL خام)
    services.costing.catalog_service.CatalogService  (caching + واجهة الخدمة)
الـ widget الآن يستقبل conn في __init__ (نفس نمط باقي الـ services
في المشروع مثل CustomerService(conn)) وينشئ CatalogService بنفسه،
بدل الاعتماد على cache على مستوى الـ class داخل الـ widget.
"""
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QComboBox, QDoubleSpinBox, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui  import QColor, QBrush

from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.font import FS_SM, FS_BASE
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import (
    ITEM_ROW_FRAME_RADIUS, ITEM_ROW_ROOT_MARGIN_H, ITEM_ROW_ROOT_MARGIN_V,
    ITEM_ROW_ROOT_SPACING, ITEM_ROW_ROW_SPACING, ITEM_ROW_ROW2_SPACING,
    ITEM_ROW_SEARCH_W, ITEM_ROW_INPUT_MIN_H, ITEM_ROW_CLEAR_BTN_SIZE,
    ITEM_ROW_INPUT_RADIUS, ITEM_ROW_QTY_W, ITEM_ROW_UNIT_W,
    ITEM_ROW_PRICE_LBL_MIN_W, ITEM_ROW_DISC_LBL_MIN_W, ITEM_ROW_TOTAL_LBL_MIN_W,
    ITEM_ROW_DEL_BTN_SIZE, ITEM_ROW_QTY_MIN, ITEM_ROW_QTY_MAX,
    ITEM_ROW_QTY_DECIMALS, ITEM_ROW_QTY_DEFAULT,
)
from services.costing.catalog_service import CatalogService


class _ItemRowWidget(QFrame, WidgetMixin):
    changed = pyqtSignal()
    removed = pyqtSignal(object)

    def __init__(self, conn, parent=None):
        """
        [تعديل هيكلي] conn أصبح إلزامياً — نفس نمط باقي الـ services
        في المشروع (مثال: CustomerService(conn)). كان قبل ذلك
        _get_products()/_products_cache يفتحان اتصال erp.db بأنفسهما
        بدون تمرير أي conn، وهذا ما جرى إصلاحه بنقل كل من الاتصال
        والـ caching إلى CatalogService.
        """
        super().__init__(parent)
        self._catalog       = CatalogService(conn)
        self._db_item_id    = None
        self._unit_price    = 0.0
        self._discount_pct  = 0.0
        self._init_widget_mixin(data=False)
        self._build()
        self._refresh_style()

    def _get_products(self) -> list:
        """
        [تعديل هيكلي] كانت classmethod تقرأ/تكتب _products_cache
        على مستوى الـ class. أصبحت الآن instance method تفوّض
        مباشرة إلى self._catalog.get_priced_products() — الكاش
        نفسه بقى مسؤولية CatalogService.
        """
        return self._catalog.get_priced_products()

    def invalidate_cache(self):
        """
        [تعديل هيكلي] كانت classmethod تصفّر _products_cache على
        مستوى الـ class (فتؤثر على كل نسخ الـ widget دفعة واحدة).
        أصبحت الآن تستدعي CatalogService.invalidate_products_cache()
        على نسخة الـ service الخاصة بهذا الـ widget فقط.
        """
        self._catalog.invalidate_products_cache()

    def _build(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        root = QVBoxLayout(self)
        root.setContentsMargins(
            ITEM_ROW_ROOT_MARGIN_H, ITEM_ROW_ROOT_MARGIN_V,
            ITEM_ROW_ROOT_MARGIN_H, ITEM_ROW_ROOT_MARGIN_V,
        )
        root.setSpacing(ITEM_ROW_ROOT_SPACING)

        # صف 1: بحث + combo
        row1 = QHBoxLayout()
        row1.setSpacing(ITEM_ROW_ROW_SPACING)

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText(tr("order_item_search"))
        self.inp_search.setFixedWidth(ITEM_ROW_SEARCH_W)
        self.inp_search.setMinimumHeight(ITEM_ROW_INPUT_MIN_H)
        self.inp_search.textChanged.connect(self._on_search)

        self.btn_clr = QPushButton(tr("combo_clear_search"))
        self.btn_clr.setFixedSize(ITEM_ROW_CLEAR_BTN_SIZE, ITEM_ROW_CLEAR_BTN_SIZE)
        self.btn_clr.clicked.connect(lambda: self.inp_search.clear())
        self.btn_clr.setVisible(False)
        self.inp_search.textChanged.connect(lambda t: self.btn_clr.setVisible(bool(t)))

        self.cmb_product = QComboBox()
        self.cmb_product.setMinimumHeight(ITEM_ROW_INPUT_MIN_H)
        self.cmb_product.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cmb_product.currentIndexChanged.connect(self._on_product_changed)

        row1.addWidget(self.inp_search)
        row1.addWidget(self.btn_clr)
        row1.addWidget(self.cmb_product, stretch=1)
        root.addLayout(row1)

        # صف 2: السعر + الخصم + الكمية + الإجمالي + ملاحظات + حذف
        row2 = QHBoxLayout()
        row2.setSpacing(ITEM_ROW_ROW2_SPACING)

        self.lbl_price_t = QLabel(tr("item_unit_price"))
        self.lbl_price = QLabel("─")
        self.lbl_price.setMinimumWidth(ITEM_ROW_PRICE_LBL_MIN_W)
        self.lbl_price.setAlignment(Qt.AlignCenter)

        self.lbl_disc_t = QLabel(tr("item_discount_lbl"))
        self.lbl_disc = QLabel("─")
        self.lbl_disc.setMinimumWidth(ITEM_ROW_DISC_LBL_MIN_W)
        self.lbl_disc.setAlignment(Qt.AlignCenter)

        self.lbl_qty = QLabel(tr("item_qty_lbl"))
        self.sp_qty = QDoubleSpinBox()
        self.sp_qty.setRange(ITEM_ROW_QTY_MIN, ITEM_ROW_QTY_MAX)
        self.sp_qty.setDecimals(ITEM_ROW_QTY_DECIMALS)
        self.sp_qty.setValue(ITEM_ROW_QTY_DEFAULT)
        self.sp_qty.setMinimumHeight(ITEM_ROW_INPUT_MIN_H)
        self.sp_qty.setFixedWidth(ITEM_ROW_QTY_W)
        self.sp_qty.valueChanged.connect(self._recalc)

        self.inp_unit = QLineEdit(tr("order_unit_default"))
        self.inp_unit.setFixedWidth(ITEM_ROW_UNIT_W)
        self.inp_unit.setMinimumHeight(ITEM_ROW_INPUT_MIN_H)

        self.lbl_total = QLabel(f"0.00 {tr('currency_sym')}")
        self.lbl_total.setMinimumWidth(ITEM_ROW_TOTAL_LBL_MIN_W)
        self.lbl_total.setAlignment(Qt.AlignCenter)

        self.lbl_note = QLabel(tr("item_notes_lbl"))
        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText(tr("notes_placeholder"))
        self.inp_notes.setMinimumHeight(ITEM_ROW_INPUT_MIN_H)

        self.btn_del = QPushButton(tr("scenarios_panel_btn_del_icon"))
        self.btn_del.setFixedSize(ITEM_ROW_DEL_BTN_SIZE, ITEM_ROW_DEL_BTN_SIZE)
        self.btn_del.clicked.connect(lambda: self.removed.emit(self))

        row2.addWidget(self.lbl_price_t)
        row2.addWidget(self.lbl_price)
        row2.addWidget(self.lbl_disc_t)
        row2.addWidget(self.lbl_disc)
        row2.addWidget(self.lbl_qty)
        row2.addWidget(self.sp_qty)
        row2.addWidget(self.inp_unit)
        row2.addWidget(self.lbl_total)
        row2.addWidget(self.lbl_note)
        row2.addWidget(self.inp_notes, stretch=1)
        row2.addWidget(self.btn_del)
        root.addLayout(row2)

        self._populate_combo()

    def _refresh_style(self, *_):
        self.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_surface']};
                border: 1px solid {_C['border']};
                border-radius: {ITEM_ROW_FRAME_RADIUS}px;
            }}
            QFrame:hover {{ border-color: {_C['accent_mid']}; }}
        """)

        self.inp_search.setStyleSheet(f"""
            QLineEdit {{
                background: {_C['accent_light']}; border: 1px solid {_C['accent_mid']};
                border-radius: {ITEM_ROW_INPUT_RADIUS}px; padding: 2px 8px; font-size: {FS_SM}px;
            }}
            QLineEdit:focus {{ border-color: {_C['accent']}; background: {_C['bg_surface']}; }}
        """)

        self.btn_clr.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;color:{_C['text_muted']};font-size:{FS_SM - 1}px;}}"
            f"QPushButton:hover{{color:{_C['danger']};}}"
        )

        self.cmb_product.setStyleSheet(f"""
            QComboBox {{
                background: {_C['bg_surface_2']}; border: 1px solid {_C['border_med']};
                border-radius: {ITEM_ROW_INPUT_RADIUS}px; padding: 2px 8px; font-size: {FS_BASE}px;
            }}
            QComboBox:focus {{ border-color: {_C['accent']}; }}
            QComboBox::drop-down {{ border: none; width: 18px; }}
        """)

        self.lbl_price_t.setStyleSheet(f"color:{_C['text_muted']}; font-size:{FS_SM}px;")
        self.lbl_price.setStyleSheet(
            f"font-size:{FS_BASE}px; font-weight:bold; color:{_C['success']};"
            f"background:{_C['success_bg']}; border:1px solid {_C['success_border']};"
            f"border-radius:{ITEM_ROW_INPUT_RADIUS}px; padding:3px 8px;"
        )

        self.lbl_disc_t.setStyleSheet(f"color:{_C['text_muted']}; font-size:{FS_SM}px;")
        self.lbl_disc.setStyleSheet(
            f"font-size:{FS_BASE}px; font-weight:bold; color:{_C['warning']};"
            f"background:{_C['warning_bg']}; border:1px solid {_C['warning_border']};"
            f"border-radius:{ITEM_ROW_INPUT_RADIUS}px; padding:3px 8px;"
        )

        self.lbl_qty.setStyleSheet(f"color:{_C['text_muted']}; font-size:{FS_SM}px;")
        self.sp_qty.setStyleSheet(f"""
            QDoubleSpinBox {{
                background: {_C['bg_surface']}; border: 2px solid {_C['accent']};
                border-radius: {ITEM_ROW_INPUT_RADIUS}px; padding: 2px 6px;
                font-size:{FS_BASE}px; font-weight:bold; color:{_C['accent']};
            }}
        """)

        self.inp_unit.setStyleSheet(f"""
            QLineEdit {{
                background: {_C['bg_surface_2']}; border: 1px solid {_C['border_med']};
                border-radius: {ITEM_ROW_INPUT_RADIUS}px; padding: 2px 5px; font-size: {FS_SM}px;
            }}
        """)

        self.lbl_total.setStyleSheet(
            f"font-size:{FS_BASE + 1}px; font-weight:bold; color:{_C['accent']};"
            f"background:{_C['accent_light']}; border:1px solid {_C['accent_mid']};"
            f"border-radius:{ITEM_ROW_INPUT_RADIUS}px; padding:3px 10px;"
        )

        self.lbl_note.setStyleSheet(f"color:{_C['text_muted']}; font-size:{FS_SM}px;")
        self.inp_notes.setStyleSheet(f"""
            QLineEdit {{
                background: {_C['bg_surface_2']}; border: 1px solid {_C['border_med']};
                border-radius: {ITEM_ROW_INPUT_RADIUS}px; padding: 2px 8px; font-size: {FS_SM}px;
            }}
        """)

        self.btn_del.setStyleSheet(f"""
            QPushButton{{background:{_C['danger_bg']};border:1px solid {_C['danger_border']};
            border-radius:{ITEM_ROW_INPUT_RADIUS}px;font-size:{FS_BASE}px;}}
            QPushButton:hover{{background:{_C['danger_hover_bg']};}}
        """)

    def _refresh_lang(self, *_):
        self.inp_search.setPlaceholderText(tr("order_item_search"))
        self.btn_clr.setText(tr("combo_clear_search"))
        self.lbl_price_t.setText(tr("item_unit_price"))
        self.lbl_disc_t.setText(tr("item_discount_lbl"))
        self.lbl_qty.setText(tr("item_qty_lbl"))
        self.lbl_note.setText(tr("item_notes_lbl"))
        self.inp_notes.setPlaceholderText(tr("notes_placeholder"))
        self.btn_del.setText(tr("scenarios_panel_btn_del_icon"))
        self._populate_combo(filter_text=self.inp_search.text())

    def _populate_combo(self, filter_text: str = ""):
        prev = self.cmb_product.currentData()
        self.cmb_product.blockSignals(True)
        self.cmb_product.clear()
        self.cmb_product.addItem(f"— {tr('order_select_product')} —", None)

        products = self._get_products()
        q = filter_text.strip().lower()
        current_cat = None

        for p in products:
            name = p["name"]
            if q and q not in name.lower():
                continue
            cat  = p.get("category_name") or tr("no_category")
            icon = tr("tab_icon_final") if p["type"] == "final" else tr("tab_icon_semi")

            if cat != current_cat:
                current_cat = cat
                sep_idx = self.cmb_product.count()
                self.cmb_product.addItem(tr("order_product_cat_sep_fmt").format(cat=cat), f"__cat__{cat}")
                model = self.cmb_product.model()
                item  = model.item(sep_idx)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemIsEnabled & ~Qt.ItemIsSelectable)
                    from PyQt5.QtGui import QFont as QF
                    f = QF(); f.setBold(True); f.setPointSize(f.pointSize() - 1)
                    item.setFont(f)
                    item.setForeground(QBrush(QColor(_C['text_separator'])))

            self.cmb_product.addItem(f"  {icon} {name}", p["id"])

        self.cmb_product.blockSignals(False)

        if prev and not isinstance(prev, str):
            for i in range(self.cmb_product.count()):
                if self.cmb_product.itemData(i) == prev:
                    self.cmb_product.setCurrentIndex(i)
                    return
        self.cmb_product.setCurrentIndex(0)
        self._on_product_changed()

    def _on_search(self, text: str):
        self._populate_combo(filter_text=text)

    def _on_product_changed(self):
        pid = self.cmb_product.currentData()
        if not pid or isinstance(pid, str):
            self._unit_price   = 0.0
            self._discount_pct = 0.0
            self.lbl_price.setText("─")
            self.lbl_disc.setText("─")
            self.lbl_total.setText(f"0.00 {tr('currency_sym')}")
            self.changed.emit()
            return

        for p in self._get_products():
            if p["id"] == pid:
                self._unit_price = p.get("price") or 0.0
                break

        self.lbl_price.setText(f"{self._unit_price:.2f} {tr('currency_sym')}")
        self.lbl_disc.setText(f"{self._discount_pct:.1f} %")
        self._recalc()

    def _recalc(self):
        qty   = self.sp_qty.value()
        total = qty * self._unit_price * (1 - self._discount_pct / 100)
        self.lbl_total.setText(f"{total:,.2f} {tr('currency_sym')}")
        self.changed.emit()

    def set_offer_discount(self, discount_pct: float):
        self._discount_pct = discount_pct
        self.lbl_disc.setText(f"{discount_pct:.1f} %")
        self._recalc()

    def get_product_id(self):
        pid = self.cmb_product.currentData()
        if not pid or isinstance(pid, str):
            return None
        return pid

    def get_product_name(self) -> str:
        pid = self.get_product_id()
        if pid:
            for p in self._get_products():
                if p["id"] == pid:
                    return p["name"]
        return ""

    def get_data(self) -> dict:
        name = self.get_product_name()
        if not name:
            return None
        return {
            "item_name":    name,
            "description":  "",
            "quantity":     self.sp_qty.value(),
            "unit":         self.inp_unit.text().strip() or tr("order_unit_default"),
            "unit_price":   self._unit_price,
            "discount_pct": self._discount_pct,
            "design_ref":   "",
            "notes":        self.inp_notes.text().strip(),
        }

    def get_total(self) -> float:
        return self.sp_qty.value() * self._unit_price * (1 - self._discount_pct / 100)

    def load_from_order_item(self, item: dict):
        self._db_item_id   = item["id"]
        self._unit_price   = item["unit_price"]
        self._discount_pct = item["discount_pct"]

        name = item["item_name"]
        for p in self._get_products():
            if p["name"] == name:
                for i in range(self.cmb_product.count()):
                    if self.cmb_product.itemData(i) == p["id"]:
                        self.cmb_product.blockSignals(True)
                        self.cmb_product.setCurrentIndex(i)
                        self.cmb_product.blockSignals(False)
                        break
                break

        self.lbl_price.setText(f"{self._unit_price:.2f} {tr('currency_sym')}")
        self.lbl_disc.setText(f"{self._discount_pct:.1f} %")
        self.sp_qty.setValue(item["quantity"])
        self.inp_unit.setText(item["unit"] or tr("order_unit_default"))
        self.inp_notes.setText(item["notes"] or "")
        self._recalc()

    @property
    def db_item_id(self):
        return self._db_item_id
