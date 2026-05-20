"""
ui/widgets/shared/splitter_scroll_guard.py
==========================================
ملفين في ملف واحد:

1. _SplitterScrollGuard
   يربط الـ splitter الداخلي (جدول + spacer) بالـ horizontal scrollbar
   — يُستخدم في make_splitter_table_guarded()

2. _ListSplitterGuard  ← الجديد
   يراقب horizontal scrollbar لجدول القايمة ويتحكم في الـ
   splitter الخارجي (list panel vs detail panel).

   القاعدة:
     • scrollbar.maximum() == 0  → الجدول كامل → اقفل الـ splitter
       عند عرضه الحالي (المستخدم مش يقدر يوسّع أكتر).
     • scrollbar.maximum() > 0   → ظهر scroll → ارفع القفل
       (المستخدم يقدر يوسّع الـ list panel تاني).

   Dynamic تماماً:
     • لو المستخدم ضيّق الـ list panel → ظهر scroll → يقدر يوسّع تاني.
     • لو وسّع لحد ما الـ scroll اختفى → بيتوقف هناك.

الاستخدام:
    # في __init__ بعد بناء الـ splitter والـ list:
    self._list_guard = _ListSplitterGuard(
        outer_splitter = self._splitter,  # list/detail splitter
        table          = self._list.table,
        list_index     = 0,
        parent         = self,
    )
    # لازم تحتفظ بيه (self._list_guard) عشان GC ميحذفوش.

    # بعد كل refresh للجدول:
    self._list_guard.refresh()
"""

from PyQt5.QtCore import QObject, Qt, QTimer
from PyQt5.QtWidgets import QSplitter, QTableWidget, QAbstractScrollArea


# ══════════════════════════════════════════════════════════════════════
# _SplitterScrollGuard — الأصلي (للجداول الداخلية في make_splitter_table)
# ══════════════════════════════════════════════════════════════════════

class _SplitterScrollGuard(QObject):
    """
    يراقب الـ horizontal scrollbar للجدول ويمنع الـ splitter
    من التوسع أكتر من اللازم لما الجدول بيتشاف كامل.

    المعاملات:
        splitter    : QSplitter
        table       : QTableWidget المراقَب
        table_index : index الـ table جوا الـ splitter (عادةً 0)
        extra_pad   : مسافة إضافية للعرض (بكسل)
    """

    def __init__(self, splitter: QSplitter, table: QTableWidget,
                 table_index: int = 0, extra_pad: int = 20,
                 parent: QObject = None):
        super().__init__(parent)
        self._splitter    = splitter
        self._table       = table
        self._table_index = table_index
        self._extra_pad   = extra_pad
        self._max_w       = None
        self._locked_w    = None

        splitter.splitterMoved.connect(self._on_moved)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._check_scroll)

        if table.viewport():
            table.viewport().installEventFilter(self)
        table.horizontalScrollBar().rangeChanged.connect(self._on_scroll_range_changed)

    def _on_scroll_range_changed(self, min_val: int, max_val: int):
        if max_val == 0:
            sizes = self._splitter.sizes()
            if sizes and self._table_index < len(sizes):
                self._locked_w = sizes[self._table_index]
        else:
            self._locked_w = None

    def _on_moved(self, pos: int, index: int):
        if self._locked_w is None:
            return
        sizes = self._splitter.sizes()
        if not sizes or self._table_index >= len(sizes):
            return
        current_w = sizes[self._table_index]
        if current_w > self._locked_w:
            new_sizes = list(sizes)
            diff = current_w - self._locked_w
            new_sizes[self._table_index] = self._locked_w
            other = 1 - self._table_index
            if other < len(new_sizes):
                new_sizes[other] += diff
            self._splitter.blockSignals(True)
            self._splitter.setSizes(new_sizes)
            self._splitter.blockSignals(False)

    def _check_scroll(self):
        sb = self._table.horizontalScrollBar()
        self._on_scroll_range_changed(sb.minimum(), sb.maximum())

    def refresh(self):
        self._timer.start()

    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        if event.type() in (QEvent.Resize, QEvent.Show):
            self._timer.start()
        return False


# ══════════════════════════════════════════════════════════════════════
# _ListSplitterGuard — جديد (للـ splitter الخارجي list/detail)
# ══════════════════════════════════════════════════════════════════════

class _ListSplitterGuard(QObject):
    """
    يراقب horizontal scrollbar لجدول القايمة ويتحكم في الـ
    splitter الخارجي (list panel vs detail panel).

    الفكرة:
      • الجدول كامل (scroll اختفى)  → اقفل الـ handle عند عرضه الحالي.
      • ظهر scroll تاني              → ارفع القفل فوراً.

    Dynamic:
      • ضيّق الـ panel → ظهر scroll → يقدر يوسّع.
      • وسّع لحد ما scroll اختفى → بيتوقف هناك.

    المعاملات:
        outer_splitter : الـ QSplitter الخارجي (list vs detail)
        table          : الجدول جوا الـ list panel
        list_index     : index الـ list panel في الـ splitter (عادةً 0)
        debounce_ms    : تأخير قبل التحقق من الـ scroll (للاستقرار)
        parent         : QObject parent (عشان GC)
    """

    def __init__(self, outer_splitter: QSplitter, table: QTableWidget,
                 list_index: int = 0, debounce_ms: int = 60,
                 parent: QObject = None):
        super().__init__(parent)

        self._splitter   = outer_splitter
        self._table      = table
        self._list_index = list_index
        self._locked_w   = None   # None = مفيش قفل
        self._enabled    = True

        # ── نراقب حركة الـ handle ──
        outer_splitter.splitterMoved.connect(self._on_handle_moved)

        # ── نراقب تغيير مدى الـ scrollbar ──
        table.horizontalScrollBar().rangeChanged.connect(
            self._on_scroll_range_changed
        )

        # ── debounce timer للـ resize events ──
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(debounce_ms)
        self._timer.timeout.connect(self._recheck)

        # ── راقب الـ viewport resize ──
        if table.viewport():
            table.viewport().installEventFilter(self)

        # ── راقب الـ table نفسه ──
        table.installEventFilter(self)

    # ══════════════════════════════════════════════════════
    # منطق القفل
    # ══════════════════════════════════════════════════════

    def _on_scroll_range_changed(self, min_val: int, max_val: int):
        """
        بيتنادى لما الـ scrollbar يظهر أو يختفي.
        max_val == 0  → الجدول كامل → اقفل.
        max_val > 0   → ظهر scroll  → ارفع القفل.
        """
        if max_val == 0:
            # الجدول كامل — احفظ العرض الحالي كحد أقصى
            sizes = self._splitter.sizes()
            if sizes and self._list_index < len(sizes):
                self._locked_w = sizes[self._list_index]
        else:
            # ظهر scroll — ارفع القفل فوراً
            self._locked_w = None

    def _on_handle_moved(self, pos: int, index: int):
        """
        لما المستخدم يحرك الـ handle:
        لو في قفل وبيحاول يعدي الحد → ارجعه.
        """
        if self._locked_w is None or not self._enabled:
            return

        sizes = self._splitter.sizes()
        if not sizes or self._list_index >= len(sizes):
            return

        current_list_w = sizes[self._list_index]

        if current_list_w > self._locked_w:
            # تجاوز الحد — ارجعه
            diff      = current_list_w - self._locked_w
            new_sizes = list(sizes)
            new_sizes[self._list_index] = self._locked_w

            other = 1 - self._list_index   # الـ detail panel
            if 0 <= other < len(new_sizes):
                new_sizes[other] += diff

            self._splitter.blockSignals(True)
            self._splitter.setSizes(new_sizes)
            self._splitter.blockSignals(False)

    # ══════════════════════════════════════════════════════
    # إعادة التحقق بعد resize أو refresh
    # ══════════════════════════════════════════════════════

    def _recheck(self):
        """إعادة تقييم حالة الـ scroll وتحديث القفل."""
        sb      = self._table.horizontalScrollBar()
        max_val = sb.maximum()
        self._on_scroll_range_changed(sb.minimum(), max_val)

    def refresh(self):
        """
        استدعيه بعد كل refresh للجدول أو تغيير بياناته.
        بيعمل debounce قبل التحقق من الـ scroll.
        """
        self._timer.start()

    # ══════════════════════════════════════════════════════
    # Event Filter
    # ══════════════════════════════════════════════════════

    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        if event.type() in (QEvent.Resize, QEvent.Show, QEvent.Polish):
            self._timer.start()
        return False   # مش بنأكل الـ event

    # ══════════════════════════════════════════════════════
    # تفعيل / تعطيل
    # ══════════════════════════════════════════════════════

    def set_enabled(self, enabled: bool):
        """تعطيل القفل مؤقتاً (مثلاً لما بنضبط الأحجام برمجياً)."""
        self._enabled = enabled
        if not enabled:
            self._locked_w = None

    @property
    def is_locked(self) -> bool:
        """True لو القفل مفعّل حالياً."""
        return self._locked_w is not None

    @property
    def locked_width(self):
        """العرض المقفول الحالي (None لو مفيش قفل)."""
        return self._locked_w