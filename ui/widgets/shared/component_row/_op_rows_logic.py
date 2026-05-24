"""
ui/tabs/costing/shared/component_row/_op_rows_logic.py
=======================================================
منطق تحميل وعرض صفوف عملية التشغيل (machine_op rows).

مُستخرج من component_row.py لتقليل الحجم وتسهيل الصيانة.
يُستخدم فقط من _row_widget.py.
"""

from PyQt5 import sip


class OpRowsMixin:
    """
    Mixin يضيف منطق machine_op_rows لـ ComponentRow.

    يفترض الـ mixin وجود:
      - self.cmb_type          : QComboBox النوع
      - self.cmb_op_row        : QComboBox صفوف العملية
      - self._sub_row_widget   : QFrame الـ sub row
      - self.lbl_op_row_cost   : QLabel تكلفة الصف
      - self._pinned_op_row_id : int | None
      - self._init_machine_op_row_id : int | None
      - self._skip_timer_load  : bool
      - self._item_combo       : _SearchableCombo
    """

    # ══════════════════════════════════════════════════════
    # expose_load_op_rows — يُستدعى من الخارج (product_form)
    # ══════════════════════════════════════════════════════

    def expose_load_op_rows(self, op_id: int, selected_row_id: int = None):
        """
        Method عامة تُستدعى من product_form عند تحميل سيناريو من DB.
        تعمل synchronously وتمنع QTimer من إعادة التحميل.
        """
        if selected_row_id is not None:
            self._pinned_op_row_id       = selected_row_id
            self._init_machine_op_row_id = selected_row_id
        self._skip_timer_load = True
        self._load_op_rows(op_id, selected_row_id)

    # ══════════════════════════════════════════════════════
    # _ensure_machine_op_rows — يضمن ظهور الصفوف فور الاختيار
    # ══════════════════════════════════════════════════════

    def _ensure_machine_op_rows(self):
        """
        يتحقق من النوع الحالي ولو كان machine_op يحمل الصفوف فوراً.
        يُستدعى بعد _fill_items مباشرة لضمان الظهور التلقائي.
        """
        try:
            if sip.isdeleted(self):
                return
        except Exception:
            return

        if self.cmb_type.currentData() != "machine_op":
            return

        data = self._item_combo.current_data()
        if not data or data[0] in ("__sep__", "__orphan__") or data[1] is None:
            return

        op_id = data[1]
        self._load_op_rows(op_id, self._pinned_op_row_id)

    # ══════════════════════════════════════════════════════
    # _load_op_rows — التحميل الفعلي
    # ══════════════════════════════════════════════════════

    def _load_op_rows(self, op_id: int, selected_row_id: int = None):
        """
        يملأ cmb_op_row بصفوف العملية ويختار الصف الصحيح.

        الأولوية:
          1. selected_row_id  (الأعلى أولوية)
          2. _init_machine_op_row_id
          3. _pinned_op_row_id
          4. الصف الأول (fallback)
        """
        try:
            if sip.isdeleted(self) or sip.isdeleted(self.cmb_op_row):
                return
        except Exception:
            return

        if op_id is None:
            self._hide_op_rows()
            return

        try:
            from db.costing.machine_op_rows_repo import fetch_op_rows, calc_op_row_cost
            conn = self._get_conn()
            if conn is None:
                self._hide_op_rows()
                return
            rows = fetch_op_rows(conn, op_id)
        except Exception:
            self._hide_op_rows()
            return

        if not rows:
            self._hide_op_rows()
            return

        # تحديد الـ target_id
        target_id = selected_row_id
        if target_id is None:
            target_id = self._init_machine_op_row_id
        if target_id is None:
            target_id = self._pinned_op_row_id

        self.cmb_op_row.blockSignals(True)
        self.cmb_op_row.clear()

        for row in rows:
            try:
                conn2 = self._get_conn()
                cost = calc_op_row_cost(conn2, row["id"]) if conn2 else 0.0
            except Exception:
                cost = 0.0
            label   = row["label"] or f"صف {row['id']}"
            display = f"{label}  ({row['value']:.4g} ÷ {row['count']:.4g})  ≈ {cost:.3f} ج"
            self.cmb_op_row.addItem(display, row["id"])

        # استعادة الاختيار
        restored = False
        if target_id is not None:
            for i in range(self.cmb_op_row.count()):
                if self.cmb_op_row.itemData(i) == target_id:
                    self.cmb_op_row.setCurrentIndex(i)
                    restored = True
                    break

        if not restored and self.cmb_op_row.count() > 0:
            self.cmb_op_row.setCurrentIndex(0)

        current_data = self.cmb_op_row.currentData()
        if current_data is not None:
            self._pinned_op_row_id = current_data
            if self._init_machine_op_row_id is None:
                self._init_machine_op_row_id = current_data

        self.cmb_op_row.blockSignals(False)
        self._sub_row_widget.setVisible(True)
        self._update_op_row_cost_label()

    def _hide_op_rows(self):
        try:
            if sip.isdeleted(self) or sip.isdeleted(self._sub_row_widget):
                return
        except Exception:
            return
        self._sub_row_widget.setVisible(False)

    def _on_op_row_changed(self, _index: int = 0):
        try:
            if sip.isdeleted(self) or sip.isdeleted(self.cmb_op_row):
                return
        except Exception:
            return
        row_id = self.cmb_op_row.currentData()
        if row_id is not None:
            self._pinned_op_row_id       = row_id
            self._init_machine_op_row_id = row_id
        self._update_op_row_cost_label()

    def _update_op_row_cost_label(self):
        try:
            if sip.isdeleted(self) or sip.isdeleted(self.cmb_op_row):
                return
        except Exception:
            return
        row_id = self.cmb_op_row.currentData()
        if row_id is None:
            row_id = self._pinned_op_row_id
        if row_id is not None and row_id != self._pinned_op_row_id:
            self._pinned_op_row_id = row_id
        if row_id is None:
            self.lbl_op_row_cost.setText("")
            return
        try:
            from db.costing.machine_op_rows_repo import calc_op_row_cost
            conn = self._get_conn()
            if conn:
                cost = calc_op_row_cost(conn, row_id)
                self.lbl_op_row_cost.setText(f"= {cost:.4f} ج/قطعة")
        except Exception:
            self.lbl_op_row_cost.setText("")