"""
ui/widgets/shared/shared_ops_mixin.py
======================================
SharedOpsMixin — مكسن يوحّد منطق النشر والتعديل المشترك
المتكرر في machine_table.py و labor_op_table.py.

يوفر:
  _edit_shared_item(item_id, name)           → فتح نافذة تعديل مشترك
  _edit_published_item(row, shared_type)     → فتح تعديل عنصر محلي منشور
  _publish_item(row, shared_type, item_data) → نشر عنصر محلي كمشترك
  _check_shared_id(item_id)                  → True لو الـ id مشترك

الاستخدام:
    class _MachineTable(QWidget, SharedOpsMixin):
        def _edit_shared(self):
            item_id, _ = self._selected_row_data()
            self._edit_shared_item(item_id, "machine")
"""

from PyQt5.QtWidgets import QMessageBox


class SharedOpsMixin:
    """
    مكسن يوحّد منطق العمليات المشتركة (publish / edit shared).

    يفترض وجود:
      - self._published_names: set[str]
    """

    # ── تحقق مبدئي ───────────────────────────────────────

    def _check_shared_id(self, item_id) -> bool:
        """True لو الـ item_id يمثل عنصراً مشتركاً."""
        try:
            from ui.tabs.companies.shared_items_mixin import is_shared_id
            return is_shared_id(item_id)
        except Exception:
            return False

    def _extract_shared_id(self, item_id):
        try:
            from ui.tabs.companies.shared_items_mixin import extract_shared_id
            return extract_shared_id(item_id)
        except Exception:
            return None

    def _is_published(self, row: dict) -> bool:
        """True لو العنصر المحلي منشور كمشترك."""
        names = getattr(self, '_published_names', set())
        return str(row.get("name", "")).strip().lower() in names

    # ── تعديل مشترك ──────────────────────────────────────

    def _edit_shared_item(self, item_id, shared_type: str, parent=None):
        """
        يفتح نافذة تعديل العنصر المشترك.
        يدعم أيضاً العناصر المحلية المنشورة.
        """
        parent = parent or self

        if not self._check_shared_id(item_id):
            row = self._find_row_by_id(item_id)
            if row and self._is_published(row):
                self._edit_published_item(row, shared_type, parent)
                return
            QMessageBox.information(
                parent, "تنبيه",
                "هذا عنصر عادي — استخدم «✏️ تعديل»."
            )
            return

        shared_id = self._extract_shared_id(item_id)
        if shared_id is None:
            return

        try:
            from db.companies.companies_schema import get_central_connection, create_central_tables
            from ui.tabs.companies.shared_items_dialog import SharedItemsDialog
            central = get_central_connection()
            create_central_tables(central)
            dlg = SharedItemsDialog(central, shared_id, parent=parent)
            dlg.exec_()
            central.close()
            from ui.events import bus
            bus.data_changed.emit()
        except Exception as e:
            QMessageBox.warning(parent, "خطأ", str(e))

    def _edit_published_item(self, row: dict, shared_type: str, parent=None):
        """يفتح تعديل عنصر محلي منشور كمشترك."""
        parent = parent or self
        try:
            from db.companies.companies_schema import get_central_connection, create_central_tables
            from ui.tabs.companies.shared_items_dialog import SharedItemsDialog
            central = get_central_connection()
            create_central_tables(central)
            shared_row = central.execute(
                "SELECT id FROM shared_items WHERE name=? AND shared_type=? LIMIT 1",
                (row.get("name", ""), shared_type)
            ).fetchone()
            if shared_row:
                dlg = SharedItemsDialog(central, shared_row["id"], parent=parent)
                dlg.exec_()
            central.close()
            from ui.events import bus
            bus.data_changed.emit()
        except Exception as e:
            QMessageBox.warning(parent, "خطأ", str(e))

    # ── نشر كمشترك ───────────────────────────────────────

    def _publish_item(self, row: dict, shared_type: str,
                      item_data: dict, parent=None):
        """
        ينشر عنصراً محلياً كمشترك.
        لو منشور بالفعل → يفتح تعديل الربط.

        item_data: dict بالبيانات الإضافية للعنصر
        """
        parent = parent or self

        if self._is_published(row):
            self._edit_published_item(row, shared_type, parent)
            return

        try:
            from db.companies.companies_schema import (
                get_central_connection, create_central_tables
            )
            from db.companies.shared_items_repo import create_shared_items_tables
            from ui.tabs.companies.shared_items_manager_helper._add_shared_item_dialog import (
                PublishAsSharedDialog
            )
            central = get_central_connection()
            create_central_tables(central)
            create_shared_items_tables(central)

            dlg = PublishAsSharedDialog(
                central_conn=central,
                shared_type=shared_type,
                item_name=row.get("name", ""),
                item_data=item_data,
                parent=parent,
            )
            dlg.exec_()
            central.close()
        except Exception as e:
            QMessageBox.warning(parent, "خطأ", str(e))

    # ── مساعد بحث ────────────────────────────────────────

    def _find_row_by_id(self, item_id) -> dict | None:
        """يبحث عن الصف في self._all_rows بالـ id."""
        all_rows = getattr(self, '_all_rows', [])
        for r in all_rows:
            if str(r.get("id")) == str(item_id):
                return r
        return None
