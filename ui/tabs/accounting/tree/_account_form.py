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
    QGroupBox, QPushButton, QLabel,
    QMessageBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor
from ui.widgets.panels.themed_inputs import ThemedLineEdit, ThemedComboBox

from services.accounting.accounts_service import AccountsService
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

        # [إصلاح dark-mode] إجبار كل الـ Themed inputs الفرعية إنها تعيد
        # تلوين نفسها صراحةً. السبب: كل ThemedLineEdit/ThemedComboBox مسجلة
        # لوحدها في bus.theme_changed عبر WidgetMixin الخاص بيها، ومفروض
        # تتلوّن تلقائيًا — لكن كإجراء دفاعي (في حال أي race condition في
        # ترتيب الإنشاء/الاتصال بالـ bus، أو استدعاء _refresh_style قبل
        # ما الـ mixin يخلص التسجيل) بننده عليها هنا صراحةً برضو، عشان
        # نضمن 100% إن كل حقول الفورم بتتلون مع الثيم مهما كان توقيت
        # التسجيل على الـ signal.
        for widget_name in ("inp_code", "inp_name", "cmb_type", "cmb_group"):
            w = getattr(self, widget_name, None)
            if w is not None and hasattr(w, "_refresh_style"):
                try:
                    w._refresh_style()
                except RuntimeError:
                    pass

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

        self.inp_code = ThemedLineEdit()
        self.inp_code.setPlaceholderText(tr("account_code_placeholder"))
        self.inp_code.setMinimumHeight(ACCOUNT_FORM_INPUT_MIN_H)
        fl.addRow(f"{tr('account_code')}:", self.inp_code)

        self.inp_name = ThemedLineEdit()
        self.inp_name.setPlaceholderText(tr("account_name_placeholder"))
        self.inp_name.setMinimumHeight(ACCOUNT_FORM_INPUT_MIN_H)
        fl.addRow(f"{tr('name')}:", self.inp_name)

        self.cmb_type = ThemedComboBox()
        self.cmb_type.setMinimumHeight(ACCOUNT_FORM_INPUT_MIN_H)
        type_labels = AccountsService(self._get_safe_conn()).get_type_labels_map()
        for t in self.acc_types:
            self.cmb_type.addItem(type_labels.get(t, t), t)
        fl.addRow(f"{tr('account_type')}:", self.cmb_type)

        self.cmb_group = ThemedComboBox()
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
            svc = AccountsService(conn)
            rows = svc.list_groups(acc_type)
            tree = svc.build_group_tree(rows)
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
        svc = AccountsService(conn)
        if parent_code:
            # [إصلاح v4] get_account_by_code بدل SQL مباشر
            parent_row = svc.get_account_by_code(parent_code)
            parent_id  = parent_row["id"] if parent_row else None
        try:
            svc.add_account(code, name, acc_type, parent_id=parent_id, group_id=group_id)
            self.inp_code.clear()
            self.inp_name.clear()
            emit_company_data_changed()
        except Exception as e:
            QMessageBox.warning(self, tr("error"), str(e))

    def load_for_edit(self, acc_id: int):
        conn = self._get_safe_conn()
        acc  = AccountsService(conn).get_account(acc_id)
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
        AccountsService(self._get_safe_conn()).update_account(
            self._editing_id, name, group_id=self.cmb_group.currentData()
        )
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