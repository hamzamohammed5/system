"""
ui/tabs/costing/shared/bom_scenarios/_db_scenarios.py
======================================================
DbScenariosMixin — منطق تحميل وإدارة السيناريوهات من قاعدة البيانات.

مُستخرج من bom_scenarios_panel.py لتقليل الحجم وتوضيح المسؤوليات.
يُستخدم فقط من _BomScenariosPanel.

[Fix] استخدام emit_company_data_changed بدل bus.data_changed.emit()
      حسب توصية files_reference/models&services.md
"""

from PyQt5.QtWidgets import QMessageBox

from db.costing.bom_scenarios_repo import (
    fetch_scenarios, insert_scenario, update_scenario,
    delete_scenario, set_default_scenario, clone_scenario,
    fetch_default_scenario,
)
from ui.widgets.core.events import emit_company_data_changed


class DbScenariosMixin:
    """
    Mixin يضيف منطق السيناريوهات من قاعدة البيانات (DB mode).

    يفترض وجود:
      - self.conn
      - self._item_id    : int | None
      - self._scenarios  : list[dict]
      - self._current_id : int | None
      - self._in_memory  : bool
      - self._rebuild_combo()
      - self._sync_current()
      - self.scenario_changed signal
    """

    def load_item(self, item_id: int):
        """تحميل سيناريوهات منتج موجود (DB mode)."""
        self._in_memory = False
        self._item_id   = item_id
        self._reload()

    def ensure_default_scenario(self, item_id: int) -> int:
        """
        يتأكد من وجود سيناريو default للمنتج.
        لو مفيش → ينشئ واحد. يرجع id السيناريو الـ default.
        """
        sc = fetch_default_scenario(self.conn, item_id)
        if sc:
            return sc["id"]
        return insert_scenario(self.conn, item_id, "سيناريو 1", is_default=True)

    def _reload(self):
        """إعادة تحميل السيناريوهات من DB."""
        if self._item_id is None:
            return
        rows = fetch_scenarios(self.conn, self._item_id)
        self._scenarios = [dict(r) for r in rows]
        prev_id = self._current_id
        self._rebuild_combo()

        restored = False
        if prev_id is not None:
            for sc in self._scenarios:
                if sc["id"] == prev_id:
                    self._current_id = prev_id
                    restored = True
                    break

        if not restored:
            for sc in self._scenarios:
                if sc["is_default"]:
                    self._current_id = sc["id"]
                    break

        self._rebuild_combo()
        self._sync_current()

    # ── CRUD في DB ────────────────────────────────────────

    def _db_set_default(self, scenario_id: int):
        set_default_scenario(self.conn, scenario_id)
        # [Fix] emit_company_data_changed بدل bus.data_changed.emit()
        emit_company_data_changed()
        self._reload()

    def _db_rename(self, scenario_id: int, name: str):
        update_scenario(self.conn, scenario_id, name)
        # [Fix] emit_company_data_changed بدل bus.data_changed.emit()
        emit_company_data_changed()
        self._reload()

    def _db_clone(self, scenario_id: int, name: str) -> int | None:
        try:
            new_id = clone_scenario(self.conn, scenario_id, name)
            # [Fix] emit_company_data_changed بدل bus.data_changed.emit()
            emit_company_data_changed()
            return new_id
        except Exception as e:
            QMessageBox.warning(None, "خطأ", str(e))
            return None

    def _db_add_new(self, name: str) -> int | None:
        if self._item_id is None:
            return None
        new_id = insert_scenario(
            self.conn, self._item_id, name, is_default=False
        )
        # [Fix] emit_company_data_changed بدل bus.data_changed.emit()
        emit_company_data_changed()
        return new_id

    def _db_delete(self, scenario_id: int) -> bool:
        result = delete_scenario(self.conn, scenario_id)
        if result:
            # [Fix] emit_company_data_changed بدل bus.data_changed.emit()
            emit_company_data_changed()
        return result