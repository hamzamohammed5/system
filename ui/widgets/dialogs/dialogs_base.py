"""
ui/widgets/dialogs/dialogs_base.py
====================================
دمج shell.py + base.py — Base classes للـ dialogs.

الملفات المحذوفة: shell.py, base.py

[إصلاح ثيم] DialogShell و BaseDialog كانا يبنيان كل الـ stylesheets
          (خلفية، هيدر بتدرج لوني، فواصل، شريط أزرار) مرة واحدة بس
          في __init__ بقيم _C و get_font_size وقت الإنشاء. بما أنهم
          QDialog (نافذة منفصلة)، الستايل كان بيتجمد طول عمر الـ dialog
          حتى لو الثيم اتغير وهي مفتوحة. الحل: استخدام WidgetMixin
          (theme=True, font=True) وفصل بناء الـ widgets (مرة واحدة)
          عن تطبيق الـ stylesheet (يتكرر عبر _refresh_style).
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QWidget, QPushButton,
)
from PyQt5.QtCore import Qt

from ui.theme import _C
from ui.font  import get_font_size, fs
from ..components.button import make_btn
from ..core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import (
    DIALOG_HDR_H_WITH_SUB, DIALOG_HDR_H,
    DIALOG_BTN_BAR_H, DIALOG_BTN_MIN_H, DIALOG_MIN_WIDTH,
    DIALOG_BODY_MARGINS, DIALOG_HDR_MARGIN_H, DIALOG_HDR_COL_SPACING,
    DIALOG_BTN_PAD_H, BTN_BORDER_RADIUS, SPACING_MD,
    BASE_DIALOG_DEFAULT_SIZE,
)


# ══════════════════════════════════════════════════════════
# DialogShell  (كان في shell.py)
# ══════════════════════════════════════════════════════════

class DialogShell(QDialog, WidgetMixin):
    """
    هيكل نافذة موحد:
      - هيدر ملون مع أيقونة وعنوان
      - منطقة محتوى (body_layout)
      - شريط أزرار (btn_layout)
      - RTL + modal تلقائي

    [تحسين 21] _make_header: استبدال `{a}dd` بـ `accent_transparent` واضح الاسم.
    """

    def __init__(self, parent=None, title: str = "", icon: str = None,
                 subtitle: str = "", accent: str = None,
                 min_width: int = DIALOG_MIN_WIDTH, min_height: int = 0):
        super().__init__(
            parent,
            Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint,
        )
        icon = icon or tr("icon_dialog_default")
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(min_width)
        if min_height:
            self.setMinimumHeight(min_height)
        self.setLayoutDirection(Qt.RightToLeft)
        self._accent  = accent or _C['accent']
        self._icon    = icon
        self._title   = title
        self._subtitle = subtitle
        self._build(icon, title, subtitle)
        # [إصلاح ثيم] DialogShell ما بيستدعيش _init_widget_mixin هنا —
        # كل subclass (MessageDialog, ConfirmDialog, ...) بيستدعيها مرة
        # واحدة بعد super().__init__() بالـ flags اللي يحتاجها فعلاً
        # (مثلاً lang=True لو فيه نصوص قابلة للترجمة). DialogShell
        # نفسه مفيهوش نصوص قابلة للترجمة فمحتاج theme+font بس.

    def _build(self, icon: str, title: str, subtitle: str):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        self._header = self._make_header(icon, title, subtitle)
        root.addWidget(self._header)

        self._body = QWidget()
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(*DIALOG_BODY_MARGINS)
        self._body_layout.setSpacing(SPACING_MD)
        root.addWidget(self._body, stretch=1)

        self._sep = QFrame()
        self._sep.setFrameShape(QFrame.HLine)
        self._sep.setFixedHeight(1)
        root.addWidget(self._sep)

        self._bar = QWidget()
        self._bar.setFixedHeight(DIALOG_BTN_BAR_H)
        self._btn_layout = QHBoxLayout(self._bar)
        self._btn_layout.setContentsMargins(DIALOG_HDR_MARGIN_H, 0, DIALOG_HDR_MARGIN_H, 0)
        self._btn_layout.setSpacing(SPACING_MD)
        self._btn_layout.addStretch()
        root.addWidget(self._bar)

    def _make_header(self, icon: str, title: str, subtitle: str) -> QFrame:
        hdr = QFrame()
        hdr.setFixedHeight(DIALOG_HDR_H_WITH_SUB if subtitle else DIALOG_HDR_H)

        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(DIALOG_HDR_MARGIN_H, 0, DIALOG_HDR_MARGIN_H, 0)
        lay.setSpacing(SPACING_MD)

        self._lbl_ico = QLabel(icon)
        self._lbl_ico.setAlignment(Qt.AlignVCenter)
        lay.addWidget(self._lbl_ico)

        col = QVBoxLayout()
        col.setSpacing(DIALOG_HDR_COL_SPACING)

        self._lbl_title = QLabel(title)
        col.addWidget(self._lbl_title)

        self._lbl_sub = None
        if subtitle:
            self._lbl_sub = QLabel(subtitle)
            col.addWidget(self._lbl_sub)

        lay.addLayout(col)
        lay.addStretch()
        return hdr

    def _refresh_style(self, *_):
        base = get_font_size()
        a = self._accent
        accent_transparent = a + "cc"

        self.setStyleSheet(
            f"QDialog {{ background:{_C['bg_page']}; }}"
        )
        self._body.setStyleSheet(f"background:{_C['bg_page']};")
        self._sep.setStyleSheet(f"background:{_C['border']}; border:none;")
        self._bar.setStyleSheet(f"background:{_C['bg_surface']};")

        self._header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {a}, stop:1 {accent_transparent});
                border-bottom:2px solid {a}99;
            }}
        """)

        self._lbl_ico.setStyleSheet(
            f"font-size:{fs(base,+2)}pt; background:transparent; border:none;"
        )
        self._lbl_title.setStyleSheet(
            f"font-size:{fs(base,+1)}pt; font-weight:bold; color:{_C['btn_primary_text']};"
            "background:transparent; border:none;"
        )
        if self._lbl_sub is not None:
            self._lbl_sub.setStyleSheet(
                f"font-size:{fs(base,-1)}pt; color:{_C['dialog_hdr_sub_text']};"
                "background:transparent; border:none;"
            )

    @property
    def body_layout(self) -> QVBoxLayout:
        return self._body_layout

    @property
    def btn_layout(self) -> QHBoxLayout:
        return self._btn_layout


# ══════════════════════════════════════════════════════════
# BaseDialog  (كان في base.py)
# ══════════════════════════════════════════════════════════

class BaseDialog(DialogShell):
    """
    قاعدة مشتركة للـ dialogs.

    Override:
        _build_content(lay) → أضف المحتوى
        _on_accept()        → منطق الحفظ
    """

    def __init__(self, parent=None, title: str = "", icon: str = None,
                 subtitle: str = "", min_size: tuple = BASE_DIALOG_DEFAULT_SIZE,
                 accent: str = None, show_btns: bool = True):
        self._btn_ok = None
        icon = icon or tr("icon_dialog_default")
        super().__init__(
            parent, title=title, icon=icon, subtitle=subtitle,
            accent=accent, min_width=min_size[0], min_height=min_size[1],
        )
        self._init_widget_mixin(theme=True, font=True)
        if show_btns:
            self._add_default_buttons()
        else:
            self._btn_ok = QPushButton()  # dummy

        self._build_content(self._body_layout)
        self._refresh_style()

    def _add_default_buttons(self):
        btn_cancel = make_btn(tr("btn_cancel"), "ghost")
        btn_cancel.setMinimumHeight(DIALOG_BTN_MIN_H)
        btn_cancel.clicked.connect(self.reject)

        self._btn_ok = make_btn(tr("btn_save"), "primary")
        self._btn_ok.setMinimumHeight(DIALOG_BTN_MIN_H)

        self._btn_ok.clicked.connect(self._on_accept)
        self.btn_layout.addWidget(btn_cancel)
        self.btn_layout.addWidget(self._btn_ok)

    def _refresh_style(self, *_):
        super()._refresh_style()
        if not self._btn_ok or not self._accent:
            return
        if self._accent == _C.get("accent"):
            return
        base = get_font_size()
        self._btn_ok.setStyleSheet(f"""
            QPushButton {{
                background:{self._accent}; color:{_C['btn_primary_text']}; font-weight:bold;
                border-radius:{BTN_BORDER_RADIUS}px; padding:0 {DIALOG_BTN_PAD_H}px;
                font-size:{fs(base,0)}pt; border:none; min-height:{DIALOG_BTN_MIN_H}px;
            }}
            QPushButton:hover {{ background:{self._accent}dd; }}
            QPushButton:disabled {{ background:{_C['text_disabled']}; }}
        """)

    def _build_content(self, lay: QVBoxLayout):
        pass

    def _on_accept(self):
        self.accept()

    def set_ok_enabled(self, enabled: bool):
        if hasattr(self, "_btn_ok"):
            self._btn_ok.setEnabled(enabled)

    def set_ok_text(self, text: str):
        if hasattr(self, "_btn_ok"):
            self._btn_ok.setText(text)