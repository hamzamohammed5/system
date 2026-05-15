"""
ui/tabs/design/dim_categories_tab.py
======================================
تبويب إدارة تصنيفات مجموعات المقاسات (scope='design').

يتيح:
  - إنشاء / تعديل / حذف تصنيفات بـ scope='design'
  - لكل تصنيف: اسم، لون، وحدة افتراضية
  - لكل تصنيف: قائمة حقول افتراضية (القالب)
    حيث كل حقل: مفتاح، تسمية، وحدة، نوع، مطلوب

هذه الحقول تُنسخ تلقائياً لأي مجموعة مقاسات جديدة تختار هذا التصنيف.
"""

import json

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QGroupBox, QFormLayout,
    QMessageBox, QCheckBox, QColorDialog, QFrame,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor, QFont

from db.shared.categories_repo import (
    fetch_categories_by_scope,
    fetch_category,
    insert_category,
    update_category,
    delete_category,
    get_template_fields,
    set_template_fields,
)
from ui.events import bus


_FIELD_TYPES = [
    ("number",  "🔢 رقم"),
    ("text",    "📝 نص"),
    ("boolean", "✅ نعم/لا"),
    ("select",  "📋 قائمة اختيار"),
]

_UNITS = ["mm", "cm", "m", "inch", "kg", "g", "L", "m²", "m³"]

_PRESET_COLORS = [
    "#795548", "#546e7a", "#7b1fa2", "#0288d1",
    "#2e7d32", "#f57f17", "#c62828", "#1565c0",
    "#00695c", "#37474f",
]

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


class DimCategoriesTab(QWidget):
    """
    تبويب تصنيفات مجموعات المقاسات.
    conn = erp.db (فيه جدول categories).
    """

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn         = conn   # erp.db
        self._editing_id  = None
        self._color       = "#607d8b"
        self._editing_fld_idx = None   # index الحقل الذي يتم تعديله في القائمة
        self._template_fields: list[dict] = []   # حقول التصنيف المحدد (في الذاكرة)
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
            QSplitter::handle:hover { background:#90caf9; }
        """)
        splitter.addWidget(self._build_list_panel())
        splitter.addWidget(self._build_detail_panel())
        splitter.setSizes([360, 620])
        root.addWidget(splitter)

    # ── لوحة قائمة التصنيفات (يمين) ───────────────────────

    def _build_list_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background:#fafafa;")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(12, 12, 8, 12)
        lay.setSpacing(8)

        lbl = QLabel("📂  تصنيفات مجموعات المقاسات")
        lbl.setStyleSheet("font-weight:bold; font-size:13px; color:#1565c0;")
        lay.addWidget(lbl)

        hint = QLabel(
            "💡 كل تصنيف يحمل قالباً من الحقول الافتراضية.\n"
            "عند إنشاء مجموعة مقاسات من تبويب \"المجموعات\"،\n"
            "حقول القالب تُنسخ تلقائياً."
        )
        hint.setStyleSheet(
            "font-size:10px; color:#555; background:#e3f2fd;"
            "border:1px solid #90caf9; border-radius:4px; padding:5px 8px;"
        )
        hint.setWordWrap(True)
        lay.addWidget(hint)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "التصنيف", "الوحدة", "الحقول"])
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Interactive)
        hh.setSectionResizeMode(3, QHeaderView.Interactive)
        self.table.setColumnWidth(2, 65)
        self.table.setColumnWidth(3, 65)
        hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.selectionModel().selectionChanged.connect(self._on_select)
        lay.addWidget(self.table, stretch=1)

        self.lbl_count = QLabel()
        self.lbl_count.setStyleSheet("color:#1565c0; font-size:10px;")
        lay.addWidget(self.lbl_count)

        btn_del = QPushButton("🗑 حذف المحدد")
        btn_del.setMinimumHeight(30)
        btn_del.setStyleSheet(_BTN_DEL)
        btn_del.clicked.connect(self._delete)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(btn_del)
        lay.addLayout(row)

        return panel

    # ── لوحة التفاصيل (يسار) ────────────────────────────────

    def _build_detail_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background:white;")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(8, 12, 12, 12)
        lay.setSpacing(10)

        # ── معلومات التصنيف ──
        grp_info = QGroupBox("📋  بيانات التصنيف")
        grp_info.setStyleSheet("""
            QGroupBox { font-weight:bold; color:#1565c0;
                border:1px solid #90caf9; border-radius:6px;
                margin-top:6px; padding-top:6px; background:#f9f9f9; }
            QGroupBox::title { subcontrol-origin:margin; padding:0 6px; }
        """)
        form = QFormLayout(grp_info)
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight)

        self.inp_name = QLineEdit()
        self.inp_name.setMinimumHeight(30)
        self.inp_name.setPlaceholderText("مثال: خشب، معدن، قماش...")
        form.addRow("الاسم :", self.inp_name)

        # الوحدة الافتراضية
        unit_row = QHBoxLayout()
        self.inp_unit = QLineEdit()
        self.inp_unit.setMinimumHeight(28)
        self.inp_unit.setText("mm")
        self.inp_unit.setMaximumWidth(80)
        for u in _UNITS:
            btn_u = QPushButton(u)
            btn_u.setFixedHeight(26)
            btn_u.setStyleSheet(
                "QPushButton{border:1px solid #c5cae9; border-radius:3px;"
                "background:#e8eaf6; padding:0 6px; font-size:10px;}"
                "QPushButton:hover{background:#c5cae9;}"
            )
            btn_u.clicked.connect(lambda _, u=u: self.inp_unit.setText(u))
            unit_row.addWidget(btn_u)
        unit_row.addStretch()
        form.addRow("الوحدة :", self.inp_unit)
        form.addRow("", unit_row)

        # اللون
        color_row = QHBoxLayout()
        self.lbl_color = QLabel()
        self.lbl_color.setFixedSize(30, 30)
        self._refresh_color_preview()
        btn_color = QPushButton("اختر لون")
        btn_color.setMinimumHeight(28)
        btn_color.clicked.connect(self._pick_color)
        # ألوان سريعة
        for c in _PRESET_COLORS:
            btn_c = QPushButton()
            btn_c.setFixedSize(20, 20)
            btn_c.setStyleSheet(
                f"QPushButton{{background:{c};border-radius:3px;"
                "border:1px solid rgba(0,0,0,0.2);}}"
                f"QPushButton:hover{{border:2px solid #333;}}"
            )
            btn_c.clicked.connect(lambda _, col=c: self._set_color(col))
            color_row.addWidget(btn_c)
        color_row.addStretch()
        form.addRow("اللون :", self.lbl_color)
        form.addRow("", color_row)

        self.lbl_mode = QLabel("— تصنيف جديد —")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0; font-size:11px;")
        form.addRow(self.lbl_mode)

        btn_row = QHBoxLayout()
        self.btn_add    = QPushButton("➕ إضافة")
        self.btn_save   = QPushButton("💾 حفظ")
        self.btn_cancel = QPushButton("✖ إلغاء")
        for b in (self.btn_add, self.btn_save, self.btn_cancel):
            b.setMinimumHeight(30)
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
        lay.addWidget(grp_info)

        # ── حقول القالب ──
        grp_fields = QGroupBox("📐  حقول القالب الافتراضية")
        grp_fields.setStyleSheet("""
            QGroupBox { font-weight:bold; color:#e65100;
                border:1px solid #ffcc80; border-radius:6px;
                margin-top:6px; padding-top:6px; background:#fffde7; }
            QGroupBox::title { subcontrol-origin:margin; padding:0 6px; }
        """)
        fields_lay = QVBoxLayout(grp_fields)
        fields_lay.setSpacing(6)

        hint2 = QLabel(
            "أضف الحقول التي ستظهر تلقائياً في أي مجموعة مقاسات تُنشأ من هذا التصنيف."
        )
        hint2.setStyleSheet(
            "font-size:10px; color:#e65100; background:transparent; border:none;"
        )
        hint2.setWordWrap(True)
        fields_lay.addWidget(hint2)

        # جدول الحقول
        self.tbl_fields = QTableWidget()
        self.tbl_fields.setColumnCount(5)
        self.tbl_fields.setHorizontalHeaderLabels(
            ["المفتاح", "التسمية", "الوحدة", "النوع", "مطلوب"]
        )
        self.tbl_fields.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_fields.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_fields.setAlternatingRowColors(True)
        self.tbl_fields.verticalHeader().setVisible(False)
        self.tbl_fields.setMaximumHeight(180)
        hh2 = self.tbl_fields.horizontalHeader()
        hh2.setSectionResizeMode(1, QHeaderView.Stretch)
        for i in (0, 2, 3, 4):
            hh2.setSectionResizeMode(i, QHeaderView.Interactive)
        self.tbl_fields.setColumnWidth(0, 90)
        self.tbl_fields.setColumnWidth(2, 60)
        self.tbl_fields.setColumnWidth(3, 100)
        self.tbl_fields.setColumnWidth(4, 55)
        hh2.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.tbl_fields.selectionModel().selectionChanged.connect(self._on_field_select)
        fields_lay.addWidget(self.tbl_fields)

        # أزرار ترتيب + حذف
        fld_ctrl_row = QHBoxLayout()
        self.btn_fld_up   = QPushButton("▲")
        self.btn_fld_down = QPushButton("▼")
        self.btn_fld_del  = QPushButton("🗑 حذف الحقل")
        for btn in (self.btn_fld_up, self.btn_fld_down):
            btn.setFixedSize(30, 26)
            btn.setStyleSheet(
                "QPushButton{background:#f5f5f5;border:1px solid #ddd;"
                "border-radius:4px;} QPushButton:hover{background:#e3f2fd;}"
            )
        self.btn_fld_del.setMinimumHeight(26)
        self.btn_fld_del.setStyleSheet(_BTN_DEL)
        self.btn_fld_up.clicked.connect(lambda: self._move_field(-1))
        self.btn_fld_down.clicked.connect(lambda: self._move_field(1))
        self.btn_fld_del.clicked.connect(self._delete_field)
        fld_ctrl_row.addWidget(self.btn_fld_up)
        fld_ctrl_row.addWidget(self.btn_fld_down)
        fld_ctrl_row.addStretch()
        fld_ctrl_row.addWidget(self.btn_fld_del)
        fields_lay.addLayout(fld_ctrl_row)

        # فورم إضافة/تعديل حقل
        fld_form_grp = QGroupBox("إضافة / تعديل حقل")
        fld_form_grp.setStyleSheet("""
            QGroupBox { font-size:11px; color:#e65100;
                border:1px solid #ffe082; border-radius:4px;
                margin-top:4px; padding-top:4px; }
        """)
        fld_form = QFormLayout(fld_form_grp)
        fld_form.setSpacing(6)
        fld_form.setLabelAlignment(Qt.AlignRight)

        fld_inline = QHBoxLayout()
        self.inp_fld_name = QLineEdit()
        self.inp_fld_name.setPlaceholderText("مفتاح: length")
        self.inp_fld_name.setMinimumHeight(26)
        self.inp_fld_name.setMinimumWidth(90)
        self.inp_fld_label = QLineEdit()
        self.inp_fld_label.setPlaceholderText("تسمية: الطول")
        self.inp_fld_label.setMinimumHeight(26)
        self.inp_fld_unit_fld = QLineEdit()
        self.inp_fld_unit_fld.setPlaceholderText("وحدة")
        self.inp_fld_unit_fld.setMaximumWidth(60)
        self.inp_fld_unit_fld.setMinimumHeight(26)
        self.cmb_fld_type = QComboBox()
        self.cmb_fld_type.setMinimumHeight(26)
        for key, lbl in _FIELD_TYPES:
            self.cmb_fld_type.addItem(lbl, key)
        self.chk_fld_req = QCheckBox("مطلوب")
        self.chk_fld_req.setChecked(True)
        fld_inline.addWidget(self.inp_fld_name)
        fld_inline.addWidget(self.inp_fld_label)
        fld_inline.addWidget(self.inp_fld_unit_fld)
        fld_inline.addWidget(self.cmb_fld_type)
        fld_inline.addWidget(self.chk_fld_req)
        fld_form.addRow(fld_inline)

        fld_btn_row = QHBoxLayout()
        self.btn_fld_add_row  = QPushButton("➕ أضف حقل")
        self.btn_fld_save_row = QPushButton("💾 حفظ التعديل")
        self.btn_fld_cancel_row = QPushButton("✖")
        self.btn_fld_add_row.setMinimumHeight(26)
        self.btn_fld_save_row.setMinimumHeight(26)
        self.btn_fld_cancel_row.setMinimumHeight(26)
        self.btn_fld_add_row.setStyleSheet(_BTN_ADD)
        self.btn_fld_save_row.setStyleSheet(_BTN_SAVE)
        self.btn_fld_cancel_row.setStyleSheet(_BTN_CANCEL)
        self.btn_fld_save_row.setVisible(False)
        self.btn_fld_cancel_row.setVisible(False)
        self.btn_fld_add_row.clicked.connect(self._add_field)
        self.btn_fld_save_row.clicked.connect(self._save_field)
        self.btn_fld_cancel_row.clicked.connect(self._reset_field_form)
        fld_btn_row.addWidget(self.btn_fld_add_row)
        fld_btn_row.addWidget(self.btn_fld_save_row)
        fld_btn_row.addWidget(self.btn_fld_cancel_row)
        fld_btn_row.addStretch()
        fld_form.addRow(fld_btn_row)

        fields_lay.addWidget(fld_form_grp)

        # زر حفظ القالب
        self.btn_save_template = QPushButton("💾  حفظ حقول القالب")
        self.btn_save_template.setMinimumHeight(32)
        self.btn_save_template.setStyleSheet(_BTN_SAVE)
        self.btn_save_template.clicked.connect(self._save_template)
        fields_lay.addWidget(self.btn_save_template)

        lay.addWidget(grp_fields, stretch=1)
        return panel

    # ══════════════════════════════════════════════════════
    # تحميل البيانات
    # ══════════════════════════════════════════════════════

    def _load(self):
        cats = fetch_categories_by_scope(self.conn, "design")
        self.table.setRowCount(0)
        for c in cats:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(c["id"])))

            name_item = QTableWidgetItem(c["name"])
            name_item.setForeground(QColor(c["color"]))
            name_item.setFont(QFont("", -1, QFont.Bold))
            self.table.setItem(r, 1, name_item)

            self.table.setItem(r, 2, QTableWidgetItem(c["default_unit"] or "mm"))

            # عدد حقول القالب
            fields = get_template_fields(self.conn, c["id"])
            cnt_item = QTableWidgetItem(str(len(fields)) if fields else "—")
            cnt_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 3, cnt_item)

        self.lbl_count.setText(f"({len(cats)} تصنيف)")

    def _load_fields_table(self):
        """يعرض self._template_fields في الجدول."""
        self.tbl_fields.setRowCount(0)
        for f in self._template_fields:
            r = self.tbl_fields.rowCount()
            self.tbl_fields.insertRow(r)
            self.tbl_fields.setItem(r, 0, QTableWidgetItem(f.get("name", "")))
            label_item = QTableWidgetItem(f.get("label", ""))
            label_item.setFont(QFont("", -1, QFont.Bold))
            self.tbl_fields.setItem(r, 1, label_item)
            self.tbl_fields.setItem(r, 2, QTableWidgetItem(f.get("unit", "")))

            type_label = next(
                (lbl for k, lbl in _FIELD_TYPES if k == f.get("field_type", "number")),
                f.get("field_type", "")
            )
            type_item = QTableWidgetItem(type_label)
            type_item.setForeground(QColor("#1565c0"))
            self.tbl_fields.setItem(r, 3, type_item)

            req_item = QTableWidgetItem("✅" if f.get("required", True) else "—")
            req_item.setTextAlignment(Qt.AlignCenter)
            self.tbl_fields.setItem(r, 4, req_item)

    # ══════════════════════════════════════════════════════
    # Signal handlers
    # ══════════════════════════════════════════════════════

    def _on_select(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        cat_id = int(self.table.item(rows[0].row(), 0).text())
        cat = fetch_category(self.conn, cat_id)
        if not cat:
            return
        self._editing_id = cat_id
        self.inp_name.setText(cat["name"])
        self.inp_unit.setText(cat["default_unit"] or "mm")
        self._color = cat["color"] or "#607d8b"
        self._refresh_color_preview()
        self.lbl_mode.setText(f"تعديل: {cat['name']}")
        self.btn_add.setVisible(False)
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)

        # تحميل الحقول
        self._template_fields = list(get_template_fields(self.conn, cat_id))
        self._editing_fld_idx = None
        self._load_fields_table()
        self._reset_field_form()

    def _on_field_select(self):
        rows = self.tbl_fields.selectionModel().selectedRows()
        if not rows:
            return
        idx = rows[0].row()
        if idx >= len(self._template_fields):
            return
        self._editing_fld_idx = idx
        f = self._template_fields[idx]
        self.inp_fld_name.setText(f.get("name", ""))
        self.inp_fld_label.setText(f.get("label", ""))
        self.inp_fld_unit_fld.setText(f.get("unit", ""))
        self.chk_fld_req.setChecked(bool(f.get("required", True)))
        for i in range(self.cmb_fld_type.count()):
            if self.cmb_fld_type.itemData(i) == f.get("field_type", "number"):
                self.cmb_fld_type.setCurrentIndex(i)
                break
        self.btn_fld_add_row.setVisible(False)
        self.btn_fld_save_row.setVisible(True)
        self.btn_fld_cancel_row.setVisible(True)

    # ══════════════════════════════════════════════════════
    # CRUD التصنيفات
    # ══════════════════════════════════════════════════════

    def _add(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم التصنيف")
            return
        unit = self.inp_unit.text().strip() or "mm"
        new_id = insert_category(
            self.conn, name, scope="design",
            color=self._color, default_unit=unit
        )
        self._editing_id = new_id
        self._template_fields = []
        self._load_fields_table()
        self._reset()
        self._load()
        bus.data_changed.emit()

    def _save(self):
        if not self._editing_id:
            return
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم التصنيف")
            return
        unit = self.inp_unit.text().strip() or "mm"
        update_category(
            self.conn, self._editing_id, name,
            scope="design", color=self._color, default_unit=unit
        )
        self._reset()
        self._load()
        bus.data_changed.emit()

    def _delete(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "تنبيه", "اختر تصنيفاً أولاً")
            return
        cat_id = int(self.table.item(rows[0].row(), 0).text())
        name   = self.table.item(rows[0].row(), 1).text()
        if QMessageBox.question(
            self, "تأكيد", f"حذف تصنيف «{name}»؟",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            delete_category(self.conn, cat_id)
            self._reset()
            self._template_fields = []
            self._load_fields_table()
            self._load()
            bus.data_changed.emit()

    def _reset(self):
        self._editing_id = None
        self.inp_name.clear()
        self.inp_unit.setText("mm")
        self._color = "#607d8b"
        self._refresh_color_preview()
        self.lbl_mode.setText("— تصنيف جديد —")
        self.btn_add.setVisible(True)
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        self.table.clearSelection()

    # ══════════════════════════════════════════════════════
    # CRUD حقول القالب (في الذاكرة — تُحفظ بزر "حفظ القالب")
    # ══════════════════════════════════════════════════════

    def _add_field(self):
        name  = self.inp_fld_name.text().strip()
        label = self.inp_fld_label.text().strip()
        if not name or not label:
            QMessageBox.warning(self, "تنبيه", "أدخل المفتاح والتسمية")
            return
        # تحقق من التكرار
        if any(f["name"] == name for f in self._template_fields):
            QMessageBox.warning(self, "تنبيه", f"المفتاح «{name}» موجود بالفعل")
            return
        self._template_fields.append({
            "name":       name,
            "label":      label,
            "unit":       self.inp_fld_unit_fld.text().strip(),
            "field_type": self.cmb_fld_type.currentData(),
            "required":   self.chk_fld_req.isChecked(),
            "sort_order": len(self._template_fields),
        })
        self._load_fields_table()
        self._reset_field_form()

    def _save_field(self):
        if self._editing_fld_idx is None:
            return
        name  = self.inp_fld_name.text().strip()
        label = self.inp_fld_label.text().strip()
        if not name or not label:
            QMessageBox.warning(self, "تنبيه", "أدخل المفتاح والتسمية")
            return
        idx = self._editing_fld_idx
        self._template_fields[idx] = {
            "name":       name,
            "label":      label,
            "unit":       self.inp_fld_unit_fld.text().strip(),
            "field_type": self.cmb_fld_type.currentData(),
            "required":   self.chk_fld_req.isChecked(),
            "sort_order": idx,
        }
        self._load_fields_table()
        self._reset_field_form()

    def _delete_field(self):
        rows = self.tbl_fields.selectionModel().selectedRows()
        if not rows:
            return
        idx = rows[0].row()
        if idx < len(self._template_fields):
            del self._template_fields[idx]
            # إعادة ترقيم sort_order
            for i, f in enumerate(self._template_fields):
                f["sort_order"] = i
            self._load_fields_table()
            self._reset_field_form()

    def _reset_field_form(self):
        self._editing_fld_idx = None
        self.inp_fld_name.clear()
        self.inp_fld_label.clear()
        self.inp_fld_unit_fld.clear()
        self.cmb_fld_type.setCurrentIndex(0)
        self.chk_fld_req.setChecked(True)
        self.btn_fld_add_row.setVisible(True)
        self.btn_fld_save_row.setVisible(False)
        self.btn_fld_cancel_row.setVisible(False)

    def _move_field(self, direction: int):
        rows = self.tbl_fields.selectionModel().selectedRows()
        if not rows:
            return
        idx = rows[0].row()
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(self._template_fields):
            return
        self._template_fields[idx], self._template_fields[new_idx] = (
            self._template_fields[new_idx], self._template_fields[idx]
        )
        for i, f in enumerate(self._template_fields):
            f["sort_order"] = i
        self._load_fields_table()
        self.tbl_fields.selectRow(new_idx)

    def _save_template(self):
        """يحفظ حقول القالب في DB."""
        if not self._editing_id:
            QMessageBox.information(
                self, "تنبيه",
                "اختر تصنيفاً أولاً أو أضف تصنيفاً جديداً"
            )
            return
        set_template_fields(self.conn, self._editing_id, self._template_fields)
        self._load()
        bus.data_changed.emit()
        # تأكيد بصري بسيط
        self.btn_save_template.setText("✅  تم الحفظ!")
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(
            1500,
            lambda: self.btn_save_template.setText("💾  حفظ حقول القالب")
        )

    # ══════════════════════════════════════════════════════
    # اللون
    # ══════════════════════════════════════════════════════

    def _pick_color(self):
        col = QColorDialog.getColor(QColor(self._color), self, "اختر اللون")
        if col.isValid():
            self._set_color(col.name())

    def _set_color(self, color: str):
        self._color = color
        self._refresh_color_preview()

    def _refresh_color_preview(self):
        self.lbl_color.setStyleSheet(
            f"background:{self._color}; border-radius:4px; border:1px solid #ccc;"
        )