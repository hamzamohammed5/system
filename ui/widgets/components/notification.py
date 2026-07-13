"""
ui/widgets/components/notification.py
=======================================
NotificationBar  — شريط إشعارات مؤقت.
BaseWarningBar   — شريط تحذير ثابت مع أزرار إصلاح وتعديل.

[Refactor V3] إصلاح imports: ui.app_settings → ui.theme + ui.font
"""
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore    import QTimer, pyqtSignal

from ui.widgets.panels.themed_inputs import ThemedFrame

from ui.theme import _C
from ui.font  import fs, get_font_size
from ..core.colors import status_colors
from ..core.i18n import tr
from ..core.widget_mixin import WidgetMixin
from ui.constants import (
    NOTIF_MARGIN_H, NOTIF_MARGIN_V, NOTIF_SPACING, NOTIF_BORDER_W,
    DISMISS_BTN_SIZE, SPACING_MD, BTN_BORDER_RADIUS,
)


def _icons() -> dict:
    return {
        "success": tr('notif_icon_success'),
        "info":    tr('notif_icon_info'),
        "warning": tr('notif_icon_warning'),
        "danger":  tr('notif_icon_danger'),
    }


# ══════════════════════════════════════════════════════════
# NotificationBar
# ══════════════════════════════════════════════════════════

class NotificationBar(ThemedFrame, WidgetMixin):
    """شريط إشعارات مؤقت مع دعم الإغلاق والإخفاء التلقائي."""

    dismissed = pyqtSignal()

    def __init__(self, show_dismiss: bool = True, parent=None):
        super().__init__(parent)
        self._show_dismiss = show_dismiss
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide_bar)
        self._level = "info"
        self._message = ""
        self._build()
        self._init_widget_mixin(theme=True, font=True, lang=True)
        self._refresh_style()

    def _build(self):
        self.setObjectName("notifBar")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(NOTIF_MARGIN_H, NOTIF_MARGIN_V,
                               NOTIF_MARGIN_H, NOTIF_MARGIN_V)
        lay.setSpacing(NOTIF_SPACING)

        self._lbl_icon = QLabel()
        lay.addWidget(self._lbl_icon)

        self._lbl_msg = QLabel()
        self._lbl_msg.setWordWrap(True)
        lay.addWidget(self._lbl_msg, stretch=1)

        self._btn_dismiss = None
        if self._show_dismiss:
            btn = QPushButton(tr('dismiss_icon'))
            btn.setFixedSize(DISMISS_BTN_SIZE, DISMISS_BTN_SIZE)
            btn.clicked.connect(self._on_dismiss)
            lay.addWidget(btn)
            self._btn_dismiss = btn

    def _refresh_style(self, *_):
        base = get_font_size()
        cfg = status_colors(self._level)

        self.setStyleSheet(f"""
            #notifBar {{
                background:{cfg['bg']}; border:{NOTIF_BORDER_W}px solid {cfg['border']};
                border-radius:{BTN_BORDER_RADIUS}px;
            }}
        """)
        self._lbl_icon.setStyleSheet(
            f"background:transparent; border:none; font-size:{fs(base, 0)}pt;"
        )
        self._lbl_msg.setStyleSheet(
            f"font-size:{fs(base, 0)}pt; font-weight:600;"
            f"color:{cfg['fg']}; background:transparent; border:none;"
        )
        if self._btn_dismiss:
            self._btn_dismiss.setStyleSheet(
                f"QPushButton{{background:transparent;border:none;"
                f"color:{_C['text_muted']};}}"
                f"QPushButton:hover{{color:{_C['text_primary']};}}"
            )

    def show(self, message: str, level: str = "info", auto_hide: int = 0):
        self._level = level
        self._message = message
        icon = _icons().get(level, tr('notif_icon_info'))

        self._lbl_icon.setText(icon)
        self._lbl_msg.setText(message)
        self._refresh_style()
        self.setVisible(True)

        if auto_hide > 0:
            self._timer.start(auto_hide)

    def _refresh_lang(self, *_):
        if self._btn_dismiss:
            self._btn_dismiss.setText(tr('dismiss_icon'))
        if self._message:
            self._lbl_icon.setText(_icons().get(self._level, tr('notif_icon_info')))

    def hide_bar(self):
        self._timer.stop()
        self.setVisible(False)

    def _on_dismiss(self):
        self.hide_bar()
        self.dismissed.emit()


# ══════════════════════════════════════════════════════════
# BaseWarningBar
# ══════════════════════════════════════════════════════════

class BaseWarningBar(ThemedFrame, WidgetMixin):
    """شريط تحذير أفقي موحد مع أزرار إصلاح وتعديل."""

    fix_clicked  = pyqtSignal()
    edit_clicked = pyqtSignal()
    dismissed    = pyqtSignal()

    def __init__(self, on_fix=None, on_edit=None,
                 fix_text: str = None,
                 edit_text: str = None,
                 show_dismiss: bool = True, parent=None):
        super().__init__(parent)
        self._custom_fix_text  = fix_text
        self._custom_edit_text = edit_text
        self._fix_text  = fix_text if fix_text is not None else tr('warning_bar_fix_text')
        self._edit_text = edit_text if edit_text is not None else tr('warning_bar_edit_text')
        self._last_message = ""
        self._build(show_dismiss)
        self._init_widget_mixin(theme=True, font=True, lang=True)
        self._refresh_style()
        self.setVisible(False)

        if on_fix:
            self.fix_clicked.connect(on_fix)
        if on_edit:
            self.edit_clicked.connect(on_edit)

    def _build(self, show_dismiss: bool):
        self.setObjectName("warningBar")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(NOTIF_MARGIN_H, NOTIF_MARGIN_V,
                               NOTIF_MARGIN_H, NOTIF_MARGIN_V)
        lay.setSpacing(SPACING_MD)

        self._lbl_icon = QLabel(tr('warning_bar_icon'))
        lay.addWidget(self._lbl_icon)

        self._lbl = QLabel()
        self._lbl.setWordWrap(True)
        lay.addWidget(self._lbl, stretch=1)

        from .button import make_btn
        self._btn_fix  = make_btn(self._fix_text,  "danger")
        self._btn_edit = make_btn(self._edit_text, "primary")
        self._btn_fix.clicked.connect(self.fix_clicked.emit)
        self._btn_edit.clicked.connect(self.edit_clicked.emit)
        lay.addWidget(self._btn_fix)
        lay.addWidget(self._btn_edit)

        self._btn_dismiss = None
        if show_dismiss:
            btn_x = make_btn(tr('dismiss_icon'), "ghost")
            btn_x.clicked.connect(self._on_dismiss)
            lay.addWidget(btn_x)
            self._btn_dismiss = btn_x

    def _refresh_style(self, *_):
        s = status_colors("warning")
        base = get_font_size()

        self.setStyleSheet(f"""
            #warningBar {{
                background:{s['bg']}; border:{NOTIF_BORDER_W}px solid {s['border']};
                border-radius:{BTN_BORDER_RADIUS}px;
            }}
        """)
        self._lbl_icon.setStyleSheet(
            f"font-size:{fs(base, +2)}pt; background:transparent; border:none;"
        )
        self._lbl.setStyleSheet(
            f"color:{s['fg']}; font-weight:bold; background:transparent; border:none;"
        )

    def show_message(self, message: str, fix_text: str = None, edit_text: str = None):
        self._last_message = message
        self._lbl.setText(message)
        if fix_text:
            self._custom_fix_text = fix_text
            self._btn_fix.setText(fix_text)
        if edit_text:
            self._custom_edit_text = edit_text
            self._btn_edit.setText(edit_text)
        self.setVisible(True)

    def show_orphans(self, orphans: list, product_name: str,
                     type_labels: dict = None):
        if not orphans:
            self.setVisible(False)
            return
        self._last_orphans = orphans
        self._last_product_name = product_name
        self._last_type_labels = type_labels
        _labels = type_labels or {
            "raw": tr('orphan_type_raw'), "semi": tr('orphan_type_semi'),
            "labor_op": tr('orphan_type_labor_op'), "machine_op": tr('orphan_type_machine_op'),
        }
        lines = [
            tr('orphan_line_item').format(
                type_label=_labels.get(o['child_type'], o['child_type']),
                name=o.get('child_name') or f"ID:{o['child_id']}",
            )
            for o in orphans
        ]
        msg = tr('orphans_warning_msg').format(
            product_name=product_name, count=len(orphans), lines="  ".join(lines)
        )
        self.show_message(msg)

    def hide_warning(self):
        self.setVisible(False)

    def _refresh_lang(self, *_):
        self._lbl_icon.setText(tr('warning_bar_icon'))
        if self._btn_dismiss:
            self._btn_dismiss.setText(tr('dismiss_icon'))
        if self._custom_fix_text is None:
            self._fix_text = tr('warning_bar_fix_text')
            self._btn_fix.setText(self._fix_text)
        if self._custom_edit_text is None:
            self._edit_text = tr('warning_bar_edit_text')
            self._btn_edit.setText(self._edit_text)
        if getattr(self, '_last_orphans', None):
            self.show_orphans(self._last_orphans, self._last_product_name, self._last_type_labels)

    def set_fix_visible(self, v: bool):
        self._btn_fix.setVisible(v)

    def set_edit_visible(self, v: bool):
        self._btn_edit.setVisible(v)

    def _on_dismiss(self):
        self.setVisible(False)
        self.dismissed.emit()