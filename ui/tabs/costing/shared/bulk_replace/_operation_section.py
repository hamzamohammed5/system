"""
ui/tabs/costing/shared/bulk_replace/_operation_section.py
==========================================================
_OperationSection — قسم اختيار العملية في نافذة الاستبدال الشامل.
"""

from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QDoubleSpinBox, QCheckBox,
    QRadioButton, QFrame,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor, QFont

from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import (
    OP_SECTION_SPACING, OP_SECTION_GRP_RADIUS, OP_SECTION_GRP_PAD_TOP,
    OP_SECTION_GRP_TITLE_PAD_H, OP_SECTION_FORM_SPACING,
    OP_SECTION_CMB_MIN_H, OP_SECTION_CMB_MIN_W, OP_SECTION_CMB_RADIUS,
    OP_SECTION_CMB_PAD_H, OP_SECTION_CMB_PAD_V,
    OP_SECTION_SP_W, OP_SECTION_FRAME_RADIUS, OP_SECTION_FRAME_PAD,
    SPACING_MD, SPACING_LG,
)
from ui.font import FS_BASE, FS_SM


class _OperationSection(QGroupBox, WidgetMixin):
    """
    قسم اختيار العملية في نافذة الاستبدال الشامل.

    الوصول للحالة:
        .do_replace   → bool
        .do_qty       → bool
        .new_child_id → int | None
        .uniform_qty  → float | None
    """

    def __init__(self, child_type: str, parent=None):
        super().__init__(tr('operation_section_title'), parent)
        self._child_type = child_type
        self._init_widget_mixin(data=False)
        self._build()

    def _build(self):
        self._refresh_style()

        lay = QVBoxLayout(self)
        lay.setSpacing(OP_SECTION_SPACING)

        # ── خيارات العملية ──
        ops_row = QHBoxLayout()
        self._rdo_replace = QRadioButton(tr('replace_element_btn'))
        self._rdo_qty     = QRadioButton(tr('edit_qty_only_btn'))
        self._rdo_both    = QRadioButton(tr('both_operations_btn'))
        self._rdo_both.setChecked(True)
        for rdo in (self._rdo_replace, self._rdo_qty, self._rdo_both):
            rdo.setStyleSheet(
                f"font-size:{FS_BASE}px; color:{_C['text_primary']};"
            )
            ops_row.addWidget(rdo)
        ops_row.addStretch()
        lay.addLayout(ops_row)

        # ── حقول البديل والكمية ──
        self._replace_frame = QFrame()
        self._update_frame_style(active=True)

        from PyQt5.QtWidgets import QFormLayout
        rf_lay = QFormLayout(self._replace_frame)
        rf_lay.setSpacing(OP_SECTION_FORM_SPACING)
        rf_lay.setLabelAlignment(Qt.AlignRight)

        self._cmb_replacement = QComboBox()
        self._cmb_replacement.setMinimumHeight(OP_SECTION_CMB_MIN_H)
        self._cmb_replacement.setMinimumWidth(OP_SECTION_CMB_MIN_W)
        self._cmb_replacement.setStyleSheet(
            f"background:{_C['bg_input']}; border:1px solid {_C['border']};"
            f"border-radius:{OP_SECTION_CMB_RADIUS}px;"
            f"padding:{OP_SECTION_CMB_PAD_V}px {OP_SECTION_CMB_PAD_H}px;"
            f"color:{_C['text_primary']};"
        )

        _child_labels = {
            "raw":        f"{tr('replacement_raw')}:",
            "labor_op":   f"{tr('replacement_labor_op')}:",
            "machine_op": f"{tr('replacement_machine_op')}:",
        }
        lbl_new = _child_labels.get(self._child_type, f"{tr('replacement')}:")
        rf_lay.addRow(lbl_new, self._cmb_replacement)

        qty_row = QHBoxLayout()
        self._chk_uniform = QCheckBox(
            f"{tr('apply_uniform_qty')}:"
        )
        self._chk_uniform.setStyleSheet(
            f"font-size:{FS_SM}px; color:{_C['text_primary']};"
        )
        self._sp_uniform = QDoubleSpinBox()
        self._sp_uniform.setRange(0.0001, 999999)
        self._sp_uniform.setDecimals(4)
        self._sp_uniform.setValue(1.0)
        self._sp_uniform.setFixedWidth(OP_SECTION_SP_W)
        self._sp_uniform.setEnabled(False)
        self._chk_uniform.toggled.connect(self._sp_uniform.setEnabled)
        qty_row.addWidget(self._chk_uniform)
        qty_row.addWidget(self._sp_uniform)
        qty_row.addStretch()
        rf_lay.addRow("", qty_row)
        lay.addWidget(self._replace_frame)

        for rdo in (self._rdo_replace, self._rdo_qty, self._rdo_both):
            rdo.toggled.connect(self._update_ui)
        self._update_ui()

    def _refresh_style(self, *_):
        self.setStyleSheet(f"""
            QGroupBox {{
                background: {_C['bg_input']};
                border: 1px solid {_C['border']};
                border-radius: {OP_SECTION_GRP_RADIUS}px;
                font-weight: bold;
                color: {_C['accent']};
                padding-top: {OP_SECTION_GRP_PAD_TOP}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top right;
                padding: 0 {OP_SECTION_GRP_TITLE_PAD_H}px;
            }}
        """)
        # تحديث لون الـ radio buttons عند تغيير الثيم
        if hasattr(self, '_rdo_replace'):
            for rdo in (self._rdo_replace, self._rdo_qty, self._rdo_both):
                rdo.setStyleSheet(
                    f"font-size:{FS_BASE}px; color:{_C['text_primary']};"
                )
        if hasattr(self, '_chk_uniform'):
            self._chk_uniform.setStyleSheet(
                f"font-size:{FS_SM}px; color:{_C['text_primary']};"
            )
        if hasattr(self, '_cmb_replacement'):
            self._cmb_replacement.setStyleSheet(
                f"background:{_C['bg_input']}; border:1px solid {_C['border']};"
                f"border-radius:{OP_SECTION_CMB_RADIUS}px;"
                f"padding:{OP_SECTION_CMB_PAD_V}px {OP_SECTION_CMB_PAD_H}px;"
                f"color:{_C['text_primary']};"
            )
        if hasattr(self, '_replace_frame'):
            self._update_frame_style(active=self.do_replace)

    def _refresh_lang(self, *_):
        self.setTitle(tr('operation_section_title'))
        if hasattr(self, '_rdo_replace'):
            self._rdo_replace.setText(tr('replace_element_btn'))
            self._rdo_qty.setText(tr('edit_qty_only_btn'))
            self._rdo_both.setText(tr('both_operations_btn'))
        if hasattr(self, '_chk_uniform'):
            self._chk_uniform.setText(f"{tr('apply_uniform_qty')}:")

    # ── خصائص الحالة ─────────────────────────────────────

    @property
    def do_replace(self) -> bool:
        return self._rdo_replace.isChecked() or self._rdo_both.isChecked()

    @property
    def do_qty(self) -> bool:
        return self._rdo_qty.isChecked() or self._rdo_both.isChecked()

    @property
    def new_child_id(self):
        data = self._cmb_replacement.currentData()
        if data in (None, "__sep__", "__empty__"):
            return None
        return data

    @property
    def uniform_qty(self) -> float | None:
        if self._chk_uniform.isChecked():
            return self._sp_uniform.value()
        return None

    # ── تحميل البيانات ────────────────────────────────────

    def load_candidates(self, candidates: list[tuple]):
        self._cmb_replacement.clear()
        self._cmb_replacement.addItem(f"— {tr('select_replacement')} —", None)

        if not candidates:
            self._cmb_replacement.addItem(tr("no_alternatives"), "__empty__")
            self._cmb_replacement.setEnabled(False)
            self._rdo_qty.setChecked(True)
            self._rdo_replace.setEnabled(False)
            self._rdo_both.setEnabled(False)
            return

        last_cat = object()
        for cid, cname, cat_name in candidates:
            if cat_name != last_cat:
                sep_text = f"─── {cat_name or tr('no_category')} ───"
                self._cmb_replacement.addItem(sep_text, "__sep__")
                idx   = self._cmb_replacement.count() - 1
                model = self._cmb_replacement.model()
                item  = model.item(idx)
                if item:
                    from PyQt5.QtCore import Qt as _Qt
                    item.setFlags(
                        item.flags() & ~_Qt.ItemIsEnabled & ~_Qt.ItemIsSelectable
                    )
                    item.setForeground(QColor(_C['text_muted']))
                    f = QFont()
                    f.setBold(True)
                    f.setPointSize(f.pointSize() - 1)
                    item.setFont(f)
                last_cat = cat_name
            self._cmb_replacement.addItem(f"{cid} — {cname}", cid)

    # ── مساعدات ──────────────────────────────────────────

    def _update_ui(self):
        show_replace = self.do_replace
        self._cmb_replacement.setEnabled(show_replace)
        self._update_frame_style(active=show_replace)

    def _update_frame_style(self, active: bool):
        if active:
            self._replace_frame.setStyleSheet(
                f"QFrame {{ background:{_C['info_bg']}; "
                f"border:1px solid {_C['info_border']};"
                f"border-radius:{OP_SECTION_FRAME_RADIUS}px;"
                f"padding:{OP_SECTION_FRAME_PAD}px; }}"
            )
        else:
            self._replace_frame.setStyleSheet(
                f"QFrame {{ background:{_C['bg_surface']}; "
                f"border:1px solid {_C['border']};"
                f"border-radius:{OP_SECTION_FRAME_RADIUS}px;"
                f"padding:{OP_SECTION_FRAME_PAD}px; }}"
            )
