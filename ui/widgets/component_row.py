"""
ui/widgets/component_row.py  (النسخة المعدَّلة)
===========================
صف مكون واحد في BOM عند إنشاء/تعديل منتج.

يعرض:
  [النوع ▼]  [العنصر ▼]  [الكمية المستهلكة]  [الكمية الكلية]  [❌]

"الكمية الكلية":
  - تظهر فقط لو النوع = raw
  - تُملأ تلقائياً من total_qty المسجل في الخامة
  - قابلة للتعديل (override) — لو عدّلتها تتحفظ في bom.raw_total_qty
  - لو فارغة → السعر يُعتبر سعر وحدة مباشرة

المعادلة:
  سعر_الوحدة = price / raw_total_qty   (لو raw_total_qty > 0)
  تكلفة      = سعر_الوحدة × qty        
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QLineEdit,
    QPushButton, QSizePolicy, QLabel
)
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtGui  import QColor, QFont
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

_SEPARATOR_DATA = ("__sep__", None)


def _build_grouped_items(items: list[tuple]) -> list[tuple]:
    groups: dict[str, list[tuple]] = {}
    NO_CAT = "__no_category__"

    for entry in items:
        item_id  = entry[0]
        name     = entry[1]
        cat_name = entry[3] if len(entry) > 3 and entry[3] else NO_CAT

        if cat_name not in groups:
            groups[cat_name] = []
        groups[cat_name].append((item_id, name))

    result = []
    for cat_name, members in groups.items():
        if cat_name == NO_CAT:
            continue
        result.append((f"─── {cat_name} ───", _SEPARATOR_DATA, True))
        for item_id, name in members:
            result.append((f"{item_id} — {name}", (None, item_id), False))

    if NO_CAT in groups:
        if result:
            result.append(("─── بدون تصنيف ───", _SEPARATOR_DATA, True))
        for item_id, name in groups[NO_CAT]:
            result.append((f"{item_id} — {name}", (None, item_id), False))

    return result


class ComponentRow(QWidget):
    removed = pyqtSignal(QWidget)

    def __init__(self, catalog_fn, child_type: str = "raw",
                 child_id=None, qty: float = 1.0,
                 raw_total_qty: float = None,
                 parent=None):
        super().__init__(parent)
        self._catalog_fn    = catalog_fn
        self._is_orphan     = False
        self._orphan_id     = None
        self._orphan_type   = None
        self._orphan_name   = None

        self._pinned_type     = child_type
        self._pinned_id       = child_id
        self._pinned_total_qty = raw_total_qty  # القيمة المحفوظة في الـ BOM

        self._build(child_type, child_id, qty, raw_total_qty)
        QTimer.singleShot(0, self._connect_signal)

    def _connect_signal(self):
        bus.data_changed.connect(
            lambda: QTimer.singleShot(0, self._on_catalog_changed)
        )

    # ══════════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════════

    def _build(self, child_type, child_id, qty, raw_total_qty):
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

        # ── العنصر ──
        self.cmb_item = QComboBox()
        self.cmb_item.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cmb_item.setMinimumWidth(150)
        self.cmb_item.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        # ── الكمية المستهلكة ──
        self.qty_edit = QLineEdit()
        self.qty_edit.setPlaceholderText("الكمية")
        self.qty_edit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.qty_edit.setMinimumWidth(60)
        self.qty_edit.setMaximumWidth(100)
        self.qty_edit.setText(str(qty) if qty else "")

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
        layout.addWidget(self.cmb_item, stretch=1)
        layout.addWidget(self.qty_edit)
        layout.addWidget(self.lbl_total_qty)
        layout.addWidget(self.total_qty_edit)
        layout.addWidget(del_btn)

        # تحديد النوع
        self.cmb_type.blockSignals(True)
        idx = next((i for i, (k, _) in enumerate(_TYPES) if k == child_type), 0)
        self.cmb_type.setCurrentIndex(idx)
        self.cmb_type.blockSignals(False)

        self._fill_items(child_type, selected_id=child_id)
        self._update_total_qty_visibility(child_type)

        self.cmb_type.currentIndexChanged.connect(self._on_type_changed)
        self.cmb_item.currentIndexChanged.connect(self._on_item_changed)
        # لما يتغير العنصر المختار، نحدّث الكمية الكلية تلقائياً
        self.cmb_item.currentIndexChanged.connect(self._auto_fill_total_qty)

    # ══════════════════════════════════════════════════════════
    # إظهار/إخفاء حقل الكمية الكلية
    # ══════════════════════════════════════════════════════════

    def _update_total_qty_visibility(self, child_type: str):
        visible = (child_type == "raw")
        self.total_qty_edit.setVisible(visible)
        self.lbl_total_qty.setVisible(visible)

    # ══════════════════════════════════════════════════════════
    # Auto-fill الكمية الكلية من بيانات الخامة
    # ══════════════════════════════════════════════════════════

    def _auto_fill_total_qty(self):
        """
        لما يختار المستخدم خامة، نملأ تلقائياً الكمية الكلية
        من total_qty المسجل في الخامة — إلا لو كان عنده قيمة مسبقة (pinned).
        """
        if self.cmb_type.currentData() != "raw":
            return
        data = self.cmb_item.currentData()
        if not data or data[0] in ("__sep__", "__orphan__") or data[1] is None:
            return

        child_id = data[1]
        catalog  = self._catalog_fn()
        raw_items = catalog.get("raw", [])

        # نبحث عن الخامة في الكاتالوج عشان نجيب total_qty
        # الكاتالوج بيرجع tuples: (id, name, cat_id, cat_name)
        # نحتاج نرجع للـ DB عن طريق الـ catalog_fn أو نجيب total_qty من مكان تاني
        # الحل: نخزن total_qty في الكاتالوج
        # لكن بما إن الكاتالوج الحالي مش بيرجع total_qty،
        # نروح للـ DB مباشرة من خلال catalog_fn context
        # الحل الأبسط: نطلب من _catalog_fn إنها ترجع total_qty في entry[4]

        # نشوف لو في total_qty في الكاتالوج (entry[4])
        for entry in raw_items:
            if entry[0] == child_id:
                tq = entry[4] if len(entry) > 4 else None
                # نملأ الحقل بس لو مش عنده قيمة مكسرة (pinned)
                if tq is not None:
                    self.total_qty_edit.setText(str(tq))
                else:
                    # لو الخامة مالهاش total_qty، امسح الحقل
                    self.total_qty_edit.clear()
                return

        # لو مش لاقي في الكاتالوج، امسح
        self.total_qty_edit.clear()

    # ══════════════════════════════════════════════════════════
    # API خارجي
    # ══════════════════════════════════════════════════════════

    def set_orphan_name(self, name: str | None):
        if not self._is_orphan:
            return
        self._orphan_name = name
        display = self._orphan_display()
        self.cmb_item.blockSignals(True)
        self.cmb_item.setItemText(0, display)
        self.cmb_item.blockSignals(False)

    def _orphan_display(self) -> str:
        if self._orphan_name:
            return f"⚠️  {self._orphan_name}  (ID: {self._orphan_id})"
        return f"⚠️  محذوف  (ID: {self._orphan_id})"

    # ══════════════════════════════════════════════════════════
    # ملء قايمة العناصر
    # ══════════════════════════════════════════════════════════

    def _fill_items(self, child_type: str, selected_id=None):
        catalog  = self._catalog_fn()
        items    = catalog.get(child_type, [])
        item_ids = {entry[0] for entry in items}

        self.cmb_item.blockSignals(True)
        self.cmb_item.clear()

        if selected_id is not None and selected_id not in item_ids:
            self._mark_orphan(child_type, selected_id)
            display = self._orphan_display()
            self.cmb_item.addItem(display, userData=("__orphan__", selected_id))
            self.cmb_item.setItemData(0, QColor("#e53935"), Qt.ForegroundRole)
        else:
            self._clear_orphan()

        grouped = _build_grouped_items(items)

        for display_text, user_data, is_separator in grouped:
            self.cmb_item.addItem(display_text, userData=user_data)
            idx = self.cmb_item.count() - 1

            if is_separator:
                self.cmb_item.setItemData(idx, QColor("#78909c"), Qt.ForegroundRole)
                font = QFont()
                font.setBold(True)
                font.setPointSize(font.pointSize() - 1)
                self.cmb_item.setItemData(idx, font, Qt.FontRole)
                model = self.cmb_item.model()
                item  = model.item(idx)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemIsEnabled & ~Qt.ItemIsSelectable)

        self.cmb_item.blockSignals(False)
        self._select_item(selected_id)

    def _select_item(self, selected_id):
        if selected_id is None:
            self._select_first_real()
            return
        if self._is_orphan and self._orphan_id == selected_id:
            self.cmb_item.setCurrentIndex(0)
            return
        for i in range(self.cmb_item.count()):
            d = self.cmb_item.itemData(i)
            if d and d[0] not in ("__sep__", "__orphan__") and d[1] == selected_id:
                self.cmb_item.setCurrentIndex(i)
                return
        self._select_first_real()

    def _select_first_real(self):
        start = 1 if self._is_orphan else 0
        for i in range(start, self.cmb_item.count()):
            d = self.cmb_item.itemData(i)
            if d and d[0] not in ("__sep__", "__orphan__"):
                self.cmb_item.setCurrentIndex(i)
                return

    def refresh_catalog(self, _new_catalog: dict = None):
        self._refresh_items()

    # ══════════════════════════════════════════════════════════
    # Orphan state
    # ══════════════════════════════════════════════════════════

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

    def is_orphan(self) -> bool:
        return self._is_orphan

    # ══════════════════════════════════════════════════════════
    # Signal handlers
    # ══════════════════════════════════════════════════════════

    def _on_catalog_changed(self):
        valid_types = {k for k, _ in _TYPES}
        if self._pinned_type not in valid_types:
            from_combo = self.cmb_type.currentData()
            if from_combo in valid_types:
                self._pinned_type = from_combo
            else:
                return
        if not self._is_orphan:
            current_data = self.cmb_item.currentData()
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
        # امسح الكمية الكلية لو غيّر النوع لمش-raw
        if new_type != "raw":
            self.total_qty_edit.clear()

    def _on_item_changed(self, idx: int):
        data = self.cmb_item.itemData(idx)

        if data and data[0] == "__sep__":
            self.cmb_item.blockSignals(True)
            for i in range(idx + 1, self.cmb_item.count()):
                d = self.cmb_item.itemData(i)
                if d and d[0] not in ("__sep__", "__orphan__"):
                    self.cmb_item.setCurrentIndex(i)
                    d2 = self.cmb_item.itemData(i)
                    if d2:
                        self._pinned_id = d2[1]
                    break
            else:
                for i in range(idx - 1, -1, -1):
                    d = self.cmb_item.itemData(i)
                    if d and d[0] not in ("__sep__", "__orphan__"):
                        self.cmb_item.setCurrentIndex(i)
                        d2 = self.cmb_item.itemData(i)
                        if d2:
                            self._pinned_id = d2[1]
                        break
            self.cmb_item.blockSignals(False)
            return

        if data and data[0] not in ("__sep__", "__orphan__") and data[1] is not None:
            self._pinned_id = data[1]
            if self._is_orphan:
                self._clear_orphan()
                self.setStyleSheet(_STYLE_NORMAL)

    # ══════════════════════════════════════════════════════════
    # جلب القيم — يرجع 4 عناصر لو raw
    # ══════════════════════════════════════════════════════════

    def get_values(self) -> tuple | None:
        """
        يرجع:
          (child_type, child_id, qty, raw_total_qty)   ← لو raw
          (child_type, child_id, qty, None)             ← لو غير raw
        أو None لو في خطأ.
        """
        try:
            data = self.cmb_item.currentData()
            qty  = float(self.qty_edit.text())
            if data is None:
                return None
            kind, child_id = data
            if kind in ("__orphan__", "__sep__") or child_id is None:
                return None
            child_type = self.cmb_type.currentData()

            raw_total_qty = None
            if child_type == "raw":
                tq_text = self.total_qty_edit.text().strip()
                if tq_text:
                    try:
                        raw_total_qty = float(tq_text)
                        if raw_total_qty <= 0:
                            raw_total_qty = None
                    except ValueError:
                        raw_total_qty = None

            return child_type, child_id, qty, raw_total_qty
        except (ValueError, TypeError):
            return None