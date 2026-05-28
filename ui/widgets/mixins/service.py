"""
ui/widgets/mixins/service.py
=====================================
ServiceMixin — Lazy-loaded services للـ widgets.

المشكلة: كل widget تستدعي الـ service مباشرة في كل method:
    ItemService(self.conn).add(...)
    CategoryService(self.conn).list_by_type(...)
لو تغير constructor الـ service، تعديلات في كل مكان.

الحل: properties كسولة تقرأ self.conn تلقائياً.
الـ service يُنشأ عند الاستدعاء الأول فقط — لا overhead لو لم يُستخدم.

الاستخدام:
    class MyPanel(BaseListPanel, ServiceMixin):
        def _load_rows(self):
            return [vars(r) for r in self._item_service.list_by_type("raw")]

        def _on_add(self, data):
            new_id = self._item_service.add(data["name"], data["price"], "raw")

ملاحظة:
    الـ service instances ليست cached — يُنشأ instance جديد في كل وصول.
    هذا مقصود: الـ conn ممكن يتغير (تغيير الشركة)، والـ service خفيف الوزن.
"""


class ServiceMixin:
    """
    Mixin يوفر lazy-loaded services للـ widgets.

    يفترض: self.conn موجود ويشير لـ DB connection صالح.
    """

    # ── Item Service ──────────────────────────────────────

    @property
    def _item_service(self):
        """Service للعناصر (خامات، نصف مصنع، منتجات)."""
        from services.shared.item_service import ItemService
        return ItemService(self.conn)

    # ── Category Service ──────────────────────────────────

    @property
    def _category_service(self):
        """Service للتصنيفات."""
        from services.shared.category_service import CategoryService
        return CategoryService(self.conn)

    # ── Product Service ───────────────────────────────────

    @property
    def _product_service(self):
        """Service للمنتجات والـ BOM."""
        from services.costing.product_service import ProductService
        return ProductService(self.conn)

    # ── Order Service ─────────────────────────────────────

    @property
    def _order_service(self):
        """Service للطلبات والعملاء."""
        from services.orders.order_service import OrderService
        return OrderService(self.conn)

    # ── Journal Service ───────────────────────────────────

    @property
    def _journal_service(self):
        """Service للقيود المحاسبية."""
        from services.accounting.journal_service import JournalService
        return JournalService(self.conn)