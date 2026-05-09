"""
ui/tabs/pricing_tab.py — مع عرض التكلفة والربح
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget,
    QPushButton, QTableWidgetItem, QLabel,
    QDoubleSpinBox, QMessageBox, QHeaderView, QFrame, QComboBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.connection    import get_connection
from db.items_repo    import fetch_items_by_type, fetch_item
from db.pricing_repo  import fetch_all_pricing, upsert_pricing, delete_pricing
from models.costing   import calc_cost
from ui.helpers       import make_table, buttons_row, section_label, danger_button
from ui.widgets.category_manager import CategoryManager
from ui.widgets.filter_bar       import FilterBar
from ui.events import bus


def _spin(max_=9999999, dec=2):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(30)
    return s


def _stat_box(label: str, color: str = "#1565c0") -> tuple:
    frame = QFrame()
    frame.setStyleSheet("""
        QFrame {
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 4px;
        }
    """)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(10, 6, 10, 6)
    lay.setSpacing(2)
    lbl_title = QLabel(label)
    lbl_title.setStyleSheet("font-size:10px; color:#888; background:transparent; border:none;")
    lbl_title.setAlignment(Qt.AlignCenter)
    lbl_val = QLabel("─")
    lbl_val.setStyleSheet(
        f"font-size:14px; font-weight:bold; color:{color};"
        "background:transparent; border:none;"
    )
    lbl_val.setAlignment(Qt.AlignCenter)
    lay.addWidget(lbl_title)
    lay.addWidget(lbl_val)
    return frame, lbl_val


class _PricingPanel(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._all_rows   = []
        self._editing_id = None
        self._build()
        self._load_products_combo()
        self._load()
        bus.data_changed.connect(self._load_products_combo)
        bus.data_changed.connect(self._load)

    def _load_products_combo(self):
        prev = self.cmb_product.currentData()
        self.cmb_product.blockSignals(True)
        self.cmb_product.clear()
        self.cmb_product.addItem("— اختر منتجاً —", None)
        for row in fetch_items_by_type(self.conn, "final"):
            self.cmb_product.addItem(row["name"], row["id"])
        restored = False
        for i in range(self.cmb_product.count()):
            if self.cmb_product.itemData(i) == prev:
                self.cmb_product.setCurrentIndex(i)
                restored = True
                break
        if not restored:
            self.cmb_product.setCurrentIndex(0)
        self.cmb_product.blockSignals(False)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(8)

        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame { background: white; border: 1px solid #e0e0e0; border-radius: 8px; }
        """)
        form_lay = QVBoxLayout(form_frame)
        form_lay.setContentsMargins(14, 12, 14, 12)
        form_lay.setSpacing(10)

        self.lbl_mode = QLabel("─── تسعير منتج ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#e65100; font-size:12px;")
        form_lay.addWidget(self.lbl_mode)

        row1 = QHBoxLayout()
        row1.setSpacing(12)

        lbl_prod = QLabel("المنتج:")
        lbl_prod.setStyleSheet("font-weight:bold;")

        # ✅ QComboBox عادي — بيقرأ المنتجات مباشرة
        self.cmb_product = QComboBox()
        self.cmb_product.setMinimumHeight(32)
        self.cmb_product.setMinimumWidth(200)
        self.cmb_product.currentIndexChanged.connect(self._on_product_selected)

        lbl_margin = QLabel("هامش الربح:")
        lbl_margin.setStyleSheet("font-weight:bold;")

        self.sp_margin = _spin(1000, 2)
        self.sp_margin.setValue(30)
        self.sp_margin.setFixedWidth(110)
        self.sp_margin.valueChanged.connect(self._update_preview)

        # ✅ علامة % برا المستطيل
        lbl_pct = QLabel("%")
        lbl_pct.setStyleSheet("font-weight:bold; color:#e65100; font-size:13px;")

        lbl_price = QLabel("السعر النهائي:")
        lbl_price.setStyleSheet("font-weight:bold;")
        self.sp_price = _spin()
        self.sp_price.setFixedWidth(130)
        self.sp_price.valueChanged.connect(self._update_profit_from_price)

        row1.addWidget(lbl_prod)
        row1.addWidget(self.cmb_product, stretch=2)
        row1.addSpacing(8)
        row1.addWidget(lbl_margin)
        row1.addWidget(self.sp_margin)
        row1.addWidget(lbl_pct)
        row1.addSpacing(8)
        row1.addWidget(lbl_price)
        row1.addWidget(self.sp_price)
        row1.addStretch()
        form_lay.addLayout(row1)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(8)
        f1, self.lbl_stat_cost        = _stat_box("التكلفة",              "#1565c0")
        f2, self.lbl_stat_price       = _stat_box("سعر البيع المقترح",    "#2e7d32")
        f3, self.lbl_stat_manual      = _stat_box("السعر اليدوي",         "#e65100")
        f4, self.lbl_stat_profit      = _stat_box("الربح",                "#1b5e20")
        f5, self.lbl_stat_margin_pct  = _stat_box("هامش الربح الفعلي %", "#6a1b9a")
        for f in (f1, f2, f3, f4, f5):
            stats_row.addWidget(f, stretch=1)
        form_lay.addLayout(stats_row)

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

        root.addWidget(section_label("─── قائمة الأسعار ───"))
        self._filter = FilterBar(self.conn, scope="final")
        self._filter.filter_changed.connect(self._apply_filter)
        root.addWidget(self._filter)

        self.table = make_table(
            ["ID", "المنتج", "التصنيف", "التكلفة", "الهامش %",
             "السعر", "الربح", "هامش فعلي %"],
            stretch_col=1
        )
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Fixed)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 160)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 70)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 80)
        self.table.setColumnWidth(7, 90)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self._on_table_select)
        root.addWidget(self.table, stretch=1)

        btn_edit = QPushButton("✏️  تعديل المحدد")
        btn_edit.setMinimumHeight(30)
        btn_edit.clicked.connect(self._edit_selected)
        root.addLayout(buttons_row(btn_edit))

    def _on_product_selected(self):
        self._update_preview()

    def _update_preview(self):
        prod_id = self.cmb_product.currentData()
        if prod_id is None:
            for lbl in (self.lbl_stat_cost, self.lbl_stat_price,
                        self.lbl_stat_manual, self.lbl_stat_profit,
                        self.lbl_stat_margin_pct):
                lbl.setText("─")
            return
        cost   = calc_cost(self.conn, prod_id)
        margin = self.sp_margin.value() / 100.0
        price  = cost * (1 + margin)
        self.lbl_stat_cost.setText(f"{cost:.2f}  ج")
        self.lbl_stat_price.setText(f"{price:.2f}  ج")
        if self._editing_id is None:
            self.sp_price.blockSignals(True)
            self.sp_price.setValue(price)
            self.sp_price.blockSignals(False)
        self._refresh_manual_stats(cost)

    def _update_profit_from_price(self):
        prod_id = self.cmb_product.currentData()
        if prod_id is None:
            return
        cost = calc_cost(self.conn, prod_id)
        self._refresh_manual_stats(cost)

    def _refresh_manual_stats(self, cost: float):
        manual = self.sp_price.value()
        profit = manual - cost
        margin_pct = ((manual - cost) / cost * 100) if cost > 0 else 0.0
        self.lbl_stat_manual.setText(f"{manual:.2f}  ج")
        color_profit = "#1b5e20" if profit >= 0 else "#b71c1c"
        self.lbl_stat_profit.setText(f"{profit:.2f}  ج")
        self.lbl_stat_profit.setStyleSheet(
            f"font-size:14px; font-weight:bold; color:{color_profit};"
            "background:transparent; border:none;"
        )
        self.lbl_stat_margin_pct.setText(f"{margin_pct:.1f} %")

    def _save(self):
        prod_id = self.cmb_product.currentData()
        if prod_id is None:
            QMessageBox.warning(self, "تنبيه", "اختر منتجاً أولاً")
            return
        price = self.sp_price.value()
        if price <= 0:
            QMessageBox.warning(self, "تنبيه", "السعر يجب أن يكون أكبر من صفر")
            return
        upsert_pricing(self.conn, prod_id, self.sp_margin.value(), price)
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
        for lbl in (self.lbl_stat_cost, self.lbl_stat_price,
                    self.lbl_stat_manual, self.lbl_stat_profit,
                    self.lbl_stat_margin_pct):
            lbl.setText("─")
        self.lbl_mode.setText("─── تسعير منتج ───")
        self.btn_cancel.setVisible(False)
        self.btn_del.setVisible(False)

    def _edit_selected(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر منتجاً من الجدول أولاً")
            return
        self._load_for_edit(int(self.table.item(row, 0).text()))

    def _on_table_select(self):
        row = self.table.currentRow()
        if row == -1:
            return
        prod_id = int(self.table.item(row, 0).text())
        cost = calc_cost(self.conn, prod_id)
        self.lbl_stat_cost.setText(f"{cost:.2f}  ج (تكلفة)")

    def _load_for_edit(self, prod_id: int):
        from db.pricing_repo import fetch_pricing
        pricing = fetch_pricing(self.conn, prod_id)
        item    = fetch_item(self.conn, prod_id)
        if not item:
            return
        self._editing_id = prod_id
        for i in range(self.cmb_product.count()):
            if self.cmb_product.itemData(i) == prod_id:
                self.cmb_product.setCurrentIndex(i)
                break
        cost = calc_cost(self.conn, prod_id)
        if pricing:
            self.sp_margin.setValue(pricing["margin"])
            self.sp_price.setValue(pricing["price"])
        else:
            self.sp_margin.setValue(30)
            self.sp_price.setValue(cost * 1.3)
        self.lbl_mode.setText(f"─── تعديل سعر: {item['name']} ───")
        self.btn_cancel.setVisible(True)
        self.btn_del.setVisible(bool(pricing))
        self._refresh_manual_stats(cost)

    def _load(self):
        self._all_rows = list(fetch_all_pricing(self.conn))
        self._apply_filter()

    def _apply_filter(self):
        self.table.setRowCount(0)
        shown = 0
        for row in self._all_rows:
            if not self._filter.match(row["name"], row["category_id"]):
                continue
            cost   = calc_cost(self.conn, row["id"])
            has_p  = row["pricing_id"] is not None
            price  = row["price"]  if has_p else None
            margin = row["margin"] if has_p else None
            profit = (price - cost) if has_p else None
            margin_actual = ((price - cost) / cost * 100) if (has_p and cost > 0) else None

            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(row["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(row["category_name"] or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{cost:.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"{margin:.1f} %" if margin is not None else "─"))
            self.table.setItem(r, 5, QTableWidgetItem(f"{price:.2f}" if price is not None else "─"))
            profit_item = QTableWidgetItem(f"{profit:.2f}" if profit is not None else "─")
            if profit is not None:
                profit_item.setForeground(QColor("#1b5e20") if profit >= 0 else QColor("#b71c1c"))
            self.table.setItem(r, 6, profit_item)
            self.table.setItem(r, 7, QTableWidgetItem(f"{margin_actual:.1f} %" if margin_actual is not None else "─"))
            shown += 1
        self._filter.set_count(shown, len(self._all_rows))


class PricingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn = get_connection()
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        tabs = QTabWidget()
        tabs.addTab(_PricingPanel(self.conn),                  "💰  الأسعار")
        tabs.addTab(CategoryManager(self.conn, scope="final"), "🏷️  التصنيفات")
        root.addWidget(tabs)

    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)