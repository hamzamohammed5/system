"""
ui/tabs/companies/shared_items_manager.py  (نسخة مكتملة)
============================================================
SharedItemsManagerDialog — نافذة إدارة العناصر المشتركة بين الشركات.

الوظائف:
  1. عرض كل العناصر المشتركة مجمّعة بالنوع
  2. إضافة عنصر مشترك جديد (خامة / ماكينة / عملية عمالة / عملية تشغيل)
  3. تعديل بيانات عنصر مشترك (يتعكس فوراً على كل الشركات)
  4. ربط / فك ربط شركات بالعنصر
  5. حذف عنصر مشترك

الاستخدام:
  dlg = SharedItemsManagerDialog(central_conn, parent=self)
  dlg.items_changed.connect(lambda: bus.data_changed.emit())
  dlg.exec_()
"""

import json
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QComboBox, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QFrame, QGroupBox, QFormLayout,
    QDoubleSpinBox, QCheckBox, QMessageBox, QScrollArea,
    QWidget, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui  import QColor, QFont, QBrush

# ── ثوابت ──
SHARED_TYPES = {
    "raw":        ("🧱", "خامات"),
    "machine":    ("⚙️", "ماكينات"),
    "labor_op":   ("👷", "عمليات عمالة"),
    "machine_op": ("🔩", "عمليات تشغيل"),
}

_ACCENT  = "#1565c0"
_GREEN   = "#2e7d32"
_ORANGE  = "#e65100"
_PURPLE  = "#6a1b9a"
_BG      = "#f5f7fa"
_WHITE   = "#ffffff"
_BORDER  = "#e0e0e0"

_BTN_SS  = """
    QPushButton {
        border-radius: 6px; padding: 4px 14px;
        font-size: 11px; font-weight: bold;
        min-height: 30px;
    }
"""
_BTN_PRIMARY = _BTN_SS + f"""
    QPushButton {{ background: {_ACCENT}; color: white; border: none; }}
    QPushButton:hover {{ background: #1976d2; }}
    QPushButton:disabled {{ background: #90a4ae; }}
"""
_BTN_SUCCESS = _BTN_SS + f"""
    QPushButton {{ background: {_GREEN}; color: white; border: none; }}
    QPushButton:hover {{ background: #388e3c; }}
"""
_BTN_DANGER = _BTN_SS + f"""
    QPushButton {{ background: #f5f5f5; color: #c62828; border: 1px solid #ef9a9a; }}
    QPushButton:hover {{ background: #ffebee; }}
"""
_BTN_GHOST = _BTN_SS + f"""
    QPushButton {{ background: transparent; color: #555; border: 1px solid {_BORDER}; }}
    QPushButton:hover {{ background: #f5f5f5; }}
"""


def _decode(data_str: str) -> dict:
    try:
        return json.loads(data_str) if data_str else {}
    except Exception:
        return {}


def _encode(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False)


# ══════════════════════════════════════════════════════════
# SharedItemsManagerDialog
# ══════════════════════════════════════════════════════════

class SharedItemsManagerDialog(QDialog):
    items_changed = pyqtSignal()

    def __init__(self, central_conn, parent=None):
        super().__init__(parent)
        self.conn = central_conn
        self._current_item_id = None
        self._current_type    = "raw"

        self.setWindowTitle("🔗  إدارة العناصر المشتركة بين الشركات")
        self.setMinimumSize(1000, 680)
        self.setModal(True)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(f"QDialog {{ background: {_BG}; }}")
        self._build()
        self._load_companies()
        self._load_items()

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        body = QSplitter(Qt.Horizontal)
        body.setStyleSheet("QSplitter::handle { background: #ddd; width: 1px; }")

        # ── يمين: قائمة العناصر ──
        left_panel = self._build_list_panel()
        body.addWidget(left_panel)

        # ── يسار: تفاصيل ──
        right_panel = self._build_detail_panel()
        body.addWidget(right_panel)

        body.setSizes([420, 560])
        root.addWidget(body, stretch=1)
        root.addWidget(self._build_footer())

    def _build_header(self) -> QFrame:
        hdr = QFrame()
        hdr.setFixedHeight(64)
        hdr.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #1565c0, stop:1 #283593);
                border-bottom: 2px solid #0d47a1;
            }}
        """)
        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(20, 0, 20, 0)

        lbl_icon = QLabel("🔗")
        lbl_icon.setStyleSheet("font-size:28px; background:transparent; border:none;")

        lbl_title = QLabel("العناصر المشتركة بين الشركات")
        lbl_title.setStyleSheet(
            "font-size:16px; font-weight:bold; color:white;"
            "background:transparent; border:none;"
        )
        lbl_sub = QLabel("أي تعديل هنا يتعكس فوراً على كل الشركات المشتركة")
        lbl_sub.setStyleSheet(
            "font-size:10px; color:#90caf9; background:transparent; border:none;"
        )

        txt_lay = QVBoxLayout()
        txt_lay.setSpacing(2)
        txt_lay.addWidget(lbl_title)
        txt_lay.addWidget(lbl_sub)

        lay.addWidget(lbl_icon)
        lay.addSpacing(10)
        lay.addLayout(txt_lay)
        lay.addStretch()
        return hdr

    def _build_list_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(f"background: {_WHITE};")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet(f"""
            QFrame {{ background: #f8f9fb;
            border-bottom: 1px solid {_BORDER}; }}
        """)
        tb_lay = QVBoxLayout(toolbar)
        tb_lay.setContentsMargins(12, 10, 12, 10)
        tb_lay.setSpacing(8)

        # فلتر النوع
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("النوع:"))
        self.cmb_type = QComboBox()
        self.cmb_type.setMinimumHeight(30)
        for key, (icon, label) in SHARED_TYPES.items():
            self.cmb_type.addItem(f"{icon} {label}", key)
        self.cmb_type.currentIndexChanged.connect(self._on_type_changed)
        type_row.addWidget(self.cmb_type, stretch=1)
        tb_lay.addLayout(type_row)

        # بحث
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 بحث بالاسم...")
        self.inp_search.setMinimumHeight(30)
        self.inp_search.textChanged.connect(self._filter_list)
        tb_lay.addWidget(self.inp_search)

        # زر إضافة
        btn_add = QPushButton("➕  إضافة عنصر مشترك جديد")
        btn_add.setStyleSheet(_BTN_SUCCESS)
        btn_add.clicked.connect(self._add_new)
        tb_lay.addWidget(btn_add)

        lay.addWidget(toolbar)

        # الجدول
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(3)
        self.items_table.setHorizontalHeaderLabels(["الاسم", "الشركات", "تاريخ التحديث"])
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.items_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setShowGrid(False)
        self.items_table.setStyleSheet("""
            QTableWidget {
                border: none; font-size: 12px;
                alternate-background-color: #f8f9fb;
            }
            QTableWidget::item { padding: 6px 8px; }
            QTableWidget::item:selected {
                background: #e3f2fd; color: #1565c0;
            }
        """)
        hh = self.items_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.Fixed)
        hh.setSectionResizeMode(2, QHeaderView.Fixed)
        self.items_table.setColumnWidth(1, 70)
        self.items_table.setColumnWidth(2, 100)
        self.items_table.itemSelectionChanged.connect(self._on_item_selected)

        lay.addWidget(self.items_table, stretch=1)
        return panel

    def _build_detail_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(f"background: {_BG};")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        # ── placeholder ──
        self._placeholder = QLabel("اختر عنصراً من القائمة لعرض تفاصيله")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setStyleSheet(
            "color: #9e9e9e; font-size: 13px; "
            "background: white; border: 1px dashed #ddd; "
            "border-radius: 8px; padding: 40px;"
        )
        lay.addWidget(self._placeholder)

        # ── منطقة التفاصيل (مخفية في البداية) ──
        self._detail_widget = QWidget()
        self._detail_widget.setVisible(False)
        detail_lay = QVBoxLayout(self._detail_widget)
        detail_lay.setContentsMargins(0, 0, 0, 0)
        detail_lay.setSpacing(12)

        # رأس العنصر
        self._lbl_item_name = QLabel()
        self._lbl_item_name.setStyleSheet(
            f"font-size:15px; font-weight:bold; color:{_ACCENT};"
            "background:white; border:1px solid #bbdefb; border-radius:8px; padding:10px 16px;"
        )
        detail_lay.addWidget(self._lbl_item_name)

        # ── بيانات العنصر ──
        self._data_grp = QGroupBox("📊  البيانات")
        self._data_grp.setStyleSheet("""
            QGroupBox {
                background: white; border: 1px solid #e0e0e0;
                border-radius: 8px; font-weight: bold; color: #1565c0;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top right;
                padding: 0 8px;
            }
        """)
        self._data_form = QFormLayout(self._data_grp)
        self._data_form.setSpacing(10)
        self._data_form.setLabelAlignment(Qt.AlignRight)
        detail_lay.addWidget(self._data_grp)

        # حقول البيانات (تتغير حسب النوع)
        self._inp_name    = QLineEdit()
        self._inp_name.setMinimumHeight(32)
        self._sp_price    = QDoubleSpinBox(); self._sp_price.setRange(0, 9999999); self._sp_price.setDecimals(4); self._sp_price.setMinimumHeight(32)
        self._sp_total_qty = QDoubleSpinBox(); self._sp_total_qty.setRange(0, 9999999); self._sp_total_qty.setDecimals(4); self._sp_total_qty.setMinimumHeight(32)
        self._sp_rate_hour = QDoubleSpinBox(); self._sp_rate_hour.setRange(0, 9999999); self._sp_rate_hour.setDecimals(4); self._sp_rate_hour.setMinimumHeight(32)
        self._sp_rate_unit = QDoubleSpinBox(); self._sp_rate_unit.setRange(0, 9999999); self._sp_rate_unit.setDecimals(4); self._sp_rate_unit.setMinimumHeight(32)
        self._sp_minutes   = QDoubleSpinBox(); self._sp_minutes.setRange(0, 9999999); self._sp_minutes.setDecimals(2); self._sp_minutes.setMinimumHeight(32)
        self._cmb_mode     = QComboBox(); self._cmb_mode.addItem("بالوقت", "time"); self._cmb_mode.addItem("بالوحدة", "unit"); self._cmb_mode.setMinimumHeight(32)
        self._sp_op_value  = QDoubleSpinBox(); self._sp_op_value.setRange(0, 9999999); self._sp_op_value.setDecimals(4); self._sp_op_value.setMinimumHeight(32)
        self._inp_machine_name = QLineEdit(); self._inp_machine_name.setMinimumHeight(32)

        _input_ss = f"""
            QLineEdit, QDoubleSpinBox, QComboBox {{
                background: white; border: 1px solid #ddd;
                border-radius: 5px; padding: 3px 8px;
            }}
            QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus {{
                border-color: {_ACCENT};
            }}
        """
        for w in [self._inp_name, self._sp_price, self._sp_total_qty,
                  self._sp_rate_hour, self._sp_rate_unit, self._sp_minutes,
                  self._cmb_mode, self._sp_op_value, self._inp_machine_name]:
            w.setStyleSheet(_input_ss)

        # زر الحفظ
        self.btn_save_data = QPushButton("💾  حفظ التعديلات")
        self.btn_save_data.setStyleSheet(_BTN_PRIMARY)
        self.btn_save_data.clicked.connect(self._save_item_data)
        detail_lay.addWidget(self.btn_save_data)

        # ── الشركات المشتركة ──
        companies_grp = QGroupBox("🏢  الشركات المشتركة")
        companies_grp.setStyleSheet(self._data_grp.styleSheet())
        c_lay = QVBoxLayout(companies_grp)
        c_lay.setSpacing(8)

        self._companies_scroll = QScrollArea()
        self._companies_scroll.setWidgetResizable(True)
        self._companies_scroll.setMaximumHeight(200)
        self._companies_scroll.setStyleSheet("QScrollArea { border: none; }")
        self._companies_content = QWidget()
        self._companies_layout  = QVBoxLayout(self._companies_content)
        self._companies_layout.setSpacing(4)
        self._companies_layout.addStretch()
        self._companies_scroll.setWidget(self._companies_content)
        c_lay.addWidget(self._companies_scroll)

        self.btn_save_links = QPushButton("💾  حفظ ربط الشركات")
        self.btn_save_links.setStyleSheet(_BTN_PRIMARY)
        self.btn_save_links.clicked.connect(self._save_company_links)
        c_lay.addWidget(self.btn_save_links)

        detail_lay.addWidget(companies_grp)

        # زر الحذف
        btn_delete = QPushButton("🗑  حذف هذا العنصر المشترك")
        btn_delete.setStyleSheet(_BTN_DANGER)
        btn_delete.clicked.connect(self._delete_item)
        detail_lay.addWidget(btn_delete)

        detail_lay.addStretch()
        lay.addWidget(self._detail_widget, stretch=1)
        return panel

    def _build_footer(self) -> QFrame:
        footer = QFrame()
        footer.setFixedHeight(52)
        footer.setStyleSheet(f"""
            QFrame {{
                background: white;
                border-top: 1px solid {_BORDER};
            }}
        """)
        lay = QHBoxLayout(footer)
        lay.setContentsMargins(20, 0, 20, 0)

        lbl_info = QLabel("💡  التعديلات تتعكس فوراً على الشركات المشتركة — مفيش حاجة تعمل Sync يدوي")
        lbl_info.setStyleSheet("color: #555; font-size: 11px;")

        btn_close = QPushButton("✖  إغلاق")
        btn_close.setStyleSheet(_BTN_GHOST)
        btn_close.clicked.connect(self.accept)

        lay.addWidget(lbl_info)
        lay.addStretch()
        lay.addWidget(btn_close)
        return footer

    # ══════════════════════════════════════════════════════
    # تحميل البيانات
    # ══════════════════════════════════════════════════════

    def _load_companies(self):
        """يحمّل كل الشركات."""
        try:
            self._all_companies = self.conn.execute(
                "SELECT id, name, color FROM companies WHERE is_active=1 ORDER BY name"
            ).fetchall()
        except Exception:
            self._all_companies = []

    def _load_items(self):
        """يحمّل العناصر المشتركة حسب النوع الحالي."""
        stype = self.cmb_type.currentData() or "raw"
        self._current_type = stype
        q = self.inp_search.text().strip().lower()

        try:
            rows = self.conn.execute(
                "SELECT s.id, s.name, s.data, s.updated_at, "
                "COUNT(lnk.company_id) as company_count "
                "FROM shared_items s "
                "LEFT JOIN company_shared_links lnk ON lnk.shared_item_id = s.id "
                "WHERE s.shared_type = ? "
                "GROUP BY s.id ORDER BY s.name",
                (stype,)
            ).fetchall()
        except Exception:
            rows = []

        self.items_table.setRowCount(0)
        for row in rows:
            if q and q not in row["name"].lower():
                continue
            r = self.items_table.rowCount()
            self.items_table.insertRow(r)
            self.items_table.setRowHeight(r, 36)

            name_item = QTableWidgetItem(f"🔗  {row['name']}")
            name_item.setData(Qt.UserRole, row["id"])
            name_item.setFont(QFont("", -1, QFont.Medium))
            self.items_table.setItem(r, 0, name_item)

            cnt_item = QTableWidgetItem(str(row["company_count"]))
            cnt_item.setTextAlignment(Qt.AlignCenter)
            cnt_item.setForeground(QColor(_ACCENT))
            self.items_table.setItem(r, 1, cnt_item)

            date_str = (row["updated_at"] or "")[:10]
            date_item = QTableWidgetItem(date_str)
            date_item.setTextAlignment(Qt.AlignCenter)
            date_item.setForeground(QColor("#9e9e9e"))
            self.items_table.setItem(r, 2, date_item)

        if rows:
            self.items_table.selectRow(0)

    def _filter_list(self):
        self._load_items()

    def _on_type_changed(self):
        self._current_item_id = None
        self._show_placeholder()
        self._load_items()

    # ══════════════════════════════════════════════════════
    # اختيار عنصر
    # ══════════════════════════════════════════════════════

    def _on_item_selected(self):
        rows = self.items_table.selectedItems()
        if not rows:
            self._show_placeholder()
            return
        item_id = self.items_table.item(self.items_table.currentRow(), 0).data(Qt.UserRole)
        if item_id is None:
            return
        self._current_item_id = item_id
        self._load_detail(item_id)

    def _load_detail(self, item_id: int):
        try:
            row = self.conn.execute(
                "SELECT id, name, shared_type, data, updated_at FROM shared_items WHERE id=?",
                (item_id,)
            ).fetchone()
        except Exception:
            return
        if not row:
            return

        stype = row["shared_type"]
        data  = _decode(row["data"])

        # رأس
        icon = SHARED_TYPES.get(stype, ("🔗", ""))[0]
        self._lbl_item_name.setText(f"{icon}  {row['name']}")

        # مسح الـ form
        while self._data_form.rowCount():
            self._data_form.removeRow(0)

        # اسم دايماً
        self._inp_name.setText(row["name"])
        self._data_form.addRow("الاسم:", self._inp_name)

        # حقول حسب النوع
        if stype == "raw":
            self._sp_price.setValue(float(data.get("price", 0.0)))
            self._sp_total_qty.setValue(float(data.get("total_qty") or 0.0))
            self._data_form.addRow("السعر (جنيه):", self._sp_price)
            self._data_form.addRow("الكمية الكلية:", self._sp_total_qty)

        elif stype == "machine":
            self._sp_rate_hour.setValue(float(data.get("rate_per_hour", 0.0)))
            self._sp_rate_unit.setValue(float(data.get("rate_per_unit", 0.0)))
            self._data_form.addRow("معدل الساعة:", self._sp_rate_hour)
            self._data_form.addRow("معدل الوحدة:", self._sp_rate_unit)

        elif stype == "labor_op":
            self._sp_minutes.setValue(float(data.get("minutes", 0.0)))
            self._data_form.addRow("الوقت (دقيقة):", self._sp_minutes)

        elif stype == "machine_op":
            mode_idx = 0 if data.get("mode", "time") == "time" else 1
            self._cmb_mode.setCurrentIndex(mode_idx)
            self._sp_op_value.setValue(float(data.get("value", 0.0)))
            self._inp_machine_name.setText(data.get("machine_name", ""))
            self._sp_rate_hour.setValue(float(data.get("rate_per_hour", 0.0)))
            self._sp_rate_unit.setValue(float(data.get("rate_per_unit", 0.0)))
            self._data_form.addRow("وضع الحساب:", self._cmb_mode)
            self._data_form.addRow("القيمة:", self._sp_op_value)
            self._data_form.addRow("اسم الماكينة:", self._inp_machine_name)
            self._data_form.addRow("معدل الساعة:", self._sp_rate_hour)
            self._data_form.addRow("معدل الوحدة:", self._sp_rate_unit)

        # ربط الشركات
        self._load_company_checkboxes(item_id)

        self._placeholder.setVisible(False)
        self._detail_widget.setVisible(True)

    def _load_company_checkboxes(self, item_id: int):
        """يملأ checkboxes الشركات."""
        # احذف القديم
        while self._companies_layout.count() > 1:
            item = self._companies_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        try:
            linked_ids = {
                row["company_id"]
                for row in self.conn.execute(
                    "SELECT company_id FROM company_shared_links WHERE shared_item_id=?",
                    (item_id,)
                ).fetchall()
            }
        except Exception:
            linked_ids = set()

        self._company_checkboxes = {}
        for comp in self._all_companies:
            chk = QCheckBox(comp["name"])
            chk.setChecked(comp["id"] in linked_ids)
            chk.setStyleSheet(f"""
                QCheckBox {{ font-size: 12px; padding: 4px; }}
                QCheckBox::indicator:checked {{
                    background: {_GREEN}; border: 1px solid {_GREEN};
                    border-radius: 3px;
                }}
            """)
            # نقطة ملونة بلون الشركة
            color = comp["color"] or "#607d8b"
            chk.setStyleSheet(chk.styleSheet() +
                f"QCheckBox {{ color: {color}; }}"
            )
            self._company_checkboxes[comp["id"]] = chk
            self._companies_layout.insertWidget(
                self._companies_layout.count() - 1, chk
            )

    def _show_placeholder(self):
        self._placeholder.setVisible(True)
        self._detail_widget.setVisible(False)
        self._current_item_id = None

    # ══════════════════════════════════════════════════════
    # إضافة عنصر جديد
    # ══════════════════════════════════════════════════════

    def _add_new(self):
        stype = self.cmb_type.currentData() or "raw"
        icon, label = SHARED_TYPES.get(stype, ("🔗", "عنصر"))
        dlg = _AddSharedItemDialog(stype, label, parent=self)
        if dlg.exec_() != QDialog.Accepted:
            return
        name, data = dlg.get_result()
        if not name:
            return
        try:
            cur = self.conn.execute(
                "INSERT INTO shared_items (name, shared_type, data) VALUES (?, ?, ?)",
                (name, stype, _encode(data))
            )
            self.conn.commit()
            new_id = cur.lastrowid
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))
            return

        self._load_items()
        # اختر العنصر الجديد
        for r in range(self.items_table.rowCount()):
            if self.items_table.item(r, 0).data(Qt.UserRole) == new_id:
                self.items_table.selectRow(r)
                break
        self.items_changed.emit()

    # ══════════════════════════════════════════════════════
    # حفظ بيانات العنصر
    # ══════════════════════════════════════════════════════

    def _save_item_data(self):
        if not self._current_item_id:
            return
        stype = self._current_type
        name  = self._inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم العنصر")
            return

        data = {}
        if stype == "raw":
            data["price"]     = self._sp_price.value()
            data["total_qty"] = self._sp_total_qty.value() or None
        elif stype == "machine":
            data["rate_per_hour"] = self._sp_rate_hour.value()
            data["rate_per_unit"] = self._sp_rate_unit.value()
        elif stype == "labor_op":
            data["minutes"] = self._sp_minutes.value()
        elif stype == "machine_op":
            data["mode"]          = self._cmb_mode.currentData()
            data["value"]         = self._sp_op_value.value()
            data["machine_name"]  = self._inp_machine_name.text().strip()
            data["rate_per_hour"] = self._sp_rate_hour.value()
            data["rate_per_unit"] = self._sp_rate_unit.value()

        try:
            self.conn.execute(
                "UPDATE shared_items SET name=?, data=?, updated_at=datetime('now') WHERE id=?",
                (name, _encode(data), self._current_item_id)
            )
            self.conn.commit()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))
            return

        self._lbl_item_name.setText(
            f"{SHARED_TYPES.get(stype, ('🔗',''))[0]}  {name}"
        )
        self._load_items()
        self.items_changed.emit()

        # رسالة تأكيد خضراء مؤقتة
        self.btn_save_data.setText("✅  تم الحفظ — يتعكس فوراً على كل الشركات")
        self.btn_save_data.setStyleSheet(_BTN_SS + "QPushButton { background:#2e7d32; color:white; border:none; }")
        QTimer.singleShot(2500, lambda: (
            self.btn_save_data.setText("💾  حفظ التعديلات"),
            self.btn_save_data.setStyleSheet(_BTN_PRIMARY)
        ))

    # ══════════════════════════════════════════════════════
    # حفظ ربط الشركات
    # ══════════════════════════════════════════════════════

    def _save_company_links(self):
        if not self._current_item_id:
            return
        selected_ids = [
            cid for cid, chk in self._company_checkboxes.items()
            if chk.isChecked()
        ]
        try:
            self.conn.execute(
                "DELETE FROM company_shared_links WHERE shared_item_id=?",
                (self._current_item_id,)
            )
            for cid in selected_ids:
                self.conn.execute(
                    "INSERT OR IGNORE INTO company_shared_links (shared_item_id, company_id) VALUES (?, ?)",
                    (self._current_item_id, cid)
                )
            self.conn.commit()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))
            return

        self._load_items()
        self.items_changed.emit()

        self.btn_save_links.setText("✅  تم حفظ الربط")
        self.btn_save_links.setStyleSheet(_BTN_SS + "QPushButton { background:#2e7d32; color:white; border:none; }")
        QTimer.singleShot(2000, lambda: (
            self.btn_save_links.setText("💾  حفظ ربط الشركات"),
            self.btn_save_links.setStyleSheet(_BTN_PRIMARY)
        ))

    # ══════════════════════════════════════════════════════
    # حذف عنصر
    # ══════════════════════════════════════════════════════

    def _delete_item(self):
        if not self._current_item_id:
            return
        name = self._inp_name.text()
        if QMessageBox.question(
            self, "تأكيد الحذف",
            f"حذف العنصر المشترك «{name}»؟\n"
            "سيختفي من كل الشركات المشتركة فيه.",
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return
        try:
            self.conn.execute("DELETE FROM shared_items WHERE id=?", (self._current_item_id,))
            self.conn.commit()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))
            return

        self._show_placeholder()
        self._load_items()
        self.items_changed.emit()


# ══════════════════════════════════════════════════════════
# Dialog إضافة عنصر جديد
# ══════════════════════════════════════════════════════════

class _AddSharedItemDialog(QDialog):
    def __init__(self, stype: str, type_label: str, parent=None):
        super().__init__(parent)
        self.stype = stype
        self.setWindowTitle(f"➕  إضافة {type_label} مشترك")
        self.setMinimumWidth(400)
        self.setModal(True)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        _ss = """
            QLineEdit, QDoubleSpinBox, QComboBox {
                background: white; border: 1px solid #ddd;
                border-radius: 5px; padding: 4px 8px; min-height: 32px;
            }
        """
        self.setStyleSheet(_ss)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم العنصر...")
        form.addRow("الاسم *:", self.inp_name)

        # حقول حسب النوع
        self._extra_widgets = {}
        if self.stype == "raw":
            sp = QDoubleSpinBox(); sp.setRange(0, 9999999); sp.setDecimals(4)
            form.addRow("السعر (جنيه):", sp)
            self._extra_widgets["price"] = sp

            sp2 = QDoubleSpinBox(); sp2.setRange(0, 9999999); sp2.setDecimals(4)
            form.addRow("الكمية الكلية (اختياري):", sp2)
            self._extra_widgets["total_qty"] = sp2

        elif self.stype == "machine":
            sp1 = QDoubleSpinBox(); sp1.setRange(0, 9999999); sp1.setDecimals(4)
            sp2 = QDoubleSpinBox(); sp2.setRange(0, 9999999); sp2.setDecimals(4)
            form.addRow("معدل الساعة:", sp1)
            form.addRow("معدل الوحدة:", sp2)
            self._extra_widgets["rate_per_hour"] = sp1
            self._extra_widgets["rate_per_unit"] = sp2

        elif self.stype == "labor_op":
            sp = QDoubleSpinBox(); sp.setRange(0, 9999999); sp.setDecimals(2)
            form.addRow("الوقت (دقيقة):", sp)
            self._extra_widgets["minutes"] = sp

        elif self.stype == "machine_op":
            cmb = QComboBox()
            cmb.addItem("بالوقت", "time"); cmb.addItem("بالوحدة", "unit")
            sp1 = QDoubleSpinBox(); sp1.setRange(0, 9999999); sp1.setDecimals(4)
            inp = QLineEdit(); inp.setPlaceholderText("اسم الماكينة...")
            sp2 = QDoubleSpinBox(); sp2.setRange(0, 9999999); sp2.setDecimals(4)
            sp3 = QDoubleSpinBox(); sp3.setRange(0, 9999999); sp3.setDecimals(4)
            form.addRow("وضع الحساب:", cmb)
            form.addRow("القيمة:", sp1)
            form.addRow("اسم الماكينة:", inp)
            form.addRow("معدل الساعة:", sp2)
            form.addRow("معدل الوحدة:", sp3)
            self._extra_widgets["mode"] = cmb
            self._extra_widgets["value"] = sp1
            self._extra_widgets["machine_name"] = inp
            self._extra_widgets["rate_per_hour"] = sp2
            self._extra_widgets["rate_per_unit"] = sp3

        lay.addLayout(form)

        btns = QHBoxLayout()
        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setStyleSheet(_BTN_GHOST)
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("➕  إضافة")
        btn_ok.setStyleSheet(_BTN_SUCCESS)
        btn_ok.clicked.connect(self._ok)

        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok, stretch=1)
        lay.addLayout(btns)

    def _ok(self):
        if not self.inp_name.text().strip():
            QMessageBox.warning(self, "تنبيه", "أدخل اسم العنصر")
            return
        self.accept()

    def get_result(self) -> tuple:
        name = self.inp_name.text().strip()
        data = {}
        for key, widget in self._extra_widgets.items():
            if isinstance(widget, QDoubleSpinBox):
                data[key] = widget.value()
            elif isinstance(widget, QComboBox):
                data[key] = widget.currentData()
            elif isinstance(widget, QLineEdit):
                data[key] = widget.text().strip()
        return name, data