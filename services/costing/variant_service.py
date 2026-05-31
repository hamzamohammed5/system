"""
services/costing/variant_service.py
======================================
VariantService — يغلّف كل عمليات raw_variants_repo.

يُستخدم من:
  - ui/tabs/costing/shared/raw_variants_panel.py
  - ui/widgets/components/component_row/variants.py

الدوال المضافة (مطلوبة من variants.py):
  - get_variants_for_item(conn, item_id) → list
  - get_variant_unit_cost(conn, variant_id, item_id) → float | None
  - get_item_price(conn, item_id) → float
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List


# ──────────────────────────────────────────────────────────
# نماذج البيانات
# ──────────────────────────────────────────────────────────

@dataclass
class VariantResult:
    id: int
    item_id: int
    name: str
    pieces: float
    notes: str = ""

    @classmethod
    def from_row(cls, row) -> "VariantResult":
        d = dict(row) if not isinstance(row, dict) else row
        return cls(
            id=d["id"],
            item_id=d["item_id"],
            name=d["name"],
            pieces=float(d["pieces"]),
            notes=d.get("notes") or "",
        )

    def calc_unit_cost(self, item_price: float) -> float:
        """سعر الوحدة = السعر الكلي ÷ عدد القطع."""
        if self.pieces > 0 and item_price > 0:
            return item_price / self.pieces
        return item_price


# ──────────────────────────────────────────────────────────
# دوال مساعدة مستقلة (تُستخدم من variants.py مباشرة)
# ──────────────────────────────────────────────────────────

def get_variants_for_item(conn, item_id: int) -> list:
    """
    يرجع كل variants الخامة كـ list of dicts.
    مطلوبة من component_row/variants.py.
    """
    try:
        from db.costing.raw_variants_repo import fetch_variants_for_item
        rows = fetch_variants_for_item(conn, item_id)
        return [dict(r) for r in rows] if rows else []
    except Exception:
        return []


def get_variant_unit_cost(conn, variant_id: int,
                           item_id: int) -> "float | None":
    """
    يحسب سعر الوحدة للـ variant = item_price ÷ pieces.
    مطلوبة من component_row/variants.py.
    """
    try:
        from db.costing.raw_variants_repo import fetch_variant
        var = fetch_variant(conn, variant_id)
        if not var:
            return None
        pieces = float(var["pieces"])
        if pieces <= 0:
            return None
        price = get_item_price(conn, item_id)
        if price <= 0:
            return None
        return price / pieces
    except Exception:
        return None


def get_item_price(conn, item_id: int) -> float:
    """
    يجلب سعر الخامة من جدول items.
    مطلوبة من component_row/variants.py.
    """
    try:
        row = conn.execute(
            "SELECT price FROM items WHERE id=?", (item_id,)
        ).fetchone()
        return float(row["price"]) if row and row["price"] else 0.0
    except Exception:
        return 0.0


# ──────────────────────────────────────────────────────────
# VariantService
# ──────────────────────────────────────────────────────────

class VariantService:
    """
    Service لإدارة variants الخامة (صفوف الإنتاج).

    الاستخدام:
        svc = VariantService(conn)
        variants = svc.list(item_id)
        svc.add(item_id, "رول 50 متر", pieces=50)
    """

    def __init__(self, conn):
        self.conn = conn

    # ── قراءة ─────────────────────────────────────────────

    def list(self, item_id: int) -> List[VariantResult]:
        """يرجع كل variants الخامة."""
        from db.costing.raw_variants_repo import fetch_variants_for_item
        return [VariantResult.from_row(r) for r in fetch_variants_for_item(self.conn, item_id)]

    def get(self, variant_id: int) -> Optional[VariantResult]:
        """يرجع variant واحد بالـ id."""
        from db.costing.raw_variants_repo import fetch_variant
        row = fetch_variant(self.conn, variant_id)
        return VariantResult.from_row(row) if row else None

    # ── كتابة ─────────────────────────────────────────────

    def add(self, item_id: int, name: str, pieces: float,
            notes: str = None) -> int:
        """
        يضيف variant جديد.
        يرجع id الـ variant الجديد.
        Raises: ValueError لو name فارغ أو pieces <= 0
        """
        name = (name or "").strip()
        if not name:
            raise ValueError("اسم الـ variant مطلوب")
        if pieces <= 0:
            raise ValueError("عدد القطع يجب أن يكون أكبر من صفر")

        from db.costing.raw_variants_repo import insert_variant
        return insert_variant(self.conn, item_id, name, pieces, notes=notes)

    def update(self, variant_id: int, name: str, pieces: float,
               notes: str = None) -> None:
        """
        يحدّث variant موجود.
        Raises: ValueError لو name فارغ أو pieces <= 0
        """
        name = (name or "").strip()
        if not name:
            raise ValueError("اسم الـ variant مطلوب")
        if pieces <= 0:
            raise ValueError("عدد القطع يجب أن يكون أكبر من صفر")

        from db.costing.raw_variants_repo import update_variant
        update_variant(self.conn, variant_id, name, pieces, notes=notes)

    def delete(self, variant_id: int) -> None:
        """يحذف variant."""
        from db.costing.raw_variants_repo import delete_variant
        delete_variant(self.conn, variant_id)

    # ── حساب ──────────────────────────────────────────────

    def calc_unit_cost(self, variant_id: int, item_price: float) -> float:
        """
        يحسب سعر الوحدة للـ variant.
        = item_price ÷ pieces
        """
        v = self.get(variant_id)
        if not v:
            return item_price
        return v.calc_unit_cost(item_price)