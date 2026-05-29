"""
services/costing/scenario_service.py
======================================
ScenarioService — يغلّف كل عمليات bom_scenarios_repo
وحساب تكلفة السيناريو (كان موزعاً في scenario_comparison_widget).

يُستخدم من:
  - ui/tabs/costing/shared/bom_scenarios/_db_scenarios.py
  - ui/tabs/costing/shared/scenario_comparison_widget.py
  - ui/tabs/costing/product/form/_save_logic.py
  - ui/tabs/costing/product/product_form.py
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


# ──────────────────────────────────────────────────────────
# نماذج البيانات
# ──────────────────────────────────────────────────────────

@dataclass
class ScenarioResult:
    id: int
    item_id: int
    name: str
    is_default: bool
    notes: str = ""

    @classmethod
    def from_row(cls, row) -> "ScenarioResult":
        d = dict(row) if not isinstance(row, dict) else row
        return cls(
            id=d["id"],
            item_id=d["item_id"],
            name=d["name"],
            is_default=bool(d["is_default"]),
            notes=d.get("notes") or "",
        )


@dataclass
class BomRowResult:
    child_type: str
    child_id: int
    qty: float
    waste_pct: float = 0.0
    variant_id: Optional[int] = None
    machine_op_row_id: Optional[int] = None

    @classmethod
    def from_row(cls, row) -> "BomRowResult":
        d = dict(row) if not isinstance(row, dict) else row
        return cls(
            child_type=d["child_type"],
            child_id=d["child_id"],
            qty=float(d["qty"]),
            waste_pct=float(d.get("waste_pct") or 0.0),
            variant_id=d.get("variant_id"),
            machine_op_row_id=d.get("machine_op_row_id"),
        )


# ──────────────────────────────────────────────────────────
# ScenarioService
# ──────────────────────────────────────────────────────────

class ScenarioService:
    """
    Service لإدارة سيناريوهات BOM وحساب تكلفتها.

    الاستخدام:
        svc = ScenarioService(conn)
        scenarios = svc.list(item_id)
        default_id = svc.ensure_default(item_id)
        cost = svc.calc_cost(scenario_id)
    """

    def __init__(self, conn):
        self.conn = conn

    # ── قراءة ─────────────────────────────────────────────

    def list(self, item_id: int) -> List[ScenarioResult]:
        """يرجع كل سيناريوهات المنتج مرتبةً بـ id."""
        from db.costing.bom_scenarios_repo import fetch_scenarios
        return [ScenarioResult.from_row(r) for r in fetch_scenarios(self.conn, item_id)]

    def get(self, scenario_id: int) -> Optional[ScenarioResult]:
        """يرجع سيناريو واحد بالـ id."""
        from db.costing.bom_scenarios_repo import fetch_scenario
        row = fetch_scenario(self.conn, scenario_id)
        return ScenarioResult.from_row(row) if row else None

    def get_default(self, item_id: int) -> Optional[ScenarioResult]:
        """يرجع السيناريو الافتراضي للمنتج، أو None لو مفيش."""
        from db.costing.bom_scenarios_repo import fetch_default_scenario
        row = fetch_default_scenario(self.conn, item_id)
        return ScenarioResult.from_row(row) if row else None

    def get_bom(self, scenario_id: int) -> List[BomRowResult]:
        """يرجع صفوف BOM للسيناريو."""
        from db.costing.bom_scenarios_repo import fetch_bom_for_scenario
        rows = fetch_bom_for_scenario(self.conn, scenario_id)
        return [BomRowResult.from_row(r) for r in (rows or [])]

    # ── كتابة ─────────────────────────────────────────────

    def create(self, item_id: int, name: str, is_default: bool = False) -> int:
        """ينشئ سيناريو جديد ويرجع id."""
        from db.costing.bom_scenarios_repo import insert_scenario
        return insert_scenario(self.conn, item_id, name, is_default=is_default)

    def rename(self, scenario_id: int, name: str) -> None:
        """يعيد تسمية سيناريو."""
        from db.costing.bom_scenarios_repo import update_scenario
        update_scenario(self.conn, scenario_id, name)

    def set_default(self, scenario_id: int) -> None:
        """يجعل السيناريو المحدد افتراضياً."""
        from db.costing.bom_scenarios_repo import set_default_scenario
        set_default_scenario(self.conn, scenario_id)

    def clone(self, scenario_id: int, new_name: str) -> int:
        """ينسخ سيناريو ويرجع id النسخة الجديدة."""
        from db.costing.bom_scenarios_repo import clone_scenario
        return clone_scenario(self.conn, scenario_id, new_name)

    def delete(self, scenario_id: int) -> bool:
        """
        يحذف سيناريو.
        يرجع False لو كان آخر سيناريو للمنتج (لا يُحذف).
        """
        from db.costing.bom_scenarios_repo import delete_scenario
        return delete_scenario(self.conn, scenario_id)

    def replace_bom(self, scenario_id: int, rows: list) -> None:
        """
        يستبدل صفوف BOM للسيناريو.
        rows: list of tuples (child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id)
        """
        from db.costing.bom_scenarios_repo import replace_bom_for_scenario
        replace_bom_for_scenario(self.conn, scenario_id, rows)

    # ── ضمان الوجود ──────────────────────────────────────

    def ensure_default(self, item_id: int) -> int:
        """
        يتأكد من وجود سيناريو default للمنتج.
        لو مفيش → ينشئ واحد باسم "سيناريو 1".
        يرجع id السيناريو الـ default.
        """
        sc = self.get_default(item_id)
        if sc:
            return sc.id
        return self.create(item_id, "سيناريو 1", is_default=True)

    # ── حساب التكلفة ──────────────────────────────────────

    def calc_cost(self, scenario_id: int) -> float:
        """
        يحسب التكلفة الكاملة لسيناريو محدد.

        منقول من ScenarioComparisonWidget._calc_scenario_cost
        ومُنظَّف ليكون في المكان الصحيح (service layer).
        """
        try:
            from db.shared.items_repo import fetch_item
            from models.costing import calc_cost
            from models.costing_base import raw_unit_price, effective_qty
            from models.costing_ops import calc_labor_op_cost, calc_machine_op_cost

            bom_rows = self.get_bom(scenario_id)
            total    = 0.0
            visited: set = set()

            for row in bom_rows:
                child_type = row.child_type
                child_id   = row.child_id
                eff_qty    = effective_qty(row.qty, row.waste_pct)

                if child_type == "raw":
                    child     = fetch_item(self.conn, child_id)
                    unit_cost = raw_unit_price(child) if child else 0.0

                elif child_type == "semi":
                    if child_id not in visited:
                        visited.add(child_id)
                    unit_cost = calc_cost(self.conn, child_id)

                elif child_type == "labor_op":
                    unit_cost = calc_labor_op_cost(self.conn, child_id)

                elif child_type == "machine_op":
                    unit_cost = calc_machine_op_cost(
                        self.conn, child_id,
                        row_id=row.machine_op_row_id,
                    )
                else:
                    unit_cost = 0.0

                total += unit_cost * eff_qty

            return total

        except Exception:
            return 0.0