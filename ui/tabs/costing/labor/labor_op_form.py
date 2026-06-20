"""
ui/tabs/costing/labor/labor_op_form.py
=======================================
LaborOpForm — فورم إضافة / تعديل عملية عمالة.

يرث من BaseCrudForm — لا EditModeMixin يدوي، لا repo مباشر.
[Refactor] المسارات الموثقة في files_reference:
  - CategoryCombo  → ui.widgets.combo.category
  - ResultBadge    → ui.widgets.panels.form_parts
[Fix A6] إصلاح from ui.events import bus → from ui.widgets.core.events import bus
[Fix D3] استبدال bus.data_changed (محذوف) بـ bus.company_data_changed
"""

from ui.widgets.base.crud_form    import BaseCrudForm
from ui.widgets.panels.form_group import FormGroup
from ui.widgets.panels.form_fields import spin_field, labeled_widget
from ui.widgets.panels.form_badges import ResultBadge
from ui.widgets.forms.inputs      import RequiredLineEdit
from ui.widgets.combo.category    import CategoryCombo
from ui.widgets.core.events       import bus
from ui.widgets.core.i18n         import tr


class LaborOpForm(BaseCrudForm):
    """
    فورم عملية عمالة.

    المعاملات:
        conn     : اتصال DB
        settings : _LaborSettingsPanel — لحساب معدل الأجر
    """

    FORM_TITLE = tr("labor_op_form_title")
    ADD_TEXT   = f"➕  {tr('add')}"
    SAVE_TEXT  = f"💾  {tr('save_edit')}"

    def __init__(self, conn, settings, parent=None):
        self._settings = settings
        super().__init__(conn, parent)
        # ربط live preview
        self._sp_minutes.valueChanged.connect(self._update_preview)
        # تحديث التكلفة لو تغيرت الإعدادات
        bus.company_data_changed.connect(self._on_company_data_changed)

    def _on_company_data_changed(self, _company_id: int = None):
        """يُستدعى عند تغيير بيانات الشركة — يحدّث المعاينة الحية."""
        self._update_preview()

    # ══════════════════════════════════════════════════════
    # بناء الحقول
    # ══════════════════════════════════════════════════════

    def _build_fields(self, group: FormGroup):
        self._inp_name    = RequiredLineEdit(tr("labor_op_name_placeholder"))
        self._sp_minutes  = spin_field(max_=99999, dec=2)
        self._cmb_cat     = CategoryCombo(self.conn, scope="labor")
        self._lbl_cost    = ResultBadge()

        group.add_row(f"{tr('op_name')} :",   self._inp_name)
        group.add_row(f"{tr('time_label')} :", labeled_widget(self._sp_minutes, tr('minutes_label')))
        group.add_row(f"{tr('category')} :",  self._cmb_cat)
        group.add_row(f"{tr('cost_label')} :", self._lbl_cost)

    # ══════════════════════════════════════════════════════
    # Live preview
    # ══════════════════════════════════════════════════════

    def _update_preview(self):
        rate = self._settings.get_hourly_rate()
        cost = (self._sp_minutes.value() / 60.0) * rate
        self._lbl_cost.set_value(
            f"{cost:.2f} {tr('currency_per_unit')}"
            f"   ({self._sp_minutes.value():.2f} {tr('minutes_abbr')} ÷ 60 × {rate:.2f})"
        )

    # ══════════════════════════════════════════════════════
    # BaseCrudForm interface
    # ══════════════════════════════════════════════════════

    def _collect(self) -> dict | None:
        if not self._inp_name.validate():
            return None
        return {
            "name":        self._inp_name.text_stripped(),
            "minutes":     self._sp_minutes.value(),
            "category_id": self._cmb_cat.get_category(),
        }

    def _do_insert(self, data: dict) -> int:
        from services.costing.labor_op_service import LaborOpService
        return LaborOpService(self.conn).add(
            data["name"], data["minutes"], category_id=data["category_id"]
        )

    def _do_update(self, op_id: int, data: dict) -> None:
        from services.costing.labor_op_service import LaborOpService
        LaborOpService(self.conn).update(
            op_id, data["name"], data["minutes"], category_id=data["category_id"]
        )

    def _do_load(self, op_id: int) -> dict | None:
        from services.costing.labor_op_service import LaborOpService
        result = LaborOpService(self.conn).get(op_id)
        if result is None:
            return None
        return {
            "id":          result.id,
            "name":        result.name,
            "minutes":     result.minutes,
            "category_id": result.category_id,
        }

    def _fill_fields(self, data: dict) -> None:
        self._inp_name.setText(data["name"])
        self._sp_minutes.setValue(data.get("minutes", 0))
        self._cmb_cat.set_category(data.get("category_id"))
        self._update_preview()

    def _reset_fields(self) -> None:
        self._inp_name.clear()
        self._sp_minutes.setValue(0)
        self._lbl_cost.reset()
        self._cmb_cat.setCurrentIndex(0)