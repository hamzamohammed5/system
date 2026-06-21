"""
ui/tabs/costing/shared/bom_scenarios/_memory_scenarios.py
==========================================================
MemoryScenariosMixin — منطق إدارة السيناريوهات في الذاكرة
(للمنتجات الجديدة التي لم تُحفظ بعد).

مُستخرج من bom_scenarios_panel.py لتقليل الحجم وتوضيح المسؤوليات.
يُستخدم فقط من _BomScenariosPanel.

[Fix] استخدام مفتاح ترجمة بدل النص المباشر لاسم السيناريو الافتراضي
      (default_scenario_initial_name) — لا نص مكتوب مباشرة في الكود.
"""

from ui.widgets.core.i18n import tr


class MemoryScenariosMixin:
    """
    Mixin يضيف منطق السيناريوهات في الذاكرة (in-memory mode).

    يفترض وجود:
      - self._scenarios  : list[dict]
      - self._current_id : int | None
      - self._in_memory  : bool
      - self._item_id    : int | None
      - self._rebuild_combo()
      - self._sync_current()
      - self.scenario_changed signal
    """

    _NEXT_TEMP_ID = -1

    def _next_temp_id(self) -> int:
        """يولّد ID مؤقت سالب فريد."""
        MemoryScenariosMixin._NEXT_TEMP_ID -= 1
        return MemoryScenariosMixin._NEXT_TEMP_ID

    def _init_memory_scenario(self):
        """يُنشئ سيناريو افتراضي في الذاكرة للمنتجات الجديدة."""
        self._in_memory  = True
        self._item_id    = None
        temp_id = self._next_temp_id()
        self._scenarios  = [{"id": temp_id, "name": tr("default_scenario_initial_name"), "is_default": True}]
        self._current_id = temp_id
        self._rebuild_combo()
        self._sync_current()

    def get_memory_scenarios(self) -> list:
        """
        يرجع السيناريوهات المحفوظة في الذاكرة.
        يُستدعى من _FormPanel عند الحفظ لكتابة السيناريوهات في DB.
        """
        return list(self._scenarios)

    def get_current_memory_index(self) -> int:
        """يرجع index السيناريو الحالي في قايمة الذاكرة."""
        for i, sc in enumerate(self._scenarios):
            if sc["id"] == self._current_id:
                return i
        return 0

    def switch_to_db_mode(self, item_id: int, current_scenario_index: int = 0):
        """
        التحويل من in-memory mode إلى DB mode بعد حفظ المنتج.
        """
        self._in_memory  = False
        self._item_id    = item_id
        self._scenarios  = []
        self._current_id = None
        self._reload()

        if 0 <= current_scenario_index < len(self._scenarios):
            target_sc = self._scenarios[current_scenario_index]
            self._current_id = target_sc["id"]
            self._rebuild_combo()
            self._sync_current()

    # ── CRUD في الذاكرة ───────────────────────────────────

    def _memory_set_default(self, scenario_id: int):
        for sc in self._scenarios:
            sc["is_default"] = (sc["id"] == scenario_id)
        self._rebuild_combo()
        self._sync_current()

    def _memory_rename(self, scenario_id: int, name: str):
        for sc in self._scenarios:
            if sc["id"] == scenario_id:
                sc["name"] = name
                break
        self._rebuild_combo()
        self._sync_current()

    def _memory_clone(self, from_id: int, name: str) -> int:
        """يضيف سيناريو جديد مرتبط بمصدره للنسخ."""
        new_id = self._next_temp_id()
        self._scenarios.append({
            "id":           new_id,
            "name":         name,
            "is_default":   False,
            "_cloned_from": from_id,
        })
        return new_id

    def _memory_add_new(self, name: str) -> int:
        """يضيف سيناريو جديد فارغ في الذاكرة."""
        new_id = self._next_temp_id()
        self._scenarios.append({
            "id":         new_id,
            "name":       name,
            "is_default": False,
        })
        return new_id

    def _memory_delete(self, scenario_id: int) -> bool:
        """
        يحذف سيناريو من الذاكرة.
        يرجع True لو نجح، False لو كان آخر سيناريو.
        """
        if len(self._scenarios) <= 1:
            return False

        was_default = False
        for sc in self._scenarios:
            if sc["id"] == scenario_id:
                was_default = sc["is_default"]
                break

        self._scenarios = [sc for sc in self._scenarios if sc["id"] != scenario_id]

        if was_default and self._scenarios:
            self._scenarios[0]["is_default"] = True

        self._current_id = self._scenarios[0]["id"] if self._scenarios else None
        return True
