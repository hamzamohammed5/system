"""
ui/tabs/design/dimension_sets_tab.py
=====================================
تبويب إدارة مجموعات المقاسات.

[تحديثات]:
  1. _FieldDialog — مصدر الاعتمادية يشمل حقول من أي مجموعة (cross-set)
  2. _ValuesPanel  — لوحة جديدة لإدخال القيم مباشرة داخل تبويب المقاسات
     - يعرض حقول المجموعة المختارة مع خانات إدخال أرقام
     - يحسب الحقول المعتمدة تلقائياً مع إمكانية تعديل الناتج
     - الإدخال مستقل عن تبويب التصميمات
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QPushButton, QLabel, QLineEdit,
    QComboBox, QDoubleSpinBox, QCheckBox, QGroupBox,
    QFormLayout, QMessageBox, QColorDialog, QDialog,
    QDialogButtonBox, QTreeWidget, QTreeWidgetItem, QScrollArea,
    QSizePolicy, QFrame,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont

from db.designs.dimension_sets_repo import (
    fetch_all_design_categories, fetch_design_category,
    insert_design_category, update_design_category, delete_design_category,
    build_category_tree, fetch_category_descendants,
    fetch_all_dimension_sets, fetch_dimension_set,
    insert_dimension_set, update_dimension_set, delete_dimension_set,
    fetch_fields_for_set, fetch_field, fetch_all_fields_for_combo,
    insert_field, update_field, delete_field, reorder_fields,
    fetch_field_dep, set_field_dep, remove_field_dep,
    fetch_standalone_values, save_standalone_value,
    calc_standalone_cross_auto,
)
from ui.helpers import make_table, buttons_row, confirm_delete, danger_button


def _spin(min_=None, max_=9999, dec=2):
    s = QDoubleSpinBox()
    s.setRange(min_ if min_ is not None else -99999, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(30)
    return s


# ══════════════════════════════════════════════════════════
# محرر حقل واحد — Dialog (محدّث: cross-set deps)
# ══════════════════════════════════════════════════════════

class _FieldDialog(QDialog):
    """
    نافذة إضافة/تعديل حقل مقاسات.
    [تحديث]: مصدر الاعتمادية يمكن أن يكون من أي مجموعة مقاسات.
    """

    def __init__(self, conn, set_id: int,
                 field_data=None, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self.set_id    = set_id
        self.field_id  = field_data["id"] if field_data else None
        self.setWindowTitle("تعديل حقل" if field_data else "إضافة حقل جديد")
        self.setMinimumWidth(460)
        self.setModal(True)
        self._build()
        if field_data:
            self._load(field_data)

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.inp_name  = QLineEdit()
        self.inp_name.setPlaceholderText("مثال: length, width ...")
        self.inp_name.setMinimumHeight(30)

        self.inp_label = QLineEdit()
        self.inp_label.setPlaceholderText("مثال: الطول، العرض ...")
        self.inp_label.setMinimumHeight(30)

        self.inp_unit = QLineEdit()
        self.inp_unit.setPlaceholderText("cm / mm / m ...")
        self.inp_unit.setText("cm")
        self.inp_unit.setMinimumHeight(30)

        self.cmb_type = QComboBox()
        self.cmb_type.addItem("رقم", "number")
        self.cmb_type.addItem("نص", "text")
        self.cmb_type.setMinimumHeight(30)
        self.cmb_type.currentIndexChanged.connect(self._on_type_changed)

        self.chk_required = QCheckBox("حقل إلزامي")
        self.chk_required.setChecked(True)

        form.addRow("الاسم (إنجليزي) :", self.inp_name)
        form.addRow("التسمية (عربي) :",  self.inp_label)
        form.addRow("الوحدة :",           self.inp_unit)
        form.addRow("النوع :",            self.cmb_type)
        form.addRow("",                   self.chk_required)
        root.addLayout(form)

        # ── قسم الاعتمادية (cross-set) ──
        self._dep_grp = QGroupBox("اعتماد على حقل آخر (اختياري)")
        self._dep_grp.setCheckable(True)
        self._dep_grp.setChecked(False)
        dep_lay = QFormLayout(self._dep_grp)
        dep_lay.setSpacing(8)
        dep_lay.setLabelAlignment(Qt.AlignRight)

        # ── فلتر المجموعة ──
        self.cmb_source_set = QComboBox()
        self.cmb_source_set.setMinimumHeight(28)
        self.cmb_source_set.addItem("— كل المجموعات —", None)
        for ds in fetch_all_dimension_sets(self.conn):
            self.cmb_source_set.addItem(ds["name"], ds["id"])
        self.cmb_source_set.currentIndexChanged.connect(self._reload_source_fields)

        # ── الحقل المصدر ──
        self.cmb_source = QComboBox()
        self.cmb_source.setMinimumHeight(28)
        self.cmb_source.setMinimumWidth(200)

        self.sp_offset = _spin(min_=-9999, max_=9999, dec=4)
        self.sp_offset.setValue(0)

        dep_lay.addRow("فلتر المجموعة :", self.cmb_source_set)
        dep_lay.addRow("الحقل المصدر :",  self.cmb_source)
        dep_lay.addRow("الإضافة / الخصم :", self.sp_offset)

        hint = QLabel("القيمة = قيمة الحقل المصدر + الإضافة (ممكن سالب للخصم)")
        hint.setStyleSheet(
            "color:#1565c0; font-size:10px;"
            "background:#e8f0fe; border-radius:4px; padding:4px 8px;"
        )
        dep_lay.addRow(hint)

        cross_hint = QLabel("💡 يمكنك اختيار حقل من مجموعة مقاسات مختلفة تماماً")
        cross_hint.setStyleSheet(
            "color:#2e7d32; font-size:10px;"
            "background:#e8f5e9; border-radius:4px; padding:4px 8px;"
        )
        dep_lay.addRow(cross_hint)

        root.addWidget(self._dep_grp)

        # تحميل الحقول المتاحة
        self._all_source_fields = []
        self._reload_source_fields()

        # ── أزرار ──
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("💾  حفظ")
        btns.button(QDialogButtonBox.Cancel).setText("✖  إلغاء")
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    def _on_type_changed(self, idx):
        """اخفاء خيار الاعتمادية إذا النوع نصي."""
        is_number = self.cmb_type.currentData() == "number"
        self._dep_grp.setEnabled(is_number)
        if not is_number:
            self._dep_grp.setChecked(False)

    def _reload_source_fields(self):
        """تحميل الحقول المتاحة كمصدر مع فلتر المجموعة."""
        filter_set_id = self.cmb_source_set.currentData()

        # جلب كل الحقول الرقمية
        all_fields = fetch_all_fields_for_combo(
            self.conn,
            exclude_field_id=self.field_id
        )
        self._all_source_fields = all_fields

        prev_field_id = self.cmb_source.currentData()
        self.cmb_source.blockSignals(True)
        self.cmb_source.clear()

        # تجميع حسب المجموعة
        current_group = None
        for row in all_fields:
            if filter_set_id is not None and row["set_id"] != filter_set_id:
                continue

            # عنوان المجموعة (مرة واحدة لكل مجموعة)
            if row["set_id"] != current_group:
                current_group = row["set_id"]
                # نضيف عنوان المجموعة كـ separator
                self.cmb_source.addItem(f"── {row['set_name']} ──", -1)
                idx = self.cmb_source.count() - 1
                self.cmb_source.setItemData(idx, QColor("#78909c"), Qt.ForegroundRole)
                font = QFont()
                font.setBold(True)
                self.cmb_source.setItemData(idx, font, Qt.FontRole)
                model = self.cmb_source.model()
                item  = model.item(idx)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemIsEnabled & ~Qt.ItemIsSelectable)

            # الحقل
            # نمييز حقول نفس المجموعة بعلامة
            marker = "↩ " if row["set_id"] == self.set_id else "↗ "
            self.cmb_source.addItem(
                f"{marker}{row['field_label']}",
                (row["field_id"], row["set_id"])
            )

        self.cmb_source.blockSignals(False)

        # استعادة الاختيار السابق
        if prev_field_id is not None:
            for i in range(self.cmb_source.count()):
                d = self.cmb_source.itemData(i)
                if isinstance(d, tuple) and d[0] == prev_field_id[0]:
                    self.cmb_source.setCurrentIndex(i)
                    break

    def _load(self, field_data):
        self.inp_name.setText(field_data["name"])
        self.inp_label.setText(field_data["label"])
        self.inp_unit.setText(field_data["unit"] or "cm")
        idx = self.cmb_type.findData(field_data["field_type"])
        if idx >= 0:
            self.cmb_type.setCurrentIndex(idx)
        self.chk_required.setChecked(bool(field_data["required"]))

        # الاعتمادية
        if self.field_id:
            dep = fetch_field_dep(self.conn, self.field_id)
            if dep:
                self._dep_grp.setChecked(True)
                src_set_id = dep["source_set_id"]

                # فلتر المجموعة
                if src_set_id:
                    for i in range(self.cmb_source_set.count()):
                        if self.cmb_source_set.itemData(i) == src_set_id:
                            self.cmb_source_set.setCurrentIndex(i)
                            break
                    self._reload_source_fields()

                # الحقل المصدر
                for i in range(self.cmb_source.count()):
                    d = self.cmb_source.itemData(i)
                    if isinstance(d, tuple) and d[0] == dep["source_field_id"]:
                        self.cmb_source.setCurrentIndex(i)
                        break
                self.sp_offset.setValue(float(dep["offset"]))

    def _save(self):
        name  = self.inp_name.text().strip()
        label = self.inp_label.text().strip()
        if not name or not label:
            QMessageBox.warning(self, "تنبيه", "أدخل الاسم والتسمية")
            return

        unit       = self.inp_unit.text().strip() or "cm"
        ftype      = self.cmb_type.currentData()
        required   = self.chk_required.isChecked()
        sort_order = 0

        if self.field_id:
            f = fetch_field(self.conn, self.field_id)
            if f:
                sort_order = f["sort_order"]
            update_field(self.conn, self.field_id, name, label,
                         unit, ftype, required, sort_order)
        else:
            existing = fetch_fields_for_set(self.conn, self.set_id)
            sort_order = len(existing)
            self.field_id = insert_field(
                self.conn, self.set_id, name, label, unit, ftype, required, sort_order
            )

        # الاعتمادية
        if self._dep_grp.isChecked() and self._dep_grp.isEnabled():
            d = self.cmb_source.currentData()
            if isinstance(d, tuple):
                src_field_id, src_set_id = d
                # إذا نفس المجموعة → source_set_id = None
                actual_src_set = src_set_id if src_set_id != self.set_id else None
                set_field_dep(
                    self.conn, self.field_id, src_field_id,
                    self.sp_offset.value(), "",
                    source_set_id=actual_src_set
                )
        else:
            remove_field_dep(self.conn, self.field_id)

        self.accept()


# ══════════════════════════════════════════════════════════
# لوحة إدخال القيم المباشر — جديد
# ══════════════════════════════════════════════════════════

class _ValuesPanel(QWidget):
    """
    لوحة إدخال قيم المقاسات مباشرة على مجموعة محددة.

    المميزات:
      - يعرض كل حقول المجموعة المختارة
      - يقبل إدخال أرقام في كل حقل
      - الحقول المعتمدة على حقول أخرى → زر "⟳ حساب" يظهر الناتج
      - الناتج قابل للتعديل اليدوي
      - يحفظ القيم في dimension_set_values (مستقلة عن التصميمات)
    """

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn    = conn
        self._set_id = None
        self._spins  = {}       # field_id → QDoubleSpinBox
        self._auto_btns = {}    # field_id → QPushButton (حساب)
        self._auto_badges = {}  # field_id → QLabel (شارة "تلقائي")
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # ── رأس ──
        hdr = QLabel("📊  إدخال قيم المقاسات")
        hdr.setStyleSheet("""
            font-weight: bold;
            font-size: 13px;
            color: #1565c0;
            background: #e8f0fe;
            border-radius: 6px;
            padding: 6px 12px;
        """)
        root.addWidget(hdr)

        hint = QLabel("اختر مجموعة مقاسات من القائمة على اليسار لبدء الإدخال")
        hint.setStyleSheet("color: #888; font-size: 11px; padding: 4px;")
        hint.setAlignment(Qt.AlignCenter)
        root.addWidget(hint)

        # ── منطقة الحقول (scroll) ──
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setStyleSheet("""
            QScrollArea { border: 1px solid #e0e0e0; border-radius: 6px; background: white; }
            QScrollBar:vertical { background:#f5f5f5; width:8px; border-radius:4px; }
            QScrollBar::handle:vertical { background:#bdbdbd; border-radius:4px; min-height:30px; }
            QScrollBar::handle:vertical:hover { background:#9e9e9e; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0px; }
        """)
        self._fields_widget = QWidget()
        self._fields_widget.setStyleSheet("background: white;")
        self._fields_layout = QVBoxLayout(self._fields_widget)
        self._fields_layout.setSpacing(6)
        self._fields_layout.setContentsMargins(12, 12, 12, 12)
        self._fields_layout.addStretch()
        self._scroll_area.setWidget(self._fields_widget)
        root.addWidget(self._scroll_area, stretch=1)

        # ── أزرار أسفل ──
        btn_bar = QHBoxLayout()

        self.btn_save = QPushButton("💾  حفظ القيم")
        self.btn_save.setMinimumHeight(32)
        self.btn_save.setEnabled(False)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background: #1565c0; color: white;
                border: none; border-radius: 5px;
                padding: 4px 18px; font-weight: bold;
            }
            QPushButton:hover { background: #0d47a1; }
            QPushButton:disabled { background: #b0bec5; }
        """)
        self.btn_save.clicked.connect(self._save_values)

        self.btn_calc_all = QPushButton("⟳  حساب الكل التلقائي")
        self.btn_calc_all.setMinimumHeight(32)
        self.btn_calc_all.setEnabled(False)
        self.btn_calc_all.setStyleSheet("""
            QPushButton {
                background: #e8f5e9; color: #2e7d32;
                border: 1px solid #a5d6a7; border-radius: 5px;
                padding: 4px 14px;
            }
            QPushButton:hover { background: #c8e6c9; }
            QPushButton:disabled { background: #f5f5f5; color: #bbb; border-color: #ddd; }
        """)
        self.btn_calc_all.clicked.connect(self._calc_all_auto)

        self.btn_reset = QPushButton("↺  مسح القيم")
        self.btn_reset.setMinimumHeight(32)
        self.btn_reset.setEnabled(False)
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background: #fff3e0; color: #e65100;
                border: 1px solid #ffcc80; border-radius: 5px;
                padding: 4px 14px;
            }
            QPushButton:hover { background: #ffe0b2; }
            QPushButton:disabled { background: #f5f5f5; color: #bbb; border-color: #ddd; }
        """)
        self.btn_reset.clicked.connect(self._reset_values)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #2e7d32; font-size: 11px;")

        btn_bar.addWidget(self.btn_save)
        btn_bar.addWidget(self.btn_calc_all)
        btn_bar.addWidget(self.btn_reset)
        btn_bar.addStretch()
        btn_bar.addWidget(self.lbl_status)
        root.addLayout(btn_bar)

    def load_set(self, set_id: int):
        """تحميل حقول مجموعة وقيمها الحالية."""
        self._set_id = set_id
        self._spins  = {}
        self._auto_btns  = {}
        self._auto_badges = {}
        self._clear_fields()

        fields = fetch_fields_for_set(self.conn, set_id)
        if not fields:
            lbl = QLabel("هذه المجموعة ليس لها حقول بعد — أضف حقولاً من قسم 'حقول المجموعة'")
            lbl.setStyleSheet("color: #888; font-size: 11px; padding: 12px;")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setWordWrap(True)
            self._fields_layout.insertWidget(0, lbl)
            self._enable_buttons(False)
            return

        # جلب القيم المحفوظة
        saved = fetch_standalone_values(self.conn, set_id)

        has_auto = False
        for f in fields:
            if f["field_type"] != "number":
                continue  # نتخطى الحقول النصية في هذا الوضع

            row_w = self._build_field_row(f, saved.get(f["id"]))
            self._fields_layout.insertWidget(
                self._fields_layout.count() - 1, row_w
            )
            if f["source_field_id"]:
                has_auto = True

        self._enable_buttons(True, has_auto=has_auto)
        self.lbl_status.setText("")

    def _build_field_row(self, field_data, current_value) -> QWidget:
        """يبني صف إدخال لحقل واحد."""
        fid = field_data["id"]
        has_dep = bool(field_data["source_field_id"])

        row_w = QFrame()
        row_w.setStyleSheet("""
            QFrame {
                background: #fafafa;
                border: 1px solid #e8eaf6;
                border-radius: 6px;
            }
            QFrame:hover {
                border-color: #90caf9;
                background: #f3f8ff;
            }
        """)
        row_lay = QHBoxLayout(row_w)
        row_lay.setContentsMargins(10, 6, 10, 6)
        row_lay.setSpacing(8)

        # ── اسم الحقل ──
        lbl = QLabel(field_data["label"])
        lbl.setFixedWidth(110)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl.setStyleSheet("background: transparent; border: none; font-weight: bold; color: #333;")

        # ── خانة الإدخال ──
        spin = QDoubleSpinBox()
        spin.setRange(-99999, 99999)
        spin.setDecimals(4)
        spin.setMinimumHeight(30)
        spin.setMinimumWidth(120)
        spin.setStyleSheet("""
            QDoubleSpinBox {
                border: 1px solid #c5cae9;
                border-radius: 4px;
                padding: 2px 6px;
                background: white;
            }
            QDoubleSpinBox:focus { border-color: #1565c0; }
        """)
        if current_value is not None:
            spin.setValue(float(current_value))

        # ── وحدة ──
        unit_lbl = QLabel(field_data["unit"] or "cm")
        unit_lbl.setFixedWidth(35)
        unit_lbl.setStyleSheet("color: #888; background: transparent; border: none; font-size: 11px;")

        self._spins[fid] = spin

        row_lay.addWidget(lbl)
        row_lay.addWidget(spin, stretch=1)
        row_lay.addWidget(unit_lbl)

        # ── زر الحساب التلقائي (إذا كان الحقل معتمداً) ──
        if has_dep:
            src_info = ""
            if field_data["source_label"]:
                src_info = field_data["source_label"]
                if field_data.get("source_set_name"):
                    set_name = field_data["source_set_name"]
                    src_info = f"{src_info} ({set_name})"

            btn_auto = QPushButton("⟳")
            btn_auto.setFixedSize(30, 30)
            btn_auto.setToolTip(
                f"حساب تلقائي من: {src_info}\n"
                f"الناتج قابل للتعديل بعد الحساب"
            )
            btn_auto.setStyleSheet("""
                QPushButton {
                    background: #e8f5e9;
                    border: 1px solid #a5d6a7;
                    border-radius: 4px;
                    color: #2e7d32;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover { background: #c8e6c9; }
            """)
            btn_auto.clicked.connect(
                lambda _, fid_=fid, sp_=spin: self._calc_one_auto(fid_, sp_)
            )
            self._auto_btns[fid] = btn_auto

            # شارة "يعتمد على"
            dep_badge = QLabel("↗")
            dep_badge.setFixedSize(20, 20)
            dep_badge.setAlignment(Qt.AlignCenter)
            dep_badge.setStyleSheet("""
                background: #e8f5e9;
                border-radius: 3px;
                color: #2e7d32;
                font-size: 11px;
                border: none;
            """)
            dep_badge.setToolTip(f"يعتمد حسابه على: {src_info}")
            self._auto_badges[fid] = dep_badge

            row_lay.addWidget(dep_badge)
            row_lay.addWidget(btn_auto)
        else:
            spacer = QLabel("")
            spacer.setFixedWidth(58)
            spacer.setStyleSheet("background: transparent; border: none;")
            row_lay.addWidget(spacer)

        return row_w

    def _clear_fields(self):
        """مسح الحقول المعروضة."""
        while self._fields_layout.count() > 1:
            item = self._fields_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _enable_buttons(self, enabled: bool, has_auto: bool = False):
        self.btn_save.setEnabled(enabled)
        self.btn_calc_all.setEnabled(enabled and has_auto)
        self.btn_reset.setEnabled(enabled)

    def _calc_one_auto(self, field_id: int, spin: QDoubleSpinBox):
        """حساب قيمة حقل واحد تلقائياً."""
        if self._set_id is None:
            return
        # احفظ القيم الحالية أولاً عشان الحساب يستخدمها
        self._save_values(silent=True)
        val = calc_standalone_cross_auto(self.conn, field_id, self._set_id)
        if val is not None:
            spin.setValue(val)
            # ألوّن الخانة باللون الأخضر لحظة
            spin.setStyleSheet("""
                QDoubleSpinBox {
                    border: 2px solid #43a047;
                    border-radius: 4px;
                    padding: 2px 6px;
                    background: #f1f8e9;
                }
            """)
            self.lbl_status.setText(f"✓ تم حساب الحقل تلقائياً = {val:.4g}")
        else:
            QMessageBox.information(
                self, "تنبيه",
                "لا توجد قيمة للحقل المصدر بعد.\n"
                "أدخل قيمة الحقل المصدر أولاً ثم احسب."
            )

    def _calc_all_auto(self):
        """حساب كل الحقول ذات الاعتماديات."""
        if self._set_id is None:
            return
        self._save_values(silent=True)
        count = 0
        for fid, spin in self._spins.items():
            if fid in self._auto_btns:
                val = calc_standalone_cross_auto(self.conn, fid, self._set_id)
                if val is not None:
                    spin.setValue(val)
                    count += 1
        if count:
            self.lbl_status.setText(f"✓ تم حساب {count} حقل تلقائياً")
        else:
            self.lbl_status.setText("⚠ لا توجد قيم مصدر كافية للحساب")

    def _save_values(self, silent: bool = False):
        """حفظ القيم في قاعدة البيانات."""
        if self._set_id is None:
            return
        for fid, spin in self._spins.items():
            save_standalone_value(self.conn, self._set_id, fid, value_num=spin.value())
        if not silent:
            self.lbl_status.setText("✓ تم الحفظ")
            # إعادة ضبط ألوان الخانات
            for spin in self._spins.values():
                spin.setStyleSheet("""
                    QDoubleSpinBox {
                        border: 1px solid #c5cae9;
                        border-radius: 4px;
                        padding: 2px 6px;
                        background: white;
                    }
                    QDoubleSpinBox:focus { border-color: #1565c0; }
                """)

    def _reset_values(self):
        """مسح كل القيم المدخلة."""
        if self._set_id is None:
            return
        if QMessageBox.question(
            self, "تأكيد", "مسح كل القيم المدخلة؟",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            for spin in self._spins.values():
                spin.setValue(0.0)
            self.lbl_status.setText("↺ تم المسح")

    def clear(self):
        self._set_id = None
        self._spins  = {}
        self._clear_fields()
        self._enable_buttons(False)
        self.lbl_status.setText("")


# ══════════════════════════════════════════════════════════
# لوحة حقول المجموعة
# ══════════════════════════════════════════════════════════

class _FieldsPanel(QWidget):
    """محرر حقول مجموعة مقاسات."""

    fields_changed = pyqtSignal()
    set_selected   = pyqtSignal(int)   # يُرسل set_id للـ ValuesPanel

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn   = conn
        self._set_id = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        hdr = QLabel("حقول المجموعة")
        hdr.setStyleSheet("font-weight:bold; color:#1565c0; font-size:12px;")
        root.addWidget(hdr)

        self.table = make_table(
            ["الترتيب", "الاسم", "التسمية", "الوحدة", "النوع", "إلزامي", "يعتمد على"],
            stretch_col=2
        )
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 90)
        self.table.setColumnWidth(3, 60)
        self.table.setColumnWidth(4, 55)
        self.table.setColumnWidth(5, 55)
        self.table.setColumnWidth(6, 130)
        root.addWidget(self.table)

        btn_add  = QPushButton("➕  إضافة حقل")
        btn_edit = QPushButton("✏️  تعديل")
        btn_del  = danger_button("🗑️  حذف")
        btn_up   = QPushButton("▲")
        btn_dn   = QPushButton("▼")
        for btn in (btn_add, btn_edit, btn_del, btn_up, btn_dn):
            btn.setMinimumHeight(28)
        btn_up.setFixedWidth(34)
        btn_dn.setFixedWidth(34)

        btn_add.clicked.connect(self._add_field)
        btn_edit.clicked.connect(self._edit_field)
        btn_del.clicked.connect(self._del_field)
        btn_up.clicked.connect(self._move_up)
        btn_dn.clicked.connect(self._move_down)

        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_edit)
        btn_row.addWidget(btn_del)
        btn_row.addStretch()
        btn_row.addWidget(btn_up)
        btn_row.addWidget(btn_dn)
        root.addLayout(btn_row)

    def load_set(self, set_id: int):
        self._set_id = set_id
        self._refresh()
        self.set_selected.emit(set_id)

    def clear(self):
        self._set_id = None
        self.table.setRowCount(0)

    def _refresh(self):
        if self._set_id is None:
            self.table.setRowCount(0)
            return
        self.table.setRowCount(0)
        fields = fetch_fields_for_set(self.conn, self._set_id)
        for f in fields:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(f["sort_order"] + 1)))
            self.table.setItem(r, 1, QTableWidgetItem(f["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(f["label"]))
            self.table.setItem(r, 3, QTableWidgetItem(f["unit"] or "cm"))
            self.table.setItem(r, 4, QTableWidgetItem(
                "رقم" if f["field_type"] == "number" else "نص"
            ))
            self.table.setItem(r, 5, QTableWidgetItem("✓" if f["required"] else ""))

            # عرض الاعتمادية مع اسم المجموعة إن كانت cross-set
            dep_text = ""
            if f["source_field_id"]:
                sign = "+" if f["dep_offset"] >= 0 else ""
                src_label = f["source_label"] or ""
                src_set   = f.get("source_set_name") or ""
                if src_set:
                    dep_text = f"{src_label} ({src_set}) {sign}{f['dep_offset']:g}"
                else:
                    dep_text = f"{src_label} {sign}{f['dep_offset']:g}"
            self.table.setItem(r, 6, QTableWidgetItem(dep_text))
            self.table.item(r, 0).setData(Qt.UserRole, f["id"])

    def _selected_field_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _add_field(self):
        if self._set_id is None:
            QMessageBox.information(self, "تنبيه", "اختر مجموعة مقاسات أولاً")
            return
        dlg = _FieldDialog(self.conn, self._set_id, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._refresh()
            self.fields_changed.emit()

    def _edit_field(self):
        fid = self._selected_field_id()
        if fid is None:
            QMessageBox.information(self, "تنبيه", "اختر حقلاً أولاً")
            return
        f = fetch_field(self.conn, fid)
        dlg = _FieldDialog(self.conn, self._set_id, field_data=f, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._refresh()
            self.fields_changed.emit()

    def _del_field(self):
        fid = self._selected_field_id()
        if fid is None:
            QMessageBox.information(self, "تنبيه", "اختر حقلاً أولاً")
            return
        f = fetch_field(self.conn, fid)
        if f and confirm_delete(self, f["label"]):
            delete_field(self.conn, fid)
            self._refresh()
            self.fields_changed.emit()

    def _move_up(self):
        self._move(-1)

    def _move_down(self):
        self._move(1)

    def _move(self, direction: int):
        row = self.table.currentRow()
        new_row = row + direction
        if new_row < 0 or new_row >= self.table.rowCount():
            return
        ids = []
        for r in range(self.table.rowCount()):
            ids.append(self.table.item(r, 0).data(Qt.UserRole))
        ids[row], ids[new_row] = ids[new_row], ids[row]
        reorder_fields(self.conn, self._set_id, ids)
        self._refresh()
        self.table.selectRow(new_row)
        self.fields_changed.emit()


# ══════════════════════════════════════════════════════════
# لوحة مجموعات المقاسات
# ══════════════════════════════════════════════════════════

class _SetsPanel(QWidget):
    """قائمة مجموعات المقاسات + فورم الإضافة/التعديل."""

    set_selected = pyqtSignal(int)   # set_id

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._editing_id = None
        self._all_rows   = []
        self._build()
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        # ── فلتر ──
        filter_row = QHBoxLayout()
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 بحث...")
        self.inp_search.setMinimumHeight(28)
        self.inp_search.textChanged.connect(self._apply_filter)
        self.cmb_cat_filter = QComboBox()
        self.cmb_cat_filter.setMinimumHeight(28)
        self.cmb_cat_filter.setMinimumWidth(130)
        self.cmb_cat_filter.currentIndexChanged.connect(self._apply_filter)
        filter_row.addWidget(QLabel("🔍"))
        filter_row.addWidget(self.inp_search, stretch=1)
        filter_row.addWidget(QLabel("📁"))
        filter_row.addWidget(self.cmb_cat_filter)
        root.addLayout(filter_row)

        # ── جدول ──
        self.table = make_table(
            ["ID", "الاسم", "التصنيف", "الوحدة", "عدد الحقول"],
            stretch_col=1
        )
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 60)
        self.table.setColumnWidth(4, 70)
        self.table.itemSelectionChanged.connect(self._on_select)
        root.addWidget(self.table)

        # ── أزرار ──
        btn_edit = QPushButton("✏️  تعديل")
        btn_del  = danger_button("🗑️  حذف")
        for b in (btn_edit, btn_del):
            b.setMinimumHeight(28)
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        root.addLayout(buttons_row(btn_edit, btn_del))

        # ── فورم الإضافة/التعديل ──
        grp  = QGroupBox("بيانات المجموعة")
        form = QFormLayout(grp)
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = QLabel("─── مجموعة جديدة ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0;")
        form.addRow(self.lbl_mode)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("مثال: مقاسات الثوب, مقاسات البنطلون ...")
        self.inp_name.setMinimumHeight(30)

        self.cmb_category = QComboBox()
        self.cmb_category.setMinimumHeight(28)

        self.inp_unit = QLineEdit()
        self.inp_unit.setText("cm")
        self.inp_unit.setFixedWidth(80)
        self.inp_unit.setMinimumHeight(28)

        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("ملاحظات...")
        self.inp_notes.setMinimumHeight(28)

        form.addRow("الاسم :",        self.inp_name)
        form.addRow("التصنيف :",      self.cmb_category)
        form.addRow("الوحدة الافتراضية :", self.inp_unit)
        form.addRow("ملاحظات :",      self.inp_notes)

        self.btn_add    = QPushButton("➕  إضافة")
        self.btn_save   = QPushButton("💾  حفظ")
        self.btn_cancel = QPushButton("✖  إلغاء")
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        for b in (self.btn_add, self.btn_save, self.btn_cancel):
            b.setMinimumHeight(30)
        self.btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self._reset)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_cancel)
        form.addRow(btn_row)
        root.addWidget(grp)

        self._reload_categories()

    def _reload_categories(self):
        for combo in (self.cmb_category, self.cmb_cat_filter):
            prev = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            if combo is self.cmb_cat_filter:
                combo.addItem("— كل التصنيفات —", None)
            else:
                combo.addItem("— بدون تصنيف —", None)
            rows = fetch_all_design_categories(self.conn)
            tree = build_category_tree(rows)
            self._add_cat_nodes(combo, tree, 0)
            for i in range(combo.count()):
                if combo.itemData(i) == prev:
                    combo.setCurrentIndex(i)
                    break
            combo.blockSignals(False)

    def _add_cat_nodes(self, combo, nodes, depth):
        indent = "    " * depth
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            combo.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            if node["children"]:
                self._add_cat_nodes(combo, node["children"], depth + 1)

    def _load(self):
        self._all_rows = list(fetch_all_dimension_sets(self.conn))
        self._reload_categories()
        self._apply_filter()

    def _apply_filter(self):
        q      = self.inp_search.text().strip().lower()
        cat_id = self.cmb_cat_filter.currentData()
        prev   = self._selected_id()
        self.table.setRowCount(0)

        for ds in self._all_rows:
            if q and q not in ds["name"].lower():
                continue
            if cat_id is not None and ds["category_id"] != cat_id:
                continue
            cnt = self.conn.execute(
                "SELECT COUNT(*) as c FROM dimension_fields WHERE set_id=?",
                (ds["id"],)
            ).fetchone()["c"]
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(ds["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(ds["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(ds["category_name"] or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(ds["default_unit"] or "cm"))
            self.table.setItem(r, 4, QTableWidgetItem(str(cnt)))
            self.table.item(r, 0).setData(Qt.UserRole, ds["id"])

        if prev is not None:
            for r in range(self.table.rowCount()):
                if self.table.item(r, 0).data(Qt.UserRole) == prev:
                    self.table.selectRow(r)
                    break

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _on_select(self):
        sid = self._selected_id()
        if sid:
            self.set_selected.emit(sid)

    def _add(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم المجموعة")
            return
        insert_dimension_set(
            self.conn, name,
            category_id=self.cmb_category.currentData(),
            default_unit=self.inp_unit.text().strip() or "cm",
            notes=self.inp_notes.text().strip()
        )
        self._reset()
        self._load()

    def _edit(self):
        sid = self._selected_id()
        if sid is None:
            QMessageBox.information(self, "تنبيه", "اختر مجموعة أولاً")
            return
        ds = fetch_dimension_set(self.conn, sid)
        if not ds:
            return
        self._editing_id = sid
        self.inp_name.setText(ds["name"])
        self.inp_unit.setText(ds["default_unit"] or "cm")
        self.inp_notes.setText(ds["notes"] or "")
        for i in range(self.cmb_category.count()):
            if self.cmb_category.itemData(i) == ds["category_id"]:
                self.cmb_category.setCurrentIndex(i)
                break
        self.lbl_mode.setText(f"─── تعديل: {ds['name']} ───")
        self.btn_add.setVisible(False)
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)

    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل الاسم")
            return
        update_dimension_set(
            self.conn, self._editing_id, name,
            category_id=self.cmb_category.currentData(),
            default_unit=self.inp_unit.text().strip() or "cm",
            notes=self.inp_notes.text().strip()
        )
        self._reset()
        self._load()

    def _delete(self):
        sid = self._selected_id()
        if sid is None:
            QMessageBox.information(self, "تنبيه", "اختر مجموعة أولاً")
            return
        ds = fetch_dimension_set(self.conn, sid)
        if not ds:
            return
        used = self.conn.execute(
            "SELECT COUNT(*) as c FROM design_dimensions WHERE set_id=?", (sid,)
        ).fetchone()["c"]
        if used:
            QMessageBox.warning(
                self, "تنبيه",
                f"المجموعة «{ds['name']}» مستخدمة في {used} تصميم — لا يمكن حذفها."
            )
            return
        if confirm_delete(self, ds["name"]):
            delete_dimension_set(self.conn, sid)
            self._load()

    def _reset(self):
        self._editing_id = None
        self.inp_name.clear()
        self.inp_unit.setText("cm")
        self.inp_notes.clear()
        self.cmb_category.setCurrentIndex(0)
        self.lbl_mode.setText("─── مجموعة جديدة ───")
        self.btn_add.setVisible(True)
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)

    def refresh(self):
        self._load()


# ══════════════════════════════════════════════════════════
# تبويب تصنيفات التصميمات
# ══════════════════════════════════════════════════════════

class _CategoriesPanel(QWidget):
    """إدارة تصنيفات التصميمات."""

    categories_changed = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._editing_id = None
        self._color      = "#1565c0"
        self._build()
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["التصنيف", "العناصر"])
        self.tree.setColumnWidth(0, 260)
        self.tree.setAlternatingRowColors(True)
        self.tree.setAnimated(True)
        root.addWidget(self.tree)

        btn_edit = QPushButton("✏️  تعديل")
        btn_del  = danger_button("🗑️  حذف")
        for b in (btn_edit, btn_del):
            b.setMinimumHeight(28)
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        root.addLayout(buttons_row(btn_edit, btn_del))

        grp  = QGroupBox("بيانات التصنيف")
        form = QFormLayout(grp)
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = QLabel("─── تصنيف جديد ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0;")
        form.addRow(self.lbl_mode)

        self.inp_name   = QLineEdit()
        self.inp_name.setMinimumHeight(30)
        self.cmb_parent = QComboBox()
        self.cmb_parent.setMinimumHeight(28)

        color_row = QHBoxLayout()
        self.lbl_color = QLabel()
        self.lbl_color.setFixedSize(28, 28)
        self._update_color_label()
        btn_color = QPushButton("لون")
        btn_color.setMinimumHeight(28)
        btn_color.clicked.connect(self._pick_color)
        color_row.addWidget(self.lbl_color)
        color_row.addWidget(btn_color)
        color_row.addStretch()

        self.inp_notes = QLineEdit()
        self.inp_notes.setMinimumHeight(28)

        form.addRow("الاسم :",    self.inp_name)
        form.addRow("تابع لـ :", self.cmb_parent)
        form.addRow("اللون :",    color_row)
        form.addRow("ملاحظات :", self.inp_notes)

        self.btn_add    = QPushButton("➕  إضافة")
        self.btn_save   = QPushButton("💾  حفظ")
        self.btn_cancel = QPushButton("✖  إلغاء")
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        for b in (self.btn_add, self.btn_save, self.btn_cancel):
            b.setMinimumHeight(30)
        self.btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self._reset)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_cancel)
        form.addRow(btn_row)
        root.addWidget(grp)

    def _update_color_label(self):
        self.lbl_color.setStyleSheet(
            f"background:{self._color}; border-radius:4px; border:1px solid #ccc;"
        )

    def _pick_color(self):
        col = QColorDialog.getColor(QColor(self._color), self, "اختر لوناً")
        if col.isValid():
            self._color = col.name()
            self._update_color_label()

    def _load(self):
        self.tree.clear()
        rows = fetch_all_design_categories(self.conn)
        tree = build_category_tree(rows)
        self._add_tree_nodes(tree, None)
        self.tree.expandAll()
        self._reload_parent_combo()

    def _add_tree_nodes(self, nodes, parent_item):
        for node in nodes:
            item = QTreeWidgetItem()
            item.setText(0, node["name"])
            item.setData(0, Qt.UserRole, node["id"])
            item.setForeground(0, QColor(node["color"]))
            cnt = self.conn.execute(
                "SELECT COUNT(*) as c FROM dimension_sets WHERE category_id=?",
                (node["id"],)
            ).fetchone()["c"]
            item.setText(1, str(cnt) if cnt else "—")
            if parent_item is None:
                self.tree.addTopLevelItem(item)
            else:
                parent_item.addChild(item)
            if node["children"]:
                self._add_tree_nodes(node["children"], item)

    def _reload_parent_combo(self, exclude_id=None):
        self.cmb_parent.blockSignals(True)
        self.cmb_parent.clear()
        self.cmb_parent.addItem("— بدون أب —", None)
        rows = fetch_all_design_categories(self.conn)
        tree = build_category_tree(rows)
        self._add_parent_nodes(tree, 0, exclude_id or set())
        self.cmb_parent.blockSignals(False)

    def _add_parent_nodes(self, nodes, depth, excluded):
        indent = "    " * depth
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            if node["id"] in excluded:
                continue
            self.cmb_parent.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            if node["children"]:
                self._add_parent_nodes(node["children"], depth + 1, excluded)

    def _selected_id(self):
        items = self.tree.selectedItems()
        return items[0].data(0, Qt.UserRole) if items else None

    def _add(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل الاسم")
            return
        insert_design_category(self.conn, name, self._color,
                               self.cmb_parent.currentData(),
                               self.inp_notes.text().strip())
        self._reset()
        self._load()
        self.categories_changed.emit()

    def _edit(self):
        cid = self._selected_id()
        if cid is None:
            QMessageBox.information(self, "تنبيه", "اختر تصنيفاً")
            return
        cat = fetch_design_category(self.conn, cid)
        if not cat:
            return
        self._editing_id = cid
        self._color = cat["color"]
        self.inp_name.setText(cat["name"])
        self.inp_notes.setText(cat["notes"] or "")
        self._update_color_label()
        excluded = set(fetch_category_descendants(self.conn, cid))
        self._reload_parent_combo(exclude_id=excluded)
        for i in range(self.cmb_parent.count()):
            if self.cmb_parent.itemData(i) == cat["parent_id"]:
                self.cmb_parent.setCurrentIndex(i)
                break
        self.lbl_mode.setText(f"─── تعديل: {cat['name']} ───")
        self.btn_add.setVisible(False)
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)

    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل الاسم")
            return
        update_design_category(self.conn, self._editing_id, name, self._color,
                               self.cmb_parent.currentData(),
                               self.inp_notes.text().strip())
        self._reset()
        self._load()
        self.categories_changed.emit()

    def _delete(self):
        cid = self._selected_id()
        if cid is None:
            QMessageBox.information(self, "تنبيه", "اختر تصنيفاً")
            return
        cat = fetch_design_category(self.conn, cid)
        if not cat:
            return
        if confirm_delete(self, cat["name"]):
            delete_design_category(self.conn, cid)
            self._load()
            self.categories_changed.emit()

    def _reset(self):
        self._editing_id = None
        self._color = "#1565c0"
        self.inp_name.clear()
        self.inp_notes.clear()
        self._update_color_label()
        self.lbl_mode.setText("─── تصنيف جديد ───")
        self.btn_add.setVisible(True)
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        self._reload_parent_combo()


# ══════════════════════════════════════════════════════════
# تبويب المقاسات الرئيسي (محدّث: إضافة _ValuesPanel)
# ══════════════════════════════════════════════════════════

class DimensionSetsTab(QWidget):
    """
    التبويب الرئيسي لإدارة مجموعات المقاسات.

    التخطيط:
      [تبويب: مجموعات المقاسات]
        ├── Splitter أفقي:
        │     ├── يسار: _SetsPanel (قائمة + فورم)
        │     └── يمين: Splitter رأسي:
        │           ├── أعلى: _FieldsPanel (الحقول + اعتماديات cross-set)
        │           └── أسفل: _ValuesPanel (إدخال الأرقام مباشرة)
      [تبويب: تصنيفات المقاسات]
    """

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        inner_tabs = QTabWidget()

        # ── تبويب المجموعات + الحقول + الإدخال ──
        sets_widget = QWidget()
        sets_layout = QVBoxLayout(sets_widget)
        sets_layout.setContentsMargins(0, 0, 0, 0)

        # Splitter أفقي رئيسي
        h_splitter = QSplitter(Qt.Horizontal)
        h_splitter.setHandleWidth(5)
        h_splitter.setStyleSheet("""
            QSplitter::handle { background: #e0e0e0; }
            QSplitter::handle:hover { background: #bbdefb; }
        """)

        # يسار: قائمة المجموعات
        self._sets_panel = _SetsPanel(self.conn)

        # يمين: splitter رأسي (حقول + إدخال قيم)
        v_splitter = QSplitter(Qt.Vertical)
        v_splitter.setHandleWidth(5)
        v_splitter.setStyleSheet("""
            QSplitter::handle { background: #e0e0e0; }
            QSplitter::handle:hover { background: #bbdefb; }
        """)

        self._fields_panel = _FieldsPanel(self.conn)
        self._values_panel = _ValuesPanel(self.conn)

        v_splitter.addWidget(self._fields_panel)
        v_splitter.addWidget(self._values_panel)
        v_splitter.setSizes([300, 350])

        h_splitter.addWidget(self._sets_panel)
        h_splitter.addWidget(v_splitter)
        h_splitter.setSizes([340, 660])

        # ربط الإشارات
        self._sets_panel.set_selected.connect(self._fields_panel.load_set)
        self._fields_panel.set_selected.connect(self._values_panel.load_set)
        # عند تعديل الحقول → أعد تحميل لوحة الإدخال
        self._fields_panel.fields_changed.connect(self._on_fields_changed)

        sets_layout.addWidget(h_splitter)
        inner_tabs.addTab(sets_widget, "📐  مجموعات المقاسات")

        # ── تبويب التصنيفات ──
        self._cats_panel = _CategoriesPanel(self.conn)
        self._cats_panel.categories_changed.connect(self._sets_panel.refresh)
        inner_tabs.addTab(self._cats_panel, "🏷️  تصنيفات المقاسات")

        root.addWidget(inner_tabs)

    def _on_fields_changed(self):
        """إعادة تحميل لوحة الإدخال عند تغيير الحقول."""
        # نعيد تحميل لوحة الإدخال بنفس المجموعة
        if self._values_panel._set_id is not None:
            self._values_panel.load_set(self._values_panel._set_id)