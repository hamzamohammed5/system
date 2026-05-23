"""
ui/tabs/accounting/tree/_account_form.py
==================================================
_AccountForm — فورم إضافة / تعديل حساب محاسبي.

تغييرات (v2):
  - يبعت bus.company_data_changed بدل bus.data_changed العام.
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
from db.accounting.accounting_schema import TYPE_AR
from ui.helpers import danger_button
from ui.events  import bus


def _get_current_company_id():
    try:
        from db.companies.company_state import company_state
        return company_state.company_id if company_state.is_ready else None
    except Exception:
        return None


def _emit_data_changed():
    """يُطلق الحدث المقيّد بالشركة النشطة."""
    cid = _get_current_company_id()
    if cid is not None:
        bus.company_data_changed.emit(cid)
    else:
        bus.data_changed.emit()


class _AccountForm(QWidget):
    """فورم إضافة وتعديل الحسابات على يمين الشجرة."""

    def __init__(self, conn, acc_types: list, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self.acc_types   = acc_types
        self._editing_id = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 8, 10, 10)
        root.setSpacing(8)

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

        root.addWidget(grp)
        root.addStretch()
        self.refresh_group_combos()

    # ── Combo التصنيفات ──────────────────────────────────

    def refresh_group_combos(self):
        self._refresh_group_combo_for_type()

    def _on_type_changed(self):
        self._refresh_group_combo_for_type()

    def _refresh_group_combo_for_type(self):
        acc_type = self.cmb_type.currentData()
        if not acc_type:
            return
        self.cmb_group.blockSignals(True)
        prev = self.cmb_group.currentData()
        self.cmb_group.clear()
        self.cmb_group.addItem("— بدون تصنيف —", None)
        try:
            rows = fetch_all_groups(self.conn, acc_type)
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

    # ── CRUD ─────────────────────────────────────────────

    def _add(self):
        code = self.inp_code.text().strip()
        name = self.inp_name.text().strip()
        if not code or not name:
            QMessageBox.warning(self, "تنبيه", "أدخل الكود والاسم")
            return
        acc_type  = self.cmb_type.currentData()
        group_id  = self.cmb_group.currentData()
        parent_id = None
        parent_code = code[:-1] if len(code) > 1 else None
        if parent_code:
            try:
                row = self.conn.execute(
                    "SELECT id FROM accounts WHERE code=?", (parent_code,)
                ).fetchone()
                parent_id = row["id"] if row else None
            except Exception:
                pass
        try:
            insert_account(self.conn, code, name, acc_type, parent_id, group_id)
            self.inp_code.clear()
            self.inp_name.clear()
            _emit_data_changed()
        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))

    def load_for_edit(self, acc_id: int):
        acc = fetch_account(self.conn, acc_id)
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
        _emit_data_changed()

    def _cancel_edit(self):
        self._editing_id = None
        self.inp_code.clear()
        self.inp_code.setReadOnly(False)
        self.inp_name.clear()
        self.lbl_form_mode.setText("── حساب جديد ──")
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)