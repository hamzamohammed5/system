"""
ui/widgets/base/section.py
==========================
BaseSection — قاعدة مشتركة للأقسام اللي فيها list + detail.

[T-05] توحيد BaseSection و CrudSection:
  - BaseSection أُضيفت إليها خصائص CrudSection:
      LIST_MAX_W, SPLITTER_RATIO, FORM_POSITION
      _create_form() → QWidget | None
      form_panel property

  - CrudSection في panels/crud_section.py أصبحت alias لـ BaseSection
    للتوافق مع الكود القديم.

[توحيد الجداول/Splitters — إصلاح] حذف FORM_POSITION = "top"/"bottom":
  المشكلة: القيمتين دول كانوا بيبنوا QVBoxLayout يدوي جوه left_widget
  (فورم + قائمة فوق بعض عموديًا) *داخل نفس عمود الـ QSplitter الأفقي* —
  ده تخطيط عمودي مدمج، مش splitter مستقل قابل للسحب بين الفورم والقائمة.
  نفس المشكلة بالظبط اللي كانت في RawSection قبل تصحيحها (كانت
  FORM_POSITION = "top" مع _create_detail() فاضية/مخفية).

  الحل: أي قسم محتاج فورم + قائمة/جدول جنب بعض (قابلين للسحب) لازم
  يستخدم _create_list() للفورم و_create_detail() للجدول مباشرة (أو
  العكس حسب LAYOUT_REVERSED) — بالظبط زي نمط OrdersTab. FORM_POSITION
  بقت تدعم قيمتين بس دلوقتي:
      "none" → لا فورم منفصل (default)
      "left" → فورم يُنشأ عبر _create_form() لكن بيُعرض جوه list panel
               نفسها (مش splitter منفصل) — للحالات النادرة اللي مش
               محتاجة فصل بصري قابل للسحب.
  أي subclass كان بيستخدم "bottom" أو "top" لازم يتحول ليبني الفورم
  والجدول كـ widgets منفصلة ويرجعهم من _create_list()/_create_detail().

  - override المطلوب:
      _create_list()   → QWidget
      _create_detail() → QWidget

  - override الاختياري:
      _create_form()        → QWidget | None
      _connect_signals()
      _refresh_data(company_id)
      _on_item_selected(item_id)
      LIST_MIN_W, LIST_MAX_W, DETAIL_MIN_W
      CONNECT_BUS, LAYOUT_REVERSED, FORM_POSITION, SPLITTER_RATIO
"""
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout,
    QSizePolicy, QSplitter,
)
from PyQt5.QtCore import Qt, QTimer

from ..theme.table_styles import splitter_style
from ui.constants import (
    LIST_PANEL_MIN_W, LIST_PANEL_MAX_W, DETAIL_PANEL_MIN_W,
    SPLITTER_HANDLE_W, SPLITTER_RATIO, SPLITTER_APPLY_DELAY,
    SPLITTER_RETRY_DELAY, REFRESH_AFTER_SAVE_DELAY,
    LIST_W_OFFSET,
)
from ui.widgets.core.widget_mixin import WidgetMixin


class BaseSection(QWidget, WidgetMixin):
    """
    قاعدة مشتركة للأقسام ذات التخطيط list + detail.

    Override المطلوب:
        _create_list()   → QWidget
        _create_detail() → QWidget

    Override الاختياري:
        _create_form()        → QWidget | None  (افتراضي: None)
        _connect_signals()
        _refresh_data(company_id)
        _on_item_selected(item_id)
        LIST_MIN_W, LIST_MAX_W, DETAIL_MIN_W
        CONNECT_BUS, LAYOUT_REVERSED, FORM_POSITION, SPLITTER_RATIO
    """

    LIST_MIN_W      : int   = LIST_PANEL_MIN_W
    LIST_MAX_W      : int   = LIST_PANEL_MAX_W
    DETAIL_MIN_W    : int   = DETAIL_PANEL_MIN_W
    CONNECT_BUS     : bool  = False
    LAYOUT_REVERSED : bool  = False

    # يسمح بإخفاء أي من الجانبين (list/detail) بالكامل لو المستخدم سحب
    # حافة الـ splitter لحد قريب جداً من النهاية. الرجوع بيتم بنفس
    # السحب اليدوي من نفس الحافة (سلوك QSplitter الافتراضي).
    # True = السلوك الافتراضي لأي قسم جديد. لو شاشة معينة محتاجة تمنع
    # الانهيار (الجانبان لازم يفضلوا ظاهرين دايماً)، تعمل override محلي:
    #     COLLAPSIBLE = False
    COLLAPSIBLE     : bool  = True

    # [T-05] من CrudSection — موضع الفورم
    # [توحيد الجداول/Splitters — إصلاح] حُذفت "top"/"bottom": كانوا بيبنوا
    # QVBoxLayout يدوي (تخطيط عمودي مدمج) بدل splitter حقيقي بين قسمين —
    # راجع تعليق أعلى الملف. أي قسم محتاج فورم+قائمة جنب بعض قابلين للسحب
    # لازم يستخدم _create_list()/_create_detail() مباشرة بدل FORM_POSITION.
    # "none" → لا فورم
    # "left" → نفس list panel (لا يُضاف splitter منفصل)
    FORM_POSITION   : str   = "none"

    # [T-05] من CrudSection — نسبة الـ splitter
    SPLITTER_RATIO  : tuple = SPLITTER_RATIO

    def __init__(self, conn=None, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._form: "QWidget | None" = None
        self._build()
        self._connect_signals()
        self._init_widget_mixin(theme=True, font=False, lang=False,
                                data=self.CONNECT_BUS)
        self._refresh_style()
        QTimer.singleShot(SPLITTER_APPLY_DELAY, self._apply_sizes)

    # ── override المطلوب ──────────────────────────────────

    def _create_list(self) -> QWidget:
        raise NotImplementedError

    def _create_detail(self) -> QWidget:
        raise NotImplementedError

    # ── override الاختياري ────────────────────────────────

    def _create_form(self) -> "QWidget | None":
        """
        [T-05] يُنشئ فورم الإضافة/التعديل.
        افتراضياً: None (لا فورم).
        Override لإضافة فورم.
        """
        return None

    # ── [i18n/themes] Theme handler ───────────────────────

    def _refresh_style(self, *_):
        self._splitter.setStyleSheet(splitter_style())

    def _connect_signals(self):
        if hasattr(self._list, "item_selected") and hasattr(self._detail, "load_item"):
            self._list.item_selected.connect(self._detail.load_item)

    def _refresh_data(self, company_id=None):
        self.refresh()

    def _on_item_selected(self, item_id: int):
        """
        [T-05] من CrudSection — يُستدعى عند اختيار عنصر.
        Override لتنفيذ منطق مخصص.
        """
        if hasattr(self._detail, "load_item"):
            self._detail.load_item(item_id)

    # ── بناء الواجهة ──────────────────────────────────────

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.setHandleWidth(SPLITTER_HANDLE_W)
        self._splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._list   = self._create_list()
        self._detail = self._create_detail()

        # [T-05] بناء الجانب الأيسر مع الفورم (لو وُجد)
        left_widget = self._build_left_panel()

        left_widget.setMinimumWidth(self.LIST_MIN_W)
        left_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self._detail.setMinimumWidth(self.DETAIL_MIN_W)
        self._detail.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        if self.LAYOUT_REVERSED:
            widgets   = [self._detail, left_widget]
            stretches = [self.SPLITTER_RATIO[1], self.SPLITTER_RATIO[0]]
        else:
            widgets   = [left_widget, self._detail]
            stretches = [self.SPLITTER_RATIO[0], self.SPLITTER_RATIO[1]]

        for i, w in enumerate(widgets):
            self._splitter.addWidget(w)
            self._splitter.setCollapsible(i, self.COLLAPSIBLE)
            self._splitter.setStretchFactor(i, stretches[i])

        root.addWidget(self._splitter)

    def _build_left_panel(self) -> QWidget:
        """
        [T-05] يبني لوحة القائمة (لو FORM_POSITION != "none").

        [توحيد الجداول/Splitters — إصلاح] حُذفت حالة "bottom"/"top":
        كانوا بيبنوا QVBoxLayout يدوي (فورم+قائمة فوق بعض) داخل نفس
        عمود الـ splitter — تخطيط عمودي مدمج مش splitter حقيقي بين
        قسمين قابلين للسحب. أي قسم محتاج فورم وجدول جنب بعض قابلين
        للسحب لازم يرجّعهم كـ widgets منفصلة من _create_list() و
        _create_detail() (بالظبط زي OrdersTab)، مش عبر FORM_POSITION.

        FORM_POSITION = "none" → يرجع self._list مباشرة
        FORM_POSITION = "left" → يرجع self._list (الفورم خارج الـ splitter،
                                  لو الـ subclass حابب يستخدمه بنفسه عبر
                                  form_panel property)
        """
        form = self._create_form()

        if form is None or self.FORM_POSITION == "none":
            self._form = None
            return self._list

        # FORM_POSITION = "left" أو أي قيمة أخرى → list فقط
        # (الفورم موجود لكن خارج الـ splitter، متاح عبر form_panel property)
        self._form = form
        return self._list

    def _apply_sizes(self):
        total = self._splitter.width() or self.width()
        if total <= 0:
            QTimer.singleShot(SPLITTER_RETRY_DELAY, self._apply_sizes)
            return

        list_w   = max(self.LIST_MIN_W, min(self.LIST_MIN_W + LIST_W_OFFSET, self.LIST_MAX_W))
        detail_w = max(self.DETAIL_MIN_W, total - list_w - self._splitter.handleWidth())

        self._splitter.blockSignals(True)
        if self.LAYOUT_REVERSED:
            self._splitter.setSizes([detail_w, list_w])
        else:
            self._splitter.setSizes([list_w, detail_w])
        self._splitter.blockSignals(False)

    # ── API ───────────────────────────────────────────────

    def refresh(self):
        if hasattr(self._list, "refresh"):
            self._list.refresh()
        QTimer.singleShot(REFRESH_AFTER_SAVE_DELAY, self._apply_sizes)

    def clear_detail(self):
        if hasattr(self._detail, "clear"):
            self._detail.clear()

    def select_item(self, item_id: int):
        """[T-05] من CrudSection — يختار عنصراً برمجياً."""
        if hasattr(self._list, "select_item"):
            self._list.select_item(item_id)
        self._on_item_selected(item_id)

    @property
    def list_panel(self) -> QWidget:
        return self._list

    @property
    def detail_panel(self) -> QWidget:
        return self._detail

    @property
    def form_panel(self) -> "QWidget | None":
        """[T-05] من CrudSection — يرجع لوحة الفورم (أو None)."""
        return self._form