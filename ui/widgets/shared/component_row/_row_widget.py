"""
ui/widgets/shared/component_row/_row_widget.py
====================================================
ComponentRow — صف مكوّن واحد في BOM.

[تقسيم v2]:
  - _row_ui.py        → بناء الواجهة
  - _op_rows_logic.py → منطق machine_op rows
  - _variants_logic.py → منطق raw variants
"""

import weakref
from PyQt5 import sip

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal, QTimer

from ui.widgets.shared.searchable_combo import _build_grouped_items
from ui.events import bus

from ._row_ui      import build_row_ui, _update_waste_style, _STYLE_NORMAL, _STYLE_ORPHAN
from ._op_rows_logic   import OpRowsMixin
from ._variants_logic  import VariantsMixin


class ComponentRow(QWidget, OpRowsMixin, VariantsMixin):
    """
    صف مكوّن واحد في BOM مع:
      - اختيار النوع (خامة / نصف مصنع / عمالة / تشغيل)
      - بحث في العناصر
      - كمية + هادر
      - variants للخامات
      - صفوف العملية لعمليات التشغيل
    """

    removed = pyqtSignal(QWidget)

    def __init__(self, catalog_fn, child_type: str = "raw",
                 child_id=None, qty: float = 1.0,
                 waste_pct: float = 0.0,
                 raw_total_qty: float = None,
                 show_total_qty: bool = False,
                 variant_id: int = None,
                 machine_op_row_id: int = None,
                 parent=None):
        super().__init__(parent)
        self._catalog_fn     = catalog_fn
        self._show_total_qty = show_total_qty
        self._is_orphan      = False
        self._orphan_id      = None
        self._orphan_type    = None
        self._orphan_name    = None

        self._pinned_type      = child_type
        self._pinned_id        = child_id
        self._pinned_total_qty = raw_total_qty
        self._pinned_variant   = variant_id

        self._pinned_op_row_id       = machine_op_row_id
        self._init_machine_op_row_id = machine_op_row_id
        self._init_child_type        = child_type
        self._init_child_id          = child_id
        self._skip_timer_load        = False

        # بناء الواجهة من _row_ui.py
        build_row_ui(self, child_type, child_id, qty, raw_total_qty,
                     waste_pct, variant_id, machine_op_row_id, show_total_qty)

        self._fill_items(child_type, selected_id=child_id)
        self._update_total_qty_visibility(child_type)
        self.cmb_type.currentIndexChanged.connect(self._on_type_changed)

        # QTimers
        if child_type == "raw" and child_id is not None:
            _weak = weakref.ref(self)
            _cid, _vid = child_id, variant_id
            QTimer.singleShot(50, lambda: (s := _weak()) and s._load_variants(_cid, _vid))
        elif child_type == "machine_op" and child_id is not None:
            _weak   = weakref.ref(self)
            _op_id  = child_id
            _row_id = machine_op_row_id

            def _timer_load():
                s = _weak()
                if s is None or s._skip_timer_load:
                    return
                s._load_op_rows(_op_id, _row_id)

            QTimer.singleShot(50, _timer_load)

        QTimer.singleShot(0, self._connect_signal)

    def _connect_signal(self):
        bus.data_changed.connect(
            lambda: QTimer.singleShot(0, self._on_catalog_changed)
        )

    # ══════════════════════════════════════════════════════
    # مساعد Connection
    # ══════════════════════════════════════════════════════

    def _get_conn(self):
        try:
            from db.shared.connection import get_connection
            return get_connection()
        except Exception:
            return None

    def _get_current_machine_op_id(self):
        if self.cmb_type.currentData() != "machine_op":
            return None
        data = self._item_combo.current_data()
        if data and data[0] not in ("__sep__", "__orphan__") and data[1] is not None:
            return data[1]
        return None

    # ══════════════════════════════════════════════════════
    # الهادر
    # ══════════════════════════════════════════════════════

    def _on_waste_changed(self, val: float):
        _update_waste_style(self, val)

    # ══════════════════════════════════════════════════════
    # إظهار/إخفاء حقل الكمية الكلية
    # ══════════════════════════════════════════════════════

    def _update_total_qty_visibility(self, child_type: str):
        visible = (child_type == "raw") and self._show_total_qty
        self.total_qty_edit.setVisible(visible)
        self.lbl_total_qty.setVisible(visible)

    def _auto_fill_total_qty(self):
        if self.cmb_type.currentData() != "raw":
            return
        data = self._item_combo.current_data()
        if not data or data[0] in ("__sep__", "__orphan__") or data[1] is None:
            return
        child_id  = data[1]
        catalog   = self._catalog_fn()
        raw_items = catalog.get("raw", [])
        for entry in raw_items:
            if entry[0] == child_id:
                tq = entry[4] if len(entry) > 4 else None
                if tq is not None:
                    self.total_qty_edit.setText(str(tq))
                else:
                    self.total_qty_edit.clear()
                return
        self.total_qty_edit.clear()

    # ══════════════════════════════════════════════════════
    # Orphan state
    # ══════════════════════════════════════════════════════

    def set_orphan_name(self, name: str | None):
        if not self._is_orphan:
            return
        self._orphan_name = name
        display = self._orphan_display()
        self._item_combo.block_signals(True)
        self._item_combo.set_item_text(0, display)
        self._item_combo.block_signals(False)

    def _orphan_display(self) -> str:
        if self._orphan_name:
            return f"⚠️  {self._orphan_name}  (ID: {self._orphan_id})"
        return f"⚠️  محذوف  (ID: {self._orphan_id})"

    def is_orphan(self) -> bool:
        return self._is_orphan

    def _mark_orphan(self, child_type: str, child_id: int):
        self._is_orphan   = True
        self._orphan_id   = child_id
        self._orphan_type = child_type
        self.setStyleSheet(_STYLE_ORPHAN)
        name_part = f" «{self._orphan_name}»" if self._orphan_name else ""
        self.setToolTip(
            f"⚠️ هذا المكون ({child_type}{name_part} ID:{child_id}) "
            "تم حذفه من قاعدة البيانات.\n"
            "اختر بديلاً من القايمة أو احذف هذا الصف."
        )

    def _clear_orphan(self):
        self._is_orphan   = False
        self._orphan_id   = None
        self._orphan_type = None
        self._orphan_name = None
        self.setStyleSheet(_STYLE_NORMAL)
        self.setToolTip("")

    # ══════════════════════════════════════════════════════
    # ملء قايمة العناصر
    # ══════════════════════════════════════════════════════

    def _fill_items(self, child_type: str, selected_id=None):
        catalog  = self._catalog_fn()
        items    = catalog.get(child_type, [])
        item_ids = {entry[0] for entry in items}

        grouped = []
        if selected_id is not None and selected_id not in item_ids:
            self._mark_orphan(child_type, selected_id)
            display = self._orphan_display()
            grouped.append((display, ("__orphan__", selected_id), False))
        else:
            self._clear_orphan()

        grouped += _build_grouped_items(items)
        self._item_combo.populate(grouped)

        if selected_id is not None:
            if self._is_orphan and self._orphan_id == selected_id:
                self._item_combo.cmb.setCurrentIndex(0)
            else:
                for i in range(self._item_combo.count()):
                    d = self._item_combo.item_data(i)
                    if d and d[0] not in ("__sep__", "__orphan__") and d[1] == selected_id:
                        self._item_combo.cmb.setCurrentIndex(i)
                        break
        else:
            self._item_combo._select_first_real()

        if child_type == "machine_op":
            _weak = weakref.ref(self)
            QTimer.singleShot(0, lambda: (s := _weak()) and s._ensure_machine_op_rows())

    def refresh_catalog(self, _new_catalog: dict = None):
        self._refresh_items()

    # ══════════════════════════════════════════════════════
    # Signal handlers
    # ══════════════════════════════════════════════════════

    def _on_item_selected(self, data):
        if data and data[0] not in ("__sep__", "__orphan__") and data[1] is not None:
            self._pinned_id = data[1]
            if self._is_orphan:
                self._clear_orphan()
                self.setStyleSheet(_STYLE_NORMAL)

            child_type = self.cmb_type.currentData()

            if child_type == "raw":
                self._auto_fill_total_qty()
                item_id = data[1]
                weak_self = weakref.ref(self)
                QTimer.singleShot(50, lambda: (s := weak_self()) and s._load_variants(item_id))
                self._hide_op_rows()
            elif child_type == "machine_op":
                op_id = data[1]
                self._hide_op_rows()
                self._pinned_op_row_id       = None
                self._init_machine_op_row_id = None
                self._skip_timer_load        = False
                self._load_op_rows(op_id, None)
                self._hide_variants()
            else:
                self._hide_variants()
                self._hide_op_rows()

    def _on_catalog_changed(self):
        from ._row_ui import _TYPES as _VALID_TYPES
        valid_types = {k for k, _ in _VALID_TYPES}
        if self._pinned_type not in valid_types:
            from_combo = self.cmb_type.currentData()
            if from_combo in valid_types:
                self._pinned_type = from_combo
            else:
                return
        if not self._is_orphan:
            current_data = self._item_combo.current_data()
            if current_data and current_data[0] not in ("__sep__", "__orphan__"):
                self._pinned_id = current_data[1]
        self._refresh_items()

    def _refresh_items(self):
        child_type  = self._pinned_type
        selected_id = self._orphan_id if self._is_orphan else self._pinned_id
        self._fill_items(child_type, selected_id=selected_id)

    def _on_type_changed(self, _):
        new_type = self.cmb_type.currentData()
        if not isinstance(new_type, str):
            return
        self._pinned_type            = new_type
        self._pinned_id              = None
        self._pinned_variant         = None
        self._pinned_op_row_id       = None
        self._init_machine_op_row_id = None
        self._skip_timer_load        = False
        self._clear_orphan()
        self._fill_items(new_type, selected_id=None)
        self._update_total_qty_visibility(new_type)
        if new_type != "raw":
            self.total_qty_edit.clear()
            self._hide_variants()
        if new_type != "machine_op":
            self._hide_op_rows()

    # ══════════════════════════════════════════════════════
    # get_values
    # ══════════════════════════════════════════════════════

    def get_values(self) -> tuple | None:
        """يرجع (child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id)"""
        try:
            data = self._item_combo.current_data()
            qty  = float(self.qty_edit.text())
            if data is None:
                return None
            kind, child_id = data
            if kind in ("__orphan__", "__sep__") or child_id is None:
                return None
            child_type = self.cmb_type.currentData()
            waste_pct  = self.waste_spin.value()

            variant_id = None
            if child_type == "raw" and self.cmb_variant.isVisible():
                variant_id = self.cmb_variant.currentData()

            machine_op_row_id = None
            if child_type == "machine_op":
                current = self.cmb_op_row.currentData()
                if current is not None:
                    machine_op_row_id = current
                    if current != self._pinned_op_row_id:
                        self._pinned_op_row_id = current
                else:
                    machine_op_row_id = self._pinned_op_row_id

            return child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id

        except (ValueError, TypeError):
            return None

    def get_waste_pct(self) -> float:
        return self.waste_spin.value()

    def get_variant_id(self):
        if self.cmb_type.currentData() == "raw" and self.cmb_variant.isVisible():
            return self.cmb_variant.currentData()
        return None

    def get_machine_op_row_id(self):
        if self.cmb_type.currentData() == "machine_op":
            current = self.cmb_op_row.currentData()
            if current is not None:
                return current
            return self._pinned_op_row_id
        return None

    @property
    def cmb_item(self):
        return self._item_combo.cmb