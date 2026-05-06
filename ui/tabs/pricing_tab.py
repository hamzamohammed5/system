"""
ui/tabs/pricing_tab.py
======================
تبويب التسعير — يحسب ويحفظ أسعار المنتجات النهائية.

الهيكل:
  ┌─────────────────────────────────────────┐
  │  فورم التسعير                           │
  │  [المنتج ▼]  [النسبة]  → السعر          │
  ├─────────────────────────────────────────┤
  │  جدول الأسعار المحفوظة                  │
  │  [فلتر التصنيف ▼]                       │
  └─────────────────────────────────────────┘

التحديثات:
  - PricingTab بات يحتوي على تبويبين داخليين:
      ① الأسعار (الفورم + الجدول)
      ② التصنيفات (CategoryManager بـ scope="pricing")
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QSplitter, QComboBox, QDoubleSpinBox, QLabel,
    QPushButton, QTableWidgetItem, QMessageBox,
    QGroupBox, QHeaderView, QTabWidget,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.connection       import get_connection
from db.items_repo       import fetch_items_by_type, fetch_item, update_item_category
from db.pricing_repo     import fetch_all_pricing, fetch_pricing, upsert_pricing, delete_pricing
from db.categories_repo  import fetch_all_categories
from models.costing      import calc_cost
from ui.helpers          import make_table, buttons_row, section_label, danger_button
from ui.widgets.category_manager import CategoryManager, CategoryCombo

from ui.events import bus

_SPLITTER_STYLE = """
    QSplitter::handle { background:#e0e0e0; border-top:1px solid #ccc; }
    QSplitter::handle:hover { background:#bbdefb; }
"""


# ══════════════════════════════════════════════════════════
# فورم التسعير
# ══════════════════════════════════════════════════════════

class _PricingForm(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        bus.data_changed.connect(self._refresh_products)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        grp  = QGroupBox("احسب سعر منتج")
        form = QFormLayout(grp)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        # ── تعريف كل الـ widgets أولاً ──

        # المنتج
        self.cmb_product = QComboBox()
        self.cmb_product.setMinimumHeight(32)
        self.cmb_product.currentIndexChanged.connect(self._on_product_changed)

        # التصنيف
        self.cmb_category = CategoryCombo(self.conn, scope="pricing")
        self.cmb_category.setMinimumHeight(32)

        # التكلفة (للعرض فقط)
        self.lbl_cost = QLabel("—")
        self.lbl_cost.setStyleSheet(
            "color:#555; background:#f5f5f5; border:1px solid #ddd;"
            "border-radius:4px; padding:4px 10px;"
        )

        # النسبة
        self.sp_margin = QDoubleSpinBox()
        self.sp_margin.setRange(0.01, 100.0)
        self.sp_margin.setDecimals(2)
        self.sp_margin.setValue(1.0)
        self.sp_margin.setSingleStep(0.1)
        self.sp_margin.setMinimumHeight(32)
        self.sp_margin.setSuffix("×")
        self.sp_margin.valueChanged.connect(self._update_preview)

        # السعر الناتج
        self.lbl_price = QLabel("—")
        self.lbl_price.setStyleSheet(
            "font-weight:bold; font-size:14px; color:#1a6e1a;"
            "background:#f0faf0; border:1px solid #b2dfb2;"
            "border-radius:4px; padding:6px 12px;"
        )

        # ── إضافة للفورم بعد تعريف الكل ──
        form.addRow("المنتج :",           self.cmb_product)
        form.addRow("التصنيف :",          self.cmb_category)
        form.addRow("التكلفة المحسوبة :", self.lbl_cost)
        form.addRow("نسبة التسعير :",     self.sp_margin)
        form.addRow("➡  السعر النهائي :", self.lbl_price)
        layout.addWidget(grp)

        # ── شرح النسبة ──
        hint = QLabel("مثال: 1.5 × التكلفة = ربح 50%  |  2.0 = ربح 100%")
        hint.setStyleSheet("color:#888; font-size:10px;")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

        # ── أزرار ──
        self.btn_save = QPushButton("💾  حفظ السعر")
        self.btn_save.setMinimumHeight(34)
        self.btn_save.setStyleSheet(
            "background:#1565c0; color:white; font-weight:bold; border-radius:4px;"
        )
        self.btn_save.clicked.connect(self._save)

        self.btn_clear = QPushButton("✖  مسح")
        self.btn_clear.setMinimumHeight(34)
        self.btn_clear.clicked.connect(self._clear)

        layout.addLayout(buttons_row(self.btn_save, self.btn_clear))
        layout.addStretch()

        self._refresh_products()

    def _refresh_products(self):
        prev = self.cmb_product.currentData()
        self.cmb_product.blockSignals(True)
        self.cmb_product.clear()
        self.cmb_product.addItem("— اختر منتجاً —", None)
        for row in fetch_items_by_type(self.conn, "final"):
            self.cmb_product.addItem(row["name"], row["id"])
        if prev:
            for i in range(self.cmb_product.count()):
                if self.cmb_product.itemData(i) == prev:
                    self.cmb_product.setCurrentIndex(i)
                    break
        self.cmb_product.blockSignals(False)
        self._on_product_changed()

    def _on_product_changed(self):
        pid = self.cmb_product.currentData()
        if pid is None:
            self.lbl_cost.setText("—")
            self.lbl_price.setText("—")
            self._cost = 0.0
            return

        self._cost = calc_cost(self.conn, pid)
        self.lbl_cost.setText(f"{self._cost:.4f}  جنيه")

        # ← جديد: حمّل تصنيف المنتج الحالي
        item = fetch_item(self.conn, pid)
        if item and item["category_id"]:
            self.cmb_category.set_category(item["category_id"])
        else:
            self.cmb_category.setCurrentIndex(0)

        pricing = fetch_pricing(self.conn, pid)
        if pricing:
            self.sp_margin.blockSignals(True)
            self.sp_margin.setValue(pricing["margin"])
            self.sp_margin.blockSignals(False)

        self._update_preview()

    def _update_preview(self):
        if not hasattr(self, "_cost"):
            return
        price = self._cost * self.sp_margin.value()
        self.lbl_price.setText(
            f"{price:.2f}  جنيه   "
            f"({self.sp_margin.value():.2f} × {self._cost:.4f})"
        )

    def _save(self):
        pid = self.cmb_product.currentData()
        if pid is None:
            QMessageBox.warning(self, "تنبيه", "اختر منتجاً أولاً")
            return

        margin   = self.sp_margin.value()
        price    = self._cost * margin
        cat_id   = self.cmb_category.get_category()   # ← جديد

        upsert_pricing(self.conn, pid, margin, price)

        # ← جديد: احفظ التصنيف على المنتج
        update_item_category(self.conn, pid, cat_id)

        QMessageBox.information(self, "تم", f"✅ تم حفظ السعر: {price:.2f} جنيه")
        bus.data_changed.emit()

    def _clear(self):
        self.cmb_product.setCurrentIndex(0)
        self.sp_margin.setValue(1.0)

    def load_product(self, item_id: int):
        """تحميل منتج من الجدول عند الضغط على تعديل."""
        for i in range(self.cmb_product.count()):
            if self.cmb_product.itemData(i) == item_id:
                self.cmb_product.setCurrentIndex(i)
                return


# ══════════════════════════════════════════════════════════
# جدول الأسعار
# ══════════════════════════════════════════════════════════

class _PricingTable(QWidget):
    def __init__(self, conn, form: _PricingForm, parent=None):
        super().__init__(parent)
        self.conn  = conn
        self._form = form
        self._filter_cat = None
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(6)

        # ── شريط الفلتر ──
        filter_row = QHBoxLayout()
        filter_row.addWidget(section_label("─── الأسعار المحفوظة ───"))
        filter_row.addStretch()
        filter_row.addWidget(QLabel("فلتر:"))
        self.cmb_filter = CategoryCombo(self.conn, scope="pricing")
        self.cmb_filter.setFixedWidth(160)
        self.cmb_filter.currentIndexChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self.cmb_filter)
        root.addLayout(filter_row)

        self.table = make_table(
            ["ID", "المنتج", "التصنيف", "التكلفة", "النسبة", "السعر"]
        )
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Fixed)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 70)
        self.table.setColumnWidth(5, 110)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table)

        btn_edit = QPushButton("✏️  تعديل")
        btn_del  = danger_button("🗑️  حذف السعر")
        for btn in (btn_edit, btn_del):
            btn.setMinimumHeight(30)
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        root.addLayout(buttons_row(btn_edit, btn_del))

    def _on_filter_changed(self):
        self._filter_cat = self.cmb_filter.get_category()
        self._load()

    def _edit(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر منتجاً أولاً")
            return
        item_id = int(self.table.item(row, 0).text())
        self._form.load_product(item_id)

    def _delete(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر منتجاً أولاً")
            return
        item_id   = int(self.table.item(row, 0).text())
        item_name = self.table.item(row, 1).text()
        if QMessageBox.question(
            self, "تأكيد", f"حذف سعر «{item_name}»؟",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            delete_pricing(self.conn, item_id)
            bus.data_changed.emit()

    def _load(self):
        self.table.setRowCount(0)
        for r, row in enumerate(fetch_all_pricing(self.conn)):
            # فلترة بالتصنيف
            if self._filter_cat is not None and row["category_id"] != self._filter_cat:
                continue
            # لو مفيش سعر محفوظ — احسبه ديناميكي
            cost   = calc_cost(self.conn, row["id"])
            margin = row["margin"] if row["pricing_id"] else None
            price  = row["price"]  if row["pricing_id"] else None

            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(row["name"]))

            # التصنيف (ملوّن)
            cat_item = QTableWidgetItem(row["category_name"] or "—")
            if row["category_color"]:
                cat_item.setForeground(QColor(row["category_color"]))
            self.table.setItem(r, 2, cat_item)

            self.table.setItem(r, 3, QTableWidgetItem(f"{cost:.4f}"))

            if margin is not None:
                self.table.setItem(r, 4, QTableWidgetItem(f"{margin:.2f}×"))
                price_item = QTableWidgetItem(f"{price:.2f} جنيه")
                price_item.setForeground(QColor("#1a6e1a"))
                self.table.setItem(r, 5, price_item)
            else:
                self.table.setItem(r, 4, QTableWidgetItem("—"))
                no_price = QTableWidgetItem("لم يُسعَّر بعد")
                no_price.setForeground(QColor("#999"))
                self.table.setItem(r, 5, no_price)


# ══════════════════════════════════════════════════════════
# اللوحة الرئيسية (فورم + جدول)
# ══════════════════════════════════════════════════════════

class _PricingMainPanel(QWidget):
    """
    اللوحة الرئيسية للتسعير:
      - فورم الحساب والحفظ
      - جدول الأسعار المحفوظة
    """
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(_SPLITTER_STYLE)

        self._form  = _PricingForm(self.conn)
        self._table = _PricingTable(self.conn, self._form)

        splitter.addWidget(self._form)
        splitter.addWidget(self._table)
        splitter.setSizes([300, 400])
        splitter.setCollapsible(0, True)

        root.addWidget(splitter)


# ══════════════════════════════════════════════════════════
# تبويب التسعير الرئيسي — مع تبويب التصنيفات
# ══════════════════════════════════════════════════════════

class PricingTab(QWidget):
    """
    يحتوي على تبويبين:
      ① الأسعار (الفورم + الجدول)
      ② التصنيفات (CategoryManager بـ scope="pricing")
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn = get_connection()
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()

        # ① لوحة الأسعار الرئيسية
        tabs.addTab(_PricingMainPanel(self.conn), "💰  الأسعار")

        # ② تصنيفات التسعير
        tabs.addTab(CategoryManager(self.conn, scope="pricing"), "🏷️  التصنيفات")

        root.addWidget(tabs)

    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)