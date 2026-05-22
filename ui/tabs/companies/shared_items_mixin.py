"""
ui/widgets/shared/shared_items_mixin.py
=========================================
Mixin يُضيف دعم العناصر المشتركة لأي panel.
"""

import json


def _row_to_dict(row) -> dict:
    """يحول sqlite3.Row أو dict لـ dict آمن."""
    if row is None:
        return {}
    if isinstance(row, dict):
        return row
    try:
        return dict(row)
    except Exception:
        return {}


def _get_central():
    try:
        from db.companies.companies_schema import get_central_connection, create_central_tables
        conn = get_central_connection()
        create_central_tables(conn)
        return conn
    except Exception:
        return None


def _get_company_id():
    try:
        from db.companies.company_state import company_state
        return company_state.company_id if company_state.is_ready else None
    except Exception:
        return None


def _decode_data(data_str) -> dict:
    """يفك تشفير عمود data لو JSON، أو يرجع dict فاضي."""
    if not data_str:
        return {}
    if isinstance(data_str, dict):
        return data_str
    try:
        return json.loads(data_str)
    except Exception:
        return {}


def _get_item_data_safe(central, row_id: int) -> dict:
    """
    يجيب بيانات عنصر مشترك بأمان —
    يتعامل مع كلا الجدولين:
      • companies_schema.shared_items  (بدون عمود data)
      • shared_items_repo.shared_items (بعمود data)
    """
    # محاولة جلب عمود data لو موجود
    try:
        r = central.execute(
            "SELECT data FROM shared_items WHERE id=?", (row_id,)
        ).fetchone()
        if r:
            return _decode_data(r["data"])
    except Exception:
        pass

    # fallback: جدول companies_schema بدون data — نبني من الأعمدة المتاحة
    try:
        r = central.execute(
            "SELECT * FROM shared_items WHERE id=?", (row_id,)
        ).fetchone()
        if r:
            d = _row_to_dict(r)
            # shared_items_repo يخزن البيانات في data (JSON)
            # companies_schema يخزنها مباشرة في source_item_id
            # نرجع dict يحاكي ما يحتاجه كل نوع
            return d
    except Exception:
        pass

    return {}


def _fetch_shared_for_company(central, company_id: int, shared_type: str) -> list:
    """
    يجيب العناصر المشتركة لشركة معينة — يتعامل مع كلا الـ schema.
    يرجع list of dicts.
    """
    rows = []

    # أولاً: حاول shared_items_repo (عمود data موجود)
    try:
        from db.companies.shared_items_repo import fetch_shared_items_for_company
        raw_rows = fetch_shared_items_for_company(central, company_id,
                                                   shared_type=shared_type)
        for r in raw_rows:
            d = _row_to_dict(r)
            data = _decode_data(d.get("data", "{}"))
            d["_data"] = data
            rows.append(d)
        return rows
    except Exception:
        pass

    # ثانياً: fallback على companies_repo
    try:
        from db.companies.companies_repo import fetch_shared_items_for_company as _fetch
        raw_rows = _fetch(central, company_id)
        for r in raw_rows:
            d = _row_to_dict(r)
            if d.get("shared_type") == shared_type:
                d["_data"] = {}
                rows.append(d)
        return rows
    except Exception:
        pass

    return []


# ══════════════════════════════════════════════════════════
# دوال مستقلة — تُستخدم مباشرة في أي panel
# ══════════════════════════════════════════════════════════

def get_shared_raws(company_id: int = None) -> list:
    cid = company_id or _get_company_id()
    if not cid:
        return []
    central = _get_central()
    if not central:
        return []
    try:
        rows = _fetch_shared_for_company(central, cid, "raw")
        result = []
        for r in rows:
            data = r.get("_data") or _get_item_data_safe(central, r["id"])
            result.append({
                "id":            f"shared_{r['id']}",
                "shared_id":     r["id"],
                "name":          r.get("name", ""),
                "type":          "raw",
                "price":         float(data.get("price", 0.0)),
                "total_qty":     data.get("total_qty"),
                "category_id":   None,
                "category_name": "🔗 مشترك",
                "is_shared":     True,
            })
        return result
    except Exception as e:
        print(f"[shared_mixin] get_shared_raws: {e}")
        return []
    finally:
        try:
            central.close()
        except Exception:
            pass


def get_shared_machines(company_id: int = None) -> list:
    cid = company_id or _get_company_id()
    if not cid:
        return []
    central = _get_central()
    if not central:
        return []
    try:
        rows = _fetch_shared_for_company(central, cid, "machine")
        result = []
        for r in rows:
            data = r.get("_data") or _get_item_data_safe(central, r["id"])
            result.append({
                "id":            f"shared_{r['id']}",
                "shared_id":     r["id"],
                "name":          r.get("name", ""),
                "rate_per_hour": float(data.get("rate_per_hour", 0.0)),
                "rate_per_unit": float(data.get("rate_per_unit", 0.0)),
                "category_id":   None,
                "category_name": "🔗 مشترك",
                "is_shared":     True,
            })
        return result
    except Exception as e:
        print(f"[shared_mixin] get_shared_machines: {e}")
        return []
    finally:
        try:
            central.close()
        except Exception:
            pass


def get_shared_labor_ops(company_id: int = None) -> list:
    cid = company_id or _get_company_id()
    if not cid:
        return []
    central = _get_central()
    if not central:
        return []
    try:
        rows = _fetch_shared_for_company(central, cid, "labor_op")
        result = []
        for r in rows:
            data = r.get("_data") or _get_item_data_safe(central, r["id"])
            result.append({
                "id":            f"shared_{r['id']}",
                "shared_id":     r["id"],
                "name":          r.get("name", ""),
                "minutes":       float(data.get("minutes", 0.0)),
                "category_id":   None,
                "category_name": "🔗 مشترك",
                "is_shared":     True,
            })
        return result
    except Exception as e:
        print(f"[shared_mixin] get_shared_labor_ops: {e}")
        return []
    finally:
        try:
            central.close()
        except Exception:
            pass


def get_shared_machine_ops(company_id: int = None) -> list:
    cid = company_id or _get_company_id()
    if not cid:
        return []
    central = _get_central()
    if not central:
        return []
    try:
        rows = _fetch_shared_for_company(central, cid, "machine_op")
        result = []
        for r in rows:
            data = r.get("_data") or _get_item_data_safe(central, r["id"])
            result.append({
                "id":            f"shared_{r['id']}",
                "shared_id":     r["id"],
                "name":          r.get("name", ""),
                "mode":          data.get("mode", "time"),
                "value":         float(data.get("value", 0.0)),
                "machine_name":  data.get("machine_name", ""),
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
        try:
            central.close()
        except Exception:
            pass


def is_shared_id(item_id) -> bool:
    return isinstance(item_id, str) and item_id.startswith("shared_")


def extract_shared_id(item_id) -> int | None:
    if is_shared_id(item_id):
        try:
            return int(str(item_id).replace("shared_", ""))
        except ValueError:
            return None
    return None


def update_shared_item_data(shared_id: int, name: str, data: dict) -> bool:
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
        try:
            central.close()
        except Exception:
            pass