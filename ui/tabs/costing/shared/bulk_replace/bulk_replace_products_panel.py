"""
ui/tabs/costing/shared/bulk_replace/bulk_replace_products_panel.py
==========================================
_ProductsPanel — لوحة عرض المنتجات المتأثرة في نافذة الاستبدال الشامل.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton,
    QScrollArea, QFrame,
)
from PyQt5.QtCore import Qt

from ui.app_settings        import _C
from ui.widgets.core.i18n   import tr
from .bulk_replace_helpers  import fetch_affected_products, ProductRow


class _ProductsPanel(QWidget):
    """
    لوحة المنتجات المتأثرة:
      - فلتر بالتصنيف
      - قائمة scrollable من ProductRow
      - شريط التحديد السريع
    """

    def __init__(self, conn, child_type: str, child_id: int, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self.child_type = child_type
        self.child_id   = child_id

        self._all_products: list = []
        self._product_rows: list = []

        self._build()
        self.load()

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        # ── شريط الفلتر ──
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel(f"🏷  {tr('filter_by_category')}:"))

        self.cmb_cat_filter = QComboBox()
        self.cmb_cat_filter.setMinimumHeight(30)
        self.cmb_cat_filter.setFixedWidth(200)
        self.cmb_cat_filter.setStyleSheet(
            f"background:{_C['bg_input']}; border:1px solid {_C['border']};"
            f"border-radius:4px; padding:2px 6px; color:{_C['text_primary']};"
        )
        self.cmb_cat_filter.addItem(f"— {tr('all')} —", None)
        self.cmb_cat_filter.currentIndexChanged.connect(self._apply_filter)

        self.lbl_count = QLabel()
        self.lbl_count.setStyleSheet(
            f"color:{_C['accent']}; font-weight:bold; font-size:11px;"
        )

        filter_row.addWidget(self.cmb_cat_filter)
        filter_row.addSpacing(16)
        filter_row.addWidget(self.lbl_count)
        filter_row.addStretch()
        lay.addLayout(filter_row)

        # ── منطقة الصفوف ──
        self._scroll_content = QWidget()
        self._scroll_content.setStyleSheet("background: transparent;")
        self._rows_layout = QVBoxLayout(self._scroll_content)
        self._rows_layout.setSpacing(4)
        self._rows_layout.setContentsMargins(0, 0, 4, 0)
        self._rows_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._scroll_content)
        scroll.setMinimumHeight(200)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {_C['border']};
                border-radius: 8px;
                background: {_C['bg_surface']};
            }}
        """)
        lay.addWidget(scroll, stretch=1)

        # ── شريط التحديد السريع ──
        lay.addWidget(self._build_quick_bar())

    def _build_quick_bar(self) -> QFrame:
        bar = QFrame()
        bar.setStyleSheet(
            f"QFrame {{ background:{_C['bg_input']}; border:1px solid {_C['border']};"
            "border-radius:6px; padding:2px; }"
        )
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.setSpacing(8)

        lbl = QLabel(f"{tr('quick_select')}:")
        lbl.setStyleSheet(f"font-size:11px; color:{_C['text_sec']};")

        _style = (
            f"QPushButton {{ background:{_C['bg_surface']}; border:1px solid {_C['border']};"
            "border-radius:4px; padding:2px 10px; font-size:11px; }"
            f"QPushButton:hover {{ background:{_C['accent_light']}; "
            f"border-color:{_C['border_focus']}; }}"
        )
        btn_all  = QPushButton(f"✅ {tr('select_all')}")
        btn_none = QPushButton(f"☐ {tr('select_none')}")
        btn_inv  = QPushButton(f"⇄ {tr('invert_selection')}")
        for btn in (btn_all, btn_none, btn_inv):
            btn.setMinimumHeight(26)
            btn.setStyleSheet(_style)

        btn_all.clicked.connect(lambda: self.select_all(True))
        btn_none.clicked.connect(lambda: self.select_all(False))
        btn_inv.clicked.connect(self.invert_selection)

        lay.addWidget(lbl)
        lay.addWidget(btn_all)
        lay.addWidget(btn_none)
        lay.addWidget(btn_inv)
        lay.addStretch()
        return bar

    # ══════════════════════════════════════════════════════
    # تحميل البيانات
    # ══════════════════════════════════════════════════════

    def load(self):
        self._all_products = fetch_affected_products(
            self.conn, self.child_type, self.child_id
        )
        self._fill_category_filter()
        self._rebuild_rows(self._all_products)

    def reload(self):
        self._all_products = fetch_affected_products(
            self.conn, self.child_type, self.child_id
        )
        self._apply_filter()

    def _fill_category_filter(self):
        self.cmb_cat_filter.blockSignals(True)
        while self.cmb_cat_filter.count() > 1:
            self.cmb_cat_filter.removeItem(1)

        seen_cats: dict = {}
        for prod in self._all_products:
            cid   = prod["category_id"]
            cname = prod["category_name"]
            if cid not in seen_cats:
                seen_cats[cid] = cname

        for cid, cname in sorted(seen_cats.items(), key=lambda x: x[1] or ""):
            self.cmb_cat_filter.addItem(cname, cid)

        self.cmb_cat_filter.blockSignals(False)

    # ══════════════════════════════════════════════════════
    # الفلترة والعرض
    # ══════════════════════════════════════════════════════

    def _apply_filter(self):
        cat_id = self.cmb_cat_filter.currentData()
        if cat_id is None:
            filtered = self._all_products
        else:
            filtered = [
                p for p in self._all_products if p["category_id"] == cat_id
            ]
        self._rebuild_rows(filtered)

    def _rebuild_rows(self, products: list):
        while self._rows_layout.count() > 1:
            item = self._rows_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self._product_rows.clear()

        if not products:
            lbl = QLabel(f"⚠️  {tr('no_products_linked')}")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(
                f"color:{_C['text_muted']}; font-size:12px; padding:20px;"
            )
            self._rows_layout.insertWidget(0, lbl)
            self._update_count()
            return

        for prod in products:
            row = ProductRow(prod)
            self._product_rows.append(row)
            self._rows_layout.insertWidget(
                self._rows_layout.count() - 1, row
            )
        self._update_count()

    def _update_count(self):
        total    = len(self._product_rows)
        selected = sum(1 for r in self._product_rows if r.is_selected)
        self.lbl_count.setText(
            f"{tr('total')}: {total}  │  {tr('selected')}: {selected}"
        )

    # ══════════════════════════════════════════════════════
    # API خارجي
    # ══════════════════════════════════════════════════════

    def select_all(self, val: bool):
        for row in self._product_rows:
            row.set_selected(val)
        self._update_count()

    def invert_selection(self):
        for row in self._product_rows:
            row.set_selected(not row.is_selected)
        self._update_count()

    def get_selected_rows(self) -> list:
        return [r for r in self._product_rows if r.is_selected]

    def has_products(self) -> bool:
        return bool(self._product_rows)