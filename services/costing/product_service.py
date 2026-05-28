"""
services/costing/product_service.py
=====================================
Business Logic للمنتجات والـ BOM.

الاستخدام:
    from services.costing.product_service import ProductService
    svc = ProductService(conn)
    result = svc.save(product_data, components)
"""

from dataclasses import dataclass, field

from db.shared.items_repo import (
    insert_item,
    update_item,
    fetch_item,
    delete_item,
    fetch_bom,
    fetch_orphan_bom_rows,
    delete_orphan_bom_rows,
)
from db.costing.bom_scenarios_repo import (
    fetch_scenarios,
    fetch_default_scenario,
    insert_scenario,
    fetch_scenario_bom,
)


# ══════════════════════════════════════════════════════════
# Dataclasses
# ══════════════════════════════════════════════════════════

@dataclass
class BomComponent:
    child_type        : str
    child_id          : int
    qty               : float
    waste_pct         : float = 0.0
    variant_id        : int | None = None
    machine_op_row_id : int | None = None

    def to_tuple(self) -> tuple:
        return (
            self.child_type,
            self.child_id,
            self.qty,
            self.waste_pct,
            self.variant_id,
            self.machine_op_row_id,
        )


@dataclass
class ProductSaveResult:
    product_id  : int
    scenario_id : int
    is_new      : bool
    bom_count   : int


@dataclass
class OrphanComponent:
    child_type : str
    child_id   : int
    child_name : str | None
    qty        : float
    waste_pct  : float = 0.0


@dataclass
class CostResult:
    product_id   : int
    product_name : str
    total_cost   : float
    breakdown    : dict = field(default_factory=dict)
    # breakdown: {"raw": 120.5, "labor": 30.0, "machine": 45.0}


# ══════════════════════════════════════════════════════════
# ProductService
# ══════════════════════════════════════════════════════════

class ProductService:
    """
    Business Logic للمنتجات (semi / final).
    يدير: إنشاء المنتج + BOM + السيناريوهات + حساب التكلفة.
    """

    def __init__(self, conn):
        self._conn = conn

    # ── Save (Add / Update) ───────────────────────────────

    def save(self, product_data: dict,
             components: list[BomComponent],
             scenario_id: int = None,
             scenario_name: str = "سيناريو 1") -> ProductSaveResult:
        """
        يحفظ المنتج والـ BOM معاً في عملية واحدة.

        product_data: {
            "id": int | None,   ← None = منتج جديد
            "name": str,
            "type": "semi" | "final",
            "price": float,
            "category_id": int | None,
        }
        """
        name = product_data.get("name", "").strip()
        if not name:
            raise ValueError("اسم المنتج مطلوب")
        if not components:
            raise ValueError("المنتج يجب أن يحتوي على مكون واحد على الأقل")

        product_id = product_data.get("id")
        is_new     = product_id is None

        # ── حفظ المنتج نفسه ──
        if is_new:
            product_id = insert_item(
                self._conn,
                name,
                product_data.get("type", "final"),
                product_data.get("price", 0),
                product_data.get("category_id"),
            )
        else:
            update_item(
                self._conn,
                product_id,
                name,
                product_data.get("price", 0),
                product_data.get("category_id"),
            )

        # ── الحصول على السيناريو أو إنشاؤه ──
        scenario_id = self._resolve_scenario(
            product_id, scenario_id, scenario_name, is_new
        )

        # ── حفظ الـ BOM ──
        self._save_bom(product_id, scenario_id, components)

        return ProductSaveResult(
            product_id  = product_id,
            scenario_id = scenario_id,
            is_new      = is_new,
            bom_count   = len(components),
        )

    def _resolve_scenario(self, product_id: int,
                          scenario_id: int | None,
                          scenario_name: str,
                          is_new: bool) -> int:
        """يجيب الـ scenario_id الصح أو ينشئ واحد جديد."""
        if scenario_id is not None:
            return scenario_id

        # جرب يجيب الـ default scenario
        try:
            sc = fetch_default_scenario(self._conn, product_id)
            if sc:
                return sc["id"]
        except Exception:
            pass

        # أنشئ سيناريو جديد
        return insert_scenario(
            self._conn, product_id, scenario_name, is_default=True
        )

    def _save_bom(self, product_id: int,
                  scenario_id: int,
                  components: list[BomComponent]) -> None:
        """يمسح الـ BOM القديم ويكتب الجديد."""
        self._conn.execute(
            "DELETE FROM bom WHERE parent_id=? AND scenario_id=?",
            (product_id, scenario_id)
        )
        for comp in components:
            self._insert_bom_row(product_id, scenario_id, comp)
        self._conn.commit()

    def _insert_bom_row(self, parent_id: int,
                        scenario_id: int,
                        comp: BomComponent) -> None:
        """يضيف صف واحد في الـ BOM."""
        # جيب اسم العنصر
        name = self._resolve_child_name(comp.child_type, comp.child_id)

        self._conn.execute(
            """INSERT INTO bom
               (parent_id, scenario_id, child_type, child_id,
                qty, child_name, waste_pct, variant_id,
                machine_op_row_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                parent_id, scenario_id,
                comp.child_type, comp.child_id,
                comp.qty, name,
                comp.waste_pct,
                comp.variant_id,
                comp.machine_op_row_id,
            )
        )

    def _resolve_child_name(self, child_type: str,
                             child_id: int) -> str | None:
        """يجيب اسم العنصر حسب نوعه."""
        table_map = {
            "raw":        "items",
            "semi":       "items",
            "labor_op":   "labor_ops",
            "machine_op": "machine_ops",
        }
        table = table_map.get(child_type)
        if not table:
            return None
        try:
            row = self._conn.execute(
                f"SELECT name FROM {table} WHERE id=?", (child_id,)
            ).fetchone()
            return row["name"] if row else None
        except Exception:
            return None

    # ── Orphans ───────────────────────────────────────────

    def get_orphan_components(self,
                              product_id: int) -> list[OrphanComponent]:
        """يرجع المكونات اللي عنصرها اتحذف من الـ DB."""
        rows = fetch_orphan_bom_rows(self._conn, product_id)
        return [
            OrphanComponent(
                child_type = r["child_type"],
                child_id   = r["child_id"],
                child_name = r["child_name"],
                qty        = r["qty"],
                waste_pct  = r.get("waste_pct", 0),
            )
            for r in rows
        ]

    def fix_orphans(self, product_id: int) -> int:
        """يحذف المكونات الـ orphan ويرجع عددها."""
        return delete_orphan_bom_rows(self._conn, product_id)

    # ── Cost Calculation ──────────────────────────────────

    def calculate_cost(self, product_id: int,
                       scenario_id: int = None) -> CostResult:
        """يحسب تكلفة المنتج ويرجع التفاصيل."""
        product = fetch_item(self._conn, product_id)
        if not product:
            raise ValueError(f"المنتج {product_id} غير موجود")

        try:
            from models.costing import calc_product_cost
            total, breakdown = calc_product_cost(
                self._conn, product_id, scenario_id
            )
        except Exception:
            total     = 0.0
            breakdown = {}

        return CostResult(
            product_id   = product_id,
            product_name = product["name"],
            total_cost   = total,
            breakdown    = breakdown,
        )

    # ── Clone ─────────────────────────────────────────────

    def clone(self, product_id: int, new_name: str) -> int:
        """
        ينسخ المنتج والـ BOM الخاص بالـ default scenario.
        يرجع ID المنتج الجديد.
        """
        new_name = new_name.strip()
        if not new_name:
            raise ValueError("اسم النسخة مطلوب")

        original = fetch_item(self._conn, product_id)
        if not original:
            raise ValueError(f"المنتج {product_id} غير موجود")

        # أنشئ المنتج الجديد
        new_id = insert_item(
            self._conn,
            new_name,
            original["type"],
            original["price"] or 0,
            original["category_id"],
        )

        # انسخ الـ BOM من الـ default scenario
        try:
            sc = fetch_default_scenario(self._conn, product_id)
            if sc:
                bom_rows = fetch_scenario_bom(self._conn, sc["id"])
                new_sc_id = insert_scenario(
                    self._conn, new_id, "سيناريو 1", is_default=True
                )
                for row in bom_rows:
                    comp = BomComponent(
                        child_type        = row["child_type"],
                        child_id          = row["child_id"],
                        qty               = row["qty"],
                        waste_pct         = row.get("waste_pct", 0),
                        variant_id        = row.get("variant_id"),
                        machine_op_row_id = row.get("machine_op_row_id"),
                    )
                    self._insert_bom_row(new_id, new_sc_id, comp)
                self._conn.commit()
        except Exception as e:
            print(f"[ProductService.clone] BOM copy warning: {e}")

        return new_id

    # ── Delete ────────────────────────────────────────────

    def delete(self, product_id: int) -> None:
        """يحذف المنتج وكل الـ BOM المرتبط به (cascade)."""
        delete_item(self._conn, product_id)