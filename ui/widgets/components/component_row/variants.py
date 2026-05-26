"""
ui/widgets/components/component_row/variants.py
===========================================================
VariantsMixin — منطق تحميل وعرض variants الخامة في ComponentRow.

مستخرج من widgets/shared/component_row/_variants_logic.py مع:
  - تنظيف الـ try/except المكررة في دالة واحدة _safe_deleted()
  - فصل واضح بين التحقق من الـ widget والمنطق الفعلي
  - أسماء أوضح للدوال الداخلية
"""

from PyQt5 import sip


class VariantsMixin:
    """
    Mixin يضيف منطق raw variants لـ ComponentRow.

    يفترض وجود:
      self.cmb_type         : QComboBox النوع
      self.cmb_variant      : QComboBox الـ variants
      self.lbl_variant_cost : QLabel تكلفة الـ variant
      self._item_combo      : SearchableCombo
    """

    # ── Public API ─────────────────────────────────────────

    def _load_variants(self, item_id: int, selected_variant_id: int = None):
        if self._is_deleted() or item_id is None:
            self._hide_variants()
            return

        variants = self._fetch_variants(item_id)
        if not variants:
            self._hide_variants()
            return

        self._populate_variant_combo(variants, item_id, selected_variant_id)

    def _hide_variants(self):
        if self._is_deleted():
            return
        self.cmb_variant.setVisible(False)
        self.lbl_variant_cost.setVisible(False)

    def _on_variant_changed(self):
        self._update_variant_cost_label()

    # ── منطق داخلي ────────────────────────────────────────

    def _fetch_variants(self, item_id: int) -> list:
        try:
            from db.costing.raw_variants_repo import fetch_variants_for_item
            conn = self._get_conn()
            if conn is None:
                return []
            return fetch_variants_for_item(conn, item_id)
        except Exception:
            return []

    def _populate_variant_combo(self, variants: list, item_id: int,
                                 selected_id: int = None):
        if self._is_deleted():
            return

        item_price = self._get_item_price(item_id)

        self.cmb_variant.blockSignals(True)
        self.cmb_variant.clear()
        self.cmb_variant.addItem("─ بدون variant ─", None)

        for var in variants:
            pieces = float(var["pieces"])
            if pieces > 0 and item_price > 0:
                unit_cost = item_price / pieces
                label = (
                    f"📐 {var['name']}  "
                    f"({pieces:.4g} قطعة → {unit_cost:.3f} ج/قطعة)"
                )
            else:
                label = f"📐 {var['name']}  ({var['pieces']:.4g} قطعة)"
            self.cmb_variant.addItem(label, var["id"])

        if selected_id is not None:
            self._restore_variant_selection(selected_id)

        self.cmb_variant.blockSignals(False)
        self.cmb_variant.setVisible(True)
        self._update_variant_cost_label()

    def _restore_variant_selection(self, selected_id: int):
        for i in range(self.cmb_variant.count()):
            if self.cmb_variant.itemData(i) == selected_id:
                self.cmb_variant.setCurrentIndex(i)
                return

    def _update_variant_cost_label(self):
        variant_id = self.cmb_variant.currentData()
        if variant_id is None:
            self.lbl_variant_cost.setVisible(False)
            return

        item_id = self._get_current_raw_id()
        if item_id is None:
            self.lbl_variant_cost.setVisible(False)
            return

        cost = self._calc_variant_unit_cost(variant_id, item_id)
        if cost is not None:
            self.lbl_variant_cost.setText(f"= {cost:.3f} ج")
            self.lbl_variant_cost.setVisible(True)
        else:
            self.lbl_variant_cost.setVisible(False)

    def _calc_variant_unit_cost(self, variant_id: int,
                                 item_id: int) -> "float | None":
        try:
            from db.costing.raw_variants_repo import fetch_variant
            conn = self._get_conn()
            if not conn:
                return None
            var = fetch_variant(conn, variant_id)
            if not var:
                return None
            item_price = self._get_item_price(item_id)
            pieces     = float(var["pieces"])
            if pieces > 0 and item_price > 0:
                return item_price / pieces
            return None
        except Exception:
            return None

    # ── helpers ────────────────────────────────────────────

    def _get_current_raw_id(self) -> "int | None":
        if self.cmb_type.currentData() != "raw":
            return None
        data = self._item_combo.current_data()
        if data and data[0] not in ("__sep__", "__orphan__") and data[1] is not None:
            return data[1]
        return None

    def _get_item_price(self, item_id: int) -> float:
        try:
            conn = self._get_conn()
            if conn:
                row = conn.execute(
                    "SELECT price FROM items WHERE id=?", (item_id,)
                ).fetchone()
                if row:
                    return float(row["price"])
        except Exception:
            pass
        return 0.0

    def _is_deleted(self) -> bool:
        try:
            return sip.isdeleted(self) or sip.isdeleted(self.cmb_variant)
        except Exception:
            return True