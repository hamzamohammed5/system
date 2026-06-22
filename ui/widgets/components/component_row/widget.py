"""
ui/widgets/components/component_row/widget.py
=========================================================
ComponentRow — صف مكوّن واحد في BOM.

[إصلاح 6] _on_type_changed: إضافة إخفاء lbl_variant_cost عند تغيير النوع.
  المشكلة: عند تغيير النوع من "raw" لـ "semi" أو غيره، كانت _hide_variants()
  تُخفي cmb_variant لكن تترك lbl_variant_cost ظاهراً مع تكلفة الخامة القديمة.
  الحل: _hide_variants() الموجودة في VariantsMixin تُخفي كلاهما بالفعل.
  لكن المشكلة أن _on_type_changed لا تستدعيها في الترتيب الصحيح.
  التأكد أن lbl_variant_cost.setVisible(False) يُستدعى صراحةً.

[WidgetMixin] استبدال weakref وربط bus يدوي بـ WidgetMixin._init_widget_mixin.
  الـ _init_widget_mixin تُستدعى عبر QTimer.singleShot(0) للحفاظ على التأجيل الأصلي.

باقي التغييرات من النسخة الأصلية محفوظة كما هي.
"""

import weakref
from dataclasses import dataclass, field

from PyQt5 import sip
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal, QTimer

from ui.widgets.utils.searchable_combo import (
    SearchableCombo, build_grouped_items,
)
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.widgets.core.i18n import tr
from ui.constants import COMPONENT_ROW_LOAD_DELAY

from .ui      import (
    build_row_ui, update_waste_style,
    COMPONENT_TYPES, STYLE_NORMAL, get_orphan_style,
)
from .op_rows  import OpRowsMixin
from .variants import VariantsMixin


# ── Orphan state ───────────────────────────────────────────

@dataclass
class _OrphanState:
    active  : bool = False
    item_id : "int | None"  = None
    type_   : "str | None"  = None
    name    : "str | None"  = None

    def clear(self):
        self.active  = False
        self.item_id = None
        self.type_   = None
        self.name    = None

    def display(self) -> str:
        name_part = tr('component_row_orphan_name_part').format(name=self.name) if self.name else ""
        return tr('component_row_orphan_display').format(
            name_part=name_part, item_id=self.item_id
        )

    def tooltip(self) -> str:
        name_part = tr('component_row_orphan_name_part').format(name=self.name) if self.name else ""
        return tr('component_row_orphan_tooltip').format(
            type_=self.type_, name_part=name_part, item_id=self.item_id
        )


# ── ComponentRow ───────────────────────────────────────────

class ComponentRow(QWidget, OpRowsMixin, VariantsMixin, WidgetMixin):
    """
    صف مكوّن واحد في BOM مع:
      - اختيار النوع (خامة / نصف مصنع / عمالة / تشغيل)
      - بحث في العناصر
      - كمية + هادر
      - variants للخامات
      - صفوف العملية لعمليات التشغيل

    [WidgetMixin] ربط company_data_changed عبر _init_widget_mixin بدل weakref يدوي.
    [E-03] refresh_cost(): يُحدِّث تكلفة الخامة عند تغيير السعر.
    [إصلاح 6] _on_type_changed: يُخفي lbl_variant_cost صراحةً عند تغيير النوع.
    """

    removed = pyqtSignal(QWidget)

    def __init__(self, catalog_fn,
                 child_type: str = "raw",
                 child_id=None,
                 qty: float = 1.0,
                 waste_pct: float = 0.0,
                 raw_total_qty: float = None,
                 show_total_qty: bool = False,
                 variant_id: int = None,
                 machine_op_row_id: int = None,
                 parent=None):
        super().__init__(parent)

        # ── state ──────────────────────────────────────────
        self._catalog_fn     = catalog_fn
        self._show_total_qty = show_total_qty
        self._orphan         = _OrphanState()
        self._conn_cache     = None

        # pinned state (يُحفظ عند التنقل بين الأنواع)
        self._pinned_type      = child_type
        self._pinned_id        = child_id
        self._pinned_total_qty = raw_total_qty
        self._pinned_variant   = variant_id

        # op_rows state
        self._pinned_op_row_id       = machine_op_row_id
        self._init_machine_op_row_id = machine_op_row_id
        self._init_child_type        = child_type
        self._init_child_id          = child_id
        self._skip_timer_load        = False

        # ── UI ─────────────────────────────────────────────
        build_row_ui(
            self, child_type, child_id, qty,
            raw_total_qty, waste_pct,
            variant_id, machine_op_row_id, show_total_qty,
        )

        # ── إعداد أولي ─────────────────────────────────────
        self._fill_items(child_type, selected_id=child_id)
        self._update_total_qty_visibility(child_type)
        self.cmb_type.currentIndexChanged.connect(self._on_type_changed)

        # ── QTimers للتحميل المؤجل ──────────────────────────
        self._schedule_deferred_loads(child_type, child_id, variant_id, machine_op_row_id)
        QTimer.singleShot(
            0,
            lambda: self._init_widget_mixin(theme=False, font=False, lang=True, data=True),
        )

    # ── Shared deleted-check ───────────────────────────────

    def _is_widget_deleted(self, *widgets) -> bool:
        """
        يتحقق إذا كان هذا الـ widget أو أي من الـ widgets المعطاة
        قد حُذف من Qt. تُستخدم من OpRowsMixin و VariantsMixin.
        """
        try:
            if sip.isdeleted(self):
                return True
            return any(sip.isdeleted(w) for w in widgets)
        except Exception:
            return True

    # ── Language refresh ────────────────────────────────────

    def _refresh_lang(self, *_):
        """
        [i18n] يحدّث كل النصوص المعروضة عند تغيير اللغة:
          - tooltip/label الـ orphan لو كان نشطاً
          - تكلفة الخامة وتولتيبها
          - يفوّض لـ OpRowsMixin/VariantsMixin لتحديث نصوصهم الداخلية
            (الكومبوهات وlabels التكلفة) لأنها تستخدم tr() كذلك.
        """
        if self._is_widget_deleted():
            return
        if self._orphan.active:
            self.setToolTip(self._orphan.tooltip())
            self._item_combo.block_signals(True)
            self._item_combo.set_item_text(0, self._orphan.display())
            self._item_combo.block_signals(False)
        self._refresh_cost_label()
        if hasattr(self, "_update_op_row_cost_label"):
            self._update_op_row_cost_label()
        if hasattr(self, "_update_variant_cost_label"):
            self._update_variant_cost_label()
        if hasattr(self, "_populate_op_row_combo") and self.cmb_type.currentData() == "machine_op":
            self._ensure_machine_op_rows()
        if hasattr(self, "_load_variants") and self.cmb_type.currentData() == "raw":
            data = self._item_combo.current_data()
            if data and data[0] not in ("__sep__", "__orphan__") and data[1] is not None:
                self._load_variants(data[1], selected_variant_id=self.get_variant_id())

    # ── Connection ─────────────────────────────────────────

    def _get_conn(self):
        """
        يرجع connection حي مع cache.

        الإصلاح (Phase 5): حذف SELECT 1 من الـ cache check.
        الـ SELECT 1 كان بيتنفذ في كل استدعاء حتى لو الـ connection سليم،
        وده overhead غير ضروري لأن ComponentRow بيتستدعى كتير جداً.
        الحل: ثق في الـ cache مباشرة — لو الـ connection مات،
        أول query حقيقية هتفشل وبيعمل retry تلقائي عن طريق get_connection().
        """
        if self._conn_cache is not None:
            return self._conn_cache
        try:
            from db.shared.connection import get_connection
            self._conn_cache = get_connection()
            return self._conn_cache
        except Exception:
            return None

    def _refresh_data(self, company_id=None):
        self._conn_cache = None
        QTimer.singleShot(0, self._on_catalog_changed)

    # ── Deferred loads ─────────────────────────────────────

    def _schedule_deferred_loads(self, child_type, child_id,
                                  variant_id, machine_op_row_id):
        if child_type == "raw" and child_id is not None:
            weak = weakref.ref(self)
            cid, vid = child_id, variant_id

            def _timer_variants():
                s = weak()
                if s is None or s._is_widget_deleted():
                    return
                s._load_variants(cid, selected_variant_id=vid)

            QTimer.singleShot(COMPONENT_ROW_LOAD_DELAY, _timer_variants)

        if child_type == "machine_op" and child_id is not None:
            weak = weakref.ref(self)
            op_id, row_id = child_id, machine_op_row_id

            def _timer_load():
                s = weak()
                if s is None or s._is_widget_deleted():
                    return
                s._load_op_rows(op_id, row_id)

            QTimer.singleShot(COMPONENT_ROW_LOAD_DELAY, _timer_load)

    # ── Waste ──────────────────────────────────────────────

    def _on_waste_changed(self, val: float):
        update_waste_style(self, val)

    # ── Total qty visibility ───────────────────────────────

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
        child_id = data[1]
        for entry in self._catalog_fn().get("raw", []):
            if entry[0] == child_id:
                tq = entry[4] if len(entry) > 4 else None
                if tq is not None:
                    self.total_qty_edit.setText(str(tq))
                else:
                    self.total_qty_edit.clear()
                return
        self.total_qty_edit.clear()

    # ── Orphan state ───────────────────────────────────────

    def _mark_orphan(self, child_type: str, child_id: int):
        self._orphan.active  = True
        self._orphan.item_id = child_id
        self._orphan.type_   = child_type
        self.setStyleSheet(get_orphan_style())
        self.setToolTip(self._orphan.tooltip())

    def _clear_orphan(self):
        self._orphan.clear()
        self.setStyleSheet(STYLE_NORMAL)
        self.setToolTip("")

    def set_orphan_name(self, name: "str | None"):
        if not self._orphan.active:
            return
        self._orphan.name = name
        self._item_combo.block_signals(True)
        self._item_combo.set_item_text(0, self._orphan.display())
        self._item_combo.block_signals(False)

    def is_orphan(self) -> bool:
        return self._orphan.active

    # ── Catalog / items ────────────────────────────────────

    def _fill_items(self, child_type: str, selected_id=None):
        catalog  = self._catalog_fn()
        items    = catalog.get(child_type, [])
        item_ids = {entry[0] for entry in items}

        grouped = []
        if selected_id is not None and selected_id not in item_ids:
            self._mark_orphan(child_type, selected_id)
            grouped.append((self._orphan.display(), ("__orphan__", selected_id), False))
        else:
            self._clear_orphan()

        grouped += build_grouped_items(items)
        self._item_combo.populate(grouped)

        if selected_id is not None:
            self._restore_item_selection(selected_id)
        else:
            self._item_combo._select_first_real()

        if child_type == "machine_op":
            weak = weakref.ref(self)
            QTimer.singleShot(
                0,
                lambda: (s := weak()) and s._ensure_machine_op_rows(),
            )

    def _restore_item_selection(self, selected_id: int):
        if self._orphan.active and self._orphan.item_id == selected_id:
            self._item_combo.cmb.setCurrentIndex(0)
            return
        for i in range(self._item_combo.count()):
            d = self._item_combo.item_data(i)
            if d and d[0] not in ("__sep__", "__orphan__") and d[1] == selected_id:
                self._item_combo.cmb.setCurrentIndex(i)
                return

    def refresh_catalog(self, _new_catalog: dict = None):
        self._refresh_items()

    def _refresh_items(self):
        child_type  = self._pinned_type
        selected_id = self._orphan.item_id if self._orphan.active else self._pinned_id
        self._fill_items(child_type, selected_id=selected_id)

    # ── Cost refresh [E-03] ────────────────────────────────

    def _refresh_cost_label(self):
        """
        [E-03] يُحدِّث عرض تكلفة الخامة (lbl_variant_cost) من الـ catalog الجديد.
        """
        if self._pinned_type != "raw":
            return
        if self._orphan.active:
            return

        cost_label = getattr(self, "lbl_variant_cost", None)
        if cost_label is None:
            return

        child_id = self._pinned_id
        if child_id is None:
            return

        catalog   = self._catalog_fn()
        raw_items = catalog.get("raw", [])

        for entry in raw_items:
            if entry[0] != child_id:
                continue

            price     = 0.0
            total_qty = None

            try:
                if len(entry) >= 4:
                    val2 = entry[2]
                    if isinstance(val2, (int, float)):
                        price = float(val2)
                        val3  = entry[3]
                        if isinstance(val3, (int, float)):
                            total_qty = float(val3)
            except (IndexError, TypeError, ValueError):
                pass

            if total_qty is not None and total_qty > 0:
                unit_cost = price / total_qty
            else:
                unit_cost = price

            try:
                if hasattr(cost_label, "setText"):
                    cost_label.setText(f"{unit_cost:,.4g}")
                    total_qty_line = (
                        tr('component_row_total_qty_line').format(total_qty=total_qty)
                        if total_qty else ""
                    )
                    cost_label.setToolTip(
                        tr('component_row_cost_tooltip').format(
                            unit_cost=f"{unit_cost:,.4f}",
                            price=f"{price:,.4f}",
                            total_qty_line=total_qty_line,
                        )
                    )
            except Exception:
                pass

            return

    # ── Signal handlers ────────────────────────────────────

    def _on_item_selected(self, data):
        if not (data and data[0] not in ("__sep__", "__orphan__") and data[1] is not None):
            return

        self._pinned_id = data[1]
        if self._orphan.active:
            self._clear_orphan()

        child_type = self.cmb_type.currentData()

        if child_type == "raw":
            self._auto_fill_total_qty()
            item_id = data[1]
            weak    = weakref.ref(self)
            QTimer.singleShot(COMPONENT_ROW_LOAD_DELAY, lambda: (s := weak()) and s._load_variants(item_id))
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
        valid_types = {k for k, _ in COMPONENT_TYPES}
        if self._pinned_type not in valid_types:
            from_combo = self.cmb_type.currentData()
            if from_combo in valid_types:
                self._pinned_type = from_combo
            else:
                return
        if not self._orphan.active:
            data = self._item_combo.current_data()
            if data and data[0] not in ("__sep__", "__orphan__"):
                self._pinned_id = data[1]
        self._refresh_items()
        self._refresh_cost_label()

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
            # [إصلاح 6] إخفاء lbl_variant_cost صراحةً عند تغيير النوع عن "raw"
            # _hide_variants() تُخفي cmb_variant لكن lbl_variant_cost قد يبقى ظاهراً
            # لو _hide_variants لم تُستدعَ بعد (مثلاً لو لا يوجد variants محملة)
            self._hide_variants()
            cost_label = getattr(self, "lbl_variant_cost", None)
            if cost_label is not None:
                cost_label.setVisible(False)
        if new_type != "machine_op":
            self._hide_op_rows()

    # ── Public getters ─────────────────────────────────────

    def get_values(self) -> "tuple | None":
        """يرجع (child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id)"""
        try:
            data = self._item_combo.current_data()
            qty  = float(self.qty_edit.text())
            if data is None:
                return None
            kind, child_id = data
            if kind in ("__orphan__", "__sep__") or child_id is None:
                return None

            child_type        = self.cmb_type.currentData()
            waste_pct         = self.waste_spin.value()
            variant_id        = self._read_variant_id(child_type)
            machine_op_row_id = self._read_op_row_id(child_type)

            return child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id

        except (ValueError, TypeError):
            return None

    def get_waste_pct(self) -> float:
        return self.waste_spin.value()

    def get_variant_id(self) -> "int | None":
        return self._read_variant_id(self.cmb_type.currentData())

    def get_machine_op_row_id(self) -> "int | None":
        return self._read_op_row_id(self.cmb_type.currentData())

    def _read_variant_id(self, child_type: str) -> "int | None":
        if child_type == "raw" and self.cmb_variant.isVisible():
            return self.cmb_variant.currentData()
        return None

    def _read_op_row_id(self, child_type: str) -> "int | None":
        if child_type != "machine_op":
            return None
        current = self.cmb_op_row.currentData()
        if current is not None:
            if current != self._pinned_op_row_id:
                self._pinned_op_row_id = current
            return current
        return self._pinned_op_row_id

    @property
    def cmb_item(self):
        return self._item_combo.cmb