"""
ui/tabs/costing/shared/bulk_replace/_operation_section.py
==========================================================
_OperationSection — قسم اختيار العملية في نافذة الاستبدال الشامل.

يعرض:
  - خيارات العملية (استبدال / تعديل كمية / الاثنين)
  - حقل اختيار العنصر البديل
  - حقل الكمية الموحدة الاختياري
"""

from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QDoubleSpinBox, QCheckBox,
    QRadioButton, QFrame,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor, QFont


class _OperationSection(QGroupBox):
    """
    قسم اختيار العملية في نافذة الاستبدال الشامل.

    الوصول للحالة:
        .do_replace   → bool
        .do_qty       → bool
        .new_child_id → int | None
        .uniform_qty  → float | None  (None = غير موحدة)
    """

    def __init__(self, child_type: str, parent=None):
        super().__init__("⚙️  العملية المطلوبة", parent)
        self._child_type = child_type
        self._build()

    def _build(self):
        self.setStyleSheet("""
            QGroupBox {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                font-weight: bold;
                color: #1565c0;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top right;
                padding: 0 8px;
            }
        """)

        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        # ── خيارات العملية ──
        ops_row = QHBoxLayout()
        self._rdo_replace = QRadioButton("🔀  استبدال العنصر")
        self._rdo_qty     = QRadioButton("🔢  تعديل الكمية فقط")
        self._rdo_both    = QRadioButton("✅  الاثنين معاً")
        self._rdo_both.setChecked(True)
        for rdo in (self._rdo_replace, self._rdo_qty, self._rdo_both):
            rdo.setStyleSheet("font-size:12px;")
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

        lbl_new = {
            "raw":        "🧱  الخامة البديلة :",
            "labor_op":   "👷  العملية البديلة :",
            "machine_op": "⚙️  العملية البديلة :",
        }.get(self._child_type, "البديل :")
        rf_lay.addRow(lbl_new, self._cmb_replacement)

        qty_row = QHBoxLayout()
        self._chk_uniform = QCheckBox("تطبيق كمية موحدة على المنتجات المختارة:")
        self._chk_uniform.setStyleSheet("font-size:11px;")
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

        # ربط الـ radio buttons
        for rdo in (self._rdo_replace, self._rdo_qty, self._rdo_both):
            rdo.toggled.connect(self._update_ui)
        self._update_ui()

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
        """
        يملأ combo البديل بالعناصر البديلة.

        candidates: list of (id, name, category_name)
        """
        self._cmb_replacement.clear()
        self._cmb_replacement.addItem("— اختر البديل —", None)

        if not candidates:
            self._cmb_replacement.addItem("لا توجد عناصر بديلة", "__empty__")
            self._cmb_replacement.setEnabled(False)
            self._rdo_qty.setChecked(True)
            self._rdo_replace.setEnabled(False)
            self._rdo_both.setEnabled(False)
            return

        last_cat = object()
        for cid, cname, cat_name in candidates:
            if cat_name != last_cat:
                sep_text = f"─── {cat_name or 'بدون تصنيف'} ───"
                self._cmb_replacement.addItem(sep_text, "__sep__")
                idx   = self._cmb_replacement.count() - 1
                model = self._cmb_replacement.model()
                item  = model.item(idx)
                if item:
                    from PyQt5.QtCore import Qt as _Qt
                    item.setFlags(
                        item.flags() & ~_Qt.ItemIsEnabled & ~_Qt.ItemIsSelectable
                    )
                    item.setForeground(QColor("#78909c"))
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
                "QFrame { background:#f8fbff; border:1px solid #bbdefb;"
                "border-radius:6px; padding:4px; }"
            )
        else:
            self._replace_frame.setStyleSheet(
                "QFrame { background:#f5f5f5; border:1px solid #e0e0e0;"
                "border-radius:6px; padding:4px; }"
            )