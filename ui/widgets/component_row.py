"""
ui/widgets/component_row.py — مع حقل نسبة الهادر (waste_pct)

التغيير: _SearchableCombo و _build_grouped_items انتقلوا لـ searchable_combo.py
         هنا بنستورد منهم بدل التكرار.
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QLineEdit,
    QPushButton, QSizePolicy, QLabel, QDoubleSpinBox,
)
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtGui  import QColor

# ✅ استيراد من الملف المنفصل بدل التكرار
from ui.widgets.searchable_combo import _SearchableCombo, _build_grouped_items
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


# ══════════════════════════════════════════════════════════
# ComponentRow — مع حقل waste_pct
# ══════════════════════════════════════════════════════════

class ComponentRow(QWidget):
    removed = pyqtSignal(QWidget)

    def __init__(self, catalog_fn, child_type: str = "raw",
                 child_id=None, qty: float = 1.0,
                 waste_pct: float = 0.0,
                 raw_total_qty: float = None,
                 show_total_qty: bool = False,
                 parent=None):
        super().__init__(parent)
        self._catalog_fn     = catalog_fn
        self._show_total_qty = show_total_qty
        self._is_orphan      = False
        self._orphan_id      = None
        self._orphan_type    = None
        self._orphan_name    = None

        self._pinned_type      = child_type
        self._pinned_id        = child_id
        self._pinned_total_qty = raw_total_qty

        self._build(child_type, child_id, qty, raw_total_qty, waste_pct)
        QTimer.singleShot(0, self._connect_signal)

    def _connect_signal(self):
        bus.data_changed.connect(
            lambda: QTimer.singleShot(0, self._on_catalog_changed)
        )

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self, child_type, child_id, qty, raw_total_qty, waste_pct=0.0):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(6)

        # ── النوع ──
        self.cmb_type = QComboBox()
        self.cmb_type.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.cmb_type.setMinimumContentsLength(10)
        self.cmb_type.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        for key, label in _TYPES:
            self.cmb_type.addItem(label, key)

        # ── العنصر (searchable) ──
        self._item_combo = _SearchableCombo()
        self._item_combo.item_selected.connect(self._on_item_selected)

        # ── الكمية المستهلكة ──
        self.qty_edit = QLineEdit()
        self.qty_edit.setPlaceholderText("الكمية")
        self.qty_edit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.qty_edit.setMinimumWidth(60)
        self.qty_edit.setMaximumWidth(90)
        self.qty_edit.setText(str(qty) if qty else "")

        # ── نسبة الهادر % ──
        self.waste_spin = QDoubleSpinBox()
        self.waste_spin.setRange(0, 100)
        self.waste_spin.setDecimals(1)
        self.waste_spin.setSuffix(" %")
        self.waste_spin.setValue(waste_pct or 0.0)
        self.waste_spin.setMinimumWidth(75)
        self.waste_spin.setMaximumWidth(90)
        self.waste_spin.setMinimumHeight(26)
        self.waste_spin.setToolTip(
            "نسبة الهادر %\n"
            "مثال: 10% → الكمية الفعلية = الكمية × 1.10\n"
            "يعني لو محتاج 10م وهادر 10%، ستشتري 11م"
        )
        self.waste_spin.setStyleSheet("""
            QDoubleSpinBox {
                background: #fff8e1;
                border: 1px solid #ffe082;
                border-radius: 4px;
                padding: 1px 4px;
                font-size: 11px;
                color: #e65100;
            }
            QDoubleSpinBox:focus {
                border-color: #ff8f00;
                background: #fffde7;
            }
        """)

        # label الهادر
        self.lbl_waste = QLabel("⚠️")
        self.lbl_waste.setFixedWidth(18)
        self.lbl_waste.setStyleSheet("color: #e65100; font-size: 11px; background:transparent;")
        self.lbl_waste.setToolTip("نسبة الهادر")
        self.waste_spin.valueChanged.connect(self._on_waste_changed)
        self._update_waste_style(waste_pct or 0.0)

        # ── الكمية الكلية (raw فقط) ──
        self.total_qty_edit = QLineEdit()
        self.total_qty_edit.setPlaceholderText("الكلي")
        self.total_qty_edit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.total_qty_edit.setMinimumWidth(60)
        self.total_qty_edit.setMaximumWidth(90)
        self.total_qty_edit.setToolTip(
            "الكمية الكلية للخامة (مثلاً طول البكرة).\n"
            "سعر الوحدة = السعر الكلي ÷ هذا الرقم.\n"
            "اتركه فارغاً لو السعر هو سعر الوحدة مباشرة."
        )
        if raw_total_qty is not None:
            self.total_qty_edit.setText(str(raw_total_qty))

        self.lbl_total_qty = QLabel("÷")
        self.lbl_total_qty.setStyleSheet("color: #888; font-size: 11px;")
        self.lbl_total_qty.setFixedWidth(14)

        # ── حذف ──
        del_btn = QPushButton("❌")
        del_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        del_btn.setFixedWidth(32)
        del_btn.clicked.connect(lambda: self.removed.emit(self))

        layout.addWidget(self.cmb_type)
        layout.addWidget(self._item_combo, stretch=1)
        layout.addWidget(self.qty_edit)
        layout.addWidget(self.lbl_waste)
        layout.addWidget(self.waste_spin)

        if self._show_total_qty:
            layout.addWidget(self.lbl_total_qty)
            layout.addWidget(self.total_qty_edit)
        else:
            self.lbl_total_qty.setVisible(False)
            self.total_qty_edit.setVisible(False)

        layout.addWidget(del_btn)

        # تحديد النوع
        self.cmb_type.blockSignals(True)
        idx = next((i for i, (k, _) in enumerate(_TYPES) if k == child_type), 0)
        self.cmb_type.setCurrentIndex(idx)
        self.cmb_type.blockSignals(False)

        self._fill_items(child_type, selected_id=child_id)
        self._update_total_qty_visibility(child_type)

        self.cmb_type.currentIndexChanged.connect(self._on_type_changed)

    # ══════════════════════════════════════════════════════
    # waste_pct — ستايل ديناميكي
    # ══════════════════════════════════════════════════════

    def _on_waste_changed(self, val: float):
        self._update_waste_style(val)

    def _update_waste_style(self, val: float):
        """يغيّر لون الخلفية حسب قيمة الهادر."""
        if val > 0:
            self.lbl_waste.setVisible(True)
            if val >= 20:
                color = "#ffcdd2"
                border = "#e53935"
            elif val >= 10:
                color = "#ffe0b2"
                border = "#f57c00"
            else:
                color = "#fff8e1"
                border = "#ffe082"
            self.waste_spin.setStyleSheet(f"""
                QDoubleSpinBox {{
                    background: {color};
                    border: 1px solid {border};
                    border-radius: 4px;
                    padding: 1px 4px;
                    font-size: 11px;
                    color: #e65100;
                    font-weight: bold;
                }}
                QDoubleSpinBox:focus {{
                    border-color: #ff8f00;
                }}
            """)
        else:
            self.lbl_waste.setVisible(False)
            self.waste_spin.setStyleSheet("""
                QDoubleSpinBox {
                    background: #f5f5f5;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    padding: 1px 4px;
                    font-size: 11px;
                    color: #999;
                }
                QDoubleSpinBox:focus {
                    border-color: #ffe082;
                    background: #fff8e1;
                    color: #e65100;
                }
            """)

    # ══════════════════════════════════════════════════════
    # إظهار/إخفاء حقل الكمية الكلية
    # ══════════════════════════════════════════════════════

    def _update_total_qty_visibility(self, child_type: str):
        visible = (child_type == "raw") and self._show_total_qty
        self.total_qty_edit.setVisible(visible)
        self.lbl_total_qty.setVisible(visible)

    # ══════════════════════════════════════════════════════
    # Auto-fill الكمية الكلية
    # ══════════════════════════════════════════════════════

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
    # API خارجي — Orphan state
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
            self._auto_fill_total_qty()

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
        self._clear_orphan()
        self._fill_items(new_type, selected_id=None)
        self._update_total_qty_visibility(new_type)
        if new_type != "raw":
            self.total_qty_edit.clear()

    # ══════════════════════════════════════════════════════
    # جلب القيم
    # ══════════════════════════════════════════════════════

    def get_values(self) -> tuple | None:
        """
        يرجع: (child_type, child_id, qty, waste_pct)
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

            return child_type, child_id, qty, waste_pct

        except (ValueError, TypeError):
            return None

    def get_waste_pct(self) -> float:
        return self.waste_spin.value()

    # للتوافق مع الكود القديم
    @property
    def cmb_item(self):
        return self._item_combo.cmb