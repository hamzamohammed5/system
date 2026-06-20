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
