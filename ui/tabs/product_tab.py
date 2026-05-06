"""
ui/tabs/product_tab.py
======================
تبويب المنتجات (نصف مصنع أو نهائي) — ثلاثة أقسام قابلة للسحب.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTabWidget,
    QLineEdit, QPushButton, QTableWidgetItem,
    QScrollArea, QMessageBox, QLabel, QFrame, QHeaderView,
)
from PyQt5.QtCore import Qt, QTimer

from db.connection      import get_connection
from db.items_repo      import (
    fetch_items_by_type, fetch_item,
    insert_item, update_item, delete_item,
    fetch_bom, insert_bom_row, replace_bom,
    fetch_orphan_bom_rows, delete_orphan_bom_rows,
    cleanup_empty_products_after_orphan_fix,
)
from db.operations_repo import fetch_all_labor_ops, fetch_all_machine_ops
from models.costing     import calc_cost
from ui.helpers         import (
    EditModeMixin, make_table, buttons_row,
    section_label, success_button, danger_button, confirm_delete
)
from ui.widgets.component_row    import ComponentRow
from ui.widgets.bom_tree         import BomTree
from ui.widgets.category_manager import CategoryManager, CategoryCombo
from ui.events import bus

_TYPE_AR = {
    "raw":        "خامة",
    "semi":       "نصف مصنع",
    "labor_op":   "عملية عمالة",
    "machine_op": "عملية تشغيل",
}

_PRODUCT_SCOPE = {
    "semi":  "semi",
    "final": "final",
}

_SPLITTER_STYLE = """
    QSplitter::handle {
        background: #e0e0e0;
        border-top: 1px solid #ccc;
    }
    QSplitter::handle:hover { background: #bbdefb; }
"""


# ══════════════════════════════════════════════════════════
# بناء الكتالوج
# ══════════════════════════════════════════════════════════

def _catalog_for_component_row(conn) -> dict:
    """
    يرجع dict بالشكل المتوافق مع component_row._build_grouped_items:
      entry = (id, name, cat_id, cat_name)   ← entry[3] = cat_name
    """
    result: dict[str, list] = {
        "raw": [], "semi": [], "labor_op": [], "machine_op": []
    }

    for row in fetch_items_by_type(conn, "raw"):
        result["raw"].append((
            row["id"], row["name"],
            row["category_id"],
            row["category_name"] or None,
        ))

    for row in fetch_items_by_type(conn, "semi"):
        result["semi"].append((
            row["id"], row["name"],
            row["category_id"],
            row["category_name"] or None,
        ))

    for op in fetch_all_labor_ops(conn):
        result["labor_op"].append((
            op["id"], op["name"],
            op["category_id"],
            op["category_name"] or None,
        ))

    for op in fetch_all_machine_ops(conn):
        result["machine_op"].append((
            op["id"], op["name"],
            op["category_id"],
            op["category_name"] or None,
        ))

    return result


# ══════════════════════════════════════════════════════════
# فورم إنشاء / تعديل المنتج
# ══════════════════════════════════════════════════════════

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

        # رؤوس الأعمدة
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

        _hdr("النوع",  150)
        _hdr("العنصر", stretch=3)
        _hdr("الكمية", 80)
        _hdr("",       32)
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
                 orphan_name: str | None = None):
        row = ComponentRow(
            catalog_fn=self._catalog_fn,
            child_type=child_type,
            child_id=child_id,
            qty=qty
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
        result = []
        for i in range(self.rows_layout.count()):
            item = self.rows_layout.itemAt(i)
            if not item:
                continue
            w = item.widget()
            if isinstance(w, ComponentRow):
                val = w.get_values()
                if val:
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
        orphan_names: dict[tuple, str | None] = {
            (o["child_type"], o["child_id"]): o["child_name"]
            for o in orphans_raw
        }

        for child_type, child_id, qty in (bom or []):
            o_name = orphan_names.get((child_type, child_id))
            self._add_row(
                child_type=child_type,
                child_id=child_id,
                qty=qty,
                orphan_name=o_name,
            )

        if not bom:
            self._add_row()

        n = len(orphan_names)
        label = (
            f"─── تعديل: {item['name']}  ⚠️ {n} مكوّن ناقص ───"
            if n else
            f"─── تعديل: {item['name']} ───"
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
            for ct, cid, qty in rows:
                insert_bom_row(self.conn, pid, ct, cid, qty)

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


# ══════════════════════════════════════════════════════════
# جدول المنتجات
# ══════════════════════════════════════════════════════════

class _ProductTable(QWidget):
    def __init__(self, conn, product_type, on_select, on_edit, on_delete, parent=None):
        super().__init__(parent)
        self.conn         = conn
        self.product_type = product_type
        self._on_select   = on_select
        self._on_edit     = on_edit
        self._on_delete   = on_delete
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 10)
        root.setSpacing(6)

        root.addWidget(section_label("─── المنتجات المحفوظة ───"))

        self.table = make_table(["ID", "الاسم", "التصنيف", "التكلفة"], stretch_col=1)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Fixed)
        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(1, 220)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 120)
        self.table.itemSelectionChanged.connect(
            lambda: self._on_select(self.selected_pid())
        )
        root.addWidget(self.table)

        btn_edit = QPushButton("✏️ تعديل المحدد")
        btn_del  = danger_button("🗑️ حذف المحدد")
        btn_edit.setMinimumHeight(30)
        btn_del.setMinimumHeight(30)
        btn_edit.clicked.connect(lambda: self._on_edit(self.selected_pid()))
        btn_del.clicked.connect(lambda: self._on_delete(self.selected_pid()))
        root.addLayout(buttons_row(btn_edit, btn_del))

    def selected_pid(self):
        row = self.table.currentRow()
        return int(self.table.item(row, 0).text()) if row >= 0 else None

    def _load(self):
        prev = self.selected_pid()
        self.table.setRowCount(0)
        for r, row in enumerate(fetch_items_by_type(self.conn, self.product_type)):
            cost = calc_cost(self.conn, row["id"])
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(row["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(
                row["category_name"] if row["category_name"] else "—"
            ))
            self.table.setItem(r, 3, QTableWidgetItem(f"{cost:.4f}"))
        if prev is not None:
            for r in range(self.table.rowCount()):
                if int(self.table.item(r, 0).text()) == prev:
                    self.table.selectRow(r)
                    break


# ══════════════════════════════════════════════════════════
# شريط التحذير
# ══════════════════════════════════════════════════════════

class _WarningBar(QFrame):
    def __init__(self, on_fix, on_edit, parent=None):
        super().__init__(parent)
        self.setObjectName("warningBar")
        self.setStyleSheet("""
            #warningBar {
                background: #fff3e0;
                border: 1px solid #e65100;
                border-radius: 6px;
            }
        """)
        self.setVisible(False)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(10)

        self._icon = QLabel("⚠️")
        self._icon.setStyleSheet("font-size:16px; background:transparent; border:none;")
        self._lbl = QLabel()
        self._lbl.setWordWrap(True)
        self._lbl.setStyleSheet(
            "color:#bf360c; font-weight:bold; background:transparent; border:none;"
        )

        btn_fix = QPushButton("🗑️ حذف الناقص")
        btn_fix.setStyleSheet(
            "background:#e65100; color:white; border:none; border-radius:4px; padding:4px 10px;"
        )
        btn_fix.clicked.connect(on_fix)

        btn_edit = QPushButton("✏️ تعديل")
        btn_edit.setStyleSheet(
            "background:#1565c0; color:white; border:none; border-radius:4px; padding:4px 10px;"
        )
        btn_edit.clicked.connect(on_edit)

        btn_dismiss = QPushButton("✖")
        btn_dismiss.setStyleSheet(
            "background:transparent; color:#888; border:1px solid #ccc;"
            "border-radius:4px; padding:4px 8px;"
        )
        btn_dismiss.clicked.connect(lambda: self.setVisible(False))

        lay.addWidget(self._icon)
        lay.addWidget(self._lbl, stretch=1)
        lay.addWidget(btn_fix)
        lay.addWidget(btn_edit)
        lay.addWidget(btn_dismiss)

    def show_orphans(self, orphans, product_name):
        if not orphans:
            self.setVisible(False)
            return
        lines = []
        for o in orphans:
            type_ar = _TYPE_AR.get(o["child_type"], o["child_type"])
            display = o["child_name"] or f"ID: {o['child_id']}"
            lines.append(f"• {type_ar}: «{display}»")
        msg = f"«{product_name}» — {len(orphans)} مكوّن محذوف:\n" + "  ".join(lines)
        self._lbl.setText(msg)
        self.setVisible(True)


# ══════════════════════════════════════════════════════════
# اللوحة الرئيسية
# ══════════════════════════════════════════════════════════

class _ProductMainPanel(QWidget):
    def __init__(self, conn, product_type: str, parent=None):
        super().__init__(parent)
        self.conn         = conn
        self.product_type = product_type
        self._build()
        bus.data_changed.connect(self._on_data_changed)

    def _get_catalog(self):
        return _catalog_for_component_row(self.conn)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(_SPLITTER_STYLE)

        self._form = _FormPanel(self.conn, self.product_type, self._get_catalog)
        bus.data_changed.connect(self._refresh_form_catalog)

        mid_widget = QWidget()
        mid_layout = QVBoxLayout(mid_widget)
        mid_layout.setContentsMargins(0, 0, 0, 0)
        mid_layout.setSpacing(0)

        self._warning = _WarningBar(
            on_fix=self._fix_orphans,
            on_edit=self._edit_selected
        )
        mid_layout.addWidget(self._warning)

        self._prod_table = _ProductTable(
            self.conn, self.product_type,
            on_select=self._on_product_selected,
            on_edit=self._edit_selected,
            on_delete=self._delete_product
        )
        mid_layout.addWidget(self._prod_table)

        self._bom_tree = BomTree()

        splitter.addWidget(self._form)
        splitter.addWidget(mid_widget)
        splitter.addWidget(self._bom_tree)
        splitter.setSizes([280, 220, 250])
        splitter.setCollapsible(0, True)
        splitter.setCollapsible(1, False)
        splitter.setCollapsible(2, True)

        root.addWidget(splitter)

    def _on_data_changed(self):
        pid = self._prod_table.selected_pid()
        if pid is not None:
            self._check_orphans(pid)
            self._bom_tree.load(self.conn, pid)

    def _on_product_selected(self, pid):
        if pid is None:
            self._bom_tree.clear_tree()
            self._warning.setVisible(False)
        else:
            self._check_orphans(pid)
            self._bom_tree.load(self.conn, pid)

    def _refresh_form_catalog(self):
        new_catalog = self._get_catalog()
        layout = self._form.rows_layout
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if not item:
                continue
            w = item.widget()
            if isinstance(w, ComponentRow):
                w.refresh_catalog(new_catalog)

    def _check_orphans(self, pid):
        orphans = fetch_orphan_bom_rows(self.conn, pid)
        item    = fetch_item(self.conn, pid)
        name    = item["name"] if item else f"ID {pid}"
        self._warning.show_orphans(orphans, name)

    def _fix_orphans(self):
        pid = self._prod_table.selected_pid()
        if pid is None:
            return
        orphans = fetch_orphan_bom_rows(self.conn, pid)
        orphan_names = [
            o["child_name"] or f"ID:{o['child_id']}"
            for o in orphans
        ]
        item = fetch_item(self.conn, pid)
        prod_name = item["name"] if item else f"ID {pid}"

        n = delete_orphan_bom_rows(self.conn, pid)
        self._warning.setVisible(False)
        self._bom_tree.load(self.conn, pid)

        auto_deleted = cleanup_empty_products_after_orphan_fix(self.conn, [pid])
        bus.data_changed.emit()

        if auto_deleted:
            self._form.reset()
            self._bom_tree.clear_tree()
            QMessageBox.information(
                self, "تم — وتم حذف المنتج",
                f"✅ تم حذف {n} مكوّن ناقص:\n"
                + "\n".join(f"  • {nm}" for nm in orphan_names)
                + f"\n\nبما أن «{prod_name}» لم يعد يحتوي على أي مكونات،\n"
                  "تم حذفه تلقائياً."
            )
        else:
            QMessageBox.information(
                self, "تم",
                f"✅ تم حذف {n} مكوّن ناقص:\n"
                + "\n".join(f"  • {nm}" for nm in orphan_names)
            )

    def _edit_selected(self, pid=None):
        if pid is None:
            pid = self._prod_table.selected_pid()
        if pid is None:
            QMessageBox.information(self, "تنبيه", "اختر منتجاً من الجدول أولاً")
            return
        self._warning.setVisible(False)
        self._form.load_product(pid)

    def _delete_product(self, pid):
        if pid is None:
            QMessageBox.information(self, "تنبيه", "اختر منتجاً أولاً")
            return
        item = fetch_item(self.conn, pid)
        if not item:
            return
        if confirm_delete(self, item["name"]):
            if self._form.is_editing and self._form._editing_id == pid:
                self._form.reset()
            delete_item(self.conn, pid)
            self._warning.setVisible(False)
            self._bom_tree.clear_tree()
            bus.data_changed.emit()


# ══════════════════════════════════════════════════════════
# التبويب الرئيسي
# ══════════════════════════════════════════════════════════

class ProductTab(QWidget):
    def __init__(self, product_type: str, parent=None):
        super().__init__(parent)
        self.product_type = product_type
        self.conn = get_connection()
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scope = _PRODUCT_SCOPE.get(self.product_type, self.product_type)
        tabs  = QTabWidget()

        icon       = "🔧" if self.product_type == "semi" else "🏭"
        label_main = f"{icon}  المنتجات"
        tabs.addTab(_ProductMainPanel(self.conn, self.product_type), label_main)
        tabs.addTab(CategoryManager(self.conn, scope=scope), "🏷️  التصنيفات")

        root.addWidget(tabs)

    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)