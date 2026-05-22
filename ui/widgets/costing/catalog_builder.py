"""
ui/widgets/costing/catalog_builder.py
=======================================
يبني الـ catalog المستخدم في ComponentRow ويدمج العناصر المحلية مع المشتركة.

الـ catalog هو dict بالشكل:
  {
    "raw":        [(id, name, category_name, price, total_qty), ...],
    "semi":       [(id, name, category_name, price, None), ...],
    "final":      [(id, name, category_name, price, None), ...],
    "labor_op":   [(id, name, category_name, minutes), ...],
    "machine_op": [(id, name, category_name, mode, machine_name), ...],
  }

العناصر المشتركة:
  - تأتي مع category_name = "🔗 مشترك"
  - id = "shared:{shared_item_id}" (string)
  - تُقرأ مباشرة من companies.db
  - أي تعديل عليها يتعكس فوراً على كل الشركات المشتركة
"""

from db.shared.items_repo import fetch_items_by_type


SHARED_CATEGORY = "🔗 مشترك"


def build_catalog(conn) -> dict:
    """
    يبني الـ catalog الكامل للـ ComponentRow.
    يدمج العناصر المحلية مع المشتركة لكل نوع.
    """
    catalog = {}

    # ── خامات ──
    catalog["raw"] = _build_raw(conn)

    # ── نصف مصنع ──
    catalog["semi"] = [
        (r["id"], r["name"], r.get("category_name") or "", 0.0, None)
        for r in fetch_items_by_type(conn, "semi")
    ]

    # ── منتج نهائي ──
    catalog["final"] = [
        (r["id"], r["name"], r.get("category_name") or "", 0.0, None)
        for r in fetch_items_by_type(conn, "final")
    ]

    # ── عمليات العمالة ──
    catalog["labor_op"] = _build_labor_ops(conn)

    # ── عمليات التشغيل ──
    catalog["machine_op"] = _build_machine_ops(conn)

    return catalog


def _build_raw(conn) -> list:
    """خامات محلية + مشتركة."""
    # محلية
    local = [
        (r["id"], r["name"], r.get("category_name") or "", r["price"], r.get("total_qty"))
        for r in fetch_items_by_type(conn, "raw")
    ]

    # مشتركة — تُقرأ من companies.db مباشرة
    shared_entries = []
    for item in _fetch_shared("raw"):
        shared_entries.append((
            item["id"],                      # "shared:{n}"
            item["name"],
            SHARED_CATEGORY,
            float(item.get("price", 0.0)),
            item.get("total_qty"),
        ))

    return local + shared_entries


def _build_labor_ops(conn) -> list:
    """عمليات عمالة محلية + مشتركة."""
    try:
        from db.costing.operations_repo import fetch_all_labor_ops
        local = [
            (r["id"], r["name"], r.get("category_name") or "", r.get("minutes", 0.0))
            for r in fetch_all_labor_ops(conn)
        ]
    except Exception:
        local = []

    shared_entries = [
        (item["id"], item["name"], SHARED_CATEGORY, float(item.get("minutes", 0.0)))
        for item in _fetch_shared("labor_op")
    ]

    return local + shared_entries


def _build_machine_ops(conn) -> list:
    """عمليات تشغيل محلية + مشتركة."""
    try:
        from db.costing.operations_repo import fetch_all_machine_ops
        local = [
            (r["id"], r["name"], r.get("category_name") or "",
             r.get("mode", "time"), r.get("machine_name", ""))
            for r in fetch_all_machine_ops(conn)
        ]
    except Exception:
        local = []

    shared_entries = [
        (item["id"], item["name"], SHARED_CATEGORY,
         item.get("mode", "time"), item.get("machine_name", ""))
        for item in _fetch_shared("machine_op")
    ]

    return local + shared_entries


def _fetch_shared(shared_type: str) -> list:
    """
    يجيب العناصر المشتركة من companies.db للشركة النشطة.
    يرجع list of dicts مع id = "shared:{n}".
    """
    try:
        from db.companies.company_state import company_state
        if not company_state.is_ready:
            return []
        company_id = company_state.company_id

        import json
        from db.companies.companies_schema import get_central_connection
        central = get_central_connection()
        rows = central.execute("""
            SELECT s.id, s.name, s.data
            FROM company_shared_links lnk
            JOIN shared_items s ON s.id = lnk.shared_item_id
            WHERE lnk.company_id = ? AND s.shared_type = ?
            ORDER BY s.name
        """, (company_id, shared_type)).fetchall()
        central.close()

        result = []
        for row in rows:
            try:
                data = json.loads(row["data"]) if row["data"] else {}
            except Exception:
                data = {}
            item = {"id": f"shared:{row['id']}", "name": row["name"]}
            item.update(data)
            result.append(item)
        return result
    except Exception as e:
        print(f"[catalog_builder] _fetch_shared({shared_type}) error: {e}")
        return []