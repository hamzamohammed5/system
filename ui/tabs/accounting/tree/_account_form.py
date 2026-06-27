"""
ui/tabs/accounting/tree/_account_form.py
==================================================
_AccountForm — فورم إضافة / تعديل حساب محاسبي.
SafeConnMixin (v3): _get_safe_conn() بدل self.conn.

[إصلاح v4]:
  - استبدال SQL المباشر داخل _add() بـ fetch_account_by_code() من repo.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGroupBox, QLineEdit, QPushButton, QLabel,
    QComboBox, QMessageBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.accounting.accounting_repo import (
    fetch_account, insert_account, update_account,
    fetch_all_groups, build_group_tree,
)
from db.accounting.accounting_repo_ui_helpers import fetch_account_by_code
from db.accounting.accounting_schema import TYPE_AR
from ui.widgets.core.events import emit_company_data_changed
from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import (
    MARGIN_ZERO,
    ACCOUNT_FORM_ROOT_MARGIN, ACCOUNT_FORM_ROOT_SPACING,
    ACCOUNT_FORM_GRP_BORDER_W, ACCOUNT_FORM_GRP_BORDER_RADIUS,
    ACCOUNT_FORM_GRP_MARGIN_TOP, ACCOUNT_FORM_GRP_PAD_TOP,
    ACCOUNT_FORM_GRP_TITLE_PAD_H, ACCOUNT_FORM_FL_SPACING,
    ACCOUNT_FORM_INPUT_MIN_H, ACCOUNT_FORM_BTN_MIN_H,
)


class _AccountForm(SafeConnMixin, QWidget, WidgetMixin):
    def __init__(self, conn, acc_types: list, parent=None):
        super().__init__(parent)
        self._init_safe_conn(conn, "accounting")
        self._init_widget_mixin(lang=False, data=False)
        self.acc_types   = acc_types
        self._editing_id = None
        self._build()
        self._refresh_style()

    def _refresh_style(self, *_):
        from ui.theme import _C
        if not hasattr(self, '_grp'):
            return
        self._grp.setStyleSheet(f"""
            QGroupBox {{ font-weight:bold; color:{_C['accent']};
                border:{ACCOUNT_FORM_GRP_BORDER_W}px solid {_C['border']}; border-radius:{ACCOUNT_FORM_GRP_BORDER_RADIUS}px;
                margin-top:{ACCOUNT_FORM_GRP_MARGIN_TOP}px; padding-top:{ACCOUNT_FORM_GRP_PAD_TOP}px; }}
            QGroupBox::title {{ subcontrol-origin:margin; padding:0 {ACCOUNT_FORM_GRP_TITLE_PAD_H}px; }}
        """)
        self.lbl_form_mode.setStyleSheet(f"font-weight:bold; color:{_C['accent']};")

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(*ACCOUNT_FORM_ROOT_MARGIN)
        root.setSpacing(ACCOUNT_FORM_ROOT_SPACING)

        self._grp = QGroupBox(tr("group_add_edit_header", type_name=tr("accounts")))
        fl = QFormLayout(self._grp)
        fl.setSpacing(ACCOUNT_FORM_FL_SPACING)
        fl.setLabelAlignment(Qt.AlignRight)

        self.lbl_form_mode = QLabel(tr("account_form_new"))
        fl.addRow(self.lbl_form_mode)

        self.inp_code = QLineEdit()
        self.inp_code.setPlaceholderText(tr("account_code_placeholder"))
        self.inp_code.setMinimumHeight(ACCOUNT_FORM_INPUT_MIN_H)
        fl.addRow(f"{tr('account_code')}:", self.inp_code)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText(tr("account_name_placeholder"))
        self.inp_name.setMinimumHeight(ACCOUNT_FORM_INPUT_MIN_H)
        fl.addRow(f"{tr('name')}:", self.inp_name)

        self.cmb_type = QComboBox()
        self.cmb_type.setMinimumHeight(ACCOUNT_FORM_INPUT_MIN_H)
        for t in self.acc_types:
            self.cmb_type.addItem(TYPE_AR.get(t, t), t)
        fl.addRow(f"{tr('account_type')}:", self.cmb_type)

        self.cmb_group = QComboBox()
        self.cmb_group.setMinimumHeight(ACCOUNT_FORM_INPUT_MIN_H)
        fl.addRow(f"{tr('account_group')}:", self.cmb_group)

        self.cmb_type.currentIndexChanged.connect(self._on_type_changed)

        btn_add         = QPushButton(tr("btn_add"))
        self.btn_save   = QPushButton(tr("btn_save"))
        self.btn_cancel = QPushButton(tr("btn_cancel"))
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        for b in (btn_add, self.btn_save, self.btn_cancel):
            b.setMinimumHeight(ACCOUNT_FORM_BTN_MIN_H)
        btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save_edit)
        self.btn_cancel.clicked.connect(self._cancel_edit)

        btn_w = QWidget()
        bl    = QHBoxLayout(btn_w)
        bl.setContentsMargins(*MARGIN_ZERO)
        bl.addWidget(btn_add)
        bl.addWidget(self.btn_save)
        bl.addWidget(self.btn_cancel)
        bl.addStretch()
        fl.addRow(btn_w)

        root.addWidget(self._grp)
        root.addStretch()
        self.refresh_group_combos()

    def refresh_group_combos(self, conn=None):
        """يُستدعى من AccountsTreePanel عند تغيير الشركة."""
        self._refresh_group_combo_for_type(conn=conn)

    def _on_type_changed(self):
        self._refresh_group_combo_for_type()

    def _refresh_group_combo_for_type(self, conn=None):
        if conn is None:
            conn = self._get_safe_conn()
        acc_type = self.cmb_type.currentData()
        if not acc_type:
            return
        self.cmb_group.blockSignals(True)
        prev = self.cmb_group.currentData()
        self.cmb_group.clear()
        self.cmb_group.addItem(tr("account_group_unassigned"), None)
        try:
            rows = fetch_all_groups(conn, acc_type)
            tree = build_group_tree(rows)
            self._add_group_nodes(tree, 0)
        except Exception as e:
            print(f"[_AccountForm] refresh error: {e}")
        for i in range(self.cmb_group.count()):
            if self.cmb_group.itemData(i) == prev:
                self.cmb_group.setCurrentIndex(i)
                break
        self.cmb_group.blockSignals(False)

    def _add_group_nodes(self, nodes, depth):
        indent = "  " * depth
        arrow  = tr("tree_node_arrow") if depth > 0 else ""
        for node in nodes:
            self.cmb_group.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            self.cmb_group.setItemData(
                self.cmb_group.count() - 1,
                QColor(node["color"]), Qt.ForegroundRole
            )
            if node["children"]:
                self._add_group_nodes(node["children"], depth + 1)

    def _add(self):
        conn = self._get_safe_conn()
        code = self.inp_code.text().strip()
        name = self.inp_name.text().strip()
        if not code or not name:
            QMessageBox.warning(self, tr("warning"), tr("account_form_enter_code_name"))
            return
        acc_type    = self.cmb_type.currentData()
        group_id    = self.cmb_group.currentData()
        parent_id   = None
        parent_code = code[:-1] if len(code) > 1 else None
        if parent_code:
            # [إصلاح v4] fetch_account_by_code بدل SQL مباشر
            parent_row = fetch_account_by_code(conn, parent_code)
            parent_id  = parent_row["id"] if parent_row else None
        try:
            insert_account(conn, code, name, acc_type, parent_id, group_id)
            self.inp_code.clear()
            self.inp_name.clear()
            emit_company_data_changed()
        except Exception as e:
            QMessageBox.warning(self, tr("error"), str(e))

    def load_for_edit(self, acc_id: int):
        conn = self._get_safe_conn()
        acc  = fetch_account(conn, acc_id)
        if not acc:
            return
        self._editing_id = acc_id
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
        self.lbl_form_mode.setText(tr("account_form_edit", name=acc["name"]))
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)

    def _save_edit(self):
        name = self.inp_name.text().strip()
        if not name or not self._editing_id:
            return
        update_account(self._get_safe_conn(), self._editing_id, name,
                       self.cmb_group.currentData())
        self._cancel_edit()
        emit_company_data_changed()

    def _cancel_edit(self):
        self._editing_id = None
        self.inp_code.clear()
        self.inp_code.setReadOnly(False)
        self.inp_name.clear()
        self.lbl_form_mode.setText(tr("account_form_new"))
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)