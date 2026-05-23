"""
ui/events.py
============
Bus مركزي للإشعارات — أي tab يحفظ بيانات يبعت signal،
وكل tab تاني مشترك فيه يعمل refresh تلقائي.

الاستخدام:
    from ui.events import bus

    # إشعار عام (للـ widgets اللي مش مرتبطة بشركة محددة)
    bus.data_changed.emit()
    bus.data_changed.connect(fn)

    # إشعار مقيّد بشركة (الأفضل لتجنب تسريب البيانات بين الشركات)
    bus.company_data_changed.emit(company_id)
    bus.company_data_changed.connect(fn)   # fn(company_id: int)

    # تغيير حجم الخط
    bus.font_changed.emit(12)
    bus.font_changed.connect(fn)
"""

from PyQt5.QtCore import QObject, pyqtSignal


class _EventBus(QObject):
    # إشعار عام — للتوافق مع الكود القديم
    data_changed = pyqtSignal()

    # إشعار مقيّد بـ company_id — الأفضل للاستخدام الجديد
    # كل widget يقارن company_id قبل ما يستجيب
    company_data_changed = pyqtSignal(int)

    # تغيير حجم الخط
    font_changed = pyqtSignal(int)


bus = _EventBus()