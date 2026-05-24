"""
ui/tabs/accounting/group_manager.py
=====================================
_GroupManagerPanel — إدارة تصنيفات الحسابات.
SafeConnMixin (v3): _get_safe_conn() بدل self.conn في كل query.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QTreeWidget, QTreeWidgetItem, QGroupBox,
    QLineEdit, QPushButton, QLabel, QColorDialog, QMessageBox,
    QHeaderView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.accounting.accounting_repo import (
    fetch_all_groups, fetch_group,
    insert_group, update_group, delete_group,
    build_group_tree,
)
from db.accounting.accounting_schema import TYPE_AR
from ui.helpers import section_label, danger_button
from ui.events  import bus
from ui.tabs.accounting.safe_conn_mixin import SafeConnMixin


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
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        root.addWidget(section_label(
            f"── تصنيفات {TYPE_AR.get(self.acc_type, '')} ──"
        ))

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["التصنيف", "عدد الحسابات"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Interactive)
        self.tree.setColumnWidth(1, 100)
        self.tree.setAlternatingRowColors(True)
        root.addWidget(self.tree, stretch=1)

        btn_row  = QHBoxLayout()
        btn_edit = QPushButton("✏️ تعديل")
        btn_del  = danger_button("🗑️ حذف")
        for b in (btn_edit, btn_del):
            b.setMinimumHeight(28)
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        btn_row.addWidget(btn_edit)
        btn_row.addWidget(btn_del)
        btn_row.addStretch()
        root.addLayout(btn_row)

        grp = QGroupBox("➕ إضافة / تعديل تصنيف")
        grp.setStyleSheet("""
            QGroupBox { font-weight:bold; color:#1565c0;
                border:1px solid #e0e0e0; border-radius:6px;
                margin-top:6px; padding-top:6px; }
            QGroupBox::title { subcontrol-origin:margin; padding:0 6px; }
        """)
        fl = QFormLayout(grp)
        fl.setSpacing(8)
        fl.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = QLabel("── تصنيف جديد ──")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0;")
        fl.addRow(self.lbl_mode)

        self.inp_name = QLineEdit()
        self.inp_name.setMinimumHeight(28)
        fl.addRow("الاسم:", self.inp_name)

        self.cmb_parent = self._make_combo()
        self.cmb_parent.setMinimumHeight(28)
        fl.addRow("تابع لـ:", self.cmb_parent)

        color_row      = QHBoxLayout()
        self._color    = "#607d8b"
        self.lbl_color = QLabel()
        self.lbl_color.setFixedSize(26, 26)
        self.lbl_color.setStyleSheet(
            f"background:{self._color}; border-radius:4px; border:1px solid #ccc;"
        )
        btn_color = QPushButton("اختر لون")
        btn_color.setMinimumHeight(26)
        btn_color.clicked.connect(self._pick_color)
        color_row.addWidget(self.lbl_color)
        color_row.addWidget(btn_color)
        color_row.addStretch()
        fl.addRow("اللون:", color_row)

        self.btn_add    = QPushButton("➕ إضافة")
        self.btn_save   = QPushButton("💾 حفظ")
        self.btn_cancel = QPushButton("✖ إلغاء")
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        for b in (self.btn_add, self.btn_save, self.btn_cancel):
            b.setMinimumHeight(28)
        self.btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save_edit)
        self.btn_cancel.clicked.connect(self._reset)

        btn_w = QWidget()
        bl    = QHBoxLayout(btn_w)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.addWidget(self.btn_add)
        bl.addWidget(self.btn_save)
        bl.addWidget(self.btn_cancel)
        bl.addStretch()
        fl.addRow(btn_w)
        root.addWidget(grp)

    def _make_combo(self):
        from PyQt5.QtWidgets import QComboBox
        return QComboBox()

    def _load(self):
        conn = self._get_safe_conn()
        self.tree.clear()
        rows = fetch_all_groups(conn, self.acc_type)
        tree = build_group_tree(rows)
        self._add_tree_nodes(tree, None)
        self.tree.expandAll()
        self._refresh_parent_combo()

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
            item.setText(1, str(count) if count else "—")
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
        self.cmb_parent.addItem("— بدون أب (رئيسي) —", None)
        rows = fetch_all_groups(conn, self.acc_type)
        tree = build_group_tree(rows)
        self._add_parent_nodes(tree, 0, exclude_id)
        self.cmb_parent.blockSignals(False)

    def _add_parent_nodes(self, nodes, depth, exclude_id):
        indent = "  " * depth
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            if node["id"] == exclude_id:
                continue
            self.cmb_parent.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            if node["children"]:
                self._add_parent_nodes(node["children"], depth + 1, exclude_id)

    def _pick_color(self):
        col = QColorDialog.getColor(QColor(self._color), self, "اختر لون")
        if col.isValid():
            self._color = col.name()
            self.lbl_color.setStyleSheet(
                f"background:{self._color}; border-radius:4px; border:1px solid #ccc;"
            )

    def _selected_id(self):
        items = self.tree.selectedItems()
        return items[0].data(0, Qt.UserRole) if items else None

    def _add(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم التصنيف")
            return
        insert_group(self._get_safe_conn(), name, self.acc_type,
                     self.cmb_parent.currentData(), self._color)
        self._reset()
        bus.company_data_changed.emit(self._company_id or 0)

    def _edit(self):
        gid = self._selected_id()
        if not gid:
            QMessageBox.information(self, "تنبيه", "اختر تصنيفًا أولًا")
            return
        grp = fetch_group(self._get_safe_conn(), gid)
        if not grp:
            return
        self._editing_id = gid
        self.inp_name.setText(grp["name"])
        self._color = grp["color"]
        self.lbl_color.setStyleSheet(
            f"background:{self._color}; border-radius:4px; border:1px solid #ccc;"
        )
        self._refresh_parent_combo(exclude_id=gid)
        for i in range(self.cmb_parent.count()):
            if self.cmb_parent.itemData(i) == grp["parent_id"]:
                self.cmb_parent.setCurrentIndex(i)
                break
        self.lbl_mode.setText(f"── تعديل: {grp['name']} ──")
        self.btn_add.setVisible(False)
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)

    def _save_edit(self):
        name = self.inp_name.text().strip()
        if not name or not self._editing_id:
            return
        update_group(self._get_safe_conn(), self._editing_id, name,
                     self.cmb_parent.currentData(), self._color)
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
        msg = f"حذف تصنيف «{grp['name']}»؟"
        if count:
            msg += f"\n⚠️ {count} حساب سيفقد تصنيفه."
        if QMessageBox.question(self, "تأكيد", msg,
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            delete_group(conn, gid)
            bus.company_data_changed.emit(self._company_id or 0)

    def _reset(self):
        self._editing_id = None
        self.inp_name.clear()
        self._color = "#607d8b"
        self.lbl_color.setStyleSheet(
            "background:#607d8b; border-radius:4px; border:1px solid #ccc;"
        )
        self.lbl_mode.setText("── تصنيف جديد ──")
        self.btn_add.setVisible(True)
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        self._refresh_parent_combo()