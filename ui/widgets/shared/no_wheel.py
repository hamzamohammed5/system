"""
ui/widgets/shared/no_wheel.py
======================
يمنع عجلة الماوس من تغيير قيمة أي input widget
(QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QSlider).

بدل ما العجلة تغيير القيمة، بتعدي الـ event للأب (scroll area أو الصفحة).

الاستخدام — مكان واحد فقط:
  install_no_wheel_filter(app)  ← مرة واحدة في main()، يغطي كل التطبيق

أو استخدم الـ subclasses المخصصة:
  NoWheelCombo / NoWheelSpin / NoWheelDouble ← لو محتاج widget منفرد
"""

from PyQt5.QtCore    import QEvent, QObject, Qt
from PyQt5.QtWidgets import (
    QApplication, QComboBox, QSpinBox, QDoubleSpinBox,
    QDateEdit, QTimeEdit, QSlider, QAbstractSpinBox,
    QAbstractScrollArea,
)


_BLOCKED_TYPES = (
    QComboBox,
    QAbstractSpinBox,   # يشمل QSpinBox + QDoubleSpinBox + QDateEdit + QTimeEdit
    QSlider,
)


def _find_scrollable_parent(widget, horizontal: bool = False):
    """
    يتسلق شجرة الـ parents ويرجع أول QAbstractScrollArea
    يملك scrollbar أفقي (لو horizontal=True) أو رأسي.
    """
    target = widget
    while target is not None:
        if isinstance(target, QAbstractScrollArea):
            if horizontal:
                sb = target.horizontalScrollBar()
                if sb and sb.maximum() > 0:
                    return target
            else:
                sb = target.verticalScrollBar()
                if sb and sb.maximum() > 0:
                    return target
        if not hasattr(target, 'parentWidget'):
            break
        target = target.parentWidget()
    return None


class _WheelFilter(QObject):
    """
    Filter واحد بيتعامل مع كل حالات الـ wheel:

      Shift + Wheel  → horizontal scroll في أقرب scroll area له
                       horizontal scrollbar مفعّل.

      Wheel على input widget → يبعته للـ parent (vertical scroll).
    """

    def eventFilter(self, obj, event):
        if event.type() != QEvent.Wheel:
            return False

        # ══ Shift + Wheel → Horizontal Scroll ══
        if event.modifiers() & Qt.ShiftModifier:
            widget_under = QApplication.widgetAt(event.globalPos())
            start = widget_under if widget_under else obj

            area = _find_scrollable_parent(start, horizontal=True)
            if area is None:
                area = _find_scrollable_parent(obj, horizontal=True)

            if area:
                sb = area.horizontalScrollBar()
                delta = event.angleDelta().y()
                sb.setValue(sb.value() - delta // 2)
                return True

            return True

        # ══ Wheel على input widget → منع التغيير ══
        if isinstance(obj, _BLOCKED_TYPES):
            parent = obj.parentWidget()
            if parent:
                QApplication.sendEvent(parent, event)
            return True

        return False


_wheel_filter_instance = None


def install_no_wheel_filter(app: QApplication):
    """
    يثبّت الـ filter الموحد على مستوى التطبيق.
    استدعها مرة واحدة في main().
    يتكفل بـ:
      - منع الـ wheel على inputs
      - Shift+Wheel → horizontal scroll
    """
    global _wheel_filter_instance
    _wheel_filter_instance = _WheelFilter(app)
    app.installEventFilter(_wheel_filter_instance)


# للتوافق مع الكود القديم — تستدعي install_no_wheel_filter مباشرة
install_shift_wheel_filter = install_no_wheel_filter


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