"""
ui/widgets/shared/base_section.py
===================================
BaseSection — قاعدة مشتركة للأقسام اللي فيها list + detail.

القواعد:
  ✅ الـ list عرضه بين LIST_MIN_W و LIST_MAX_W — الـ handle مش بيتحرك أكتر
  ✅ لو النافذة أكبر من المجموع → الـ detail يكبر، الـ list يفضل ثابت
  ✅ الـ handle بيتوقف تلقائياً لما الجدول بيتشاف كامل (scroll اختفى)
  ✅ لو ضيّق الجدول وظهر scroll تاني → الـ handle بيتحرك عادي (dynamic)
  ✅ كل ده بيشتغل عبر _ListSplitterGuard المربوط بجدول الـ list panel
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QSizePolicy, QSplitter,
)
from PyQt5.QtCore import Qt, QTimer
from ui.app_settings import _C


class _ConstrainedSplitter(QSplitter):
    """
    QSplitter بيمنع الـ list panel من تعدي MAX_W.
    لما المستخدم يحرك الـ handle، لو الـ list راح فوق MAX_W
    بيرجعه للـ MAX_W تلقائياً.

    ملاحظة: الحد الأقصى الديناميكي (scroll-based) بيتولاه _ListSplitterGuard
    بشكل مستقل — الـ _ConstrainedSplitter بيطبّق الحد الأقصى الثابت (LIST_MAX_W).
    """
    def __init__(self, list_index: int, min_w: int, max_w: int,
                 orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self._list_index = list_index
        self._min_w      = min_w
        self._max_w      = max_w
        self.splitterMoved.connect(self._on_moved)

    def _on_moved(self, pos: int, index: int):
        sizes = self.sizes()
        if not sizes:
            return
        list_w = sizes[self._list_index]

        if list_w > self._max_w:
            diff = list_w - self._max_w
            new_sizes = list(sizes)
            new_sizes[self._list_index] = self._max_w
            other = 1 - self._list_index
            if other < len(new_sizes):
                new_sizes[other] += diff
            self.blockSignals(True)
            self.setSizes(new_sizes)
            self.blockSignals(False)

        elif list_w < self._min_w:
            diff = self._min_w - list_w
            new_sizes = list(sizes)
            new_sizes[self._list_index] = self._min_w
            other = 1 - self._list_index
            if other < len(new_sizes):
                new_sizes[other] = max(200, new_sizes[other] - diff)
            self.blockSignals(True)
            self.setSizes(new_sizes)
            self.blockSignals(False)

    def update_constraints(self, min_w: int, max_w: int):
        self._min_w = min_w
        self._max_w = max_w


class BaseSection(QWidget):
    LIST_MIN_W : int = 280
    LIST_MAX_W : int = 560

    def __init__(self, conn=None, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._list_guard = None   # _ListSplitterGuard للـ list
        self._build()
        self._connect_signals()
        self._attach_list_guard()           # ← ربط الـ guard بعد البناء
        QTimer.singleShot(50, self._apply_sizes)

    def _create_list(self):   raise NotImplementedError
    def _create_detail(self): raise NotImplementedError
    def _connect_signals(self): pass

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._splitter = _ConstrainedSplitter(
            list_index=0,
            min_w=self.LIST_MIN_W,
            max_w=self.LIST_MAX_W,
            orientation=Qt.Horizontal,
        )
        self._splitter.setHandleWidth(5)
        self._splitter.setStyleSheet(f"""
            QSplitter::handle {{ background: {_C['border']}; width: 5px; }}
            QSplitter::handle:hover {{ background: {_C['accent_mid']}; }}
            QSplitter::handle:pressed {{ background: {_C['accent']}; }}
        """)
        self._splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._list   = self._create_list()
        self._detail = self._create_detail()

        self._list.setMinimumWidth(self.LIST_MIN_W)
        self._list.setMaximumWidth(self.LIST_MAX_W)
        self._list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self._detail.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._detail.setMinimumWidth(300)

        self._splitter.addWidget(self._list)
        self._splitter.addWidget(self._detail)
        self._splitter.setCollapsible(0, False)
        self._splitter.setCollapsible(1, False)
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)

        root.addWidget(self._splitter)

    # ══════════════════════════════════════════════════════
    # ربط _ListSplitterGuard بجدول الـ list
    # ══════════════════════════════════════════════════════

    def _attach_list_guard(self):
        """
        يربط _ListSplitterGuard بجدول الـ list panel.

        الـ guard بيراقب horizontal scrollbar الجدول:
          • scroll اختفى  → يوقف الـ handle عند العرض الحالي.
          • scroll ظهر    → يرفع القفل (الـ handle يتحرك عادي).

        يحتاج الـ list panel يكون عنده `self.table` (BaseListPanel).
        """
        table = getattr(self._list, 'table', None)
        if table is None:
            return   # الـ list مش BaseListPanel

        try:
            from ui.widgets.shared.splitter_scroll_guard import _ListSplitterGuard
            self._list_guard = _ListSplitterGuard(
                outer_splitter = self._splitter,
                table          = table,
                list_index     = 0,
                debounce_ms    = 60,
                parent         = self,
            )
        except Exception:
            pass   # التطبيق يشتغل عادي بدون الـ guard

    # ══════════════════════════════════════════════════════
    # تحديث الـ guard بعد كل refresh للـ list
    # ══════════════════════════════════════════════════════

    def _refresh_list_guard(self):
        """
        استدعه بعد أي تغيير في بيانات الجدول أو عرض الأعمدة.
        بيعمل debounce تلقائياً.
        """
        if self._list_guard is not None:
            self._list_guard.refresh()

    # ══════════════════════════════════════════════════════

    def _apply_sizes(self):
        total = self._splitter.width()
        if total <= 0:
            total = self.width()
        if total <= 0:
            QTimer.singleShot(100, self._apply_sizes)
            return

        # عطّل الـ guard مؤقتاً عشان setSizes ما يطلّعش false lock
        if self._list_guard is not None:
            self._list_guard.set_enabled(False)

        list_w   = max(self.LIST_MIN_W,
                       min(self._list.width() or self.LIST_MIN_W, self.LIST_MAX_W))
        detail_w = max(300, total - list_w - self._splitter.handleWidth())
        self._splitter.blockSignals(True)
        self._splitter.setSizes([list_w, detail_w])
        self._splitter.blockSignals(False)

        # أعد تفعيل الـ guard بعد تأخير بسيط عشان الـ layout يستقر
        if self._list_guard is not None:
            QTimer.singleShot(80, lambda: (
                self._list_guard.set_enabled(True),
                self._list_guard.refresh(),
            ))
        else:
            self._refresh_list_guard()

    def _fit_splitter_delayed(self, delay_ms: int = 80):
        QTimer.singleShot(delay_ms, self._apply_sizes)

    def refresh(self):
        if hasattr(self._list, 'refresh'):
            self._list.refresh()
        self._fit_splitter_delayed()