"""
ui/tabs/design/compare_tab.py
==============================
تبويب الجدول المقارن — يعرض الأشكال في جدول ديناميكي
حيث كل عمود = حقل مقاس، وكل صف = شكل.

الفلاتر:
  - مجموعة المقاسات (أعمدة الجدول تتغير معها)
  - التصنيف
  - بحث نصي

ميزات إضافية:
  - تعديل قيمة مقاس مباشرة من الجدول (double-click)
  - تصدير الجدول كـ CSV
"""

import csv
import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QInputDialog,
    QFileDialog, QFrame,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui  import QColor, QFont, QBrush

from db.design.design_repo import (
    fetch_all_dimension_sets,
    fetch_all_design_categories,
    fetch_shapes_with_dimensions,
    save_shape_dimensions,
    fetch_fields_for_set,
)
from ui.events import bus


class CompareTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn         = conn
        self._fields      = []    # حقول المجموعة الحالية
        self._shape_data  = []    # بيانات الأشكال المحملة
        self._build()
        self._load_filter_combos()
        self._load_table()
        bus.data_changed.connect(self._on_data_changed)

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

        # ── شريط الفلاتر ──
        filter_frame = QFrame()
        filter_frame.setStyleSheet("""
            QFrame {
                background: #e3f2fd;
                border: 1px solid #90caf9;
                border-radius: 8px;
            }
        """)
        filter_lay = QHBoxLayout(filter_frame)
        filter_lay.setContentsMargins(12, 8, 12, 8)
        filter_lay.setSpacing(12)

        # مجموعة المقاسات
        lbl_set = QLabel("📏 مجموعة المقاسات:")
        lbl_set.setStyleSheet(
            "font-weight:bold; font-size:11px; color:#1565c0;"
            "background:transparent; border:none;"
        )
        self.cmb_set = QComboBox()
        self.cmb_set.setMinimumHeight(30)
        self.cmb_set.setMinimumWidth(200)
        self.cmb_set.setStyleSheet(self._combo_style("#90caf9"))
        self.cmb_set.currentIndexChanged.connect(self._on_set_changed)

        # التصنيف
        lbl_cat = QLabel("🏷 التصنيف:")
        lbl_cat.setStyleSheet(
            "font-weight:bold; font-size:11px; color:#6a1b9a;"
            "background:transparent; border:none;"
        )
        self.cmb_cat = QComboBox()
        self.cmb_cat.setMinimumHeight(30)
        self.cmb_cat.setMinimumWidth(160)
        self.cmb_cat.setStyleSheet(self._combo_style("#ce93d8"))
        self.cmb_cat.currentIndexChanged.connect(self._load_table)

        # بحث
        lbl_search = QLabel("🔍")
        lbl_search.setStyleSheet("background:transparent; border:none; font-size:13px;")
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("بحث بالاسم...")
        self.inp_search.setMinimumHeight(30)
        self.inp_search.setMinimumWidth(160)
        self.inp_search.setStyleSheet("""
            QLineEdit {
                background:white; border:1px solid #90caf9;
                border-radius:4px; padding:2px 8px; font-size:12px;
            }
            QLineEdit:focus { border-color:#1565c0; }
        """)
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(250)
        self._search_timer.timeout.connect(self._load_table)
        self.inp_search.textChanged.connect(lambda: self._search_timer.start())

        # زر مسح
        btn_reset = QPushButton("↺ مسح")
        btn_reset.setMinimumHeight(28)
        btn_reset.setStyleSheet("""
            QPushButton { background:#e8eaf6; color:#3949ab;
                border:1px solid #c5cae9; border-radius:4px; padding:0 10px; }
            QPushButton:hover { background:#c5cae9; }
        """)
        btn_reset.clicked.connect(self._reset_filters)

        # زر تصدير
        btn_export = QPushButton("📤 تصدير CSV")
        btn_export.setMinimumHeight(28)
        btn_export.setStyleSheet("""
            QPushButton { background:#e8f5e9; color:#2e7d32;
                border:1px solid #a5d6a7; border-radius:4px;
                padding:0 12px; font-weight:bold; }
            QPushButton:hover { background:#c8e6c9; }
        """)
        btn_export.clicked.connect(self._export_csv)

        self.lbl_count = QLabel()
        self.lbl_count.setStyleSheet(
            "color:#1565c0; font-weight:bold; font-size:11px;"
            "background:transparent; border:none;"
        )

        filter_lay.addWidget(lbl_set)
        filter_lay.addWidget(self.cmb_set)
        filter_lay.addWidget(lbl_cat)
        filter_lay.addWidget(self.cmb_cat)
        filter_lay.addWidget(lbl_search)
        filter_lay.addWidget(self.inp_search)
        filter_lay.addWidget(btn_reset)
        filter_lay.addStretch()
        filter_lay.addWidget(self.lbl_count)
        filter_lay.addWidget(btn_export)
        lay.addWidget(filter_frame)

        # ── تلميح التعديل ──
        hint = QLabel(
            "💡 انقر مرتين على خلية مقاس لتعديل قيمتها مباشرة  │  "
            "الصف يُحفظ تلقائياً عند الانتهاء من التعديل"
        )
        hint.setStyleSheet(
            "font-size:10px; color:#e65100; background:#fff8e1;"
            "border:1px solid #ffe082; border-radius:4px; padding:4px 8px;"
        )
        lay.addWidget(hint)

        # ── الجدول ──
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.cellDoubleClicked.connect(self._on_cell_double_click)

        lay.addWidget(self.table, stretch=1)

        # ── إحصائيات سريعة ──
        self._stats_frame = QFrame()
        self._stats_frame.setStyleSheet("""
            QFrame {
                background: #f9f9f9;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
            }
        """)
        self._stats_lay = QHBoxLayout(self._stats_frame)
        self._stats_lay.setContentsMargins(12, 6, 12, 6)
        self._stats_lay.setSpacing(20)
        self._stats_frame.setFixedHeight(42)
        lay.addWidget(self._stats_frame)

    # ══════════════════════════════════════════════════════
    # تحميل الفلاتر
    # ══════════════════════════════════════════════════════

    def _load_filter_combos(self):
        # مجموعات المقاسات
        prev_set = self.cmb_set.currentData()
        self.cmb_set.blockSignals(True)
        self.cmb_set.clear()
        self.cmb_set.addItem("— كل المجموعات —", None)
        for ds in fetch_all_dimension_sets(self.conn):
            self.cmb_set.addItem(f"📏 {ds['name']}  ({ds['unit']})", ds["id"])
        # استعادة
        for i in range(self.cmb_set.count()):
            if self.cmb_set.itemData(i) == prev_set:
                self.cmb_set.setCurrentIndex(i)
                break
        self.cmb_set.blockSignals(False)

        # تصنيفات
        prev_cat = self.cmb_cat.currentData()
        self.cmb_cat.blockSignals(True)
        self.cmb_cat.clear()
        self.cmb_cat.addItem("— كل التصنيفات —", None)
        for c in fetch_all_design_categories(self.conn):
            self.cmb_cat.addItem(f"{c['icon']}  {c['name']}", c["id"])
        for i in range(self.cmb_cat.count()):
            if self.cmb_cat.itemData(i) == prev_cat:
                self.cmb_cat.setCurrentIndex(i)
                break
        self.cmb_cat.blockSignals(False)

    # ══════════════════════════════════════════════════════
    # تحميل الجدول
    # ══════════════════════════════════════════════════════

    def _on_set_changed(self):
        set_id = self.cmb_set.currentData()
        if set_id:
            self._fields = [dict(f) for f in fetch_fields_for_set(self.conn, set_id)]
        else:
            self._fields = []
        self._load_table()

    def _load_table(self):
        set_id = self.cmb_set.currentData()
        cat_id = self.cmb_cat.currentData()
        query  = self.inp_search.text().strip().lower()

        # جلب البيانات
        if set_id:
            shapes = fetch_shapes_with_dimensions(self.conn, set_id, cat_id)
        else:
            # بدون تحديد مجموعة — اعرض كل الأشكال بدون أعمدة مقاسات
            from db.design.design_repo import fetch_all_shapes
            raw = fetch_all_shapes(self.conn, category_id=cat_id)
            shapes = []
            for s in raw:
                d = dict(s)
                d["_fields"] = []
                d["_dims"]   = {}
                shapes.append(d)

        # فلتر البحث
        if query:
            shapes = [
                s for s in shapes
                if query in (s["name"] or "").lower()
                or query in (s.get("material") or "").lower()
                or query in (s.get("category_name") or "").lower()
            ]

        self._shape_data = shapes

        # بناء الأعمدة
        fixed_cols  = ["#", "الاسم", "التصنيف", "المادة"]
        field_labels = [f["label"] for f in self._fields]
        all_cols     = fixed_cols + field_labels

        self.table.blockSignals(True)
        self.table.setColumnCount(len(all_cols))
        self.table.setHorizontalHeaderLabels(all_cols)
        self.table.setRowCount(0)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 40)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        for i in range(2, len(fixed_cols)):
            hh.setSectionResizeMode(i, QHeaderView.Interactive)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 100)
        for i in range(len(fixed_cols), len(all_cols)):
            hh.setSectionResizeMode(i, QHeaderView.Interactive)
            self.table.setColumnWidth(i, 80)
        hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # ملء الصفوف
        for idx, shape in enumerate(shapes):
            r = self.table.rowCount()
            self.table.insertRow(r)

            # #
            num_item = QTableWidgetItem(str(idx + 1))
            num_item.setTextAlignment(Qt.AlignCenter)
            num_item.setFlags(num_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(r, 0, num_item)

            # الاسم
            name_item = QTableWidgetItem(shape["name"])
            name_item.setFont(QFont("", -1, QFont.Bold))
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            # لون التصنيف
            if shape.get("category_color"):
                name_item.setForeground(QColor(shape["category_color"]))
            self.table.setItem(r, 1, name_item)

            # التصنيف
            cat_text = ""
            if shape.get("category_name"):
                cat_text = f"{shape.get('category_icon','') or ''}  {shape['category_name']}"
            cat_item = QTableWidgetItem(cat_text)
            cat_item.setFlags(cat_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(r, 2, cat_item)

            # المادة
            mat_item = QTableWidgetItem(shape.get("material") or "—")
            mat_item.setFlags(mat_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(r, 3, mat_item)

            # حقول المقاسات
            dims = shape.get("_dims", {})
            for fi, field in enumerate(self._fields):
                col = len(fixed_cols) + fi
                fid = field["id"]
                val = dims.get(fid, "")
                cell = QTableWidgetItem(str(val) if val is not None else "")
                cell.setData(Qt.UserRole, (shape["id"], fid))  # shape_id, field_id
                if not val:
                    cell.setBackground(QBrush(QColor("#fff8e1")))
                    cell.setForeground(QColor("#bbb"))
                    cell.setText("—")
                self.table.setItem(r, col, cell)

        self.table.blockSignals(False)
        self.lbl_count.setText(f"({len(shapes)} شكل)")
        self._update_stats(shapes)

    def _update_stats(self, shapes: list):
        # مسح الإحصائيات القديمة
        while self._stats_lay.count():
            item = self._stats_lay.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        total = len(shapes)
        # عدد الأشكال التي لها قيم مقاسات ناقصة
        missing = sum(
            1 for s in shapes
            if any(
                not s.get("_dims", {}).get(f["id"])
                for f in self._fields
            )
        ) if self._fields else 0

        stats = [
            ("📐 إجمالي الأشكال", str(total), "#1565c0"),
            ("⚠️ مقاسات ناقصة", str(missing), "#e65100" if missing else "#2e7d32"),
        ]

        # إضافة عدد الحقول
        if self._fields:
            stats.append(("📋 الحقول", str(len(self._fields)), "#6a1b9a"))

        for title, value, color in stats:
            frame = QFrame()
            frame.setStyleSheet("QFrame{background:transparent; border:none;}")
            fl = QHBoxLayout(frame)
            fl.setContentsMargins(0, 0, 0, 0)
            fl.setSpacing(6)
            lbl_t = QLabel(title)
            lbl_t.setStyleSheet(f"color:#888; font-size:10px; background:transparent; border:none;")
            lbl_v = QLabel(value)
            lbl_v.setStyleSheet(
                f"font-weight:bold; font-size:13px; color:{color};"
                "background:transparent; border:none;"
            )
            fl.addWidget(lbl_t)
            fl.addWidget(lbl_v)
            self._stats_lay.addWidget(frame)

        self._stats_lay.addStretch()

    # ══════════════════════════════════════════════════════
    # تعديل مباشر
    # ══════════════════════════════════════════════════════

    def _on_cell_double_click(self, row: int, col: int):
        item = self.table.item(row, col)
        if not item:
            return
        data = item.data(Qt.UserRole)
        if not data:
            return  # عمود ثابت

        shape_id, field_id = data
        field = next((f for f in self._fields if f["id"] == field_id), None)
        if not field:
            return

        current_val = item.text() if item.text() != "—" else ""
        label = field["label"]
        unit  = field.get("unit") or ""

        new_val, ok = QInputDialog.getText(
            self,
            f"تعديل: {label}",
            f"{label}  {'(' + unit + ')' if unit else ''}  :",
            text=current_val
        )
        if not ok:
            return

        new_val = new_val.strip()
        # حفظ في DB
        save_shape_dimensions(self.conn, shape_id, {field_id: new_val})

        # تحديث الخلية مباشرة
        item.setText(new_val if new_val else "—")
        if new_val:
            item.setBackground(QBrush(QColor("#ffffff")))
            item.setForeground(QColor("#212121"))
        else:
            item.setBackground(QBrush(QColor("#fff8e1")))
            item.setForeground(QColor("#bbb"))

        # تحديث _shape_data
        for s in self._shape_data:
            if s["id"] == shape_id:
                s["_dims"][field_id] = new_val
                break

        self._update_stats(self._shape_data)

    # ══════════════════════════════════════════════════════
    # تصدير CSV
    # ══════════════════════════════════════════════════════

    def _export_csv(self):
        if self.table.rowCount() == 0:
            QMessageBox.information(self, "تنبيه", "لا توجد بيانات للتصدير")
            return

        default_name = f"designs_compare_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self, "حفظ كـ CSV", default_name, "CSV Files (*.csv)"
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                # header
                headers = [
                    self.table.horizontalHeaderItem(c).text()
                    for c in range(self.table.columnCount())
                ]
                writer.writerow(headers)
                # rows
                for r in range(self.table.rowCount()):
                    row_data = []
                    for c in range(self.table.columnCount()):
                        item = self.table.item(r, c)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)

            QMessageBox.information(
                self, "تم التصدير",
                f"✅ تم حفظ الجدول في:\n{path}"
            )
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل التصدير:\n{e}")

    # ══════════════════════════════════════════════════════
    # مساعدات
    # ══════════════════════════════════════════════════════

    def _reset_filters(self):
        self.cmb_set.setCurrentIndex(0)
        self.cmb_cat.setCurrentIndex(0)
        self.inp_search.clear()

    def _on_data_changed(self):
        self._load_filter_combos()
        self._on_set_changed()

    @staticmethod
    def _combo_style(border_color: str) -> str:
        return f"""
            QComboBox {{
                background:white; border:1px solid {border_color};
                border-radius:4px; padding:2px 8px; font-size:12px;
            }}
            QComboBox:focus {{ border-color:#1565c0; }}
            QComboBox::drop-down {{ border:none; }}
        """