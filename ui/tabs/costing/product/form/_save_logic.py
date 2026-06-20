"""
ui/tabs/costing/product/form/_save_logic.py
============================================
_SaveLogic — منطق حفظ بيانات المنتج في DB.

مسؤوليته:
  - إدراج منتج جديد
  - تحديث منتج موجود
  - حفظ BOM للسيناريو الحالي
  - ضمان وجود سيناريو default

يُستخدم من `product_form.py` فقط.

[Refactor] استخدام ProductService + BomComponent بدل repos مباشرة:
  من: db.shared.items_repo + db.costing.bom_scenarios_repo
  إلى: services.costing.product_service
"""

from PyQt5.QtWidgets import QMessageBox

from services.costing.product_service import ProductService, BomComponent
from ui.widgets.core.i18n             import tr


class _SaveLogic:
    """
    Helper يتولى منطق الحفظ في DB عبر ProductService.

    الاستخدام:
        saver = _SaveLogic(conn_fn=self._live_conn)
        pid = saver.save(
            is_editing=True,
            editing_id=5,
            name="منتج أ",
            product_type="final",
            category_id=2,
            current_scenario_id=10,
            rows=[...],
            scenarios_panel=self._scenarios_panel,
            parent_widget=self,
        )
        # pid = None لو فشل، وإلا ID المنتج المحفوظ
    """

    def __init__(self, conn_fn):
        """
        conn_fn: callable يرجع connection حي (عادةً self._live_conn)
        """
        self._conn_fn = conn_fn

    def save(self, *, is_editing: bool, editing_id,
             name: str, product_type: str, category_id,
             current_scenario_id, rows: list,
             scenarios_panel, parent_widget) -> int | None:
        """
        يحفظ المنتج والـ BOM عبر ProductService.

        rows: list of tuples (child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id)

        يرجع:
          - None لو فشل (مع عرض رسالة خطأ)
          - product_id لو نجح
        """
        if not name:
            QMessageBox.warning(parent_widget, tr("warning"), tr("enter_product_name"))
            return None
        if not rows:
            QMessageBox.warning(parent_widget, tr("warning"), tr("add_one_component"))
            return None

        # تحويل الصفوف إلى BomComponent objects
        components = []
        for r in rows:
            # r = (child_type, child_id, qty, waste_pct, variant_id, machine_op_row_id)
            # نضمن وجود كل العناصر
            child_type       = r[0]
            child_id         = r[1]
            qty              = r[2]
            waste_pct        = r[3] if len(r) > 3 and r[3] is not None else 0.0
            variant_id       = r[4] if len(r) > 4 else None
            machine_op_row_id = r[5] if len(r) > 5 else None

            components.append(BomComponent(
                child_type=child_type,
                child_id=child_id,
                qty=qty,
                waste_pct=waste_pct,
                variant_id=variant_id,
                machine_op_row_id=machine_op_row_id,
            ))

        try:
            conn = self._conn_fn()
            svc  = ProductService(conn)

            # بناء product_data
            product_data = {
                "id":          editing_id if is_editing else None,
                "name":        name,
                "type":        product_type,
                "price":       0,
                "category_id": category_id,
            }

            # تحديد الـ scenario_id للحفظ
            # لو in_memory (current_scenario_id سالب) → None (ProductService ينشئ سيناريو جديد)
            # لو DB mode → نمرر الـ id الحالي
            save_scenario_id = None
            if current_scenario_id is not None and current_scenario_id > 0:
                save_scenario_id = current_scenario_id
            elif is_editing and current_scenario_id is None:
                # نضمن وجود سيناريو default
                save_scenario_id = scenarios_panel.ensure_default_scenario(editing_id)

            result = svc.save(
                product_data=product_data,
                components=components,
                scenario_id=save_scenario_id,
            )

            conn.commit()
            return result.product_id

        except Exception as e:
            QMessageBox.warning(parent_widget, tr("error"), str(e))
            return None