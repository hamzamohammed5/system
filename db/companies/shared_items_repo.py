"""
db/companies/shared_items_repo.py  (نسخة مُحدَّثة)
===================================
إدارة العناصر المشتركة بين الشركات — نموذج موحّد.

إصلاح 33: استبدال _decode/_encode المحلية بـ decode_json/encode_json من json_utils.
"""

from db.shared.json_utils import decode_json, encode_json


# ══════════════════════════════════════════════════════════
# Migration — إنشاء الجداول لو مش موجودة
# ══════════════════════════════════════════════════════════

def create_shared_items_tables(conn):
    """يُنشئ جداول العناصر المشتركة في companies.db."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS shared_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            shared_type TEXT    NOT NULL
                CHECK(shared_type IN ('raw','machine','labor_op','machine_op')),
            data        TEXT    NOT NULL DEFAULT '{}',
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS company_shared_links (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            shared_item_id INTEGER NOT NULL REFERENCES shared_items(id) ON DELETE CASCADE,
            company_id     INTEGER NOT NULL REFERENCES companies(id)    ON DELETE CASCADE,
            linked_at      TEXT    NOT NULL DEFAULT (datetime('now')),
            UNIQUE(shared_item_id, company_id)
        );
    """)
    conn.commit()


# ══════════════════════════════════════════════════════════
# مساعدات الـ JSON — [إصلاح 33] من json_utils مباشرة
# ══════════════════════════════════════════════════════════

# للتوافق مع أي كود داخلي يستدعيهم بالاسم القديم
_decode = decode_json
_encode = encode_json


def _default_data(shared_type: str) -> dict:
    if shared_type == "raw":
        return {"price": 0.0, "total_qty": None}
    elif shared_type == "machine":
        return {"rate_per_hour": 0.0, "rate_per_unit": 0.0}
    elif shared_type == "labor_op":
        return {"minutes": 0.0}
    elif shared_type == "machine_op":
        return {"mode": "time", "value": 0.0, "machine_name": "",
                "rate_per_hour": 0.0, "rate_per_unit": 0.0}
    return {}


# ══════════════════════════════════════════════════════════
# CRUD — shared_items
# ══════════════════════════════════════════════════════════

def fetch_all_shared_items(conn, shared_type: str = None) -> list:
    if shared_type:
        return conn.execute(
            "SELECT id, name, shared_type, data, updated_at "
            "FROM shared_items WHERE shared_type=? ORDER BY name",
            (shared_type,)
        ).fetchall()
    return conn.execute(
        "SELECT id, name, shared_type, data, updated_at "
        "FROM shared_items ORDER BY shared_type, name"
    ).fetchall()


def fetch_shared_item(conn, item_id: int):
    return conn.execute(
        "SELECT id, name, shared_type, data, updated_at "
        "FROM shared_items WHERE id=?",
        (item_id,)
    ).fetchone()


def insert_shared_item(conn, name: str, shared_type: str,
                        data: dict = None) -> int:
    d = data if data is not None else _default_data(shared_type)
    cur = conn.execute(
        "INSERT INTO shared_items (name, shared_type, data) VALUES (?, ?, ?)",
        (name, shared_type, encode_json(d))
    )
    conn.commit()
    return cur.lastrowid


def update_shared_item(conn, item_id: int, name: str, data: dict):
    conn.execute(
        "UPDATE shared_items SET name=?, data=?, updated_at=datetime('now') WHERE id=?",
        (name, encode_json(data), item_id)
    )
    conn.commit()


def delete_shared_item(conn, item_id: int):
    conn.execute("DELETE FROM shared_items WHERE id=?", (item_id,))
    conn.commit()


# ══════════════════════════════════════════════════════════
# CRUD — company_shared_links
# ══════════════════════════════════════════════════════════

def fetch_linked_companies(conn, shared_item_id: int) -> list:
    return conn.execute(
        """SELECT c.id, c.name, c.color, lnk.linked_at
           FROM company_shared_links lnk
           JOIN companies c ON c.id = lnk.company_id
           WHERE lnk.shared_item_id = ?
           ORDER BY c.name""",
        (shared_item_id,)
    ).fetchall()


def fetch_shared_items_for_company(conn, company_id: int,
                                    shared_type: str = None) -> list:
    if shared_type:
        return conn.execute(
            """SELECT s.id, s.name, s.shared_type, s.data, s.updated_at
               FROM company_shared_links lnk
               JOIN shared_items s ON s.id = lnk.shared_item_id
               WHERE lnk.company_id=? AND s.shared_type=?
               ORDER BY s.name""",
            (company_id, shared_type)
        ).fetchall()
    return conn.execute(
        """SELECT s.id, s.name, s.shared_type, s.data, s.updated_at
           FROM company_shared_links lnk
           JOIN shared_items s ON s.id = lnk.shared_item_id
           WHERE lnk.company_id=?
           ORDER BY s.shared_type, s.name""",
        (company_id,)
    ).fetchall()


def is_company_linked(conn, shared_item_id: int, company_id: int) -> bool:
    row = conn.execute(
        "SELECT 1 FROM company_shared_links WHERE shared_item_id=? AND company_id=?",
        (shared_item_id, company_id)
    ).fetchone()
    return row is not None


def link_company(conn, shared_item_id: int, company_id: int):
    conn.execute(
        "INSERT OR IGNORE INTO company_shared_links (shared_item_id, company_id) VALUES (?, ?)",
        (shared_item_id, company_id)
    )
    conn.commit()


def unlink_company(conn, shared_item_id: int, company_id: int):
    conn.execute(
        "DELETE FROM company_shared_links WHERE shared_item_id=? AND company_id=?",
        (shared_item_id, company_id)
    )
    conn.commit()


def set_linked_companies(conn, shared_item_id: int, company_ids: list):
    conn.execute(
        "DELETE FROM company_shared_links WHERE shared_item_id=?",
        (shared_item_id,)
    )
    for cid in company_ids:
        conn.execute(
            "INSERT INTO company_shared_links (shared_item_id, company_id) VALUES (?, ?)",
            (shared_item_id, cid)
        )
    conn.commit()


# ══════════════════════════════════════════════════════════
# قراءة بيانات العنصر كـ dict جاهزة للاستخدام
# ══════════════════════════════════════════════════════════

def get_item_data(conn, shared_item_id: int) -> dict:
    row = fetch_shared_item(conn, shared_item_id)
    if not row:
        return {}
    return decode_json(row["data"])


def get_item_as_raw(conn, shared_item_id: int) -> dict | None:
    row = fetch_shared_item(conn, shared_item_id)
    if not row or row["shared_type"] != "raw":
        return None
    d = decode_json(row["data"])
    return {
        "id":            shared_item_id,
        "name":          row["name"],
        "type":          "raw",
        "price":         d.get("price", 0.0),
        "total_qty":     d.get("total_qty"),
        "category_id":   None,
        "category_name": "🔗 مشترك",
        "is_shared":     True,
        "shared_id":     shared_item_id,
    }


def get_item_as_machine(conn, shared_item_id: int) -> dict | None:
    row = fetch_shared_item(conn, shared_item_id)
    if not row or row["shared_type"] != "machine":
        return None
    d = decode_json(row["data"])
    return {
        "id":             shared_item_id,
        "name":           row["name"],
        "rate_per_hour":  d.get("rate_per_hour", 0.0),
        "rate_per_unit":  d.get("rate_per_unit", 0.0),
        "category_id":    None,
        "category_name":  "🔗 مشترك",
        "is_shared":      True,
        "shared_id":      shared_item_id,
    }


def get_item_as_labor_op(conn, shared_item_id: int) -> dict | None:
    row = fetch_shared_item(conn, shared_item_id)
    if not row or row["shared_type"] != "labor_op":
        return None
    d = decode_json(row["data"])
    return {
        "id":            shared_item_id,
        "name":          row["name"],
        "minutes":       d.get("minutes", 0.0),
        "category_id":   None,
        "category_name": "🔗 مشترك",
        "is_shared":     True,
        "shared_id":     shared_item_id,
    }