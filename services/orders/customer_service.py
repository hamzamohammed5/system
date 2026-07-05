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
    من أجل قراءة/تعديل/إنشاء بيانات العميل نفسه.
  - [تعديل هيكلي] add_customer/update_customer نُقلا فعلياً إلى هذا
    الملف (لم يعودا pass-through على OrderService). كانت النسخة
    القديمة تعتمد على أن يذهب أي مستخدم لـ CustomerService لإنشاء
    عميل جديد إلى OrderService بدلاً منه، رغم أن CustomerService
    يدّعي أنه "نقطة الدخول الوحيدة" — تناقض تم حله بجعل هذا الملف
    المالك الحصري لعمليات الكتابة الخاصة بالعميل، بينما OrderService
    أصبح يستدعي CustomerService (composition) بدل تكرار المنطق.
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
    insert_customer, update_customer,
    insert_contact as _insert_contact,
    update_contact as _update_contact,
    delete_contact as _delete_contact,
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

    def add(self, name: str,
           customer_type: str = "individual",
           phone: str = "",
           phone2: str = "",
           email: str = "",
           address: str = "",
           city: str = "",
           notes: str = "") -> int:
        """
        [مضاف] إنشاء عميل جديد.
        نُقلت هنا من OrderService.add_customer — هذا الملف هو
        المالك الحصري لعمليات الكتابة الخاصة بالعميل الآن.
        """
        name = name.strip()
        if not name:
            raise ValueError("اسم العميل مطلوب")
        return insert_customer(
            self.conn,
            name=name, customer_type=customer_type,
            phone=phone.strip(), phone2=phone2.strip(),
            email=email.strip(), address=address.strip(),
            city=city.strip(), notes=notes.strip(),
        )

    def update(self, customer_id: int,
              name: str,
              customer_type: str = "individual",
              phone: str = "",
              phone2: str = "",
              email: str = "",
              address: str = "",
              city: str = "",
              notes: str = "",
              is_active: int = 1) -> None:
        """
        [مضاف] تعديل بيانات عميل موجود.
        نُقلت هنا من OrderService.update_customer لنفس السبب أعلاه.
        """
        name = name.strip()
        if not name:
            raise ValueError("اسم العميل مطلوب")
        update_customer(
            self.conn, customer_id,
            name=name, customer_type=customer_type,
            phone=phone.strip(), phone2=phone2.strip(),
            email=email.strip(), address=address.strip(),
            city=city.strip(), notes=notes.strip(),
            is_active=is_active,
        )

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

    # ────────────────────────────────────────────────────
    # جهات الاتصال — كتابة
    # ────────────────────────────────────────────────────

    def add_contact(self, customer_id: int,
                    name: str,
                    role: str = "",
                    phone: str = "",
                    email: str = "",
                    notes: str = "") -> int:
        """
        [مضاف] إضافة جهة اتصال لعميل موجود.

        كانت insert_contact موجودة فعلاً في db.orders.customers_repo
        لكن بدون غلاف في CustomerService، مما اضطر _customer_form.py
        لتعطيل حفظ جهات الاتصال بالكامل (انظر التعليق القديم هناك)
        التزاماً بمبدأ الطبقات وعدم استدعاء الـ repo مباشرة من UI.
        """
        name = name.strip()
        if not name:
            raise ValueError("اسم جهة الاتصال مطلوب")
        return _insert_contact(
            self.conn, customer_id,
            name=name, role=role.strip(), phone=phone.strip(),
            email=email.strip(), notes=notes.strip(),
        )

    def update_contact(self, contact_id: int,
                       name: str,
                       role: str = "",
                       phone: str = "",
                       email: str = "",
                       notes: str = "") -> None:
        """[مضاف] تعديل جهة اتصال موجودة."""
        name = name.strip()
        if not name:
            raise ValueError("اسم جهة الاتصال مطلوب")
        _update_contact(
            self.conn, contact_id,
            name=name, role=role.strip(), phone=phone.strip(),
            email=email.strip(), notes=notes.strip(),
        )

    def delete_contact(self, contact_id: int) -> None:
        """[مضاف] حذف جهة اتصال."""
        _delete_contact(self.conn, contact_id)
