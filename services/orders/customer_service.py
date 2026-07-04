"""
services/orders/customer_service.py
=====================================
CustomerService — طبقة الخدمة لعملاء نظام الطلبات (customers).

يغطي:
  - قراءة عميل واحد / كل العملاء
  - إحصائيات العميل (عدد الطلبات، القيمة الإجمالية، إلخ)
  - جهات اتصال العميل
  - تفعيل/تعطيل العميل
  - حذف عميل
  - طلبات عميل معيّن (facade على OrderService — دومين مختلف)

مبدأ العزل المعماري:
  - هذا الملف هو الوحيد المسموح له باستدعاء db.orders.customers_repo
    من أجل قراءة/تعديل بيانات العميل نفسه.
  - إنشاء/تعديل العميل (add_customer/update_customer) موجودان بالفعل
    في services.orders.order_service.OrderService — لم يُكرَّرا هنا
    تجنباً لتشتت منطق الكتابة بين ملفين؛ هذا الملف يوفرهما كـ
    pass-through لراحة الاستخدام من نفس الواجهة.
  - طلبات العميل (fetch_customer_orders) تنتمي لدومين الطلبات
    (db.orders.orders_repo) لا دومين العملاء — تُغطى هنا بدالة facade
    فقط لتجنّب استدعاء db.orders.orders_repo مباشرة من UI؛ المنطق
    الفعلي يبقى في orders_repo.

هذا الـ service هو نقطة الدخول الوحيدة لطبقة الـ UI لكل ما يخص
عملاء نظام الطلبات:
    from services.orders.customer_service import CustomerService
    svc = CustomerService(conn)
"""
from __future__ import annotations

import logging
from typing import Optional

from db.orders.customers_repo import (
    fetch_customer, fetch_all_customers,
    delete_customer, toggle_customer_active,
    fetch_customer_stats, fetch_contacts,
)
from db.orders.orders_repo import fetch_customer_orders

logger = logging.getLogger(__name__)


class CustomerService:
    """
    طبقة خدمة عملاء الطلبات — نقطة الدخول الوحيدة لطبقة الـ UI.

    المعاملات:
        conn : اتصال قاعدة بيانات الطلبات (نفس قاعدة الشركة)
    """

    def __init__(self, conn):
        self.conn = conn

    # ────────────────────────────────────────────────────
    # قراءة
    # ────────────────────────────────────────────────────

    def get_customer(self, customer_id: int) -> Optional[dict]:
        return fetch_customer(self.conn, customer_id)

    def list_customers(self) -> list:
        return fetch_all_customers(self.conn)

    def get_stats(self, customer_id: int) -> dict:
        return fetch_customer_stats(self.conn, customer_id)

    def list_contacts(self, customer_id: int) -> list:
        return fetch_contacts(self.conn, customer_id)

    # ────────────────────────────────────────────────────
    # كتابة
    # ────────────────────────────────────────────────────

    def delete(self, customer_id: int) -> bool:
        return delete_customer(self.conn, customer_id)

    def toggle_active(self, customer_id: int) -> None:
        toggle_customer_active(self.conn, customer_id)

    # ────────────────────────────────────────────────────
    # تكامل مع دومين الطلبات (facade)
    # ────────────────────────────────────────────────────

    def list_orders(self, customer_id: int) -> list:
        """
        طلبات عميل معيّن — تُجلب من db.orders.orders_repo وليس
        customers_repo (دومين مختلف). موجودة هنا كـ facade فقط
        لتوفير نقطة دخول واحدة من UI بدل استدعاء orders_repo مباشرة.
        """
        return fetch_customer_orders(self.conn, customer_id)
