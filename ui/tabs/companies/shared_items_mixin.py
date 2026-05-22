"""
ui/widgets/shared/shared_items_mixin.py
=========================================
Mixin يُضيف دعم العناصر المشتركة لأي panel.

الاستخدام:
    class _TablePanel(QWidget, SharedItemsMixin):
        def _load(self):
            rows = list(fetch_items_by_type(conn, "raw"))
            rows += self.get_shared_rows("raw")   # ← يضيف المشتركة
            self._all_rows = rows
            self._apply_filter()
"""

from db.companies.shared_items_repo import (
    fetch_shared_items_for_company,
    get_item_data,
)
from db.companies.companies_schema import get_central_connection
from db.companies.companies_schema import create_central_tables as _ensure_tables


def _get_central():
    try:
        conn = get_central_connection()
        _ensure_tables(conn)
        return conn
    except Exception:
        return None


def _get_company_id() -> int | None:
    try:
        from db.companies.company_state import company_state
        return company_state.company_id if company_state.is_ready else None
    except Exception:
        return None


# ══════════════════════════════════════════════════════════
# دوال مستقلة — تُستخدم مباشرة في أي panel
# ══════════════════════════════════════════════════════════

def get_shared_raws(company_id: int = None) -> list[dict]:
    """يرجع العناصر المشتركة من نوع 'raw' كـ list of dicts تشبه صفوف items."""
    cid = company_id or _get_company_id()
    if not cid:
        return []
    central = _get_central()
    if not central:
        return []
    try:
        rows = fetch_shared_items_for_company(central, cid, shared_type="raw")
        result = []
        for r in rows:
            d = get_item_data(central, r["id"])
            result.append({
                "id":            f"shared_{r['id']}",   # prefix عشان نميزه
                "shared_id":     r["id"],
                "name":          r["name"],
                "type":          "raw",
                "price":         d.get("price", 0.0),
                "total_qty":     d.get("total_qty"),
                "category_id":   None,
                "category_name": "🔗 مشترك",
                "is_shared":     True,
            })
        return result
    except Exception as e:
        print(f"[shared_mixin] get_shared_raws: {e}")
        return []
    finally:
        central.close()


def get_shared_machines(company_id: int = None) -> list[dict]:
    cid = company_id or _get_company_id()
    if not cid:
        return []
    central = _get_central()
    if not central:
        return []
    try:
        rows = fetch_shared_items_for_company(central, cid, shared_type="machine")
        result = []
        for r in rows:
            d = get_item_data(central, r["id"])
            result.append({
                "id":            f"shared_{r['id']}",
                "shared_id":     r["id"],
                "name":          r["name"],
                "rate_per_hour": d.get("rate_per_hour", 0.0),
                "rate_per_unit": d.get("rate_per_unit", 0.0),
                "category_id":   None,
                "category_name": "🔗 مشترك",
                "is_shared":     True,
            })
        return result
    except Exception as e:
        print(f"[shared_mixin] get_shared_machines: {e}")
        return []
    finally:
        central.close()


def get_shared_labor_ops(company_id: int = None) -> list[dict]:
    cid = company_id or _get_company_id()
    if not cid:
        return []
    central = _get_central()
    if not central:
        return []
    try:
        rows = fetch_shared_items_for_company(central, cid, shared_type="labor_op")
        result = []
        for r in rows:
            d = get_item_data(central, r["id"])
            result.append({
                "id":            f"shared_{r['id']}",
                "shared_id":     r["id"],
                "name":          r["name"],
                "minutes":       d.get("minutes", 0.0),
                "category_id":   None,
                "category_name": "🔗 مشترك",
                "is_shared":     True,
            })
        return result
    except Exception as e:
        print(f"[shared_mixin] get_shared_labor_ops: {e}")
        return []
    finally:
        central.close()


def get_shared_machine_ops(company_id: int = None) -> list[dict]:
    cid = company_id or _get_company_id()
    if not cid:
        return []
    central = _get_central()
    if not central:
        return []
    try:
        rows = fetch_shared_items_for_company(central, cid, shared_type="machine_op")
        result = []
        for r in rows:
            d = get_item_data(central, r["id"])
            result.append({
                "id":            f"shared_{r['id']}",
                "shared_id":     r["id"],
                "name":          r["name"],
                "mode":          d.get("mode", "time"),
                "value":         d.get("value", 0.0),
                "machine_name":  d.get("machine_name", ""),
                "rate_per_hour": 0.0,
                "rate_per_unit": 0.0,
                "category_id":   None,
                "category_name": "🔗 مشترك",
                "is_shared":     True,
            })
        return result
    except Exception as e:
        print(f"[shared_mixin] get_shared_machine_ops: {e}")
        return []
    finally:
        central.close()


def is_shared_id(item_id) -> bool:
    """يتحقق هل الـ id ده خاص بعنصر مشترك."""
    return isinstance(item_id, str) and item_id.startswith("shared_")


def extract_shared_id(item_id) -> int | None:
    """يستخرج الـ shared_id من الـ id المركب."""
    if is_shared_id(item_id):
        try:
            return int(str(item_id).replace("shared_", ""))
        except ValueError:
            return None
    return None


def update_shared_item_data(shared_id: int, name: str, data: dict) -> bool:
    """
    يعدل بيانات عنصر مشترك من أي شركة — يُحدّث المركزي فوراً.
    يرجع True لو نجح.
    """
    central = _get_central()
    if not central:
        return False
    try:
        from db.companies.shared_items_repo import update_shared_item
        update_shared_item(central, shared_id, name, data)
        return True
    except Exception as e:
        print(f"[shared_mixin] update_shared_item_data: {e}")
        return False
    finally:
        central.close()