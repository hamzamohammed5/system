"""
ui/widgets/no_wheel.py
======================
يمنع عجلة الماوس من تغيير قيمة أي input widget
(QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QSlider).

بدل ما العجلة تغيير القيمة، بتعدي الـ event للأب (scroll area أو الصفحة).

الاستخدام — مكانين:
  1. install_no_wheel_filter(app)  ← مرة واحدة في main()، يغطي كل التطبيق
  2. NoWheelCombo / NoWheelSpin / NoWheelDouble ← لو محتاج widget منفرد
"""

from PyQt5.QtCore    import QEvent, QObject
from PyQt5.QtWidgets import (
    QApplication, QComboBox, QSpinBox, QDoubleSpinBox,
    QDateEdit, QTimeEdit, QSlider, QAbstractSpinBox,
)


_BLOCKED_TYPES = (
    QComboBox,
    QAbstractSpinBox,   # يشمل QSpinBox + QDoubleSpinBox + QDateEdit + QTimeEdit
    QSlider,
)


class _NoWheelFilter(QObject):    # ← لازم يرث من QObject
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            if isinstance(obj, _BLOCKED_TYPES):
                parent = obj.parentWidget()
                if parent:
                    QApplication.sendEvent(parent, event)
                return True
        return False


_filter_instance = None


def install_no_wheel_filter(app: QApplication):
    global _filter_instance
    _filter_instance = _NoWheelFilter(app)   # app كـ parent عشان ميتحذفش
    app.installEventFilter(_filter_instance)


# ══════════════════════════════════════════════════════════
# Subclasses جاهزة — لو محتاج widget واحد بدون الفلتر العام
# ══════════════════════════════════════════════════════════

class NoWheelCombo(QComboBox):
    """QComboBox لا يستجيب لعجلة الماوس."""
    def wheelEvent(self, event):
        event.ignore()


class NoWheelSpin(QSpinBox):
    """QSpinBox لا يستجيب لعجلة الماوس."""
    def wheelEvent(self, event):
        event.ignore()


class NoWheelDouble(QDoubleSpinBox):
    """QDoubleSpinBox لا يستجيب لعجلة الماوس."""
    def wheelEvent(self, event):
        event.ignore()


class NoWheelDate(QDateEdit):
    """QDateEdit لا يستجيب لعجلة الماوس."""
    def wheelEvent(self, event):
        event.ignore()


class NoWheelSlider(QSlider):
    """QSlider لا يستجيب لعجلة الماوس."""
    def wheelEvent(self, event):
        event.ignore()
