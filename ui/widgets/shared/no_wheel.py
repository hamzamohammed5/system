"""
ui/widgets/shared/no_wheel.py
======================
يمنع عجلة الماوس من تغيير قيمة أي input widget
(QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QSlider).

بدل ما العجلة تغيير القيمة، بتعدي الـ event للأب (scroll area أو الصفحة).

الاستخدام — مكانين:
  1. install_no_wheel_filter(app)  ← مرة واحدة في main()، يغطي كل التطبيق
  2. NoWheelCombo / NoWheelSpin / NoWheelDouble ← لو محتاج widget منفرد
"""

from PyQt5.QtCore    import QEvent, QObject, Qt 
from PyQt5.QtWidgets import (
    QApplication, QComboBox, QSpinBox, QDoubleSpinBox,
    QDateEdit, QTimeEdit, QSlider, QAbstractSpinBox,
)

from PyQt5.QtWidgets import QScrollArea, QAbstractScrollArea
from PyQt5.QtCore import QPoint


_BLOCKED_TYPES = (
    QComboBox,
    QAbstractSpinBox,   # يشمل QSpinBox + QDoubleSpinBox + QDateEdit + QTimeEdit
    QSlider,
)


class _NoWheelFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            if isinstance(obj, _BLOCKED_TYPES):
                # لو Shift مضغوط، ابلوك تماماً — الـ ShiftWheelFilter هيتكلم
                if event.modifiers() & Qt.ShiftModifier:
                    return True
                parent = obj.parentWidget()
                if parent:
                    QApplication.sendEvent(parent, event)
                return True
        return False


_filter_instance = None


class _WheelFilter(QObject):
    """
    Filter واحد بيتعامل مع كل حالات الـ wheel:
      - Shift + Wheel  → horizontal scroll في أقرب scroll area
      - Wheel على input widget → يبعته للـ parent (vertical scroll)
    """
    def eventFilter(self, obj, event):
        if event.type() != QEvent.Wheel:
            return False

        # ══ Shift + Wheel → Horizontal Scroll ══
        if event.modifiers() & Qt.ShiftModifier:
            target = obj
            while target is not None:
                if isinstance(target, QAbstractScrollArea):
                    sb = target.horizontalScrollBar()
                    if sb and sb.maximum() > 0:
                        delta = event.angleDelta().y()
                        sb.setValue(sb.value() - delta // 2)
                        return True
                if not hasattr(target, 'parentWidget'):
                    break
                target = target.parentWidget()
            return True  # بلوك حتى لو مفيش horizontal scroll

        # ══ Wheel على input widget → منع التغيير، vertical scroll للـ parent ══
        if isinstance(obj, _BLOCKED_TYPES):
            parent = obj.parentWidget()
            if parent:
                QApplication.sendEvent(parent, event)
            return True

        return False


_wheel_filter_instance = None


def install_no_wheel_filter(app: QApplication):
    """نفس الاسم القديم للتوافق — بس دلوقتي بيثبت الـ filter الموحد."""
    global _wheel_filter_instance
    _wheel_filter_instance = _WheelFilter(app)
    app.installEventFilter(_wheel_filter_instance)


def install_shift_wheel_filter(app: QApplication):
    """مش محتاجها دلوقتي — موجودة للتوافق مع main.py."""
    pass  # الـ filter الموحد بيتولى الاتنين
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

# ══════════════════════════════════════════════════════════
# Shift+Wheel → Horizontal Scroll
# ══════════════════════════════════════════════════════════


class _ShiftWheelFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            if event.modifiers() & Qt.ShiftModifier:
                # نلاقي أقرب scroll area للـ widget اللي تحت المؤشر
                target = obj
                while target is not None:
                    if isinstance(target, QAbstractScrollArea):
                        sb = target.horizontalScrollBar()
                        if sb and sb.maximum() > 0:
                            delta = event.angleDelta().y()
                            sb.setValue(sb.value() - delta // 2)
                            return True  # ← consume هنا، متوصلش لحد تاني
                    if not hasattr(target, 'parentWidget'):
                        break
                    target = target.parentWidget()
                return True  # ← حتى لو مفيش horizontal scroll، ابلوك الـ event
        return False


_shift_filter_instance = None


def install_shift_wheel_filter(app: QApplication):
    """
    يثبّت Shift+Wheel → horizontal scroll على مستوى التطبيق كله.
    استدعها مرة واحدة في main() بعد install_no_wheel_filter.
    """
    global _shift_filter_instance
    _shift_filter_instance = _ShiftWheelFilter(app)
    app.installEventFilter(_shift_filter_instance)