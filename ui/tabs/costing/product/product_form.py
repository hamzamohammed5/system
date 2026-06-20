"""
ui/tabs/costing/product/product_form.py
========================================
_FormPanel — فورم إضافة / تعديل المنتج.

[Fix #1] توحيد import LiveConnMixin: ui.widgets.core.conn
[Fix #3] استخدام emit_company_data_changed بدل bus.data_changed.emit()
[Fix C1] استبدال "منتج جديد" hardcoded بـ tr("new_product")
[Fix #9] استبدال db imports بـ services
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PyQt5.QtCore    import Qt, QTimer

from services.costing.scenario_service import ScenarioService
from services.costing.product_service  import ProductService
from services.shared.item_service      import ItemService

from ui.widgets.core.conn    import LiveConnMixin
from ui.widgets.core.events  import emit_company_data_changed
from ui.widgets.core.i18n    import tr

from .form._header_bar   import _FormHeaderBar
from .form._rows_manager import _RowsManager
from .form._save_logic   import _SaveLogic

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui.widgets.components.component_row.widget import ComponentRow


class _FormPanel(QWidget, LiveConnMixin):
    def __init__(self, conn, product_type: str, catalog_fn, parent=None):
        super().__init__(parent)
        self.conn         = conn
        self.product_type = product_type
        self._catalog_fn  = catalog_fn
        self._editing_id  = None
        self.is_editing   = False
        self._scope       = product_type
        self._current_scenario_id = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._header = _FormHeaderBar(self._live_conn(), scope=self._scope)
        self._header.add_row_clicked.connect(lambda: self._add_row())
        self._header.save_clicked.connect(self.save)
        self._header.cancel_clicked.connect(self._do_cancel)
        self._header.scenario_changed.connect(self._on_scenario_changed)
        root.addWidget(self._header)

        self._rows = _RowsManager(self._catalog_fn)
        root.addWidget(self._rows, stretch=1)

        self._saver = _SaveLogic(conn_fn=self._live_conn)

        self._add_row()

    # ── Shorthands للـ header ─────────────────────────────

    @property
    def rows_layout(self):
        return self._rows.rows_layout

    @property
    def lbl_mode(self):
        return self._header.lbl_mode

    # ══════════════════════════════════════════════════════
    # صفوف المكونات
    # ══════════════════════════════════════════════════════

    def _add_row(self, child_type: str = "raw", child_id=None,
                 qty: float = 1.0, orphan_name: str = None,
                 waste_pct: float = 0.0, variant_id: int = None,
                 machine_op_row_id: int = None) -> "ComponentRow":
        return self._rows.add_row(
            child_type=child_type, child_id=child_id, qty=qty,
            orphan_name=orphan_name, waste_pct=waste_pct,
            variant_id=variant_id, machine_op_row_id=machine_op_row_id,
        )

    def _remove_row(self, widget):
        self._rows._remove_row(widget)

    def collect_rows(self):
        return self._rows.collect_rows()

    def clear_rows(self):
        self._rows.clear_rows()

    # ══════════════════════════════════════════════════════
    # تحميل المنتج للتعديل
    # ══════════════════════════════════════════════════════

    def load_product(self, pid: int):
        try:
            conn = self._live_conn()
            item = ItemService(conn).get(pid)
        except Exception:
            return
        if not item:
            return

        self.clear_rows()
        self._header.product_name = item.name
        self._header.set_category(item.category_id)
        self._header.scenarios_panel.load_item(pid)

        try:
            svc = ScenarioService(conn)
            sc  = svc.get_default(pid)
            sc_id = sc.id if sc else svc.ensure_default(pid)
        except Exception:
            sc_id = None

        self._current_scenario_id = sc_id
        if sc_id:
            self._load_bom_for_scenario(pid, sc_id)

        try:
            orphan_count = len(ProductService(conn).get_orphan_components(pid))
        except Exception:
            orphan_count = 0

        label = (
            tr("editing_product_orphans_label").format(name=item.name, count=orphan_count)
            if orphan_count else tr("editing_product_label").format(name=item.name)
        )
        self.enter_edit_mode(pid, label)
        self._header.inp_name.setFocus()

    def _load_bom_for_scenario(self, pid: int, scenario_id: int):
        self.clear_rows()
        try:
            conn = self._live_conn()
        except Exception:
            self._add_row()
            return

        try:
            orphans    = ProductService(conn).get_orphan_components(pid)
            orphan_map = {(o.child_type, o.child_id): getattr(o, "name", None)
                          for o in orphans}
        except Exception:
            orphan_map = {}

        try:
            svc      = ScenarioService(conn)
            bom_rows = svc.get_bom(scenario_id)
        except Exception:
            bom_rows = []

        for row_data in (bom_rows or []):
            if hasattr(row_data, "child_type"):
                child_type        = row_data.child_type
                child_id          = row_data.child_id
                qty               = row_data.qty
                waste_pct         = float(row_data.waste_pct or 0.0)
                variant_id        = row_data.variant_id
                machine_op_row_id = row_data.machine_op_row_id
            else:
                child_type        = row_data["child_type"]
                child_id          = row_data["child_id"]
                qty               = row_data["qty"]
                waste_pct         = float(row_data.get("waste_pct") or 0.0)
                variant_id        = row_data.get("variant_id")
                machine_op_row_id = row_data.get("machine_op_row_id")

            o_name = orphan_map.get((child_type, child_id))

            component_row = self._add_row(
                child_type=child_type, child_id=child_id, qty=qty,
                orphan_name=o_name, waste_pct=waste_pct,
                variant_id=variant_id, machine_op_row_id=machine_op_row_id,
            )

            if child_type == "machine_op" and child_id is not None:
                component_row.expose_load_op_rows(child_id, machine_op_row_id)

        if not bom_rows:
            self._add_row()

    def _on_scenario_changed(self, scenario_id: int):
        if self._editing_id is None:
            return
        self._current_scenario_id = scenario_id
        self._load_bom_for_scenario(self._editing_id, scenario_id)

    # ══════════════════════════════════════════════════════
    # Reset
    # ══════════════════════════════════════════════════════

    def reset(self):
        self._header.reset()
        self.clear_rows()
        self._add_row()
        self._current_scenario_id = None
        # [Fix C1] بدل "منتج جديد" hardcoded
        self.exit_edit_mode(tr("new_product"))

    # ══════════════════════════════════════════════════════
    # حفظ
    # ══════════════════════════════════════════════════════

    def save(self):
        pid = self._saver.save(
            is_editing=self.is_editing,
            editing_id=self._editing_id,
            name=self._header.product_name,
            product_type=self.product_type,
            category_id=self._header.category_id,
            current_scenario_id=self._current_scenario_id,
            rows=self.collect_rows(),
            scenarios_panel=self._header.scenarios_panel,
            parent_widget=self,
        )
        if pid is not None:
            self.reset()
            QTimer.singleShot(0, emit_company_data_changed)

    # ══════════════════════════════════════════════════════
    # وضع التعديل
    # ══════════════════════════════════════════════════════

    def enter_edit_mode(self, pid, label: str = ""):
        self._editing_id = pid
        self.is_editing  = True
        self._header.enter_edit_mode(label)

    def exit_edit_mode(self, label: str = ""):
        self._editing_id = None
        self.is_editing  = False
        # [Fix C1] بدل "منتج جديد" hardcoded
        self._header.exit_edit_mode(label or tr("new_product"))

    def _do_cancel(self):
        self.reset()