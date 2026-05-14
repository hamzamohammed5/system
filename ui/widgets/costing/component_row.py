"""
ui/widgets/costing/component_row.py
=====================================
الإصلاحات في هذا الملف:

1. _load_op_rows: استخدام QTimer.singleShot مثل raw variants تماماً
   - لأن الـ widget مش بيكون visible وقت الـ build
   - بعض Qt versions مش بترجع currentData() صح لو الـ widget مش shown بعد
   
2. _load_op_rows: استدعاء _on_op_row_changed() يدوياً بعد blockSignals(False)
   - عشان تُحدَّث تكلفة الصف في الـ label فوراً
   
3. _build: تحميل machine_op rows في QTimer مثل raw variants
   - ضمان إن الـ widget اتبنى خالص قبل التحميل
   
4. _pinned_op_row_id: بيتحدث في كل نقطة ممكنة
"""

import weakref
from PyQt5 import sip

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit,
    QPushButton, QSizePolicy, QLabel, QDoubleSpinBox, QFrame,
)
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtGui  import QColor

from ui.widgets.shared.searchable_combo import _SearchableCombo, _build_grouped_items
from ui.events import bus

_TYPES = [
    ("raw",        "🧱 خامة"),
    ("semi",       "🔧 نصف مصنع"),
    ("labor_op",   "👷 عملية عمالة"),
    ("machine_op", "⚙️ عملية تشغيل"),
]

_STYLE_NORMAL = ""
_STYLE_ORPHAN = """
    QWidget { background-color: #fff3e0; border-radius: 4px; }
    QComboBox, QLineEdit {
        background-color: #fff3e0;
        border: 1.5px solid #e65100;
        border-radius: 4px;
    }
"""


class ComponentRow(QWidget):
    removed = pyqtSignal(QWidget)

    def __init__(self, catalog_fn, child_type: str = "raw",
                 child_id=None, qty: float = 1.0,
                 waste_pct: float = 0.0,
                 raw_total_qty: float = None,
                 show_total_qty: bool = False,
                 variant_id: int = None,
                 machine_op_row_id: int = None,
                 parent=None):
        super().__init__(parent)
        self._catalog_fn     = catalog_fn
        self._show_total_qty = show_total_qty
        self._is_orphan      = False
        self._orphan_id      = None
        self._orphan_type    = None
        self._orphan_name    = None

        self._pinned_type          = child_type
        self._pinned_id            = child_id
        self._pinned_total_qty     = raw_total_qty
        self._pinned_variant       = variant_id

        # _pinned_op_row_id هو المصدر الوحيد الموثوق لـ machine_op_row_id
        # بيُحدَّث في كل تغيير (من المستخدم أو من التحميل)
        self._pinned_op_row_id     = machine_op_row_id

        # نحفظ القيم للاستخدام في QTimer callbacks
        self._init_child_type       = child_type
        self._init_child_id         = child_id
        self._init_machine_op_row_id = machine_op_row_id

        self._build(child_type, child_id, qty, raw_total_qty,
                    waste_pct, variant_id, machine_op_row_id)
        QTimer.singleShot(0, self._connect_signal)

    def _connect_signal(self):
        bus.data_changed.connect(
            lambda: QTimer.singleShot(0, self._on_catalog_changed)
        )

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self, child_type, child_id, qty, raw_total_qty,
               waste_pct=0.0, variant_id=None, machine_op_row_id=None):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 2, 0, 2)
        outer.setSpacing(2)

        main_row = QHBoxLayout()
        main_row.setContentsMargins(0, 0, 0, 0)
        main_row.setSpacing(6)

        self.cmb_type = QComboBox()
        self.cmb_type.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.cmb_type.setMinimumContentsLength(10)
        self.cmb_type.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        for key, label in _TYPES:
            self.cmb_type.addItem(label, key)

        self._item_combo = _SearchableCombo()
        self._item_combo.item_selected.connect(self._on_item_selected)

        self.cmb_variant = QComboBox()
        self.cmb_variant.setMinimumHeight(26)
        self.cmb_variant.setMinimumWidth(130)
        self.cmb_variant.setMaximumWidth(180)
        self.cmb_variant.setToolTip("وحدة الإنتاج — تكلفة الوحدة = سعر الخامة ÷ عدد القطع")
        self.cmb_variant.setStyleSheet("""
            QComboBox {
                background: #e8f5e9;
                border: 1px solid #a5d6a7;
                border-radius: 4px;
                padding: 1px 6px;
                font-size: 11px;
                color: #2e7d32;
            }
            QComboBox:focus { border-color: #2e7d32; }
            QComboBox::drop-down { border: none; }
        """)
        self.cmb_variant.setVisible(False)
        self.cmb_variant.currentIndexChanged.connect(self._on_variant_changed)

        self.lbl_variant_cost = QLabel()
        self.lbl_variant_cost.setStyleSheet(
            "font-size:10px; color:#2e7d32; font-weight:bold;"
            "background:#f1f8e9; border:1px solid #c8e6c9;"
            "border-radius:3px; padding:1px 5px;"
        )
        self.lbl_variant_cost.setVisible(False)

        self.qty_edit = QLineEdit()
        self.qty_edit.setPlaceholderText("الكمية")
        self.qty_edit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.qty_edit.setMinimumWidth(60)
        self.qty_edit.setMaximumWidth(90)
        self.qty_edit.setText(str(qty) if qty else "")

        self.waste_spin = QDoubleSpinBox()
        self.waste_spin.setRange(0, 100)
        self.waste_spin.setDecimals(1)
        self.waste_spin.setSuffix(" %")
        self.waste_spin.setValue(waste_pct or 0.0)
        self.waste_spin.setMinimumWidth(75)
        self.waste_spin.setMaximumWidth(90)
        self.waste_spin.setMinimumHeight(26)
        self.waste_spin.setToolTip("نسبة الهادر %\nمثال: 10% → الكمية الفعلية = الكمية × 1.10")
        self.waste_spin.setStyleSheet("""
            QDoubleSpinBox {
                background: #fff8e1; border: 1px solid #ffe082;
                border-radius: 4px; padding: 1px 4px;
                font-size: 11px; color: #e65100;
            }
            QDoubleSpinBox:focus { border-color: #ff8f00; background: #fffde7; }
        """)

        self.lbl_waste = QLabel("⚠️")
        self.lbl_waste.setFixedWidth(18)
        self.lbl_waste.setStyleSheet(
            "color: #e65100; font-size: 11px; background:transparent;"
        )
        self.lbl_waste.setToolTip("نسبة الهادر")
        self.waste_spin.valueChanged.connect(self._on_waste_changed)
        self._update_waste_style(waste_pct or 0.0)

        self.total_qty_edit = QLineEdit()
        self.total_qty_edit.setPlaceholderText("الكلي")
        self.total_qty_edit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.total_qty_edit.setMinimumWidth(60)
        self.total_qty_edit.setMaximumWidth(90)
        self.total_qty_edit.setToolTip("الكمية الكلية للخامة.\nسعر الوحدة = السعر الكلي ÷ هذا الرقم.")
        if raw_total_qty is not None:
            self.total_qty_edit.setText(str(raw_total_qty))

        self.lbl_total_qty = QLabel("÷")
        self.lbl_total_qty.setStyleSheet("color: #888; font-size: 11px;")
        self.lbl_total_qty.setFixedWidth(14)

        del_btn = QPushButton("❌")
        del_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        del_btn.setFixedWidth(32)
        del_btn.clicked.connect(lambda: self.removed.emit(self))

        main_row.addWidget(self.cmb_type)
        main_row.addWidget(self._item_combo, stretch=1)
        main_row.addWidget(self.cmb_variant)
        main_row.addWidget(self.lbl_variant_cost)
        main_row.addWidget(self.qty_edit)
        main_row.addWidget(self.lbl_waste)
        main_row.addWidget(self.waste_spin)

        if self._show_total_qty:
            main_row.addWidget(self.lbl_total_qty)
            main_row.addWidget(self.total_qty_edit)
        else:
            self.lbl_total_qty.setVisible(False)
            self.total_qty_edit.setVisible(False)

        main_row.addWidget(del_btn)
        outer.addLayout(main_row)

        # ── السطر الفرعي لصفوف عملية التشغيل ──
        self._sub_row_widget = QFrame()
        self._sub_row_widget.setStyleSheet("""
            QFrame {
                background: #fce4ec;
                border: 1px solid #f48fb1;
                border-radius: 4px;
                margin-right: 4px;
            }
        """)
        sub_layout = QHBoxLayout(self._sub_row_widget)
        sub_layout.setContentsMargins(8, 3, 8, 3)
        sub_layout.setSpacing(8)

        lbl_row_icon = QLabel("↳ صف العملية:")
        lbl_row_icon.setStyleSheet(
            "color:#880e4f; font-weight:bold; font-size:11px;"
            "background:transparent; border:none;"
        )
        sub_layout.addWidget(lbl_row_icon)

        self.cmb_op_row = QComboBox()
        self.cmb_op_row.setMinimumHeight(26)
        self.cmb_op_row.setMinimumWidth(280)
        self.cmb_op_row.setToolTip(
            "صف العملية — اختر الصف المطلوب\n"
            "التكلفة = (قيمة × معدل التشغيل) ÷ العدد"
        )
        self.cmb_op_row.setStyleSheet("""
            QComboBox {
                background: white;
                border: 1px solid #f48fb1;
                border-radius: 4px;
                padding: 1px 6px;
                font-size: 11px;
                color: #880e4f;
            }
            QComboBox:focus { border-color: #880e4f; }
            QComboBox::drop-down { border: none; }
        """)
        self.cmb_op_row.currentIndexChanged.connect(self._on_op_row_changed)
        sub_layout.addWidget(self.cmb_op_row, stretch=1)

        self.lbl_op_row_cost = QLabel()
        self.lbl_op_row_cost.setStyleSheet(
            "font-size:11px; color:#880e4f; font-weight:bold;"
            "background:transparent; border:none;"
        )
        sub_layout.addWidget(self.lbl_op_row_cost)
        sub_layout.addStretch()

        self._sub_row_widget.setVisible(False)
        outer.addWidget(self._sub_row_widget)

        # تحديد النوع
        self.cmb_type.blockSignals(True)
        idx = next((i for i, (k, _) in enumerate(_TYPES) if k == child_type), 0)
        self.cmb_type.setCurrentIndex(idx)
        self.cmb_type.blockSignals(False)

        self._fill_items(child_type, selected_id=child_id)
        self._update_total_qty_visibility(child_type)

        self.cmb_type.currentIndexChanged.connect(self._on_type_changed)

        # ✅ الإصلاح الرئيسي: نستخدم QTimer.singleShot لكلا النوعين
        # عشان نضمن إن الـ widget اتبنى خالص وأُضيف للـ layout
        if child_type == "raw" and child_id is not None:
            _weak = weakref.ref(self)
            _cid, _vid = child_id, variant_id
            QTimer.singleShot(50, lambda: (s := _weak()) and s._load_variants(_cid, _vid))

        elif child_type == "machine_op" and child_id is not None:
            # ✅ استخدام QTimer مثل raw variants - يضمن الـ widget جاهز
            _weak = weakref.ref(self)
            _op_id = child_id
            _row_id = machine_op_row_id
            QTimer.singleShot(50, lambda: (s := _weak()) and s._load_op_rows(_op_id, _row_id))

    # ══════════════════════════════════════════════════════
    # ✅ Op Rows - الإصلاح الكامل
    # ══════════════════════════════════════════════════════

    def _load_op_rows(self, op_id: int, selected_row_id: int = None):
        """
        يملأ cmb_op_row بصفوف العملية.

        الإصلاحات:
        1. لا placeholder — كل الصفوف تُعرض مباشرة
        2. بعد setCurrentIndex نستخرج القيمة ونحفظها في _pinned_op_row_id
        3. selected_row_id له الأولوية دائماً
        4. ✅ بعد blockSignals(False) نستدعي _on_op_row_changed يدوياً
           عشان يتحدث الـ label ويُسجَّل الاختيار
        """
        try:
            if sip.isdeleted(self) or sip.isdeleted(self.cmb_op_row):
                return
        except Exception:
            return

        if op_id is None:
            self._hide_op_rows()
            return

        try:
            from db.machine_op_rows_repo import fetch_op_rows, calc_op_row_cost
            conn = self._get_conn()
            if conn is None:
                self._hide_op_rows()
                return
            rows = fetch_op_rows(conn, op_id)
        except Exception:
            self._hide_op_rows()
            return

        if not rows:
            self._hide_op_rows()
            return

        # الأولوية: selected_row_id > _pinned_op_row_id
        target_id = selected_row_id if selected_row_id is not None else self._pinned_op_row_id

        self.cmb_op_row.blockSignals(True)
        self.cmb_op_row.clear()

        # لا placeholder — نملأ الصفوف مباشرة
        for row in rows:
            try:
                conn2 = self._get_conn()
                cost = calc_op_row_cost(conn2, row["id"]) if conn2 else 0.0
            except Exception:
                cost = 0.0
            label = row["label"] or f"صف {row['id']}"
            display = f"{label}  ({row['value']:.4g} ÷ {row['count']:.4g})  ≈ {cost:.3f} ج"
            self.cmb_op_row.addItem(display, row["id"])

        # محاولة استعادة الاختيار المستهدف
        restored = False
        if target_id is not None:
            for i in range(self.cmb_op_row.count()):
                if self.cmb_op_row.itemData(i) == target_id:
                    self.cmb_op_row.setCurrentIndex(i)
                    restored = True
                    break

        if not restored:
            if self.cmb_op_row.count() > 0:
                self.cmb_op_row.setCurrentIndex(0)

        # ✅ المفتاح: نحفظ القيمة الفعلية المختارة الآن في _pinned_op_row_id
        current_data = self.cmb_op_row.currentData()
        if current_data is not None:
            self._pinned_op_row_id = current_data

        # ✅ الإصلاح: نفعّل الـ signals أولاً ثم نستدعي handler يدوياً
        self.cmb_op_row.blockSignals(False)
        self._sub_row_widget.setVisible(True)

        # ✅ استدعاء يدوي عشان يُحدَّث الـ label فوراً بعد التحميل
        self._update_op_row_cost_label()

    def _hide_op_rows(self):
        try:
            if sip.isdeleted(self) or sip.isdeleted(self._sub_row_widget):
                return
        except Exception:
            return
        self._sub_row_widget.setVisible(False)

    def _on_op_row_changed(self, _index: int = 0):
        """
        المستخدم اختار صفاً → نحدّث _pinned_op_row_id فوراً.
        """
        try:
            if sip.isdeleted(self) or sip.isdeleted(self.cmb_op_row):
                return
        except Exception:
            return

        row_id = self.cmb_op_row.currentData()
        if row_id is not None:
            self._pinned_op_row_id = row_id
        self._update_op_row_cost_label()

    def _update_op_row_cost_label(self):
        try:
            if sip.isdeleted(self) or sip.isdeleted(self.cmb_op_row):
                return
        except Exception:
            return

        # نعتمد على _pinned_op_row_id كمصدر أساسي
        row_id = self._pinned_op_row_id
        # تحقق إضافي من currentData
        current = self.cmb_op_row.currentData()
        if current is not None:
            row_id = current
            # نحدث _pinned أيضاً لو اختلف
            if current != self._pinned_op_row_id:
                self._pinned_op_row_id = current

        if row_id is None:
            self.lbl_op_row_cost.setText("")
            return
        try:
            from db.machine_op_rows_repo import calc_op_row_cost
            conn = self._get_conn()
            if conn:
                cost = calc_op_row_cost(conn, row_id)
                self.lbl_op_row_cost.setText(f"= {cost:.4f} ج/قطعة")
        except Exception:
            self.lbl_op_row_cost.setText("")

    # ══════════════════════════════════════════════════════
    # Variants
    # ══════════════════════════════════════════════════════

    def _load_variants(self, item_id: int, selected_variant_id: int = None):
        try:
            if sip.isdeleted(self) or sip.isdeleted(self.cmb_variant):
                return
        except Exception:
            return

        if item_id is None:
            self._hide_variants()
            return
        try:
            from db.raw_variants_repo import fetch_variants_for_item
            conn = self._get_conn()
            if conn is None:
                self._hide_variants()
                return
            variants = fetch_variants_for_item(conn, item_id)
        except Exception:
            self._hide_variants()
            return
        if not variants:
            self._hide_variants()
            return

        item_price = self._get_item_price(item_id)
        self.cmb_variant.blockSignals(True)
        self.cmb_variant.clear()
        self.cmb_variant.addItem("─ بدون variant ─", None)
        for var in variants:
            pieces = float(var["pieces"])
            if pieces > 0 and item_price > 0:
                unit_cost = item_price / pieces
                label = f"📐 {var['name']}  ({pieces:.4g} قطعة → {unit_cost:.3f} ج/قطعة)"
            else:
                label = f"📐 {var['name']}  ({var['pieces']:.4g} قطعة)"
            self.cmb_variant.addItem(label, var["id"])

        if selected_variant_id is not None:
            for i in range(self.cmb_variant.count()):
                if self.cmb_variant.itemData(i) == selected_variant_id:
                    self.cmb_variant.setCurrentIndex(i)
                    break
        self.cmb_variant.blockSignals(False)
        self.cmb_variant.setVisible(True)
        self._update_variant_cost_label()

    def _hide_variants(self):
        self.cmb_variant.setVisible(False)
        self.lbl_variant_cost.setVisible(False)

    def _on_variant_changed(self):
        self._update_variant_cost_label()

    def _update_variant_cost_label(self):
        variant_id = self.cmb_variant.currentData()
        if variant_id is None:
            self.lbl_variant_cost.setVisible(False)
            return
        item_id = self._get_current_raw_id()
        if item_id is None:
            self.lbl_variant_cost.setVisible(False)
            return
        try:
            from db.raw_variants_repo import fetch_variant
            conn = self._get_conn()
            if not conn:
                self.lbl_variant_cost.setVisible(False)
                return
            var = fetch_variant(conn, variant_id)
            if not var:
                self.lbl_variant_cost.setVisible(False)
                return
            item_price = self._get_item_price(item_id)
            pieces = float(var["pieces"])
            if pieces > 0 and item_price > 0:
                unit_cost = item_price / pieces
                self.lbl_variant_cost.setText(f"= {unit_cost:.3f} ج")
                self.lbl_variant_cost.setVisible(True)
            else:
                self.lbl_variant_cost.setVisible(False)
        except Exception:
            self.lbl_variant_cost.setVisible(False)

    # ══════════════════════════════════════════════════════
    # مساعدات
    # ══════════════════════════════════════════════════════

    def _get_conn(self):
        try:
            from db.connection import get_connection
            return get_connection()
        except Exception:
            return None

    def _get_item_price(self, item_id: int) -> float:
        try:
            conn = self._get_conn()
            if conn:
                row = conn.execute(
                    "SELECT price, total_qty FROM items WHERE id=?", (item_id,)
                ).fetchone()
                if row:
                    return float(row["price"])
        except Exception:
            pass
        return 0.0

    def _get_current_raw_id(self):
        if self.cmb_type.currentData() != "raw":
            return None
        data = self._item_combo.current_data()
        if data and data[0] not in ("__sep__", "__orphan__") and data[1] is not None:
            return data[1]
        return None

    def _get_current_machine_op_id(self):
        if self.cmb_type.currentData() != "machine_op":
            return None
        data = self._item_combo.current_data()
        if data and data[0] not in ("__sep__", "__orphan__") and data[1] is not None:
            return data[1]
        return None

    # ══════════════════════════════════════════════════════
    # waste_pct
    # ══════════════════════════════════════════════════════

    def _on_waste_changed(self, val: float):
        self._update_waste_style(val)

    def _update_waste_style(self, val: float):
        if val > 0:
            self.lbl_waste.setVisible(True)
            if val >= 20:
                color, border = "#ffcdd2", "#e53935"
            elif val >= 10:
                color, border = "#ffe0b2", "#f57c00"
            else:
                color, border = "#fff8e1", "#ffe082"
            self.waste_spin.setStyleSheet(f"""
                QDoubleSpinBox {{
                    background: {color}; border: 1px solid {border};
                    border-radius: 4px; padding: 1px 4px;
                    font-size: 11px; color: #e65100; font-weight: bold;
                }}
                QDoubleSpinBox:focus {{ border-color: #ff8f00; }}
            """)
        else:
            self.lbl_waste.setVisible(False)
            self.waste_spin.setStyleSheet("""
                QDoubleSpinBox {
                    background: #f5f5f5; border: 1px solid #e0e0e0;
                    border-radius: 4px; padding: 1px 4px;
                    font-size: 11px; color: #999;
                }
                QDoubleSpinBox:focus {
                    border-color: #ffe082; background: #fff8e1; color: #e65100;
                }
            """)

    # ══════════════════════════════════════════════════════
    # إظهار/إخفاء الحقول
    # ══════════════════════════════════════════════════════

    def _update_total_qty_visibility(self, child_type: str):
        visible = (child_type == "raw") and self._show_total_qty
        self.total_qty_edit.setVisible(visible)
        self.lbl_total_qty.setVisible(visible)

    def _auto_fill_total_qty(self):
        if self.cmb_type.currentData() != "raw":
            return
        data = self._item_combo.current_data()
        if not data or data[0] in ("__sep__", "__orphan__") or data[1] is None:
            return
        child_id  = data[1]
        catalog   = self._catalog_fn()
        raw_items = catalog.get("raw", [])
        for entry in raw_items:
            if entry[0] == child_id:
                tq = entry[4] if len(entry) > 4 else None
                if tq is not None:
                    self.total_qty_edit.setText(str(tq))
                else:
                    self.total_qty_edit.clear()
                return
        self.total_qty_edit.clear()

    # ══════════════════════════════════════════════════════
    # Orphan state
    # ══════════════════════════════════════════════════════

    def set_orphan_name(self, name: str | None):
        if not self._is_orphan:
            return
        self._orphan_name = name
        display = self._orphan_display()
        self._item_combo.block_signals(True)
        self._item_combo.set_item_text(0, display)
        self._item_combo.block_signals(False)

    def _orphan_display(self) -> str:
        if self._orphan_name:
            return f"⚠️  {self._orphan_name}  (ID: {self._orphan_id})"
        return f"⚠️  محذوف  (ID: {self._orphan_id})"

    def is_orphan(self) -> bool:
        return self._is_orphan

    # ══════════════════════════════════════════════════════
    # ملء قايمة العناصر
    # ══════════════════════════════════════════════════════

    def _fill_items(self, child_type: str, selected_id=None):
        catalog  = self._catalog_fn()
        items    = catalog.get(child_type, [])
        item_ids = {entry[0] for entry in items}

        grouped = []
        if selected_id is not None and selected_id not in item_ids:
            self._mark_orphan(child_type, selected_id)
            display = self._orphan_display()
            grouped.append((display, ("__orphan__", selected_id), False))
        else:
            self._clear_orphan()

        grouped += _build_grouped_items(items)
        self._item_combo.populate(grouped)

        if selected_id is not None:
            if self._is_orphan and self._orphan_id == selected_id:
                self._item_combo.cmb.setCurrentIndex(0)
            else:
                for i in range(self._item_combo.count()):
                    d = self._item_combo.item_data(i)
                    if d and d[0] not in ("__sep__", "__orphan__") and d[1] == selected_id:
                        self._item_combo.cmb.setCurrentIndex(i)
                        break
        else:
            self._item_combo._select_first_real()

    def refresh_catalog(self, _new_catalog: dict = None):
        self._refresh_items()

    # ══════════════════════════════════════════════════════
    # Orphan helpers
    # ══════════════════════════════════════════════════════

    def _mark_orphan(self, child_type: str, child_id: int):
        self._is_orphan   = True
        self._orphan_id   = child_id
        self._orphan_type = child_type
        self.setStyleSheet(_STYLE_ORPHAN)
        name_part = f" «{self._orphan_name}»" if self._orphan_name else ""
        self.setToolTip(
            f"⚠️ هذا المكون ({child_type}{name_part} ID:{child_id}) "
            "تم حذفه من قاعدة البيانات.\n"
            "اختر بديلاً من القايمة أو احذف هذا الصف."
        )

    def _clear_orphan(self):
        self._is_orphan   = False
        self._orphan_id   = None
        self._orphan_type = None
        self._orphan_name = None
        self.setStyleSheet(_STYLE_NORMAL)
        self.setToolTip("")

    # ══════════════════════════════════════════════════════
    # Signal handlers
    # ══════════════════════════════════════════════════════

    def _on_item_selected(self, data):
        if data and data[0] not in ("__sep__", "__orphan__") and data[1] is not None:
            self._pinned_id = data[1]
            if self._is_orphan:
                self._clear_orphan()
                self.setStyleSheet(_STYLE_NORMAL)

            child_type = self.cmb_type.currentData()

            if child_type == "raw":
                self._auto_fill_total_qty()
                item_id = data[1]
                weak_self = weakref.ref(self)
                QTimer.singleShot(50, lambda: (s := weak_self()) and s._load_variants(item_id))
                self._hide_op_rows()
            elif child_type == "machine_op":
                op_id = data[1]
                self._hide_op_rows()
                # المستخدم اختار عملية جديدة → نصفر الـ pinned
                self._pinned_op_row_id = None
                # ✅ نستخدم QTimer أيضاً هنا لضمان الـ widget جاهز
                _weak = weakref.ref(self)
                _oid = op_id
                QTimer.singleShot(50, lambda: (s := _weak()) and s._load_op_rows(_oid, None))
                self._hide_variants()
            else:
                self._hide_variants()
                self._hide_op_rows()

    def _on_catalog_changed(self):
        valid_types = {k for k, _ in _TYPES}
        if self._pinned_type not in valid_types:
            from_combo = self.cmb_type.currentData()
            if from_combo in valid_types:
                self._pinned_type = from_combo
            else:
                return
        if not self._is_orphan:
            current_data = self._item_combo.current_data()
            if current_data and current_data[0] not in ("__sep__", "__orphan__"):
                self._pinned_id = current_data[1]
        self._refresh_items()

    def _refresh_items(self):
        child_type  = self._pinned_type
        selected_id = self._orphan_id if self._is_orphan else self._pinned_id
        self._fill_items(child_type, selected_id=selected_id)

    def _on_type_changed(self, _):
        new_type = self.cmb_type.currentData()
        if not isinstance(new_type, str):
            return
        self._pinned_type = new_type
        self._pinned_id   = None
        self._pinned_variant   = None
        self._pinned_op_row_id = None
        self._clear_orphan()
        self._fill_items(new_type, selected_id=None)
        self._update_total_qty_visibility(new_type)
        if new_type != "raw":
            self.total_qty_edit.clear()
            self._hide_variants()
        if new_type != "machine_op":
            self._hide_op_rows()

    # ══════════════════════════════════════════════════════
    # ✅ get_values — المصدر الموثوق: _pinned_op_row_id
    # ══════════════════════════════════════════════════════

    def get_values(self) -> tuple | None:
        """
        يرجع (child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id)
        
        machine_op_row_id:
        - المصدر الأساسي: _pinned_op_row_id
        - يُحدَّث في كل تغيير (من المستخدم أو من التحميل)
        - تحقق إضافي من currentData() لضمان التزامن
        """
        try:
            data = self._item_combo.current_data()
            qty  = float(self.qty_edit.text())
            if data is None:
                return None
            kind, child_id = data
            if kind in ("__orphan__", "__sep__") or child_id is None:
                return None
            child_type = self.cmb_type.currentData()
            waste_pct  = self.waste_spin.value()

            variant_id = None
            if child_type == "raw" and self.cmb_variant.isVisible():
                variant_id = self.cmb_variant.currentData()

            machine_op_row_id = None
            if child_type == "machine_op":
                # _pinned_op_row_id هو المصدر الأساسي الموثوق
                machine_op_row_id = self._pinned_op_row_id

                # تحقق إضافي: لو currentData مختلف ومحدد
                current = self.cmb_op_row.currentData()
                if current is not None and current != machine_op_row_id:
                    machine_op_row_id = current
                    self._pinned_op_row_id = current

            return child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id

        except (ValueError, TypeError):
            return None

    def get_waste_pct(self) -> float:
        return self.waste_spin.value()

    def get_variant_id(self):
        if self.cmb_type.currentData() == "raw" and self.cmb_variant.isVisible():
            return self.cmb_variant.currentData()
        return None

    def get_machine_op_row_id(self):
        """يُرجع _pinned_op_row_id دائماً كمصدر موثوق."""
        if self.cmb_type.currentData() == "machine_op":
            return self._pinned_op_row_id
        return None

    @property
    def cmb_item(self):
        return self._item_combo.cmb