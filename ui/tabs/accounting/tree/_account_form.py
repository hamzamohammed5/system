"""
ui/tabs/accounting/tree/_account_form.py
==================================================
_AccountForm — فورم إضافة / تعديل حساب محاسبي.

[إصلاح]:
  - يرث من BaseCrudForm بدل بناء CRUD يدوي.
  - يستخدم FormGroup + CrudButtonsBar من widgets المشتركة.
  - SafeConnMixin (v3): _get_safe_conn() بدل self.conn.
"""

from PyQt5.QtWidgets import QComboBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.accounting.accounting_repo import (
    fetch_account, insert_account, update_account,
    fetch_all_groups, build_group_tree,
)
from db.accounting.accounting_schema import TYPE_AR
from ui.widgets.shared.panels import (
    BaseCrudForm, FormGroup, labeled_widget,
    RequiredLineEdit, StyledComboBox,
    get_group_box_style,
)
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
from ui.events import bus


def _get_current_company_id():
    try:
        from db.companies.company_state import company_state
        return company_state.company_id if company_state.is_ready else None
    except Exception:
        return None


def _emit_data_changed():
    cid = _get_current_company_id()
    if cid is not None:
        bus.company_data_changed.emit(cid)
    else:
        bus.data_changed.emit()


class _AccountForm(SafeConnMixin, BaseCrudForm):
    """
    فورم إضافة / تعديل حساب محاسبي.
    يرث من BaseCrudForm للحصول على منطق CRUD موحد.
    """

    FORM_TITLE      = "إضافة / تعديل حساب"
    FORM_TITLE_ICON = "📒"
    ADD_TEXT        = "➕  إضافة"
    SAVE_TEXT       = "💾  حفظ"
    CANCEL_TEXT     = "✖  إلغاء"

    def __init__(self, conn, acc_types: list, parent=None):
        self.acc_types = acc_types
        # تهيئة SafeConnMixin قبل BaseCrudForm
        self._pre_conn = conn
        super().__init__(conn, parent)
        self._init_safe_conn(conn, "accounting")

    def _post_init(self):
        """يُستدعى بعد __init__ لتهيئة إضافية."""
        self.refresh_group_combos()

    # ── بناء الحقول ───────────────────────────────────────

    def _build_fields(self, grp: FormGroup):
        self.inp_code = RequiredLineEdit()
        self.inp_code.setPlaceholderText("مثال: 1141")
        grp.add_row("الكود:", self.inp_code)

        self.inp_name = RequiredLineEdit()
        self.inp_name.setPlaceholderText("اسم الحساب...")
        grp.add_row("الاسم:", self.inp_name)

        self.cmb_type = StyledComboBox()
        for t in self.acc_types:
            self.cmb_type.addItem(TYPE_AR.get(t, t), t)
        self.cmb_type.currentIndexChanged.connect(self._on_type_changed)
        grp.add_row("النوع:", self.cmb_type)

        self.cmb_group = StyledComboBox()
        grp.add_row("التصنيف:", self.cmb_group)

    # ── CRUD hooks ────────────────────────────────────────

    def _collect(self) -> dict | None:
        if not self.inp_code.validate():
            return None
        if not self.inp_name.validate():
            return None
        return {
            "code":     self.inp_code.text_stripped(),
            "name":     self.inp_name.text_stripped(),
            "acc_type": self.cmb_type.currentData(),
            "group_id": self.cmb_group.currentData(),
        }

    def _do_insert(self, data: dict) -> int:
        conn = self._get_safe_conn()
        code      = data["code"]
        name      = data["name"]
        acc_type  = data["acc_type"]
        group_id  = data["group_id"]
        parent_id = None
        parent_code = code[:-1] if len(code) > 1 else None
        if parent_code:
            try:
                row = conn.execute(
                    "SELECT id FROM accounts WHERE code=?", (parent_code,)
                ).fetchone()
                parent_id = row["id"] if row else None
            except Exception:
                pass
        insert_account(conn, code, name, acc_type, parent_id, group_id)
        _emit_data_changed()
        return 0  # accounts لا تُرجع id مهماً هنا

    def _do_update(self, item_id: int, data: dict):
        update_account(
            self._get_safe_conn(), item_id,
            data["name"], data["group_id"]
        )
        _emit_data_changed()

    def _do_load(self, item_id: int) -> dict | None:
        return fetch_account(self._get_safe_conn(), item_id)

    def _fill_fields(self, data: dict):
        self.inp_code.setText(data["code"])
        self.inp_code.setReadOnly(True)
        self.inp_name.setText(data["name"])
        for i in range(self.cmb_type.count()):
            if self.cmb_type.itemData(i) == data["type"]:
                self.cmb_type.setCurrentIndex(i)
                break
        self._refresh_group_combo_for_type()
        for i in range(self.cmb_group.count()):
            if self.cmb_group.itemData(i) == data["group_id"]:
                self.cmb_group.setCurrentIndex(i)
                break

    def _reset_fields(self):
        self.inp_code.clear()
        self.inp_code.setReadOnly(False)
        self.inp_name.clear()

    # ── منطق التصنيفات ────────────────────────────────────

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
        self.cmb_group.addItem("— بدون تصنيف —", None)
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
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            self.cmb_group.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            self.cmb_group.setItemData(
                self.cmb_group.count() - 1,
                QColor(node["color"]), Qt.ForegroundRole
            )
            if node["children"]:
                self._add_group_nodes(node["children"], depth + 1)

    # للتوافق مع الكود الذي يستدعي load_for_edit مباشرة
    def load_for_edit(self, acc_id: int):
        super().load_for_edit(acc_id)