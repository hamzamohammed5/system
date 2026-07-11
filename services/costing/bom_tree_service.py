"""
services/costing/bom_tree_service.py
======================================
BomTreeService — يغلّف كل منطق جلب بيانات BOM Tree.

ينقل من bom_tree.py:
  - _fetch_all_scenarios
  - _fetch_bom_with_row_id_by_scenario  (مع PRAGMA SQL المعقد)
  - _get_sub_bom_for_item
  - _get_scenario_id_for_item
  - منطق الحذف

يُستخدم من:
  - ui/tabs/costing/shared/bom_tree.py
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Callable


# ──────────────────────────────────────────────────────────
# نماذج البيانات
# ──────────────────────────────────────────────────────────

@dataclass
class ScenarioInfo:
    id: int
    item_id: int
    name: str
    is_default: bool

    @classmethod
    def from_row(cls, row) -> "ScenarioInfo":
        d = dict(row) if not isinstance(row, dict) else row
        return cls(
            id=d["id"],
            item_id=d["item_id"],
            name=d["name"],
            is_default=bool(d["is_default"]),
        )


@dataclass
class BomComponentRow:
    """صف BOM واحد — يمثل مكوناً في السيناريو."""
    child_type: str
    child_id: int
    qty: float
    waste_pct: float = 0.0
    variant_id: Optional[int] = None
    machine_op_row_id: Optional[int] = None

    @classmethod
    def from_dict(cls, d: dict) -> "BomComponentRow":
        return cls(
            child_type=d["child_type"],
            child_id=d["child_id"],
            qty=float(d["qty"]),
            waste_pct=float(d.get("waste_pct") or 0.0),
            variant_id=d.get("variant_id"),
            machine_op_row_id=d.get("machine_op_row_id"),
        )


@dataclass
class NodeData:
    """
    بيانات مكوّن BOM اللازمة لبناء node في الشجرة.
    تُبنى داخل BomTreeService.get_node_data — الـ UI لا يستدعي
    db/ أو models/ مباشرة، فقط يستهلك هذا الـ dataclass.
    """
    name: str
    unit_cost: float
    op_row_label: Optional[str] = None


# ──────────────────────────────────────────────────────────
# BomTreeService
# ──────────────────────────────────────────────────────────

class BomTreeService:
    """
    Service لجلب بيانات BOM Tree بكل أشكالها.

    يحل محل الـ SQL المباشر في bom_tree.py ويوحّد منطق
    الـ PRAGMA-based column detection في مكان واحد.

    الاستخدام:
        svc = BomTreeService(conn)
        scenarios = svc.get_scenarios(item_id)
        bom = svc.get_bom_for_scenario(scenario_id)
        sub = svc.get_sub_bom(item_id)
    """

    def __init__(self, conn):
        self.conn = conn
        self._bom_cols: Optional[set] = None  # cache للأعمدة

    # ── قراءة ─────────────────────────────────────────────

    def get_scenarios(self, item_id: int) -> List[ScenarioInfo]:
        """يرجع كل سيناريوهات المنتج مرتبةً بـ id."""
        try:
            rows = self.conn.execute(
                "SELECT id, item_id, name, is_default "
                "FROM bom_scenarios WHERE item_id=? ORDER BY id",
                (item_id,)
            ).fetchall()
            return [ScenarioInfo.from_row(r) for r in rows]
        except Exception:
            return []

    def get_bom_for_scenario(self, scenario_id: int) -> List[BomComponentRow]:
        """
        يرجع صفوف BOM للسيناريو المحدد.

        يتعامل تلقائياً مع الـ schemas المختلفة (مع/بدون waste_pct,
        variant_id, machine_op_row_id) باستخدام PRAGMA مرة واحدة
        ثم يخزّن النتيجة في cache.
        """
        try:
            cols = self._get_bom_columns()
            has_row_id  = "machine_op_row_id" in cols
            has_variant = "variant_id" in cols
            has_waste   = "waste_pct" in cols

            if has_row_id and has_variant and has_waste:
                sql = (
                    "SELECT child_type, child_id, qty, "
                    "COALESCE(waste_pct,0) as waste_pct, "
                    "variant_id, machine_op_row_id "
                    "FROM bom WHERE scenario_id=? ORDER BY id"
                )
            elif has_row_id and has_waste:
                sql = (
                    "SELECT child_type, child_id, qty, "
                    "COALESCE(waste_pct,0) as waste_pct, "
                    "NULL as variant_id, machine_op_row_id "
                    "FROM bom WHERE scenario_id=? ORDER BY id"
                )
            elif has_waste:
                sql = (
                    "SELECT child_type, child_id, qty, "
                    "COALESCE(waste_pct,0) as waste_pct, "
                    "NULL as variant_id, NULL as machine_op_row_id "
                    "FROM bom WHERE scenario_id=? ORDER BY id"
                )
            else:
                sql = (
                    "SELECT child_type, child_id, qty, "
                    "0 as waste_pct, "
                    "NULL as variant_id, NULL as machine_op_row_id "
                    "FROM bom WHERE scenario_id=? ORDER BY id"
                )

            rows = self.conn.execute(sql, (scenario_id,)).fetchall()
            if rows:
                return [BomComponentRow.from_dict(dict(r)) for r in rows]

        except Exception:
            pass

        # fallback — BOM بدون scenario_id (النظام القديم)
        return self._fallback_bom(scenario_id)

    def get_sub_bom(self, item_id: int) -> List[BomComponentRow]:
        """
        يرجع BOM الفرعي للنصف مصنع
        (يستخدم الـ default scenario أو أول سيناريو).
        """
        sc_id = self._get_default_scenario_id(item_id)
        if sc_id is not None:
            return self.get_bom_for_scenario(sc_id)
        return []

    def get_default_scenario_id(self, item_id: int) -> Optional[int]:
        """يرجع id الـ default scenario للمنتج."""
        return self._get_default_scenario_id(item_id)

    def get_node_data(self, child_type: str, child_id: int,
                      machine_op_row_id: Optional[int] = None) -> Optional["NodeData"]:
        """
        يجيب بيانات المكوّن (name + unit_cost) اللازمة لبناء node في الشجرة.

        [إصلاح هيكلي] انتقل من bom_tree.py (_fetch_node_data) — كان يستدعي
        db.shared.items_repo و db.costing.operations_repo و models/* مباشرة
        من tabs/، متجاوزاً services/. الاستدعاءات نفسها (نفس التوقيعات)
        نُقلت هنا بدون تغيير في المنطق.
        """
        try:
            if child_type == "raw":
                from db.shared.items_repo import fetch_item
                from models.costing_base  import raw_unit_price
                row = fetch_item(self.conn, child_id)
                if not row:
                    return None
                return NodeData(
                    name=row["name"],
                    unit_cost=raw_unit_price(row),
                )

            elif child_type == "semi":
                from db.shared.items_repo import fetch_item
                from models.costing       import calc_cost
                row = fetch_item(self.conn, child_id)
                if not row:
                    return None
                return NodeData(
                    name=row["name"],
                    unit_cost=calc_cost(self.conn, child_id),
                )

            elif child_type == "labor_op":
                from db.costing.operations_repo import fetch_labor_op
                from models.costing_ops         import calc_labor_op_cost
                op = fetch_labor_op(self.conn, child_id)
                if not op:
                    return None
                return NodeData(
                    name=op["name"],
                    unit_cost=calc_labor_op_cost(self.conn, child_id),
                )

            elif child_type == "machine_op":
                from db.costing.operations_repo import fetch_machine_op
                from models.costing_ops         import calc_machine_op_cost
                op = fetch_machine_op(self.conn, child_id)
                if not op:
                    return None
                op_row_label = None
                if machine_op_row_id is not None:
                    try:
                        row_info = self.conn.execute(
                            "SELECT label FROM machine_op_rows WHERE id=?",
                            (machine_op_row_id,)
                        ).fetchone()
                        if row_info and row_info["label"]:
                            op_row_label = row_info["label"]
                    except Exception:
                        pass
                return NodeData(
                    name=op["name"],
                    unit_cost=calc_machine_op_cost(
                        self.conn, child_id, row_id=machine_op_row_id
                    ),
                    op_row_label=op_row_label,
                )

        except Exception:
            return None

        return None

    # ── حذف ───────────────────────────────────────────────

    def delete_component(self, scenario_id: int, child_type: str,
                         child_id: int) -> None:
        """يحذف مكوناً من سيناريو محدد."""
        self.conn.execute(
            "DELETE FROM bom WHERE scenario_id=? AND child_type=? AND child_id=?",
            (scenario_id, child_type, child_id),
        )
        self.conn.commit()

    def delete_bom_row(self, parent_id: int, child_type: str,
                       child_id: int) -> None:
        """يحذف مكوناً من BOM الرئيسي (بدون سيناريوهات)."""
        from db.shared.items_repo import delete_bom_row
        delete_bom_row(self.conn, parent_id, child_type, child_id)

    # ── مساعدات داخلية ────────────────────────────────────

    def _get_bom_columns(self) -> set:
        """
        يجيب أعمدة جدول bom — مع cache لتجنب تكرار PRAGMA.
        يُصفَّر الـ cache عند إعادة إنشاء الـ service.
        """
        if self._bom_cols is None:
            try:
                rows = self.conn.execute(
                    "PRAGMA table_info(bom)"
                ).fetchall()
                self._bom_cols = {r["name"] for r in rows}
            except Exception:
                self._bom_cols = set()
        return self._bom_cols

    def invalidate_columns_cache(self) -> None:
        """يُصفَّر cache الأعمدة — يُستدعى بعد migration."""
        self._bom_cols = None

    def _get_default_scenario_id(self, item_id: int) -> Optional[int]:
        """يرجع id الـ default scenario أو أول سيناريو."""
        try:
            sc = self.conn.execute(
                "SELECT id FROM bom_scenarios "
                "WHERE item_id=? AND is_default=1 LIMIT 1",
                (item_id,)
            ).fetchone()
            if not sc:
                sc = self.conn.execute(
                    "SELECT id FROM bom_scenarios "
                    "WHERE item_id=? ORDER BY id LIMIT 1",
                    (item_id,)
                ).fetchone()
            return sc["id"] if sc else None
        except Exception:
            return None

    def _fallback_bom(self, scenario_id: int) -> List[BomComponentRow]:
        """
        Fallback للـ BOM القديم بدون scenario_id.
        يُستخدم فقط لو الـ query الأساسية فشلت أو ما رجعت نتائج.
        """
        try:
            # محاولة جلب parent_id من السيناريو
            sc = self.conn.execute(
                "SELECT item_id FROM bom_scenarios WHERE id=? LIMIT 1",
                (scenario_id,)
            ).fetchone()
            if not sc:
                return []

            from db.shared.items_repo import fetch_bom
            old_rows = fetch_bom(self.conn, sc["item_id"])
            result = []
            for r in old_rows:
                if isinstance(r, tuple):
                    result.append(BomComponentRow(
                        child_type=r[0], child_id=r[1],
                        qty=r[2], waste_pct=float(r[3]) if len(r) > 3 else 0.0,
                    ))
                else:
                    result.append(BomComponentRow(
                        child_type=r["child_type"],
                        child_id=r["child_id"],
                        qty=float(r["qty"]),
                        waste_pct=float(r["waste_pct"]) if "waste_pct" in r.keys() else 0.0,
                    ))
            return result
        except Exception:
            return []