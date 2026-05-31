"""
ui/widgets/managers/category.py
=============================
CategoryManager — شجرة لإدارة التصنيفات الهرمية.
CategoryForm    — فورم إضافة/تعديل التصنيف.

التغييرات:
  - [i18n] كل النصوص الظاهرة للمستخدم تستخدم tr() بدل النصوص العربية المباشرة.
  - [i18n] CategoryForm و CategoryManager يشتركان في bus.language_changed.
  - [Q-03] تمرير conn مباشرة لـ CategoryService بدل استدعاء _live_conn()
    في كل عملية (add, save, delete, load, _load).
  - [إصلاح هيكلة] استبدال imports مباشرة من db/ بـ CategoryService methods.
    القديم: from db.shared.categories_repo import fetch_all_categories, fetch_category, ...
    الجديد: كل الاستدعاءات عبر CategoryService — المسار الصحيح:
            widget → service → repo (db/)
    الدوال المضافة لـ CategoryService:
      - get_all(conn, scope) → list
      - get_one(conn, cat_id) → dict | None
      - get_descendants(conn, cat_id) → set
      - count_items(conn, cat_id) → dict
      - get_tree(conn, scope) → list  (بناء الشجرة من النتائج)
"""

from PyQt5.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout,
    QTreeWidget, QTreeWidgetItem, QLineEdit, QComboBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from ..core.conn          import LiveConnMixin
from ..core.i18n          import tr
from ..components.button  import make_btn
from ..dialogs.confirm    import confirm_delete
from ..dialogs.message    import msg_info, msg_warning
from ..theme.layout_styles import tree_style
from ..components.label   import ModeLabel
from ui.widgets.core.events import emit_company_data_changed


# ── CategoryForm ──────────────────────────────────────────

class CategoryForm(QGroupBox, LiveConnMixin):
    """فورم إضافة/تعديل التصنيف."""

    def __init__(self, conn, scope: str, tree_widget, parent=None):
        super().__init__(tr("category_data"), parent)
        self.conn        = conn
        self.scope       = scope
        self._tree       = tree_widget
        self._editing_id = None
        self._build()
        self._connect_language_bus()

    def _connect_language_bus(self):
        """[i18n] يشترك في bus.language_changed لتحديث النصوص."""
        try:
            from ui.events import bus
            bus.language_changed.connect(
                self._on_language_changed, Qt.UniqueConnection
            )
        except Exception:
            pass

    def _on_language_changed(self, lang_code: str):
        """[i18n] يُحدّث نصوص الـ groupbox والأزرار."""
        self.setTitle(tr("category_data"))
        self.btn_add.setText(tr("btn_add"))
        self.btn_save.setText(tr("btn_save"))
        self.btn_cancel.setText(tr("btn_cancel"))

    def _build(self):
        from ..helpers.color_picker import ColorPickerWidget

        form = QFormLayout(self)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = ModeLabel(add_text=tr("category_add"))
        form.addRow(self.lbl_mode)

        self.inp_name = QLineEdit()
        self.inp_name.setMinimumHeight(30)
        self.inp_name.setPlaceholderText(tr("category_name"))
        form.addRow(f"{tr('category_name')} :", self.inp_name)

        self.cmb_parent = QComboBox()
        self.cmb_parent.setMinimumHeight(30)
        form.addRow(f"{tr('category_parent')} :", self.cmb_parent)

        self._color_picker = ColorPickerWidget(default="#607d8b")
        form.addRow(f"{tr('category_color')} :", self._color_picker)

        btn_row = QHBoxLayout()
        self.btn_add    = make_btn(tr("btn_add"),    "primary")
        self.btn_save   = make_btn(tr("btn_save"),   "success")
        self.btn_cancel = make_btn(tr("btn_cancel"), "ghost")
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        self.btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self._reset)
        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn_row.addWidget(btn)
        form.addRow(btn_row)

        self._refresh_parent_combo()

    def _refresh_parent_combo(self, conn=None, exclude_id: int = None):
        """
        [Q-03] يستقبل conn اختياري بدل استدعاء _live_conn() داخلياً.
        [إصلاح هيكلة] يستخدم CategoryService بدل db import مباشر.
        """
        if conn is None:
            try:
                conn = self._live_conn()
            except Exception:
                return

        self.cmb_parent.blockSignals(True)
        self.cmb_parent.clear()
        self.cmb_parent.addItem(tr("filter_all"), None)

        try:
            from services.shared.category_service import CategoryService
            svc  = CategoryService(conn)
            rows = svc.get_all(self.scope)
            tree = svc.build_tree(rows)
        except Exception:
            self.cmb_parent.blockSignals(False)
            return

        excluded = set()
        if exclude_id is not None:
            try:
                from services.shared.category_service import CategoryService
                excluded = CategoryService(conn).get_descendants(exclude_id)
            except Exception:
                pass

        self._add_parent_nodes(tree, depth=0, excluded=excluded)
        self.cmb_parent.blockSignals(False)

    def _add_parent_nodes(self, nodes, depth, excluded):
        indent = "    " * depth
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            if node["id"] in excluded:
                continue
            self.cmb_parent.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            if node["children"]:
                self._add_parent_nodes(node["children"], depth + 1, excluded)

    def _add(self):
        name = self.inp_name.text().strip()
        if not name:
            msg_warning(self, tr("warning"), tr("category_name_required"))
            return

        try:
            conn = self._live_conn()
        except Exception as e:
            msg_warning(self, tr("error"), str(e))
            return

        from services.shared.category_service import CategoryService
        try:
            CategoryService(conn).add(
                name, self.scope,
                self._color_picker.current_color(),
                self.cmb_parent.currentData()
            )
        except ValueError as e:
            msg_warning(self, tr("warning"), str(e))
            return

        self._reset(conn=conn)
        emit_company_data_changed()

    def _save(self):
        if self._editing_id is None:
            return
        name = self.inp_name.text().strip()
        if not name:
            msg_warning(self, tr("warning"), tr("category_name_required"))
            return

        try:
            conn = self._live_conn()
        except Exception as e:
            msg_warning(self, tr("error"), str(e))
            return

        from services.shared.category_service import CategoryService
        try:
            CategoryService(conn).update(
                self._editing_id, name, self.scope,
                self._color_picker.current_color(),
                self.cmb_parent.currentData()
            )
        except ValueError as e:
            msg_warning(self, tr("warning"), str(e))
            return

        self._reset(conn=conn)
        emit_company_data_changed()

    def load_for_edit(self, cat_id: int):
        try:
            conn = self._live_conn()
        except Exception:
            return

        # [إصلاح هيكلة] استخدام CategoryService بدل fetch_category مباشرة
        from services.shared.category_service import CategoryService
        svc = CategoryService(conn)
        cat = svc.get_one(cat_id)
        if not cat:
            return

        self._editing_id = cat_id
        self.inp_name.setText(cat["name"])
        self._color_picker.set_color(cat["color"])

        self._refresh_parent_combo(conn=conn, exclude_id=cat_id)

        for i in range(self.cmb_parent.count()):
            if self.cmb_parent.itemData(i) == cat["parent_id"]:
                self.cmb_parent.setCurrentIndex(i)
                break
        self.lbl_mode.set_edit_mode(cat["name"])
        self.btn_add.setVisible(False)
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)

    def _reset(self, conn=None):
        self._editing_id = None
        self._color_picker.set_color("#607d8b")
        self.inp_name.clear()
        self.lbl_mode.set_add_mode()
        self.btn_add.setVisible(True)
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        self._refresh_parent_combo(conn=conn)


# ── CategoryManager ───────────────────────────────────────

class CategoryManager(QWidget, LiveConnMixin):
    """شجرة QTreeWidget لإدارة التصنيفات الهرمية."""

    def __init__(self, conn, scope: str = "all", parent=None):
        super().__init__(parent)
        self.conn  = conn
        self.scope = scope
        self._build()
        self._load()
        from ui.events import bus
        bus.data_changed.connect(self._load)
        self._connect_language_bus()

    def _connect_language_bus(self):
        """[i18n] يشترك في bus.language_changed لتحديث النصوص."""
        try:
            from ui.events import bus
            bus.language_changed.connect(
                self._on_language_changed, Qt.UniqueConnection
            )
        except Exception:
            pass

    def _on_language_changed(self, lang_code: str):
        """[i18n] يُحدّث عناوين الأعمدة ونصوص الأزرار."""
        self.tree.setHeaderLabels([
            tr("category"), tr("category_new"), tr("quantity")
        ])
        self.btn_edit.setText(tr("btn_edit"))
        self.btn_del.setText(tr("btn_delete"))

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            tr("category"), tr("category_new"), tr("quantity")
        ])
        self.tree.setColumnWidth(0, 260)
        self.tree.setColumnWidth(1, 60)
        self.tree.setColumnWidth(2, 80)
        self.tree.setAlternatingRowColors(True)
        self.tree.setAnimated(True)
        self.tree.setStyleSheet(tree_style())
        self.tree.itemSelectionChanged.connect(self._on_select)
        root.addWidget(self.tree)

        btn_row = QHBoxLayout()
        self.btn_edit = make_btn(tr("btn_edit"),   "normal")
        self.btn_del  = make_btn(tr("btn_delete"), "danger")
        self.btn_edit.clicked.connect(self._edit)
        self.btn_del.clicked.connect(self._delete)
        btn_row.addWidget(self.btn_edit)
        btn_row.addWidget(self.btn_del)
        btn_row.addStretch()
        root.addLayout(btn_row)

        self._form = CategoryForm(self.conn, self.scope, self.tree)
        root.addWidget(self._form)

    def _load(self):
        """
        [Q-03] _live_conn() مرة واحدة.
        [إصلاح هيكلة] يستخدم CategoryService بدل db imports مباشرة.
        """
        try:
            conn = self._live_conn()
        except Exception:
            return

        expanded = set()

        def _collect(item):
            if item.isExpanded():
                expanded.add(item.data(0, Qt.UserRole))
            for i in range(item.childCount()):
                _collect(item.child(i))

        for i in range(self.tree.topLevelItemCount()):
            _collect(self.tree.topLevelItem(i))

        self.tree.clear()

        # [إصلاح هيكلة] استخدام CategoryService بدل fetch_all_categories + build_tree
        try:
            from services.shared.category_service import CategoryService
            svc  = CategoryService(conn)
            rows = svc.get_all(self.scope)
            tree = svc.build_tree(rows)
        except Exception:
            return

        self._add_items(tree, parent=None, expanded=expanded, conn=conn)
        self.tree.expandAll()

    def _add_items(self, nodes, parent, expanded, conn):
        """
        [إصلاح هيكلة] يستخدم CategoryService بدل count_category_items مباشرة.
        conn يُمرر كـ parameter — نفس الـ connection الذي فتحه _load().
        """
        for node in nodes:
            item = QTreeWidgetItem()
            item.setText(0, node["name"])
            item.setData(0, Qt.UserRole, node["id"])
            item.setForeground(0, QColor(node["color"]))

            child_count = len(node["children"])
            item.setText(1, str(child_count) if child_count else "—")

            # [إصلاح هيكلة] استخدام CategoryService بدل count_category_items مباشرة
            try:
                from services.shared.category_service import CategoryService
                counts = CategoryService(conn).count_items(node["id"])
                total  = sum(counts.values())
            except Exception:
                total = 0
            item.setText(2, str(total) if total else "—")

            if parent is None:
                self.tree.addTopLevelItem(item)
            else:
                parent.addChild(item)

            if node["id"] in expanded:
                item.setExpanded(True)

            if node["children"]:
                self._add_items(node["children"], item, expanded, conn)

    def _selected_id(self):
        items = self.tree.selectedItems()
        return items[0].data(0, Qt.UserRole) if items else None

    def _on_select(self):
        pass

    def _edit(self):
        cat_id = self._selected_id()
        if cat_id is None:
            msg_info(self, tr("warning"), tr("category_select_first"))
            return
        self._form.load_for_edit(cat_id)

    def _delete(self):
        cat_id = self._selected_id()
        if cat_id is None:
            msg_info(self, tr("warning"), tr("category_select_first"))
            return

        try:
            conn = self._live_conn()
        except Exception as e:
            msg_warning(self, tr("error"), str(e))
            return

        from services.shared.category_service import CategoryService
        svc     = CategoryService(conn)
        preview = svc.get_delete_preview(cat_id)
        if not preview:
            return

        if confirm_delete(self, preview.cat_name,
                        extra_msg=preview.warning_text()):
            svc.delete_cascade(cat_id)
            emit_company_data_changed()