"""
db/raw_variants_repo.py
========================
عمليات قراءة/كتابة جدول raw_variants.

كل خامة (raw item) ممكن يكون ليها variants — كل variant بيعبر عن
عدد القطع اللي بتنتجها من الخامة دي.

مثال:
  خامة "قماش" سعرها 100 جنيه:
    - variant "قميص كبير"  → pieces = 2  → تكلفة الوحدة = 100 ÷ 2 = 50 ج
    - variant "قميص صغير" → pieces = 3  → تكلفة الوحدة = 100 ÷ 3 = 33.33 ج

لو مفيش variant محدد → بيستخدم سعر الخامة كما هو (أو مقسوم على total_qty
لو محددة — نفس السلوك الحالي).
"""


def create_raw_variants_table(conn):
    """إنشاء الجدول لو مش موجود."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS raw_variants (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id  INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
            name     TEXT    NOT NULL,
            pieces   REAL    NOT NULL DEFAULT 1
                CHECK(pieces > 0),
            notes    TEXT
        )
    """)
    conn.commit()


# ══════════════════════════════════════════════════════════
# CRUD
# ══════════════════════════════════════════════════════════

def fetch_variants_for_item(conn, item_id: int) -> list:
    """كل الـ variants الخاصة بخامة معينة."""
    return conn.execute(
        "SELECT id, item_id, name, pieces, notes "
        "FROM raw_variants WHERE item_id = ? ORDER BY name",
        (item_id,)
    ).fetchall()


def fetch_variant(conn, variant_id: int):
    return conn.execute(
        "SELECT id, item_id, name, pieces, notes FROM raw_variants WHERE id = ?",
        (variant_id,)
    ).fetchone()


def insert_variant(conn, item_id: int, name: str,
                   pieces: float, notes: str = None) -> int:
    cur = conn.execute(
        "INSERT INTO raw_variants (item_id, name, pieces, notes) VALUES (?, ?, ?, ?)",
        (item_id, name, pieces, notes or "")
    )
    conn.commit()
    return cur.lastrowid


def update_variant(conn, variant_id: int, name: str,
                   pieces: float, notes: str = None):
    conn.execute(
        "UPDATE raw_variants SET name=?, pieces=?, notes=? WHERE id=?",
        (name, pieces, notes or "", variant_id)
    )
    conn.commit()


def delete_variant(conn, variant_id: int):
    conn.execute("DELETE FROM raw_variants WHERE id=?", (variant_id,))
    conn.commit()


# ══════════════════════════════════════════════════════════
# حساب التكلفة مع variant
# ══════════════════════════════════════════════════════════

def calc_unit_cost_with_variant(item_row, variant_id: int | None,
                                 conn) -> float:
    """
    يحسب تكلفة الوحدة الواحدة من الخامة مع مراعاة الـ variant.

    الأولوية:
      1. لو variant_id محدد → سعر الخامة ÷ pieces الخاصة بالـ variant
      2. لو مفيش variant ولكن total_qty محددة → سعر ÷ total_qty
      3. غير كده → السعر مباشرة

    ملاحظة: raw_unit_price الحالية تتعامل مع حالتي 2 و 3.
    الـ variant تضيف حالة 1 كأولوية أعلى.
    """
    from models.costing_base import raw_unit_price

    price = float(item_row["price"])

    if variant_id is not None:
        var = fetch_variant(conn, variant_id)
        if var and float(var["pieces"]) > 0:
            return price / float(var["pieces"])

    # fallback للسلوك الحالي
    return raw_unit_price(item_row)