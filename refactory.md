# خطة تعديل ملفات المراجع

## سبب التعديل
دمج `ui/events.py` في `ui/widgets/core/events.py` مع:
1. حذف `data_changed` signal (لا يوجد حالة بدون company_id)
2. حذف `ui/events.py` كملف مستقل
3. المصدر الوحيد أصبح `ui.widgets.core.events`

---

## التغييرات بالترتيب

---


### 5. `ui_widgets_9_managers_shared.md` — CategoryManager + SharedItemsListPanel

**المكان:** كل مكان فيه إشارة لـ `bus.data_changed`

**تغيير:**
```python
# قبل
# يستمع لـ bus.data_changed + bus.language_changed
```
**إلى:**
```python
# يستمع لـ bus.company_data_changed + bus.language_changed
```

**تغيير في CategoryForm:**
```python
# قبل
# يُطلق emit_company_data_changed() بعد النجاح
```
لا تغيير — موجود صح بالفعل.

---

### 6. `services_3_orders_accounting.md` — ملاحظات مهمة

**المكان:** قسم `## ملاحظات مهمة` → النقطة 1

**تغيير من:**
```python
# 1. bus events: استخدم emit_company_data_changed() من ui.widgets.core.events
#    بدل bus.data_changed.emit()
```
**إلى:**
```python
# 1. bus events: استخدم دائماً emit_company_data_changed() من ui.widgets.core.events
#    data_changed محذوف — كل الإشعارات عبر company_data_changed
```

---


## ملخص التغييرات

| الملف | نوع التغيير | عدد المواضع |
|-------|------------|------------|
| `ui_root.md` | حذف `data_changed` + تغيير مسار الاستيراد | 4 مواضع |
| `ui_widgets_1_core.md` | حذف `data_changed` + تحديث الأمثلة | 3 مواضع |
| `ui_widgets_2_base.md` | تنظيف إشارة `bus.data_changed.emit()` | 1 موضع |
| `ui_widgets_7_mixins.md` | حذف `data_changed` من `_connect_bus` | 2 موضع |
| `ui_widgets_9_managers_shared.md` | تغيير `data_changed` → `company_data_changed` | 1 موضع |
| `services_3_orders_accounting.md` | تحديث ملاحظة bus events | 1 موضع |
| `ui_widgets_5_panels_forms_combo.md` | تغيير CategoryCombo | 1 موضع |

**إجمالي: 13 موضع في 7 ملفات**