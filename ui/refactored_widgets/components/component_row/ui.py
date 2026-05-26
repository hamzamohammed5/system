"""
ui/widgets/components/component_row/ui.py
=====================================================
بناء واجهة ComponentRow.

مستخرج من widgets/shared/component_row/_row_ui.py مع:
  - تنظيف الـ styles في ثوابت منفصلة
  - دالة واحدة build_row_ui() تبني كل الـ UI
  - _update_waste_style() منفصلة وأوضح
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit,
    QPushButton, QSizePolicy, QLabel, QDoubleSpinBox, QFrame,
)

from ui.widgets.utils.searchable_combo import SearchableCombo

# ── أنواع المكونات ─────────────────────────────────────────
COMPONENT_TYPES = [
    ("raw",        "🧱 خامة"),
    ("semi",       "🔧 نصف مصنع"),
    ("labor_op",   "👷 عملية عمالة"),
    ("machine_op", "⚙️ عملية تشغيل"),
]

# ── ستايلات الصف ───────────────────────────────────────────
STYLE_NORMAL = ""
STYLE_ORPHAN = """
    QWidget { background-color: #fff3e0; border-radius: 4px; }
    QComboBox, QLineEdit {
        background-color: #fff3e0;
        border: 1.5px solid #e65100;
        border-radius: 4px;
    }
"""

# ── ستايلات الـ variant combo ──────────────────────────────
_VARIANT_COMBO_STYLE = """
    QComboBox {
        background: #e8f5e9; border: 1px solid #a5d6a7;
        border-radius: 4px; padding: 1px 6px;
        font-size: 11px; color: #2e7d32;
    }
    QComboBox:focus { border-color: #2e7d32; }
    QComboBox::drop-down { border: none; }
"""

_VARIANT_COST_STYLE = (
    "font-size:10px; color:#2e7d32; font-weight:bold;"
    "background:#f1f8e9; border:1px solid #c8e6c9;"
    "border-radius:3px; padding:1px 5px;"
)

# ── ستايلات الـ op_row ─────────────────────────────────────
_SUB_ROW_STYLE = """
    QFrame {
        background: #fce4ec; border: 1px solid #f48fb1;
        border-radius: 4px; margin-right: 4px;
    }
"""
_OP_ROW_COMBO_STYLE = """
    QComboBox {
        background: white; border: 1px solid #f48fb1;
        border-radius: 4px; padding: 1px 6px;
        font-size: 11px; color: #880e4f;
    }
    QComboBox:focus { border-color: #880e4f; }
    QComboBox::drop-down { border: none; }
"""

# ── ستايلات الـ waste ──────────────────────────────────────
_WASTE_BASE = """
    QDoubleSpinBox {
        background: #fff8e1; border: 1px solid #ffe082;
        border-radius: 4px; padding: 1px 4px;
        font-size: 11px; color: #e65100;
    }
    QDoubleSpinBox:focus { border-color: #ff8f00; background: #fffde7; }
"""
_WASTE_ZERO = """
    QDoubleSpinBox {
        background: #f5f5f5; border: 1px solid #e0e0e0;
        border-radius: 4px; padding: 1px 4px;
        font-size: 11px; color: #999;
    }
    QDoubleSpinBox:focus {
        border-color: #ffe082; background: #fff8e1; color: #e65100;
    }
"""
_WASTE_COLORS = {
    "high":   ("#ffcdd2", "#e53935"),
    "medium": ("#ffe0b2", "#f57c00"),
    "low":    ("#fff8e1", "#ffe082"),
}


def build_row_ui(widget, child_type: str, child_id,
                 qty: float, raw_total_qty,
                 waste_pct: float, variant_id,
                 machine_op_row_id, show_total_qty: bool):
    """
    يبني كامل واجهة ComponentRow على الـ widget المعطى.
    يضيف كل الـ attributes مباشرة على widget.
    """
    outer = QVBoxLayout(widget)
    outer.setContentsMargins(0, 2, 0, 2)
    outer.setSpacing(2)

    # ── الصف الرئيسي ──────────────────────────────────────
    main_row = QHBoxLayout()
    main_row.setContentsMargins(0, 0, 0, 0)
    main_row.setSpacing(6)

    _build_type_combo(widget, child_type, main_row)
    _build_item_combo(widget, main_row)
    _build_variant_widgets(widget, main_row)
    _build_qty_widget(widget, qty, main_row)
    _build_waste_widget(widget, waste_pct, main_row)
    _build_total_qty_widget(widget, raw_total_qty, show_total_qty, main_row)
    _build_delete_button(widget, main_row)

    outer.addLayout(main_row)

    # ── صف عملية التشغيل ──────────────────────────────────
    _build_sub_row(widget, outer)


# ── بناء المكونات الفردية ──────────────────────────────────

def _build_type_combo(widget, child_type: str, layout: QHBoxLayout):
    widget.cmb_type = QComboBox()
    widget.cmb_type.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    widget.cmb_type.setMinimumContentsLength(10)
    widget.cmb_type.setSizeAdjustPolicy(QComboBox.AdjustToContents)
    for key, label in COMPONENT_TYPES:
        widget.cmb_type.addItem(label, key)

    # تحديد النوع الأولي
    widget.cmb_type.blockSignals(True)
    idx = next((i for i, (k, _) in enumerate(COMPONENT_TYPES) if k == child_type), 0)
    widget.cmb_type.setCurrentIndex(idx)
    widget.cmb_type.blockSignals(False)

    layout.addWidget(widget.cmb_type)


def _build_item_combo(widget, layout: QHBoxLayout):
    widget._item_combo = SearchableCombo()
    widget._item_combo.item_selected.connect(widget._on_item_selected)
    layout.addWidget(widget._item_combo, stretch=1)


def _build_variant_widgets(widget, layout: QHBoxLayout):
    widget.cmb_variant = QComboBox()
    widget.cmb_variant.setMinimumHeight(26)
    widget.cmb_variant.setMinimumWidth(130)
    widget.cmb_variant.setMaximumWidth(180)
    widget.cmb_variant.setToolTip(
        "وحدة الإنتاج — تكلفة الوحدة = سعر الخامة ÷ عدد القطع"
    )
    widget.cmb_variant.setStyleSheet(_VARIANT_COMBO_STYLE)
    widget.cmb_variant.setVisible(False)
    widget.cmb_variant.currentIndexChanged.connect(widget._on_variant_changed)

    widget.lbl_variant_cost = QLabel()
    widget.lbl_variant_cost.setStyleSheet(_VARIANT_COST_STYLE)
    widget.lbl_variant_cost.setVisible(False)

    layout.addWidget(widget.cmb_variant)
    layout.addWidget(widget.lbl_variant_cost)


def _build_qty_widget(widget, qty: float, layout: QHBoxLayout):
    widget.qty_edit = QLineEdit()
    widget.qty_edit.setPlaceholderText("الكمية")
    widget.qty_edit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    widget.qty_edit.setMinimumWidth(60)
    widget.qty_edit.setMaximumWidth(90)
    widget.qty_edit.setText(str(qty) if qty else "")
    layout.addWidget(widget.qty_edit)


def _build_waste_widget(widget, waste_pct: float, layout: QHBoxLayout):
    widget.waste_spin = QDoubleSpinBox()
    widget.waste_spin.setRange(0, 100)
    widget.waste_spin.setDecimals(1)
    widget.waste_spin.setSuffix(" %")
    widget.waste_spin.setValue(waste_pct or 0.0)
    widget.waste_spin.setMinimumWidth(75)
    widget.waste_spin.setMaximumWidth(90)
    widget.waste_spin.setMinimumHeight(26)
    widget.waste_spin.setToolTip(
        "نسبة الهادر %\nمثال: 10% → الكمية الفعلية = الكمية × 1.10"
    )
    widget.waste_spin.valueChanged.connect(widget._on_waste_changed)

    widget.lbl_waste = QLabel("⚠️")
    widget.lbl_waste.setFixedWidth(18)
    widget.lbl_waste.setStyleSheet(
        "color:#e65100; font-size:11px; background:transparent;"
    )
    widget.lbl_waste.setToolTip("نسبة الهادر")

    update_waste_style(widget, waste_pct or 0.0)

    layout.addWidget(widget.lbl_waste)
    layout.addWidget(widget.waste_spin)


def _build_total_qty_widget(widget, raw_total_qty,
                             show_total_qty: bool, layout: QHBoxLayout):
    widget.total_qty_edit = QLineEdit()
    widget.total_qty_edit.setPlaceholderText("الكلي")
    widget.total_qty_edit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    widget.total_qty_edit.setMinimumWidth(60)
    widget.total_qty_edit.setMaximumWidth(90)
    widget.total_qty_edit.setToolTip("الكمية الكلية للخامة.")
    if raw_total_qty is not None:
        widget.total_qty_edit.setText(str(raw_total_qty))

    widget.lbl_total_qty = QLabel("÷")
    widget.lbl_total_qty.setStyleSheet("color:#888; font-size:11px;")
    widget.lbl_total_qty.setFixedWidth(14)

    if show_total_qty:
        layout.addWidget(widget.lbl_total_qty)
        layout.addWidget(widget.total_qty_edit)
    else:
        widget.lbl_total_qty.setVisible(False)
        widget.total_qty_edit.setVisible(False)


def _build_delete_button(widget, layout: QHBoxLayout):
    btn = QPushButton("❌")
    btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    btn.setFixedWidth(32)
    btn.clicked.connect(lambda: widget.removed.emit(widget))
    layout.addWidget(btn)


def _build_sub_row(widget, outer: QVBoxLayout):
    """يبني صف عملية التشغيل الفرعي."""
    widget._sub_row_widget = QFrame()
    widget._sub_row_widget.setStyleSheet(_SUB_ROW_STYLE)

    sub_layout = QHBoxLayout(widget._sub_row_widget)
    sub_layout.setContentsMargins(8, 3, 8, 3)
    sub_layout.setSpacing(8)

    lbl_icon = QLabel("↳ صف العملية:")
    lbl_icon.setStyleSheet(
        "color:#880e4f; font-weight:bold; font-size:11px;"
        "background:transparent; border:none;"
    )
    sub_layout.addWidget(lbl_icon)

    widget.cmb_op_row = QComboBox()
    widget.cmb_op_row.setMinimumHeight(26)
    widget.cmb_op_row.setMinimumWidth(280)
    widget.cmb_op_row.setStyleSheet(_OP_ROW_COMBO_STYLE)
    widget.cmb_op_row.currentIndexChanged.connect(widget._on_op_row_changed)
    sub_layout.addWidget(widget.cmb_op_row, stretch=1)

    widget.lbl_op_row_cost = QLabel()
    widget.lbl_op_row_cost.setStyleSheet(
        "font-size:11px; color:#880e4f; font-weight:bold;"
        "background:transparent; border:none;"
    )
    sub_layout.addWidget(widget.lbl_op_row_cost)
    sub_layout.addStretch()

    widget._sub_row_widget.setVisible(False)
    outer.addWidget(widget._sub_row_widget)


# ── تحديث ستايل الهادر ────────────────────────────────────

def update_waste_style(widget, val: float):
    """يحدّث ستايل الـ waste spinbox حسب القيمة."""
    if val > 0:
        widget.lbl_waste.setVisible(True)
        if val >= 20:
            bg, border = _WASTE_COLORS["high"]
        elif val >= 10:
            bg, border = _WASTE_COLORS["medium"]
        else:
            bg, border = _WASTE_COLORS["low"]

        widget.waste_spin.setStyleSheet(f"""
            QDoubleSpinBox {{
                background: {bg}; border: 1px solid {border};
                border-radius: 4px; padding: 1px 4px;
                font-size: 11px; color: #e65100; font-weight: bold;
            }}
            QDoubleSpinBox:focus {{ border-color: #ff8f00; }}
        """)
    else:
        widget.lbl_waste.setVisible(False)
        widget.waste_spin.setStyleSheet(_WASTE_ZERO)