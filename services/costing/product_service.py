"""
services/costing/product_service.py
=====================================
Business Logic للمنتجات والـ BOM.

الاستخدام:
    from services.costing.product_service import ProductService
    svc = ProductService(conn)
    result = svc.save(product_data, components)

[C-02 / A-03] _save_bom يستخدم replace_bom_for_scenario() من الـ repo
  بدل SQL مباشر. هذا يضمن:
    1. التعامل الصحيح مع كل حالات أعمدة BOM (variant_id, machine_op_row_id)
       سواء أُضيفت عبر migration أم لا.
    2. عدم رمي OperationalError صامت على قواعد بيانات قديمة.
    3. مركزية منطق الـ INSERT في مكان واحد (bom_scenarios_repo).

[C-01] calculate_cost يستخدم calc_product_cost الجديدة التي تدعم scenario_id.

إصلاح اسم الدالة:
  fetch_scenario_bom → fetch_bom_for_scenario (الاسم الصحيح في bom_scenarios_repo)
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
    cleanup_empty_products_after_orphan_fix,
)
from db.costing.bom_scenarios_repo import (
    fetch_scenarios,
    fetch_default_scenario,
    insert_scenario,
    fetch_bom_for_scenario,         # [إصلاح] الاسم الصحيح (كان fetch_scenario_bom خطأ)
    replace_bom_for_scenario,       # [C-02 / A-03] للاستخدام في _save_bom
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
        """
        يحول الـ component لـ tuple بالصيغة التي تتوقعها replace_bom_for_scenario.
        الصيغة: (child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id)
        """
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
    # breakdown: {"raw": float, "labor": float, "machine": float,
    #             "semi": float, "total": float}


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

        components: list[BomComponent] — لازم فيه عنصر واحد على الأقل
        scenario_id: int | None — None = يُحدَّد تلقائياً (default أو جديد)
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
        self._save_bom(scenario_id, components)

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

    def _save_bom(self, scenario_id: int,
                  components: list[BomComponent]) -> None:
        """
        يمسح الـ BOM القديم للسيناريو ويكتب الجديد.

        [C-02 / A-03] يستخدم replace_bom_for_scenario() من bom_scenarios_repo
        بدل SQL مباشر. الـ repo يتعامل مع:
          - وجود/غياب أعمدة variant_id و machine_op_row_id (migration-safe)
          - بناء الـ INSERT الصحيح تلقائياً حسب الأعمدة الموجودة
          - لا خطر من OperationalError على قواعد بيانات قديمة

        الصيغة المتوقعة لكل tuple:
          (child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id)
        """
        rows = [comp.to_tuple() for comp in components]
        replace_bom_for_scenario(self._conn, scenario_id, rows)

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

    def cleanup_empty_products_after_orphan_fix(self,
                                                 product_ids: list[int]) -> list[int]:
        """
        يحذف المنتجات (semi/final) اللي أصبحت بدون أي مكون BOM
        بعد إصلاح الـ orphans، ويرجع قائمة IDs المنتجات المحذوفة.

        [إضافة] غلاف service حول cleanup_empty_products_after_orphan_fix
        من db.shared.items_repo — كان يُستدعى مباشرة من tabs/ (كسر هيكلي).
        """
        return cleanup_empty_products_after_orphan_fix(self._conn, product_ids)

    # ── Cost Calculation ──────────────────────────────────

    def calculate_cost(self, product_id: int,
                       scenario_id: int | None = None) -> CostResult:
        """
        يحسب تكلفة المنتج ويرجع التفاصيل.

        [C-01] يستخدم calc_product_cost الجديدة التي تدعم scenario_id.
        calc_product_cost ترجع (total_cost, breakdown) بـ 4 categories:
          raw, labor, machine, semi, total.
        """
        product = fetch_item(self._conn, product_id)
        if not product:
            raise ValueError(f"المنتج {product_id} غير موجود")

        from models.costing import calc_product_cost
        total, breakdown = calc_product_cost(
            self._conn, product_id, scenario_id
        )

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
                bom_rows = fetch_bom_for_scenario(self._conn, sc["id"])
                new_sc_id = insert_scenario(
                    self._conn, new_id, "سيناريو 1", is_default=True
                )
                # استخدم replace_bom_for_scenario مباشرة مع نفس الصيغة
                rows = [
                    (
                        row["child_type"],
                        row["child_id"],
                        row["qty"],
                        float(row["waste_pct"]) if row["waste_pct"] is not None else 0.0,
                        row["variant_id"]        if "variant_id"        in row.keys() else None,
                        row["machine_op_row_id"] if "machine_op_row_id" in row.keys() else None,
                    )
                    for row in bom_rows
                ]
                replace_bom_for_scenario(self._conn, new_sc_id, rows)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(
                "[ProductService.clone] BOM copy warning for product %d: %s",
                product_id, e
            )

        return new_id

    # ── Delete ────────────────────────────────────────────

    def delete(self, product_id: int) -> None:
        """يحذف المنتج وكل الـ BOM المرتبط به (cascade)."""
        delete_item(self._conn, product_id)