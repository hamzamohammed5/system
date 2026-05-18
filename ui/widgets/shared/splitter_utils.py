"""
ui/widgets/shared/splitter_utils.py
=====================================
أدوات مشتركة لإدارة الـ splitter بشكل ذكي:

1. SmartSplitter   — QSplitter بيضبط نفسه تلقائياً على محتوى الجدول
2. fit_list_panel  — دالة تضبط عرض الـ list panel على عرض الجدول الفعلي
3. SplitterAutoFit — mixin لأي widget يحتوي splitter + جدول قائمة

الاستخدام:
    from ui.widgets.shared.splitter_utils import fit_list_panel, SmartSplitter

    # في أي tab فيه splitter + جدول قائمة يسار + تفاصيل يمين:
    splitter = SmartSplitter(Qt.Horizontal)
    splitter.addWidget(self._list)
    splitter.addWidget(self._detail)
    splitter.set_list_widget(self._list, list_table=self._list.table)
    splitter.setSizes([320, 800])   # fallback لحد ما البيانات تتحمل
"""

from PyQt5.QtWidgets import QSplitter, QTableWidget, QWidget
from PyQt5.QtCore    import Qt, QTimer


# ══════════════════════════════════════════════════════════
# ثوابت
# ══════════════════════════════════════════════════════════

_MIN_LIST_W  = 280   # أقل عرض للقائمة
_MAX_LIST_W  = 620   # أقصى عرض للقائمة
_TOOLBAR_PAD = 24    # هامش إضافي للـ toolbar فوق الجدول + حواف
_SCROLLBAR_W = 18    # احتياطي عرض الـ scrollbar


# ══════════════════════════════════════════════════════════
# fit_list_panel — الدالة الأساسية (مشتركة)
# ══════════════════════════════════════════════════════════

def fit_list_panel(splitter: QSplitter,
                   list_index: int,
                   table: QTableWidget,
                   min_w: int = _MIN_LIST_W,
                   max_w: int = _MAX_LIST_W,
                   extra_pad: int = _TOOLBAR_PAD) -> int:
    """
    يضبط عرض الـ list panel في الـ splitter بحيث يساوي
    مجموع عرض الأعمدة الفعلية في الجدول (بعد ملء البيانات).

    يرجع العرض المستخدم.

    المعاملات:
        splitter   : الـ QSplitter
        list_index : رقم الـ panel (عادة 0)
        table      : الجدول داخل الـ panel
        min_w      : الحد الأدنى للعرض
        max_w      : الحد الأقصى للعرض
        extra_pad  : هامش إضافي (toolbar + حواف + scrollbar)
    """
    sizes = splitter.sizes()
    if not sizes or len(sizes) <= list_index:
        return min_w

    total = sum(sizes)
    if total <= 0:
        return min_w

    # حساب مجموع الأعمدة الفعلية
    col_total = _SCROLLBAR_W
    hh = table.horizontalHeader()
    for col in range(table.columnCount()):
        col_total += table.columnWidth(col)

    # الـ vertical header لو ظاهر
    vh = table.verticalHeader()
    if not vh.isHidden():
        col_total += vh.width()

    ideal = col_total + extra_pad
    target = max(min_w, min(ideal, max_w))

    # توزيع الباقي
    remaining = total - target
    old_list_w = sizes[list_index]
    old_other  = total - old_list_w

    new_sizes = list(sizes)
    new_sizes[list_index] = target

    if len(sizes) > 1 and old_other > 0:
        for i, sz in enumerate(sizes):
            if i != list_index:
                ratio = sz / old_other if old_other > 0 else 1.0
                new_sizes[i] = max(200, int(remaining * ratio))

    # تصحيح الفارق
    diff = total - sum(new_sizes)
    if diff != 0:
        detail_idx = 1 if list_index == 0 else 0
        if detail_idx < len(new_sizes):
            new_sizes[detail_idx] = max(200, new_sizes[detail_idx] + diff)

    splitter.setSizes(new_sizes)
    return target


def fit_list_panel_delayed(splitter: QSplitter,
                            list_index: int,
                            table: QTableWidget,
                            delay_ms: int = 0,
                            min_w: int = _MIN_LIST_W,
                            max_w: int = _MAX_LIST_W):
    """
    نفس fit_list_panel لكن مؤجل بـ delay_ms ميلي ثانية.
    مفيد لما الـ layout لسه مش اتحسب.
    """
    if delay_ms <= 0:
        fit_list_panel(splitter, list_index, table, min_w, max_w)
    else:
        QTimer.singleShot(
            delay_ms,
            lambda: fit_list_panel(splitter, list_index, table, min_w, max_w)
        )


# ══════════════════════════════════════════════════════════
# SmartSplitter — QSplitter بـ auto-fit
# ══════════════════════════════════════════════════════════

class SmartSplitter(QSplitter):
    """
    QSplitter بيضبط عرض الـ list panel تلقائياً.

    الاستخدام:
        splitter = SmartSplitter(Qt.Horizontal)
        splitter.addWidget(list_panel)
        splitter.addWidget(detail_panel)
        splitter.set_list_widget(list_panel, list_table=list_panel.table)
        splitter.setSizes([320, 800])   # fallback أولي

    بعد استدعاء _load() أو _apply_filter():
        splitter.fit_now()   # أو fit_delayed()
    """

    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self._list_index = 0
        self._table      = None
        self._min_w      = _MIN_LIST_W
        self._max_w      = _MAX_LIST_W

        self.setHandleWidth(4)
        self._apply_style()

    def _apply_style(self):
        from ui.app_settings import _C
        self.setStyleSheet(f"""
            QSplitter::handle {{
                background: {_C['border']};
            }}
            QSplitter::handle:hover {{
                background: {_C['accent_mid']};
            }}
            QSplitter::handle:pressed {{
                background: {_C['accent']};
            }}
        """)

    def set_list_widget(self, widget: QWidget,
                        list_table: QTableWidget,
                        list_index: int = 0,
                        min_w: int = _MIN_LIST_W,
                        max_w: int = _MAX_LIST_W):
        """
        يربط الـ splitter بالجدول للـ auto-fit.

        list_table : الجدول داخل الـ list panel
        list_index : رقم الـ panel في الـ splitter (افتراضي 0)
        """
        self._list_index = list_index
        self._table      = list_table
        self._min_w      = min_w
        self._max_w      = max_w

    def fit_now(self) -> int:
        """يضبط العرض فوراً — استدعيه بعد ملء البيانات."""
        if self._table is None:
            return self._min_w
        return fit_list_panel(
            self, self._list_index, self._table,
            self._min_w, self._max_w
        )

    def fit_delayed(self, delay_ms: int = 50):
        """يضبط العرض بعد تأخير بسيط (لضمان اكتمال الـ layout)."""
        if self._table is None:
            return
        QTimer.singleShot(
            delay_ms,
            self.fit_now
        )