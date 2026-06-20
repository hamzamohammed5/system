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


class _OperationSection(QGroupBox):
    """
    قسم اختيار العملية في نافذة الاستبدال الشامل.

    الوصول للحالة:
        .do_replace   → bool
        .do_qty       → bool
        .new_child_id → int | None
        .uniform_qty  → float | None
    """

    def __init__(self, child_type: str, parent=None):
        super().__init__(f"⚙️  {tr('operation_required')}", parent)
        self._child_type = child_type
        self._build()

    def _build(self):
        self._apply_group_style()

        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        # ── خيارات العملية ──
        ops_row = QHBoxLayout()
        self._rdo_replace = QRadioButton(f"🔀  {tr('replace_element')}")
        self._rdo_qty     = QRadioButton(f"🔢  {tr('edit_qty_only')}")
        self._rdo_both    = QRadioButton(f"✅  {tr('both_operations')}")
        self._rdo_both.setChecked(True)
        for rdo in (self._rdo_replace, self._rdo_qty, self._rdo_both):
            rdo.setStyleSheet(
                f"font-size:12px; color:{_C['text_primary']};"
            )
            ops_row.addWidget(rdo)
        ops_row.addStretch()
        lay.addLayout(ops_row)

        # ── حقول البديل والكمية ──
        self._replace_frame = QFrame()
        self._update_frame_style(active=True)

        from PyQt5.QtWidgets import QFormLayout
        rf_lay = QFormLayout(self._replace_frame)
        rf_lay.setSpacing(8)
        rf_lay.setLabelAlignment(Qt.AlignRight)

        self._cmb_replacement = QComboBox()
        self._cmb_replacement.setMinimumHeight(32)
        self._cmb_replacement.setMinimumWidth(280)
        self._cmb_replacement.setStyleSheet(
            f"background:{_C['bg_input']}; border:1px solid {_C['border']};"
            f"border-radius:4px; padding:2px 6px; color:{_C['text_primary']};"
        )

        _child_labels = {
            "raw":        f"🧱  {tr('replacement_raw')}:",
            "labor_op":   f"👷  {tr('replacement_labor_op')}:",
            "machine_op": f"⚙️  {tr('replacement_machine_op')}:",
        }
        lbl_new = _child_labels.get(self._child_type, f"{tr('replacement')}:")
        rf_lay.addRow(lbl_new, self._cmb_replacement)

        qty_row = QHBoxLayout()
        self._chk_uniform = QCheckBox(
            f"{tr('apply_uniform_qty')}:"
        )
        self._chk_uniform.setStyleSheet(
            f"font-size:11px; color:{_C['text_primary']};"
        )
        self._sp_uniform = QDoubleSpinBox()
        self._sp_uniform.setRange(0.0001, 999999)
        self._sp_uniform.setDecimals(4)
        self._sp_uniform.setValue(1.0)
        self._sp_uniform.setFixedWidth(100)
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

    def _apply_group_style(self):
        self.setStyleSheet(f"""
            QGroupBox {{
                background: {_C['bg_input']};
                border: 1px solid {_C['border']};
                border-radius: 8px;
                font-weight: bold;
                color: {_C['accent']};
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top right;
                padding: 0 8px;
            }}
        """)

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
                "border-radius:6px; padding:4px; }"
            )
        else:
            self._replace_frame.setStyleSheet(
                f"QFrame {{ background:{_C['bg_surface']}; "
                f"border:1px solid {_C['border']};"
                "border-radius:6px; padding:4px; }"
            )