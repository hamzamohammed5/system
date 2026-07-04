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


from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.font import FS_XS, FS_SM
from services.design.dimension_set_service import DimensionSetService
from ui.widgets.combo.unit import UnitCombo
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import (
    DIM_FIELD_DLG_MIN_W, DIM_FIELD_DLG_ROOT_SPACING, DIM_FIELD_DLG_ROOT_MARGIN,
    DIM_FIELD_DLG_FORM_SPACING, DIM_FIELD_DLG_INPUT_H, DIM_FIELD_DLG_GRP_RADIUS,
    DIM_FIELD_DLG_GRP_MARGIN_TOP, DIM_FIELD_DLG_GRP_PAD_TOP, DIM_FIELD_DLG_GRP_TITLE_RIGHT,
    DIM_FIELD_DLG_GRP_TITLE_PAD, DIM_FIELD_DLG_SOURCE_CMB_MIN_W, DIM_FIELD_DLG_PREVIEW_RADIUS,
    DIM_FIELD_DLG_PREVIEW_PAD_V, DIM_FIELD_DLG_PREVIEW_PAD_H, DIM_FIELD_DLG_SPIN_DEFAULT_MIN,
    DIM_FIELD_DLG_SPIN_DEFAULT_MAX, DIM_FIELD_DLG_SPIN_DEFAULT_DEC, DIM_FIELD_DLG_OFFSET_MIN,
    DIM_FIELD_DLG_OFFSET_MAX, DIM_FIELD_DLG_OFFSET_DEC,
)


def _spin(min_=None, max_=DIM_FIELD_DLG_SPIN_DEFAULT_MAX, dec=DIM_FIELD_DLG_SPIN_DEFAULT_DEC):
    s = QDoubleSpinBox()
    s.setRange(min_ if min_ is not None else DIM_FIELD_DLG_SPIN_DEFAULT_MIN, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(DIM_FIELD_DLG_INPUT_H)
    return s


# ══════════════════════════════════════════════════════════
# محرر حقل واحد — Dialog (cross-set deps)
# ══════════════════════════════════════════════════════════

class _FieldDialog(QDialog, WidgetMixin):
    """
    نافذة إضافة/تعديل حقل مقاسات.
    الاعتمادية تختار مجموعة مقاسات + حقل منها.
    """

    def __init__(self, conn, set_id: int, field_data=None, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self.set_id    = set_id
        self.field_id  = field_data["id"] if field_data else None
        self._svc = DimensionSetService(conn)
        self.setWindowTitle(tr("dim_field_dlg_edit_title") if field_data else tr("dim_field_dlg_new_title"))
        self.setMinimumWidth(DIM_FIELD_DLG_MIN_W)
        self.setModal(True)
        self._build()
        self._init_widget_mixin(lang=False, data=False)
        self._refresh_style()
        if field_data:
            self._load(field_data)

    def _refresh_style(self, *_):
        self._dep_grp.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                color: {_C['accent']};
                border: 1px solid {_C['accent_mid']};
                border-radius: {DIM_FIELD_DLG_GRP_RADIUS}px;
                margin-top: {DIM_FIELD_DLG_GRP_MARGIN_TOP}px;
                padding-top: {DIM_FIELD_DLG_GRP_PAD_TOP}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                right: {DIM_FIELD_DLG_GRP_TITLE_RIGHT}px;
                padding: 0 {DIM_FIELD_DLG_GRP_TITLE_PAD}px;
            }}
        """)
        self._source_preview.setStyleSheet(f"""
            color: {_C['accent']}; font-size: {FS_SM}pt;
            background: {_C['accent_light']}; border: 1px solid {_C['accent_mid']};
            border-radius: {DIM_FIELD_DLG_PREVIEW_RADIUS}px; padding: {DIM_FIELD_DLG_PREVIEW_PAD_V}px {DIM_FIELD_DLG_PREVIEW_PAD_H}px;
        """)
        self._hint.setStyleSheet(
            f"color: {_C['accent']}; font-size: {FS_XS}pt;"
            f"background: {_C['accent_light']}; border-radius: {DIM_FIELD_DLG_PREVIEW_RADIUS}px; padding: {DIM_FIELD_DLG_PREVIEW_PAD_V}px {DIM_FIELD_DLG_PREVIEW_PAD_H}px;"
        )

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(DIM_FIELD_DLG_ROOT_SPACING)
        root.setContentsMargins(DIM_FIELD_DLG_ROOT_MARGIN, DIM_FIELD_DLG_ROOT_MARGIN,
                                 DIM_FIELD_DLG_ROOT_MARGIN, DIM_FIELD_DLG_ROOT_MARGIN)

        form = QFormLayout()
        form.setSpacing(DIM_FIELD_DLG_FORM_SPACING)
        form.setLabelAlignment(Qt.AlignRight)

        self.inp_name  = QLineEdit()
        self.inp_name.setPlaceholderText(tr("dim_field_name_en_placeholder"))
        self.inp_name.setMinimumHeight(DIM_FIELD_DLG_INPUT_H)

        self.inp_label = QLineEdit()
        self.inp_label.setPlaceholderText(tr("dim_field_label_ar_placeholder"))
        self.inp_label.setMinimumHeight(DIM_FIELD_DLG_INPUT_H)

        # ── وحدة الحقل — UnitCombo مع حفظ آخر اختيار ──
        self.cmb_unit = UnitCombo(
            conn     = self.conn,
            last_key = "field_dialog_unit",
            current  = tr("dim_sets_list_default_unit"),
        )
        self.cmb_unit.setMinimumHeight(DIM_FIELD_DLG_INPUT_H)

        self.cmb_type = QComboBox()
        self.cmb_type.addItem(tr("dim_field_type_number"), "number")
        self.cmb_type.addItem(tr("dim_field_type_text"),  "text")
        self.cmb_type.setMinimumHeight(DIM_FIELD_DLG_INPUT_H)
        self.cmb_type.currentIndexChanged.connect(self._on_type_changed)

        self.chk_required = QCheckBox(tr("dim_field_required_check"))
        self.chk_required.setChecked(True)

        form.addRow(tr("dim_field_name_en_label") + " :", self.inp_name)
        form.addRow(tr("dim_field_label_ar_label") + " :",  self.inp_label)
        form.addRow(tr("unit") + " :",           self.cmb_unit)
        form.addRow(tr("type") + " :",            self.cmb_type)
        form.addRow("",                   self.chk_required)
        root.addLayout(form)

        # ── قسم الاعتمادية (cross-set) ──
        self._dep_grp = QGroupBox(tr("dim_field_dep_group_title"))
        self._dep_grp.setCheckable(True)
        self._dep_grp.setChecked(False)
        dep_lay = QFormLayout(self._dep_grp)
        dep_lay.setSpacing(DIM_FIELD_DLG_FORM_SPACING)
        dep_lay.setLabelAlignment(Qt.AlignRight)

        self.cmb_source_set = QComboBox()
        self.cmb_source_set.setMinimumHeight(DIM_FIELD_DLG_INPUT_H)
        self.cmb_source_set.addItem(tr("dim_field_select_source_set"), None)

        all_sets = self._svc.list_sets()
        for ds in all_sets:
            if ds["id"] == self.set_id:
                self.cmb_source_set.addItem(tr("dim_field_same_set_prefix").format(name=ds["name"]), ds["id"])
                break
        for ds in all_sets:
            if ds["id"] != self.set_id:
                self.cmb_source_set.addItem(ds["name"], ds["id"])

        self.cmb_source_set.currentIndexChanged.connect(self._reload_source_fields)

        self.cmb_source = QComboBox()
        self.cmb_source.setMinimumHeight(DIM_FIELD_DLG_INPUT_H)
        self.cmb_source.setMinimumWidth(DIM_FIELD_DLG_SOURCE_CMB_MIN_W)

        self._source_preview = QLabel("")
        self._source_preview.setVisible(False)
        self._source_preview.setWordWrap(True)

        self.sp_offset = _spin(min_=DIM_FIELD_DLG_OFFSET_MIN, max_=DIM_FIELD_DLG_OFFSET_MAX, dec=DIM_FIELD_DLG_OFFSET_DEC)
        self.sp_offset.setValue(0)
        self.sp_offset.valueChanged.connect(self._update_preview)
        self.cmb_source.currentIndexChanged.connect(self._update_preview)

        self._hint = QLabel(tr("dim_field_dep_hint"))

        dep_lay.addRow(tr("dim_field_source_set_label") + " :", self.cmb_source_set)
        dep_lay.addRow(tr("dim_field_source_field_label") + " :",    self.cmb_source)
        dep_lay.addRow(tr("dim_field_offset_label") + " :",     self.sp_offset)
        dep_lay.addRow(tr("dim_field_preview_label") + " :",         self._source_preview)
        dep_lay.addRow(self._hint)
        root.addWidget(self._dep_grp)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText(tr("btn_save"))
        btns.button(QDialogButtonBox.Cancel).setText(tr("btn_cancel"))
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

        fields = self._svc.list_fields(set_id)
        added  = 0
        for f in fields:
            if f["field_type"] != "number":
                continue
            if f["id"] == self.field_id:
                continue
            self.cmb_source.addItem(f["label"], (f["id"], set_id))
            added += 1

        if added == 0:
            self.cmb_source.addItem(tr("dim_field_no_numeric_fields"), None)
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
                tr("dim_src_preview_fmt").format(
                    name=f"{row['label']} ({row['set_name']})",
                    val=f"{src_val:g}", sign=sign,
                    result=f"{result:g}", unit=""
                ).strip()
            )
            self._source_preview.setVisible(True)
        else:
            self._source_preview.setText(tr("dim_field_preview_no_value"))
            self._source_preview.setVisible(True)

    def _load(self, field_data):
        self.inp_name.setText(field_data["name"])
        self.inp_label.setText(field_data["label"])

        # اختيار الوحدة في UnitCombo
        unit = field_data["unit"] or tr("dim_sets_list_default_unit")
        self.cmb_unit.set_unit(unit)

        idx = self.cmb_type.findData(field_data["field_type"])
        if idx >= 0:
            self.cmb_type.setCurrentIndex(idx)
        self.chk_required.setChecked(bool(field_data["required"]))

        if self.field_id:
            dep = self._svc.get_field_dep(self.field_id)
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
            QMessageBox.warning(self, tr("warning"), tr("dim_field_name_required"))
            return

        # الوحدة من UnitCombo
        unit     = self.cmb_unit.current_unit()
        ftype    = self.cmb_type.currentData()
        required = self.chk_required.isChecked()

        if self.field_id:
            f = self._svc.get_field(self.field_id)
            sort_order = f["sort_order"] if f else 0
            self._svc.update_field(self.field_id, name, label,
                                   unit, ftype, required, sort_order)
        else:
            existing   = self._svc.list_fields(self.set_id)
            sort_order = len(existing)
            self.field_id = self._svc.create_field(
                self.set_id, name, label,
                unit, ftype, required, sort_order
            )

        if self._dep_grp.isChecked() and self._dep_grp.isEnabled():
            d = self.cmb_source.currentData()
            if isinstance(d, tuple):
                src_field_id, src_set_id = d
                actual_src_set = None if src_set_id == self.set_id else src_set_id
                self._svc.set_field_dep(
                    self.field_id, src_field_id,
                    self.sp_offset.value(), "",
                    src_set_id=actual_src_set
                )
        else:
            self._svc.remove_field_dep(self.field_id)

        self.accept()