"""
services/shared/item_service.py
=================================
Business Logic للعناصر (خامات، نصف مصنع، منتجات نهائية).

الاستخدام:
    from services.shared.item_service import ItemService
    svc = ItemService(conn)
    new_id = svc.add("قماش", price=50.0, item_type="raw")

التغييرات:
  - [تحسين 18] get_usage_count يشمل كل child_types في BOM.
    القديم: يبحث فقط في ('raw','semi') ويُهمل labor_op و machine_op.
    الجديد: يبحث في كل الأنواع ('raw','semi','labor_op','machine_op')
    لأن العنصر قد يكون مستخدماً كـ operation في BOM أيضاً.
"""

from dataclasses import dataclass, field

from db.shared.items_repo import (
    fetch_item,
    fetch_items_by_type,
    insert_item,
    update_item,
    delete_item,
)


# ══════════════════════════════════════════════════════════
# Dataclasses
# ══════════════════════════════════════════════════════════

@dataclass
class ItemValidationError:
    field   : str
    message : str


@dataclass
class ItemResult:
    id          : int
    name        : str
    price       : float
    item_type   : str
    category_id : int | None
    total_qty   : float | None


@dataclass
class DeletePreview:
    item_name  : str
    usage_count: int          # عدد الـ BOM rows اللي بتستخدمه

    def can_delete(self) -> bool:
        return self.usage_count == 0

    def warning_text(self) -> str:
        if self.usage_count:
            return (
                f"⚠️ «{self.item_name}» مستخدم في {self.usage_count} "
                f"منتج — حذفه سيؤثر على حسابات التكلفة."
            )
        return ""


# ══════════════════════════════════════════════════════════
# ItemService
# ══════════════════════════════════════════════════════════

class ItemService:
    """
    Business Logic للعناصر.
    يدعم: raw / semi / final / labor / machine
    """

    def __init__(self, conn):
        self._conn = conn

    # ── Validation ────────────────────────────────────────

    def validate(self, name: str,
                 price: float) -> list[ItemValidationError]:
        errors = []
        if not name.strip():
            errors.append(ItemValidationError("name", "الاسم مطلوب"))
        if price < 0:
            errors.append(ItemValidationError("price", "السعر لا يكون سالباً"))
        return errors

    # ── Read ──────────────────────────────────────────────

    def get(self, item_id: int) -> ItemResult | None:
        row = fetch_item(self._conn, item_id)
        if not row:
            return None
        return self._to_result(row)

    def list_by_type(self, item_type: str) -> list[ItemResult]:
        rows = fetch_items_by_type(self._conn, item_type)
        return [self._to_result(r) for r in rows]

    def _to_result(self, row) -> ItemResult:
        return ItemResult(
            id          = row["id"],
            name        = row["name"],
            price       = float(row["price"] or 0),
            item_type   = row["type"],
            category_id = row["category_id"],
            total_qty   = row["total_qty"],
        )

    # ── Write ─────────────────────────────────────────────

    def add(self, name: str, price: float,
            item_type: str,
            category_id: int = None,
            total_qty: float = None) -> int:
        """يضيف عنصر جديد ويرجع الـ ID."""
        errors = self.validate(name, price)
        if errors:
            raise ValueError(errors[0].message)
        return insert_item(
            self._conn, name.strip(), item_type,
            price, category_id, total_qty
        )

    def update(self, item_id: int, name: str,
               price: float,
               category_id: int = None,
               total_qty: float = None) -> None:
        """يحدث بيانات العنصر."""
        errors = self.validate(name, price)
        if errors:
            raise ValueError(errors[0].message)
        update_item(
            self._conn, item_id, name.strip(),
            price, category_id, total_qty
        )

    # ── Delete ────────────────────────────────────────────

    def get_delete_preview(self,
                           item_id: int) -> DeletePreview | None:
        """يرجع معلومات الحذف قبل التنفيذ."""
        row = fetch_item(self._conn, item_id)
        if not row:
            return None
        return DeletePreview(
            item_name   = row["name"],
            usage_count = self.get_usage_count(item_id),
        )

    def get_usage_count(self, item_id: int) -> int:
        """
        كام منتج بيستخدم العنصر ده في الـ BOM.

        [تحسين 18] يشمل الآن كل child_types:
          - raw        : خامة
          - semi       : نصف مصنع
          - labor_op   : عملية عمالة
          - machine_op : عملية تشغيل

        القديم كان يبحث فقط في ('raw','semi') مما يُهمل
        استخدام العنصر كـ operation ويُعطي عدد ناقص.
        """
        try:
            row = self._conn.execute(
                "SELECT COUNT(DISTINCT parent_id) AS cnt "
                "FROM bom WHERE child_id=? "
                "AND child_type IN ('raw','semi','labor_op','machine_op')",
                (item_id,)
            ).fetchone()
            return row["cnt"] if row else 0
        except Exception:
            return 0

    def delete(self, item_id: int) -> bool:
        """
        يحذف العنصر.
        يرجع True لو نجح، False لو مستخدم في BOM.
        """
        preview = self.get_delete_preview(item_id)
        if not preview or not preview.can_delete():
            return False
        delete_item(self._conn, item_id)
        return True

    def force_delete(self, item_id: int) -> None:
        """يحذف العنصر حتى لو مستخدم في BOM — للحالات الاستثنائية."""
        delete_item(self._conn, item_id)