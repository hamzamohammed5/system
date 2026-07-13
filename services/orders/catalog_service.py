"""
services/orders/catalog_service.py
=====================================
CatalogService — طبقة الخدمة لكتالوج المنتجات المسعّرة والعروض.

يغطي:
  - المنتجات المسعّرة (final/semi) مع تصنيفاتها
  - العروض وبنودها

مبدأ العزل المعماري:
  - هذا الملف هو الوحيد المسموح له باستدعاء db.costing.catalog_repo.
  - [مضاف حديثاً] كان المنطق (SQL + فتح اتصال) موجوداً مباشرة داخل
    ui/tabs/orders/order_form/_products_fetcher.py — نُقل بالكامل
    هنا. الاتصال (conn) لم يعد يُفتح ضمنياً داخل الدالة، بل يُمرَّر
    للـ constructor بنفس نمط باقي الـ services في المشروع
    (مثل CustomerService(conn)):
        from services.costing.catalog_service import CatalogService
        svc = CatalogService(erp_conn)
        products = svc.get_priced_products()

  - [مضاف حديثاً] الـ caching الذي كان class-level على
    ui.tabs.orders.order_form._item_row_widget._ItemRowWidget
    (_products_cache) نُقل بالكامل لهذا الملف. الـ cache الآن على
    مستوى instance من CatalogService، لأن الـ service (وليس الـ UI)
    هو من يعرف متى تنتهي صلاحية البيانات المخزَّنة.

هذا الـ service هو نقطة الدخول الوحيدة لطبقة الـ UI لكل ما يخص
كتالوج المنتجات المسعّرة والعروض:
    from services.costing.catalog_service import CatalogService
    svc = CatalogService(erp_conn)
"""
from __future__ import annotations

import logging
from typing import Optional

from db.orders.catalog_repo import (
    fetch_priced_products, fetch_offers, fetch_offer_lines,
)

logger = logging.getLogger(__name__)


class CatalogService:
    """
    طبقة خدمة كتالوج المنتجات — نقطة الدخول الوحيدة لطبقة الـ UI.

    المعاملات:
        conn : اتصال قاعدة بيانات erp (نفس القاعدة التي تحوي
               items/pricing/categories/offers)
    """

    def __init__(self, conn):
        self.conn = conn
        self._products_cache: Optional[list] = None
        self._offers_cache: Optional[list] = None

    # ────────────────────────────────────────────────────
    # المنتجات المسعّرة
    # ────────────────────────────────────────────────────

    def get_priced_products(self, force_refresh: bool = False) -> list:
        """
        يرجع المنتجات المسعّرة (final/semi) مع تصنيفاتها.

        [مضاف حديثاً] الـ caching نُقل هنا من _ItemRowWidget
        (كان class-level cache على الـ widget نفسه).
        force_refresh=True يتجاوز الكاش ويعيد الجلب من DB.
        """
        if self._products_cache is None or force_refresh:
            self._products_cache = fetch_priced_products(self.conn)
        return self._products_cache

    def invalidate_products_cache(self) -> None:
        """
        [مضاف حديثاً] يقابل الدالة القديمة
        _ItemRowWidget.invalidate_cache() — تُستدعى بعد أي تعديل
        على المنتجات/الأسعار في مكان آخر من التطبيق حتى لا يعمل
        الـ UI ببيانات قديمة.
        """
        self._products_cache = None

    # ────────────────────────────────────────────────────
    # العروض
    # ────────────────────────────────────────────────────

    def get_offers(self, force_refresh: bool = False) -> list:
        if self._offers_cache is None or force_refresh:
            self._offers_cache = fetch_offers(self.conn)
        return self._offers_cache

    def get_offer_lines(self, offer_id: int) -> list:
        """بنود عرض معيّن — لا تُخزَّن مؤقتاً لأنها تُطلب لكل عرض بمعرفه."""
        return fetch_offer_lines(self.conn, offer_id)

    def invalidate_offers_cache(self) -> None:
        self._offers_cache = None
