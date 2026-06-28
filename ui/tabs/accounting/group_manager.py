"""
ui/tabs/accounting/group_manager.py
=====================================
_GroupManagerPanel — إدارة تصنيفات الحسابات.

[تحسين v5]:
  - ColorPickerWidget بدل لون picker مكرر يدوياً.
  - باقي التحسينات كما هي (FormGroup, ModeLabel, SafeConnMixin).
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem,
    QLineEdit, QMessageBox,
    QComboBox, QHeaderView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.accounting.accounting_repo import (
    fetch_all_groups, fetch_group,
    insert_group, update_group, delete_group,
    build_group_tree,
)
from db.accounting.accounting_schema import TYPE_AR
from ui.widgets.core.events import bus
from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.helpers.color_picker import ColorPickerWidget
from ui.widgets.components.headers_page import SectionHeader
from ui.widgets.components.button import make_btn as _make_btn
from ui.widgets.components.headers_list import StatusBar as ListStatusBar
from ui.widgets.theme.layout_styles import tree_style as get_tree_style
from ui.widgets.dialogs.confirm import confirm_delete
from ui.widgets.panels.form_group import FormGroup
from ui.widgets.components.label import ModeLabel
from ui.widgets.core.i18n import tr
from ui.widgets.dialogs.message import msg_warning, msg_info
from ui.constants import (
    GROUP_MGR_ROOT_MARGIN, GROUP_MGR_ROOT_SPACING,
    GROUP_MGR_COL_COUNT_W, GROUP_MGR_INPUT_MIN_H,
)


class _GroupManagerPanel(SafeConnMixin, QWidget):
    def __init__(self, conn, acc_type: str, parent=None):
        super().__init__(parent)
        self._init_safe_conn(conn, "accounting")
        self.acc_type    = acc_type
        self._editing_id = None
        self._company_id = self._get_company_id()
        self._build()
        self._load()
        bus.company_data_changed.connect(self._on_company_event)

    def _on_company_event(self, company_id: int):
        if self._on_company_event_safe(company_id):
            self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(*GROUP_MGR_ROOT_MARGIN)
        root.setSpacing(GROUP_MGR_ROOT_SPACING)

        # ── هيدر القسم ──
        hdr = SectionHeader(tr("group_categories_header", type_name=TYPE_AR.get(self.acc_type, '')))
        root.addWidget(hdr)

        # ── الشجرة ──
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([tr("group_tree_col"), tr("group_count_col")])
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Interactive)
        self.tree.setColumnWidth(1, GROUP_MGR_COL_COUNT_W)
        self.tree.setAlternatingRowColors(True)
        self.tree.setStyleSheet(get_tree_style())
        root.addWidget(self.tree, stretch=1)

        # ── أزرار التعديل والحذف ──
        btn_row  = QHBoxLayout()
        btn_edit = _make_btn(tr("btn_edit"), "normal")
        btn_del  = _make_btn(tr("btn_delete"),  "danger")
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        btn_row.addWidget(btn_edit)
        btn_row.addWidget(btn_del)
        btn_row.addStretch()
        root.addLayout(btn_row)

        # ── شريط الحالة ──
        self._status = ListStatusBar()
        root.addWidget(self._status)

        # ── فورم الإضافة/التعديل (FormGroup الموحد) ──
        grp = FormGroup(tr("group_add_edit_header", type_name=TYPE_AR.get(self.acc_type, '')))

        self._lbl_mode = ModeLabel(add_text=tr("group_new_placeholder"))
        grp.add_label_row(self._lbl_mode)

        self.inp_name = QLineEdit()
        self.inp_name.setMinimumHeight(GROUP_MGR_INPUT_MIN_H)
        self.inp_name.setPlaceholderText(tr("group_name_placeholder"))
        grp.add_row(tr("name") + ":", self.inp_name)

        self.cmb_parent = QComboBox()
        self.cmb_parent.setMinimumHeight(GROUP_MGR_INPUT_MIN_H)
        grp.add_row(tr("group_parent_label"), self.cmb_parent)

        # ── ColorPickerWidget الموحد ──
        self._color_picker = ColorPickerWidget(default=tr("group_default_color"))
        grp.add_row(tr("group_color_label"), self._color_picker)

        # ── أزرار الفورم ──
        btn_w = QWidget()
        btn_w.setStyleSheet("background: transparent;")
        bl    = QHBoxLayout(btn_w)
        bl.setContentsMargins(0, 0, 0, 0)
        self.btn_add    = _make_btn(tr("btn_add"), "primary")
        self.btn_save   = _make_btn(tr("btn_save"),  "success")
        self.btn_cancel = _make_btn(tr("btn_cancel"), "ghost")
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        self.btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save_edit)
        self.btn_cancel.clicked.connect(self._reset)
        bl.addWidget(self.btn_add)
        bl.addWidget(self.btn_save)
        bl.addWidget(self.btn_cancel)
        bl.addStretch()
        grp.add_label_row(btn_w)

        root.addWidget(grp)

    def _load(self):
        conn = self._get_safe_conn()
        self.tree.clear()
        rows = fetch_all_groups(conn, self.acc_type)
        tree = build_group_tree(rows)
        self._add_tree_nodes(tree, None)
        self.tree.expandAll()
        self._refresh_parent_combo()

        total = self.tree.topLevelItemCount()
        self._status.set_count(total, total)

    def _add_tree_nodes(self, nodes, parent):
        conn = self._get_safe_conn()
        for node in nodes:
            try:
                count = conn.execute(
                    "SELECT COUNT(*) as c FROM accounts WHERE group_id=? AND is_leaf=1",
                    (node["id"],)
                ).fetchone()["c"]
            except Exception:
                count = 0
            item = QTreeWidgetItem()
            item.setText(0, node["name"])
            item.setText(1, str(count) if count else tr("dash"))
            item.setData(0, Qt.UserRole, node["id"])
            item.setForeground(0, QColor(node["color"]))
            if parent:
                parent.addChild(item)
            else:
                self.tree.addTopLevelItem(item)
            if node["children"]:
                self._add_tree_nodes(node["children"], item)

    def _refresh_parent_combo(self, exclude_id=None):
        conn = self._get_safe_conn()
        self.cmb_parent.blockSignals(True)
        self.cmb_parent.clear()
        self.cmb_parent.addItem(tr("group_without_parent"), None)
        rows = fetch_all_groups(conn, self.acc_type)
        tree = build_group_tree(rows)
        self._add_parent_nodes(tree, 0, exclude_id)
        self.cmb_parent.blockSignals(False)

    def _add_parent_nodes(self, nodes, depth, exclude_id):
        indent = "  " * depth
        arrow  = tr("category_tree_arrow") if depth > 0 else ""
        for node in nodes:
            if node["id"] == exclude_id:
                continue
            self.cmb_parent.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            if node["children"]:
                self._add_parent_nodes(node["children"], depth + 1, exclude_id)

    def _selected_id(self):
        items = self.tree.selectedItems()
        return items[0].data(0, Qt.UserRole) if items else None

    def _add(self):
        name = self.inp_name.text().strip()
        if not name:
            msg_warning(self, tr("warning"), tr("category_name_required"))
            return
        insert_group(self._get_safe_conn(), name, self.acc_type,
                     self.cmb_parent.currentData(),
                     self._color_picker.current_color())
        self._reset()
        bus.company_data_changed.emit(self._company_id or 0)

    def _edit(self):
        gid = self._selected_id()
        if not gid:
            msg_info(self, tr("warning"), tr("select_category_first"))
            return
        grp = fetch_group(self._get_safe_conn(), gid)
        if not grp:
            return
        self._editing_id = gid
        self.inp_name.setText(grp["name"])
        self._color_picker.set_color(grp["color"])
        self._refresh_parent_combo(exclude_id=gid)
        for i in range(self.cmb_parent.count()):
            if self.cmb_parent.itemData(i) == grp["parent_id"]:
                self.cmb_parent.setCurrentIndex(i)
                break
        self._lbl_mode.set_edit_mode(grp["name"])
        self.btn_add.setVisible(False)
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)

    def _save_edit(self):
        name = self.inp_name.text().strip()
        if not name or not self._editing_id:
            return
        update_group(self._get_safe_conn(), self._editing_id, name,
                     self.cmb_parent.currentData(),
                     self._color_picker.current_color())
        self._reset()
        bus.company_data_changed.emit(self._company_id or 0)

    def _delete(self):
        gid  = self._selected_id()
        if not gid:
            return
        conn = self._get_safe_conn()
        grp  = fetch_group(conn, gid)
        try:
            count = conn.execute(
                "SELECT COUNT(*) as c FROM accounts WHERE group_id=?", (gid,)
            ).fetchone()["c"]
        except Exception:
            count = 0

        extra = tr("group_delete_accounts_warn", count=count) if count else ""
        if confirm_delete(self, grp["name"], extra_msg=extra):
            delete_group(conn, gid)
            bus.company_data_changed.emit(self._company_id or 0)

    def _reset(self):
        self._editing_id = None
        self.inp_name.clear()
        self._color_picker.set_color(tr("group_default_color"))
        self._lbl_mode.set_add_mode()
        self.btn_add.setVisible(True)
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        self._refresh_parent_combo()