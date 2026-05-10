"""
ui/tabs/accounting/investors_tab.py
=====================================
تبويب إدارة المستثمرين — يشمل:

  1. _InvestorFormPanel   — إضافة / تعديل بيانات مستثمر
  2. _InvestorsTable      — جدول كل المستثمرين مع الأرصدة
  3. _InvestorDetails     — تفاصيل مستثمر واحد (الحركات + المخطط)
  4. _LinkInvestorDialog  — ربط مستثمر بصف قيد (يُفتح من قيود اليومية)
  5. InvestorsTab         — التبويب الرئيسي
  6. InvestorCombo        — Dropdown للاختيار من قيود اليومية

الاستخدام من journal_tab.py:
    from ui.tabs.accounting.investors_tab import InvestorCombo, _LinkInvestorDialog
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QSplitter, QTabWidget, QFrame, QScrollArea,
    QLabel, QPushButton, QLineEdit, QDateEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDialog, QComboBox, QDoubleSpinBox,
    QAbstractItemView, QGroupBox, QRadioButton,
    QButtonGroup, QTextEdit,
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui  import QColor, QFont, QBrush

from db.investors_repo import (
    fetch_all_investors, fetch_investor,
    insert_investor, update_investor, delete_investor,
    investor_exists, link_investor_to_line,
    fetch_investor_entries, fetch_entry_investor_links,
    delete_investor_link, delete_entry_investor_links,
    calc_investor_summary, calc_all_investors_summary,
    create_investors_tables,
)
from db.accounting_repo import (
    fetch_all_entries, fetch_entry_lines, fetch_account,
    fetch_leaf_accounts,
)
from ui.helpers import (
    make_table, setup_table_columns, buttons_row,
    section_label, danger_button, confirm_delete,
    EditModeMixin,
)
from ui.events import bus


def _money(val: float) -> str:
    return f"{val:,.2f}  ج"


def _stat_box(title: str, color: str = "#1565c0"):
    frame = QFrame()
    frame.setStyleSheet(f"""
        QFrame {{
            background: white;
            border-left: 4px solid {color};
            border-radius: 8px;
            padding: 2px;
        }}
    """)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(12, 8, 12, 8)
    lay.setSpacing(2)
    lt = QLabel(title)
    lt.setStyleSheet("font-size:10px; color:#888; background:transparent; border:none;")
    lv = QLabel("─")
    lv.setStyleSheet(
        f"font-size:15px; font-weight:bold; color:{color};"
        "background:transparent; border:none;"
    )
    lay.addWidget(lt)
    lay.addWidget(lv)
    return frame, lv


# ══════════════════════════════════════════════════════════
# Combo لاختيار المستثمر (يُستخدم في قيود اليومية)
# ══════════════════════════════════════════════════════════

class InvestorCombo(QComboBox):
    """
    Dropdown يعرض المستثمرين الموجودين + خيار "جديد".
    يُستخدم داخل صف القيد لتحديد مستثمر.
    """
    new_investor_requested = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        create_investors_tables(conn)
        self.setMinimumHeight(28)
        self.setMinimumWidth(160)
        self.refresh()
        bus.data_changed.connect(self.refresh)

    def refresh(self):
        prev = self.currentData()
        self.blockSignals(True)
        self.clear()
        self.addItem("— اختر مستثمر —", None)

        investors = fetch_all_investors(self.conn)
        for inv in investors:
            self.addItem(f"👤  {inv['name']}", inv["id"])

        self.addItem("➕  إضافة مستثمر جديد...", "__new__")

        # استعادة الاختيار
        for i in range(self.count()):
            if self.itemData(i) == prev:
                self.setCurrentIndex(i)
                break
        self.blockSignals(False)

    def current_investor_id(self):
        data = self.currentData()
        if data is None or data == "__new__":
            return None
        return data

    def set_investor(self, inv_id: int):
        for i in range(self.count()):
            if self.itemData(i) == inv_id:
                self.setCurrentIndex(i)
                return


# ══════════════════════════════════════════════════════════
# نافذة ربط مستثمر بقيد (تُفتح من قيود اليومية)
# ══════════════════════════════════════════════════════════

class LinkInvestorDialog(QDialog):
    """
    نافذة تظهر عند الضغط على "ربط بمستثمر" في صف قيد.
    تتيح:
      - اختيار مستثمر موجود أو إضافة جديد
      - تحديد نوع الحركة (capital / drawings)
      - اختيار صف القيد المحدد
    """

    def __init__(self, conn, entry_id: int, parent=None):
        super().__init__(parent)
        self.conn     = conn
        self.entry_id = entry_id
        create_investors_tables(conn)

        self.setWindowTitle("🔗  ربط قيد بمستثمر")
        self.setMinimumWidth(560)
        self.setModal(True)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build()
        self._load_lines()
        self._load_existing_links()

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 16)

        # ── العنوان ──
        hdr = QLabel(f"🔗  ربط قيد بمستثمر")
        hdr.setStyleSheet(
            "font-size:14px; font-weight:bold; color:#1565c0;"
            "background:#e8f4fd; border-radius:6px; padding:8px 12px;"
        )
        hdr.setAlignment(Qt.AlignCenter)
        root.addWidget(hdr)

        # ── اختيار المستثمر ──
        grp_inv = QGroupBox("المستثمر")
        grp_inv.setStyleSheet("""
            QGroupBox { font-weight:bold; color:#1565c0;
                border:1px solid #e0e0e0; border-radius:6px;
                margin-top:6px; padding-top:8px; }
            QGroupBox::title { subcontrol-origin:margin; padding:0 6px; }
        """)
        inv_lay = QFormLayout(grp_inv)
        inv_lay.setSpacing(10)
        inv_lay.setLabelAlignment(Qt.AlignRight)

        self.cmb_investor = InvestorCombo(self.conn)
        self.cmb_investor.currentIndexChanged.connect(self._on_investor_changed)
        inv_lay.addRow("المستثمر:", self.cmb_investor)

        # إضافة مستثمر جديد inline
        self._new_inv_frame = QFrame()
        self._new_inv_frame.setStyleSheet(
            "QFrame { background:#f0f8ff; border:1px solid #bbdefb; border-radius:4px; }"
        )
        self._new_inv_frame.setVisible(False)
        nfl = QFormLayout(self._new_inv_frame)
        nfl.setSpacing(8)
        nfl.setLabelAlignment(Qt.AlignRight)

        self.inp_new_name = QLineEdit()
        self.inp_new_name.setPlaceholderText("اسم المستثمر الجديد...")
        self.inp_new_name.setMinimumHeight(28)

        self.dt_joined = QDateEdit(QDate.currentDate())
        self.dt_joined.setCalendarPopup(True)
        self.dt_joined.setDisplayFormat("yyyy-MM-dd")
        self.dt_joined.setFixedWidth(130)

        self.inp_new_notes = QLineEdit()
        self.inp_new_notes.setPlaceholderText("ملاحظات...")

        nfl.addRow("الاسم:", self.inp_new_name)
        nfl.addRow("تاريخ الانضمام:", self.dt_joined)
        nfl.addRow("ملاحظات:", self.inp_new_notes)
        inv_lay.addRow(self._new_inv_frame)
        root.addWidget(grp_inv)

        # ── اختيار صف القيد ──
        grp_line = QGroupBox("صف القيد المراد ربطه")
        grp_line.setStyleSheet(grp_inv.styleSheet())
        line_lay = QVBoxLayout(grp_line)

        self.tbl_lines = QTableWidget()
        self.tbl_lines.setColumnCount(5)
        self.tbl_lines.setHorizontalHeaderLabels(
            ["#", "الحساب", "النوع", "مدين", "دائن"]
        )
        self.tbl_lines.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_lines.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_lines.setAlternatingRowColors(True)
        self.tbl_lines.setMinimumHeight(120)
        hh = self.tbl_lines.horizontalHeader()
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        for col, w in {0: 35, 2: 75, 3: 90, 4: 90}.items():
            hh.setSectionResizeMode(col, QHeaderView.Fixed)
            self.tbl_lines.setColumnWidth(col, w)
        self.tbl_lines.itemSelectionChanged.connect(self._on_line_selected)
        line_lay.addWidget(self.tbl_lines)
        root.addWidget(grp_line)

        # ── نوع الحركة ──
        grp_type = QGroupBox("نوع الحركة")
        grp_type.setStyleSheet(grp_inv.styleSheet())
        type_lay = QHBoxLayout(grp_type)

        self.rdo_capital  = QRadioButton("💰  رأس مال (Capital)")
        self.rdo_drawings = QRadioButton("💸  مسحوبات (Drawings)")
        self.rdo_capital.setChecked(True)
        self.rdo_capital.setStyleSheet("font-size:12px; font-weight:bold; color:#2e7d32;")
        self.rdo_drawings.setStyleSheet("font-size:12px; font-weight:bold; color:#c62828;")
        self._type_group = QButtonGroup(self)
        self._type_group.addButton(self.rdo_capital, 0)
        self._type_group.addButton(self.rdo_drawings, 1)

        type_lay.addWidget(self.rdo_capital)
        type_lay.addWidget(self.rdo_drawings)
        type_lay.addStretch()
        root.addWidget(grp_type)

        # ── ملاحظة ──
        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("ملاحظة إضافية (اختياري)...")
        self.inp_notes.setMinimumHeight(28)
        root.addWidget(QLabel("ملاحظة:"))
        root.addWidget(self.inp_notes)

        # ── الروابط الموجودة ──
        root.addWidget(section_label("── الروابط الموجودة لهذا القيد ──"))
        self.tbl_existing = QTableWidget()
        self.tbl_existing.setColumnCount(5)
        self.tbl_existing.setHorizontalHeaderLabels(
            ["المستثمر", "النوع", "الحساب", "المبلغ", "حذف"]
        )
        self.tbl_existing.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_existing.setAlternatingRowColors(True)
        self.tbl_existing.setMaximumHeight(100)
        hh2 = self.tbl_existing.horizontalHeader()
        hh2.setSectionResizeMode(0, QHeaderView.Stretch)
        for col, w in {1: 80, 2: 120, 3: 80, 4: 50}.items():
            hh2.setSectionResizeMode(col, QHeaderView.Fixed)
            self.tbl_existing.setColumnWidth(col, w)
        root.addWidget(self.tbl_existing)

        # ── أزرار ──
        btn_link   = QPushButton("🔗  ربط")
        btn_cancel = QPushButton("✖  إغلاق")
        btn_link.setMinimumHeight(34)
        btn_cancel.setMinimumHeight(34)
        btn_link.setStyleSheet("""
            QPushButton { background:#1565c0; color:white; font-weight:bold;
                border-radius:6px; padding:0 20px; }
            QPushButton:hover { background:#0d47a1; }
        """)
        btn_cancel.setStyleSheet("""
            QPushButton { background:#f5f5f5; color:#555;
                border:1px solid #ddd; border-radius:6px; padding:0 16px; }
            QPushButton:hover { background:#eeeeee; }
        """)
        btn_link.clicked.connect(self._link)
        btn_cancel.clicked.connect(self.accept)
        root.addLayout(buttons_row(btn_link, btn_cancel))

    def _on_investor_changed(self):
        data = self.cmb_investor.currentData()
        self._new_inv_frame.setVisible(data == "__new__")

    def _load_lines(self):
        """يحمّل صفوف القيد في الجدول."""
        lines = fetch_entry_lines(self.conn, self.entry_id)
        self.tbl_lines.setRowCount(0)
        self._line_ids = []
        for ln in lines:
            r = self.tbl_lines.rowCount()
            self.tbl_lines.insertRow(r)
            self._line_ids.append(ln["id"])

            self.tbl_lines.setItem(r, 0, QTableWidgetItem(str(r + 1)))
            acc_item = QTableWidgetItem(
                f"{ln['account_code']} — {ln['account_name']}"
            )
            acc_item.setToolTip(f"{ln['account_code']} — {ln['account_name']}")
            self.tbl_lines.setItem(r, 1, acc_item)

            acc_type = ln.get("account_type", "")
            self.tbl_lines.setItem(r, 2, QTableWidgetItem(acc_type))

            # حدد نوع الحركة تلقائياً
            if ln["debit"] > 0:
                di = QTableWidgetItem(f"{ln['debit']:,.2f}")
                di.setForeground(QColor("#1565c0"))
                self.tbl_lines.setItem(r, 3, di)
                self.tbl_lines.setItem(r, 4, QTableWidgetItem(""))
            else:
                self.tbl_lines.setItem(r, 3, QTableWidgetItem(""))
                ci = QTableWidgetItem(f"{ln['credit']:,.2f}")
                ci.setForeground(QColor("#c62828"))
                self.tbl_lines.setItem(r, 4, ci)

        if lines:
            self.tbl_lines.selectRow(0)

    def _on_line_selected(self):
        """اقترح نوع الحركة بناءً على الحساب المختار."""
        row = self.tbl_lines.currentRow()
        if row < 0 or row >= len(self._line_ids):
            return
        lines = fetch_entry_lines(self.conn, self.entry_id)
        if row < len(lines):
            ln = lines[row]
            acc_type = ln.get("account_type", "")
            if acc_type == "capital":
                self.rdo_capital.setChecked(True)
            elif acc_type == "drawings":
                self.rdo_drawings.setChecked(True)

    def _load_existing_links(self):
        """يحمّل الروابط الموجودة للقيد."""
        links = fetch_entry_investor_links(self.conn, self.entry_id)
        self.tbl_existing.setRowCount(0)
        self._existing_link_ids = []
        for lk in links:
            r = self.tbl_existing.rowCount()
            self.tbl_existing.insertRow(r)
            self._existing_link_ids.append(lk["id"])

            self.tbl_existing.setItem(r, 0, QTableWidgetItem(lk["investor_name"]))
            move_ar = "رأس مال" if lk["move_type"] == "capital" else "مسحوبات"
            mt_item = QTableWidgetItem(move_ar)
            mt_item.setForeground(
                QColor("#2e7d32") if lk["move_type"] == "capital" else QColor("#c62828")
            )
            self.tbl_existing.setItem(r, 1, mt_item)
            self.tbl_existing.setItem(r, 2, QTableWidgetItem(""))
            self.tbl_existing.setItem(r, 3, QTableWidgetItem(f"{lk['amount']:,.2f}"))
            btn_del = QPushButton("🗑️")
            btn_del.setFixedSize(40, 24)
            btn_del.setStyleSheet("color:#c62828; border:none; background:transparent;")
            btn_del.clicked.connect(lambda _, lid=lk["id"]: self._delete_link(lid))
            self.tbl_existing.setCellWidget(r, 4, btn_del)

    def _delete_link(self, link_id: int):
        if QMessageBox.question(
            self, "تأكيد", "حذف هذا الربط؟",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            delete_investor_link(self.conn, link_id)
            self._load_existing_links()
            bus.data_changed.emit()

    def _link(self):
        """يطبق الربط."""
        data = self.cmb_investor.currentData()

        # إنشاء مستثمر جديد لو لزم
        if data == "__new__":
            name = self.inp_new_name.text().strip()
            if not name:
                QMessageBox.warning(self, "تنبيه", "أدخل اسم المستثمر الجديد")
                return
            existing = investor_exists(self.conn, name)
            if existing:
                investor_id = existing
            else:
                investor_id = insert_investor(
                    self.conn, name,
                    notes=self.inp_new_notes.text().strip(),
                    joined_at=self.dt_joined.date().toString("yyyy-MM-dd")
                )
            bus.data_changed.emit()
        elif data is None:
            QMessageBox.warning(self, "تنبيه", "اختر مستثمراً أولاً")
            return
        else:
            investor_id = data

        # الصف المختار
        row = self.tbl_lines.currentRow()
        if row < 0 or row >= len(self._line_ids):
            QMessageBox.warning(self, "تنبيه", "اختر صف قيد أولاً")
            return
        line_id = self._line_ids[row]

        # تحديد المبلغ من الصف
        lines = fetch_entry_lines(self.conn, self.entry_id)
        if row >= len(lines):
            return
        ln = lines[row]
        amount = ln["debit"] if ln["debit"] > 0 else ln["credit"]

        # نوع الحركة
        move_type = "capital" if self.rdo_capital.isChecked() else "drawings"

        link_investor_to_line(
            self.conn, investor_id, self.entry_id, line_id,
            move_type, amount, self.inp_notes.text().strip()
        )

        bus.data_changed.emit()
        self._load_existing_links()
        QMessageBox.information(self, "تم", "✅ تم ربط القيد بالمستثمر")


# ══════════════════════════════════════════════════════════
# فورم إضافة / تعديل مستثمر
# ══════════════════════════════════════════════════════════

class _InvestorFormPanel(QWidget, EditModeMixin):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self.init_edit_mode(self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(10)

        grp = QGroupBox("بيانات المستثمر")
        grp.setStyleSheet("""
            QGroupBox { font-weight:bold; color:#1565c0;
                border:1px solid #e0e0e0; border-radius:8px;
                margin-top:8px; padding-top:10px; }
            QGroupBox::title { subcontrol-origin:margin; padding:0 8px; }
        """)
        form = QFormLayout(grp)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = QLabel("─── مستثمر جديد ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0; font-size:12px;")
        form.addRow(self.lbl_mode)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم المستثمر...")
        self.inp_name.setMinimumHeight(32)

        self.dt_joined = QDateEdit(QDate.currentDate())
        self.dt_joined.setCalendarPopup(True)
        self.dt_joined.setDisplayFormat("yyyy-MM-dd")
        self.dt_joined.setFixedWidth(140)
        self.dt_joined.setMinimumHeight(30)

        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("ملاحظات...")
        self.inp_notes.setMinimumHeight(28)

        form.addRow("الاسم:", self.inp_name)
        form.addRow("تاريخ الانضمام:", self.dt_joined)
        form.addRow("ملاحظات:", self.inp_notes)

        self.btn_add    = QPushButton("➕  إضافة مستثمر")
        self.btn_save   = QPushButton("💾  حفظ التعديل")
        self.btn_cancel = QPushButton("✖  إلغاء")
        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn.setMinimumHeight(32)
        self.btn_add.setStyleSheet(
            "QPushButton { background:#1565c0; color:white; font-weight:bold;"
            "border-radius:6px; padding:0 14px; }"
            "QPushButton:hover { background:#0d47a1; }"
        )
        self.btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save_edit)
        self.btn_cancel.clicked.connect(self._cancel)
        form.addRow(self._btn_widget())

        root.addWidget(grp)
        root.addStretch()

    def _btn_widget(self):
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.btn_add)
        lay.addWidget(self.btn_save)
        lay.addWidget(self.btn_cancel)
        lay.addStretch()
        return w

    def _collect(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم المستثمر")
            return None, None, None
        return (
            name,
            self.inp_notes.text().strip(),
            self.dt_joined.date().toString("yyyy-MM-dd"),
        )

    def _add(self):
        name, notes, joined_at = self._collect()
        if not name:
            return
        if investor_exists(self.conn, name):
            QMessageBox.warning(self, "تنبيه", f"المستثمر «{name}» موجود بالفعل")
            return
        insert_investor(self.conn, name, notes, joined_at)
        self._reset()
        bus.data_changed.emit()

    def _save_edit(self):
        name, notes, joined_at = self._collect()
        if not name:
            return
        update_investor(self.conn, self._editing_id, name, notes, joined_at)
        self._reset()
        bus.data_changed.emit()

    def _cancel(self):
        self._reset()

    def load_for_edit(self, inv_id: int):
        inv = fetch_investor(self.conn, inv_id)
        if not inv:
            return
        self.inp_name.setText(inv["name"])
        self.inp_notes.setText(inv["notes"] or "")
        self.dt_joined.setDate(QDate.fromString(inv["joined_at"], "yyyy-MM-dd"))
        self.enter_edit_mode(inv_id, f"─── تعديل: {inv['name']} ───")

    def _reset(self):
        self.inp_name.clear()
        self.inp_notes.clear()
        self.dt_joined.setDate(QDate.currentDate())
        self.exit_edit_mode("─── مستثمر جديد ───")


# ══════════════════════════════════════════════════════════
# جدول المستثمرين
# ══════════════════════════════════════════════════════════

class _InvestorsTable(QWidget):
    def __init__(self, conn, form: _InvestorFormPanel, on_select, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._form     = form
        self._on_select = on_select
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(6)

        root.addWidget(section_label("── المستثمرون ──"))

        self.table = make_table(
            ["ID", "الاسم", "تاريخ الانضمام",
             "رأس المال", "المسحوبات", "صافي الاستثمار"],
            stretch_col=1
        )
        setup_table_columns(
            self.table,
            widths={0: 40, 2: 110, 3: 110, 4: 110, 5: 120},
            stretch_col=1,
        )
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(
            lambda: self._on_select(self._selected_id())
        )
        root.addWidget(self.table, stretch=1)

        btn_edit = QPushButton("✏️  تعديل")
        btn_del  = danger_button("🗑️  حذف")
        for btn in (btn_edit, btn_del):
            btn.setMinimumHeight(30)
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        root.addLayout(buttons_row(btn_edit, btn_del))

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return int(item.text()) if item else None

    def _load(self):
        summaries = calc_all_investors_summary(self.conn)
        prev_id   = self._selected_id()
        self.table.setRowCount(0)

        for s in summaries:
            r = self.table.rowCount()
            self.table.insertRow(r)

            self.table.setItem(r, 0, QTableWidgetItem(str(s["investor_id"])))
            name_item = QTableWidgetItem(s["investor_name"])
            name_item.setFont(QFont("", -1, QFont.Bold))
            self.table.setItem(r, 1, name_item)
            self.table.setItem(r, 2, QTableWidgetItem(s.get("joined_at", "─")))

            # رأس المال
            cap_item = QTableWidgetItem(f"{s['total_capital']:,.2f}")
            cap_item.setForeground(QColor("#2e7d32"))
            self.table.setItem(r, 3, cap_item)

            # المسحوبات
            drw_item = QTableWidgetItem(f"{s['total_drawings']:,.2f}")
            drw_item.setForeground(QColor("#c62828"))
            self.table.setItem(r, 4, drw_item)

            # الصافي
            net = s["net_investment"]
            net_item = QTableWidgetItem(f"{net:,.2f}")
            net_item.setFont(QFont("", -1, QFont.Bold))
            net_item.setForeground(QColor("#1565c0") if net >= 0 else QColor("#c62828"))
            self.table.setItem(r, 5, net_item)

        # استعادة التحديد
        if prev_id is not None:
            for r in range(self.table.rowCount()):
                if int(self.table.item(r, 0).text()) == prev_id:
                    self.table.selectRow(r)
                    break

    def _edit(self):
        inv_id = self._selected_id()
        if not inv_id:
            QMessageBox.information(self, "تنبيه", "اختر مستثمراً أولاً")
            return
        self._form.load_for_edit(inv_id)

    def _delete(self):
        inv_id = self._selected_id()
        if not inv_id:
            QMessageBox.information(self, "تنبيه", "اختر مستثمراً أولاً")
            return
        inv = fetch_investor(self.conn, inv_id)
        if not inv:
            return
        if confirm_delete(self, inv["name"]):
            delete_investor(self.conn, inv_id)
            bus.data_changed.emit()


# ══════════════════════════════════════════════════════════
# لوحة تفاصيل مستثمر واحد
# ══════════════════════════════════════════════════════════

class _InvestorDetails(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(10)

        # ── العنوان ──
        self.lbl_title = QLabel("اختر مستثمراً لعرض تفاصيله")
        self.lbl_title.setStyleSheet(
            "font-size:14px; font-weight:bold; color:#1565c0;"
            "background:#e8f4fd; border-radius:8px; padding:10px 16px;"
        )
        self.lbl_title.setAlignment(Qt.AlignCenter)
        root.addWidget(self.lbl_title)

        # ── بطاقات الإحصائيات ──
        cards = QHBoxLayout()
        cards.setSpacing(10)
        f1, self.lbl_capital   = _stat_box("إجمالي رأس المال",      "#2e7d32")
        f2, self.lbl_drawings  = _stat_box("إجمالي المسحوبات",      "#c62828")
        f3, self.lbl_net       = _stat_box("صافي الاستثمار الحالي", "#1565c0")
        f4, self.lbl_entries   = _stat_box("عدد الحركات",           "#6a1b9a")
        for f in (f1, f2, f3, f4):
            cards.addWidget(f, stretch=1)
        root.addLayout(cards)

        # ── جدول الحركات ──
        root.addWidget(section_label("── حركات المستثمر ──"))
        self.table = make_table(
            ["التاريخ", "رقم القيد", "الوصف", "النوع", "الحساب", "المبلغ"],
            stretch_col=2
        )
        setup_table_columns(
            self.table,
            widths={0: 90, 1: 85, 3: 80, 4: 140, 5: 110},
            stretch_col=2,
        )
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, stretch=1)

        # ── ملاحظات ──
        self.lbl_notes = QLabel("")
        self.lbl_notes.setStyleSheet(
            "font-size:10px; color:#888; background:transparent;"
        )
        self.lbl_notes.setWordWrap(True)
        root.addWidget(self.lbl_notes)

    def load(self, investor_id: int):
        s = calc_investor_summary(self.conn, investor_id)
        if not s:
            return

        self.lbl_title.setText(
            f"👤  {s['investor_name']}  │  انضم: {s.get('joined_at', '─')}"
        )

        self.lbl_capital.setText(_money(s["total_capital"]))
        self.lbl_drawings.setText(_money(s["total_drawings"]))

        net = s["net_investment"]
        self.lbl_net.setText(_money(net))
        color = "#1565c0" if net >= 0 else "#c62828"
        self.lbl_net.setStyleSheet(
            f"font-size:15px; font-weight:bold; color:{color};"
            "background:transparent; border:none;"
        )

        entries = s.get("entries", [])
        self.lbl_entries.setText(str(len(entries)))

        self.table.setRowCount(0)
        for e in entries:
            r = self.table.rowCount()
            self.table.insertRow(r)

            self.table.setItem(r, 0, QTableWidgetItem(e.get("date", "─")))
            self.table.setItem(r, 1, QTableWidgetItem(e.get("ref_no", "─")))

            desc_item = QTableWidgetItem(e.get("entry_desc", "─"))
            desc_item.setToolTip(e.get("entry_desc", ""))
            self.table.setItem(r, 2, desc_item)

            move_type = e.get("move_type", "")
            move_ar   = "💰 رأس مال" if move_type == "capital" else "💸 مسحوبات"
            mt_item   = QTableWidgetItem(move_ar)
            mt_item.setForeground(
                QColor("#2e7d32") if move_type == "capital" else QColor("#c62828")
            )
            self.table.setItem(r, 3, mt_item)

            acc = f"{e.get('account_code','')} — {e.get('account_name','')}"
            acc_item = QTableWidgetItem(acc)
            acc_item.setToolTip(acc)
            self.table.setItem(r, 4, acc_item)

            amt_item = QTableWidgetItem(f"{e.get('amount', 0):,.2f}")
            amt_item.setForeground(
                QColor("#2e7d32") if move_type == "capital" else QColor("#c62828")
            )
            self.table.setItem(r, 5, amt_item)

        notes_text = s.get("notes", "")
        self.lbl_notes.setText(f"📝 {notes_text}" if notes_text else "")

    def clear(self):
        self.lbl_title.setText("اختر مستثمراً لعرض تفاصيله")
        for lbl in (self.lbl_capital, self.lbl_drawings,
                    self.lbl_net, self.lbl_entries):
            lbl.setText("─")
        self.table.setRowCount(0)
        self.lbl_notes.setText("")


# ══════════════════════════════════════════════════════════
# لوحة ربط قيود بمستثمرين (من قيود اليومية)
# ══════════════════════════════════════════════════════════

class _LinkFromJournalPanel(QWidget):
    """
    لوحة تتيح للمستخدم فتح نافذة الربط من قيود اليومية.
    تعرض القيود الأخيرة مع زر "ربط بمستثمر" لكل قيد.
    """

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(6)

        root.addWidget(section_label("── ربط القيود بالمستثمرين ──"))

        hint = QLabel(
            "💡 اختر قيداً واضغط «ربط» لنسبته لمستثمر معين"
        )
        hint.setStyleSheet(
            "color:#555; font-size:10px; background:#fffde7;"
            "border:1px solid #f9a825; border-radius:4px; padding:6px 10px;"
        )
        hint.setWordWrap(True)
        root.addWidget(hint)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["رقم القيد", "التاريخ", "الوصف", "DR", "CR", "ربط"]
        )
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        for col, w in {0: 80, 1: 90, 3: 85, 4: 85, 5: 70}.items():
            hh.setSectionResizeMode(col, QHeaderView.Fixed)
            self.table.setColumnWidth(col, w)
        root.addWidget(self.table, stretch=1)

    def _load(self):
        entries = fetch_all_entries(self.conn, limit=100)
        self.table.setRowCount(0)
        self._entry_ids = []

        for e in entries:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self._entry_ids.append(e["id"])

            self.table.setItem(r, 0, QTableWidgetItem(e["ref_no"]))
            self.table.setItem(r, 1, QTableWidgetItem(e["date"]))
            desc_item = QTableWidgetItem(e["description"])
            desc_item.setToolTip(e["description"])
            self.table.setItem(r, 2, desc_item)
            self.table.setItem(r, 3, QTableWidgetItem(f"{e['total_debit']:,.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"{e['total_credit']:,.2f}"))

            # زر الربط
            btn_link = QPushButton("🔗 ربط")
            btn_link.setMinimumHeight(24)
            btn_link.setStyleSheet(
                "QPushButton { background:#e8f4fd; color:#1565c0;"
                "border:1px solid #90caf9; border-radius:4px;"
                "font-size:10px; font-weight:bold; padding:2px 6px; }"
                "QPushButton:hover { background:#1565c0; color:white; }"
            )
            btn_link.clicked.connect(
                lambda _, eid=e["id"]: self._open_link_dialog(eid)
            )
            self.table.setCellWidget(r, 5, btn_link)

    def _open_link_dialog(self, entry_id: int):
        dlg = LinkInvestorDialog(self.conn, entry_id, parent=self)
        dlg.exec_()
        bus.data_changed.emit()


# ══════════════════════════════════════════════════════════
# لوحة ملخص جميع المستثمرين
# ══════════════════════════════════════════════════════════

class _AllInvestorsSummary(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(10)

        # ── بطاقات إجمالية ──
        cards = QHBoxLayout()
        cards.setSpacing(10)
        f1, self.lbl_total_inv   = _stat_box("عدد المستثمرين",          "#1565c0")
        f2, self.lbl_total_cap   = _stat_box("إجمالي رأس المال الكلي",  "#2e7d32")
        f3, self.lbl_total_draw  = _stat_box("إجمالي المسحوبات الكلية", "#c62828")
        f4, self.lbl_total_net   = _stat_box("صافي الاستثمار الكلي",    "#6a1b9a")
        for f in (f1, f2, f3, f4):
            cards.addWidget(f, stretch=1)
        root.addLayout(cards)

        # ── جدول مقارنة ──
        root.addWidget(section_label("── مقارنة المستثمرين ──"))
        self.table = make_table(
            ["المستثمر", "تاريخ الانضمام",
             "رأس المال", "المسحوبات", "صافي الاستثمار", "النسبة %"],
            stretch_col=0,
        )
        setup_table_columns(
            self.table,
            widths={1: 110, 2: 110, 3: 110, 4: 120, 5: 80},
            stretch_col=0,
        )
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, stretch=1)

    def _load(self):
        summaries = calc_all_investors_summary(self.conn)

        total_cap  = sum(s["total_capital"]  for s in summaries)
        total_draw = sum(s["total_drawings"] for s in summaries)
        total_net  = sum(s["net_investment"] for s in summaries)

        self.lbl_total_inv.setText(str(len(summaries)))
        self.lbl_total_cap.setText(_money(total_cap))
        self.lbl_total_draw.setText(_money(total_draw))
        self.lbl_total_net.setText(_money(total_net))

        self.table.setRowCount(0)
        for s in summaries:
            r = self.table.rowCount()
            self.table.insertRow(r)

            name_item = QTableWidgetItem(s["investor_name"])
            name_item.setFont(QFont("", -1, QFont.Bold))
            self.table.setItem(r, 0, name_item)
            self.table.setItem(r, 1, QTableWidgetItem(s.get("joined_at", "─")))

            cap_item = QTableWidgetItem(f"{s['total_capital']:,.2f}")
            cap_item.setForeground(QColor("#2e7d32"))
            self.table.setItem(r, 2, cap_item)

            drw_item = QTableWidgetItem(f"{s['total_drawings']:,.2f}")
            drw_item.setForeground(QColor("#c62828"))
            self.table.setItem(r, 3, drw_item)

            net = s["net_investment"]
            net_item = QTableWidgetItem(f"{net:,.2f}")
            net_item.setFont(QFont("", -1, QFont.Bold))
            net_item.setForeground(QColor("#1565c0") if net >= 0 else QColor("#c62828"))
            self.table.setItem(r, 4, net_item)

            # النسبة من إجمالي رأس المال
            pct = (s["total_capital"] / total_cap * 100) if total_cap > 0 else 0.0
            pct_item = QTableWidgetItem(f"{pct:.1f} %")
            self.table.setItem(r, 5, pct_item)


# ══════════════════════════════════════════════════════════
# التبويب الرئيسي للمستثمرين
# ══════════════════════════════════════════════════════════

class InvestorsTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        create_investors_tables(conn)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border:none; background:#f9f9f9; }
            QTabBar::tab {
                background:#f0f0f0; border:1px solid #ddd;
                border-bottom:none; padding:8px 14px;
                font-size:11px; color:#555;
            }
            QTabBar::tab:selected {
                background:white; color:#1565c0;
                font-weight:bold; border-top:2px solid #1565c0;
            }
            QTabBar::tab:hover:!selected { background:#e8f0fe; color:#1565c0; }
        """)

        # ── تبويب 1: إدارة المستثمرين ──
        mgmt_widget = self._build_management_tab()
        tabs.addTab(mgmt_widget, "👥  المستثمرون")

        # ── تبويب 2: ربط بقيود ──
        link_widget = _LinkFromJournalPanel(self.conn)
        tabs.addTab(link_widget, "🔗  ربط بالقيود")

        # ── تبويب 3: ملخص شامل ──
        summary_widget = _AllInvestorsSummary(self.conn)
        tabs.addTab(summary_widget, "📊  ملخص الاستثمار")

        root.addWidget(tabs)

    def _build_management_tab(self) -> QWidget:
        widget = QWidget()
        root   = QVBoxLayout(widget)
        root.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet("""
            QSplitter::handle { background:#e0e0e0; }
            QSplitter::handle:hover { background:#bbdefb; }
        """)

        # ── الجزء العلوي: الجدول + الفورم ──
        top_splitter = QSplitter(Qt.Horizontal)
        top_splitter.setHandleWidth(6)

        form  = _InvestorFormPanel(self.conn)
        self._details = _InvestorDetails(self.conn)

        table = _InvestorsTable(self.conn, form, self._on_investor_selected)

        top_splitter.addWidget(form)
        top_splitter.addWidget(table)
        top_splitter.setSizes([280, 520])
        top_splitter.setCollapsible(0, True)

        splitter.addWidget(top_splitter)
        splitter.addWidget(self._details)
        splitter.setSizes([280, 400])

        root.addWidget(splitter)
        return widget

    def _on_investor_selected(self, inv_id):
        if inv_id:
            self._details.load(inv_id)
        else:
            self._details.clear()