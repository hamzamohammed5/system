"""
ui/tabs/pricing_tab.py — مع FilterBar موحّد
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget,
    QPushButton, QTableWidgetItem, QLabel,
    QDoubleSpinBox, QMessageBox, QHeaderView, QFrame,
)
from PyQt5.QtCore import Qt

from db.connection    import get_connection
from db.items_repo    import fetch_items_by_type, fetch_item
from db.pricing_repo  import fetch_all_pricing, upsert_pricing, delete_pricing
from models.costing   import calc_cost
from ui.helpers       import make_table, buttons_row, section_label, danger_button
from ui.widgets.category_manager import CategoryManager, CategoryCombo
from ui.widgets.filter_bar       import FilterBar
from ui.events import bus


def _spin(max_=9999999, dec=2):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(30)
    return s


# ══════════════════════════════════════════════════════════
# لوحة التسعير
# ══════════════════════════════════════════════════════════

class _PricingPanel(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._all_rows = []
        self._editing_id = None
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(8)

        # ── فورم التسعير ──
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        form_lay = QVBoxLayout(form_frame)
        form_lay.setContentsMargins(14, 12, 14, 12)
        form_lay.setSpacing(10)

        self.lbl_mode = QLabel("─── تسعير منتج ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#e65100; font-size:12px;")
        form_lay.addWidget(self.lbl_mode)

        row1 = QHBoxLayout()
        row1.setSpacing(12)

        # اختيار المنتج
        lbl_prod = QLabel("المنتج:")
        lbl_prod.setStyleSheet("font-weight:bold;")
        self.cmb_product = CategoryCombo(self.conn, scope="final")
        self.cmb_product.setMinimumHeight(32)
        self.cmb_product.setMinimumWidth(200)
        self.cmb_product.currentIndexChanged.connect(self._on_product_selected)

        # هامش الربح
        lbl_margin = QLabel("هامش الربح %:")
        lbl_margin.setStyleSheet("font-weight:bold;")
        self.sp_margin = _spin(1000, 2)
        self.sp_margin.setSuffix("  %")
        self.sp_margin.setValue(30)
        self.sp_margin.setFixedWidth(120)
        self.sp_margin.valueChanged.connect(self._update_price_preview)

        # السعر المقترح
        self.lbl_suggested = QLabel("─")
        self.lbl_suggested.setStyleSheet(
            "color:#1a6e1a; font-weight:bold; font-size:12px;"
            "background:#f0faf0; border:1px solid #b2dfb2;"
            "border-radius:4px; padding:4px 10px;"
        )

        # السعر اليدوي
        lbl_price = QLabel("السعر النهائي:")
        lbl_price.setStyleSheet("font-weight:bold;")
        self.sp_price = _spin()
        self.sp_price.setFixedWidth(130)

        row1.addWidget(lbl_prod)
        row1.addWidget(self.cmb_product, stretch=2)
        row1.addSpacing(8)
        row1.addWidget(lbl_margin)
        row1.addWidget(self.sp_margin)
        row1.addWidget(QLabel("→"))
        row1.addWidget(self.lbl_suggested)
        row1.addSpacing(8)
        row1.addWidget(lbl_price)
        row1.addWidget(self.sp_price)
        row1.addStretch()
        form_lay.addLayout(row1)

        # أزرار
        self.btn_save   = QPushButton("💾  حفظ السعر")
        self.btn_cancel = QPushButton("✖  إلغاء")
        self.btn_del    = danger_button("🗑️  حذف السعر")
        for btn in (self.btn_save, self.btn_cancel, self.btn_del):
            btn.setMinimumHeight(30)
        self.btn_cancel.setVisible(False)
        self.btn_del.setVisible(False)
        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self._reset_form)
        self.btn_del.clicked.connect(self._delete)
        form_lay.addLayout(buttons_row(self.btn_save, self.btn_cancel, self.btn_del))

        root.addWidget(form_frame)

        # ── شريط الفلتر ──
        root.addWidget(section_label("─── قائمة الأسعار ───"))
        self._filter = FilterBar(self.conn, scope="final")
        self._filter.filter_changed.connect(self._apply_filter)
        root.addWidget(self._filter)

        # ── جدول الأسعار ──
        self.table = make_table(
            ["ID", "المنتج", "التصنيف", "التكلفة", "الهامش %", "السعر", "الربح"],
            stretch_col=1
        )
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Fixed)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 180)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 90)
        self.table.setColumnWidth(6, 90)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self._on_table_select)
        root.addWidget(self.table, stretch=1)

        btn_edit = QPushButton("✏️  تعديل المحدد")
        btn_edit.setMinimumHeight(30)
        btn_edit.clicked.connect(self._edit_selected)
        root.addLayout(buttons_row(btn_edit))

    # ══════════════════════════════════════════════════════
    # منطق
    # ══════════════════════════════════════════════════════

    def _on_product_selected(self):
        self._update_price_preview()

    def _update_price_preview(self):
        prod_id = self.cmb_product.get_category()
        if prod_id is None:
            self.lbl_suggested.setText("─")
            return
        cost    = calc_cost(self.conn, prod_id)
        margin  = self.sp_margin.value() / 100.0
        price   = cost * (1 + margin)
        self.lbl_suggested.setText(f"{price:.2f}  جنيه")
        # نحدّث السعر اليدوي تلقائياً لو مش في وضع تعديل
        if self._editing_id is None:
            self.sp_price.setValue(price)

    def _save(self):
        prod_id = self.cmb_product.get_category()
        if prod_id is None:
            QMessageBox.warning(self, "تنبيه", "اختر منتجاً أولاً")
            return
        margin = self.sp_margin.value()
        price  = self.sp_price.value()
        if price <= 0:
            QMessageBox.warning(self, "تنبيه", "السعر يجب أن يكون أكبر من صفر")
            return
        upsert_pricing(self.conn, prod_id, margin, price)
        self._reset_form()
        bus.data_changed.emit()

    def _delete(self):
        if self._editing_id is None:
            return
        item = fetch_item(self.conn, self._editing_id)
        name = item["name"] if item else f"ID:{self._editing_id}"
        if QMessageBox.question(
            self, "تأكيد", f"حذف سعر «{name}»؟",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            delete_pricing(self.conn, self._editing_id)
            self._reset_form()
            bus.data_changed.emit()

    def _reset_form(self):
        self._editing_id = None
        self.cmb_product.setCurrentIndex(0)
        self.sp_margin.setValue(30)
        self.sp_price.setValue(0)
        self.lbl_suggested.setText("─")
        self.lbl_mode.setText("─── تسعير منتج ───")
        self.btn_cancel.setVisible(False)
        self.btn_del.setVisible(False)

    def _edit_selected(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر منتجاً من الجدول أولاً")
            return
        prod_id = int(self.table.item(row, 0).text())
        self._load_for_edit(prod_id)

    def _on_table_select(self):
        row = self.table.currentRow()
        if row == -1:
            return
        # double-click للتعديل — single click للمعاينة فقط
        prod_id = int(self.table.item(row, 0).text())
        cost = calc_cost(self.conn, prod_id)
        self.lbl_suggested.setText(f"{cost:.2f}  جنيه (تكلفة)")

    def _load_for_edit(self, prod_id: int):
        from db.pricing_repo import fetch_pricing
        pricing = fetch_pricing(self.conn, prod_id)
        item    = fetch_item(self.conn, prod_id)
        if not item:
            return
        self._editing_id = prod_id
        self.cmb_product.set_category(prod_id)
        if pricing:
            self.sp_margin.setValue(pricing["margin"])
            self.sp_price.setValue(pricing["price"])
        else:
            cost = calc_cost(self.conn, prod_id)
            self.sp_margin.setValue(30)
            self.sp_price.setValue(cost * 1.3)
        self.lbl_mode.setText(f"─── تعديل سعر: {item['name']} ───")
        self.btn_cancel.setVisible(True)
        self.btn_del.setVisible(bool(pricing))
        self._update_price_preview()

    def _load(self):
        self._all_rows = list(fetch_all_pricing(self.conn))
        self._apply_filter()

    def _apply_filter(self):
        self.table.setRowCount(0)
        shown = 0
        for row in self._all_rows:
            if not self._filter.match(row["name"], row["category_id"]):
                continue
            cost    = calc_cost(self.conn, row["id"])
            margin  = row["margin"] if row["pricing_id"] else "─"
            price   = row["price"]  if row["pricing_id"] else "─"
            profit  = (row["price"] - cost) if row["pricing_id"] else "─"

            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(row["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(row["category_name"] or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{cost:.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(
                f"{margin:.1f} %" if isinstance(margin, float) else margin
            ))
            self.table.setItem(r, 5, QTableWidgetItem(
                f"{price:.2f}" if isinstance(price, float) else price
            ))
            self.table.setItem(r, 6, QTableWidgetItem(
                f"{profit:.2f}" if isinstance(profit, float) else profit
            ))

            # لون الربح
            if isinstance(profit, float):
                color = "#1b5e20" if profit >= 0 else "#b71c1c"
                item_w = self.table.item(r, 6)
                item_w.setForeground(Qt.GlobalColor.darkGreen if profit >= 0 else Qt.GlobalColor.red)

            shown += 1
        self._filter.set_count(shown, len(self._all_rows))


# ══════════════════════════════════════════════════════════
# التبويب الرئيسي
# ══════════════════════════════════════════════════════════

class PricingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn = get_connection()
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()
        tabs.addTab(_PricingPanel(self.conn),                       "💰  الأسعار")
        tabs.addTab(CategoryManager(self.conn, scope="final"),      "🏷️  التصنيفات")

        root.addWidget(tabs)

    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)
