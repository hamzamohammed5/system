"""
db/shared/shared_items_bridge.py
=================================
جسر العناصر المشتركة — يقرأ من companies.db مباشرة ويدمجها مع erp.db.

إصلاح 6:  _get_erp_conn() يتحقق من is_ready قبل الاستدعاء.
إصلاح 33: استبدال _decode/_encode المحلية بـ decode_json/encode_json من json_utils.
"""

from typing import Optional
from db.shared.json_utils import decode_json, encode_json


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
        from db.companies.companies_schema import get_central_connection
        return get_central_connection()

    def _get_erp_conn(self):
        """
        [إصلاح 6] يتحقق من is_ready قبل الاستدعاء.
        """
        from db.companies.company_state import company_state
        if not company_state.is_ready:
            raise RuntimeError(
                "SharedItemsBridge: لا توجد شركة نشطة — اختر شركة أولاً."
            )
        return company_state.get_erp_conn()

    # ══════════════════════════════════════════════════════
    # جلب العناصر المشتركة من companies.db
    # ══════════════════════════════════════════════════════

    def fetch_shared_items_for_type(self, shared_type: str,
                                     _conn=None) -> list:
        owned = _conn is None
        conn  = _conn or self._get_central_conn()
        try:
            rows = conn.execute("""
                SELECT s.id, s.name, s.shared_type, s.data, s.updated_at
                FROM company_shared_links lnk
                JOIN shared_items s ON s.id = lnk.shared_item_id
                WHERE lnk.company_id = ? AND s.shared_type = ?
                ORDER BY s.name
            """, (self.company_id, shared_type)).fetchall()

            result = []
            for row in rows:
                # [إصلاح 33] decode_json بدل _decode المحلية
                d    = decode_json(row["data"])
                item = self._row_to_item(row, d, shared_type)
                result.append(item)
            return result
        except Exception as e:
            print(f"[SharedItemsBridge] fetch_shared_items_for_type error: {e}")
            return []
        finally:
            if owned:
                conn.close()

    def _row_to_item(self, row, data: dict, shared_type: str) -> dict:
        base = {
            "id":             f"shared:{row['id']}",
            "shared_item_id": row["id"],
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
        from db.shared.items_repo import fetch_items_by_type
        erp = self._get_erp_conn()
        local_items = [dict(r) for r in fetch_items_by_type(erp, item_type)]
        shared_items = self.fetch_shared_items_for_type(item_type)
        return local_items + shared_items

    def fetch_all_with_shared(self, item_type: str) -> list:
        return self.fetch_items_by_type_with_shared(item_type)

    # ══════════════════════════════════════════════════════
    # جلب عنصر مشترك واحد
    # ══════════════════════════════════════════════════════

    def fetch_shared_item_as_row(self, shared_item_id: int,
                                  shared_type: str = None,
                                  _conn=None) -> Optional[dict]:
        owned = _conn is None
        conn  = _conn or self._get_central_conn()
        try:
            row = conn.execute(
                "SELECT id, name, shared_type, data, updated_at "
                "FROM shared_items WHERE id=?",
                (shared_item_id,)
            ).fetchone()
            if not row:
                return None
            # [إصلاح 33] decode_json بدل _decode المحلية
            d = decode_json(row["data"])
            return self._row_to_item(row, d, shared_type or row["shared_type"])
        except Exception:
            return None
        finally:
            if owned:
                conn.close()

    # ══════════════════════════════════════════════════════
    # تحديث عنصر مشترك
    # ══════════════════════════════════════════════════════

    def update_shared_item(self, shared_item_id: int, name: str, data: dict,
                            _conn=None):
        owned = _conn is None
        conn  = _conn or self._get_central_conn()
        try:
            # [إصلاح 33] encode_json بدل _encode المحلية
            conn.execute(
                "UPDATE shared_items SET name=?, data=?, updated_at=datetime('now') WHERE id=?",
                (name, encode_json(data), shared_item_id)
            )
            conn.commit()
        finally:
            if owned:
                conn.close()

    # ══════════════════════════════════════════════════════
    # ربط / فك ربط
    # ══════════════════════════════════════════════════════

    def link_shared_item(self, shared_item_id: int, _conn=None):
        owned = _conn is None
        conn  = _conn or self._get_central_conn()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO company_shared_links (shared_item_id, company_id) VALUES (?, ?)",
                (shared_item_id, self.company_id)
            )
            conn.commit()
        finally:
            if owned:
                conn.close()

    def unlink_shared_item(self, shared_item_id: int, _conn=None):
        owned = _conn is None
        conn  = _conn or self._get_central_conn()
        try:
            conn.execute(
                "DELETE FROM company_shared_links WHERE shared_item_id=? AND company_id=?",
                (shared_item_id, self.company_id)
            )
            conn.commit()
        finally:
            if owned:
                conn.close()

    def is_linked(self, shared_item_id: int, _conn=None) -> bool:
        owned = _conn is None
        conn  = _conn or self._get_central_conn()
        try:
            row = conn.execute(
                "SELECT 1 FROM company_shared_links WHERE shared_item_id=? AND company_id=?",
                (shared_item_id, self.company_id)
            ).fetchone()
            return row is not None
        except Exception:
            return False
        finally:
            if owned:
                conn.close()

    # ══════════════════════════════════════════════════════
    # عمليات batch
    # ══════════════════════════════════════════════════════

    def batch_link(self, shared_item_ids: list[int]):
        conn = self._get_central_conn()
        try:
            for sid in shared_item_ids:
                conn.execute(
                    "INSERT OR IGNORE INTO company_shared_links "
                    "(shared_item_id, company_id) VALUES (?, ?)",
                    (sid, self.company_id)
                )
            conn.commit()
        finally:
            conn.close()

    def batch_unlink(self, shared_item_ids: list[int]):
        conn = self._get_central_conn()
        try:
            for sid in shared_item_ids:
                conn.execute(
                    "DELETE FROM company_shared_links "
                    "WHERE shared_item_id=? AND company_id=?",
                    (sid, self.company_id)
                )
            conn.commit()
        finally:
            conn.close()

    # ══════════════════════════════════════════════════════
    # حساب تكلفة عنصر مشترك
    # ══════════════════════════════════════════════════════

    def calc_shared_raw_unit_price(self, shared_item_id: int,
                                    _conn=None) -> float:
        item = self.fetch_shared_item_as_row(shared_item_id, "raw", _conn=_conn)
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
    try:
        from db.companies.company_state import company_state
        if not company_state.is_ready:
            return None
        return SharedItemsBridge(company_state.company_id)
    except Exception:
        return None


def is_shared_id(item_id) -> bool:
    return isinstance(item_id, str) and item_id.startswith("shared:")


def extract_shared_id(item_id) -> Optional[int]:
    if is_shared_id(item_id):
        try:
            return int(item_id.split(":")[1])
        except Exception:
            return None
    return None