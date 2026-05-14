"""
ui/tabs/costing/product/product_form.py

الإصلاح الجوهري:
  _load_bom_for_scenario: بعد إنشاء كل ComponentRow،
  لو كان النوع machine_op، نستدعي expose_load_op_rows مباشرة (synchronously)
  بدل الاعتماد على الـ QTimer اللي ممكن يجي بعد ما get_values اتنادي.

  هذا يضمن إن الـ cmb_op_row يكون ممتلئ بالصفوف والاختيار الصحيح محفوظ
  قبل أي عملية حفظ.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QScrollArea,
    QSizePolicy, QMessageBox,
)
from PyQt5.QtCore import Qt, QTimer

from db.items_repo import (
    fetch_item, insert_item, update_item,
    fetch_orphan_bom_rows,
)
from db.bom_scenarios_repo import (
    fetch_default_scenario, insert_scenario,
    fetch_bom_for_scenario, replace_bom_for_scenario,
)
from ui.helpers import success_button
from ui.widgets.costing.component_row    import ComponentRow
from ui.widgets.shared.category_manager import CategoryCombo
from ui.widgets.shared.scrollable_form  import wrap_in_scroll
from ui.widgets.costing.bom_scenarios_panel import _BomScenariosPanel
from ui.events import bus


class _FormPanel(QWidget):
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

        header_inner = QWidget()
        header_inner.setMinimumWidth(400)
        header_inner.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        header_scroll = wrap_in_scroll(header_inner)
        header_scroll.setFixedHeight(150)

        header_lay = QVBoxLayout(header_inner)
        header_lay.setContentsMargins(12, 8, 12, 8)
        header_lay.setSpacing(6)

        top = QHBoxLayout()
        top.setSpacing(8)

        self.lbl_mode = QLabel("─── منتج جديد ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0; font-size:12px;")
        self.lbl_mode.setMinimumWidth(160)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم المنتج...")
        self.inp_name.setMinimumHeight(32)

        self.cmb_category = CategoryCombo(self.conn, scope=self._scope)
        self.cmb_category.setMinimumHeight(32)
        self.cmb_category.setFixedWidth(160)

        self.btn_add_row = QPushButton("+ مكون")
        self.btn_add_row.setMinimumHeight(32)
        self.btn_add_row.clicked.connect(lambda: self._add_row())

        self.btn_save   = success_button("حفظ")
        self.btn_cancel = QPushButton("X الغاء")
        self.btn_save.setMinimumHeight(32)
        self.btn_cancel.setMinimumHeight(32)
        self.btn_save.clicked.connect(self.save)
        self.btn_cancel.clicked.connect(self._do_cancel)
        self.btn_cancel.setVisible(False)

        top.addWidget(self.lbl_mode)
        top.addWidget(self.inp_name, stretch=3)
        top.addSpacing(4)
        top.addWidget(QLabel("التصنيف:"))
        top.addWidget(self.cmb_category)
        top.addSpacing(8)
        top.addWidget(self.btn_add_row)
        top.addWidget(self.btn_save)
        top.addWidget(self.btn_cancel)
        header_lay.addLayout(top)

        self._scenarios_panel = _BomScenariosPanel(self.conn)
        self._scenarios_panel.scenario_changed.connect(self._on_scenario_changed)
        header_lay.addWidget(self._scenarios_panel)

        headers = QWidget()
        hlay = QHBoxLayout(headers)
        hlay.setContentsMargins(0, 0, 0, 0)
        hlay.setSpacing(6)

        def _hdr(text, w=None, stretch=0):
            lbl = QLabel(text)
            lbl.setStyleSheet(
                "font-size:11px; font-weight:bold; color:#555;"
                "border-bottom:1px solid #ccc; padding-bottom:2px;"
            )
            if w:
                lbl.setFixedWidth(w)
            hlay.addWidget(lbl, stretch=stretch)

        _hdr("النوع",          150)
        _hdr("العنصر",         stretch=3)
        _hdr("الصف / Variant", 160)
        _hdr("تكلفة/قطعة",    80)
        _hdr("الكمية",         80)
        _hdr("الهادر %",       90)
        _hdr("",               32)
        header_lay.addWidget(headers)

        root.addWidget(header_scroll)

        self.rows_container = QWidget()
        self.rows_layout    = QVBoxLayout(self.rows_container)
        self.rows_layout.setSpacing(2)
        self.rows_layout.setContentsMargins(12, 4, 12, 4)
        self.rows_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.rows_container)
        scroll.setMinimumHeight(80)
        scroll.setStyleSheet("border:none;")
        root.addWidget(scroll, stretch=1)

        self._add_row()

    # ══════════════════════════════════════════════════════
    # صفوف المكونات
    # ══════════════════════════════════════════════════════

    def _add_row(self, child_type="raw", child_id=None, qty=1.0,
                 orphan_name: str = None, waste_pct: float = 0.0,
                 variant_id: int = None, machine_op_row_id: int = None):
        row = ComponentRow(
            catalog_fn=self._catalog_fn,
            child_type=child_type,
            child_id=child_id,
            qty=qty,
            waste_pct=waste_pct,
            variant_id=variant_id,
            machine_op_row_id=machine_op_row_id,
        )
        if row.is_orphan() and orphan_name:
            row.set_orphan_name(orphan_name)
        row.removed.connect(self._remove_row)
        self.rows_layout.insertWidget(self.rows_layout.count() - 1, row)
        QTimer.singleShot(0, row.refresh_catalog)
        return row

    def _remove_row(self, widget):
        self.rows_layout.removeWidget(widget)
        widget.deleteLater()

    def collect_rows(self):
        """
        يجمع (child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id)
        التأكد من 6 عناصر في كل tuple
        """
        result = []
        for i in range(self.rows_layout.count()):
            item = self.rows_layout.itemAt(i)
            if not item:
                continue
            w = item.widget()
            if isinstance(w, ComponentRow):
                val = w.get_values()
                if val:
                    val = tuple(val)
                    while len(val) < 6:
                        val = val + (None,)
                    result.append(val)
        return result

    def clear_rows(self):
        while self.rows_layout.count() > 1:
            item = self.rows_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    # ══════════════════════════════════════════════════════
    # تحميل المنتج للتعديل
    # ══════════════════════════════════════════════════════

    def load_product(self, pid: int):
        item = fetch_item(self.conn, pid)
        if not item:
            return
        self.clear_rows()
        self.inp_name.setText(item["name"])
        self.cmb_category.set_category(item["category_id"])

        self._scenarios_panel.load_item(pid)

        sc = fetch_default_scenario(self.conn, pid)
        if not sc:
            sc_id = insert_scenario(self.conn, pid, "سيناريو 1", is_default=True)
        else:
            sc_id = sc["id"]

        self._current_scenario_id = sc_id
        self._load_bom_for_scenario(pid, sc_id)

        n_orphans = len(fetch_orphan_bom_rows(self.conn, pid))
        label = (
            f"تعديل: {item['name']}  {n_orphans} مكون ناقص"
            if n_orphans else f"تعديل: {item['name']}"
        )
        self.enter_edit_mode(pid, label)
        self.inp_name.setFocus()

    def _load_bom_for_scenario(self, pid: int, scenario_id: int):
        """
        تحميل مكونات BOM لسيناريو محدد.

        ✅ الإصلاح الجوهري:
        بعد إنشاء كل ComponentRow من نوع machine_op،
        نستدعي expose_load_op_rows مباشرة (synchronously)
        لضمان إن الـ cmb_op_row ممتلئ والاختيار الصحيح محفوظ
        قبل أي استدعاء لـ get_values().

        هذا يحل مشكلة الـ race condition بين QTimer (50ms) وعملية الحفظ.
        """
        self.clear_rows()

        orphan_map = {
            (o["child_type"], o["child_id"]): o["child_name"]
            for o in fetch_orphan_bom_rows(self.conn, pid)
        }

        try:
            bom_rows = fetch_bom_for_scenario(self.conn, scenario_id)
        except Exception:
            from db.items_repo import fetch_bom
            bom_rows = fetch_bom(self.conn, pid)

        for row_data in (bom_rows or []):
            child_type = row_data["child_type"]
            child_id   = row_data["child_id"]
            qty        = row_data["qty"]

            try:
                waste_pct = float(row_data["waste_pct"]) if row_data["waste_pct"] else 0.0
            except (KeyError, TypeError):
                waste_pct = 0.0

            try:
                variant_id = row_data["variant_id"]
            except (KeyError, IndexError):
                variant_id = None

            try:
                machine_op_row_id = row_data["machine_op_row_id"]
            except (KeyError, IndexError):
                machine_op_row_id = None

            o_name = orphan_map.get((child_type, child_id))

            # ✅ إنشاء الـ row مع تمرير machine_op_row_id للـ __init__
            component_row = self._add_row(
                child_type=child_type,
                child_id=child_id,
                qty=qty,
                orphan_name=o_name,
                waste_pct=waste_pct,
                variant_id=variant_id,
                machine_op_row_id=machine_op_row_id,
            )

            # ✅ الإصلاح الجوهري: لو كان machine_op، نحمل الصفوف synchronously
            # هذا يتجاوز مشكلة الـ QTimer race condition
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
        self.inp_name.clear()
        self.cmb_category.setCurrentIndex(0)
        self.clear_rows()
        self._add_row()
        self._scenarios_panel.clear()
        self._current_scenario_id = None
        self.exit_edit_mode("منتج جديد")

    # ══════════════════════════════════════════════════════
    # حفظ
    # ══════════════════════════════════════════════════════

    def save(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "ادخل اسم المنتج اولا")
            return
        rows = self.collect_rows()
        if not rows:
            QMessageBox.warning(self, "تنبيه", "اضف مكونا واحدا على الاقل")
            return

        if self.is_editing:
            update_item(
                self.conn, self._editing_id, name, 0,
                category_id=self.cmb_category.get_category()
            )
            if self._current_scenario_id is None:
                self._current_scenario_id = self._scenarios_panel.ensure_default_scenario(
                    self._editing_id
                )
            replace_bom_for_scenario(self.conn, self._current_scenario_id, rows)
        else:
            pid = insert_item(
                self.conn, name, self.product_type, 0,
                category_id=self.cmb_category.get_category()
            )
            sc_id = insert_scenario(self.conn, pid, "سيناريو 1", is_default=True)
            replace_bom_for_scenario(self.conn, sc_id, rows)

        self.conn.commit()
        self.reset()
        QTimer.singleShot(0, bus.data_changed.emit)

    def enter_edit_mode(self, pid, label=""):
        self._editing_id = pid
        self.is_editing  = True
        self.lbl_mode.setText(label)
        self.btn_cancel.setVisible(True)

    def exit_edit_mode(self, label=""):
        self._editing_id = None
        self.is_editing  = False
        self.lbl_mode.setText(label)
        self.btn_cancel.setVisible(False)

    def _do_cancel(self):
        self.reset()