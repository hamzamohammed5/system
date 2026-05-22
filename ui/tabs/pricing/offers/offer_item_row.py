"""
ui/tabs/pricing/offers/offer_item_row.py
=================================
_OfferItemRow — صف منتج واحد داخل فورم العرض.
"""

from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QDoubleSpinBox, QComboBox,
)
from PyQt5.QtCore import Qt

from db.shared.items_repo  import fetch_items_by_type
from models.costing import calc_cost
from ui.events      import bus


def _spin(max_=999999, dec=2):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(30)
    return s


class _OfferItemRow(QFrame):
    """صف منتج واحد داخل فورم العرض."""

    def __init__(self, conn, on_remove, on_change, parent=None):
        super().__init__(parent)
        self._conn      = conn
        self._on_remove = on_remove
        self._on_change = on_change
        self._build()
        self._load_products()
        bus.data_changed.connect(self._reload_products)

    # ── connection صالح دايماً ────────────────────────────
    def _live_conn(self):
        if self._conn is not None:
            try:
                self._conn.execute("SELECT 1")
                return self._conn
            except Exception:
                pass
        from db.companies.company_state import company_state
        return company_state.get_erp_conn()

    def _build(self):
        self.setStyleSheet("""
            QFrame {
                background: #fafafa;
                border: 1px solid #e8e8e8;
                border-radius: 6px;
            }
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(8)

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 بحث...")
        self.inp_search.setFixedWidth(120)
        self.inp_search.setMinimumHeight(28)
        self.inp_search.setStyleSheet("""
            QLineEdit {
                background: white; border: 1px solid #c5cae9;
                border-radius: 4px; padding: 2px 6px; font-size: 11px;
            }
            QLineEdit:focus { border-color: #e65100; }
        """)
        self.inp_search.textChanged.connect(
            lambda t: self._load_products(filter_text=t.strip())
        )

        self.cmb_product = QComboBox()
        self.cmb_product.setMinimumWidth(180)
        self.cmb_product.setMinimumHeight(28)
        self.cmb_product.currentIndexChanged.connect(self._on_product_changed)

        self.lbl_cost = QLabel("─")
        self.lbl_cost.setFixedWidth(72)
        self.lbl_cost.setStyleSheet(
            "color:#1565c0; font-size:11px; background:transparent; border:none;"
        )
        self.lbl_cost.setAlignment(Qt.AlignCenter)
        self.lbl_cost.setToolTip("تكلفة الإنتاج / وحدة")

        self.lbl_listed = QLabel("─")
        self.lbl_listed.setFixedWidth(72)
        self.lbl_listed.setStyleSheet(
            "color:#2e7d32; font-size:11px; background:transparent; border:none;"
        )
        self.lbl_listed.setAlignment(Qt.AlignCenter)
        self.lbl_listed.setToolTip("سعر التسعير / وحدة")

        self.sp_qty = _spin(99999, 4)
        self.sp_qty.setValue(1.0)
        self.sp_qty.setFixedWidth(85)
        self.sp_qty.valueChanged.connect(self._on_product_changed)

        self.lbl_line = QLabel("─")
        self.lbl_line.setFixedWidth(80)
        self.lbl_line.setStyleSheet(
            "color:#e65100; font-weight:bold; font-size:11px;"
            "background:transparent; border:none;"
        )
        self.lbl_line.setAlignment(Qt.AlignCenter)
        self.lbl_line.setToolTip("إجمالي سعر السطر قبل الخصم")

        self.lbl_warn = QLabel("⚠️")
        self.lbl_warn.setStyleSheet(
            "color:#e65100; font-size:11px; background:transparent; border:none;"
        )
        self.lbl_warn.setFixedWidth(20)
        self.lbl_warn.setToolTip("هذا المنتج ليس له سعر في التسعير")
        self.lbl_warn.setVisible(False)

        btn_del = QPushButton("❌")
        btn_del.setFixedSize(28, 28)
        btn_del.setStyleSheet(
            "QPushButton { background:transparent; border:none; font-size:13px; }"
            "QPushButton:hover { color:#e53935; }"
        )
        btn_del.clicked.connect(lambda: self._on_remove(self))

        lay.addWidget(self.inp_search)
        lay.addWidget(self.cmb_product, stretch=1)
        lay.addWidget(QLabel("تكلفة:"))
        lay.addWidget(self.lbl_cost)
        lay.addWidget(QLabel("سعر:"))
        lay.addWidget(self.lbl_listed)
        lay.addWidget(QLabel("×"))
        lay.addWidget(self.sp_qty)
        lay.addWidget(QLabel("="))
        lay.addWidget(self.lbl_line)
        lay.addWidget(self.lbl_warn)
        lay.addWidget(btn_del)

    def _load_products(self, filter_text: str = ""):
        try:
            conn = self._live_conn()
        except Exception:
            return

        prev_id = self.get_item_id()
        self.cmb_product.blockSignals(True)
        self.cmb_product.clear()
        q = filter_text.lower()

        try:
            priced_ids = {
                r["item_id"]
                for r in conn.execute("SELECT item_id FROM pricing").fetchall()
            }
            for item_type in ("final", "semi"):
                rows = fetch_items_by_type(conn, item_type)
                icon = "🏭" if item_type == "final" else "🔧"
                for row in rows:
                    if row["id"] not in priced_ids:
                        continue
                    if q and q not in row["name"].lower():
                        continue
                    self.cmb_product.addItem(f"{icon} {row['name']}", row["id"])
        except Exception:
            pass

        self.cmb_product.blockSignals(False)
        if prev_id is not None:
            for i in range(self.cmb_product.count()):
                if self.cmb_product.itemData(i) == prev_id:
                    self.cmb_product.setCurrentIndex(i)
                    return
        self._on_product_changed()

    def _reload_products(self):
        self._load_products(filter_text=self.inp_search.text().strip())

    def _on_product_changed(self):
        item_id = self.get_item_id()
        if item_id is None:
            self.lbl_cost.setText("─")
            self.lbl_listed.setText("─")
            self.lbl_line.setText("─")
            self.lbl_warn.setVisible(False)
            if self._on_change:
                self._on_change()
            return

        try:
            conn = self._live_conn()
            unit_cost   = calc_cost(conn, item_id)
            pricing_row = conn.execute(
                "SELECT price FROM pricing WHERE item_id=?", (item_id,)
            ).fetchone()
        except Exception:
            return

        unit_price  = pricing_row["price"] if pricing_row else 0.0
        has_pricing = pricing_row is not None

        self.lbl_cost.setText(f"{unit_cost:.2f}")
        self.lbl_listed.setText(f"{unit_price:.2f}" if has_pricing else "─")
        self.lbl_warn.setVisible(not has_pricing)

        line_total = unit_price * self.sp_qty.value()
        self.lbl_line.setText(f"{line_total:.2f}" if has_pricing else "─")

        if self._on_change:
            self._on_change()

    def get_item_id(self):
        return self.cmb_product.currentData()

    def get_qty(self) -> float:
        return self.sp_qty.value()

    def get_values(self) -> tuple | None:
        item_id = self.get_item_id()
        if item_id is None:
            return None
        return item_id, self.sp_qty.value()

    def set_values(self, item_id: int, qty: float):
        for i in range(self.cmb_product.count()):
            if self.cmb_product.itemData(i) == item_id:
                self.cmb_product.setCurrentIndex(i)
                break
        self.sp_qty.setValue(qty)
        self._on_product_changed()