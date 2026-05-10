"""
ui/tabs/accounting/journal_tab.py  — مع ربط المستثمرين
=========================================================
التغييرات عن النسخة السابقة:
  1. _SmartLine: لما الحساب capital/drawings → يظهر combo اختيار المستثمر
  2. _JournalForm._save: لما يحفظ القيد → يسجل ربط المستثمر تلقائياً
  3. باقي الكود بدون تغيير جوهري
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QSplitter, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QAbstractItemView,
    QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox,
    QScrollArea, QRadioButton, QButtonGroup,
    QDialog, QApplication,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QDate, QTimer, QPoint
from PyQt5.QtGui  import QColor, QFont, QBrush

from db.accounting_repo import (
    fetch_all_entries, fetch_entry_lines,
    insert_entry, add_entry_lines,
    delete_entry, validate_entry_balance,
    fetch_account, fetch_all_accounts,
    fetch_all_groups, build_group_tree,
    get_normal_balance,
)
from db.accounting_schema import NORMAL_BALANCE, TYPE_AR
from ui.helpers import (
    make_table, setup_table_columns, buttons_row,
    section_label, danger_button, confirm_delete,
)
from ui.events import bus
from .helpers  import TYPE_COLORS

# ── ثوابت ──────────────────────────────────────────────

_TYPE_ORDER = ["asset", "liability", "capital", "drawings", "revenue", "expense"]

_TYPE_ICONS = {
    "asset":     "🏦",
    "liability": "📋",
    "capital":   "👑",
    "drawings":  "💸",
    "revenue":   "💹",
    "expense":   "📤",
}

# الأنواع التي تستدعي ربط المستثمر
_INVESTOR_TYPES = {"capital", "drawings"}


# ══════════════════════════════════════════════════════════
# منطق التوجيه التلقائي
# ══════════════════════════════════════════════════════════

def _resolve_side(acc_type: str, is_increase: bool) -> str:
    nb = NORMAL_BALANCE.get(acc_type, "dr")
    return nb if is_increase else ("cr" if nb == "dr" else "dr")


# ══════════════════════════════════════════════════════════
# Popup قائمة الحسابات
# ══════════════════════════════════════════════════════════

class _AccountTreePopup(QDialog):
    def __init__(self, conn, acc_types=None, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.conn           = conn
        self.acc_types      = acc_types or _TYPE_ORDER
        self._selected_id   = None
        self._selected_name = None
        self._expanded: set = set()
        for t in self.acc_types:
            self._expanded.add(f"type:{t}")
        self._all_accounts = []
        self._filter_text  = ""
        self._build()
        self._load_accounts()

    def _build(self):
        self.setMinimumWidth(420)
        self.setMaximumHeight(480)
        self.setStyleSheet("""
            QDialog {
                background: white;
                border: 1px solid #c5cae9;
                border-radius: 8px;
            }
        """)
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(4)

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 بحث بالاسم أو الكود...")
        self.inp_search.setMinimumHeight(30)
        self.inp_search.setStyleSheet("""
            QLineEdit {
                background: #f0f4ff; border: 1px solid #c5cae9;
                border-radius: 4px; padding: 2px 8px; font-size: 12px;
            }
            QLineEdit:focus { border-color: #1565c0; background: white; }
        """)
        self.inp_search.textChanged.connect(self._on_search)
        root.addWidget(self.inp_search)

        from PyQt5.QtWidgets import QListWidget, QListWidgetItem
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget { border: 1px solid #e0e0e0; border-radius: 4px;
                          background: white; outline: none; }
            QListWidget::item { padding: 3px 6px; border-bottom: 1px solid #f0f0f0; }
            QListWidget::item:selected { background: #e3f2fd; color: #1565c0; }
            QListWidget::item:hover:!selected { background: #f5f5f5; }
        """)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        root.addWidget(self.list_widget)

        hint = QLabel("اضغط مرتين أو Enter للاختيار")
        hint.setStyleSheet("font-size:9px; color:#aaa; background:transparent;")
        hint.setAlignment(Qt.AlignCenter)
        root.addWidget(hint)

    def _load_accounts(self):
        self._all_accounts = []
        for acc_type in self.acc_types:
            try:
                rows = fetch_all_accounts(self.conn, acc_type)
                for r in rows:
                    if r["is_leaf"]:
                        self._all_accounts.append({
                            "id":         r["id"],
                            "code":       r["code"],
                            "name":       r["name"],
                            "type":       r["type"],
                            "group_id":   r["group_id"],
                            "group_name": r["group_name"] if "group_name" in r.keys() else None,
                        })
            except Exception:
                pass
        self._render()

    def _on_search(self, text):
        self._filter_text = text.strip().lower()
        if self._filter_text:
            for t in self.acc_types:
                self._expanded.add(f"type:{t}")
        self._render()

    def _render(self):
        from PyQt5.QtWidgets import QListWidgetItem
        self.list_widget.clear()
        q = self._filter_text

        by_type: dict = {}
        for acc in self._all_accounts:
            t = acc["type"]
            if t not in by_type:
                by_type[t] = {}
            grp_key  = acc["group_name"] or "─── بدون تصنيف ───"
            grp_id   = acc["group_id"]   or -1
            grp_full = (grp_id, grp_key)
            if grp_full not in by_type[t]:
                by_type[t][grp_full] = []
            by_type[t][grp_full].append(acc)

        for acc_type in self.acc_types:
            if acc_type not in by_type:
                continue
            groups = by_type[acc_type]
            if q:
                has_match = any(
                    q in acc["name"].lower() or q in acc["code"].lower()
                    for accs in groups.values() for acc in accs
                )
                if not has_match:
                    continue

            type_key  = f"type:{acc_type}"
            expanded  = type_key in self._expanded
            icon      = _TYPE_ICONS.get(acc_type, "📁")
            type_label = TYPE_AR.get(acc_type, acc_type)
            toggle    = "▼" if expanded else "▶"
            color     = TYPE_COLORS.get(acc_type, "#333")

            type_item = QListWidgetItem(f"{toggle} {icon}  {type_label}")
            type_item.setData(Qt.UserRole, {"kind": "type", "type": acc_type, "key": type_key})
            f = QFont()
            f.setBold(True)
            f.setPointSize(f.pointSize() + 1)
            type_item.setFont(f)
            type_item.setForeground(QColor(color))
            type_item.setBackground(QColor("#f0f4ff"))
            self.list_widget.addItem(type_item)

            if not expanded:
                continue

            for (grp_id, grp_name), accs in sorted(groups.items(), key=lambda x: x[0][1]):
                matched_accs = accs
                if q:
                    matched_accs = [a for a in accs
                                    if q in a["name"].lower() or q in a["code"].lower()]
                if not matched_accs:
                    continue

                grp_key_full = f"grp:{acc_type}:{grp_id}"
                grp_expanded = grp_key_full in self._expanded
                toggle_g = "▼" if grp_expanded else "▶"

                grp_item = QListWidgetItem(f"    {toggle_g} 🏷  {grp_name}")
                grp_item.setData(Qt.UserRole, {"kind": "group", "key": grp_key_full})
                gf = QFont()
                gf.setBold(True)
                gf.setItalic(True)
                grp_item.setFont(gf)
                grp_item.setForeground(QColor("#546e7a"))
                grp_item.setBackground(QColor("#fafbff"))
                self.list_widget.addItem(grp_item)

                if not grp_expanded and not q:
                    continue

                for acc in sorted(matched_accs, key=lambda a: a["code"]):
                    nb = get_normal_balance(acc["type"])
                    nb_text = "DR↑" if nb == "dr" else "CR↑"
                    label = f"        {acc['code']} — {acc['name']}  [{nb_text}]"
                    acc_item = QListWidgetItem(label)
                    acc_item.setData(Qt.UserRole, {
                        "kind": "account",
                        "id":   acc["id"],
                        "name": f"{acc['code']} — {acc['name']}",
                        "type": acc["type"],
                    })
                    acc_item.setForeground(QColor(color))
                    self.list_widget.addItem(acc_item)

    def _on_item_clicked(self, item):
        data = item.data(Qt.UserRole)
        if not data:
            return
        kind = data.get("kind")
        if kind in ("type", "group"):
            key = data["key"]
            if key in self._expanded:
                self._expanded.discard(key)
            else:
                self._expanded.add(key)
            self._render()

    def _on_item_double_clicked(self, item):
        data = item.data(Qt.UserRole)
        if not data or data.get("kind") != "account":
            return
        self._selected_id   = data["id"]
        self._selected_name = data["name"]
        self.accept()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            current = self.list_widget.currentItem()
            if current:
                self._on_item_double_clicked(current)
            return
        if event.key() == Qt.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)

    def get_selected(self):
        return self._selected_id, self._selected_name

    def get_selected_type(self):
        """يرجع نوع الحساب المختار."""
        if not self._selected_id:
            return None
        acc = fetch_account(self.conn, self._selected_id)
        return acc["type"] if acc else None


# ══════════════════════════════════════════════════════════
# زر اختيار الحساب
# ══════════════════════════════════════════════════════════

class _AccountPickerButton(QWidget):
    def __init__(self, conn, acc_types=None, parent=None):
        super().__init__(parent)
        self.conn          = conn
        self.acc_types     = acc_types
        self._account_id   = None
        self._account_name = None
        self._account_type = None
        self._on_changed_cb = None
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        self.btn = QPushButton("— اختر الحساب —")
        self.btn.setMinimumHeight(30)
        self.btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn.setStyleSheet("""
            QPushButton {
                background: white; border: 1px solid #c5cae9;
                border-radius: 4px; padding: 2px 10px;
                text-align: right; font-size: 11px; color: #333;
            }
            QPushButton:hover { border-color: #1565c0; background: #f0f4ff; }
        """)
        self.btn.clicked.connect(self._open_popup)

        self.lbl_nb = QLabel("")
        self.lbl_nb.setFixedWidth(44)
        self.lbl_nb.setAlignment(Qt.AlignCenter)
        self.lbl_nb.setStyleSheet(
            "font-size:10px; font-weight:bold; border-radius:3px; padding:2px 4px;"
        )

        lay.addWidget(self.btn, stretch=1)
        lay.addWidget(self.lbl_nb)

    def _open_popup(self):
        popup = _AccountTreePopup(self.conn, self.acc_types, parent=self)
        pos = self.btn.mapToGlobal(QPoint(0, self.btn.height()))
        popup.move(pos)
        popup.resize(max(self.width() + 60, 420), 420)
        for t in (self.acc_types or _TYPE_ORDER):
            popup._expanded.add(f"type:{t}")
        popup._render()
        if popup.exec_() == QDialog.Accepted:
            acc_id, acc_name = popup.get_selected()
            if acc_id:
                acc = fetch_account(self.conn, acc_id)
                self._account_id   = acc_id
                self._account_name = acc_name
                self._account_type = acc["type"] if acc else None
                self.btn.setText(acc_name)
                self._update_nb_label()
                QTimer.singleShot(50, self._fire_changed)

    def _fire_changed(self):
        if self._on_changed_cb:
            self._on_changed_cb()

    def set_on_changed(self, cb):
        self._on_changed_cb = cb

    def _update_nb_label(self):
        if not self._account_id:
            self.lbl_nb.setText("")
            return
        acc = fetch_account(self.conn, self._account_id)
        if not acc:
            return
        nb = get_normal_balance(acc["type"])
        if nb == "dr":
            self.lbl_nb.setText("DR↑")
            self.lbl_nb.setStyleSheet(
                "font-size:10px; font-weight:bold; color:#1565c0;"
                "background:#e3f2fd; border-radius:3px; padding:2px 4px;"
            )
        else:
            self.lbl_nb.setText("CR↑")
            self.lbl_nb.setStyleSheet(
                "font-size:10px; font-weight:bold; color:#c62828;"
                "background:#fdecea; border-radius:3px; padding:2px 4px;"
            )

    def current_account_id(self):
        return self._account_id

    def current_account_type(self):
        return self._account_type

    def set_account(self, acc_id: int, acc_name: str = None):
        self._account_id = acc_id
        acc = fetch_account(self.conn, acc_id)
        self._account_type = acc["type"] if acc else None
        if acc_name:
            self._account_name = acc_name
            self.btn.setText(acc_name)
        elif acc:
            self._account_name = f"{acc['code']} — {acc['name']}"
            self.btn.setText(self._account_name)
        self._update_nb_label()

    def reset(self):
        self._account_id   = None
        self._account_name = None
        self._account_type = None
        self.btn.setText("— اختر الحساب —")
        self.lbl_nb.setText("")
        self.lbl_nb.setStyleSheet(
            "font-size:10px; font-weight:bold; border-radius:3px; padding:2px 4px;"
        )


# ══════════════════════════════════════════════════════════
# صف ذكي واحد — مع ربط المستثمر
# ══════════════════════════════════════════════════════════

class _SmartLine(QFrame):
    def __init__(self, conn, erp_conn, on_change, on_remove,
                 on_move_up, on_move_dn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self.erp_conn    = erp_conn
        self._on_change  = on_change
        self._on_remove  = on_remove
        self._on_move_up = on_move_up
        self._on_move_dn = on_move_dn
        self._resolved_side = "dr"
        self._build()

    def _build(self):
        self.setStyleSheet("""
            QFrame {
                background: #fafbff;
                border: 1px solid #dde3f0;
                border-radius: 6px;
            }
            QFrame:hover { border-color: #90aad4; }
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(4)

        # ── الصف الرئيسي ──
        main_row = QHBoxLayout()
        main_row.setSpacing(6)

        # أزرار الترتيب
        self.btn_up = QPushButton("▲")
        self.btn_dn = QPushButton("▼")
        for b in (self.btn_up, self.btn_dn):
            b.setFixedSize(18, 18)
            b.setStyleSheet(
                "QPushButton { background:transparent; border:none; color:#bbb; font-size:8px; }"
                "QPushButton:hover { color:#1565c0; }"
            )
        self.btn_up.clicked.connect(lambda: self._on_move_up(self))
        self.btn_dn.clicked.connect(lambda: self._on_move_dn(self))
        ord_col = QVBoxLayout()
        ord_col.setSpacing(0)
        ord_col.setContentsMargins(0, 0, 0, 0)
        ord_col.addWidget(self.btn_up)
        ord_col.addWidget(self.btn_dn)
        main_row.addLayout(ord_col)

        # اختيار الحساب
        self._acc = _AccountPickerButton(self.conn)
        self._acc.set_on_changed(self._on_acc_changed)
        main_row.addWidget(self._acc, stretch=4)

        # اتجاه العملية
        dir_frame = QFrame()
        dir_frame.setStyleSheet("QFrame { background:transparent; border:none; }")
        dir_lay = QHBoxLayout(dir_frame)
        dir_lay.setContentsMargins(0, 0, 0, 0)
        dir_lay.setSpacing(3)
        self.rdo_inc = QRadioButton("زيادة ✚")
        self.rdo_dec = QRadioButton("نقص ✖")
        self.rdo_inc.setChecked(True)
        self.rdo_inc.setStyleSheet("font-size:10px; color:#2e7d32; font-weight:bold;")
        self.rdo_dec.setStyleSheet("font-size:10px; color:#c62828; font-weight:bold;")
        self._dir_group = QButtonGroup(self)
        self._dir_group.addButton(self.rdo_inc, 1)
        self._dir_group.addButton(self.rdo_dec, 0)
        self.rdo_inc.toggled.connect(self._on_dir_changed)
        dir_lay.addWidget(self.rdo_inc)
        dir_lay.addWidget(self.rdo_dec)
        dir_frame.setFixedWidth(130)
        main_row.addWidget(dir_frame)

        # المبلغ
        self.sp_amount = QDoubleSpinBox()
        self.sp_amount.setRange(0, 999_999_999)
        self.sp_amount.setDecimals(2)
        self.sp_amount.setMinimumHeight(28)
        self.sp_amount.setFixedWidth(110)
        self.sp_amount.valueChanged.connect(self._on_change)
        main_row.addWidget(self.sp_amount)

        # البيان
        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("بيان...")
        self.inp_desc.setMinimumHeight(28)
        main_row.addWidget(self.inp_desc, stretch=2)

        # حذف
        btn_del = QPushButton("✖")
        btn_del.setFixedSize(22, 22)
        btn_del.setStyleSheet(
            "QPushButton { background:transparent; border:none; color:#bbb; font-size:11px; }"
            "QPushButton:hover { color:#e53935; }"
        )
        btn_del.clicked.connect(lambda: self._on_remove(self))
        main_row.addWidget(btn_del)

        lay.addLayout(main_row)

        # ── صف ربط المستثمر (يظهر عند capital/drawings) ──
        self._investor_row = QFrame()
        self._investor_row.setStyleSheet(
            "QFrame { background:#fff8e1; border:1px solid #ffe082;"
            "border-radius:4px; margin-top:2px; }"
        )
        inv_lay = QHBoxLayout(self._investor_row)
        inv_lay.setContentsMargins(8, 4, 8, 4)
        inv_lay.setSpacing(8)

        lbl_inv = QLabel("👤  ربط بمستثمر:")
        lbl_inv.setStyleSheet(
            "font-size:10px; font-weight:bold; color:#f57f17;"
            "background:transparent; border:none;"
        )
        lbl_inv.setFixedWidth(95)
        inv_lay.addWidget(lbl_inv)

        self.cmb_investor = QComboBox()
        self.cmb_investor.setMinimumHeight(24)
        self.cmb_investor.setStyleSheet("font-size:11px;")
        self._reload_investors()
        inv_lay.addWidget(self.cmb_investor, stretch=1)

        lbl_hint = QLabel("(اختياري)")
        lbl_hint.setStyleSheet(
            "font-size:9px; color:#aaa; background:transparent; border:none;"
        )
        inv_lay.addWidget(lbl_hint)

        lay.addWidget(self._investor_row)
        self._investor_row.setVisible(False)

        self._update_side_style()

    def _reload_investors(self):
        if self.erp_conn is None:
            return
        try:
            from db.investors_repo import fetch_all_investors
            prev = self.cmb_investor.currentData()
            self.cmb_investor.blockSignals(True)
            self.cmb_investor.clear()
            self.cmb_investor.addItem("— لا يوجد ربط —", None)
            for inv in fetch_all_investors(self.erp_conn):
                self.cmb_investor.addItem(f"👤 {inv['name']}", inv["id"])
            self.cmb_investor.blockSignals(False)
            if prev:
                for i in range(self.cmb_investor.count()):
                    if self.cmb_investor.itemData(i) == prev:
                        self.cmb_investor.setCurrentIndex(i)
                        break
        except Exception:
            pass

    # ── منطق التوجيه ──────────────────────────────────────

    def _get_acc_type(self) -> str | None:
        acc_id = self._acc.current_account_id()
        if not acc_id:
            return None
        acc = fetch_account(self.conn, acc_id)
        return acc["type"] if acc else None

    def _update_side_style(self):
        acc_type = self._get_acc_type()
        is_inc   = self.rdo_inc.isChecked()

        # إظهار/إخفاء صف المستثمر
        show_investor = acc_type in _INVESTOR_TYPES if acc_type else False
        self._investor_row.setVisible(show_investor)
        if show_investor:
            self._reload_investors()

        if acc_type:
            side = _resolve_side(acc_type, is_inc)
            self._resolved_side = side
            if side == "dr":
                self.setStyleSheet("""
                    QFrame {
                        background: #f4f8ff;
                        border: 1px solid #c5d8f7;
                        border-right: 3px solid #1565c0;
                        border-radius: 6px;
                    }
                """)
            else:
                self.setStyleSheet("""
                    QFrame {
                        background: #fff4f4;
                        border: 1px solid #f7c5c5;
                        border-right: 3px solid #c62828;
                        border-radius: 6px;
                    }
                """)
        else:
            self._resolved_side = "dr"
            self.setStyleSheet("""
                QFrame {
                    background: #fafbff;
                    border: 1px solid #dde3f0;
                    border-radius: 6px;
                }
            """)

    def _on_acc_changed(self):
        self._update_side_style()
        self._on_change()

    def _on_dir_changed(self):
        self._update_side_style()
        self._on_change()

    # ── API ──────────────────────────────────────────────

    def get_values(self) -> dict | None:
        acc_id = self._acc.current_account_id()
        amount = self.sp_amount.value()
        if not acc_id or amount == 0:
            return None
        side = self._resolved_side
        return {
            "account_id":  acc_id,
            "debit":       amount if side == "dr" else 0.0,
            "credit":      amount if side == "cr" else 0.0,
            "description": self.inp_desc.text().strip(),
        }

    def get_investor_link(self) -> dict | None:
        """يرجع بيانات ربط المستثمر لو موجودة."""
        if not self._investor_row.isVisible():
            return None
        inv_id = self.cmb_investor.currentData()
        if not inv_id:
            return None
        acc_type = self._get_acc_type()
        return {
            "investor_id": inv_id,
            "acc_type":    acc_type,
            "amount":      self.sp_amount.value(),
        }

    def get_amount(self) -> float:
        return self.sp_amount.value()

    def get_side(self) -> str:
        return self._resolved_side


# ══════════════════════════════════════════════════════════
# لوحة الصفوف
# ══════════════════════════════════════════════════════════

class _LinesPanel(QFrame):
    def __init__(self, conn, erp_conn, on_balance_changed, parent=None):
        super().__init__(parent)
        self.conn                = conn
        self.erp_conn            = erp_conn
        self._on_balance_changed = on_balance_changed
        self._lines: list[_SmartLine] = []
        self._build()

    def _build(self):
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        hdr = QFrame()
        hdr.setStyleSheet("background:#f0f4ff; border-radius:7px 7px 0 0;")
        hdr.setFixedHeight(38)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(12, 4, 12, 4)

        lbl = QLabel("📋  صفوف القيد")
        lbl.setStyleSheet(
            "font-weight:bold; font-size:12px; color:#1565c0;"
            "background:transparent; border:none;"
        )
        self.lbl_dr = QLabel("DR: 0.00")
        self.lbl_dr.setStyleSheet(
            "font-weight:bold; color:#1565c0; background:#e3f2fd;"
            "border-radius:4px; padding:2px 8px; font-size:11px; border:none;"
        )
        self.lbl_cr = QLabel("CR: 0.00")
        self.lbl_cr.setStyleSheet(
            "font-weight:bold; color:#c62828; background:#fdecea;"
            "border-radius:4px; padding:2px 8px; font-size:11px; border:none;"
        )
        hl.addWidget(lbl)
        hl.addStretch()
        hl.addWidget(self.lbl_dr)
        hl.addSpacing(8)
        hl.addWidget(self.lbl_cr)
        root.addWidget(hdr)

        # ترويسة أعمدة
        col_hdr = QWidget()
        col_hdr.setStyleSheet("background:#fafbff;")
        ch_lay = QHBoxLayout(col_hdr)
        ch_lay.setContentsMargins(28, 2, 8, 2)
        ch_lay.setSpacing(6)

        def _ch(text, w=None, stretch=0):
            l = QLabel(text)
            l.setStyleSheet(
                "font-size:9px; color:#888; font-weight:bold;"
                "background:transparent; border:none;"
            )
            if w:
                l.setFixedWidth(w)
            ch_lay.addWidget(l, stretch=stretch)

        _ch("الحساب",  stretch=4)
        _ch("الاتجاه", w=130)
        _ch("المبلغ",  w=110)
        _ch("البيان",  stretch=2)
        _ch("",        w=22)
        root.addWidget(col_hdr)

        # منطقة الصفوف
        self._rows_w   = QWidget()
        self._rows_w.setStyleSheet("background:transparent;")
        self._rows_lay = QVBoxLayout(self._rows_w)
        self._rows_lay.setSpacing(3)
        self._rows_lay.setContentsMargins(6, 6, 6, 6)
        self._rows_lay.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._rows_w)
        scroll.setMinimumHeight(150)
        scroll.setMaximumHeight(380)
        scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")
        root.addWidget(scroll)

        btn_add = QPushButton("➕  إضافة صف")
        btn_add.setMinimumHeight(28)
        btn_add.setStyleSheet("""
            QPushButton {
                background: #f0f4ff; color: #1565c0;
                border: 1px solid #c5cae9; border-radius: 4px;
                font-weight: bold; padding: 2px 12px; margin: 4px 8px;
            }
            QPushButton:hover { background: #1565c0; color: white; }
        """)
        btn_add.clicked.connect(self.add_line)
        root.addWidget(btn_add)

    # ── إدارة الصفوف ──────────────────────────────────────

    def add_line(self) -> _SmartLine:
        line = _SmartLine(
            conn        = self.conn,
            erp_conn    = self.erp_conn,
            on_change   = self._on_line_changed,
            on_remove   = self._remove_line,
            on_move_up  = self._move_up,
            on_move_dn  = self._move_dn,
        )
        self._lines.append(line)
        self._rows_lay.insertWidget(self._rows_lay.count() - 1, line)
        self._refresh_totals()
        return line

    def _remove_line(self, line):
        if len(self._lines) <= 1:
            QMessageBox.information(None, "تنبيه", "لازم يكون في صف واحد على الأقل")
            return
        self._lines.remove(line)
        self._rows_lay.removeWidget(line)
        line.deleteLater()
        self._on_line_changed()

    def _move_up(self, line):
        idx = self._lines.index(line)
        if idx == 0:
            return
        self._lines[idx], self._lines[idx - 1] = self._lines[idx - 1], self._lines[idx]
        self._rebuild_rows()

    def _move_dn(self, line):
        idx = self._lines.index(line)
        if idx >= len(self._lines) - 1:
            return
        self._lines[idx], self._lines[idx + 1] = self._lines[idx + 1], self._lines[idx]
        self._rebuild_rows()

    def _rebuild_rows(self):
        while self._rows_lay.count() > 1:
            item = self._rows_lay.takeAt(0)
            if item and item.widget():
                item.widget().setParent(None)
        for line in self._lines:
            self._rows_lay.insertWidget(self._rows_lay.count() - 1, line)

    def _on_line_changed(self):
        self._refresh_totals()
        self._on_balance_changed()

    def _refresh_totals(self):
        total_dr = sum(ln.get_amount() for ln in self._lines if ln.get_side() == "dr")
        total_cr = sum(ln.get_amount() for ln in self._lines if ln.get_side() == "cr")
        self.lbl_dr.setText(f"DR: {total_dr:,.2f}")
        self.lbl_cr.setText(f"CR: {total_cr:,.2f}")

    # ── API ──────────────────────────────────────────────

    def get_total_dr(self) -> float:
        return sum(ln.get_amount() for ln in self._lines if ln.get_side() == "dr")

    def get_total_cr(self) -> float:
        return sum(ln.get_amount() for ln in self._lines if ln.get_side() == "cr")

    def get_all_values(self) -> list:
        return [v for ln in self._lines if (v := ln.get_values()) is not None]

    def get_all_investor_links(self) -> list:
        """يجيب كل ربط مستثمرين موجود في الصفوف."""
        links = []
        for ln in self._lines:
            link = ln.get_investor_link()
            if link:
                links.append(link)
        return links

    def clear_lines(self):
        for ln in list(self._lines):
            self._rows_lay.removeWidget(ln)
            ln.deleteLater()
        self._lines.clear()
        self._refresh_totals()


# ══════════════════════════════════════════════════════════
# فورم القيد
# ══════════════════════════════════════════════════════════

class _JournalForm(QWidget):
    def __init__(self, conn, erp_conn=None, parent=None):
        super().__init__(parent)
        self.conn     = conn
        self.erp_conn = erp_conn
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        self.lbl_mode = QLabel("── قيد يومية جديد ──")
        self.lbl_mode.setStyleSheet(
            "font-weight:bold; color:#1565c0; font-size:12px;"
        )
        root.addWidget(self.lbl_mode)

        info_row = QHBoxLayout()
        info_row.setSpacing(8)

        self.dt_date = QDateEdit(QDate.currentDate())
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDisplayFormat("yyyy-MM-dd")
        self.dt_date.setFixedWidth(130)
        self.dt_date.setMinimumHeight(30)

        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("وصف القيد الإجمالي...")
        self.inp_desc.setMinimumHeight(30)

        info_row.addWidget(QLabel("التاريخ:"))
        info_row.addWidget(self.dt_date)
        info_row.addSpacing(12)
        info_row.addWidget(QLabel("الوصف:"))
        info_row.addWidget(self.inp_desc, stretch=1)
        root.addLayout(info_row)

        self._lines_panel = _LinesPanel(
            self.conn, self.erp_conn, self._on_balance_changed
        )
        root.addWidget(self._lines_panel)

        # شريط التوازن
        bal_frame = QFrame()
        bal_frame.setStyleSheet("""
            QFrame {
                background: #f0f4ff;
                border: 1px solid #c5cae9;
                border-radius: 6px;
            }
        """)
        bal_lay = QHBoxLayout(bal_frame)
        bal_lay.setContentsMargins(14, 8, 14, 8)
        bal_lay.setSpacing(4)

        def _sep():
            s = QLabel("│")
            s.setStyleSheet("color:#c5cae9; font-size:18px; margin:0 8px;")
            return s

        lbl_dr_t = QLabel("إجمالي DR:")
        lbl_dr_t.setStyleSheet("font-weight:bold; color:#1565c0;")
        self.lbl_sum_dr = QLabel("0.00")
        self.lbl_sum_dr.setStyleSheet(
            "font-size:14px; font-weight:bold; color:#1565c0;"
            "background:#e3f2fd; border-radius:4px; padding:3px 10px; margin-left:4px;"
        )
        lbl_cr_t = QLabel("إجمالي CR:")
        lbl_cr_t.setStyleSheet("font-weight:bold; color:#c62828;")
        self.lbl_sum_cr = QLabel("0.00")
        self.lbl_sum_cr.setStyleSheet(
            "font-size:14px; font-weight:bold; color:#c62828;"
            "background:#fdecea; border-radius:4px; padding:3px 10px; margin-left:4px;"
        )
        lbl_diff_t = QLabel("الفرق:")
        lbl_diff_t.setStyleSheet("font-weight:bold; color:#555;")
        self.lbl_diff = QLabel("0.00")
        self.lbl_diff.setStyleSheet(
            "font-size:14px; font-weight:bold; color:#888;"
            "background:#f5f5f5; border-radius:4px; padding:3px 10px; margin-left:4px;"
        )
        self.lbl_status = QLabel("○ أضف صفوف")
        self.lbl_status.setStyleSheet("font-size:12px; font-weight:bold; color:#888;")

        for w in (lbl_dr_t, self.lbl_sum_dr, _sep(),
                  lbl_cr_t, self.lbl_sum_cr, _sep(),
                  lbl_diff_t, self.lbl_diff, _sep(),
                  self.lbl_status):
            bal_lay.addWidget(w)
        bal_lay.addStretch()
        root.addWidget(bal_frame)

        self.btn_save   = QPushButton("💾  حفظ القيد")
        self.btn_cancel = QPushButton("✖  مسح")
        self.btn_save.setMinimumHeight(34)
        self.btn_cancel.setMinimumHeight(34)
        self.btn_save.setEnabled(False)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background:#1565c0; color:white;
                font-weight:bold; border-radius:6px; padding:0 20px;
            }
            QPushButton:hover  { background:#0d47a1; }
            QPushButton:disabled { background:#b0bec5; color:#eceff1; }
        """)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background:#f5f5f5; color:#555;
                border:1px solid #ddd; border-radius:6px; padding:0 14px;
            }
            QPushButton:hover { background:#eeeeee; }
        """)
        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self._clear)
        root.addLayout(buttons_row(self.btn_save, self.btn_cancel))

        self._lines_panel.add_line()
        self._lines_panel.add_line()

    # ── التوازن ──────────────────────────────────────────

    def _on_balance_changed(self):
        total_dr = self._lines_panel.get_total_dr()
        total_cr = self._lines_panel.get_total_cr()
        diff     = total_dr - total_cr

        self.lbl_sum_dr.setText(f"{total_dr:,.2f}")
        self.lbl_sum_cr.setText(f"{total_cr:,.2f}")
        self.lbl_diff.setText(f"{abs(diff):,.2f}")

        if total_dr == 0 and total_cr == 0:
            self.lbl_status.setText("○ أضف صفوف")
            self.lbl_status.setStyleSheet("font-size:12px; font-weight:bold; color:#888;")
            self.lbl_diff.setStyleSheet(
                "font-size:14px; font-weight:bold; color:#888;"
                "background:#f5f5f5; border-radius:4px; padding:3px 10px; margin-left:4px;"
            )
            self.btn_save.setEnabled(False)
        elif abs(diff) < 0.001:
            self.lbl_status.setText("✅  متوازن — يمكن الحفظ")
            self.lbl_status.setStyleSheet("font-size:12px; font-weight:bold; color:#2e7d32;")
            self.lbl_diff.setStyleSheet(
                "font-size:14px; font-weight:bold; color:#2e7d32;"
                "background:#f1f8e9; border-radius:4px; padding:3px 10px; margin-left:4px;"
            )
            self.btn_save.setEnabled(True)
        else:
            side_ar = "DR أكبر" if diff > 0 else "CR أكبر"
            self.lbl_status.setText(
                f"⚠️  غير متوازن ({side_ar} بـ {abs(diff):,.2f})"
            )
            self.lbl_status.setStyleSheet("font-size:12px; font-weight:bold; color:#c62828;")
            self.lbl_diff.setStyleSheet(
                "font-size:14px; font-weight:bold; color:#c62828;"
                "background:#fdecea; border-radius:4px; padding:3px 10px; margin-left:4px;"
            )
            self.btn_save.setEnabled(False)

    # ── حفظ ──────────────────────────────────────────────

    def _save(self):
        desc = self.inp_desc.text().strip()
        if not desc:
            QMessageBox.warning(self, "تنبيه", "أدخل وصف القيد")
            return

        all_lines = self._lines_panel.get_all_values()
        if not all_lines:
            QMessageBox.warning(self, "تنبيه", "أضف صفاً واحداً على الأقل")
            return

        dr_lines = [l for l in all_lines if l["debit"]  > 0]
        cr_lines = [l for l in all_lines if l["credit"] > 0]
        if not dr_lines:
            QMessageBox.warning(self, "تنبيه", "لا يوجد أي صف مدين (DR)")
            return
        if not cr_lines:
            QMessageBox.warning(self, "تنبيه", "لا يوجد أي صف دائن (CR)")
            return

        if not validate_entry_balance(all_lines):
            td = sum(l["debit"]  for l in all_lines)
            tc = sum(l["credit"] for l in all_lines)
            QMessageBox.warning(
                self, "خطأ في التوازن",
                f"مجموع DR ({td:,.2f}) ≠ مجموع CR ({tc:,.2f})"
            )
            return

        date     = self.dt_date.date().toString("yyyy-MM-dd")
        entry_id = insert_entry(self.conn, date, desc, "manual")
        add_entry_lines(self.conn, entry_id, all_lines)

        # ── تسجيل ربط المستثمرين ──
        investor_links = self._lines_panel.get_all_investor_links()
        if investor_links and self.erp_conn:
            from db.investors_repo import link_investor_to_line
            for link in investor_links:
                inv_id   = link["investor_id"]
                acc_type = link["acc_type"]
                amount   = link["amount"]
                move_type = "capital" if acc_type == "capital" else "drawings"
                # اجيب line_id المناسب
                if move_type == "capital":
                    line_row = self.conn.execute(
                        "SELECT id FROM journal_lines WHERE entry_id=? AND credit>0 LIMIT 1",
                        (entry_id,)
                    ).fetchone()
                else:
                    line_row = self.conn.execute(
                        "SELECT id FROM journal_lines WHERE entry_id=? AND debit>0 LIMIT 1",
                        (entry_id,)
                    ).fetchone()
                line_id = line_row["id"] if line_row else 0
                try:
                    link_investor_to_line(
                        self.erp_conn, inv_id, entry_id, line_id,
                        move_type, amount, desc
                    )
                except Exception as e:
                    print(f"[JournalForm] investor link error: {e}")

        self._clear()
        bus.data_changed.emit()
        QMessageBox.information(self, "تم", "✅ تم حفظ القيد بنجاح")

    def _clear(self):
        self._lines_panel.clear_lines()
        self.inp_desc.clear()
        self.dt_date.setDate(QDate.currentDate())
        self.lbl_mode.setText("── قيد يومية جديد ──")
        self.btn_save.setEnabled(False)
        self._lines_panel.add_line()
        self._lines_panel.add_line()
        self._on_balance_changed()


# ══════════════════════════════════════════════════════════
# جدول القيود — شجري
# ══════════════════════════════════════════════════════════

class _JournalTreeTable(QWidget):
    COLS = ["#", "رقم القيد", "التاريخ", "البيان / الحساب", "DR", "CR", "الحالة"]

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._expanded: set[int] = set()
        self._entries_data = []
        self._row_meta = {}
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        root.addWidget(section_label("── القيود المحاسبية المحفوظة ──"))

        btn_expand_all   = QPushButton("⊞ توسيع الكل")
        btn_collapse_all = QPushButton("⊟ طي الكل")
        btn_del          = danger_button("🗑️  حذف القيد المحدد")
        for btn in (btn_expand_all, btn_collapse_all, btn_del):
            btn.setMinimumHeight(26)
        _btn_style = (
            "QPushButton { background:#e8f4fd; color:#1565c0; border:1px solid #90caf9;"
            "border-radius:4px; padding:2px 10px; font-size:11px; }"
            "QPushButton:hover { background:#1565c0; color:white; }"
        )
        btn_expand_all.setStyleSheet(_btn_style)
        btn_collapse_all.setStyleSheet(_btn_style)
        btn_expand_all.clicked.connect(self._expand_all)
        btn_collapse_all.clicked.connect(self._collapse_all)
        btn_del.clicked.connect(self._delete_selected)
        root.addLayout(buttons_row(btn_expand_all, btn_collapse_all, btn_del))

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(3, QHeaderView.Stretch)
        for col, w in {0: 28, 1: 85, 2: 90, 4: 95, 5: 95, 6: 85}.items():
            hh.setSectionResizeMode(col, QHeaderView.Fixed)
            self.table.setColumnWidth(col, w)
        hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setWordWrap(False)
        self.table.cellClicked.connect(self._on_cell_clicked)
        root.addWidget(self.table, stretch=1)

    def _load(self):
        entries = fetch_all_entries(self.conn)
        self._entries_data = []
        for e in entries:
            lines = fetch_entry_lines(self.conn, e["id"])
            self._entries_data.append({
                "id":           e["id"],
                "ref_no":       e["ref_no"],
                "date":         e["date"],
                "type":         e["type"],
                "description":  e["description"],
                "total_debit":  e["total_debit"],
                "total_credit": e["total_credit"],
                "lines":        [dict(l) for l in lines],
            })
        self._render()

    def _render(self):
        self.table.setRowCount(0)
        self._row_meta = {}

        for entry in self._entries_data:
            eid      = entry["id"]
            expanded = eid in self._expanded
            total_dr = entry["total_debit"]
            total_cr = entry["total_credit"]

            r = self.table.rowCount()
            self.table.insertRow(r)
            self._row_meta[r] = {"entry_id": eid, "is_parent": True, "is_child": False}

            toggle_item = QTableWidgetItem("▼" if expanded else "▶")
            toggle_item.setTextAlignment(Qt.AlignCenter)
            toggle_item.setForeground(QBrush(QColor("#1565c0")))
            f = QFont()
            f.setBold(True)
            toggle_item.setFont(f)
            self.table.setItem(r, 0, toggle_item)

            self.table.setItem(r, 1, self._bold_item(entry["ref_no"], "#1565c0"))
            self.table.setItem(r, 2, self._bold_item(entry["date"]))
            self.table.setItem(r, 3, self._bold_item(entry["description"]))
            self.table.setItem(r, 4, self._bold_item(f"{total_dr:,.2f}", "#1565c0"))
            self.table.setItem(r, 5, self._bold_item(f"{total_cr:,.2f}", "#c62828"))

            diff = total_dr - total_cr
            bal_color = "#2e7d32" if abs(diff) < 0.01 else "#c62828"
            bal_text  = "✅ متوازن" if abs(diff) < 0.01 else f"⚠️ {abs(diff):,.2f}"
            self.table.setItem(r, 6, self._bold_item(bal_text, bal_color))

            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                if item:
                    item.setBackground(QBrush(QColor("#eef3fb")))

            if expanded:
                for line in entry["lines"]:
                    rc = self.table.rowCount()
                    self.table.insertRow(rc)
                    self._row_meta[rc] = {"entry_id": eid, "is_parent": False, "is_child": True}

                    acc_name = line.get("account_name", "")
                    acc_code = line.get("account_code", "")
                    prefix   = "    └─ "
                    desc_text = f"{prefix}{acc_code} — {acc_name}"
                    if line.get("description"):
                        desc_text += f"  │  {line['description']}"

                    is_dr      = line["debit"] > 0
                    side_color = "#1565c0" if is_dr else "#c62828"
                    row_bg     = QColor("#f4f8ff") if is_dr else QColor("#fff4f4")

                    for c in range(3):
                        self.table.setItem(rc, c, QTableWidgetItem(""))

                    desc_item = QTableWidgetItem(desc_text)
                    desc_item.setToolTip(f"{acc_code} — {acc_name}")
                    desc_item.setForeground(QBrush(QColor(side_color)))
                    self.table.setItem(rc, 3, desc_item)

                    if is_dr:
                        self.table.setItem(rc, 4, self._colored_item(f"{line['debit']:,.2f}", "#1565c0"))
                        self.table.setItem(rc, 5, QTableWidgetItem(""))
                    else:
                        self.table.setItem(rc, 4, QTableWidgetItem(""))
                        self.table.setItem(rc, 5, self._colored_item(f"{line['credit']:,.2f}", "#c62828"))

                    self.table.setItem(rc, 6, QTableWidgetItem(""))

                    for c in range(self.table.columnCount()):
                        item = self.table.item(rc, c)
                        if item:
                            item.setBackground(QBrush(row_bg))

    def _bold_item(self, text, color=None):
        item = QTableWidgetItem(text)
        f = QFont()
        f.setBold(True)
        item.setFont(f)
        if color:
            item.setForeground(QBrush(QColor(color)))
        return item

    def _colored_item(self, text, color):
        item = QTableWidgetItem(text)
        item.setForeground(QBrush(QColor(color)))
        return item

    def _on_cell_clicked(self, row, col):
        meta = self._row_meta.get(row)
        if not meta or not meta["is_parent"]:
            return
        if col not in (0, 1):
            return
        eid = meta["entry_id"]
        if eid in self._expanded:
            self._expanded.discard(eid)
        else:
            self._expanded.add(eid)
        self._render()

    def _expand_all(self):
        self._expanded = {e["id"] for e in self._entries_data}
        self._render()

    def _collapse_all(self):
        self._expanded.clear()
        self._render()

    def _selected_entry_id(self):
        row  = self.table.currentRow()
        meta = self._row_meta.get(row)
        if not meta:
            return None
        return meta["entry_id"]

    def _delete_selected(self):
        eid = self._selected_entry_id()
        if eid is None:
            QMessageBox.information(self, "تنبيه", "اختر قيداً أولاً")
            return
        entry_data = next((e for e in self._entries_data if e["id"] == eid), None)
        desc = entry_data["description"] if entry_data else f"ID:{eid}"
        if confirm_delete(self, desc):
            delete_entry(self.conn, eid)
            self._expanded.discard(eid)
            bus.data_changed.emit()


# ══════════════════════════════════════════════════════════
# تبويب القيود الكامل
# ══════════════════════════════════════════════════════════

class JournalTab(QWidget):
    def __init__(self, conn, erp_conn=None, parent=None):
        super().__init__(parent)
        self.conn     = conn
        self.erp_conn = erp_conn
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet("""
            QSplitter::handle { background:#e0e0e0; }
            QSplitter::handle:hover { background:#bbdefb; }
        """)

        self._form       = _JournalForm(self.conn, self.erp_conn)
        self._tree_table = _JournalTreeTable(self.conn)

        splitter.addWidget(self._form)
        splitter.addWidget(self._tree_table)
        splitter.setSizes([440, 360])
        splitter.setCollapsible(0, True)

        root.addWidget(splitter)