"""
ui/tabs/design/dimension_sets_tab.py
=====================================
تبويب إدارة مجموعات المقاسات.

التغييرات:
  1. _FieldDialog  — خانة الاعتمادية تختار مجموعة مقاسات + حقل منها (cross-set)
  2. _ValuesPanel  — لما تختار مجموعة مصدر في الاعتمادية، القيم بتتحمل منها تلقائياً
                     + حقل "الاسم" لكل صف يتحفظ في value_text
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
from PyQt5.QtGui  import QColor, QFont

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
    calc_standalone_cross_auto, fetch_source_set_values,
)
from ui.helpers import make_table, buttons_row, confirm_delete, danger_button


def _spin(min_=None, max_=9999, dec=2):
    s = QDoubleSpinBox()
    s.setRange(min_ if min_ is not None else -99999, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(30)
    return s


# ══════════════════════════════════════════════════════════
# محرر حقل واحد — Dialog (cross-set deps)
# ══════════════════════════════════════════════════════════

class _FieldDialog(QDialog):
    """
    نافذة إضافة/تعديل حقل مقاسات.
    الاعتمادية تختار مجموعة مقاسات + حقل منها.
    """

    def __init__(self, conn, set_id: int, field_data=None, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self.set_id    = set_id
        self.field_id  = field_data["id"] if field_data else None
        self.setWindowTitle("تعديل حقل" if field_data else "إضافة حقل جديد")
        self.setMinimumWidth(480)
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
        self.cmb_type.addItem("نص",  "text")
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
        self._dep_grp = QGroupBox("اعتماد على حقل من مجموعة مقاسات (اختياري)")
        self._dep_grp.setCheckable(True)
        self._dep_grp.setChecked(False)
        dep_lay = QFormLayout(self._dep_grp)
        dep_lay.setSpacing(8)
        dep_lay.setLabelAlignment(Qt.AlignRight)

        # اختيار المجموعة أولاً
        self.cmb_source_set = QComboBox()
        self.cmb_source_set.setMinimumHeight(28)
        self.cmb_source_set.addItem("— اختر مجموعة مقاسات —", None)
        for ds in fetch_all_dimension_sets(self.conn):
            label = f"← نفس المجموعة: {ds['name']}" if ds["id"] == self.set_id \
                    else ds["name"]
            self.cmb_source_set.addItem(label, ds["id"])
        self.cmb_source_set.currentIndexChanged.connect(self._reload_source_fields)

        # الحقل المصدر (يتحدد بعد اختيار المجموعة)
        self.cmb_source = QComboBox()
        self.cmb_source.setMinimumHeight(28)
        self.cmb_source.setMinimumWidth(200)
        self.cmb_source.setPlaceholderText("اختر مجموعة أولاً...")

        self.sp_offset = _spin(min_=-9999, max_=9999, dec=4)
        self.sp_offset.setValue(0)

        dep_lay.addRow("المجموعة المصدر :", self.cmb_source_set)
        dep_lay.addRow("الحقل المصدر :",    self.cmb_source)
        dep_lay.addRow("إضافة / خصم :",     self.sp_offset)

        hint = QLabel("القيمة = قيمة الحقل المصدر + الإضافة (سالب للخصم)")
        hint.setStyleSheet(
            "color:#1565c0; font-size:10px;"
            "background:#e8f0fe; border-radius:4px; padding:4px 8px;"
        )
        dep_lay.addRow(hint)

        root.addWidget(self._dep_grp)

        # أزرار
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("💾  حفظ")
        btns.button(QDialogButtonBox.Cancel).setText("✖  إلغاء")
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    def _on_type_changed(self, idx):
        is_number = self.cmb_type.currentData() == "number"
        self._dep_grp.setEnabled(is_number)
        if not is_number:
            self._dep_grp.setChecked(False)

    def _reload_source_fields(self):
        """تحميل حقول المجموعة المختارة فقط."""
        set_id = self.cmb_source_set.currentData()
        self.cmb_source.clear()

        if set_id is None:
            self.cmb_source.setPlaceholderText("اختر مجموعة أولاً...")
            return

        fields = fetch_fields_for_set(self.conn, set_id)
        for f in fields:
            if f["field_type"] != "number":
                continue
            if f["id"] == self.field_id:
                continue   # لا تعتمد على نفسك
            self.cmb_source.addItem(f["label"], (f["id"], set_id))

        if self.cmb_source.count() == 0:
            self.cmb_source.addItem("— لا توجد حقول رقمية —", None)

    def _load(self, field_data):
        self.inp_name.setText(field_data["name"])
        self.inp_label.setText(field_data["label"])
        self.inp_unit.setText(field_data["unit"] or "cm")
        idx = self.cmb_type.findData(field_data["field_type"])
        if idx >= 0:
            self.cmb_type.setCurrentIndex(idx)
        self.chk_required.setChecked(bool(field_data["required"]))

        if self.field_id:
            dep = fetch_field_dep(self.conn, self.field_id)
            if dep:
                self._dep_grp.setChecked(True)
                src_set_id = dep["source_set_id"] or self.set_id

                # اختيار المجموعة المصدر
                for i in range(self.cmb_source_set.count()):
                    if self.cmb_source_set.itemData(i) == src_set_id:
                        self.cmb_source_set.setCurrentIndex(i)
                        break
                self._reload_source_fields()

                # اختيار الحقل المصدر
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

        unit     = self.inp_unit.text().strip() or "cm"
        ftype    = self.cmb_type.currentData()
        required = self.chk_required.isChecked()

        if self.field_id:
            f = fetch_field(self.conn, self.field_id)
            sort_order = f["sort_order"] if f else 0
            update_field(self.conn, self.field_id, name, label,
                         unit, ftype, required, sort_order)
        else:
            existing   = fetch_fields_for_set(self.conn, self.set_id)
            sort_order = len(existing)
            self.field_id = insert_field(
                self.conn, self.set_id, name, label,
                unit, ftype, required, sort_order
            )

        # الاعتمادية
        if self._dep_grp.isChecked() and self._dep_grp.isEnabled():
            d = self.cmb_source.currentData()
            if isinstance(d, tuple):
                src_field_id, src_set_id = d
                # لو نفس المجموعة → source_set_id = None
                actual_src_set = None if src_set_id == self.set_id else src_set_id
                set_field_dep(
                    self.conn, self.field_id, src_field_id,
                    self.sp_offset.value(), "",
                    source_set_id=actual_src_set
                )
        else:
            remove_field_dep(self.conn, self.field_id)

        self.accept()


# ══════════════════════════════════════════════════════════
# لوحة إدخال القيم — مع اسم لكل صف + تحميل من المجموعة المصدر
# ══════════════════════════════════════════════════════════

class _ValuesPanel(QWidget):
    """
    لوحة إدخال قيم المقاسات مباشرة على مجموعة محددة.

    الميزات:
      - كل صف فيه حقل "الاسم" يُحفظ كـ value_text في dimension_set_values
      - الحقول المعتمدة على مجموعة خارجية: يظهر زر "⟳" يجيب القيمة منها تلقائياً
      - عند الحساب التلقائي تظهر قيمة المجموعة المصدر بجانب الخانة كـ reference
    """

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn    = conn
        self._set_id = None
        self._rows   = {}   # field_id → {"spin": QDoubleSpinBox, "name_inp": QLineEdit, "ref_lbl": QLabel|None}
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        hdr = QLabel("📊  إدخال قيم المقاسات")
        hdr.setStyleSheet("""
            font-weight: bold; font-size: 13px; color: #1565c0;
            background: #e8f0fe; border-radius: 6px; padding: 6px 12px;
        """)
        root.addWidget(hdr)

        self._hint = QLabel("اختر مجموعة مقاسات من القائمة لبدء الإدخال")
        self._hint.setStyleSheet("color: #888; font-size: 11px; padding: 4px;")
        self._hint.setAlignment(Qt.AlignCenter)
        root.addWidget(self._hint)

        # منطقة التمرير
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet("""
            QScrollArea { border: 1px solid #e0e0e0; border-radius: 6px; background: white; }
            QScrollBar:vertical { background:#f5f5f5; width:8px; border-radius:4px; }
            QScrollBar::handle:vertical { background:#bdbdbd; border-radius:4px; min-height:30px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0px; }
        """)
        self._fields_w   = QWidget()
        self._fields_w.setStyleSheet("background: white;")
        self._fields_lay = QVBoxLayout(self._fields_w)
        self._fields_lay.setSpacing(6)
        self._fields_lay.setContentsMargins(12, 12, 12, 12)
        self._fields_lay.addStretch()
        self._scroll.setWidget(self._fields_w)
        root.addWidget(self._scroll, stretch=1)

        # شريط الأزرار
        bar = QHBoxLayout()

        self.btn_save = QPushButton("💾  حفظ القيم")
        self.btn_save.setMinimumHeight(32)
        self.btn_save.setEnabled(False)
        self.btn_save.setStyleSheet("""
            QPushButton { background:#1565c0; color:white; border:none;
                border-radius:5px; padding:4px 18px; font-weight:bold; }
            QPushButton:hover { background:#0d47a1; }
            QPushButton:disabled { background:#b0bec5; }
        """)
        self.btn_save.clicked.connect(self._save_values)

        self.btn_calc = QPushButton("⟳  حساب التلقائي")
        self.btn_calc.setMinimumHeight(32)
        self.btn_calc.setEnabled(False)
        self.btn_calc.setStyleSheet("""
            QPushButton { background:#e8f5e9; color:#2e7d32;
                border:1px solid #a5d6a7; border-radius:5px; padding:4px 14px; }
            QPushButton:hover { background:#c8e6c9; }
            QPushButton:disabled { background:#f5f5f5; color:#bbb; border-color:#ddd; }
        """)
        self.btn_calc.clicked.connect(self._calc_all_auto)

        self.btn_reset = QPushButton("↺  مسح")
        self.btn_reset.setMinimumHeight(32)
        self.btn_reset.setEnabled(False)
        self.btn_reset.setStyleSheet("""
            QPushButton { background:#fff3e0; color:#e65100;
                border:1px solid #ffcc80; border-radius:5px; padding:4px 14px; }
            QPushButton:hover { background:#ffe0b2; }
            QPushButton:disabled { background:#f5f5f5; color:#bbb; border-color:#ddd; }
        """)
        self.btn_reset.clicked.connect(self._reset_values)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color:#2e7d32; font-size:11px;")

        bar.addWidget(self.btn_save)
        bar.addWidget(self.btn_calc)
        bar.addWidget(self.btn_reset)
        bar.addStretch()
        bar.addWidget(self.lbl_status)
        root.addLayout(bar)

    # ──────────────────────────────────────────────────────

    def load_set(self, set_id: int):
        self._set_id = set_id
        self._rows   = {}
        self._clear_fields()
        self._hint.setVisible(False)

        fields = fetch_fields_for_set(self.conn, set_id)
        num_fields = [f for f in fields if f["field_type"] == "number"]

        if not num_fields:
            lbl = QLabel("هذه المجموعة ليس لها حقول رقمية — أضف حقولاً أولاً")
            lbl.setStyleSheet("color:#888; font-size:11px; padding:12px;")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setWordWrap(True)
            self._fields_lay.insertWidget(0, lbl)
            self._set_buttons(False, False)
            return

        saved    = fetch_standalone_values(self.conn, set_id)
        has_auto = False

        for f in num_fields:
            has_dep = bool(f["source_field_id"])
            if has_dep:
                has_auto = True
            saved_info = saved.get(f["id"], {})
            row_w = self._build_row(f, saved_info)
            self._fields_lay.insertWidget(
                self._fields_lay.count() - 1, row_w
            )

        self._set_buttons(True, has_auto)
        self.lbl_status.setText("")

    def _build_row(self, field_data, saved_info: dict) -> QWidget:
        """
        saved_info: {"value_num": float|None, "value_text": str|None}
        """
        fid      = field_data["id"]
        has_dep  = bool(field_data["source_field_id"])
        src_set_id = field_data.get("source_set_id")   # None = نفس المجموعة
        current_value = saved_info.get("value_num") if isinstance(saved_info, dict) else saved_info
        saved_name    = saved_info.get("value_text", "") if isinstance(saved_info, dict) else ""

        frame = QFrame()
        frame.setStyleSheet("""
            QFrame { background:#fafafa; border:1px solid #e8eaf6; border-radius:6px; }
            QFrame:hover { border-color:#90caf9; background:#f3f8ff; }
        """)
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(8)

        # ── اسم الصف (label مخصص يُحفظ كـ value_text) ──
        name_inp = QLineEdit()
        name_inp.setPlaceholderText("اسم / تسمية...")
        name_inp.setFixedWidth(110)
        name_inp.setMinimumHeight(28)
        name_inp.setStyleSheet("""
            QLineEdit { border:1px solid #c5cae9; border-radius:4px;
                padding:2px 6px; background:white; font-size:11px; }
            QLineEdit:focus { border-color:#1565c0; }
        """)
        if saved_name:
            name_inp.setText(saved_name)

        # ── تسمية الحقل ──
        lbl = QLabel(field_data["label"])
        lbl.setFixedWidth(100)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl.setStyleSheet(
            "background:transparent; border:none; font-weight:bold; color:#333;"
        )

        # ── خانة الإدخال ──
        spin = QDoubleSpinBox()
        spin.setRange(-99999, 99999)
        spin.setDecimals(4)
        spin.setMinimumHeight(28)
        spin.setMinimumWidth(110)
        spin.setStyleSheet("""
            QDoubleSpinBox { border:1px solid #c5cae9; border-radius:4px;
                padding:2px 6px; background:white; }
            QDoubleSpinBox:focus { border-color:#1565c0; }
        """)
        if current_value is not None:
            spin.setValue(float(current_value))

        # ── وحدة ──
        unit_lbl = QLabel(field_data["unit"] or "cm")
        unit_lbl.setFixedWidth(30)
        unit_lbl.setStyleSheet(
            "color:#888; background:transparent; border:none; font-size:10px;"
        )

        lay.addWidget(name_inp)
        lay.addWidget(lbl)
        lay.addWidget(spin, stretch=1)
        lay.addWidget(unit_lbl)

        # ── label مرجعي لقيمة المصدر (cross-set) ──
        ref_lbl = None
        if has_dep and src_set_id:
            # اجلب القيمة الحالية من المجموعة المصدر وعرضها
            ref_lbl = QLabel("")
            ref_lbl.setFixedWidth(90)
            ref_lbl.setAlignment(Qt.AlignCenter)
            ref_lbl.setStyleSheet("""
                color:#1565c0; font-size:10px; background:#e8f0fe;
                border:1px solid #bbdefb; border-radius:3px; padding:1px 4px;
            """)
            ref_lbl.setToolTip("القيمة الحالية في المجموعة المصدر")
            # تحميل القيمة فوراً
            self._refresh_ref_label(ref_lbl, field_data["source_field_id"], src_set_id, field_data["dep_offset"])
            lay.addWidget(ref_lbl)
        else:
            # مساحة فارغة للمحاذاة
            spacer = QLabel("")
            spacer.setFixedWidth(90)
            spacer.setStyleSheet("background:transparent; border:none;")
            lay.addWidget(spacer)

        # ── زر الحساب التلقائي ──
        if has_dep:
            src_info = field_data.get("source_label") or ""
            src_set  = field_data.get("source_set_name") or ""
            tooltip  = f"يعتمد على: {src_info}"
            if src_set:
                tooltip += f" (من مجموعة: {src_set})"

            btn_auto = QPushButton("⟳")
            btn_auto.setFixedSize(30, 30)
            btn_auto.setToolTip(tooltip)
            btn_auto.setStyleSheet("""
                QPushButton { background:#e8f5e9; border:1px solid #a5d6a7;
                    border-radius:4px; color:#2e7d32; font-size:13px; font-weight:bold; }
                QPushButton:hover { background:#c8e6c9; }
            """)
            btn_auto.clicked.connect(
                lambda _, fid_=fid, sp_=spin, rl_=ref_lbl,
                       src_fid=field_data["source_field_id"],
                       src_sid=src_set_id,
                       offset=field_data["dep_offset"]:
                self._calc_one(fid_, sp_, rl_, src_fid, src_sid, offset)
            )

            badge = QLabel("↗")
            badge.setFixedSize(18, 18)
            badge.setAlignment(Qt.AlignCenter)
            badge.setStyleSheet("""
                background:#e8f5e9; border-radius:3px;
                color:#2e7d32; font-size:10px; border:none;
            """)
            badge.setToolTip(tooltip)

            lay.addWidget(badge)
            lay.addWidget(btn_auto)
        else:
            spacer2 = QLabel("")
            spacer2.setFixedWidth(52)
            spacer2.setStyleSheet("background:transparent; border:none;")
            lay.addWidget(spacer2)

        self._rows[fid] = {"spin": spin, "name_inp": name_inp, "ref_lbl": ref_lbl}
        return frame

    def _refresh_ref_label(self, ref_lbl: QLabel, source_field_id: int,
                            source_set_id: int, offset: float):
        """يحدّث الـ label المرجعي بالقيمة الحالية من المجموعة المصدر."""
        try:
            row = self.conn.execute(
                "SELECT value_num FROM dimension_set_values WHERE set_id=? AND field_id=?",
                (source_set_id, source_field_id)
            ).fetchone()
            if row and row["value_num"] is not None:
                src_val = float(row["value_num"])
                result  = src_val + float(offset)
                sign    = "+" if offset >= 0 else ""
                ref_lbl.setText(f"مصدر: {src_val:g} → {result:g}")
                ref_lbl.setStyleSheet("""
                    color:#1565c0; font-size:10px; background:#e8f0fe;
                    border:1px solid #bbdefb; border-radius:3px; padding:1px 4px;
                """)
            else:
                ref_lbl.setText("مصدر: —")
                ref_lbl.setStyleSheet("""
                    color:#aaa; font-size:10px; background:#f5f5f5;
                    border:1px solid #e0e0e0; border-radius:3px; padding:1px 4px;
                """)
        except Exception:
            ref_lbl.setText("مصدر: —")

    def _clear_fields(self):
        while self._fields_lay.count() > 1:
            item = self._fields_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _set_buttons(self, enabled: bool, has_auto: bool = False):
        self.btn_save.setEnabled(enabled)
        self.btn_calc.setEnabled(enabled and has_auto)
        self.btn_reset.setEnabled(enabled)

    def _calc_one(self, field_id: int, spin: QDoubleSpinBox,
                  ref_lbl, source_field_id: int, source_set_id,
                  offset: float):
        """يحسب قيمة حقل واحد من المجموعة المصدر."""
        if self._set_id is None:
            return
        # احفظ أولاً
        self._save_values(silent=True)
        # الحساب
        val = calc_standalone_cross_auto(self.conn, field_id, self._set_id)
        if val is not None:
            spin.setValue(val)
            spin.setStyleSheet("""
                QDoubleSpinBox { border:2px solid #43a047; border-radius:4px;
                    padding:2px 6px; background:#f1f8e9; }
            """)
            self.lbl_status.setText(f"✓ تم الحساب = {val:.4g}")
            # تحديث الـ ref label بعد الحساب
            if ref_lbl and source_set_id:
                self._refresh_ref_label(ref_lbl, source_field_id, source_set_id, offset)
        else:
            QMessageBox.information(
                self, "تنبيه",
                "لا توجد قيمة للحقل المصدر بعد.\n"
                "أدخل قيمة الحقل المصدر في مجموعتها أولاً ثم احسب."
            )

    def _calc_all_auto(self):
        if self._set_id is None:
            return
        self._save_values(silent=True)
        count = 0

        # اجلب حقول المجموعة الحالية
        fields = fetch_fields_for_set(self.conn, self._set_id)

        for f in fields:
            if f["field_type"] != "number" or not f["source_field_id"]:
                continue
            fid = f["id"]
            if fid not in self._rows:
                continue
            val = calc_standalone_cross_auto(self.conn, fid, self._set_id)
            if val is not None:
                self._rows[fid]["spin"].setValue(val)
                self._rows[fid]["spin"].setStyleSheet("""
                    QDoubleSpinBox { border:2px solid #43a047; border-radius:4px;
                        padding:2px 6px; background:#f1f8e9; }
                """)
                # تحديث الـ ref label
                ref_lbl = self._rows[fid].get("ref_lbl")
                if ref_lbl and f.get("source_set_id"):
                    self._refresh_ref_label(
                        ref_lbl, f["source_field_id"],
                        f["source_set_id"], f["dep_offset"]
                    )
                count += 1

        self.lbl_status.setText(
            f"✓ تم حساب {count} حقل" if count
            else "⚠ لا توجد قيم مصدر كافية — أدخل القيم في مجموعاتها أولاً"
        )

    def _save_values(self, silent: bool = False):
        if self._set_id is None:
            return
        for fid, row in self._rows.items():
            val      = row["spin"].value()
            row_name = row["name_inp"].text().strip()
            # نحفظ الرقم في value_num والاسم في value_text
            self.conn.execute("""
                INSERT INTO dimension_set_values (set_id, field_id, value_num, value_text)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(set_id, field_id) DO UPDATE SET
                    value_num=excluded.value_num,
                    value_text=excluded.value_text
            """, (self._set_id, fid, val, row_name or None))
        self.conn.commit()

        if not silent:
            self.lbl_status.setText("✓ تم الحفظ")
            for row in self._rows.values():
                row["spin"].setStyleSheet("""
                    QDoubleSpinBox { border:1px solid #c5cae9; border-radius:4px;
                        padding:2px 6px; background:white; }
                    QDoubleSpinBox:focus { border-color:#1565c0; }
                """)

    def _reset_values(self):
        if self._set_id is None:
            return
        if QMessageBox.question(
            self, "تأكيد", "مسح كل القيم والأسماء المدخلة؟",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            for row in self._rows.values():
                row["spin"].setValue(0.0)
                row["name_inp"].clear()
                if row.get("ref_lbl"):
                    row["ref_lbl"].setText("مصدر: —")
            self.lbl_status.setText("↺ تم المسح")

    def clear(self):
        self._set_id = None
        self._rows   = {}
        self._clear_fields()
        self._set_buttons(False)
        self._hint.setVisible(True)
        self.lbl_status.setText("")


# ══════════════════════════════════════════════════════════
# لوحة حقول المجموعة
# ══════════════════════════════════════════════════════════

class _FieldsPanel(QWidget):
    """محرر حقول مجموعة مقاسات."""

    fields_changed = pyqtSignal()
    set_selected   = pyqtSignal(int)

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn    = conn
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
        self.table.setColumnWidth(6, 160)
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

            dep_text = ""
            if f["source_field_id"]:
                sign     = "+" if f["dep_offset"] >= 0 else ""
                src_lbl  = f["source_label"] or ""
                src_set  = f.get("source_set_name") or ""
                dep_text = (
                    f"{src_lbl} ({src_set}) {sign}{f['dep_offset']:g}"
                    if src_set else
                    f"{src_lbl} {sign}{f['dep_offset']:g}"
                )
            self.table.setItem(r, 6, QTableWidgetItem(dep_text))
            self.table.item(r, 0).setData(Qt.UserRole, f["id"])

    def _selected_field_id(self):
        row  = self.table.currentRow()
        item = self.table.item(row, 0) if row >= 0 else None
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

    def _move_up(self):   self._move(-1)
    def _move_down(self): self._move(1)

    def _move(self, direction: int):
        row     = self.table.currentRow()
        new_row = row + direction
        if new_row < 0 or new_row >= self.table.rowCount():
            return
        ids = [
            self.table.item(r, 0).data(Qt.UserRole)
            for r in range(self.table.rowCount())
        ]
        ids[row], ids[new_row] = ids[new_row], ids[row]
        reorder_fields(self.conn, self._set_id, ids)
        self._refresh()
        self.table.selectRow(new_row)
        self.fields_changed.emit()


# ══════════════════════════════════════════════════════════
# لوحة مجموعات المقاسات (القائمة + الفورم)
# ══════════════════════════════════════════════════════════

class _SetsPanel(QWidget):
    """قائمة مجموعات المقاسات + فورم الإضافة/التعديل."""

    set_selected = pyqtSignal(int)

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

        # فلتر
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

        # جدول
        self.table = make_table(
            ["ID", "الاسم", "التصنيف", "الوحدة", "الحقول"],
            stretch_col=1
        )
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 60)
        self.table.setColumnWidth(4, 60)
        self.table.itemSelectionChanged.connect(self._on_select)
        root.addWidget(self.table)

        btn_edit = QPushButton("✏️  تعديل")
        btn_del  = danger_button("🗑️  حذف")
        for b in (btn_edit, btn_del):
            b.setMinimumHeight(28)
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        root.addLayout(buttons_row(btn_edit, btn_del))

        # فورم
        grp  = QGroupBox("بيانات المجموعة")
        form = QFormLayout(grp)
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight)

        self.lbl_mode = QLabel("─── مجموعة جديدة ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0;")
        form.addRow(self.lbl_mode)

        self.inp_name     = QLineEdit()
        self.inp_name.setPlaceholderText("مثال: مقاسات الثوب ...")
        self.inp_name.setMinimumHeight(30)
        self.cmb_category = QComboBox()
        self.cmb_category.setMinimumHeight(28)
        self.inp_unit     = QLineEdit()
        self.inp_unit.setText("cm")
        self.inp_unit.setFixedWidth(80)
        self.inp_unit.setMinimumHeight(28)
        self.inp_notes    = QLineEdit()
        self.inp_notes.setPlaceholderText("ملاحظات...")
        self.inp_notes.setMinimumHeight(28)

        form.addRow("الاسم :",             self.inp_name)
        form.addRow("التصنيف :",           self.cmb_category)
        form.addRow("الوحدة الافتراضية :", self.inp_unit)
        form.addRow("ملاحظات :",           self.inp_notes)

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
            combo.addItem(
                "— كل التصنيفات —" if combo is self.cmb_cat_filter
                else "— بدون تصنيف —",
                None
            )
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
        row  = self.table.currentRow()
        item = self.table.item(row, 0) if row >= 0 else None
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
                f"المجموعة «{ds['name']}» مستخدمة في {used} تصميم."
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
# لوحة المجموعات (عرض كامل)
# ══════════════════════════════════════════════════════════

class _GroupsPanel(QWidget):
    """
    تبويب 'المجموعات' — يعرض مجموعات المقاسات كاملة
    مع إمكانية البحث والتصفية.
    """

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        hdr = QLabel("📐  كل مجموعات المقاسات")
        hdr.setStyleSheet("""
            font-weight:bold; font-size:13px; color:#1565c0;
            background:#e8f0fe; border-radius:6px; padding:6px 12px;
        """)
        root.addWidget(hdr)

        search_row = QHBoxLayout()
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 بحث باسم المجموعة...")
        self.inp_search.setMinimumHeight(28)
        self.inp_search.textChanged.connect(self._apply_filter)
        search_row.addWidget(QLabel("🔍"))
        search_row.addWidget(self.inp_search, stretch=1)
        root.addLayout(search_row)

        self.table = make_table(
            ["ID", "اسم المجموعة", "التصنيف", "الوحدة", "عدد الحقول", "الحقول"],
            stretch_col=1
        )
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 60)
        self.table.setColumnWidth(4, 70)
        self.table.setColumnWidth(5, 200)
        root.addWidget(self.table, stretch=1)

        self._load()

    def _load(self):
        self._all_rows = list(fetch_all_dimension_sets(self.conn))
        self._apply_filter()

    def _apply_filter(self):
        q = self.inp_search.text().strip().lower()
        self.table.setRowCount(0)

        for ds in self._all_rows:
            if q and q not in ds["name"].lower():
                continue

            fields = fetch_fields_for_set(self.conn, ds["id"])
            cnt    = len(fields)
            field_names = "، ".join(f["label"] for f in fields[:6])
            if cnt > 6:
                field_names += f" ... (+{cnt - 6})"

            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(ds["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(ds["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(ds["category_name"] or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(ds["default_unit"] or "cm"))
            self.table.setItem(r, 4, QTableWidgetItem(str(cnt)))
            self.table.setItem(r, 5, QTableWidgetItem(field_names))
            self.table.item(r, 0).setData(Qt.UserRole, ds["id"])

    def refresh(self):
        self._load()


# ══════════════════════════════════════════════════════════
# التبويب الرئيسي
# ══════════════════════════════════════════════════════════

class DimensionSetsTab(QWidget):
    """
    التبويب الرئيسي لإدارة مجموعات المقاسات.

    التخطيط:
      [تبويب: مجموعات المقاسات]
        └── Splitter أفقي:
              ├── يسار:  _SetsPanel   (قائمة + فورم)
              └── يمين:  Splitter رأسي:
                    ├── أعلى: _FieldsPanel  (الحقول + اعتماديات cross-set)
                    └── أسفل: _ValuesPanel  (إدخال قيم + اسم لكل صف +
                                             ref label لقيم المجموعة المصدر)
      [تبويب: المجموعات]
        └── _GroupsPanel (عرض كامل لكل المجموعات وحقولها)
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

        h_splitter = QSplitter(Qt.Horizontal)
        h_splitter.setHandleWidth(5)
        h_splitter.setStyleSheet("""
            QSplitter::handle { background:#e0e0e0; }
            QSplitter::handle:hover { background:#bbdefb; }
        """)

        self._sets_panel = _SetsPanel(self.conn)

        v_splitter = QSplitter(Qt.Vertical)
        v_splitter.setHandleWidth(5)
        v_splitter.setStyleSheet("""
            QSplitter::handle { background:#e0e0e0; }
            QSplitter::handle:hover { background:#bbdefb; }
        """)

        self._fields_panel = _FieldsPanel(self.conn)
        self._values_panel = _ValuesPanel(self.conn)

        v_splitter.addWidget(self._fields_panel)
        v_splitter.addWidget(self._values_panel)
        v_splitter.setSizes([300, 350])

        h_splitter.addWidget(self._sets_panel)
        h_splitter.addWidget(v_splitter)
        h_splitter.setSizes([340, 660])

        self._sets_panel.set_selected.connect(self._fields_panel.load_set)
        self._fields_panel.set_selected.connect(self._values_panel.load_set)
        self._fields_panel.fields_changed.connect(self._on_fields_changed)

        sets_layout.addWidget(h_splitter)
        inner_tabs.addTab(sets_widget, "📐  مجموعات المقاسات")

        # ── تبويب المجموعات (عرض كامل) ──
        self._groups_panel = _GroupsPanel(self.conn)
        inner_tabs.addTab(self._groups_panel, "📋  المجموعات")

        inner_tabs.currentChanged.connect(self._on_tab_changed)

        root.addWidget(inner_tabs)

    def _on_tab_changed(self, index):
        if index == 1:
            self._groups_panel.refresh()

    def _on_fields_changed(self):
        if self._values_panel._set_id is not None:
            self._values_panel.load_set(self._values_panel._set_id)