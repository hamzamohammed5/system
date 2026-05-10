"""
ui/tabs/accounting/accounts_tree.py
=====================================
AccountsTreePanel — شجرة الحسابات مع فورم الإضافة والتعديل.

الإصلاح: منع الـ recursive calls بين _load و _refresh_group_combos
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QTreeWidget, QTreeWidgetItem, QGroupBox, QSplitter,
    QLineEdit, QPushButton, QLabel, QComboBox, QMessageBox,
    QHeaderView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor, QFont

from db.accounting_repo import (
    fetch_all_accounts, fetch_account,
    insert_account, update_account, delete_account,
    get_account_balance, get_normal_balance,
    fetch_all_groups, build_group_tree,
)
from db.accounting_schema import TYPE_AR
from ui.helpers import section_label, danger_button, confirm_delete
from ui.events  import bus
from .helpers   import TYPE_COLORS


class AccountsTreePanel(QWidget):
    def __init__(self, conn, acc_types: list, title: str, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self.acc_types   = acc_types
        self.title       = title
        self._editing_id = None
        self._loading    = False   # ← flag لمنع الـ recursive calls
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(5)

        # ── يسار: الشجرة ──
        left = QWidget()
        ll   = QVBoxLayout(left)
        ll.setContentsMargins(10, 8, 6, 10)
        ll.setSpacing(6)
        ll.addWidget(section_label(f"── {self.title} ──"))

        filter_row = QHBoxLayout()
        self.cmb_group_filter = QComboBox()
        self.cmb_group_filter.setMinimumHeight(26)
        self.cmb_group_filter.addItem("— كل التصنيفات —", None)
        # ← نربط بـ _on_filter_changed مش _load مباشرة
        self.cmb_group_filter.currentIndexChanged.connect(self._on_filter_changed)
        filter_row.addWidget(QLabel("🏷"))
        filter_row.addWidget(self.cmb_group_filter, stretch=1)
        ll.addLayout(filter_row)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["الكود", "اسم الحساب", "الرصيد"])
        hh = self.tree.header()
        hh.setSectionResizeMode(0, QHeaderView.Interactive)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Interactive)
        self.tree.setColumnWidth(0, 70)
        self.tree.setColumnWidth(2, 110)
        self.tree.setAlternatingRowColors(True)
        ll.addWidget(self.tree, stretch=1)

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
        ll.addLayout(btn_row)
        splitter.addWidget(left)

        # ── يمين: فورم الإضافة ──
        right = QWidget()
        rl    = QVBoxLayout(right)
        rl.setContentsMargins(6, 8, 10, 10)
        rl.setSpacing(8)

        grp = QGroupBox("➕ إضافة / تعديل حساب")
        grp.setStyleSheet("""
            QGroupBox { font-weight:bold; color:#1565c0;
                border:1px solid #e0e0e0; border-radius:6px;
                margin-top:8px; padding-top:8px; }
            QGroupBox::title { subcontrol-origin:margin; padding:0 6px; }
        """)
        fl = QFormLayout(grp)
        fl.setSpacing(8)
        fl.setLabelAlignment(Qt.AlignRight)

        self.lbl_form_mode = QLabel("── حساب جديد ──")
        self.lbl_form_mode.setStyleSheet("font-weight:bold; color:#1565c0;")
        fl.addRow(self.lbl_form_mode)

        self.inp_code = QLineEdit()
        self.inp_code.setPlaceholderText("مثال: 1141")
        self.inp_code.setMinimumHeight(28)
        fl.addRow("الكود:", self.inp_code)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم الحساب...")
        self.inp_name.setMinimumHeight(28)
        fl.addRow("الاسم:", self.inp_name)

        self.cmb_type = QComboBox()
        self.cmb_type.setMinimumHeight(28)
        for t in self.acc_types:
            self.cmb_type.addItem(TYPE_AR.get(t, t), t)
        fl.addRow("النوع:", self.cmb_type)

        self.cmb_group = QComboBox()
        self.cmb_group.setMinimumHeight(28)
        fl.addRow("التصنيف:", self.cmb_group)

        # ربط signal بعد ما cmb_group اتعمل
        self.cmb_type.currentIndexChanged.connect(self._on_type_changed)

        btn_add         = QPushButton("➕ إضافة")
        self.btn_save   = QPushButton("💾 حفظ")
        self.btn_cancel = QPushButton("✖ إلغاء")
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        for b in (btn_add, self.btn_save, self.btn_cancel):
            b.setMinimumHeight(28)
        btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save_edit)
        self.btn_cancel.clicked.connect(self._cancel_edit)

        btn_w = QWidget()
        bl    = QHBoxLayout(btn_w)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.addWidget(btn_add)
        bl.addWidget(self.btn_save)
        bl.addWidget(self.btn_cancel)
        bl.addStretch()
        fl.addRow(btn_w)
        rl.addWidget(grp)
        rl.addStretch()
        splitter.addWidget(right)
        splitter.setSizes([420, 280])

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(splitter)

        # نحدّث الـ combos بعد بناء كل الـ widgets
        self._refresh_group_combos()

    # ══════════════════════════════════════════════════════
    # فلتر التصنيف — منفصل عن _load
    # ══════════════════════════════════════════════════════

    def _on_filter_changed(self):
        """يُستدعى فقط لما المستخدم يغير الفلتر — مش من _load."""
        if self._loading:
            return
        self._build_tree()

    def _on_type_changed(self):
        self._refresh_group_combo_for_type()

    # ══════════════════════════════════════════════════════
    # تحديث combos التصنيفات
    # ══════════════════════════════════════════════════════

    def _refresh_group_combos(self):
        """يحدّث combo الفلتر وcombo الفورم — بدون إطلاق signals."""
        # ── فلتر الشجرة ──
        self.cmb_group_filter.blockSignals(True)
        prev = self.cmb_group_filter.currentData()
        self.cmb_group_filter.clear()
        self.cmb_group_filter.addItem("— كل التصنيفات —", None)
        for t in self.acc_types:
            rows = fetch_all_groups(self.conn, t)
            tree = build_group_tree(rows)
            self._add_filter_nodes(tree, 0)
        # استعادة الاختيار السابق
        for i in range(self.cmb_group_filter.count()):
            if self.cmb_group_filter.itemData(i) == prev:
                self.cmb_group_filter.setCurrentIndex(i)
                break
        self.cmb_group_filter.blockSignals(False)

        # ── combo النوع في الفورم ──
        self._refresh_group_combo_for_type()

    def _add_filter_nodes(self, nodes, depth):
        indent = "  " * depth
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            self.cmb_group_filter.addItem(
                f"{indent}{arrow}{node['name']}", node["id"]
            )
            self.cmb_group_filter.setItemData(
                self.cmb_group_filter.count() - 1,
                QColor(node["color"]), Qt.ForegroundRole
            )
            if node["children"]:
                self._add_filter_nodes(node["children"], depth + 1)

    def _refresh_group_combo_for_type(self):
        acc_type = self.cmb_type.currentData()
        if not acc_type:
            return
        self.cmb_group.blockSignals(True)
        prev = self.cmb_group.currentData()
        self.cmb_group.clear()
        self.cmb_group.addItem("— بدون تصنيف —", None)
        rows = fetch_all_groups(self.conn, acc_type)
        tree = build_group_tree(rows)
        self._add_group_nodes_to_combo(tree, 0)
        for i in range(self.cmb_group.count()):
            if self.cmb_group.itemData(i) == prev:
                self.cmb_group.setCurrentIndex(i)
                break
        self.cmb_group.blockSignals(False)

    def _add_group_nodes_to_combo(self, nodes, depth):
        indent = "  " * depth
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            self.cmb_group.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            self.cmb_group.setItemData(
                self.cmb_group.count() - 1,
                QColor(node["color"]), Qt.ForegroundRole
            )
            if node["children"]:
                self._add_group_nodes_to_combo(node["children"], depth + 1)

    # ══════════════════════════════════════════════════════
    # تحميل البيانات
    # ══════════════════════════════════════════════════════

    def _load(self):
        """يُستدعى عند التهيئة وعند bus.data_changed — يحدّث combos والشجرة."""
        if self._loading:
            return
        self._loading = True
        try:
            self._refresh_group_combos()
            self._build_tree()
        finally:
            self._loading = False

    def _build_tree(self):
        """يبني الشجرة بناءً على الفلتر الحالي — بدون تحديث combos."""
        self.tree.clear()
        gid_filter = self.cmb_group_filter.currentData()

        for acc_type in self.acc_types:
            try:
                rows = fetch_all_accounts(self.conn, acc_type)
            except Exception:
                rows = []

            # بناء شجرة الحسابات
            nodes = {r["id"]: dict(r) for r in rows}
            roots = []
            for nid, node in nodes.items():
                pid = node["parent_id"]
                if pid and pid in nodes:
                    nodes[pid].setdefault("children", []).append(node)
                else:
                    roots.append(node)

            # فلتر بالتصنيف لو محدد
            if gid_filter is not None:
                roots = self._filter_by_group(roots, gid_filter)

            if not roots:
                continue

            type_item = QTreeWidgetItem()
            type_item.setText(1, f"── {TYPE_AR.get(acc_type, acc_type)} ──")
            type_item.setForeground(1, QColor(TYPE_COLORS.get(acc_type, "#333")))
            f = type_item.font(1)
            f.setBold(True)
            type_item.setFont(1, f)
            self.tree.addTopLevelItem(type_item)
            self._add_acc_nodes(roots, type_item)
            type_item.setExpanded(True)

        self.tree.expandToDepth(2)

    def _filter_by_group(self, nodes: list, gid: int) -> list:
        """يفلتر الحسابات اللي group_id بتاعها = gid أو أبناءه."""
        from db.accounting_repo import _get_group_descendants
        desc = _get_group_descendants(self.conn, gid)

        result = []
        for node in nodes:
            if node.get("group_id") in desc:
                result.append(node)
            elif node.get("children"):
                filtered_children = self._filter_by_group(
                    node["children"], gid
                )
                if filtered_children:
                    node = dict(node)
                    node["children"] = filtered_children
                    result.append(node)
        return result

    def _add_acc_nodes(self, nodes, parent):
        for node in nodes:
            bal   = get_account_balance(self.conn, node["id"])
            color = TYPE_COLORS.get(node["type"], "#333")
            item  = QTreeWidgetItem()
            item.setText(0, node["code"])
            item.setText(1, node["name"])
            item.setText(2, f"{bal:,.2f}")
            item.setData(0, Qt.UserRole, node["id"])
            item.setForeground(0, QColor(color))
            if node.get("group_name"):
                item.setToolTip(1, f"{node['name']}  |  🏷 {node['group_name']}")
            if not node.get("is_leaf", 1):
                f = item.font(1)
                f.setBold(True)
                item.setFont(1, f)
            if bal < 0:
                item.setForeground(2, QColor("#c62828"))
            elif bal > 0:
                item.setForeground(2, QColor("#2e7d32"))
            if parent:
                parent.addChild(item)
            else:
                self.tree.addTopLevelItem(item)
            if node.get("children"):
                self._add_acc_nodes(node["children"], item)

    # ══════════════════════════════════════════════════════
    # CRUD
    # ══════════════════════════════════════════════════════

    def _selected_id(self):
        items = self.tree.selectedItems()
        if not items:
            return None
        return items[0].data(0, Qt.UserRole)

    def _add(self):
        code = self.inp_code.text().strip()
        name = self.inp_name.text().strip()
        if not code or not name:
            QMessageBox.warning(self, "تنبيه", "أدخل الكود والاسم")
            return
        acc_type    = self.cmb_type.currentData()
        group_id    = self.cmb_group.currentData()
        parent_code = code[:-1] if len(code) > 1 else None
        parent_id   = None
        if parent_code:
            try:
                row = self.conn.execute(
                    "SELECT id FROM accounts WHERE code=?", (parent_code,)
                ).fetchone()
                parent_id = row["id"] if row else None
            except Exception:
                parent_id = None
        try:
            insert_account(self.conn, code, name, acc_type, parent_id, group_id)
            self.inp_code.clear()
            self.inp_name.clear()
            bus.data_changed.emit()
        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))

    def _edit(self):
        aid = self._selected_id()
        if not aid:
            QMessageBox.information(self, "تنبيه", "اختر حسابًا أولًا")
            return
        acc = fetch_account(self.conn, aid)
        if not acc:
            return
        self._editing_id = aid
        self.inp_code.setText(acc["code"])
        self.inp_code.setReadOnly(True)
        self.inp_name.setText(acc["name"])
        for i in range(self.cmb_type.count()):
            if self.cmb_type.itemData(i) == acc["type"]:
                self.cmb_type.setCurrentIndex(i)
                break
        self._refresh_group_combo_for_type()
        for i in range(self.cmb_group.count()):
            if self.cmb_group.itemData(i) == acc["group_id"]:
                self.cmb_group.setCurrentIndex(i)
                break
        self.lbl_form_mode.setText(f"── تعديل: {acc['name']} ──")
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)

    def _save_edit(self):
        name = self.inp_name.text().strip()
        if not name or not self._editing_id:
            return
        update_account(self.conn, self._editing_id, name,
                       self.cmb_group.currentData())
        self._cancel_edit()
        bus.data_changed.emit()

    def _cancel_edit(self):
        self._editing_id = None
        self.inp_code.clear()
        self.inp_code.setReadOnly(False)
        self.inp_name.clear()
        self.lbl_form_mode.setText("── حساب جديد ──")
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)

    def _delete(self):
        aid = self._selected_id()
        if not aid:
            return
        acc = fetch_account(self.conn, aid)
        if not acc:
            return
        try:
            has = self.conn.execute(
                "SELECT COUNT(*) as c FROM journal_lines WHERE account_id=?",
                (aid,)
            ).fetchone()["c"]
        except Exception:
            has = 0
        if has:
            QMessageBox.warning(
                self, "تحذير",
                f"الحساب «{acc['name']}» له {has} حركة — لا يمكن حذفه."
            )
            return
        if confirm_delete(self, acc["name"]):
            delete_account(self.conn, aid)
            bus.data_changed.emit()