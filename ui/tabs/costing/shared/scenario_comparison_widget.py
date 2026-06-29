"""
ui/tabs/costing/shared/scenario_comparison_widget.py
================================================
ScenarioComparisonWidget — يقارن تكلفة السيناريو الافتراضي بأي سيناريو آخر.

[Refactor] ربط bus.theme_changed لتحديث stylesheet ديناميكياً.
[Refactor] استخدام ScenarioService بدل منطق الحساب المباشر داخل الـ widget.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QFrame,
)
from PyQt5.QtCore import Qt

from models.costing               import calc_cost
from services.costing.scenario_service import ScenarioService
from ui.theme import _C
from ui.widgets.core.i18n         import tr
from ui.widgets.components.stat_card import stat_card_pair
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.font import FS_XS, FS_SM, FS_BASE, FS_MD, FS_LG


class ScenarioComparisonWidget(QFrame, WidgetMixin):
    """
    يقارن السيناريو الافتراضي بسيناريو مختار ويعرض:
      - التكلفة في كل سيناريو
      - الفرق في التكلفة
      - الفرق في الربح
      - هامش الربح الفعلي
    """

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn          = conn
        self._item_id      = None
        self._fixed_price  = 0.0
        self._default_cost = 0.0
        self._build()
        self._init_widget_mixin(lang=False, data=False)

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        self._apply_frame_style()

        root = QVBoxLayout(self)        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(8)

        # ── رأس ──
        header_row = QHBoxLayout()
        lbl_icon = QLabel("📊")
        lbl_icon.setStyleSheet(
            f"font-size:{FS_LG}px; background:transparent; border:none;"
        )
        self.lbl_title = QLabel(tr("scenario_comparison"))
        self.lbl_title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        lbl_sc = QLabel(f"{tr('compare_scenario')}:")
        self._lbl_sc = lbl_sc

        self.cmb_scenario = QComboBox()
        self.cmb_scenario.setMinimumHeight(28)
        self.cmb_scenario.setMinimumWidth(180)
        self.cmb_scenario.currentIndexChanged.connect(self._on_scenario_changed)

        header_row.addWidget(lbl_icon)
        header_row.addWidget(self.lbl_title)
        header_row.addStretch()
        header_row.addWidget(lbl_sc)
        header_row.addWidget(self.cmb_scenario)
        root.addLayout(header_row)

        # ── صف التكاليف ──
        cost_row = QHBoxLayout()
        cost_row.setSpacing(6)
        f1, self.lbl_default_cost = stat_card_pair(
            tr("default_scenario_cost"), _C['accent']
        )
        f2, self.lbl_compare_cost = stat_card_pair(
            tr("compare_scenario_cost"), _C['purple']
        )
        f3, self.lbl_cost_diff    = stat_card_pair(
            tr("cost_diff"), _C['orange']
        )
        for f in (f1, f2, f3):
            cost_row.addWidget(f, stretch=1)
        root.addLayout(cost_row)

        # ── صف الربح ──
        profit_row = QHBoxLayout()
        profit_row.setSpacing(6)
        f4, self.lbl_fixed_price    = stat_card_pair(tr("fixed_price"),              _C['text_sec'])
        f5, self.lbl_default_profit = stat_card_pair(tr("default_scenario_profit"),  _C['success'])
        f6, self.lbl_compare_profit = stat_card_pair(tr("compare_scenario_profit"),  _C['purple'])
        f7, self.lbl_profit_diff    = stat_card_pair(tr("profit_diff"),               _C['orange'])
        f8, self.lbl_compare_margin = stat_card_pair(tr("compare_profit_margin"),     _C['success'])
        for f in (f4, f5, f6, f7, f8):
            profit_row.addWidget(f, stretch=1)
        root.addLayout(profit_row)

        # ── رسالة التوجيه ──
        self.lbl_note = QLabel(tr("select_scenario_to_compare"))
        self.lbl_note.setAlignment(Qt.AlignCenter)
        root.addWidget(self.lbl_note)

        self._refresh_style()

    def _apply_frame_style(self):
        self.setStyleSheet(f"""
            QFrame {{
                background: {_C['purple_bg']};
                border: 1px solid {_C['purple_border']};
                border-radius: 8px;
            }}
        """)

    def _refresh_style(self, *_):
        """يُطبق الـ stylesheet عند تغيير الثيم."""
        self._apply_frame_style()
        if hasattr(self, "lbl_title"):
            self.lbl_title.setStyleSheet(
                f"font-weight:bold; font-size:{FS_BASE}px; color:{_C['purple']};"
                "background:transparent; border:none;"
            )
        if hasattr(self, "_lbl_sc"):
            self._lbl_sc.setStyleSheet(
                f"font-size:{FS_SM}px; color:{_C['purple']}; background:transparent; border:none;"
            )
        if hasattr(self, "cmb_scenario"):
            self.cmb_scenario.setStyleSheet(f"""
                QComboBox {{
                    background: {_C['bg_input']};
                    border: 1px solid {_C['purple_border']};
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-size: {FS_SM}px;
                    color: {_C['purple']};
                }}
                QComboBox:focus {{ border-color: {_C['purple']}; }}
                QComboBox::drop-down {{ border: none; }}
            """)
        if hasattr(self, "lbl_note"):
            self.lbl_note.setStyleSheet(
                f"font-size:{FS_XS}px; color:{_C['purple']}; background:transparent; border:none;"
            )

    # ══════════════════════════════════════════════════════
    # API خارجي
    # ══════════════════════════════════════════════════════

    def load_product(self, item_id: int, fixed_price: float):
        self._item_id      = item_id
        self._fixed_price  = fixed_price
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
        self.cmb_scenario.addItem(f"─ {tr('select_scenario')} ─", None)

        if self._item_id is None:
            self.cmb_scenario.blockSignals(False)
            return

        try:
            svc  = ScenarioService(self.conn)
            rows = svc.list(self._item_id)
        except Exception:
            rows = []

        for sc in rows:
            star = "⭐ " if sc.is_default else "📋 "
            self.cmb_scenario.addItem(f"{star}{sc.name}", sc.id)

        self.cmb_scenario.blockSignals(False)
        self._refresh_comparison()

    def _calc_default_cost(self, item_id: int) -> float:
        return calc_cost(self.conn, item_id)

    def _calc_scenario_cost(self, scenario_id: int) -> float:
        """
        [Refactor] استخدام ScenarioService.calc_cost بدل منطق الحساب
        المعقد الذي كان داخل الـ widget مباشرة.
        """
        try:
            svc = ScenarioService(self.conn)
            return svc.calc_cost(scenario_id)
        except Exception:
            return 0.0

    def _refresh_comparison(self):
        sc_id = self.cmb_scenario.currentData()

        self.lbl_fixed_price.setText(
            f"{self._fixed_price:.2f} {tr('currency_abbr')}"
        )
        self.lbl_default_cost.setText(
            f"{self._default_cost:.4f} {tr('currency_abbr')}"
        )
        default_profit = self._fixed_price - self._default_cost
        self.lbl_default_profit.setText(
            f"{default_profit:.2f} {tr('currency_abbr')}"
        )
        self._color_label(self.lbl_default_profit, default_profit)

        if sc_id is None:
            for lbl in (self.lbl_compare_cost, self.lbl_cost_diff,
                        self.lbl_compare_profit, self.lbl_profit_diff,
                        self.lbl_compare_margin):
                lbl.setText("─")
            self.lbl_note.setText(tr("select_scenario_to_compare"))
            return

        compare_cost = self._calc_scenario_cost(sc_id)
        self.lbl_compare_cost.setText(
            f"{compare_cost:.4f} {tr('currency_abbr')}"
        )

        cost_diff = compare_cost - self._default_cost
        sign      = "+" if cost_diff > 0 else ""
        self.lbl_cost_diff.setText(
            f"{sign}{cost_diff:.4f} {tr('currency_abbr')}"
        )
        self._color_label(self.lbl_cost_diff, -cost_diff)

        compare_profit = self._fixed_price - compare_cost
        self.lbl_compare_profit.setText(
            f"{compare_profit:.2f} {tr('currency_abbr')}"
        )
        self._color_label(self.lbl_compare_profit, compare_profit)

        profit_diff = compare_profit - default_profit
        sign2       = "+" if profit_diff > 0 else ""
        self.lbl_profit_diff.setText(
            f"{sign2}{profit_diff:.2f} {tr('currency_abbr')}"
        )
        self._color_label(self.lbl_profit_diff, profit_diff)

        if compare_cost > 0 and self._fixed_price > 0:
            margin = (self._fixed_price - compare_cost) / compare_cost * 100
            self.lbl_compare_margin.setText(f"{margin:.1f} %")
            self._color_label(self.lbl_compare_margin, margin)
        else:
            self.lbl_compare_margin.setText("─")

        if cost_diff > 0:
            self.lbl_note.setText(
                f"⬆ {tr('compare_higher_cost')} {cost_diff:.4f} "
                f"{tr('currency_per_piece')} — "
                f"{tr('profit_decreases')} {abs(profit_diff):.2f} "
                f"{tr('currency_abbr')}"
            )
        elif cost_diff < 0:
            self.lbl_note.setText(
                f"⬇ {tr('compare_lower_cost')} {abs(cost_diff):.4f} "
                f"{tr('currency_per_piece')} — "
                f"{tr('profit_increases')} {abs(profit_diff):.2f} "
                f"{tr('currency_abbr')}"
            )
        else:
            self.lbl_note.setText(tr("equal_cost_scenarios"))

    # ══════════════════════════════════════════════════════
    # مساعدات
    # ══════════════════════════════════════════════════════

    def _color_label(self, lbl: QLabel, value: float):
        color = (
            _C['success']      if value > 0
            else (_C['danger'] if value < 0
            else _C['text_sec'])
        )
        lbl.setStyleSheet(
            f"font-size:{FS_MD}px; font-weight:bold; color:{color};"
            "background:transparent; border:none;"
        )

    def _reset_labels(self):
        for lbl in (self.lbl_default_cost, self.lbl_compare_cost, self.lbl_cost_diff,
                    self.lbl_fixed_price, self.lbl_default_profit,
                    self.lbl_compare_profit, self.lbl_profit_diff,
                    self.lbl_compare_margin):
            lbl.setText("─")
        self.lbl_note.setText(tr("select_product_to_compare"))

    def _on_scenario_changed(self, _):
        self._refresh_comparison()