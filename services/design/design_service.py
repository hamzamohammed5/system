"""
services/design/design_service.py
===================================
Service layer للتصميمات وتصنيفاتها.
"""

from db.designs.designs_repo import (
    fetch_all_designs, fetch_design,
    insert_design, update_design, delete_design,
)
from db.designs.design_item_categories_repo import (
    fetch_all_item_categories, fetch_item_category,
    insert_item_category, update_item_category, delete_item_category,
    build_item_category_tree, fetch_item_category_descendants,
    count_designs_per_category,
)


class DesignService:
    def __init__(self, conn):
        self.conn = conn

    # ── Designs ─────────────────────────────────────────
    def list_designs(self, category_id=None, set_id=None, name_q=""):
        return fetch_all_designs(self.conn, category_id, set_id, name_q)
    
    def get_design(self, did): 
        return fetch_design(self.conn, did)
    
    def create_design(self, name, cat_id=None, notes=""):
        return insert_design(self.conn, name, cat_id, notes)
    
    def update_design(self, did, name, cat_id=None, notes=""):
        update_design(self.conn, did, name, cat_id, notes)
    
    def delete_design(self, did): 
        delete_design(self.conn, did)

    # ── Item Categories ─────────────────────────────────
    def list_item_categories(self): 
        return fetch_all_item_categories(self.conn)
    
    def get_item_category(self, cid): 
        return fetch_item_category(self.conn, cid)
    
    def create_item_category(self, name, color, parent_id=None):
        return insert_item_category(self.conn, name, color, parent_id)
    
    def update_item_category(self, cid, name, color, parent_id=None):
        update_item_category(self.conn, cid, name, color, parent_id)
    
    def delete_item_category(self, cid): 
        delete_item_category(self.conn, cid)
    
    def build_tree(self, rows): 
        return build_item_category_tree(rows)
    
    def get_descendants(self, cid): 
        return fetch_item_category_descendants(self.conn, cid)
    
    def count_designs_per_category(self): 
        return count_designs_per_category(self.conn)

    # ── Listing / Grid (مع فلترة وأول xcf) ───────────────
    def list_designs_filtered(self, name_q="", category_id=None, set_id=None):
        """
        جلب التصميمات مع فلترة بالاسم والتصنيف والمجموعة.
        first_xcf: يأخذ أولوية المجموعة المفلترة لو محددة (مع fallback لأول ملف عموماً).
        """
        conn = self.conn
        if set_id is not None:
            set_id_int = int(set_id)
            first_xcf_sql = f"""
                COALESCE(
                    (SELECT ds2.xcf_path
                     FROM   design_sizes ds2
                     WHERE  ds2.design_id = d.id
                       AND  ds2.set_id    = {set_id_int}
                       AND  ds2.xcf_path IS NOT NULL
                       AND  ds2.xcf_path != ''
                     ORDER  BY ds2.sort_order, ds2.id
                     LIMIT  1),
                    (SELECT ds3.xcf_path
                     FROM   design_sizes ds3
                     WHERE  ds3.design_id = d.id
                       AND  ds3.xcf_path IS NOT NULL
                       AND  ds3.xcf_path != ''
                     ORDER  BY ds3.sort_order, ds3.id
                     LIMIT  1)
                )
            """
        else:
            first_xcf_sql = """
                (SELECT ds2.xcf_path
                 FROM   design_sizes ds2
                 WHERE  ds2.design_id = d.id
                   AND  ds2.xcf_path IS NOT NULL
                   AND  ds2.xcf_path != ''
                 ORDER  BY ds2.sort_order, ds2.id
                 LIMIT  1)
            """

        sql = f"""
            SELECT d.id, d.name, d.item_category_id, d.notes,
                   d.created_at, d.updated_at,
                   ic.name                              AS category_name,
                   ic.color                             AS category_color,
                   COUNT(DISTINCT ds.id)                AS sizes_count,
                   SUM(CASE WHEN ds.xcf_path IS NOT NULL
                                 AND ds.xcf_path != ''
                            THEN 1 ELSE 0 END)          AS files_count,
                   {first_xcf_sql}                      AS first_xcf
            FROM   designs d
            LEFT JOIN design_item_categories ic ON ic.id = d.item_category_id
            LEFT JOIN design_sizes ds           ON ds.design_id = d.id
        """
        conditions, params = [], []

        if name_q:
            conditions.append("d.name LIKE ?")
            params.append(f"%{name_q}%")

        if category_id is not None:
            try:
                desc = fetch_item_category_descendants(conn, category_id)
                ph   = ",".join("?" * len(desc))
                conditions.append(f"d.item_category_id IN ({ph})")
                params.extend(desc)
            except Exception:
                conditions.append("d.item_category_id = ?")
                params.append(category_id)

        if set_id is not None:
            conditions.append(
                "EXISTS (SELECT 1 FROM design_sizes ds2 "
                "WHERE ds2.design_id = d.id AND ds2.set_id = ?)"
            )
            params.append(set_id)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " GROUP BY d.id ORDER BY d.updated_at DESC, d.name"
        return conn.execute(sql, params).fetchall()

    def get_first_xcf_for_design(self, design_id, set_id=None):
        """
        يجيب مسار الـ xcf المناسب للتصميم:
          - لو set_id محدد → أول ملف ينتمي لهذه المجموعة
          - fallback      → أول ملف موجود عموماً بغض النظر عن المجموعة
        يرجع None لو مفيش ملف.
        """
        conn = self.conn
        if set_id is not None:
            row = conn.execute(
                """
                SELECT xcf_path FROM design_sizes
                WHERE  design_id = ?
                  AND  set_id    = ?
                  AND  xcf_path IS NOT NULL
                  AND  xcf_path != ''
                ORDER  BY sort_order, id
                LIMIT  1
                """,
                (design_id, set_id),
            ).fetchone()
            if row and row["xcf_path"]:
                return row["xcf_path"]

        row = conn.execute(
            """
            SELECT xcf_path FROM design_sizes
            WHERE  design_id = ?
              AND  xcf_path IS NOT NULL
              AND  xcf_path != ''
            ORDER  BY sort_order, id
            LIMIT  1
            """,
            (design_id,),
        ).fetchone()
        return row["xcf_path"] if row and row["xcf_path"] else None
