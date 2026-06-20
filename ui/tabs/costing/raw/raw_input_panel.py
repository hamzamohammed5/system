"""
ui/tabs/costing/raw/raw_input_panel.py
=======================================
RawInputPanel — فورم إضافة / تعديل الخامة مع لوحة Variants.

يرث من BaseCrudForm ويستدعي ItemService بدل repos مباشرة.
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy
from PyQt5.QtCore import Qt

from ui.widgets.base.crud_form         import BaseCrudForm

from ui.widgets.panels.form_fields import (labeled_widget, spin_field)
from ui.widgets.panels.form_badges import ResultBadge
from ui.widgets.panels.form_group import FormGroup


from ui.widgets.forms.inputs           import RequiredLineEdit, AmountSpinBox
from ui.widgets.combo.category         import CategoryCombo
from ui.tabs.costing.shared.raw_variants_panel import _RawVariantsPanel
from ui.widgets.core.i18n              import tr
from ui.theme                          import _C
from ui.font                           import FS_XS


def _live_price(inp_price) -> float:
    """يقرأ سعر من QLineEdit بأمان."""
    try:
        return float(inp_price.text() or "0")
    except ValueError:
        return 0.0


class RawInputPanel(BaseCrudForm):
    """
    فورم الخامة — يرث من BaseCrudForm.

    BaseCrudForm يوفر:
      - _build()    : يبني الـ form تلقائياً من _build_fields
      - _add()      : يستدعي _collect ثم _do_insert
      - _save_edit(): يستدعي _collect ثم _do_update
      - _cancel()   : يستدعي _reset_fields
      - EditModeMixin + LiveConnMixin
    """

    FORM_TITLE = tr("raw_form_title")
    ADD_TEXT   = tr("raw_add_btn")
    SAVE_TEXT  = tr("btn_save")

    def __init__(self, conn, parent=None):
        super().__init__(conn, parent)
        # ربط live preview بعد بناء الـ fields
        self.inp_price.textChanged.connect(self._on_price_changed)
        self.sp_total_qty.valueChanged.connect(self._update_hint)

    # ══════════════════════════════════════════════════════
    # بناء الحقول
    # ══════════════════════════════════════════════════════

    def _build_fields(self, group: FormGroup):
        self.inp_name    = RequiredLineEdit(tr("raw_name_required"))
        self.inp_name.setMinimumHeight(32)

        self.inp_price   = AmountSpinBox(dec=2)
        self.inp_price.setFixedWidth(120)

        self.sp_total_qty = spin_field(max_=999999, dec=4)
        self.sp_total_qty.setFixedWidth(120)
        self.sp_total_qty.setToolTip(tr("raw_qty_tooltip"))

        self.lbl_hint = QLabel()
        self.lbl_hint.setStyleSheet(
            f"color: {_C['info']}; font-size: {FS_XS}px;"
            f"background: {_C['info_bg']}; border-radius: 4px; padding: 4px 8px;"
        )
        self.lbl_hint.setWordWrap(True)

        self.cmb_category = CategoryCombo(self.conn, scope="raw")

        group.add_row(f"{tr('raw_name_label')} *",      self.inp_name)
        group.add_row(f"{tr('raw_price_label')} :",      labeled_widget(self.inp_price, tr("currency_abbr")))
        group.add_row(f"{tr('raw_qty_label')} :", labeled_widget(self.sp_total_qty, tr("raw_qty_unit")))
        group.add_row("",                   self.lbl_hint)
        group.add_row(f"{tr('category')} :",          self.cmb_category)

        # لوحة variants تُضاف بعد الـ group عبر _build_extra
        self._variants = _RawVariantsPanel(self.conn)

    def _build_extra(self, root_layout):
        """يُضاف بعد الـ FormGroup — hook في BaseCrudForm."""
        root_layout.addWidget(self._variants)

    # ══════════════════════════════════════════════════════
    # Live preview
    # ══════════════════════════════════════════════════════

    def _on_price_changed(self):
        self._update_hint()
        if self._editing_id is not None:
            self._variants.refresh_price(_live_price(self.inp_price))

    def _update_hint(self):
        price = _live_price(self.inp_price)
        tq    = self.sp_total_qty.value() if self.sp_total_qty.value() > 0 else None

        if tq and tq > 0 and price > 0:
            unit = price / tq
            self.lbl_hint.setText(
                tr("raw_hint_with_qty", price=f"{price:.2f}", qty=f"{tq:.4g}", unit=f"{unit:.4f}")
            )
        elif tq and tq > 0:
            self.lbl_hint.setText(tr("raw_hint_qty_only"))
        else:
            self.lbl_hint.setText(tr("raw_hint_no_qty"))

    # ══════════════════════════════════════════════════════
    # BaseCrudForm interface
    # ══════════════════════════════════════════════════════

    def _collect(self) -> dict | None:
        if not self.inp_name.validate():
            return None
        price     = float(self.inp_price.value()) if hasattr(self.inp_price, "value") \
                    else _live_price(self.inp_price)
        total_qty = self.sp_total_qty.value() if self.sp_total_qty.value() > 0 else None
        return {
            "name":        self.inp_name.text_stripped(),
            "price":       price,
            "total_qty":   total_qty,
            "category_id": self.cmb_category.get_category(),
        }

    def _do_insert(self, data: dict) -> int:
        from services.shared.item_service import ItemService
        new_id = ItemService(self.conn).add(
            data["name"], data["price"], "raw",
            category_id=data["category_id"],
            total_qty=data["total_qty"],
        )
        self._variants.load_item(new_id, data["price"])
        # إبقاء الفورم في وضع التعديل لإضافة variants
        self.enter_edit_mode(new_id, f"─── {tr('raw_add_variants_mode', name=data['name'])} ───")
        self.btn_add.setVisible(False)
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)
        return new_id

    def _do_update(self, item_id: int, data: dict) -> None:
        from services.shared.item_service import ItemService
        ItemService(self.conn).update(
            item_id, data["name"], data["price"],
            category_id=data["category_id"],
            total_qty=data["total_qty"],
        )

    def _do_load(self, item_id: int) -> dict | None:
        from services.shared.item_service import ItemService
        result = ItemService(self.conn).get(item_id)
        if result is None:
            return None
        return {
            "id":          result.id,
            "name":        result.name,
            "price":       result.price,
            "total_qty":   result.total_qty,
            "category_id": result.category_id,
        }

    def _fill_fields(self, data: dict) -> None:
        self.inp_name.setText(data["name"])
        # AmountSpinBox أو QLineEdit حسب الـ base
        if hasattr(self.inp_price, "setValue"):
            self.inp_price.setValue(data.get("price", 0))
        else:
            self.inp_price.setText(str(data.get("price", "")))
        tq = data.get("total_qty")
        self.sp_total_qty.setValue(float(tq) if tq else 0.0)
        self.cmb_category.set_category(data.get("category_id"))
        self._update_hint()
        self._variants.load_item(data["id"], data.get("price", 0))

    def _reset_fields(self) -> None:
        self.inp_name.clear()
        if hasattr(self.inp_price, "setValue"):
            self.inp_price.setValue(0)
        else:
            self.inp_price.clear()
        self.sp_total_qty.setValue(0)
        self.cmb_category.setCurrentIndex(0)
        self._update_hint()
        self._variants.clear()