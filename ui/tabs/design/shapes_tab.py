"""
ui/tabs/design/shapes_tab.py
==============================
تبويب الأشكال — عرض + إضافة + تعديل + حذف + إدخال المقاسات.

التصميم:
  يسار: قايمة الأشكال مع فلتر بالتصنيف ومجموعة المقاسات
  يمين: فورم تفاصيل الشكل + حقول المقاسات الديناميكية
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QGroupBox, QFormLayout,
    QTextEdit, QMessageBox, QFrame, QScrollArea,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui  import QColor, QFont

from db.design.design_repo import (
    fetch_all_shapes, fetch_shape, insert_shape, update_shape, delete_shape,
    fetch_all_design_categories, fetch_all_dimension_sets,
    fetch_fields_for_set, fetch_shape_dimensions,
    save_shape_dimensions, delete_shape_dimensions_for_set,
)
from ui.events import bus


class ShapesTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._editing_id = None
        self._dim_inputs: dict = {}   # {field_id: QLineEdit/QComboBox}
        self._build()
        self._load_filters()
        self._load_shapes()
        bus.data_changed.connect(self._reload)

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        main = QHBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(4)
        splitter.setStyleSheet("""
            QSplitter::handle { background: #e0e0e0; }
            QSplitter::handle:hover { background: #ce93d8; }
        """)

        # ── الجانب الأيسر: القايمة ──
        left = self._build_list_panel()
        splitter.addWidget(left)

        # ── الجانب الأيمن: الفورم ──
        right = self._build_form_panel()
        splitter.addWidget(right)

        splitter.setSizes([420, 560])
        main.addWidget(splitter)

    def _build_list_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background: #fafafa;")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(12, 12, 8, 12)
        lay.setSpacing(8)

        # ── فلاتر ──
        lbl_filters = QLabel("🔍  فلترة الأشكال")
        lbl_filters.setStyleSheet(
            "font-weight:bold; font-size:12px; color:#6a1b9a;"
        )
        lay.addWidget(lbl_filters)

        # بحث نصي
        search_row = QHBoxLayout()
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("بحث بالاسم أو الوصف...")
        self.inp_search.setMinimumHeight(30)
        self.inp_search.setStyleSheet("""
            QLineEdit {
                background:white; border:1px solid #ce93d8;
                border-radius:5px; padding:2px 8px; font-size:12px;
            }
            QLineEdit:focus { border-color:#7b1fa2; }
        """)
        btn_clr = QPushButton("✖")
        btn_clr.setFixedSize(26, 26)
        btn_clr.setStyleSheet(
            "QPushButton{background:transparent;border:none;color:#aaa;}"
            "QPushButton:hover{color:#e53935;}"
        )
        btn_clr.clicked.connect(self.inp_search.clear)
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(250)
        self._search_timer.timeout.connect(self._load_shapes)
        self.inp_search.textChanged.connect(lambda: self._search_timer.start())
        search_row.addWidget(self.inp_search, stretch=1)
        search_row.addWidget(btn_clr)
        lay.addLayout(search_row)

        # فلتر تصنيف
        self.cmb_filter_cat = QComboBox()
        self.cmb_filter_cat.setMinimumHeight(28)
        self.cmb_filter_cat.setStyleSheet(self._combo_style("#ce93d8"))
        self.cmb_filter_cat.currentIndexChanged.connect(self._load_shapes)
        lay.addWidget(self.cmb_filter_cat)

        # فلتر مجموعة مقاسات
        self.cmb_filter_set = QComboBox()
        self.cmb_filter_set.setMinimumHeight(28)
        self.cmb_filter_set.setStyleSheet(self._combo_style("#90caf9"))
        self.cmb_filter_set.currentIndexChanged.connect(self._load_shapes)
        lay.addWidget(self.cmb_filter_set)

        # عداد
        self.lbl_count = QLabel()
        self.lbl_count.setStyleSheet(
            "color:#6a1b9a; font-size:10px; font-weight:bold;"
        )
        lay.addWidget(self.lbl_count)

        # ── الجدول ──
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "الاسم", "التصنيف", "المقاسات"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setColumnHidden(0, True)
        self.table.verticalHeader().setVisible(False)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Interactive)
        hh.setSectionResizeMode(3, QHeaderView.Interactive)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 110)
        hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.selectionModel().selectionChanged.connect(self._on_select)
        lay.addWidget(self.table, stretch=1)

        # ── أزرار الجدول ──
        btn_row = QHBoxLayout()
        self.btn_new = QPushButton("➕ شكل جديد")
        self.btn_del = QPushButton("🗑 حذف")
        self.btn_new.setMinimumHeight(32)
        self.btn_del.setMinimumHeight(32)
        self.btn_new.setStyleSheet(self._btn_style("#6a1b9a", "#7b1fa2"))
        self.btn_del.setStyleSheet(
            "QPushButton{background:#ffebee;color:#c62828;"
            "border:1px solid #ef9a9a;border-radius:5px;padding:0 12px;}"
            "QPushButton:hover{background:#ffcdd2;}"
        )
        self.btn_new.clicked.connect(self._new_shape)
        self.btn_del.clicked.connect(self._delete_shape)
        btn_row.addWidget(self.btn_new)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_del)
        lay.addLayout(btn_row)

        return panel

    def _build_form_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background: white;")

        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── رأس الفورم ──
        self.lbl_form_title = QLabel("✏️  بيانات الشكل")
        self.lbl_form_title.setFixedHeight(38)
        self.lbl_form_title.setStyleSheet("""
            QLabel {
                background: #f3e5f5;
                border-bottom: 2px solid #ce93d8;
                font-size: 13px; font-weight: bold; color: #6a1b9a;
                padding-right: 12px;
            }
        """)
        outer.addWidget(self.lbl_form_title)

        # ── محتوى الفورم بـ scroll ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border:none; background:white; }
            QScrollBar:vertical {
                background:#f5f5f5; width:8px; border-radius:4px;
            }
            QScrollBar::handle:vertical {
                background:#ce93d8; border-radius:4px; min-height:30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
        """)

        content = QWidget()
        content.setStyleSheet("background:white;")
        self._form_layout = QVBoxLayout(content)
        self._form_layout.setContentsMargins(16, 12, 16, 16)
        self._form_layout.setSpacing(12)

        # ── البيانات الأساسية ──
        basic = QGroupBox("📋  البيانات الأساسية")
        basic.setStyleSheet(self._group_style("#6a1b9a"))
        form = QFormLayout(basic)
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم الشكل...")
        self.inp_name.setMinimumHeight(32)
        form.addRow("الاسم :", self.inp_name)

        self.cmb_cat = QComboBox()
        self.cmb_cat.setMinimumHeight(30)
        form.addRow("التصنيف :", self.cmb_cat)

        self.inp_material = QLineEdit()
        self.inp_material.setPlaceholderText("مثال: خشب زان، حديد مجلفن...")
        self.inp_material.setMinimumHeight(30)
        form.addRow("المادة :", self.inp_material)

        self.inp_desc = QTextEdit()
        self.inp_desc.setPlaceholderText("وصف اختياري...")
        self.inp_desc.setMaximumHeight(70)
        form.addRow("الوصف :", self.inp_desc)

        self.inp_notes = QTextEdit()
        self.inp_notes.setPlaceholderText("ملاحظات...")
        self.inp_notes.setMaximumHeight(60)
        form.addRow("ملاحظات :", self.inp_notes)

        self._form_layout.addWidget(basic)

        # ── مجموعة المقاسات ──
        set_grp = QGroupBox("📏  مجموعة المقاسات")
        set_grp.setStyleSheet(self._group_style("#1565c0"))
        set_lay = QVBoxLayout(set_grp)

        self.cmb_dim_set = QComboBox()
        self.cmb_dim_set.setMinimumHeight(30)
        self.cmb_dim_set.currentIndexChanged.connect(self._on_dim_set_changed)
        set_lay.addWidget(self.cmb_dim_set)

        self._form_layout.addWidget(set_grp)

        # ── حاوية حقول المقاسات الديناميكية ──
        self._dims_group = QGroupBox("📐  قيم المقاسات")
        self._dims_group.setStyleSheet(self._group_style("#e65100"))
        self._dims_form = QFormLayout(self._dims_group)
        self._dims_form.setSpacing(8)
        self._dims_form.setLabelAlignment(Qt.AlignRight)
        self._form_layout.addWidget(self._dims_group)

        self._form_layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll, stretch=1)

        # ── أزرار الحفظ ──
        btn_bar = QFrame()
        btn_bar.setStyleSheet("""
            QFrame {
                background: #f8f8f8;
                border-top: 1px solid #e0e0e0;
            }
        """)
        btn_bar.setFixedHeight(50)
        btn_bar_lay = QHBoxLayout(btn_bar)
        btn_bar_lay.setContentsMargins(16, 8, 16, 8)

        self.btn_save   = QPushButton("💾  حفظ")
        self.btn_cancel = QPushButton("✖  إلغاء")
        self.btn_save.setMinimumHeight(34)
        self.btn_cancel.setMinimumHeight(34)
        self.btn_save.setStyleSheet(self._btn_style("#2e7d32", "#1b5e20"))
        self.btn_cancel.setStyleSheet(
            "QPushButton{background:#f5f5f5;color:#555;"
            "border:1px solid #ddd;border-radius:5px;padding:0 16px;}"
            "QPushButton:hover{background:#eee;}"
        )
        self.lbl_mode = QLabel("اختر شكلاً أو أضف جديداً")
        self.lbl_mode.setStyleSheet("color:#6a1b9a; font-size:11px;")

        self.btn_save.clicked.connect(self._save_shape)
        self.btn_cancel.clicked.connect(self._cancel_edit)
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)

        btn_bar_lay.addWidget(self.lbl_mode)
        btn_bar_lay.addStretch()
        btn_bar_lay.addWidget(self.btn_cancel)
        btn_bar_lay.addWidget(self.btn_save)

        outer.addWidget(btn_bar)

        return panel

    # ══════════════════════════════════════════════════════
    # تحميل البيانات
    # ══════════════════════════════════════════════════════

    def _load_filters(self):
        """تحميل خيارات الفلاتر."""
        # فلاتر القايمة
        self.cmb_filter_cat.blockSignals(True)
        self.cmb_filter_set.blockSignals(True)
        self.cmb_filter_cat.clear()
        self.cmb_filter_set.clear()
        self.cmb_filter_cat.addItem("— كل التصنيفات —", None)
        self.cmb_filter_set.addItem("— كل المقاسات —", None)

        for cat in fetch_all_design_categories(self.conn):
            self.cmb_filter_cat.addItem(f"{cat['icon']}  {cat['name']}", cat["id"])

        for ds in fetch_all_dimension_sets(self.conn):
            self.cmb_filter_set.addItem(f"📏  {ds['name']}  ({ds['unit']})", ds["id"])

        self.cmb_filter_cat.blockSignals(False)
        self.cmb_filter_set.blockSignals(False)

        # فورم التصنيف
        self.cmb_cat.clear()
        self.cmb_cat.addItem("— بدون تصنيف —", None)
        for cat in fetch_all_design_categories(self.conn):
            self.cmb_cat.addItem(f"{cat['icon']}  {cat['name']}", cat["id"])

        # فورم مجموعة المقاسات
        self.cmb_dim_set.blockSignals(True)
        self.cmb_dim_set.clear()
        self.cmb_dim_set.addItem("— بدون مقاسات —", None)
        for ds in fetch_all_dimension_sets(self.conn):
            self.cmb_dim_set.addItem(f"📏  {ds['name']}  ({ds['unit']})", ds["id"])
        self.cmb_dim_set.blockSignals(False)

    def _load_shapes(self):
        q      = self.inp_search.text().strip().lower()
        cat_id = self.cmb_filter_cat.currentData()
        set_id = self.cmb_filter_set.currentData()

        shapes = fetch_all_shapes(self.conn,
                                   category_id=cat_id,
                                   dim_set_id=set_id)

        if q:
            shapes = [s for s in shapes
                      if q in s["name"].lower()
                      or q in (s["description"] or "").lower()
                      or q in (s["material"] or "").lower()]

        self.table.setRowCount(0)
        for s in shapes:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(s["id"])))

            # اسم الشكل
            name_item = QTableWidgetItem(s["name"])
            name_item.setFont(QFont("", -1, QFont.Bold))
            self.table.setItem(r, 1, name_item)

            # التصنيف
            cat_text = ""
            if s["category_name"]:
                cat_text = f"{s['category_icon'] or ''}  {s['category_name']}"
                cat_item = QTableWidgetItem(cat_text)
                if s["category_color"]:
                    cat_item.setForeground(QColor(s["category_color"]))
                self.table.setItem(r, 2, cat_item)
            else:
                self.table.setItem(r, 2, QTableWidgetItem("—"))

            # مجموعة المقاسات
            set_text = s["dim_set_name"] or "—"
            self.table.setItem(r, 3, QTableWidgetItem(set_text))

        self.lbl_count.setText(f"({len(shapes)} شكل)")

    def _reload(self):
        self._load_filters()
        self._load_shapes()

    # ══════════════════════════════════════════════════════
    # عرض حقول المقاسات الديناميكية
    # ══════════════════════════════════════════════════════

    def _on_dim_set_changed(self, _):
        set_id = self.cmb_dim_set.currentData()
        self._rebuild_dim_fields(set_id)

    def _rebuild_dim_fields(self, set_id: int = None,
                             existing_values: dict = None):
        """يعيد بناء حقول المقاسات حسب مجموعة المقاسات المختارة."""
        # مسح الحقول القديمة
        while self._dims_form.rowCount() > 0:
            self._dims_form.removeRow(0)
        self._dim_inputs.clear()

        if set_id is None:
            self._dims_group.setTitle("📐  قيم المقاسات  (لا توجد مجموعة مقاسات)")
            return

        fields = fetch_fields_for_set(self.conn, set_id)
        if not fields:
            self._dims_group.setTitle("📐  قيم المقاسات  (لا توجد حقول)")
            return

        self._dims_group.setTitle(f"📐  قيم المقاسات  ({len(fields)} حقل)")

        for field in fields:
            fid    = field["id"]
            label  = field["label"]
            unit   = field["unit"] or ""
            ftype  = field["field_type"]
            req    = bool(field["required"])

            lbl_text = f"{label}"
            if unit:
                lbl_text += f"  ({unit})"
            if req:
                lbl_text += "  *"

            saved_val = ""
            if existing_values and fid in existing_values:
                saved_val = existing_values[fid]

            if ftype == "boolean":
                from PyQt5.QtWidgets import QCheckBox
                inp = QCheckBox()
                inp.setChecked(saved_val.lower() in ("1", "true", "نعم", "yes"))
                self._dim_inputs[fid] = inp
            elif ftype == "select" and field["options"]:
                import json
                inp = QComboBox()
                inp.setMinimumHeight(28)
                try:
                    opts = json.loads(field["options"])
                    for opt in opts:
                        inp.addItem(str(opt), str(opt))
                except Exception:
                    pass
                if saved_val:
                    for i in range(inp.count()):
                        if inp.itemText(i) == saved_val:
                            inp.setCurrentIndex(i)
                            break
                self._dim_inputs[fid] = inp
            else:
                inp = QLineEdit()
                inp.setMinimumHeight(28)
                inp.setPlaceholderText(f"أدخل {label}...")
                inp.setText(saved_val)
                inp.setStyleSheet("""
                    QLineEdit {
                        background:white; border:1px solid #ffcc80;
                        border-radius:4px; padding:2px 6px;
                    }
                    QLineEdit:focus { border-color:#e65100; }
                """)
                self._dim_inputs[fid] = inp

            self._dims_form.addRow(lbl_text, inp)

    # ══════════════════════════════════════════════════════
    # إجراءات CRUD
    # ══════════════════════════════════════════════════════

    def _on_select(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        shape_id = int(self.table.item(rows[0].row(), 0).text())
        self._load_shape_to_form(shape_id)

    def _load_shape_to_form(self, shape_id: int):
        shape = fetch_shape(self.conn, shape_id)
        if not shape:
            return

        self._editing_id = shape_id

        # البيانات الأساسية
        self.inp_name.setText(shape["name"])
        self.inp_material.setText(shape["material"] or "")
        self.inp_desc.setPlainText(shape["description"] or "")
        self.inp_notes.setPlainText(shape["notes"] or "")

        # التصنيف
        for i in range(self.cmb_cat.count()):
            if self.cmb_cat.itemData(i) == shape["category_id"]:
                self.cmb_cat.setCurrentIndex(i)
                break

        # مجموعة المقاسات
        self.cmb_dim_set.blockSignals(True)
        for i in range(self.cmb_dim_set.count()):
            if self.cmb_dim_set.itemData(i) == shape["dim_set_id"]:
                self.cmb_dim_set.setCurrentIndex(i)
                break
        self.cmb_dim_set.blockSignals(False)

        # حقول المقاسات مع القيم المحفوظة
        existing = fetch_shape_dimensions(self.conn, shape_id)
        self._rebuild_dim_fields(shape["dim_set_id"], existing)

        # وضع التعديل
        self._enter_edit_mode(shape["name"])

    def _new_shape(self):
        """تهيئة الفورم لشكل جديد."""
        self._editing_id = None
        self.inp_name.clear()
        self.inp_material.clear()
        self.inp_desc.clear()
        self.inp_notes.clear()
        self.cmb_cat.setCurrentIndex(0)
        self.cmb_dim_set.setCurrentIndex(0)
        self._rebuild_dim_fields(None)
        self.table.clearSelection()
        self._enter_edit_mode(None)
        self.inp_name.setFocus()

    def _enter_edit_mode(self, name: str = None):
        if name:
            self.lbl_mode.setText(f"تعديل:  {name}")
            self.lbl_form_title.setText(f"✏️  تعديل:  {name}")
        else:
            self.lbl_mode.setText("إضافة شكل جديد")
            self.lbl_form_title.setText("➕  شكل جديد")
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)

    def _cancel_edit(self):
        self._editing_id = None
        self.lbl_form_title.setText("✏️  بيانات الشكل")
        self.lbl_mode.setText("اختر شكلاً أو أضف جديداً")
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        self.inp_name.clear()
        self.inp_material.clear()
        self.inp_desc.clear()
        self.inp_notes.clear()
        self.cmb_dim_set.setCurrentIndex(0)
        self._rebuild_dim_fields(None)
        self.table.clearSelection()

    def _save_shape(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم الشكل")
            return

        cat_id  = self.cmb_cat.currentData()
        set_id  = self.cmb_dim_set.currentData()
        mat     = self.inp_material.text().strip()
        desc    = self.inp_desc.toPlainText().strip()
        notes   = self.inp_notes.toPlainText().strip()

        if self._editing_id:
            update_shape(self.conn, self._editing_id, name, cat_id,
                         set_id, desc, mat, notes)
            shape_id = self._editing_id
        else:
            shape_id = insert_shape(self.conn, name, cat_id, set_id,
                                     desc, mat, notes)

        # حفظ المقاسات
        if set_id and self._dim_inputs:
            dim_values = {}
            for fid, inp in self._dim_inputs.items():
                from PyQt5.QtWidgets import QCheckBox
                if isinstance(inp, QCheckBox):
                    dim_values[fid] = "1" if inp.isChecked() else "0"
                elif isinstance(inp, QComboBox):
                    dim_values[fid] = inp.currentText()
                else:
                    dim_values[fid] = inp.text().strip()
            save_shape_dimensions(self.conn, shape_id, dim_values)

        bus.data_changed.emit()
        self._cancel_edit()
        self._load_shapes()

    def _delete_shape(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "تنبيه", "اختر شكلاً أولاً")
            return
        shape_id = int(self.table.item(rows[0].row(), 0).text())
        name_item = self.table.item(rows[0].row(), 1)
        name = name_item.text() if name_item else str(shape_id)

        if QMessageBox.question(
            self, "تأكيد", f"حذف الشكل «{name}»؟\nسيتم حذف كل مقاساته أيضاً.",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            delete_shape(self.conn, shape_id)
            if self._editing_id == shape_id:
                self._cancel_edit()
            bus.data_changed.emit()
            self._load_shapes()

    # ══════════════════════════════════════════════════════
    # مساعدات ستايل
    # ══════════════════════════════════════════════════════

    @staticmethod
    def _combo_style(border: str) -> str:
        return f"""
            QComboBox {{
                background:white; border:1px solid {border};
                border-radius:5px; padding:2px 8px; font-size:12px;
            }}
            QComboBox:focus {{ border-color:#6a1b9a; }}
            QComboBox::drop-down {{ border:none; }}
        """

    @staticmethod
    def _btn_style(bg: str, hover: str) -> str:
        return f"""
            QPushButton {{
                background:{bg}; color:white; border:none;
                border-radius:5px; padding:0 16px; font-weight:bold;
            }}
            QPushButton:hover {{ background:{hover}; }}
        """

    @staticmethod
    def _group_style(color: str) -> str:
        return f"""
            QGroupBox {{
                font-weight:bold; color:{color};
                border:1px solid #e0e0e0; border-radius:8px;
                margin-top:8px; padding-top:8px; background:white;
            }}
            QGroupBox::title {{
                subcontrol-origin:margin; padding:0 6px;
            }}
        """