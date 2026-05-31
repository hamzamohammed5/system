"""
services/shared/category_service.py
======================================
CategoryService — منطق التصنيفات.

[إصلاح هيكلة] إضافة methods جديدة لدعم استبدال db imports المباشرة في الـ widgets:
  - get_all(scope)          → list[dict]    بدل fetch_all_categories
  - get_one(cat_id)         → dict | None   بدل fetch_category
  - get_descendants(cat_id) → set[int]      بدل fetch_descendants
  - count_items(cat_id)     → dict          بدل count_category_items
  - build_tree(rows)        → list[dict]    بدل build_tree من repo (static)

الـ widgets تستخدم هذه المethods بدل الاستيراد المباشر من db/shared/categories_repo.
المسار الصحيح: widget → CategoryService → categories_repo (db/)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Set


@dataclass
class DeletePreview:
    """معاينة تأثير حذف تصنيف."""
    cat_id      : int
    cat_name    : str
    children    : list = field(default_factory=list)
    item_counts : dict = field(default_factory=dict)

    def warning_text(self) -> str:
        lines = []
        if self.children:
            lines.append(f"سيتم حذف {len(self.children)} تصنيف فرعي")
        if self.item_counts:
            total = sum(self.item_counts.values())
            lines.append(f"مرتبط بـ {total} عنصر")
        return "\n".join(lines)


class CategoryService:
    """
    Service لإدارة التصنيفات.

    الاستخدام:
        svc = CategoryService(conn)
        rows = svc.get_all("raw")
        tree = svc.build_tree(rows)
        cat  = svc.get_one(cat_id)
        svc.add("اسم", "raw", "#607d8b", parent_id)
        svc.update(cat_id, "اسم جديد", "raw", "#607d8b", parent_id)
        svc.delete_cascade(cat_id)
    """

    def __init__(self, conn):
        self._conn = conn

    # ══════════════════════════════════════════════════════
    # قراءة
    # ══════════════════════════════════════════════════════

    def get_all(self, scope: str = "all") -> List[dict]:
        """
        [إضافة] يرجع كل التصنيفات لـ scope محدد.
        يحل محل استدعاء fetch_all_categories مباشرة من الـ widgets.
        """
        from db.shared.categories_repo import fetch_all_categories
        return fetch_all_categories(self._conn, scope)

    def get_one(self, cat_id: int) -> "dict | None":
        """
        [إضافة] يرجع تصنيف واحد بالـ id.
        يحل محل استدعاء fetch_category مباشرة من الـ widgets.
        """
        from db.shared.categories_repo import fetch_category
        return fetch_category(self._conn, cat_id)

    def get_descendants(self, cat_id: int) -> Set[int]:
        """
        [إضافة] يرجع set بـ IDs كل الأبناء والأحفاد.
        يحل محل استدعاء fetch_descendants مباشرة من الـ widgets.
        """
        from db.shared.categories_repo import fetch_descendants
        return set(fetch_descendants(self._conn, cat_id))

    def count_items(self, cat_id: int) -> dict:
        """
        [إضافة] يرجع dict بعدد العناصر المرتبطة بالتصنيف لكل نوع.
        يحل محل استدعاء count_category_items مباشرة من الـ widgets.
        """
        from db.shared.categories_repo import count_category_items
        return count_category_items(self._conn, cat_id)

    @staticmethod
    def build_tree(rows: list) -> List[dict]:
        """
        [إضافة] يبني شجرة هرمية من قائمة التصنيفات المسطحة.
        يحل محل استدعاء build_tree من repo مباشرة في الـ widgets.
        static method — لا تحتاج conn.
        """
        from db.shared.categories_repo import build_tree
        return build_tree(rows)

    # ══════════════════════════════════════════════════════
    # كتابة
    # ══════════════════════════════════════════════════════

    def add(self, name: str, scope: str, color: str = "#607d8b",
            parent_id: int = None) -> int:
        """
        يضيف تصنيف جديد.
        Raises: ValueError لو الاسم فارغ أو مكرر.
        """
        name = (name or "").strip()
        if not name:
            raise ValueError("اسم التصنيف مطلوب")

        from db.shared.categories_repo import insert_category
        return insert_category(self._conn, name, scope, color, parent_id)

    def update(self, cat_id: int, name: str, scope: str,
               color: str = "#607d8b", parent_id: int = None) -> None:
        """
        يُحدِّث تصنيف موجود.
        Raises: ValueError لو الاسم فارغ.
        """
        name = (name or "").strip()
        if not name:
            raise ValueError("اسم التصنيف مطلوب")

        from db.shared.categories_repo import update_category
        update_category(self._conn, cat_id, name, scope, color, parent_id)

    def delete_cascade(self, cat_id: int) -> None:
        """يحذف التصنيف وكل أبنائه cascade."""
        from db.shared.categories_repo import delete_category
        delete_category(self._conn, cat_id)

    def get_delete_preview(self, cat_id: int) -> "DeletePreview | None":
        """
        يرجع معاينة تأثير حذف تصنيف.
        يرجع None لو التصنيف غير موجود.
        """
        cat = self.get_one(cat_id)
        if not cat:
            return None

        children    = list(self.get_descendants(cat_id))
        item_counts = self.count_items(cat_id)

        return DeletePreview(
            cat_id      = cat_id,
            cat_name    = cat["name"],
            children    = children,
            item_counts = item_counts,
        )