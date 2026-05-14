"""
ui/tabs/costing/raw/raw_input_panel.py
=======================================
_InputPanel — فورم إضافة / تعديل الخامة مع لوحة Variants.
مع scroll عمودي لما المساحة تكون ضيقة.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QGroupBox, QMessageBox,
    QScrollArea, QSizePolicy,
)
from PyQt5.QtCore import Qt

from db.items_repo import fetch_item, insert_item, update_item
from ui.helpers import EditModeMixin, buttons_row
from ui.widgets.shared.category_manager import CategoryCombo
from ui.widgets.costing.raw_variants_panel import _RawVariantsPanel
from ui.widgets.shared.scrollable_form import wrap_in_scroll
from ui.events import bus


def _labeled(widget, unit: str) -> QWidget:
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(6)
    lay.addWidget(widget)
    lay.addWidget(QLabel(unit))
    lay.addStretch()
    return w


class _InputPanel(QWidget, EditModeMixin):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self.init_edit_mode(self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode)

    def _build(self):
        # Layout خارجي — يحتوي فقط على الـ scroll area
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # الحاوية الداخلية التي تُبنى عليها كل الـ widgets
        self._inner = QWidget()
        self._inner.setMinimumWidth(280)
        self._inner.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        scroll = wrap_in_scroll(self._inner)
        outer.addWidget(scroll)

        # بناء المحتوى داخل self._inner
        root = QVBoxLayout(self._inner)
        root.setSpacing(8)
        root.setContentsMargins(12, 12, 12, 12)

        # ── بيانات الخامة الأساسية ──
        grp = QGroupBox("بيانات الخامة")
        grp_layout = QVBoxLayout(grp)
        grp_layout.setSpacing(10)

        self.lbl_mode = QLabel("─── إضافة خامة جديدة ───")
        self.lbl_mode.setStyleSheet("font-weight: bold; color: #1565c0; font-size: 12px;")
        grp_layout.addWidget(self.lbl_mode)

        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("أدخل اسم الخامة...")
        self.inp_name.setMinimumHeight(32)

        self.inp_price = QLineEdit()
        self.inp_price.setPlaceholderText("0.00")
        self.inp_price.setFixedWidth(120)

        self.inp_total_qty = QLineEdit()
        self.inp_total_qty.setPlaceholderText("اتركه فارغاً لو السعر بالوحدة")
        self.inp_total_qty.setFixedWidth(120)

        self.lbl_hint = QLabel()
        self.lbl_hint.setStyleSheet(
            "color: #1565c0; font-size: 10px;"
            "background: #e8f0fe; border-radius: 4px; padding: 4px 8px;"
        )
        self.lbl_hint.setWordWrap(True)
        self._update_hint()

        self.inp_price.textChanged.connect(lambda _: self._on_price_changed())
        self.inp_total_qty.textChanged.connect(lambda _: self._update_hint())

        self.cmb_category = CategoryCombo(self.conn, scope="raw")

        form.addRow("اسم الخامة :",       self.inp_name)
        form.addRow("السعر الكلي :",       _labeled(self.inp_price,     "جنيه"))
        form.addRow("الكمية الإجمالية :",  _labeled(self.inp_total_qty, "وحدة"))
        form.addRow("",                   self.lbl_hint)
        form.addRow("التصنيف :",          self.cmb_category)
        grp_layout.addLayout(form)

        self.btn_add    = QPushButton("➕  إضافة خامة")
        self.btn_save   = QPushButton("💾  حفظ التعديل")
        self.btn_cancel = QPushButton("✖  إلغاء")
        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn.setMinimumHeight(32)
        self.btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save_edit)
        self.btn_cancel.clicked.connect(self._cancel_edit)
        grp_layout.addLayout(buttons_row(self.btn_add, self.btn_save, self.btn_cancel))

        root.addWidget(grp)

        # ── لوحة Variants ──
        self._variants_panel = _RawVariantsPanel(self.conn)
        root.addWidget(self._variants_panel)

        root.addStretch()

    # ══════════════════════════════════════════════════════
    # تحديث تلميح السعر
    # ══════════════════════════════════════════════════════

    def _on_price_changed(self):
        self._update_hint()
        if self._editing_id is not None:
            try:
                price = float(self.inp_price.text() or "0")
                self._variants_panel.refresh_price(price)
            except ValueError:
                pass

    def _update_hint(self):
        try:
            price = float(self.inp_price.text() or "0")
        except ValueError:
            price = 0.0
        tq_text = self.inp_total_qty.text().strip()
        try:
            tq = float(tq_text) if tq_text else None
        except ValueError:
            tq = None

        if tq and tq > 0 and price > 0:
            unit = price / tq
            self.lbl_hint.setText(
                f"💡 سعر الوحدة = {price:.2f} ÷ {tq:.4g} = {unit:.4f} جنيه/وحدة"
            )
        elif tq and tq > 0:
            self.lbl_hint.setText("💡 سعر الوحدة = السعر الكلي ÷ الكمية الإجمالية")
        else:
            self.lbl_hint.setText(
                "💡 بدون كمية إجمالية: السعر المسجل = سعر الوحدة مباشرة"
            )

    # ══════════════════════════════════════════════════════
    # تحميل للتعديل
    # ══════════════════════════════════════════════════════

    def load_for_edit(self, item_id: int):
        item = fetch_item(self.conn, item_id)
        if not item:
            return
        self.inp_name.setText(item["name"])
        self.inp_price.setText(str(item["price"]))
        tq = item["total_qty"]
        self.inp_total_qty.setText(str(tq) if tq is not None else "")
        self.cmb_category.set_category(item["category_id"])
        self.inp_name.setFocus()
        self.enter_edit_mode(item_id, f"─── تعديل: {item['name']} ───")

        try:
            price = float(item["price"])
        except (TypeError, ValueError):
            price = 0.0
        self._variants_panel.load_item(item_id, price)

    # ══════════════════════════════════════════════════════
    # CRUD
    # ══════════════════════════════════════════════════════

    def _add(self):
        name, price, total_qty = self._collect()
        if name is None:
            return
        new_id = insert_item(self.conn, name, "raw", price,
                             category_id=self.cmb_category.get_category(),
                             total_qty=total_qty)
        self._variants_panel.load_item(new_id, price)
        self.enter_edit_mode(new_id, f"─── أضف وحدات إنتاج لـ: {name} ───")
        self.btn_add.setVisible(False)
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)
        bus.data_changed.emit()

    def _save_edit(self):
        name, price, total_qty = self._collect()
        if name is None:
            return
        update_item(self.conn, self._editing_id, name, price,
                    category_id=self.cmb_category.get_category(),
                    total_qty=total_qty)
        self._reset()
        bus.data_changed.emit()

    def _cancel_edit(self):
        self._reset()

    def _collect(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم الخامة")
            return None, None, None
        try:
            price = float(self.inp_price.text() or "0")
        except ValueError:
            QMessageBox.warning(self, "خطأ", "السعر يجب أن يكون رقماً")
            return None, None, None

        tq_text = self.inp_total_qty.text().strip()
        if tq_text:
            try:
                total_qty = float(tq_text)
                if total_qty <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "خطأ", "الكمية الإجمالية يجب أن تكون رقماً موجباً")
                return None, None, None
        else:
            total_qty = None

        return name, price, total_qty

    def _reset(self):
        self.inp_name.clear()
        self.inp_price.clear()
        self.inp_total_qty.clear()
        self.cmb_category.setCurrentIndex(0)
        self._update_hint()
        self._variants_panel.clear()
        self.exit_edit_mode("─── إضافة خامة جديدة ───")