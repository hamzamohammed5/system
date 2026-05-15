"""
ui/tabs/design/dim_categories_tab.py
======================================
تبويب إدارة تصنيفات مجموعات المقاسات.

يعمل على designs.db مباشرة (جدول dim_set_categories + dim_set_category_fields).

لكل تصنيف:
  - اسم + لون + أيقونة + وحدة افتراضية
  - قائمة حقول افتراضية (القالب): مفتاح، تسمية، وحدة، نوع، مطلوب
    → تُنسخ تلقائياً لأي مجموعة مقاسات جديدة تختار هذا التصنيف

الـ widgets المستخدمة من shared:
  - WrapDelegate من ui/helpers.py  (للجداول)
  - wrap_in_scroll من ui/widgets/shared/scrollable_form.py
"""

import json

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QGroupBox, QFormLayout,
    QMessageBox, QCheckBox, QColorDialog, QFrame,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui  import QColor, QFont

from db.design.design_repo import (
    fetch_all_dim_set_categories,
    fetch_dim_set_category,
    insert_dim_set_category,
    update_dim_set_category,
    delete_dim_set_category,
    fetch_category_template_fields,
    insert_category_template_field,
    update_category_template_field,
    delete_category_template_field,
    reorder_category_template_fields,
    apply_category_template_to_set,
)
from ui.helpers import make_table, WrapDelegate
from ui.widgets.shared.scrollable_form import wrap_in_scroll
from ui.events import bus


# ══════════════════════════════════════════════════════════
# ثوابت
# ══════════════════════════════════════════════════════════

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

_ICONS = ["📏", "🪵", "⚙️", "🧵", "🪟", "🔩", "🧱", "🪨", "🛠️", "🎨"]

_S_ADD = ("QPushButton{background:#e8f5e9;color:#2e7d32;"
          "border:1px solid #a5d6a7;border-radius:5px;"
          "padding:0 14px;font-weight:bold;}"
          "QPushButton:hover{background:#c8e6c9;}")
_S_SAVE = ("QPushButton{background:#e3f2fd;color:#1565c0;"
           "border:1px solid #90caf9;border-radius:5px;"
           "padding:0 14px;font-weight:bold;}"
           "QPushButton:hover{background:#bbdefb;}")
_S_DEL = ("QPushButton{background:#ffebee;color:#c62828;"
          "border:1px solid #ef9a9a;border-radius:5px;padding:0 12px;}"
          "QPushButton:hover{background:#ffcdd2;}")
_S_CANCEL = ("QPushButton{background:#f5f5f5;color:#555;"
             "border:1px solid #ddd;border-radius:5px;padding:0 12px;}"
             "QPushButton:hover{background:#eee;}")
_S_NEUTRAL = ("QPushButton{background:#f5f5f5;border:1px solid #ddd;"
              "border-radius:4px;}"
              "QPushButton:hover{background:#e3f2fd;}")


def _grp(title: str, color: str = "#1565c0",
         border: str = "#90caf9", bg: str = "#f9f9f9") -> QGroupBox:
    g = QGroupBox(title)
    g.setStyleSheet(f"""
        QGroupBox {{
            font-weight:bold; color:{color};
            border:1px solid {border}; border-radius:6px;
            margin-top:8px; padding-top:8px; background:{bg};
        }}
        QGroupBox::title {{ subcontrol-origin:margin; padding:0 6px; }}
    """)
    return g


# ══════════════════════════════════════════════════════════
# DimCategoriesTab
# ══════════════════════════════════════════════════════════

class DimCategoriesTab(QWidget):
    """
    تبويب تصنيفات مجموعات المقاسات.
    conn = designs.db  (dim_set_categories + dim_set_category_fields)
    """

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn             = conn
        self._editing_id      = None      # ID التصنيف قيد التعديل
        self._color           = "#607d8b"
        self._icon            = "📏"
        self._editing_fld_id  = None      # ID الحقل قيد التعديل (من DB)
        self._selected_cat_id = None      # التصنيف المحدد في الجدول
        self._build()
        self._load_cats()
        bus.data_changed.connect(self._on_bus)

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(4)
        splitter.setStyleSheet("""
            QSplitter::handle{background:#e0e0e0;}
            QSplitter::handle:hover{background:#90caf9;}
        """)
        splitter.addWidget(self._build_left())
        splitter.addWidget(self._build_right())
        splitter.setSizes([370, 610])
        root.addWidget(splitter)

    # ── لوحة يمين: قائمة التصنيفات ────────────────────────

    def _build_left(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background:#fafafa;")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(12, 12, 8, 12)
        lay.setSpacing(8)

        lbl = QLabel("📂  تصنيفات مجموعات المقاسات")
        lbl.setStyleSheet("font-weight:bold; font-size:13px; color:#1565c0;")
        lay.addWidget(lbl)

        hint = QLabel(
            "💡 كل تصنيف يحمل قالب حقول افتراضية.\n"
            "عند إنشاء مجموعة مقاسات وتختار تصنيف،\n"
            "حقول القالب تُنسخ تلقائياً للمجموعة."
        )
        hint.setStyleSheet(
            "font-size:10px; color:#555; background:#e3f2fd;"
            "border:1px solid #90caf9; border-radius:4px; padding:5px 8px;"
        )
        hint.setWordWrap(True)
        lay.addWidget(hint)

        # ── جدول التصنيفات ──
        self.tbl_cats = make_table(
            ["ID", "الأيقونة", "الاسم", "الوحدة", "الحقول"],
            stretch_col=2
        )
        self.tbl_cats.setColumnHidden(0, True)
        self.tbl_cats.setColumnWidth(1, 55)
        self.tbl_cats.setColumnWidth(3, 65)
        self.tbl_cats.setColumnWidth(4, 55)
        self.tbl_cats.selectionModel().selectionChanged.connect(self._on_cat_selected)
        lay.addWidget(self.tbl_cats, stretch=1)

        self.lbl_cats_count = QLabel()
        self.lbl_cats_count.setStyleSheet("color:#1565c0; font-size:10px;")
        lay.addWidget(self.lbl_cats_count)

        # ── فورم التصنيف (داخل scroll) ──
        form_container = QWidget()
        form_lay = QVBoxLayout(form_container)
        form_lay.setContentsMargins(0, 0, 0, 0)
        form_lay.setSpacing(0)

        grp = _grp("بيانات التصنيف")
        form = QFormLayout(grp)
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight)

        # الاسم
        self.inp_name = QLineEdit()
        self.inp_name.setMinimumHeight(30)
        self.inp_name.setPlaceholderText("مثال: خشب، معدن، قماش...")
        form.addRow("الاسم :", self.inp_name)

        # الوحدة الافتراضية
        unit_row = QHBoxLayout()
        self.inp_unit = QLineEdit()
        self.inp_unit.setMinimumHeight(28)
        self.inp_unit.setText("mm")
        self.inp_unit.setMaximumWidth(70)
        for u in _UNITS:
            b = QPushButton(u)
            b.setFixedHeight(24)
            b.setStyleSheet(
                "QPushButton{border:1px solid #c5cae9;border-radius:3px;"
                "background:#e8eaf6;padding:0 5px;font-size:10px;}"
                "QPushButton:hover{background:#c5cae9;}"
            )
            b.clicked.connect(lambda _, u=u: self.inp_unit.setText(u))
            unit_row.addWidget(b)
        unit_row.addStretch()
        form.addRow("الوحدة :", self.inp_unit)
        form.addRow("", unit_row)

        # الأيقونة
        icon_row = QHBoxLayout()
        self.inp_icon_txt = QLineEdit()
        self.inp_icon_txt.setMaximumWidth(50)
        self.inp_icon_txt.setMinimumHeight(28)
        self.inp_icon_txt.setText("📏")
        for ico in _ICONS:
            b = QPushButton(ico)
            b.setFixedSize(28, 28)
            b.setStyleSheet(
                "QPushButton{border:1px solid #e0e0e0;border-radius:3px;"
                "background:white;}"
                "QPushButton:hover{background:#e3f2fd;}"
            )
            b.clicked.connect(lambda _, i=ico: self.inp_icon_txt.setText(i))
            icon_row.addWidget(b)
        icon_row.addStretch()
        form.addRow("الأيقونة :", self.inp_icon_txt)
        form.addRow("", icon_row)

        # اللون
        color_row = QHBoxLayout()
        self.lbl_color = QLabel()
        self.lbl_color.setFixedSize(28, 28)
        self._refresh_color_preview()
        btn_pick = QPushButton("اختر")
        btn_pick.setMinimumHeight(26)
        btn_pick.clicked.connect(self._pick_color)
        for c in _PRESET_COLORS:
            bc = QPushButton()
            bc.setFixedSize(20, 20)
            bc.setStyleSheet(
                f"QPushButton{{background:{c};border-radius:3px;"
                "border:1px solid rgba(0,0,0,0.2);}}"
                f"QPushButton:hover{{border:2px solid #333;}}"
            )
            bc.clicked.connect(lambda _, col=c: self._set_color(col))
            color_row.addWidget(bc)
        color_row.addStretch()
        form.addRow("اللون :", self.lbl_color)
        form.addRow("", color_row)

        # ملاحظات
        self.inp_notes = QLineEdit()
        self.inp_notes.setMinimumHeight(28)
        self.inp_notes.setPlaceholderText("ملاحظات اختيارية...")
        form.addRow("ملاحظات :", self.inp_notes)

        # وضع النموذج
        self.lbl_cat_mode = QLabel("— تصنيف جديد —")
        self.lbl_cat_mode.setStyleSheet("font-weight:bold; color:#1565c0; font-size:10px;")
        form.addRow(self.lbl_cat_mode)

        # أزرار
        btn_row = QHBoxLayout()
        self.btn_cat_add    = QPushButton("➕ إضافة")
        self.btn_cat_save   = QPushButton("💾 حفظ")
        self.btn_cat_cancel = QPushButton("✖")
        self.btn_cat_del    = QPushButton("🗑 حذف")
        for b in (self.btn_cat_add, self.btn_cat_save,
                  self.btn_cat_cancel, self.btn_cat_del):
            b.setMinimumHeight(28)
        self.btn_cat_add.setStyleSheet(_S_ADD)
        self.btn_cat_save.setStyleSheet(_S_SAVE)
        self.btn_cat_cancel.setStyleSheet(_S_CANCEL)
        self.btn_cat_del.setStyleSheet(_S_DEL)
        self.btn_cat_save.setVisible(False)
        self.btn_cat_cancel.setVisible(False)

        self.btn_cat_add.clicked.connect(self._add_cat)
        self.btn_cat_save.clicked.connect(self._save_cat)
        self.btn_cat_cancel.clicked.connect(self._reset_cat_form)
        self.btn_cat_del.clicked.connect(self._delete_cat)

        btn_row.addWidget(self.btn_cat_add)
        btn_row.addWidget(self.btn_cat_save)
        btn_row.addWidget(self.btn_cat_cancel)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_cat_del)
        form.addRow(btn_row)

        form_lay.addWidget(grp)
        lay.addWidget(wrap_in_scroll(form_container, min_height=0))
        return panel

    # ── لوحة يسار: حقول القالب ─────────────────────────────

    def _build_right(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background:white;")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(8, 12, 12, 12)
        lay.setSpacing(8)

        self.lbl_fields_title = QLabel("📐  حقول القالب الافتراضية")
        self.lbl_fields_title.setStyleSheet(
            "font-weight:bold; font-size:13px; color:#e65100;"
        )
        lay.addWidget(self.lbl_fields_title)

        hint = QLabel(
            "💡 اختر تصنيفاً لعرض حقوله وتعديلها.\n"
            "هذه الحقول تُنسخ تلقائياً عند إنشاء مجموعة مقاسات من هذا التصنيف."
        )
        hint.setStyleSheet(
            "font-size:10px; color:#e65100; background:#fff8e1;"
            "border:1px solid #ffe082; border-radius:4px; padding:4px 8px;"
        )
        hint.setWordWrap(True)
        lay.addWidget(hint)

        # ── جدول الحقول ──
        self.tbl_fields = make_table(
            ["ID", "المفتاح", "التسمية", "الوحدة", "النوع", "مطلوب"],
            stretch_col=2
        )
        self.tbl_fields.setColumnHidden(0, True)
        self.tbl_fields.setColumnWidth(1, 100)
        self.tbl_fields.setColumnWidth(3, 60)
        self.tbl_fields.setColumnWidth(4, 120)
        self.tbl_fields.setColumnWidth(5, 55)
        self.tbl_fields.selectionModel().selectionChanged.connect(self._on_field_selected)
        lay.addWidget(self.tbl_fields, stretch=1)

        # أزرار ترتيب
        ord_row = QHBoxLayout()
        self.btn_fld_up   = QPushButton("▲ أعلى")
        self.btn_fld_down = QPushButton("▼ أسفل")
        for b in (self.btn_fld_up, self.btn_fld_down):
            b.setMinimumHeight(26)
            b.setStyleSheet(_S_NEUTRAL)
        self.btn_fld_up.clicked.connect(lambda: self._move_field(-1))
        self.btn_fld_down.clicked.connect(lambda: self._move_field(1))
        ord_row.addWidget(self.btn_fld_up)
        ord_row.addWidget(self.btn_fld_down)
        ord_row.addStretch()
        self.lbl_flds_count = QLabel()
        self.lbl_flds_count.setStyleSheet("color:#e65100; font-size:10px;")
        ord_row.addWidget(self.lbl_flds_count)
        lay.addLayout(ord_row)

        # ── فورم الحقل ──
        grp2 = _grp("بيانات الحقل", color="#e65100",
                     border="#ffcc80", bg="#fffde7")
        form2 = QFormLayout(grp2)
        form2.setSpacing(8)
        form2.setLabelAlignment(Qt.AlignRight)

        # صف واحد يجمع المفتاح والتسمية والوحدة
        inline = QHBoxLayout()
        self.inp_fld_name = QLineEdit()
        self.inp_fld_name.setPlaceholderText("مفتاح: length")
        self.inp_fld_name.setMinimumHeight(28)

        self.inp_fld_label = QLineEdit()
        self.inp_fld_label.setPlaceholderText("تسمية: الطول")
        self.inp_fld_label.setMinimumHeight(28)

        self.inp_fld_unit = QLineEdit()
        self.inp_fld_unit.setPlaceholderText("وحدة")
        self.inp_fld_unit.setMaximumWidth(65)
        self.inp_fld_unit.setMinimumHeight(28)

        inline.addWidget(self.inp_fld_name, 2)
        inline.addWidget(self.inp_fld_label, 3)
        inline.addWidget(self.inp_fld_unit, 1)
        form2.addRow("المفتاح / التسمية / الوحدة :", inline)

        # النوع + خيارات select
        type_row = QHBoxLayout()
        self.cmb_fld_type = QComboBox()
        self.cmb_fld_type.setMinimumHeight(28)
        for key, lbl in _FIELD_TYPES:
            self.cmb_fld_type.addItem(lbl, key)
        self.cmb_fld_type.currentIndexChanged.connect(self._on_fld_type_changed)

        self.inp_fld_options = QLineEdit()
        self.inp_fld_options.setPlaceholderText("خيارات مفصولة بفاصلة: أ, ب, ج")
        self.inp_fld_options.setMinimumHeight(28)
        self.inp_fld_options.setVisible(False)

        type_row.addWidget(self.cmb_fld_type, 1)
        type_row.addWidget(self.inp_fld_options, 2)
        form2.addRow("النوع :", type_row)

        self.chk_required = QCheckBox("مطلوب (Required)")
        self.chk_required.setChecked(True)
        form2.addRow("", self.chk_required)

        # وضع النموذج
        self.lbl_fld_mode = QLabel("إضافة حقل")
        self.lbl_fld_mode.setStyleSheet("color:#e65100; font-size:10px;")
        form2.addRow(self.lbl_fld_mode)

        # أزرار الحقل
        fld_btn_row = QHBoxLayout()
        self.btn_fld_add    = QPushButton("➕ إضافة حقل")
        self.btn_fld_save   = QPushButton("💾 حفظ")
        self.btn_fld_cancel = QPushButton("✖")
        self.btn_fld_del    = QPushButton("🗑 حذف")
        for b in (self.btn_fld_add, self.btn_fld_save,
                  self.btn_fld_cancel, self.btn_fld_del):
            b.setMinimumHeight(28)
        self.btn_fld_add.setStyleSheet(_S_ADD)
        self.btn_fld_save.setStyleSheet(_S_SAVE)
        self.btn_fld_cancel.setStyleSheet(_S_CANCEL)
        self.btn_fld_del.setStyleSheet(_S_DEL)
        self.btn_fld_save.setVisible(False)
        self.btn_fld_cancel.setVisible(False)

        self.btn_fld_add.clicked.connect(self._add_field)
        self.btn_fld_save.clicked.connect(self._save_field)
        self.btn_fld_cancel.clicked.connect(self._reset_field_form)
        self.btn_fld_del.clicked.connect(self._delete_field)

        fld_btn_row.addWidget(self.btn_fld_add)
        fld_btn_row.addWidget(self.btn_fld_save)
        fld_btn_row.addWidget(self.btn_fld_cancel)
        fld_btn_row.addStretch()
        fld_btn_row.addWidget(self.btn_fld_del)
        form2.addRow(fld_btn_row)

        lay.addWidget(grp2)
        return panel

    # ══════════════════════════════════════════════════════
    # تحميل البيانات
    # ══════════════════════════════════════════════════════

    def _load_cats(self):
        cats = fetch_all_dim_set_categories(self.conn)
        self.tbl_cats.setRowCount(0)
        for c in cats:
            r = self.tbl_cats.rowCount()
            self.tbl_cats.insertRow(r)
            self.tbl_cats.setItem(r, 0, QTableWidgetItem(str(c["id"])))

            ico = QTableWidgetItem(c["icon"] or "📏")
            ico.setTextAlignment(Qt.AlignCenter)
            self.tbl_cats.setItem(r, 1, ico)

            name_item = QTableWidgetItem(c["name"])
            name_item.setForeground(QColor(c["color"]))
            name_item.setFont(QFont("", -1, QFont.Bold))
            self.tbl_cats.setItem(r, 2, name_item)

            self.tbl_cats.setItem(r, 3, QTableWidgetItem(c["default_unit"] or "mm"))

            # عدد حقول القالب
            fields = fetch_category_template_fields(self.conn, c["id"])
            cnt = QTableWidgetItem(str(len(fields)) if fields else "—")
            cnt.setTextAlignment(Qt.AlignCenter)
            self.tbl_cats.setItem(r, 4, cnt)

        self.lbl_cats_count.setText(f"({len(cats)} تصنيف)")

        # إعادة تحديد التصنيف المحدد
        if self._selected_cat_id is not None:
            for r in range(self.tbl_cats.rowCount()):
                if int(self.tbl_cats.item(r, 0).text()) == self._selected_cat_id:
                    self.tbl_cats.selectRow(r)
                    break

    def _load_fields(self, cat_id: int):
        self._selected_cat_id = cat_id
        cat = fetch_dim_set_category(self.conn, cat_id)
        if cat:
            self.lbl_fields_title.setText(
                f"📐  حقول القالب:  {cat['icon'] or ''} {cat['name']}"
                f"  (وحدة: {cat['default_unit'] or 'mm'})"
            )

        fields = fetch_category_template_fields(self.conn, cat_id)
        self.tbl_fields.setRowCount(0)
        for f in fields:
            r = self.tbl_fields.rowCount()
            self.tbl_fields.insertRow(r)
            self.tbl_fields.setItem(r, 0, QTableWidgetItem(str(f["id"])))
            self.tbl_fields.setItem(r, 1, QTableWidgetItem(f["name"] or ""))

            lbl_item = QTableWidgetItem(f["label"] or "")
            lbl_item.setFont(QFont("", -1, QFont.Bold))
            self.tbl_fields.setItem(r, 2, lbl_item)

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

        self.lbl_flds_count.setText(f"({len(fields)} حقل)")
        self._reset_field_form()

    def _on_bus(self):
        self._load_cats()
        if self._selected_cat_id:
            self._load_fields(self._selected_cat_id)

    # ══════════════════════════════════════════════════════
    # Signal handlers
    # ══════════════════════════════════════════════════════

    def _on_cat_selected(self):
        rows = self.tbl_cats.selectionModel().selectedRows()
        if not rows:
            return
        cat_id = int(self.tbl_cats.item(rows[0].row(), 0).text())
        self._load_cat_to_form(cat_id)
        self._load_fields(cat_id)

    def _on_field_selected(self):
        rows = self.tbl_fields.selectionModel().selectedRows()
        if not rows:
            return
        fld_id = int(self.tbl_fields.item(rows[0].row(), 0).text())
        self._load_field_to_form(fld_id)

    def _on_fld_type_changed(self):
        self.inp_fld_options.setVisible(
            self.cmb_fld_type.currentData() == "select"
        )

    # ══════════════════════════════════════════════════════
    # CRUD التصنيفات
    # ══════════════════════════════════════════════════════

    def _load_cat_to_form(self, cat_id: int):
        cat = fetch_dim_set_category(self.conn, cat_id)
        if not cat:
            return
        self._editing_id = cat_id
        self.inp_name.setText(cat["name"])
        self.inp_unit.setText(cat["default_unit"] or "mm")
        self.inp_icon_txt.setText(cat["icon"] or "📏")
        self.inp_notes.setText(cat["notes"] or "")
        self._color = cat["color"] or "#607d8b"
        self._refresh_color_preview()
        self.lbl_cat_mode.setText(f"تعديل: {cat['name']}")
        self.btn_cat_add.setVisible(False)
        self.btn_cat_save.setVisible(True)
        self.btn_cat_cancel.setVisible(True)

    def _add_cat(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم التصنيف")
            return
        new_id = insert_dim_set_category(
            self.conn,
            name=name,
            description=self.inp_notes.text().strip(),
            default_unit=self.inp_unit.text().strip() or "mm",
            color=self._color,
            icon=self.inp_icon_txt.text().strip() or "📏",
            notes=self.inp_notes.text().strip(),
        )
        self._selected_cat_id = new_id
        self._reset_cat_form()
        bus.data_changed.emit()

    def _save_cat(self):
        if not self._editing_id:
            return
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم التصنيف")
            return
        update_dim_set_category(
            self.conn,
            cat_id=self._editing_id,
            name=name,
            description=self.inp_notes.text().strip(),
            default_unit=self.inp_unit.text().strip() or "mm",
            color=self._color,
            icon=self.inp_icon_txt.text().strip() or "📏",
            notes=self.inp_notes.text().strip(),
        )
        self._reset_cat_form()
        bus.data_changed.emit()

    def _delete_cat(self):
        rows = self.tbl_cats.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "تنبيه", "اختر تصنيفاً أولاً")
            return
        cat_id = int(self.tbl_cats.item(rows[0].row(), 0).text())
        cat = fetch_dim_set_category(self.conn, cat_id)
        if not cat:
            return

        # عدد مجموعات المقاسات المرتبطة
        linked = self.conn.execute(
            "SELECT COUNT(*) as c FROM dimension_sets WHERE category_id=?",
            (cat_id,)
        ).fetchone()["c"]

        msg = f"حذف تصنيف «{cat['name']}»؟\nسيتم حذف كل حقوله الافتراضية."
        if linked:
            msg += f"\n⚠️ {linked} مجموعة مقاسات مرتبطة — ستفقد تصنيفها."

        if QMessageBox.question(
            self, "تأكيد", msg, QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            delete_dim_set_category(self.conn, cat_id)
            self._selected_cat_id = None
            self.tbl_fields.setRowCount(0)
            self.lbl_fields_title.setText("📐  حقول القالب الافتراضية")
            self._reset_cat_form()
            bus.data_changed.emit()

    def _reset_cat_form(self):
        self._editing_id = None
        self.inp_name.clear()
        self.inp_unit.setText("mm")
        self.inp_icon_txt.setText("📏")
        self.inp_notes.clear()
        self._color = "#607d8b"
        self._refresh_color_preview()
        self.lbl_cat_mode.setText("— تصنيف جديد —")
        self.btn_cat_add.setVisible(True)
        self.btn_cat_save.setVisible(False)
        self.btn_cat_cancel.setVisible(False)

    # ══════════════════════════════════════════════════════
    # CRUD حقول القالب
    # ══════════════════════════════════════════════════════

    def _load_field_to_form(self, fld_id: int):
        """يحمّل بيانات حقل من DB إلى الفورم."""
        # نجيب الحقل من الجدول مباشرة
        row = self.conn.execute(
            "SELECT * FROM dim_set_category_fields WHERE id=?", (fld_id,)
        ).fetchone()
        if not row:
            return
        self._editing_fld_id = fld_id
        self.inp_fld_name.setText(row["name"] or "")
        self.inp_fld_label.setText(row["label"] or "")
        self.inp_fld_unit.setText(row["unit"] or "")
        self.chk_required.setChecked(bool(row["required"]))

        # النوع
        for i in range(self.cmb_fld_type.count()):
            if self.cmb_fld_type.itemData(i) == row["field_type"]:
                self.cmb_fld_type.setCurrentIndex(i)
                break

        # الخيارات
        if row["field_type"] == "select" and row["options"]:
            try:
                opts = json.loads(row["options"])
                self.inp_fld_options.setText(", ".join(str(o) for o in opts))
            except Exception:
                self.inp_fld_options.clear()
            self.inp_fld_options.setVisible(True)
        else:
            self.inp_fld_options.clear()
            self.inp_fld_options.setVisible(False)

        self.lbl_fld_mode.setText(f"تعديل: {row['label']}")
        self.btn_fld_add.setVisible(False)
        self.btn_fld_save.setVisible(True)
        self.btn_fld_cancel.setVisible(True)

    def _add_field(self):
        if not self._selected_cat_id:
            QMessageBox.information(self, "تنبيه", "اختر تصنيفاً أولاً")
            return
        name  = self.inp_fld_name.text().strip()
        label = self.inp_fld_label.text().strip()
        if not name or not label:
            QMessageBox.warning(self, "تنبيه", "أدخل المفتاح والتسمية")
            return

        # تحقق من التكرار في نفس التصنيف
        dup = self.conn.execute(
            "SELECT id FROM dim_set_category_fields "
            "WHERE category_id=? AND name=?",
            (self._selected_cat_id, name)
        ).fetchone()
        if dup:
            QMessageBox.warning(self, "تنبيه", f"المفتاح «{name}» موجود بالفعل")
            return

        sort_order = self.tbl_fields.rowCount()
        insert_category_template_field(
            self.conn,
            cat_id=self._selected_cat_id,
            name=name,
            label=label,
            unit=self.inp_fld_unit.text().strip(),
            field_type=self.cmb_fld_type.currentData(),
            options=self._parse_options(),
            required=self.chk_required.isChecked(),
            sort_order=sort_order,
        )
        self._reset_field_form()
        self._load_fields(self._selected_cat_id)
        self._load_cats()  # تحديث عداد الحقول في الجدول

    def _save_field(self):
        if not self._editing_fld_id:
            return
        name  = self.inp_fld_name.text().strip()
        label = self.inp_fld_label.text().strip()
        if not name or not label:
            QMessageBox.warning(self, "تنبيه", "أدخل المفتاح والتسمية")
            return

        # نجيب sort_order الحالي
        row = self.conn.execute(
            "SELECT sort_order FROM dim_set_category_fields WHERE id=?",
            (self._editing_fld_id,)
        ).fetchone()
        sort_order = row["sort_order"] if row else 0

        update_category_template_field(
            self.conn,
            field_id=self._editing_fld_id,
            name=name,
            label=label,
            unit=self.inp_fld_unit.text().strip(),
            field_type=self.cmb_fld_type.currentData(),
            options=self._parse_options(),
            required=self.chk_required.isChecked(),
            sort_order=sort_order,
        )
        self._reset_field_form()
        self._load_fields(self._selected_cat_id)

    def _delete_field(self):
        rows = self.tbl_fields.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "تنبيه", "اختر حقلاً أولاً")
            return
        fld_id = int(self.tbl_fields.item(rows[0].row(), 0).text())
        row = self.conn.execute(
            "SELECT label FROM dim_set_category_fields WHERE id=?", (fld_id,)
        ).fetchone()
        name = row["label"] if row else str(fld_id)

        if QMessageBox.question(
            self, "تأكيد", f"حذف الحقل «{name}» من القالب؟",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            delete_category_template_field(self.conn, fld_id)
            self._reset_field_form()
            self._load_fields(self._selected_cat_id)
            self._load_cats()

    def _reset_field_form(self):
        self._editing_fld_id = None
        self.inp_fld_name.clear()
        self.inp_fld_label.clear()
        self.inp_fld_unit.clear()
        self.cmb_fld_type.setCurrentIndex(0)
        self.inp_fld_options.clear()
        self.inp_fld_options.setVisible(False)
        self.chk_required.setChecked(True)
        self.lbl_fld_mode.setText("إضافة حقل")
        self.btn_fld_add.setVisible(True)
        self.btn_fld_save.setVisible(False)
        self.btn_fld_cancel.setVisible(False)

    def _move_field(self, direction: int):
        rows = self.tbl_fields.selectionModel().selectedRows()
        if not rows or not self._selected_cat_id:
            return
        cur = rows[0].row()
        nxt = cur + direction
        if nxt < 0 or nxt >= self.tbl_fields.rowCount():
            return

        # نجيب IDs الحقول بالترتيب الحالي
        ids = [
            int(self.tbl_fields.item(r, 0).text())
            for r in range(self.tbl_fields.rowCount())
        ]
        ids[cur], ids[nxt] = ids[nxt], ids[cur]
        reorder_category_template_fields(self.conn, self._selected_cat_id, ids)
        self._load_fields(self._selected_cat_id)
        self.tbl_fields.selectRow(nxt)

    def _parse_options(self):
        if self.cmb_fld_type.currentData() != "select":
            return None
        text = self.inp_fld_options.text().strip()
        if not text:
            return None
        return [o.strip() for o in text.split(",") if o.strip()]

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
            f"background:{self._color}; border-radius:4px;"
            "border:1px solid #ccc;"
        )