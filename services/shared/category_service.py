"""
services/shared/category_service.py
=====================================
Business Logic للتصنيفات — مفصولة عن الـ UI والـ DB.

الاستخدام:
    from services.shared.category_service import CategoryService
    svc = CategoryService(conn)
    preview = svc.get_delete_preview(cat_id)
    svc.delete_cascade(cat_id)
"""

from dataclasses import dataclass, field

from db.shared.categories_repo import (
    fetch_category,
    fetch_descendants,
    fetch_all_categories,
    insert_category,
    update_category,
    delete_category,
    count_category_items,
    build_tree,
)


# ══════════════════════════════════════════════════════════
# Dataclasses
# ══════════════════════════════════════════════════════════

@dataclass
class DeletePreview:
    cat_name    : str
    child_count : int
    item_counts : dict = field(default_factory=dict)  # {"عناصر": 3, "ماكينات": 1}

    @property
    def item_count(self) -> int:
        return sum(self.item_counts.values())

    def warning_text(self) -> str:
        lines = []
        if self.child_count:
            lines.append(
                f"⚠️ يحتوي على {self.child_count} تصنيف فرعي — سيتم حذفها جميعاً."
            )
        if self.item_count:
            details = "، ".join(f"{v} {k}" for k, v in self.item_counts.items() if v)
            lines.append(f"⚠️ {details} ستفقد تصنيفها.")
        return "\n".join(lines)


@dataclass
class CategoryNode:
    id        : int
    name      : str
    color     : str
    scope     : str
    parent_id : int | None
    children  : list["CategoryNode"] = field(default_factory=list)


# ══════════════════════════════════════════════════════════
# CategoryService
# ══════════════════════════════════════════════════════════

class CategoryService:
    """
    Business Logic للتصنيفات.
    الـ conn بيتحدد عند إنشاء الـ instance.
    """

    def __init__(self, conn):
        self._conn = conn

    # ── Read ──────────────────────────────────────────────

    def get_tree(self, scope: str = None) -> list[CategoryNode]:
        """يرجع شجرة التصنيفات كـ dataclasses."""
        rows = fetch_all_categories(self._conn, scope)
        raw_tree = build_tree(rows)
        return [self._to_node(n) for n in raw_tree]

    def _to_node(self, raw: dict) -> CategoryNode:
        return CategoryNode(
            id        = raw["id"],
            name      = raw["name"],
            color     = raw["color"],
            scope     = raw["scope"],
            parent_id = raw["parent_id"],
            children  = [self._to_node(c) for c in raw.get("children", [])],
        )

    # ── Write ─────────────────────────────────────────────

    def add(self, name: str, scope: str, color: str,
            parent_id: int = None) -> int:
        """يضيف تصنيف جديد ويرجع الـ ID."""
        name = name.strip()
        if not name:
            raise ValueError("اسم التصنيف مطلوب")
        return insert_category(self._conn, name, scope, color, parent_id)

    def update(self, cat_id: int, name: str, scope: str,
               color: str, parent_id: int = None) -> None:
        """يحدث بيانات التصنيف."""
        name = name.strip()
        if not name:
            raise ValueError("اسم التصنيف مطلوب")
        # update_category في الـ repo بيتحقق من circular reference
        update_category(self._conn, cat_id, name, scope, color, parent_id)

    # ── Delete ────────────────────────────────────────────

    def get_delete_preview(self, cat_id: int) -> DeletePreview | None:
        """يرجع معلومات الحذف قبل التنفيذ، أو None لو التصنيف مش موجود."""
        cat = fetch_category(self._conn, cat_id)
        if not cat:
            return None

        descendants = fetch_descendants(self._conn, cat_id)
        child_count = len(descendants) - 1  # بنطرح التصنيف نفسه
        item_counts = count_category_items(self._conn, cat_id)

        return DeletePreview(
            cat_name    = cat["name"],
            child_count = child_count,
            item_counts = item_counts,
        )

    def delete_cascade(self, cat_id: int) -> int:
        """
        يحذف التصنيف وكل أبنائه.
        يرجع عدد التصنيفات المحذوفة.
        """
        descendants = fetch_descendants(self._conn, cat_id)
        for did in sorted(descendants, reverse=True):
            delete_category(self._conn, did)
        return len(descendants)