"""
services/costing/catalog_service.py
======================================
CatalogService — يبني الـ catalog الكامل المستخدم في ComponentRow.

يبني الـ catalog المستخدم في ComponentRow ويدمج العناصر المحلية
مع المشتركة (عبر services.companies.CompanyService و SharedItemsService).

[قرار هيكلي 1] db.shared و db.costing يُستوردان مباشرة وبدون
try/except. db.shared طبقة بيانات مشتركة مصممة عمداً ليستخدمها كل
domain (items تُستخدم في costing/inventory/orders) — هذا ليس كسراً
هيكلياً، بعكس استيراد service من ui/ (كان الخطأ في bulk_replace
قبل الإصلاح). أي خطأ في db.shared أو db.costing هنا هو خطأ برمجي
يجب أن يظهر لا أن يُبلع بصمت.

[قرار هيكلي 2] الاعتماد على services.companies متعمد أيضاً:
  - العناصر المشتركة بين الشركات مصدرها central db، ومنطق الوصول
    له (company_id النشط، caching، إلخ) موجود بالفعل في
    services/companies. تكراره هنا يعني ازدواجية منطق خطيرة.
  - البديل الوحيد الأنظف هو استدعاء db.companies مباشرة من هنا،
    وهذا أسوأ لأنه يكسر عزل company_state عن باقي الدومينز.
  - لذلك: service → service عبر domain boundary مقبول هنا، بشرط
    أن يكون الاعتماد صريحاً (imports واضحة، لا SQL مباشر لـ db آخر).

[i18n] هذا الملف لا يحتوي على أي نص عرض مباشر. بدل النص، الـ
service يرجع مفتاحاً رمزياً ثابتاً SHARED_CATEGORY_KEY = "shared"
في مكان category_name للعناصر المشتركة. طبقة الـ ui (مثل
_catalog_provider.py) هي المسؤولة عن استدعاء tr("shared") وتحويل
المفتاح لنص معروض — الـ service لا يجب أن يعرف شيئاً عن نظام
الترجمة أو النصوص المعروضة.

يُستخدم من:
  - ui/tabs/costing/product/_catalog_provider.py

الـ catalog شكله:
  {
    "raw":        [(id, name, category_name, price, total_qty), ...],
    "semi":       [(id, name, category_name, price, None), ...],
    "final":      [(id, name, category_name, price, None), ...],
    "labor_op":   [(id, name, category_name, minutes), ...],
    "machine_op": [(id, name, category_name, mode, machine_name), ...],
  }

  category_name للعناصر المشتركة = SHARED_CATEGORY_KEY ("shared")
  وليس نصاً عربياً جاهزاً — راجع الـ ui لترجمته عبر tr().
"""

from __future__ import annotations
from typing import Dict, List, Any

from db.shared.items_repo import fetch_items_by_type
from db.costing.operations_repo import fetch_all_labor_ops, fetch_all_machine_ops

# [i18n] مفتاح رمزي فقط — ليس نصاً معروضاً. الـ ui يترجمه عبر tr("shared").
SHARED_CATEGORY_KEY = "shared"


class CatalogService:
    """
    Service لبناء الـ catalog الكامل للـ ComponentRow.

    يدمج العناصر المحلية مع المشتركة لكل نوع، عبر CompanyService
    و SharedItemsService (بدل التواصل المباشر مع db.companies).

    الاستخدام:
        svc = CatalogService(conn)
        catalog = svc.build()
    """

    def __init__(self, conn):
        self.conn = conn

    # ── API رئيسي ─────────────────────────────────────────

    def build(self) -> Dict[str, List]:
        """يبني الـ catalog الكامل لكل الأنواع."""
        return {
            "raw":        self.build_raw(),
            "semi":       self.build_semi(),
            "final":      self.build_final(),
            "labor_op":   self.build_labor_ops(),
            "machine_op": self.build_machine_ops(),
        }

    def build_raw(self) -> List:
        """خامات محلية + مشتركة."""
        local = [
            (r["id"], r["name"], r.get("category_name") or "",
             r["price"], r.get("total_qty"))
            for r in fetch_items_by_type(self.conn, "raw")
        ]
        shared = [
            (item["id"], item["name"], SHARED_CATEGORY_KEY,
             float(item.get("price", 0.0)), item.get("total_qty"))
            for item in self._fetch_shared("raw")
        ]
        return local + shared

    def build_semi(self) -> List:
        """نصف مصنع محلي فقط."""
        return [
            (r["id"], r["name"], r.get("category_name") or "", 0.0, None)
            for r in fetch_items_by_type(self.conn, "semi")
        ]

    def build_final(self) -> List:
        """منتج نهائي محلي فقط."""
        return [
            (r["id"], r["name"], r.get("category_name") or "", 0.0, None)
            for r in fetch_items_by_type(self.conn, "final")
        ]

    def build_labor_ops(self) -> List:
        """عمليات عمالة محلية + مشتركة."""
        local = [
            (r["id"], r["name"], r.get("category_name") or "",
             r.get("minutes", 0.0))
            for r in fetch_all_labor_ops(self.conn)
        ]

        shared = [
            (item["id"], item["name"], SHARED_CATEGORY_KEY,
             float(item.get("minutes", 0.0)))
            for item in self._fetch_shared("labor_op")
        ]
        return local + shared

    def build_machine_ops(self) -> List:
        """عمليات تشغيل محلية + مشتركة."""
        local = [
            (r["id"], r["name"], r.get("category_name") or "",
             r.get("mode", "time"), r.get("machine_name", ""))
            for r in fetch_all_machine_ops(self.conn)
        ]

        shared = [
            (item["id"], item["name"], SHARED_CATEGORY_KEY,
             item.get("mode", "time"), item.get("machine_name", ""))
            for item in self._fetch_shared("machine_op")
        ]
        return local + shared

    # ── مساعد جلب المشترك ─────────────────────────────────

    def _fetch_shared(self, shared_type: str) -> List[dict]:
        """
        يجيب العناصر المشتركة للشركة النشطة عبر CompanyService
        و SharedItemsService — بدون لمس db.companies مباشرة.

        يرجع list of dicts مع id = "shared:{n}" (نفس شكل الإخراج السابق).

        ملاحظة: الـ try/except هنا مقصود ومختلف عن استيرادات db.costing
        أعلى الملف — هذه الدالة تعبر إلى domain آخر (companies) قد لا
        يكون جاهزاً بعد (لا توجد شركة نشطة، central db غير مهيأ، ...)،
        وهي حالة تشغيل طبيعية وليست خطأ برمجي يجب إخفاؤه.
        """
        try:
            from services.companies.company_service import CompanyService
            if not CompanyService.is_company_ready():
                return []
            company_id = CompanyService.get_current_company_id()
            if company_id is None:
                return []

            from services.companies.shared_items_service import SharedItemsService
            conn = CompanyService.get_central_conn_and_init()
            svc  = SharedItemsService(conn)

            items = svc.list_for_company(company_id, shared_type)

            result = []
            for it in items:
                item = {"id": f"shared:{it.id}", "name": it.name}
                item.update(it.data or {})
                result.append(item)
            return result

        except Exception as e:
            import sys
            print(f"[CatalogService] _fetch_shared({shared_type}) error: {e}",
                  file=sys.stderr)
            return []