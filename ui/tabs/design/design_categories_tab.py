"""
ui/tabs/design/design_categories_tab.py
========================================
تبويب إدارة تصنيفات التصميم.

بسيط: جدول + فورم CRUD
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QGroupBox, QFormLayout,
    QColorDialog, QTextEdit, QMessageBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor, QFont

from db.design.design_repo import (
    fetch_all_design_categories,
    insert_design_category, update_design_category, delete_design_category,
)
from ui.events import bus

_ICONS = ["📐", "🪑", "🖼", "🚪", "🪞", "🛏", "📦", "🔩", "🪟", "🛋", "🏠", "⚙️"]

_BTN_ADD = """
    QPushButton { background:#e8f5e9; color:#2e7d32;
        border:1px solid #a5d6a7; border-radius:5px;
        padding:0 14px; font-weight:bold; }
    QPushButton:hover { background:#c8e6c9; }
"""
_BTN_SAVE = """
    QPushButton { background:#e3f2fd; color:#1565c0;
        border:1px solid #90caf9; border-radius:5px;
        padding:0 14px; font-weight:bold; }
    QPushButton:hover { background:#bbdefb; }
"""
_BTN_DEL = """
    QPushButton { background:#ffebee; color:#c62828;
        border:1px solid #ef9a9a; border-radius:5px; padding:0 12px; }
    QPushButton:hover { background:#ffcdd2; }
"""
_BTN_CANCEL = """
    QPushButton { background:#f5f5f5; color:#555;
        border:1px solid #ddd; border-radius:5px; padding:0 12px; }
    QPushButton:hover { background:#eee; }
"""


class DesignCategoriesTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._editing_id = None
        self._color      = "#607d8b"
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(4)
        splitter.setStyleSheet("""
            QSplitter::handle { background:#e0e0e0; }
            QSplitter::handle:hover { background:#ce93d8; }
        """)
        splitter.addWidget(self._build_list_panel())
        splitter.addWidget(self._build_form_panel())
        splitter.setSizes([500, 380])
        root.addWidget(splitter)

    def _build_list_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background:#fafafa;")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(12, 12, 8, 12)
        lay.setSpacing(8)

        lbl = QLabel("🏷  تصنيفات التصميم")
        lbl.setStyleSheet("font-weight:bold; font-size:13px; color:#6a1b9a;")
        lay.addWidget(lbl)

        hint = QLabel(
            "💡 التصنيفات بتساعدك تجمع الأشكال المتشابهة:\n"
            "  مثال: أثاث، ديكور، أبواب، شبابيك..."
        )
        hint.setStyleSheet(
            "font-size:10px; color:#555; background:#f3e5f5;"
            "border:1px solid #ce93d8; border-radius:4px; padding:5px 8px;"
        )
        hint.setWordWrap(True)
        lay.addWidget(hint)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "الأيقونة", "الاسم", "عدد الأشكال"])
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.Interactive)
        hh.setSectionResizeMode(3, QHeaderView.Interactive)
        self.table.setColumnWidth(1, 60)
        self.table.setColumnWidth(3, 100)
        hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.selectionModel().selectionChanged.connect(self._on_select)
        lay.addWidget(self.table, stretch=1)

        self.lbl_count = QLabel()
        self.lbl_count.setStyleSheet("color:#6a1b9a; font-size:10px;")
        lay.addWidget(self.lbl_count)

        btn_row = QHBoxLayout()
        self.btn_del = QPushButton("🗑 حذف المحدد")
        self.btn_del.setMinimumHeight(30)
        self.btn_del.setStyleSheet(_BTN_DEL)
        self.btn_del.clicked.connect(self._delete)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_del)
        lay.addLayout(btn_row)

        return panel

    def _build_form_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background:white;")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(8, 12, 12, 12)
        lay.setSpacing(10)

        grp = QGroupBox("بيانات التصنيف")
        grp.setStyleSheet("""
            QGroupBox { font-weight:bold; color:#6a1b9a;
                border:1px solid #ce93d8; border-radius:6px;
                margin-top:6px; padding-top:6px; background:#f3e5f5; }
            QGroupBox::title { subcontrol-origin:margin; padding:0 6px; }
        """)
        form = QFormLayout(grp)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.inp_name = QLineEdit()
        self.inp_name.setMinimumHeight(32)
        self.inp_name.setPlaceholderText("مثال: أثاث، ديكور، أبواب...")
        form.addRow("الاسم :", self.inp_name)

        # الأيقونة
        icon_row = QHBoxLayout()
        self.inp_icon = QLineEdit()
        self.inp_icon.setMinimumHeight(32)
        self.inp_icon.setMaximumWidth(80)
        self.inp_icon.setPlaceholderText("🪑")
        self.inp_icon.setText("📐")

        # أزرار الأيقونات السريعة
        for ico in _ICONS:
            btn_ico = QPushButton(ico)
            btn_ico.setFixedSize(32, 32)
            btn_ico.setStyleSheet(
                "QPushButton{border:1px solid #e0e0e0; border-radius:4px;"
                "background:white;}"
                "QPushButton:hover{background:#f3e5f5;}"
            )
            btn_ico.clicked.connect(lambda _, i=ico: self.inp_icon.setText(i))
            icon_row.addWidget(btn_ico)
        icon_row.addStretch()
        form.addRow("الأيقونة :", self.inp_icon)
        form.addRow("", icon_row)

        # اللون
        color_row = QHBoxLayout()
        self.lbl_color = QLabel()
        self.lbl_color.setFixedSize(32, 32)
        self._refresh_color_preview()
        btn_color = QPushButton("اختر لون")
        btn_color.setMinimumHeight(28)
        btn_color.clicked.connect(self._pick_color)
        color_row.addWidget(self.lbl_color)
        color_row.addWidget(btn_color)
        color_row.addStretch()
        form.addRow("اللون :", color_row)

        self.inp_notes = QTextEdit()
        self.inp_notes.setMaximumHeight(70)
        self.inp_notes.setPlaceholderText("ملاحظات اختيارية...")
        form.addRow("ملاحظات :", self.inp_notes)

        self.lbl_mode = QLabel("— تصنيف جديد —")
        self.lbl_mode.setStyleSheet(
            "font-weight:bold; color:#6a1b9a; font-size:11px;"
        )
        form.addRow(self.lbl_mode)

        btn_row = QHBoxLayout()
        self.btn_add    = QPushButton("➕ إضافة")
        self.btn_save   = QPushButton("💾 حفظ")
        self.btn_cancel = QPushButton("✖ إلغاء")
        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn.setMinimumHeight(30)
        self.btn_add.setStyleSheet(_BTN_ADD)
        self.btn_save.setStyleSheet(_BTN_SAVE)
        self.btn_cancel.setStyleSheet(_BTN_CANCEL)

        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)

        self.btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self._reset)

        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_cancel)
        btn_row.addStretch()
        form.addRow(btn_row)
        lay.addWidget(grp)
        lay.addStretch()
        return panel

    # ══════════════════════════════════════════════════════
    # تحميل
    # ══════════════════════════════════════════════════════

    def _load(self):
        cats = fetch_all_design_categories(self.conn)
        self.table.setRowCount(0)
        for c in cats:
            # عدد الأشكال
            cnt = self.conn.execute(
                "SELECT COUNT(*) as n FROM shapes WHERE category_id=?", (c["id"],)
            ).fetchone()["n"]

            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(c["id"])))

            # أيقونة
            ico_item = QTableWidgetItem(c["icon"] or "📐")
            ico_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 1, ico_item)

            # اسم
            name_item = QTableWidgetItem(c["name"])
            name_item.setForeground(QColor(c["color"]))
            name_item.setFont(QFont("", -1, QFont.Bold))
            self.table.setItem(r, 2, name_item)

            cnt_item = QTableWidgetItem(str(cnt) if cnt else "—")
            cnt_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 3, cnt_item)

        self.lbl_count.setText(f"({len(cats)} تصنيف)")

    # ══════════════════════════════════════════════════════
    # Signal handlers
    # ══════════════════════════════════════════════════════

    def _on_select(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        cat_id = int(self.table.item(rows[0].row(), 0).text())
        cats = fetch_all_design_categories(self.conn)
        cat = next((c for c in cats if c["id"] == cat_id), None)
        if not cat:
            return
        self._editing_id = cat_id
        self.inp_name.setText(cat["name"])
        self.inp_icon.setText(cat["icon"] or "📐")
        self._color = cat["color"] or "#607d8b"
        self._refresh_color_preview()
        self.inp_notes.setPlainText(cat["notes"] or "")
        self.lbl_mode.setText(f"تعديل: {cat['name']}")
        self.btn_add.setVisible(False)
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)

    def _pick_color(self):
        col = QColorDialog.getColor(QColor(self._color), self, "اختر اللون")
        if col.isValid():
            self._color = col.name()
            self._refresh_color_preview()

    def _refresh_color_preview(self):
        self.lbl_color.setStyleSheet(
            f"background:{self._color}; border-radius:4px;"
            "border:1px solid #ccc;"
        )

    # ══════════════════════════════════════════════════════
    # CRUD
    # ══════════════════════════════════════════════════════

    def _add(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم التصنيف")
            return
        icon  = self.inp_icon.text().strip() or "📐"
        notes = self.inp_notes.toPlainText().strip()
        insert_design_category(self.conn, name, self._color, icon, notes)
        self._reset()
        bus.data_changed.emit()

    def _save(self):
        if not self._editing_id:
            return
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم التصنيف")
            return
        icon  = self.inp_icon.text().strip() or "📐"
        notes = self.inp_notes.toPlainText().strip()
        update_design_category(self.conn, self._editing_id,
                                name, self._color, icon, notes)
        self._reset()
        bus.data_changed.emit()

    def _delete(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "تنبيه", "اختر تصنيفاً أولاً")
            return
        cat_id = int(self.table.item(rows[0].row(), 0).text())
        name_item = self.table.item(rows[0].row(), 2)
        name = name_item.text() if name_item else str(cat_id)
        cnt = self.conn.execute(
            "SELECT COUNT(*) as n FROM shapes WHERE category_id=?", (cat_id,)
        ).fetchone()["n"]
        msg = f"حذف تصنيف «{name}»؟"
        if cnt:
            msg += f"\n⚠️ {cnt} شكل مرتبط — سيفقد التصنيف."
        if QMessageBox.question(
            self, "تأكيد", msg, QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            delete_design_category(self.conn, cat_id)
            self._reset()
            bus.data_changed.emit()

    def _reset(self):
        self._editing_id = None
        self.inp_name.clear()
        self.inp_icon.setText("📐")
        self._color = "#607d8b"
        self._refresh_color_preview()
        self.inp_notes.clear()
        self.lbl_mode.setText("— تصنيف جديد —")
        self.btn_add.setVisible(True)
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        self.table.clearSelection()
        self._load()