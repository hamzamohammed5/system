"""
ui/tabs/orders/order_form/
_item_row_widget.py
====================
_ItemRowWidget — صف بند واحد داخل فورم الطلب.
"""

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QComboBox, QDoubleSpinBox, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui  import QColor, QBrush

from ._products_fetcher import fetch_priced_products

_BLUE   = "#1565c0"
_GREEN  = "#2e7d32"
_GRAY   = "#6b7280"
_BG     = "#f8f9fb"
_BORDER = "#cdd3e0"
_WHITE  = "#ffffff"


class _ItemRowWidget(QFrame):
    changed = pyqtSignal()
    removed = pyqtSignal(object)

    _products_cache: list = None

    @classmethod
    def _get_products(cls) -> list:
        if cls._products_cache is None:
            cls._products_cache = fetch_priced_products()
        return cls._products_cache

    @classmethod
    def invalidate_cache(cls):
        cls._products_cache = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self._db_item_id   = None
        self._unit_price   = 0.0
        self._discount_pct = 0.0
        self._build()

    def _build(self):
        self.setStyleSheet(f"""
            QFrame {{
                background: {_WHITE};
                border: 1px solid #e5e9f0;
                border-radius: 8px;
            }}
            QFrame:hover {{ border-color: #93c5fd; }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(5)

        # صف 1: بحث + combo
        row1 = QHBoxLayout()
        row1.setSpacing(6)

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 بحث...")
        self.inp_search.setFixedWidth(100)
        self.inp_search.setMinimumHeight(30)
        self.inp_search.setStyleSheet(f"""
            QLineEdit {{
                background: #f0f4ff; border: 1px solid #c5cae9;
                border-radius: 5px; padding: 2px 8px; font-size: 11px;
            }}
            QLineEdit:focus {{ border-color: {_BLUE}; background: {_WHITE}; }}
        """)
        self.inp_search.textChanged.connect(self._on_search)

        self.btn_clr = QPushButton("✖")
        self.btn_clr.setFixedSize(22, 22)
        self.btn_clr.setStyleSheet(
            "QPushButton{background:transparent;border:none;color:#aaa;font-size:10px;}"
            "QPushButton:hover{color:#e53935;}"
        )
        self.btn_clr.clicked.connect(lambda: self.inp_search.clear())
        self.btn_clr.setVisible(False)
        self.inp_search.textChanged.connect(lambda t: self.btn_clr.setVisible(bool(t)))

        self.cmb_product = QComboBox()
        self.cmb_product.setMinimumHeight(30)
        self.cmb_product.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cmb_product.setStyleSheet(f"""
            QComboBox {{
                background: {_BG}; border: 1px solid {_BORDER};
                border-radius: 5px; padding: 2px 8px; font-size: 12px;
            }}
            QComboBox:focus {{ border-color: {_BLUE}; }}
            QComboBox::drop-down {{ border: none; width: 18px; }}
        """)
        self.cmb_product.currentIndexChanged.connect(self._on_product_changed)

        row1.addWidget(self.inp_search)
        row1.addWidget(self.btn_clr)
        row1.addWidget(self.cmb_product, stretch=1)
        root.addLayout(row1)

        # صف 2: السعر + الخصم + الكمية + الإجمالي + ملاحظات + حذف
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        lbl_price_t = QLabel("سعر الوحدة:")
        lbl_price_t.setStyleSheet(f"color:{_GRAY}; font-size:11px;")
        self.lbl_price = QLabel("─")
        self.lbl_price.setMinimumWidth(85)
        self.lbl_price.setAlignment(Qt.AlignCenter)
        self.lbl_price.setStyleSheet(
            f"font-size:12px; font-weight:bold; color:{_GREEN};"
            "background:#f0fdf4; border:1px solid #bbf7d0;"
            "border-radius:5px; padding:3px 8px;"
        )

        lbl_disc_t = QLabel("خصم:")
        lbl_disc_t.setStyleSheet(f"color:{_GRAY}; font-size:11px;")
        self.lbl_disc = QLabel("─")
        self.lbl_disc.setMinimumWidth(60)
        self.lbl_disc.setAlignment(Qt.AlignCenter)
        self.lbl_disc.setStyleSheet(
            "font-size:12px; font-weight:bold; color:#b45309;"
            "background:#fffbeb; border:1px solid #fde68a;"
            "border-radius:5px; padding:3px 8px;"
        )

        lbl_qty = QLabel("الكمية:")
        lbl_qty.setStyleSheet(f"color:{_GRAY}; font-size:11px;")
        self.sp_qty = QDoubleSpinBox()
        self.sp_qty.setRange(0.001, 99_999)
        self.sp_qty.setDecimals(3)
        self.sp_qty.setValue(1)
        self.sp_qty.setMinimumHeight(30)
        self.sp_qty.setFixedWidth(90)
        self.sp_qty.setStyleSheet(f"""
            QDoubleSpinBox {{
                background: {_WHITE}; border: 2px solid {_BLUE};
                border-radius: 5px; padding: 2px 6px;
                font-size:12px; font-weight:bold; color:{_BLUE};
            }}
        """)
        self.sp_qty.valueChanged.connect(self._recalc)

        self.inp_unit = QLineEdit("قطعة")
        self.inp_unit.setFixedWidth(55)
        self.inp_unit.setMinimumHeight(30)
        self.inp_unit.setStyleSheet(f"""
            QLineEdit {{
                background: {_BG}; border: 1px solid {_BORDER};
                border-radius: 5px; padding: 2px 5px; font-size: 11px;
            }}
        """)

        self.lbl_total = QLabel("0.00 ج")
        self.lbl_total.setMinimumWidth(95)
        self.lbl_total.setAlignment(Qt.AlignCenter)
        self.lbl_total.setStyleSheet(
            f"font-size:13px; font-weight:bold; color:{_BLUE};"
            "background:#eff6ff; border:1px solid #bfdbfe;"
            "border-radius:5px; padding:3px 10px;"
        )

        lbl_note = QLabel("ملاحظات:")
        lbl_note.setStyleSheet(f"color:{_GRAY}; font-size:11px;")
        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("...")
        self.inp_notes.setMinimumHeight(30)
        self.inp_notes.setStyleSheet(f"""
            QLineEdit {{
                background: {_BG}; border: 1px solid {_BORDER};
                border-radius: 5px; padding: 2px 8px; font-size: 11px;
            }}
        """)

        btn_del = QPushButton("🗑")
        btn_del.setFixedSize(30, 30)
        btn_del.setStyleSheet("""
            QPushButton{background:#fef2f2;border:1px solid #fecaca;
            border-radius:5px;font-size:13px;}
            QPushButton:hover{background:#fee2e2;}
        """)
        btn_del.clicked.connect(lambda: self.removed.emit(self))

        row2.addWidget(lbl_price_t)
        row2.addWidget(self.lbl_price)
        row2.addWidget(lbl_disc_t)
        row2.addWidget(self.lbl_disc)
        row2.addWidget(lbl_qty)
        row2.addWidget(self.sp_qty)
        row2.addWidget(self.inp_unit)
        row2.addWidget(self.lbl_total)
        row2.addWidget(lbl_note)
        row2.addWidget(self.inp_notes, stretch=1)
        row2.addWidget(btn_del)
        root.addLayout(row2)

        self._populate_combo()

    def _populate_combo(self, filter_text: str = ""):
        prev = self.cmb_product.currentData()
        self.cmb_product.blockSignals(True)
        self.cmb_product.clear()
        self.cmb_product.addItem("— اختر منتجاً —", None)

        products = self._get_products()
        q = filter_text.strip().lower()
        current_cat = None

        for p in products:
            name = p["name"]
            if q and q not in name.lower():
                continue
            cat  = p.get("category_name") or "بدون تصنيف"
            icon = "🏭" if p["type"] == "final" else "🔧"

            if cat != current_cat:
                current_cat = cat
                sep_idx = self.cmb_product.count()
                self.cmb_product.addItem(f"── {cat} ──", f"__cat__{cat}")
                model = self.cmb_product.model()
                item  = model.item(sep_idx)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemIsEnabled & ~Qt.ItemIsSelectable)
                    from PyQt5.QtGui import QFont as QF
                    f = QF(); f.setBold(True); f.setPointSize(f.pointSize() - 1)
                    item.setFont(f)
                    item.setForeground(QBrush(QColor("#78909c")))

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
            self.lbl_total.setText("0.00 ج")
            self.changed.emit()
            return

        for p in self._get_products():
            if p["id"] == pid:
                self._unit_price = p.get("price") or 0.0
                break

        self.lbl_price.setText(f"{self._unit_price:.2f} ج")
        self.lbl_disc.setText(f"{self._discount_pct:.1f} %")
        self._recalc()

    def _recalc(self):
        qty   = self.sp_qty.value()
        total = qty * self._unit_price * (1 - self._discount_pct / 100)
        self.lbl_total.setText(f"{total:,.2f} ج")
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
            "unit":         self.inp_unit.text().strip() or "قطعة",
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

        self.lbl_price.setText(f"{self._unit_price:.2f} ج")
        self.lbl_disc.setText(f"{self._discount_pct:.1f} %")
        self.sp_qty.setValue(item["quantity"])
        self.inp_unit.setText(item["unit"] or "قطعة")
        self.inp_notes.setText(item["notes"] or "")
        self._recalc()

    @property
    def db_item_id(self):
        return self._db_item_id