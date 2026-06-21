"""
ui/tabs/costing/shared/bom_scenarios/_db_scenarios.py
======================================================
DbScenariosMixin — منطق تحميل وإدارة السيناريوهات من قاعدة البيانات.

مُستخرج من bom_scenarios_panel.py لتقليل الحجم وتوضيح المسؤوليات.
يُستخدم فقط من _BomScenariosPanel.

[Refactor] استخدام ScenarioService بدل bom_scenarios_repo مباشرة.
[Fix] استخدام emit_company_data_changed بدل bus.data_changed.emit()
      حسب توصية files_reference/models&services.md
[Fix] استخدام مفتاح ترجمة (t("error")) بدل النص المباشر "خطأ"
      في رسالة QMessageBox.warning — لا نص مكتوب مباشرة في الكود.
"""

from PyQt5.QtWidgets import QMessageBox

from services.costing.scenario_service import ScenarioService
from ui.widgets.core.events import emit_company_data_changed
from ui.widgets.core.i18n import tr


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
        # [Refactor] استخدام ScenarioService بدل bom_scenarios_repo مباشرة
        svc = ScenarioService(self.conn)
        return svc.ensure_default(item_id)

    def _reload(self):
        """إعادة تحميل السيناريوهات من DB."""
        if self._item_id is None:
            return

        # [Refactor] استخدام ScenarioService بدل bom_scenarios_repo مباشرة
        svc  = ScenarioService(self.conn)
        rows = svc.list(self._item_id)
        self._scenarios = [
            {
                "id":         sc.id,
                "name":       sc.name,
                "is_default": sc.is_default,
            }
            for sc in rows
        ]

        prev_id  = self._current_id
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
        # [Refactor] استخدام ScenarioService بدل bom_scenarios_repo مباشرة
        svc = ScenarioService(self.conn)
        svc.set_default(scenario_id)
        emit_company_data_changed()
        self._reload()

    def _db_rename(self, scenario_id: int, name: str):
        # [Refactor] استخدام ScenarioService بدل bom_scenarios_repo مباشرة
        svc = ScenarioService(self.conn)
        svc.rename(scenario_id, name)
        emit_company_data_changed()
        self._reload()

    def _db_clone(self, scenario_id: int, name: str) -> int | None:
        try:
            # [Refactor] استخدام ScenarioService بدل bom_scenarios_repo مباشرة
            svc    = ScenarioService(self.conn)
            new_id = svc.clone(scenario_id, name)
            emit_company_data_changed()
            return new_id
        except Exception as e:
            QMessageBox.warning(None, t("error"), str(e))
            return None

    def _db_add_new(self, name: str) -> int | None:
        if self._item_id is None:
            return None
        # [Refactor] استخدام ScenarioService بدل bom_scenarios_repo مباشرة
        svc    = ScenarioService(self.conn)
        new_id = svc.create(self._item_id, name, is_default=False)
        emit_company_data_changed()
        return new_id

    def _db_delete(self, scenario_id: int) -> bool:
        # [Refactor] استخدام ScenarioService بدل bom_scenarios_repo مباشرة
        svc    = ScenarioService(self.conn)
        result = svc.delete(scenario_id)
        if result:
            emit_company_data_changed()
        return result