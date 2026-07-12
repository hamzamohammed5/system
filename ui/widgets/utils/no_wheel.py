"""
ui/widgets/utils/no_wheel.py
========================================
يمنع عجلة الماوس من تغيير قيمة input widgets.
نسخة موحدة من widgets/shared/no_wheel.py
"""
from PyQt5.QtCore    import QEvent, QObject, Qt
from PyQt5.QtWidgets import (
    QApplication, QSpinBox, QDoubleSpinBox,
    QDateEdit, QTimeEdit, QSlider, QAbstractSpinBox,
    QAbstractScrollArea,
)
from ui.widgets.panels.themed_inputs import ThemedComboBox

_BLOCKED = (ThemedComboBox, QAbstractSpinBox, QSlider)


def _find_scrollable_parent(widget, horizontal: bool = False):
    target = widget
    while target is not None:
        if isinstance(target, QAbstractScrollArea):
            sb = (target.horizontalScrollBar() if horizontal
                  else target.verticalScrollBar())
            if sb and sb.maximum() > 0:
                return target
        if not hasattr(target, 'parentWidget'):
            break
        target = target.parentWidget()
    return None


class _WheelFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() != QEvent.Wheel:
            return False

        if event.modifiers() & Qt.ShiftModifier:
            widget_under = QApplication.widgetAt(event.globalPos())
            start = widget_under if widget_under else obj
            area  = (_find_scrollable_parent(start, horizontal=True) or
                     _find_scrollable_parent(obj,   horizontal=True))
            if area:
                area.horizontalScrollBar().setValue(
                    area.horizontalScrollBar().value() - event.angleDelta().y() // 2
                )
            return True

        if isinstance(obj, _BLOCKED):
            parent = obj.parentWidget()
            if parent:
                QApplication.sendEvent(parent, event)
            return True

        return False


_wheel_filter_instance = None


def install_no_wheel_filter(app: QApplication):
    global _wheel_filter_instance
    _wheel_filter_instance = _WheelFilter(app)
    app.installEventFilter(_wheel_filter_instance)


# alias
install_shift_wheel_filter = install_no_wheel_filter


class NoWheelCombo(ThemedComboBox):
    def wheelEvent(self, e): e.ignore()


class NoWheelSpin(QSpinBox):
    def wheelEvent(self, e): e.ignore()


class NoWheelDouble(QDoubleSpinBox):
    def wheelEvent(self, e): e.ignore()


class NoWheelDate(QDateEdit):
    def wheelEvent(self, e): e.ignore()


class NoWheelSlider(QSlider):
    def wheelEvent(self, e): e.ignore()