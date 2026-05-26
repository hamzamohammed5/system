"""
ui/widgets/components/component_row/op_rows.py
==========================================================
OpRowsMixin — منطق تحميل وعرض صفوف عمليات التشغيل في ComponentRow.

مستخرج من widgets/shared/component_row/_op_rows_logic.py مع:
  - دالة _is_deleted() مشتركة بدل تكرار try/except
  - _determine_target_id() لفصل منطق الأولوية
  - أسماء واضحة ومتسقة
"""

from PyQt5 import sip


class OpRowsMixin:
    """
    Mixin يضيف منطق machine_op_rows لـ ComponentRow.

    يفترض وجود:
      self.cmb_type               : QComboBox النوع
      self.cmb_op_row             : QComboBox صفوف العملية
      self._sub_row_widget        : QFrame الصف الفرعي
      self.lbl_op_row_cost        : QLabel تكلفة الصف
      self._pinned_op_row_id      : int | None
      self._init_machine_op_row_id: int | None
      self._skip_timer_load       : bool
      self._item_combo            : SearchableCombo
    """

    # ── Public API ─────────────────────────────────────────

    def expose_load_op_rows(self, op_id: int, selected_row_id: int = None):
        """
        يُستدعى من الخارج (product_form) عند تحميل سيناريو من DB.
        يعمل synchronously ويمنع QTimer من إعادة التحميل.
        """
        if selected_row_id is not None:
            self._pinned_op_row_id       = selected_row_id
            self._init_machine_op_row_id = selected_row_id
        self._skip_timer_load = True
        self._load_op_rows(op_id, selected_row_id)

    def _ensure_machine_op_rows(self):
        """يتحقق من النوع ولو كان machine_op يحمل الصفوف فوراً."""
        if self._is_op_row_deleted():
            return
        if self.cmb_type.currentData() != "machine_op":
            return

        data = self._item_combo.current_data()
        if not data or data[0] in ("__sep__", "__orphan__") or data[1] is None:
            return

        self._load_op_rows(data[1], self._pinned_op_row_id)

    def _hide_op_rows(self):
        if self._is_op_row_deleted():
            return
        self._sub_row_widget.setVisible(False)

    # ── منطق التحميل ──────────────────────────────────────

    def _load_op_rows(self, op_id: int, selected_row_id: int = None):
        """
        يملأ cmb_op_row بصفوف العملية ويختار الصف الصحيح.

        أولوية الاختيار:
          1. selected_row_id  (الأعلى)
          2. _init_machine_op_row_id
          3. _pinned_op_row_id
          4. الصف الأول (fallback)
        """
        if self._is_op_row_deleted() or op_id is None:
            self._hide_op_rows()
            return

        rows = self._fetch_op_rows(op_id)
        if not rows:
            self._hide_op_rows()
            return

        target_id = self._determine_target_id(selected_row_id)
        self._populate_op_row_combo(rows, target_id)
        self._sub_row_widget.setVisible(True)
        self._update_op_row_cost_label()

    def _fetch_op_rows(self, op_id: int) -> list:
        try:
            from db.costing.machine_op_rows_repo import fetch_op_rows
            conn = self._get_conn()
            if conn is None:
                return []
            return fetch_op_rows(conn, op_id)
        except Exception:
            return []

    def _determine_target_id(self, selected_row_id: int = None) -> "int | None":
        """يحدد الـ ID المستهدف حسب الأولوية."""
        return (
            selected_row_id
            or self._init_machine_op_row_id
            or self._pinned_op_row_id
        )

    def _populate_op_row_combo(self, rows: list, target_id: "int | None"):
        self.cmb_op_row.blockSignals(True)
        self.cmb_op_row.clear()

        for row in rows:
            cost  = self._calc_row_cost(row["id"])
            label = row["label"] or f"صف {row['id']}"
            display = (
                f"{label}  "
                f"({row['value']:.4g} ÷ {row['count']:.4g})"
                f"  ≈ {cost:.3f} ج"
            )
            self.cmb_op_row.addItem(display, row["id"])

        restored = self._restore_op_row_selection(target_id)
        if not restored and self.cmb_op_row.count() > 0:
            self.cmb_op_row.setCurrentIndex(0)

        current = self.cmb_op_row.currentData()
        if current is not None:
            self._pinned_op_row_id = current
            if self._init_machine_op_row_id is None:
                self._init_machine_op_row_id = current

        self.cmb_op_row.blockSignals(False)

    def _restore_op_row_selection(self, target_id: "int | None") -> bool:
        if target_id is None:
            return False
        for i in range(self.cmb_op_row.count()):
            if self.cmb_op_row.itemData(i) == target_id:
                self.cmb_op_row.setCurrentIndex(i)
                return True
        return False

    def _calc_row_cost(self, row_id: int) -> float:
        try:
            from db.costing.machine_op_rows_repo import calc_op_row_cost
            conn = self._get_conn()
            if conn:
                return calc_op_row_cost(conn, row_id)
        except Exception:
            pass
        return 0.0

    # ── Signal handlers ────────────────────────────────────

    def _on_op_row_changed(self, _index: int = 0):
        if self._is_op_row_deleted():
            return
        row_id = self.cmb_op_row.currentData()
        if row_id is not None:
            self._pinned_op_row_id       = row_id
            self._init_machine_op_row_id = row_id
        self._update_op_row_cost_label()

    def _update_op_row_cost_label(self):
        if self._is_op_row_deleted():
            return

        row_id = self.cmb_op_row.currentData() or self._pinned_op_row_id
        if row_id is None:
            self.lbl_op_row_cost.setText("")
            return

        # sync الـ pinned id
        if row_id != self._pinned_op_row_id:
            self._pinned_op_row_id = row_id

        cost = self._calc_row_cost(row_id)
        self.lbl_op_row_cost.setText(f"= {cost:.4f} ج/قطعة")

    def _get_current_machine_op_id(self) -> "int | None":
        if self.cmb_type.currentData() != "machine_op":
            return None
        data = self._item_combo.current_data()
        if data and data[0] not in ("__sep__", "__orphan__") and data[1] is not None:
            return data[1]
        return None

    # ── helper ─────────────────────────────────────────────

    def _is_op_row_deleted(self) -> bool:
        try:
            return (
                sip.isdeleted(self)
                or sip.isdeleted(self.cmb_op_row)
                or sip.isdeleted(self._sub_row_widget)
            )
        except Exception:
            return True