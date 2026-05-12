"""
ui/tabs/costing/product/product_form.py
================================
_FormPanel — فورم إنشاء / تعديل المنتج (اسم + مكونات BOM).
مع دعم variant_id للخامات.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QScrollArea,
)
from PyQt5.QtCore import Qt, QTimer

from db.items_repo import (
    fetch_item, insert_item, update_item,
    fetch_bom, insert_bom_row, replace_bom,
    fetch_orphan_bom_rows,
)
from ui.helpers import success_button
from ui.widgets.component_row    import ComponentRow
from ui.widgets.category_manager import CategoryCombo
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
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        top = QHBoxLayout()
        self.lbl_mode = QLabel("─── منتج جديد ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0; font-size:12px;")

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم المنتج...")
        self.inp_name.setMinimumHeight(32)

        self.btn_add_row = QPushButton("➕ مكون")
        self.btn_add_row.setMinimumHeight(32)
        self.btn_add_row.clicked.connect(lambda: self._add_row())

        self.cmb_category = CategoryCombo(self.conn, scope=self._scope)
        self.cmb_category.setMinimumHeight(32)
        self.cmb_category.setFixedWidth(160)

        self.btn_save   = success_button("💾 حفظ")
        self.btn_cancel = QPushButton("✖ إلغاء")
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
        root.addLayout(top)

        # رؤوس الأعمدة — أضفنا "وحدة الإنتاج"
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

        _hdr("النوع",        150)
        _hdr("العنصر",       stretch=3)
        _hdr("وحدة الإنتاج", 130)   # ← جديد
        _hdr("تكلفة/قطعة",  80)    # ← جديد (label cost)
        _hdr("الكمية",       80)
        _hdr("الهادر %",     90)
        _hdr("",             32)
        root.addWidget(headers)

        self.rows_container = QWidget()
        self.rows_layout    = QVBoxLayout(self.rows_container)
        self.rows_layout.setSpacing(2)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.rows_container)
        scroll.setMinimumHeight(80)
        scroll.setStyleSheet("border:none;")
        root.addWidget(scroll, stretch=1)

        self._add_row()

    def _add_row(self, child_type="raw", child_id=None, qty=1.0,
                 orphan_name: str = None, waste_pct: float = 0.0,
                 variant_id: int = None):
        row = ComponentRow(
            catalog_fn=self._catalog_fn,
            child_type=child_type,
            child_id=child_id,
            qty=qty,
            waste_pct=waste_pct,
            variant_id=variant_id,
        )
        if row.is_orphan() and orphan_name:
            row.set_orphan_name(orphan_name)
        row.removed.connect(self._remove_row)
        self.rows_layout.insertWidget(self.rows_layout.count() - 1, row)
        QTimer.singleShot(0, row.refresh_catalog)

    def _remove_row(self, widget):
        self.rows_layout.removeWidget(widget)
        widget.deleteLater()

    def collect_rows(self):
        """
        يجمع صفوف BOM.
        كل صف: (child_type, child_id, qty, waste_pct, variant_id)
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
                    # تأكد إن الـ tuple فيه 5 عناصر
                    if len(val) == 4:
                        val = val + (None,)
                    result.append(val)
        return result

    def clear_rows(self):
        while self.rows_layout.count() > 1:
            item = self.rows_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    def load_product(self, pid: int):
        item = fetch_item(self.conn, pid)
        if not item:
            return
        self.clear_rows()
        self.inp_name.setText(item["name"])
        self.cmb_category.set_category(item["category_id"])
        bom = fetch_bom(self.conn, pid)
        orphans_raw = fetch_orphan_bom_rows(self.conn, pid)
        orphan_names = {
            (o["child_type"], o["child_id"]): o["child_name"]
            for o in orphans_raw
        }
        for row_data in (bom or []):
            child_type = row_data["child_type"]
            child_id   = row_data["child_id"]
            qty        = row_data["qty"]
            waste_pct  = float(row_data["waste_pct"]) if row_data["waste_pct"] else 0.0
            # variant_id
            try:
                variant_id = row_data["variant_id"]
            except (IndexError, KeyError):
                variant_id = None

            o_name = orphan_names.get((child_type, child_id))
            self._add_row(
                child_type=child_type,
                child_id=child_id,
                qty=qty,
                orphan_name=o_name,
                waste_pct=waste_pct,
                variant_id=variant_id,
            )
        if not bom:
            self._add_row()
        n = len(orphan_names)
        label = (
            f"─── تعديل: {item['name']}  ⚠️ {n} مكوّن ناقص ───"
            if n else f"─── تعديل: {item['name']} ───"
        )
        self.enter_edit_mode(pid, label)
        self.inp_name.setFocus()

    def reset(self):
        self.inp_name.clear()
        self.cmb_category.setCurrentIndex(0)
        self.clear_rows()
        self._add_row()
        self.exit_edit_mode("─── منتج جديد ───")

    def save(self):
        from PyQt5.QtWidgets import QMessageBox
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم المنتج أولاً")
            return
        rows = self.collect_rows()
        if not rows:
            QMessageBox.warning(self, "تنبيه", "أضف مكوناً واحداً على الأقل")
            return
        if self.is_editing:
            update_item(self.conn, self._editing_id, name, 0,
                        category_id=self.cmb_category.get_category())
            replace_bom(self.conn, self._editing_id, rows)
        else:
            pid = insert_item(self.conn, name, self.product_type, 0,
                              category_id=self.cmb_category.get_category())
            for row_data in rows:
                ct       = row_data[0]
                cid      = row_data[1]
                qty      = row_data[2]
                waste_pct = row_data[3] if len(row_data) > 3 else 0.0
                vid      = row_data[4] if len(row_data) > 4 else None
                insert_bom_row(self.conn, pid, ct, cid, qty, waste_pct, vid)
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