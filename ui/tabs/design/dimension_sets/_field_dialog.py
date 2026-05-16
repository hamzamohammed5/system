"""
ui/tabs/design/dimension_sets/_field_dialog.py
=====================================
"""

from PyQt5.QtWidgets import (
    QVBoxLayout, QDoubleSpinBox,
    QLabel, QLineEdit,
    QComboBox, QCheckBox, QGroupBox,
    QFormLayout, QMessageBox, QDialog,
    QDialogButtonBox
    )

from PyQt5.QtCore import Qt


from db.designs.dimension_sets_repo import (
    fetch_all_dimension_sets,
    fetch_fields_for_set, fetch_field,
    insert_field, update_field,
    fetch_field_dep, set_field_dep, remove_field_dep,

)

# ── الوحدات المتاحة (موحّدة) ──
UNIT_OPTIONS = [
    ("px",   "px — بكسل"),
    ("mm",   "mm — مليمتر"),
    ("cm",   "cm — سنتيمتر"),
    ("m",    "m  — متر"),
    ("inch", "inch — بوصة"),
]

def _spin(min_=None, max_=9999, dec=2):
    s = QDoubleSpinBox()
    s.setRange(min_ if min_ is not None else -99999, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(30)
    return s


def make_unit_combo(current: str = "cm") -> QComboBox:
    """يبني QComboBox موحّد لاختيار الوحدة."""
    cmb = QComboBox()
    cmb.setMinimumHeight(30)
    for val, label in UNIT_OPTIONS:
        cmb.addItem(label, val)
    # اختيار الوحدة الحالية
    for i in range(cmb.count()):
        if cmb.itemData(i) == current:
            cmb.setCurrentIndex(i)
            break
    return cmb


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
        self.setMinimumWidth(500)
        self.setModal(True)
        self._build()
        if field_data:
            self._load(field_data)

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 16)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.inp_name  = QLineEdit()
        self.inp_name.setPlaceholderText("مثال: length, width ...")
        self.inp_name.setMinimumHeight(30)

        self.inp_label = QLineEdit()
        self.inp_label.setPlaceholderText("مثال: الطول، العرض ...")
        self.inp_label.setMinimumHeight(30)

        # ── وحدة الحقل (dropdown بدل QLineEdit) ──
        self.cmb_unit = make_unit_combo("cm")

        self.cmb_type = QComboBox()
        self.cmb_type.addItem("رقم", "number")
        self.cmb_type.addItem("نص",  "text")
        self.cmb_type.setMinimumHeight(30)
        self.cmb_type.currentIndexChanged.connect(self._on_type_changed)

        self.chk_required = QCheckBox("حقل إلزامي")
        self.chk_required.setChecked(True)

        form.addRow("الاسم (إنجليزي) :", self.inp_name)
        form.addRow("التسمية (عربي) :",  self.inp_label)
        form.addRow("الوحدة :",           self.cmb_unit)
        form.addRow("النوع :",            self.cmb_type)
        form.addRow("",                   self.chk_required)
        root.addLayout(form)

        # ── قسم الاعتمادية (cross-set) ──
        self._dep_grp = QGroupBox("اعتماد على حقل من مجموعة مقاسات (اختياري)")
        self._dep_grp.setCheckable(True)
        self._dep_grp.setChecked(False)
        self._dep_grp.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #1565c0;
                border: 1px solid #c5cae9;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                right: 12px;
                padding: 0 4px;
            }
        """)
        dep_lay = QFormLayout(self._dep_grp)
        dep_lay.setSpacing(10)
        dep_lay.setLabelAlignment(Qt.AlignRight)

        self.cmb_source_set = QComboBox()
        self.cmb_source_set.setMinimumHeight(30)
        self.cmb_source_set.addItem("— اختر مجموعة مقاسات —", None)

        all_sets = fetch_all_dimension_sets(self.conn)
        for ds in all_sets:
            if ds["id"] == self.set_id:
                self.cmb_source_set.addItem(f"← نفس المجموعة: {ds['name']}", ds["id"])
                break
        for ds in all_sets:
            if ds["id"] != self.set_id:
                self.cmb_source_set.addItem(ds["name"], ds["id"])

        self.cmb_source_set.currentIndexChanged.connect(self._reload_source_fields)

        self.cmb_source = QComboBox()
        self.cmb_source.setMinimumHeight(30)
        self.cmb_source.setMinimumWidth(220)

        self._source_preview = QLabel("")
        self._source_preview.setStyleSheet("""
            color: #1565c0; font-size: 11px;
            background: #e8f0fe; border: 1px solid #bbdefb;
            border-radius: 4px; padding: 4px 8px;
        """)
        self._source_preview.setVisible(False)
        self._source_preview.setWordWrap(True)

        self.sp_offset = _spin(min_=-9999, max_=9999, dec=4)
        self.sp_offset.setValue(0)
        self.sp_offset.valueChanged.connect(self._update_preview)
        self.cmb_source.currentIndexChanged.connect(self._update_preview)

        hint = QLabel("القيمة = قيمة الحقل المصدر + الإضافة (سالب للخصم)")
        hint.setStyleSheet(
            "color: #1565c0; font-size: 10px;"
            "background: #e8f0fe; border-radius: 4px; padding: 4px 8px;"
        )

        dep_lay.addRow("المجموعة المصدر :", self.cmb_source_set)
        dep_lay.addRow("الحقل المصدر :",    self.cmb_source)
        dep_lay.addRow("إضافة / خصم :",     self.sp_offset)
        dep_lay.addRow("المعاينة :",         self._source_preview)
        dep_lay.addRow(hint)
        root.addWidget(self._dep_grp)

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
        set_id = self.cmb_source_set.currentData()
        self.cmb_source.clear()
        self._source_preview.setVisible(False)

        if set_id is None:
            return

        fields = fetch_fields_for_set(self.conn, set_id)
        added  = 0
        for f in fields:
            if f["field_type"] != "number":
                continue
            if f["id"] == self.field_id:
                continue
            self.cmb_source.addItem(f["label"], (f["id"], set_id))
            added += 1

        if added == 0:
            self.cmb_source.addItem("— لا توجد حقول رقمية —", None)
        else:
            self._update_preview()

    def _update_preview(self):
        if not self._dep_grp.isChecked():
            self._source_preview.setVisible(False)
            return

        src_set_id = self.cmb_source_set.currentData()
        d = self.cmb_source.currentData()
        if not src_set_id or not isinstance(d, tuple):
            self._source_preview.setVisible(False)
            return

        src_field_id = d[0]
        offset = self.sp_offset.value()

        row = self.conn.execute(
            "SELECT dsv.value_num, df.label, ds.name AS set_name "
            "FROM dimension_set_values dsv "
            "JOIN dimension_fields df ON df.id = dsv.field_id "
            "JOIN dimension_sets ds ON ds.id = dsv.set_id "
            "WHERE dsv.set_id=? AND dsv.field_id=?",
            (src_set_id, src_field_id)
        ).fetchone()

        if row and row["value_num"] is not None:
            src_val = float(row["value_num"])
            result  = src_val + offset
            sign    = f"+{offset:g}" if offset >= 0 else f"{offset:g}"
            self._source_preview.setText(
                f"من «{row['set_name']}» → {row['label']} = {src_val:g}  |  "
                f"النتيجة: {src_val:g} {sign} = {result:g}"
            )
            self._source_preview.setVisible(True)
        else:
            self._source_preview.setText("لا توجد قيمة محفوظة بعد في المجموعة المصدر")
            self._source_preview.setVisible(True)

    def _load(self, field_data):
        self.inp_name.setText(field_data["name"])
        self.inp_label.setText(field_data["label"])

        # اختيار الوحدة في الـ dropdown
        unit = field_data["unit"] or "cm"
        for i in range(self.cmb_unit.count()):
            if self.cmb_unit.itemData(i) == unit:
                self.cmb_unit.setCurrentIndex(i)
                break

        idx = self.cmb_type.findData(field_data["field_type"])
        if idx >= 0:
            self.cmb_type.setCurrentIndex(idx)
        self.chk_required.setChecked(bool(field_data["required"]))

        if self.field_id:
            dep = fetch_field_dep(self.conn, self.field_id)
            if dep:
                self._dep_grp.setChecked(True)
                src_set_id = dep["source_set_id"] or self.set_id

                for i in range(self.cmb_source_set.count()):
                    if self.cmb_source_set.itemData(i) == src_set_id:
                        self.cmb_source_set.setCurrentIndex(i)
                        break
                self._reload_source_fields()

                for i in range(self.cmb_source.count()):
                    d = self.cmb_source.itemData(i)
                    if isinstance(d, tuple) and d[0] == dep["source_field_id"]:
                        self.cmb_source.setCurrentIndex(i)
                        break

                self.sp_offset.setValue(float(dep["offset"]))
                self._update_preview()

    def _save(self):
        name  = self.inp_name.text().strip()
        label = self.inp_label.text().strip()
        if not name or not label:
            QMessageBox.warning(self, "تنبيه", "أدخل الاسم والتسمية")
            return

        # الوحدة من الـ dropdown
        unit     = self.cmb_unit.currentData() or "cm"
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

        if self._dep_grp.isChecked() and self._dep_grp.isEnabled():
            d = self.cmb_source.currentData()
            if isinstance(d, tuple):
                src_field_id, src_set_id = d
                actual_src_set = None if src_set_id == self.set_id else src_set_id
                set_field_dep(
                    self.conn, self.field_id, src_field_id,
                    self.sp_offset.value(), "",
                    source_set_id=actual_src_set
                )
        else:
            remove_field_dep(self.conn, self.field_id)

        self.accept()