"""
ui/widgets/utils/tooltip.py
=======================================
دوال مساعدة موحدة للـ tooltips في الجداول والـ widgets.

[Refactor V3 — المرحلة 3] إضافة refresh_tooltips alias لتوحيد الوظيفة
المتوزعة سابقاً على هذا الملف وعلى tables/flexible.py.

[إصلاح tooltip أبيض على Windows] إضافة CustomTooltipFilter +
install_custom_tooltip_filter().

  السبب: على Windows (خصوصاً windowsvista/windows11 style)، QToolTip
  الافتراضي بيتجاهل أحياناً كلاً من:
    1. الـ QSS المطبّق على QApplication (QToolTip {...} في theme.py)
    2. الـ QPalette (ToolTipBase/ToolTipText)
  ويرجع لرسم tooltip أبيض/افتراضي عبر محرك الثيم الأصلي للنظام
  (native theming engine) بدل محرك رسم Qt نفسه.

  الحل: event filter على مستوى QApplication يعترض QEvent.ToolTip
  قبل المعالجة الافتراضية، ويعرض بدلاً منه QLabel مخصص
  (window flag = Qt.ToolTip) بألوان الثيم الحالية من ui.theme._C
  مقروءة مباشرة وقت الظهور — يتماشى تلقائياً مع أي تغيير ثيم لاحق.

  الاستخدام (مرة واحدة، من main.py بعد إنشاء QApplication):
      from ui.widgets.utils.tooltip import install_custom_tooltip_filter
      install_custom_tooltip_filter(qt_app)

  ملاحظة: هذا الفلتر مستقل تماماً عن apply_table_tooltips/apply_tree_tooltips
  أعلاه — تلك الدوال تحدد *نص* الـ tooltip المعروض على كل خلية/عنصر،
  بينما هذا الفلتر يتحكم فقط في *شكل رسم* أي tooltip في التطبيق بعد
  أن يتحدد نصه (من هذا الملف أو من setToolTip() العادية في أي widget).
"""
from PyQt5.QtWidgets import (
    QTableWidget, QTreeWidget, QTreeWidgetItem,
    QLabel, QApplication, QWidget,
)
from PyQt5.QtCore import QObject, QEvent, Qt, QPoint


def apply_table_tooltips(table: QTableWidget,
                          cols: "list[int] | None" = None) -> None:
    """
    يضيف tooltip = النص الكامل لكل خلية في الجدول.

    cols: أعمدة محددة، أو None لكل الأعمدة.
    يُستدعى بعد ملء الجدول بالبيانات.
    """
    n_cols      = table.columnCount()
    target_cols = cols if cols is not None else list(range(n_cols))

    for r in range(table.rowCount()):
        for c in target_cols:
            item = table.item(r, c)
            if item and item.text() and not item.toolTip():
                item.setToolTip(item.text())


# alias موحّد — يُستخدم من tables/flexible.py بدل تعريف مكرر
refresh_tooltips = apply_table_tooltips


def apply_tree_tooltips(tree: QTreeWidget,
                         item: "QTreeWidgetItem | None" = None,
                         cols: "list[int] | None" = None,
                         recursive: bool = True) -> None:
    """
    يضيف tooltip = النص الكامل لكل عنصر في الشجرة.

    item     : عنصر محدد، أو None لكل العناصر.
    cols     : أعمدة محددة، أو None لكل الأعمدة.
    recursive: يشمل العناصر الفرعية.
    """
    n_cols      = tree.columnCount()
    target_cols = cols if cols is not None else list(range(n_cols))

    def _apply(node: QTreeWidgetItem):
        for c in target_cols:
            text = node.text(c)
            if text and not node.toolTip(c):
                node.setToolTip(c, text)
        if recursive:
            for i in range(node.childCount()):
                _apply(node.child(i))

    if item is not None:
        _apply(item)
    else:
        for i in range(tree.topLevelItemCount()):
            _apply(tree.topLevelItem(i))


# ══════════════════════════════════════════════════════════
# Custom tooltip rendering — يتخطى الرسم الأصلي للنظام (Windows)
# ══════════════════════════════════════════════════════════

class _TooltipLabel(QLabel):
    """QLabel عائم يُستخدم كـ tooltip مخصص — لا يمر بمحرك رسم النظام."""

    def __init__(self):
        super().__init__(None, Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setWordWrap(True)
        self.setMargin(0)

    def show_at(self, text: str, global_pos: QPoint):
        from ui.theme import _C
        from ui.font import fs, get_font_size

        base = get_font_size()
        size = fs(base, -1)

        self.setText(text)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {_C['text_primary']};
                color: {_C['bg_surface']};
                border: 1px solid {_C['text_primary']};
                border-radius: 4px;
                padding: 5px 10px;
                font-size: {size}pt;
            }}
        """)
        self.adjustSize()

        # إزاحة بسيطة عن مؤشر الماوس — نفس سلوك الـ tooltip الافتراضي تقريباً
        pos = QPoint(global_pos.x() + 14, global_pos.y() + 18)

        screen = QApplication.screenAt(global_pos) or QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            if pos.x() + self.width() > geo.right():
                pos.setX(geo.right() - self.width())
            if pos.y() + self.height() > geo.bottom():
                pos.setY(global_pos.y() - self.height() - 6)

        self.move(pos)
        self.show()


class CustomTooltipFilter(QObject):
    """
    Event filter عام: يعترض QEvent.ToolTip قبل المعالجة الافتراضية
    ويعرض _TooltipLabel بدلاً من QToolTip الأصلي.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._label = _TooltipLabel()

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.ToolTip:
            from PyQt5.QtGui import QHelpEvent
            widget = obj if isinstance(obj, QWidget) else None
            text = widget.toolTip() if widget else ""
            if text and isinstance(event, QHelpEvent):
                self._label.show_at(text, event.globalPos())
                return True  # امنع Qt من عرض الـ QToolTip الافتراضي كمان
            else:
                self._label.hide()
                return True

        if event.type() in (QEvent.Leave, QEvent.MouseButtonPress,
                            QEvent.HoverLeave, QEvent.Wheel):
            self._label.hide()

        return False


_installed_filter: "CustomTooltipFilter | None" = None


def install_custom_tooltip_filter(app: QApplication) -> CustomTooltipFilter:
    """
    يركّب الفلتر مرة واحدة على مستوى QApplication.
    يُستدعى من main.py بعد إنشاء QApplication مباشرة.

    آمن الاستدعاء المتكرر: لو مركّب بالفعل، يرجّع نفس instance
    بدون تركيب فلتر تاني فوقه.
    """
    global _installed_filter
    if _installed_filter is not None:
        return _installed_filter

    _installed_filter = CustomTooltipFilter(app)
    app.installEventFilter(_installed_filter)
    return _installed_filter
