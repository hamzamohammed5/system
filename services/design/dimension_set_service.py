"""
services/design/dimension_set_service.py
==========================================
Service layer لمجموعات المقاسات وحقولها واعتمادياتها.
يُستدعى من tabs/design/ بدلاً من repos مباشرة.
"""

from db.designs.dimension_sets_repo import (
    fetch_all_dimension_sets, fetch_dimension_set,
    insert_dimension_set, update_dimension_set, delete_dimension_set,
    fetch_fields_for_set, fetch_field,
    insert_field, update_field, delete_field, reorder_fields,
    fetch_field_dep, set_field_dep, remove_field_dep,
    fetch_all_design_categories, fetch_design_category,
    insert_design_category, update_design_category, delete_design_category,
    build_category_tree, fetch_category_descendants,
)
from db.designs.dimension_instances_repo import (
    fetch_instances_for_set, fetch_instance,
    insert_instance, update_instance, delete_instance, duplicate_instance,
    fetch_instance_values, save_instance_values, calc_instance_cross_auto,
)


class DimensionSetService:
    """CRUD كاملة لمجموعات المقاسات وحقولها وتصنيفاتها."""

    def __init__(self, conn):
        self.conn = conn

    # ── Sets ────────────────────────────────────────────
    def list_sets(self): 
        return fetch_all_dimension_sets(self.conn)
    
    def get_set(self, sid): 
        return fetch_dimension_set(self.conn, sid)
    
    def create_set(self, name, cat_id, unit, notes):
        return insert_dimension_set(self.conn, name, cat_id, unit, notes)
    
    def update_set(self, sid, name, cat_id, unit, notes):
        update_dimension_set(self.conn, sid, name, cat_id, unit, notes)
    
    def delete_set(self, sid): 
        delete_dimension_set(self.conn, sid)

    def count_designs_for_set(self, sid) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) as c FROM design_sizes WHERE set_id=?", (sid,)
        ).fetchone()["c"]

    def count_fields_for_set(self, sid) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) as c FROM dimension_fields WHERE set_id=?", (sid,)
        ).fetchone()["c"]

    def count_instances_for_set(self, sid) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) as c FROM dimension_set_instances WHERE set_id=?", (sid,)
        ).fetchone()["c"]

    # ── Fields ──────────────────────────────────────────
    def list_fields(self, set_id): 
        return fetch_fields_for_set(self.conn, set_id)
    
    def get_field(self, fid): 
        return fetch_field(self.conn, fid)
    
    def create_field(self, set_id, name, label, unit, ftype, required, sort_order):
        return insert_field(self.conn, set_id, name, label, unit, ftype, required, sort_order)
    
    def update_field(self, fid, name, label, unit, ftype, required, sort_order):
        update_field(self.conn, fid, name, label, unit, ftype, required, sort_order)
    
    def delete_field(self, fid): 
        delete_field(self.conn, fid)
    
    def reorder_fields(self, set_id, ids): 
        reorder_fields(self.conn, set_id, ids)

    # ── Field Dependencies ──────────────────────────────
    def get_field_dep(self, fid): 
        return fetch_field_dep(self.conn, fid)
    
    def set_field_dep(self, fid, src_fid, offset, notes, src_set_id=None):
        set_field_dep(self.conn, fid, src_fid, offset, notes, source_set_id=src_set_id)
    
    def remove_field_dep(self, fid): 
        remove_field_dep(self.conn, fid)

    # ── Categories ──────────────────────────────────────
    def list_categories(self): 
        return fetch_all_design_categories(self.conn)
    
    def get_category(self, cid): 
        return fetch_design_category(self.conn, cid)
    
    def create_category(self, name, color, parent_id):
        return insert_design_category(self.conn, name, color, parent_id)
    
    def update_category(self, cid, name, color, parent_id):
        update_design_category(self.conn, cid, name, color, parent_id)
    
    def delete_category(self, cid): 
        delete_design_category(self.conn, cid)
    
    def build_tree(self, rows): 
        return build_category_tree(rows)
    
    def get_descendants(self, cid): 
        return fetch_category_descendants(self.conn, cid)

    def count_sets_in_category(self, cid) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) as c FROM dimension_sets WHERE category_id=?", (cid,)
        ).fetchone()["c"]

    # ── Instances ───────────────────────────────────────
    def list_instances(self, set_id): 
        return fetch_instances_for_set(self.conn, set_id)
    
    def get_instance(self, iid): 
        return fetch_instance(self.conn, iid)
    
    def create_instance(self, set_id, name):
        return insert_instance(self.conn, set_id, name)
    
    def update_instance(self, iid, name): 
        update_instance(self.conn, iid, name)
    
    def delete_instance(self, iid): 
        delete_instance(self.conn, iid)
    
    def duplicate_instance(self, iid, new_name):
        return duplicate_instance(self.conn, iid, new_name)

    def get_instance_values(self, iid): 
        return fetch_instance_values(self.conn, iid)
    
    def save_instance_values(self, iid, set_id, values):
        save_instance_values(self.conn, iid, set_id, values)
    
    def calc_cross_auto(self, field_id, instance_id):
        return calc_instance_cross_auto(self.conn, field_id, instance_id)

    def get_source_instance_value(self, source_instance_id, source_field_id):
        row = self.conn.execute(
            "SELECT value_num FROM dimension_set_values "
            "WHERE instance_id=? AND field_id=?",
            (source_instance_id, source_field_id)
        ).fetchone()
        return float(row["value_num"]) if row and row["value_num"] is not None else None

    def get_set_name(self, set_id) -> str:
        row = self.conn.execute(
            "SELECT name FROM dimension_sets WHERE id=?", (set_id,)
        ).fetchone()
        return row["name"] if row else f"#{set_id}"
