"""
services/design/design_size_service.py
========================================
Service layer لمقاسات التصميم.
"""

from db.designs.designs_sizes_repo import (
    fetch_design_sizes, fetch_design_size,
    insert_design_size, update_design_size, delete_design_size,
    update_design_size_path, fetch_canvas_size, fetch_canvas_dpi,
    fetch_instances_for_set_with_values, instance_already_used,
)
from db.designs.dimension_sets_repo import fetch_all_dimension_sets, fetch_fields_for_set


class DesignSizeService:
    def __init__(self, conn):
        self.conn = conn

    def list_sizes(self, design_id): 
        return fetch_design_sizes(self.conn, design_id)
    
    def get_size(self, size_id): 
        return fetch_design_size(self.conn, size_id)
    
    def create_size(self, design_id, set_id, instance_id,
                    width_field_id=None, height_field_id=None,
                    xcf_path=None, notes="", dpi_field_id=None):
        return insert_design_size(
            self.conn, design_id, set_id, instance_id,
            width_field_id, height_field_id, xcf_path, notes,
            dpi_field_id=dpi_field_id
        )
    
    def update_size(self, size_id, width_field_id, height_field_id,
                    xcf_path, notes, dpi_field_id=None):
        update_design_size(self.conn, size_id, width_field_id, height_field_id,
                           xcf_path, notes, dpi_field_id=dpi_field_id)
    
    def update_path(self, size_id, path): 
        update_design_size_path(self.conn, size_id, path)
    
    def delete_size(self, size_id): 
        delete_design_size(self.conn, size_id)

    def get_canvas_size(self, size_id): 
        return fetch_canvas_size(self.conn, size_id)
    
    def get_canvas_dpi(self, size_id): 
        return fetch_canvas_dpi(self.conn, size_id)

    def list_all_sets(self): 
        return fetch_all_dimension_sets(self.conn)
    
    def list_fields_for_set(self, set_id): 
        return fetch_fields_for_set(self.conn, set_id)
    
    def list_instances_for_set(self, set_id):
        return fetch_instances_for_set_with_values(self.conn, set_id)
    
    def is_instance_used(self, design_id, instance_id, exclude_size_id=None):
        return instance_already_used(self.conn, design_id, instance_id, exclude_size_id)

    def get_set_default_unit(self, set_id) -> str:
        row = self.conn.execute(
            "SELECT default_unit FROM dimension_sets WHERE id=?", (set_id,)
        ).fetchone()
        return row["default_unit"] if row and row["default_unit"] else "cm"

    def get_field_value(self, instance_id, field_id):
        row = self.conn.execute(
            "SELECT value_num FROM dimension_set_values "
            "WHERE instance_id=? AND field_id=?",
            (instance_id, field_id)
        ).fetchone()
        return row["value_num"] if row else None
