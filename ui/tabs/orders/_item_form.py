"""
ui/tabs/orders/_item_form.py
=============================
Dialog لإضافة أو تعديل بند في الطلب.

✅ يستخدم _make_btn من panels
✅ يستخدم _C palette
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QDoubleSpinBox, QMessageBox,
)
from PyQt5.QtCore import Qt

from db.orders.orders_repo import (
    fetch_order_items, insert_order_item, update_order_item,
)
from ui.widgets.shared.panels import _make_btn
from ui.app_settings import _C


def _spin(min_=0, max_=9999999, dec=2, suffix=""):
    s = QDoubleSpinBox()
    s.setRange(min_, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(34)
    if suffix:
        s.setSuffix(f" {suffix}")
    return s


class _ItemForm(QDialog):
    def __init__(self, conn, order_id: int, item_id: int = None, parent=None):
        super().__init__(parent)
        self.conn     = conn
        self.order_id = order_id
        self.item_id  = item_id

        self.setWindowTitle("تعديل بند" if item_id else "إضافة بند")
        self.setMinimumWidth(480)
        self.setModal(True)
        self.setStyleSheet(f"""
            QLineEdit, QDoubleSpinBox {{
                background: {_C['bg_input']};
                border: 1px solid {_C['border_med']};
                border-radius: 6px;
                padding: 4px 10px;
                color: {_C['text_primary']};
                min-height: 34px;
            }}
            QLineEdit:focus, QDoubleSpinBox:focus {{
                border-color: {_C['accent']};
                background: white;
            }}
        """)

        self._build()
        if item_id:
            self._load()

        self.sp_qty.valueChanged.connect(self._update_total)
        self.sp_price.valueChanged.connect(self._update_total)
        self.sp_discount.valueChanged.connect(self._update_total)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        hdr = QLabel("➕  إضافة بند" if not self.item_id else "✏️  تعديل بند")
        hdr.setStyleSheet(f"""
            font-size: 13px; font-weight: bold; color: {_C['accent_text']};
            background: {_C['accent_light']};
            border-radius: 8px; padding: 8px 14px;
        """)
        root.addWidget(hdr)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم البند أو المنتج...")
        form.addRow("البند * :", self.inp_name)

        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("وصف تفصيلي (اختياري)...")
        form.addRow("الوصف :", self.inp_desc)

        self.sp_qty = _spin(min_=0.001, max_=99999, dec=3)
        self.sp_qty.setValue(1)
        form.addRow("الكمية :", self.sp_qty)

        self.inp_unit = QLineEdit()
        self.inp_unit.setText("قطعة")
        self.inp_unit.setPlaceholderText("قطعة، متر، كجم ...")
        form.addRow("الوحدة :", self.inp_unit)

        self.sp_price = _spin(max_=9999999, dec=2, suffix="ج")
        form.addRow("سعر الوحدة :", self.sp_price)

        self.sp_discount = _spin(max_=100, dec=2, suffix="%")
        form.addRow("الخصم :", self.sp_discount)

        # الإجمالي (للعرض فقط)
        self.lbl_total = QLabel("0.00 ج")
        self.lbl_total.setStyleSheet(f"""
            font-size: 14px; font-weight: bold; color: {_C['accent_text']};
            background: {_C['accent_light']};
            border: 1px solid {_C['accent_mid']};
            border-radius: 6px; padding: 6px 12px;
        """)
        form.addRow("الإجمالي :", self.lbl_total)

        self.inp_design_ref = QLineEdit()
        self.inp_design_ref.setPlaceholderText("كود التصميم أو المرجع (اختياري)...")
        form.addRow("مرجع التصميم :", self.inp_design_ref)

        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("ملاحظات على البند...")
        form.addRow("ملاحظات :", self.inp_notes)

        root.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = _make_btn("إلغاء", "ghost")
        btn_cancel.clicked.connect(self.reject)

        btn_save = _make_btn("💾  حفظ البند", "primary")
        btn_save.setMinimumHeight(36)
        btn_save.clicked.connect(self._save)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save, stretch=1)
        root.addLayout(btn_row)

    def _update_total(self):
        qty      = self.sp_qty.value()
        price    = self.sp_price.value()
        discount = self.sp_discount.value()
        total    = qty * price * (1 - discount / 100)
        self.lbl_total.setText(f"{total:,.2f} ج")

    def _load(self):
        items = fetch_order_items(self.conn, self.order_id)
        item  = next((i for i in items if i["id"] == self.item_id), None)
        if not item:
            return

        self.inp_name.setText(item["item_name"])
        self.inp_desc.setText(item["description"] or "")
        self.sp_qty.setValue(item["quantity"])
        self.inp_unit.setText(item["unit"])
        self.sp_price.setValue(item["unit_price"])
        self.sp_discount.setValue(item["discount_pct"])
        self.inp_design_ref.setText(item["design_ref"] or "")
        self.inp_notes.setText(item["notes"] or "")
        self._update_total()

    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم البند")
            self.inp_name.setFocus()
            return

        qty      = self.sp_qty.value()
        unit     = self.inp_unit.text().strip() or "قطعة"
        price    = self.sp_price.value()
        discount = self.sp_discount.value()
        desc     = self.inp_desc.text().strip()
        ref      = self.inp_design_ref.text().strip()
        notes    = self.inp_notes.text().strip()

        if self.item_id:
            update_order_item(
                self.conn, self.item_id,
                item_name=name, description=desc,
                quantity=qty, unit=unit,
                unit_price=price, discount_pct=discount,
                design_ref=ref, notes=notes,
            )
        else:
            insert_order_item(
                self.conn, self.order_id,
                item_name=name, description=desc,
                quantity=qty, unit=unit,
                unit_price=price, discount_pct=discount,
                design_ref=ref, notes=notes,
            )

        self.accept()