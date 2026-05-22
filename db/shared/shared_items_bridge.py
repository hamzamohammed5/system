"""
db/shared/shared_items_bridge.py
=================================
جسر العناصر المشتركة — يقرأ من companies.db مباشرة ويدمجها مع erp.db.

المبدأ:
  - العناصر المشتركة مخزنة في companies.db (shared_items + company_shared_links)
  - الشركة تقرأ بياناتها مباشرة من companies.db — مفيش نسخ محلية
  - أي تعديل على shared_item يتعكس فوراً على كل الشركات المشتركة فيه
  - العناصر المشتركة تظهر مع أيقونة 🔗 وbadge "مشترك"

الاستخدام:
  from db.shared.shared_items_bridge import SharedItemsBridge
  bridge = SharedItemsBridge(company_id)
  all_raws = bridge.fetch_items_by_type_with_shared("raw")
"""

import json
from typing import Optional


# ══════════════════════════════════════════════════════════
# مساعدات JSON
# ══════════════════════════════════════════════════════════

def _decode(data_str: str) -> dict:
    try:
        return json.loads(data_str) if data_str else {}
    except Exception:
        return {}


def _encode(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False)


# ══════════════════════════════════════════════════════════
# SharedItemsBridge
# ══════════════════════════════════════════════════════════

class SharedItemsBridge:
    """
    يوفر واجهة موحدة لجلب العناصر (محلية + مشتركة).
    يقرأ العناصر المشتركة من companies.db مباشرة.
    """

    SHARED_CATEGORY_NAME = "🔗 مشترك"
    SHARED_ICON = "🔗"

    def __init__(self, company_id: int):
        self.company_id = company_id

    def _get_central_conn(self):
        """يفتح connection لـ companies.db."""
        from db.companies.companies_schema import get_central_connection
        return get_central_connection()

    def _get_erp_conn(self):
        """يرجع erp connection للشركة الحالية."""
        from db.companies.company_state import company_state
        return company_state.get_erp_conn()

    # ══════════════════════════════════════════════════════
    # جلب العناصر المشتركة من companies.db
    # ══════════════════════════════════════════════════════

    def fetch_shared_items_for_type(self, shared_type: str) -> list:
        """
        يجيب العناصر المشتركة التي الشركة الحالية مشتركة فيها.
        كل عنصر يرجع كـ dict يشبه صف items لسهولة الاستخدام.
        """
        try:
            central = self._get_central_conn()
            rows = central.execute("""
                SELECT s.id, s.name, s.shared_type, s.data, s.updated_at
                FROM company_shared_links lnk
                JOIN shared_items s ON s.id = lnk.shared_item_id
                WHERE lnk.company_id = ? AND s.shared_type = ?
                ORDER BY s.name
            """, (self.company_id, shared_type)).fetchall()
            central.close()

            result = []
            for row in rows:
                d = _decode(row["data"])
                item = self._row_to_item(row, d, shared_type)
                result.append(item)
            return result
        except Exception as e:
            print(f"[SharedItemsBridge] fetch_shared_items_for_type error: {e}")
            return []

    def _row_to_item(self, row, data: dict, shared_type: str) -> dict:
        """يحول صف shared_items إلى dict يشبه صف items."""
        base = {
            "id":             f"shared:{row['id']}",   # ID مركب لتمييزه
            "shared_item_id": row["id"],               # الـ ID الحقيقي في companies.db
            "name":           row["name"],
            "type":           shared_type,
            "category_id":    None,
            "category_name":  self.SHARED_CATEGORY_NAME,
            "is_shared":      True,
            "updated_at":     row["updated_at"],
        }
        if shared_type == "raw":
            base["price"]     = float(data.get("price", 0.0))
            base["total_qty"] = data.get("total_qty")
        elif shared_type == "machine":
            base["rate_per_hour"] = float(data.get("rate_per_hour", 0.0))
            base["rate_per_unit"] = float(data.get("rate_per_unit", 0.0))
        elif shared_type == "labor_op":
            base["minutes"] = float(data.get("minutes", 0.0))
        elif shared_type == "machine_op":
            base["mode"]          = data.get("mode", "time")
            base["value"]         = float(data.get("value", 0.0))
            base["machine_name"]  = data.get("machine_name", "")
            base["rate_per_hour"] = float(data.get("rate_per_hour", 0.0))
            base["rate_per_unit"] = float(data.get("rate_per_unit", 0.0))
        return base

    # ══════════════════════════════════════════════════════
    # دمج المحلي مع المشترك
    # ══════════════════════════════════════════════════════

    def fetch_items_by_type_with_shared(self, item_type: str) -> list:
        """
        يجيب عناصر النوع المطلوب (محلية + مشتركة).
        العناصر المشتركة تأتي في آخر القائمة تحت تصنيف "🔗 مشترك".
        """
        from db.shared.items_repo import fetch_items_by_type
        erp = self._get_erp_conn()
        local_items = [dict(r) for r in fetch_items_by_type(erp, item_type)]

        shared_items = self.fetch_shared_items_for_type(item_type)

        return local_items + shared_items

    def fetch_all_with_shared(self, item_type: str) -> list:
        """نفس fetch_items_by_type_with_shared — alias."""
        return self.fetch_items_by_type_with_shared(item_type)

    # ══════════════════════════════════════════════════════
    # جلب عنصر مشترك واحد
    # ══════════════════════════════════════════════════════

    def fetch_shared_item_as_row(self, shared_item_id: int,
                                  shared_type: str = None) -> Optional[dict]:
        """يجيب عنصر مشترك واحد كـ dict."""
        try:
            central = self._get_central_conn()
            row = central.execute(
                "SELECT id, name, shared_type, data, updated_at "
                "FROM shared_items WHERE id=?",
                (shared_item_id,)
            ).fetchone()
            central.close()
            if not row:
                return None
            d = _decode(row["data"])
            return self._row_to_item(row, d, shared_type or row["shared_type"])
        except Exception:
            return None

    # ══════════════════════════════════════════════════════
    # تحديث عنصر مشترك (يتعكس على كل الشركات فوراً)
    # ══════════════════════════════════════════════════════

    def update_shared_item(self, shared_item_id: int, name: str, data: dict):
        """
        يحدث بيانات عنصر مشترك في companies.db.
        التحديث يتعكس فوراً على كل الشركات لأنها تقرأ من companies.db مباشرة.
        """
        try:
            central = self._get_central_conn()
            central.execute(
                "UPDATE shared_items SET name=?, data=?, updated_at=datetime('now') WHERE id=?",
                (name, _encode(data), shared_item_id)
            )
            central.close()
        except Exception as e:
            print(f"[SharedItemsBridge] update_shared_item error: {e}")
            raise

    # ══════════════════════════════════════════════════════
    # ربط / فك ربط
    # ══════════════════════════════════════════════════════

    def link_shared_item(self, shared_item_id: int):
        """يربط عنصر مشترك بالشركة الحالية."""
        try:
            central = self._get_central_conn()
            central.execute(
                "INSERT OR IGNORE INTO company_shared_links (shared_item_id, company_id) VALUES (?, ?)",
                (shared_item_id, self.company_id)
            )
            central.close()
        except Exception as e:
            print(f"[SharedItemsBridge] link error: {e}")
            raise

    def unlink_shared_item(self, shared_item_id: int):
        """يفك ربط عنصر مشترك من الشركة الحالية."""
        try:
            central = self._get_central_conn()
            central.execute(
                "DELETE FROM company_shared_links WHERE shared_item_id=? AND company_id=?",
                (shared_item_id, self.company_id)
            )
            central.close()
        except Exception as e:
            print(f"[SharedItemsBridge] unlink error: {e}")
            raise

    def is_linked(self, shared_item_id: int) -> bool:
        """هل الشركة الحالية مشتركة في هذا العنصر؟"""
        try:
            central = self._get_central_conn()
            row = central.execute(
                "SELECT 1 FROM company_shared_links WHERE shared_item_id=? AND company_id=?",
                (shared_item_id, self.company_id)
            ).fetchone()
            central.close()
            return row is not None
        except Exception:
            return False

    # ══════════════════════════════════════════════════════
    # حساب تكلفة عنصر مشترك
    # ══════════════════════════════════════════════════════

    def calc_shared_raw_unit_price(self, shared_item_id: int) -> float:
        """يحسب سعر وحدة الخامة المشتركة."""
        item = self.fetch_shared_item_as_row(shared_item_id, "raw")
        if not item:
            return 0.0
        price     = float(item.get("price", 0.0))
        total_qty = item.get("total_qty")
        if total_qty and float(total_qty) > 0:
            return price / float(total_qty)
        return price


# ══════════════════════════════════════════════════════════
# Singleton helper
# ══════════════════════════════════════════════════════════

def get_bridge() -> Optional[SharedItemsBridge]:
    """يرجع bridge للشركة النشطة حالياً."""
    try:
        from db.companies.company_state import company_state
        if not company_state.is_ready:
            return None
        return SharedItemsBridge(company_state.company_id)
    except Exception:
        return None


def is_shared_id(item_id) -> bool:
    """هل الـ id ده لعنصر مشترك؟"""
    return isinstance(item_id, str) and item_id.startswith("shared:")


def extract_shared_id(item_id) -> Optional[int]:
    """يستخرج الـ shared_item_id من الـ composite id."""
    if is_shared_id(item_id):
        try:
            return int(item_id.split(":")[1])
        except Exception:
            return None
    return None