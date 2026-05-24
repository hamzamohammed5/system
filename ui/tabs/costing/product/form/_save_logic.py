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
"""

from PyQt5.QtWidgets import QMessageBox

from db.shared.items_repo import insert_item, update_item
from db.costing.bom_scenarios_repo import (
    insert_scenario, replace_bom_for_scenario,
)


class _SaveLogic:
    """
    Helper يتولى منطق الحفظ في DB.

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
        يحفظ المنتج والـ BOM.

        يرجع:
          - None لو فشل (مع عرض رسالة خطأ)
          - product_id لو نجح
        """
        if not name:
            QMessageBox.warning(parent_widget, "تنبيه", "ادخل اسم المنتج اولا")
            return None
        if not rows:
            QMessageBox.warning(parent_widget, "تنبيه", "اضف مكونا واحدا على الاقل")
            return None

        try:
            conn = self._conn_fn()

            if is_editing:
                update_item(conn, editing_id, name, 0, category_id=category_id)
                if current_scenario_id is None:
                    current_scenario_id = scenarios_panel.ensure_default_scenario(
                        editing_id
                    )
                replace_bom_for_scenario(conn, current_scenario_id, rows)
                pid = editing_id
            else:
                pid = insert_item(conn, name, product_type, 0, category_id=category_id)
                sc_id = insert_scenario(conn, pid, "سيناريو 1", is_default=True)
                replace_bom_for_scenario(conn, sc_id, rows)

            conn.commit()
            return pid

        except Exception as e:
            QMessageBox.warning(parent_widget, "خطأ", str(e))
            return None