"""
ui/events.py
============
Bus مركزي للإشعارات — أي tab يحفظ بيانات يبعت signal،
وكل tab تاني مشترك فيه يعمل refresh تلقائي.

الاستخدام:
    from ui.events import bus
    bus.data_changed.emit()          # بعد أي حفظ
    bus.data_changed.connect(fn)     # للاشتراك في التحديثات
"""

from PyQt5.QtCore import QObject, pyqtSignal


class _EventBus(QObject):
    data_changed = pyqtSignal()


bus = _EventBus()