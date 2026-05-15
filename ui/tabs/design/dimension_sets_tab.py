"""
ui/tabs/design/dimension_sets_tab.py
=====================================
تبويب إدارة مجموعات المقاسات وحقولها.

التغييرات الجديدة:
  - إضافة Combo تصنيف (scope='design' من erp.db) في فورم المجموعة
  - لما تختار تصنيف عند إنشاء مجموعة جديدة:
      → الوحدة الافتراضية تتعبى تلقائياً
      → الحقول القالبية تتنسخ تلقائياً بعد الحفظ (بدون سؤال)
  - التصنيف بيتحفظ في عمود category_id في dimension_sets (designs.db)
    وفي نفس الوقت الـ erp.db بيحتفظ بالقالب

الربط بين DB-ين:
  self.conn       → designs.db (الأشكال والمجموعات)
  self.conn_erp   → erp.db     (التصنيفات والقوالب)
"""

import json

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QGroupBox, QFormLayout,
    QMessageBox, QCheckBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor, QFont

from db.design.design_repo import (
    fetch_all_dimension_sets, fetch_dimension_set,
    insert_dimension_set, update_dimension_set, delete_dimension_set,
    fetch_fields_for_set, fetch_field,
    insert_dimension_field, update_dimension_field,
    delete_dimension_field, reorder_fields,
)
from db.shared.categories_repo import (
    fetch_categories_by_scope, get_template_fields,
    apply_template_to_dimension_set,
)
from db.shared.connection import get_connection
from ui.events import bus


_FIELD_TYPES = [
    ("number",  "🔢 رقم"),
    ("text",    "📝 نص"),
    ("boolean", "✅ نعم/لا"),
    ("select",  "📋 قائمة اختيار"),
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


class DimensionSetsTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn             = conn          # designs.db
        self.conn_erp         = get_connection("costing")   # erp.db للتصنيفات
        self._editing_set_id  = None
        self._editing_fld_id  = None
        self._selected_set_id = None
        self._build()
        self._load_category_combo()
        self._load_sets()
        bus.data_changed.connect(self._reload)

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(4)
        splitter.setStyleSheet("""
            QSplitter::handle { background:#e0e0e0; }
            QSplitter::handle:hover { background:#90caf9; }
        """)
        splitter.addWidget(self._build_sets_panel())
        splitter.addWidget(self._build_fields_panel())
        splitter.setSizes([400, 580])
        root.addWidget(splitter)

    # ── لوحة مجموعات المقاسات (يمين) ──────────────────────

    def _build_sets_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background:#fafafa;")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(12, 12, 8, 12)
        lay.setSpacing(8)

        lbl = QLabel("📏  مجموعات المقاسات")
        lbl.setStyleSheet("font-weight:bold; font-size:13px; color:#1565c0;")
        lay.addWidget(lbl)

        # جدول المجموعات
        self.tbl_sets = QTableWidget()
        self.tbl_sets.setColumnCount(4)
        self.tbl_sets.setHorizontalHeaderLabels(["ID", "الاسم", "الوحدة", "التصنيف"])
        self.tbl_sets.setColumnHidden(0, True)
        self.tbl_sets.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_sets.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_sets.setAlternatingRowColors(True)
        self.tbl_sets.verticalHeader().setVisible(False)
        hh = self.tbl_sets.horizontalHeader()
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Interactive)
        hh.setSectionResizeMode(3, QHeaderView.Interactive)
        self.tbl_sets.setColumnWidth(2, 65)
        self.tbl_sets.setColumnWidth(3, 120)
        hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.tbl_sets.selectionModel().selectionChanged.connect(self._on_set_selected)
        lay.addWidget(self.tbl_sets, stretch=1)

        self.lbl_sets_count = QLabel()
        self.lbl_sets_count.setStyleSheet("color:#1565c0; font-size:10px;")
        lay.addWidget(self.lbl_sets_count)

        # ── فورم إضافة/تعديل المجموعة ──
        grp = QGroupBox("بيانات المجموعة")
        grp.setStyleSheet("""
            QGroupBox { font-weight:bold; color:#1565c0;
                border:1px solid #90caf9; border-radius:6px;
                margin-top:6px; padding-top:6px; background:white; }
            QGroupBox::title { subcontrol-origin:margin; padding:0 6px; }
        """)
        form = QFormLayout(grp)
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight)

        self.inp_set_name = QLineEdit()
        self.inp_set_name.setMinimumHeight(30)
        self.inp_set_name.setPlaceholderText("مثال: مقاسات خشب، مقاسات معدن...")
        form.addRow("الاسم :", self.inp_set_name)

        # ── التصنيف (scope=design من erp.db) ──
        self.cmb_set_cat = QComboBox()
        self.cmb_set_cat.setMinimumHeight(30)
        self.cmb_set_cat.setStyleSheet("""
            QComboBox { background:white; border:1px solid #90caf9;
                border-radius:4px; padding:2px 8px; }
            QComboBox:focus { border-color:#1565c0; }
            QComboBox::drop-down { border:none; }
        """)
        self.cmb_set_cat.currentIndexChanged.connect(self._on_cat_selected)
        form.addRow("التصنيف :", self.cmb_set_cat)

        # تلميح الحقول الافتراضية
        self.lbl_template_hint = QLabel()
        self.lbl_template_hint.setStyleSheet(
            "font-size:10px; color:#1565c0; background:#e3f2fd;"
            "border:1px solid #90caf9; border-radius:4px; padding:3px 6px;"
        )
        self.lbl_template_hint.setWordWrap(True)
        self.lbl_template_hint.setVisible(False)
        form.addRow(self.lbl_template_hint)

        self.inp_set_unit = QLineEdit()
        self.inp_set_unit.setMinimumHeight(28)
        self.inp_set_unit.setPlaceholderText("mm / cm / m / inch")
        self.inp_set_unit.setText("mm")
        form.addRow("الوحدة :", self.inp_set_unit)

        self.inp_set_desc = QLineEdit()
        self.inp_set_desc.setMinimumHeight(28)
        self.inp_set_desc.setPlaceholderText("وصف اختياري...")
        form.addRow("الوصف :", self.inp_set_desc)

        self.lbl_set_mode = QLabel("إضافة مجموعة")
        self.lbl_set_mode.setStyleSheet("color:#1565c0; font-size:10px;")
        form.addRow(self.lbl_set_mode)

        btn_row = QHBoxLayout()
        self.btn_set_add    = QPushButton("➕ إضافة")
        self.btn_set_save   = QPushButton("💾 حفظ")
        self.btn_set_cancel = QPushButton("✖")
        self.btn_set_del    = QPushButton("🗑 حذف")
        for btn in (self.btn_set_add, self.btn_set_save,
                    self.btn_set_cancel, self.btn_set_del):
            btn.setMinimumHeight(28)

        self.btn_set_add.setStyleSheet(_BTN_ADD)
        self.btn_set_save.setStyleSheet(_BTN_SAVE)
        self.btn_set_cancel.setStyleSheet(_BTN_CANCEL)
        self.btn_set_del.setStyleSheet(_BTN_DEL)

        self.btn_set_save.setVisible(False)
        self.btn_set_cancel.setVisible(False)

        self.btn_set_add.clicked.connect(self._add_set)
        self.btn_set_save.clicked.connect(self._save_set)
        self.btn_set_cancel.clicked.connect(self._reset_set_form)
        self.btn_set_del.clicked.connect(self._delete_set)

        btn_row.addWidget(self.btn_set_add)
        btn_row.addWidget(self.btn_set_save)
        btn_row.addWidget(self.btn_set_cancel)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_set_del)
        form.addRow(btn_row)

        lay.addWidget(grp)
        return panel

    # ── لوحة الحقول (يسار) ─────────────────────────────────

    def _build_fields_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background:white;")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(8, 12, 12, 12)
        lay.setSpacing(8)

        self.lbl_fields_title = QLabel("📐  حقول المجموعة")
        self.lbl_fields_title.setStyleSheet(
            "font-weight:bold; font-size:13px; color:#e65100;"
        )
        lay.addWidget(self.lbl_fields_title)

        hint = QLabel("💡 اختر مجموعة من اليمين لعرض حقولها وإدارتها")
        hint.setStyleSheet(
            "font-size:10px; color:#888; background:#fff8e1;"
            "border:1px solid #ffe082; border-radius:4px; padding:4px 8px;"
        )
        hint.setWordWrap(True)
        lay.addWidget(hint)

        # جدول الحقول
        self.tbl_fields = QTableWidget()
        self.tbl_fields.setColumnCount(6)
        self.tbl_fields.setHorizontalHeaderLabels(
            ["ID", "المفتاح", "التسمية", "الوحدة", "النوع", "مطلوب"]
        )
        self.tbl_fields.setColumnHidden(0, True)
        self.tbl_fields.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_fields.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_fields.setAlternatingRowColors(True)
        self.tbl_fields.verticalHeader().setVisible(False)
        hh2 = self.tbl_fields.horizontalHeader()
        hh2.setSectionResizeMode(2, QHeaderView.Stretch)
        for i in (1, 3, 4, 5):
            hh2.setSectionResizeMode(i, QHeaderView.Interactive)
        self.tbl_fields.setColumnWidth(1, 100)
        self.tbl_fields.setColumnWidth(3, 65)
        self.tbl_fields.setColumnWidth(4, 120)
        self.tbl_fields.setColumnWidth(5, 60)
        hh2.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.tbl_fields.selectionModel().selectionChanged.connect(self._on_field_selected)
        lay.addWidget(self.tbl_fields, stretch=1)

        # أزرار الترتيب
        order_row = QHBoxLayout()
        self.btn_fld_up   = QPushButton("▲ أعلى")
        self.btn_fld_down = QPushButton("▼ أسفل")
        for btn in (self.btn_fld_up, self.btn_fld_down):
            btn.setMinimumHeight(26)
            btn.setStyleSheet(
                "QPushButton{background:#f5f5f5;border:1px solid #ddd;"
                "border-radius:4px;padding:0 10px;}"
                "QPushButton:hover{background:#e3f2fd;}"
            )
        self.btn_fld_up.clicked.connect(lambda: self._move_field(-1))
        self.btn_fld_down.clicked.connect(lambda: self._move_field(1))
        order_row.addWidget(self.btn_fld_up)
        order_row.addWidget(self.btn_fld_down)
        order_row.addStretch()
        self.lbl_fields_count = QLabel()
        self.lbl_fields_count.setStyleSheet("color:#e65100; font-size:10px;")
        order_row.addWidget(self.lbl_fields_count)
        lay.addLayout(order_row)

        # فورم الحقل
        grp2 = QGroupBox("بيانات الحقل")
        grp2.setStyleSheet("""
            QGroupBox { font-weight:bold; color:#e65100;
                border:1px solid #ffcc80; border-radius:6px;
                margin-top:6px; padding-top:6px; background:#fffde7; }
            QGroupBox::title { subcontrol-origin:margin; padding:0 6px; }
        """)
        form2 = QFormLayout(grp2)
        form2.setSpacing(8)
        form2.setLabelAlignment(Qt.AlignRight)

        self.inp_fld_name = QLineEdit()
        self.inp_fld_name.setMinimumHeight(28)
        self.inp_fld_name.setPlaceholderText("مفتاح إنجليزي: length, width...")
        form2.addRow("المفتاح :", self.inp_fld_name)

        self.inp_fld_label = QLineEdit()
        self.inp_fld_label.setMinimumHeight(28)
        self.inp_fld_label.setPlaceholderText("التسمية المعروضة: الطول، العرض...")
        form2.addRow("التسمية :", self.inp_fld_label)

        self.inp_fld_unit = QLineEdit()
        self.inp_fld_unit.setMinimumHeight(28)
        self.inp_fld_unit.setPlaceholderText("mm / kg / ...")
        form2.addRow("الوحدة :", self.inp_fld_unit)

        self.cmb_fld_type = QComboBox()
        self.cmb_fld_type.setMinimumHeight(28)
        for key, label in _FIELD_TYPES:
            self.cmb_fld_type.addItem(label, key)
        self.cmb_fld_type.currentIndexChanged.connect(self._on_fld_type_changed)
        form2.addRow("النوع :", self.cmb_fld_type)

        self.inp_fld_options = QLineEdit()
        self.inp_fld_options.setMinimumHeight(28)
        self.inp_fld_options.setPlaceholderText('مفصولة بفاصلة: خيار1, خيار2')
        self.inp_fld_options.setVisible(False)
        self.lbl_fld_options = QLabel("الخيارات :")
        self.lbl_fld_options.setVisible(False)
        form2.addRow(self.lbl_fld_options, self.inp_fld_options)

        self.chk_fld_required = QCheckBox("مطلوب (Required)")
        self.chk_fld_required.setChecked(True)
        form2.addRow("", self.chk_fld_required)

        self.lbl_fld_mode = QLabel("إضافة حقل")
        self.lbl_fld_mode.setStyleSheet("color:#e65100; font-size:10px;")
        form2.addRow(self.lbl_fld_mode)

        btn_row2 = QHBoxLayout()
        self.btn_fld_add    = QPushButton("➕ إضافة حقل")
        self.btn_fld_save   = QPushButton("💾 حفظ")
        self.btn_fld_cancel = QPushButton("✖")
        self.btn_fld_del    = QPushButton("🗑 حذف")
        for btn in (self.btn_fld_add, self.btn_fld_save,
                    self.btn_fld_cancel, self.btn_fld_del):
            btn.setMinimumHeight(28)

        self.btn_fld_add.setStyleSheet(_BTN_ADD)
        self.btn_fld_save.setStyleSheet(_BTN_SAVE)
        self.btn_fld_cancel.setStyleSheet(_BTN_CANCEL)
        self.btn_fld_del.setStyleSheet(_BTN_DEL)

        self.btn_fld_save.setVisible(False)
        self.btn_fld_cancel.setVisible(False)

        self.btn_fld_add.clicked.connect(self._add_field)
        self.btn_fld_save.clicked.connect(self._save_field)
        self.btn_fld_cancel.clicked.connect(self._reset_field_form)
        self.btn_fld_del.clicked.connect(self._delete_field)

        btn_row2.addWidget(self.btn_fld_add)
        btn_row2.addWidget(self.btn_fld_save)
        btn_row2.addWidget(self.btn_fld_cancel)
        btn_row2.addStretch()
        btn_row2.addWidget(self.btn_fld_del)
        form2.addRow(btn_row2)

        lay.addWidget(grp2)
        return panel

    # ══════════════════════════════════════════════════════
    # تحميل التصنيفات في الـ Combo
    # ══════════════════════════════════════════════════════

    def _load_category_combo(self):
        """يحمّل تصنيفات scope='design' من erp.db."""
        prev = self.cmb_set_cat.currentData()
        self.cmb_set_cat.blockSignals(True)
        self.cmb_set_cat.clear()
        self.cmb_set_cat.addItem("— بدون تصنيف —", None)

        try:
            cats = fetch_categories_by_scope(self.conn_erp, "design")
            for c in cats:
                # عدد الحقول القالبية
                fields = get_template_fields(self.conn_erp, c["id"])
                suffix = f"  ({len(fields)} حقل)" if fields else ""
                self.cmb_set_cat.addItem(f"{c['name']}{suffix}", c["id"])
                idx = self.cmb_set_cat.count() - 1
                self.cmb_set_cat.setItemData(idx, QColor(c["color"]), Qt.ForegroundRole)
        except Exception as e:
            print(f"[DimensionSetsTab] load categories: {e}")

        # استعادة الاختيار السابق
        for i in range(self.cmb_set_cat.count()):
            if self.cmb_set_cat.itemData(i) == prev:
                self.cmb_set_cat.setCurrentIndex(i)
                break

        self.cmb_set_cat.blockSignals(False)

    def _on_cat_selected(self):
        """لما يتغير التصنيف — يملي الوحدة الافتراضية ويعرض معاينة الحقول."""
        cat_id = self.cmb_set_cat.currentData()
        if cat_id is None:
            self.lbl_template_hint.setVisible(False)
            return

        try:
            cat    = self.conn_erp.execute(
                "SELECT default_unit, template_fields FROM categories WHERE id=?",
                (cat_id,)
            ).fetchone()
            if not cat:
                self.lbl_template_hint.setVisible(False)
                return

            # تعبئة الوحدة
            unit = cat["default_unit"] or "mm"
            self.inp_set_unit.setText(unit)

            # معاينة الحقول
            fields = []
            if cat["template_fields"]:
                try:
                    fields = json.loads(cat["template_fields"])
                except Exception:
                    fields = []

            if fields:
                names = "، ".join(f["label"] for f in fields[:6])
                if len(fields) > 6:
                    names += f"... (+{len(fields)-6})"
                self.lbl_template_hint.setText(
                    f"✅ سيتم نسخ {len(fields)} حقل تلقائياً:\n{names}"
                )
                self.lbl_template_hint.setVisible(True)
            else:
                self.lbl_template_hint.setText("ℹ️ هذا التصنيف لا يحتوي على حقول افتراضية")
                self.lbl_template_hint.setVisible(True)
        except Exception as e:
            print(f"[DimensionSetsTab] _on_cat_selected: {e}")
            self.lbl_template_hint.setVisible(False)

    # ══════════════════════════════════════════════════════
    # تحميل البيانات
    # ══════════════════════════════════════════════════════

    def _load_sets(self):
        sets = fetch_all_dimension_sets(self.conn)
        self.tbl_sets.setRowCount(0)

        # نبني map للتصنيفات من erp.db
        cat_map = {}
        try:
            cats = fetch_categories_by_scope(self.conn_erp, "design")
            cat_map = {c["id"]: c for c in cats}
        except Exception:
            pass

        for s in sets:
            r = self.tbl_sets.rowCount()
            self.tbl_sets.insertRow(r)
            self.tbl_sets.setItem(r, 0, QTableWidgetItem(str(s["id"])))

            name_item = QTableWidgetItem(s["name"])
            name_item.setFont(QFont("", -1, QFont.Bold))
            self.tbl_sets.setItem(r, 1, name_item)
            self.tbl_sets.setItem(r, 2, QTableWidgetItem(s["unit"] or ""))

            # التصنيف
            cat_id   = s["category_id"] if "category_id" in s.keys() else None
            cat_name = ""
            if cat_id and cat_id in cat_map:
                cat      = cat_map[cat_id]
                cat_name = cat["name"]
                cat_item = QTableWidgetItem(cat_name)
                cat_item.setForeground(QColor(cat["color"]))
                self.tbl_sets.setItem(r, 3, cat_item)
            else:
                self.tbl_sets.setItem(r, 3, QTableWidgetItem("—"))

        self.lbl_sets_count.setText(f"({len(sets)} مجموعة)")

        # إعادة تحديد المجموعة السابقة
        if self._selected_set_id is not None:
            for r in range(self.tbl_sets.rowCount()):
                if int(self.tbl_sets.item(r, 0).text()) == self._selected_set_id:
                    self.tbl_sets.selectRow(r)
                    break

    def _load_fields(self, set_id: int):
        self._selected_set_id = set_id
        s = fetch_dimension_set(self.conn, set_id)
        if s:
            self.lbl_fields_title.setText(
                f"📐  حقول:  {s['name']}  ({s['unit']})"
            )

        fields = fetch_fields_for_set(self.conn, set_id)
        self.tbl_fields.setRowCount(0)
        for f in fields:
            r = self.tbl_fields.rowCount()
            self.tbl_fields.insertRow(r)
            self.tbl_fields.setItem(r, 0, QTableWidgetItem(str(f["id"])))
            self.tbl_fields.setItem(r, 1, QTableWidgetItem(f["name"] or ""))
            label_item = QTableWidgetItem(f["label"] or "")
            label_item.setFont(QFont("", -1, QFont.Bold))
            self.tbl_fields.setItem(r, 2, label_item)
            self.tbl_fields.setItem(r, 3, QTableWidgetItem(f["unit"] or ""))

            type_label = next(
                (lbl for k, lbl in _FIELD_TYPES if k == f["field_type"]),
                f["field_type"]
            )
            type_item = QTableWidgetItem(type_label)
            type_item.setForeground(QColor("#1565c0"))
            self.tbl_fields.setItem(r, 4, type_item)

            req_item = QTableWidgetItem("✅" if f["required"] else "—")
            req_item.setTextAlignment(Qt.AlignCenter)
            self.tbl_fields.setItem(r, 5, req_item)

        self.lbl_fields_count.setText(f"({len(fields)} حقل)")
        self._reset_field_form()

    def _reload(self):
        self._load_category_combo()
        self._load_sets()
        if self._selected_set_id:
            self._load_fields(self._selected_set_id)

    # ══════════════════════════════════════════════════════
    # Signal handlers
    # ══════════════════════════════════════════════════════

    def _on_set_selected(self):
        rows = self.tbl_sets.selectionModel().selectedRows()
        if not rows:
            return
        set_id = int(self.tbl_sets.item(rows[0].row(), 0).text())
        self._load_set_to_form(set_id)
        self._load_fields(set_id)

    def _on_field_selected(self):
        rows = self.tbl_fields.selectionModel().selectedRows()
        if not rows:
            return
        fld_id = int(self.tbl_fields.item(rows[0].row(), 0).text())
        self._load_field_to_form(fld_id)

    def _on_fld_type_changed(self):
        is_select = self.cmb_fld_type.currentData() == "select"
        self.inp_fld_options.setVisible(is_select)
        self.lbl_fld_options.setVisible(is_select)

    # ══════════════════════════════════════════════════════
    # فورم المجموعة — CRUD
    # ══════════════════════════════════════════════════════

    def _load_set_to_form(self, set_id: int):
        s = fetch_dimension_set(self.conn, set_id)
        if not s:
            return
        self._editing_set_id = set_id
        self.inp_set_name.setText(s["name"])
        self.inp_set_unit.setText(s["unit"] or "mm")
        self.inp_set_desc.setText(s["description"] or "")

        # اختيار التصنيف
        cat_id = s["category_id"] if "category_id" in s.keys() else None
        self.cmb_set_cat.blockSignals(True)
        for i in range(self.cmb_set_cat.count()):
            if self.cmb_set_cat.itemData(i) == cat_id:
                self.cmb_set_cat.setCurrentIndex(i)
                break
        self.cmb_set_cat.blockSignals(False)
        self.lbl_template_hint.setVisible(False)  # عند التعديل مش بنعرض الهنت

        self.lbl_set_mode.setText(f"تعديل: {s['name']}")
        self.btn_set_add.setVisible(False)
        self.btn_set_save.setVisible(True)
        self.btn_set_cancel.setVisible(True)

    def _add_set(self):
        name = self.inp_set_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم المجموعة")
            return
        unit   = self.inp_set_unit.text().strip() or "mm"
        desc   = self.inp_set_desc.text().strip()
        cat_id = self.cmb_set_cat.currentData()

        # إنشاء المجموعة
        new_id = insert_dimension_set(self.conn, name, desc, unit,
                                       category_id=cat_id)
        self._selected_set_id = new_id

        # ═══ نسخ الحقول من القالب تلقائياً ═══
        if cat_id is not None:
            copied = apply_template_to_dimension_set(
                self.conn_erp, self.conn, cat_id, new_id
            )
            if copied:
                # تحديث الـ UI مباشرة بدون رسالة
                pass

        self._reset_set_form()
        bus.data_changed.emit()

    def _save_set(self):
        if not self._editing_set_id:
            return
        name = self.inp_set_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم المجموعة")
            return
        unit   = self.inp_set_unit.text().strip() or "mm"
        desc   = self.inp_set_desc.text().strip()
        cat_id = self.cmb_set_cat.currentData()
        update_dimension_set(self.conn, self._editing_set_id,
                              name, desc, unit, category_id=cat_id)
        self._reset_set_form()
        bus.data_changed.emit()

    def _delete_set(self):
        rows = self.tbl_sets.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "تنبيه", "اختر مجموعة أولاً")
            return
        set_id = int(self.tbl_sets.item(rows[0].row(), 0).text())
        s = fetch_dimension_set(self.conn, set_id)
        if not s:
            return
        shapes_count = self.conn.execute(
            "SELECT COUNT(*) as c FROM shapes WHERE dim_set_id=?", (set_id,)
        ).fetchone()["c"]
        msg = f"حذف مجموعة «{s['name']}»؟\nسيتم حذف كل حقولها."
        if shapes_count:
            msg += f"\n⚠️ {shapes_count} شكل مرتبط — سيفقد المجموعة."
        if QMessageBox.question(
            self, "تأكيد", msg, QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            delete_dimension_set(self.conn, set_id)
            self._selected_set_id = None
            self.tbl_fields.setRowCount(0)
            self.lbl_fields_title.setText("📐  حقول المجموعة")
            self._reset_set_form()
            bus.data_changed.emit()

    def _reset_set_form(self):
        self._editing_set_id = None
        self.inp_set_name.clear()
        self.inp_set_unit.setText("mm")
        self.inp_set_desc.clear()
        self.cmb_set_cat.blockSignals(True)
        self.cmb_set_cat.setCurrentIndex(0)
        self.cmb_set_cat.blockSignals(False)
        self.lbl_template_hint.setVisible(False)
        self.lbl_set_mode.setText("إضافة مجموعة")
        self.btn_set_add.setVisible(True)
        self.btn_set_save.setVisible(False)
        self.btn_set_cancel.setVisible(False)

    # ══════════════════════════════════════════════════════
    # فورم الحقل — CRUD
    # ══════════════════════════════════════════════════════

    def _load_field_to_form(self, fld_id: int):
        f = fetch_field(self.conn, fld_id)
        if not f:
            return
        self._editing_fld_id = fld_id
        self.inp_fld_name.setText(f["name"] or "")
        self.inp_fld_label.setText(f["label"] or "")
        self.inp_fld_unit.setText(f["unit"] or "")
        self.chk_fld_required.setChecked(bool(f["required"]))

        for i in range(self.cmb_fld_type.count()):
            if self.cmb_fld_type.itemData(i) == f["field_type"]:
                self.cmb_fld_type.setCurrentIndex(i)
                break

        if f["field_type"] == "select" and f["options"]:
            try:
                opts = json.loads(f["options"])
                self.inp_fld_options.setText(", ".join(str(o) for o in opts))
            except Exception:
                self.inp_fld_options.setText("")
        else:
            self.inp_fld_options.clear()

        self.lbl_fld_mode.setText(f"تعديل: {f['label']}")
        self.btn_fld_add.setVisible(False)
        self.btn_fld_save.setVisible(True)
        self.btn_fld_cancel.setVisible(True)

    def _add_field(self):
        if not self._selected_set_id:
            QMessageBox.information(self, "تنبيه", "اختر مجموعة مقاسات أولاً")
            return
        name  = self.inp_fld_name.text().strip()
        label = self.inp_fld_label.text().strip()
        if not name or not label:
            QMessageBox.warning(self, "تنبيه", "أدخل المفتاح والتسمية")
            return
        unit     = self.inp_fld_unit.text().strip()
        ftype    = self.cmb_fld_type.currentData()
        required = self.chk_fld_required.isChecked()
        options  = self._parse_options()
        sort_order = self.tbl_fields.rowCount()
        insert_dimension_field(
            self.conn, self._selected_set_id,
            name, label, unit, ftype, options, required, sort_order
        )
        self._reset_field_form()
        self._load_fields(self._selected_set_id)
        bus.data_changed.emit()

    def _save_field(self):
        if not self._editing_fld_id:
            return
        name  = self.inp_fld_name.text().strip()
        label = self.inp_fld_label.text().strip()
        if not name or not label:
            QMessageBox.warning(self, "تنبيه", "أدخل المفتاح والتسمية")
            return
        unit     = self.inp_fld_unit.text().strip()
        ftype    = self.cmb_fld_type.currentData()
        required = self.chk_fld_required.isChecked()
        options  = self._parse_options()
        f = fetch_field(self.conn, self._editing_fld_id)
        update_dimension_field(
            self.conn, self._editing_fld_id,
            name, label, unit, ftype, options, required,
            f["sort_order"] if f else 0
        )
        self._reset_field_form()
        self._load_fields(self._selected_set_id)
        bus.data_changed.emit()

    def _delete_field(self):
        rows = self.tbl_fields.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "تنبيه", "اختر حقلاً أولاً")
            return
        fld_id = int(self.tbl_fields.item(rows[0].row(), 0).text())
        f = fetch_field(self.conn, fld_id)
        if not f:
            return
        if QMessageBox.question(
            self, "تأكيد",
            f"حذف الحقل «{f['label']}»؟\nكل قيمه في الأشكال ستُحذف.",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            delete_dimension_field(self.conn, fld_id)
            self._reset_field_form()
            self._load_fields(self._selected_set_id)
            bus.data_changed.emit()

    def _reset_field_form(self):
        self._editing_fld_id = None
        self.inp_fld_name.clear()
        self.inp_fld_label.clear()
        self.inp_fld_unit.clear()
        self.cmb_fld_type.setCurrentIndex(0)
        self.inp_fld_options.clear()
        self.inp_fld_options.setVisible(False)
        self.lbl_fld_options.setVisible(False)
        self.chk_fld_required.setChecked(True)
        self.lbl_fld_mode.setText("إضافة حقل")
        self.btn_fld_add.setVisible(True)
        self.btn_fld_save.setVisible(False)
        self.btn_fld_cancel.setVisible(False)

    def _parse_options(self) -> list | None:
        if self.cmb_fld_type.currentData() != "select":
            return None
        text = self.inp_fld_options.text().strip()
        if not text:
            return None
        return [o.strip() for o in text.split(",") if o.strip()]

    def _move_field(self, direction: int):
        rows = self.tbl_fields.selectionModel().selectedRows()
        if not rows or not self._selected_set_id:
            return
        current_row = rows[0].row()
        new_row = current_row + direction
        if new_row < 0 or new_row >= self.tbl_fields.rowCount():
            return
        ids = [
            int(self.tbl_fields.item(r, 0).text())
            for r in range(self.tbl_fields.rowCount())
        ]
        ids[current_row], ids[new_row] = ids[new_row], ids[current_row]
        reorder_fields(self.conn, self._selected_set_id, ids)
        self._load_fields(self._selected_set_id)
        self.tbl_fields.selectRow(new_row)