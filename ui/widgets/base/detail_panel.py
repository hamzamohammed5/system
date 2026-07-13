"""
ui/widgets/base/detail_panel.py
=============================
BaseDetailPanel — قاعدة مشتركة لكل لوحات التفاصيل.

[إصلاح 2.2] from ..theme.styles import scroll_style
         → from ..theme.layout_styles import scroll_style

[i18n] EMPTY_ICON/EMPTY_TITLE الافتراضية، علامة الـ "─" الافتراضية لاسم العنصر،
       ورسالة خطأ التحميل — كلها استُبدلت بمفاتيح tr() من ar.py/en.py.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QSizePolicy
from PyQt5.QtCore    import Qt, pyqtSignal

from ui.constants                    import (
    DETAIL_CONTENT_MIN_W, DETAIL_MIN_W, DETAIL_EMPTY_MIN_H,
    MARGIN_CONTENT_PANEL, SPACING_LG,
    NOTIF_AUTO_HIDE_SUCCESS, NOTIF_AUTO_HIDE_DEFAULT,
)
from ..components.headers_page       import DetailHeader
from ..panels.state                  import EmptyState
from ..components.notification       import NotificationBar
from ui.widgets.core.widget_mixin    import WidgetMixin
from ..theme.layout_styles           import scroll_style   # [إصلاح 2.2]


from ui.widgets.core.i18n import tr


class BaseDetailPanel(QWidget, WidgetMixin):
    """
    قاعدة مشتركة لكل لوحات التفاصيل.

    Override المطلوب:
        _load_data(item_id)  → dict | None
        _fill_data(data)
        _build_content(layout)

    Override الاختياري:
        _build_header_cards()
        _build_header_buttons()
        _fill_header(data)
        _refresh_data(company_id)
        EMPTY_ICON, EMPTY_TITLE, EMPTY_SUBTITLE, HEADER_BG
        MIN_CONTENT_W, CONNECT_BUS
    """

    saved   = pyqtSignal(int)
    deleted = pyqtSignal()

    EMPTY_ICON     : str  = "empty_icon_default"
    EMPTY_TITLE    : str  = "detail_select_item"
    EMPTY_SUBTITLE : str  = ""
    HEADER_BG      : str  = None
    MIN_CONTENT_W  : int  = DETAIL_CONTENT_MIN_W
    CONNECT_BUS    : bool = False

    def __init__(self, conn=None, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._item_id   = None
        self._item_data = None
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumWidth(DETAIL_MIN_W)
        self._build()
        self._set_mode(has_data=False)

        if self.CONNECT_BUS:
            self._init_widget_mixin(theme=True, font=True, lang=True, data=True)
        else:
            self._init_widget_mixin(theme=True, lang=True)
        self._refresh_style()

    # ── override hooks ────────────────────────────────────

    def _build_header_cards(self):
        pass

    def _build_header_buttons(self):
        pass

    def _build_content(self, layout: QVBoxLayout):
        pass

    def _load_data(self, item_id: int):
        return None

    def _fill_data(self, data: dict):
        pass

    def _fill_header(self, data: dict):
        self._hdr.set_title(data.get("name", tr("value_dash")))

    def _refresh_data(self, company_id=None):
        if self._item_id is not None:
            self.load_item(self._item_id)

    # ── بناء الواجهة ──────────────────────────────────────

    def _build(self):
        from ui.theme import _C
        # [إصلاح ثيم — جذري] كنا هنا بنحسب header_bg = self.HEADER_BG or
        # _C['bg_surface'] ونبعتها كـ *قيمة نصية ثابتة* لـ DetailHeader —
        # يعني لو HEADER_BG=None، DetailHeader كانت بتقفل على لون الثيم
        # اللحظي وقت البناء (مثلاً "#FAFAF8" في الثيم الفاتح) للأبد، وكل
        # تحديث لاحق لـ _C['bg_surface'] (بعد تبديل الثيم) ما كانش بيوصلها،
        # لأن DetailHeader._refresh_style() كانت تُعيد رسم نفس القيمة
        # الثابتة دي في كل مرة بدل قراءة _C الحيّة.
        #
        # الحل: لو مفيش HEADER_BG مخصص فعليًا من الـ subclass، نبعت bg=None
        # صراحةً — وDetailHeader (بعد تعديلها في headers_page.py) بتتعامل
        # مع None كـ "تابع لون الثيم دايمًا" وتقرأ _C['bg_surface'] وقت كل
        # رسم فعلي، مش نسخة قديمة منه.
        header_bg = self.HEADER_BG  # None لو مفيش تخصيص — يبقى ياخده DetailHeader كـ "تابع الثيم"

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._notif = NotificationBar(show_dismiss=True)
        root.addWidget(self._notif)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet(scroll_style())
        self._scroll = scroll

        inner = QWidget()
        inner.setMinimumWidth(self.MIN_CONTENT_W)
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(0, 0, 0, 0)
        inner_lay.setSpacing(0)

        self._hdr = DetailHeader(bg=header_bg)
        self._build_header_cards()
        self._build_header_buttons()
        inner_lay.addWidget(self._hdr)

        content = QWidget()
        self._content_lay = QVBoxLayout(content)
        self._content_lay.setContentsMargins(*MARGIN_CONTENT_PANEL)
        self._content_lay.setSpacing(SPACING_LG)
        self._build_content(self._content_lay)
        self._content_lay.addStretch()
        inner_lay.addWidget(content, stretch=1)

        scroll.setWidget(inner)
        root.addWidget(scroll, stretch=1)

        self._empty = EmptyState(
            icon=tr(self.EMPTY_ICON), title=tr(self.EMPTY_TITLE),
            subtitle=self.EMPTY_SUBTITLE,
            style="plain", color=_C['text_muted'], min_height=DETAIL_EMPTY_MIN_H,
        )
        root.addWidget(self._empty)

    # ── [i18n/themes] Theme & Language handlers ───────────

    def _refresh_style(self, *_):
        from ui.theme import _C
        _bg = _C['bg_page']
        self._bg_color = _bg
        self.setStyleSheet(f"background:{_bg};")
        self._scroll.setStyleSheet(scroll_style())
        inner = self._scroll.widget()
        if inner:
            inner.setStyleSheet(f"background:{_bg};")
            for child in inner.children():
                if isinstance(child, QWidget) and child is not self._hdr:
                    child.setStyleSheet(f"background:{_bg};")
        # تحديث لون header عند تغيير الثيم (لو لم يُحدَّد HEADER_BG ثابت)
        # [إصلاح ثيم] كان هنا كود بيكتب self._hdr.setStyleSheet(...) يدويًا
        # كمحاولة تصحيح خارجي للون الهيدر — لكنه كان بيتضارب مع
        # DetailHeader._refresh_style() الخاصة بيها (اللي بتتنفذ أيضًا عند
        # نفس bus.theme_changed، بترتيب غير مضمون). بعد إصلاح DetailHeader
        # نفسها لتقرأ _C['bg_surface'] الحيّة بدل نسخة ثابتة قديمة، التصحيح
        # اليدوي هنا بقى غير لازم ومصدر تضارب — تمت إزالته.
        # [إصلاح ثيم — dark bug] لوحظ إن DetailHeader (self._hdr) وأي
        # QWidget شفاف جواه (زي top/cards_section/_tb_section اللي معمولة
        # بـ setStyleSheet("background:transparent;") مرة واحدة وقت البناء)
        # أحيانًا بتفضل بستايل الثيم القديم — تحديدًا لو الـ panel اتبنى
        # وهو مش ظاهر فعليًا (تاب غير نشط)، فـ Qt بيأجل إعادة رسم بعض
        # الـ QFrame المتداخلة (caching) لحد أول repaint كامل بعد الظهور.
        # نفس المشكلة اللي وثّقناها في ThemedFrame.showEvent — لكن هنا
        # عندنا شجرة widgets متداخلة مش frame واحدة.
        #
        # الحل: نجبر repolish فعلي (unpolish + polish) على self._hdr وكل
        # أبناءه المباشرين المرئيين، عشان نضمن Qt يعيد تطبيق الـ QSS من
        # الصفر بدل ما يعتمد على cache قديم.
        self._force_repolish(self._hdr)

    def _force_repolish(self, widget: QWidget):
        """يجبر Qt يعيد تطبيق الـ stylesheet من الصفر (unpolish + polish)
        على widget وكل أبناءه، بدل الاعتماد على إعادة رسم تلقائية قد
        تستخدم نسخة قديمة (cached) من الستايل."""
        if widget is None:
            return
        style = widget.style()
        for w in [widget] + widget.findChildren(QWidget):
            try:
                style.unpolish(w)
                style.polish(w)
                w.update()
            except RuntimeError:
                pass

    def _refresh_lang(self, *_):
        translated = tr(self.EMPTY_TITLE)
        try:
            self._empty.set_title(translated)
        except Exception:
            pass

    # ── public API ────────────────────────────────────────

    def load_item(self, item_id: int):
        self._item_id = item_id
        try:
            data = self._load_data(item_id)
        except Exception as e:
            self.show_error(tr("detail_load_error").format(error=e))
            return

        self._item_data = dict(data) if data else None
        if not self._item_data:
            self._set_mode(has_data=False)
            return

        self._set_mode(has_data=True)
        self._fill_header(self._item_data)
        self._fill_data(self._item_data)

    def clear(self):
        self._item_id   = None
        self._item_data = None
        self._notif.hide_bar()
        self._set_mode(has_data=False)

    # ── إشعارات ───────────────────────────────────────────

    def show_success(self, msg: str, auto_hide: int = NOTIF_AUTO_HIDE_SUCCESS):
        self._notif.show(msg, "success", auto_hide)

    def show_error(self, msg: str):
        self._notif.show(msg, "danger")

    def show_warning(self, msg: str, auto_hide: int = NOTIF_AUTO_HIDE_DEFAULT):
        self._notif.show(msg, "warning", auto_hide)

    def show_info(self, msg: str, auto_hide: int = NOTIF_AUTO_HIDE_DEFAULT):
        self._notif.show(msg, "info", auto_hide)

    # ── state ─────────────────────────────────────────────

    def _set_mode(self, has_data: bool):
        self._scroll.setVisible(has_data)
        self._hdr.setVisible(has_data)
        self._empty.setVisible(not has_data)

    # ── خصائص ────────────────────────────────────────────

    @property
    def item_id(self) -> "int | None":
        return self._item_id

    @property
    def item_data(self) -> "dict | None":
        return self._item_data

    @property
    def header(self) -> DetailHeader:
        return self._hdr

    @property
    def content_layout(self) -> QVBoxLayout:
        return self._content_lay