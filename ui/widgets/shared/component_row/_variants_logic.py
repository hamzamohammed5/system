"""
ui/tabs/costing/shared/component_row/_variants_logic.py
========================================================
منطق تحميل وعرض variants الخامة في ComponentRow.

مُستخرج من component_row.py لتقليل الحجم.
يُستخدم فقط من _row_widget.py.
"""

from PyQt5 import sip


class VariantsMixin:
    """
    Mixin يضيف منطق raw variants لـ ComponentRow.

    يفترض وجود:
      - self.cmb_type         : QComboBox النوع
      - self.cmb_variant      : QComboBox الـ variants
      - self.lbl_variant_cost : QLabel تكلفة الـ variant
      - self._item_combo      : _SearchableCombo
    """

    def _load_variants(self, item_id: int, selected_variant_id: int = None):
        try:
            if sip.isdeleted(self) or sip.isdeleted(self.cmb_variant):
                return
        except Exception:
            return

        if item_id is None:
            self._hide_variants()
            return

        try:
            from db.costing.raw_variants_repo import fetch_variants_for_item
            conn = self._get_conn()
            if conn is None:
                self._hide_variants()
                return
            variants = fetch_variants_for_item(conn, item_id)
        except Exception:
            self._hide_variants()
            return

        if not variants:
            self._hide_variants()
            return

        item_price = self._get_item_price(item_id)
        self.cmb_variant.blockSignals(True)
        self.cmb_variant.clear()
        self.cmb_variant.addItem("─ بدون variant ─", None)

        for var in variants:
            pieces = float(var["pieces"])
            if pieces > 0 and item_price > 0:
                unit_cost = item_price / pieces
                label = f"📐 {var['name']}  ({pieces:.4g} قطعة → {unit_cost:.3f} ج/قطعة)"
            else:
                label = f"📐 {var['name']}  ({var['pieces']:.4g} قطعة)"
            self.cmb_variant.addItem(label, var["id"])

        if selected_variant_id is not None:
            for i in range(self.cmb_variant.count()):
                if self.cmb_variant.itemData(i) == selected_variant_id:
                    self.cmb_variant.setCurrentIndex(i)
                    break

        self.cmb_variant.blockSignals(False)
        self.cmb_variant.setVisible(True)
        self._update_variant_cost_label()

    def _hide_variants(self):
        self.cmb_variant.setVisible(False)
        self.lbl_variant_cost.setVisible(False)

    def _on_variant_changed(self):
        self._update_variant_cost_label()

    def _update_variant_cost_label(self):
        variant_id = self.cmb_variant.currentData()
        if variant_id is None:
            self.lbl_variant_cost.setVisible(False)
            return
        item_id = self._get_current_raw_id()
        if item_id is None:
            self.lbl_variant_cost.setVisible(False)
            return
        try:
            from db.costing.raw_variants_repo import fetch_variant
            conn = self._get_conn()
            if not conn:
                self.lbl_variant_cost.setVisible(False)
                return
            var = fetch_variant(conn, variant_id)
            if not var:
                self.lbl_variant_cost.setVisible(False)
                return
            item_price = self._get_item_price(item_id)
            pieces = float(var["pieces"])
            if pieces > 0 and item_price > 0:
                unit_cost = item_price / pieces
                self.lbl_variant_cost.setText(f"= {unit_cost:.3f} ج")
                self.lbl_variant_cost.setVisible(True)
            else:
                self.lbl_variant_cost.setVisible(False)
        except Exception:
            self.lbl_variant_cost.setVisible(False)

    def _get_current_raw_id(self):
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