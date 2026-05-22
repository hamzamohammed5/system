"""
ui/tabs/companies/shared_items_manager.py
==========================================
نافذة إدارة العناصر المشتركة بين الشركات.

الوظائف:
  - إنشاء عنصر مشترك جديد (خامة / ماكينة / عملية عمالة / عملية تشغيل)
  - تعديل بيانات العنصر — يتعكس على كل الشركات فوراً
  - تحديد الشركات المشتركة في كل عنصر (checkbox لكل شركة)
  - حذف العنصر المشترك أو فك ربط شركة
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QWidget, QLabel, QPushButton, QLineEdit,
    QComboBox, QDoubleSpinBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QScrollArea, QMessageBox, QGroupBox,
    QFormLayout, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui  import QColor

from db.companies.shared_items_repo import (
    create_shared_items_tables,
    fetch_all_shared_items,
    fetch_shared_item,
    insert_shared_item,
    update_shared_item,
    delete_shared_item,
    fetch_linked_companies,
    fetch_shared_items_for_company,
    set_linked_companies,
    get_item_data,
)
from db.companies.companies_repo import fetch_all_companies


_TYPE_AR = {
    "raw":        "خامة",
    "machine":    "ماكينة",
    "labor_op":   "عملية عمالة",
    "machine_op": "عملية تشغيل",
}

_TYPE_ICON = {
    "raw":        "📦",
    "machine":    "🖥️",
    "labor_op":   "👷",
    "machine_op": "⚙️",
}

_C = {
    "accent":       "#1565c0",
    "accent_hover": "#0d47a1",
    "accent_light": "#e3f2fd",
    "bg":           "#f5f7fa",
    "bg_surface":   "#ffffff",
    "bg_input":     "#ffffff",
    "border":       "#e0e0e0",
    "border_med":   "#bdbdbd",
    "text":         "#212121",
    "text_sec":     "#616161",
    "text_muted":   "#9e9e9e",
    "shared_bg":    "#e8f5e9",
    "shared_color": "#2e7d52",
    "danger":       "#c62828",
    "danger_light": "#ffebee",
}


class SharedItemsManagerDialog(QDialog):
    """نافذة إدارة العناصر المشتركة."""

    items_changed = pyqtSignal()  # يُطلق عند أي تغيير

    def __init__(self, central_conn, parent=None):
        super().__init__(parent)
        self._conn      = central_conn
        self._editing_id = None
        self._all_companies = []

        create_shared_items_tables(self._conn)

        self.setWindowTitle("🔗  إدارة العناصر المشتركة")
        self.setMinimumSize(1000, 680)
        self.setModal(True)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build()
        self._load_companies()
        self._load_items()

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        # ── العنوان ──
        title_row = QHBoxLayout()
        title = QLabel("🔗  العناصر المشتركة بين الشركات")
        title.setStyleSheet(
            f"font-size:15pt; font-weight:bold; color:{_C['accent']};"
        )
        title_row.addWidget(title)
        title_row.addStretch()

        hint = QLabel("أي تعديل في عنصر مشترك يظهر فوراً في كل الشركات المرتبطة به")
        hint.setStyleSheet(
            f"font-size:10pt; color:{_C['shared_color']};"
            f"background:{_C['shared_bg']}; border-radius:5px; padding:4px 10px;"
        )
        title_row.addWidget(hint)
        root.addLayout(title_row)

        # ── المحتوى الرئيسي ──
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)
        splitter.addWidget(self._build_list_panel())
        splitter.addWidget(self._build_form_panel())
        splitter.setSizes([520, 440])
        root.addWidget(splitter, stretch=1)

        # ── زر الإغلاق ──
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("✖  إغلاق")
        close_btn.setFixedHeight(34)
        close_btn.setStyleSheet(self._btn_style(_C['border_med'], "#eee"))
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)

    def _build_list_panel(self) -> QWidget:
        panel = QWidget()
        lay   = QVBoxLayout(panel)
        lay.setContentsMargins(0, 0, 6, 0)
        lay.setSpacing(6)

        # ── شريط الأدوات ──
        toolbar = QHBoxLayout()
        lbl = QLabel("العناصر المشتركة")
        lbl.setStyleSheet("font-weight:bold; font-size:11pt;")
        toolbar.addWidget(lbl)
        toolbar.addStretch()

        add_btn = QPushButton("➕  عنصر جديد")
        add_btn.setFixedHeight(32)
        add_btn.setStyleSheet(self._btn_style(_C['accent'], _C['accent_hover'], white=True))
        add_btn.clicked.connect(self._new_item)
        toolbar.addWidget(add_btn)
        lay.addLayout(toolbar)

        # ── فلتر النوع ──
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("النوع:"))
        self._type_filter = QComboBox()
        self._type_filter.setFixedHeight(28)
        self._type_filter.addItem("الكل", userData=None)
        for key, ar in _TYPE_AR.items():
            self._type_filter.addItem(f"{_TYPE_ICON[key]}  {ar}", userData=key)
        self._type_filter.currentIndexChanged.connect(self._load_items)
        filter_row.addWidget(self._type_filter)
        filter_row.addStretch()
        lay.addLayout(filter_row)

        # ── الجدول ──
        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["", "الاسم", "النوع", "الشركات"])
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Fixed)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._table.setColumnWidth(0, 32)
        self._table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {_C['border']};
                border-radius: 6px;
                background: {_C['bg_surface']};
                alternate-background-color: {_C['bg']};
            }}
            QTableWidget::item {{ padding: 5px 8px; border:none; }}
            QTableWidget::item:selected {{
                background: {_C['accent_light']};
                color: {_C['accent']};
            }}
            QHeaderView::section {{
                background: {_C['bg']}; padding: 6px 8px;
                border: none; border-bottom: 2px solid {_C['border_med']};
                font-weight:600; color:{_C['text_sec']};
            }}
        """)
        self._table.itemSelectionChanged.connect(self._on_select)
        lay.addWidget(self._table)

        # ── أزرار الحذف ──
        del_btn = QPushButton("🗑️  حذف المحدد")
        del_btn.setFixedHeight(30)
        del_btn.setStyleSheet(self._btn_style(_C['danger_light'], "#ffcdd2"))
        del_btn.clicked.connect(self._delete_item)
        lay.addWidget(del_btn)

        return panel

    def _build_form_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(f"""
            QWidget {{
                background: {_C['bg_surface']};
                border: 1px solid {_C['border']};
                border-radius: 8px;
            }}
        """)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        self._form_title = QLabel("✨  عنصر جديد")
        self._form_title.setStyleSheet(
            "font-weight:bold; font-size:12pt; background:transparent;"
        )
        lay.addWidget(self._form_title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background:{_C['border']}; border:none;")
        sep.setFixedHeight(1)
        lay.addWidget(sep)

        # ── نوع العنصر ──
        lay.addWidget(self._lbl("نوع العنصر:"))
        self._type_combo = QComboBox()
        self._type_combo.setFixedHeight(32)
        for key, ar in _TYPE_AR.items():
            self._type_combo.addItem(f"{_TYPE_ICON[key]}  {ar}", userData=key)
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)
        lay.addWidget(self._type_combo)

        # ── الاسم ──
        lay.addWidget(self._lbl("الاسم:"))
        self._inp_name = QLineEdit()
        self._inp_name.setFixedHeight(32)
        self._inp_name.setPlaceholderText("اسم العنصر المشترك...")
        self._inp_name.setStyleSheet(self._inp_style())
        lay.addWidget(self._inp_name)

        # ── حقول البيانات (تتغير حسب النوع) ──
        self._data_widget = QWidget()
        self._data_widget.setStyleSheet("background:transparent;")
        self._data_layout = QVBoxLayout(self._data_widget)
        self._data_layout.setContentsMargins(0, 0, 0, 0)
        self._data_layout.setSpacing(6)
        lay.addWidget(self._data_widget)

        # ── الشركات ──
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"background:{_C['border']}; border:none;")
        sep2.setFixedHeight(1)
        lay.addWidget(sep2)

        companies_lbl = QLabel("الشركات المشتركة:")
        companies_lbl.setStyleSheet(
            f"font-weight:bold; font-size:10pt; background:transparent;"
        )
        lay.addWidget(companies_lbl)

        hint2 = QLabel("✔ اختر الشركات اللي تشارك في هذا العنصر")
        hint2.setStyleSheet(
            f"font-size:9pt; color:{_C['text_muted']}; background:transparent;"
        )
        lay.addWidget(hint2)

        # Scroll area للشركات
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(140)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {_C['border']};
                border-radius:5px; background:{_C['bg']};
            }}
        """)
        self._companies_widget = QWidget()
        self._companies_widget.setStyleSheet("background:transparent;")
        self._companies_layout = QVBoxLayout(self._companies_widget)
        self._companies_layout.setContentsMargins(8, 6, 8, 6)
        self._companies_layout.setSpacing(4)
        scroll.setWidget(self._companies_widget)
        lay.addWidget(scroll)

        lay.addStretch()

        # ── أزرار الحفظ ──
        btn_row = QHBoxLayout()
        self._save_btn = QPushButton("💾  حفظ")
        self._save_btn.setFixedHeight(36)
        self._save_btn.setStyleSheet(
            self._btn_style(_C['accent'], _C['accent_hover'], white=True)
        )
        self._save_btn.clicked.connect(self._save)

        self._cancel_btn = QPushButton("✖  إلغاء")
        self._cancel_btn.setFixedHeight(36)
        self._cancel_btn.setStyleSheet(self._btn_style(_C['border_med'], "#eee"))
        self._cancel_btn.clicked.connect(self._reset_form)

        btn_row.addWidget(self._save_btn)
        btn_row.addWidget(self._cancel_btn)
        lay.addLayout(btn_row)

        # بناء الحقول الأولية
        self._rebuild_data_fields()

        return panel

    # ══════════════════════════════════════════════════════
    # حقول البيانات الديناميكية
    # ══════════════════════════════════════════════════════

    def _on_type_changed(self, _=None):
        self._rebuild_data_fields()

    def _rebuild_data_fields(self):
        # تنظيف الحقول القديمة
        while self._data_layout.count():
            item = self._data_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._data_fields = {}
        t = self._type_combo.currentData()

        def _add_spin(key, label, unit="", max_=999999, dec=2):
            row = QHBoxLayout()
            row.addWidget(self._lbl(label + ":"))
            sp = QDoubleSpinBox()
            sp.setRange(0, max_)
            sp.setDecimals(dec)
            sp.setFixedHeight(30)
            sp.setFixedWidth(130)
            sp.setStyleSheet(self._inp_style())
            if unit:
                row.addWidget(sp)
                row.addWidget(self._lbl(unit))
                row.addStretch()
            else:
                row.addWidget(sp)
                row.addStretch()
            w = QWidget()
            w.setStyleSheet("background:transparent;")
            w.setLayout(row)
            self._data_layout.addWidget(w)
            self._data_fields[key] = sp

        if t == "raw":
            _add_spin("price",     "السعر الكلي",        "جنيه")
            _add_spin("total_qty", "الكمية الإجمالية",   "وحدة")

        elif t == "machine":
            _add_spin("rate_per_hour", "معدل التشغيل / ساعة", "جنيه/ساعة")
            _add_spin("rate_per_unit", "معدل التشغيل / وحدة", "جنيه/وحدة")

        elif t == "labor_op":
            _add_spin("minutes", "الوقت", "دقيقة")

        elif t == "machine_op":
            # وضع الحساب
            row_mode = QHBoxLayout()
            row_mode.addWidget(self._lbl("وضع الحساب:"))
            mode_combo = QComboBox()
            mode_combo.setFixedHeight(30)
            mode_combo.addItem("⏱ بالوقت", userData="time")
            mode_combo.addItem("📦 بالوحدة", userData="unit")
            row_mode.addWidget(mode_combo)
            row_mode.addStretch()
            w_mode = QWidget()
            w_mode.setStyleSheet("background:transparent;")
            w_mode.setLayout(row_mode)
            self._data_layout.addWidget(w_mode)
            self._data_fields["mode_combo"] = mode_combo

            _add_spin("value", "القيمة")

            # اسم الماكينة
            row_m = QHBoxLayout()
            row_m.addWidget(self._lbl("اسم الماكينة:"))
            inp_m = QLineEdit()
            inp_m.setFixedHeight(30)
            inp_m.setStyleSheet(self._inp_style())
            row_m.addWidget(inp_m)
            w_m = QWidget()
            w_m.setStyleSheet("background:transparent;")
            w_m.setLayout(row_m)
            self._data_layout.addWidget(w_m)
            self._data_fields["machine_name"] = inp_m

    def _fill_data_fields(self, data: dict):
        for key, widget in self._data_fields.items():
            if key == "mode_combo":
                mode = data.get("mode", "time")
                for i in range(widget.count()):
                    if widget.itemData(i) == mode:
                        widget.setCurrentIndex(i)
                        break
            elif key == "machine_name":
                widget.setText(data.get("machine_name", ""))
            elif isinstance(widget, QDoubleSpinBox):
                val = data.get(key)
                widget.setValue(float(val) if val is not None else 0.0)

    def _collect_data_fields(self) -> dict:
        t = self._type_combo.currentData()
        d = {}
        for key, widget in self._data_fields.items():
            if key == "mode_combo":
                d["mode"] = widget.currentData()
            elif key == "machine_name":
                d["machine_name"] = widget.text().strip()
            elif isinstance(widget, QDoubleSpinBox):
                val = widget.value()
                # total_qty: لو 0 يبقى None
                if key == "total_qty" and val == 0:
                    d[key] = None
                else:
                    d[key] = val
        return d

    # ══════════════════════════════════════════════════════
    # checkboxes الشركات
    # ══════════════════════════════════════════════════════

    def _load_companies(self):
        self._all_companies = list(fetch_all_companies(self._conn))

    def _rebuild_company_checkboxes(self, linked_ids: set = None):
        while self._companies_layout.count():
            item = self._companies_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._company_checkboxes = {}
        linked_ids = linked_ids or set()

        if not self._all_companies:
            lbl = QLabel("لا توجد شركات مسجلة")
            lbl.setStyleSheet(f"color:{_C['text_muted']}; background:transparent;")
            self._companies_layout.addWidget(lbl)
            return

        for c in self._all_companies:
            cb = QCheckBox(f"  {c['name']}")
            cb.setChecked(c["id"] in linked_ids)
            cb.setStyleSheet(f"""
                QCheckBox {{
                    font-size: 10pt;
                    background: transparent;
                    padding: 2px 4px;
                }}
                QCheckBox::indicator {{
                    width: 16px; height: 16px;
                    border: 2px solid {_C['border_med']};
                    border-radius: 3px;
                    background: white;
                }}
                QCheckBox::indicator:checked {{
                    background: {_C['accent']};
                    border-color: {_C['accent']};
                    image: none;
                }}
                QCheckBox:hover {{ background: {_C['accent_light']}; border-radius:4px; }}
            """)
            self._companies_layout.addWidget(cb)
            self._company_checkboxes[c["id"]] = cb

        self._companies_layout.addStretch()

    def _get_checked_companies(self) -> list[int]:
        return [cid for cid, cb in self._company_checkboxes.items() if cb.isChecked()]

    # ══════════════════════════════════════════════════════
    # تحميل الجدول
    # ══════════════════════════════════════════════════════

    def _load_items(self):
        filter_type = self._type_filter.currentData()
        rows = fetch_all_shared_items(self._conn, shared_type=filter_type)

        self._table.setRowCount(0)
        for row in rows:
            ri = self._table.rowCount()
            self._table.insertRow(ri)

            # أيقونة النوع
            ico = QTableWidgetItem(_TYPE_ICON.get(row["shared_type"], ""))
            ico.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(ri, 0, ico)

            # الاسم
            name_item = QTableWidgetItem(row["name"])
            name_item.setData(Qt.UserRole, row["id"])
            self._table.setItem(ri, 1, name_item)

            # النوع
            type_item = QTableWidgetItem(_TYPE_AR.get(row["shared_type"], row["shared_type"]))
            type_item.setForeground(QColor(_C['text_sec']))
            self._table.setItem(ri, 2, type_item)

            # عدد الشركات
            linked = fetch_linked_companies(self._conn, row["id"])
            count_item = QTableWidgetItem(f"🏢 {len(linked)}")
            count_item.setTextAlignment(Qt.AlignCenter)
            if len(linked) > 0:
                count_item.setForeground(QColor(_C['shared_color']))
            self._table.setItem(ri, 3, count_item)

            self._table.setRowHeight(ri, 36)

    # ══════════════════════════════════════════════════════
    # أحداث الجدول
    # ══════════════════════════════════════════════════════

    def _on_select(self):
        row = self._table.currentRow()
        if row == -1:
            return
        item_id = self._table.item(row, 1).data(Qt.UserRole)
        self._load_for_edit(item_id)

    def _selected_id(self):
        row = self._table.currentRow()
        if row == -1:
            return None
        return self._table.item(row, 1).data(Qt.UserRole)

    # ══════════════════════════════════════════════════════
    # CRUD
    # ══════════════════════════════════════════════════════

    def _new_item(self):
        self._editing_id = None
        self._form_title.setText("✨  عنصر جديد")
        self._inp_name.clear()
        self._type_combo.setEnabled(True)
        self._type_combo.setCurrentIndex(0)
        self._rebuild_data_fields()
        self._rebuild_company_checkboxes()
        self._inp_name.setFocus()

    def _load_for_edit(self, item_id: int):
        row = fetch_shared_item(self._conn, item_id)
        if not row:
            return
        self._editing_id = item_id
        self._form_title.setText(f"✏️  تعديل: {row['name']}")
        self._inp_name.setText(row["name"])

        # تعيين النوع
        self._type_combo.setEnabled(False)  # لا تغيير النوع بعد الإنشاء
        for i in range(self._type_combo.count()):
            if self._type_combo.itemData(i) == row["shared_type"]:
                self._type_combo.setCurrentIndex(i)
                break

        self._rebuild_data_fields()

        data = get_item_data(self._conn, item_id)
        self._fill_data_fields(data)

        # الشركات المرتبطة
        linked = fetch_linked_companies(self._conn, item_id)
        linked_ids = {r["id"] for r in linked}
        self._rebuild_company_checkboxes(linked_ids)

    def _save(self):
        name = self._inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم العنصر")
            return

        shared_type = self._type_combo.currentData()
        data        = self._collect_data_fields()
        company_ids = self._get_checked_companies()

        try:
            if self._editing_id is None:
                # إنشاء جديد
                new_id = insert_shared_item(self._conn, name, shared_type, data)
                set_linked_companies(self._conn, new_id, company_ids)
                msg = f"✅  تم إنشاء «{name}» وربطه بـ {len(company_ids)} شركة"
            else:
                # تعديل
                update_shared_item(self._conn, self._editing_id, name, data)
                set_linked_companies(self._conn, self._editing_id, company_ids)
                msg = f"✅  تم تحديث «{name}» — {len(company_ids)} شركة مشتركة"

            self._load_items()
            self.items_changed.emit()
            QMessageBox.information(self, "تم", msg)

        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _delete_item(self):
        item_id = self._selected_id()
        if item_id is None:
            QMessageBox.information(self, "تنبيه", "اختر عنصراً أولاً")
            return
        row = fetch_shared_item(self._conn, item_id)
        if not row:
            return
        linked = fetch_linked_companies(self._conn, item_id)
        msg = f"حذف «{row['name']}»؟"
        if linked:
            names = "، ".join(r["name"] for r in linked)
            msg += f"\n\nسيُزال من {len(linked)} شركة: {names}"

        if QMessageBox.question(self, "تأكيد الحذف", msg,
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            delete_shared_item(self._conn, item_id)
            self._reset_form()
            self._load_items()
            self.items_changed.emit()

    def _reset_form(self):
        self._editing_id = None
        self._form_title.setText("✨  عنصر جديد")
        self._inp_name.clear()
        self._type_combo.setEnabled(True)
        self._type_combo.setCurrentIndex(0)
        self._rebuild_data_fields()
        self._rebuild_company_checkboxes()
        self._table.clearSelection()

    # ══════════════════════════════════════════════════════
    # مساعدات الـ style
    # ══════════════════════════════════════════════════════

    def _lbl(self, text: str) -> QLabel:
        l = QLabel(text)
        l.setStyleSheet(
            f"font-size:10pt; color:{_C['text_sec']}; background:transparent;"
        )
        return l

    def _inp_style(self) -> str:
        return f"""
            QLineEdit, QDoubleSpinBox, QComboBox {{
                border: 1px solid {_C['border_med']};
                border-radius: 5px;
                padding: 2px 8px;
                background: {_C['bg_input']};
            }}
            QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus {{
                border-color: {_C['accent']};
            }}
        """

    def _btn_style(self, bg: str, hover: str, white: bool = False) -> str:
        color = "white" if white else _C['text']
        return f"""
            QPushButton {{
                background: {bg}; color: {color};
                font-weight: 600; border: none;
                border-radius: 5px; padding: 4px 16px;
            }}
            QPushButton:hover {{ background: {hover}; }}
        """