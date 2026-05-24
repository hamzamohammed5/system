"""
ui/widgets/shared/scenario_comparison_widget.py
================================================
ScenarioComparisonWidget — يقارن تكلفة السيناريو الافتراضي بأي سيناريو آخر
ويحسب الفرق في الربح لو السعر ثابت.

[تحديث]: يستخدم stat_card_pair من stat_row بدل _stat_card المحلية.

الاستخدام:
    widget = ScenarioComparisonWidget(conn)
    widget.load_product(item_id, current_price)
    layout.addWidget(widget)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QFrame,
)
from PyQt5.QtCore import Qt

from models.costing import calc_cost
from ui.widgets.shared.stat_row import stat_card_pair   # ← الموحد بدل _stat_card المحلية


class ScenarioComparisonWidget(QFrame):
    """
    يقارن السيناريو الافتراضي بسيناريو مختار.
    يعرض:
      - التكلفة في كل سيناريو
      - الفرق في التكلفة (زيادة / توفير)
      - الفرق في الربح (السعر ثابت)
      - هامش الربح الفعلي في السيناريو المختار
    """

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn          = conn
        self._item_id      = None
        self._fixed_price  = 0.0
        self._default_cost = 0.0
        self._build()

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        self.setStyleSheet("""
            QFrame {
                background: #f3e5f5;
                border: 1px solid #ce93d8;
                border-radius: 8px;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(8)

        # ── رأس ──
        header_row = QHBoxLayout()
        lbl_icon = QLabel("📊")
        lbl_icon.setStyleSheet("font-size:14px; background:transparent; border:none;")
        lbl_title = QLabel("مقارنة السيناريوهات")
        lbl_title.setStyleSheet(
            "font-weight:bold; font-size:12px; color:#6a1b9a;"
            "background:transparent; border:none;"
        )
        lbl_title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        lbl_sc = QLabel("السيناريو المقارن:")
        lbl_sc.setStyleSheet(
            "font-size:11px; color:#6a1b9a;"
            "background:transparent; border:none;"
        )

        self.cmb_scenario = QComboBox()
        self.cmb_scenario.setMinimumHeight(28)
        self.cmb_scenario.setMinimumWidth(180)
        self.cmb_scenario.setStyleSheet("""
            QComboBox {
                background: white;
                border: 1px solid #ce93d8;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
                color: #4a148c;
            }
            QComboBox:focus { border-color: #7b1fa2; }
            QComboBox::drop-down { border: none; }
        """)
        self.cmb_scenario.currentIndexChanged.connect(self._on_scenario_changed)

        header_row.addWidget(lbl_icon)
        header_row.addWidget(lbl_title)
        header_row.addStretch()
        header_row.addWidget(lbl_sc)
        header_row.addWidget(self.cmb_scenario)
        root.addLayout(header_row)

        # ── الصف الأول: التكاليف — يستخدم stat_card_pair الموحدة ──
        cost_row = QHBoxLayout()
        cost_row.setSpacing(6)
        f1, self.lbl_default_cost = stat_card_pair("تكلفة السيناريو الافتراضي", "#1565c0")
        f2, self.lbl_compare_cost = stat_card_pair("تكلفة السيناريو المقارن",  "#6a1b9a")
        f3, self.lbl_cost_diff    = stat_card_pair("فرق التكلفة",               "#e65100")
        for f in (f1, f2, f3):
            cost_row.addWidget(f, stretch=1)
        root.addLayout(cost_row)

        # ── الصف الثاني: الربح (السعر ثابت) ──
        profit_row = QHBoxLayout()
        profit_row.setSpacing(6)
        f4, self.lbl_fixed_price    = stat_card_pair("السعر الثابت",               "#555")
        f5, self.lbl_default_profit = stat_card_pair("ربح السيناريو الافتراضي",    "#2e7d32")
        f6, self.lbl_compare_profit = stat_card_pair("ربح السيناريو المقارن",      "#6a1b9a")
        f7, self.lbl_profit_diff    = stat_card_pair("فرق الربح",                  "#e65100")
        f8, self.lbl_compare_margin = stat_card_pair("هامش الربح (سيناريو مقارن)", "#1b5e20")
        for f in (f4, f5, f6, f7, f8):
            profit_row.addWidget(f, stretch=1)
        root.addLayout(profit_row)

        # ── رسالة التوجيه ──
        self.lbl_note = QLabel("اختر سيناريو للمقارنة")
        self.lbl_note.setStyleSheet(
            "font-size:10px; color:#6a1b9a; background:transparent; border:none;"
        )
        self.lbl_note.setAlignment(Qt.AlignCenter)
        root.addWidget(self.lbl_note)

    # ══════════════════════════════════════════════════════
    # API خارجي
    # ══════════════════════════════════════════════════════

    def load_product(self, item_id: int, fixed_price: float):
        self._item_id     = item_id
        self._fixed_price = fixed_price
        self._default_cost = self._calc_default_cost(item_id)
        self._reload_scenarios()

    def update_price(self, new_price: float):
        self._fixed_price = new_price
        self._refresh_comparison()

    def clear(self):
        self._item_id      = None
        self._fixed_price  = 0.0
        self._default_cost = 0.0
        self.cmb_scenario.blockSignals(True)
        self.cmb_scenario.clear()
        self.cmb_scenario.blockSignals(False)
        self._reset_labels()

    # ══════════════════════════════════════════════════════
    # التحميل والحساب
    # ══════════════════════════════════════════════════════

    def _reload_scenarios(self):
        self.cmb_scenario.blockSignals(True)
        self.cmb_scenario.clear()
        self.cmb_scenario.addItem("─ اختر سيناريو ─", None)

        if self._item_id is None:
            self.cmb_scenario.blockSignals(False)
            return

        try:
            rows = self.conn.execute(
                "SELECT id, name, is_default FROM bom_scenarios "
                "WHERE item_id=? ORDER BY id",
                (self._item_id,)
            ).fetchall()
        except Exception:
            rows = []

        for r in rows:
            star = "⭐ " if r["is_default"] else "📋 "
            label = f"{star}{r['name']}"
            self.cmb_scenario.addItem(label, r["id"])

        self.cmb_scenario.blockSignals(False)
        self._refresh_comparison()

    def _calc_default_cost(self, item_id: int) -> float:
        return calc_cost(self.conn, item_id)

    def _calc_scenario_cost(self, scenario_id: int) -> float:
        try:
            from db.costing.bom_scenarios_repo import fetch_bom_for_scenario
            from db.shared.items_repo import fetch_item
            from models.costing_base import raw_unit_price, effective_qty
            from models.costing_ops import calc_labor_op_cost, calc_machine_op_cost

            bom_rows = fetch_bom_for_scenario(self.conn, scenario_id)
            total = 0.0
            visited = set()

            for row in bom_rows:
                child_type = row["child_type"]
                child_id   = row["child_id"]
                qty        = row["qty"]
                waste_pct  = float(row["waste_pct"]) if row["waste_pct"] else 0.0
                eff_qty    = effective_qty(qty, waste_pct)

                if child_type == "raw":
                    child = fetch_item(self.conn, child_id)
                    unit_cost = raw_unit_price(child) if child else 0.0
                elif child_type == "semi":
                    if child_id not in visited:
                        visited.add(child_id)
                    unit_cost = calc_cost(self.conn, child_id)
                elif child_type == "labor_op":
                    unit_cost = calc_labor_op_cost(self.conn, child_id)
                elif child_type == "machine_op":
                    mor_id = None
                    try:
                        mor_id = row["machine_op_row_id"]
                    except (KeyError, IndexError):
                        pass
                    unit_cost = calc_machine_op_cost(self.conn, child_id, row_id=mor_id)
                else:
                    unit_cost = 0.0

                total += unit_cost * eff_qty

            return total
        except Exception:
            return 0.0

    def _refresh_comparison(self):
        sc_id = self.cmb_scenario.currentData()

        self.lbl_fixed_price.setText(f"{self._fixed_price:.2f} ج")
        self.lbl_default_cost.setText(f"{self._default_cost:.4f} ج")
        default_profit = self._fixed_price - self._default_cost
        self.lbl_default_profit.setText(f"{default_profit:.2f} ج")
        self._color_label(self.lbl_default_profit, default_profit)

        if sc_id is None:
            for lbl in (self.lbl_compare_cost, self.lbl_cost_diff,
                        self.lbl_compare_profit, self.lbl_profit_diff,
                        self.lbl_compare_margin):
                lbl.setText("─")
            self.lbl_note.setText("اختر سيناريو للمقارنة مع السيناريو الافتراضي")
            return

        compare_cost = self._calc_scenario_cost(sc_id)
        self.lbl_compare_cost.setText(f"{compare_cost:.4f} ج")

        cost_diff = compare_cost - self._default_cost
        sign = "+" if cost_diff > 0 else ""
        self.lbl_cost_diff.setText(f"{sign}{cost_diff:.4f} ج")
        self._color_label(self.lbl_cost_diff, -cost_diff)

        compare_profit = self._fixed_price - compare_cost
        self.lbl_compare_profit.setText(f"{compare_profit:.2f} ج")
        self._color_label(self.lbl_compare_profit, compare_profit)

        profit_diff = compare_profit - default_profit
        sign2 = "+" if profit_diff > 0 else ""
        self.lbl_profit_diff.setText(f"{sign2}{profit_diff:.2f} ج")
        self._color_label(self.lbl_profit_diff, profit_diff)

        if compare_cost > 0 and self._fixed_price > 0:
            margin = (self._fixed_price - compare_cost) / compare_cost * 100
            self.lbl_compare_margin.setText(f"{margin:.1f} %")
            self._color_label(self.lbl_compare_margin, margin)
        else:
            self.lbl_compare_margin.setText("─")

        if cost_diff > 0:
            self.lbl_note.setText(
                f"⬆ السيناريو المقارن أعلى تكلفة بـ {cost_diff:.4f} ج/قطعة — "
                f"الربح ينخفض {abs(profit_diff):.2f} ج"
            )
        elif cost_diff < 0:
            self.lbl_note.setText(
                f"⬇ السيناريو المقارن أقل تكلفة بـ {abs(cost_diff):.4f} ج/قطعة — "
                f"الربح يرتفع {abs(profit_diff):.2f} ج"
            )
        else:
            self.lbl_note.setText("التكلفة متساوية في السيناريوهين")

    # ══════════════════════════════════════════════════════
    # مساعدات
    # ══════════════════════════════════════════════════════

    def _color_label(self, lbl: QLabel, value: float):
        if value > 0:
            color = "#1b5e20"
        elif value < 0:
            color = "#b71c1c"
        else:
            color = "#555555"
        lbl.setStyleSheet(
            f"font-size:13px; font-weight:bold; color:{color};"
            "background:transparent; border:none;"
        )

    def _reset_labels(self):
        for lbl in (self.lbl_default_cost, self.lbl_compare_cost, self.lbl_cost_diff,
                    self.lbl_fixed_price, self.lbl_default_profit,
                    self.lbl_compare_profit, self.lbl_profit_diff,
                    self.lbl_compare_margin):
            lbl.setText("─")
        self.lbl_note.setText("اختر منتجاً لبدء المقارنة")

    def _on_scenario_changed(self, _):
        self._refresh_comparison()